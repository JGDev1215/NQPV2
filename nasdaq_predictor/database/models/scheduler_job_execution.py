"""
Database models for scheduler job execution tracking.

Tracks execution history, failures, and performance metrics for all scheduled jobs.
"""

from datetime import datetime
from typing import Optional
import uuid


class JobExecution:
    """Track execution of a scheduled job."""

    def __init__(
        self,
        job_id: str,
        job_name: str,
        status: str,  # 'SUCCESS', 'FAILURE', 'SKIPPED', 'RUNNING'
        started_at: datetime,
        completed_at: Optional[datetime] = None,
        duration_seconds: Optional[float] = None,
        error_message: Optional[str] = None,
        error_traceback: Optional[str] = None,
        records_processed: int = 0,
        records_failed: int = 0,
        metadata: Optional[dict] = None,
    ):
        """
        Initialize job execution record.

        Args:
            job_id: APScheduler job ID
            job_name: Human-readable job name
            status: Execution status (SUCCESS/FAILURE/SKIPPED/RUNNING)
            started_at: Job start timestamp
            completed_at: Job completion timestamp
            duration_seconds: Execution duration in seconds
            error_message: Error message if job failed
            error_traceback: Full error traceback
            records_processed: Number of records processed
            records_failed: Number of records that failed
            metadata: Additional execution metadata
        """
        self.id = str(uuid.uuid4())
        self.job_id = job_id
        self.job_name = job_name
        self.status = status
        self.started_at = started_at
        self.completed_at = completed_at
        self.duration_seconds = duration_seconds
        self.error_message = error_message
        self.error_traceback = error_traceback
        self.records_processed = records_processed
        self.records_failed = records_failed
        self.metadata = metadata or {}
        self.created_at = datetime.utcnow()

    def to_dict(self) -> dict:
        """Convert to dictionary for storage."""
        return {
            'id': self.id,
            'job_id': self.job_id,
            'job_name': self.job_name,
            'status': self.status,
            'started_at': self.started_at.isoformat() if self.started_at else None,
            'completed_at': self.completed_at.isoformat() if self.completed_at else None,
            'duration_seconds': self.duration_seconds,
            'error_message': self.error_message,
            'error_traceback': self.error_traceback,
            'records_processed': self.records_processed,
            'records_failed': self.records_failed,
            'metadata': self.metadata,
            'created_at': self.created_at.isoformat(),
        }

    @classmethod
    def from_dict(cls, data: dict) -> 'JobExecution':
        """Create JobExecution from dictionary."""
        return cls(
            job_id=data.get('job_id'),
            job_name=data.get('job_name'),
            status=data.get('status'),
            started_at=datetime.fromisoformat(data['started_at']) if data.get('started_at') else None,
            completed_at=datetime.fromisoformat(data['completed_at']) if data.get('completed_at') else None,
            duration_seconds=data.get('duration_seconds'),
            error_message=data.get('error_message'),
            error_traceback=data.get('error_traceback'),
            records_processed=data.get('records_processed', 0),
            records_failed=data.get('records_failed', 0),
            metadata=data.get('metadata', {})
        )


class JobMetrics:
    """Track performance metrics for a job over time."""

    def __init__(
        self,
        job_id: str,
        job_name: str,
        total_executions: int = 0,
        successful_executions: int = 0,
        failed_executions: int = 0,
        skipped_executions: int = 0,
        avg_duration_seconds: float = 0.0,
        min_duration_seconds: Optional[float] = None,
        max_duration_seconds: Optional[float] = None,
        success_rate: float = 0.0,
        last_execution_status: Optional[str] = None,
        last_execution_at: Optional[datetime] = None,
        last_error_message: Optional[str] = None,
    ):
        """
        Initialize job metrics.

        Args:
            job_id: APScheduler job ID
            job_name: Human-readable job name
            total_executions: Total number of executions
            successful_executions: Number of successful executions
            failed_executions: Number of failed executions
            skipped_executions: Number of skipped executions
            avg_duration_seconds: Average execution duration
            min_duration_seconds: Minimum execution duration
            max_duration_seconds: Maximum execution duration
            success_rate: Success rate percentage (0-100)
            last_execution_status: Status of last execution
            last_execution_at: Timestamp of last execution
            last_error_message: Error message from last failure
        """
        self.id = str(uuid.uuid4())
        self.job_id = job_id
        self.job_name = job_name
        self.total_executions = total_executions
        self.successful_executions = successful_executions
        self.failed_executions = failed_executions
        self.skipped_executions = skipped_executions
        self.avg_duration_seconds = avg_duration_seconds
        self.min_duration_seconds = min_duration_seconds
        self.max_duration_seconds = max_duration_seconds
        self.success_rate = success_rate
        self.last_execution_status = last_execution_status
        self.last_execution_at = last_execution_at
        self.last_error_message = last_error_message
        self.updated_at = datetime.utcnow()

    def to_dict(self) -> dict:
        """Convert to dictionary for storage."""
        return {
            'id': self.id,
            'job_id': self.job_id,
            'job_name': self.job_name,
            'total_executions': self.total_executions,
            'successful_executions': self.successful_executions,
            'failed_executions': self.failed_executions,
            'skipped_executions': self.skipped_executions,
            'avg_duration_seconds': self.avg_duration_seconds,
            'min_duration_seconds': self.min_duration_seconds,
            'max_duration_seconds': self.max_duration_seconds,
            'success_rate': self.success_rate,
            'last_execution_status': self.last_execution_status,
            'last_execution_at': self.last_execution_at.isoformat() if self.last_execution_at else None,
            'last_error_message': self.last_error_message,
            'updated_at': self.updated_at.isoformat(),
        }

    @classmethod
    def from_dict(cls, data: dict) -> 'JobMetrics':
        """Create JobMetrics from dictionary."""
        return cls(
            job_id=data.get('job_id'),
            job_name=data.get('job_name'),
            total_executions=data.get('total_executions', 0),
            successful_executions=data.get('successful_executions', 0),
            failed_executions=data.get('failed_executions', 0),
            skipped_executions=data.get('skipped_executions', 0),
            avg_duration_seconds=data.get('avg_duration_seconds', 0.0),
            min_duration_seconds=data.get('min_duration_seconds'),
            max_duration_seconds=data.get('max_duration_seconds'),
            success_rate=data.get('success_rate', 0.0),
            last_execution_status=data.get('last_execution_status'),
            last_execution_at=datetime.fromisoformat(data['last_execution_at']) if data.get('last_execution_at') else None,
            last_error_message=data.get('last_error_message')
        )


class FailedJobAlert:
    """Alert for failed scheduled job requiring attention."""

    def __init__(
        self,
        job_id: str,
        job_name: str,
        error_message: str,
        failure_timestamp: datetime,
        consecutive_failures: int = 1,
        last_successful_execution: Optional[datetime] = None,
        recommendation: Optional[str] = None,
    ):
        """
        Initialize failed job alert.

        Args:
            job_id: APScheduler job ID
            job_name: Human-readable job name
            error_message: Error message from failure
            failure_timestamp: When the job failed
            consecutive_failures: Number of consecutive failures
            last_successful_execution: Timestamp of last successful run
            recommendation: Recommended action to resolve
        """
        self.id = str(uuid.uuid4())
        self.job_id = job_id
        self.job_name = job_name
        self.error_message = error_message
        self.failure_timestamp = failure_timestamp
        self.consecutive_failures = consecutive_failures
        self.last_successful_execution = last_successful_execution
        self.recommendation = recommendation
        self.acknowledged = False
        self.created_at = datetime.utcnow()

    def to_dict(self) -> dict:
        """Convert to dictionary for storage."""
        return {
            'id': self.id,
            'job_id': self.job_id,
            'job_name': self.job_name,
            'error_message': self.error_message,
            'failure_timestamp': self.failure_timestamp.isoformat(),
            'consecutive_failures': self.consecutive_failures,
            'last_successful_execution': self.last_successful_execution.isoformat() if self.last_successful_execution else None,
            'recommendation': self.recommendation,
            'acknowledged': self.acknowledged,
            'created_at': self.created_at.isoformat(),
        }

    @classmethod
    def from_dict(cls, data: dict) -> 'FailedJobAlert':
        """Create FailedJobAlert from dictionary."""
        return cls(
            job_id=data.get('job_id'),
            job_name=data.get('job_name'),
            error_message=data.get('error_message'),
            failure_timestamp=datetime.fromisoformat(data['failure_timestamp']) if data.get('failure_timestamp') else None,
            consecutive_failures=data.get('consecutive_failures', 1),
            last_successful_execution=datetime.fromisoformat(data['last_successful_execution']) if data.get('last_successful_execution') else None,
            recommendation=data.get('recommendation')
        )
