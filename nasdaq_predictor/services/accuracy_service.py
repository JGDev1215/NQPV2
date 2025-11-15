"""
Accuracy Service for Prediction Verification.

Consolidates common prediction evaluation and accuracy metrics logic
extracted from PredictionVerificationService and IntradayVerificationService.

Provides reusable methods for:
1. Evaluating prediction correctness
2. Calculating price movements
3. Computing accuracy metrics
4. Building standardized result structures
"""

import logging
from typing import Dict, Any, Optional, Tuple
from datetime import datetime

logger = logging.getLogger(__name__)


class AccuracyService:
    """Service for standardized accuracy evaluation and metrics calculation.

    Provides reusable accuracy evaluation logic that both PredictionVerificationService
    and IntradayVerificationService can use, eliminating duplication and ensuring
    consistent evaluation logic across different prediction types.

    Supports:
    - Threshold-based evaluation (with neutral detection)
    - Directional evaluation (bullish/bearish only)
    - Price change calculations (absolute and percentage)
    - Accuracy metrics computation
    - Standardized result structure building
    """

    # Standard evaluation result types
    RESULT_CORRECT = 'CORRECT'
    RESULT_WRONG = 'WRONG'
    RESULT_NEUTRAL_RANGE = 'NEUTRAL_RANGE'

    # Standard prediction types
    PREDICTION_BULLISH = 'BULLISH'
    PREDICTION_BEARISH = 'BEARISH'
    PREDICTION_NEUTRAL = 'NEUTRAL'

    def __init__(self, neutral_threshold_percent: float = 0.1):
        """Initialize AccuracyService with configurable thresholds.

        Args:
            neutral_threshold_percent: Price change threshold for neutral detection (default: 0.1%)
        """
        self.neutral_threshold_percent = neutral_threshold_percent
        logger.debug(f"AccuracyService initialized with neutral_threshold={neutral_threshold_percent}%")

    def evaluate_prediction(
        self,
        prediction_type: str,
        price_change_percent: float
    ) -> str:
        """Evaluate if a prediction was correct based on actual price movement.

        Uses threshold-based evaluation: price movements within neutral_threshold
        are treated as neutral, otherwise directional comparison is used.

        Args:
            prediction_type: BULLISH, BEARISH, or NEUTRAL
            price_change_percent: Actual price change percentage

        Returns:
            str: 'CORRECT', 'WRONG', or 'NEUTRAL_RANGE'
        """
        # Check if price movement was within neutral range
        if abs(price_change_percent) <= self.neutral_threshold_percent:
            # Price barely moved - correct if predicted neutral, otherwise neutral range
            return self.RESULT_CORRECT if prediction_type == self.PREDICTION_NEUTRAL else self.RESULT_NEUTRAL_RANGE

        # Price moved significantly - evaluate directionality
        if prediction_type == self.PREDICTION_BULLISH:
            return self.RESULT_CORRECT if price_change_percent > 0 else self.RESULT_WRONG
        elif prediction_type == self.PREDICTION_BEARISH:
            return self.RESULT_CORRECT if price_change_percent < 0 else self.RESULT_WRONG
        elif prediction_type == self.PREDICTION_NEUTRAL:
            # Predicted neutral but price moved significantly
            return self.RESULT_WRONG
        else:
            logger.warning(f"Unknown prediction type: {prediction_type}")
            return self.RESULT_WRONG

    def evaluate_directional_prediction(
        self,
        prediction: str,
        actual_price: float,
        reference_price: float
    ) -> bool:
        """Evaluate prediction correctness using simple directional comparison.

        Uses absolute price comparison (no threshold) - suitable for hour-based
        predictions where any movement in predicted direction is considered correct.

        Args:
            prediction: BULLISH or BEARISH
            actual_price: Actual closing price
            reference_price: Reference price (e.g., opening price)

        Returns:
            bool: True if prediction was correct, False otherwise
        """
        actual_direction = self.calculate_direction(actual_price, reference_price)

        is_correct = prediction == actual_direction
        logger.debug(
            f"Directional evaluation: {prediction} vs {actual_direction} (actual={actual_price}, ref={reference_price}) → {is_correct}"
        )
        return is_correct

    def calculate_price_change(
        self,
        actual_price: float,
        reference_price: float
    ) -> Dict[str, Any]:
        """Calculate price change in multiple formats.

        Args:
            actual_price: Current/closing price
            reference_price: Baseline/reference price

        Returns:
            dict with keys:
                - absolute: Absolute price change (actual - reference)
                - percent: Percentage change ((actual - reference) / reference * 100)
                - direction: Direction of movement (BULLISH, BEARISH, or NEUTRAL)
        """
        absolute_change = actual_price - reference_price

        # Avoid division by zero
        if reference_price == 0:
            logger.warning(f"Reference price is 0, cannot calculate percentage change")
            percent_change = 0.0
        else:
            percent_change = (absolute_change / reference_price) * 100

        direction = self.calculate_direction(actual_price, reference_price)

        return {
            'absolute': round(absolute_change, 4),
            'percent': round(percent_change, 4),
            'direction': direction
        }

    def calculate_direction(
        self,
        actual_price: float,
        reference_price: float
    ) -> str:
        """Determine directional movement from price comparison.

        Args:
            actual_price: Current/closing price
            reference_price: Baseline/reference price

        Returns:
            str: BULLISH (if actual > reference), BEARISH (if actual < reference), or NEUTRAL (if equal)
        """
        if actual_price > reference_price:
            return self.PREDICTION_BULLISH
        elif actual_price < reference_price:
            return self.PREDICTION_BEARISH
        else:
            return self.PREDICTION_NEUTRAL

    def calculate_accuracy_metrics(
        self,
        correct_count: int,
        total_count: int,
        wrong_count: Optional[int] = None
    ) -> Dict[str, float]:
        """Calculate accuracy and success metrics.

        Args:
            correct_count: Number of correct predictions
            total_count: Total number of predictions verified
            wrong_count: Number of wrong predictions (optional, for validation)

        Returns:
            dict with keys:
                - accuracy_percent: Accuracy as percentage (correct / total * 100)
                - success_rate: Same as accuracy_percent (alternative name)
                - correct_percent: Percentage of correct predictions
                - error_percent: Percentage of wrong predictions
        """
        if total_count == 0:
            logger.debug("No predictions to calculate accuracy for")
            return {
                'accuracy_percent': 0.0,
                'success_rate': 0.0,
                'correct_percent': 0.0,
                'error_percent': 0.0
            }

        accuracy = round((correct_count / total_count) * 100, 2)
        error_count = total_count - correct_count
        error_percent = round((error_count / total_count) * 100, 2)

        return {
            'accuracy_percent': accuracy,
            'success_rate': accuracy,  # Alias for accuracy_percent
            'correct_percent': round((correct_count / total_count) * 100, 2),
            'error_percent': error_percent
        }

    def build_verification_summary(
        self,
        total_verified: int,
        correct_count: int,
        wrong_count: int,
        errors: Optional[list] = None,
        timestamp: Optional[datetime] = None,
        success: bool = True
    ) -> Dict[str, Any]:
        """Build standardized verification summary result structure.

        This is the format returned by both verification services.

        Args:
            total_verified: Total predictions verified
            correct_count: Number of correct predictions
            wrong_count: Number of wrong predictions
            errors: List of errors encountered (default: empty list)
            timestamp: Verification timestamp (default: now)
            success: Overall success status (default: True)

        Returns:
            dict with standard verification summary structure
        """
        if errors is None:
            errors = []

        if timestamp is None:
            timestamp = datetime.utcnow()

        return {
            'success': success,
            'timestamp': timestamp.isoformat() if isinstance(timestamp, datetime) else timestamp,
            'total_verified': total_verified,
            'correct': correct_count,
            'wrong': wrong_count,
            'errors': errors,
            'accuracy_metrics': self.calculate_accuracy_metrics(correct_count, total_verified, wrong_count)
        }

    def build_ticker_result(
        self,
        verified_count: int,
        correct_count: int,
        wrong_count: int
    ) -> Dict[str, int]:
        """Build standardized ticker-level verification result.

        Returned by verification services when summarizing results per ticker.

        Args:
            verified_count: Predictions verified for this ticker
            correct_count: Correct predictions for this ticker
            wrong_count: Wrong predictions for this ticker

        Returns:
            dict with ticker-level result structure
        """
        return {
            'verified_count': verified_count,
            'correct_count': correct_count,
            'wrong_count': wrong_count
        }

    def is_correct_result(self, result: str) -> bool:
        """Check if an evaluation result represents a correct prediction.

        Args:
            result: Evaluation result string

        Returns:
            bool: True if result is CORRECT
        """
        return result == self.RESULT_CORRECT

    def is_wrong_result(self, result: str) -> bool:
        """Check if an evaluation result represents a wrong prediction.

        Args:
            result: Evaluation result string

        Returns:
            bool: True if result is WRONG
        """
        return result == self.RESULT_WRONG

    def is_neutral_range_result(self, result: str) -> bool:
        """Check if evaluation result indicates neutral range (no clear direction).

        Args:
            result: Evaluation result string

        Returns:
            bool: True if result is NEUTRAL_RANGE
        """
        return result == self.RESULT_NEUTRAL_RANGE

    def set_neutral_threshold(self, threshold_percent: float) -> None:
        """Update the neutral threshold for directional detection.

        Args:
            threshold_percent: New threshold percentage
        """
        self.neutral_threshold_percent = threshold_percent
        logger.info(f"Updated neutral threshold to {threshold_percent}%")

    def get_neutral_threshold(self) -> float:
        """Get the current neutral threshold.

        Returns:
            float: Current neutral threshold percentage
        """
        return self.neutral_threshold_percent

    def format_price_change_string(
        self,
        price_change_percent: float,
        absolute_change: Optional[float] = None
    ) -> str:
        """Format price change for display/logging.

        Args:
            price_change_percent: Percentage change
            absolute_change: Optional absolute change for display

        Returns:
            str: Formatted price change string (e.g., "+2.45%" or "+$5.00 (+2.45%)")
        """
        percent_str = f"{price_change_percent:+.2f}%"

        if absolute_change is not None:
            return f"+${absolute_change:,.2f} ({percent_str})" if absolute_change >= 0 else f"-${abs(absolute_change):,.2f} ({percent_str})"

        return percent_str

    def summarize_verification_results(
        self,
        results: Dict[str, Any]
    ) -> str:
        """Create a human-readable summary of verification results.

        Args:
            results: Verification summary dict from build_verification_summary()

        Returns:
            str: Human-readable summary string
        """
        total = results.get('total_verified', 0)
        correct = results.get('correct', 0)
        wrong = results.get('wrong', 0)
        errors = len(results.get('errors', []))
        accuracy = results.get('accuracy_metrics', {}).get('accuracy_percent', 0.0)

        return (
            f"Verified {total} predictions: "
            f"{correct} correct ({accuracy:.1f}%), "
            f"{wrong} wrong, "
            f"{errors} errors"
        )
