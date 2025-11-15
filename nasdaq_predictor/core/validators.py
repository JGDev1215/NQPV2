"""
Input validation utilities for API endpoints and services.

Provides reusable validators for common data types and constraints.
"""

from datetime import datetime
from typing import List, Set

from .exceptions import ValidationException


class TickerValidator:
    """Validator for market ticker symbols."""

    # Allowed trading instruments
    ALLOWED_TICKERS: Set[str] = {"NQ=F", "ES=F", "^FTSE", "BTC-USD", "ETH-USD"}

    @classmethod
    def validate_ticker(cls, ticker: str) -> str:
        """Validate a ticker symbol.

        Args:
            ticker: The ticker symbol to validate.

        Returns:
            The validated ticker symbol (uppercase).

        Raises:
            ValidationException: If ticker is invalid or not allowed.
        """
        if not isinstance(ticker, str):
            raise ValidationException(f"Ticker must be a string, got {type(ticker)}")

        ticker = ticker.upper().strip()

        if not ticker:
            raise ValidationException("Ticker cannot be empty")

        if len(ticker) > 20:
            raise ValidationException(f"Ticker too long: {ticker} (max 20 chars)")

        if ticker not in cls.ALLOWED_TICKERS:
            raise ValidationException(
                f"Invalid ticker: {ticker}. "
                f"Allowed tickers: {', '.join(sorted(cls.ALLOWED_TICKERS))}"
            )

        return ticker

    @classmethod
    def validate_tickers(cls, tickers: List[str]) -> List[str]:
        """Validate a list of ticker symbols.

        Args:
            tickers: List of ticker symbols.

        Returns:
            List of validated ticker symbols.

        Raises:
            ValidationException: If any ticker is invalid.
        """
        if not isinstance(tickers, list):
            raise ValidationException("Tickers must be a list")

        if not tickers:
            raise ValidationException("Tickers list cannot be empty")

        return [cls.validate_ticker(t) for t in tickers]


class IntervalValidator:
    """Validator for OHLC data intervals."""

    ALLOWED_INTERVALS: Set[str] = {"1m", "5m", "15m", "30m", "1h", "1d", "1wk", "1mo"}

    @classmethod
    def validate_interval(cls, interval: str) -> str:
        """Validate a data interval.

        Args:
            interval: The interval string (e.g., '1h', '1d').

        Returns:
            The validated interval.

        Raises:
            ValidationException: If interval is invalid.
        """
        if not isinstance(interval, str):
            raise ValidationException(f"Interval must be a string, got {type(interval)}")

        interval = interval.lower().strip()

        if interval not in cls.ALLOWED_INTERVALS:
            raise ValidationException(
                f"Invalid interval: {interval}. "
                f"Allowed intervals: {', '.join(sorted(cls.ALLOWED_INTERVALS))}"
            )

        return interval


class TimeframeValidator:
    """Validator for Fibonacci timeframes."""

    ALLOWED_TIMEFRAMES: Set[str] = {"daily", "weekly", "monthly"}

    @classmethod
    def validate_timeframe(cls, timeframe: str) -> str:
        """Validate a Fibonacci timeframe.

        Args:
            timeframe: The timeframe (daily, weekly, monthly).

        Returns:
            The validated timeframe (lowercase).

        Raises:
            ValidationException: If timeframe is invalid.
        """
        if not isinstance(timeframe, str):
            raise ValidationException(f"Timeframe must be a string, got {type(timeframe)}")

        timeframe = timeframe.lower().strip()

        if timeframe not in cls.ALLOWED_TIMEFRAMES:
            raise ValidationException(
                f"Invalid timeframe: {timeframe}. "
                f"Allowed: {', '.join(sorted(cls.ALLOWED_TIMEFRAMES))}"
            )

        return timeframe


class DateValidator:
    """Validator for date ranges."""

    @staticmethod
    def validate_date_range(
        start_date: datetime, end_date: datetime
    ) -> tuple[datetime, datetime]:
        """Validate that start_date is before end_date.

        Args:
            start_date: The start of the date range.
            end_date: The end of the date range.

        Returns:
            Tuple of (start_date, end_date) if valid.

        Raises:
            ValidationException: If start_date >= end_date.
        """
        if not isinstance(start_date, datetime):
            raise ValidationException(f"start_date must be datetime, got {type(start_date)}")

        if not isinstance(end_date, datetime):
            raise ValidationException(f"end_date must be datetime, got {type(end_date)}")

        if start_date >= end_date:
            raise ValidationException(
                f"start_date ({start_date}) must be before end_date ({end_date})"
            )

        return start_date, end_date

    @staticmethod
    def validate_date_string(date_str: str, format: str = "%Y-%m-%d") -> datetime:
        """Validate and parse a date string.

        Args:
            date_str: The date string to parse.
            format: The expected date format.

        Returns:
            Parsed datetime object.

        Raises:
            ValidationException: If date string cannot be parsed.
        """
        try:
            return datetime.strptime(date_str, format)
        except ValueError as e:
            raise ValidationException(f"Invalid date format: {date_str}. Expected {format}") from e


class LimitValidator:
    """Validator for pagination limits."""

    DEFAULT_LIMIT = 100
    MIN_LIMIT = 1
    MAX_LIMIT = 1000

    @classmethod
    def validate_limit(cls, limit: int) -> int:
        """Validate a pagination limit.

        Args:
            limit: The requested limit.

        Returns:
            The validated limit (clamped to min/max).

        Raises:
            ValidationException: If limit is not an integer.
        """
        if not isinstance(limit, int):
            raise ValidationException(f"Limit must be an integer, got {type(limit)}")

        if limit < cls.MIN_LIMIT:
            return cls.MIN_LIMIT

        if limit > cls.MAX_LIMIT:
            return cls.MAX_LIMIT

        return limit


class PriceValidator:
    """Validator for price values."""

    MIN_PRICE = 0.01
    MAX_PRICE = 1_000_000.00

    @classmethod
    def validate_price(cls, price: float) -> float:
        """Validate a price value.

        Args:
            price: The price to validate.

        Returns:
            The validated price.

        Raises:
            ValidationException: If price is invalid.
        """
        if not isinstance(price, (int, float)):
            raise ValidationException(f"Price must be numeric, got {type(price)}")

        if price < cls.MIN_PRICE:
            raise ValidationException(f"Price too low: {price} (minimum {cls.MIN_PRICE})")

        if price > cls.MAX_PRICE:
            raise ValidationException(f"Price too high: {price} (maximum {cls.MAX_PRICE})")

        return float(price)


class ConfidenceValidator:
    """Validator for confidence scores (0-100)."""

    @staticmethod
    def validate_confidence(confidence: float) -> float:
        """Validate a confidence score.

        Args:
            confidence: The confidence percentage (0-100).

        Returns:
            The validated confidence value.

        Raises:
            ValidationException: If confidence is out of range.
        """
        if not isinstance(confidence, (int, float)):
            raise ValidationException(f"Confidence must be numeric, got {type(confidence)}")

        if not 0.0 <= confidence <= 100.0:
            raise ValidationException(
                f"Confidence must be between 0-100, got {confidence}"
            )

        return float(confidence)
