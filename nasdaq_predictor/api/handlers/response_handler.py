"""
Standardized API response formatting.

Provides consistent response structure across all API endpoints.
"""

import logging
from datetime import datetime
from flask import jsonify
from typing import Any, Dict, Optional

logger = logging.getLogger(__name__)


class ResponseHandler:
    """Handles standardized API response formatting.

    All API endpoints should use this handler to return consistent response structures.
    """

    @staticmethod
    def success(
        data: Any = None,
        message: str = 'Success',
        status_code: int = 200,
        meta: Optional[Dict[str, Any]] = None
    ) -> tuple:
        """Create a success response.

        Args:
            data: Response data (dict, list, or primitive)
            message: Success message
            status_code: HTTP status code (default: 200)
            meta: Optional metadata (pagination, timestamps, etc.)

        Returns:
            tuple: (JSON response, HTTP status code)
        """
        response = {
            'success': True,
            'message': message,
            'data': data,
            'timestamp': datetime.utcnow().isoformat()
        }

        if meta:
            response['meta'] = meta

        return jsonify(response), status_code

    @staticmethod
    def created(
        data: Any = None,
        message: str = 'Resource created',
        meta: Optional[Dict[str, Any]] = None
    ) -> tuple:
        """Create a 201 Created response.

        Args:
            data: Created resource data
            message: Success message
            meta: Optional metadata

        Returns:
            tuple: (JSON response, 201 status code)
        """
        return ResponseHandler.success(data, message, 201, meta)

    @staticmethod
    def accepted(
        data: Any = None,
        message: str = 'Request accepted',
        meta: Optional[Dict[str, Any]] = None
    ) -> tuple:
        """Create a 202 Accepted response for async operations.

        Args:
            data: Initial response data (task ID, job ID, etc.)
            message: Success message
            meta: Optional metadata

        Returns:
            tuple: (JSON response, 202 status code)
        """
        return ResponseHandler.success(data, message, 202, meta)

    @staticmethod
    def paginated(
        data: list,
        total: int,
        page: int = 1,
        page_size: int = 20,
        message: str = 'Success'
    ) -> tuple:
        """Create a paginated response.

        Args:
            data: List of items
            total: Total number of items
            page: Current page number (1-indexed)
            page_size: Items per page
            message: Success message

        Returns:
            tuple: (JSON response, 200 status code)
        """
        total_pages = (total + page_size - 1) // page_size  # Ceiling division

        response = {
            'success': True,
            'message': message,
            'data': data,
            'pagination': {
                'page': page,
                'page_size': page_size,
                'total': total,
                'total_pages': total_pages,
                'has_next': page < total_pages,
                'has_prev': page > 1
            },
            'timestamp': datetime.utcnow().isoformat()
        }

        return jsonify(response), 200

    @staticmethod
    def batch_results(
        results: Dict[str, Any],
        total: int,
        successful: int,
        failed: int,
        message: str = 'Batch processing complete'
    ) -> tuple:
        """Create a batch processing result response.

        Args:
            results: Dict of item results
            total: Total items processed
            successful: Successfully processed count
            failed: Failed count
            message: Status message

        Returns:
            tuple: (JSON response, 200 status code)
        """
        response = {
            'success': True,
            'message': message,
            'data': results,
            'batch_status': {
                'total': total,
                'successful': successful,
                'failed': failed,
                'success_rate': round((successful / total * 100), 2) if total > 0 else 0.0
            },
            'timestamp': datetime.utcnow().isoformat()
        }

        return jsonify(response), 200

    @staticmethod
    def no_content() -> tuple:
        """Create a 204 No Content response.

        Returns:
            tuple: (empty response, 204 status code)
        """
        return '', 204

    @staticmethod
    def stream(
        data: Any,
        message: str = 'Streaming data',
        meta: Optional[Dict[str, Any]] = None
    ) -> tuple:
        """Create a streaming response wrapper.

        Args:
            data: Data to stream
            message: Description message
            meta: Optional metadata

        Returns:
            tuple: (JSON response, 200 status code)
        """
        response = {
            'success': True,
            'message': message,
            'stream': data,
            'timestamp': datetime.utcnow().isoformat()
        }

        if meta:
            response['meta'] = meta

        return jsonify(response), 200

    @staticmethod
    def error(
        error_message: str,
        error_type: str = 'Error',
        status_code: int = 500,
        details: Optional[Dict[str, Any]] = None
    ) -> tuple:
        """Create an error response.

        Args:
            error_message: Error message
            error_type: Type of error
            status_code: HTTP status code
            details: Optional error details

        Returns:
            tuple: (JSON response, HTTP status code)
        """
        response = {
            'success': False,
            'error': error_message,
            'error_type': error_type,
            'status': status_code,
            'timestamp': datetime.utcnow().isoformat()
        }

        if details:
            response['details'] = details

        return jsonify(response), status_code
