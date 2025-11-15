"""
Market Data model for NQP application.

This module defines the MarketData dataclass that represents OHLC price data
in the database.
"""

from dataclasses import dataclass, field, asdict
from datetime import datetime
from typing import Optional, Dict, Any
from enum import Enum
from decimal import Decimal


class MarketDataInterval(Enum):
    """Enum for market data intervals/timeframes."""
    ONE_MINUTE = '1m'
    FIVE_MINUTES = '5m'
    FIFTEEN_MINUTES = '15m'
    THIRTY_MINUTES = '30m'
    ONE_HOUR = '1h'
    FOUR_HOURS = '4h'
    ONE_DAY = '1d'
    ONE_WEEK = '1w'
    ONE_MONTH = '1M'


@dataclass
class MarketData:
    """
    MarketData dataclass representing OHLC price data.

    Attributes:
        ticker_id: UUID of the ticker
        timestamp: Timestamp of the data point
        open: Opening price
        high: Highest price
        low: Lowest price
        close: Closing price
        volume: Trading volume
        interval: Time interval (1m, 1h, 1d, etc.)
        id: Unique identifier (UUID)
        source: Data source (default: 'yfinance')
        fetched_at: Timestamp when data was fetched (tracks freshness)
        metadata: Additional metadata as JSON
        created_at: When the record was created
    """
    ticker_id: str
    timestamp: datetime
    open: float
    high: float
    low: float
    close: float
    interval: str  # MarketDataInterval enum value
    volume: Optional[int] = None
    id: Optional[str] = None
    source: str = 'yfinance'
    fetched_at: Optional[datetime] = None  # When data was fetched from yfinance
    metadata: Dict[str, Any] = field(default_factory=dict)
    created_at: Optional[datetime] = None

    def __post_init__(self):
        """Validate market data after initialization."""
        # Validate interval
        valid_intervals = [i.value for i in MarketDataInterval]
        if self.interval not in valid_intervals:
            raise ValueError(
                f"Invalid interval: {self.interval}. "
                f"Must be one of: {valid_intervals}"
            )

        # Validate prices
        if self.open <= 0:
            raise ValueError(f"Open price must be positive: {self.open}")
        if self.high <= 0:
            raise ValueError(f"High price must be positive: {self.high}")
        if self.low <= 0:
            raise ValueError(f"Low price must be positive: {self.low}")
        if self.close <= 0:
            raise ValueError(f"Close price must be positive: {self.close}")

        # Validate OHLC relationships
        if self.high < self.low:
            raise ValueError(
                f"High ({self.high}) cannot be less than low ({self.low})"
            )
        if self.high < self.open or self.high < self.close:
            raise ValueError(
                f"High ({self.high}) must be >= open ({self.open}) and close ({self.close})"
            )
        if self.low > self.open or self.low > self.close:
            raise ValueError(
                f"Low ({self.low}) must be <= open ({self.open}) and close ({self.close})"
            )

        # Validate volume
        if self.volume is not None and self.volume < 0:
            raise ValueError(f"Volume cannot be negative: {self.volume}")

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'MarketData':
        """
        Create a MarketData instance from a dictionary.

        Args:
            data: Dictionary containing market data

        Returns:
            MarketData: MarketData instance

        Example:
            >>> data = {
            ...     'ticker_id': '123',
            ...     'timestamp': '2025-01-11T10:00:00Z',
            ...     'open': 15200.0,
            ...     'high': 15250.0,
            ...     'low': 15190.0,
            ...     'close': 15240.0,
            ...     'volume': 1000000,
            ...     'interval': '1h'
            ... }
            >>> market_data = MarketData.from_dict(data)
        """
        # Handle datetime strings
        if 'timestamp' in data and isinstance(data['timestamp'], str):
            data['timestamp'] = datetime.fromisoformat(data['timestamp'].replace('Z', '+00:00'))

        if 'created_at' in data and isinstance(data['created_at'], str):
            data['created_at'] = datetime.fromisoformat(data['created_at'].replace('Z', '+00:00'))

        if 'fetched_at' in data and isinstance(data['fetched_at'], str):
            data['fetched_at'] = datetime.fromisoformat(data['fetched_at'].replace('Z', '+00:00'))

        # Convert string numbers to float if needed
        for field in ['open', 'high', 'low', 'close']:
            if field in data and isinstance(data[field], (str, Decimal)):
                data[field] = float(data[field])

        if 'volume' in data and isinstance(data['volume'], str):
            data['volume'] = int(data['volume']) if data['volume'] else None

        return cls(**data)

    def to_dict(self) -> Dict[str, Any]:
        """
        Convert MarketData instance to a dictionary.

        Returns:
            Dict[str, Any]: Dictionary representation
        """
        data = asdict(self)

        # Convert datetime to ISO format strings
        if self.timestamp:
            data['timestamp'] = self.timestamp.isoformat()

        if self.fetched_at:
            data['fetched_at'] = self.fetched_at.isoformat()

        if self.created_at:
            data['created_at'] = self.created_at.isoformat()

        return data

    def to_db_dict(self) -> Dict[str, Any]:
        """
        Convert MarketData instance to a dictionary for database insertion.
        Excludes id, created_at, and fetched_at fields (not in Supabase schema).

        Returns:
            Dict[str, Any]: Dictionary for database insertion
        """
        data = self.to_dict()

        # Remove auto-generated fields and fields not in schema
        data.pop('id', None)
        data.pop('created_at', None)
        data.pop('fetched_at', None)  # Not in Supabase schema

        return data

    def get_range(self) -> float:
        """
        Calculate the price range (high - low).

        Returns:
            float: Price range
        """
        return self.high - self.low

    def get_range_percentage(self) -> float:
        """
        Calculate the range as a percentage of the open price.

        Returns:
            float: Range percentage
        """
        if self.open == 0:
            return 0.0
        return (self.get_range() / self.open) * 100

    def is_bullish(self) -> bool:
        """
        Check if the candle is bullish (close > open).

        Returns:
            bool: True if bullish, False otherwise
        """
        return self.close > self.open

    def is_bearish(self) -> bool:
        """
        Check if the candle is bearish (close < open).

        Returns:
            bool: True if bearish, False otherwise
        """
        return self.close < self.open

    def is_doji(self, threshold: float = 0.001) -> bool:
        """
        Check if the candle is a doji (open ≈ close).

        Args:
            threshold: Maximum difference ratio to consider as doji (default: 0.1%)

        Returns:
            bool: True if doji, False otherwise
        """
        if self.open == 0:
            return False
        return abs(self.close - self.open) / self.open <= threshold

    def get_body_size(self) -> float:
        """
        Calculate the size of the candle body (|close - open|).

        Returns:
            float: Body size
        """
        return abs(self.close - self.open)

    def get_upper_wick(self) -> float:
        """
        Calculate the size of the upper wick.

        Returns:
            float: Upper wick size
        """
        return self.high - max(self.open, self.close)

    def get_lower_wick(self) -> float:
        """
        Calculate the size of the lower wick.

        Returns:
            float: Lower wick size
        """
        return min(self.open, self.close) - self.low

    def __repr__(self) -> str:
        """String representation of MarketData."""
        return (
            f"<MarketData ticker_id={self.ticker_id} "
            f"timestamp={self.timestamp} interval={self.interval} "
            f"O={self.open:.2f} H={self.high:.2f} L={self.low:.2f} C={self.close:.2f}>"
        )

    def __str__(self) -> str:
        """Human-readable string representation."""
        direction = "Bullish" if self.is_bullish() else "Bearish" if self.is_bearish() else "Doji"
        return (
            f"{self.timestamp.strftime('%Y-%m-%d %H:%M')} [{self.interval}] "
            f"O:{self.open:.2f} H:{self.high:.2f} L:{self.low:.2f} C:{self.close:.2f} "
            f"V:{self.volume or 0} ({direction})"
        )
