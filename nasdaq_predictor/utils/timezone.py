"""
Timezone utilities for handling market time conversions
"""
from datetime import datetime, timedelta
import pytz


def ensure_utc(timestamp: datetime) -> datetime:
    """
    Ensure timestamp is in UTC timezone

    Args:
        timestamp: Datetime object

    Returns:
        Datetime object in UTC timezone
    """
    if timestamp.tzinfo is None:
        return pytz.UTC.localize(timestamp)
    return timestamp.astimezone(pytz.UTC)


def get_et_midnight(current_time_utc: datetime) -> datetime:
    """
    Get midnight ET for the current day with proper DST handling

    Args:
        current_time_utc: Current time in UTC

    Returns:
        Midnight ET converted to UTC
    """
    eastern = pytz.timezone('US/Eastern')
    current_time_et = current_time_utc.astimezone(eastern)

    # Get midnight ET for current day
    et_midnight_naive = current_time_et.replace(hour=0, minute=0, second=0, microsecond=0)
    et_midnight = eastern.normalize(eastern.localize(et_midnight_naive.replace(tzinfo=None)))
    et_midnight_utc = et_midnight.astimezone(pytz.UTC)

    return et_midnight_utc


def get_candle_open_time(current_time: datetime, interval_minutes: int) -> datetime:
    """
    Calculate the opening time of the current candle based on clock timing

    Args:
        current_time: datetime object in UTC
        interval_minutes: candle interval in minutes (3, 5, 30, 60, 240)

    Returns:
        datetime object representing the candle open time

    Example:
        If current_time is 14:37 and interval is 5 minutes:
        Returns 14:35 (the start of the 14:35-14:40 candle)
    """
    if interval_minutes == 240:  # 4-hourly
        candle_hour = (current_time.hour // 4) * 4
        return current_time.replace(hour=candle_hour, minute=0, second=0, microsecond=0)
    elif interval_minutes == 60:  # Hourly
        return current_time.replace(minute=0, second=0, microsecond=0)
    else:  # 3, 5, 30 minutes
        candle_minute = (current_time.minute // interval_minutes) * interval_minutes
        return current_time.replace(minute=candle_minute, second=0, microsecond=0)


def get_week_start(current_time: datetime) -> datetime:
    """
    Get the start of the current week (Monday 00:00 UTC)

    Args:
        current_time: Current time in UTC

    Returns:
        Start of week in UTC
    """
    days_since_monday = current_time.weekday()
    week_start = (current_time - timedelta(days=days_since_monday)).replace(
        hour=0, minute=0, second=0, microsecond=0
    )
    return week_start


def get_month_start(current_time: datetime) -> datetime:
    """
    Get the start of the current month (1st of month 00:00 UTC)

    Args:
        current_time: Current time in UTC

    Returns:
        Start of month in UTC
    """
    return current_time.replace(day=1, hour=0, minute=0, second=0, microsecond=0)


def get_ny_time(utc_time: datetime) -> datetime:
    """
    Convert UTC time to NY Eastern Time (handles DST automatically)

    Args:
        utc_time: Datetime object in UTC

    Returns:
        Datetime object in US/Eastern timezone
    """
    utc_time = ensure_utc(utc_time)
    eastern = pytz.timezone('US/Eastern')
    return utc_time.astimezone(eastern)


def get_ny_hour_timestamp(date: datetime, hour: int, minute: int = 0) -> datetime:
    """
    Get UTC timestamp for a specific NY time on a given date

    Args:
        date: Date (in any timezone)
        hour: Hour in NY time (0-23)
        minute: Minute in NY time (0-59)

    Returns:
        UTC timestamp for that NY time
    """
    eastern = pytz.timezone('US/Eastern')

    # Convert input to NY timezone
    ny_date = date.astimezone(eastern) if date.tzinfo else eastern.localize(date)

    # Create target time in NY
    ny_time = ny_date.replace(hour=hour, minute=minute, second=0, microsecond=0)
    ny_time = eastern.normalize(ny_time)

    # Convert to UTC
    return ny_time.astimezone(pytz.UTC)


def get_7am_ny_timestamp(current_time_utc: datetime) -> datetime:
    """
    Get 7:00am NY timestamp for the current day

    Args:
        current_time_utc: Current time in UTC

    Returns:
        7:00am NY time converted to UTC
    """
    return get_ny_hour_timestamp(current_time_utc, hour=7, minute=0)


def get_830am_ny_timestamp(current_time_utc: datetime) -> datetime:
    """
    Get 8:30am NY timestamp for the current day

    Args:
        current_time_utc: Current time in UTC

    Returns:
        8:30am NY time converted to UTC
    """
    return get_ny_hour_timestamp(current_time_utc, hour=8, minute=30)


def get_london_time(utc_time: datetime) -> datetime:
    """
    Convert UTC time to London time (handles GMT/BST automatically)

    Args:
        utc_time: Datetime object in UTC

    Returns:
        Datetime object in Europe/London timezone
    """
    utc_time = ensure_utc(utc_time)
    london = pytz.timezone('Europe/London')
    return utc_time.astimezone(london)


def get_london_hour_timestamp(date: datetime, hour: int, minute: int = 0) -> datetime:
    """
    Get UTC timestamp for a specific London time on a given date

    Args:
        date: Date (in any timezone)
        hour: Hour in London time (0-23)
        minute: Minute in London time (0-59)

    Returns:
        UTC timestamp for that London time
    """
    london = pytz.timezone('Europe/London')

    # Convert input to London timezone
    london_date = date.astimezone(london) if date.tzinfo else london.localize(date)

    # Create target time in London
    london_time = london_date.replace(hour=hour, minute=minute, second=0, microsecond=0)
    london_time = london.normalize(london_time)

    # Convert to UTC
    return london_time.astimezone(pytz.UTC)


def get_ticker_time(utc_time: datetime, ticker_symbol: str) -> datetime:
    """
    Convert UTC time to the appropriate timezone for a given ticker

    Args:
        utc_time: Datetime object in UTC
        ticker_symbol: Ticker symbol (e.g., 'NQ=F', '^FTSE')

    Returns:
        Datetime object in the appropriate timezone
    """
    if ticker_symbol == '^FTSE':
        return get_london_time(utc_time)
    else:
        # Default to NY time for US futures, indices, and crypto
        return get_ny_time(utc_time)


def get_ticker_hour_timestamp(date: datetime, hour: int, minute: int, ticker_symbol: str) -> datetime:
    """
    Get UTC timestamp for a specific hour in the ticker's local timezone

    Args:
        date: Date (in any timezone)
        hour: Hour in ticker's local time (0-23)
        minute: Minute in ticker's local time (0-59)
        ticker_symbol: Ticker symbol (e.g., 'NQ=F', '^FTSE')

    Returns:
        UTC timestamp for that local time
    """
    if ticker_symbol == '^FTSE':
        return get_london_hour_timestamp(date, hour, minute)
    else:
        # Default to NY time for US futures, indices, and crypto
        return get_ny_hour_timestamp(date, hour, minute)


def get_current_prediction_window(current_time_utc: datetime, ticker_symbol: str = 'NQ=F') -> str:
    """
    Determine which prediction time window we're currently in

    Args:
        current_time_utc: Current time in UTC
        ticker_symbol: Ticker symbol (defaults to 'NQ=F' for backward compatibility)

    Returns:
        Time window identifier:
        - 'pre_9am': Before 9:00am local (12am-8:59am)
        - '9am_hour': 9:00am-9:59am local
        - '10am_hour': 10:00am-10:59am local
        - 'post_10am': 11:00am-6:59pm local
        - 'evening': 7:00pm-11:59pm local
    """
    local_time = get_ticker_time(current_time_utc, ticker_symbol)
    hour = local_time.hour

    if hour < 9:
        return 'pre_9am'
    elif hour == 9:
        return '9am_hour'
    elif hour == 10:
        return '10am_hour'
    elif 11 <= hour < 19:  # 11am to 6:59pm
        return 'post_10am'
    else:  # 7pm to 11:59pm
        return 'evening'


def format_time_until(target_time: datetime, current_time: datetime) -> str:
    """
    Format time difference as human-readable string

    Args:
        target_time: Target datetime
        current_time: Current datetime

    Returns:
        Formatted string like "2h 30m" or "15m" or "PASSED"
    """
    if target_time <= current_time:
        return "PASSED"

    delta = target_time - current_time
    hours = int(delta.total_seconds() // 3600)
    minutes = int((delta.total_seconds() % 3600) // 60)

    if hours > 0:
        return f"{hours}h {minutes}m"
    else:
        return f"{minutes}m"
