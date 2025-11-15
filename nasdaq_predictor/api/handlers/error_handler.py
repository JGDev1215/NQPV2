"""
Centralized error handling for API endpoints.

Converts exceptions to standardized JSON error responses with appropriate HTTP status codes.
"""

import logging
from flask import jsonify
from datetime import datetime

# Import custom exceptions
try:
    from ...core.exceptions import (
        NQPException,
        ValidationException,
        DataFetchException,
        AnalysisException,
        DatabaseException,
        SchedulerException,
    )
except ImportError:
    # Fallback if core exceptions don't exist yet
    NQPException = Exception
    ValidationException = Exception
    DataFetchException = Exception
    AnalysisException = Exception
    DatabaseException = Exception
    SchedulerException = Exception

logger = logging.getLogger(__name__)


class ErrorHandler:
    """Centralized error handling for API responses.

    Maps Python exceptions to appropriate HTTP status codes and JSON response formats.
    """

    # Mapping of exception types to HTTP status codes
    ERROR_CODES = {
        ValidationException: 400,  # Bad Request
        DataFetchException: 503,   # Service Unavailable
        AnalysisException: 500,    # Internal Server Error
        DatabaseException: 503,    # Service Unavailable
        SchedulerException: 500,   # Internal Server Error
        NQPException: 500,         # Internal Server Error
        ValueError: 400,           # Bad Request
        KeyError: 400,             # Bad Request
        TypeError: 400,            # Bad Request
    }

    @staticmethod
    def handle_error(error: Exception, status_code: int = None) -> tuple:
        """Convert exception to JSON error response.

        Args:
            error: Exception to handle
            status_code: Optional override for HTTP status code

        Returns:
            tuple: (JSON response, HTTP status code)
        """
        # Determine status code from exception type or use override
        if status_code is None:
            status_code = ErrorHandler.ERROR_CODES.get(
                type(error),
                500  # Default to Internal Server Error
            )

        # Log the error
        logger.error(
            f"API Error [{status_code}]: {type(error).__name__} - {str(error)}",
            exc_info=True
        )

        # Build error response
        response = {
            'success': False,
            'error': str(error),
            'error_type': type(error).__name__,
            'status': status_code,
            'timestamp': datetime.utcnow().isoformat()
        }

        return jsonify(response), status_code

    @staticmethod
    def validation_error(message: str) -> tuple:
        """Create a validation error response.

        Args:
            message: Error message

        Returns:
            tuple: (JSON response, 400 status code)
        """
        response = {
            'success': False,
            'error': message,
            'error_type': 'ValidationError',
            'status': 400,
            'timestamp': datetime.utcnow().isoformat()
        }
        return jsonify(response), 400

    @staticmethod
    def not_found_error(resource: str) -> tuple:
        """Create a not found error response.

        Args:
            resource: Name of resource not found

        Returns:
            tuple: (JSON response, 404 status code)
        """
        response = {
            'success': False,
            'error': f'{resource} not found',
            'error_type': 'NotFoundError',
            'status': 404,
            'timestamp': datetime.utcnow().isoformat()
        }
        return jsonify(response), 404

    @staticmethod
    def server_error(message: str = 'Internal server error') -> tuple:
        """Create a server error response.

        Args:
            message: Error message

        Returns:
            tuple: (JSON response, 500 status code)
        """
        response = {
            'success': False,
            'error': message,
            'error_type': 'ServerError',
            'status': 500,
            'timestamp': datetime.utcnow().isoformat()
        }
        return jsonify(response), 500
