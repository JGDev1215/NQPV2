"""
Decorators for scheduled jobs with retry logic, market awareness, and error handling.

Provides production-grade decorators for APScheduler jobs:
- Exponential backoff retry logic for transient failures
- Market-aware execution (only during trading hours)
- Automatic job execution tracking and metrics
- Comprehensive error logging and reporting

Reference: SCHEDULING_JOBS_EXPERT report sections 4-6.

Example:
    >>> from nasdaq_predictor.scheduler.decorators import with_exponential_backoff, market_aware
    >>>
    >>> @market_aware(monitored_tickers=['NQ=F', 'ES=F'])
    >>> @with_exponential_backoff(max_attempts=3)
    >>> def fetch_market_data():
    ...     # This job will only run during market hours
    ...     # Will retry up to 3 times with exponential backoff on failure
    ...     return sync_data()
"""

import functools
import time
import logging
from typing import Callable, List, Optional
from datetime import datetime
import pytz

logger = logging.getLogger(__name__)


def with_exponential_backoff(
    max_attempts: int = 3,
    initial_delay_seconds: float = 60,
    backoff_multiplier: float = 2.0,
    max_delay_seconds: float = 3600,
    jitter: bool = True
):
    """Retry decorator with exponential backoff for scheduled jobs.

    Implements exponential backoff with optional jitter to handle transient
    failures. Useful for API calls and external service interactions.

    Args:
        max_attempts: Maximum number of retry attempts (including first attempt)
        initial_delay_seconds: Initial delay before first retry
        backoff_multiplier: Multiplier for delay between retries (e.g., 2.0 for exponential)
        max_delay_seconds: Maximum delay between retries (prevents unbounded growth)
        jitter: Add random jitter to delay to prevent thundering herd

    Returns:
        Decorator function

    Raises:
        Exception: Re-raises original exception after max attempts exhausted

    Example:
        @with_exponential_backoff(max_attempts=3, initial_delay_seconds=60)
        def fetch_data():
            return api.get_data()  # Retries up to 3 times on failure

        @with_exponential_backoff(
            max_attempts=5,
            initial_delay_seconds=30,
            backoff_multiplier=1.5,
            jitter=True
        )
        def sync_with_db():
            return db.sync()
    """

    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            """Wrapper with retry logic."""
            last_exception = None

            for attempt in range(1, max_attempts + 1):
                try:
                    logger.info(f"Attempt {attempt}/{max_attempts}: {func.__name__}")
                    start_time = datetime.utcnow()
                    result = func(*args, **kwargs)
                    duration = (datetime.utcnow() - start_time).total_seconds()
                    logger.info(f"✓ {func.__name__} succeeded in {duration:.2f}s")
                    return result

                except Exception as e:
                    last_exception = e
                    logger.warning(
                        f"Attempt {attempt} failed with {type(e).__name__}: {str(e)}"
                    )

                    if attempt == max_attempts:
                        # Final attempt failed
                        logger.error(
                            f"✗ {func.__name__} failed after {max_attempts} attempts: {str(e)}"
                        )
                        raise

                    # Calculate delay with exponential backoff
                    delay = min(
                        initial_delay_seconds * (backoff_multiplier ** (attempt - 1)),
                        max_delay_seconds
                    )

                    # Add jitter if enabled
                    if jitter:
                        import random
                        jitter_amount = random.uniform(0, delay * 0.1)
                        delay += jitter_amount

                    logger.info(f"Retrying in {delay:.1f}s...")
                    time.sleep(delay)

            # Should not reach here, but raise last exception just in case
            if last_exception:
                raise last_exception

        return wrapper

    return decorator


def market_aware(
    monitored_tickers: Optional[List[str]] = None,
    skip_if_closed: bool = True,
    required_all_open: bool = False
):
    """Execute job only during market trading hours.

    Checks if specified markets are open before executing job.
    Allows jobs to skip gracefully when markets are closed.

    Args:
        monitored_tickers: List of tickers to check for market status
                          (e.g., ['NQ=F', 'ES=F', '^FTSE'])
        skip_if_closed: If True, skip execution silently when markets closed
                       If False, raise exception when markets closed
        required_all_open: If True, all tickers must be open
                          If False, at least one ticker must be open

    Returns:
        Decorator function

    Example:
        # Skip job silently if US markets are closed
        @market_aware(monitored_tickers=['NQ=F', 'ES=F'])
        def sync_market_data():
            return fetch_data()

        # Fail job if market is closed
        @market_aware(
            monitored_tickers=['NQ=F'],
            skip_if_closed=False
        )
        def critical_market_job():
            return process_market_data()

        # Run only if all markets are open
        @market_aware(
            monitored_tickers=['NQ=F', 'ES=F', '^FTSE'],
            required_all_open=True
        )
        def global_market_sync():
            return sync_all_markets()
    """

    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            """Wrapper with market awareness."""
            if not monitored_tickers:
                logger.debug(f"{func.__name__}: No tickers specified, skipping market check")
                return func(*args, **kwargs)

            # Import market status service
            try:
                from nasdaq_predictor.services.market_status_service import MarketStatusService
            except ImportError:
                logger.warning("MarketStatusService not available, skipping market check")
                return func(*args, **kwargs)

            try:
                # Get current time in UTC
                current_time = datetime.now(pytz.UTC)
                market_service = MarketStatusService()

                # Check market status for each ticker
                market_statuses = {}
                open_count = 0

                for ticker in monitored_tickers:
                    try:
                        status = market_service.get_market_status(ticker, current_time)
                        market_statuses[ticker] = status.status if hasattr(status, 'status') else str(status)

                        if market_statuses[ticker] == 'OPEN':
                            open_count += 1
                    except Exception as e:
                        logger.warning(f"Error checking market status for {ticker}: {e}")
                        market_statuses[ticker] = 'UNKNOWN'

                logger.info(f"Market check for {func.__name__}: {market_statuses}")

                # Determine if should execute based on requirements
                should_execute = False

                if required_all_open:
                    # All markets must be open
                    should_execute = open_count == len(monitored_tickers)
                else:
                    # At least one market must be open
                    should_execute = open_count > 0

                if not should_execute:
                    if skip_if_closed:
                        logger.info(f"Skipping {func.__name__}: markets not in required state")
                        return {
                            'skipped': True,
                            'reason': 'market_closed',
                            'market_statuses': market_statuses
                        }
                    else:
                        raise RuntimeError(
                            f"Cannot execute {func.__name__}: markets not open "
                            f"(statuses: {market_statuses})"
                        )

                # Markets are open, execute job
                logger.info(f"Executing {func.__name__}: markets are open")
                return func(*args, **kwargs)

            except Exception as e:
                if skip_if_closed:
                    logger.warning(f"Market check failed in {func.__name__}, skipping: {e}")
                    return {
                        'skipped': True,
                        'reason': 'market_check_failed',
                        'error': str(e)
                    }
                else:
                    logger.error(f"Market check failed in {func.__name__}: {e}")
                    raise

        return wrapper

    return decorator


def job_timeout(timeout_seconds: int = 300):
    """Decorator to enforce job execution timeout.

    Logs warning if job takes longer than expected. Note: This is a
    soft timeout via logging, not actual execution termination.

    Args:
        timeout_seconds: Maximum expected execution time in seconds

    Returns:
        Decorator function

    Example:
        @job_timeout(timeout_seconds=300)  # 5 minute timeout
        def long_running_job():
            return process_large_dataset()
    """

    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            """Wrapper with timeout tracking."""
            start_time = datetime.utcnow()

            try:
                result = func(*args, **kwargs)
                duration = (datetime.utcnow() - start_time).total_seconds()

                if duration > timeout_seconds:
                    logger.warning(
                        f"⚠ {func.__name__} exceeded timeout: "
                        f"{duration:.1f}s > {timeout_seconds}s"
                    )
                else:
                    logger.info(f"✓ {func.__name__} completed in {duration:.1f}s")

                return result

            except Exception as e:
                duration = (datetime.utcnow() - start_time).total_seconds()
                logger.error(
                    f"✗ {func.__name__} failed after {duration:.1f}s: {str(e)}"
                )
                raise

        return wrapper

    return decorator


def job_metrics(job_name: str = None):
    """Decorator to collect job execution metrics.

    Tracks execution count, average duration, success/failure rates.

    Args:
        job_name: Human-readable job name for logging

    Returns:
        Decorator function

    Example:
        @job_metrics(job_name='Market Data Sync')
        def sync_market_data():
            return fetch_and_store_data()
    """

    def decorator(func: Callable) -> Callable:
        # Initialize metrics storage
        if not hasattr(func, '_metrics'):
            func._metrics = {
                'execution_count': 0,
                'success_count': 0,
                'failure_count': 0,
                'total_duration': 0.0,
                'last_execution': None,
                'last_error': None
            }

        job_display_name = job_name or func.__name__

        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            """Wrapper with metrics collection."""
            func._metrics['execution_count'] += 1
            start_time = datetime.utcnow()

            try:
                result = func(*args, **kwargs)
                func._metrics['success_count'] += 1
                duration = (datetime.utcnow() - start_time).total_seconds()
                func._metrics['total_duration'] += duration
                func._metrics['last_execution'] = start_time.isoformat()

                avg_duration = func._metrics['total_duration'] / func._metrics['execution_count']
                logger.info(
                    f"{job_display_name}: {func._metrics['execution_count']} executions, "
                    f"{func._metrics['success_count']} succeeded, "
                    f"avg {avg_duration:.1f}s"
                )

                return result

            except Exception as e:
                func._metrics['failure_count'] += 1
                func._metrics['last_error'] = str(e)
                duration = (datetime.utcnow() - start_time).total_seconds()
                func._metrics['total_duration'] += duration

                logger.error(
                    f"{job_display_name}: Failed "
                    f"({func._metrics['failure_count']}/{func._metrics['execution_count']}): {str(e)}"
                )
                raise

        def get_metrics():
            """Get current metrics for this job."""
            metrics = func._metrics.copy()
            if metrics['execution_count'] > 0:
                metrics['avg_duration'] = metrics['total_duration'] / metrics['execution_count']
                metrics['success_rate'] = (metrics['success_count'] / metrics['execution_count']) * 100
            return metrics

        func.get_metrics = get_metrics
        return wrapper

    return decorator


def composite_job(*decorators):
    """Compose multiple decorators for job function.

    Applies multiple decorators in the correct order for scheduled jobs.

    Args:
        *decorators: Decorator functions to apply in order

    Returns:
        Composite decorator

    Example:
        @composite_job(
            with_exponential_backoff(max_attempts=3),
            market_aware(monitored_tickers=['NQ=F']),
            job_timeout(timeout_seconds=300),
            job_metrics(job_name='Data Sync')
        )
        def scheduled_data_sync():
            return sync_data()
    """

    def decorator(func: Callable) -> Callable:
        result = func
        # Apply decorators in reverse order (so they apply in the order specified)
        for dec in reversed(decorators):
            result = dec(result)
        return result

    return decorator
