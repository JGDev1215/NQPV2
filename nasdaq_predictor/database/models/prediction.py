"""
Prediction model for NQP application.

This module defines the Prediction dataclass that represents prediction results
in the database.
"""

from dataclasses import dataclass, field, asdict
from datetime import datetime
from typing import Optional, Dict, Any
from enum import Enum
from decimal import Decimal


class PredictionResult(Enum):
    """Enum for prediction results."""
    BULLISH = 'BULLISH'
    BEARISH = 'BEARISH'
    NEUTRAL = 'NEUTRAL'


class PredictionAccuracy(Enum):
    """Enum for prediction accuracy status."""
    CORRECT = 'CORRECT'
    WRONG = 'WRONG'
    PENDING = 'PENDING'


@dataclass
class Prediction:
    """
    Prediction dataclass representing a market prediction.

    Attributes:
        ticker_id: UUID of the ticker
        timestamp: When the prediction was made
        prediction: Prediction result (BULLISH, BEARISH, NEUTRAL)
        confidence: Confidence level (0-100)
        weighted_score: Weighted score (0-1)
        bullish_count: Number of bullish signals
        bearish_count: Number of bearish signals
        total_signals: Total number of signals
        id: Unique identifier (UUID)
        actual_result: Actual outcome (CORRECT, WRONG, PENDING, NULL)
        actual_price_change: Actual price change
        verification_timestamp: When the prediction was verified
        market_status: Market status at prediction time
        volatility_level: Volatility level at prediction time
        session: Trading session
        metadata: Additional metadata as JSON
        created_at: When the record was created
        updated_at: When the record was last updated
    """
    ticker_id: str
    timestamp: datetime
    prediction: str  # PredictionResult enum value
    confidence: float
    weighted_score: float
    bullish_count: int
    bearish_count: int
    total_signals: int
    id: Optional[str] = None
    actual_result: Optional[str] = None  # PredictionAccuracy enum value
    actual_price_change: Optional[float] = None
    verification_timestamp: Optional[datetime] = None
    market_status: Optional[str] = None
    volatility_level: Optional[str] = None
    session: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

    def __post_init__(self):
        """Validate prediction data after initialization."""
        # Validate prediction
        valid_predictions = [p.value for p in PredictionResult]
        if self.prediction not in valid_predictions:
            raise ValueError(
                f"Invalid prediction: {self.prediction}. "
                f"Must be one of: {valid_predictions}"
            )

        # Validate confidence
        if not 0 <= self.confidence <= 100:
            raise ValueError(f"Confidence must be between 0 and 100: {self.confidence}")

        # Validate weighted score
        if not 0 <= self.weighted_score <= 1:
            raise ValueError(f"Weighted score must be between 0 and 1: {self.weighted_score}")

        # Validate signal counts
        if self.bullish_count < 0:
            raise ValueError(f"Bullish count cannot be negative: {self.bullish_count}")
        if self.bearish_count < 0:
            raise ValueError(f"Bearish count cannot be negative: {self.bearish_count}")
        if self.total_signals <= 0:
            raise ValueError(f"Total signals must be positive: {self.total_signals}")

        # Validate actual_result if provided
        if self.actual_result is not None:
            valid_results = [a.value for a in PredictionAccuracy]
            if self.actual_result not in valid_results:
                raise ValueError(
                    f"Invalid actual_result: {self.actual_result}. "
                    f"Must be one of: {valid_results}"
                )

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'Prediction':
        """
        Create a Prediction instance from a dictionary.

        Args:
            data: Dictionary containing prediction data

        Returns:
            Prediction: Prediction instance
        """
        # Handle datetime strings
        for dt_field in ['timestamp', 'verification_timestamp', 'created_at', 'updated_at']:
            if dt_field in data and isinstance(data[dt_field], str):
                data[dt_field] = datetime.fromisoformat(data[dt_field].replace('Z', '+00:00'))

        # Convert Decimal to float
        for float_field in ['confidence', 'weighted_score', 'actual_price_change']:
            if float_field in data and isinstance(data[float_field], (str, Decimal)):
                data[float_field] = float(data[float_field]) if data[float_field] else None

        # Convert string numbers to int
        for int_field in ['bullish_count', 'bearish_count', 'total_signals']:
            if int_field in data and isinstance(data[int_field], str):
                data[int_field] = int(data[int_field])

        return cls(**data)

    def to_dict(self) -> Dict[str, Any]:
        """
        Convert Prediction instance to a dictionary.

        Returns:
            Dict[str, Any]: Dictionary representation
        """
        data = asdict(self)

        # Convert datetime to ISO format strings
        for dt_field in ['timestamp', 'verification_timestamp', 'created_at', 'updated_at']:
            if getattr(self, dt_field):
                data[dt_field] = getattr(self, dt_field).isoformat()

        return data

    def to_db_dict(self) -> Dict[str, Any]:
        """
        Convert Prediction instance to a dictionary for database insertion.
        Excludes id, created_at, and updated_at fields.

        Returns:
            Dict[str, Any]: Dictionary for database insertion
        """
        data = self.to_dict()

        # Remove auto-generated fields
        data.pop('id', None)
        data.pop('created_at', None)
        data.pop('updated_at', None)

        return data

    def is_bullish(self) -> bool:
        """Check if prediction is bullish."""
        return self.prediction == PredictionResult.BULLISH.value

    def is_bearish(self) -> bool:
        """Check if prediction is bearish."""
        return self.prediction == PredictionResult.BEARISH.value

    def is_neutral(self) -> bool:
        """Check if prediction is neutral."""
        return self.prediction == PredictionResult.NEUTRAL.value

    def is_verified(self) -> bool:
        """Check if prediction has been verified."""
        return self.actual_result is not None and self.actual_result != PredictionAccuracy.PENDING.value

    def is_correct(self) -> bool:
        """Check if prediction was correct."""
        return self.actual_result == PredictionAccuracy.CORRECT.value

    def is_wrong(self) -> bool:
        """Check if prediction was wrong."""
        return self.actual_result == PredictionAccuracy.WRONG.value

    def is_pending(self) -> bool:
        """Check if prediction is pending verification."""
        return self.actual_result is None or self.actual_result == PredictionAccuracy.PENDING.value

    def get_bullish_percentage(self) -> float:
        """
        Calculate the percentage of bullish signals.

        Returns:
            float: Bullish percentage (0-100)
        """
        if self.total_signals == 0:
            return 0.0
        return (self.bullish_count / self.total_signals) * 100

    def get_bearish_percentage(self) -> float:
        """
        Calculate the percentage of bearish signals.

        Returns:
            float: Bearish percentage (0-100)
        """
        if self.total_signals == 0:
            return 0.0
        return (self.bearish_count / self.total_signals) * 100

    def get_confidence_level(self) -> str:
        """
        Get a human-readable confidence level.

        Returns:
            str: Confidence level (Low, Moderate, High, Very High)
        """
        if self.confidence < 25:
            return "Low"
        elif self.confidence < 50:
            return "Moderate"
        elif self.confidence < 75:
            return "High"
        else:
            return "Very High"

    def __repr__(self) -> str:
        """String representation of Prediction."""
        return (
            f"<Prediction ticker_id={self.ticker_id} "
            f"timestamp={self.timestamp} prediction={self.prediction} "
            f"confidence={self.confidence:.2f}% actual_result={self.actual_result}>"
        )

    def __str__(self) -> str:
        """Human-readable string representation."""
        status = f" - {self.actual_result}" if self.actual_result else " - Pending"
        return (
            f"{self.timestamp.strftime('%Y-%m-%d %H:%M')} "
            f"{self.prediction} (Confidence: {self.confidence:.2f}%, "
            f"Score: {self.weighted_score:.4f}, "
            f"Bullish: {self.bullish_count}/{self.total_signals}){status}"
        )
