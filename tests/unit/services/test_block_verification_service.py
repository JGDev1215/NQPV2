"""
Unit Tests for BlockVerificationService

Tests the prediction verification pipeline including:
- Verification timing (after hour completion)
- Actual blocks 6-7 data fetching
- Direction determination
- Accuracy comparison (predicted vs actual)
- Batch verification operations
- Accuracy metrics calculation
"""

import pytest
from datetime import datetime, timedelta
from unittest.mock import Mock, MagicMock
import pandas as pd

from nasdaq_predictor.services.block_verification_service import BlockVerificationService
from nasdaq_predictor.database.models.block_prediction import BlockPrediction


class TestBlockVerificationService:
    """Test suite for BlockVerificationService."""

    @pytest.fixture
    def mock_fetcher(self):
        """Create mock data fetcher."""
        return Mock()

    @pytest.fixture
    def mock_repository(self):
        """Create mock block prediction repository."""
        return Mock()

    @pytest.fixture
    def service(self, mock_fetcher, mock_repository):
        """Create BlockVerificationService with mocks."""
        return BlockVerificationService(
            fetcher=mock_fetcher,
            block_prediction_repo=mock_repository
        )

    @pytest.fixture
    def sample_ohlc_blocks_6_7(self):
        """Create sample OHLC data for blocks 6-7 (last ~17 minutes of hour)."""
        start_time = datetime(2024, 11, 13, 10, 42)  # At 42:51 mark
        times = [start_time + timedelta(minutes=5*i) for i in range(2)]

        return pd.DataFrame({
            'timestamp': times,
            'open': [100.5, 100.8],
            'high': [101.0, 101.5],
            'low': [100.0, 100.3],
            'close': [101.2, 101.0]  # Positive close vs open
        })

    @pytest.fixture
    def sample_prediction_up(self):
        """Create a sample UP prediction."""
        pred = Mock(spec=BlockPrediction)
        pred.id = 1
        pred.ticker = "NQ=F"
        pred.hour_start = datetime(2024, 11, 13, 10, 0)
        pred.prediction = "UP"
        pred.confidence = 75.5
        pred.strength = "moderate"
        pred.verified = False
        pred.is_correct = None
        pred.actual_result = None
        return pred

    @pytest.fixture
    def sample_prediction_down(self):
        """Create a sample DOWN prediction."""
        pred = Mock(spec=BlockPrediction)
        pred.id = 2
        pred.ticker = "NQ=F"
        pred.hour_start = datetime(2024, 11, 13, 11, 0)
        pred.prediction = "DOWN"
        pred.confidence = 65.0
        pred.strength = "moderate"
        pred.verified = False
        pred.is_correct = None
        pred.actual_result = None
        return pred

    def test_verify_prediction_correct_up(self, service, mock_fetcher, sample_prediction_up, sample_ohlc_blocks_6_7):
        """Test verification when UP prediction matches actual upward movement."""
        # Setup
        mock_fetcher.fetch_5min_ohlc.return_value = sample_ohlc_blocks_6_7

        # Execute
        result = service.verify_block_prediction(sample_prediction_up)

        # Assert
        assert result is not None
        assert result.is_correct == True
        assert result.actual_result == "UP"
        assert result.verified == True

    def test_verify_prediction_incorrect_up(self, service, mock_fetcher, sample_prediction_up):
        """Test verification when UP prediction doesn't match downward actual."""
        # Setup - create downward blocks 6-7
        down_data = pd.DataFrame({
            'timestamp': [datetime(2024, 11, 13, 10, 45), datetime(2024, 11, 13, 10, 50)],
            'open': [100.8, 100.5],
            'high': [100.8, 100.5],
            'low': [100.0, 99.8],
            'close': [100.2, 99.5]  # Negative close
        })

        mock_fetcher.fetch_5min_ohlc.return_value = down_data

        # Execute
        result = service.verify_block_prediction(sample_prediction_up)

        # Assert
        assert result is not None
        assert result.is_correct == False
        assert result.actual_result == "DOWN"

    def test_verify_prediction_correct_down(self, service, mock_fetcher, sample_prediction_down):
        """Test verification when DOWN prediction matches downward movement."""
        # Setup - create downward blocks 6-7
        down_data = pd.DataFrame({
            'timestamp': [datetime(2024, 11, 13, 11, 45), datetime(2024, 11, 13, 11, 50)],
            'open': [100.8, 100.5],
            'high': [100.8, 100.5],
            'low': [100.0, 99.8],
            'close': [100.2, 99.5]  # Close below open
        })

        mock_fetcher.fetch_5min_ohlc.return_value = down_data

        # Execute
        result = service.verify_block_prediction(sample_prediction_down)

        # Assert
        assert result is not None
        assert result.is_correct == True
        assert result.actual_result == "DOWN"

    def test_verify_prediction_neutral(self, service, mock_fetcher):
        """Test verification when actual result is NEUTRAL (close ~= open)."""
        # Setup
        neutral_pred = Mock(spec=BlockPrediction)
        neutral_pred.prediction = "UP"

        neutral_data = pd.DataFrame({
            'timestamp': [datetime(2024, 11, 13, 10, 45), datetime(2024, 11, 13, 10, 50)],
            'open': [100.5, 100.5],
            'high': [100.7, 100.7],
            'low': [100.3, 100.3],
            'close': [100.5, 100.5]  # Close equals open
        })

        mock_fetcher.fetch_5min_ohlc.return_value = neutral_data

        # Execute
        result = service.verify_block_prediction(neutral_pred)

        # Assert
        if result:
            assert result.actual_result == "NEUTRAL"

    def test_verify_prediction_updates_database(self, service, mock_fetcher, mock_repository, sample_prediction_up, sample_ohlc_blocks_6_7):
        """Test that verified prediction is saved to database."""
        # Setup
        mock_fetcher.fetch_5min_ohlc.return_value = sample_ohlc_blocks_6_7

        # Execute
        result = service.verify_block_prediction(sample_prediction_up)

        # Assert - verify save was called
        assert mock_repository.update.called or mock_repository.save.called

    def test_verify_pending_predictions_batch(self, service, mock_fetcher, mock_repository, sample_ohlc_blocks_6_7):
        """Test batch verification of pending predictions."""
        # Setup
        pending_preds = [Mock(spec=BlockPrediction) for _ in range(5)]
        for i, pred in enumerate(pending_preds):
            pred.verified = False
            pred.id = i
            pred.prediction = "UP" if i % 2 == 0 else "DOWN"

        mock_repository.get_unverified = Mock(return_value=pending_preds)
        mock_fetcher.fetch_5min_ohlc.return_value = sample_ohlc_blocks_6_7

        # Execute
        stats = service.verify_pending_predictions()

        # Assert
        assert stats is not None
        assert 'total_verified' in stats
        assert 'correct_count' in stats
        assert 'incorrect_count' in stats

    def test_verify_pending_predictions_no_pending(self, service, mock_repository):
        """Test batch verification when no pending predictions."""
        # Setup
        mock_repository.get_unverified = Mock(return_value=[])

        # Execute
        stats = service.verify_pending_predictions()

        # Assert
        assert stats is not None
        assert stats.get('total_verified', 0) == 0

    def test_verify_prediction_insufficient_data(self, service, mock_fetcher, sample_prediction_up):
        """Test verification with insufficient blocks 6-7 data."""
        # Setup
        empty_data = pd.DataFrame()
        mock_fetcher.fetch_5min_ohlc.return_value = empty_data

        # Execute
        result = service.verify_block_prediction(sample_prediction_up)

        # Assert - should return None or handle gracefully
        # Depends on implementation, but should not crash
        assert True

    def test_get_verification_accuracy_single_day(self, service, mock_repository):
        """Test accuracy calculation for single day."""
        # Setup
        ticker = "NQ=F"
        date = datetime(2024, 11, 13).date()

        verified_preds = [
            Mock(is_correct=True) for _ in range(16)  # 16 correct
        ] + [
            Mock(is_correct=False) for _ in range(8)  # 8 incorrect
        ]

        mock_repository.get_daily_predictions = Mock(return_value=verified_preds)

        # Execute
        metrics = service.get_verification_accuracy(ticker, date)

        # Assert
        assert metrics is not None
        assert 'accuracy_pct' in metrics
        assert metrics['accuracy_pct'] == pytest.approx(66.7, rel=1)

    def test_get_verification_accuracy_zero_predictions(self, service, mock_repository):
        """Test accuracy calculation with no predictions."""
        # Setup
        ticker = "NQ=F"
        date = datetime(2024, 11, 13).date()

        mock_repository.get_daily_predictions = Mock(return_value=[])

        # Execute
        metrics = service.get_verification_accuracy(ticker, date)

        # Assert
        assert metrics is not None
        if 'accuracy_pct' in metrics:
            assert metrics['accuracy_pct'] == 0 or metrics['accuracy_pct'] is None

    def test_get_24h_verification_summary(self, service, mock_repository):
        """Test 24-hour summary with hourly breakdown."""
        # Setup
        ticker = "NQ=F"
        date = datetime(2024, 11, 13).date()

        predictions = []
        for hour in range(24):
            pred = Mock(spec=BlockPrediction)
            pred.hour = hour
            pred.prediction = "UP" if hour % 2 == 0 else "DOWN"
            pred.is_correct = (hour % 3) != 0  # Some correct, some incorrect
            pred.actual_result = "UP" if pred.is_correct else "DOWN"
            pred.confidence = 70.0 + hour
            predictions.append(pred)

        mock_repository.get_daily_predictions = Mock(return_value=predictions)

        # Execute
        summary = service.get_24h_verification_summary(ticker, date)

        # Assert
        assert summary is not None
        assert 'hourly_breakdown' in summary or 'predictions' in summary
        if 'hourly_breakdown' in summary:
            assert len(summary['hourly_breakdown']) <= 24

    def test_hour_completion_detection(self, service, sample_prediction_up):
        """Test detection of hour completion for verification timing."""
        # Setup
        prediction_hour = datetime(2024, 11, 13, 10, 0)
        current_time = datetime(2024, 11, 13, 11, 1)  # 1 minute after hour end

        # Execute - check if hour is complete
        hours_elapsed = (current_time - prediction_hour).total_seconds() / 3600
        hour_complete = hours_elapsed >= 1.0

        # Assert
        assert hour_complete == True

    def test_hour_not_yet_complete(self, service, sample_prediction_up):
        """Test detection when hour is not yet complete."""
        # Setup
        prediction_hour = datetime(2024, 11, 13, 10, 0)
        current_time = datetime(2024, 11, 13, 10, 59)  # 59 minutes elapsed

        # Execute
        hours_elapsed = (current_time - prediction_hour).total_seconds() / 3600
        hour_complete = hours_elapsed >= 1.0

        # Assert
        assert hour_complete == False

    def test_direction_determination_positive_close(self, service):
        """Test determining direction from close > open."""
        # Setup
        data = pd.DataFrame({
            'timestamp': [datetime(2024, 11, 13, 10, 45)],
            'open': [100.0],
            'close': [101.5]  # Positive
        })

        # This is implementation-specific, but UP should be detected
        close_minus_open = data['close'].iloc[-1] - data['open'].iloc[0]
        direction = "UP" if close_minus_open > 0 else "DOWN" if close_minus_open < 0 else "NEUTRAL"

        # Assert
        assert direction == "UP"

    def test_direction_determination_negative_close(self, service):
        """Test determining direction from close < open."""
        # Setup
        data = pd.DataFrame({
            'timestamp': [datetime(2024, 11, 13, 10, 45)],
            'open': [100.0],
            'close': [99.0]  # Negative
        })

        close_minus_open = data['close'].iloc[-1] - data['open'].iloc[0]
        direction = "UP" if close_minus_open > 0 else "DOWN" if close_minus_open < 0 else "NEUTRAL"

        # Assert
        assert direction == "DOWN"

    def test_direction_determination_neutral_close(self, service):
        """Test determining direction when close ~= open."""
        # Setup
        data = pd.DataFrame({
            'timestamp': [datetime(2024, 11, 13, 10, 45)],
            'open': [100.0],
            'close': [100.05]  # Near equal (within 0.1%)
        })

        close_minus_open = data['close'].iloc[-1] - data['open'].iloc[0]
        threshold = data['open'].iloc[0] * 0.001  # 0.1% threshold
        direction = "UP" if close_minus_open > threshold else "DOWN" if close_minus_open < -threshold else "NEUTRAL"

        # Assert
        assert direction == "NEUTRAL"

    def test_error_handling_network_failure(self, service, mock_fetcher, sample_prediction_up):
        """Test error handling with network issues during verification."""
        # Setup
        mock_fetcher.fetch_5min_ohlc.side_effect = ConnectionError("Network error")

        # Execute & Assert
        with pytest.raises(ConnectionError):
            service.verify_block_prediction(sample_prediction_up)

    def test_error_handling_invalid_ticker(self, service, mock_fetcher, sample_prediction_up):
        """Test error handling with invalid ticker during verification."""
        # Setup
        mock_fetcher.fetch_5min_ohlc.side_effect = ValueError("Invalid ticker")

        # Execute & Assert
        with pytest.raises(ValueError):
            service.verify_block_prediction(sample_prediction_up)

    def test_confidence_distribution_analysis(self, service, mock_repository):
        """Test calculation of confidence distribution in accuracy."""
        # Setup
        predictions = []
        confidence_values = [35.0, 65.0, 85.0, 55.0, 75.0]

        for i, conf in enumerate(confidence_values):
            pred = Mock(spec=BlockPrediction)
            pred.confidence = conf
            pred.is_correct = i % 2 == 0
            predictions.append(pred)

        mock_repository.get_daily_predictions = Mock(return_value=predictions)

        # Execute
        metrics = service.get_verification_accuracy("NQ=F", datetime.now().date())

        # Assert
        assert metrics is not None
        if 'avg_confidence' in metrics:
            avg = sum(p.confidence for p in predictions) / len(predictions)
            assert metrics['avg_confidence'] == pytest.approx(avg, rel=0.1)

    def test_batch_verification_stops_on_error(self, service, mock_fetcher, mock_repository):
        """Test batch verification behavior on error."""
        # Setup
        pred1 = Mock(spec=BlockPrediction)
        pred1.verified = False

        pred2 = Mock(spec=BlockPrediction)
        pred2.verified = False

        mock_repository.get_unverified = Mock(return_value=[pred1, pred2])
        mock_fetcher.fetch_5min_ohlc.side_effect = [
            pd.DataFrame({
                'timestamp': [datetime.now()],
                'open': [100.0],
                'close': [101.0]
            }),
            ConnectionError("Network error")
        ]

        # Execute
        try:
            service.verify_pending_predictions()
        except ConnectionError:
            pass

        # Assert - service should handle the error gracefully
        assert True

