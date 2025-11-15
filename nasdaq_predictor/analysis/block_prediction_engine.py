"""
Block Prediction Engine for 7-Block Framework.

Orchestrator that implements the three decision trees from PREDICTION_MODEL_LOGIC.md
to generate final hourly predictions based on analyzed blocks 1-5.

Main entry point for the prediction generation pipeline.
"""

import logging
from typing import Dict, Tuple, Optional, List
from .block_segmentation import BlockAnalysis
from .early_bias import EarlyBiasAnalyzer
from .sustained_counter import SustainedCounterAnalyzer

logger = logging.getLogger(__name__)


class BlockPredictionEngine:
    """
    Generates block-based predictions using the 7-block framework.

    Combines early bias detection, sustained counter analysis, and 5/7 point
    deviation to produce final UP/DOWN/NEUTRAL predictions with confidence.
    """

    # Deviation thresholds for strength classification
    STRONG_THRESHOLD = 2.0          # >= 2.0 std devs = strong
    MODERATE_THRESHOLD = 0.5        # >= 0.5 std devs = moderate
    NEUTRAL_THRESHOLD = 0.5         # < 0.5 std devs = neutral

    # Early bias strength threshold for continuation decisions
    EARLY_BIAS_STRENGTH_THRESHOLD = 1.0

    @staticmethod
    def generate_block_prediction(
        blocks_1_5: List[BlockAnalysis],
        opening_price: float,
        volatility: float
    ) -> Dict:
        """
        Generate a block-based prediction from blocks 1-5 analysis.

        Args:
            blocks_1_5: List of BlockAnalysis for blocks 1-5
            opening_price: Hour opening price (equilibrium reference)
            volatility: Hour volatility in price units

        Returns:
            Dictionary with prediction results containing:
            - prediction: UP, DOWN, or NEUTRAL
            - confidence: float 0-100
            - strength: "weak", "moderate", "strong"
            - early_bias: UP, DOWN, or NEUTRAL
            - early_bias_strength: float (std devs)
            - has_sustained_counter: bool
            - counter_direction: UP, DOWN, or None
            - deviation_at_5_7: float (std devs)
            - decision_tree_path: str (Tree 1, Tree 2, or Tree 3)

        Raises:
            ValueError: If blocks_1_5 is invalid or volatility is invalid
        """
        if not blocks_1_5 or len(blocks_1_5) < 5:
            raise ValueError(f"Expected 5 blocks, got {len(blocks_1_5)}")

        if volatility <= 0:
            raise ValueError(f"Volatility must be positive: {volatility}")

        # Extract individual blocks
        block_1 = blocks_1_5[0]
        block_2 = blocks_1_5[1]
        block_3 = blocks_1_5[2]
        block_4 = blocks_1_5[3]
        block_5 = blocks_1_5[4]

        # Step 1: Determine early bias from blocks 1-2
        early_bias, early_bias_strength = EarlyBiasAnalyzer.determine_early_bias(
            block_1, block_2, opening_price, volatility
        )
        logger.info(
            f"Early bias determined: {early_bias} (strength={early_bias_strength:.2f}σ)"
        )

        # Step 2: Check for sustained counter in blocks 3-5
        has_counter, counter_direction = SustainedCounterAnalyzer.check_sustained_counter(
            block_3, block_4, block_5, early_bias
        )
        logger.info(
            f"Counter analysis: has_counter={has_counter}, "
            f"direction={counter_direction}"
        )

        # Step 3: Get deviation at 5/7 point (end of block 5)
        deviation_at_5_7 = block_5.deviation_from_open
        logger.info(f"Deviation at 5/7 point: {deviation_at_5_7:.2f}σ")

        # Step 4: Apply decision tree based on signals
        if has_counter:
            # Decision Tree 1: Reversal detected
            prediction, strength = BlockPredictionEngine._apply_reversal_tree(
                counter_direction, deviation_at_5_7
            )
            decision_tree = "Tree 1: Reversal Detected"

        elif early_bias == 'NEUTRAL':
            # Decision Tree 2: No counter, early bias is neutral
            prediction, strength = BlockPredictionEngine._apply_neutral_tree(
                deviation_at_5_7
            )
            decision_tree = "Tree 2: Neutral Early Bias"

        else:
            # Decision Tree 3: Continuation (early bias != neutral, no counter)
            prediction, strength = BlockPredictionEngine._apply_continuation_tree(
                early_bias, early_bias_strength, deviation_at_5_7
            )
            decision_tree = "Tree 3: Continuation"

        # Step 5: Calculate confidence score
        confidence = BlockPredictionEngine._calculate_confidence(
            prediction=prediction,
            strength=strength,
            early_bias=early_bias,
            early_bias_strength=early_bias_strength,
            has_counter=has_counter,
            counter_direction=counter_direction,
            deviation_at_5_7=deviation_at_5_7
        )

        logger.info(
            f"Final prediction: {prediction} ({strength}) "
            f"confidence={confidence:.1f}% via {decision_tree}"
        )

        return {
            'prediction': prediction,
            'confidence': confidence,
            'strength': strength,
            'early_bias': early_bias,
            'early_bias_strength': round(early_bias_strength, 2),
            'has_sustained_counter': has_counter,
            'counter_direction': counter_direction,
            'deviation_at_5_7': round(deviation_at_5_7, 2),
            'decision_tree_path': decision_tree
        }

    @staticmethod
    def _apply_reversal_tree(
        counter_direction: str,
        deviation_at_5_7: float
    ) -> Tuple[str, str]:
        """
        Decision Tree 1: Reversal Detected (has_sustained_counter == True).

        From PREDICTION_MODEL_LOGIC.md Decision Tree 1:
        ├─ Is price near open at 5/7?
        │  ├─ |deviation_at_5_7| < 0.5
        │  │  └─ NEUTRAL, "weak"
        │  │     (Reversal underway but not decisive)
        │  │
        │  └─ |deviation_at_5_7| >= 0.5
        │     ├─ |deviation_at_5_7| < 2.0
        │     │  └─ counter_direction, "moderate"
        │     │
        │     └─ |deviation_at_5_7| >= 2.0
        │        └─ counter_direction, "strong"

        Args:
            counter_direction: Direction of the counter (UP or DOWN)
            deviation_at_5_7: Deviation at prediction point (std devs)

        Returns:
            Tuple of (prediction: UP/DOWN/NEUTRAL, strength: weak/moderate/strong)
        """
        abs_deviation = abs(deviation_at_5_7)

        if abs_deviation < BlockPredictionEngine.MODERATE_THRESHOLD:
            # Reversal detected but price not yet decisive
            logger.debug(
                f"Tree 1: Reversal underway but inconclusive "
                f"(|dev|={abs_deviation:.2f} < 0.5)"
            )
            return 'NEUTRAL', 'weak'

        elif abs_deviation < BlockPredictionEngine.STRONG_THRESHOLD:
            # Reversal confirmed at moderate strength
            logger.debug(
                f"Tree 1: Reversal confirmed moderate "
                f"(0.5 <= |dev|={abs_deviation:.2f} < 2.0)"
            )
            return counter_direction, 'moderate'

        else:
            # Reversal strong with significant movement
            logger.debug(
                f"Tree 1: Reversal confirmed strong "
                f"(|dev|={abs_deviation:.2f} >= 2.0)"
            )
            return counter_direction, 'strong'

    @staticmethod
    def _apply_neutral_tree(
        deviation_at_5_7: float
    ) -> Tuple[str, str]:
        """
        Decision Tree 2: No Sustained Counter, Early Bias = NEUTRAL.

        From PREDICTION_MODEL_LOGIC.md Decision Tree 2:
        ├─ Is price still near open at 5/7?
        │  ├─ |deviation_at_5_7| < 0.5
        │  │  └─ NEUTRAL, "weak"
        │  │     (No bias developed)
        │  │
        │  └─ |deviation_at_5_7| >= 0.5
        │     └─ Developed bias by 5/7
        │        ├─ deviation_at_5_7 > 0 → UP
        │        └─ deviation_at_5_7 < 0 → DOWN
        │           ├─ |deviation_at_5_7| < 2.0
        │           │  └─ developed_direction, "moderate"
        │           │
        │           └─ |deviation_at_5_7| >= 2.0
        │              └─ developed_direction, "strong"

        Args:
            deviation_at_5_7: Deviation at prediction point (std devs)

        Returns:
            Tuple of (prediction: UP/DOWN/NEUTRAL, strength: weak/moderate/strong)
        """
        abs_deviation = abs(deviation_at_5_7)

        if abs_deviation < BlockPredictionEngine.MODERATE_THRESHOLD:
            # No bias developed, still neutral at 5/7
            logger.debug(
                f"Tree 2: No bias developed by 5/7 "
                f"(|dev|={abs_deviation:.2f} < 0.5)"
            )
            return 'NEUTRAL', 'weak'

        # Bias developed by 5/7
        developed_direction = 'UP' if deviation_at_5_7 > 0 else 'DOWN'

        if abs_deviation < BlockPredictionEngine.STRONG_THRESHOLD:
            # Moderate strength bias development
            logger.debug(
                f"Tree 2: {developed_direction} bias developed (moderate) "
                f"(0.5 <= |dev|={abs_deviation:.2f} < 2.0)"
            )
            return developed_direction, 'moderate'

        else:
            # Strong bias development
            logger.debug(
                f"Tree 2: {developed_direction} bias developed (strong) "
                f"(|dev|={abs_deviation:.2f} >= 2.0)"
            )
            return developed_direction, 'strong'

    @staticmethod
    def _apply_continuation_tree(
        early_bias: str,
        early_bias_strength: float,
        deviation_at_5_7: float
    ) -> Tuple[str, str]:
        """
        Decision Tree 3: Continuation (Early Bias ≠ NEUTRAL, No Counter).

        From PREDICTION_MODEL_LOGIC.md Decision Tree 3:
        ├─ Is deviation at 5/7 strong?
        │  ├─ |deviation_at_5_7| >= 2.0
        │  │  └─ early_bias, "strong"
        │  │     (Momentum building)
        │  │
        │  └─ |deviation_at_5_7| < 2.0
        │     ├─ early_bias_strength >= 1.0
        │     │  └─ early_bias, "moderate"
        │     │     (Momentum holding)
        │     │
        │     └─ early_bias_strength < 1.0
        │        └─ early_bias, "weak"
        │           (Weak early momentum)

        Args:
            early_bias: Direction of early bias (UP or DOWN)
            early_bias_strength: Strength of early bias (std devs)
            deviation_at_5_7: Deviation at prediction point (std devs)

        Returns:
            Tuple of (prediction: UP/DOWN, strength: weak/moderate/strong)
        """
        abs_deviation = abs(deviation_at_5_7)

        if abs_deviation >= BlockPredictionEngine.STRONG_THRESHOLD:
            # Momentum accelerating
            logger.debug(
                f"Tree 3: {early_bias} momentum accelerating "
                f"(|dev|={abs_deviation:.2f} >= 2.0)"
            )
            return early_bias, 'strong'

        elif early_bias_strength >= BlockPredictionEngine.EARLY_BIAS_STRENGTH_THRESHOLD:
            # Momentum holding at moderate strength
            logger.debug(
                f"Tree 3: {early_bias} momentum holding "
                f"(strength={early_bias_strength:.2f} >= 1.0, "
                f"|dev|={abs_deviation:.2f} < 2.0)"
            )
            return early_bias, 'moderate'

        else:
            # Weak early momentum
            logger.debug(
                f"Tree 3: {early_bias} momentum weak "
                f"(strength={early_bias_strength:.2f} < 1.0)"
            )
            return early_bias, 'weak'

    @staticmethod
    def _calculate_confidence(
        prediction: str,
        strength: str,
        early_bias: str,
        early_bias_strength: float,
        has_counter: bool,
        counter_direction: Optional[str],
        deviation_at_5_7: float
    ) -> float:
        """
        Calculate confidence score (0-100) based on all signals.

        Confidence factors:
        1. Strength level (weak=40%, moderate=70%, strong=95%)
        2. Early bias alignment (prediction matches early bias: +10%)
        3. Counter confirmation (counter in place: +5%)
        4. Deviation magnitude (larger deviation: additional points)

        Args:
            prediction: Final prediction (UP/DOWN/NEUTRAL)
            strength: Prediction strength level
            early_bias: Early bias direction
            early_bias_strength: Early bias magnitude (std devs)
            has_counter: Whether counter detected
            counter_direction: Direction of counter if present
            deviation_at_5_7: Deviation at 5/7 point (std devs)

        Returns:
            Confidence score 0-100
        """
        # Base confidence from strength level
        if strength == 'strong':
            confidence = 85.0
        elif strength == 'moderate':
            confidence = 65.0
        else:  # weak
            confidence = 35.0

        # Bonus for early bias alignment (prediction matches early bias)
        if prediction != 'NEUTRAL' and early_bias == prediction:
            confidence += 10.0
            logger.debug(f"Confidence +10: early bias aligns with prediction")

        # Bonus for counter confirmation
        if has_counter and counter_direction == prediction:
            confidence += 5.0
            logger.debug(f"Confidence +5: counter confirms prediction")

        # Bonus/penalty for deviation magnitude
        abs_deviation = abs(deviation_at_5_7)
        if abs_deviation >= 2.0:
            confidence = min(confidence + 10.0, 95.0)
            logger.debug(f"Confidence +10: large deviation ({abs_deviation:.2f}σ)")
        elif abs_deviation < 0.25:
            confidence = max(confidence - 5.0, 20.0)
            logger.debug(f"Confidence -5: very small deviation ({abs_deviation:.2f}σ)")

        # Cap confidence at 95% (never 100%, always some uncertainty)
        confidence = min(confidence, 95.0)
        confidence = max(confidence, 5.0)  # Minimum 5%

        logger.debug(f"Final confidence: {confidence:.1f}%")
        return round(confidence, 1)

    @staticmethod
    def classify_strength(magnitude: float) -> str:
        """
        Classify magnitude into strength level.

        Args:
            magnitude: Value in standard deviations

        Returns:
            "weak", "moderate", or "strong"
        """
        abs_magnitude = abs(magnitude)
        if abs_magnitude >= BlockPredictionEngine.STRONG_THRESHOLD:
            return 'strong'
        elif abs_magnitude >= BlockPredictionEngine.MODERATE_THRESHOLD:
            return 'moderate'
        else:
            return 'weak'
