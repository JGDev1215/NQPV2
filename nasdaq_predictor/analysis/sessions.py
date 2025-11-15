"""
ICT Killzone session range analysis
"""
import logging
from datetime import datetime
from typing import Optional, Dict, Any
import pandas as pd

from ..models.market_data import SessionRange
from ..data.fetcher import YahooFinanceDataFetcher

logger = logging.getLogger(__name__)


def get_session_range(
    ticker_symbol: str,
    session_start_hour: int,
    session_start_minute: int,
    session_end_hour: int,
    session_end_minute: int,
    current_time: datetime,
    fetcher: Optional[YahooFinanceDataFetcher] = None,
    only_show_after_end: bool = False
) -> Optional[SessionRange]:
    """
    Calculate the HIGH and LOW range for a specific trading session from start until current time (live range)
    Based on ICT Killzone methodology - "Live Trading Hours Until To Close"

    Args:
        ticker_symbol: The ticker to analyze
        session_start_hour: Start hour in UTC (0-23)
        session_start_minute: Start minute (0-59)
        session_end_hour: End hour in UTC (0-23)
        session_end_minute: End minute (0-59)
        current_time: Current timestamp in UTC
        fetcher: Optional YahooFinanceDataFetcher instance
        only_show_after_end: If True, only return data after session has ended (for kill zones)

    Returns:
        SessionRange object with high, low, and range, or None if data unavailable
    """
    try:
        if fetcher is None:
            fetcher = YahooFinanceDataFetcher()

        # Get today's date in UTC
        today_start = current_time.replace(hour=0, minute=0, second=0, microsecond=0)

        # Define session start and end times
        session_start = today_start.replace(hour=session_start_hour, minute=session_start_minute)
        session_end = today_start.replace(hour=session_end_hour, minute=session_end_minute)

        # NEW: If only_show_after_end is True, check if current time is after session end
        # This ensures kill zones only display after the session has finished
        if only_show_after_end and current_time < session_end:
            return None

        # Fetch intraday data (5-minute intervals for better granularity)
        hist = fetcher.fetch_intraday_data(ticker_symbol, period='2d', interval='5m')

        if hist is None or hist.empty:
            return None

        # LIVE RANGE: Calculate range from session start to CURRENT TIME (or session end if session is closed)
        # This creates a dynamic range that grows as the session progresses
        range_end_time = min(current_time, session_end)

        # Get data for the session (from start until current time or session end)
        session_data = hist[(hist.index >= session_start) & (hist.index <= range_end_time)]

        if session_data.empty:
            return None

        session_high = session_data['High'].max()
        session_low = session_data['Low'].min()

        return SessionRange(
            high=session_high,
            low=session_low,
            range=session_high - session_low
        )

    except Exception as e:
        logger.error(f"Error calculating session range for {ticker_symbol}: {str(e)}", exc_info=True)
        return None


def analyze_price_vs_range(current_price: float, session_range: Optional[SessionRange]) -> str:
    """
    Determine if current price is above, within, or below the session range

    Args:
        current_price: Current market price
        session_range: SessionRange object or None

    Returns:
        'ABOVE', 'WITHIN', 'BELOW', or 'N/A'
    """
    if session_range is None:
        return 'N/A'

    if current_price > session_range.high:
        return 'ABOVE'
    elif current_price < session_range.low:
        return 'BELOW'
    else:
        return 'WITHIN'


def get_all_session_ranges(
    ticker_symbol: str,
    current_time: datetime,
    current_price: float,
    fetcher: Optional[YahooFinanceDataFetcher] = None
) -> Dict[str, Dict[str, Any]]:
    """
    Calculate all ICT killzone session ranges

    Args:
        ticker_symbol: Ticker symbol
        current_time: Current time in UTC
        current_price: Current market price
        fetcher: Optional YahooFinanceDataFetcher instance

    Returns:
        Dictionary with session ranges for Asia, London, NY AM, and NY PM
    """
    from ..config.settings import ICT_SESSIONS

    if fetcher is None:
        fetcher = YahooFinanceDataFetcher()

    session_ranges = {}

    for session_name, session_config in ICT_SESSIONS.items():
        # Kill zones should only display after the session has ended
        session_range = get_session_range(
            ticker_symbol,
            session_config['start_hour'],
            session_config['start_minute'],
            session_config['end_hour'],
            session_config['end_minute'],
            current_time,
            fetcher,
            only_show_after_end=True  # Only show kill zones after they've ended
        )

        # Convert SessionRange to dict for JSON serialization
        range_dict = None
        if session_range:
            range_dict = {
                'high': session_range.high,
                'low': session_range.low,
                'range': session_range.range
            }

        session_ranges[session_name] = {
            'range': range_dict,
            'position': analyze_price_vs_range(current_price, session_range)
        }

    return session_ranges
