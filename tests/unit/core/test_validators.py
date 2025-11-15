"""
Unit tests for validation utilities.

Tests input validation for all data types and constraints.
"""

import pytest
from datetime import datetime
import pytz

from nasdaq_predictor.core.validators import (
    TickerValidator,
    IntervalValidator,
    TimeframeValidator,
    DateValidator,
    LimitValidator,
    PriceValidator,
    ConfidenceValidator,
)
from nasdaq_predictor.core.exceptions import ValidationException


class TestTickerValidator:
    """Test ticker symbol validation."""

    def test_valid_tickers(self):
        """Test validation of allowed tickers."""
        valid_tickers = ["NQ=F", "ES=F", "^FTSE", "BTC-USD", "ETH-USD"]
        for ticker in valid_tickers:
            assert TickerValidator.validate_ticker(ticker) == ticker

    def test_ticker_case_insensitive(self):
        """Test ticker validation is case insensitive."""
        assert TickerValidator.validate_ticker("nq=f") == "NQ=F"
        assert TickerValidator.validate_ticker("es=f") == "ES=F"

    def test_ticker_strip_whitespace(self):
        """Test ticker whitespace is stripped."""
        assert TickerValidator.validate_ticker(" NQ=F ") == "NQ=F"
        assert TickerValidator.validate_ticker("\tES=F\n") == "ES=F"

    def test_invalid_ticker_raises_exception(self):
        """Test invalid ticker raises exception."""
        with pytest.raises(ValidationException) as exc_info:
            TickerValidator.validate_ticker("INVALID")
        assert "Invalid ticker" in str(exc_info.value)

    def test_empty_ticker_raises_exception(self):
        """Test empty ticker raises exception."""
        with pytest.raises(ValidationException) as exc_info:
            TickerValidator.validate_ticker("")
        assert "empty" in str(exc_info.value).lower()

    def test_ticker_too_long_raises_exception(self):
        """Test ticker exceeding max length raises exception."""
        with pytest.raises(ValidationException) as exc_info:
            TickerValidator.validate_ticker("A" * 21)
        assert "too long" in str(exc_info.value).lower()

    def test_non_string_ticker_raises_exception(self):
        """Test non-string ticker raises exception."""
        with pytest.raises(ValidationException):
            TickerValidator.validate_ticker(123)

    def test_validate_tickers_list(self):
        """Test validating list of tickers."""
        tickers = TickerValidator.validate_tickers(["NQ=F", "ES=F", "^FTSE"])
        assert len(tickers) == 3
        assert all(t in ["NQ=F", "ES=F", "^FTSE"] for t in tickers)

    def test_validate_tickers_empty_list_raises_exception(self):
        """Test empty ticker list raises exception."""
        with pytest.raises(ValidationException):
            TickerValidator.validate_tickers([])

    def test_validate_tickers_non_list_raises_exception(self):
        """Test non-list input raises exception."""
        with pytest.raises(ValidationException):
            TickerValidator.validate_tickers("NQ=F")


class TestIntervalValidator:
    """Test interval validation."""

    def test_valid_intervals(self):
        """Test valid intervals."""
        valid = ["1m", "5m", "15m", "30m", "1h", "1d", "1wk", "1mo"]
        for interval in valid:
            assert IntervalValidator.validate_interval(interval) == interval

    def test_interval_case_insensitive(self):
        """Test interval is case insensitive."""
        assert IntervalValidator.validate_interval("1H") == "1h"
        assert IntervalValidator.validate_interval("1D") == "1d"

    def test_invalid_interval_raises_exception(self):
        """Test invalid interval raises exception."""
        with pytest.raises(ValidationException) as exc_info:
            IntervalValidator.validate_interval("2h")
        assert "Invalid interval" in str(exc_info.value)

    def test_non_string_interval_raises_exception(self):
        """Test non-string interval raises exception."""
        with pytest.raises(ValidationException):
            IntervalValidator.validate_interval(1)


class TestTimeframeValidator:
    """Test timeframe validation."""

    def test_valid_timeframes(self):
        """Test valid timeframes."""
        valid = ["daily", "weekly", "monthly"]
        for timeframe in valid:
            assert TimeframeValidator.validate_timeframe(timeframe) == timeframe

    def test_timeframe_case_insensitive(self):
        """Test timeframe is case insensitive."""
        assert TimeframeValidator.validate_timeframe("DAILY") == "daily"
        assert TimeframeValidator.validate_timeframe("Weekly") == "weekly"

    def test_invalid_timeframe_raises_exception(self):
        """Test invalid timeframe raises exception."""
        with pytest.raises(ValidationException) as exc_info:
            TimeframeValidator.validate_timeframe("yearly")
        assert "Invalid timeframe" in str(exc_info.value)


class TestDateValidator:
    """Test date validation."""

    def test_valid_date_range(self):
        """Test valid date range."""
        start = datetime(2025, 1, 1, tzinfo=pytz.UTC)
        end = datetime(2025, 12, 31, tzinfo=pytz.UTC)
        result_start, result_end = DateValidator.validate_date_range(start, end)
        assert result_start == start
        assert result_end == end

    def test_invalid_date_range_raises_exception(self):
        """Test invalid date range raises exception."""
        start = datetime(2025, 12, 31, tzinfo=pytz.UTC)
        end = datetime(2025, 1, 1, tzinfo=pytz.UTC)
        with pytest.raises(ValidationException) as exc_info:
            DateValidator.validate_date_range(start, end)
        assert "before" in str(exc_info.value).lower()

    def test_equal_dates_raises_exception(self):
        """Test equal start and end dates raises exception."""
        date = datetime(2025, 6, 15, tzinfo=pytz.UTC)
        with pytest.raises(ValidationException):
            DateValidator.validate_date_range(date, date)

    def test_non_datetime_raises_exception(self):
        """Test non-datetime input raises exception."""
        with pytest.raises(ValidationException):
            DateValidator.validate_date_range("2025-01-01", "2025-12-31")

    def test_parse_date_string_valid(self):
        """Test parsing valid date string."""
        date = DateValidator.validate_date_string("2025-06-15")
        assert date.year == 2025
        assert date.month == 6
        assert date.day == 15

    def test_parse_date_string_custom_format(self):
        """Test parsing date with custom format."""
        date = DateValidator.validate_date_string("06/15/2025", "%m/%d/%Y")
        assert date.month == 6
        assert date.day == 15

    def test_parse_invalid_date_string_raises_exception(self):
        """Test invalid date string raises exception."""
        with pytest.raises(ValidationException):
            DateValidator.validate_date_string("invalid-date")


class TestLimitValidator:
    """Test pagination limit validation."""

    def test_valid_limit(self):
        """Test valid limits."""
        assert LimitValidator.validate_limit(50) == 50
        assert LimitValidator.validate_limit(100) == 100
        assert LimitValidator.validate_limit(500) == 500

    def test_limit_below_minimum_clamped(self):
        """Test limit below minimum is clamped to minimum."""
        assert LimitValidator.validate_limit(0) == 1
        assert LimitValidator.validate_limit(-10) == 1

    def test_limit_above_maximum_clamped(self):
        """Test limit above maximum is clamped to maximum."""
        assert LimitValidator.validate_limit(2000) == 1000
        assert LimitValidator.validate_limit(5000) == 1000

    def test_non_integer_limit_raises_exception(self):
        """Test non-integer limit raises exception."""
        with pytest.raises(ValidationException):
            LimitValidator.validate_limit("100")

    def test_float_limit_raises_exception(self):
        """Test float limit raises exception."""
        with pytest.raises(ValidationException):
            LimitValidator.validate_limit(50.5)


class TestPriceValidator:
    """Test price value validation."""

    def test_valid_prices(self):
        """Test valid price values."""
        assert PriceValidator.validate_price(100.0) == 100.0
        assert PriceValidator.validate_price(0.01) == 0.01
        assert PriceValidator.validate_price(999999.99) == 999999.99

    def test_integer_price_converted_to_float(self):
        """Test integer prices are converted to float."""
        result = PriceValidator.validate_price(100)
        assert result == 100.0
        assert isinstance(result, float)

    def test_price_too_low_raises_exception(self):
        """Test price below minimum raises exception."""
        with pytest.raises(ValidationException) as exc_info:
            PriceValidator.validate_price(0.001)
        assert "too low" in str(exc_info.value).lower()

    def test_price_too_high_raises_exception(self):
        """Test price above maximum raises exception."""
        with pytest.raises(ValidationException) as exc_info:
            PriceValidator.validate_price(2_000_000.00)
        assert "too high" in str(exc_info.value).lower()

    def test_negative_price_raises_exception(self):
        """Test negative price raises exception."""
        with pytest.raises(ValidationException):
            PriceValidator.validate_price(-100.0)

    def test_non_numeric_price_raises_exception(self):
        """Test non-numeric price raises exception."""
        with pytest.raises(ValidationException):
            PriceValidator.validate_price("100.0")


class TestConfidenceValidator:
    """Test confidence score validation."""

    def test_valid_confidence_scores(self):
        """Test valid confidence scores."""
        assert ConfidenceValidator.validate_confidence(0.0) == 0.0
        assert ConfidenceValidator.validate_confidence(50.0) == 50.0
        assert ConfidenceValidator.validate_confidence(100.0) == 100.0

    def test_confidence_as_integer(self):
        """Test confidence as integer is converted to float."""
        result = ConfidenceValidator.validate_confidence(75)
        assert result == 75.0
        assert isinstance(result, float)

    def test_confidence_too_low_raises_exception(self):
        """Test confidence below 0 raises exception."""
        with pytest.raises(ValidationException) as exc_info:
            ConfidenceValidator.validate_confidence(-1.0)
        assert "0-100" in str(exc_info.value)

    def test_confidence_too_high_raises_exception(self):
        """Test confidence above 100 raises exception."""
        with pytest.raises(ValidationException) as exc_info:
            ConfidenceValidator.validate_confidence(101.0)
        assert "0-100" in str(exc_info.value)

    def test_non_numeric_confidence_raises_exception(self):
        """Test non-numeric confidence raises exception."""
        with pytest.raises(ValidationException):
            ConfidenceValidator.validate_confidence("75")

    def test_boundary_values(self):
        """Test boundary values."""
        assert ConfidenceValidator.validate_confidence(0.0) == 0.0
        assert ConfidenceValidator.validate_confidence(100.0) == 100.0


class TestValidatorIntegration:
    """Test validators working together."""

    def test_validate_prediction_input(self):
        """Test validating complete prediction input."""
        ticker = TickerValidator.validate_ticker("NQ=F")
        interval = IntervalValidator.validate_interval("1h")
        confidence = ConfidenceValidator.validate_confidence(75.5)

        assert ticker == "NQ=F"
        assert interval == "1h"
        assert confidence == 75.5

    def test_validate_data_request(self):
        """Test validating data request parameters."""
        ticker = TickerValidator.validate_ticker("ES=F")
        limit = LimitValidator.validate_limit(500)
        timeframe = TimeframeValidator.validate_timeframe("DAILY")

        assert ticker == "ES=F"
        assert limit == 500
        assert timeframe == "daily"
