"""
Middleware for request validation using Marshmallow schemas.

Provides decorators and utilities to validate incoming requests against
defined schemas, returning standardized error responses on validation failures.

Example:
    >>> from flask import Flask
    >>> from nasdaq_predictor.api.validation_middleware import validate_request
    >>> from nasdaq_predictor.api.validation_schemas import PredictionQuerySchema
    >>>
    >>> app = Flask(__name__)
    >>>
    >>> @app.route('/api/predictions/<ticker>')
    >>> @validate_request(PredictionQuerySchema())
    >>> def get_predictions(ticker):
    ...     # request.validated_data contains the validated parameters
    ...     interval = request.validated_data.get('interval', '1h')
    ...     limit = request.validated_data.get('limit', 100)
    ...     return {'ticker': ticker, 'interval': interval, 'limit': limit}
"""

import logging
from functools import wraps
from typing import Type, Optional
from flask import request, jsonify, Response
from marshmallow import Schema, ValidationError, pre_load

logger = logging.getLogger(__name__)


def validate_request(schema_class: Type[Schema], source: str = 'auto'):
    """Decorator to validate request parameters against schema.

    Validates incoming request data (query parameters or JSON body) against
    a Marshmallow schema. On validation failure, returns standardized error response.

    Args:
        schema_class: Marshmallow Schema class to validate against
        source: Data source ('auto', 'query', 'json', 'form')
            'auto' - Try JSON first, fall back to query parameters
            'query' - Only use query parameters
            'json' - Only use JSON body
            'form' - Only use form data

    Returns:
        Decorator function

    Raises:
        ValueError: If source is invalid

    Example:
        @app.route('/api/predictions')
        @validate_request(PredictionQuerySchema())
        def get_predictions():
            interval = request.validated_data['interval']
            ...
    """

    # Validate source parameter
    valid_sources = ['auto', 'query', 'json', 'form']
    if source not in valid_sources:
        raise ValueError(f"source must be one of {valid_sources}, got {source}")

    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs) -> Response:
            """Wrapper function that performs validation."""
            try:
                # Determine data source
                data = _get_request_data(source)

                # Instantiate schema
                schema = schema_class

                # Validate and load data
                try:
                    validated_data = schema.load(data)
                    request.validated_data = validated_data
                    logger.debug(f"✓ Request validation passed for {f.__name__}")
                    return f(*args, **kwargs)

                except ValidationError as err:
                    logger.warning(f"✗ Request validation failed for {f.__name__}: {err.messages}")
                    return _create_validation_error_response(err.messages), 400

            except Exception as e:
                logger.error(f"Error in validation middleware: {e}", exc_info=True)
                return _create_error_response(
                    error_code='VALIDATION_ERROR',
                    message='Validation error occurred',
                    details={'error': str(e)}
                ), 500

        return decorated_function

    return decorator


def _get_request_data(source: str = 'auto') -> dict:
    """Extract data from request based on source.

    Args:
        source: Data source type ('auto', 'query', 'json', 'form')

    Returns:
        Dictionary of request data

    Raises:
        ValueError: If source is invalid
    """
    if source == 'query':
        return request.args.to_dict(flat=False)

    elif source == 'json':
        data = request.get_json(force=True, silent=True) or {}
        return data if isinstance(data, dict) else {}

    elif source == 'form':
        return request.form.to_dict(flat=False)

    elif source == 'auto':
        # Try JSON first
        if request.is_json:
            data = request.get_json(force=True, silent=True)
            if isinstance(data, dict):
                return data

        # Fall back to query parameters
        return request.args.to_dict(flat=False)

    else:
        raise ValueError(f"Invalid source: {source}")


def _create_validation_error_response(errors: dict) -> dict:
    """Create standardized validation error response.

    Args:
        errors: Marshmallow validation errors dictionary

    Returns:
        Standardized error response dictionary
    """
    return {
        'success': False,
        'status': 'error',
        'error': {
            'code': 'VALIDATION_ERROR',
            'message': 'Request validation failed',
            'details': errors
        }
    }


def _create_error_response(
    error_code: str = 'ERROR',
    message: str = 'An error occurred',
    details: Optional[dict] = None
) -> dict:
    """Create standardized error response.

    Args:
        error_code: Error code string
        message: Human-readable error message
        details: Optional additional error details

    Returns:
        Standardized error response dictionary
    """
    response = {
        'success': False,
        'status': 'error',
        'error': {
            'code': error_code,
            'message': message
        }
    }

    if details:
        response['error']['details'] = details

    return response


def optional_validation(schema_class: Type[Schema]):
    """Decorator for optional validation (doesn't fail on validation errors).

    Useful for endpoints where validation is preferred but not required.
    Validated data is available in request.validated_data if validation succeeded.

    Args:
        schema_class: Marshmallow Schema class to validate against

    Returns:
        Decorator function
    """

    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            """Wrapper function that performs optional validation."""
            try:
                data = _get_request_data('auto')
                schema = schema_class

                try:
                    validated_data = schema.load(data)
                    request.validated_data = validated_data
                    logger.debug(f"Optional validation passed for {f.__name__}")
                except ValidationError as err:
                    logger.debug(f"Optional validation skipped (non-fatal): {err.messages}")
                    request.validated_data = data  # Use raw data if validation fails

            except Exception as e:
                logger.debug(f"Optional validation error (non-fatal): {e}")
                request.validated_data = _get_request_data('auto')

            return f(*args, **kwargs)

        return decorated_function

    return decorator


class RequestValidator:
    """Utility class for manual request validation in handlers.

    Example:
        validator = RequestValidator()
        validated = validator.validate(request, PredictionQuerySchema())
        if not validated['valid']:
            return jsonify(validated['error']), 400
        params = validated['data']
    """

    @staticmethod
    def validate(req, schema_class: Type[Schema], source: str = 'auto') -> dict:
        """Validate request data against schema.

        Args:
            req: Flask request object
            schema_class: Marshmallow Schema class
            source: Data source ('auto', 'query', 'json', 'form')

        Returns:
            Dictionary with keys:
            - 'valid': Boolean indicating if validation passed
            - 'data': Validated data (if valid=True)
            - 'error': Error response (if valid=False)
        """
        try:
            # Get data from request
            if source == 'query':
                data = req.args.to_dict(flat=False)
            elif source == 'json':
                data = req.get_json(force=True, silent=True) or {}
            elif source == 'form':
                data = req.form.to_dict(flat=False)
            else:  # auto
                if req.is_json:
                    data = req.get_json(force=True, silent=True)
                    if not isinstance(data, dict):
                        data = {}
                else:
                    data = req.args.to_dict(flat=False)

            # Validate
            schema = schema_class
            validated_data = schema.load(data)

            return {
                'valid': True,
                'data': validated_data,
                'error': None
            }

        except ValidationError as err:
            return {
                'valid': False,
                'data': None,
                'error': _create_validation_error_response(err.messages)
            }

        except Exception as e:
            logger.error(f"Validation error: {e}", exc_info=True)
            return {
                'valid': False,
                'data': None,
                'error': _create_error_response(
                    error_code='VALIDATION_ERROR',
                    message='Validation failed',
                    details={'error': str(e)}
                )
            }
