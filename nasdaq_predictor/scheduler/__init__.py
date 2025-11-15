"""
Scheduler package for NQP application.

This package provides background job scheduling using APScheduler to automatically
fetch market data, calculate predictions, and perform maintenance tasks.

Usage:
    from nasdaq_predictor.scheduler import start_scheduler, stop_scheduler, get_scheduler

    # Start the scheduler
    start_scheduler()

    # Get scheduler instance
    scheduler = get_scheduler()

    # Stop the scheduler
    stop_scheduler()
"""

import logging
from typing import Optional
from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.jobstores.memory import MemoryJobStore
from apscheduler.jobstores.sqlalchemy import SQLAlchemyJobStore
from apscheduler.executors.pool import ThreadPoolExecutor
from pytz import utc

from ..config.scheduler_config import SchedulerConfig

logger = logging.getLogger(__name__)

# Global scheduler instance
_scheduler_instance: Optional[BackgroundScheduler] = None


def create_scheduler() -> BackgroundScheduler:
    """
    Create and configure a new BackgroundScheduler instance.

    Supports both memory-based and persistent (Supabase) job stores.
    Job persistence allows jobs to survive application restarts.

    Returns:
        BackgroundScheduler: Configured scheduler instance
    """
    # Determine job store type
    job_store_type = SchedulerConfig.JOB_STORE_TYPE.lower()

    if job_store_type == 'supabase' and SchedulerConfig.SUPABASE_DB_URL:
        try:
            # Use Supabase PostgreSQL for persistent job storage
            jobstores = {
                'default': SQLAlchemyJobStore(
                    url=SchedulerConfig.SUPABASE_DB_URL,
                    engine_options={'pool_pre_ping': True}  # Test connection before use
                )
            }
            logger.info(
                "Scheduler configured with Supabase PostgreSQL job store "
                "(jobs will persist across restarts)"
            )
        except Exception as e:
            logger.warning(
                f"Failed to connect to Supabase job store: {e}. "
                f"Falling back to memory-based job store (jobs will be lost on restart)"
            )
            jobstores = {'default': MemoryJobStore()}
    else:
        # Use in-memory job store (default, no persistence)
        jobstores = {'default': MemoryJobStore()}
        logger.info(
            "Scheduler configured with memory-based job store "
            "(jobs will be lost on restart)"
        )

    executors = {
        'default': ThreadPoolExecutor(max_workers=3)
    }

    job_defaults = {
        'coalesce': SchedulerConfig.COALESCE,
        'max_instances': SchedulerConfig.MAX_INSTANCES,
        'misfire_grace_time': SchedulerConfig.MISFIRE_GRACE_TIME
    }

    scheduler = BackgroundScheduler(
        jobstores=jobstores,
        executors=executors,
        job_defaults=job_defaults,
        timezone=utc
    )

    logger.info("BackgroundScheduler created successfully")
    return scheduler


def get_scheduler() -> BackgroundScheduler:
    """
    Get the global scheduler instance.

    Returns:
        BackgroundScheduler: Global scheduler instance

    Raises:
        RuntimeError: If scheduler has not been initialized
    """
    global _scheduler_instance

    if _scheduler_instance is None:
        raise RuntimeError("Scheduler has not been initialized. Call start_scheduler() first.")

    return _scheduler_instance


def start_scheduler() -> BackgroundScheduler:
    """
    Start the background scheduler and register all jobs.

    Returns:
        BackgroundScheduler: Started scheduler instance
    """
    global _scheduler_instance

    if _scheduler_instance is not None and _scheduler_instance.running:
        logger.warning("Scheduler is already running")
        return _scheduler_instance

    if not SchedulerConfig.ENABLED:
        logger.info("Scheduler is disabled in configuration")
        return None

    logger.info("Starting background scheduler...")

    # Create scheduler instance
    _scheduler_instance = create_scheduler()

    # Register jobs
    _register_jobs(_scheduler_instance)

    # Start the scheduler
    _scheduler_instance.start()

    logger.info("Background scheduler started successfully")
    logger.info(f"Registered jobs: {[job.id for job in _scheduler_instance.get_jobs()]}")

    return _scheduler_instance


def stop_scheduler():
    """
    Stop the background scheduler gracefully.
    """
    global _scheduler_instance

    if _scheduler_instance is None:
        logger.warning("Scheduler has not been initialized")
        return

    if not _scheduler_instance.running:
        logger.warning("Scheduler is not running")
        return

    logger.info("Stopping background scheduler...")

    _scheduler_instance.shutdown(wait=True)

    logger.info("Background scheduler stopped successfully")


def _register_jobs(scheduler: BackgroundScheduler):
    """
    Register all scheduled jobs with the scheduler.

    Args:
        scheduler: BackgroundScheduler instance
    """
    from .jobs import (
        fetch_and_store_market_data,
        calculate_and_store_predictions,
        cleanup_old_data,
        verify_prediction_accuracy,
        generate_hourly_predictions,
        verify_intraday_predictions,
        calculate_fibonacci_pivots
    )

    # Job 1: Market data sync (interval-based: every 90 seconds for high-frequency updates)
    # Runs every 90 seconds (1.5 minutes) to ensure continuous market data availability
    if SchedulerConfig.ENABLE_MARKET_DATA_JOB:
        scheduler.add_job(
            fetch_and_store_market_data,
            'interval',
            seconds=90,
            id=SchedulerConfig.JOB_ID_MARKET_DATA,
            name='Market Data Sync',
            replace_existing=True
        )
        logger.info(
            f"Registered job: {SchedulerConfig.JOB_ID_MARKET_DATA} "
            f"(interval: every 90 seconds for continuous market data availability)"
        )

    # Job 2: Prediction calculation (cron-based: runs after data sync completes)
    # Runs at :08, :23, :38, :53 (6-minute offset after market timeframes)
    # This ensures market data sync (at :02, :17, :32, :47) completes before predictions run
    # 6-minute gap accommodates data sync that can take up to 5 minutes with retries
    if SchedulerConfig.ENABLE_PREDICTION_JOB:
        scheduler.add_job(
            calculate_and_store_predictions,
            'cron',
            minute='8,23,38,53',
            id=SchedulerConfig.JOB_ID_PREDICTION,
            name='Prediction Calculation',
            replace_existing=True
        )
        logger.info(
            f"Registered job: {SchedulerConfig.JOB_ID_PREDICTION} "
            f"(cron: at minutes 8,23,38,53 - 6-min offset, runs after data sync)"
        )

    # Job 3: Data cleanup (daily at specified time)
    if SchedulerConfig.ENABLE_CLEANUP_JOB:
        scheduler.add_job(
            cleanup_old_data,
            'cron',
            hour=SchedulerConfig.CLEANUP_HOUR,
            minute=SchedulerConfig.CLEANUP_MINUTE,
            id=SchedulerConfig.JOB_ID_CLEANUP,
            name='Data Cleanup',
            replace_existing=True
        )
        logger.info(
            f"Registered job: {SchedulerConfig.JOB_ID_CLEANUP} "
            f"(daily at {SchedulerConfig.CLEANUP_HOUR}:{SchedulerConfig.CLEANUP_MINUTE:02d})"
        )

    # Job 4: Prediction verification (cron-based: runs after predictions complete)
    # Runs at :13, :28, :43, :58 (11-minute offset after market timeframes)
    # This ensures prediction calculation (at :08, :23, :38, :53) completes before verification
    # 11-minute gap: allows prediction calculation ~5 minutes + buffer
    if SchedulerConfig.ENABLE_VERIFICATION_JOB:
        scheduler.add_job(
            verify_prediction_accuracy,
            'cron',
            minute='13,28,43,58',
            id='verification',
            name='Prediction Verification',
            replace_existing=True
        )
        logger.info(
            f"Registered job: verification "
            f"(cron: at minutes 13,28,43,58 - 11-min offset, runs after predictions)"
        )

    # Job 5: Hourly intraday predictions (cron-based: after prediction calculation)
    # Runs at :13, :28, :43, :58 (5-minute offset after prediction calculation at :08)
    # Separated from daily prediction calculation to avoid concurrent resource contention
    scheduler.add_job(
        generate_hourly_predictions,
        'cron',
        minute='13,28,43,58',
        id='hourly_predictions',
        name='Hourly Intraday Predictions',
        replace_existing=True
    )
    logger.info(
        f"Registered job: hourly_predictions (cron: at minutes 13,28,43,58 - 5-min offset after daily predictions)"
    )

    # Job 6: Intraday prediction verification (cron-based: runs after hourly predictions)
    # Runs at :18, :33, :48, :03 (10-minute offset after hourly predictions at :08/:13)
    # Separated from daily verification to reduce resource contention
    scheduler.add_job(
        verify_intraday_predictions,
        'cron',
        minute='18,33,48,3',
        id='intraday_verification',
        name='Intraday Prediction Verification',
        replace_existing=True
    )
    logger.info(
        f"Registered job: intraday_verification (cron: at minutes 18,33,48,3 - 10-min offset)"
    )

    # Job 7: Fibonacci pivot points (daily at 00:05 UTC)
    scheduler.add_job(
        calculate_fibonacci_pivots,
        'cron',
        hour=0,
        minute=5,
        id='fibonacci_pivots',
        name='Fibonacci Pivot Calculation',
        replace_existing=True
    )
    logger.info(
        f"Registered job: fibonacci_pivots (daily at 00:05 UTC)"
    )


def get_scheduler_status() -> dict:
    """
    Get the current status of the scheduler and all jobs.

    Returns:
        dict: Scheduler status information
    """
    global _scheduler_instance

    if _scheduler_instance is None:
        return {
            'initialized': False,
            'running': False,
            'jobs': []
        }

    jobs = []
    for job in _scheduler_instance.get_jobs():
        jobs.append({
            'id': job.id,
            'name': job.name,
            'next_run': job.next_run_time.isoformat() if job.next_run_time else None,
            'trigger': str(job.trigger)
        })

    return {
        'initialized': True,
        'running': _scheduler_instance.running,
        'timezone': str(_scheduler_instance.timezone),
        'jobs': jobs
    }


def get_next_data_update() -> dict:
    """
    Get the next scheduled data update time for intelligent frontend refresh.

    Returns the soonest upcoming job run time between market data sync and prediction jobs,
    along with metadata about which job will run.

    Returns:
        dict: Contains next_update_time (ISO format), seconds_until_update, job_type, job_name
    """
    from datetime import datetime
    import pytz

    global _scheduler_instance

    if _scheduler_instance is None or not _scheduler_instance.running:
        return {
            'next_update_time': None,
            'seconds_until_update': None,
            'job_type': None,
            'job_name': None,
            'error': 'Scheduler not running'
        }

    # Get market data and prediction jobs
    relevant_job_ids = ['market_data_sync', 'prediction_calculation']
    upcoming_jobs = []

    for job in _scheduler_instance.get_jobs():
        if job.id in relevant_job_ids and job.next_run_time:
            upcoming_jobs.append({
                'id': job.id,
                'name': job.name,
                'next_run': job.next_run_time
            })

    if not upcoming_jobs:
        return {
            'next_update_time': None,
            'seconds_until_update': None,
            'job_type': None,
            'job_name': None,
            'error': 'No upcoming data update jobs'
        }

    # Find the soonest job
    soonest_job = min(upcoming_jobs, key=lambda j: j['next_run'])

    # Calculate seconds until job runs
    now = datetime.now(pytz.UTC)
    seconds_until = (soonest_job['next_run'] - now).total_seconds()

    # Map job ID to type
    job_type_map = {
        'market_data_sync': 'market_data',
        'prediction_calculation': 'prediction'
    }

    return {
        'next_update_time': soonest_job['next_run'].isoformat(),
        'seconds_until_update': int(seconds_until),
        'job_type': job_type_map.get(soonest_job['id'], 'unknown'),
        'job_name': soonest_job['name']
    }


__all__ = [
    'start_scheduler',
    'stop_scheduler',
    'get_scheduler',
    'get_scheduler_status',
    'get_next_data_update'
]
