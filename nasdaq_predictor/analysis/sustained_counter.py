"""
Sustained Counter Analyzer for 7-Block Framework.

Analyzes blocks 3-5 (mid-pivot zone) to detect sustained reversals
against the early bias.
"""

import logging
from typing import Tuple, Optional
from .block_segmentation import BlockAnalysis

logger = logging.getLogger(__name__)


class SustainedCounterAnalyzer:
    """
    Analyzes blocks 3-5 to detect sustained counter-moves.

    From PREDICTION_MODEL_LOGIC.md Step 5:
    - Checks if price reversed against early bias
    - Requires 50% of block time on opposite side of open
    - Provides evidence of trend reversal before completion
    """

    TIME_THRESHOLD = 0.5  # 50% of block time required for sustained counter

    @staticmethod
    def check_sustained_counter(
        block_3: BlockAnalysis,
        block_4: BlockAnalysis,
        block_5: BlockAnalysis,
        early_bias: str
    ) -> Tuple[bool, Optional[str]]:
        """
        Check for sustained counter-move in blocks 3-5.

        Args:
            block_3: Block 3 analysis
            block_4: Block 4 analysis
            block_5: Block 5 analysis
            early_bias: Early bias direction (UP, DOWN, NEUTRAL)

        Returns:
            Tuple of (has_counter: bool, counter_direction: UP/DOWN/None)

        Logic:
            - If early_bias == UP: check for sustained DOWN (price below open 50%+ of time)
            - If early_bias == DOWN: check for sustained UP (price above open 50%+ of time)
            - If early_bias == NEUTRAL: no counter possible (no bias to counter)
        """
        if early_bias not in ['UP', 'DOWN', 'NEUTRAL']:
            raise ValueError(f"Invalid early_bias: {early_bias}")

        # Neutral bias has no counter
        if early_bias == 'NEUTRAL':
            logger.debug("No sustained counter check for NEUTRAL early bias")
            return False, None

        # Check each block for sustained counter
        for block in [block_3, block_4, block_5]:
            has_counter, direction = SustainedCounterAnalyzer._check_block_counter(
                block, early_bias
            )

            if has_counter:
                logger.info(
                    f"Sustained {direction} counter detected in {block}. "
                    f"Against early bias {early_bias}"
                )
                return True, direction

        logger.debug(f"No sustained counter detected against {early_bias} bias")
        return False, None

    @staticmethod
    def _check_block_counter(
        block: BlockAnalysis,
        early_bias: str
    ) -> Tuple[bool, Optional[str]]:
        """
        Check if a single block shows sustained counter against early bias.

        Decision Logic:
            - For UP bias: counter is DOWN if price_at_end < open AND time_below >= 50%
            - For DOWN bias: counter is UP if price_at_end > open AND time_above >= 50%

        Args:
            block: Block analysis to check
            early_bias: Direction of early bias (UP or DOWN)

        Returns:
            Tuple of (has_counter: bool, direction: UP/DOWN/None)
        """
        if early_bias == 'UP':
            # Check for DOWN counter
            # Requires: price below open AND 50%+ time below open
            if (block.price_at_end < block.open_price and
                block.time_below_open >= SustainedCounterAnalyzer.TIME_THRESHOLD):
                logger.debug(
                    f"{block.block_number}: DOWN counter confirmed "
                    f"(close={block.price_at_end:.2f} < open={block.open_price:.2f}, "
                    f"time_below={block.time_below_open:.1%})"
                )
                return True, 'DOWN'

        elif early_bias == 'DOWN':
            # Check for UP counter
            # Requires: price above open AND 50%+ time above open
            if (block.price_at_end > block.open_price and
                block.time_above_open >= SustainedCounterAnalyzer.TIME_THRESHOLD):
                logger.debug(
                    f"{block.block_number}: UP counter confirmed "
                    f"(close={block.price_at_end:.2f} > open={block.open_price:.2f}, "
                    f"time_above={block.time_above_open:.1%})"
                )
                return True, 'UP'

        return False, None

    @staticmethod
    def get_counter_strength(block: BlockAnalysis) -> float:
        """
        Get the strength of a counter-move (how convincing is it).

        Args:
            block: Block with counter

        Returns:
            Strength value based on time allocation (0-1)
        """
        # Use the time spent on the opposite side as strength
        return max(block.time_above_open, block.time_below_open)
