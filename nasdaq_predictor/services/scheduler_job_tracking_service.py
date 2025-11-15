"""
Scheduler job tracking service for NQP application.

This service provides job execution tracking, metrics calculation,
and failure alert generation for all scheduled jobs.
"""

import logging
import functools
import traceback
from typing import Any, Callable, Dict, Optional
from datetime import datetime

from ..database.repositories.scheduler_job_execution_repository import SchedulerJobExecutionRepository
from ..database.models.scheduler_job_execution import JobExecution, JobMetrics, FailedJobAlert
from ..config.scheduler_config import SchedulerConfig

logger = logging.getLogger(__name__)


class SchedulerJobTrackingService:
    """
    Service for tracking scheduler job execution and calculating metrics.

    Provides decorators and methods to wrap job functions and automatically
    track execution details, calculate performance metrics, and alert on failures.
    """

    def __init__(self):
        """Initialize the SchedulerJobTrackingService."""
        self.repository = SchedulerJobExecutionRepository()
        self.tracking_enabled = SchedulerConfig.TRACK_JOB_EXECUTION
        self.history_enabled = SchedulerConfig.TRACK_EXECUTION_HISTORY

    def track_job_execution(self, job_id: str, job_name: str):
        """
        Decorator to track job execution automatically.

        Captures execution details, duration, error information, and updates metrics.
        Creates failure alerts if consecutive failures are detected.

        Args:
            job_id: APScheduler job ID
            job_name: Human-readable job name

        Returns:
            Decorator function

        Example:
            >>> service = SchedulerJobTrackingService()
            >>> @service.track_job_execution('market_data_sync', 'Market Data Sync')
            ... def fetch_and_store_market_data():
            ...     # Job logic here
            ...     pass
        """
        def decorator(func: Callable) -> Callable:
            @functools.wraps(func)
            def wrapper(*args: Any, **kwargs: Any) -> Any:
                if not self.tracking_enabled:
                    # If tracking is disabled, just run the job
                    return func(*args, **kwargs)

                execution_id = None
                started_at = datetime.utcnow()

                try:
                    # Create job execution record
                    execution = JobExecution(
                        job_id=job_id,
                        job_name=job_name,
                        status='RUNNING',
                        started_at=started_at
                    )

                    if self.history_enabled:
                        self.repository.store_job_execution(execution)
                        execution_id = execution.id

                    # Execute the job function
                    logger.info(f"Starting job: {job_name}")
                    result = func(*args, **kwargs)

                    # Calculate execution details
                    completed_at = datetime.utcnow()
                    duration_seconds = (completed_at - started_at).total_seconds()

                    # Get records processed from result if available
                    records_processed = 0
                    records_failed = 0

                    if isinstance(result, dict):
                        records_processed = result.get('records_processed', 0)
                        records_failed = result.get('records_failed', 0)

                    # Update execution record with success
                    if self.history_enabled:
                        success_execution = JobExecution(
                            job_id=job_id,
                            job_name=job_name,
                            status='SUCCESS',
                            started_at=started_at,
                            completed_at=completed_at,
                            duration_seconds=duration_seconds,
                            records_processed=records_processed,
                            records_failed=records_failed,
                            metadata={
                                'execution_id': execution_id,
                                'result': str(result) if result else None
                            }
                        )
                        self.repository.store_job_execution(success_execution)

                    # Update metrics
                    self._update_metrics(
                        job_id,
                        job_name,
                        'SUCCESS',
                        duration_seconds,
                        records_processed,
                        records_failed
                    )

                    logger.info(
                        f"Job {job_name} completed successfully in {duration_seconds:.2f}s "
                        f"(processed: {records_processed}, failed: {records_failed})"
                    )

                    return result

                except Exception as e:
                    # Calculate execution details
                    completed_at = datetime.utcnow()
                    duration_seconds = (completed_at - started_at).total_seconds()
                    error_message = str(e)
                    error_traceback = traceback.format_exc()

                    # Store failure execution
                    if self.history_enabled:
                        failure_execution = JobExecution(
                            job_id=job_id,
                            job_name=job_name,
                            status='FAILURE',
                            started_at=started_at,
                            completed_at=completed_at,
                            duration_seconds=duration_seconds,
                            error_message=error_message,
                            error_traceback=error_traceback,
                            metadata={
                                'execution_id': execution_id
                            }
                        )
                        self.repository.store_job_execution(failure_execution)

                    # Update metrics
                    self._update_metrics(
                        job_id,
                        job_name,
                        'FAILURE',
                        duration_seconds
                    )

                    # Check for consecutive failures and create alert
                    consecutive_failures = self.repository.get_consecutive_failures(job_id)
                    logger.warning(
                        f"Job {job_name} failed: {error_message} "
                        f"(consecutive failures: {consecutive_failures})"
                    )

                    if consecutive_failures >= 2:
                        self._create_failure_alert(
                            job_id,
                            job_name,
                            error_message,
                            consecutive_failures
                        )

                    # Re-raise the exception
                    raise

            return wrapper
        return decorator

    def _update_metrics(
        self,
        job_id: str,
        job_name: str,
        status: str,
        duration_seconds: float,
        records_processed: int = 0,
        records_failed: int = 0
    ) -> None:
        """
        Update job metrics after execution.

        Args:
            job_id: APScheduler job ID
            job_name: Human-readable job name
            status: Execution status (SUCCESS/FAILURE/SKIPPED)
            duration_seconds: Execution duration
            records_processed: Number of records processed
            records_failed: Number of records that failed
        """
        try:
            # Get or create metrics
            metrics = self.repository.get_job_metrics(job_id)

            if not metrics:
                # Create new metrics record
                metrics = JobMetrics(
                    job_id=job_id,
                    job_name=job_name,
                    total_executions=1,
                    successful_executions=1 if status == 'SUCCESS' else 0,
                    failed_executions=1 if status == 'FAILURE' else 0,
                    skipped_executions=1 if status == 'SKIPPED' else 0,
                    avg_duration_seconds=duration_seconds,
                    min_duration_seconds=duration_seconds if duration_seconds > 0 else None,
                    max_duration_seconds=duration_seconds if duration_seconds > 0 else None,
                    success_rate=100.0 if status == 'SUCCESS' else 0.0,
                    last_execution_status=status,
                    last_execution_at=datetime.utcnow()
                )
                self.repository.store_job_metrics(metrics)
            else:
                # Update existing metrics
                self.repository.update_job_metrics(
                    job_id,
                    status,
                    duration_seconds,
                    records_processed,
                    records_failed
                )

            logger.debug(f"Updated metrics for job {job_id}")

        except Exception as e:
            logger.error(f"Error updating metrics for job {job_id}: {e}")

    def _create_failure_alert(
        self,
        job_id: str,
        job_name: str,
        error_message: str,
        consecutive_failures: int
    ) -> None:
        """
        Create a failure alert for consecutive job failures.

        Args:
            job_id: APScheduler job ID
            job_name: Human-readable job name
            error_message: Error message from failure
            consecutive_failures: Number of consecutive failures
        """
        try:
            # Get last successful execution
            executions = self.repository.get_job_executions_by_id(job_id, limit=20)
            last_successful_execution = None

            for execution in executions:
                if execution.status == 'SUCCESS':
                    last_successful_execution = execution.started_at
                    break

            # Determine recommendation based on error
            recommendation = self._get_recommendation(error_message, job_name)

            # Create alert
            alert = FailedJobAlert(
                job_id=job_id,
                job_name=job_name,
                error_message=error_message,
                failure_timestamp=datetime.utcnow(),
                consecutive_failures=consecutive_failures,
                last_successful_execution=last_successful_execution,
                recommendation=recommendation
            )

            success = self.repository.store_job_alert(alert)

            if success:
                logger.warning(
                    f"Created alert for job {job_name}: "
                    f"{consecutive_failures} consecutive failures"
                )
            else:
                logger.error(f"Failed to create alert for job {job_name}")

        except Exception as e:
            logger.error(f"Error creating failure alert for {job_name}: {e}")

    def _get_recommendation(self, error_message: str, job_name: str) -> str:
        """
        Generate a recommendation based on the error.

        Args:
            error_message: Error message from the failure
            job_name: Human-readable job name

        Returns:
            str: Recommendation for resolving the issue
        """
        error_lower = error_message.lower()

        # Common error patterns
        if 'timeout' in error_lower or 'timed out' in error_lower:
            return (
                "Job is timing out. Consider increasing the timeout limit "
                "in SchedulerConfig or optimizing the job logic."
            )
        elif 'connection' in error_lower or 'network' in error_lower:
            return (
                "Network/connection error detected. Check internet connectivity "
                "and external service availability (Supabase, YFinance)."
            )
        elif 'authentication' in error_lower or 'unauthorized' in error_lower:
            return (
                "Authentication/authorization error. Verify API keys and "
                "credentials in environment variables."
            )
        elif 'database' in error_lower or 'supabase' in error_lower:
            return (
                "Database error detected. Check Supabase connectivity "
                "and table schema."
            )
        elif 'memory' in error_lower or 'out of' in error_lower:
            return (
                "Memory or resource exhaustion. Consider increasing system "
                "resources or optimizing job memory usage."
            )
        else:
            return (
                f"Job {job_name} has encountered consecutive failures. "
                "Check logs for more details."
            )

    def get_job_status(self, job_id: str) -> Dict[str, Any]:
        """
        Get the current status of a job.

        Args:
            job_id: APScheduler job ID

        Returns:
            Dict with job status information
        """
        try:
            # Get metrics
            metrics = self.repository.get_job_metrics(job_id)

            if not metrics:
                return {
                    'job_id': job_id,
                    'status': 'UNKNOWN',
                    'never_executed': True
                }

            # Get active alerts
            alerts = self.repository.get_active_alerts(job_id)

            # Get execution statistics (last 24 hours)
            stats = self.repository.get_execution_statistics(job_id, hours=24)

            return {
                'job_id': job_id,
                'job_name': metrics.job_name,
                'status': metrics.last_execution_status,
                'last_execution_at': metrics.last_execution_at.isoformat() if metrics.last_execution_at else None,
                'total_executions': metrics.total_executions,
                'successful_executions': metrics.successful_executions,
                'failed_executions': metrics.failed_executions,
                'success_rate': round(metrics.success_rate, 2),
                'avg_duration': round(metrics.avg_duration_seconds, 2),
                'min_duration': round(metrics.min_duration_seconds, 2) if metrics.min_duration_seconds else None,
                'max_duration': round(metrics.max_duration_seconds, 2) if metrics.max_duration_seconds else None,
                'last_error_message': metrics.last_error_message,
                'active_alerts': len(alerts),
                'last_24h_stats': stats
            }

        except Exception as e:
            logger.error(f"Error retrieving job status for {job_id}: {e}")
            return {'error': str(e)}

    def get_all_job_statuses(self) -> Dict[str, Any]:
        """
        Get status for all jobs.

        Returns:
            Dict with all job statuses
        """
        try:
            metrics_list = self.repository.get_all_job_metrics()
            statuses = {}

            for metrics in metrics_list:
                statuses[metrics.job_id] = self.get_job_status(metrics.job_id)

            return {
                'total_jobs': len(statuses),
                'jobs': statuses
            }

        except Exception as e:
            logger.error(f"Error retrieving all job statuses: {e}")
            return {'error': str(e)}
