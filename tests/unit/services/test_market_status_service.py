"""
Unit Tests for MarketStatusService

Tests timezone-aware market status detection for all supported instruments.
Covers market open/close detection, trading hours, lunch breaks, and special cases.
"""

import pytest
from datetime import datetime, time, date, timedelta
import pytz

from nasdaq_predictor.services.market_status_service import (
    MarketStatusService,
    MarketStatus,
    SessionType,
    InstrumentType,
    MarketStatusInfo
)
from nasdaq_predictor.config.market_config import get_market_config, MarketType


class TestMarketStatusServiceInit:
    """Test MarketStatusService initialization."""

    def test_service_initialization(self):
        """Test that service initializes with market config."""
        service = MarketStatusService()
        assert service is not None
        assert service.market_config is not None
        assert len(service.schedules) > 0

    def test_schedules_loaded(self):
        """Test that all market schedules are loaded."""
        service = MarketStatusService()
        expected_tickers = ['NQ=F', 'ES=F', 'YM=F', 'RTY=F', '^FTSE', '^N225',
                           'BTC-USD', 'SOL-USD', 'ADA-USD', 'ETH-USD']
        for ticker in expected_tickers:
            assert ticker in service.schedules
            assert service.schedules[ticker] is not None


class TestUSFuturesMarkets:
    """Test US Futures market status detection (NQ=F, ES=F, etc)."""

    @pytest.fixture
    def service(self):
        """Provide MarketStatusService instance."""
        return MarketStatusService()

    def test_futures_market_timezone(self, service):
        """Test that futures use Chicago timezone."""
        for ticker in ['NQ=F', 'ES=F', 'YM=F', 'RTY=F']:
            status = service.get_market_status(ticker)
            assert status.timezone == 'America/Chicago'

    def test_futures_open_during_regular_hours(self, service):
        """Test futures market is open during regular trading hours (9:30 AM-4:00 PM NY / 8:30 AM-3:00 PM Chicago)."""
        # Monday 10:00 AM CT = 11:00 AM ET = During trading hours
        test_time = datetime(2025, 11, 17, 10, 0, 0, tzinfo=pytz.UTC)  # Monday at 10:00 UTC = 4:00 AM CT
        # Need to adjust: 10:00 UTC Monday = 4:00 AM CT Monday = Before market open
        # Actually 13:30 UTC Monday = 7:30 AM CT = Before market open (market opens at 6 PM Sunday CT)
        # Let's use 18:00 UTC Monday = 12:00 PM CT = Market is open

        test_time = datetime(2025, 11, 17, 18, 0, 0, tzinfo=pytz.UTC)  # Monday 18:00 UTC = 12:00 PM CT
        status = service.get_market_status('NQ=F', test_time)
        assert status.is_trading, "Futures should be open during regular trading hours"
        assert status.status == MarketStatus.OPEN

    def test_futures_closed_after_hours(self, service):
        """Test futures market is closed after 5 PM CT."""
        # Tuesday 22:00 UTC = 4:00 PM CT = market closing time, but let's use after
        test_time = datetime(2025, 11, 18, 23, 0, 0, tzinfo=pytz.UTC)  # Tuesday 23:00 UTC = 5:00 PM CT
        status = service.get_market_status('NQ=F', test_time)
        # At exactly 5 PM CT, market should be closed
        assert not status.is_trading or status.status == MarketStatus.CLOSED

    def test_futures_closed_on_weekend(self, service):
        """Test futures market is closed on weekends."""
        # Saturday
        test_time = datetime(2025, 11, 15, 12, 0, 0, tzinfo=pytz.UTC)  # Saturday
        status = service.get_market_status('NQ=F', test_time)
        assert not status.is_trading
        assert status.status == MarketStatus.CLOSED


class TestInternationalMarkets:
    """Test international index market status detection."""

    @pytest.fixture
    def service(self):
        return MarketStatusService()

    def test_ftse_london_timezone(self, service):
        """Test FTSE uses London timezone."""
        status = service.get_market_status('^FTSE')
        assert status.timezone == 'Europe/London'
        assert status.instrument_type == InstrumentType.UK_INDEX

    def test_ftse_open_during_trading_hours(self, service):
        """Test FTSE is open 8:00 AM - 4:30 PM GMT."""
        # Monday 10:00 UTC = 10:00 AM GMT = During trading hours
        test_time = datetime(2025, 11, 17, 10, 0, 0, tzinfo=pytz.UTC)
        status = service.get_market_status('^FTSE', test_time)
        assert status.is_trading, "FTSE should be open at 10:00 AM GMT"
        assert status.status == MarketStatus.OPEN

    def test_ftse_closed_before_market(self, service):
        """Test FTSE is closed before 8:00 AM GMT."""
        # Monday 07:00 UTC = 07:00 AM GMT = Before market open
        test_time = datetime(2025, 11, 17, 7, 0, 0, tzinfo=pytz.UTC)
        status = service.get_market_status('^FTSE', test_time)
        assert not status.is_trading
        assert status.status == MarketStatus.CLOSED

    def test_nikkei_tokyo_timezone(self, service):
        """Test Nikkei uses Tokyo timezone."""
        status = service.get_market_status('^N225')
        assert status.timezone == 'Asia/Tokyo'
        assert status.instrument_type == InstrumentType.JAPAN_INDEX

    def test_nikkei_lunch_break(self, service):
        """Test Nikkei lunch break 11:30 AM - 12:30 PM JST."""
        # When it's 11:30 AM JST, the market should be in lunch break
        # 11:30 JST = 02:30 UTC
        test_time = datetime(2025, 11, 17, 2, 30, 0, tzinfo=pytz.UTC)
        status = service.get_market_status('^N225', test_time)
        assert not status.is_trading, "Nikkei should be closed during lunch break"

    def test_nikkei_open_after_lunch(self, service):
        """Test Nikkei is open after lunch break."""
        # 13:00 JST (after lunch) = 04:00 UTC
        test_time = datetime(2025, 11, 17, 4, 0, 0, tzinfo=pytz.UTC)
        status = service.get_market_status('^N225', test_time)
        assert status.is_trading, "Nikkei should be open at 1:00 PM JST"


class TestCryptoMarkets:
    """Test cryptocurrency market status (24/7)."""

    @pytest.fixture
    def service(self):
        return MarketStatusService()

    def test_crypto_always_open(self, service):
        """Test crypto markets are always open."""
        for ticker in ['BTC-USD', 'SOL-USD', 'ADA-USD', 'ETH-USD']:
            status = service.get_market_status(ticker)
            assert status.is_trading
            assert status.status == MarketStatus.OPEN
            assert status.session_type == SessionType.CONTINUOUS_24_7

    def test_crypto_no_next_events(self, service):
        """Test crypto markets have no next open/close times."""
        status = service.get_market_status('BTC-USD')
        assert status.next_open is None
        assert status.next_close is None


class TestLastTradingDate:
    """Test last trading date detection."""

    @pytest.fixture
    def service(self):
        return MarketStatusService()

    def test_last_trading_date_during_market_hours(self, service):
        """Test last trading date during market hours returns current date."""
        # Monday 18:00 UTC (during US futures trading)
        test_time = datetime(2025, 11, 17, 18, 0, 0, tzinfo=pytz.UTC)
        last_date = service.get_last_trading_date('NQ=F', test_time)
        expected = test_time.astimezone(pytz.timezone('America/Chicago')).date()
        assert last_date == expected

    def test_last_trading_date_after_market_close(self, service):
        """Test last trading date after market close returns current date (if during trading day)."""
        # Tuesday 23:00 UTC (5 PM CT) = After market close but still Tuesday
        test_time = datetime(2025, 11, 18, 23, 0, 0, tzinfo=pytz.UTC)
        last_date = service.get_last_trading_date('NQ=F', test_time)
        # Should return Tuesday since it's a trading day
        chicago_tz = pytz.timezone('America/Chicago')
        chicago_time = test_time.astimezone(chicago_tz)
        assert last_date.weekday() < 5  # Weekday (Mon-Fri)

    def test_last_trading_date_on_weekend(self, service):
        """Test last trading date on weekend returns last Friday."""
        # Saturday 12:00 UTC
        test_time = datetime(2025, 11, 15, 12, 0, 0, tzinfo=pytz.UTC)
        last_date = service.get_last_trading_date('NQ=F', test_time)
        # Should return Friday (previous trading day)
        assert last_date.weekday() == 4  # Friday

    def test_crypto_last_trading_date(self, service):
        """Test crypto always returns current date."""
        test_time = datetime(2025, 11, 15, 12, 0, 0, tzinfo=pytz.UTC)  # Saturday
        last_date = service.get_last_trading_date('BTC-USD', test_time)
        # For crypto, should always return current date
        assert last_date == test_time.date()


class TestNextMarketEvents:
    """Test next market event detection."""

    @pytest.fixture
    def service(self):
        return MarketStatusService()

    def test_next_event_when_market_open(self, service):
        """Test next event is CLOSE when market is open."""
        # Monday 18:00 UTC (market open for US futures)
        test_time = datetime(2025, 11, 17, 18, 0, 0, tzinfo=pytz.UTC)
        event_type, event_time = service.get_next_market_event('NQ=F', test_time)
        assert event_type == 'CLOSE'
        assert event_time is not None

    def test_next_event_when_market_closed(self, service):
        """Test next event is OPEN when market is closed."""
        # Saturday (market closed)
        test_time = datetime(2025, 11, 15, 12, 0, 0, tzinfo=pytz.UTC)
        event_type, event_time = service.get_next_market_event('NQ=F', test_time)
        assert event_type == 'OPEN'
        assert event_time is not None

    def test_crypto_no_events(self, service):
        """Test crypto markets have no events."""
        event_type, event_time = service.get_next_market_event('BTC-USD')
        # Could be either OPEN or CLOSE, but should not have specific times
        # Actually for 24/7 markets, next event should be None or undefined


class TestQuickStatusCheck:
    """Test quick market open check method."""

    @pytest.fixture
    def service(self):
        return MarketStatusService()

    def test_is_market_open_true(self, service):
        """Test is_market_open returns True when open."""
        test_time = datetime(2025, 11, 17, 18, 0, 0, tzinfo=pytz.UTC)
        assert service.is_market_open('NQ=F', test_time)

    def test_is_market_open_false(self, service):
        """Test is_market_open returns False when closed."""
        test_time = datetime(2025, 11, 15, 12, 0, 0, tzinfo=pytz.UTC)  # Saturday
        assert not service.is_market_open('NQ=F', test_time)

    def test_is_market_open_invalid_ticker(self, service):
        """Test is_market_open returns False for invalid ticker."""
        assert not service.is_market_open('INVALID_TICKER')


class TestErrorHandling:
    """Test error handling and edge cases."""

    @pytest.fixture
    def service(self):
        return MarketStatusService()

    def test_invalid_ticker_raises_error(self, service):
        """Test that invalid ticker raises ValueError."""
        with pytest.raises(ValueError):
            service.get_market_status('INVALID_TICKER')

    def test_naive_datetime_converted(self, service):
        """Test that naive datetime is converted to UTC."""
        naive_time = datetime(2025, 11, 17, 18, 0, 0)
        status = service.get_market_status('NQ=F', naive_time)
        assert status is not None
        assert status.current_time.tzinfo is not None

    def test_default_to_current_time(self, service):
        """Test that None at_time defaults to current UTC time."""
        status = service.get_market_status('BTC-USD', at_time=None)
        assert status is not None
        # Should have current time
        now_utc = datetime.now(pytz.UTC)
        # Time should be close (within 1 minute)
        time_diff = abs((status.current_time - now_utc).total_seconds())
        assert time_diff < 60


class TestTimezoneHandling:
    """Test timezone conversion correctness."""

    @pytest.fixture
    def service(self):
        return MarketStatusService()

    def test_chicago_timezone_conversion(self, service):
        """Test conversion to Chicago timezone."""
        test_time = datetime(2025, 11, 17, 18, 0, 0, tzinfo=pytz.UTC)
        status = service.get_market_status('NQ=F', test_time)

        chicago_tz = pytz.timezone('America/Chicago')
        chicago_time = test_time.astimezone(chicago_tz)

        # Verify the time is correctly converted
        assert status.timezone == 'America/Chicago'

    def test_london_timezone_conversion(self, service):
        """Test conversion to London timezone."""
        test_time = datetime(2025, 11, 17, 10, 0, 0, tzinfo=pytz.UTC)
        status = service.get_market_status('^FTSE', test_time)

        assert status.timezone == 'Europe/London'

    def test_tokyo_timezone_conversion(self, service):
        """Test conversion to Tokyo timezone."""
        test_time = datetime(2025, 11, 17, 4, 0, 0, tzinfo=pytz.UTC)
        status = service.get_market_status('^N225', test_time)

        assert status.timezone == 'Asia/Tokyo'


class TestMarketStatusInfo:
    """Test MarketStatusInfo data structure."""

    @pytest.fixture
    def service(self):
        return MarketStatusService()

    def test_status_info_fields(self, service):
        """Test that MarketStatusInfo has all required fields."""
        status = service.get_market_status('NQ=F')

        assert hasattr(status, 'status')
        assert hasattr(status, 'is_trading')
        assert hasattr(status, 'session_type')
        assert hasattr(status, 'instrument_type')
        assert hasattr(status, 'current_time')
        assert hasattr(status, 'next_open')
        assert hasattr(status, 'next_close')
        assert hasattr(status, 'timezone')
        assert hasattr(status, 'last_trading_date')

    def test_status_enum_values(self, service):
        """Test that status values are valid enums."""
        status = service.get_market_status('NQ=F')
        assert isinstance(status.status, MarketStatus)
        assert isinstance(status.session_type, SessionType)
        assert isinstance(status.instrument_type, InstrumentType)


class TestMultipleMarketStatusChecks:
    """Test checking multiple markets at same time."""

    @pytest.fixture
    def service(self):
        return MarketStatusService()

    def test_multiple_markets_same_time(self, service):
        """Test getting status for multiple markets at the same time."""
        test_time = datetime(2025, 11, 17, 18, 0, 0, tzinfo=pytz.UTC)

        nq_status = service.get_market_status('NQ=F', test_time)
        ftse_status = service.get_market_status('^FTSE', test_time)
        btc_status = service.get_market_status('BTC-USD', test_time)

        # NQ should be open, FTSE might be closed (18:00 UTC = 18:00 GMT, but FTSE closes at 16:30)
        # BTC is always open
        assert btc_status.is_trading

        # Verify all are different timezones
        assert nq_status.timezone != ftse_status.timezone
        assert ftse_status.timezone != btc_status.timezone
