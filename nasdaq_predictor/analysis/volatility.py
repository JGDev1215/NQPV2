"""
Volatility calculations for analysis frameworks
"""
import logging
from typing import Dict, List, Any
import numpy as np
from ..models.market_data import Volatility

logger = logging.getLogger(__name__)


def calculate_volatility(hourly_movement: List[Dict[str, Any]]) -> Volatility:
    """
    Calculate current volatility from hourly price movements

    Args:
        hourly_movement: List of hourly OHLC data dictionaries

    Returns:
        Volatility object with metrics
    """
    if not hourly_movement or len(hourly_movement) < 2:
        return Volatility(
            hourly_range_pct=0,
            level='UNKNOWN'
        )

    # Calculate average hourly range as percentage
    ranges = []
    for candle in hourly_movement:
        if candle['high'] and candle['low'] and candle['open']:
            range_pct = abs((candle['high'] - candle['low']) / candle['open']) * 100
            ranges.append(range_pct)

    if not ranges:
        return Volatility(
            hourly_range_pct=0,
            level='UNKNOWN'
        )

    avg_range_pct = sum(ranges) / len(ranges)

    # Classify volatility level
    if avg_range_pct < 0.5:
        level = 'LOW'
    elif avg_range_pct < 1.0:
        level = 'MODERATE'
    elif avg_range_pct < 1.5:
        level = 'HIGH'
    else:
        level = 'EXTREME'

    return Volatility(
        hourly_range_pct=round(avg_range_pct, 2),
        level=level
    )


def calculate_hourly_volatility(
    bars: List[Dict[str, Any]],
    opening_price: float
) -> float:
    """
    Calculate volatility in price units from intra-hour bar data.

    Uses close-to-close returns to calculate standard deviation,
    then scales by mean closing price to get volatility in price units.

    This volatility is used to normalize deviations in the 7-block framework.
    Each deviation is measured as: (price - open) / volatility in units of std devs.

    Args:
        bars: List of OHLC bars within the hour (dict with: close)
        opening_price: Opening price of the hour (equilibrium point)

    Returns:
        float: Volatility in price units (std devs)

    Raises:
        ValueError: If bars list is empty
    """
    if not bars:
        raise ValueError("Bars list cannot be empty")

    try:
        # Extract closing prices
        closes = [float(bar['close']) for bar in bars if 'close' in bar]

        if len(closes) < 2:
            # Fallback: 1% of opening price if insufficient data
            logger.warning(
                f"Insufficient bar data for volatility calculation (n={len(closes)}), "
                f"using 1% of opening price: {opening_price * 0.01:.2f}"
            )
            return opening_price * 0.01

        # Calculate close-to-close returns
        returns = []
        for i in range(1, len(closes)):
            if closes[i - 1] > 0:
                ret = (closes[i] - closes[i - 1]) / closes[i - 1]
                returns.append(ret)

        if not returns:
            # Fallback if no valid returns
            logger.warning(
                "No valid returns calculated, using 1% of opening price"
            )
            return opening_price * 0.01

        # Calculate standard deviation of returns
        returns_std = float(np.std(returns)) if len(returns) > 1 else 0

        # Calculate mean closing price
        mean_close = float(np.mean(closes))

        # Volatility = std_dev(returns) × mean(closes)
        volatility = returns_std * mean_close

        # Fallback if calculated volatility is too small
        if volatility <= 0:
            logger.debug(
                f"Calculated volatility is {volatility}, "
                f"using 1% of opening price instead"
            )
            return opening_price * 0.01

        logger.debug(
            f"Calculated hourly volatility: {volatility:.2f} "
            f"(std_dev={returns_std:.4f}, mean_close={mean_close:.2f})"
        )
        return volatility

    except Exception as e:
        logger.error(f"Error calculating hourly volatility: {e}")
        # Fallback on error
        return opening_price * 0.01
