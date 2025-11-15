"""
Reference level calculations for market analysis
"""
import logging
import pandas as pd
from datetime import datetime, timedelta
from typing import Optional, Dict, Any, List

from ..models.market_data import ReferenceLevels, RangeLevel
from ..utils.timezone import (
    ensure_utc,
    get_et_midnight,
    get_candle_open_time,
    get_week_start,
    get_month_start,
    get_7am_ny_timestamp,
    get_830am_ny_timestamp
)
from ..config.settings import ICT_SESSIONS

logger = logging.getLogger(__name__)


def calculate_daily_open(hourly_hist: pd.DataFrame, current_time: datetime) -> Optional[float]:
    """
    Calculate Daily Open (Midnight ET with proper DST handling)

    Args:
        hourly_hist: Hourly OHLC data
        current_time: Current time in UTC

    Returns:
        Daily open price or None
    """
    et_midnight_utc = get_et_midnight(current_time)
    daily_open_data = hourly_hist[hourly_hist.index >= et_midnight_utc]

    if not daily_open_data.empty:
        return daily_open_data['Open'].iloc[0]
    return None


def calculate_hourly_open(hourly_hist: pd.DataFrame, current_time: datetime) -> Optional[float]:
    """
    Calculate Hourly Open (current hourly candle opening price)

    Args:
        hourly_hist: Hourly OHLC data
        current_time: Current time in UTC

    Returns:
        Hourly open price or None
    """
    candle_1h_time = get_candle_open_time(current_time, 60)
    hourly_data = hourly_hist[hourly_hist.index >= candle_1h_time]

    if not hourly_data.empty:
        return hourly_data['Open'].iloc[0]

    # Fallback: find nearest candle
    nearby_data = hourly_hist[hourly_hist.index <= candle_1h_time]
    if not nearby_data.empty:
        return nearby_data['Open'].iloc[-1]

    return None


def calculate_4hourly_open(hourly_hist: pd.DataFrame, current_time: datetime) -> Optional[float]:
    """
    Calculate 4-Hourly Open (current 4-hourly candle opening price)

    Uses hourly OHLC data to find the opening price at 4-hour boundaries
    (00:00, 04:00, 08:00, 12:00, 16:00, 20:00 UTC). Does NOT use dedicated
    4-hour data, but leverages hourly candles to locate precise 4h boundaries.

    Args:
        hourly_hist: Hourly OHLC data (used to find 4h boundaries)
        current_time: Current time in UTC

    Returns:
        4-hourly open price or None
    """
    candle_4h_time = get_candle_open_time(current_time, 240)
    four_hourly_data = hourly_hist[hourly_hist.index >= candle_4h_time]

    if not four_hourly_data.empty:
        return four_hourly_data['Open'].iloc[0]

    # Fallback: find nearest candle
    nearby_data = hourly_hist[hourly_hist.index <= candle_4h_time]
    if not nearby_data.empty:
        return nearby_data['Open'].iloc[-1]

    return None


def calculate_30min_open(minute_hist: pd.DataFrame, current_time: datetime) -> Optional[float]:
    """
    Calculate 30-Minute Open (current 30-minute candle opening price)

    Uses 1-minute OHLC data to find the opening price at 30-minute boundaries
    (XX:00 or XX:30 NY time). This leverages granular 1m data to locate precise
    timeframe boundaries.

    Args:
        minute_hist: 1-minute OHLC data (used to find 30m boundaries)
        current_time: Current time in UTC

    Returns:
        30-minute open price or None
    """
    candle_30m_time = get_candle_open_time(current_time, 30)
    thirty_min_data = minute_hist[minute_hist.index >= candle_30m_time]

    if not thirty_min_data.empty:
        return thirty_min_data['Open'].iloc[0]

    # Fallback: find nearest candle
    nearby_data = minute_hist[minute_hist.index <= candle_30m_time]
    if not nearby_data.empty:
        return nearby_data['Open'].iloc[-1]

    return None


def calculate_weekly_open(hourly_hist: pd.DataFrame, current_time: datetime) -> Optional[float]:
    """
    Calculate Weekly Open (Monday 00:00 UTC this week)

    Args:
        hourly_hist: Hourly OHLC data
        current_time: Current time in UTC

    Returns:
        Weekly open price or None
    """
    week_start = get_week_start(current_time)
    weekly_open_data = hourly_hist[hourly_hist.index >= week_start]

    if not weekly_open_data.empty:
        return weekly_open_data['Open'].iloc[0]
    return None


def calculate_monthly_open(hourly_hist: pd.DataFrame, current_time: datetime) -> Optional[float]:
    """
    Calculate Monthly Open (1st of month 00:00 UTC)

    Args:
        hourly_hist: Hourly OHLC data
        current_time: Current time in UTC

    Returns:
        Monthly open price or None
    """
    month_start = get_month_start(current_time)
    monthly_open_data = hourly_hist[hourly_hist.index >= month_start]

    if not monthly_open_data.empty:
        return monthly_open_data['Open'].iloc[0]
    return None


def calculate_prev_week_open(hourly_hist: pd.DataFrame, current_time: datetime) -> Optional[float]:
    """
    Calculate Previous Week Open (Previous Monday 00:00 UTC)

    Args:
        hourly_hist: Hourly OHLC data
        current_time: Current time in UTC

    Returns:
        Previous week open price or None
    """
    week_start = get_week_start(current_time)
    prev_week_start = week_start - timedelta(days=7)
    prev_week_data = hourly_hist[(hourly_hist.index >= prev_week_start) & (hourly_hist.index < week_start)]

    if not prev_week_data.empty:
        return prev_week_data['Open'].iloc[0]
    return None


def calculate_prev_day_high_low(daily_hist: pd.DataFrame) -> tuple[Optional[float], Optional[float]]:
    """
    Calculate Previous Day High and Low

    Args:
        daily_hist: Daily OHLC data

    Returns:
        Tuple of (prev_day_high, prev_day_low)
    """
    if len(daily_hist) >= 2:
        prev_day = daily_hist.iloc[-2]
        return prev_day['High'], prev_day['Low']
    return None, None


def calculate_7am_open(hourly_hist: pd.DataFrame, current_time: datetime) -> Optional[float]:
    """
    Calculate 7:00am NY Open (captured at 8:50am for the day's prediction)

    Args:
        hourly_hist: Hourly OHLC data
        current_time: Current time in UTC

    Returns:
        7:00am NY open price or None
    """
    seven_am_utc = get_7am_ny_timestamp(current_time)
    seven_am_data = hourly_hist[hourly_hist.index >= seven_am_utc]

    if not seven_am_data.empty:
        return seven_am_data['Open'].iloc[0]

    # Fallback: find nearest candle before/at 7am
    nearby_data = hourly_hist[hourly_hist.index <= seven_am_utc]
    if not nearby_data.empty:
        logger.warning("7am open not available, using previous candle close as fallback")
        return nearby_data['Close'].iloc[-1]  # Use close of previous candle as proxy

    logger.warning("7am open not available, no historical data found")
    return None


def calculate_830am_open(
    hourly_hist: pd.DataFrame,
    minute_hist: pd.DataFrame,
    current_time: datetime
) -> Optional[float]:
    """
    Calculate 8:30am NY Open (captured at 8:50am for the day's prediction)

    Note: 8:30am is a 30-minute candle boundary. We need to find the open price
    at exactly 8:30am NY time. May need to use minute data if hourly is insufficient.

    Args:
        hourly_hist: Hourly OHLC data
        minute_hist: Minute OHLC data (for precise 8:30am)
        current_time: Current time in UTC

    Returns:
        8:30am NY open price or None
    """
    eight_thirty_am_utc = get_830am_ny_timestamp(current_time)

    # First try: Look for exact 8:30am candle in minute data
    if not minute_hist.empty:
        minute_data_at_830 = minute_hist[minute_hist.index >= eight_thirty_am_utc]
        if not minute_data_at_830.empty:
            return minute_data_at_830['Open'].iloc[0]

        # Fallback: Use close of previous minute candle
        minute_before_830 = minute_hist[minute_hist.index <= eight_thirty_am_utc]
        if not minute_before_830.empty:
            return minute_before_830['Close'].iloc[-1]

    # Second try: Use hourly data (8am-9am candle open or interpolation)
    eight_am_utc = get_7am_ny_timestamp(current_time).replace(hour=eight_thirty_am_utc.hour)
    hourly_data_at_8 = hourly_hist[hourly_hist.index >= eight_am_utc]
    if not hourly_data_at_8.empty:
        # If we're in the 8am hour, use the hourly open as approximation
        logger.warning("8:30am open not available, using 8am hourly open as fallback")
        return hourly_data_at_8['Open'].iloc[0]

    logger.warning("8:30am open not available, no historical data found")
    return None


def calculate_previous_hourly_open(hourly_hist: pd.DataFrame, current_time: datetime) -> Optional[float]:
    """
    Calculate Previous Hourly Open (opening price of the previous hour's candle)

    Args:
        hourly_hist: Hourly OHLC data
        current_time: Current time in UTC

    Returns:
        Previous hourly open price or None
    """
    # Get current hour candle start time
    current_candle_time = get_candle_open_time(current_time, 60)

    # Go back 1 hour to get previous hour's candle
    previous_hour_time = current_candle_time - timedelta(hours=1)

    # Find the candle that opened at previous_hour_time
    previous_hour_data = hourly_hist[
        (hourly_hist.index >= previous_hour_time) &
        (hourly_hist.index < current_candle_time)
    ]

    if not previous_hour_data.empty:
        return previous_hour_data['Open'].iloc[0]

    # Fallback: find nearest candle before previous hour
    nearby_data = hourly_hist[hourly_hist.index <= previous_hour_time]
    if not nearby_data.empty:
        return nearby_data['Open'].iloc[-1]

    return None


def calculate_range_0700_0715(minute_hist: pd.DataFrame, current_time: datetime) -> Optional[RangeLevel]:
    """
    Calculate 7:00-7:15 AM NY time range (high and low during this 15-minute window)

    Args:
        minute_hist: Minute OHLC data
        current_time: Current time in UTC

    Returns:
        RangeLevel with high/low or None
    """
    # Get 7:00 AM NY timestamp
    seven_am_utc = get_7am_ny_timestamp(current_time)
    seven_fifteen_utc = seven_am_utc + timedelta(minutes=15)

    # Get data within the 7:00-7:15 range
    range_data = minute_hist[
        (minute_hist.index >= seven_am_utc) &
        (minute_hist.index < seven_fifteen_utc)
    ]

    if not range_data.empty:
        range_high = range_data['High'].max()
        range_low = range_data['Low'].min()
        return RangeLevel(high=range_high, low=range_low)

    return None


def calculate_range_0830_0845(minute_hist: pd.DataFrame, current_time: datetime) -> Optional[RangeLevel]:
    """
    Calculate 8:30-8:45 AM NY time range (high and low during this 15-minute window)

    Args:
        minute_hist: Minute OHLC data
        current_time: Current time in UTC

    Returns:
        RangeLevel with high/low or None
    """
    # Get 8:30 AM NY timestamp
    eight_thirty_utc = get_830am_ny_timestamp(current_time)
    eight_fortyfive_utc = eight_thirty_utc + timedelta(minutes=15)

    # Get data within the 8:30-8:45 range
    range_data = minute_hist[
        (minute_hist.index >= eight_thirty_utc) &
        (minute_hist.index < eight_fortyfive_utc)
    ]

    if not range_data.empty:
        range_high = range_data['High'].max()
        range_low = range_data['Low'].min()
        return RangeLevel(high=range_high, low=range_low)

    return None


def calculate_asian_killzone(
    hourly_hist: pd.DataFrame,
    minute_hist: pd.DataFrame,
    current_time: datetime
) -> Optional[RangeLevel]:
    """
    Calculate Asian Kill Zone range (01:00-05:00 UTC high and low)
    Only shows after the session has ended.

    Args:
        hourly_hist: Hourly OHLC data
        minute_hist: Minute OHLC data
        current_time: Current time in UTC

    Returns:
        RangeLevel with high/low or None
    """
    session_config = ICT_SESSIONS['asia']
    start_hour = session_config['start_hour']
    end_hour = session_config['end_hour']

    # Create session start/end times for current day
    session_start = current_time.replace(hour=start_hour, minute=0, second=0, microsecond=0)
    session_end = current_time.replace(hour=end_hour, minute=0, second=0, microsecond=0)

    # Only show kill zone after the session has ended
    if current_time < session_end:
        return None

    # If current time is before session end, use previous day's session
    if current_time.hour < end_hour:
        session_start -= timedelta(days=1)
        session_end -= timedelta(days=1)

    # Try minute data first for more precision
    if not minute_hist.empty:
        range_data = minute_hist[
            (minute_hist.index >= session_start) &
            (minute_hist.index < session_end)
        ]
        if not range_data.empty:
            return RangeLevel(high=range_data['High'].max(), low=range_data['Low'].min())

    # Fallback to hourly data
    range_data = hourly_hist[
        (hourly_hist.index >= session_start) &
        (hourly_hist.index < session_end)
    ]

    if not range_data.empty:
        return RangeLevel(high=range_data['High'].max(), low=range_data['Low'].min())

    return None


def calculate_london_killzone(
    hourly_hist: pd.DataFrame,
    minute_hist: pd.DataFrame,
    current_time: datetime
) -> Optional[RangeLevel]:
    """
    Calculate London Kill Zone range (07:00-10:00 UTC high and low)
    Only shows after the session has ended.

    Args:
        hourly_hist: Hourly OHLC data
        minute_hist: Minute OHLC data
        current_time: Current time in UTC

    Returns:
        RangeLevel with high/low or None
    """
    session_config = ICT_SESSIONS['london']
    start_hour = session_config['start_hour']
    end_hour = session_config['end_hour']

    # Create session start/end times for current day
    session_start = current_time.replace(hour=start_hour, minute=0, second=0, microsecond=0)
    session_end = current_time.replace(hour=end_hour, minute=0, second=0, microsecond=0)

    # Only show kill zone after the session has ended
    if current_time < session_end:
        return None

    # If current time is before session end, use previous day's session
    if current_time.hour < end_hour:
        session_start -= timedelta(days=1)
        session_end -= timedelta(days=1)

    # Try minute data first for more precision
    if not minute_hist.empty:
        range_data = minute_hist[
            (minute_hist.index >= session_start) &
            (minute_hist.index < session_end)
        ]
        if not range_data.empty:
            return RangeLevel(high=range_data['High'].max(), low=range_data['Low'].min())

    # Fallback to hourly data
    range_data = hourly_hist[
        (hourly_hist.index >= session_start) &
        (hourly_hist.index < session_end)
    ]

    if not range_data.empty:
        return RangeLevel(high=range_data['High'].max(), low=range_data['Low'].min())

    return None


def calculate_ny_am_killzone(
    hourly_hist: pd.DataFrame,
    minute_hist: pd.DataFrame,
    current_time: datetime
) -> Optional[RangeLevel]:
    """
    Calculate NY AM Kill Zone range (13:30-16:00 UTC high and low)
    Only shows after the session has ended.

    Args:
        hourly_hist: Hourly OHLC data
        minute_hist: Minute OHLC data
        current_time: Current time in UTC

    Returns:
        RangeLevel with high/low or None
    """
    session_config = ICT_SESSIONS['ny']
    start_hour = session_config['start_hour']
    start_minute = session_config['start_minute']
    end_hour = session_config['end_hour']

    # Create session start/end times for current day
    session_start = current_time.replace(hour=start_hour, minute=start_minute, second=0, microsecond=0)
    session_end = current_time.replace(hour=end_hour, minute=0, second=0, microsecond=0)

    # Only show kill zone after the session has ended
    if current_time < session_end:
        return None

    # If current time is before session end, use previous day's session
    if current_time.hour < end_hour or (current_time.hour == start_hour and current_time.minute < start_minute):
        session_start -= timedelta(days=1)
        session_end -= timedelta(days=1)

    # Try minute data first for more precision
    if not minute_hist.empty:
        range_data = minute_hist[
            (minute_hist.index >= session_start) &
            (minute_hist.index < session_end)
        ]
        if not range_data.empty:
            return RangeLevel(high=range_data['High'].max(), low=range_data['Low'].min())

    # Fallback to hourly data
    range_data = hourly_hist[
        (hourly_hist.index >= session_start) &
        (hourly_hist.index < session_end)
    ]

    if not range_data.empty:
        return RangeLevel(high=range_data['High'].max(), low=range_data['Low'].min())

    return None


def calculate_ny_pm_killzone(
    hourly_hist: pd.DataFrame,
    minute_hist: pd.DataFrame,
    current_time: datetime
) -> Optional[RangeLevel]:
    """
    Calculate NY PM Kill Zone range (17:30-20:00 UTC / 1:30PM-4:00PM ET high and low)
    Only shows after the session has ended.

    Args:
        hourly_hist: Hourly OHLC data
        minute_hist: Minute OHLC data
        current_time: Current time in UTC

    Returns:
        RangeLevel with high/low or None
    """
    session_config = ICT_SESSIONS['ny_pm']
    start_hour = session_config['start_hour']
    start_minute = session_config['start_minute']
    end_hour = session_config['end_hour']

    # Create session start/end times for current day
    session_start = current_time.replace(hour=start_hour, minute=start_minute, second=0, microsecond=0)
    session_end = current_time.replace(hour=end_hour, minute=0, second=0, microsecond=0)

    # Only show kill zone after the session has ended
    if current_time < session_end:
        return None

    # If current time is before session end, use previous day's session
    if current_time.hour < end_hour or (current_time.hour == start_hour and current_time.minute < start_minute):
        session_start -= timedelta(days=1)
        session_end -= timedelta(days=1)

    # Try minute data first for more precision
    if not minute_hist.empty:
        range_data = minute_hist[
            (minute_hist.index >= session_start) &
            (minute_hist.index < session_end)
        ]
        if not range_data.empty:
            return RangeLevel(high=range_data['High'].max(), low=range_data['Low'].min())

    # Fallback to hourly data
    range_data = hourly_hist[
        (hourly_hist.index >= session_start) &
        (hourly_hist.index < session_end)
    ]

    if not range_data.empty:
        return RangeLevel(high=range_data['High'].max(), low=range_data['Low'].min())

    return None


def calculate_all_reference_levels(
    hourly_hist: pd.DataFrame,
    minute_hist: pd.DataFrame,
    daily_hist: pd.DataFrame,
    current_time: datetime
) -> ReferenceLevels:
    """
    Calculate all reference levels for a ticker

    This function calculates 18 reference price levels used as weights in the prediction model.

    Data usage strategy:
    - 1-minute data: Used for precise timeframe boundaries (30m, 7am-7:15am, 8:30am-8:45am ranges)
    - Hourly data: Used for daily open, hourly open, 4-hour open, week/month opens, kill zones
    - Daily data: Used for previous day high/low
    - 30-minute data: NOT used for reference levels, but kept for intraday prediction model

    Args:
        hourly_hist: Hourly OHLC data (for daily/hourly/4h opens and kill zones)
        minute_hist: Minute OHLC data (for precise 30m/15m boundaries)
        daily_hist: Daily OHLC data (for previous day high/low)
        current_time: Current time in UTC

    Returns:
        ReferenceLevels object with all calculated levels
    """
    # Ensure current_time is in UTC
    current_time = ensure_utc(current_time)

    # Calculate previous day high/low
    prev_day_high, prev_day_low = calculate_prev_day_high_low(daily_hist)

    # Calculate all reference levels (18-level system)
    return ReferenceLevels(
        # Existing 11 reference levels (backward compatible)
        daily_open=calculate_daily_open(hourly_hist, current_time),
        hourly_open=calculate_hourly_open(hourly_hist, current_time),
        four_hourly_open=calculate_4hourly_open(hourly_hist, current_time),
        prev_day_high=prev_day_high,
        prev_day_low=prev_day_low,
        prev_week_open=calculate_prev_week_open(hourly_hist, current_time),
        thirty_min_open=calculate_30min_open(minute_hist, current_time),
        weekly_open=calculate_weekly_open(hourly_hist, current_time),
        monthly_open=calculate_monthly_open(hourly_hist, current_time),
        seven_am_open=calculate_7am_open(hourly_hist, current_time),
        eight_thirty_am_open=calculate_830am_open(hourly_hist, minute_hist, current_time),
        # NEW: 7 additional reference levels (including NY PM Kill Zone)
        previous_hourly_open=calculate_previous_hourly_open(hourly_hist, current_time),
        previous_day_high=prev_day_high,  # Consistent naming
        previous_day_low=prev_day_low,    # Consistent naming
        range_0700_0715=calculate_range_0700_0715(minute_hist, current_time),
        range_0830_0845=calculate_range_0830_0845(minute_hist, current_time),
        asian_kill_zone=calculate_asian_killzone(hourly_hist, minute_hist, current_time),
        london_kill_zone=calculate_london_killzone(hourly_hist, minute_hist, current_time),
        ny_am_kill_zone=calculate_ny_am_killzone(hourly_hist, minute_hist, current_time),
        ny_pm_kill_zone=calculate_ny_pm_killzone(hourly_hist, minute_hist, current_time)
    )


def get_hourly_movement(
    hourly_hist: pd.DataFrame,
    current_time: datetime,
    midnight_open: Optional[float]
) -> List[Dict[str, Any]]:
    """
    Calculate today's hourly price movement from midnight ET to now

    Args:
        hourly_hist: Hourly OHLC data
        current_time: Current time in UTC
        midnight_open: Midnight open price

    Returns:
        List of dictionaries with hourly movement data
    """
    et_midnight_utc = get_et_midnight(current_time)
    today_hourly_data = hourly_hist[hourly_hist.index >= et_midnight_utc]

    hourly_movement = []
    if not today_hourly_data.empty:
        for idx, row in today_hourly_data.iterrows():
            hourly_movement.append({
                'time': idx.strftime('%H:%M UTC'),
                'open': row['Open'],
                'high': row['High'],
                'low': row['Low'],
                'close': row['Close'],
                'change_from_midnight': row['Close'] - midnight_open if midnight_open else 0
            })

    return hourly_movement


def get_ny_open(hourly_hist: pd.DataFrame, current_time: datetime) -> Optional[float]:
    """
    Calculate NY 9:30 AM Open (13:30 UTC / 9:30 AM ET)

    Args:
        hourly_hist: Hourly OHLC data
        current_time: Current time in UTC

    Returns:
        NY open price or None
    """
    ny_open_time = current_time.replace(hour=13, minute=30, second=0, microsecond=0)
    ny_open_data = hourly_hist[hourly_hist.index >= ny_open_time]

    if not ny_open_data.empty:
        return ny_open_data['Open'].iloc[0]
    return None
