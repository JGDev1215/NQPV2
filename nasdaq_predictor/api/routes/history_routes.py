"""
History Routes

Endpoints for historical market data and analysis.

Routes:
  GET /history - History page (renders HTML)
  GET /api/history/<ticker> - Historical data for ticker
"""

import logging
from datetime import datetime, timedelta
from flask import Blueprint, render_template, request, current_app

from ..handlers.error_handler import ErrorHandler
from ..handlers.response_handler import ResponseHandler
from ...core import TickerValidator, IntervalValidator, ValidationException

logger = logging.getLogger(__name__)

history_bp = Blueprint('history', __name__, url_prefix='')


@history_bp.route('/history')
def history_page():
    """Render the 24-hour prediction history page."""
    try:
        return render_template('history.html')
    except Exception as e:
        logger.error(f"Error rendering history page: {str(e)}")
        return ErrorHandler.server_error('Failed to load history page')


@history_bp.route('/api/history/<ticker_symbol>', methods=['GET'])
def get_historical_data(ticker_symbol):
    """
    Get historical market data for a specific ticker.

    Supports date range queries and interval selection.

    Args:
        ticker_symbol: Ticker symbol
        query params:
          - days: Number of days of history (default: 5, max: 365)
          - interval: Data interval (1m, 5m, 1h, 1d, default: 1d)
          - limit: Max number of records (default: 100, max: 1000)

    Returns:
        JSON with paginated historical data
    """
    try:
        # Validate ticker input
        ticker = TickerValidator.validate_ticker(ticker_symbol)

        # Validate and get days parameter
        days = request.args.get('days', 5, type=int)
        if days < 1 or days > 365:
            days = 5

        # Validate interval parameter
        interval = request.args.get('interval', '1d', type=str)
        try:
            interval = IntervalValidator.validate_interval(interval)
        except ValidationException as e:
            return ErrorHandler.validation_error(str(e))

        # Validate and get limit parameter
        limit = request.args.get('limit', 100, type=int)
        if limit < 1 or limit > 1000:
            limit = 100

        # Get DI container and resolve data sync service
        container = current_app.container
        try:
            data_sync_service = container.resolve('data_sync_service')
            # Get historical data for ticker
            end_date = datetime.utcnow()
            start_date = end_date - timedelta(days=days)

            historical_data = data_sync_service.get_historical_data(
                ticker=ticker,
                start_date=start_date,
                end_date=end_date,
                interval=interval,
                limit=limit
            )
        except Exception as e:
            logger.warning(f"Data sync service error: {e}, using fallback")
            # Fallback if service not available
            historical_data = []

        if not historical_data:
            return ResponseHandler.success(
                data=[],
                message=f'No historical data available for {ticker}',
                meta={
                    'ticker': ticker,
                    'days': days,
                    'interval': interval,
                    'count': 0
                }
            )

        # Convert DTOs to dictionaries if needed
        data_list = [
            d.to_dict() if hasattr(d, 'to_dict') else d
            for d in historical_data
        ]

        return ResponseHandler.paginated(
            data=data_list,
            total=len(data_list),
            page=1,
            page_size=limit,
            message=f'Historical data retrieved for {ticker}',
            meta={
                'ticker': ticker,
                'days': days,
                'interval': interval,
                'count': len(data_list)
            }
        )

    except ValidationException as e:
        logger.warning(f"Validation error for ticker {ticker_symbol}: {str(e)}")
        return ErrorHandler.validation_error(str(e))
    except Exception as e:
        logger.error(f"Error getting historical data for {ticker_symbol}: {str(e)}")
        return ErrorHandler.handle_error(e)


__all__ = ['history_bp']
