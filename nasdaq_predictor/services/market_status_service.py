"""
Market Status Service for NQP Application

Provides timezone-aware market status detection for different instruments
and trading venues. Supports US futures, international indices, and crypto markets.

Handles market open/close detection, next event calculation, and last trading date.
"""

import logging
from datetime import datetime, time, timedelta, date
from typing import Optional, Tuple, List
from dataclasses import dataclass
from enum import Enum
import pytz

from ..config.market_config import get_market_config, MarketType, Timezone

logger = logging.getLogger(__name__)


class MarketStatus(Enum):
    """Enumeration of possible market statuses."""
    OPEN = "OPEN"
    CLOSED = "CLOSED"
    PRE_MARKET = "PRE_MARKET"
    AFTER_HOURS = "AFTER_HOURS"


class SessionType(Enum):
    """Trading session types."""
    ELECTRONIC = "ELECTRONIC"  # US Futures (24/5)
    REGULAR = "REGULAR"        # Traditional exchanges (9-5 equivalent)
    EXTENDED = "EXTENDED"      # Extended hours trading
    CONTINUOUS_24_7 = "24/7"   # Crypto markets


class InstrumentType(Enum):
    """Classification of trading instruments."""
    US_FUTURES = "US_FUTURES"
    UK_INDEX = "UK_INDEX"
    JAPAN_INDEX = "JAPAN_INDEX"
    CRYPTO = "CRYPTO"


@dataclass
class MarketStatusInfo:
    """
    Rich information about current market status.

    Attributes:
        status: Current status (OPEN, CLOSED, PRE_MARKET, AFTER_HOURS)
        is_trading: Whether market is actively trading
        session_type: Type of trading session
        instrument_type: Classification of instrument
        current_time: Current time (timezone-aware)
        next_open: Next market open time (None if 24/7)
        next_close: Next market close time (None if 24/7)
        timezone: Market timezone (e.g., "America/Chicago")
        last_trading_date: Most recent trading date
    """
    status: MarketStatus
    is_trading: bool
    session_type: SessionType
    instrument_type: InstrumentType
    current_time: datetime
    next_open: Optional[datetime]
    next_close: Optional[datetime]
    timezone: str
    last_trading_date: date


@dataclass
class TradingSession:
    """Represents a single trading session (e.g., Monday regular hours)."""
    day_of_week: int  # 0=Monday, 6=Sunday
    start_time: time  # In market timezone
    end_time: time    # In market timezone
    session_type: SessionType


@dataclass
class MarketSchedule:
    """Complete trading schedule for an instrument."""
    ticker: str
    instrument_type: InstrumentType
    timezone: str
    sessions: List[TradingSession]
    lunch_break_start: Optional[time] = None  # For markets with lunch breaks
    lunch_break_end: Optional[time] = None
    is_24_7: bool = False  # For crypto markets

    def __post_init__(self):
        """Validate the market schedule."""
        if self.is_24_7 and self.sessions:
            logger.warning(f"24/7 market {self.ticker} has sessions defined - ignoring")


class MarketStatusService:
    """
    Service for determining market status of instruments.

    Handles timezone-aware market open/close detection for different
    instruments and trading venues worldwide.
    """

    def __init__(self):
        """Initialize MarketStatusService with market schedules from config."""
        self.market_config = get_market_config()
        self.schedules = self._convert_config_to_schedules()
        self.timezone_cache = {}

    def _convert_config_to_schedules(self) -> dict:
        """
        Convert MarketHoursConfig schedules to MarketSchedule objects.

        Returns:
            Dictionary mapping ticker symbols to MarketSchedule objects
        """
        schedules = {}

        # Map specific tickers to their instrument types
        ticker_instrument_map = {
            "NQ=F": InstrumentType.US_FUTURES,
            "ES=F": InstrumentType.US_FUTURES,
            "YM=F": InstrumentType.US_FUTURES,
            "RTY=F": InstrumentType.US_FUTURES,
            "^FTSE": InstrumentType.UK_INDEX,
            "^N225": InstrumentType.JAPAN_INDEX,
            "BTC-USD": InstrumentType.CRYPTO,
            "SOL-USD": InstrumentType.CRYPTO,
            "ADA-USD": InstrumentType.CRYPTO,
            "ETH-USD": InstrumentType.CRYPTO,
        }

        for ticker in self.market_config.get_all_tickers():
            config_schedule = self.market_config.get_schedule(ticker)

            # Convert config TradingSession objects to internal TradingSession format
            trading_sessions = []
            for config_session in config_schedule.sessions:
                trading_sessions.append(
                    TradingSession(
                        day_of_week=config_session.day.value,
                        start_time=config_session.start_time,
                        end_time=config_session.end_time,
                        session_type=self._map_market_type_to_session_type(
                            config_schedule.market_type
                        )
                    )
                )

            # Get instrument type from mapping, with fallback
            instrument_type = ticker_instrument_map.get(
                ticker,
                self._map_market_type_to_instrument_type(config_schedule.market_type)
            )

            # Create MarketSchedule
            schedules[ticker] = MarketSchedule(
                ticker=ticker,
                instrument_type=instrument_type,
                timezone=config_schedule.timezone,
                sessions=trading_sessions,
                lunch_break_start=config_schedule.lunch_break_start,
                lunch_break_end=config_schedule.lunch_break_end,
                is_24_7=config_schedule.is_24_7
            )

        logger.info(f"Initialized market schedules for {len(schedules)} instruments from config")
        return schedules

    @staticmethod
    def _map_market_type_to_session_type(market_type: MarketType) -> SessionType:
        """Map MarketType to SessionType."""
        mapping = {
            MarketType.FUTURES: SessionType.ELECTRONIC,
            MarketType.EQUITY: SessionType.REGULAR,
            MarketType.INDEX: SessionType.REGULAR,
            MarketType.CRYPTO: SessionType.CONTINUOUS_24_7,
        }
        return mapping.get(market_type, SessionType.REGULAR)

    @staticmethod
    def _map_market_type_to_instrument_type(market_type: MarketType) -> InstrumentType:
        """Map MarketType to InstrumentType (fallback)."""
        mapping = {
            MarketType.FUTURES: InstrumentType.US_FUTURES,
            MarketType.INDEX: InstrumentType.UK_INDEX,  # Default for indices
            MarketType.CRYPTO: InstrumentType.CRYPTO,
        }
        return mapping.get(market_type, InstrumentType.US_FUTURES)

    def get_market_status(
        self,
        ticker: str,
        at_time: Optional[datetime] = None
    ) -> MarketStatusInfo:
        """
        Get market status for a ticker at a specific time.

        Args:
            ticker: Ticker symbol (e.g., "NQ=F", "^FTSE")
            at_time: Time to check (defaults to current UTC time)

        Returns:
            MarketStatusInfo with comprehensive market status

        Raises:
            ValueError: If ticker not found in market schedules
        """
        if ticker not in self.schedules:
            raise ValueError(f"No market schedule configured for ticker: {ticker}")

        schedule = self.schedules[ticker]

        # Default to current UTC time
        if at_time is None:
            at_time = datetime.now(pytz.UTC)

        # Ensure time is timezone-aware
        if at_time.tzinfo is None:
            at_time = pytz.UTC.localize(at_time)

        # Convert to market timezone
        market_tz = pytz.timezone(schedule.timezone)
        market_time = at_time.astimezone(market_tz)

        # 24/7 markets are always open
        if schedule.is_24_7:
            return MarketStatusInfo(
                status=MarketStatus.OPEN,
                is_trading=True,
                session_type=SessionType.CONTINUOUS_24_7,
                instrument_type=schedule.instrument_type,
                current_time=at_time,
                next_open=None,
                next_close=None,
                timezone=schedule.timezone,
                last_trading_date=market_time.date()
            )

        # Determine if market is currently open
        is_open, current_session = self._is_market_open(market_time, schedule)

        # Calculate next open/close times
        next_open, next_close = self._calculate_next_events(market_time, schedule)

        # Determine status type
        if is_open:
            status = MarketStatus.OPEN
            is_trading = True
        else:
            status = MarketStatus.CLOSED
            is_trading = False

        return MarketStatusInfo(
            status=status,
            is_trading=is_trading,
            session_type=current_session.session_type if current_session else SessionType.REGULAR,
            instrument_type=schedule.instrument_type,
            current_time=at_time,
            next_open=next_open,
            next_close=next_close,
            timezone=schedule.timezone,
            last_trading_date=self.get_last_trading_date(ticker, at_time)
        )

    def _is_market_open(
        self,
        market_time: datetime,
        schedule: MarketSchedule
    ) -> Tuple[bool, Optional[TradingSession]]:
        """
        Determine if market is open at the given market time.

        Handles lunch breaks and multiple sessions per day.
        """
        current_date = market_time.date()
        current_day = market_time.weekday()
        current_clock = market_time.time()

        # Find sessions for current day
        matching_sessions = [s for s in schedule.sessions if s.day_of_week == current_day]

        for session in matching_sessions:
            if session.start_time <= current_clock < session.end_time:
                # Check for lunch break
                if schedule.lunch_break_start and schedule.lunch_break_end:
                    if schedule.lunch_break_start <= current_clock < schedule.lunch_break_end:
                        return False, None
                return True, session

        return False, None

    def _calculate_next_events(
        self,
        market_time: datetime,
        schedule: MarketSchedule
    ) -> Tuple[Optional[datetime], Optional[datetime]]:
        """
        Calculate next market open and close times.
        """
        market_tz = pytz.timezone(schedule.timezone)

        next_open = None
        next_close = None

        current_day = market_time.weekday()
        current_time = market_time.time()

        # Find next close (if not already passed today)
        for session in schedule.sessions:
            if session.day_of_week == current_day and current_time < session.end_time:
                next_close_time = market_time.replace(
                    hour=session.end_time.hour,
                    minute=session.end_time.minute,
                    second=0,
                    microsecond=0
                )
                next_close = next_close_time.astimezone(pytz.UTC)
                break

        # If no close found today, search remaining days
        if not next_close:
            search_days = 7
            for offset in range(1, search_days + 1):
                search_date = market_time + timedelta(days=offset)
                search_day = search_date.weekday()

                matching_sessions = [s for s in schedule.sessions if s.day_of_week == search_day]
                if matching_sessions:
                    session = matching_sessions[0]
                    next_open_time = search_date.replace(
                        hour=session.start_time.hour,
                        minute=session.start_time.minute,
                        second=0,
                        microsecond=0
                    )
                    next_open = next_open_time.astimezone(pytz.UTC)
                    break

        return next_open, next_close

    def get_last_trading_date(
        self,
        ticker: str,
        at_time: Optional[datetime] = None
    ) -> date:
        """
        Get the last trading date for a ticker.

        During market hours: returns current date
        After market closes: returns current date
        Before market opens: returns previous trading day
        """
        if ticker not in self.schedules:
            raise ValueError(f"No market schedule configured for ticker: {ticker}")

        if at_time is None:
            at_time = datetime.now(pytz.UTC)

        # Ensure time is timezone-aware
        if at_time.tzinfo is None:
            at_time = pytz.UTC.localize(at_time)

        schedule = self.schedules[ticker]
        market_tz = pytz.timezone(schedule.timezone)
        market_time = at_time.astimezone(market_tz)

        # For 24/7 markets, always return current date
        if schedule.is_24_7:
            return market_time.date()

        # Check if market is currently open (without recursion)
        is_open, _ = self._is_market_open(market_time, schedule)

        # If market is open, return today
        if is_open:
            return market_time.date()

        # Market is closed - find last trading day
        search_date = market_time.date()
        for offset in range(1, 7):  # Search back up to 7 days
            search_date = search_date - timedelta(days=1)
            search_day = search_date.weekday()

            # Check if this day has trading sessions
            has_session = any(s.day_of_week == search_day for s in schedule.sessions)
            if has_session:
                return search_date

        # Fallback (shouldn't reach here)
        return market_time.date()

    def is_market_open(self, ticker: str, at_time: Optional[datetime] = None) -> bool:
        """Quick check if market is open."""
        try:
            status = self.get_market_status(ticker, at_time)
            return status.is_trading
        except ValueError:
            return False

    def get_next_market_event(
        self,
        ticker: str,
        at_time: Optional[datetime] = None
    ) -> Tuple[str, Optional[datetime]]:
        """
        Get next market event (open or close).

        Returns:
            Tuple of (event_type: "OPEN"|"CLOSE", event_time: datetime or None)
        """
        status = self.get_market_status(ticker, at_time)

        if status.is_trading:
            # Market is open, next event is close
            return "CLOSE", status.next_close
        else:
            # Market is closed, next event is open
            return "OPEN", status.next_open
