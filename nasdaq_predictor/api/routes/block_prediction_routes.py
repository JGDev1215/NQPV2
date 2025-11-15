"""
Block Prediction API Routes for 7-Block Framework.

REST API endpoints for accessing, generating, and verifying block predictions.

Endpoints:
- GET /api/block-predictions/<ticker> - 24-hour predictions
- GET /api/block-predictions/<ticker>/<hour> - Single hour prediction
- POST /api/block-predictions/generate - Manual generation trigger
- GET /api/block-predictions/<ticker>/accuracy - Accuracy metrics
- GET /api/block-predictions/<ticker>/summary - 24-hour summary
"""

import logging
from datetime import datetime
from flask import Blueprint, request, current_app, render_template
from urllib.parse import unquote
import pytz

from ...database.models.block_prediction import BlockPrediction
from ..handlers.response_handler import ResponseHandler
from ..handlers.error_handler import ErrorHandler
from ...services.market_status_service import MarketStatusService

# Initialize market status service
_market_status_service = None

def get_market_status_service():
    """Get or initialize MarketStatusService instance."""
    global _market_status_service
    if _market_status_service is None:
        _market_status_service = MarketStatusService()
    return _market_status_service

logger = logging.getLogger(__name__)

# Create blueprint for API routes
block_prediction_api_bp = Blueprint(
    'block_predictions_api',
    __name__,
    url_prefix='/api/block-predictions'
)

# Create blueprint for page routes
block_prediction_page_bp = Blueprint(
    'block_predictions_page',
    __name__,
    url_prefix=''
)


@block_prediction_page_bp.route('/block-predictions')
def block_predictions_page():
    """Render the 7-block predictions page."""
    try:
        return render_template('block_predictions.html')
    except Exception as e:
        logger.error(f"Error rendering block predictions page: {str(e)}")
        return ErrorHandler.server_error('Failed to load block predictions page')


@block_prediction_api_bp.route('/<ticker>', methods=['GET'])
def get_24h_predictions(ticker):
    """
    Get 24-hour block predictions for a ticker.

    Args:
        ticker: Asset ticker symbol (URL parameter)
        date: Trading date (query parameter, optional, defaults to today)

    Returns:
        JSON with list of 24 BlockPrediction objects
    """
    try:
        # URL decode ticker (handles special characters like ^FTSE, ES=F)
        ticker = unquote(ticker)

        # Get date from query params
        date_str = request.args.get('date')
        if date_str:
            try:
                date = datetime.fromisoformat(date_str)
            except ValueError:
                return ResponseHandler.error(
                    error_message=f"Invalid date format: {date_str}. Use ISO format: YYYY-MM-DD",
                    status_code=400
                )
        else:
            date = datetime.utcnow()

        # Get service from DI container
        service = current_app.container.resolve('block_prediction_service')

        # Fetch predictions
        predictions = service.get_hourly_predictions_24h(ticker, date)

        if not predictions:
            # Include market status context when no predictions found
            response_data = {
                'ticker': ticker,
                'date': date.date().isoformat(),
                'predictions': []
            }

            try:
                market_status_service = get_market_status_service()
                market_status = market_status_service.get_market_status(ticker, date)
                response_data['market_context'] = {
                    'market_status': market_status.status.value,
                    'is_trading': market_status.is_trading,
                    'timezone': market_status.timezone,
                    'last_trading_date': market_status.last_trading_date.isoformat(),
                    'note': 'Predictions may be unavailable if market is closed or no data available'
                }
            except Exception as e:
                logger.debug(f"Could not get market context for {ticker}: {str(e)}")

            return ResponseHandler.success(
                data=response_data,
                message=f"No predictions found for {ticker} on {date.date()}"
            )

        # Convert to dictionaries
        pred_data = [p.to_dict() for p in predictions]

        return ResponseHandler.success(
            data={
                'ticker': ticker,
                'date': date.date().isoformat(),
                'predictions': pred_data,
                'count': len(pred_data)
            },
            message=f"Retrieved {len(pred_data)} predictions for {ticker}"
        )

    except Exception as e:
        logger.error(f"Error retrieving 24h predictions: {e}", exc_info=True)
        return ResponseHandler.error(error_message=f"Error: {str(e)}", status_code=500)


@block_prediction_api_bp.route('/<ticker>/<int:hour>', methods=['GET'])
def get_hourly_prediction(ticker, hour):
    """
    Get prediction for a specific hour.

    Args:
        ticker: Asset ticker symbol (URL parameter)
        hour: Hour of day 0-23 (URL parameter)
        date: Trading date (query parameter, optional)

    Returns:
        JSON with single BlockPrediction object
    """
    try:
        # Validate hour
        if not 0 <= hour <= 23:
            return ResponseHandler.error(
                error_message=f"Hour must be 0-23, got {hour}"
            , status_code=400
            )

        # URL decode ticker
        ticker = unquote(ticker)

        # Get date from query params
        date_str = request.args.get('date')
        if date_str:
            try:
                date = datetime.fromisoformat(date_str)
            except ValueError:
                return ResponseHandler.error(
                    message=f"Invalid date format: {date_str}"
                , status_code=400
            )
        else:
            date = datetime.utcnow()

        # Create hour start timestamp
        hour_start = date.replace(hour=hour, minute=0, second=0, microsecond=0)

        # Get service from DI container
        service = current_app.container.resolve('block_prediction_service')

        # Fetch prediction
        prediction = service.get_hourly_prediction(ticker, hour_start)

        if not prediction:
            # Include market status context when prediction not found
            error_data = {
                'ticker': ticker,
                'hour': hour,
                'error': f"No prediction found for {ticker} at hour {hour}"
            }

            try:
                market_status_service = get_market_status_service()
                market_status = market_status_service.get_market_status(ticker, date)
                error_data['market_context'] = {
                    'market_status': market_status.status.value,
                    'is_trading': market_status.is_trading,
                    'timezone': market_status.timezone,
                    'last_trading_date': market_status.last_trading_date.isoformat(),
                    'note': 'Prediction unavailable if market is closed or no data available'
                }
            except Exception as e:
                logger.debug(f"Could not get market context for {ticker}: {str(e)}")

            return ResponseHandler.error(
                error_message=f"No prediction found for {ticker} at hour {hour}",
                data=error_data,
                status_code=404
            )

        return ResponseHandler.success(
            data=prediction.to_dict(),
            message=f"Retrieved prediction for {ticker} hour {hour}"
        )

    except Exception as e:
        logger.error(f"Error retrieving hourly prediction: {e}", exc_info=True)
        return ResponseHandler.error(error_message=f"Error: {str(e)}", status_code=500)


@block_prediction_api_bp.route('/generate', methods=['POST'])
def generate_predictions():
    """
    Manually trigger prediction generation for specified tickers.

    Request body:
    {
        "tickers": ["NQ=F", "ES=F"],
        "date": "2024-11-13" (optional, defaults to today)
    }

    Returns:
        JSON with generation results and statistics
    """
    try:
        # Parse request body
        data = request.get_json()
        if not data:
            return ResponseHandler.error(
                error_message="Request body required with 'tickers' list"
            , status_code=400
            )

        tickers = data.get('tickers', [])
        if not isinstance(tickers, list) or not tickers:
            return ResponseHandler.error(
                error_message="'tickers' must be a non-empty list"
            , status_code=400
            )

        # Get date from body
        date_str = data.get('date')
        if date_str:
            try:
                date = datetime.fromisoformat(date_str)
            except ValueError:
                return ResponseHandler.error(
                    message=f"Invalid date format: {date_str}"
                , status_code=400
            )
        else:
            date = datetime.utcnow()

        # Get service from DI container
        service = current_app.container.resolve('block_prediction_service')

        # Generate predictions for each ticker
        results = {
            'tickers': tickers,
            'date': date.date().isoformat(),
            'generations': {}
        }

        total_generated = 0
        total_failed = 0

        for ticker in tickers:
            try:
                ticker = unquote(ticker)
                generation_result = service.generate_24h_block_predictions(ticker, date)

                # generation_result is now a dict with detailed breakdown
                pred_count = generation_result.get('total_generated', 0)

                ticker_result = {
                    'status': 'success',
                    'total_generated': pred_count,
                    'generated_hours': generation_result.get('generated', []),
                    'skipped_future': generation_result.get('skipped_future', []),
                    'skipped_no_data': generation_result.get('skipped_no_data', []),
                    'predictions': [p.to_dict() for p in generation_result.get('predictions', [])]
                }
                total_generated += pred_count

                # Log warning if no predictions generated and include market context
                if pred_count == 0:
                    try:
                        market_status_service = get_market_status_service()
                        market_status = market_status_service.get_market_status(ticker, date)

                        ticker_result['context'] = {
                            'reason': 'no_predictions_generated',
                            'market_status': market_status.status.value,
                            'is_trading': market_status.is_trading,
                            'timezone': market_status.timezone,
                            'last_trading_date': market_status.last_trading_date.isoformat(),
                            'next_market_event': None
                        }

                        if market_status.is_trading:
                            ticker_result['context']['next_market_event'] = {
                                'event': 'CLOSE',
                                'time': market_status.next_close.isoformat() if market_status.next_close else None
                            }
                        else:
                            ticker_result['context']['next_market_event'] = {
                                'event': 'OPEN',
                                'time': market_status.next_open.isoformat() if market_status.next_open else None
                            }

                        logger.warning(
                            f"No predictions generated for {ticker}: "
                            f"market_status={market_status.status.value}, "
                            f"is_trading={market_status.is_trading}, "
                            f"future={len(generation_result.get('skipped_future', []))}, "
                            f"no_data={len(generation_result.get('skipped_no_data', []))}"
                        )
                    except Exception as e:
                        logger.warning(
                            f"No predictions generated for {ticker}: "
                            f"future={len(generation_result.get('skipped_future', []))}, "
                            f"no_data={len(generation_result.get('skipped_no_data', []))} "
                            f"(could not get market status: {str(e)})"
                        )

                results['generations'][ticker] = ticker_result

            except Exception as e:
                logger.error(f"Error generating predictions for {ticker}: {e}", exc_info=True)
                results['generations'][ticker] = {
                    'status': 'failed',
                    'error': str(e),
                    'error_type': type(e).__name__
                }
                total_failed += 1

        results['summary'] = {
            'total_generated': total_generated,
            'total_failed': total_failed
        }

        return ResponseHandler.success(
            data=results,
            message=f"Generated {total_generated} predictions ({total_failed} failed)"
        )

    except Exception as e:
        logger.error(f"Error in generate_predictions: {e}", exc_info=True)
        return ResponseHandler.error(error_message=f"Error: {str(e)}", status_code=500)


@block_prediction_api_bp.route('/<ticker>/accuracy', methods=['GET'])
def get_accuracy(ticker):
    """
    Get accuracy metrics for a ticker.

    Args:
        ticker: Asset ticker symbol (URL parameter)
        date: Trading date (query parameter, optional)

    Returns:
        JSON with accuracy statistics
    """
    try:
        # URL decode ticker
        ticker = unquote(ticker)

        # Get date from query params
        date_str = request.args.get('date')
        if date_str:
            try:
                date = datetime.fromisoformat(date_str).date()
            except ValueError:
                return ResponseHandler.error(
                    message=f"Invalid date format: {date_str}"
                , status_code=400
            )
        else:
            date = datetime.utcnow().date()

        # Get service from DI container
        service = current_app.container.resolve('block_verification_service')

        # Get accuracy metrics
        metrics = service.get_verification_accuracy(ticker, date)

        return ResponseHandler.success(
            data=metrics,
            message=f"Retrieved accuracy metrics for {ticker}"
        )

    except Exception as e:
        logger.error(f"Error retrieving accuracy: {e}", exc_info=True)
        return ResponseHandler.error(error_message=f"Error: {str(e)}", status_code=500)


@block_prediction_api_bp.route('/<ticker>/summary', methods=['GET'])
def get_24h_summary(ticker):
    """
    Get 24-hour summary with hourly breakdown and verification status.

    Args:
        ticker: Asset ticker symbol (URL parameter)
        date: Trading date (query parameter, optional)

    Returns:
        JSON with hourly grid showing predictions vs actuals
    """
    try:
        # URL decode ticker
        ticker = unquote(ticker)

        # Get date from query params
        date_str = request.args.get('date')
        if date_str:
            try:
                date = datetime.fromisoformat(date_str).date()
            except ValueError:
                return ResponseHandler.error(
                    message=f"Invalid date format: {date_str}"
                , status_code=400
            )
        else:
            date = datetime.utcnow().date()

        # Get service from DI container
        service = current_app.container.resolve('block_verification_service')

        # Get 24h summary
        summary = service.get_24h_verification_summary(ticker, date)

        return ResponseHandler.success(
            data=summary,
            message=f"Retrieved 24h summary for {ticker}"
        )

    except Exception as e:
        logger.error(f"Error retrieving 24h summary: {e}", exc_info=True)
        return ResponseHandler.error(error_message=f"Error: {str(e)}", status_code=500)


@block_prediction_api_bp.errorhandler(404)
def not_found(error):
    """Handle 404 errors for this blueprint."""
    return ResponseHandler.error(message="Block prediction endpoint not found"), 404


@block_prediction_api_bp.errorhandler(500)
def server_error(error):
    """Handle 500 errors for this blueprint."""
    return ResponseHandler.error(message="Internal server error"), 500


__all__ = ['block_prediction_api_bp', 'block_prediction_page_bp']
