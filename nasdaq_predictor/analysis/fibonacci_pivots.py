"""
Fibonacci Pivot Point Calculator

Calculates support and resistance levels using Fibonacci ratios.
Formula:
- Pivot Point (PP) = (High + Low + Close) / 3
- Resistance 1 (R1) = PP + 0.382 × (High - Low)
- Resistance 2 (R2) = PP + 0.618 × (High - Low)
- Resistance 3 (R3) = PP + 1.000 × (High - Low)
- Support 1 (S1) = PP - 0.382 × (High - Low)
- Support 2 (S2) = PP - 0.618 × (High - Low)
- Support 3 (S3) = PP - 1.000 × (High - Low)
"""

from dataclasses import dataclass
from datetime import datetime, timedelta
from typing import Dict, List, Optional
import logging

import yfinance as yf
import pandas as pd
import pytz

logger = logging.getLogger(__name__)

# Fibonacci ratios used for pivot calculations
FIB_RATIO_382 = 0.382
FIB_RATIO_618 = 0.618
FIB_RATIO_100 = 1.000


@dataclass
class FibonacciPivotLevels:
    """Data class to hold Fibonacci pivot point levels"""
    ticker_symbol: str
    timeframe: str  # 'daily', 'weekly', 'monthly'
    calculation_date: datetime

    # Source OHLC data
    period_high: float
    period_low: float
    period_close: float

    # Calculated pivot levels
    pivot_point: float
    resistance_1: float
    resistance_2: float
    resistance_3: float
    support_1: float
    support_2: float
    support_3: float

    def to_dict(self) -> Dict:
        """Convert to dictionary for JSON serialization"""
        return {
            'ticker_symbol': self.ticker_symbol,
            'timeframe': self.timeframe,
            'calculation_date': self.calculation_date.isoformat(),
            'period_high': round(self.period_high, 4),
            'period_low': round(self.period_low, 4),
            'period_close': round(self.period_close, 4),
            'pivot_point': round(self.pivot_point, 4),
            'resistance_1': round(self.resistance_1, 4),
            'resistance_2': round(self.resistance_2, 4),
            'resistance_3': round(self.resistance_3, 4),
            'support_1': round(self.support_1, 4),
            'support_2': round(self.support_2, 4),
            'support_3': round(self.support_3, 4)
        }

    def get_all_levels(self) -> List[Dict]:
        """Get all levels as a sorted list with metadata"""
        levels = [
            {'name': 'R3', 'type': 'resistance', 'price': self.resistance_3, 'level': 3},
            {'name': 'R2', 'type': 'resistance', 'price': self.resistance_2, 'level': 2},
            {'name': 'R1', 'type': 'resistance', 'price': self.resistance_1, 'level': 1},
            {'name': 'PP', 'type': 'pivot', 'price': self.pivot_point, 'level': 0},
            {'name': 'S1', 'type': 'support', 'price': self.support_1, 'level': -1},
            {'name': 'S2', 'type': 'support', 'price': self.support_2, 'level': -2},
            {'name': 'S3', 'type': 'support', 'price': self.support_3, 'level': -3}
        ]
        # Sort by price descending (R3 at top, S3 at bottom)
        return sorted(levels, key=lambda x: x['price'], reverse=True)

    def find_closest_levels(self, current_price: float, count: int = 2) -> List[Dict]:
        """
        Find the N closest pivot levels to the current price

        Args:
            current_price: Current market price
            count: Number of closest levels to return (default 2)

        Returns:
            List of closest levels with distance information
        """
        all_levels = self.get_all_levels()

        # Calculate distance for each level
        for level in all_levels:
            level['distance'] = current_price - level['price']
            level['abs_distance'] = abs(level['distance'])

        # Sort by absolute distance
        sorted_levels = sorted(all_levels, key=lambda x: x['abs_distance'])

        # Return top N closest
        return sorted_levels[:count]


class FibonacciPivotCalculator:
    """Calculator for Fibonacci-based pivot points"""

    def __init__(self):
        self.utc = pytz.UTC

    def calculate_pivots(
        self,
        high: float,
        low: float,
        close: float
    ) -> Dict[str, float]:
        """
        Calculate Fibonacci pivot levels from OHLC data

        Args:
            high: Period high price
            low: Period low price
            close: Period close price

        Returns:
            Dictionary with all pivot levels
        """
        # Calculate pivot point
        pivot_point = (high + low + close) / 3

        # Calculate range
        price_range = high - low

        # Calculate resistance levels
        resistance_1 = pivot_point + (FIB_RATIO_382 * price_range)
        resistance_2 = pivot_point + (FIB_RATIO_618 * price_range)
        resistance_3 = pivot_point + (FIB_RATIO_100 * price_range)

        # Calculate support levels
        support_1 = pivot_point - (FIB_RATIO_382 * price_range)
        support_2 = pivot_point - (FIB_RATIO_618 * price_range)
        support_3 = pivot_point - (FIB_RATIO_100 * price_range)

        return {
            'pivot_point': pivot_point,
            'resistance_1': resistance_1,
            'resistance_2': resistance_2,
            'resistance_3': resistance_3,
            'support_1': support_1,
            'support_2': support_2,
            'support_3': support_3
        }

    def fetch_ohlc_data(
        self,
        ticker: str,
        timeframe: str,
        periods: int = 1
    ) -> Optional[pd.DataFrame]:
        """
        Fetch OHLC data from yfinance for specified timeframe

        Args:
            ticker: Ticker symbol (e.g., 'NQ=F')
            timeframe: 'daily', 'weekly', or 'monthly'
            periods: Number of periods to fetch (default 1 for most recent)

        Returns:
            DataFrame with OHLC data or None if error
        """
        try:
            ticker_obj = yf.Ticker(ticker)

            # Map timeframe to yfinance period and interval
            if timeframe == 'daily':
                period = '5d'
                interval = '1d'
            elif timeframe == 'weekly':
                period = '1mo'
                interval = '1wk'
            elif timeframe == 'monthly':
                period = '3mo'
                interval = '1mo'
            else:
                logger.error(f"Invalid timeframe: {timeframe}")
                return None

            # Fetch data
            hist = ticker_obj.history(period=period, interval=interval)

            if hist.empty:
                logger.warning(f"No data returned for {ticker} {timeframe}")
                return None

            # Get most recent N periods
            return hist.tail(periods)

        except Exception as e:
            logger.error(f"Error fetching OHLC data for {ticker} {timeframe}: {e}")
            return None

    def calculate_for_ticker(
        self,
        ticker: str,
        timeframe: str
    ) -> Optional[FibonacciPivotLevels]:
        """
        Calculate Fibonacci pivots for a specific ticker and timeframe

        Args:
            ticker: Ticker symbol (e.g., 'NQ=F')
            timeframe: 'daily', 'weekly', or 'monthly'

        Returns:
            FibonacciPivotLevels object or None if error
        """
        try:
            # Fetch OHLC data
            df = self.fetch_ohlc_data(ticker, timeframe, periods=1)

            if df is None or df.empty:
                logger.error(f"No data available for {ticker} {timeframe}")
                return None

            # Get most recent period data
            latest = df.iloc[-1]
            high = float(latest['High'])
            low = float(latest['Low'])
            close = float(latest['Close'])

            # Get calculation date (timestamp of the bar)
            calc_date = pd.Timestamp(latest.name).to_pydatetime()
            if calc_date.tzinfo is None:
                calc_date = self.utc.localize(calc_date)
            else:
                calc_date = calc_date.astimezone(self.utc)

            # Calculate pivot levels
            pivots = self.calculate_pivots(high, low, close)

            # Create FibonacciPivotLevels object
            return FibonacciPivotLevels(
                ticker_symbol=ticker,
                timeframe=timeframe,
                calculation_date=calc_date,
                period_high=high,
                period_low=low,
                period_close=close,
                pivot_point=pivots['pivot_point'],
                resistance_1=pivots['resistance_1'],
                resistance_2=pivots['resistance_2'],
                resistance_3=pivots['resistance_3'],
                support_1=pivots['support_1'],
                support_2=pivots['support_2'],
                support_3=pivots['support_3']
            )

        except Exception as e:
            logger.error(f"Error calculating pivots for {ticker} {timeframe}: {e}", exc_info=True)
            return None

    def calculate_all_timeframes(
        self,
        ticker: str
    ) -> Dict[str, Optional[FibonacciPivotLevels]]:
        """
        Calculate Fibonacci pivots for all timeframes (daily, weekly, monthly)

        Args:
            ticker: Ticker symbol (e.g., 'NQ=F')

        Returns:
            Dictionary with timeframe as key and FibonacciPivotLevels as value
        """
        results = {}
        timeframes = ['daily', 'weekly', 'monthly']

        for timeframe in timeframes:
            logger.info(f"Calculating {timeframe} pivots for {ticker}")
            results[timeframe] = self.calculate_for_ticker(ticker, timeframe)

        return results

    def calculate_all_tickers(
        self,
        tickers: List[str]
    ) -> Dict[str, Dict[str, Optional[FibonacciPivotLevels]]]:
        """
        Calculate Fibonacci pivots for multiple tickers across all timeframes

        Args:
            tickers: List of ticker symbols (e.g., ['NQ=F', 'ES=F', '^FTSE'])

        Returns:
            Nested dictionary: {ticker: {timeframe: FibonacciPivotLevels}}
        """
        results = {}

        for ticker in tickers:
            logger.info(f"Calculating Fibonacci pivots for {ticker}")
            results[ticker] = self.calculate_all_timeframes(ticker)

        return results


def calculate_fibonacci_pivots_for_all() -> Dict[str, Dict[str, Optional[FibonacciPivotLevels]]]:
    """
    Convenience function to calculate Fibonacci pivots for all configured tickers

    Returns:
        Nested dictionary with all calculations
    """
    # Default tickers (NQ=F, ES=F, ^FTSE)
    tickers = ['NQ=F', 'ES=F', '^FTSE']

    calculator = FibonacciPivotCalculator()
    return calculator.calculate_all_tickers(tickers)


if __name__ == '__main__':
    # Test the calculator
    logging.basicConfig(level=logging.INFO)

    print("Testing Fibonacci Pivot Calculator")
    print("=" * 60)

    calculator = FibonacciPivotCalculator()

    # Test single ticker
    ticker = 'NQ=F'
    timeframe = 'daily'

    result = calculator.calculate_for_ticker(ticker, timeframe)

    if result:
        print(f"\n{ticker} - {timeframe.upper()} Fibonacci Pivots")
        print(f"Calculation Date: {result.calculation_date}")
        print(f"Source Data: H={result.period_high:.2f}, L={result.period_low:.2f}, C={result.period_close:.2f}")
        print(f"\nPivot Levels:")
        print(f"  R3: {result.resistance_3:.2f}")
        print(f"  R2: {result.resistance_2:.2f}")
        print(f"  R1: {result.resistance_1:.2f}")
        print(f"  PP: {result.pivot_point:.2f}")
        print(f"  S1: {result.support_1:.2f}")
        print(f"  S2: {result.support_2:.2f}")
        print(f"  S3: {result.support_3:.2f}")

        # Test closest levels
        current_price = result.period_close
        closest = result.find_closest_levels(current_price, count=2)
        print(f"\nClosest levels to current price ({current_price:.2f}):")
        for i, level in enumerate(closest, 1):
            print(f"  {i}. {level['name']}: {level['price']:.2f} (distance: {level['distance']:.2f})")
    else:
        print(f"Failed to calculate pivots for {ticker} {timeframe}")
