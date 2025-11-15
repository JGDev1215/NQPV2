"""
Data models for market data structures
"""
from dataclasses import dataclass
from datetime import datetime
from typing import Optional, List, Dict, Any


@dataclass
class OHLCData:
    """Open, High, Low, Close candlestick data"""
    timestamp: datetime
    open: float
    high: float
    low: float
    close: float
    volume: float


@dataclass
class RangeLevel:
    """Range-based reference level storing high and low prices

    Used for ICT kill zones and time-based ranges where we need to check
    if current price is above the range high (BULLISH), below the range low (BEARISH),
    or within the range (NEUTRAL).
    """
    high: float
    low: float

    @property
    def midpoint(self) -> float:
        """Calculate midpoint of the range"""
        return (self.high + self.low) / 2

    @property
    def range_size(self) -> float:
        """Calculate size of the range"""
        return self.high - self.low

    def get_position(self, price: float) -> str:
        """
        Determine position of price relative to range.

        Returns:
            'ABOVE' if price > high
            'BELOW' if price < low
            'WITHIN' if low <= price <= high
        """
        if price > self.high:
            return 'ABOVE'
        elif price < self.low:
            return 'BELOW'
        else:
            return 'WITHIN'


@dataclass
class ReferenceLevels:
    """Reference levels for signal calculation

    Supports both single-price reference levels (float) and range-based
    reference levels (RangeLevel) for ICT kill zones and time ranges.
    """
    # Existing 11 reference levels (backward compatible)
    daily_open: Optional[float] = None
    hourly_open: Optional[float] = None
    four_hourly_open: Optional[float] = None
    prev_day_high: Optional[float] = None
    prev_day_low: Optional[float] = None
    prev_week_open: Optional[float] = None
    thirty_min_open: Optional[float] = None
    weekly_open: Optional[float] = None
    monthly_open: Optional[float] = None
    seven_am_open: Optional[float] = None
    eight_thirty_am_open: Optional[float] = None

    # NEW: 7 additional reference levels for 18-level system
    previous_hourly_open: Optional[float] = None
    previous_day_high: Optional[float] = None  # Consistent naming with previous_day_low
    previous_day_low: Optional[float] = None
    range_0700_0715: Optional[RangeLevel] = None  # 7:00-7:15 AM range
    range_0830_0845: Optional[RangeLevel] = None  # 8:30-8:45 AM range
    asian_kill_zone: Optional[RangeLevel] = None  # Asian session range
    london_kill_zone: Optional[RangeLevel] = None  # London session range
    ny_am_kill_zone: Optional[RangeLevel] = None  # NY AM session range
    ny_pm_kill_zone: Optional[RangeLevel] = None  # NY PM session range

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary with new 18-level naming convention

        Returns dictionary mapping weight keys to reference level values.
        For RangeLevel objects, returns the RangeLevel itself (not just midpoint).
        """
        return {
            # Map to new 18-level weight keys
            'daily_open_midnight': self.daily_open,
            'ny_open_0830': self.eight_thirty_am_open,
            'thirty_min_open': self.thirty_min_open,
            'ny_open_0700': self.seven_am_open,
            'four_hour_open': self.four_hourly_open,
            'weekly_open': self.weekly_open,
            'hourly_open': self.hourly_open,
            'previous_hourly_open': self.previous_hourly_open,
            'previous_week_open': self.prev_week_open,
            'previous_day_high': self.previous_day_high or self.prev_day_high,
            'previous_day_low': self.previous_day_low or self.prev_day_low,
            'monthly_open': self.monthly_open,
            'range_0700_0715': self.range_0700_0715,
            'range_0830_0845': self.range_0830_0845,
            'asian_kill_zone': self.asian_kill_zone,
            'london_kill_zone': self.london_kill_zone,
            'ny_am_kill_zone': self.ny_am_kill_zone,
            'ny_pm_kill_zone': self.ny_pm_kill_zone,
        }


@dataclass
class SessionRange:
    """Session range data (High/Low for trading session)"""
    high: float
    low: float
    range: float


@dataclass
class SignalData:
    """Individual signal data for a reference level"""
    signal: Optional[int]  # 1 for bullish, 0 for bearish, None for N/A
    reference_level: Optional[float]
    distance: Optional[float]
    status: str  # 'BULLISH', 'BEARISH', or 'N/A'


@dataclass
class ConfidenceHorizon:
    """Confidence data for a specific time horizon"""
    confidence: float
    level: str  # 'HIGH', 'MODERATE', 'LOW', 'SPECULATIVE'


@dataclass
class IntradayPrediction:
    """Intraday hourly prediction for a specific time window (9am or 10am)"""
    prediction: str  # 'BULLISH' or 'BEARISH'
    confidence: float  # Adjusted confidence with decay factor applied
    base_confidence: float  # Original confidence before decay
    decay_factor: float  # Time-based decay multiplier (0.0-1.0)
    status: str  # 'PENDING', 'ACTIVE', 'LOCKED', 'VERIFIED'
    actual_result: Optional[str] = None  # 'CORRECT' or 'WRONG' (after verification)
    target_close: Optional[float] = None  # Actual close price at target hour
    reference_open: Optional[float] = None  # Open price at prediction hour
    time_until_target: Optional[str] = None  # Human-readable time until target


@dataclass
class IntradayPredictions:
    """Complete intraday prediction data for both 9am and 10am windows"""
    current_time_ny: str  # Current time in NY Eastern
    current_time_utc: str  # Current time in UTC
    current_time_window: str  # 'pre_9am', '9am_hour', '10am_hour', 'post_10am', 'evening'

    # 9am prediction (targeting 10am close)
    nine_am: IntradayPrediction

    # 10am prediction (targeting 11am close)
    ten_am: IntradayPrediction

    # Morning reference prices
    seven_am_open: Optional[float] = None
    eight_thirty_am_open: Optional[float] = None

    # Previous day predictions (for comparison during morning hours)
    previous_day_9am: Optional[IntradayPrediction] = None
    previous_day_10am: Optional[IntradayPrediction] = None

    # Metadata
    predictions_locked: bool = False
    predictions_locked_at: Optional[str] = None
    next_prediction_time: Optional[str] = None


@dataclass
class Volatility:
    """Volatility metrics"""
    hourly_range_pct: float
    level: str  # 'LOW', 'MODERATE', 'HIGH', 'EXTREME', 'UNKNOWN'




@dataclass
class MarketStatus:
    """Market status information"""
    status: str  # 'OPEN', 'CLOSED', 'PRE-MARKET', 'AFTER-HOURS', 'UNKNOWN'
    next_open: Optional[str]


@dataclass
class MarketData:
    """Complete market data for a ticker"""
    ticker: str
    current_price: float
    current_time: datetime
    reference_levels: ReferenceLevels
    signals: Dict[str, SignalData]
    weighted_score: float
    prediction: str  # 'BULLISH' or 'BEARISH'
    confidence: float
    bullish_count: int
    total_signals: int
    market_status: MarketStatus
    session_ranges: Dict[str, Any]
    intraday_predictions: IntradayPredictions  # UPDATED: Replaces confidence_horizons and eod_predictions
    volatility: Volatility
    midnight_open: Optional[float] = None
    ny_open: Optional[float] = None
    # Keep for backward compatibility during transition
    confidence_horizons: Optional[Dict[str, ConfidenceHorizon]] = None
