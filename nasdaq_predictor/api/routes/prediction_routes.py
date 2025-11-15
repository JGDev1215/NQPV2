"""
Prediction Routes

Endpoints for retrieving predictions, analysis, and signals for specific tickers.

Routes:
  GET /api/predictions/<ticker> - Current prediction for ticker
  GET /api/predictions/<ticker>/history-24h - 24-hour prediction history
"""

import logging
from datetime import datetime
from flask import Blueprint, request, current_app

from ..handlers.error_handler import ErrorHandler
from ..handlers.response_handler import ResponseHandler
from ...core import TickerValidator, ValidationException

logger = logging.getLogger(__name__)

prediction_bp = Blueprint('predictions', __name__, url_prefix='/api')


@prediction_bp.route('/predictions/<ticker_symbol>', methods=['GET'])
def get_prediction_history(ticker_symbol):
    """
    Get current prediction for a specific ticker.

    Args:
        ticker_symbol: Ticker symbol (e.g., 'NQ=F')

    Returns:
        JSON with current prediction and confidence
    """
    try:
        # Validate ticker input
        ticker = TickerValidator.validate_ticker(ticker_symbol)

        # Get DI container and resolve market analysis service
        container = current_app.container
        if container is None:
            raise AttributeError("Container is None")
        market_service = container.resolve('market_analysis_service')

        # Get current prediction for ticker
        prediction = market_service.process_ticker_data(ticker)

        if not prediction:
            return ErrorHandler.not_found_error(f'No prediction available for {ticker}')

        return ResponseHandler.success(
            data=prediction if isinstance(prediction, dict) else (prediction.to_dict() if hasattr(prediction, 'to_dict') else prediction),
            message=f'Current prediction retrieved for {ticker}',
            meta={
                'ticker': ticker,
                'timestamp': datetime.utcnow().isoformat()
            }
        )

    except ValidationException as e:
        logger.warning(f"Validation error for ticker {ticker_symbol}: {str(e)}")
        return ErrorHandler.validation_error(str(e))
    except Exception as e:
        logger.error(f"Error getting prediction for {ticker_symbol}: {str(e)}")
        return ErrorHandler.handle_error(e)


@prediction_bp.route('/predictions/<ticker_symbol>/history-24h', methods=['GET'])
def get_prediction_history_24h(ticker_symbol):
    """
    Get 24-hour prediction history for a specific ticker.

    Includes hourly intraday predictions and accuracy verification.

    Args:
        ticker_symbol: Ticker symbol (e.g., 'NQ=F')
        query params:
          - limit: Number of predictions to return (default: 24, max: 100)

    Returns:
        JSON with 24-hour prediction history and statistics
    """
    try:
        # Validate ticker input
        ticker = TickerValidator.validate_ticker(ticker_symbol)

        # Get optional limit parameter
        limit = request.args.get('limit', 24, type=int)
        if limit < 1 or limit > 100:
            limit = 24

        # Get DI container and resolve repositories
        container = current_app.container
        ticker_repo = container.resolve('ticker_repository')
        intraday_repo = container.resolve('intraday_prediction_repository')

        # Get ticker ID from symbol
        ticker_record = ticker_repo.get_ticker_by_symbol(ticker)
        if not ticker_record:
            logger.warning(f"Ticker not found in database: {ticker}")
            return ResponseHandler.success(
                data=[],
                message=f'No prediction history available for {ticker}',
                meta={
                    'ticker': ticker,
                    'count': 0,
                    'timestamp': datetime.utcnow().isoformat()
                }
            )

        ticker_id = ticker_record.id

        # Get 24-hour intraday predictions from repository
        intraday_predictions = intraday_repo.get_24h_intraday_predictions(ticker_id)

        if not intraday_predictions:
            return ResponseHandler.success(
                data=[],
                message=f'No 24-hour predictions available for {ticker}',
                meta={
                    'ticker': ticker,
                    'count': 0,
                    'timestamp': datetime.utcnow().isoformat()
                }
            )

        # Transform intraday predictions to match frontend expectations
        predictions_data = []
        for pred in intraday_predictions:
            pred_dict = pred.to_dict() if hasattr(pred, 'to_dict') else pred

            # Map final_confidence to confidence for frontend compatibility
            if 'final_confidence' in pred_dict:
                pred_dict['confidence'] = pred_dict['final_confidence']

            # Calculate actual_price_change if both reference and target prices exist
            if (pred_dict.get('reference_price') is not None and
                pred_dict.get('target_close_price') is not None):
                pred_dict['actual_price_change'] = (
                    pred_dict['target_close_price'] - pred_dict['reference_price']
                )

            predictions_data.append(pred_dict)

        # Sort by target_hour descending (most recent first)
        predictions_data.sort(key=lambda p: p.get('target_hour', 0), reverse=True)

        # Apply limit
        predictions_data = predictions_data[:limit]

        return ResponseHandler.success(
            data=predictions_data,
            message=f'24-hour prediction history retrieved for {ticker}',
            meta={
                'ticker': ticker,
                'count': len(predictions_data),
                'limit': limit
            }
        )

    except ValidationException as e:
        logger.warning(f"Validation error for ticker {ticker_symbol}: {str(e)}")
        return ErrorHandler.validation_error(str(e))
    except Exception as e:
        logger.error(f"Error getting 24h history for {ticker_symbol}: {str(e)}")
        return ErrorHandler.handle_error(e)


__all__ = ['prediction_bp']
