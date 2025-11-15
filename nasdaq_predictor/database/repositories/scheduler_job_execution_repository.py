"""
Scheduler job execution repository for NQP application.

This module provides CRUD operations for scheduler job execution tracking,
metrics aggregation, and failed job alerts.
"""

import logging
from typing import List, Optional, Dict, Any
from datetime import datetime, timedelta

from ..supabase_client import get_supabase_client
from ..models.scheduler_job_execution import JobExecution, JobMetrics, FailedJobAlert
from ...config.database_config import DatabaseConfig

logger = logging.getLogger(__name__)


class SchedulerJobExecutionRepository:
    """
    Repository for scheduler job execution tracking.

    Provides methods to store and retrieve job execution records, metrics,
    and failure alerts in the Supabase database.
    """

    def __init__(self):
        """Initialize the SchedulerJobExecutionRepository."""
        self.client = get_supabase_client()
        self.executions_table = DatabaseConfig.TABLE_JOB_EXECUTIONS
        self.metrics_table = DatabaseConfig.TABLE_JOB_METRICS
        self.alerts_table = DatabaseConfig.TABLE_JOB_ALERTS

    # ========================================================================
    # Job Execution Methods
    # ========================================================================

    def store_job_execution(self, execution: JobExecution) -> bool:
        """
        Store a job execution record in the database.

        Args:
            execution: JobExecution object to store

        Returns:
            bool: True if successful, False otherwise

        Example:
            >>> repo = SchedulerJobExecutionRepository()
            >>> execution = JobExecution(
            ...     job_id='market_data_sync',
            ...     job_name='Market Data Sync',
            ...     status='SUCCESS',
            ...     started_at=datetime.utcnow(),
            ...     completed_at=datetime.utcnow(),
            ...     duration_seconds=45.5
            ... )
            >>> repo.store_job_execution(execution)
            True
        """
        try:
            response = self.client.table(self.executions_table).insert(
                execution.to_dict()
            ).execute()

            if response.data:
                logger.info(f"Stored job execution for {execution.job_name}")
                return True
            else:
                logger.error(f"Failed to store job execution for {execution.job_name}")
                return False

        except Exception as e:
            logger.error(f"Error storing job execution: {e}")
            return False

    def get_job_execution(self, execution_id: str) -> Optional[JobExecution]:
        """
        Get a specific job execution record.

        Args:
            execution_id: Execution record ID (UUID)

        Returns:
            JobExecution object or None if not found
        """
        try:
            response = (
                self.client.table(self.executions_table)
                .select('*')
                .eq('id', execution_id)
                .execute()
            )

            if response.data and len(response.data) > 0:
                return JobExecution.from_dict(response.data[0])
            return None

        except Exception as e:
            logger.error(f"Error retrieving job execution {execution_id}: {e}")
            return None

    def get_job_executions_by_id(
        self,
        job_id: str,
        limit: int = 100,
        offset: int = 0
    ) -> List[JobExecution]:
        """
        Get all execution records for a specific job.

        Args:
            job_id: APScheduler job ID
            limit: Maximum number of records to return
            offset: Number of records to skip

        Returns:
            List of JobExecution objects
        """
        try:
            response = (
                self.client.table(self.executions_table)
                .select('*')
                .eq('job_id', job_id)
                .order('created_at', desc=True)
                .range(offset, offset + limit - 1)
                .execute()
            )

            if not response.data:
                logger.debug(f"No execution records found for job {job_id}")
                return []

            executions = [JobExecution.from_dict(row) for row in response.data]
            logger.debug(f"Retrieved {len(executions)} execution records for job {job_id}")
            return executions

        except Exception as e:
            logger.error(f"Error retrieving executions for job {job_id}: {e}")
            return []

    def get_recent_executions(
        self,
        hours: int = 24,
        limit: int = 100
    ) -> List[JobExecution]:
        """
        Get execution records from the last N hours.

        Args:
            hours: Number of hours to look back
            limit: Maximum number of records to return

        Returns:
            List of JobExecution objects
        """
        try:
            cutoff_time = datetime.utcnow() - timedelta(hours=hours)

            response = (
                self.client.table(self.executions_table)
                .select('*')
                .gte('created_at', cutoff_time.isoformat())
                .order('created_at', desc=True)
                .limit(limit)
                .execute()
            )

            if not response.data:
                logger.debug(f"No recent execution records found")
                return []

            executions = [JobExecution.from_dict(row) for row in response.data]
            logger.debug(f"Retrieved {len(executions)} recent execution records")
            return executions

        except Exception as e:
            logger.error(f"Error retrieving recent executions: {e}")
            return []

    def get_failed_executions(
        self,
        job_id: Optional[str] = None,
        limit: int = 50
    ) -> List[JobExecution]:
        """
        Get failed execution records.

        Args:
            job_id: Filter by specific job ID (optional)
            limit: Maximum number of records to return

        Returns:
            List of failed JobExecution objects
        """
        try:
            query = (
                self.client.table(self.executions_table)
                .select('*')
                .eq('status', 'FAILURE')
            )

            if job_id:
                query = query.eq('job_id', job_id)

            response = (
                query
                .order('created_at', desc=True)
                .limit(limit)
                .execute()
            )

            if not response.data:
                logger.debug("No failed execution records found")
                return []

            executions = [JobExecution.from_dict(row) for row in response.data]
            logger.debug(f"Retrieved {len(executions)} failed execution records")
            return executions

        except Exception as e:
            logger.error(f"Error retrieving failed executions: {e}")
            return []

    # ========================================================================
    # Job Metrics Methods
    # ========================================================================

    def store_job_metrics(self, metrics: JobMetrics) -> bool:
        """
        Store or update job metrics record.

        Args:
            metrics: JobMetrics object to store

        Returns:
            bool: True if successful, False otherwise
        """
        try:
            # Check if metrics record exists
            existing = (
                self.client.table(self.metrics_table)
                .select('id')
                .eq('job_id', metrics.job_id)
                .execute()
            )

            if existing.data and len(existing.data) > 0:
                # Update existing record
                response = (
                    self.client.table(self.metrics_table)
                    .update(metrics.to_dict())
                    .eq('job_id', metrics.job_id)
                    .execute()
                )
            else:
                # Insert new record
                response = self.client.table(self.metrics_table).insert(
                    metrics.to_dict()
                ).execute()

            if response.data:
                logger.info(f"Stored job metrics for {metrics.job_name}")
                return True
            else:
                logger.error(f"Failed to store job metrics for {metrics.job_name}")
                return False

        except Exception as e:
            logger.error(f"Error storing job metrics: {e}")
            return False

    def get_job_metrics(self, job_id: str) -> Optional[JobMetrics]:
        """
        Get metrics for a specific job.

        Args:
            job_id: APScheduler job ID

        Returns:
            JobMetrics object or None if not found
        """
        try:
            response = (
                self.client.table(self.metrics_table)
                .select('*')
                .eq('job_id', job_id)
                .execute()
            )

            if response.data and len(response.data) > 0:
                return JobMetrics.from_dict(response.data[0])
            return None

        except Exception as e:
            logger.error(f"Error retrieving metrics for job {job_id}: {e}")
            return None

    def get_all_job_metrics(self) -> List[JobMetrics]:
        """
        Get metrics for all jobs.

        Returns:
            List of JobMetrics objects
        """
        try:
            response = (
                self.client.table(self.metrics_table)
                .select('*')
                .order('updated_at', desc=True)
                .execute()
            )

            if not response.data:
                logger.debug("No job metrics found")
                return []

            metrics = [JobMetrics.from_dict(row) for row in response.data]
            logger.debug(f"Retrieved metrics for {len(metrics)} jobs")
            return metrics

        except Exception as e:
            logger.error(f"Error retrieving all job metrics: {e}")
            return []

    def update_job_metrics(
        self,
        job_id: str,
        status: str,
        duration_seconds: float,
        records_processed: int = 0,
        records_failed: int = 0
    ) -> bool:
        """
        Update job metrics after execution.

        Args:
            job_id: APScheduler job ID
            status: Execution status (SUCCESS/FAILURE/SKIPPED)
            duration_seconds: Execution duration
            records_processed: Number of records processed
            records_failed: Number of records that failed

        Returns:
            bool: True if successful, False otherwise
        """
        try:
            # Get current metrics
            metrics = self.get_job_metrics(job_id)

            if not metrics:
                logger.warning(f"No metrics found for job {job_id}, cannot update")
                return False

            # Update counts
            metrics.total_executions += 1
            metrics.last_execution_status = status
            metrics.last_execution_at = datetime.utcnow()

            if status == 'SUCCESS':
                metrics.successful_executions += 1
            elif status == 'FAILURE':
                metrics.failed_executions += 1
            elif status == 'SKIPPED':
                metrics.skipped_executions += 1

            # Update duration metrics
            if duration_seconds > 0:
                # Calculate new average
                old_total = metrics.avg_duration_seconds * (metrics.total_executions - 1)
                metrics.avg_duration_seconds = (old_total + duration_seconds) / metrics.total_executions

                # Update min/max
                if metrics.min_duration_seconds is None or duration_seconds < metrics.min_duration_seconds:
                    metrics.min_duration_seconds = duration_seconds
                if metrics.max_duration_seconds is None or duration_seconds > metrics.max_duration_seconds:
                    metrics.max_duration_seconds = duration_seconds

            # Calculate success rate
            if metrics.total_executions > 0:
                metrics.success_rate = (metrics.successful_executions / metrics.total_executions) * 100

            return self.store_job_metrics(metrics)

        except Exception as e:
            logger.error(f"Error updating metrics for job {job_id}: {e}")
            return False

    # ========================================================================
    # Job Alert Methods
    # ========================================================================

    def store_job_alert(self, alert: FailedJobAlert) -> bool:
        """
        Store a failed job alert.

        Args:
            alert: FailedJobAlert object to store

        Returns:
            bool: True if successful, False otherwise
        """
        try:
            response = self.client.table(self.alerts_table).insert(
                alert.to_dict()
            ).execute()

            if response.data:
                logger.info(f"Stored alert for failed job {alert.job_name}")
                return True
            else:
                logger.error(f"Failed to store alert for job {alert.job_name}")
                return False

        except Exception as e:
            logger.error(f"Error storing job alert: {e}")
            return False

    def get_active_alerts(self, job_id: Optional[str] = None) -> List[FailedJobAlert]:
        """
        Get unacknowledged (active) job failure alerts.

        Args:
            job_id: Filter by specific job ID (optional)

        Returns:
            List of FailedJobAlert objects
        """
        try:
            query = (
                self.client.table(self.alerts_table)
                .select('*')
                .eq('acknowledged', False)
            )

            if job_id:
                query = query.eq('job_id', job_id)

            response = (
                query
                .order('failure_timestamp', desc=True)
                .execute()
            )

            if not response.data:
                logger.debug("No active alerts found")
                return []

            alerts = [FailedJobAlert.from_dict(row) for row in response.data]
            logger.debug(f"Retrieved {len(alerts)} active alerts")
            return alerts

        except Exception as e:
            logger.error(f"Error retrieving active alerts: {e}")
            return []

    def acknowledge_alert(self, alert_id: str) -> bool:
        """
        Mark a job alert as acknowledged.

        Args:
            alert_id: Alert record ID

        Returns:
            bool: True if successful, False otherwise
        """
        try:
            response = (
                self.client.table(self.alerts_table)
                .update({'acknowledged': True})
                .eq('id', alert_id)
                .execute()
            )

            if response.data:
                logger.info(f"Acknowledged alert {alert_id}")
                return True
            else:
                logger.error(f"Failed to acknowledge alert {alert_id}")
                return False

        except Exception as e:
            logger.error(f"Error acknowledging alert: {e}")
            return False

    def get_consecutive_failures(self, job_id: str) -> int:
        """
        Get the number of consecutive failures for a job.

        Args:
            job_id: APScheduler job ID

        Returns:
            int: Number of consecutive failures (0 if last execution succeeded)
        """
        try:
            executions = self.get_job_executions_by_id(job_id, limit=10)

            if not executions:
                return 0

            # Count consecutive failures from the most recent
            consecutive_failures = 0
            for execution in executions:
                if execution.status == 'FAILURE':
                    consecutive_failures += 1
                else:
                    break

            return consecutive_failures

        except Exception as e:
            logger.error(f"Error calculating consecutive failures for {job_id}: {e}")
            return 0

    # ========================================================================
    # Helper Methods
    # ========================================================================

    def cleanup_old_executions(self, days: int = 30) -> int:
        """
        Delete job execution records older than N days.

        Args:
            days: Number of days to keep

        Returns:
            int: Number of records deleted
        """
        try:
            cutoff_date = datetime.utcnow() - timedelta(days=days)

            response = (
                self.client.table(self.executions_table)
                .delete()
                .lt('created_at', cutoff_date.isoformat())
                .execute()
            )

            logger.info(f"Deleted job execution records older than {days} days")
            return len(response.data) if response.data else 0

        except Exception as e:
            logger.error(f"Error cleaning up old executions: {e}")
            return 0

    def get_execution_statistics(self, job_id: str, hours: int = 24) -> Dict[str, Any]:
        """
        Get execution statistics for a job over a time period.

        Args:
            job_id: APScheduler job ID
            hours: Time period in hours

        Returns:
            Dict with execution statistics
        """
        try:
            cutoff_time = datetime.utcnow() - timedelta(hours=hours)

            response = (
                self.client.table(self.executions_table)
                .select('status,duration_seconds')
                .eq('job_id', job_id)
                .gte('created_at', cutoff_time.isoformat())
                .execute()
            )

            if not response.data:
                return {
                    'job_id': job_id,
                    'total': 0,
                    'successful': 0,
                    'failed': 0,
                    'skipped': 0,
                    'success_rate': 0.0,
                    'avg_duration': 0.0
                }

            total = len(response.data)
            successful = sum(1 for r in response.data if r['status'] == 'SUCCESS')
            failed = sum(1 for r in response.data if r['status'] == 'FAILURE')
            skipped = sum(1 for r in response.data if r['status'] == 'SKIPPED')

            durations = [r['duration_seconds'] for r in response.data if r['duration_seconds']]
            avg_duration = sum(durations) / len(durations) if durations else 0.0

            return {
                'job_id': job_id,
                'time_period_hours': hours,
                'total': total,
                'successful': successful,
                'failed': failed,
                'skipped': skipped,
                'success_rate': (successful / total * 100) if total > 0 else 0.0,
                'avg_duration': avg_duration
            }

        except Exception as e:
            logger.error(f"Error calculating execution statistics for {job_id}: {e}")
            return {}
