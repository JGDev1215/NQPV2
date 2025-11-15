"""
Scheduler configuration for NQP application.

This module contains configuration settings for the background scheduler
that handles periodic data fetching, prediction calculation, and data cleanup.
"""

import os
from dotenv import load_dotenv

load_dotenv()


class SchedulerConfig:
    """Configuration settings for APScheduler."""

    # ========================================================================
    # Scheduler Settings
    # ========================================================================

    # Enable/disable scheduler
    ENABLED: bool = os.getenv('SCHEDULER_ENABLED', 'true').lower() == 'true'

    # Scheduler timezone
    TIMEZONE: str = os.getenv('SCHEDULER_TIMEZONE', 'UTC')

    # Job execution settings
    MISFIRE_GRACE_TIME: int = int(os.getenv('SCHEDULER_MISFIRE_GRACE_TIME', '300'))  # 5 minutes
    COALESCE: bool = True  # Combine multiple missed executions into one
    MAX_INSTANCES: int = 1  # Only one instance of each job at a time

    # ========================================================================
    # Job Intervals
    # ========================================================================

    # Market data sync interval (minutes)
    MARKET_DATA_INTERVAL: int = int(os.getenv('SCHEDULER_MARKET_DATA_INTERVAL_MINUTES', '10'))

    # Prediction calculation interval (minutes)
    PREDICTION_INTERVAL: int = int(os.getenv('SCHEDULER_PREDICTION_INTERVAL_MINUTES', '15'))

    # Data cleanup schedule (cron: hour, minute)
    CLEANUP_HOUR: int = int(os.getenv('SCHEDULER_CLEANUP_HOUR', '2'))
    CLEANUP_MINUTE: int = int(os.getenv('SCHEDULER_CLEANUP_MINUTE', '0'))

    # Prediction verification interval (minutes)
    VERIFICATION_INTERVAL: int = int(os.getenv('VERIFICATION_INTERVAL_MINUTES', '15'))

    # ========================================================================
    # Timing Offsets (for synchronized execution with YFinance data delay)
    # ========================================================================

    # Data sync offset: Wait N minutes after timeframe completes (:00, :15, :30, :45)
    # YFinance has 1-2 minute latency for minute-level data, so 2 min is conservative
    DATA_SYNC_OFFSET_MINUTES: int = int(os.getenv('SCHEDULER_DATA_SYNC_OFFSET_MINUTES', '2'))

    # Prediction offset: Wait N minutes after timeframe for predictions to run
    # Accounts for: 2 min data delay + 3 min for sync to complete = 5 min total
    PREDICTION_OFFSET_MINUTES: int = int(os.getenv('SCHEDULER_PREDICTION_OFFSET_MINUTES', '5'))

    # Verification offset: Wait N minutes after predictions for verification
    # Accounts for: 5 min prediction time + 2 min for calculation to complete = 7 min total
    VERIFICATION_OFFSET_MINUTES: int = int(os.getenv('SCHEDULER_VERIFICATION_OFFSET_MINUTES', '7'))

    # ========================================================================
    # Job Store Configuration (Persistence)
    # ========================================================================

    # Job store type: 'memory' or 'supabase'
    JOB_STORE_TYPE: str = os.getenv('SCHEDULER_JOB_STORE_TYPE', 'supabase')

    # Supabase PostgreSQL connection for job persistence
    # Format: postgresql://user:password@host:port/database
    # Get from Supabase project settings > Database > Connection string
    SUPABASE_DB_URL: str = os.getenv(
        'SUPABASE_DB_URL',
        os.getenv('DATABASE_URL', '')  # Fallback to DATABASE_URL if available
    )

    # Job execution tracking settings
    TRACK_JOB_EXECUTION: bool = os.getenv('TRACK_JOB_EXECUTION', 'true').lower() == 'true'
    TRACK_EXECUTION_HISTORY: bool = os.getenv('TRACK_EXECUTION_HISTORY', 'true').lower() == 'true'

    # ========================================================================
    # Retry Settings
    # ========================================================================

    # Maximum retry attempts for failed jobs
    MAX_RETRY_ATTEMPTS: int = int(os.getenv('MAX_RETRY_ATTEMPTS', '3'))

    # Initial retry delay in seconds
    RETRY_BACKOFF_SECONDS: int = int(os.getenv('RETRY_BACKOFF_SECONDS', '60'))

    # Exponential backoff multiplier
    RETRY_BACKOFF_MULTIPLIER: float = 2.0

    # ========================================================================
    # Job Timeouts
    # ========================================================================

    # Maximum execution time for jobs (seconds)
    MARKET_DATA_TIMEOUT: int = int(os.getenv('JOB_MARKET_DATA_TIMEOUT', '300'))  # 5 minutes
    PREDICTION_TIMEOUT: int = int(os.getenv('JOB_PREDICTION_TIMEOUT', '180'))  # 3 minutes
    CLEANUP_TIMEOUT: int = int(os.getenv('JOB_CLEANUP_TIMEOUT', '600'))  # 10 minutes

    # ========================================================================
    # Monitoring & Logging
    # ========================================================================

    # Log level for scheduler
    LOG_LEVEL: str = os.getenv('SCHEDULER_LOG_LEVEL', 'INFO')

    # Enable job notifications
    ENABLE_NOTIFICATIONS: bool = os.getenv('ENABLE_JOB_NOTIFICATIONS', 'false').lower() == 'true'

    # Notification channels
    NOTIFICATION_EMAIL: str = os.getenv('NOTIFICATION_EMAIL', '')
    NOTIFICATION_SLACK_WEBHOOK: str = os.getenv('NOTIFICATION_SLACK_WEBHOOK', '')

    # ========================================================================
    # Job IDs
    # ========================================================================

    JOB_ID_MARKET_DATA: str = 'market_data_sync'
    JOB_ID_PREDICTION: str = 'prediction_calculation'
    JOB_ID_CLEANUP: str = 'data_cleanup'

    # ========================================================================
    # Feature Flags
    # ========================================================================

    # Enable individual jobs
    ENABLE_MARKET_DATA_JOB: bool = os.getenv('ENABLE_MARKET_DATA_JOB', 'true').lower() == 'true'
    ENABLE_PREDICTION_JOB: bool = os.getenv('ENABLE_PREDICTION_JOB', 'true').lower() == 'true'
    ENABLE_CLEANUP_JOB: bool = os.getenv('ENABLE_CLEANUP_JOB', 'true').lower() == 'true'
    ENABLE_VERIFICATION_JOB: bool = os.getenv('ENABLE_VERIFICATION_JOB', 'true').lower() == 'true'

    # ========================================================================
    # Helper Methods
    # ========================================================================

    @classmethod
    def get_retry_delay(cls, attempt: int) -> int:
        """
        Calculate retry delay with exponential backoff.

        Args:
            attempt: Retry attempt number (1-based)

        Returns:
            int: Delay in seconds
        """
        return int(cls.RETRY_BACKOFF_SECONDS * (cls.RETRY_BACKOFF_MULTIPLIER ** (attempt - 1)))

    @classmethod
    def is_job_enabled(cls, job_id: str) -> bool:
        """
        Check if a specific job is enabled.

        Args:
            job_id: Job identifier

        Returns:
            bool: True if job is enabled
        """
        job_flags = {
            cls.JOB_ID_MARKET_DATA: cls.ENABLE_MARKET_DATA_JOB,
            cls.JOB_ID_PREDICTION: cls.ENABLE_PREDICTION_JOB,
            cls.JOB_ID_CLEANUP: cls.ENABLE_CLEANUP_JOB,
        }
        return job_flags.get(job_id, False)

    @classmethod
    def get_config_dict(cls) -> dict:
        """
        Get all configuration as a dictionary.

        Returns:
            dict: Configuration values
        """
        return {
            'enabled': cls.ENABLED,
            'timezone': cls.TIMEZONE,
            'market_data_interval': cls.MARKET_DATA_INTERVAL,
            'prediction_interval': cls.PREDICTION_INTERVAL,
            'cleanup_hour': cls.CLEANUP_HOUR,
            'max_retry_attempts': cls.MAX_RETRY_ATTEMPTS,
            'jobs_enabled': {
                'market_data': cls.ENABLE_MARKET_DATA_JOB,
                'prediction': cls.ENABLE_PREDICTION_JOB,
                'cleanup': cls.ENABLE_CLEANUP_JOB,
            }
        }

    @classmethod
    def validate_config(cls) -> bool:
        """
        Validate scheduler configuration.

        Returns:
            bool: True if configuration is valid

        Raises:
            ValueError: If configuration is invalid
        """
        if cls.MARKET_DATA_INTERVAL < 1:
            raise ValueError("Market data interval must be at least 1 minute")

        if cls.PREDICTION_INTERVAL < 1:
            raise ValueError("Prediction interval must be at least 1 minute")

        if not 0 <= cls.CLEANUP_HOUR <= 23:
            raise ValueError("Cleanup hour must be between 0 and 23")

        if not 0 <= cls.CLEANUP_MINUTE <= 59:
            raise ValueError("Cleanup minute must be between 0 and 59")

        return True

    @classmethod
    def __repr__(cls) -> str:
        """String representation of configuration."""
        return (
            f"<SchedulerConfig enabled={cls.ENABLED} "
            f"market_data_interval={cls.MARKET_DATA_INTERVAL}min "
            f"prediction_interval={cls.PREDICTION_INTERVAL}min>"
        )


# Create global instance
scheduler_config = SchedulerConfig()

# Validate configuration on import
try:
    SchedulerConfig.validate_config()
except ValueError as e:
    import logging
    logging.warning(f"Scheduler configuration validation failed: {e}")
