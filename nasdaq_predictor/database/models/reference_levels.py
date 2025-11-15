"""
Reference Levels model for NQP application.

This module defines the ReferenceLevels dataclass that represents calculated
reference price levels in the database.
"""

from dataclasses import dataclass, field, asdict
from datetime import datetime
from typing import Optional, Dict, Any
from decimal import Decimal


@dataclass
class ReferenceLevels:
    """
    ReferenceLevels dataclass representing calculated reference price levels.

    Attributes:
        ticker_id: UUID of the ticker
        timestamp: When the reference levels were calculated
        daily_open: Daily open price (midnight ET)
        hourly_open: Current hour open price
        four_hourly_open: Current 4-hour candle open price
        thirty_min_open: Current 30-minute candle open price
        prev_day_high: Previous day high
        prev_day_low: Previous day low
        prev_week_open: Previous week open (Monday 00:00 UTC)
        weekly_open: Current week open
        monthly_open: Current month open
        seven_am_open: 7:00am NY open
        eight_thirty_am_open: 8:30am NY open
        current_price: Current market price
        ny_time: New York time
        london_time: London time
        range_0700_0715_high: High of 7:00-7:15 AM NY range
        range_0700_0715_low: Low of 7:00-7:15 AM NY range
        range_0830_0845_high: High of 8:30-8:45 AM NY range
        range_0830_0845_low: Low of 8:30-8:45 AM NY range
        asian_kill_zone_high: High of Asian Kill Zone (1:00-5:00 AM UTC)
        asian_kill_zone_low: Low of Asian Kill Zone (1:00-5:00 AM UTC)
        london_kill_zone_high: High of London Kill Zone (7:00-10:00 AM UTC)
        london_kill_zone_low: Low of London Kill Zone (7:00-10:00 AM UTC)
        ny_am_kill_zone_high: High of NY AM Kill Zone (8:30-11:00 AM ET)
        ny_am_kill_zone_low: Low of NY AM Kill Zone (8:30-11:00 AM ET)
        ny_pm_kill_zone_high: High of NY PM Kill Zone (1:30-4:00 PM ET)
        ny_pm_kill_zone_low: Low of NY PM Kill Zone (1:30-4:00 PM ET)
        id: Unique identifier (UUID)
        metadata: Additional metadata as JSON
        created_at: When the record was created
    """
    ticker_id: str
    timestamp: datetime
    daily_open: Optional[float] = None
    hourly_open: Optional[float] = None
    four_hourly_open: Optional[float] = None
    thirty_min_open: Optional[float] = None
    prev_day_high: Optional[float] = None
    prev_day_low: Optional[float] = None
    prev_week_open: Optional[float] = None
    weekly_open: Optional[float] = None
    monthly_open: Optional[float] = None
    seven_am_open: Optional[float] = None
    eight_thirty_am_open: Optional[float] = None
    current_price: Optional[float] = None
    ny_time: Optional[datetime] = None
    london_time: Optional[datetime] = None

    # Range-based reference levels (kill zones and time ranges)
    range_0700_0715_high: Optional[float] = None
    range_0700_0715_low: Optional[float] = None
    range_0830_0845_high: Optional[float] = None
    range_0830_0845_low: Optional[float] = None
    asian_kill_zone_high: Optional[float] = None
    asian_kill_zone_low: Optional[float] = None
    london_kill_zone_high: Optional[float] = None
    london_kill_zone_low: Optional[float] = None
    ny_am_kill_zone_high: Optional[float] = None
    ny_am_kill_zone_low: Optional[float] = None
    ny_pm_kill_zone_high: Optional[float] = None
    ny_pm_kill_zone_low: Optional[float] = None

    id: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)
    created_at: Optional[datetime] = None

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'ReferenceLevels':
        """
        Create a ReferenceLevels instance from a dictionary.

        Args:
            data: Dictionary containing reference levels data

        Returns:
            ReferenceLevels: ReferenceLevels instance
        """
        # Handle datetime strings
        for dt_field in ['timestamp', 'ny_time', 'london_time', 'created_at']:
            if dt_field in data and isinstance(data[dt_field], str):
                data[dt_field] = datetime.fromisoformat(data[dt_field].replace('Z', '+00:00'))

        # Convert Decimal to float for all price fields
        price_fields = [
            'daily_open', 'hourly_open', 'four_hourly_open', 'thirty_min_open',
            'prev_day_high', 'prev_day_low', 'prev_week_open', 'weekly_open',
            'monthly_open', 'seven_am_open', 'eight_thirty_am_open', 'current_price',
            # Range-based fields
            'range_0700_0715_high', 'range_0700_0715_low',
            'range_0830_0845_high', 'range_0830_0845_low',
            'asian_kill_zone_high', 'asian_kill_zone_low',
            'london_kill_zone_high', 'london_kill_zone_low',
            'ny_am_kill_zone_high', 'ny_am_kill_zone_low',
            'ny_pm_kill_zone_high', 'ny_pm_kill_zone_low'
        ]
        for field in price_fields:
            if field in data and isinstance(data[field], (str, Decimal)):
                data[field] = float(data[field]) if data[field] else None

        return cls(**data)

    def to_dict(self) -> Dict[str, Any]:
        """
        Convert ReferenceLevels instance to a dictionary.

        Returns:
            Dict[str, Any]: Dictionary representation
        """
        data = asdict(self)

        # Convert datetime to ISO format strings
        for dt_field in ['timestamp', 'ny_time', 'london_time', 'created_at']:
            if getattr(self, dt_field):
                data[dt_field] = getattr(self, dt_field).isoformat()

        return data

    def to_db_dict(self) -> Dict[str, Any]:
        """
        Convert ReferenceLevels instance to a dictionary for database insertion.
        Excludes id and created_at fields.

        Returns:
            Dict[str, Any]: Dictionary for database insertion
        """
        data = self.to_dict()

        # Remove auto-generated fields
        data.pop('id', None)
        data.pop('created_at', None)

        return data

    def get_all_levels(self) -> Dict[str, Optional[float]]:
        """
        Get all reference levels as a dictionary.

        Returns:
            Dict[str, Optional[float]]: Dictionary of reference levels
        """
        return {
            'daily_open': self.daily_open,
            'hourly_open': self.hourly_open,
            '4_hourly_open': self.four_hourly_open,
            '30_min_open': self.thirty_min_open,
            'prev_day_high': self.prev_day_high,
            'prev_day_low': self.prev_day_low,
            'prev_week_open': self.prev_week_open,
            'weekly_open': self.weekly_open,
            'monthly_open': self.monthly_open,
            '7am_open': self.seven_am_open,
            '830am_open': self.eight_thirty_am_open,
        }

    def get_valid_levels(self) -> Dict[str, float]:
        """
        Get only the reference levels that have valid values (not None).

        Returns:
            Dict[str, float]: Dictionary of valid reference levels
        """
        return {k: v for k, v in self.get_all_levels().items() if v is not None}

    def count_valid_levels(self) -> int:
        """
        Count the number of valid reference levels.

        Returns:
            int: Number of valid levels
        """
        return len(self.get_valid_levels())

    def __repr__(self) -> str:
        """String representation of ReferenceLevels."""
        valid_count = self.count_valid_levels()
        return (
            f"<ReferenceLevels ticker_id={self.ticker_id} "
            f"timestamp={self.timestamp} valid_levels={valid_count}/11>"
        )

    def __str__(self) -> str:
        """Human-readable string representation."""
        levels = self.get_valid_levels()
        levels_str = ", ".join([f"{k}={v:.2f}" for k, v in levels.items()])
        return f"{self.timestamp.strftime('%Y-%m-%d %H:%M')}: {levels_str}"
