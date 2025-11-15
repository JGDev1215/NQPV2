"""
Market status utilities for determining if markets are open
"""
from datetime import datetime
import pytz
import logging
from typing import Dict, Optional

from ..models.market_data import MarketStatus

logger = logging.getLogger(__name__)


def get_market_status(ticker_symbol: str, current_time: datetime) -> MarketStatus:
    """
    Determine if the market is open, closed, pre-market, or after-hours

    Args:
        ticker_symbol: The ticker to check
        current_time: Current timestamp in UTC

    Returns:
        MarketStatus object with status and next_open time (if closed)
    """
    try:
        # Convert to US Eastern Time
        eastern = pytz.timezone('US/Eastern')
        current_time_et = current_time.astimezone(eastern)

        # Get current day of week (0=Monday, 6=Sunday)
        weekday = current_time_et.weekday()
        current_hour = current_time_et.hour
        current_minute = current_time_et.minute
        current_time_minutes = current_hour * 60 + current_minute

        # Market hours in ET (in minutes from midnight)
        pre_market_start = 4 * 60  # 4:00 AM
        market_open = 9 * 60 + 30   # 9:30 AM
        market_close = 16 * 60      # 4:00 PM
        after_hours_end = 20 * 60   # 8:00 PM

        if ticker_symbol in ['NQ=F', 'ES=F']:
            # Futures (NQ=F, ES=F): Sunday 6:00 PM - Friday 5:00 PM ET (nearly 24/5)
            # Closed: Friday 5:00 PM - Sunday 6:00 PM

            if weekday == 4 and current_time_minutes >= 17 * 60:  # Friday after 5:00 PM
                return MarketStatus(
                    status='CLOSED',
                    next_open='Sunday 6:00 PM ET'
                )
            elif weekday == 5:  # Saturday (all day closed)
                return MarketStatus(
                    status='CLOSED',
                    next_open='Sunday 6:00 PM ET'
                )
            elif weekday == 6 and current_time_minutes < 18 * 60:  # Sunday before 6:00 PM
                return MarketStatus(
                    status='CLOSED',
                    next_open='Sunday 6:00 PM ET'
                )
            else:
                return MarketStatus(
                    status='OPEN',
                    next_open=None
                )

        elif ticker_symbol in ['BTC-USD', 'SOL-USD', 'ADA-USD']:
            # Cryptocurrency trades 24/7
            return MarketStatus(
                status='OPEN (24/7)',
                next_open=None
            )

        elif ticker_symbol == '^FTSE':
            # FTSE 100: 8:00 AM - 4:30 PM London time (GMT/BST)
            # Using London timezone for accurate market hours
            london = pytz.timezone('Europe/London')
            current_time_london = current_time.astimezone(london)

            # Get current day and time
            weekday = current_time_london.weekday()
            current_hour = current_time_london.hour
            current_minute = current_time_london.minute
            current_time_minutes = current_hour * 60 + current_minute

            # Market hours in London time (in minutes from midnight)
            market_open = 8 * 60           # 8:00 AM
            market_close = 16 * 60 + 30    # 4:30 PM

            # Check if weekend
            if weekday >= 5:  # Saturday (5) or Sunday (6)
                return MarketStatus(
                    status='CLOSED',
                    next_open='Monday 8:00 AM GMT'
                )

            # Check if before market open
            if current_time_minutes < market_open:
                return MarketStatus(
                    status='CLOSED',
                    next_open='Today 8:00 AM GMT'
                )

            # Check if after market close
            if current_time_minutes >= market_close:
                next_day = 'Monday' if weekday == 4 else 'Tomorrow'  # Friday -> Monday
                return MarketStatus(
                    status='CLOSED',
                    next_open=f'{next_day} 8:00 AM GMT'
                )

            # Market is open
            return MarketStatus(
                status='OPEN',
                next_open=None
            )

        else:
            return MarketStatus(
                status='UNKNOWN',
                next_open=None
            )

    except Exception as e:
        logger.error(f"Error determining market status for {ticker_symbol}: {str(e)}", exc_info=True)
        return MarketStatus(
            status='UNKNOWN',
            next_open=None
        )


def is_within_trading_session(timestamp: datetime, ticker_symbol: str, trading_sessions: Dict) -> bool:
    """
    Check if a timestamp falls within the trading session for a given ticker

    Args:
        timestamp: Timestamp to check
        ticker_symbol: Ticker symbol
        trading_sessions: Trading session configuration dict

    Returns:
        True if within trading session, False otherwise
    """
    if ticker_symbol not in trading_sessions:
        return True  # If no session defined, include all data

    session = trading_sessions[ticker_symbol]

    # Convert timestamp to UTC if not already
    if timestamp.tzinfo is None:
        timestamp = pytz.UTC.localize(timestamp)
    else:
        timestamp = timestamp.astimezone(pytz.UTC)

    hour = timestamp.hour + timestamp.minute / 60.0

    # Crypto trades 24/7 - no filtering
    if session['type'] == 'crypto':
        return True

    if session['type'] == 'futures' and not session['uses_main_only']:
        # Futures trade nearly 24/7, exclude only the 1-hour maintenance break (21:00-22:00 UTC)
        # Also exclude weekends (Saturday 21:00 to Sunday 22:00)
        if timestamp.weekday() == 5:  # Saturday
            return hour < 21.0
        elif timestamp.weekday() == 6:  # Sunday
            return hour >= 22.0
        else:
            return not (21.0 <= hour < 22.0)
    else:
        # Cash index or main session only
        # Exclude weekends entirely
        if timestamp.weekday() >= 5:  # Saturday or Sunday
            return False
        return session['main_session_start'] <= hour <= session['main_session_end']
