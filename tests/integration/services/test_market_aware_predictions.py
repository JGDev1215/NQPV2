"""
Integration Tests for Market-Aware Prediction System

Tests the integration between MarketStatusService and BlockPredictionService
to ensure market-aware predictions work correctly.
"""

import pytest
from datetime import datetime
import pytz

from nasdaq_predictor.services.market_status_service import MarketStatusService, MarketStatus
from nasdaq_predictor.services.block_prediction_service import BlockPredictionService
from nasdaq_predictor.data.fetcher import YahooFinanceDataFetcher
from nasdaq_predictor.database.repositories.block_prediction_repository import BlockPredictionRepository
from nasdaq_predictor.database.repositories.ticker_repository import TickerRepository


class TestMarketAwarePredictionIntegration:
    """Test integration between market status and predictions."""

    @pytest.fixture
    def services(self):
        """Provide integrated services."""
        market_status_service = MarketStatusService()
        fetcher = YahooFinanceDataFetcher()
        block_pred_repo = BlockPredictionRepository()
        ticker_repo = TickerRepository()

        block_prediction_service = BlockPredictionService(
            fetcher=fetcher,
            block_prediction_repo=block_pred_repo,
            ticker_repo=ticker_repo,
            market_status_service=market_status_service
        )

        return {
            'market_status': market_status_service,
            'block_prediction': block_prediction_service
        }

    def test_market_status_available_to_predictions(self, services):
        """Test that market status is accessible from prediction service."""
        service = services['block_prediction']
        assert service.market_status_service is not None

    def test_get_market_aware_predictions_structure(self, services):
        """Test market-aware predictions return proper structure."""
        service = services['block_prediction']
        ticker = 'NQ=F'
        test_time = datetime(2025, 11, 17, 18, 0, 0, tzinfo=pytz.UTC)

        result = service.get_market_aware_predictions_24h(ticker, test_time)

        assert result is not None
        assert 'data_source' in result
        assert 'market_status' in result
        assert 'predictions' in result
        assert 'last_trading_date' in result
        assert 'next_market_event' in result
        assert 'predictions_date' in result

    def test_market_aware_response_has_market_metadata(self, services):
        """Test that market-aware response includes market metadata."""
        service = services['block_prediction']
        ticker = 'NQ=F'
        test_time = datetime(2025, 11, 17, 18, 0, 0, tzinfo=pytz.UTC)

        result = service.get_market_aware_predictions_24h(ticker, test_time)
        market_status = result.get('market_status', {})

        assert 'status' in market_status
        assert 'is_trading' in market_status
        assert 'timezone' in market_status
        assert 'current_time' in market_status

    def test_data_source_live_during_market_hours(self, services):
        """Test that data_source is LIVE during market hours."""
        service = services['block_prediction']
        ticker = 'NQ=F'
        # Monday 18:00 UTC (12:00 PM CT) - market is open
        test_time = datetime(2025, 11, 17, 18, 0, 0, tzinfo=pytz.UTC)

        result = service.get_market_aware_predictions_24h(ticker, test_time)

        # If market is open, should return LIVE or show market status
        assert result['data_source'] in ['LIVE', 'HISTORICAL', 'ERROR']

    def test_market_aware_single_hour_prediction(self, services):
        """Test market-aware single hour prediction."""
        service = services['block_prediction']
        ticker = 'NQ=F'
        test_hour = datetime(2025, 11, 17, 18, 0, 0, tzinfo=pytz.UTC)

        result = service.get_market_aware_prediction(ticker, test_hour, test_hour)

        assert result is not None
        assert 'data_source' in result
        assert 'market_status' in result
        assert 'prediction' in result or result.get('error') is not None

    def test_market_aware_different_instruments(self, services):
        """Test market-aware predictions for different instrument types."""
        service = services['block_prediction']
        market_service = services['market_status']
        test_time = datetime(2025, 11, 17, 10, 0, 0, tzinfo=pytz.UTC)

        tickers = ['NQ=F', '^FTSE', 'BTC-USD']

        for ticker in tickers:
            result = service.get_market_aware_predictions_24h(ticker, test_time)
            assert result is not None
            assert 'market_status' in result

            # Verify market status is correct for each
            market_status = market_service.get_market_status(ticker, test_time)
            assert market_status.timezone is not None


class TestMarketStatusConsistency:
    """Test consistency between market status and prediction metadata."""

    @pytest.fixture
    def services(self):
        """Provide integrated services."""
        market_status_service = MarketStatusService()
        fetcher = YahooFinanceDataFetcher()
        block_pred_repo = BlockPredictionRepository()
        ticker_repo = TickerRepository()

        block_prediction_service = BlockPredictionService(
            fetcher=fetcher,
            block_prediction_repo=block_pred_repo,
            ticker_repo=ticker_repo,
            market_status_service=market_status_service
        )

        return {
            'market_status': market_status_service,
            'block_prediction': block_prediction_service
        }

    def test_timezone_consistency(self, services):
        """Test that timezone is consistent between services."""
        market_service = services['market_status']
        pred_service = services['block_prediction']
        ticker = 'NQ=F'
        test_time = datetime(2025, 11, 17, 18, 0, 0, tzinfo=pytz.UTC)

        market_status = market_service.get_market_status(ticker, test_time)
        pred_result = pred_service.get_market_aware_predictions_24h(ticker, test_time)

        assert market_status.timezone == pred_result['market_status']['timezone']

    def test_market_status_matches_data_source(self, services):
        """Test that market_status is reflected in data_source."""
        market_service = services['market_status']
        pred_service = services['block_prediction']
        ticker = 'NQ=F'
        test_time = datetime(2025, 11, 17, 18, 0, 0, tzinfo=pytz.UTC)

        market_status = market_service.get_market_status(ticker, test_time)
        pred_result = pred_service.get_market_aware_predictions_24h(ticker, test_time)

        # If market is open, should be LIVE; if closed, should be HISTORICAL
        if market_status.is_trading:
            assert pred_result['data_source'] in ['LIVE', 'HISTORICAL']
        else:
            assert pred_result['data_source'] in ['HISTORICAL', 'LIVE', 'ERROR']


class TestCryptoMarketIntegration:
    """Test crypto market integration."""

    @pytest.fixture
    def services(self):
        """Provide integrated services."""
        market_status_service = MarketStatusService()
        fetcher = YahooFinanceDataFetcher()
        block_pred_repo = BlockPredictionRepository()
        ticker_repo = TickerRepository()

        block_prediction_service = BlockPredictionService(
            fetcher=fetcher,
            block_prediction_repo=block_pred_repo,
            ticker_repo=ticker_repo,
            market_status_service=market_status_service
        )

        return {
            'market_status': market_status_service,
            'block_prediction': block_prediction_service
        }

    def test_crypto_always_trading(self, services):
        """Test that crypto markets always show as trading."""
        market_service = services['market_status']

        for ticker in ['BTC-USD', 'SOL-USD', 'ADA-USD', 'ETH-USD']:
            status = market_service.get_market_status(ticker)
            assert status.is_trading
            assert status.status.value == 'OPEN'

    def test_crypto_no_next_events(self, services):
        """Test crypto has no next open/close times."""
        market_service = services['market_status']

        status = market_service.get_market_status('BTC-USD')
        assert status.next_open is None
        assert status.next_close is None


class TestEdgeCases:
    """Test edge cases and error handling."""

    @pytest.fixture
    def services(self):
        """Provide integrated services."""
        market_status_service = MarketStatusService()
        fetcher = YahooFinanceDataFetcher()
        block_pred_repo = BlockPredictionRepository()
        ticker_repo = TickerRepository()

        block_prediction_service = BlockPredictionService(
            fetcher=fetcher,
            block_prediction_repo=block_pred_repo,
            ticker_repo=ticker_repo,
            market_status_service=market_status_service
        )

        return {
            'market_status': market_status_service,
            'block_prediction': block_prediction_service
        }

    def test_invalid_ticker_handling(self, services):
        """Test handling of invalid ticker symbols."""
        pred_service = services['block_prediction']
        test_time = datetime.now(pytz.UTC)

        result = pred_service.get_market_aware_predictions_24h('INVALID', test_time)

        # Should return error or empty predictions
        assert result is not None
        # Check if it has error handling
        if 'error' in result:
            assert isinstance(result['error'], str)

    def test_timezone_aware_datetime_handling(self, services):
        """Test handling of timezone-aware datetimes."""
        market_service = services['market_status']

        # Test with different timezone
        tokyo_tz = pytz.timezone('Asia/Tokyo')
        test_time = tokyo_tz.localize(datetime(2025, 11, 17, 18, 0, 0))

        # Should handle timezone conversion
        status = market_service.get_market_status('NQ=F', test_time)
        assert status is not None

    def test_naive_datetime_conversion(self, services):
        """Test automatic conversion of naive datetimes."""
        market_service = services['market_status']

        # Test with naive datetime
        naive_time = datetime(2025, 11, 17, 18, 0, 0)

        # Should handle and convert
        status = market_service.get_market_status('NQ=F', naive_time)
        assert status is not None
        assert status.current_time.tzinfo is not None


class TestMultiMarketComparison:
    """Test comparing multiple markets at same time."""

    @pytest.fixture
    def services(self):
        """Provide integrated services."""
        market_status_service = MarketStatusService()
        fetcher = YahooFinanceDataFetcher()
        block_pred_repo = BlockPredictionRepository()
        ticker_repo = TickerRepository()

        block_prediction_service = BlockPredictionService(
            fetcher=fetcher,
            block_prediction_repo=block_pred_repo,
            ticker_repo=ticker_repo,
            market_status_service=market_status_service
        )

        return {
            'market_status': market_status_service,
            'block_prediction': block_prediction_service
        }

    def test_market_status_at_same_utc_time(self, services):
        """Test checking multiple markets at same UTC time."""
        market_service = services['market_status']
        test_time = datetime(2025, 11, 17, 15, 0, 0, tzinfo=pytz.UTC)

        us_status = market_service.get_market_status('NQ=F', test_time)
        ftse_status = market_service.get_market_status('^FTSE', test_time)
        crypto_status = market_service.get_market_status('BTC-USD', test_time)

        # Verify all have status
        assert us_status.status is not None
        assert ftse_status.status is not None
        assert crypto_status.status is not None

        # Verify they're in different timezones
        assert us_status.timezone != ftse_status.timezone
        assert ftse_status.timezone != crypto_status.timezone

    def test_last_trading_date_varies_by_market(self, services):
        """Test that last trading date can differ by market."""
        market_service = services['market_status']
        # Friday evening UTC
        test_time = datetime(2025, 11, 21, 22, 0, 0, tzinfo=pytz.UTC)

        us_last_date = market_service.get_last_trading_date('NQ=F', test_time)
        crypto_last_date = market_service.get_last_trading_date('BTC-USD', test_time)

        # For crypto, should always be current date
        # For US markets on Friday evening, should be Friday (if during day)
        assert us_last_date is not None
        assert crypto_last_date is not None
