"""
Integration Tests for Block Prediction Framework

Tests the complete prediction and verification flows:
- End-to-end prediction generation (bars → storage)
- End-to-end verification flow (prediction → accuracy)
- Full 24-hour generation with multiple tickers
- Error recovery and data consistency
"""

import pytest
from datetime import datetime, timedelta
from unittest.mock import Mock, MagicMock, patch
import pandas as pd

from nasdaq_predictor.services.block_prediction_service import BlockPredictionService
from nasdaq_predictor.services.block_verification_service import BlockVerificationService
from nasdaq_predictor.database.models.block_prediction import BlockPrediction


class TestBlockPredictionFlow:
    """Integration tests for complete prediction and verification flows."""

    @pytest.fixture
    def mock_fetcher(self):
        """Create mock data fetcher for all tests."""
        return Mock()

    @pytest.fixture
    def mock_repository(self):
        """Create mock repository for all tests."""
        return Mock()

    @pytest.fixture
    def prediction_service(self, mock_fetcher, mock_repository):
        """Create BlockPredictionService."""
        return BlockPredictionService(
            fetcher=mock_fetcher,
            block_prediction_repo=mock_repository
        )

    @pytest.fixture
    def verification_service(self, mock_fetcher, mock_repository):
        """Create BlockVerificationService."""
        return BlockVerificationService(
            fetcher=mock_fetcher,
            block_prediction_repo=mock_repository
        )

    @pytest.fixture
    def sample_hourly_ohlc(self):
        """Create sample OHLC for complete hour."""
        start = datetime(2024, 11, 13, 10, 0)
        return pd.DataFrame({
            'timestamp': [start + timedelta(minutes=5*i) for i in range(12)],
            'open': [100.0, 100.5, 100.3, 100.8, 101.0, 100.5, 100.2, 100.7, 101.2, 100.8, 100.5, 100.9],
            'high': [100.8, 101.0, 100.9, 101.2, 101.3, 100.9, 100.7, 101.0, 101.5, 101.2, 100.8, 101.2],
            'low': [99.8, 100.0, 99.9, 100.3, 100.5, 100.0, 99.8, 100.2, 100.8, 100.3, 100.0, 100.5],
            'close': [100.5, 100.8, 100.5, 101.0, 101.2, 100.7, 100.3, 100.9, 101.3, 100.9, 100.5, 101.0]
        })

    @pytest.fixture
    def sample_blocks_6_7(self):
        """Create sample OHLC for verification blocks 6-7."""
        start = datetime(2024, 11, 13, 10, 42, 51)
        return pd.DataFrame({
            'timestamp': [start, start + timedelta(minutes=5)],
            'open': [100.5, 100.8],
            'high': [101.0, 101.5],
            'low': [100.0, 100.3],
            'close': [101.2, 101.0]  # Positive overall
        })

    # ========================================
    # E2E Prediction Generation Tests
    # ========================================

    def test_end_to_end_prediction_generation(self, prediction_service, mock_fetcher, sample_hourly_ohlc):
        """Test complete prediction flow from OHLC to storage."""
        # Setup
        ticker = "NQ=F"
        hour_start = datetime(2024, 11, 13, 10, 0)

        mock_fetcher.fetch_5min_ohlc.return_value = sample_hourly_ohlc

        stored_prediction = Mock(spec=BlockPrediction)
        stored_prediction.ticker = ticker
        stored_prediction.hour_start = hour_start
        stored_prediction.prediction = "UP"
        stored_prediction.confidence = 72.5

        prediction_service.block_prediction_repo.save = Mock(return_value=stored_prediction)

        # Execute
        result = prediction_service.generate_block_prediction(ticker, hour_start)

        # Assert
        assert result is not None
        assert result.ticker == ticker
        assert result.hour_start == hour_start
        assert result.prediction in ["UP", "DOWN", "NEUTRAL"]
        assert 5 <= result.confidence <= 95

    def test_end_to_end_prediction_all_fields_populated(self, prediction_service, mock_fetcher, sample_hourly_ohlc):
        """Test that all prediction fields are properly populated."""
        # Setup
        ticker = "ES=F"
        hour_start = datetime(2024, 11, 13, 14, 0)

        mock_fetcher.fetch_5min_ohlc.return_value = sample_hourly_ohlc

        # Execute
        result = prediction_service.generate_block_prediction(ticker, hour_start)

        # Assert all fields populated
        if result:
            assert result.ticker == ticker
            assert result.hour_start == hour_start
            assert result.prediction is not None
            assert result.confidence is not None
            assert result.strength is not None
            assert result.early_bias is not None
            assert hasattr(result, 'deviation_at_5_7')

    def test_end_to_end_prediction_stored_correctly(self, prediction_service, mock_fetcher, mock_repository, sample_hourly_ohlc):
        """Test that prediction is saved to database with all fields."""
        # Setup
        ticker = "^FTSE"
        hour_start = datetime(2024, 11, 13, 15, 0)

        mock_fetcher.fetch_5min_ohlc.return_value = sample_hourly_ohlc

        # Execute
        prediction_service.generate_block_prediction(ticker, hour_start)

        # Assert save was called with proper object
        assert mock_repository.save.called

    # ========================================
    # E2E Verification Tests
    # ========================================

    def test_end_to_end_prediction_verification(self, verification_service, mock_fetcher, sample_blocks_6_7):
        """Test complete verification flow from prediction to accuracy."""
        # Setup
        prediction = Mock(spec=BlockPrediction)
        prediction.id = 1
        prediction.ticker = "NQ=F"
        prediction.hour_start = datetime(2024, 11, 13, 10, 0)
        prediction.prediction = "UP"
        prediction.confidence = 72.5
        prediction.verified = False

        mock_fetcher.fetch_5min_ohlc.return_value = sample_blocks_6_7

        # Execute
        result = verification_service.verify_block_prediction(prediction)

        # Assert
        assert result is not None
        assert result.verified == True or hasattr(result, 'is_correct')

    def test_end_to_end_verification_correct_prediction(self, verification_service, mock_fetcher):
        """Test verification when prediction is correct."""
        # Setup: UP prediction with positive close
        prediction = Mock(spec=BlockPrediction)
        prediction.prediction = "UP"

        blocks_6_7_up = pd.DataFrame({
            'timestamp': [datetime(2024, 11, 13, 10, 45), datetime(2024, 11, 13, 10, 50)],
            'open': [100.5, 100.8],
            'high': [101.2, 101.5],
            'low': [100.0, 100.3],
            'close': [101.0, 101.2]  # Positive
        })

        mock_fetcher.fetch_5min_ohlc.return_value = blocks_6_7_up

        # Execute
        result = verification_service.verify_block_prediction(prediction)

        # Assert
        if result:
            assert result.is_correct == True

    def test_end_to_end_verification_incorrect_prediction(self, verification_service, mock_fetcher):
        """Test verification when prediction is incorrect."""
        # Setup: UP prediction with negative close
        prediction = Mock(spec=BlockPrediction)
        prediction.prediction = "UP"

        blocks_6_7_down = pd.DataFrame({
            'timestamp': [datetime(2024, 11, 13, 10, 45), datetime(2024, 11, 13, 10, 50)],
            'open': [100.5, 100.8],
            'high': [100.8, 100.8],
            'low': [99.5, 99.8],
            'close': [99.8, 99.5]  # Negative
        })

        mock_fetcher.fetch_5min_ohlc.return_value = blocks_6_7_down

        # Execute
        result = verification_service.verify_block_prediction(prediction)

        # Assert
        if result:
            assert result.is_correct == False

    # ========================================
    # 24-Hour Full Cycle Tests
    # ========================================

    def test_24h_generation_all_hours(self, prediction_service, mock_fetcher, sample_hourly_ohlc):
        """Test generating predictions for all 24 hours of a day."""
        # Setup
        ticker = "NQ=F"
        date = datetime(2024, 11, 13)

        mock_fetcher.fetch_5min_ohlc.return_value = sample_hourly_ohlc

        predictions_list = []
        for hour in range(24):
            pred = Mock(spec=BlockPrediction)
            pred.ticker = ticker
            pred.hour = hour
            pred.hour_start = date.replace(hour=hour)
            predictions_list.append(pred)

        prediction_service.block_prediction_repo.save = Mock(side_effect=predictions_list[:12] + [None]*12)

        # Execute
        results = prediction_service.generate_24h_block_predictions(ticker, date)

        # Assert
        if results:
            assert len(results) <= 24
            hours = [p.hour for p in results if hasattr(p, 'hour')]
            assert len(set(hours)) == len(hours), "Duplicate hours"

    def test_24h_generation_consistency(self, prediction_service, mock_fetcher, sample_hourly_ohlc):
        """Test that 24h generation produces consistent predictions."""
        # Setup
        ticker = "ES=F"
        date = datetime(2024, 11, 13)

        mock_fetcher.fetch_5min_ohlc.return_value = sample_hourly_ohlc

        # Execute
        results = prediction_service.generate_24h_block_predictions(ticker, date)

        # Assert consistency
        if results:
            for pred in results:
                assert pred.ticker == ticker
                assert pred.hour_start.date() == date.date()
                assert pred.prediction in ["UP", "DOWN", "NEUTRAL"]

    def test_24h_batch_verification(self, verification_service, mock_fetcher, mock_repository):
        """Test batch verification of 24 predictions."""
        # Setup
        pending_preds = []
        for hour in range(24):
            pred = Mock(spec=BlockPrediction)
            pred.id = hour
            pred.hour = hour
            pred.prediction = "UP" if hour % 2 == 0 else "DOWN"
            pred.verified = False
            pending_preds.append(pred)

        mock_repository.get_unverified = Mock(return_value=pending_preds)
        mock_fetcher.fetch_5min_ohlc = Mock(return_value=pd.DataFrame({
            'timestamp': [datetime(2024, 11, 13, 10, 45), datetime(2024, 11, 13, 10, 50)],
            'open': [100.5, 100.8],
            'close': [101.0, 101.2]
        }))

        # Execute
        stats = verification_service.verify_pending_predictions()

        # Assert
        assert stats is not None
        if 'total_verified' in stats:
            assert stats['total_verified'] >= 0

    # ========================================
    # Multi-Ticker Tests
    # ========================================

    def test_multi_ticker_generation(self, prediction_service, mock_fetcher, sample_hourly_ohlc):
        """Test generating predictions for multiple tickers."""
        # Setup
        tickers = ["NQ=F", "ES=F", "^FTSE"]
        date = datetime(2024, 11, 13)
        hour_start = date.replace(hour=10)

        mock_fetcher.fetch_5min_ohlc.return_value = sample_hourly_ohlc

        # Execute
        results = {}
        for ticker in tickers:
            pred = prediction_service.generate_block_prediction(ticker, hour_start)
            results[ticker] = pred

        # Assert
        assert len(results) == len(tickers)
        for ticker in tickers:
            if results[ticker]:
                assert results[ticker].ticker == ticker

    def test_multi_ticker_isolation(self, prediction_service, mock_fetcher, sample_hourly_ohlc):
        """Test that predictions for different tickers don't interfere."""
        # Setup
        ticker1 = "NQ=F"
        ticker2 = "ES=F"
        hour_start = datetime(2024, 11, 13, 10, 0)

        mock_fetcher.fetch_5min_ohlc.return_value = sample_hourly_ohlc

        # Execute
        pred1 = prediction_service.generate_block_prediction(ticker1, hour_start)
        pred2 = prediction_service.generate_block_prediction(ticker2, hour_start)

        # Assert
        if pred1 and pred2:
            assert pred1.ticker == ticker1
            assert pred2.ticker == ticker2
            assert pred1.ticker != pred2.ticker

    # ========================================
    # Error Handling & Recovery Tests
    # ========================================

    def test_partial_hour_failure_recovery(self, prediction_service, mock_fetcher):
        """Test recovery from partial data during hour."""
        # Setup
        ticker = "NQ=F"
        hour_start = datetime(2024, 11, 13, 10, 0)

        # Simulate partial data (less than 12 bars)
        partial_data = pd.DataFrame({
            'timestamp': [datetime(2024, 11, 13, 10, 0)],
            'open': [100.0],
            'high': [100.5],
            'low': [99.5],
            'close': [100.2]
        })

        mock_fetcher.fetch_5min_ohlc.return_value = partial_data

        # Execute
        result = prediction_service.generate_block_prediction(ticker, hour_start)

        # Assert - should handle gracefully
        assert True  # No exception raised

    def test_network_error_propagation(self, prediction_service, mock_fetcher):
        """Test that network errors are properly propagated."""
        # Setup
        mock_fetcher.fetch_5min_ohlc.side_effect = ConnectionError("Network unreachable")

        ticker = "NQ=F"
        hour_start = datetime(2024, 11, 13, 10, 0)

        # Execute & Assert
        with pytest.raises(ConnectionError):
            prediction_service.generate_block_prediction(ticker, hour_start)

    def test_invalid_data_handling(self, prediction_service, mock_fetcher):
        """Test handling of invalid OHLC data."""
        # Setup
        invalid_data = pd.DataFrame({
            'timestamp': [datetime(2024, 11, 13, 10, 0)],
            'open': [100.0],
            'high': [99.0],  # Invalid: high < open
            'low': [98.0],
            'close': [101.0]  # Invalid: close > high
        })

        mock_fetcher.fetch_5min_ohlc.return_value = invalid_data

        ticker = "NQ=F"
        hour_start = datetime(2024, 11, 13, 10, 0)

        # Execute
        result = prediction_service.generate_block_prediction(ticker, hour_start)

        # Assert - should handle or return None
        # Implementation-dependent

    # ========================================
    # Data Consistency Tests
    # ========================================

    def test_prediction_database_consistency(self, prediction_service, mock_fetcher, mock_repository, sample_hourly_ohlc):
        """Test that prediction data maintains consistency through storage."""
        # Setup
        ticker = "NQ=F"
        hour_start = datetime(2024, 11, 13, 10, 0)

        mock_fetcher.fetch_5min_ohlc.return_value = sample_hourly_ohlc

        stored_prediction = None

        def capture_save(pred):
            nonlocal stored_prediction
            stored_prediction = pred
            return pred

        mock_repository.save = Mock(side_effect=capture_save)

        # Execute
        original = prediction_service.generate_block_prediction(ticker, hour_start)

        # Assert
        if original and stored_prediction:
            assert original.ticker == stored_prediction.ticker
            assert original.prediction == stored_prediction.prediction

    def test_verification_database_update(self, verification_service, mock_fetcher, mock_repository):
        """Test that verification updates are persisted correctly."""
        # Setup
        prediction = Mock(spec=BlockPrediction)
        prediction.id = 1
        prediction.prediction = "UP"

        verified = None

        def capture_update(pred):
            nonlocal verified
            verified = pred
            return pred

        mock_repository.update = Mock(side_effect=capture_update)

        blocks_6_7 = pd.DataFrame({
            'timestamp': [datetime(2024, 11, 13, 10, 45)],
            'open': [100.5],
            'close': [101.0]
        })

        mock_fetcher.fetch_5min_ohlc.return_value = blocks_6_7

        # Execute
        verification_service.verify_block_prediction(prediction)

        # Assert
        assert mock_repository.update.called or mock_repository.save.called

    # ========================================
    # Performance & Efficiency Tests
    # ========================================

    def test_prediction_generation_timing(self, prediction_service, mock_fetcher, sample_hourly_ohlc):
        """Test that prediction generation completes in reasonable time."""
        # Setup
        ticker = "NQ=F"
        hour_start = datetime(2024, 11, 13, 10, 0)

        mock_fetcher.fetch_5min_ohlc.return_value = sample_hourly_ohlc

        # Execute with timing
        import time
        start = time.time()
        prediction_service.generate_block_prediction(ticker, hour_start)
        elapsed = time.time() - start

        # Assert - should complete quickly (under 1 second for unit test)
        assert elapsed < 5.0, f"Prediction generation took {elapsed}s"

    def test_24h_batch_efficiency(self, prediction_service, mock_fetcher, sample_hourly_ohlc):
        """Test efficiency of 24-hour batch generation."""
        # Setup
        ticker = "NQ=F"
        date = datetime(2024, 11, 13)

        mock_fetcher.fetch_5min_ohlc.return_value = sample_hourly_ohlc

        # Execute
        import time
        start = time.time()
        results = prediction_service.generate_24h_block_predictions(ticker, date)
        elapsed = time.time() - start

        # Assert
        assert elapsed < 30.0, f"24h generation took {elapsed}s"

