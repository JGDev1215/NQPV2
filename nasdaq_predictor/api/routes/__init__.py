"""
API Routes - Modular route blueprints for different features.

This module organizes API endpoints into logical feature-based blueprints:
- market_routes: Market data and status endpoints
- prediction_routes: Prediction and analysis endpoints
- history_routes: Historical data and 24h history
- fibonacci_routes: Fibonacci pivot levels
- misc_routes: Health checks and other endpoints

All blueprints are registered together via create_api_blueprints().
"""

import logging
from flask import Blueprint, Flask

logger = logging.getLogger(__name__)


def create_api_blueprints(app: Flask) -> Blueprint:
    """Create and register all API route blueprints.

    Args:
        app: Flask application instance

    Returns:
        Blueprint: Main API blueprint with all sub-blueprints registered
    """
    # Create main API blueprint
    api_bp = Blueprint('api', __name__)

    logger.info("Creating API route blueprints...")

    try:
        # Import all route modules
        from .market_routes import market_bp
        from .prediction_routes import prediction_bp
        from .history_routes import history_bp
        from .fibonacci_routes import fibonacci_bp
        from .misc_routes import misc_bp
        from .scheduler_metrics_routes import scheduler_metrics_bp
        from .block_prediction_routes import block_prediction_api_bp, block_prediction_page_bp

        # Try to import market-aware routes
        try:
            from .market_aware_routes import market_aware_api_bp, market_status_api_bp
            market_aware_available = True
            logger.debug("✓ market_aware_routes imported successfully")
        except Exception as e:
            logger.warning(f"Could not import market_aware_routes: {e}")
            market_aware_available = False

        # Initialize market-aware services if available
        if market_aware_available:
            try:
                from ..services.market_status_service import MarketStatusService
                from ..services.block_prediction_service import BlockPredictionService

                # Initialize services (will be available in app context for routes)
                market_status_service = MarketStatusService()
                app.market_status_service = market_status_service
                logger.debug("✓ Initialized MarketStatusService")

                # Try to get BlockPredictionService from container
                if hasattr(app, 'container') and app.container:
                    try:
                        app.block_prediction_service = app.container.block_prediction_service()
                        logger.debug("✓ Initialized BlockPredictionService from container")
                    except Exception as e:
                        logger.debug(f"Container BlockPredictionService not available: {e}, routes will create as needed")
                else:
                    logger.debug("App container not yet available, BlockPredictionService will be created by routes")

            except Exception as e:
                logger.warning(f"Could not initialize market-aware services: {e}")

        # Register all sub-blueprints
        api_bp.register_blueprint(market_bp)
        logger.debug("✓ Registered market_bp")

        api_bp.register_blueprint(prediction_bp)
        logger.debug("✓ Registered prediction_bp")

        api_bp.register_blueprint(history_bp)
        logger.debug("✓ Registered history_bp")

        api_bp.register_blueprint(fibonacci_bp)
        logger.debug("✓ Registered fibonacci_bp")

        api_bp.register_blueprint(misc_bp)
        logger.debug("✓ Registered misc_bp")

        api_bp.register_blueprint(scheduler_metrics_bp)
        logger.debug("✓ Registered scheduler_metrics_bp")

        api_bp.register_blueprint(block_prediction_api_bp)
        logger.debug("✓ Registered block_prediction_api_bp")

        api_bp.register_blueprint(block_prediction_page_bp)
        logger.debug("✓ Registered block_prediction_page_bp")

        # Register market-aware blueprints if available
        if market_aware_available:
            api_bp.register_blueprint(market_aware_api_bp)
            logger.debug("✓ Registered market_aware_api_bp")

            api_bp.register_blueprint(market_status_api_bp)
            logger.debug("✓ Registered market_status_api_bp")

            blueprint_count = 10
        else:
            blueprint_count = 8

        logger.info(f"Successfully created API blueprints with {blueprint_count} sub-blueprints")

        return api_bp

    except Exception as e:
        logger.error(f"Failed to create API blueprints: {str(e)}", exc_info=True)
        raise


__all__ = ['create_api_blueprints']
