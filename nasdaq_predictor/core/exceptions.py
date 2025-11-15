"""
Custom exception hierarchy for NQP application.

Provides typed exceptions for better error handling and recovery.
"""


class NQPException(Exception):
    """Base exception for all NQP application errors."""

    pass


class DataFetchException(NQPException):
    """Raised when external data fetching fails.

    Examples:
        - Yahoo Finance API timeout
        - Invalid ticker symbol
        - Network connectivity issues
    """

    pass


class AnalysisException(NQPException):
    """Raised when market analysis fails.

    Examples:
        - Insufficient data for analysis
        - Invalid calculation results
        - Reference level calculation errors
    """

    pass


class DatabaseException(NQPException):
    """Raised when database operations fail.

    Examples:
        - Connection timeout
        - Query execution error
        - Data integrity violation
    """

    pass


class ValidationException(NQPException):
    """Raised when input validation fails.

    Examples:
        - Invalid ticker symbol
        - Out-of-range values
        - Missing required fields
    """

    pass


class SchedulerException(NQPException):
    """Raised when scheduler operations fail.

    Examples:
        - Job execution error
        - Invalid schedule configuration
        - Job not found
    """

    pass


class CacheException(NQPException):
    """Raised when caching operations fail.

    Examples:
        - Cache miss
        - Stale cache data
        - Cache corruption
    """

    pass


class TickerNotFoundException(NQPException):
    """Raised when a ticker symbol cannot be resolved to UUID.

    Examples:
        - Ticker symbol not found in database
        - Invalid ticker symbol provided
        - Ticker configuration missing
    """

    pass


class DataNotFoundException(NQPException):
    """Raised when required market data cannot be found.

    Examples:
        - No OHLC data available for time range
        - Supabase query returned empty result
        - Historical data not yet synced
    """

    pass


class InsufficientDataException(NQPException):
    """Raised when market data exists but is insufficient for analysis.

    Examples:
        - Too few OHLC bars for hourly analysis
        - Incomplete bars (missing OHLC values)
        - Data gaps in time series
    """

    pass
