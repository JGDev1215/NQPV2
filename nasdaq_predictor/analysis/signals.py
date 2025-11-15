"""
Signal generation and prediction calculations
"""
from typing import Dict, Any
from ..models.market_data import ReferenceLevels, SignalData, RangeLevel
from ..config.settings import WEIGHTS


def calculate_signals(current_price: float, reference_levels: ReferenceLevels) -> Dict[str, Any]:
    """
    Calculate signals, weighted score, prediction, and confidence

    Supports both single-price reference levels and range-based reference levels (RangeLevel).
    For range-based levels:
        - BULLISH (signal=1): price > range.high
        - BEARISH (signal=0): price < range.low
        - NEUTRAL (signal=None): range.low <= price <= range.high (not counted in weighted score)

    Args:
        current_price: Current market price
        reference_levels: ReferenceLevels object

    Returns:
        Dictionary containing:
            - signals: Dict of signal data for each reference level
            - weighted_score: Weighted score (0 to 1.0)
            - prediction: 'BULLISH' or 'BEARISH'
            - confidence: Confidence percentage (0-100)
            - bullish_count: Number of bullish signals
            - total_signals: Total number of valid signals (excludes neutrals)
    """
    signals = {}
    weighted_score = 0.0
    valid_signals = 0
    total_weight_used = 0.0  # Track actual weight used (excluding neutrals)

    # Convert reference levels to dict for iteration (handle both dict and ReferenceLevels object)
    ref_levels_dict = reference_levels if isinstance(reference_levels, dict) else reference_levels.to_dict()

    for key, ref_level in ref_levels_dict.items():
        if ref_level is not None:
            # Check if this is a range-based reference level
            if isinstance(ref_level, RangeLevel):
                # Range-based signal calculation
                position = ref_level.get_position(current_price)

                if position == 'ABOVE':
                    signal = 1  # BULLISH
                    distance = current_price - ref_level.high
                    status = 'BULLISH'
                    reference_value = ref_level.high
                    # Add to weighted score
                    weighted_score += signal * WEIGHTS[key]
                    total_weight_used += WEIGHTS[key]
                    valid_signals += 1

                elif position == 'BELOW':
                    signal = 0  # BEARISH
                    distance = current_price - ref_level.low
                    status = 'BEARISH'
                    reference_value = ref_level.low
                    # Add to weighted score (0 * weight = 0)
                    weighted_score += signal * WEIGHTS[key]
                    total_weight_used += WEIGHTS[key]
                    valid_signals += 1

                else:  # WITHIN
                    signal = None  # NEUTRAL
                    distance = 0.0
                    status = 'NEUTRAL'
                    reference_value = ref_level.midpoint
                    # Do NOT add to weighted score or valid_signals
                    # This weight is effectively skipped

                signals[key] = {
                    'signal': signal,
                    'level': key,  # Reference level name for storage
                    'value': reference_value,  # Reference level value
                    'weight': WEIGHTS.get(key, 0.0),  # Weight for this level
                    'reference_level': reference_value,
                    'range_high': ref_level.high,
                    'range_low': ref_level.low,
                    'is_range': True,
                    'distance': distance,
                    'status': status
                }

            else:
                # Single-price reference level (traditional logic)
                signal = 1 if current_price > ref_level else 0
                distance = current_price - ref_level
                status = 'BULLISH' if signal == 1 else 'BEARISH'

                signals[key] = {
                    'signal': signal,
                    'level': key,  # Reference level name for storage
                    'value': ref_level,  # Reference level value
                    'weight': WEIGHTS.get(key, 0.0),  # Weight for this level
                    'reference_level': ref_level,
                    'is_range': False,
                    'distance': distance,
                    'status': status
                }

                # Add to weighted score
                weighted_score += signal * WEIGHTS[key]
                total_weight_used += WEIGHTS[key]
                valid_signals += 1

        else:
            # N/A signal (reference level not available)
            signals[key] = {
                'signal': None,
                'level': key,  # Reference level name for storage
                'value': None,  # Reference level value
                'weight': WEIGHTS.get(key, 0.0),  # Weight for this level
                'reference_level': None,
                'is_range': False,
                'distance': None,
                'status': 'N/A'
            }

    # Calculate prediction and confidence
    # Normalize weighted_score by total_weight_used (not 1.0) to account for skipped neutral ranges
    if total_weight_used > 0:
        normalized_score = weighted_score / total_weight_used
    else:
        normalized_score = 0.5  # Default to neutral if no valid signals

    prediction = 'BULLISH' if normalized_score >= 0.5 else 'BEARISH'
    confidence = abs((normalized_score - 0.5) / 0.5) * 100

    # Count bullish signals (exclude neutrals)
    bullish_count = sum(1 for s in signals.values() if s['signal'] == 1)

    return {
        'signals': signals,
        'weighted_score': weighted_score,
        'normalized_score': normalized_score,
        'total_weight_used': total_weight_used,
        'prediction': prediction,
        'confidence': confidence,
        'bullish_count': bullish_count,
        'total_signals': valid_signals
    }
