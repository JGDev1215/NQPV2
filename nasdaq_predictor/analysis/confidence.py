"""
Intraday Hourly Prediction System for 9am and 10am candles
Predicts whether the close price will be higher (BULLISH) or lower (BEARISH) than the open price
"""
import logging
import pandas as pd
from datetime import datetime
from typing import Optional, Dict, Any

from ..config.settings import (
    PREDICTION_WINDOWS,
    CONFIDENCE_DECAY_CONFIG,
    DISPLAY_CUTOFFS
)
from ..models.market_data import IntradayPrediction, IntradayPredictions
from ..utils.timezone import (
    get_ny_time,
    get_ny_hour_timestamp,
    get_current_prediction_window,
    format_time_until,
    get_ticker_time,
    get_ticker_hour_timestamp
)

logger = logging.getLogger(__name__)


def calculate_decay_factor(current_time_utc: datetime, target_hour: int, ticker_symbol: str) -> float:
    """
    Calculate confidence decay factor based on time distance to prediction target

    The closer we are to the target hour, the higher the confidence.
    Uses exponential decay: confidence decreases as we get further from target.

    Args:
        current_time_utc: Current time in UTC
        target_hour: Target hour in ticker's local time (9 or 10)
        ticker_symbol: Ticker symbol (e.g., 'NQ=F', '^FTSE')

    Returns:
        Decay factor between 0.0 and 1.0 (1.0 = at target, lower = further away)
    """
    local_time = get_ticker_time(current_time_utc, ticker_symbol)
    target_time_utc = get_ticker_hour_timestamp(current_time_utc, target_hour, 0, ticker_symbol)

    # Calculate time distance in hours
    time_delta = abs((target_time_utc - current_time_utc).total_seconds() / 3600)

    # Maximum hours before we start showing predictions
    max_hours = CONFIDENCE_DECAY_CONFIG['max_hours_before']

    # If beyond max hours, return minimum confidence
    if time_delta > max_hours:
        return CONFIDENCE_DECAY_CONFIG['min_confidence_factor']

    # Exponential decay: factor = 1.0 - (distance/max_distance)^2
    # This creates a curve where confidence increases rapidly as we approach target
    normalized_distance = time_delta / max_hours
    decay_factor = 1.0 - (normalized_distance ** 2)

    # Ensure we don't go below minimum confidence factor
    decay_factor = max(decay_factor, CONFIDENCE_DECAY_CONFIG['min_confidence_factor'])

    return decay_factor


def check_prediction_accuracy(
    predicted_direction: str,
    reference_open: float,
    actual_close: float
) -> str:
    """
    Check if prediction was correct by comparing predicted direction
    with actual price movement

    Args:
        predicted_direction: 'BULLISH' or 'BEARISH'
        reference_open: Open price at prediction time
        actual_close: Close price at target time

    Returns:
        'CORRECT' or 'WRONG'
    """
    actual_direction = 'BULLISH' if actual_close > reference_open else 'BEARISH'
    return 'CORRECT' if predicted_direction == actual_direction else 'WRONG'


def get_target_close_price(
    hourly_data: pd.DataFrame,
    target_hour: int,
    current_time_utc: datetime,
    ticker_symbol: str
) -> Optional[float]:
    """
    Get the close price at the target hour (if available)

    Args:
        hourly_data: Hourly OHLC dataframe
        target_hour: Target hour in ticker's local time (10 for 9am pred, 11 for 10am pred)
        current_time_utc: Current time in UTC
        ticker_symbol: Ticker symbol (e.g., 'NQ=F', '^FTSE')

    Returns:
        Close price at target hour, or None if not yet available
    """
    target_time_utc = get_ticker_hour_timestamp(current_time_utc, target_hour, 0, ticker_symbol)

    # Look for candle at or after target time
    target_data = hourly_data[hourly_data.index >= target_time_utc]

    if not target_data.empty:
        # Return the close of the first candle at/after target
        return target_data['Close'].iloc[0]

    return None


def get_reference_open_price(
    hourly_data: pd.DataFrame,
    reference_hour: int,
    current_time_utc: datetime,
    ticker_symbol: str
) -> Optional[float]:
    """
    Get the open price at the reference hour (9am or 10am)

    Args:
        hourly_data: Hourly OHLC dataframe
        reference_hour: Reference hour in ticker's local time (9 or 10)
        current_time_utc: Current time in UTC
        ticker_symbol: Ticker symbol (e.g., 'NQ=F', '^FTSE')

    Returns:
        Open price at reference hour, or None if not available
    """
    reference_time_utc = get_ticker_hour_timestamp(current_time_utc, reference_hour, 0, ticker_symbol)

    # Look for candle at or after reference time
    ref_data = hourly_data[hourly_data.index >= reference_time_utc]

    if not ref_data.empty:
        return ref_data['Open'].iloc[0]

    return None


def generate_single_prediction(
    base_confidence: float,
    base_prediction: str,
    current_time_utc: datetime,
    target_hour: int,
    reference_hour: int,
    hourly_data: pd.DataFrame,
    time_window: str,
    ticker_symbol: str
) -> IntradayPrediction:
    """
    Generate a single intraday prediction (for 9am or 10am)

    Args:
        base_confidence: Base confidence from signal calculation (0-100%)
        base_prediction: Base prediction ('BULLISH' or 'BEARISH')
        current_time_utc: Current time in UTC
        target_hour: Target close hour (10 for 9am, 11 for 10am)
        reference_hour: Reference open hour (9 or 10)
        hourly_data: Hourly OHLC data
        time_window: Current time window
        ticker_symbol: Ticker symbol (e.g., 'NQ=F', '^FTSE')

    Returns:
        IntradayPrediction object
    """
    # Calculate decay factor based on time until target
    decay_factor = calculate_decay_factor(current_time_utc, reference_hour, ticker_symbol)

    # Apply decay to confidence (but keep it above min_confidence_factor%)
    adjusted_confidence = base_confidence * (
        CONFIDENCE_DECAY_CONFIG['min_confidence_factor'] +
        (1 - CONFIDENCE_DECAY_CONFIG['min_confidence_factor']) * decay_factor
    )

    # Get local time for status determination (NY for US tickers, London for FTSE)
    local_time = get_ticker_time(current_time_utc, ticker_symbol)

    # Determine status accounting for yfinance 15-minute delay
    # Data is available ~16 minutes after the hour
    # 9am open available at 9:16am, 10am close available at 10:16am
    if time_window == 'pre_9am':
        status = 'PENDING'
    elif time_window == f'{reference_hour}am_hour':
        status = 'ACTIVE'
    elif time_window in ['post_10am', 'evening']:
        # 9am prediction locked at 10:16am, 10am prediction locked at 11:16am
        lock_hour = target_hour
        lock_minute = 16
        if local_time.hour > lock_hour or (local_time.hour == lock_hour and local_time.minute >= lock_minute):
            status = 'LOCKED'
        else:
            status = 'ACTIVE'
    else:
        status = 'PENDING'

    # Get reference open price (for verification)
    reference_open = get_reference_open_price(hourly_data, reference_hour, current_time_utc, ticker_symbol)

    # Get target close price (if available, considering 15-min delay)
    target_close = get_target_close_price(hourly_data, target_hour, current_time_utc, ticker_symbol)

    # Check accuracy if we have both prices
    actual_result = None
    if reference_open and target_close and status == 'LOCKED':
        actual_result = check_prediction_accuracy(base_prediction, reference_open, target_close)
        status = 'VERIFIED'

    # Calculate time until target
    target_time_utc = get_ticker_hour_timestamp(current_time_utc, target_hour, 0, ticker_symbol)
    time_until_target = format_time_until(target_time_utc, current_time_utc)

    return IntradayPrediction(
        prediction=base_prediction,
        confidence=round(adjusted_confidence, 1),
        base_confidence=round(base_confidence, 1),
        decay_factor=round(decay_factor, 3),
        status=status,
        actual_result=actual_result,
        target_close=target_close,
        reference_open=reference_open,
        time_until_target=time_until_target
    )


def calculate_intraday_predictions(
    base_confidence: float,
    base_prediction: str,
    current_time_utc: datetime,
    hourly_data: pd.DataFrame,
    ticker_symbol: str,
    seven_am_open: Optional[float] = None,
    eight_thirty_am_open: Optional[float] = None,
    previous_day_predictions: Optional[Dict[str, Any]] = None
) -> IntradayPredictions:
    """
    Calculate intraday hourly predictions for both 9am and 10am windows

    This is the main function that generates predictions for:
    - 9am candle (predicting if 10am close > 9am open = BULLISH, else BEARISH)
    - 10am candle (predicting if 11am close > 10am open = BULLISH, else BEARISH)

    Args:
        base_confidence: Base confidence from weighted signal (0-100%)
        base_prediction: Base prediction ('BULLISH' or 'BEARISH')
        current_time_utc: Current time in UTC
        hourly_data: Hourly OHLC dataframe
        ticker_symbol: Ticker symbol (e.g., 'NQ=F', '^FTSE')
        seven_am_open: 7:00am local open price (may be None if unavailable)
        eight_thirty_am_open: 8:30am local open price (may be None if unavailable)
        previous_day_predictions: Previous day's predictions (for display)

    Returns:
        IntradayPredictions object with both 9am and 10am predictions
    """
    # Get local time and determine current window (timezone-aware)
    local_time = get_ticker_time(current_time_utc, ticker_symbol)
    time_window = get_current_prediction_window(current_time_utc, ticker_symbol)

    # Generate 9am prediction (targeting 10am close)
    nine_am_prediction = generate_single_prediction(
        base_confidence=base_confidence,
        base_prediction=base_prediction,
        current_time_utc=current_time_utc,
        target_hour=10,  # 10am close
        reference_hour=9,  # 9am open
        hourly_data=hourly_data,
        time_window=time_window,
        ticker_symbol=ticker_symbol
    )

    # Generate 10am prediction (targeting 11am close)
    ten_am_prediction = generate_single_prediction(
        base_confidence=base_confidence,
        base_prediction=base_prediction,
        current_time_utc=current_time_utc,
        target_hour=11,  # 11am close
        reference_hour=10,  # 10am open
        hourly_data=hourly_data,
        time_window=time_window,
        ticker_symbol=ticker_symbol
    )

    # Determine if predictions are locked (accounting for yfinance 15-min delay)
    # Locked at 11:16am local time when 10am close data becomes available
    predictions_locked = local_time.hour > 11 or (local_time.hour == 11 and local_time.minute >= 16)
    predictions_locked_at = None
    if predictions_locked:
        tz_label = 'GMT/BST' if ticker_symbol == '^FTSE' else 'EDT/EST'
        predictions_locked_at = f"{local_time.strftime('%Y-%m-%d')} 11:16 AM {tz_label}"

    # Determine next prediction time
    next_prediction_time = None
    if time_window in ['evening', 'pre_9am']:
        next_9am = get_ticker_hour_timestamp(current_time_utc, 9, 0, ticker_symbol)
        next_prediction_time = get_ticker_time(next_9am, ticker_symbol).strftime('%Y-%m-%d %I:%M %p %Z')

    # Parse previous day predictions if available
    prev_9am = None
    prev_10am = None
    if previous_day_predictions:
        if '9am' in previous_day_predictions:
            prev_9am = previous_day_predictions['9am']
        if '10am' in previous_day_predictions:
            prev_10am = previous_day_predictions['10am']

    return IntradayPredictions(
        current_time_ny=local_time.strftime('%Y-%m-%d %I:%M %p %Z'),
        current_time_utc=current_time_utc.strftime('%Y-%m-%d %H:%M:%S UTC'),
        current_time_window=time_window,
        nine_am=nine_am_prediction,
        ten_am=ten_am_prediction,
        seven_am_open=seven_am_open,
        eight_thirty_am_open=eight_thirty_am_open,
        previous_day_9am=prev_9am,
        previous_day_10am=prev_10am,
        predictions_locked=predictions_locked,
        predictions_locked_at=predictions_locked_at,
        next_prediction_time=next_prediction_time
    )
