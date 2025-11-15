"""
Decorator to standardize all API responses.

Wraps endpoint functions to ensure consistent response format across
all API endpoints, including error handling and formatting.

Usage:
    @app.route('/api/data')
    @standardize_response
    def get_data():
        return {'key': 'value'}  # Automatically wrapped in success response
"""

import logging
from functools import wraps
from flask import jsonify, Response
from typing import Tuple, Dict, Any, Union

from .response_models import (
    SuccessResponse, ErrorResponse, ErrorCode, ApiResponse, ApiMetadata
)

logger = logging.getLogger(__name__)


def standardize_response(f):
    """Decorator to standardize API response format.

    Automatically wraps endpoint return values in standardized response format.
    Handles both successful returns and exceptions.

    Args:
        f: Flask route function to decorate

    Returns:
        Decorated function that returns standardized responses

    Usage Examples:
        # Return dict data
        @app.route('/api/data')
        @standardize_response
        def get_data():
            return {'items': [1, 2, 3]}
        # Response: {'success': True, 'status': 'success', 'data': {'items': ...}, ...}

        # Return tuple with status code
        @app.route('/api/create', methods=['POST'])
        @standardize_response
        def create_item():
            return {'id': '123'}, 201
        # Response: {'success': True, ...} with HTTP 201

        # Return explicit response object
        @app.route('/api/items')
        @standardize_response
        def get_items():
            items = [...]
            return SuccessResponse(data={'items': items})
        # Response: Direct response from SuccessResponse

        # Raise exception for errors
        @app.route('/api/data/<id>')
        @standardize_response
        def get_data(id):
            if not id:
                raise ValueError('ID is required')
            return {'id': id}
        # Error Response: {'success': False, 'error': {'code': 'VALIDATION_ERROR', ...}}
    """
    @wraps(f)
    def decorated_function(*args, **kwargs) -> Response:
        """Wrapper that processes function return value and exceptions."""
        try:
            result = f(*args, **kwargs)

            # Handle different return types
            if isinstance(result, tuple):
                # Handle (data, status_code) tuple
                data, status_code = result if len(result) == 2 else (result[0], 200)
            else:
                data = result
                status_code = 200

            # If result is already a response object, return it directly
            if isinstance(data, ApiResponse):
                return jsonify(data.to_dict()), status_code
            elif isinstance(data, dict) and 'success' in data and 'status' in data:
                # Already formatted as response
                return jsonify(data), status_code

            # Wrap in success response
            response = SuccessResponse(
                data=data if isinstance(data, dict) else {'result': data}
            )
            return jsonify(response.to_dict()), status_code

        except ValueError as e:
            # Validation errors
            logger.warning(f"Validation error in {f.__name__}: {str(e)}")
            error_response = ErrorResponse(
                code=ErrorCode.VALIDATION_ERROR,
                message=str(e)
            )
            return jsonify(error_response.to_dict()), 400

        except KeyError as e:
            # Missing required keys/fields
            logger.warning(f"Missing field in {f.__name__}: {str(e)}")
            error_response = ErrorResponse(
                code=ErrorCode.BAD_REQUEST,
                message=f"Missing required field: {str(e)}"
            )
            return jsonify(error_response.to_dict()), 400

        except Exception as e:
            # Catch unexpected errors
            logger.error(f"Unexpected error in {f.__name__}: {str(e)}", exc_info=True)
            error_response = ErrorResponse(
                code=ErrorCode.INTERNAL_ERROR,
                message="An unexpected error occurred",
                details={'error_type': type(e).__name__}
            )
            return jsonify(error_response.to_dict()), 500

    return decorated_function


def error_handler(http_status: int = 500, error_code: ErrorCode = None):
    """Decorator for explicit error handling in endpoints.

    Allows routes to handle specific errors and return them in standardized format.

    Args:
        http_status: HTTP status code to return on error
        error_code: ErrorCode enum value for the error

    Usage:
        @app.route('/api/data/<id>')
        @error_handler(http_status=404, error_code=ErrorCode.NOT_FOUND)
        def get_data(id):
            item = db.get(id)
            if not item:
                raise ValueError(f'Item {id} not found')
            return {'item': item}
    """
    error_code = error_code or ErrorCode.INTERNAL_ERROR

    def decorator(f):
        @wraps(f)
        def wrapper(*args, **kwargs):
            try:
                return f(*args, **kwargs)
            except Exception as e:
                logger.error(f"Handled error in {f.__name__}: {str(e)}")
                error_response = ErrorResponse(
                    code=error_code,
                    message=str(e)
                )
                return jsonify(error_response.to_dict()), http_status

        return wrapper

    return decorator


def paginated_response(items_key: str = 'items'):
    """Decorator for paginated endpoint responses.

    Expects endpoint to return tuple of (items, total, limit, offset)
    or dict with those keys.

    Args:
        items_key: Key name for items in response data

    Usage:
        @app.route('/api/predictions')
        @paginated_response(items_key='predictions')
        def list_predictions():
            items = [...]
            return items, 100, 10, 0  # (items, total, limit, offset)
    """
    def decorator(f):
        @wraps(f)
        def wrapper(*args, **kwargs):
            from .response_models import PaginatedResponse

            try:
                result = f(*args, **kwargs)

                if isinstance(result, tuple) and len(result) == 4:
                    items, total, limit, offset = result
                elif isinstance(result, dict):
                    items = result.get('items', [])
                    total = result.get('total', len(items))
                    limit = result.get('limit', len(items))
                    offset = result.get('offset', 0)
                else:
                    raise ValueError("Expected tuple of (items, total, limit, offset) or dict")

                response = PaginatedResponse(
                    items=items,
                    total=total,
                    limit=limit,
                    offset=offset
                )
                return jsonify(response.to_dict()), 200

            except Exception as e:
                logger.error(f"Error in {f.__name__}: {str(e)}")
                error_response = ErrorResponse(
                    code=ErrorCode.INTERNAL_ERROR,
                    message="Error processing pagination"
                )
                return jsonify(error_response.to_dict()), 500

        return wrapper

    return decorator


class ResponseFormatter:
    """Utility class for formatting responses in handler functions.

    Provides static methods to format responses without using decorators.

    Usage:
        @app.route('/api/data')
        def get_data():
            try:
                data = fetch_data()
                return ResponseFormatter.success(data)
            except Exception as e:
                return ResponseFormatter.error(
                    code=ErrorCode.INTERNAL_ERROR,
                    message=str(e)
                )
    """

    @staticmethod
    def success(
        data: Dict[str, Any],
        http_status: int = 200,
        message: str = None
    ) -> Tuple[Response, int]:
        """Format success response.

        Args:
            data: Response data
            http_status: HTTP status code
            message: Optional message

        Returns:
            Tuple of (JSON response, HTTP status code)
        """
        response = SuccessResponse(data=data, message=message)
        return jsonify(response.to_dict()), http_status

    @staticmethod
    def error(
        code: Union[ErrorCode, str] = ErrorCode.INTERNAL_ERROR,
        message: str = 'An error occurred',
        details: Dict = None,
        http_status: int = 400
    ) -> Tuple[Response, int]:
        """Format error response.

        Args:
            code: ErrorCode enum or string
            message: Error message
            details: Optional error details
            http_status: HTTP status code

        Returns:
            Tuple of (JSON response, HTTP status code)
        """
        if isinstance(code, str):
            code = ErrorCode[code] if code in ErrorCode.__members__ else ErrorCode.INTERNAL_ERROR

        response = ErrorResponse(
            code=code,
            message=message,
            details=details
        )
        return jsonify(response.to_dict()), http_status

    @staticmethod
    def paginated(
        items: list,
        total: int,
        limit: int,
        offset: int
    ) -> Tuple[Response, int]:
        """Format paginated response.

        Args:
            items: List of items
            total: Total count
            limit: Items per page
            offset: Current offset

        Returns:
            Tuple of (JSON response, HTTP status code)
        """
        from .response_models import PaginatedResponse
        response = PaginatedResponse(
            items=items,
            total=total,
            limit=limit,
            offset=offset
        )
        return jsonify(response.to_dict()), 200

    @staticmethod
    def not_found(message: str = 'Resource not found') -> Tuple[Response, int]:
        """Format not found error response."""
        response = ErrorResponse(
            code=ErrorCode.NOT_FOUND,
            message=message
        )
        return jsonify(response.to_dict()), 404

    @staticmethod
    def unauthorized(message: str = 'Unauthorized') -> Tuple[Response, int]:
        """Format unauthorized error response."""
        response = ErrorResponse(
            code=ErrorCode.UNAUTHORIZED,
            message=message
        )
        return jsonify(response.to_dict()), 401

    @staticmethod
    def forbidden(message: str = 'Forbidden') -> Tuple[Response, int]:
        """Format forbidden error response."""
        response = ErrorResponse(
            code=ErrorCode.FORBIDDEN,
            message=message
        )
        return jsonify(response.to_dict()), 403

    @staticmethod
    def validation_error(message: str = 'Validation failed', details: Dict = None) -> Tuple[Response, int]:
        """Format validation error response."""
        response = ErrorResponse(
            code=ErrorCode.VALIDATION_ERROR,
            message=message,
            details=details
        )
        return jsonify(response.to_dict()), 400

    @staticmethod
    def rate_limit_exceeded(message: str = 'Rate limit exceeded') -> Tuple[Response, int]:
        """Format rate limit error response."""
        response = ErrorResponse(
            code=ErrorCode.RATE_LIMIT,
            message=message
        )
        return jsonify(response.to_dict()), 429

    @staticmethod
    def service_unavailable(message: str = 'Service unavailable') -> Tuple[Response, int]:
        """Format service unavailable response."""
        response = ErrorResponse(
            code=ErrorCode.SERVICE_UNAVAILABLE,
            message=message
        )
        return jsonify(response.to_dict()), 503
