"""
Miscellaneous Routes

Endpoints for accuracy metrics, signal analysis, and other analysis endpoints.

Routes:
  GET /api/accuracy/<ticker> - Prediction accuracy metrics
  GET /api/signals/<ticker> - Signal analysis for ticker
  GET /api/prediction/<prediction_id>/signals - Signals for specific prediction
  GET / - Homepage (renders HTML)
"""

import logging
from datetime import datetime
from flask import Blueprint, render_template, request, current_app

from ..handlers.error_handler import ErrorHandler
from ..handlers.response_handler import ResponseHandler
from ...core import TickerValidator, ValidationException

logger = logging.getLogger(__name__)

misc_bp = Blueprint('misc', __name__, url_prefix='')


@misc_bp.route('/')
def index():
    """
    Render the main dashboard page.

    Returns:
        Rendered HTML dashboard
    """
    try:
        return render_template('index.html')
    except Exception as e:
        logger.error(f"Error rendering index page: {str(e)}")
        return ErrorHandler.server_error('Failed to load dashboard')


@misc_bp.route('/api/accuracy/<ticker_symbol>', methods=['GET'])
def get_prediction_accuracy(ticker_symbol):
    """
    Get prediction accuracy metrics for a ticker.

    Provides:
    - Overall accuracy percentage
    - Correct/wrong prediction counts
    - Accuracy by prediction type
    - Confidence vs actual result correlation

    Args:
        ticker_symbol: Ticker symbol (e.g., 'NQ=F')
        query params:
          - period_hours: Time period in hours (default: 24, max: 720)

    Returns:
        JSON with accuracy metrics
    """
    try:
        # Validate ticker input
        ticker = TickerValidator.validate_ticker(ticker_symbol)

        # Get optional period parameter
        period_hours = request.args.get('period_hours', 24, type=int)
        if period_hours < 1 or period_hours > 720:
            period_hours = 24

        # Get DI container and resolve accuracy service
        container = current_app.container
        try:
            accuracy_service = container.resolve('accuracy_service')
            accuracy_metrics = accuracy_service.calculate_accuracy(ticker, period_hours=period_hours)
        except Exception as e:
            logger.warning(f"Accuracy service error: {e}, using placeholder")
            # Placeholder response if service not available
            accuracy_metrics = None

        if not accuracy_metrics:
            # Return placeholder accuracy metrics
            accuracy_data = {
                'symbol': ticker,
                'period_hours': period_hours,
                'total_predictions': 0,
                'correct_predictions': 0,
                'accuracy_percentage': 0.0,
                'confidence_avg': 0.0,
                'timestamp': datetime.utcnow().isoformat()
            }
        else:
            accuracy_data = accuracy_metrics.to_dict() if hasattr(accuracy_metrics, 'to_dict') else accuracy_metrics

        return ResponseHandler.success(
            data=accuracy_data,
            message=f'Accuracy metrics retrieved for {ticker}',
            meta={
                'ticker': ticker,
                'period_hours': period_hours
            }
        )

    except ValidationException as e:
        logger.warning(f"Validation error for ticker {ticker_symbol}: {str(e)}")
        return ErrorHandler.validation_error(str(e))
    except Exception as e:
        logger.error(f"Error getting accuracy for {ticker_symbol}: {str(e)}")
        return ErrorHandler.handle_error(e)


@misc_bp.route('/api/signals/<ticker_symbol>', methods=['GET'])
def get_signal_analysis(ticker_symbol):
    """
    Get detailed signal analysis for a ticker.

    Provides:
    - Individual signal values
    - Signal weights
    - Weighted contributions to final prediction
    - Signal strength indicators

    Args:
        ticker_symbol: Ticker symbol

    Returns:
        JSON with signal analysis
    """
    try:
        # Validate ticker input
        ticker = TickerValidator.validate_ticker(ticker_symbol)

        # Get DI container and resolve market service
        container = current_app.container
        try:
            market_service = container.resolve('market_analysis_service')
            prediction = market_service.process_ticker_data(ticker)
        except Exception as e:
            logger.warning(f"Market service error: {e}, using placeholder")
            prediction = None

        if not prediction:
            # Return placeholder signal analysis
            signals_data = {
                'symbol': ticker,
                'signals': [],
                'total_weight': 0.0,
                'timestamp': datetime.utcnow().isoformat()
            }
        else:
            # Extract signals from prediction if available
            signals_dict = getattr(prediction, 'signals', {})
            if isinstance(signals_dict, dict) and not isinstance(signals_dict, dict):
                signals_list = []
            elif isinstance(signals_dict, dict):
                signals_list = [
                    {'name': k, 'value': v if isinstance(v, (int, float)) else 0.0}
                    for k, v in signals_dict.items()
                ]
            else:
                signals_list = []

            signals_data = {
                'symbol': ticker,
                'signals': signals_list,
                'total_weight': sum(s.get('value', 0) for s in signals_list),
                'timestamp': datetime.utcnow().isoformat()
            }

        return ResponseHandler.success(
            data=signals_data,
            message=f'Signal analysis retrieved for {ticker}',
            meta={
                'ticker': ticker,
                'signal_count': len(signals_data.get('signals', []))
            }
        )

    except ValidationException as e:
        logger.warning(f"Validation error for ticker {ticker_symbol}: {str(e)}")
        return ErrorHandler.validation_error(str(e))
    except Exception as e:
        logger.error(f"Error getting signal analysis for {ticker_symbol}: {str(e)}")
        return ErrorHandler.handle_error(e)


@misc_bp.route('/api/prediction/<prediction_id>/signals', methods=['GET'])
def get_prediction_signals(prediction_id):
    """
    Get signals for a specific prediction.

    Provides detailed breakdown of which signals contributed to a specific prediction.

    Args:
        prediction_id: Prediction UUID

    Returns:
        JSON with signal details for prediction
    """
    try:
        # Validate prediction_id format (basic UUID check)
        if not prediction_id or len(prediction_id.strip()) == 0:
            return ErrorHandler.validation_error('Prediction ID required')

        prediction_id = prediction_id.strip()

        # Try to retrieve signals for the specific prediction
        # This would normally query a database or cache service
        container = current_app.container
        try:
            # Try to resolve a prediction service or query service
            prediction_service = container.resolve('prediction_service')
            prediction_signals = prediction_service.get_prediction_signals(prediction_id)
        except Exception as e:
            logger.warning(f"Prediction service error: {e}, using placeholder")
            prediction_signals = None

        if not prediction_signals:
            # Return placeholder response if prediction not found
            signals_data = {
                'prediction_id': prediction_id,
                'signals': [],
                'timestamp': datetime.utcnow().isoformat()
            }
        else:
            signals_data = prediction_signals.to_dict() if hasattr(prediction_signals, 'to_dict') else prediction_signals

        return ResponseHandler.success(
            data=signals_data,
            message=f'Signals retrieved for prediction {prediction_id}',
            meta={
                'prediction_id': prediction_id
            }
        )

    except Exception as e:
        logger.error(f"Error getting signals for {prediction_id}: {str(e)}")
        return ErrorHandler.handle_error(e)


__all__ = ['misc_bp']
