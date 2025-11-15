"""
Data quality validation for OHLC data before storage.

Ensures data integrity and prevents corrupt values in database.
Validates OHLC constraints, data ranges, and common error conditions.

Constraints enforced:
1. All prices must be >= 0 (no negative prices)
2. High >= max(Open, Close)
3. Low <= min(Open, Close)
4. No NaN values in prices or volume
5. Volume must be >= 0
6. High >= Low
7. Timestamp must be valid datetime

Example:
    >>> validator = OHLCValidator('NQ=F')
    >>> bar = {
    ...     'open': 100.0,
    ...     'high': 105.0,
    ...     'low': 99.0,
    ...     'close': 103.0,
    ...     'volume': 1000000,
    ...     'timestamp': datetime.now(pytz.UTC)
    ... }
    >>> is_valid, errors = validator.validate_bar(bar)
    >>> if not is_valid:
    ...     print(f"Validation failed: {errors}")
"""

import logging
from typing import Dict, List, Tuple, Any
from datetime import datetime
import math

logger = logging.getLogger(__name__)


class OHLCValidator:
    """Validates OHLC (Open, High, Low, Close) data.

    Provides validation for individual bars and batches of bars.
    Enforces OHLC constraints to prevent corrupt data in database.
    """

    def __init__(self, ticker: str):
        """Initialize OHLC validator.

        Args:
            ticker: Ticker symbol (e.g., 'NQ=F', 'ES=F')
        """
        self.ticker = ticker
        self.validation_errors = []
        self.validation_stats = {
            'total_checked': 0,
            'valid_bars': 0,
            'invalid_bars': 0,
            'nan_errors': 0,
            'constraint_errors': 0,
            'range_errors': 0
        }

    def validate_bar(self, bar: Dict[str, Any]) -> Tuple[bool, List[str]]:
        """Validate a single OHLC bar.

        Args:
            bar: Dictionary with keys: open, high, low, close, volume, timestamp

        Returns:
            Tuple of (is_valid: bool, errors: List[str])
        """
        errors = []
        self.validation_stats['total_checked'] += 1

        # Check for required fields
        required_fields = ['open', 'high', 'low', 'close', 'volume', 'timestamp']
        for field in required_fields:
            if field not in bar:
                errors.append(f"Missing required field: {field}")

        if errors:
            self.validation_stats['invalid_bars'] += 1
            return False, errors

        # Extract values
        try:
            o = float(bar['open'])
            h = float(bar['high'])
            l = float(bar['low'])
            c = float(bar['close'])
            v = float(bar['volume'])
        except (ValueError, TypeError) as e:
            errors.append(f"Invalid numeric value: {e}")
            self.validation_stats['invalid_bars'] += 1
            return False, errors

        # Check for NaN values (NaN != NaN is a standard NaN check)
        nan_found = False
        if math.isnan(o):
            errors.append("NaN value in open price")
            nan_found = True
        if math.isnan(h):
            errors.append("NaN value in high price")
            nan_found = True
        if math.isnan(l):
            errors.append("NaN value in low price")
            nan_found = True
        if math.isnan(c):
            errors.append("NaN value in close price")
            nan_found = True
        if math.isnan(v):
            errors.append("NaN value in volume")
            nan_found = True

        if nan_found:
            self.validation_stats['nan_errors'] += 1
            self.validation_stats['invalid_bars'] += 1
            return False, errors

        # Check for infinite values
        if any(math.isinf(x) for x in [o, h, l, c, v]):
            errors.append("Infinite value detected in OHLC or volume")
            self.validation_stats['invalid_bars'] += 1
            return False, errors

        # Check for negative prices
        if o < 0 or h < 0 or l < 0 or c < 0:
            errors.append(f"Negative prices detected: O={o}, H={h}, L={l}, C={c}")
            self.validation_stats['range_errors'] += 1

        # Check for negative volume
        if v < 0:
            errors.append(f"Negative volume: {v}")
            self.validation_stats['range_errors'] += 1

        # OHLC constraint: H >= max(O,C) and L <= min(O,C)
        max_oc = max(o, c)
        min_oc = min(o, c)

        if h < max_oc:
            errors.append(f"High {h} < max(O,C) {max_oc}")
            self.validation_stats['constraint_errors'] += 1

        if l > min_oc:
            errors.append(f"Low {l} > min(O,C) {min_oc}")
            self.validation_stats['constraint_errors'] += 1

        # Ensure High >= Low
        if h < l:
            errors.append(f"High {h} < Low {l}")
            self.validation_stats['constraint_errors'] += 1

        # Check for extreme outliers (>50% change within bar) - warning only
        if o > 0:
            pct_change = abs((c - o) / o) * 100
            if pct_change > 50:
                logger.warning(f"{self.ticker}: Extreme price change {pct_change:.1f}% in bar")
                # Don't fail validation for extreme outliers, but log warning

        # Check timestamp validity
        try:
            if isinstance(bar['timestamp'], str):
                # Try to parse string timestamp
                datetime.fromisoformat(bar['timestamp'].replace('Z', '+00:00'))
            elif isinstance(bar['timestamp'], datetime):
                # Already a datetime object
                pass
            else:
                errors.append(f"Invalid timestamp type: {type(bar['timestamp'])}")
        except (ValueError, AttributeError) as e:
            errors.append(f"Invalid timestamp: {e}")

        if errors:
            self.validation_stats['invalid_bars'] += 1
            return False, errors

        self.validation_stats['valid_bars'] += 1
        return True, []

    def validate_batch(self, bars: List[Dict[str, Any]]) -> Tuple[bool, List[str], int]:
        """Validate a batch of OHLC bars.

        Args:
            bars: List of bar dictionaries

        Returns:
            Tuple of (all_valid: bool, errors: List[str], valid_count: int)
        """
        total_errors = []
        valid_count = 0

        for i, bar in enumerate(bars):
            is_valid, errors = self.validate_bar(bar)

            if is_valid:
                valid_count += 1
            else:
                total_errors.append(f"Bar {i}: {', '.join(errors)}")

        all_valid = len(total_errors) == 0
        return all_valid, total_errors, valid_count

    def get_stats(self) -> Dict[str, int]:
        """Get validation statistics.

        Returns:
            Dictionary with validation statistics
        """
        return self.validation_stats.copy()

    def get_error_summary(self) -> str:
        """Get summary of validation results.

        Returns:
            Human-readable summary string
        """
        stats = self.validation_stats
        total = stats['total_checked']

        if total == 0:
            return "No bars validated"

        summary = (
            f"Validation Summary ({self.ticker}):\n"
            f"  Total checked: {total}\n"
            f"  Valid bars: {stats['valid_bars']}\n"
            f"  Invalid bars: {stats['invalid_bars']}\n"
            f"    - NaN errors: {stats['nan_errors']}\n"
            f"    - Constraint errors: {stats['constraint_errors']}\n"
            f"    - Range errors: {stats['range_errors']}"
        )
        return summary

    def reset_stats(self) -> None:
        """Reset validation statistics."""
        self.validation_stats = {
            'total_checked': 0,
            'valid_bars': 0,
            'invalid_bars': 0,
            'nan_errors': 0,
            'constraint_errors': 0,
            'range_errors': 0
        }


class DataQualityMonitor:
    """Monitors overall data quality across all tickers.

    Tracks validation metrics over time to detect systematic data issues.
    """

    def __init__(self):
        """Initialize data quality monitor."""
        self.validators: Dict[str, OHLCValidator] = {}
        self.overall_stats = {
            'total_bars_checked': 0,
            'total_valid_bars': 0,
            'total_invalid_bars': 0,
            'tickers_monitored': set()
        }

    def get_validator(self, ticker: str) -> OHLCValidator:
        """Get or create validator for ticker.

        Args:
            ticker: Ticker symbol

        Returns:
            OHLCValidator instance
        """
        if ticker not in self.validators:
            self.validators[ticker] = OHLCValidator(ticker)
        return self.validators[ticker]

    def validate_bar(self, ticker: str, bar: Dict[str, Any]) -> Tuple[bool, List[str]]:
        """Validate bar for specific ticker.

        Args:
            ticker: Ticker symbol
            bar: OHLC bar data

        Returns:
            Tuple of (is_valid, errors)
        """
        validator = self.get_validator(ticker)
        is_valid, errors = validator.validate_bar(bar)

        # Update overall stats
        self.overall_stats['total_bars_checked'] += 1
        self.overall_stats['tickers_monitored'].add(ticker)

        if is_valid:
            self.overall_stats['total_valid_bars'] += 1
        else:
            self.overall_stats['total_invalid_bars'] += 1

        return is_valid, errors

    def get_overall_stats(self) -> Dict[str, Any]:
        """Get overall validation statistics.

        Returns:
            Dictionary with aggregated statistics
        """
        return {
            'total_bars_checked': self.overall_stats['total_bars_checked'],
            'total_valid_bars': self.overall_stats['total_valid_bars'],
            'total_invalid_bars': self.overall_stats['total_invalid_bars'],
            'tickers_monitored': list(self.overall_stats['tickers_monitored']),
            'num_tickers': len(self.overall_stats['tickers_monitored']),
            'validity_rate': (
                self.overall_stats['total_valid_bars'] / self.overall_stats['total_bars_checked'] * 100
                if self.overall_stats['total_bars_checked'] > 0
                else 0
            )
        }

    def get_ticker_stats(self, ticker: str) -> Dict[str, Any]:
        """Get statistics for specific ticker.

        Args:
            ticker: Ticker symbol

        Returns:
            Dictionary with ticker-specific statistics
        """
        validator = self.get_validator(ticker)
        stats = validator.get_stats()
        total = stats['total_checked']

        return {
            'ticker': ticker,
            **stats,
            'validity_rate': (
                stats['valid_bars'] / total * 100
                if total > 0
                else 0
            )
        }
