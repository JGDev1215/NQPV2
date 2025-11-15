"""
Data Transfer Objects (DTOs) for API requests and responses.

DTOs provide type-safe, validated data structures for moving data between
layers of the application. They help catch errors early and document expected
data formats.
"""

from dataclasses import dataclass, asdict
from datetime import datetime
from typing import Dict, List, Optional, Any


@dataclass
class OHLCDTO:
    """OHLC (Open, High, Low, Close) market data."""

    symbol: str
    timestamp: datetime
    open: float
    high: float
    low: float
    close: float
    volume: int

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        data = asdict(self)
        data["timestamp"] = self.timestamp.isoformat()
        return data


@dataclass
class ReferencePointDTO:
    """A single reference level/point for market analysis."""

    name: str  # e.g., 'daily_open_midnight', 'ny_am_kill_zone_high'
    value: float  # The price level
    weight: float  # Weight in overall signal (0-1.0)

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return asdict(self)


@dataclass
class SignalDTO:
    """Individual signal component."""

    name: str  # Signal name
    value: float  # 0 = bearish, 1 = bullish
    weight: float  # Signal weight in overall calculation
    contribution: float  # value * weight

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return asdict(self)


@dataclass
class PredictionDTO:
    """Prediction result for a ticker."""

    symbol: str
    prediction: str  # 'BULLISH' or 'BEARISH'
    confidence: float  # 0-100 percentage
    weighted_score: float  # 0-1.0 signal score
    timestamp: datetime
    reference_levels: Dict[str, Any]  # All 18 reference levels
    signals: Dict[str, Any]  # Individual signal components
    market_status: str = "UNKNOWN"  # 'OPEN', 'CLOSED', 'PREMARKET'

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        data = asdict(self)
        data["timestamp"] = self.timestamp.isoformat()
        return data


@dataclass
class IntradayPredictionDTO:
    """Hourly prediction for intraday trading."""

    symbol: str
    hour: int  # 9-16 representing 9am-4pm ET
    prediction: str  # 'BULLISH' or 'BEARISH'
    confidence: float  # 0-100
    timestamp: datetime
    next_hour_open: Optional[float] = None  # Expected open of next hour
    reference_level: Optional[float] = None  # Reference level used

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        data = asdict(self)
        data["timestamp"] = self.timestamp.isoformat()
        return data


@dataclass
class FibonacciPivotDTO:
    """Fibonacci pivot levels for a timeframe."""

    symbol: str
    timeframe: str  # 'daily', 'weekly', 'monthly'
    date: datetime
    high: float  # Period high
    low: float  # Period low
    resistance_1: float
    resistance_2: float
    resistance_3: float
    support_1: float
    support_2: float
    support_3: float
    pivot_point: float

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        data = asdict(self)
        data["date"] = self.date.isoformat()
        return data


@dataclass
class AccuracyMetricsDTO:
    """Prediction accuracy statistics."""

    symbol: str
    period_hours: int
    total_predictions: int
    correct_predictions: int
    accuracy_percentage: float
    confidence_avg: float
    timestamp: datetime

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        data = asdict(self)
        data["timestamp"] = self.timestamp.isoformat()
        return data


@dataclass
class MarketSummaryDTO:
    """Summary of all market predictions."""

    timestamp: datetime
    bullish_count: int  # Number of bullish predictions
    bearish_count: int  # Number of bearish predictions
    avg_confidence: float  # Average confidence across all predictions
    overall_trend: str  # 'BULLISH', 'BEARISH', or 'NEUTRAL'
    market_status: str  # Overall market status
    last_update_seconds_ago: int

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        data = asdict(self)
        data["timestamp"] = self.timestamp.isoformat()
        return data


@dataclass
class ResponseDTO:
    """Standard API response wrapper.

    All API endpoints should return data wrapped in this DTO for consistency.
    """

    success: bool
    data: Optional[Dict[str, Any]] = None
    error: Optional[str] = None
    error_type: Optional[str] = None
    timestamp: Optional[datetime] = None
    cached: bool = False
    cache_age_seconds: int = 0

    def __post_init__(self):
        """Set timestamp to now if not provided."""
        if self.timestamp is None:
            self.timestamp = datetime.utcnow()

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization."""
        return {
            "success": self.success,
            "data": self.data,
            "error": self.error,
            "error_type": self.error_type,
            "timestamp": self.timestamp.isoformat() if self.timestamp else None,
            "cached": self.cached,
            "cache_age_seconds": self.cache_age_seconds,
        }


@dataclass
class SchedulerStatusDTO:
    """Status of scheduler and background jobs."""

    enabled: bool
    total_jobs: int
    active_jobs: int
    jobs: List[Dict[str, Any]]  # Job details
    next_execution: Optional[datetime] = None
    last_execution: Optional[datetime] = None
    errors: Optional[List[str]] = None

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        data = asdict(self)
        if self.next_execution:
            data["next_execution"] = self.next_execution.isoformat()
        if self.last_execution:
            data["last_execution"] = self.last_execution.isoformat()
        return data


@dataclass
class HealthCheckDTO:
    """Application health status."""

    healthy: bool
    version: str
    uptime_seconds: int
    scheduler_enabled: bool
    database_connected: bool
    last_data_update: Optional[datetime] = None
    errors: Optional[List[str]] = None

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        data = asdict(self)
        if self.last_data_update:
            data["last_data_update"] = self.last_data_update.isoformat()
        return data
