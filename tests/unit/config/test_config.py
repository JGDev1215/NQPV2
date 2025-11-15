"""
Unit tests for application configuration.

Tests configuration classes, validation, and environment variable handling.
"""

import pytest
import os
from unittest.mock import patch

from nasdaq_predictor.config.config import (
    DatabaseConfig,
    CacheConfig,
    SchedulerConfig,
    TradingSessionConfig,
    TradingConfig,
    AnalysisConfig,
    LoggingConfig,
    AppConfig,
)
from nasdaq_predictor.core.exceptions import ValidationException


class TestDatabaseConfig:
    """Test database configuration."""

    def test_create_database_config(self):
        """Test creating database config."""
        config = DatabaseConfig(
            url="https://test.supabase.co",
            key="test_key",
        )

        assert config.url == "https://test.supabase.co"
        assert config.key == "test_key"

    def test_database_config_validation_success(self):
        """Test database config validation succeeds."""
        config = DatabaseConfig(
            url="https://test.supabase.co",
            key="test_key",
        )

        config.validate()  # Should not raise

    def test_database_config_missing_url_raises_exception(self):
        """Test database config validation fails without URL."""
        config = DatabaseConfig(url="", key="test_key")

        with pytest.raises(ValueError) as exc:
            config.validate()

        assert "SUPABASE_URL" in str(exc.value)

    def test_database_config_missing_key_raises_exception(self):
        """Test database config validation fails without key."""
        config = DatabaseConfig(url="https://test.supabase.co", key="")

        with pytest.raises(ValueError) as exc:
            config.validate()

        assert "SUPABASE_KEY" in str(exc.value)

    def test_database_config_invalid_timeout(self):
        """Test database config validation fails with invalid timeout."""
        config = DatabaseConfig(
            url="https://test.supabase.co",
            key="test_key",
            timeout_seconds=0,
        )

        with pytest.raises(ValueError):
            config.validate()


class TestCacheConfig:
    """Test cache configuration."""

    def test_create_cache_config(self):
        """Test creating cache config."""
        config = CacheConfig(enabled=True, duration_minutes=15)

        assert config.enabled is True
        assert config.duration_minutes == 15

    def test_cache_config_disabled(self):
        """Test cache disabled."""
        config = CacheConfig(enabled=False)

        assert config.enabled is False

    def test_cache_config_validation_success(self):
        """Test cache config validation succeeds."""
        config = CacheConfig(duration_minutes=15, max_entries=1000)

        config.validate()  # Should not raise

    def test_cache_config_invalid_duration(self):
        """Test cache config validation fails with invalid duration."""
        config = CacheConfig(duration_minutes=0)

        with pytest.raises(ValueError):
            config.validate()

    def test_cache_config_invalid_backend(self):
        """Test cache config validation fails with invalid backend."""
        config = CacheConfig(backend="invalid_backend")

        with pytest.raises(ValueError) as exc:
            config.validate()

        assert "backend" in str(exc.value).lower()


class TestSchedulerConfig:
    """Test scheduler configuration."""

    def test_create_scheduler_config(self):
        """Test creating scheduler config."""
        config = SchedulerConfig(enabled=True, max_workers=3)

        assert config.enabled is True
        assert config.max_workers == 3

    def test_scheduler_config_disabled(self):
        """Test scheduler disabled."""
        config = SchedulerConfig(enabled=False)

        assert config.enabled is False

    def test_scheduler_config_validation_success(self):
        """Test scheduler config validation succeeds."""
        config = SchedulerConfig(
            max_workers=3,
            market_data_interval_minutes=10,
            cleanup_hour=2,
        )

        config.validate()  # Should not raise

    def test_scheduler_config_invalid_cleanup_hour(self):
        """Test scheduler config validation fails with invalid cleanup hour."""
        config = SchedulerConfig(cleanup_hour=25)

        with pytest.raises(ValueError) as exc:
            config.validate()

        assert "cleanup_hour" in str(exc.value)

    def test_scheduler_config_invalid_cleanup_minute(self):
        """Test scheduler config validation fails with invalid cleanup minute."""
        config = SchedulerConfig(cleanup_minute=60)

        with pytest.raises(ValueError):
            config.validate()


class TestTradingConfig:
    """Test trading configuration."""

    def test_create_trading_config(self):
        """Test creating trading config."""
        config = TradingConfig()

        assert "NQ=F" in config.allowed_tickers
        assert "ES=F" in config.allowed_tickers

    def test_trading_config_default_sessions(self):
        """Test trading config has default sessions."""
        config = TradingConfig()

        assert "NQ=F" in config.sessions
        assert "ES=F" in config.sessions
        assert "^FTSE" in config.sessions

    def test_trading_session_config(self):
        """Test trading session configuration."""
        session = TradingSessionConfig(
            type="futures",
            main_session_start=13.5,
            main_session_end=20.0,
        )

        assert session.type == "futures"
        assert session.main_session_start == 13.5

    def test_trading_config_validation_success(self):
        """Test trading config validation succeeds."""
        config = TradingConfig()

        config.validate()  # Should not raise

    def test_trading_config_validation_empty_tickers(self):
        """Test trading config validation fails with empty tickers."""
        config = TradingConfig(allowed_tickers=set())

        with pytest.raises(ValueError) as exc:
            config.validate()

        assert "allowed_tickers" in str(exc.value)


class TestAnalysisConfig:
    """Test analysis configuration."""

    def test_create_analysis_config(self):
        """Test creating analysis config."""
        config = AnalysisConfig()

        assert "daily_open_midnight" in config.weights
        assert "ny_am_kill_zone" in config.weights

    def test_analysis_config_weights_sum_to_one(self):
        """Test analysis config weights sum to 1.0."""
        config = AnalysisConfig()

        weights_sum = sum(config.weights.values())
        assert abs(weights_sum - 1.0) < 0.001

    def test_analysis_config_validation_success(self):
        """Test analysis config validation succeeds."""
        config = AnalysisConfig()

        config.validate()  # Should not raise

    def test_analysis_config_invalid_weights_sum(self):
        """Test analysis config validation fails with invalid weights."""
        weights = {"level1": 0.5, "level2": 0.3}  # Sum = 0.8, not 1.0

        with pytest.raises(ValueError) as exc:
            AnalysisConfig(weights=weights)

        assert "sum to 1.0" in str(exc.value)

    def test_analysis_config_invalid_confidence_max(self):
        """Test analysis config validation fails with invalid confidence max."""
        config = AnalysisConfig(confidence_max=0)

        with pytest.raises(ValueError):
            config.validate()


class TestLoggingConfig:
    """Test logging configuration."""

    def test_create_logging_config(self):
        """Test creating logging config."""
        config = LoggingConfig(level="INFO")

        assert config.level == "INFO"

    def test_logging_config_valid_levels(self):
        """Test logging config with valid levels."""
        valid_levels = ["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"]

        for level in valid_levels:
            config = LoggingConfig(level=level)
            config.validate()  # Should not raise

    def test_logging_config_invalid_level(self):
        """Test logging config validation fails with invalid level."""
        config = LoggingConfig(level="INVALID")

        with pytest.raises(ValueError) as exc:
            config.validate()

        assert "log level" in str(exc.value).lower()


class TestAppConfig:
    """Test application configuration."""

    def test_create_app_config(self):
        """Test creating app config."""
        config = AppConfig()

        assert config.app_version == "1.0.0"
        assert config.port == 5000

    def test_app_config_has_all_subconfigs(self):
        """Test app config contains all sub-configurations."""
        config = AppConfig()

        assert isinstance(config.database, DatabaseConfig)
        assert isinstance(config.cache, CacheConfig)
        assert isinstance(config.scheduler, SchedulerConfig)
        assert isinstance(config.trading, TradingConfig)
        assert isinstance(config.analysis, AnalysisConfig)
        assert isinstance(config.logging, LoggingConfig)

    def test_app_config_validation_success(self):
        """Test app config validation succeeds."""
        config = AppConfig(
            database=DatabaseConfig(
                url="https://test.supabase.co",
                key="test_key",
            ),
        )

        config.validate()  # Should not raise

    def test_app_config_invalid_port(self):
        """Test app config validation fails with invalid port."""
        config = AppConfig(port=70000)

        with pytest.raises(ValueError) as exc:
            config.validate()

        assert "port" in str(exc.value)

    def test_app_config_invalid_environment(self):
        """Test app config validation fails with invalid environment."""
        config = AppConfig(environment="invalid")

        with pytest.raises(ValueError) as exc:
            config.validate()

        assert "environment" in str(exc.value)

    def test_app_config_from_env(self):
        """Test creating app config from environment variables."""
        with patch.dict(os.environ, {
            "SUPABASE_URL": "https://test.supabase.co",
            "SUPABASE_KEY": "test_key",
            "FLASK_ENV": "production",
        }):
            config = AppConfig.from_env()

            assert config.environment == "production"

    def test_app_config_is_production(self):
        """Test is_production() check."""
        config = AppConfig(environment="production")

        assert config.is_production() is True
        assert config.is_development() is False

    def test_app_config_is_development(self):
        """Test is_development() check."""
        config = AppConfig(environment="development")

        assert config.is_development() is True
        assert config.is_production() is False

    def test_app_config_debug_mode(self):
        """Test debug mode configuration."""
        config = AppConfig(debug=True)

        assert config.debug is True

    @patch.dict(os.environ, {"DEBUG": "true"})
    def test_app_config_debug_from_env(self):
        """Test debug mode from environment."""
        config = AppConfig()

        assert config.debug is True

    @patch.dict(os.environ, {"PORT": "8080"})
    def test_app_config_port_from_env(self):
        """Test port from environment."""
        config = AppConfig()

        assert config.port == 8080


class TestConfigIntegration:
    """Test configuration integration."""

    def test_full_app_config_validation(self):
        """Test validating complete app configuration."""
        config = AppConfig(
            app_version="1.0.0",
            environment="production",
            database=DatabaseConfig(
                url="https://test.supabase.co",
                key="test_key",
            ),
            cache=CacheConfig(enabled=True),
            scheduler=SchedulerConfig(enabled=True),
        )

        config.validate()  # Should not raise

    def test_config_environment_specific_settings(self):
        """Test environment-specific configuration."""
        prod_config = AppConfig(environment="production", debug=False)
        dev_config = AppConfig(environment="development", debug=True)

        assert prod_config.is_production()
        assert dev_config.is_development()

    def test_trading_config_ticker_access(self):
        """Test accessing ticker configurations."""
        config = AppConfig()

        assert config.trading.has("NQ=F") if hasattr(config.trading, "has") else "NQ=F" in config.trading.sessions


class TestConfigDefaults:
    """Test configuration defaults."""

    def test_cache_default_duration(self):
        """Test cache default duration."""
        config = CacheConfig()

        assert config.duration_minutes == 15

    def test_scheduler_default_intervals(self):
        """Test scheduler default intervals."""
        config = SchedulerConfig()

        assert config.market_data_interval_minutes == 10
        assert config.prediction_interval_minutes == 15

    def test_analysis_default_thresholds(self):
        """Test analysis default thresholds."""
        config = AnalysisConfig()

        assert config.bullish_threshold == 0.5
        assert config.bearish_threshold == 0.5

    def test_app_default_version(self):
        """Test app default version."""
        config = AppConfig()

        assert config.app_version == "1.0.0"
