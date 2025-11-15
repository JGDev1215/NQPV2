"""
Tests for OHLC data quality validation.

Tests the OHLCValidator and DataQualityMonitor classes to ensure
data integrity constraints are properly enforced before storage.
"""

import pytest
import math
from datetime import datetime
import pytz
from nasdaq_predictor.core.data_quality_validator import OHLCValidator, DataQualityMonitor


class TestOHLCValidator:
    """Test cases for OHLCValidator class."""

    @pytest.fixture
    def validator(self):
        """Create validator instance for testing."""
        return OHLCValidator('NQ=F')

    def test_valid_bar(self, validator, sample_ohlc_bar):
        """Test validation of valid OHLC bar."""
        is_valid, errors = validator.validate_bar(sample_ohlc_bar)

        assert is_valid == True
        assert len(errors) == 0

    def test_valid_bar_with_various_prices(self, validator):
        """Test validation with various valid price combinations."""
        test_cases = [
            {'o': 100.0, 'h': 110.0, 'l': 95.0, 'c': 105.0},  # Normal
            {'o': 100.0, 'h': 100.0, 'l': 100.0, 'c': 100.0},  # Flat
            {'o': 100.0, 'h': 100.5, 'l': 99.5, 'c': 100.0},   # Small range
        ]

        for case in test_cases:
            bar = {
                'open': case['o'],
                'high': case['h'],
                'low': case['l'],
                'close': case['c'],
                'volume': 1000000,
                'timestamp': datetime.now(pytz.UTC).isoformat()
            }
            is_valid, errors = validator.validate_bar(bar)
            assert is_valid, f"Bar should be valid: {case}, errors: {errors}"

    def test_missing_required_field(self, validator):
        """Test rejection of missing required fields."""
        bar = {
            'open': 100.0,
            'high': 105.0,
            'low': 99.0,
            'close': 103.0,
            # Missing volume and timestamp
        }

        is_valid, errors = validator.validate_bar(bar)
        assert is_valid == False
        assert any('Missing' in error or 'missing' in error for error in errors)

    def test_nan_in_open(self, validator):
        """Test rejection of NaN in open price."""
        bar = {
            'open': float('nan'),
            'high': 105.0,
            'low': 99.0,
            'close': 103.0,
            'volume': 1000000,
            'timestamp': datetime.now(pytz.UTC).isoformat()
        }

        is_valid, errors = validator.validate_bar(bar)
        assert is_valid == False
        assert any('NaN' in error for error in errors)

    def test_nan_in_high(self, validator):
        """Test rejection of NaN in high price."""
        bar = {
            'open': 100.0,
            'high': float('nan'),
            'low': 99.0,
            'close': 103.0,
            'volume': 1000000,
            'timestamp': datetime.now(pytz.UTC).isoformat()
        }

        is_valid, errors = validator.validate_bar(bar)
        assert is_valid == False
        assert any('NaN' in error for error in errors)

    def test_nan_in_volume(self, validator):
        """Test rejection of NaN in volume."""
        bar = {
            'open': 100.0,
            'high': 105.0,
            'low': 99.0,
            'close': 103.0,
            'volume': float('nan'),
            'timestamp': datetime.now(pytz.UTC).isoformat()
        }

        is_valid, errors = validator.validate_bar(bar)
        assert is_valid == False
        assert any('NaN' in error for error in errors)

    def test_infinite_price(self, validator):
        """Test rejection of infinite values."""
        bar = {
            'open': 100.0,
            'high': float('inf'),
            'low': 99.0,
            'close': 103.0,
            'volume': 1000000,
            'timestamp': datetime.now(pytz.UTC).isoformat()
        }

        is_valid, errors = validator.validate_bar(bar)
        assert is_valid == False
        assert any('Infinite' in error for error in errors)

    def test_negative_price(self, validator):
        """Test rejection of negative prices."""
        bar = {
            'open': -100.0,  # Negative open
            'high': 105.0,
            'low': 99.0,
            'close': 103.0,
            'volume': 1000000,
            'timestamp': datetime.now(pytz.UTC).isoformat()
        }

        is_valid, errors = validator.validate_bar(bar)
        assert is_valid == False
        assert any('Negative' in error for error in errors)

    def test_negative_volume(self, validator):
        """Test rejection of negative volume."""
        bar = {
            'open': 100.0,
            'high': 105.0,
            'low': 99.0,
            'close': 103.0,
            'volume': -1000000,  # Negative volume
            'timestamp': datetime.now(pytz.UTC).isoformat()
        }

        is_valid, errors = validator.validate_bar(bar)
        assert is_valid == False
        assert any('Negative' in error or 'negative' in error for error in errors)

    def test_high_less_than_max_oc(self, validator):
        """Test rejection when High < max(Open, Close)."""
        bar = {
            'open': 100.0,
            'high': 102.0,  # Too low (less than close)
            'low': 99.0,
            'close': 103.0,
            'volume': 1000000,
            'timestamp': datetime.now(pytz.UTC).isoformat()
        }

        is_valid, errors = validator.validate_bar(bar)
        assert is_valid == False
        assert any('High' in error for error in errors)

    def test_low_greater_than_min_oc(self, validator):
        """Test rejection when Low > min(Open, Close)."""
        bar = {
            'open': 100.0,
            'high': 105.0,
            'low': 101.0,  # Too high (greater than open)
            'close': 102.0,
            'volume': 1000000,
            'timestamp': datetime.now(pytz.UTC).isoformat()
        }

        is_valid, errors = validator.validate_bar(bar)
        assert is_valid == False
        assert any('Low' in error for error in errors)

    def test_high_less_than_low(self, validator):
        """Test rejection when High < Low."""
        bar = {
            'open': 100.0,
            'high': 95.0,  # High < Low
            'low': 99.0,
            'close': 103.0,
            'volume': 1000000,
            'timestamp': datetime.now(pytz.UTC).isoformat()
        }

        is_valid, errors = validator.validate_bar(bar)
        assert is_valid == False
        assert any('High' in error and 'Low' in error for error in errors)

    def test_batch_validation(self, validator, sample_ohlc_bars_24h):
        """Test validation of batch of OHLC bars."""
        is_valid, errors, valid_count = validator.validate_batch(sample_ohlc_bars_24h)

        assert is_valid == True
        assert len(errors) == 0
        assert valid_count == len(sample_ohlc_bars_24h)

    def test_batch_with_invalid_bars(self, validator):
        """Test batch validation with mixed valid/invalid bars."""
        bars = [
            {
                'open': 100.0,
                'high': 105.0,
                'low': 99.0,
                'close': 103.0,
                'volume': 1000000,
                'timestamp': datetime.now(pytz.UTC).isoformat()
            },
            {
                'open': float('nan'),  # Invalid
                'high': 105.0,
                'low': 99.0,
                'close': 103.0,
                'volume': 1000000,
                'timestamp': datetime.now(pytz.UTC).isoformat()
            },
            {
                'open': 100.0,
                'high': 105.0,
                'low': 99.0,
                'close': 103.0,
                'volume': 1000000,
                'timestamp': datetime.now(pytz.UTC).isoformat()
            }
        ]

        is_valid, errors, valid_count = validator.validate_batch(bars)
        assert is_valid == False
        assert len(errors) > 0
        assert valid_count == 2  # Only 2 valid bars

    def test_statistics(self, validator, sample_ohlc_bars_24h):
        """Test that statistics are collected correctly."""
        validator.validate_batch(sample_ohlc_bars_24h)
        stats = validator.get_stats()

        assert stats['total_checked'] == len(sample_ohlc_bars_24h)
        assert stats['valid_bars'] == len(sample_ohlc_bars_24h)
        assert stats['invalid_bars'] == 0

    def test_reset_statistics(self, validator):
        """Test resetting statistics."""
        validator.validate_bar({
            'open': 100.0,
            'high': 105.0,
            'low': 99.0,
            'close': 103.0,
            'volume': 1000000,
            'timestamp': datetime.now(pytz.UTC).isoformat()
        })

        stats_before = validator.get_stats()
        assert stats_before['total_checked'] == 1

        validator.reset_stats()
        stats_after = validator.get_stats()
        assert stats_after['total_checked'] == 0


class TestDataQualityMonitor:
    """Test cases for DataQualityMonitor class."""

    @pytest.fixture
    def monitor(self):
        """Create monitor instance for testing."""
        return DataQualityMonitor()

    def test_single_ticker_validation(self, monitor, sample_ohlc_bar):
        """Test validation for single ticker."""
        is_valid, errors = monitor.validate_bar('NQ=F', sample_ohlc_bar)

        assert is_valid == True
        assert len(errors) == 0

    def test_multiple_tickers(self, monitor, sample_ohlc_bar):
        """Test monitoring multiple tickers."""
        tickers = ['NQ=F', 'ES=F', '^FTSE']

        for ticker in tickers:
            monitor.validate_bar(ticker, sample_ohlc_bar)

        overall_stats = monitor.get_overall_stats()
        assert overall_stats['num_tickers'] == 3
        assert overall_stats['total_bars_checked'] == 3

    def test_validity_rate_calculation(self, monitor):
        """Test validity rate calculation."""
        valid_bar = {
            'open': 100.0,
            'high': 105.0,
            'low': 99.0,
            'close': 103.0,
            'volume': 1000000,
            'timestamp': datetime.now(pytz.UTC).isoformat()
        }

        invalid_bar = {
            'open': float('nan'),
            'high': 105.0,
            'low': 99.0,
            'close': 103.0,
            'volume': 1000000,
            'timestamp': datetime.now(pytz.UTC).isoformat()
        }

        monitor.validate_bar('NQ=F', valid_bar)
        monitor.validate_bar('NQ=F', valid_bar)
        monitor.validate_bar('NQ=F', invalid_bar)

        overall_stats = monitor.get_overall_stats()
        assert overall_stats['total_bars_checked'] == 3
        assert overall_stats['total_valid_bars'] == 2
        assert overall_stats['total_invalid_bars'] == 1
        assert overall_stats['validity_rate'] == pytest.approx(66.67, rel=1)

    def test_ticker_specific_stats(self, monitor, sample_ohlc_bars_24h):
        """Test getting statistics for specific ticker."""
        for bar in sample_ohlc_bars_24h:
            monitor.validate_bar('NQ=F', bar)

        stats = monitor.get_ticker_stats('NQ=F')
        assert stats['ticker'] == 'NQ=F'
        assert stats['total_checked'] == len(sample_ohlc_bars_24h)
        assert stats['valid_bars'] == len(sample_ohlc_bars_24h)


class TestEdgeCases:
    """Test edge cases and boundary conditions."""

    @pytest.fixture
    def validator(self):
        """Create validator instance."""
        return OHLCValidator('TEST')

    def test_zero_volume(self, validator):
        """Test bar with zero volume (valid)."""
        bar = {
            'open': 100.0,
            'high': 105.0,
            'low': 99.0,
            'close': 103.0,
            'volume': 0,  # Zero volume is valid
            'timestamp': datetime.now(pytz.UTC).isoformat()
        }

        is_valid, errors = validator.validate_bar(bar)
        assert is_valid == True

    def test_very_small_prices(self, validator):
        """Test with very small but valid prices."""
        bar = {
            'open': 0.01,
            'high': 0.015,
            'low': 0.009,
            'close': 0.012,
            'volume': 1000000,
            'timestamp': datetime.now(pytz.UTC).isoformat()
        }

        is_valid, errors = validator.validate_bar(bar)
        assert is_valid == True

    def test_very_large_prices(self, validator):
        """Test with very large prices."""
        bar = {
            'open': 100000.0,
            'high': 105000.0,
            'low': 99000.0,
            'close': 103000.0,
            'volume': 1000000,
            'timestamp': datetime.now(pytz.UTC).isoformat()
        }

        is_valid, errors = validator.validate_bar(bar)
        assert is_valid == True

    def test_extreme_volume(self, validator):
        """Test with extreme volume numbers."""
        bar = {
            'open': 100.0,
            'high': 105.0,
            'low': 99.0,
            'close': 103.0,
            'volume': 10**15,  # Very large volume
            'timestamp': datetime.now(pytz.UTC).isoformat()
        }

        is_valid, errors = validator.validate_bar(bar)
        assert is_valid == True

    def test_string_timestamp(self, validator):
        """Test with string timestamp (should work)."""
        bar = {
            'open': 100.0,
            'high': 105.0,
            'low': 99.0,
            'close': 103.0,
            'volume': 1000000,
            'timestamp': '2025-11-15T10:30:00Z'
        }

        is_valid, errors = validator.validate_bar(bar)
        assert is_valid == True

    def test_datetime_timestamp(self, validator):
        """Test with datetime timestamp object (should work)."""
        bar = {
            'open': 100.0,
            'high': 105.0,
            'low': 99.0,
            'close': 103.0,
            'volume': 1000000,
            'timestamp': datetime.now(pytz.UTC)
        }

        is_valid, errors = validator.validate_bar(bar)
        assert is_valid == True

    def test_string_numbers(self, validator):
        """Test with string numbers (should be converted)."""
        bar = {
            'open': '100.0',
            'high': '105.0',
            'low': '99.0',
            'close': '103.0',
            'volume': '1000000',
            'timestamp': datetime.now(pytz.UTC).isoformat()
        }

        is_valid, errors = validator.validate_bar(bar)
        assert is_valid == True

    def test_integer_prices(self, validator):
        """Test with integer prices (should be valid)."""
        bar = {
            'open': 100,  # Integer instead of float
            'high': 105,
            'low': 99,
            'close': 103,
            'volume': 1000000,
            'timestamp': datetime.now(pytz.UTC).isoformat()
        }

        is_valid, errors = validator.validate_bar(bar)
        assert is_valid == True
