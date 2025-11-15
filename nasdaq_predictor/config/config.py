"""
Improved configuration management using dataclasses.

This module provides a clean, type-safe configuration system that replaces
scattered configuration across multiple files and environment variables.

Usage:
    >>> config = AppConfig.from_env()
    >>> cache_duration = config.cache.duration_minutes
    >>> tickers = config.trading.allowed_tickers
"""

import os
from dataclasses import dataclass, field
from typing import Dict, Set

import pytz


# ========================================
# Database Configuration
# ========================================


@dataclass
class DatabaseConfig:
    """Database connection configuration."""

    url: str = field(default_factory=lambda: os.getenv("SUPABASE_URL", ""))
    key: str = field(default_factory=lambda: os.getenv("SUPABASE_KEY", ""))
    timeout_seconds: int = 30
    pool_size: int = 5
    echo_sql: bool = False  # Log SQL queries

    def validate(self) -> None:
        """Validate database configuration.

        Raises:
            ValueError: If configuration is invalid.
        """
        if not self.url:
            raise ValueError("SUPABASE_URL environment variable not set")
        if not self.key:
            raise ValueError("SUPABASE_KEY environment variable not set")
        if self.timeout_seconds < 1:
            raise ValueError("timeout_seconds must be >= 1")
        if self.pool_size < 1:
            raise ValueError("pool_size must be >= 1")


# ========================================
# Cache Configuration
# ========================================


@dataclass
class CacheConfig:
    """Caching configuration."""

    enabled: bool = True
    duration_minutes: int = 15  # Cache expiry time
    max_entries: int = 1000  # Maximum in-memory entries
    backend: str = "memory"  # memory, redis, etc.

    def validate(self) -> None:
        """Validate cache configuration."""
        if self.duration_minutes < 1:
            raise ValueError("duration_minutes must be >= 1")
        if self.max_entries < 1:
            raise ValueError("max_entries must be >= 1")
        if self.backend not in ["memory", "redis"]:
            raise ValueError("backend must be 'memory' or 'redis'")


# ========================================
# Scheduler Configuration
# ========================================


@dataclass
class SchedulerConfig:
    """Background job scheduler configuration."""

    enabled: bool = field(
        default_factory=lambda: os.getenv("SCHEDULER_ENABLED", "true") == "true"
    )
    max_workers: int = 3
    market_data_interval_minutes: int = 10
    prediction_interval_minutes: int = 15
    verification_interval_minutes: int = 15
    cleanup_interval_hours: int = 24
    cleanup_hour: int = 2  # Time of day to run cleanup (0-23)
    cleanup_minute: int = 0
    max_retry_attempts: int = 3
    retry_backoff_seconds: int = 60

    def validate(self) -> None:
        """Validate scheduler configuration."""
        if self.max_workers < 1:
            raise ValueError("max_workers must be >= 1")
        if self.market_data_interval_minutes < 1:
            raise ValueError("market_data_interval_minutes must be >= 1")
        if self.prediction_interval_minutes < 1:
            raise ValueError("prediction_interval_minutes must be >= 1")
        if not (0 <= self.cleanup_hour <= 23):
            raise ValueError("cleanup_hour must be 0-23")
        if not (0 <= self.cleanup_minute <= 59):
            raise ValueError("cleanup_minute must be 0-59")


# ========================================
# Trading Configuration
# ========================================


@dataclass
class TradingSessionConfig:
    """Configuration for a single trading instrument."""

    type: str  # futures, index, stock, crypto
    main_session_start: float  # UTC hour (e.g., 13.5 for 13:30)
    main_session_end: float  # UTC hour
    timezone: str = "UTC"
    uses_main_only: bool = False  # If True, only use main session


@dataclass
class TradingConfig:
    """Trading instruments and sessions configuration."""

    allowed_tickers: Set[str] = field(
        default_factory=lambda: {"NQ=F", "ES=F", "^FTSE", "BTC-USD", "ETH-USD"}
    )

    # Session configs for each ticker
    sessions: Dict[str, TradingSessionConfig] = field(default_factory=dict)

    # Data fetching periods
    hist_period_hourly: str = "30d"
    hist_period_minute: str = "7d"
    hist_period_30min: str = "60d"
    hist_period_daily: str = "1y"

    # Data intervals
    hist_interval_hourly: str = "1h"
    hist_interval_minute: str = "1m"
    hist_interval_30min: str = "30m"

    def __post_init__(self):
        """Initialize default trading sessions if not provided."""
        if not self.sessions:
            self.sessions = {
                "NQ=F": TradingSessionConfig(
                    type="futures",
                    main_session_start=13.5,
                    main_session_end=20.0,
                    timezone="America/New_York",
                    uses_main_only=False,
                ),
                "ES=F": TradingSessionConfig(
                    type="futures",
                    main_session_start=13.5,
                    main_session_end=20.0,
                    timezone="America/New_York",
                    uses_main_only=False,
                ),
                "^FTSE": TradingSessionConfig(
                    type="index",
                    main_session_start=8.0,
                    main_session_end=16.5,
                    timezone="Europe/London",
                    uses_main_only=True,
                ),
                "BTC-USD": TradingSessionConfig(
                    type="crypto",
                    main_session_start=0.0,
                    main_session_end=24.0,
                    timezone="UTC",
                    uses_main_only=False,
                ),
                "ETH-USD": TradingSessionConfig(
                    type="crypto",
                    main_session_start=0.0,
                    main_session_end=24.0,
                    timezone="UTC",
                    uses_main_only=False,
                ),
            }

    def validate(self) -> None:
        """Validate trading configuration."""
        if not self.allowed_tickers:
            raise ValueError("allowed_tickers cannot be empty")
        for session in self.sessions.values():
            if not (0 <= session.main_session_start < 24):
                raise ValueError("main_session_start must be 0-24")
            if not (0 <= session.main_session_end <= 24):
                raise ValueError("main_session_end must be 0-24")


# ========================================
# Analysis Configuration (Reference Levels & Weights)
# ========================================


@dataclass
class AnalysisConfig:
    """Market analysis and signal configuration."""

    # 18-level weighted signal system
    weights: Dict[str, float] = field(
        default_factory=lambda: {
            "daily_open_midnight": 0.100,
            "ny_open_0830": 0.063,
            "thirty_min_open": 0.080,
            "ny_open_0700": 0.068,
            "four_hour_open": 0.056,
            "weekly_open": 0.049,
            "hourly_open": 0.042,
            "previous_hourly_open": 0.041,
            "previous_week_open": 0.024,
            "previous_day_high": 0.023,
            "previous_day_low": 0.023,
            "monthly_open": 0.021,
            "range_0700_0715": 0.073,  # 7:00-7:15 AM range
            "range_0830_0845": 0.079,  # 8:30-8:45 AM range
            "asian_kill_zone": 0.053,  # Asian session
            "london_kill_zone": 0.069,  # London session
            "ny_am_kill_zone": 0.083,  # NY AM session
            "ny_pm_kill_zone": 0.053,  # NY PM session
        }
    )

    # Confidence decay settings
    confidence_max: float = 100.0  # Maximum confidence %
    confidence_decay_hours: int = 4  # Hours until confidence decays
    confidence_decay_factor: float = 0.95  # Multiplier per hour

    # Signal thresholds
    bullish_threshold: float = 0.5  # Score >= 0.5 = BULLISH
    bearish_threshold: float = 0.5  # Score < 0.5 = BEARISH

    def __post_init__(self):
        """Validate weights sum to 1.0."""
        weights_sum = sum(self.weights.values())
        if abs(weights_sum - 1.0) > 0.001:
            raise ValueError(f"Weights must sum to 1.0, got {weights_sum}")

    def validate(self) -> None:
        """Validate analysis configuration."""
        if self.confidence_max <= 0:
            raise ValueError("confidence_max must be > 0")
        if self.confidence_decay_hours < 1:
            raise ValueError("confidence_decay_hours must be >= 1")
        if not (0 < self.confidence_decay_factor <= 1.0):
            raise ValueError("confidence_decay_factor must be 0-1")
        if not (0 < self.bullish_threshold < 1):
            raise ValueError("bullish_threshold must be 0-1")


# ========================================
# Logging Configuration
# ========================================


@dataclass
class LoggingConfig:
    """Logging configuration."""

    level: str = field(
        default_factory=lambda: os.getenv("LOG_LEVEL", "INFO")
    )
    format: str = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    file_path: str = "logs/app.log"
    max_file_size_mb: int = 50
    backup_count: int = 5

    def validate(self) -> None:
        """Validate logging configuration."""
        valid_levels = {"DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"}
        if self.level not in valid_levels:
            raise ValueError(f"Invalid log level: {self.level}")


# ========================================
# Application Configuration (Main)
# ========================================


@dataclass
class AppConfig:
    """Complete application configuration.

    Aggregates all sub-configurations (database, cache, scheduler, etc.)
    into a single, type-safe configuration object.
    """

    app_version: str = "1.0.0"
    environment: str = field(
        default_factory=lambda: os.getenv("FLASK_ENV", "production")
    )
    debug: bool = field(
        default_factory=lambda: os.getenv("DEBUG", "false").lower() == "true"
    )
    port: int = field(
        default_factory=lambda: int(os.getenv("PORT", "5000"))
    )

    # Sub-configurations
    database: DatabaseConfig = field(default_factory=DatabaseConfig)
    cache: CacheConfig = field(default_factory=CacheConfig)
    scheduler: SchedulerConfig = field(default_factory=SchedulerConfig)
    trading: TradingConfig = field(default_factory=TradingConfig)
    analysis: AnalysisConfig = field(default_factory=AnalysisConfig)
    logging: LoggingConfig = field(default_factory=LoggingConfig)

    @classmethod
    def from_env(cls) -> "AppConfig":
        """Create configuration from environment variables.

        Returns:
            AppConfig instance fully configured from env vars.

        Raises:
            ValueError: If required environment variables are missing.
        """
        config = cls()
        config.validate()
        return config

    def validate(self) -> None:
        """Validate all sub-configurations.

        Raises:
            ValueError: If any configuration is invalid.
        """
        self.database.validate()
        self.cache.validate()
        self.scheduler.validate()
        self.trading.validate()
        self.analysis.validate()
        self.logging.validate()

        # Custom validation
        if self.port < 1 or self.port > 65535:
            raise ValueError("port must be 1-65535")

        valid_envs = {"development", "staging", "production"}
        if self.environment not in valid_envs:
            raise ValueError(f"Invalid environment: {self.environment}")

    def is_production(self) -> bool:
        """Check if running in production."""
        return self.environment == "production"

    def is_development(self) -> bool:
        """Check if running in development."""
        return self.environment == "development"
