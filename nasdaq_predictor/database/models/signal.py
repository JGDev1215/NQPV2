"""
Signal model for NQP application.

This module defines the Signal dataclass that represents individual signal
breakdowns in the database.
"""

from dataclasses import dataclass, field, asdict
from datetime import datetime
from typing import Optional, Dict, Any
from enum import Enum
from decimal import Decimal


class SignalStatus(Enum):
    """Enum for signal status."""
    BULLISH = 'BULLISH'
    BEARISH = 'BEARISH'
    NA = 'N/A'


@dataclass
class Signal:
    """
    Signal dataclass representing an individual signal from a reference level.

    Attributes:
        prediction_id: UUID of the prediction this signal belongs to
        reference_level_name: Name of the reference level (e.g., 'daily_open')
        reference_level_value: Price value of the reference level
        current_price: Current market price at signal generation
        signal: Binary signal (0=BEARISH, 1=BULLISH)
        weight: Weight of this signal in the overall calculation
        weighted_contribution: Signal * weight
        distance: Distance from reference level (current_price - reference_level_value)
        id: Unique identifier (UUID)
        distance_percentage: Distance as percentage of reference level
        status: Signal status (BULLISH, BEARISH, N/A)
        metadata: Additional metadata as JSON
        created_at: When the record was created
    """
    prediction_id: str
    reference_level_name: str
    reference_level_value: float
    current_price: float
    signal: int
    weight: float
    weighted_contribution: float
    distance: float
    id: Optional[str] = None
    distance_percentage: Optional[float] = None
    status: str = SignalStatus.NA.value
    metadata: Dict[str, Any] = field(default_factory=dict)
    created_at: Optional[datetime] = None

    def __post_init__(self):
        """Validate signal data after initialization."""
        # Validate signal
        if self.signal not in [0, 1]:
            raise ValueError(f"Signal must be 0 (BEARISH) or 1 (BULLISH): {self.signal}")

        # Validate weight
        if not 0 <= self.weight <= 1:
            raise ValueError(f"Weight must be between 0 and 1: {self.weight}")

        # Validate prices
        if self.reference_level_value <= 0:
            raise ValueError(f"Reference level value must be positive: {self.reference_level_value}")
        if self.current_price <= 0:
            raise ValueError(f"Current price must be positive: {self.current_price}")

        # Validate status
        valid_statuses = [s.value for s in SignalStatus]
        if self.status not in valid_statuses:
            raise ValueError(
                f"Invalid status: {self.status}. "
                f"Must be one of: {valid_statuses}"
            )

        # Calculate distance_percentage if not provided
        if self.distance_percentage is None and self.reference_level_value > 0:
            self.distance_percentage = (self.distance / self.reference_level_value) * 100

        # Auto-set status based on signal if not explicitly set
        if self.status == SignalStatus.NA.value:
            self.status = SignalStatus.BULLISH.value if self.signal == 1 else SignalStatus.BEARISH.value

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'Signal':
        """
        Create a Signal instance from a dictionary.

        Args:
            data: Dictionary containing signal data

        Returns:
            Signal: Signal instance
        """
        # Handle datetime strings
        if 'created_at' in data and isinstance(data['created_at'], str):
            data['created_at'] = datetime.fromisoformat(data['created_at'].replace('Z', '+00:00'))

        # Convert Decimal to float
        for float_field in ['reference_level_value', 'current_price', 'weight',
                           'weighted_contribution', 'distance', 'distance_percentage']:
            if float_field in data and isinstance(data[float_field], (str, Decimal)):
                data[float_field] = float(data[float_field]) if data[float_field] else None

        # Convert string numbers to int
        if 'signal' in data and isinstance(data['signal'], str):
            data['signal'] = int(data['signal'])

        return cls(**data)

    def to_dict(self) -> Dict[str, Any]:
        """
        Convert Signal instance to a dictionary.

        Returns:
            Dict[str, Any]: Dictionary representation
        """
        data = asdict(self)

        # Convert datetime to ISO format string
        if self.created_at:
            data['created_at'] = self.created_at.isoformat()

        return data

    def to_db_dict(self) -> Dict[str, Any]:
        """
        Convert Signal instance to a dictionary for database insertion.
        Excludes id and created_at fields.

        Returns:
            Dict[str, Any]: Dictionary for database insertion
        """
        data = self.to_dict()

        # Remove auto-generated fields
        data.pop('id', None)
        data.pop('created_at', None)

        return data

    def is_bullish(self) -> bool:
        """Check if signal is bullish."""
        return self.signal == 1

    def is_bearish(self) -> bool:
        """Check if signal is bearish."""
        return self.signal == 0

    def is_above_reference(self) -> bool:
        """Check if current price is above reference level."""
        return self.current_price > self.reference_level_value

    def is_below_reference(self) -> bool:
        """Check if current price is below reference level."""
        return self.current_price < self.reference_level_value

    def get_distance_abs(self) -> float:
        """
        Get absolute distance from reference level.

        Returns:
            float: Absolute distance
        """
        return abs(self.distance)

    def get_contribution_percentage(self, total_weight: float = 1.0) -> float:
        """
        Get this signal's contribution as a percentage of total weight.

        Args:
            total_weight: Total weight of all signals (default: 1.0)

        Returns:
            float: Contribution percentage
        """
        if total_weight == 0:
            return 0.0
        return (self.weight / total_weight) * 100

    def __repr__(self) -> str:
        """String representation of Signal."""
        return (
            f"<Signal prediction_id={self.prediction_id} "
            f"ref_level={self.reference_level_name} "
            f"signal={self.signal} status={self.status} "
            f"weight={self.weight:.4f}>"
        )

    def __str__(self) -> str:
        """Human-readable string representation."""
        direction = "↑ BULLISH" if self.is_bullish() else "↓ BEARISH"
        return (
            f"{self.reference_level_name}: {direction} "
            f"(Ref: {self.reference_level_value:.2f}, "
            f"Current: {self.current_price:.2f}, "
            f"Distance: {self.distance:+.2f} [{self.distance_percentage:+.2f}%], "
            f"Weight: {self.weight:.4f}, "
            f"Contribution: {self.weighted_contribution:.4f})"
        )
