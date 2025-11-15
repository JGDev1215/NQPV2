"""
Intraday prediction calculation module.

This module provides utility functions for calculating intraday predictions
at specific target hours, used by the backfill script and scheduler.
"""

import logging
from datetime import datetime
from typing import Dict, List, Optional

logger = logging.getLogger(__name__)


def calculate_intraday_predictions(
    signals: Dict,
    current_price: float,
    current_time_utc: datetime,
    target_hours: List[int]
) -> Dict[int, Dict]:
    """
    Calculate intraday predictions for specific target hours.

    This is a simplified version for backfilling that creates predictions
    for arbitrary target hours (not just 9am and 10am).

    Args:
        signals: Signals dict with prediction, confidence, etc.
        current_price: Current price at prediction time
        current_time_utc: Current time in UTC
        target_hours: List of target hours (e.g., [9, 10, 11, 12])

    Returns:
        Dictionary mapping target_hour -> prediction_data
    """
    predictions = {}

    for target_hour in target_hours:
        # Calculate time distance to target (in hours)
        current_hour = current_time_utc.hour
        hours_until_target = target_hour - current_hour

        # If target is in the past or too far in future, use lower confidence
        if hours_until_target < 0:
            # Target has passed, use full confidence
            decay_factor = 1.0
        elif hours_until_target == 0:
            # We're at the target hour, maximum confidence
            decay_factor = 1.0
        elif hours_until_target == 1:
            # 1 hour away, high confidence
            decay_factor = 0.95
        elif hours_until_target == 2:
            # 2 hours away, good confidence
            decay_factor = 0.85
        elif hours_until_target <= 4:
            # 3-4 hours away, moderate confidence
            decay_factor = 0.70
        else:
            # More than 4 hours away, lower confidence
            decay_factor = max(0.50, 1.0 - (hours_until_target / 24))

        # Calculate final confidence
        base_confidence = signals.get('confidence', 50.0)
        final_confidence = base_confidence * decay_factor

        predictions[target_hour] = {
            'prediction': signals['prediction'],
            'base_confidence': base_confidence,
            'decay_factor': decay_factor,
            'final_confidence': final_confidence,
            'hours_until_target': hours_until_target
        }

        logger.debug(
            f"Prediction for hour {target_hour}: {signals['prediction']} "
            f"(Base: {base_confidence:.1f}%, Decay: {decay_factor:.3f}, "
            f"Final: {final_confidence:.1f}%)"
        )

    return predictions
