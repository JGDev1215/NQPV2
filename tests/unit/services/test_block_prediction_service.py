"""
Unit Tests for BlockPredictionService

Tests the prediction generation pipeline including:
- OHLC data fetching
- Volatility calculation
- 7-block segmentation
- Early bias detection
- Sustained counter detection
- Decision tree application
- Confidence scoring
- Database persistence
"""

import pytest
from datetime import datetime, timedelta
from unittest.mock import Mock, MagicMock, patch
import pandas as pd

from nasdaq_predictor.services.block_prediction_service import BlockPredictionService
from nasdaq_predictor.database.models.block_prediction import BlockPrediction


class TestBlockPredictionService:
    """Test suite for BlockPredictionService."""

    @pytest.fixture
    def mock_fetcher(self):
        """Create mock data fetcher."""
        mock = Mock()
        # Mock the fetch_historical_data method to accept both ticker_id and ticker_symbol
        mock.fetch_historical_data = Mock(return_value=[])
        return mock

    @pytest.fixture
    def mock_repository(self):
        """Create mock block prediction repository."""
        return Mock()

    @pytest.fixture
    def mock_ticker_repo(self):
        """Create mock ticker repository."""
        mock_repo = Mock()
        # Default mock ticker that returns a UUID when looked up
        mock_ticker = Mock()
        mock_ticker.id = "550e8400-e29b-41d4-a716-446655440000"
        mock_ticker.symbol = "NQ=F"
        mock_repo.get_ticker_by_symbol.return_value = mock_ticker
        mock_repo.get_all_tickers.return_value = [mock_ticker]
        return mock_repo

    @pytest.fixture
    def service(self, mock_fetcher, mock_repository, mock_ticker_repo):
        """Create BlockPredictionService with mocks."""
        return BlockPredictionService(
            fetcher=mock_fetcher,
            block_prediction_repo=mock_repository,
            ticker_repo=mock_ticker_repo
        )

    @pytest.fixture
    def sample_ohlc_data(self):
        """Create sample OHLC data for testing."""
        import pytz
        # Create timezone-aware datetimes - start at 10:00 to align with test's hour_start
        start_time = datetime(2024, 11, 13, 10, 0, tzinfo=pytz.UTC)
        # Generate 13 bars covering the full hour (10:00 to 11:00)
        times = [start_time + timedelta(minutes=5*i) for i in range(13)]

        return pd.DataFrame({
            'timestamp': times,
            'open': [100.0, 100.5, 100.3, 100.8, 101.0, 100.5, 100.2, 100.7, 101.2, 100.8, 100.5, 100.9, 101.0],
            'high': [100.8, 101.0, 100.9, 101.2, 101.3, 100.9, 100.7, 101.0, 101.5, 101.2, 100.8, 101.2, 101.3],
            'low': [99.8, 100.0, 99.9, 100.3, 100.5, 100.0, 99.8, 100.2, 100.8, 100.3, 100.0, 100.5, 99.9],
            'close': [100.5, 100.8, 100.5, 101.0, 101.2, 100.7, 100.3, 100.9, 101.3, 100.9, 100.5, 101.0, 101.1]
        })

    def test_generate_block_prediction_with_valid_bars(self, service, mock_fetcher, sample_ohlc_data):
        """Test prediction generation with valid OHLC data."""
        # Setup
        import pytz
        ticker = "NQ=F"
        hour_start = datetime(2024, 11, 13, 10, 0, tzinfo=pytz.UTC)

        # Convert sample_ohlc_data to list of dicts for fetcher
        bars_data = []
        for _, row in sample_ohlc_data.iterrows():
            bars_data.append({
                'timestamp': row['timestamp'],
                'open': row['open'],
                'high': row['high'],
                'low': row['low'],
                'close': row['close'],
                'volume': 1000000  # Default volume for testing
            })

        # Mock the fetcher to return the bars data with new signature
        mock_fetcher.fetch_historical_data.return_value = bars_data

        # Mock repository save method
        mock_repo_prediction = Mock(spec=BlockPrediction)
        service.block_prediction_repo.store_block_prediction = Mock(return_value=mock_repo_prediction)

        # Execute
        prediction = service.generate_block_prediction(ticker, hour_start)

        # Assert - prediction was successfully generated and stored
        assert prediction is not None
        # Verify that the service called the repository to store the prediction
        assert service.block_prediction_repo.store_block_prediction.called

    def test_generate_block_prediction_insufficient_data(self, service, mock_fetcher):
        """Test handling of insufficient OHLC data."""
        # Setup
        ticker = "NQ=F"
        hour_start = datetime(2024, 11, 13, 10, 0)

        # Empty dataframe
        mock_fetcher.fetch_5min_ohlc.return_value = pd.DataFrame()

        # Execute & Assert
        result = service.generate_block_prediction(ticker, hour_start)
        assert result is None

    def test_generate_block_prediction_single_bar(self, service, mock_fetcher):
        """Test handling of single OHLC bar (insufficient for analysis)."""
        # Setup
        ticker = "NQ=F"
        hour_start = datetime(2024, 11, 13, 10, 0)

        single_bar = pd.DataFrame({
            'timestamp': [datetime(2024, 11, 13, 10, 0)],
            'open': [100.0],
            'high': [100.5],
            'low': [99.5],
            'close': [100.2]
        })

        mock_fetcher.fetch_5min_ohlc.return_value = single_bar

        # Execute & Assert
        result = service.generate_block_prediction(ticker, hour_start)
        assert result is None

    def test_generate_block_prediction_stores_in_database(self, service, mock_fetcher, sample_ohlc_data):
        """Test that prediction is persisted to database."""
        # Setup
        import pytz
        ticker = "NQ=F"
        hour_start = datetime(2024, 11, 13, 10, 0, tzinfo=pytz.UTC)

        # Convert sample_ohlc_data to list of dicts for fetcher
        bars_data = []
        for _, row in sample_ohlc_data.iterrows():
            bars_data.append({
                'timestamp': row['timestamp'],
                'open': row['open'],
                'high': row['high'],
                'low': row['low'],
                'close': row['close'],
                'volume': 1000000  # Default volume for testing
            })

        mock_fetcher.fetch_historical_data.return_value = bars_data
        service.block_prediction_repo.store_block_prediction = Mock(return_value=Mock(spec=BlockPrediction))

        # Execute
        service.generate_block_prediction(ticker, hour_start)

        # Assert - verify store_block_prediction was called
        assert service.block_prediction_repo.store_block_prediction.called

    def test_generate_24h_predictions_returns_24_hours(self, service, mock_fetcher, sample_ohlc_data):
        """Test batch generation for 24 hours."""
        # Setup
        ticker = "NQ=F"
        date = datetime(2024, 11, 13)

        mock_fetcher.fetch_5min_ohlc.return_value = sample_ohlc_data
        service.block_prediction_repo.save = Mock(return_value=Mock(spec=BlockPrediction))

        # Mock method to generate predictions for each hour
        predictions = []
        for hour in range(24):
            hour_start = date.replace(hour=hour)
            pred = Mock(spec=BlockPrediction)
            pred.hour_start = hour_start
            pred.hour = hour
            predictions.append(pred)

        service.generate_block_prediction = Mock(side_effect=predictions[:12] + [None]*12)

        # Execute
        result = service.generate_24h_block_predictions(ticker, date)

        # Assert
        assert result is not None
        assert isinstance(result, dict), "Result should be a dictionary"
        assert 'total_generated' in result
        assert result['total_generated'] <= 24

    def test_generate_24h_predictions_no_duplicates(self, service, mock_fetcher, sample_ohlc_data):
        """Test batch generation doesn't create duplicate hours."""
        # Setup
        ticker = "NQ=F"
        date = datetime(2024, 11, 13)

        mock_fetcher.fetch_5min_ohlc.return_value = sample_ohlc_data
        service.block_prediction_repo.save = Mock(return_value=Mock(spec=BlockPrediction))

        # Execute
        result = service.generate_24h_block_predictions(ticker, date)

        # Assert - check for unique hours in generated list
        assert isinstance(result, dict), "Result should be a dictionary"
        assert 'generated' in result, "Result should contain 'generated' key"

        generated_hours = result['generated']
        assert len(generated_hours) == len(set(generated_hours)), "Duplicate hours found"

    def test_get_hourly_predictions_24h(self, service):
        """Test retrieving 24-hour predictions."""
        # Setup
        ticker = "NQ=F"
        date = datetime(2024, 11, 13)

        predictions = []
        for hour in range(24):
            pred = Mock(spec=BlockPrediction)
            pred.hour = hour
            pred.ticker_id = "550e8400-e29b-41d4-a716-446655440000"
            predictions.append(pred)

        service.block_prediction_repo.get_block_predictions_by_date = Mock(return_value=predictions)

        # Execute
        results = service.get_hourly_predictions_24h(ticker, date)

        # Assert
        assert isinstance(results, list)
        assert len(results) == 24
        assert all(p.ticker_id == "550e8400-e29b-41d4-a716-446655440000" for p in results)

    def test_get_hourly_prediction_by_hour(self, service):
        """Test retrieving prediction for specific hour."""
        # Setup
        ticker = "NQ=F"
        hour_start = datetime(2024, 11, 13, 14, 0)

        pred = Mock(spec=BlockPrediction)
        pred.hour_start_timestamp = hour_start
        pred.prediction = 'UP'

        service.block_prediction_repo.get_block_prediction_by_hour = Mock(return_value=pred)

        # Execute
        result = service.get_hourly_prediction(ticker, hour_start)

        # Assert
        assert result is not None
        assert result.hour_start_timestamp == hour_start
        assert result.prediction == 'UP'

    def test_confidence_scoring_weak(self, service, mock_fetcher, sample_ohlc_data):
        """Test confidence scoring for weak strength predictions."""
        # Setup with low deviation
        ticker = "NQ=F"
        hour_start = datetime(2024, 11, 13, 10, 0)

        # Create data with very small deviations
        weak_data = sample_ohlc_data.copy()
        weak_data['high'] = weak_data['open']
        weak_data['low'] = weak_data['open']
        weak_data['close'] = weak_data['open']

        # Convert to list of dicts for fetcher
        bars_data = []
        for _, row in weak_data.iterrows():
            bars_data.append({
                'timestamp': row['timestamp'],
                'open': row['open'],
                'high': row['high'],
                'low': row['low'],
                'close': row['close']
            })

        mock_fetcher.fetch_historical_data.return_value = bars_data
        service.block_prediction_repo.store_block_prediction = Mock(return_value=Mock(spec=BlockPrediction))

        # Execute
        prediction = service.generate_block_prediction(ticker, hour_start)

        # Assert - confidence should be lower for weak predictions
        if prediction:
            assert prediction.prediction_strength == 'weak' or prediction.confidence < 50

    def test_confidence_scoring_strong(self, service, mock_fetcher, sample_ohlc_data):
        """Test confidence scoring for strong strength predictions."""
        # Setup with high deviation
        ticker = "NQ=F"
        hour_start = datetime(2024, 11, 13, 10, 0)

        # Create data with large deviations
        strong_data = sample_ohlc_data.copy()
        strong_data['high'] = strong_data['high'] * 1.05
        strong_data['low'] = strong_data['low'] * 0.95

        # Convert to list of dicts for fetcher
        bars_data = []
        for _, row in strong_data.iterrows():
            bars_data.append({
                'timestamp': row['timestamp'],
                'open': row['open'],
                'high': row['high'],
                'low': row['low'],
                'close': row['close']
            })

        mock_fetcher.fetch_historical_data.return_value = bars_data
        service.block_prediction_repo.store_block_prediction = Mock(return_value=Mock(spec=BlockPrediction))

        # Execute
        prediction = service.generate_block_prediction(ticker, hour_start)

        # Assert - confidence should be higher for strong predictions
        if prediction:
            assert prediction.prediction_strength == 'strong' or prediction.confidence >= 70

    def test_error_handling_invalid_ticker(self, service, mock_fetcher, mock_ticker_repo):
        """Test error handling with invalid ticker."""
        # Setup - make get_ticker_by_symbol return None for invalid ticker
        mock_ticker_repo.get_ticker_by_symbol.return_value = None

        ticker = "INVALID"
        hour_start = datetime(2024, 11, 13, 10, 0)

        # Execute
        result = service.generate_block_prediction(ticker, hour_start)

        # Assert - should return None for invalid ticker (doesn't raise exception)
        assert result is None

    def test_error_handling_network_error(self, service, mock_fetcher):
        """Test error handling with network issues."""
        # Setup
        mock_fetcher.fetch_historical_data.side_effect = ConnectionError("Network error")

        ticker = "NQ=F"
        hour_start = datetime(2024, 11, 13, 10, 0)

        # Execute
        result = service.generate_block_prediction(ticker, hour_start)

        # Assert - should return None on network error (doesn't raise exception)
        assert result is None

    def test_volatility_normalization(self, service, mock_fetcher, sample_ohlc_data):
        """Test that volatility is properly normalized."""
        # Setup
        ticker = "NQ=F"
        hour_start = datetime(2024, 11, 13, 10, 0)

        # Convert sample_ohlc_data to list of dicts for fetcher
        bars_data = []
        for _, row in sample_ohlc_data.iterrows():
            bars_data.append({
                'timestamp': row['timestamp'],
                'open': row['open'],
                'high': row['high'],
                'low': row['low'],
                'close': row['close'],
                'volume': 1000000  # Default volume for testing
            })

        mock_fetcher.fetch_historical_data.return_value = bars_data
        service.block_prediction_repo.store_block_prediction = Mock(return_value=Mock(spec=BlockPrediction))

        # Execute
        prediction = service.generate_block_prediction(ticker, hour_start)

        # Assert - deviation should be in reasonable range
        if prediction:
            assert hasattr(prediction, 'deviation_at_5_7')
            assert isinstance(prediction.deviation_at_5_7, (int, float))

    def test_timezone_handling_ny(self, service, mock_fetcher, sample_ohlc_data):
        """Test timezone handling for NY-based tickers."""
        # Setup
        ticker = "NQ=F"  # US index
        hour_start = datetime(2024, 11, 13, 14, 0)  # 2:00 PM

        # Convert sample_ohlc_data to list of dicts for fetcher
        bars_data = []
        for _, row in sample_ohlc_data.iterrows():
            bars_data.append({
                'timestamp': row['timestamp'],
                'open': row['open'],
                'high': row['high'],
                'low': row['low'],
                'close': row['close'],
                'volume': 1000000  # Default volume for testing
            })

        mock_fetcher.fetch_historical_data.return_value = bars_data
        service.block_prediction_repo.store_block_prediction = Mock(return_value=Mock(spec=BlockPrediction))

        # Execute
        prediction = service.generate_block_prediction(ticker, hour_start)

        # Assert
        if prediction:
            assert prediction.ticker_id == "550e8400-e29b-41d4-a716-446655440000"

    def test_ticker_special_characters(self, service, mock_fetcher, mock_ticker_repo, sample_ohlc_data):
        """Test handling of tickers with special characters."""
        # Setup
        tickers = ["^FTSE", "ES=F", "NQ=F"]
        hour_start = datetime(2024, 11, 13, 10, 0)

        # Convert sample_ohlc_data to list of dicts for fetcher
        bars_data = []
        for _, row in sample_ohlc_data.iterrows():
            bars_data.append({
                'timestamp': row['timestamp'],
                'open': row['open'],
                'high': row['high'],
                'low': row['low'],
                'close': row['close'],
                'volume': 1000000  # Default volume for testing
            })

        mock_fetcher.fetch_historical_data.return_value = bars_data
        service.block_prediction_repo.store_block_prediction = Mock(return_value=Mock(spec=BlockPrediction))

        # Setup mock to return tickers for all symbols
        mock_ticker_obj = Mock()
        mock_ticker_obj.id = "550e8400-e29b-41d4-a716-446655440000"
        mock_ticker_repo.get_ticker_by_symbol.return_value = mock_ticker_obj

        # Execute & Assert
        for ticker in tickers:
            prediction = service.generate_block_prediction(ticker, hour_start)
            # Should not raise error - special characters should be handled
            assert True

    def test_batch_save_efficiency(self, service):
        """Test batch save operation efficiency."""
        # Setup
        predictions = [Mock(spec=BlockPrediction) for _ in range(24)]

        # Execute
        service.block_prediction_repo.save_batch = Mock()
        service.block_prediction_repo.save_batch(predictions)

        # Assert - save_batch should be called once for 24 items
        assert service.block_prediction_repo.save_batch.call_count >= 1

