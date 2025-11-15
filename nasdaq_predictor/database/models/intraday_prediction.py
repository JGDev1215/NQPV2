"""
Intraday Prediction model for NQP application.

This module defines the IntradayPrediction dataclass that represents hourly
intraday predictions (9am, 10am, etc.) in the database.
"""

from dataclasses import dataclass, field, asdict
from datetime import datetime
from typing import Optional, Dict, Any
from enum import Enum
from decimal import Decimal


@dataclass
class IntradayPrediction:
    """
    IntradayPrediction dataclass representing hourly intraday predictions.

    Attributes:
        ticker_id: UUID of the ticker
        target_hour: Target hour for prediction (0-23)
        target_timestamp: Target timestamp for the prediction
        prediction_made_at: When the prediction was made
        prediction: Prediction result (BULLISH, BEARISH, NEUTRAL)
        base_confidence: Base confidence level
        decay_factor: Time-decay factor applied
        final_confidence: Final confidence after decay
        reference_price: Reference price used for prediction
        id: Unique identifier (UUID)
        prediction_id: Related prediction ID (if any)
        target_close_price: Actual close price at target hour
        actual_result: Actual outcome (CORRECT, WRONG, PENDING)
        verified_at: When the prediction was verified
        metadata: Additional metadata as JSON
        created_at: When the record was created
    """
    ticker_id: str
    target_hour: int
    target_timestamp: datetime
    prediction_made_at: datetime
    prediction: str
    base_confidence: float
    decay_factor: float
    final_confidence: float
    reference_price: float
    id: Optional[str] = None
    prediction_id: Optional[str] = None
    target_close_price: Optional[float] = None
    actual_result: Optional[str] = None
    verified_at: Optional[datetime] = None
    metadata: Dict[str, Any] = field(default_factory=dict)
    created_at: Optional[datetime] = None

    def __post_init__(self):
        """Validate intraday prediction data after initialization."""
        # Validate target_hour
        if not 0 <= self.target_hour <= 23:
            raise ValueError(f"Target hour must be between 0 and 23: {self.target_hour}")

        # Validate prediction
        valid_predictions = ['BULLISH', 'BEARISH', 'NEUTRAL']
        if self.prediction not in valid_predictions:
            raise ValueError(
                f"Invalid prediction: {self.prediction}. "
                f"Must be one of: {valid_predictions}"
            )

        # Validate confidence values
        if not 0 <= self.base_confidence <= 100:
            raise ValueError(f"Base confidence must be between 0 and 100: {self.base_confidence}")
        if not 0 <= self.final_confidence <= 100:
            raise ValueError(f"Final confidence must be between 0 and 100: {self.final_confidence}")
        if not 0 <= self.decay_factor <= 1:
            raise ValueError(f"Decay factor must be between 0 and 1: {self.decay_factor}")

        # Validate reference price
        if self.reference_price <= 0:
            raise ValueError(f"Reference price must be positive: {self.reference_price}")

        # Validate actual_result if provided
        if self.actual_result is not None:
            valid_results = ['CORRECT', 'WRONG', 'PENDING']
            if self.actual_result not in valid_results:
                raise ValueError(
                    f"Invalid actual_result: {self.actual_result}. "
                    f"Must be one of: {valid_results}"
                )

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'IntradayPrediction':
        """
        Create an IntradayPrediction instance from a dictionary.

        Args:
            data: Dictionary containing intraday prediction data

        Returns:
            IntradayPrediction: IntradayPrediction instance
        """
        # Handle datetime strings
        for dt_field in ['target_timestamp', 'prediction_made_at', 'verified_at', 'created_at']:
            if dt_field in data and isinstance(data[dt_field], str):
                data[dt_field] = datetime.fromisoformat(data[dt_field].replace('Z', '+00:00'))

        # Convert Decimal to float
        for float_field in ['base_confidence', 'decay_factor', 'final_confidence',
                           'reference_price', 'target_close_price']:
            if float_field in data and isinstance(data[float_field], (str, Decimal)):
                data[float_field] = float(data[float_field]) if data[float_field] else None

        # Convert string to int
        if 'target_hour' in data and isinstance(data['target_hour'], str):
            data['target_hour'] = int(data['target_hour'])

        return cls(**data)

    def to_dict(self) -> Dict[str, Any]:
        """
        Convert IntradayPrediction instance to a dictionary.

        Returns:
            Dict[str, Any]: Dictionary representation
        """
        data = asdict(self)

        # Convert datetime to ISO format strings
        for dt_field in ['target_timestamp', 'prediction_made_at', 'verified_at', 'created_at']:
            if getattr(self, dt_field):
                data[dt_field] = getattr(self, dt_field).isoformat()

        return data

    def to_db_dict(self) -> Dict[str, Any]:
        """
        Convert IntradayPrediction instance to a dictionary for database insertion.
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
        """Check if prediction is bullish."""
        return self.prediction == 'BULLISH'

    def is_bearish(self) -> bool:
        """Check if prediction is bearish."""
        return self.prediction == 'BEARISH'

    def is_neutral(self) -> bool:
        """Check if prediction is neutral."""
        return self.prediction == 'NEUTRAL'

    def is_verified(self) -> bool:
        """Check if prediction has been verified."""
        return self.actual_result is not None and self.actual_result != 'PENDING'

    def is_correct(self) -> bool:
        """Check if prediction was correct."""
        return self.actual_result == 'CORRECT'

    def is_wrong(self) -> bool:
        """Check if prediction was wrong."""
        return self.actual_result == 'WRONG'

    def is_pending(self) -> bool:
        """Check if prediction is pending verification."""
        return self.actual_result is None or self.actual_result == 'PENDING'

    def get_time_until_target(self, current_time: Optional[datetime] = None) -> float:
        """
        Calculate time until target in minutes.

        Args:
            current_time: Current time (defaults to now)

        Returns:
            float: Minutes until target (negative if past)
        """
        if current_time is None:
            current_time = datetime.now(self.target_timestamp.tzinfo)

        delta = self.target_timestamp - current_time
        return delta.total_seconds() / 60

    def get_confidence_level(self) -> str:
        """
        Get a human-readable confidence level.

        Returns:
            str: Confidence level (Low, Moderate, High, Very High)
        """
        if self.final_confidence < 25:
            return "Low"
        elif self.final_confidence < 50:
            return "Moderate"
        elif self.final_confidence < 75:
            return "High"
        else:
            return "Very High"

    def __repr__(self) -> str:
        """String representation of IntradayPrediction."""
        return (
            f"<IntradayPrediction ticker_id={self.ticker_id} "
            f"target_hour={self.target_hour} prediction={self.prediction} "
            f"final_confidence={self.final_confidence:.2f}%>"
        )

    def __str__(self) -> str:
        """Human-readable string representation."""
        status = f" - {self.actual_result}" if self.actual_result else " - Pending"
        return (
            f"{self.target_timestamp.strftime('%Y-%m-%d %H:00')} "
            f"{self.prediction} (Confidence: {self.final_confidence:.2f}%, "
            f"Decay: {self.decay_factor:.4f}){status}"
        )
