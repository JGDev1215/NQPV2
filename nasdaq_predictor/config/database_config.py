"""
Database configuration for NQP application.

This module contains configuration settings for Supabase database operations,
including connection pooling, retry policies, timeout settings, and data retention.

Usage:
    from nasdaq_predictor.config.database_config import DatabaseConfig

    config = DatabaseConfig()
    timeout = config.QUERY_TIMEOUT
"""

import os
from typing import Dict, Any
from dotenv import load_dotenv

load_dotenv()


class DatabaseConfig:
    """
    Database configuration settings.

    This class contains all database-related configuration parameters
    for the NQP application.
    """

    # ========================================================================
    # Connection Settings
    # ========================================================================

    # Supabase credentials (loaded from environment)
    SUPABASE_URL: str = os.getenv('SUPABASE_URL', '')
    SUPABASE_KEY: str = os.getenv('SUPABASE_KEY', '')
    SUPABASE_SERVICE_KEY: str = os.getenv('SUPABASE_SERVICE_KEY', '')

    # Connection pool settings
    CONNECTION_POOL_SIZE: int = int(os.getenv('DB_CONNECTION_POOL_SIZE', '10'))
    CONNECTION_MAX_OVERFLOW: int = int(os.getenv('DB_CONNECTION_MAX_OVERFLOW', '20'))

    # ========================================================================
    # Query Settings
    # ========================================================================

    # Query timeout in seconds
    QUERY_TIMEOUT: int = int(os.getenv('DB_TIMEOUT', '30'))

    # Retry settings
    MAX_RETRY_ATTEMPTS: int = int(os.getenv('DB_RETRY_ATTEMPTS', '3'))
    RETRY_DELAY_SECONDS: float = float(os.getenv('DB_RETRY_DELAY', '1.0'))
    RETRY_BACKOFF_MULTIPLIER: float = 2.0  # Exponential backoff

    # Batch operation settings
    BATCH_INSERT_SIZE: int = int(os.getenv('DB_BATCH_SIZE', '1000'))
    BULK_UPSERT_SIZE: int = int(os.getenv('DB_BULK_UPSERT_SIZE', '500'))

    # ========================================================================
    # Data Retention Settings
    # ========================================================================

    # How long to keep different types of data (in days)
    RETENTION_MINUTE_DATA: int = int(os.getenv('RETENTION_MINUTE_DATA', '90'))  # 90 days
    RETENTION_HOURLY_DATA: int = int(os.getenv('RETENTION_HOURLY_DATA', '365'))  # 1 year
    RETENTION_DAILY_DATA: int = int(os.getenv('RETENTION_DAILY_DATA', '3650'))  # 10 years
    RETENTION_PREDICTIONS: int = int(os.getenv('RETENTION_PREDICTIONS', '365'))  # 1 year
    RETENTION_SIGNALS: int = int(os.getenv('RETENTION_SIGNALS', '365'))  # 1 year

    # ========================================================================
    # Cache Settings
    # ========================================================================

    # Cache TTL (time-to-live) in seconds
    CACHE_TTL_MARKET_DATA: int = 300  # 5 minutes
    CACHE_TTL_PREDICTIONS: int = 900  # 15 minutes
    CACHE_TTL_REFERENCE_LEVELS: int = 1800  # 30 minutes
    CACHE_TTL_TICKERS: int = 3600  # 1 hour

    # ========================================================================
    # Table Names (for reference)
    # ========================================================================

    TABLE_TICKERS: str = 'tickers'
    TABLE_MARKET_DATA: str = 'market_data'
    TABLE_REFERENCE_LEVELS: str = 'reference_levels'
    TABLE_PREDICTIONS: str = 'predictions'
    TABLE_SIGNALS: str = 'signals'
    TABLE_INTRADAY_PREDICTIONS: str = 'intraday_predictions'
    TABLE_BLOCK_PREDICTIONS: str = 'block_predictions'
    TABLE_SESSION_RANGES: str = 'session_ranges'
    TABLE_JOB_EXECUTIONS: str = 'scheduler_job_executions'
    TABLE_JOB_METRICS: str = 'scheduler_job_metrics'
    TABLE_JOB_ALERTS: str = 'scheduler_job_alerts'

    # ========================================================================
    # Query Limits
    # ========================================================================

    # Maximum number of records to return in a single query
    DEFAULT_QUERY_LIMIT: int = 1000
    MAX_QUERY_LIMIT: int = 10000

    # ========================================================================
    # Validation Settings
    # ========================================================================

    # Price validation ranges (to catch data errors)
    MIN_VALID_PRICE: float = 0.01
    MAX_VALID_PRICE: float = 1000000.0

    # Confidence validation
    MIN_CONFIDENCE: float = 0.0
    MAX_CONFIDENCE: float = 100.0

    # Signal validation
    MIN_SIGNAL_VALUE: int = 0
    MAX_SIGNAL_VALUE: int = 1

    # ========================================================================
    # Logging Settings
    # ========================================================================

    # Enable query logging
    LOG_QUERIES: bool = os.getenv('DB_LOG_QUERIES', 'false').lower() == 'true'
    LOG_SLOW_QUERIES: bool = True
    SLOW_QUERY_THRESHOLD_MS: int = 1000  # Log queries taking more than 1 second

    # ========================================================================
    # Feature Flags
    # ========================================================================

    # Enable/disable certain features
    ENABLE_QUERY_CACHING: bool = True
    ENABLE_BATCH_OPERATIONS: bool = True
    ENABLE_AUTO_RETRY: bool = True
    ENABLE_DATA_VALIDATION: bool = True

    # ========================================================================
    # Helper Methods
    # ========================================================================

    @classmethod
    def validate_config(cls) -> bool:
        """
        Validate that all required configuration values are set.

        Returns:
            bool: True if configuration is valid, False otherwise
        """
        if not cls.SUPABASE_URL:
            raise ValueError("SUPABASE_URL is not set in environment variables")

        if not cls.SUPABASE_KEY:
            raise ValueError("SUPABASE_KEY is not set in environment variables")

        return True

    @classmethod
    def get_retention_days(cls, data_type: str) -> int:
        """
        Get retention period for a specific data type.

        Args:
            data_type: Type of data ('minute', 'hourly', 'daily', 'predictions', 'signals')

        Returns:
            int: Number of days to retain data

        Raises:
            ValueError: If data_type is not recognized
        """
        retention_map = {
            'minute': cls.RETENTION_MINUTE_DATA,
            '1m': cls.RETENTION_MINUTE_DATA,
            '5m': cls.RETENTION_MINUTE_DATA,
            '15m': cls.RETENTION_MINUTE_DATA,
            '30m': cls.RETENTION_MINUTE_DATA,
            'hourly': cls.RETENTION_HOURLY_DATA,
            '1h': cls.RETENTION_HOURLY_DATA,
            '4h': cls.RETENTION_HOURLY_DATA,
            'daily': cls.RETENTION_DAILY_DATA,
            '1d': cls.RETENTION_DAILY_DATA,
            '1w': cls.RETENTION_DAILY_DATA,
            '1M': cls.RETENTION_DAILY_DATA,
            'predictions': cls.RETENTION_PREDICTIONS,
            'signals': cls.RETENTION_SIGNALS,
        }

        if data_type not in retention_map:
            raise ValueError(f"Unknown data type: {data_type}")

        return retention_map[data_type]

    @classmethod
    def get_table_name(cls, table_type: str) -> str:
        """
        Get table name for a specific table type.

        Args:
            table_type: Type of table ('tickers', 'market_data', etc.)

        Returns:
            str: Table name

        Raises:
            ValueError: If table_type is not recognized
        """
        table_map = {
            'tickers': cls.TABLE_TICKERS,
            'market_data': cls.TABLE_MARKET_DATA,
            'reference_levels': cls.TABLE_REFERENCE_LEVELS,
            'predictions': cls.TABLE_PREDICTIONS,
            'signals': cls.TABLE_SIGNALS,
            'intraday_predictions': cls.TABLE_INTRADAY_PREDICTIONS,
            'session_ranges': cls.TABLE_SESSION_RANGES,
            'job_executions': cls.TABLE_JOB_EXECUTIONS,
            'job_metrics': cls.TABLE_JOB_METRICS,
            'job_alerts': cls.TABLE_JOB_ALERTS,
        }

        if table_type not in table_map:
            raise ValueError(f"Unknown table type: {table_type}")

        return table_map[table_type]

    @classmethod
    def get_config_dict(cls) -> Dict[str, Any]:
        """
        Get all configuration as a dictionary.

        Returns:
            Dict[str, Any]: Dictionary of configuration values
        """
        return {
            'supabase_url': cls.SUPABASE_URL,
            'connection_pool_size': cls.CONNECTION_POOL_SIZE,
            'query_timeout': cls.QUERY_TIMEOUT,
            'max_retry_attempts': cls.MAX_RETRY_ATTEMPTS,
            'batch_insert_size': cls.BATCH_INSERT_SIZE,
            'retention_minute_data': cls.RETENTION_MINUTE_DATA,
            'retention_hourly_data': cls.RETENTION_HOURLY_DATA,
            'retention_daily_data': cls.RETENTION_DAILY_DATA,
            'cache_ttl_market_data': cls.CACHE_TTL_MARKET_DATA,
            'enable_query_caching': cls.ENABLE_QUERY_CACHING,
            'enable_batch_operations': cls.ENABLE_BATCH_OPERATIONS,
            'log_queries': cls.LOG_QUERIES,
        }

    @classmethod
    def __repr__(cls) -> str:
        """String representation of configuration."""
        return f"<DatabaseConfig url={cls.SUPABASE_URL[:30]}... timeout={cls.QUERY_TIMEOUT}s>"


# Create a global instance for easy access
db_config = DatabaseConfig()

# Validate configuration on import
try:
    DatabaseConfig.validate_config()
except ValueError as e:
    import logging
    logging.warning(f"Database configuration validation failed: {e}")
