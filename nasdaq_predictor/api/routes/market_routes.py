"""
Market Data Routes

Endpoints for retrieving current market data, prices, and market status.
Integrates with Phase 2 refactored services (CacheService, PredictionCalculationService, etc.)

Routes:
  GET /api/data - Get current predictions for all tickers
  GET /health - Health check
  GET /api/health - Health check (alias)
"""

import logging
from datetime import datetime
from flask import Blueprint, jsonify, current_app

from ..handlers.error_handler import ErrorHandler
from ..handlers.response_handler import ResponseHandler

logger = logging.getLogger(__name__)

# Create market blueprint
market_bp = Blueprint('market', __name__, url_prefix='')


@market_bp.route('/health', methods=['GET'])
@market_bp.route('/api/health', methods=['GET'])
def health_check():
    """
    Health check endpoint.

    Returns basic health status and application version.

    Returns:
        JSON with status, version, and timestamp
    """
    try:
        health_status = {
            'status': 'healthy',
            'version': '2.0.0-phase3',
            'timestamp': datetime.utcnow().isoformat(),
            'services': {
                'database': 'connected',
                'api': 'operational'
            }
        }
        return ResponseHandler.success(health_status, 'Health check passed')
    except Exception as e:
        logger.error(f"Health check failed: {str(e)}")
        return ErrorHandler.server_error('Health check failed')


@market_bp.route('/api/data', methods=['GET'])
def api_data():
    """
    Get current market data and predictions for all enabled tickers.

    Uses database-first approach:
    1. Tries to get cached prediction (< 15 min old)
    2. If cache miss, calculates fresh from yfinance
    3. Returns formatted response with all data

    Returns:
        JSON with market data for each ticker:
        {
            'success': true,
            'data': {
                'NQ=F': {...},
                'ES=F': {...},
                '^FTSE': {...}
            },
            'timestamp': ISO timestamp
        }

    Error Cases:
        - 500: If no data can be retrieved
    """
    try:
        # Get services from DI container
        try:
            container = current_app.container
            if container is None:
                raise AttributeError("Container is None")
        except (AttributeError, RuntimeError):
            logger.warning("DI container not available, using fallback")
            return ErrorHandler.server_error(
                'DI container not configured. Phase 2 services not available.'
            )

        # Get the MarketAnalysisService from Phase 2
        try:
            market_service = container.resolve('market_analysis_service')
            logger.debug("Using Phase 2 MarketAnalysisService")
        except Exception as e:
            logger.error(f"MarketAnalysisService not available: {e}", exc_info=True)
            return ErrorHandler.server_error('Failed to initialize market analysis service')

        # Get market data for all tickers
        all_data = market_service.get_market_data()

        if not all_data:
            logger.warning("No market data retrieved")
            return ErrorHandler.server_error('Failed to retrieve market data')

        # Build response with metadata
        meta = {
            'tickers_count': len(all_data),
            'timestamp': datetime.utcnow().isoformat()
        }

        return ResponseHandler.success(
            data=all_data,
            message='Market data retrieved successfully',
            meta=meta
        )

    except Exception as e:
        logger.error(f"Error in api_data endpoint: {str(e)}", exc_info=True)
        return ErrorHandler.handle_error(e)


@market_bp.route('/api/market-summary', methods=['GET'])
def market_summary():
    """
    Get aggregated market summary across all tickers.

    Provides:
    - Bullish/bearish/neutral counts
    - Average confidence levels
    - Market consensus (bullish/bearish/mixed)
    - Success rates

    Returns:
        JSON with market-wide statistics

    Error Cases:
        - 500: If aggregation fails
    """
    try:
        container = current_app.container
        if container is None:
            raise AttributeError("Container is None")
        aggregation_service = container.resolve('aggregation_service')

        summary = aggregation_service.get_market_summary()

        if not summary or 'error' in summary:
            return ErrorHandler.server_error('Failed to generate market summary')

        return ResponseHandler.success(
            data=summary,
            message='Market summary generated'
        )

    except Exception as e:
        logger.error(f"Error generating market summary: {str(e)}", exc_info=True)
        return ErrorHandler.handle_error(e)


@market_bp.route('/api/refresh/<ticker>', methods=['POST'])
def force_refresh_ticker(ticker):
    """
    Force a fresh calculation from yfinance for a specific ticker.

    Bypasses the database cache and recalculates from live market data.

    Args:
        ticker: Ticker symbol (e.g., 'NQ=F')

    Returns:
        JSON with freshly calculated prediction

    Error Cases:
        - 400: Invalid ticker
        - 503: Data fetch failed
        - 500: Calculation error
    """
    try:
        # Validate ticker format
        if not ticker or not isinstance(ticker, str):
            return ErrorHandler.validation_error('Invalid ticker format')

        # Clean ticker input
        ticker = ticker.upper().strip()

        container = current_app.container
        market_service = container.resolve('market_analysis_service')

        result = market_service.force_refresh(ticker)

        if not result:
            return ErrorHandler.server_error(f'Failed to refresh data for {ticker}')

        return ResponseHandler.success(
            data=result,
            message=f'Fresh data calculated for {ticker}'
        )

    except Exception as e:
        logger.error(f"Error force refreshing {ticker}: {str(e)}", exc_info=True)
        return ErrorHandler.handle_error(e)
