"""
Scheduled jobs for NQP application.

This module contains all the scheduled job functions that are executed
by APScheduler at regular intervals.
"""

import logging
from datetime import datetime
from flask import current_app

from ..services.scheduler_job_tracking_service import SchedulerJobTrackingService
from ..config.scheduler_config import SchedulerConfig

logger = logging.getLogger(__name__)

# Global Flask app instance (set during scheduler initialization)
_flask_app = None

# Initialize job tracking service
tracking_service = SchedulerJobTrackingService()


def set_flask_app(app):
    """Set the Flask app instance for use in scheduler jobs."""
    global _flask_app
    _flask_app = app
    logger.info("Flask app instance set for scheduler jobs")


def _require_app_context(func):
    """Decorator to ensure scheduler jobs run within Flask app context."""
    def wrapper(*args, **kwargs):
        global _flask_app
        if not _flask_app:
            logger.error("Flask app not initialized in scheduler jobs module")
            raise RuntimeError("Flask app not available for scheduler jobs")

        with _flask_app.app_context():
            return func(*args, **kwargs)
    return wrapper


@_require_app_context
@tracking_service.track_job_execution('market_data_sync', 'Market Data Sync')
def fetch_and_store_market_data():
    """
    Scheduled job: Fetch market data from yfinance and store in Supabase.

    This job runs every N minutes (default: 90 seconds) and:
    1. Gets all enabled tickers
    2. Fetches OHLC data from yfinance (1m, 1h, 1d)
    3. Stores data in Supabase market_data table

    Execution: Every 90 seconds (configurable)
    """
    job_start = datetime.utcnow()
    logger.info("=" * 80)
    logger.info(f"JOB STARTED: Market Data Sync at {job_start.isoformat()}")
    logger.info("=" * 80)

    try:
        # Resolve service from DI container
        sync_service = current_app.container.resolve('data_sync_service')
        results = sync_service.sync_all_tickers()

        job_end = datetime.utcnow()
        duration = (job_end - job_start).total_seconds()

        logger.info("-" * 80)
        logger.info("RESULTS:")
        logger.info(f"  Total Tickers: {results.get('total_tickers', 0)}")
        logger.info(f"  Successful: {results.get('successful', 0)}")
        logger.info(f"  Failed: {results.get('failed', 0)}")

        for ticker_result in results.get('tickers', []):
            symbol = ticker_result.get('symbol', 'Unknown')
            if ticker_result.get('success'):
                records = ticker_result.get('records_stored', 0)
                logger.info(f"  ✓ {symbol}: {records} records")
            else:
                error = ticker_result.get('error', 'Unknown error')
                logger.error(f"  ✗ {symbol}: {error}")

        logger.info("-" * 80)
        logger.info(f"JOB COMPLETED: Duration {duration:.2f}s")
        logger.info("=" * 80)

    except Exception as e:
        job_end = datetime.utcnow()
        duration = (job_end - job_start).total_seconds()

        logger.error("=" * 80)
        logger.error(f"JOB FAILED: Market Data Sync")
        logger.error(f"Error: {e}")
        logger.error(f"Duration: {duration:.2f}s")
        logger.error("=" * 80)

        # Re-raise for APScheduler to handle
        raise


@_require_app_context
@tracking_service.track_job_execution('prediction_calculation', 'Prediction Calculation')
def calculate_and_store_predictions():
    """
    Scheduled job: Calculate predictions and signals for all tickers.

    This job runs every N minutes (default: 15) and:
    1. Gets all enabled tickers
    2. Retrieves latest market data
    3. Calculates reference levels
    4. Generates predictions and signals
    5. Stores in Supabase predictions and signals tables

    Execution: Every 15 minutes (configurable)
    """
    job_start = datetime.utcnow()
    logger.info("=" * 80)
    logger.info(f"JOB STARTED: Prediction Calculation at {job_start.isoformat()}")
    logger.info("=" * 80)

    try:
        # Resolve service from DI container
        sync_service = current_app.container.resolve('data_sync_service')
        results = sync_service.calculate_predictions_for_all()

        job_end = datetime.utcnow()
        duration = (job_end - job_start).total_seconds()

        logger.info("-" * 80)
        logger.info("RESULTS:")
        logger.info(f"  Total Tickers: {results.get('total_tickers', 0)}")
        logger.info(f"  Successful: {results.get('successful', 0)}")
        logger.info(f"  Failed: {results.get('failed', 0)}")

        for pred_result in results.get('predictions', []):
            symbol = pred_result.get('symbol', 'Unknown')
            if pred_result.get('success'):
                prediction = pred_result.get('prediction', 'N/A')
                logger.info(f"  ✓ {symbol}: {prediction}")
            else:
                error = pred_result.get('error', 'Unknown error')
                logger.error(f"  ✗ {symbol}: {error}")

        logger.info("-" * 80)
        logger.info(f"JOB COMPLETED: Duration {duration:.2f}s")
        logger.info("=" * 80)

    except Exception as e:
        job_end = datetime.utcnow()
        duration = (job_end - job_start).total_seconds()

        logger.error("=" * 80)
        logger.error(f"JOB FAILED: Prediction Calculation")
        logger.error(f"Error: {e}")
        logger.error(f"Duration: {duration:.2f}s")
        logger.error("=" * 80)

        # Re-raise for APScheduler to handle
        raise


@_require_app_context
@tracking_service.track_job_execution('data_cleanup', 'Data Cleanup')
def cleanup_old_data():
    """
    Scheduled job: Clean up old data based on retention policies.

    This job runs daily at a specified time (default: 2:00 AM) and:
    1. Deletes minute data older than retention period (default: 90 days)
    2. Deletes hourly data older than retention period (default: 365 days)
    3. Deletes predictions older than retention period (default: 365 days)
    4. Logs summary of deleted records

    Execution: Daily at 2:00 AM (configurable)
    """
    job_start = datetime.utcnow()
    logger.info("=" * 80)
    logger.info(f"JOB STARTED: Data Cleanup at {job_start.isoformat()}")
    logger.info("=" * 80)

    try:
        # Resolve service from DI container
        sync_service = current_app.container.resolve('data_sync_service')
        results = sync_service.cleanup_expired_data()

        job_end = datetime.utcnow()
        duration = (job_end - job_start).total_seconds()

        logger.info("-" * 80)
        logger.info("RESULTS:")
        deleted = results.get('deleted_records', {})
        logger.info(f"  Minute Data: {deleted.get('minute_data', 0)} records")
        logger.info(f"  Hourly Data: {deleted.get('hourly_data', 0)} records")
        logger.info(f"  Predictions: {deleted.get('predictions', 0)} records")
        logger.info("-" * 80)
        logger.info(f"JOB COMPLETED: Duration {duration:.2f}s")
        logger.info("=" * 80)

    except Exception as e:
        job_end = datetime.utcnow()
        duration = (job_end - job_start).total_seconds()

        logger.error("=" * 80)
        logger.error(f"JOB FAILED: Data Cleanup")
        logger.error(f"Error: {e}")
        logger.error(f"Duration: {duration:.2f}s")
        logger.error("=" * 80)

        # Re-raise for APScheduler to handle
        raise


@_require_app_context
@tracking_service.track_job_execution('verification', 'Prediction Verification')
def verify_prediction_accuracy():
    """
    Scheduled job: Verify prediction accuracy by comparing with actual price movements.

    This job runs every 15 minutes (configurable) and:
    1. Finds predictions older than 15 minutes with NULL actual_result
    2. Fetches current price from market_data
    3. Compares price movement with prediction direction
    4. Updates actual_result, actual_price_change, verification_timestamp
    5. Logs verification statistics

    Execution: Every 15 minutes (configurable)
    """
    job_start = datetime.utcnow()
    logger.info("=" * 80)
    logger.info(f"JOB STARTED: Prediction Verification at {job_start.isoformat()}")
    logger.info("=" * 80)

    try:
        # Resolve service from DI container
        verification_service = current_app.container.resolve('verification_service')
        results = verification_service.verify_pending_predictions()

        job_end = datetime.utcnow()
        duration = (job_end - job_start).total_seconds()

        logger.info("-" * 80)
        logger.info("RESULTS:")
        logger.info(f"  Total Verified: {results.get('total_verified', 0)}")

        if results.get('errors'):
            logger.warning(f"  Errors: {len(results['errors'])}")
            for error in results['errors'][:5]:  # Show first 5 errors
                logger.warning(f"    - {error['ticker']}: {error['error']}")

        logger.info("-" * 80)
        logger.info(f"JOB COMPLETED: Duration {duration:.2f}s")
        logger.info("=" * 80)

    except Exception as e:
        job_end = datetime.utcnow()
        duration = (job_end - job_start).total_seconds()

        logger.error("=" * 80)
        logger.error(f"JOB FAILED: Prediction Verification")
        logger.error(f"Error: {e}")
        logger.error(f"Duration: {duration:.2f}s")
        logger.error("=" * 80)

        # Re-raise for APScheduler to handle
        raise


@_require_app_context
@tracking_service.track_job_execution('hourly_predictions', 'Hourly Intraday Predictions')
def generate_hourly_predictions():
    """
    Scheduled job: Generate hourly intraday predictions (0-16 hours).

    This job runs every 15 minutes (configurable) and:
    1. Gets all enabled tickers
    2. Generates predictions for all hours from midnight (0) to 4 PM (16)
    3. Stores predictions in intraday_predictions table
    4. Verifies past predictions with actual prices
    5. Uses time-decay confidence adjustment

    Execution: Every 15 minutes (configurable)
    """
    job_start = datetime.utcnow()
    logger.info("=" * 80)
    logger.info(f"JOB STARTED: Hourly Prediction Generation at {job_start.isoformat()}")
    logger.info("=" * 80)

    try:
        # Resolve service from DI container
        service = current_app.container.resolve('intraday_prediction_service')
        results = service.generate_and_store_hourly_predictions()

        job_end = datetime.utcnow()
        duration = (job_end - job_start).total_seconds()

        logger.info("-" * 80)
        logger.info("RESULTS:")
        logger.info(f"  Total Tickers: {results.get('total_tickers', 0)}")
        logger.info(f"  Successful: {results.get('successful', 0)}")
        logger.info(f"  Failed: {results.get('failed', 0)}")
        logger.info(f"  Total Predictions Stored: {results.get('total_predictions_stored', 0)}")

        for ticker_result in results.get('tickers', []):
            symbol = ticker_result.get('symbol', 'Unknown')
            if ticker_result.get('success'):
                count = ticker_result.get('predictions_stored', 0)
                logger.info(f"  ✓ {symbol}: {count} predictions")
            else:
                error = ticker_result.get('error', 'Unknown error')
                logger.error(f"  ✗ {symbol}: {error}")

        logger.info("-" * 80)
        logger.info(f"JOB COMPLETED: Duration {duration:.2f}s")
        logger.info("=" * 80)

    except Exception as e:
        job_end = datetime.utcnow()
        duration = (job_end - job_start).total_seconds()

        logger.error("=" * 80)
        logger.error(f"JOB FAILED: Hourly Prediction Generation")
        logger.error(f"Error: {e}")
        logger.error(f"Duration: {duration:.2f}s")
        logger.error("=" * 80)

        # Re-raise for APScheduler to handle
        raise


@_require_app_context
@tracking_service.track_job_execution('intraday_verification', 'Intraday Prediction Verification')
def verify_intraday_predictions():
    """
    Scheduled job: Verify intraday prediction accuracy by comparing with actual hourly prices.

    This job runs every 15 minutes (configurable) and:
    1. Finds intraday predictions with PENDING status where target hour has passed
    2. Fetches actual close price for the target hour from 30-min market data
    3. Compares price movement with prediction direction
    4. Updates actual_result, target_close_price, verified_at fields
    5. Logs verification statistics

    Execution: Every 15 minutes (configurable)
    """
    job_start = datetime.utcnow()
    logger.info("=" * 80)
    logger.info(f"JOB STARTED: Intraday Prediction Verification at {job_start.isoformat()}")
    logger.info("=" * 80)

    try:
        # Resolve service from DI container
        verification_service = current_app.container.resolve('intraday_verification_service')
        results = verification_service.verify_pending_intraday_predictions()

        job_end = datetime.utcnow()
        duration = (job_end - job_start).total_seconds()

        logger.info("-" * 80)
        logger.info("RESULTS:")
        logger.info(f"  Total Verified: {results.get('total_verified', 0)}")
        logger.info(f"  Correct: {results.get('correct', 0)}")
        logger.info(f"  Wrong: {results.get('wrong', 0)}")

        if results.get('errors'):
            logger.warning(f"  Errors: {len(results['errors'])}")
            for error in results['errors'][:5]:  # Show first 5 errors
                logger.warning(f"    - {error['ticker']}: {error['error']}")

        logger.info("-" * 80)
        logger.info(f"JOB COMPLETED: Duration {duration:.2f}s")
        logger.info("=" * 80)

    except Exception as e:
        job_end = datetime.utcnow()
        duration = (job_end - job_start).total_seconds()

        logger.error("=" * 80)
        logger.error(f"JOB FAILED: Intraday Prediction Verification")
        logger.error(f"Error: {e}")
        logger.error(f"Duration: {duration:.2f}s")
        logger.error("=" * 80)

        # Re-raise for APScheduler to handle
        raise


@_require_app_context
@tracking_service.track_job_execution('fibonacci_pivots', 'Fibonacci Pivot Calculation')
def calculate_fibonacci_pivots():
    """
    Scheduled job: Calculate Fibonacci pivot points for all tickers.

    This job runs daily at 00:05 UTC and:
    1. Calculates Fibonacci pivots for all enabled tickers
    2. Calculates for 3 timeframes: daily, weekly, monthly
    3. Stores results in fibonacci_pivots table

    Formula:
    - Pivot Point (PP) = (High + Low + Close) / 3
    - R1 = PP + 0.382 × (High - Low)
    - R2 = PP + 0.618 × (High - Low)
    - R3 = PP + 1.000 × (High - Low)
    - S1 = PP - 0.382 × (High - Low)
    - S2 = PP - 0.618 × (High - Low)
    - S3 = PP - 1.000 × (High - Low)

    Execution: Daily at 00:05 UTC (after market close data is available)
    """
    job_start = datetime.utcnow()
    logger.info("=" * 80)
    logger.info(f"JOB STARTED: Fibonacci Pivot Calculation at {job_start.isoformat()}")
    logger.info("=" * 80)

    try:
        from ..analysis.fibonacci_pivots import FibonacciPivotCalculator
        from ..database.repositories.fibonacci_pivot_repository import FibonacciPivotRepository

        # Initialize calculator and repository
        calculator = FibonacciPivotCalculator()
        repository = FibonacciPivotRepository()

        # Tickers to calculate (NQ=F, ES=F, ^FTSE)
        tickers = ['NQ=F', 'ES=F', '^FTSE']
        timeframes = ['daily', 'weekly', 'monthly']

        total_calculated = 0
        total_stored = 0
        failed_calculations = []

        # Calculate for each ticker and timeframe
        for ticker in tickers:
            for timeframe in timeframes:
                try:
                    logger.info(f"Calculating {timeframe} pivots for {ticker}...")

                    # Calculate Fibonacci pivots
                    pivot_levels = calculator.calculate_for_ticker(ticker, timeframe)

                    if pivot_levels:
                        total_calculated += 1

                        # Store in database
                        result = repository.insert_or_update(pivot_levels)

                        if result:
                            total_stored += 1
                            logger.info(
                                f"✓ {ticker} {timeframe}: "
                                f"PP={pivot_levels.pivot_point:.2f}, "
                                f"R1={pivot_levels.resistance_1:.2f}, "
                                f"S1={pivot_levels.support_1:.2f}"
                            )
                        else:
                            failed_calculations.append(f"{ticker} {timeframe} (storage failed)")
                            logger.warning(f"Failed to store {ticker} {timeframe} pivots")
                    else:
                        failed_calculations.append(f"{ticker} {timeframe} (calculation failed)")
                        logger.warning(f"Failed to calculate {ticker} {timeframe} pivots")

                except Exception as e:
                    failed_calculations.append(f"{ticker} {timeframe} ({str(e)})")
                    logger.error(f"Error processing {ticker} {timeframe}: {e}")

        job_end = datetime.utcnow()
        duration = (job_end - job_start).total_seconds()

        logger.info("-" * 80)
        logger.info("RESULTS:")
        logger.info(f"  Total Calculated: {total_calculated}")
        logger.info(f"  Total Stored: {total_stored}")
        logger.info(f"  Failed: {len(failed_calculations)}")

        if failed_calculations:
            logger.warning("  Failed Calculations:")
            for failure in failed_calculations:
                logger.warning(f"    - {failure}")

        logger.info("-" * 80)
        logger.info(f"JOB COMPLETED: Duration {duration:.2f}s")
        logger.info("=" * 80)

    except Exception as e:
        job_end = datetime.utcnow()
        duration = (job_end - job_start).total_seconds()

        logger.error("=" * 80)
        logger.error(f"JOB FAILED: Fibonacci Pivot Calculation")
        logger.error(f"Error: {e}")
        logger.error(f"Duration: {duration:.2f}s")
        logger.error("=" * 80)

        # Re-raise for APScheduler to handle
        raise
