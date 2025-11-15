"""
NQP Core Module

Foundational abstractions, exceptions, and utilities for the entire application.
"""

from .exceptions import (
    NQPException,
    DataFetchException,
    AnalysisException,
    DatabaseException,
    ValidationException,
    SchedulerException,
    CacheException,
)
from .result import Result, Ok, Err
from .validators import (
    TickerValidator,
    DateValidator,
    IntervalValidator,
    TimeframeValidator,
    LimitValidator,
    PriceValidator,
    ConfidenceValidator,
)
from .dtos import (
    OHLCDTO,
    PredictionDTO,
    ReferencePointDTO,
    SignalDTO,
    IntradayPredictionDTO,
    FibonacciPivotDTO,
    AccuracyMetricsDTO,
    MarketSummaryDTO,
    ResponseDTO,
    SchedulerStatusDTO,
    HealthCheckDTO,
)

__all__ = [
    # Exceptions
    "NQPException",
    "DataFetchException",
    "AnalysisException",
    "DatabaseException",
    "ValidationException",
    "SchedulerException",
    "CacheException",
    # Result type
    "Result",
    "Ok",
    "Err",
    # Validators
    "TickerValidator",
    "DateValidator",
    "IntervalValidator",
    "TimeframeValidator",
    "LimitValidator",
    "PriceValidator",
    "ConfidenceValidator",
    # DTOs
    "OHLCDTO",
    "PredictionDTO",
    "ReferencePointDTO",
    "SignalDTO",
    "IntradayPredictionDTO",
    "FibonacciPivotDTO",
    "AccuracyMetricsDTO",
    "MarketSummaryDTO",
    "ResponseDTO",
    "SchedulerStatusDTO",
    "HealthCheckDTO",
]
