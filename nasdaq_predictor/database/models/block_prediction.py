"""
Block Prediction model for NQP application.

This module defines the BlockPrediction dataclass that represents 7-block
hourly predictions in the database.
"""

from dataclasses import dataclass, field, asdict
from datetime import datetime
from typing import Optional, Dict, Any, List
from enum import Enum
from decimal import Decimal


@dataclass
class BlockPrediction:
    """
    BlockPrediction dataclass representing 7-block hourly predictions.

    Each hour is divided into 7 blocks (~8.57 minutes each).
    Prediction is made at the 5/7 point (~42.86 minutes into the hour).
    Verification happens at hour end (after block 7 completes).

    Attributes:
        ticker_id: UUID of the ticker
        hour_start_timestamp: Start of the hour being analyzed (UTC)
        prediction_timestamp: When prediction was made (at 5/7 point)
        prediction: Prediction result (UP, DOWN, NEUTRAL)
        confidence: Confidence level (0-100%)
        prediction_strength: Strength classification (weak, moderate, strong)
        reference_price: Opening price of the hour

        -- Early Bias Analysis (Blocks 1-2)
        early_bias: Direction from blocks 1-2 (UP, DOWN, NEUTRAL)
        early_bias_strength: Magnitude of early bias (std devs)

        -- Sustained Counter Analysis (Blocks 3-5)
        has_sustained_counter: Whether reversal pattern detected
        counter_direction: Direction if counter exists (UP, DOWN, None)

        -- Block Data
        block_data: JSONB with detailed block OHLC for blocks 1-5

        -- Reference Levels
        reference_levels: JSONB snapshot of reference levels at 5/7 point
        deviation_at_5_7: Price deviation at prediction point (std devs)
        volatility: Calculated volatility for this hour

        -- Verification (filled at hour end)
        blocks_6_7_close: Closing price of block 7
        actual_result: Outcome (CORRECT, WRONG, PENDING)
        verified_at: When verification occurred

        -- Metadata
        id: Unique identifier (UUID)
        metadata: Additional metadata as JSON
        created_at: When the record was created
    """
    ticker_id: str
    hour_start_timestamp: datetime
    prediction_timestamp: datetime
    prediction: str  # UP, DOWN, NEUTRAL
    confidence: float  # 0-100
    prediction_strength: str  # weak, moderate, strong
    reference_price: float  # Hour opening price
    early_bias: str  # UP, DOWN, NEUTRAL
    early_bias_strength: float  # Standard deviations
    has_sustained_counter: bool
    counter_direction: Optional[str] = None  # UP, DOWN, or None

    # Block and analysis data
    block_data: Dict[str, Any] = field(default_factory=dict)  # Blocks 1-7 OHLC
    reference_levels: Dict[str, Any] = field(default_factory=dict)  # Reference snapshot
    deviation_at_5_7: float = 0.0  # Deviation from reference (std devs)
    volatility: float = 0.0  # Calculated volatility for hour

    # Verification fields
    blocks_6_7_close: Optional[float] = None  # Close of block 7
    actual_result: Optional[str] = None  # CORRECT, WRONG, PENDING
    verified_at: Optional[datetime] = None

    # Auto-generated fields
    id: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)
    created_at: Optional[datetime] = None

    def __post_init__(self):
        """Validate block prediction data after initialization."""
        # Validate prediction
        valid_predictions = ['UP', 'DOWN', 'NEUTRAL']
        if self.prediction not in valid_predictions:
            raise ValueError(
                f"Invalid prediction: {self.prediction}. "
                f"Must be one of: {valid_predictions}"
            )

        # Validate early bias
        if self.early_bias not in valid_predictions:
            raise ValueError(
                f"Invalid early_bias: {self.early_bias}. "
                f"Must be one of: {valid_predictions}"
            )

        # Validate counter direction if present
        if self.counter_direction is not None:
            if self.counter_direction not in valid_predictions:
                raise ValueError(
                    f"Invalid counter_direction: {self.counter_direction}. "
                    f"Must be one of: {valid_predictions}"
                )

        # Validate strength
        valid_strengths = ['weak', 'moderate', 'strong']
        if self.prediction_strength not in valid_strengths:
            raise ValueError(
                f"Invalid prediction_strength: {self.prediction_strength}. "
                f"Must be one of: {valid_strengths}"
            )

        # Validate confidence values
        if not 0 <= self.confidence <= 100:
            raise ValueError(f"Confidence must be between 0 and 100: {self.confidence}")

        # Validate reference price
        if self.reference_price <= 0:
            raise ValueError(f"Reference price must be positive: {self.reference_price}")

        # Validate counter consistency
        if self.has_sustained_counter and self.counter_direction is None:
            raise ValueError(
                "If has_sustained_counter is True, counter_direction must be set"
            )

        # Validate actual_result if provided
        if self.actual_result is not None:
            valid_results = ['CORRECT', 'WRONG', 'PENDING']
            if self.actual_result not in valid_results:
                raise ValueError(
                    f"Invalid actual_result: {self.actual_result}. "
                    f"Must be one of: {valid_results}"
                )

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'BlockPrediction':
        """
        Create a BlockPrediction instance from a dictionary.

        Args:
            data: Dictionary containing block prediction data

        Returns:
            BlockPrediction: BlockPrediction instance
        """
        # Handle datetime strings
        for dt_field in ['hour_start_timestamp', 'prediction_timestamp', 'verified_at', 'created_at']:
            if dt_field in data and isinstance(data[dt_field], str):
                data[dt_field] = datetime.fromisoformat(data[dt_field].replace('Z', '+00:00'))

        # Convert Decimal to float
        for float_field in ['confidence', 'early_bias_strength', 'deviation_at_5_7',
                           'volatility', 'reference_price', 'blocks_6_7_close']:
            if float_field in data and isinstance(data[float_field], (str, Decimal)):
                data[float_field] = float(data[float_field]) if data[float_field] else None

        return cls(**data)

    def to_dict(self) -> Dict[str, Any]:
        """
        Convert BlockPrediction instance to a dictionary.

        Returns:
            Dict[str, Any]: Dictionary representation
        """
        data = asdict(self)

        # Convert datetime to ISO format strings
        for dt_field in ['hour_start_timestamp', 'prediction_timestamp', 'verified_at', 'created_at']:
            if getattr(self, dt_field):
                data[dt_field] = getattr(self, dt_field).isoformat()

        return data

    def to_db_dict(self) -> Dict[str, Any]:
        """
        Convert BlockPrediction instance to a dictionary for database insertion.
        Excludes id and created_at fields.

        Returns:
            Dict[str, Any]: Dictionary for database insertion
        """
        data = self.to_dict()

        # Remove auto-generated fields
        data.pop('id', None)
        data.pop('created_at', None)

        return data

    # Helper methods
    def is_up(self) -> bool:
        """Check if prediction is UP."""
        return self.prediction == 'UP'

    def is_down(self) -> bool:
        """Check if prediction is DOWN."""
        return self.prediction == 'DOWN'

    def is_neutral(self) -> bool:
        """Check if prediction is NEUTRAL."""
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

    def is_strong(self) -> bool:
        """Check if prediction is strong."""
        return self.prediction_strength == 'strong'

    def is_moderate(self) -> bool:
        """Check if prediction is moderate."""
        return self.prediction_strength == 'moderate'

    def is_weak(self) -> bool:
        """Check if prediction is weak."""
        return self.prediction_strength == 'weak'

    def get_hour_number(self) -> int:
        """Get the hour number (0-23) from hour_start_timestamp."""
        return self.hour_start_timestamp.hour

    def get_confidence_level(self) -> str:
        """
        Get a human-readable confidence level.

        Returns:
            str: Confidence level (Very Low, Low, Moderate, High, Very High)
        """
        if self.confidence < 20:
            return "Very Low"
        elif self.confidence < 40:
            return "Low"
        elif self.confidence < 60:
            return "Moderate"
        elif self.confidence < 80:
            return "High"
        else:
            return "Very High"

    def __repr__(self) -> str:
        """String representation of BlockPrediction."""
        hour = self.get_hour_number()
        return (
            f"<BlockPrediction ticker_id={self.ticker_id} "
            f"hour={hour:02d}:00 prediction={self.prediction} "
            f"confidence={self.confidence:.1f}% strength={self.prediction_strength}>"
        )

    def __str__(self) -> str:
        """Human-readable string representation."""
        hour = self.get_hour_number()
        status = f" - {self.actual_result}" if self.actual_result else " - Pending"
        early_bias_str = f" (early_bias={self.early_bias}"
        if self.has_sustained_counter:
            early_bias_str += f", counter={self.counter_direction}"
        early_bias_str += ")"

        return (
            f"{self.hour_start_timestamp.strftime('%Y-%m-%d')} "
            f"{hour:02d}:00-{(hour+1)%24:02d}:00 "
            f"{self.prediction} "
            f"({self.prediction_strength}, {self.confidence:.1f}%)"
            f"{early_bias_str}{status}"
        )
