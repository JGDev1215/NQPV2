"""
Standardized API response models for all endpoints.
All API responses should follow these formats.

This module provides:
- Response status enums
- Error code enums
- Response wrapper classes (SuccessResponse, ErrorResponse, PaginatedResponse)
- Helper methods for creating consistent responses

Every endpoint should return one of these response types to ensure
consistent formatting for client applications.
"""

from typing import Any, Dict, List, Optional
from enum import Enum
from datetime import datetime
from dataclasses import dataclass, asdict


class ResponseStatus(str, Enum):
    """Standard response status values."""
    SUCCESS = "success"
    ERROR = "error"
    PARTIAL = "partial"  # Some data succeeded, some failed


class ErrorCode(str, Enum):
    """Standard error codes for all error responses."""
    VALIDATION_ERROR = "VALIDATION_ERROR"
    NOT_FOUND = "NOT_FOUND"
    UNAUTHORIZED = "UNAUTHORIZED"
    FORBIDDEN = "FORBIDDEN"
    RATE_LIMIT = "RATE_LIMIT"
    INTERNAL_ERROR = "INTERNAL_ERROR"
    SERVICE_UNAVAILABLE = "SERVICE_UNAVAILABLE"
    INVALID_REQUEST = "INVALID_REQUEST"
    CONFLICT = "CONFLICT"
    BAD_REQUEST = "BAD_REQUEST"


class HttpStatus(int, Enum):
    """HTTP status codes used in API responses."""
    OK = 200
    CREATED = 201
    NO_CONTENT = 204
    BAD_REQUEST = 400
    UNAUTHORIZED = 401
    FORBIDDEN = 403
    NOT_FOUND = 404
    CONFLICT = 409
    UNPROCESSABLE_ENTITY = 422
    RATE_LIMIT = 429
    INTERNAL_ERROR = 500
    SERVICE_UNAVAILABLE = 503


@dataclass
class ApiMetadata:
    """Metadata included in all API responses."""
    timestamp: str
    version: str = "1.0"
    request_id: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {k: v for k, v in asdict(self).items() if v is not None}


class ApiResponse:
    """Base response model for all API endpoints."""

    def __init__(
        self,
        status: ResponseStatus,
        data: Optional[Dict[str, Any]] = None,
        error: Optional[Dict[str, Any]] = None,
        metadata: Optional[ApiMetadata] = None
    ):
        """Initialize API response.

        Args:
            status: Response status (SUCCESS, ERROR, PARTIAL)
            data: Response data dictionary
            error: Error information dictionary
            metadata: Response metadata
        """
        self.status = status
        self.data = data or {}
        self.error = error
        self.metadata = metadata or ApiMetadata(
            timestamp=datetime.utcnow().isoformat(),
            version="1.0"
        )

    def to_dict(self) -> Dict:
        """Convert to JSON-serializable dictionary."""
        response = {
            'success': self.status == ResponseStatus.SUCCESS,
            'status': self.status.value,
            'data': self.data,
            'metadata': self.metadata.to_dict()
        }
        if self.error:
            response['error'] = self.error
        return response

    def to_json(self):
        """Convert to JSON-compatible format."""
        return self.to_dict()


class SuccessResponse(ApiResponse):
    """Response for successful requests.

    Example:
        response = SuccessResponse(
            data={'ticker': 'NQ=F', 'prediction': 'UP'},
            metadata=ApiMetadata(timestamp=...)
        )
    """

    def __init__(
        self,
        data: Dict[str, Any],
        message: str = None,
        metadata: Optional[ApiMetadata] = None
    ):
        """Initialize success response.

        Args:
            data: Response data
            message: Optional success message
            metadata: Optional metadata
        """
        if message:
            data['message'] = message

        super().__init__(
            status=ResponseStatus.SUCCESS,
            data=data,
            metadata=metadata
        )


class ErrorResponse(ApiResponse):
    """Response for error requests.

    Example:
        response = ErrorResponse(
            code=ErrorCode.VALIDATION_ERROR,
            message='Invalid ticker symbol',
            details={'ticker': 'Invalid value'}
        )
    """

    def __init__(
        self,
        code: ErrorCode,
        message: str,
        details: Optional[Dict] = None,
        metadata: Optional[ApiMetadata] = None
    ):
        """Initialize error response.

        Args:
            code: Error code enum
            message: Human-readable error message
            details: Optional error details (field-specific errors, etc.)
            metadata: Optional metadata
        """
        error_dict = {
            'code': code.value if isinstance(code, ErrorCode) else code,
            'message': message,
            'details': details or {}
        }
        super().__init__(
            status=ResponseStatus.ERROR,
            error=error_dict,
            metadata=metadata
        )


class PaginatedResponse(ApiResponse):
    """Response for paginated data.

    Example:
        response = PaginatedResponse(
            items=[{...}, {...}],
            total=1000,
            limit=50,
            offset=0
        )
    """

    def __init__(
        self,
        items: List[Dict],
        total: int,
        limit: int,
        offset: int,
        metadata: Optional[ApiMetadata] = None
    ):
        """Initialize paginated response.

        Args:
            items: List of result items
            total: Total number of items available
            limit: Items per page
            offset: Current offset
            metadata: Optional metadata
        """
        pagination = {
            'total': total,
            'limit': limit,
            'offset': offset,
            'has_next': (offset + limit) < total,
            'page': (offset // limit) + 1,
            'total_pages': (total + limit - 1) // limit  # Ceiling division
        }

        data = {
            'items': items,
            'pagination': pagination
        }

        combined_metadata = metadata or ApiMetadata(
            timestamp=datetime.utcnow().isoformat()
        )

        super().__init__(
            status=ResponseStatus.SUCCESS,
            data=data,
            metadata=combined_metadata
        )


class PartialResponse(ApiResponse):
    """Response when some operations succeeded and some failed.

    Example:
        response = PartialResponse(
            succeeded=[{...}, {...}],
            failed=[{'item': ..., 'error': ...}],
            message='3 of 5 items processed successfully'
        )
    """

    def __init__(
        self,
        succeeded: List[Dict],
        failed: List[Dict],
        message: str = 'Some operations failed',
        metadata: Optional[ApiMetadata] = None
    ):
        """Initialize partial response.

        Args:
            succeeded: List of successful items
            failed: List of failed items with error info
            message: Summary message
            metadata: Optional metadata
        """
        data = {
            'succeeded': succeeded,
            'failed': failed,
            'succeeded_count': len(succeeded),
            'failed_count': len(failed),
            'total': len(succeeded) + len(failed),
            'message': message
        }

        super().__init__(
            status=ResponseStatus.PARTIAL,
            data=data,
            metadata=metadata
        )


class ResponseBuilder:
    """Builder class for constructing responses fluently.

    Example:
        response = (ResponseBuilder()
            .success()
            .with_data({'result': value})
            .with_metadata(request_id='abc123')
            .build())
    """

    def __init__(self):
        """Initialize response builder."""
        self._status = ResponseStatus.SUCCESS
        self._data = {}
        self._error = None
        self._metadata = None
        self._http_status = 200

    def success(self) -> 'ResponseBuilder':
        """Set status to success."""
        self._status = ResponseStatus.SUCCESS
        self._http_status = 200
        return self

    def error(self) -> 'ResponseBuilder':
        """Set status to error."""
        self._status = ResponseStatus.ERROR
        self._http_status = 400
        return self

    def partial(self) -> 'ResponseBuilder':
        """Set status to partial."""
        self._status = ResponseStatus.PARTIAL
        self._http_status = 200
        return self

    def with_data(self, data: Dict[str, Any]) -> 'ResponseBuilder':
        """Set response data."""
        self._data = data
        return self

    def with_error(self, code: ErrorCode, message: str, details: Dict = None) -> 'ResponseBuilder':
        """Set error information."""
        self._error = {
            'code': code.value,
            'message': message,
            'details': details or {}
        }
        return self

    def with_status_code(self, code: int) -> 'ResponseBuilder':
        """Set HTTP status code."""
        self._http_status = code
        return self

    def with_metadata(self, **kwargs) -> 'ResponseBuilder':
        """Set metadata fields."""
        if self._metadata is None:
            self._metadata = ApiMetadata(
                timestamp=datetime.utcnow().isoformat()
            )
        for key, value in kwargs.items():
            if hasattr(self._metadata, key):
                setattr(self._metadata, key, value)
        return self

    def build(self) -> tuple:
        """Build the response tuple (dict, status_code).

        Returns:
            Tuple of (response_dict, http_status_code)
        """
        response = ApiResponse(
            status=self._status,
            data=self._data,
            error=self._error,
            metadata=self._metadata
        )
        return response.to_dict(), self._http_status
