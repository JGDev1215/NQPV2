"""
Session Range model for NQP application.

This module defines the SessionRange dataclass that represents ICT killzone
session ranges in the database.
"""

from dataclasses import dataclass, field, asdict
from datetime import datetime, date
from typing import Optional, Dict, Any
from enum import Enum
from decimal import Decimal


class SessionName(Enum):
    """Enum for trading session names."""
    ASIA = 'Asia'
    LONDON = 'London'
    NY_AM = 'NY AM'
    NY_PM = 'NY PM'
    FULL_DAY = 'Full Day'


class VolatilityLevel(Enum):
    """Enum for volatility levels."""
    LOW = 'LOW'
    MODERATE = 'MODERATE'
    HIGH = 'HIGH'
    EXTREME = 'EXTREME'


@dataclass
class SessionRange:
    """
    SessionRange dataclass representing ICT killzone session ranges.

    Attributes:
        ticker_id: UUID of the ticker
        date: Date of the session
        session_name: Name of the session (Asia, London, NY AM, NY PM, Full Day)
        session_start: Start time of the session
        session_end: End time of the session
        id: Unique identifier (UUID)
        high: Highest price in the session
        low: Lowest price in the session
        open: Opening price of the session
        close: Closing price of the session
        range_points: Range in points (high - low)
        volatility_percentage: Volatility as percentage
        volatility_level: Volatility level (LOW, MODERATE, HIGH, EXTREME)
        metadata: Additional metadata as JSON
        created_at: When the record was created
    """
    ticker_id: str
    date: date
    session_name: str  # SessionName enum value
    session_start: datetime
    session_end: datetime
    id: Optional[str] = None
    high: Optional[float] = None
    low: Optional[float] = None
    open: Optional[float] = None
    close: Optional[float] = None
    range_points: Optional[float] = None
    volatility_percentage: Optional[float] = None
    volatility_level: Optional[str] = None  # VolatilityLevel enum value
    metadata: Dict[str, Any] = field(default_factory=dict)
    created_at: Optional[datetime] = None

    def __post_init__(self):
        """Validate session range data after initialization."""
        # Validate session_name
        valid_sessions = [s.value for s in SessionName]
        if self.session_name not in valid_sessions:
            raise ValueError(
                f"Invalid session_name: {self.session_name}. "
                f"Must be one of: {valid_sessions}"
            )

        # Validate volatility_level if provided
        if self.volatility_level is not None:
            valid_levels = [v.value for v in VolatilityLevel]
            if self.volatility_level not in valid_levels:
                raise ValueError(
                    f"Invalid volatility_level: {self.volatility_level}. "
                    f"Must be one of: {valid_levels}"
                )

        # Validate session times
        if self.session_end <= self.session_start:
            raise ValueError("Session end must be after session start")

        # Validate OHLC if all are provided
        if all([self.high, self.low, self.open, self.close]):
            if self.high < self.low:
                raise ValueError(f"High ({self.high}) cannot be less than low ({self.low})")
            if self.high < self.open or self.high < self.close:
                raise ValueError(f"High must be >= open and close")
            if self.low > self.open or self.low > self.close:
                raise ValueError(f"Low must be <= open and close")

        # Calculate range_points if not provided
        if self.range_points is None and self.high and self.low:
            self.range_points = self.high - self.low

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'SessionRange':
        """
        Create a SessionRange instance from a dictionary.

        Args:
            data: Dictionary containing session range data

        Returns:
            SessionRange: SessionRange instance
        """
        # Handle date string
        if 'date' in data and isinstance(data['date'], str):
            data['date'] = date.fromisoformat(data['date'])

        # Handle datetime strings
        for dt_field in ['session_start', 'session_end', 'created_at']:
            if dt_field in data and isinstance(data[dt_field], str):
                data[dt_field] = datetime.fromisoformat(data[dt_field].replace('Z', '+00:00'))

        # Convert Decimal to float
        for float_field in ['high', 'low', 'open', 'close', 'range_points', 'volatility_percentage']:
            if float_field in data and isinstance(data[float_field], (str, Decimal)):
                data[float_field] = float(data[float_field]) if data[float_field] else None

        return cls(**data)

    def to_dict(self) -> Dict[str, Any]:
        """
        Convert SessionRange instance to a dictionary.

        Returns:
            Dict[str, Any]: Dictionary representation
        """
        data = asdict(self)

        # Convert date to ISO format string
        if self.date:
            data['date'] = self.date.isoformat()

        # Convert datetime to ISO format strings
        for dt_field in ['session_start', 'session_end', 'created_at']:
            if getattr(self, dt_field):
                data[dt_field] = getattr(self, dt_field).isoformat()

        return data

    def to_db_dict(self) -> Dict[str, Any]:
        """
        Convert SessionRange instance to a dictionary for database insertion.
        Excludes id and created_at fields.

        Returns:
            Dict[str, Any]: Dictionary for database insertion
        """
        data = self.to_dict()

        # Remove auto-generated fields
        data.pop('id', None)
        data.pop('created_at', None)

        return data

    def get_range(self) -> float:
        """
        Get the session range in points.

        Returns:
            float: Range in points (high - low)
        """
        if self.high is None or self.low is None:
            return 0.0
        return self.high - self.low

    def get_midpoint(self) -> Optional[float]:
        """
        Calculate the midpoint of the session range.

        Returns:
            Optional[float]: Midpoint price or None if data unavailable
        """
        if self.high is None or self.low is None:
            return None
        return (self.high + self.low) / 2

    def is_bullish(self) -> bool:
        """Check if session was bullish (close > open)."""
        if self.close is None or self.open is None:
            return False
        return self.close > self.open

    def is_bearish(self) -> bool:
        """Check if session was bearish (close < open)."""
        if self.close is None or self.open is None:
            return False
        return self.close < self.open

    def get_body_percentage(self) -> float:
        """
        Calculate the body size as percentage of range.

        Returns:
            float: Body percentage (0-100)
        """
        if self.open is None or self.close is None or self.range_points == 0:
            return 0.0
        body = abs(self.close - self.open)
        return (body / self.range_points) * 100

    def is_low_volatility(self) -> bool:
        """Check if session has low volatility."""
        return self.volatility_level == VolatilityLevel.LOW.value

    def is_high_volatility(self) -> bool:
        """Check if session has high or extreme volatility."""
        return self.volatility_level in [VolatilityLevel.HIGH.value, VolatilityLevel.EXTREME.value]

    def __repr__(self) -> str:
        """String representation of SessionRange."""
        return (
            f"<SessionRange ticker_id={self.ticker_id} "
            f"date={self.date} session={self.session_name} "
            f"range={self.range_points:.2f if self.range_points else 'N/A'}>"
        )

    def __str__(self) -> str:
        """Human-readable string representation."""
        direction = "Bullish" if self.is_bullish() else "Bearish" if self.is_bearish() else "Neutral"
        volatility = f" [{self.volatility_level}]" if self.volatility_level else ""
        range_str = f"{self.range_points:.2f}" if self.range_points else "N/A"
        return (
            f"{self.date} {self.session_name}: "
            f"O:{self.open:.2f if self.open else 'N/A'} "
            f"H:{self.high:.2f if self.high else 'N/A'} "
            f"L:{self.low:.2f if self.low else 'N/A'} "
            f"C:{self.close:.2f if self.close else 'N/A'} "
            f"Range:{range_str} ({direction}){volatility}"
        )
