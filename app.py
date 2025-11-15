"""
NASDAQ Predictor - Main Flask Application (Modular Version with Scheduler)
"""
import os
import sys
import atexit
import logging
from datetime import datetime
from flask import Flask, jsonify, redirect
from dotenv import load_dotenv

from nasdaq_predictor.api.routes import create_api_blueprints
from nasdaq_predictor.api.swagger import initialize_swagger
from nasdaq_predictor.container import create_container
from nasdaq_predictor.scheduler import start_scheduler, stop_scheduler, get_scheduler_status, get_next_data_update
from nasdaq_predictor.config.scheduler_config import SchedulerConfig
from nasdaq_predictor.config.settings import AUTO_REFRESH_BUFFER_SECONDS

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Load environment variables
load_dotenv()

# Create Flask app
app = Flask(__name__)

# Global flag to track scheduler initialization
scheduler_initialized = False


def initialize_application():
    """Initialize the application."""
    global scheduler_initialized

    if scheduler_initialized:
        logger.info("Application already initialized")
        return

    logger.info("=" * 80)
    logger.info("INITIALIZING NQP APPLICATION")
    logger.info("=" * 80)

    # Initialize background scheduler
    if SchedulerConfig.ENABLED:
        try:
            logger.info("Starting background scheduler...")
            scheduler = start_scheduler()

            if scheduler:
                logger.info("✓ Background scheduler started successfully")
                logger.info(f"  - Market Data Sync: Cron-based at minutes {SchedulerConfig.DATA_SYNC_OFFSET_MINUTES},17,32,47")
                logger.info(f"  - Prediction Calc: Cron-based at minutes {SchedulerConfig.PREDICTION_OFFSET_MINUTES},20,35,50")
                logger.info(f"  - Prediction Verif: Cron-based at minutes {SchedulerConfig.VERIFICATION_OFFSET_MINUTES},22,37,52")
                logger.info(f"  - Data Cleanup: Daily at {SchedulerConfig.CLEANUP_HOUR}:00")

                # Log next run times
                status = get_scheduler_status()
                if status.get('jobs'):
                    logger.info("  - Scheduled jobs:")
                    for job in status['jobs']:
                        logger.info(f"    • {job['name']}: Next run at {job['next_run']}")
            else:
                logger.warning("⚠ Scheduler is disabled in configuration")

        except Exception as e:
            logger.error(f"✗ Failed to start scheduler: {e}")
            logger.error("Application will continue without scheduler")
            # Log full traceback for debugging
            import traceback
            logger.error(traceback.format_exc())
    else:
        logger.info("⚠ Background scheduler is disabled (SCHEDULER_ENABLED=false)")

    scheduler_initialized = True
    logger.info("=" * 80)
    logger.info("NQP APPLICATION READY")
    logger.info("=" * 80)


# Initialize application immediately (Flask 3.x compatible)
with app.app_context():
    # Set Flask app instance for scheduler jobs (must be done before scheduler initialization)
    from nasdaq_predictor.scheduler.jobs import set_flask_app
    set_flask_app(app)

    initialize_application()


# Register shutdown handler
def shutdown_handler():
    """Gracefully shutdown the application."""
    logger.info("=" * 80)
    logger.info("SHUTTING DOWN NQP APPLICATION")
    logger.info("=" * 80)

    try:
        stop_scheduler()
        logger.info("✓ Scheduler stopped successfully")
    except Exception as e:
        logger.error(f"✗ Error stopping scheduler: {e}")

    logger.info("=" * 80)
    logger.info("NQP APPLICATION STOPPED")
    logger.info("=" * 80)

atexit.register(shutdown_handler)


# Initialize DI Container (Phase 2 Services)
try:
    logger.info("Initializing Dependency Injection Container...")
    app.container = create_container()
    logger.info("✓ DI Container initialized successfully with all Phase 2 services")

    # Detect circular dependencies (Phase 1.1)
    try:
        app.container.detect_circular_dependencies()
        logger.info("✓ Circular dependency detection passed - no circular dependencies found")
    except RuntimeError as e:
        logger.error(f"✗ Circular dependency detected: {e}")
        raise

except Exception as e:
    logger.error(f"✗ Failed to initialize DI Container: {e}")
    logger.error("Application will continue but services will not be available")
    import traceback
    logger.error(traceback.format_exc())
    app.container = None

# Create and register API blueprints
api_bp = create_api_blueprints(app)
app.register_blueprint(api_bp)

# Initialize Swagger/OpenAPI documentation
initialize_swagger(app)


# Scheduler status endpoint
@app.route('/api/scheduler/status')
def scheduler_status():
    """
    Get scheduler status and job information.

    Returns:
        JSON response with scheduler status, running jobs, and next execution times

    Example response:
        {
            "success": true,
            "scheduler": {
                "initialized": true,
                "running": true,
                "timezone": "UTC",
                "jobs": [
                    {
                        "id": "market_data_sync",
                        "name": "Market Data Sync",
                        "next_run": "2025-01-11T14:40:00+00:00",
                        "trigger": "interval[0:10:00]"
                    }
                ]
            }
        }
    """
    try:
        status = get_scheduler_status()
        return jsonify({
            'success': True,
            'scheduler': status,
            'timestamp': datetime.utcnow().isoformat()
        }), 200
    except Exception as e:
        logger.error(f"Error getting scheduler status: {e}")
        return jsonify({
            'success': False,
            'error': str(e),
            'scheduler': {
                'initialized': False,
                'running': False,
                'jobs': []
            },
            'timestamp': datetime.utcnow().isoformat()
        }), 500


# Next update time endpoint for intelligent frontend refresh
@app.route('/api/scheduler/next-update')
def next_update_time():
    """
    Get the next scheduled data update time for intelligent frontend refresh.

    Returns when frontend should refresh to get fresh data, accounting for
    scheduler job execution times and a buffer period.

    Returns:
        JSON response with next update timing information

    Example response:
        {
            "success": true,
            "next_update_time": "2025-11-11T22:48:00+00:00",
            "seconds_until_update": 245,
            "refresh_at": "2025-11-11T22:48:15+00:00",
            "seconds_until_refresh": 260,
            "job_type": "market_data",
            "job_name": "Market Data Sync"
        }
    """
    try:
        update_info = get_next_data_update()

        if 'error' in update_info:
            return jsonify({
                'success': False,
                'error': update_info['error'],
                'timestamp': datetime.utcnow().isoformat()
            }), 503

        # Calculate when frontend should actually refresh (job time + buffer)
        seconds_until_job = update_info['seconds_until_update']
        seconds_until_refresh = seconds_until_job + AUTO_REFRESH_BUFFER_SECONDS

        # Calculate refresh timestamp
        from datetime import timedelta
        import pytz
        refresh_time = datetime.now(pytz.UTC) + timedelta(seconds=seconds_until_refresh)

        return jsonify({
            'success': True,
            'next_update_time': update_info['next_update_time'],
            'seconds_until_update': seconds_until_job,
            'refresh_at': refresh_time.isoformat(),
            'seconds_until_refresh': seconds_until_refresh,
            'job_type': update_info['job_type'],
            'job_name': update_info['job_name'],
            'timestamp': datetime.utcnow().isoformat()
        }), 200

    except Exception as e:
        logger.error(f"Error getting next update time: {e}")
        return jsonify({
            'success': False,
            'error': str(e),
            'timestamp': datetime.utcnow().isoformat()
        }), 500


# Enhanced health check endpoint
@app.route('/api/health')
def health_check():
    """
    Health check endpoint with scheduler status.

    Returns:
        JSON response with application health status and scheduler information
    """
    try:
        scheduler_status_data = get_scheduler_status()

        return jsonify({
            'status': 'healthy',
            'timestamp': datetime.utcnow().isoformat(),
            'application': {
                'name': 'NQP - NASDAQ Predictor',
                'version': '2.0.0',
                'environment': os.getenv('FLASK_ENV', 'production')
            },
            'scheduler': {
                'initialized': scheduler_status_data.get('initialized', False),
                'running': scheduler_status_data.get('running', False),
                'jobs_count': len(scheduler_status_data.get('jobs', [])),
                'enabled': SchedulerConfig.ENABLED
            }
        }), 200
    except Exception as e:
        logger.error(f"Health check error: {e}")
        return jsonify({
            'status': 'degraded',
            'error': str(e),
            'timestamp': datetime.utcnow().isoformat(),
            'application': {
                'name': 'NQP - NASDAQ Predictor',
                'version': '2.0.0',
                'environment': os.getenv('FLASK_ENV', 'production')
            }
        }), 200


# Root endpoint
@app.route('/')
def index():
    """
    Root endpoint - redirect to API or serve dashboard.
    """
    # Check if running in production or development
    if os.getenv('FLASK_ENV') == 'development':
        return jsonify({
            'message': 'NQP - NASDAQ Predictor API',
            'version': '2.0.0',
            'endpoints': {
                'dashboard': '/api',
                'market_data': '/api/data',
                'scheduler_status': '/api/scheduler/status',
                'health': '/api/health'
            }
        })
    else:
        # In production, redirect to dashboard
        return redirect('/api')


if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    debug = os.environ.get('FLASK_DEBUG', 'False').lower() == 'true'

    logger.info("=" * 80)
    logger.info(f"STARTING NQP APPLICATION")
    logger.info(f"Port: {port}")
    logger.info(f"Debug: {debug}")
    logger.info(f"Environment: {os.getenv('FLASK_ENV', 'production')}")
    logger.info(f"Scheduler Enabled: {SchedulerConfig.ENABLED}")
    logger.info("=" * 80)

    app.run(host='0.0.0.0', port=port, debug=debug)
