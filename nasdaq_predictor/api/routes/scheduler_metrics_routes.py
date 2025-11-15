"""
Scheduler metrics and monitoring REST API endpoints.

Provides endpoints for monitoring scheduled job execution, viewing metrics,
execution history, and managing failure alerts.
"""

import logging
from flask import Blueprint, request, jsonify
from datetime import datetime

from ...services.scheduler_job_tracking_service import SchedulerJobTrackingService
from ...database.repositories.scheduler_job_execution_repository import SchedulerJobExecutionRepository

logger = logging.getLogger(__name__)

# Create blueprint
scheduler_metrics_bp = Blueprint('scheduler_metrics', __name__, url_prefix='/api/scheduler')

# Initialize services
tracking_service = SchedulerJobTrackingService()
execution_repo = SchedulerJobExecutionRepository()


# ========================================================================
# Scheduler Status Endpoints
# ========================================================================

@scheduler_metrics_bp.route('/status', methods=['GET'])
def get_scheduler_status():
    """
    Get overall scheduler status and all job statuses.

    Returns:
        Dict with scheduler status and metrics for all jobs
    """
    try:
        statuses = tracking_service.get_all_job_statuses()
        return jsonify(statuses), 200
    except Exception as e:
        logger.error(f"Error retrieving scheduler status: {e}")
        return jsonify({'error': str(e)}), 500


# ========================================================================
# Job-Specific Status Endpoints
# ========================================================================

@scheduler_metrics_bp.route('/jobs/<job_id>/status', methods=['GET'])
def get_job_status(job_id):
    """
    Get status and metrics for a specific job.

    Args:
        job_id: APScheduler job ID

    Returns:
        Dict with job status, execution history, and metrics
    """
    try:
        status = tracking_service.get_job_status(job_id)

        if 'error' in status:
            return jsonify(status), 500

        return jsonify(status), 200

    except Exception as e:
        logger.error(f"Error retrieving status for job {job_id}: {e}")
        return jsonify({'error': str(e)}), 500


@scheduler_metrics_bp.route('/jobs/<job_id>/metrics', methods=['GET'])
def get_job_metrics(job_id):
    """
    Get detailed metrics for a specific job.

    Args:
        job_id: APScheduler job ID

    Returns:
        Dict with detailed execution metrics
    """
    try:
        metrics = execution_repo.get_job_metrics(job_id)

        if not metrics:
            return jsonify({'error': f'No metrics found for job {job_id}'}), 404

        return jsonify({
            'job_id': metrics.job_id,
            'job_name': metrics.job_name,
            'total_executions': metrics.total_executions,
            'successful_executions': metrics.successful_executions,
            'failed_executions': metrics.failed_executions,
            'skipped_executions': metrics.skipped_executions,
            'success_rate': round(metrics.success_rate, 2),
            'avg_duration_seconds': round(metrics.avg_duration_seconds, 2),
            'min_duration_seconds': round(metrics.min_duration_seconds, 2) if metrics.min_duration_seconds else None,
            'max_duration_seconds': round(metrics.max_duration_seconds, 2) if metrics.max_duration_seconds else None,
            'last_execution_status': metrics.last_execution_status,
            'last_execution_at': metrics.last_execution_at.isoformat() if metrics.last_execution_at else None,
            'last_error_message': metrics.last_error_message
        }), 200

    except Exception as e:
        logger.error(f"Error retrieving metrics for job {job_id}: {e}")
        return jsonify({'error': str(e)}), 500


# ========================================================================
# Job Execution History Endpoints
# ========================================================================

@scheduler_metrics_bp.route('/jobs/<job_id>/executions', methods=['GET'])
def get_job_executions(job_id):
    """
    Get execution history for a specific job.

    Query parameters:
        - limit: Maximum number of records to return (default: 100)
        - offset: Number of records to skip (default: 0)

    Args:
        job_id: APScheduler job ID

    Returns:
        List of JobExecution records
    """
    try:
        limit = request.args.get('limit', 100, type=int)
        offset = request.args.get('offset', 0, type=int)

        # Validate parameters
        limit = min(limit, 500)  # Cap at 500 records
        offset = max(offset, 0)

        executions = execution_repo.get_job_executions_by_id(job_id, limit=limit, offset=offset)

        return jsonify({
            'job_id': job_id,
            'count': len(executions),
            'limit': limit,
            'offset': offset,
            'executions': [
                {
                    'id': e.id,
                    'job_id': e.job_id,
                    'job_name': e.job_name,
                    'status': e.status,
                    'started_at': e.started_at.isoformat() if e.started_at else None,
                    'completed_at': e.completed_at.isoformat() if e.completed_at else None,
                    'duration_seconds': round(e.duration_seconds, 2) if e.duration_seconds else None,
                    'error_message': e.error_message,
                    'records_processed': e.records_processed,
                    'records_failed': e.records_failed,
                    'created_at': e.created_at.isoformat() if e.created_at else None
                }
                for e in executions
            ]
        }), 200

    except Exception as e:
        logger.error(f"Error retrieving executions for job {job_id}: {e}")
        return jsonify({'error': str(e)}), 500


@scheduler_metrics_bp.route('/jobs/<job_id>/executions/failed', methods=['GET'])
def get_job_failed_executions(job_id):
    """
    Get failed execution records for a specific job.

    Query parameters:
        - limit: Maximum number of records to return (default: 50)

    Args:
        job_id: APScheduler job ID

    Returns:
        List of failed JobExecution records
    """
    try:
        limit = request.args.get('limit', 50, type=int)
        limit = min(limit, 200)  # Cap at 200 records

        executions = execution_repo.get_failed_executions(job_id=job_id, limit=limit)

        return jsonify({
            'job_id': job_id,
            'count': len(executions),
            'executions': [
                {
                    'id': e.id,
                    'status': e.status,
                    'started_at': e.started_at.isoformat() if e.started_at else None,
                    'completed_at': e.completed_at.isoformat() if e.completed_at else None,
                    'duration_seconds': round(e.duration_seconds, 2) if e.duration_seconds else None,
                    'error_message': e.error_message,
                    'created_at': e.created_at.isoformat() if e.created_at else None
                }
                for e in executions
            ]
        }), 200

    except Exception as e:
        logger.error(f"Error retrieving failed executions for job {job_id}: {e}")
        return jsonify({'error': str(e)}), 500


@scheduler_metrics_bp.route('/jobs/<job_id>/executions/<execution_id>', methods=['GET'])
def get_job_execution(job_id, execution_id):
    """
    Get details of a specific job execution.

    Args:
        job_id: APScheduler job ID
        execution_id: Execution record UUID

    Returns:
        JobExecution details
    """
    try:
        execution = execution_repo.get_job_execution(execution_id)

        if not execution:
            return jsonify({'error': f'Execution {execution_id} not found'}), 404

        # Verify it belongs to the requested job
        if execution.job_id != job_id:
            return jsonify({'error': f'Execution does not belong to job {job_id}'}), 400

        return jsonify({
            'id': execution.id,
            'job_id': execution.job_id,
            'job_name': execution.job_name,
            'status': execution.status,
            'started_at': execution.started_at.isoformat() if execution.started_at else None,
            'completed_at': execution.completed_at.isoformat() if execution.completed_at else None,
            'duration_seconds': round(execution.duration_seconds, 2) if execution.duration_seconds else None,
            'error_message': execution.error_message,
            'error_traceback': execution.error_traceback,
            'records_processed': execution.records_processed,
            'records_failed': execution.records_failed,
            'metadata': execution.metadata,
            'created_at': execution.created_at.isoformat() if execution.created_at else None
        }), 200

    except Exception as e:
        logger.error(f"Error retrieving execution {execution_id}: {e}")
        return jsonify({'error': str(e)}), 500


@scheduler_metrics_bp.route('/jobs/<job_id>/executions/statistics', methods=['GET'])
def get_execution_statistics(job_id):
    """
    Get execution statistics for a job over a time period.

    Query parameters:
        - hours: Number of hours to look back (default: 24, max: 720)

    Args:
        job_id: APScheduler job ID

    Returns:
        Dict with execution statistics
    """
    try:
        hours = request.args.get('hours', 24, type=int)
        hours = min(max(hours, 1), 720)  # Between 1 and 720 hours (30 days)

        stats = execution_repo.get_execution_statistics(job_id, hours=hours)

        if not stats:
            return jsonify({'error': f'No statistics available for job {job_id}'}), 404

        return jsonify(stats), 200

    except Exception as e:
        logger.error(f"Error retrieving statistics for job {job_id}: {e}")
        return jsonify({'error': str(e)}), 500


# ========================================================================
# Failure Alert Endpoints
# ========================================================================

@scheduler_metrics_bp.route('/alerts', methods=['GET'])
def get_active_alerts():
    """
    Get all active (unacknowledged) failure alerts.

    Query parameters:
        - job_id: Filter by specific job ID (optional)

    Returns:
        List of active FailedJobAlert records
    """
    try:
        job_id = request.args.get('job_id', None)

        alerts = execution_repo.get_active_alerts(job_id=job_id)

        return jsonify({
            'count': len(alerts),
            'alerts': [
                {
                    'id': a.id,
                    'job_id': a.job_id,
                    'job_name': a.job_name,
                    'error_message': a.error_message,
                    'failure_timestamp': a.failure_timestamp.isoformat() if a.failure_timestamp else None,
                    'consecutive_failures': a.consecutive_failures,
                    'last_successful_execution': a.last_successful_execution.isoformat() if a.last_successful_execution else None,
                    'recommendation': a.recommendation,
                    'acknowledged': a.acknowledged,
                    'created_at': a.created_at.isoformat() if a.created_at else None
                }
                for a in alerts
            ]
        }), 200

    except Exception as e:
        logger.error(f"Error retrieving active alerts: {e}")
        return jsonify({'error': str(e)}), 500


@scheduler_metrics_bp.route('/alerts/<alert_id>', methods=['GET'])
def get_alert(alert_id):
    """
    Get details of a specific failure alert.

    Args:
        alert_id: Alert record UUID

    Returns:
        FailedJobAlert details
    """
    try:
        # Note: We'd need to implement a get_alert method in the repository
        # For now, we'll get it from the active alerts list
        alerts = execution_repo.get_active_alerts()
        alert = next((a for a in alerts if a.id == alert_id), None)

        if not alert:
            return jsonify({'error': f'Alert {alert_id} not found'}), 404

        return jsonify({
            'id': alert.id,
            'job_id': alert.job_id,
            'job_name': alert.job_name,
            'error_message': alert.error_message,
            'failure_timestamp': alert.failure_timestamp.isoformat() if alert.failure_timestamp else None,
            'consecutive_failures': alert.consecutive_failures,
            'last_successful_execution': alert.last_successful_execution.isoformat() if alert.last_successful_execution else None,
            'recommendation': alert.recommendation,
            'acknowledged': alert.acknowledged,
            'created_at': alert.created_at.isoformat() if alert.created_at else None
        }), 200

    except Exception as e:
        logger.error(f"Error retrieving alert {alert_id}: {e}")
        return jsonify({'error': str(e)}), 500


@scheduler_metrics_bp.route('/alerts/<alert_id>/acknowledge', methods=['POST'])
def acknowledge_alert(alert_id):
    """
    Mark a failure alert as acknowledged.

    Args:
        alert_id: Alert record UUID

    Returns:
        Success confirmation or error message
    """
    try:
        success = execution_repo.acknowledge_alert(alert_id)

        if success:
            return jsonify({
                'message': f'Alert {alert_id} acknowledged',
                'alert_id': alert_id,
                'acknowledged': True
            }), 200
        else:
            return jsonify({'error': f'Failed to acknowledge alert {alert_id}'}), 500

    except Exception as e:
        logger.error(f"Error acknowledging alert {alert_id}: {e}")
        return jsonify({'error': str(e)}), 500


# ========================================================================
# Recent Activity Endpoints
# ========================================================================

@scheduler_metrics_bp.route('/activity/recent', methods=['GET'])
def get_recent_activity():
    """
    Get recent job execution activity (last N hours).

    Query parameters:
        - hours: Number of hours to look back (default: 24, max: 168)

    Returns:
        List of recent JobExecution records
    """
    try:
        hours = request.args.get('hours', 24, type=int)
        hours = min(max(hours, 1), 168)  # Between 1 and 168 hours (1 week)

        executions = execution_repo.get_recent_executions(hours=hours, limit=200)

        return jsonify({
            'hours': hours,
            'count': len(executions),
            'executions': [
                {
                    'id': e.id,
                    'job_id': e.job_id,
                    'job_name': e.job_name,
                    'status': e.status,
                    'started_at': e.started_at.isoformat() if e.started_at else None,
                    'duration_seconds': round(e.duration_seconds, 2) if e.duration_seconds else None,
                    'error_message': e.error_message,
                    'created_at': e.created_at.isoformat() if e.created_at else None
                }
                for e in executions
            ]
        }), 200

    except Exception as e:
        logger.error(f"Error retrieving recent activity: {e}")
        return jsonify({'error': str(e)}), 500


@scheduler_metrics_bp.route('/health', methods=['GET'])
def scheduler_health_check():
    """
    Quick health check for scheduler.

    Returns:
        Health status of all jobs
    """
    try:
        statuses = tracking_service.get_all_job_statuses()

        # Calculate overall health
        jobs = statuses.get('jobs', {})
        total_jobs = len(jobs)
        healthy_jobs = sum(1 for j in jobs.values() if j.get('status') == 'SUCCESS')
        critical_jobs = sum(1 for j in jobs.values() if j.get('active_alerts', 0) > 0)

        health_status = 'HEALTHY' if critical_jobs == 0 else 'WARNING' if critical_jobs < total_jobs / 2 else 'CRITICAL'

        return jsonify({
            'status': health_status,
            'total_jobs': total_jobs,
            'healthy_jobs': healthy_jobs,
            'critical_jobs': critical_jobs,
            'timestamp': datetime.utcnow().isoformat()
        }), 200

    except Exception as e:
        logger.error(f"Error during health check: {e}")
        return jsonify({'error': str(e), 'status': 'UNKNOWN'}), 500


# Export blueprint
__all__ = ['scheduler_metrics_bp']
