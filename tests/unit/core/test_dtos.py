"""
Unit tests for Data Transfer Objects (DTOs).

Tests DTO creation, serialization, and validation.
"""

import pytest
from datetime import datetime
import pytz
from dataclasses import asdict

from nasdaq_predictor.core.dtos import (
    OHLCDTO,
    PredictionDTO,
    ReferencePointDTO,
    SignalDTO,
    IntradayPredictionDTO,
    FibonacciPivotDTO,
    AccuracyMetricsDTO,
    MarketSummaryDTO,
    ResponseDTO,
    SchedulerStatusDTO,
    HealthCheckDTO,
)


class TestOHLCDTO:
    """Test OHLC data transfer object."""

    def test_create_ohlc_dto(self):
        """Test creating OHLC DTO."""
        now = datetime.utcnow()
        ohlc = OHLCDTO(
            symbol="NQ=F",
            timestamp=now,
            open=19100.0,
            high=19250.0,
            low=19050.0,
            close=19200.0,
            volume=1000000,
        )

        assert ohlc.symbol == "NQ=F"
        assert ohlc.close == 19200.0

    def test_ohlc_to_dict(self):
        """Test converting OHLC DTO to dictionary."""
        now = datetime.utcnow()
        ohlc = OHLCDTO(
            symbol="NQ=F",
            timestamp=now,
            open=19100.0,
            high=19250.0,
            low=19050.0,
            close=19200.0,
            volume=1000000,
        )

        data = ohlc.to_dict()
        assert isinstance(data, dict)
        assert data["symbol"] == "NQ=F"
        assert data["close"] == 19200.0
        assert isinstance(data["timestamp"], str)  # ISO format


class TestPredictionDTO:
    """Test prediction data transfer object."""

    def test_create_prediction_dto(self):
        """Test creating prediction DTO."""
        pred = PredictionDTO(
            symbol="NQ=F",
            prediction="BULLISH",
            confidence=75.5,
            weighted_score=0.825,
            timestamp=datetime.utcnow(),
            reference_levels={"daily_open": 19100.0},
            signals={"signal_1": 1.0},
            market_status="OPEN",
        )

        assert pred.symbol == "NQ=F"
        assert pred.prediction == "BULLISH"
        assert pred.confidence == 75.5

    def test_prediction_dto_bullish(self):
        """Test bullish prediction."""
        pred = PredictionDTO(
            symbol="ES=F",
            prediction="BULLISH",
            confidence=80.0,
            weighted_score=0.85,
            timestamp=datetime.utcnow(),
            reference_levels={},
            signals={},
        )

        assert pred.prediction == "BULLISH"
        assert pred.confidence == 80.0

    def test_prediction_dto_bearish(self):
        """Test bearish prediction."""
        pred = PredictionDTO(
            symbol="^FTSE",
            prediction="BEARISH",
            confidence=65.0,
            weighted_score=0.35,
            timestamp=datetime.utcnow(),
            reference_levels={},
            signals={},
        )

        assert pred.prediction == "BEARISH"
        assert pred.confidence == 65.0

    def test_prediction_to_dict(self):
        """Test converting prediction to dictionary."""
        now = datetime.utcnow()
        pred = PredictionDTO(
            symbol="NQ=F",
            prediction="BULLISH",
            confidence=75.5,
            weighted_score=0.825,
            timestamp=now,
            reference_levels={},
            signals={},
        )

        data = pred.to_dict()
        assert data["symbol"] == "NQ=F"
        assert data["prediction"] == "BULLISH"
        assert isinstance(data["timestamp"], str)


class TestReferencePointDTO:
    """Test reference point data transfer object."""

    def test_create_reference_point(self):
        """Test creating reference point DTO."""
        point = ReferencePointDTO(
            name="daily_open_midnight",
            value=19100.0,
            weight=0.100,
        )

        assert point.name == "daily_open_midnight"
        assert point.value == 19100.0
        assert point.weight == 0.100

    def test_reference_point_to_dict(self):
        """Test converting to dict."""
        point = ReferencePointDTO(
            name="ny_am_kill_zone",
            value=19250.0,
            weight=0.083,
        )

        data = point.to_dict()
        assert data["name"] == "ny_am_kill_zone"
        assert data["value"] == 19250.0


class TestSignalDTO:
    """Test signal data transfer object."""

    def test_create_signal(self):
        """Test creating signal DTO."""
        signal = SignalDTO(
            name="daily_open",
            value=1.0,  # Bullish
            weight=0.100,
            contribution=0.100,
        )

        assert signal.name == "daily_open"
        assert signal.value == 1.0

    def test_signal_bullish(self):
        """Test bullish signal."""
        signal = SignalDTO(
            name="test",
            value=1.0,
            weight=0.050,
            contribution=0.050,
        )

        assert signal.value == 1.0

    def test_signal_bearish(self):
        """Test bearish signal."""
        signal = SignalDTO(
            name="test",
            value=0.0,
            weight=0.050,
            contribution=0.0,
        )

        assert signal.value == 0.0


class TestIntradayPredictionDTO:
    """Test intraday prediction data transfer object."""

    def test_create_intraday_prediction(self):
        """Test creating intraday prediction DTO."""
        pred = IntradayPredictionDTO(
            symbol="NQ=F",
            hour=9,  # 9am ET
            prediction="BULLISH",
            confidence=65.0,
            timestamp=datetime.utcnow(),
        )

        assert pred.symbol == "NQ=F"
        assert pred.hour == 9
        assert pred.prediction == "BULLISH"

    def test_intraday_prediction_valid_hours(self):
        """Test valid intraday hours (9-16)."""
        for hour in range(9, 17):
            pred = IntradayPredictionDTO(
                symbol="NQ=F",
                hour=hour,
                prediction="BULLISH",
                confidence=50.0,
                timestamp=datetime.utcnow(),
            )
            assert pred.hour == hour


class TestFibonacciPivotDTO:
    """Test Fibonacci pivot data transfer object."""

    def test_create_fibonacci_pivot(self):
        """Test creating Fibonacci pivot DTO."""
        date = datetime(2025, 6, 15)
        fib = FibonacciPivotDTO(
            symbol="NQ=F",
            timeframe="daily",
            date=date,
            high=19300.0,
            low=19100.0,
            resistance_1=19250.0,
            resistance_2=19350.0,
            resistance_3=19450.0,
            support_1=19050.0,
            support_2=18950.0,
            support_3=18850.0,
            pivot_point=19175.0,
        )

        assert fib.symbol == "NQ=F"
        assert fib.timeframe == "daily"
        assert fib.resistance_1 == 19250.0

    def test_fib_pivot_timeframes(self):
        """Test Fibonacci with different timeframes."""
        date = datetime(2025, 6, 15)
        for timeframe in ["daily", "weekly", "monthly"]:
            fib = FibonacciPivotDTO(
                symbol="NQ=F",
                timeframe=timeframe,
                date=date,
                high=19300.0,
                low=19100.0,
                resistance_1=19250.0,
                resistance_2=19350.0,
                resistance_3=19450.0,
                support_1=19050.0,
                support_2=18950.0,
                support_3=18850.0,
                pivot_point=19175.0,
            )
            assert fib.timeframe == timeframe


class TestAccuracyMetricsDTO:
    """Test accuracy metrics data transfer object."""

    def test_create_accuracy_metrics(self):
        """Test creating accuracy metrics DTO."""
        metrics = AccuracyMetricsDTO(
            symbol="NQ=F",
            period_hours=24,
            total_predictions=24,
            correct_predictions=18,
            accuracy_percentage=75.0,
            confidence_avg=70.5,
            timestamp=datetime.utcnow(),
        )

        assert metrics.symbol == "NQ=F"
        assert metrics.accuracy_percentage == 75.0
        assert metrics.confidence_avg == 70.5

    def test_accuracy_calculation(self):
        """Test accuracy calculations."""
        correct = 18
        total = 24
        accuracy = (correct / total) * 100

        metrics = AccuracyMetricsDTO(
            symbol="NQ=F",
            period_hours=24,
            total_predictions=total,
            correct_predictions=correct,
            accuracy_percentage=accuracy,
            confidence_avg=70.0,
            timestamp=datetime.utcnow(),
        )

        assert metrics.accuracy_percentage == 75.0


class TestMarketSummaryDTO:
    """Test market summary data transfer object."""

    def test_create_market_summary(self):
        """Test creating market summary DTO."""
        summary = MarketSummaryDTO(
            timestamp=datetime.utcnow(),
            bullish_count=2,
            bearish_count=1,
            avg_confidence=72.0,
            overall_trend="BULLISH",
            market_status="OPEN",
            last_update_seconds_ago=5,
        )

        assert summary.bullish_count == 2
        assert summary.bearish_count == 1
        assert summary.overall_trend == "BULLISH"

    def test_market_trend_determination(self):
        """Test market trend determination."""
        summary = MarketSummaryDTO(
            timestamp=datetime.utcnow(),
            bullish_count=3,
            bearish_count=0,
            avg_confidence=80.0,
            overall_trend="BULLISH",
            market_status="OPEN",
            last_update_seconds_ago=2,
        )

        assert summary.overall_trend == "BULLISH"
        assert summary.bullish_count > summary.bearish_count


class TestResponseDTO:
    """Test standard response data transfer object."""

    def test_create_success_response(self):
        """Test creating success response."""
        response = ResponseDTO(
            success=True,
            data={"prediction": "BULLISH", "confidence": 75.0},
            timestamp=datetime.utcnow(),
        )

        assert response.success is True
        assert response.data is not None
        assert response.error is None

    def test_create_error_response(self):
        """Test creating error response."""
        response = ResponseDTO(
            success=False,
            error="Invalid ticker",
            error_type="ValidationException",
            timestamp=datetime.utcnow(),
        )

        assert response.success is False
        assert response.error is not None
        assert response.data is None

    def test_response_timestamp_auto_set(self):
        """Test response timestamp is auto-set to now."""
        response = ResponseDTO(success=True)
        assert response.timestamp is not None

    def test_response_to_dict(self):
        """Test converting response to dictionary."""
        response = ResponseDTO(
            success=True,
            data={"test": "value"},
            timestamp=datetime.utcnow(),
        )

        data = response.to_dict()
        assert isinstance(data, dict)
        assert data["success"] is True
        assert isinstance(data["timestamp"], str)

    def test_response_cached_flag(self):
        """Test cached flag in response."""
        response = ResponseDTO(
            success=True,
            data={},
            cached=True,
            cache_age_seconds=15,
        )

        assert response.cached is True
        assert response.cache_age_seconds == 15


class TestSchedulerStatusDTO:
    """Test scheduler status data transfer object."""

    def test_create_scheduler_status(self):
        """Test creating scheduler status DTO."""
        status = SchedulerStatusDTO(
            enabled=True,
            total_jobs=7,
            active_jobs=5,
            jobs=[
                {"id": "job1", "name": "data_sync", "next_run": "2025-11-12 15:30:00"}
            ],
        )

        assert status.enabled is True
        assert status.total_jobs == 7
        assert len(status.jobs) == 1

    def test_scheduler_status_disabled(self):
        """Test disabled scheduler status."""
        status = SchedulerStatusDTO(
            enabled=False,
            total_jobs=0,
            active_jobs=0,
            jobs=[],
        )

        assert status.enabled is False


class TestHealthCheckDTO:
    """Test health check data transfer object."""

    def test_create_health_check(self):
        """Test creating health check DTO."""
        health = HealthCheckDTO(
            healthy=True,
            version="1.0.0",
            uptime_seconds=3600,
            scheduler_enabled=True,
            database_connected=True,
        )

        assert health.healthy is True
        assert health.version == "1.0.0"

    def test_health_check_unhealthy(self):
        """Test unhealthy health check."""
        health = HealthCheckDTO(
            healthy=False,
            version="1.0.0",
            uptime_seconds=100,
            scheduler_enabled=False,
            database_connected=False,
            errors=["Database connection failed", "Scheduler not running"],
        )

        assert health.healthy is False
        assert len(health.errors) == 2


class TestDTOSerialization:
    """Test DTO serialization to JSON-compatible format."""

    def test_dto_asdict_conversion(self):
        """Test converting DTO to asdict format."""
        pred = PredictionDTO(
            symbol="NQ=F",
            prediction="BULLISH",
            confidence=75.0,
            weighted_score=0.825,
            timestamp=datetime.utcnow(),
            reference_levels={},
            signals={},
        )

        data = asdict(pred)
        assert isinstance(data, dict)
        assert data["symbol"] == "NQ=F"

    def test_response_dto_json_serializable(self):
        """Test response DTO is JSON serializable."""
        response = ResponseDTO(
            success=True,
            data={"test": "data"},
            timestamp=datetime.utcnow(),
        )

        # Should be convertible to dict for JSON serialization
        data = response.to_dict()
        assert all(isinstance(v, (str, bool, int, float, dict, list, type(None)))
                  for v in data.values())
