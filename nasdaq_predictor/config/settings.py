"""
Configuration settings for the NASDAQ Predictor application
"""

# Application Configuration
APP_VERSION = '1.0.0'
CACHE_DURATION = 900  # seconds (15 minutes)
ALLOWED_TICKERS = ['NQ=F', 'ES=F', '^FTSE', 'BTC-USD', 'SOL-USD', 'ADA-USD']

# Data fetching configuration
HIST_PERIOD_HOURLY = '30d'  # Period for hourly data
HIST_PERIOD_MINUTE = '7d'   # Period for minute data
HIST_PERIOD_5MIN = '7d'     # Period for 5-minute data (block segmentation, intraday analysis)
HIST_PERIOD_15MIN = '30d'   # Period for 15-minute data (mid-timeframe analysis)
HIST_PERIOD_30MIN = '60d'    # Period for 30-minute data
HIST_INTERVAL_HOURLY = '1h'
HIST_INTERVAL_MINUTE = '1m'
HIST_INTERVAL_5MIN = '5m'
HIST_INTERVAL_15MIN = '15m'
HIST_INTERVAL_30MIN = '30m'

# Normalized weights for reference levels (sum to 1.0)
# 18-level system including single-price levels and range-based levels
WEIGHTS = {
    "daily_open_midnight": 0.100,  # Reduced to accommodate NY PM kill zone
    "ny_open_0830": 0.063,
    "thirty_min_open": 0.080,
    "ny_open_0700": 0.068,
    "four_hour_open": 0.056,
    "weekly_open": 0.049,
    "hourly_open": 0.042,
    "previous_hourly_open": 0.041,
    "previous_week_open": 0.024,
    "previous_day_high": 0.023,
    "previous_day_low": 0.023,
    "monthly_open": 0.021,
    "range_0700_0715": 0.073,      # 7:00-7:15 AM range (high/low)
    "range_0830_0845": 0.079,      # 8:30-8:45 AM range (high/low)
    "asian_kill_zone": 0.053,      # Asian session range (01:00-05:00 UTC)
    "london_kill_zone": 0.069,     # London session range (07:00-10:00 UTC)
    "ny_am_kill_zone": 0.083,      # NY AM session range (13:30-16:00 UTC)
    "ny_pm_kill_zone": 0.053,      # NY PM session range (17:30-20:00 UTC / 1:30PM-4:00PM ET)
}

# Validate weights sum to 1.0
_weights_sum = sum(WEIGHTS.values())
assert abs(_weights_sum - 1.0) < 0.001, f"Weights must sum to 1.0, got {_weights_sum}"

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
    'ES=F': {
        # S&P 500 Futures trades nearly 24/7 with 1-hour break
        # Main session: 13:30-20:00 UTC (9:30 AM - 4:00 PM ET)
        # Extended: Sunday 22:00 UTC to Friday 21:00 UTC with 21:00-22:00 break
        'type': 'futures',
        'main_session_start': 13.5,  # 13:30 UTC
        'main_session_end': 20.0,     # 20:00 UTC
        'uses_main_only': False       # Uses all trading hours
    },
    'BTC-USD': {
        # Bitcoin trades 24/7 on cryptocurrency exchanges
        'type': 'crypto',
        'main_session_start': 0.0,    # Not applicable (24/7)
        'main_session_end': 24.0,     # Not applicable (24/7)
        'uses_main_only': False       # Trades continuously
    },
    'SOL-USD': {
        # Solana trades 24/7 on cryptocurrency exchanges
        'type': 'crypto',
        'main_session_start': 0.0,    # Not applicable (24/7)
        'main_session_end': 24.0,     # Not applicable (24/7)
        'uses_main_only': False       # Trades continuously
    },
    'ADA-USD': {
        # Cardano trades 24/7 on cryptocurrency exchanges
        'type': 'crypto',
        'main_session_start': 0.0,    # Not applicable (24/7)
        'main_session_end': 24.0,     # Not applicable (24/7)
        'uses_main_only': False       # Trades continuously
    }
}

# Intraday Hourly Prediction Configuration (replaces time-based confidence decay)
# Predicts if close > open (BULLISH) or close < open (BEARISH) for hourly candles
PREDICTION_WINDOWS = {
    '9am': {
        'hour': 9,           # 9:00am NY time
        'target_hour': 10,   # Predicting 10am close (end of 9am candle)
        'label': '9am → 10am Close'
    },
    '10am': {
        'hour': 10,          # 10:00am NY time
        'target_hour': 11,   # Predicting 11am close (end of 10am candle)
        'label': '10am → 11am Close'
    }
}

# Confidence decay configuration for intraday predictions
CONFIDENCE_DECAY_CONFIG = {
    'max_hours_before': 6,      # Start showing predictions 6 hours before window
    'min_confidence_factor': 0.5,  # Minimum confidence multiplier (50% of base)
    'decay_curve': 'exponential'   # Exponential decay as time increases from target
}

# Morning reference price capture time
MORNING_CAPTURE_TIME = {
    'hour': 8,      # 8:50am NY time
    'minute': 50
}

# Display cutoff times (NY Eastern Time)
DISPLAY_CUTOFFS = {
    'evening_cutoff_hour': 19,  # 7:00pm - lock current day results
    'midnight_reset_hour': 0    # 12:00am - prepare for new day
}

# ICT Killzone session times (in UTC)
ICT_SESSIONS = {
    'asia': {
        'start_hour': 1,
        'start_minute': 0,
        'end_hour': 5,
        'end_minute': 0
    },
    'london': {
        'start_hour': 7,
        'start_minute': 0,
        'end_hour': 10,
        'end_minute': 0
    },
    'ny': {
        'start_hour': 13,
        'start_minute': 30,
        'end_hour': 16,
        'end_minute': 0
    },
    'ny_pm': {
        'start_hour': 17,
        'start_minute': 30,
        'end_hour': 20,
        'end_minute': 0
    }
}

# Auto-refresh configuration for intelligent frontend updates
AUTO_REFRESH_ENABLED = True
AUTO_REFRESH_BUFFER_SECONDS = 15  # Wait 15s after job runs before refreshing
MIN_REFRESH_INTERVAL_SECONDS = 60  # Never refresh faster than 1 minute
SHOW_DATA_FRESHNESS_INDICATOR = True
FRESHNESS_THRESHOLD_WARNING = 120  # Yellow indicator after 2 minutes
FRESHNESS_THRESHOLD_STALE = 600    # Red indicator after 10 minutes
