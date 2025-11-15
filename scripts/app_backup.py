import os
import logging
import threading
from typing import Dict, Optional, Any
from flask import Flask, render_template, jsonify
import yfinance as yf
import pandas as pd
from datetime import datetime, timedelta
import pytz
from dotenv import load_dotenv

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

load_dotenv()

app = Flask(__name__)

# Constants
APP_VERSION = '1.0.0'
CACHE_DURATION = 900  # seconds (15 minutes)
ALLOWED_TICKERS = ['NQ=F', '^NDX', '^FTSE']

# Data fetching configuration
HIST_PERIOD_HOURLY = '30d'  # Period for hourly data
HIST_PERIOD_MINUTE = '7d'   # Period for minute data
HIST_INTERVAL_HOURLY = '1h'
HIST_INTERVAL_MINUTE = '1m'

# Normalized weights (sum to 1.0)
WEIGHTS = {
    'daily_open': 0.25,
    'hourly_open': 0.10,
    '4_hourly_open': 0.12,
    'prev_day_high': 0.05,
    'prev_day_low': 0.05,
    'prev_week_open': 0.05,
    '30_min_open': 0.23,
    'weekly_open': 0.10,
    'monthly_open': 0.05
}

# Validate weights sum to 1.0
_weights_sum = sum(WEIGHTS.values())
assert abs(_weights_sum - 1.0) < 0.001, f"Weights must sum to 1.0, got {_weights_sum}"

# Thread-safe cache
class ThreadSafeCache:
    def __init__(self):
        self._cache = {'data': None, 'timestamp': None}
        self._lock = threading.Lock()

    def get(self):
        with self._lock:
            return self._cache['data'], self._cache['timestamp']

    def set(self, data, timestamp):
        with self._lock:
            self._cache['data'] = data
            self._cache['timestamp'] = timestamp

    def is_valid(self, duration):
        with self._lock:
            if self._cache['data'] is None or self._cache['timestamp'] is None:
                return False
            time_diff = (datetime.now() - self._cache['timestamp']).total_seconds()
            return time_diff < duration

cache = ThreadSafeCache()

# Trading session hours (in UTC)
TRADING_SESSIONS = {
    'NQ=F': {
        # NASDAQ-100 Futures trades nearly 24/7 with 1-hour break
        # Main session: 13:30-20:00 UTC (9:30 AM - 4:00 PM ET)
        # Extended: Sunday 22:00 UTC to Friday 21:00 UTC with 21:00-22:00 break
        'type': 'futures',
        'main_session_start': 13.5,  # 13:30 UTC
        'main_session_end': 20.0,     # 20:00 UTC
        'uses_main_only': False       # Uses all trading hours
    },
    '^FTSE': {
        # FTSE 100 cash index: 8:00 AM - 4:30 PM London time
        # In UTC: 8:00-16:30 (GMT) or 7:00-15:30 (BST, summer)
        # Using GMT hours (winter time) for simplicity
        'type': 'cash',
        'main_session_start': 8.0,    # 8:00 UTC
        'main_session_end': 16.5,     # 16:30 UTC
        'uses_main_only': True        # Only trades during main session
    },
    '^NDX': {
        # NASDAQ-100 cash index: 9:30 AM - 4:00 PM ET
        # In UTC: 13:30-20:00 (EST) or 12:30-19:00 (EDT)
        # Using EST hours for consistency
        'type': 'cash',
        'main_session_start': 13.5,   # 13:30 UTC (9:30 AM ET)
        'main_session_end': 20.0,     # 20:00 UTC (4:00 PM ET)
        'uses_main_only': True        # Only trades during main session
    }
}


def is_within_trading_session(timestamp, ticker_symbol):
    """Check if a timestamp falls within the trading session for a given ticker"""
    if ticker_symbol not in TRADING_SESSIONS:
        return True  # If no session defined, include all data

    session = TRADING_SESSIONS[ticker_symbol]

    # Convert timestamp to UTC if not already
    if timestamp.tzinfo is None:
        timestamp = pytz.UTC.localize(timestamp)
    else:
        timestamp = timestamp.astimezone(pytz.UTC)

    hour = timestamp.hour + timestamp.minute / 60.0

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


def filter_trading_session_data(hist, ticker_symbol):
    """Filter historical data to only include trading session hours"""
    if hist.empty:
        return hist

    # Apply trading session filter
    mask = hist.index.map(lambda x: is_within_trading_session(x, ticker_symbol))
    filtered_hist = hist[mask]

    return filtered_hist


def get_candle_open_time(current_time, interval_minutes):
    """
    Calculate the opening time of the current candle based on clock timing.

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


def get_reference_levels(ticker_symbol):
    """Calculate all reference levels for a given ticker"""
    try:
        ticker = yf.Ticker(ticker_symbol)

        # Fetch hourly data
        hist = ticker.history(period=HIST_PERIOD_HOURLY, interval=HIST_INTERVAL_HOURLY)

        if hist.empty:
            return None

        # Filter to only trading session hours
        hist = filter_trading_session_data(hist, ticker_symbol)

        if hist.empty:
            return None

        # Fetch 1-minute data for small timeframe calculations
        hist_1m = ticker.history(period=HIST_PERIOD_MINUTE, interval=HIST_INTERVAL_MINUTE)

        # Filter 1-minute data to trading session hours
        hist_1m = filter_trading_session_data(hist_1m, ticker_symbol)

        # Get current price (most recent close from filtered data)
        current_price = hist['Close'].iloc[-1]
        current_time = hist.index[-1]

        # Convert to UTC if not already
        if current_time.tzinfo is None:
            current_time = pytz.UTC.localize(current_time)
        else:
            current_time = current_time.astimezone(pytz.UTC)

        # Get daily data for previous day high/low
        daily_hist = ticker.history(period='7d', interval='1d')

        # Filter daily data to trading session days
        daily_hist = filter_trading_session_data(daily_hist, ticker_symbol)

        reference_levels = {}

        # Previous Day High/Low
        if len(daily_hist) >= 2:
            prev_day = daily_hist.iloc[-2]
            reference_levels['prev_day_high'] = prev_day['High']
            reference_levels['prev_day_low'] = prev_day['Low']
        else:
            reference_levels['prev_day_high'] = None
            reference_levels['prev_day_low'] = None

        # 30-Minute Open (current 30-minute candle opening price based on clock timing)
        candle_30m_time = get_candle_open_time(current_time, 30)
        thirty_min_data = hist[hist.index >= candle_30m_time]
        if not thirty_min_data.empty:
            reference_levels['30_min_open'] = thirty_min_data['Open'].iloc[0]
        else:
            # Fallback: find nearest candle
            nearby_data = hist[hist.index <= candle_30m_time]
            if not nearby_data.empty:
                reference_levels['30_min_open'] = nearby_data['Open'].iloc[-1]
            else:
                reference_levels['30_min_open'] = None

        # Hourly Open (current hourly candle opening price based on clock timing)
        candle_1h_time = get_candle_open_time(current_time, 60)
        hourly_data = hist[hist.index >= candle_1h_time]
        if not hourly_data.empty:
            reference_levels['hourly_open'] = hourly_data['Open'].iloc[0]
        else:
            # Fallback: find nearest candle
            nearby_data = hist[hist.index <= candle_1h_time]
            if not nearby_data.empty:
                reference_levels['hourly_open'] = nearby_data['Open'].iloc[-1]
            else:
                reference_levels['hourly_open'] = None

        # 4-Hourly Open (current 4-hourly candle opening price based on clock timing)
        candle_4h_time = get_candle_open_time(current_time, 240)
        four_hourly_data = hist[hist.index >= candle_4h_time]
        if not four_hourly_data.empty:
            reference_levels['4_hourly_open'] = four_hourly_data['Open'].iloc[0]
        else:
            # Fallback: find nearest candle
            nearby_data = hist[hist.index <= candle_4h_time]
            if not nearby_data.empty:
                reference_levels['4_hourly_open'] = nearby_data['Open'].iloc[-1]
            else:
                reference_levels['4_hourly_open'] = None

        # Daily Open (Midnight ET with proper DST handling)
        eastern = pytz.timezone('US/Eastern')
        current_time_et = current_time.astimezone(eastern)

        # Get midnight ET for current day
        et_midnight_naive = current_time_et.replace(hour=0, minute=0, second=0, microsecond=0)
        et_midnight = eastern.normalize(eastern.localize(et_midnight_naive.replace(tzinfo=None)))
        et_midnight_utc = et_midnight.astimezone(pytz.UTC)

        daily_open_data = hist[hist.index >= et_midnight_utc]
        if not daily_open_data.empty:
            reference_levels['daily_open'] = daily_open_data['Open'].iloc[0]
        else:
            reference_levels['daily_open'] = None

        # Weekly Open (Monday 00:00 UTC this week)
        days_since_monday = current_time.weekday()
        week_start = (current_time - timedelta(days=days_since_monday)).replace(hour=0, minute=0, second=0, microsecond=0)
        weekly_open_data = hist[hist.index >= week_start]
        if not weekly_open_data.empty:
            reference_levels['weekly_open'] = weekly_open_data['Open'].iloc[0]
        else:
            reference_levels['weekly_open'] = None

        # Monthly Open (1st of month 00:00 UTC)
        month_start = current_time.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
        monthly_open_data = hist[hist.index >= month_start]
        if not monthly_open_data.empty:
            reference_levels['monthly_open'] = monthly_open_data['Open'].iloc[0]
        else:
            reference_levels['monthly_open'] = None

        # Previous Week Open (Previous Monday 00:00 UTC)
        prev_week_start = week_start - timedelta(days=7)
        prev_week_data = hist[(hist.index >= prev_week_start) & (hist.index < week_start)]
        if not prev_week_data.empty:
            reference_levels['prev_week_open'] = prev_week_data['Open'].iloc[0]
        else:
            reference_levels['prev_week_open'] = None

        # Midnight Open (00:00 UTC today) - already calculated as daily_open
        midnight_open = reference_levels.get('daily_open')

        # NY 9:30 AM Open (13:30 UTC / 9:30 AM ET)
        ny_open_time = current_time.replace(hour=13, minute=30, second=0, microsecond=0)
        ny_open_data = hist[hist.index >= ny_open_time]
        ny_open = ny_open_data['Open'].iloc[0] if not ny_open_data.empty else None

        # Today's hourly price movement from midnight ET to now
        # Use the same et_midnight_utc calculated above
        today_hourly_data = hist[hist.index >= et_midnight_utc]

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

        return {
            'current_price': current_price,
            'current_time': current_time,
            'reference_levels': reference_levels,
            'midnight_open': midnight_open,
            'ny_open': ny_open,
            'hourly_movement': hourly_movement  # Still calculated for volatility purposes
        }

    except Exception as e:
        logger.error(f"Error fetching data for {ticker_symbol}: {str(e)}", exc_info=True)
        return None


def get_session_range(ticker_symbol, session_start_hour, session_start_minute, session_end_hour, session_end_minute, current_time):
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

    Returns:
        Dictionary with high, low, and range, or None if data unavailable
    """
    try:
        ticker = yf.Ticker(ticker_symbol)
        # Fetch intraday data (5-minute intervals for better granularity)
        hist = ticker.history(period='2d', interval='5m')

        if hist.empty:
            return None

        # Get today's date in UTC
        today_start = current_time.replace(hour=0, minute=0, second=0, microsecond=0)

        # Define session start and end times
        session_start = today_start.replace(hour=session_start_hour, minute=session_start_minute)
        session_end = today_start.replace(hour=session_end_hour, minute=session_end_minute)

        # LIVE RANGE: Calculate range from session start to CURRENT TIME (or session end if session is closed)
        # This creates a dynamic range that grows as the session progresses
        range_end_time = min(current_time, session_end)

        # Get data for the session (from start until current time or session end)
        session_data = hist[(hist.index >= session_start) & (hist.index <= range_end_time)]

        if session_data.empty:
            return None

        session_high = session_data['High'].max()
        session_low = session_data['Low'].min()

        return {
            'high': session_high,
            'low': session_low,
            'range': session_high - session_low
        }

    except Exception as e:
        logger.error(f"Error calculating session range for {ticker_symbol}: {str(e)}", exc_info=True)
        return None


def analyze_price_vs_range(current_price, session_range):
    """
    Determine if current price is above, within, or below the session range

    Returns:
        'ABOVE', 'WITHIN', or 'BELOW'
    """
    if session_range is None:
        return 'N/A'

    if current_price > session_range['high']:
        return 'ABOVE'
    elif current_price < session_range['low']:
        return 'BELOW'
    else:
        return 'WITHIN'


def get_market_status(ticker_symbol, current_time):
    """
    Determine if the market is open, closed, pre-market, or after-hours

    Args:
        ticker_symbol: The ticker to check
        current_time: Current timestamp in UTC

    Returns:
        Dictionary with status and next_open time (if closed)
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

        if ticker_symbol == 'NQ=F':
            # NQ=F Futures: Sunday 6:00 PM - Friday 5:00 PM ET (nearly 24/5)
            # Closed: Friday 5:00 PM - Sunday 6:00 PM

            if weekday == 4 and current_time_minutes >= 17 * 60:  # Friday after 5:00 PM
                return {
                    'status': 'CLOSED',
                    'next_open': 'Sunday 6:00 PM ET'
                }
            elif weekday == 5:  # Saturday (all day closed)
                return {
                    'status': 'CLOSED',
                    'next_open': 'Sunday 6:00 PM ET'
                }
            elif weekday == 6 and current_time_minutes < 18 * 60:  # Sunday before 6:00 PM
                return {
                    'status': 'CLOSED',
                    'next_open': 'Sunday 6:00 PM ET'
                }
            else:
                return {
                    'status': 'OPEN',
                    'next_open': None
                }

        elif ticker_symbol == '^NDX':
            # NDX Cash Index: NYSE hours 9:30 AM - 4:00 PM ET, Monday-Friday

            # Weekend check
            if weekday >= 5:  # Saturday or Sunday
                return {
                    'status': 'CLOSED',
                    'next_open': 'Monday 9:30 AM ET'
                }

            # Weekday checks
            if current_time_minutes < pre_market_start:
                return {
                    'status': 'CLOSED',
                    'next_open': f'{current_time_et.strftime("%A")} 9:30 AM ET'
                }
            elif pre_market_start <= current_time_minutes < market_open:
                return {
                    'status': 'PRE-MARKET',
                    'next_open': f'{current_time_et.strftime("%A")} 9:30 AM ET'
                }
            elif market_open <= current_time_minutes < market_close:
                return {
                    'status': 'OPEN',
                    'next_open': None
                }
            elif market_close <= current_time_minutes < after_hours_end:
                return {
                    'status': 'AFTER-HOURS',
                    'next_open': 'Next trading day 9:30 AM ET'
                }
            else:
                return {
                    'status': 'CLOSED',
                    'next_open': 'Next trading day 9:30 AM ET'
                }

        else:
            return {
                'status': 'UNKNOWN',
                'next_open': None
            }

    except Exception as e:
        logger.error(f"Error determining market status for {ticker_symbol}: {str(e)}", exc_info=True)
        return {
            'status': 'UNKNOWN',
            'next_open': None
        }


def calculate_signals(current_price, reference_levels):
    """Calculate signals, weighted score, prediction, and confidence"""
    signals = {}
    weighted_score = 0.0
    valid_signals = 0

    for key, ref_level in reference_levels.items():
        if ref_level is not None:
            # Signal = 1 if current price > reference, else 0
            signal = 1 if current_price > ref_level else 0
            distance = current_price - ref_level
            status = 'BULLISH' if signal == 1 else 'BEARISH'

            signals[key] = {
                'signal': signal,
                'reference_level': ref_level,
                'distance': distance,
                'status': status
            }

            # Add to weighted score
            weighted_score += signal * WEIGHTS[key]
            valid_signals += 1
        else:
            signals[key] = {
                'signal': None,
                'reference_level': None,
                'distance': None,
                'status': 'N/A'
            }

    # Calculate prediction and confidence
    prediction = 'BULLISH' if weighted_score >= 0.5 else 'BEARISH'
    confidence = abs((weighted_score - 0.5) / 0.5) * 100

    # Count bullish signals
    bullish_count = sum(1 for s in signals.values() if s['signal'] == 1)

    return {
        'signals': signals,
        'weighted_score': weighted_score,
        'prediction': prediction,
        'confidence': confidence,
        'bullish_count': bullish_count,
        'total_signals': valid_signals
    }


def calculate_confidence_horizons(base_confidence):
    """
    Calculate confidence levels for different time horizons with decay factors

    Args:
        base_confidence: Base confidence from weighted score (0-100%)

    Returns:
        Dictionary with confidence levels for 15min, 1hour, 4hour, 1day
    """
    # Decay factors for different time horizons
    decay_factors = {
        '15min': 0.95,   # Minimal decay - very recent signals
        '1hour': 0.75,   # Moderate decay
        '4hour': 0.50,   # Significant decay
        '1day': 0.35     # High uncertainty over 24 hours
    }

    horizons = {}
    for horizon, factor in decay_factors.items():
        confidence = base_confidence * factor

        # Determine reliability level
        if confidence >= 70:
            level = 'HIGH'
        elif confidence >= 50:
            level = 'MODERATE'
        elif confidence >= 30:
            level = 'LOW'
        else:
            level = 'SPECULATIVE'

        horizons[horizon] = {
            'confidence': round(confidence, 1),
            'level': level
        }

    return horizons


def calculate_volatility(hourly_movement):
    """
    Calculate current volatility from hourly price movements

    Args:
        hourly_movement: List of hourly OHLC data

    Returns:
        Dictionary with volatility metrics
    """
    if not hourly_movement or len(hourly_movement) < 2:
        return {
            'hourly_range_pct': 0,
            'level': 'UNKNOWN'
        }

    # Calculate average hourly range as percentage
    ranges = []
    for candle in hourly_movement:
        if candle['high'] and candle['low'] and candle['open']:
            range_pct = abs((candle['high'] - candle['low']) / candle['open']) * 100
            ranges.append(range_pct)

    if not ranges:
        return {
            'hourly_range_pct': 0,
            'level': 'UNKNOWN'
        }

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

    return {
        'hourly_range_pct': round(avg_range_pct, 2),
        'level': level
    }


def calculate_risk_metrics(current_price, reference_levels, signals_data):
    """
    Calculate risk management metrics including stop loss and flip scenarios

    Args:
        current_price: Current market price
        reference_levels: Dictionary of reference levels
        signals_data: Output from calculate_signals function

    Returns:
        Dictionary with risk metrics
    """
    # Find nearest support level (highest level below current price)
    supports = []
    for key, level in reference_levels.items():
        if level and level < current_price:
            supports.append({
                'level': level,
                'name': key,
                'distance': current_price - level
            })

    nearest_support = min(supports, key=lambda x: x['distance']) if supports else None

    # Calculate stop loss (nearest support or 1% below)
    if nearest_support:
        stop_loss_price = nearest_support['level']
        stop_loss_distance = current_price - stop_loss_price
    else:
        stop_loss_price = current_price * 0.99  # Default 1% stop
        stop_loss_distance = current_price - stop_loss_price

    stop_loss_pct = (stop_loss_distance / current_price) * 100

    # Find flip scenario (which level would flip the prediction)
    prediction = signals_data['prediction']
    bullish_count = signals_data['bullish_count']
    total_signals = signals_data['total_signals']

    if prediction == 'BULLISH':
        # Need to lose enough bullish signals to flip
        signals_to_flip = bullish_count - (total_signals - bullish_count) + 1

        # Find the highest reference level above current price
        resistances = []
        for key, level in reference_levels.items():
            if level and level > current_price:
                resistances.append({
                    'level': level,
                    'name': key
                })

        flip_level = min(resistances, key=lambda x: x['level']) if resistances else None
    else:
        # BEARISH - need to gain enough bullish signals to flip
        signals_to_flip = (total_signals - bullish_count) - bullish_count + 1

        # Find the lowest reference level below current price
        flip_level = nearest_support

    # Estimate flip probability (simplified)
    if flip_level:
        distance_to_flip = abs(current_price - flip_level['level'])
        distance_pct = (distance_to_flip / current_price) * 100

        # Simple probability model: further away = lower probability
        if distance_pct < 0.5:
            flip_probability = 25
        elif distance_pct < 1.0:
            flip_probability = 15
        elif distance_pct < 2.0:
            flip_probability = 8
        else:
            flip_probability = 3
    else:
        flip_probability = 5  # Default low probability

    return {
        'stop_loss_price': round(stop_loss_price, 2) if stop_loss_price else None,
        'stop_loss_distance': round(stop_loss_distance, 2) if stop_loss_distance else None,
        'stop_loss_pct': round(stop_loss_pct, 2) if stop_loss_pct else None,
        'nearest_support': nearest_support,
        'flip_scenario': {
            'level': flip_level,
            'signals_to_flip': signals_to_flip if flip_level else None,
            'probability_15min': flip_probability
        }
    }


def process_ticker_data(ticker_symbol: str) -> Optional[Dict[str, Any]]:
    """
    Process market data for a single ticker symbol

    Args:
        ticker_symbol: The ticker to process

    Returns:
        Dictionary with processed market data or None if fetch fails
    """
    try:
        data = get_reference_levels(ticker_symbol)
        if not data:
            logger.warning(f"Failed to fetch reference levels for {ticker_symbol}")
            return None

        signals = calculate_signals(data['current_price'], data['reference_levels'])

        # Get session ranges - ICT Killzone Times (UTC)
        # Asian Session: 2000-0000 EST = 01:00-05:00 UTC
        # London Open: 0200-0500 EST = 07:00-10:00 UTC
        # New York AM: 0830-1100 EST = 13:30-16:00 UTC
        asia_range = get_session_range(ticker_symbol, 1, 0, 5, 0, data['current_time'])
        london_range = get_session_range(ticker_symbol, 7, 0, 10, 0, data['current_time'])
        ny_range = get_session_range(ticker_symbol, 13, 30, 16, 0, data['current_time'])

        # Get market status
        market_status = get_market_status(ticker_symbol, data['current_time'])

        # Calculate confidence horizons
        confidence_horizons = calculate_confidence_horizons(signals['confidence'])

        # Calculate volatility
        volatility = calculate_volatility(data.get('hourly_movement', []))

        # Calculate risk metrics
        risk_metrics = calculate_risk_metrics(
            data['current_price'],
            data['reference_levels'],
            signals
        )

        return {
            'current_price': data['current_price'],
            'current_time': data['current_time'].strftime('%Y-%m-%d %H:%M:%S %Z'),
            'market_status': market_status['status'],
            'next_open': market_status['next_open'],
            'midnight_open': data.get('midnight_open'),
            'ny_open': data.get('ny_open'),
            'session_ranges': {
                'asia': {
                    'range': asia_range,
                    'position': analyze_price_vs_range(data['current_price'], asia_range)
                },
                'london': {
                    'range': london_range,
                    'position': analyze_price_vs_range(data['current_price'], london_range)
                },
                'ny': {
                    'range': ny_range,
                    'position': analyze_price_vs_range(data['current_price'], ny_range)
                }
            },
            'confidence_horizons': confidence_horizons,
            'volatility': volatility,
            'risk_metrics': risk_metrics,
            **signals
        }
    except Exception as e:
        logger.error(f"Error processing ticker {ticker_symbol}: {str(e)}", exc_info=True)
        return None


def get_market_data():
    """Fetch and calculate market data for both instruments"""
    result = {}

    # Process both tickers
    for ticker in ['NQ=F', '^NDX']:
        ticker_data = process_ticker_data(ticker)
        result[ticker] = ticker_data if ticker_data else {'error': 'Failed to fetch data'}

    return result


@app.route('/')
def index():
    """Render the main dashboard"""
    return render_template('index.html')


@app.route('/health')
@app.route('/api/health')
def health_check():
    """Health check endpoint for monitoring and deployment platforms"""
    try:
        cached_data, cached_time = cache.get()
        cache_status = 'healthy' if cached_data is not None else 'empty'
        cache_age = None
        if cached_time is not None:
            cache_age = (datetime.now() - cached_time).total_seconds()

        return jsonify({
            'status': 'healthy',
            'timestamp': datetime.now(pytz.UTC).strftime('%Y-%m-%d %H:%M:%S %Z'),
            'cache_status': cache_status,
            'cache_age_seconds': cache_age,
            'version': APP_VERSION
        }), 200
    except Exception as e:
        logger.error(f"Health check failed: {str(e)}", exc_info=True)
        return jsonify({
            'status': 'unhealthy',
            'error': str(e),
            'timestamp': datetime.now(pytz.UTC).strftime('%Y-%m-%d %H:%M:%S %Z')
        }), 500


@app.route('/api/data')
def api_data():
    """API endpoint to get market data with caching"""
    request_start = datetime.now()

    # Check if cache is valid
    if cache.is_valid(CACHE_DURATION):
        cached_data, cached_time = cache.get()
        time_diff = (datetime.now() - cached_time).total_seconds()
        response_time = (datetime.now() - request_start).total_seconds() * 1000  # in milliseconds
        logger.info(f"Serving cached data (age: {time_diff:.1f}s, response_time: {response_time:.2f}ms)")
        return jsonify({
            'data': cached_data,
            'cached': True,
            'cache_age': time_diff,
            'response_time_ms': round(response_time, 2)
        })

    # Fetch fresh data
    try:
        logger.info("Fetching fresh market data")
        current_time = datetime.now()
        data = get_market_data()
        cache.set(data, current_time)

        response_time = (datetime.now() - request_start).total_seconds() * 1000  # in milliseconds
        logger.info(f"Fresh data fetched successfully (response_time: {response_time:.2f}ms)")

        return jsonify({
            'data': data,
            'cached': False,
            'timestamp': current_time.strftime('%Y-%m-%d %H:%M:%S'),
            'response_time_ms': round(response_time, 2)
        })
    except Exception as e:
        response_time = (datetime.now() - request_start).total_seconds() * 1000
        logger.error(f"Error fetching market data (response_time: {response_time:.2f}ms): {str(e)}", exc_info=True)
        return jsonify({
            'error': 'Failed to fetch market data',
            'error_detail': str(e),
            'response_time_ms': round(response_time, 2)
        }), 500


if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port, debug=False)
