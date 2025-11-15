"""
Market-Aware API Routes for Block Predictions.

REST API endpoints for market-aware predictions and market status.

Endpoints:
- GET /api/market-status/<ticker> - Current market status for a ticker
- GET /api/market-aware/<ticker> - Market-aware 24h predictions
- GET /api/market-aware/<ticker>/<hour> - Market-aware single hour prediction
- GET /api/market-open/<ticker> - Quick check if market is open
"""

import logging
from datetime import datetime
from flask import Blueprint, request, current_app
from urllib.parse import unquote
import pytz

from ...services.market_status_service import MarketStatusService
from ...services.block_prediction_service import BlockPredictionService
from ..handlers.response_handler import ResponseHandler
from ..handlers.error_handler import ErrorHandler

logger = logging.getLogger(__name__)

# Create blueprint for market-aware API routes
market_aware_api_bp = Blueprint(
    'market_aware_api',
    __name__,
    url_prefix='/api/market-aware'
)

# Create blueprint for market status routes
market_status_api_bp = Blueprint(
    'market_status_api',
    __name__,
    url_prefix='/api/market-status'
)


@market_status_api_bp.route('/<ticker>', methods=['GET'])
def get_market_status(ticker):
    """
    Get current market status for a ticker.

    Args:
        ticker: Asset ticker symbol (URL parameter)
        at_time: Time to check status (query parameter, optional, ISO format)

    Returns:
        JSON with MarketStatusInfo:
            {
                "status": "OPEN" | "CLOSED" | "PRE_MARKET" | "AFTER_HOURS",
                "is_trading": bool,
                "session_type": string,
                "timezone": string,
                "current_time": datetime ISO string,
                "next_open": datetime ISO string or null,
                "next_close": datetime ISO string or null,
                "last_trading_date": date ISO string
            }
    """
    try:
        # Decode ticker
        ticker = unquote(ticker).strip().upper()
        logger.debug(f"Getting market status for {ticker}")

        # Get optional at_time parameter
        at_time_str = request.args.get('at_time')
        at_time = None
        if at_time_str:
            try:
                at_time = datetime.fromisoformat(at_time_str.replace('Z', '+00:00'))
            except ValueError:
                return ErrorHandler.bad_request(f"Invalid at_time format: {at_time_str}")

        # Get market status service from app context
        market_status_service = current_app.market_status_service

        # Get market status
        status_info = market_status_service.get_market_status(ticker, at_time)

        # Convert to dictionary for JSON serialization
        result = {
            "ticker": ticker,
            "status": status_info.status.value,
            "is_trading": status_info.is_trading,
            "session_type": status_info.session_type.value,
            "timezone": status_info.timezone,
            "current_time": status_info.current_time.isoformat(),
            "next_open": status_info.next_open.isoformat() if status_info.next_open else None,
            "next_close": status_info.next_close.isoformat() if status_info.next_close else None,
            "last_trading_date": status_info.last_trading_date.isoformat()
        }

        return ResponseHandler.success(result, f"Market status for {ticker}")

    except ValueError as e:
        logger.warning(f"Invalid ticker: {str(e)}")
        return ErrorHandler.not_found(f"Ticker {ticker} not found or not supported")
    except Exception as e:
        logger.error(f"Error getting market status for {ticker}: {str(e)}", exc_info=True)
        return ErrorHandler.server_error(f"Failed to retrieve market status")


@market_status_api_bp.route('/<ticker>/is-open', methods=['GET'])
def is_market_open(ticker):
    """
    Quick check if market is currently open for a ticker.

    Args:
        ticker: Asset ticker symbol (URL parameter)

    Returns:
        JSON:
            {
                "ticker": string,
                "is_open": bool,
                "timestamp": datetime ISO string
            }
    """
    try:
        ticker = unquote(ticker).strip().upper()
        logger.debug(f"Checking if market is open for {ticker}")

        market_status_service = current_app.market_status_service
        is_open = market_status_service.is_market_open(ticker)

        result = {
            "ticker": ticker,
            "is_open": is_open,
            "timestamp": datetime.now(pytz.UTC).isoformat()
        }

        return ResponseHandler.success(result)

    except Exception as e:
        logger.error(f"Error checking market status for {ticker}: {str(e)}")
        return ErrorHandler.server_error(f"Failed to check market status")


@market_aware_api_bp.route('/<ticker>', methods=['GET'])
def get_market_aware_predictions_24h(ticker):
    """
    Get 24h block predictions with market status awareness.

    Returns LIVE predictions if market is open, HISTORICAL from last trading day if closed.

    Args:
        ticker: Asset ticker symbol (URL parameter)
        date: Optional date for predictions (query parameter, ISO format)

    Returns:
        JSON with market-aware predictions:
            {
                "data_source": "LIVE" | "HISTORICAL",
                "market_status": {
                    "status": string,
                    "is_trading": bool,
                    "timezone": string,
                    "current_time": datetime ISO string
                },
                "predictions_date": date ISO string,
                "predictions": List[BlockPrediction],
                "last_trading_date": date ISO string,
                "next_market_event": {
                    "type": "OPEN" | "CLOSE",
                    "time": datetime ISO string or null
                }
            }
    """
    try:
        ticker = unquote(ticker).strip().upper()
        logger.debug(f"Getting market-aware 24h predictions for {ticker}")

        # Get block prediction service from app context
        block_prediction_service = current_app.block_prediction_service

        # Get optional date/time parameter
        at_time = None
        date_str = request.args.get('date')
        if date_str:
            try:
                at_time = datetime.fromisoformat(date_str.replace('Z', '+00:00'))
            except ValueError:
                return ErrorHandler.bad_request(f"Invalid date format: {date_str}")

        # Get market-aware predictions
        result = block_prediction_service.get_market_aware_predictions_24h(ticker, at_time)

        if result.get("data_source") == "ERROR":
            return ErrorHandler.server_error(result.get("error"))

        # Convert prediction objects to dictionaries
        predictions_data = []
        for pred in result.get("predictions", []):
            if isinstance(pred, dict):
                predictions_data.append(pred)
            else:
                # Convert BlockPrediction object to dict if needed
                pred_dict = {
                    "ticker": getattr(pred, 'ticker', ticker),
                    "hour_start_timestamp": getattr(pred, 'hour_start_timestamp', '').isoformat() if hasattr(getattr(pred, 'hour_start_timestamp', None), 'isoformat') else str(getattr(pred, 'hour_start_timestamp', '')),
                    "block_predictions": getattr(pred, 'block_predictions', []),
                    "prediction_strength": getattr(pred, 'prediction_strength', 0.0)
                }
                predictions_data.append(pred_dict)

        result["predictions"] = predictions_data

        return ResponseHandler.success(result, f"Market-aware 24h predictions for {ticker}")

    except Exception as e:
        logger.error(f"Error getting market-aware predictions for {ticker}: {str(e)}", exc_info=True)
        return ErrorHandler.server_error(f"Failed to retrieve market-aware predictions")


@market_aware_api_bp.route('/<ticker>/<int:hour>', methods=['GET'])
def get_market_aware_prediction_hour(ticker, hour):
    """
    Get market-aware prediction for a specific hour.

    Args:
        ticker: Asset ticker symbol (URL parameter)
        hour: Hour (0-23) in the day (URL parameter)
        date: Optional date (query parameter, ISO format)

    Returns:
        JSON with market-aware prediction:
            {
                "data_source": "LIVE" | "HISTORICAL",
                "market_status": {...},
                "prediction": BlockPrediction or null,
                "prediction_date": date ISO string,
                "next_market_event": {...}
            }
    """
    try:
        ticker = unquote(ticker).strip().upper()

        if hour < 0 or hour > 23:
            return ErrorHandler.bad_request(f"Hour must be between 0 and 23, got {hour}")

        logger.debug(f"Getting market-aware prediction for {ticker} hour {hour}")

        # Get block prediction service
        block_prediction_service = current_app.block_prediction_service

        # Build datetime for the hour
        at_time = None
        date_str = request.args.get('date')
        if date_str:
            try:
                at_time = datetime.fromisoformat(date_str.replace('Z', '+00:00'))
                # Set to the specified hour
                at_time = at_time.replace(hour=hour, minute=0, second=0, microsecond=0)
            except ValueError:
                return ErrorHandler.bad_request(f"Invalid date format: {date_str}")
        else:
            # Use current time, set to specified hour
            at_time = datetime.now(pytz.UTC).replace(hour=hour, minute=0, second=0, microsecond=0)

        # Get market-aware prediction
        result = block_prediction_service.get_market_aware_prediction(ticker, at_time, at_time)

        if result is None:
            return ErrorHandler.server_error("Failed to retrieve market-aware prediction")

        # Convert prediction object to dict if needed
        if result.get("prediction") and not isinstance(result["prediction"], dict):
            pred = result["prediction"]
            pred_dict = {
                "ticker": getattr(pred, 'ticker', ticker),
                "hour_start_timestamp": getattr(pred, 'hour_start_timestamp', '').isoformat() if hasattr(getattr(pred, 'hour_start_timestamp', None), 'isoformat') else str(getattr(pred, 'hour_start_timestamp', '')),
                "block_predictions": getattr(pred, 'block_predictions', []),
                "prediction_strength": getattr(pred, 'prediction_strength', 0.0)
            }
            result["prediction"] = pred_dict

        return ResponseHandler.success(result, f"Market-aware prediction for {ticker} hour {hour}")

    except Exception as e:
        logger.error(f"Error getting market-aware prediction for {ticker} hour {hour}: {str(e)}", exc_info=True)
        return ErrorHandler.server_error(f"Failed to retrieve market-aware prediction")
