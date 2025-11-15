"""
Request validation schemas for all API endpoints.
Uses Marshmallow for schema validation and error handling.

Schemas define:
- Required/optional fields
- Field types and constraints
- Default values
- Custom validation rules

Example:
    >>> from marshmallow import ValidationError
    >>> schema = PredictionQuerySchema()
    >>> try:
    ...     data = schema.load({'ticker': 'NQ=F', 'interval': '1h'})
    ... except ValidationError as err:
    ...     print(err.messages)
"""

import logging
from typing import Optional
from datetime import datetime
from marshmallow import Schema, fields, validate, ValidationError, validates_schema

logger = logging.getLogger(__name__)


class PredictionQuerySchema(Schema):
    """Schema for prediction query parameters.

    Validates ticker symbol, time interval, and pagination parameters.
    """

    # Ticker symbol - must be one of the supported tickers
    ticker = fields.Str(
        required=True,
        validate=[
            validate.OneOf(
                ['NQ=F', 'ES=F', '^FTSE', 'NQ', 'ES', 'FTSE'],
                error='Invalid ticker. Must be one of: NQ=F, ES=F, ^FTSE'
            ),
            validate.Length(min=2, max=10)
        ],
        error_messages={
            'required': 'ticker is required',
            'null': 'ticker cannot be null'
        }
    )

    # Time interval - frequency of data
    interval = fields.Str(
        required=False,
        validate=validate.OneOf(
            ['1m', '5m', '15m', '30m', '1h', '4h', '1d'],
            error='Invalid interval. Must be one of: 1m, 5m, 15m, 30m, 1h, 4h, 1d'
        ),
        missing='1h',
        load_default='1h'
    )

    # Pagination limit
    limit = fields.Int(
        required=False,
        validate=validate.Range(min=1, max=1000, error='limit must be between 1 and 1000'),
        missing=100,
        load_default=100
    )

    # Pagination offset
    offset = fields.Int(
        required=False,
        validate=validate.Range(min=0, error='offset must be >= 0'),
        missing=0,
        load_default=0
    )

    # Optional confidence threshold filter
    min_confidence = fields.Float(
        required=False,
        validate=validate.Range(min=0.0, max=1.0, error='min_confidence must be between 0 and 1'),
        missing=None,
        load_default=None
    )

    class Meta:
        """Marshmallow schema meta configuration."""
        # Skip unknown fields (be lenient with extra parameters)
        unknown = 'EXCLUDE'


class HistoricalDataQuerySchema(Schema):
    """Schema for historical data queries.

    Validates ticker, date range, and interval parameters.
    """

    # Ticker symbol
    ticker = fields.Str(
        required=True,
        validate=validate.OneOf(
            ['NQ=F', 'ES=F', '^FTSE'],
            error='Invalid ticker'
        ),
        error_messages={'required': 'ticker is required'}
    )

    # Start date for historical range
    start_date = fields.DateTime(
        required=True,
        format='%Y-%m-%d',
        error_messages={'required': 'start_date is required', 'invalid': 'Invalid date format (use YYYY-MM-DD)'}
    )

    # End date for historical range
    end_date = fields.DateTime(
        required=True,
        format='%Y-%m-%d',
        error_messages={'required': 'end_date is required', 'invalid': 'Invalid date format (use YYYY-MM-DD)'}
    )

    # Time interval for historical data
    interval = fields.Str(
        required=False,
        validate=validate.OneOf(['1m', '5m', '1h', '1d']),
        missing='1h',
        load_default='1h'
    )

    @validates_schema
    def validate_date_range(self, data, **kwargs):
        """Validate that end_date is after start_date."""
        if 'start_date' in data and 'end_date' in data:
            if data['start_date'] >= data['end_date']:
                raise ValidationError('end_date must be after start_date')

    class Meta:
        """Marshmallow schema meta configuration."""
        unknown = 'EXCLUDE'


class MarketStatusQuerySchema(Schema):
    """Schema for market status queries."""

    # Ticker symbol
    ticker = fields.Str(
        required=True,
        validate=validate.OneOf(['NQ=F', 'ES=F', '^FTSE']),
        error_messages={'required': 'ticker is required'}
    )

    # Optional timestamp for historical market status
    timestamp = fields.DateTime(
        required=False,
        format='%Y-%m-%dT%H:%M:%SZ',
        missing=None,
        load_default=None
    )

    class Meta:
        """Marshmallow schema meta configuration."""
        unknown = 'EXCLUDE'


class BlockPredictionQuerySchema(Schema):
    """Schema for 7-block prediction queries."""

    # Ticker symbol
    ticker = fields.Str(
        required=True,
        validate=validate.OneOf(['NQ=F', 'ES=F', '^FTSE']),
        error_messages={'required': 'ticker is required'}
    )

    # Number of blocks to return
    limit = fields.Int(
        required=False,
        validate=validate.Range(min=1, max=100),
        missing=7,
        load_default=7
    )

    # Direction filter (UP, DOWN, NEUTRAL, or ALL)
    direction = fields.Str(
        required=False,
        validate=validate.OneOf(['UP', 'DOWN', 'NEUTRAL', 'ALL']),
        missing='ALL',
        load_default='ALL'
    )

    class Meta:
        """Marshmallow schema meta configuration."""
        unknown = 'EXCLUDE'


class MarketDataBulkQuerySchema(Schema):
    """Schema for bulk market data requests (multiple tickers)."""

    # List of ticker symbols
    tickers = fields.List(
        fields.Str(
            validate=validate.OneOf(['NQ=F', 'ES=F', '^FTSE'])
        ),
        required=True,
        validate=validate.Length(min=1, max=10, error='Must provide 1-10 tickers'),
        error_messages={'required': 'tickers is required'}
    )

    # Time interval
    interval = fields.Str(
        required=False,
        validate=validate.OneOf(['1h', '1d']),
        missing='1h',
        load_default='1h'
    )

    class Meta:
        """Marshmallow schema meta configuration."""
        unknown = 'EXCLUDE'


class DataRecordSchema(Schema):
    """Schema for validating individual market data records."""

    # OHLC data
    open = fields.Float(required=True, validate=validate.Range(min=0.01))
    high = fields.Float(required=True, validate=validate.Range(min=0.01))
    low = fields.Float(required=True, validate=validate.Range(min=0.01))
    close = fields.Float(required=True, validate=validate.Range(min=0.01))
    volume = fields.Int(required=True, validate=validate.Range(min=0))

    # Timestamp
    timestamp = fields.DateTime(
        required=True,
        format='%Y-%m-%dT%H:%M:%SZ'
    )

    # Ticker symbol
    ticker = fields.Str(
        required=True,
        validate=validate.OneOf(['NQ=F', 'ES=F', '^FTSE'])
    )

    class Meta:
        """Marshmallow schema meta configuration."""
        unknown = 'EXCLUDE'


class PaginationSchema(Schema):
    """Schema for pagination parameters."""

    limit = fields.Int(
        required=False,
        validate=validate.Range(min=1, max=1000),
        missing=50,
        load_default=50
    )

    offset = fields.Int(
        required=False,
        validate=validate.Range(min=0),
        missing=0,
        load_default=0
    )

    class Meta:
        """Marshmallow schema meta configuration."""
        unknown = 'EXCLUDE'


class SchedulerQuerySchema(Schema):
    """Schema for scheduler endpoint queries."""

    # Include detailed metrics
    detailed = fields.Bool(
        required=False,
        missing=False,
        load_default=False
    )

    # Include job execution history
    include_history = fields.Bool(
        required=False,
        missing=False,
        load_default=False
    )

    class Meta:
        """Marshmallow schema meta configuration."""
        unknown = 'EXCLUDE'
