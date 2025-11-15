"""
Early Bias Analyzer for 7-Block Framework.

Analyzes blocks 1-2 (early zone) to determine initial directional momentum.
"""

import logging
from typing import Tuple
from .block_segmentation import BlockAnalysis

logger = logging.getLogger(__name__)


class EarlyBiasAnalyzer:
    """
    Analyzes blocks 1-2 to detect early directional bias.

    From PREDICTION_MODEL_LOGIC.md Step 4:
    - Looks at price deviation in block 2
    - Checks if price returned to opening level
    - Classifies as UP, DOWN, or NEUTRAL
    - Reduces strength if price crosses open (weak conviction)
    """

    NEUTRAL_THRESHOLD = 0.5  # < 0.5 std devs = neutral

    @staticmethod
    def determine_early_bias(
        block_1: BlockAnalysis,
        block_2: BlockAnalysis,
        opening_price: float,
        volatility: float
    ) -> Tuple[str, float]:
        """
        Determine early bias from blocks 1-2.

        Args:
            block_1: Block 1 analysis
            block_2: Block 2 analysis
            opening_price: Hour opening price
            volatility: Hour volatility (std dev units)

        Returns:
            Tuple of (direction: UP/DOWN/NEUTRAL, strength: float)

        Raises:
            ValueError: If inputs are invalid
        """
        if volatility <= 0:
            raise ValueError(f"Volatility must be positive: {volatility}")

        # Get deviation at end of block 2
        deviation_block_2 = block_2.deviation_from_open

        # Check if price returned to open
        # Returns to open if either block crosses the opening level
        returned_to_open = block_1.crosses_open or block_2.crosses_open

        # Classify bias (Decision Tree from PREDICTION_MODEL_LOGIC.md)
        if abs(deviation_block_2) < EarlyBiasAnalyzer.NEUTRAL_THRESHOLD:
            # NEUTRAL case: price still near open
            direction = 'NEUTRAL'
            strength = abs(deviation_block_2)
            reason = f"Price near open (deviation={deviation_block_2:.2f}σ)"

        elif deviation_block_2 > 0 and not returned_to_open:
            # UP bias, did NOT return to open: full strength
            direction = 'UP'
            strength = deviation_block_2
            reason = f"UP bias, conviction (no return to open), strength={strength:.2f}σ"

        elif deviation_block_2 > 0 and returned_to_open:
            # UP bias, but returned to open: 50% strength (weak conviction)
            direction = 'UP'
            strength = deviation_block_2 * 0.5
            reason = f"UP bias, weak (price tested open), strength={strength:.2f}σ"

        elif deviation_block_2 < 0 and not returned_to_open:
            # DOWN bias, did NOT return to open: full strength
            direction = 'DOWN'
            strength = abs(deviation_block_2)
            reason = f"DOWN bias, conviction (no return to open), strength={strength:.2f}σ"

        else:  # deviation_block_2 < 0 and returned_to_open
            # DOWN bias, but returned to open: 50% strength (weak conviction)
            direction = 'DOWN'
            strength = abs(deviation_block_2) * 0.5
            reason = f"DOWN bias, weak (price tested open), strength={strength:.2f}σ"

        logger.debug(
            f"Early Bias Analysis: {direction} (strength={strength:.2f}σ) - {reason}"
        )

        return direction, strength

    @staticmethod
    def classify_bias_strength(strength: float) -> str:
        """
        Classify strength into readable level.

        Args:
            strength: Strength value in standard deviations

        Returns:
            "weak", "moderate", or "strong"
        """
        if strength < 1.0:
            return "weak"
        elif strength < 2.0:
            return "moderate"
        else:
            return "strong"
