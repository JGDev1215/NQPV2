"""
Market Hours Configuration for NQP Application

Defines trading schedules for all supported instruments with timezone awareness.
This configuration drives the MarketStatusService for market status detection.

Supports:
- US Futures (NASDAQ-100, S&P 500, Dow Jones, Russell 2000)
- International Indices (FTSE 100, Nikkei 225)
- Cryptocurrencies (Bitcoin, Solana, Cardano, Ethereum)
"""

from enum import Enum
from typing import Dict, List, Optional, Tuple
from datetime import time


class MarketType(Enum):
    """Classification of market types."""
    FUTURES = "FUTURES"
    EQUITY = "EQUITY"
    INDEX = "INDEX"
    CRYPTO = "CRYPTO"


class Timezone(Enum):
    """Trading venue timezones."""
    CHICAGO = "America/Chicago"      # US Futures (CME)
    NEW_YORK = "America/New_York"    # US Equities
    LONDON = "Europe/London"         # LSE, FTSE
    TOKYO = "Asia/Tokyo"             # TSE, Nikkei
    SYDNEY = "Australia/Sydney"      # ASX
    SINGAPORE = "Asia/Singapore"     # SGX
    HONG_KONG = "Asia/Hong_Kong"     # HKEX
    UTC = "UTC"                       # Crypto exchanges


class SessionDay(Enum):
    """Day of week for trading sessions (0=Monday, 6=Sunday)."""
    MONDAY = 0
    TUESDAY = 1
    WEDNESDAY = 2
    THURSDAY = 3
    FRIDAY = 4
    SATURDAY = 5
    SUNDAY = 6


class TradingSession:
    """Represents a single trading session (e.g., Monday regular hours)."""

    def __init__(
        self,
        day: SessionDay,
        start_hour: int,
        start_minute: int,
        end_hour: int,
        end_minute: int,
        session_name: str = "Regular"
    ):
        self.day = day
        self.start_time = time(start_hour, start_minute)
        self.end_time = time(end_hour, end_minute)
        self.session_name = session_name

    def __repr__(self) -> str:
        return (
            f"TradingSession({self.day.name}, "
            f"{self.start_time.strftime('%H:%M')}-{self.end_time.strftime('%H:%M')}, "
            f"{self.session_name})"
        )


class MarketSchedule:
    """Complete trading schedule for an instrument."""

    def __init__(
        self,
        ticker: str,
        market_type: MarketType,
        timezone: Timezone,
        sessions: List[TradingSession],
        lunch_break_start: Optional[Tuple[int, int]] = None,
        lunch_break_end: Optional[Tuple[int, int]] = None,
        is_24_7: bool = False
    ):
        self.ticker = ticker
        self.market_type = market_type
        self.timezone = timezone.value
        self.sessions = sessions
        self.lunch_break_start = time(*lunch_break_start) if lunch_break_start else None
        self.lunch_break_end = time(*lunch_break_end) if lunch_break_end else None
        self.is_24_7 = is_24_7

    def __repr__(self) -> str:
        return f"MarketSchedule({self.ticker}, {self.market_type.value}, {self.timezone})"


class MarketHoursConfig:
    """
    Central configuration for all market trading hours.

    Provides:
    - Market schedule definitions for all instruments
    - Easy access to trading hours by ticker
    - Support for extending with new instruments
    - Timezone-aware schedule information
    """

    def __init__(self):
        """Initialize market hours configuration."""
        self.schedules: Dict[str, MarketSchedule] = {}
        self._initialize_all_markets()

    def _initialize_all_markets(self) -> None:
        """Initialize all supported market schedules."""
        # US Futures Markets
        self._setup_us_futures()

        # International Indices
        self._setup_international_indices()

        # Cryptocurrencies
        self._setup_crypto_markets()

    def _setup_us_futures(self) -> None:
        """Set up US futures trading schedules (CME - Chicago timezone)."""
        # US Futures trading: Sunday 6 PM - Friday 5 PM CST with 1-hour break 5-6 PM
        # In terms of day_of_week: Sunday (6) 18:00-23:59, Mon-Fri (0-4) 00:00-17:00
        us_futures_sessions = [
            # Sunday evening session (6 PM - 11:59 PM CST)
            TradingSession(SessionDay.SUNDAY, 18, 0, 23, 59, "Evening Session"),
            # Monday through Friday regular sessions (12 AM - 5 PM CST)
            TradingSession(SessionDay.MONDAY, 0, 0, 17, 0, "Regular Session"),
            TradingSession(SessionDay.TUESDAY, 0, 0, 17, 0, "Regular Session"),
            TradingSession(SessionDay.WEDNESDAY, 0, 0, 17, 0, "Regular Session"),
            TradingSession(SessionDay.THURSDAY, 0, 0, 17, 0, "Regular Session"),
            TradingSession(SessionDay.FRIDAY, 0, 0, 17, 0, "Regular Session"),
        ]

        for ticker in ["NQ=F", "ES=F", "YM=F", "RTY=F"]:
            self.schedules[ticker] = MarketSchedule(
                ticker=ticker,
                market_type=MarketType.FUTURES,
                timezone=Timezone.CHICAGO,
                sessions=us_futures_sessions
            )

    def _setup_international_indices(self) -> None:
        """Set up international index trading schedules."""
        # FTSE 100 (London Stock Exchange)
        # Trading: Monday-Friday 8:00 AM - 4:30 PM GMT (Europe/London)
        ftse_sessions = [
            TradingSession(SessionDay.MONDAY, 8, 0, 16, 30, "Regular Session"),
            TradingSession(SessionDay.TUESDAY, 8, 0, 16, 30, "Regular Session"),
            TradingSession(SessionDay.WEDNESDAY, 8, 0, 16, 30, "Regular Session"),
            TradingSession(SessionDay.THURSDAY, 8, 0, 16, 30, "Regular Session"),
            TradingSession(SessionDay.FRIDAY, 8, 0, 16, 30, "Regular Session"),
        ]

        self.schedules["^FTSE"] = MarketSchedule(
            ticker="^FTSE",
            market_type=MarketType.INDEX,
            timezone=Timezone.LONDON,
            sessions=ftse_sessions
        )

        # Nikkei 225 (Tokyo Stock Exchange)
        # Trading: Monday-Friday 9:00 AM - 3:00 PM JST with lunch break 11:30 AM - 12:30 PM
        nikkei_sessions = [
            TradingSession(SessionDay.MONDAY, 9, 0, 15, 0, "Regular Session"),
            TradingSession(SessionDay.TUESDAY, 9, 0, 15, 0, "Regular Session"),
            TradingSession(SessionDay.WEDNESDAY, 9, 0, 15, 0, "Regular Session"),
            TradingSession(SessionDay.THURSDAY, 9, 0, 15, 0, "Regular Session"),
            TradingSession(SessionDay.FRIDAY, 9, 0, 15, 0, "Regular Session"),
        ]

        self.schedules["^N225"] = MarketSchedule(
            ticker="^N225",
            market_type=MarketType.INDEX,
            timezone=Timezone.TOKYO,
            sessions=nikkei_sessions,
            lunch_break_start=(11, 30),
            lunch_break_end=(12, 30)
        )

    def _setup_crypto_markets(self) -> None:
        """Set up cryptocurrency trading schedules (24/7)."""
        crypto_tickers = ["BTC-USD", "SOL-USD", "ADA-USD", "ETH-USD"]

        for ticker in crypto_tickers:
            self.schedules[ticker] = MarketSchedule(
                ticker=ticker,
                market_type=MarketType.CRYPTO,
                timezone=Timezone.UTC,
                sessions=[],  # 24/7 markets have no restricted sessions
                is_24_7=True
            )

    def get_schedule(self, ticker: str) -> Optional[MarketSchedule]:
        """
        Get market schedule for a ticker.

        Args:
            ticker: Ticker symbol (e.g., "NQ=F", "^FTSE")

        Returns:
            MarketSchedule if found, None otherwise
        """
        return self.schedules.get(ticker)

    def get_all_tickers(self) -> List[str]:
        """Get list of all configured tickers."""
        return list(self.schedules.keys())

    def get_tickers_by_market_type(self, market_type: MarketType) -> List[str]:
        """Get all tickers for a specific market type."""
        return [
            ticker for ticker, schedule in self.schedules.items()
            if schedule.market_type == market_type
        ]

    def get_tickers_by_timezone(self, timezone: Timezone) -> List[str]:
        """Get all tickers trading in a specific timezone."""
        return [
            ticker for ticker, schedule in self.schedules.items()
            if schedule.timezone == timezone.value
        ]

    def add_schedule(self, schedule: MarketSchedule) -> None:
        """
        Add or update a market schedule.

        Allows runtime extension of market configuration without modifying
        hardcoded settings.

        Args:
            schedule: MarketSchedule object to add
        """
        self.schedules[schedule.ticker] = schedule

    def is_24_7_market(self, ticker: str) -> bool:
        """Check if a ticker trades 24/7."""
        schedule = self.get_schedule(ticker)
        return schedule.is_24_7 if schedule else False

    def get_market_timezone(self, ticker: str) -> Optional[str]:
        """Get market timezone for a ticker."""
        schedule = self.get_schedule(ticker)
        return schedule.timezone if schedule else None

    def list_all_schedules(self) -> List[str]:
        """Get human-readable list of all market schedules."""
        result = []

        for market_type in MarketType:
            tickers = self.get_tickers_by_market_type(market_type)
            if tickers:
                result.append(f"\n{market_type.value}:")
                for ticker in sorted(tickers):
                    schedule = self.get_schedule(ticker)
                    if schedule.is_24_7:
                        result.append(f"  {ticker}: 24/7 ({schedule.timezone})")
                    else:
                        sessions_summary = ", ".join([
                            s.day.name[:3] for s in schedule.sessions
                        ])
                        result.append(
                            f"  {ticker}: {sessions_summary} ({schedule.timezone})"
                        )

        return result


# Global instance
_market_config: Optional[MarketHoursConfig] = None


def get_market_config() -> MarketHoursConfig:
    """
    Get or create the global MarketHoursConfig instance.

    Uses lazy initialization pattern to avoid circular imports.
    """
    global _market_config
    if _market_config is None:
        _market_config = MarketHoursConfig()
    return _market_config
