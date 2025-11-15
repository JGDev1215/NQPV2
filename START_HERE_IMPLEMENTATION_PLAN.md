# 🚀 NASDAQ PREDICTOR - COMPREHENSIVE IMPLEMENTATION PLAN

**Purpose:** Complete guide for agents to systematically improve the application based on all 8 specialist reviews.

**How to Use:**
1. User: "Read START_HERE_IMPLEMENTATION_PLAN.md and begin implementation"
2. Agent: Follows this plan sequentially, executing each phase
3. Result: Production-grade financial prediction system

---

## 📊 QUICK STATS

- **Total Improvement Tasks:** 48
- **Critical Issues:** 12 (P0/P1)
- **Estimated Timeline:** 8-12 weeks (1 developer)
- **Files to Modify:** 35+
- **New Files to Create:** 8-10
- **Lines of Code:** ~2,500 additions/modifications
- **Expected ROI:** 60%+ bug reduction, 5-10x performance improvement

---

## 🎯 PHASE OVERVIEW

| Phase | Priority | Duration | Key Focus | Status |
|-------|----------|----------|-----------|--------|
| **Phase 0** | P0 | 1 day | Setup & validation | Not Started |
| **Phase 1** | P0 | 3 days | Critical foundations | Not Started |
| **Phase 2** | P0 | 3 days | API & data integrity | Not Started |
| **Phase 3** | P1 | 4 days | Scheduling & monitoring | Not Started |
| **Phase 4** | P1 | 5 days | Testing infrastructure | Not Started |
| **Phase 5** | P2 | 6 days | Performance optimization | Not Started |
| **Phase 6** | P2 | 6 days | UI/UX modernization | Not Started |
| **Phase 7** | P2 | Ongoing | Polish & maintenance | Not Started |

---

## ⚙️ PHASE 0: SETUP & VALIDATION (Day 1)

**Goal:** Establish baseline, verify environment, create supporting infrastructure

### Task 0.1: Environment Verification
- **File:** None (validation only)
- **Action:** Verify all dependencies installed
  ```bash
  # Check Python version (3.10+)
  python --version

  # Check dependencies
  pip list | grep -E "flask|supabase|apscheduler|pytest|yfinance"

  # Verify database connection
  python -c "from nasdaq_predictor.database.models import *; print('DB OK')"
  ```
- **Success Criteria:** All imports successful

### Task 0.2: Create Implementation Tracking Database
- **File:** Create `implementation_status.json`
- **Action:** Create JSON file to track implementation progress
  ```json
  {
    "phase": 0,
    "started_at": "2025-11-15",
    "tasks": {
      "phase_1": {"status": "pending", "subtasks": []},
      "phase_2": {"status": "pending", "subtasks": []},
      "phase_3": {"status": "pending", "subtasks": []},
      "phase_4": {"status": "pending", "subtasks": []},
      "phase_5": {"status": "pending", "subtasks": []},
      "phase_6": {"status": "pending", "subtasks": []}
    }
  }
  ```
- **Success Criteria:** JSON created and readable

### Task 0.3: Review All Agent Reports
- **Files to Read:**
  - `API_ARCHITECTURE_REVIEW.md` - API gaps
  - `YAHOO_FINANCE_REVIEW_SUMMARY.txt` - Data fetching issues
  - `DATABASE_REVIEW_EXECUTIVE_SUMMARY.txt` - Database optimizations
  - `SERVICE_ARCHITECTURE_ANALYSIS.md` - DI container gaps
  - `COMPREHENSIVE_TESTING_STRATEGY.md` - Testing roadmap
- **Action:** Understand critical issues and interdependencies
- **Success Criteria:** Can explain 5 critical issues and their impacts

### Task 0.4: Backup Current State
- **Action:** Create git branch for implementation
  ```bash
  git checkout -b implementation/comprehensive-improvements
  git commit --allow-empty -m "START: Comprehensive system improvements"
  ```
- **Success Criteria:** New branch created and visible in git

---

## 🔴 PHASE 1: CRITICAL FOUNDATIONS (Days 2-4)

### Goal: Implement essential production safeguards

---

## 1️⃣.1 DI CONTAINER VALIDATION & FIXES

**Priority:** P0 | **Effort:** 4-6 hours | **Impact:** HIGH (prevents runtime crashes)

### 1.1.1: Fix Missing DI Registrations

**Files to Modify:**
- `/Users/soonjeongguan/Desktop/Repository/CLAUDECODE/NQP/nasdaq_predictor/core/services_container.py`

**Current State:** MarketStatusService and SchedulerJobTrackingService not registered

**Implementation:**

1. Open the services_container.py file
2. Find the `build_container()` or `register_services()` function
3. Add these registrations (reference: SERVICE_ARCHITECTURE_ANALYSIS.md):

```python
# Add to services container - AFTER existing registrations

# Register MarketStatusService
container.register_singleton(
    'market_status_service',
    lambda: MarketStatusService()
)

# Register SchedulerJobTrackingService with dependencies
container.register_singleton(
    'scheduler_job_tracking_service',
    lambda c: SchedulerJobTrackingService(
        job_execution_repository=c.resolve('scheduler_job_execution_repository'),
        logger=logging.getLogger('scheduler_tracking')
    )
)

# Register missing imports
from nasdaq_predictor.services.market_status_service import MarketStatusService
from nasdaq_predictor.services.scheduler_job_tracking_service import SchedulerJobTrackingService
```

**Testing:**
```python
# In tests/test_di_container.py - add this test
def test_all_services_registered():
    from app import create_app
    app = create_app()
    container = app.container

    required_services = [
        'market_status_service',
        'scheduler_job_tracking_service',
        'data_sync_service',
        'block_prediction_service',
        'verification_service'
    ]

    for service_name in required_services:
        try:
            service = container.resolve(service_name)
            assert service is not None, f"{service_name} is None"
        except Exception as e:
            raise AssertionError(f"Failed to resolve {service_name}: {e}")
```

**Success Criteria:**
- ✅ Both services resolve without errors
- ✅ Unit test passes
- ✅ Application starts without DI errors

---

### 1.1.2: Add Circular Dependency Detection

**File:** `/nasdaq_predictor/core/services_container.py`

**Implementation:**

Add validation method to container class:

```python
def detect_circular_dependencies(self):
    """Detect circular dependencies in service graph."""
    visited = set()
    recursion_stack = set()

    def visit(service_name, path=[]):
        if service_name in recursion_stack:
            cycle = " -> ".join(path + [service_name])
            raise RuntimeError(f"Circular dependency detected: {cycle}")

        if service_name in visited:
            return

        visited.add(service_name)
        recursion_stack.add(service_name)

        # Get dependencies for this service
        if service_name in self._dependencies:
            for dep in self._dependencies[service_name]:
                visit(dep, path + [service_name])

        recursion_stack.remove(service_name)

    # Check all registered services
    for service_name in self._registry:
        visit(service_name)
```

**Call during initialization:**

```python
# In app.py, after container setup
try:
    container.detect_circular_dependencies()
    logger.info("✓ No circular dependencies detected")
except RuntimeError as e:
    logger.error(f"✗ Circular dependency found: {e}")
    raise
```

**Success Criteria:**
- ✅ Circular dependency detection runs on startup
- ✅ No circular dependencies detected
- ✅ Clear error message if found

---

## 1️⃣.2 API RATE LIMITING

**Priority:** P0 | **Effort:** 8-10 hours | **Impact:** CRITICAL (prevents API throttling)

### 1.2.1: Install Rate Limiting Library

**Action:** Install Flask-Limiter and Redis

```bash
pip install Flask-Limiter redis
```

### 1.2.2: Create Rate Limiter Configuration

**File:** Create `/nasdaq_predictor/config/rate_limiter_config.py`

```python
"""
Rate limiting configuration for API endpoints.
Prevents API abuse and throttling from upstream providers.
"""

from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
import redis

class RateLimiterConfig:
    """Configuration for different rate limit tiers."""

    # Public endpoints - loose limits
    PUBLIC_LIMITS = {
        'default': '100/hour',
        'dashboard': '50/hour'
    }

    # Authenticated endpoints - stricter limits
    AUTH_LIMITS = {
        'predictions': '500/hour',
        'historical': '200/hour',
        'data': '1000/hour'
    }

    # Internal jobs - very strict (prevent runaway jobs)
    INTERNAL_LIMITS = {
        'market_data_sync': '720/day',  # Every 90 seconds
        'predictions': '96/day',         # Every 15 minutes
        'verification': '96/day'         # Every 15 minutes
    }

    # Storage backend
    REDIS_URL = 'redis://localhost:6379'
    STORAGE_URL = REDIS_URL

def init_rate_limiter(app):
    """Initialize rate limiter for Flask app."""
    limiter = Limiter(
        app=app,
        key_func=get_remote_address,
        storage_uri=RateLimiterConfig.STORAGE_URL,
        default_limits=['200/hour'],
        strategy='moving-window'
    )

    return limiter
```

### 1.2.3: Apply Rate Limiting to All API Routes

**Files to Modify:** All files in `/nasdaq_predictor/api/routes/`

**Pattern:**

```python
# Example: nasdaq_predictor/api/routes/prediction_routes.py

from flask import Blueprint, request, jsonify
from flask_limiter.util import get_remote_address

prediction_bp = Blueprint('predictions', __name__, url_prefix='/api/predictions')
limiter = current_app.limiter  # Injected from app.py

# Apply per-endpoint limits
@prediction_bp.route('/<ticker>/block', methods=['GET'])
@limiter.limit('100/hour')  # 100 requests per hour per IP
def get_block_predictions(ticker):
    """Get 7-block predictions for ticker."""
    # Implementation...
    pass

@prediction_bp.route('/<ticker>/history', methods=['GET'])
@limiter.limit('50/hour')  # Historical data less frequently
def get_prediction_history(ticker):
    """Get historical prediction data."""
    # Implementation...
    pass
```

**Apply to all route files:**
1. `prediction_routes.py` - Add @limiter decorators
2. `market_status_routes.py` - Add @limiter decorators
3. `historical_data_routes.py` - Add @limiter decorators
4. `scheduler_metrics_routes.py` - Add @limiter decorators

### 1.2.4: Test Rate Limiting

**File:** Create `tests/test_rate_limiting.py`

```python
"""Tests for API rate limiting."""

import pytest
from flask import Flask
from nasdaq_predictor.config.rate_limiter_config import init_rate_limiter

def test_rate_limit_exceeded():
    """Test that rate limit is enforced."""
    app = Flask(__name__)
    app.config['TESTING'] = True
    limiter = init_rate_limiter(app)

    @app.route('/test')
    @limiter.limit('5/hour')
    def test_endpoint():
        return 'OK', 200

    client = app.test_client()

    # Make 5 requests (should succeed)
    for i in range(5):
        response = client.get('/test')
        assert response.status_code == 200

    # 6th request should be rate limited
    response = client.get('/test')
    assert response.status_code == 429  # Too Many Requests
```

**Success Criteria:**
- ✅ Rate limiter installed and initialized
- ✅ All API endpoints have rate limiting applied
- ✅ Unit tests pass
- ✅ Requests exceed limit return 429 status

---

## 1️⃣.3 INPUT VALIDATION SCHEMAS

**Priority:** P0 | **Effort:** 6-8 hours | **Impact:** HIGH (prevents bad data)

### 1.3.1: Create Validation Schemas

**File:** Create `/nasdaq_predictor/api/validation_schemas.py`

```python
"""
Request validation schemas for all API endpoints.
Uses Marshmallow for schema validation.
"""

from marshmallow import Schema, fields, validate, ValidationError

class PredictionQuerySchema(Schema):
    """Schema for prediction query parameters."""
    ticker = fields.Str(
        required=True,
        validate=validate.OneOf(['NQ=F', 'ES=F', '^FTSE']),
        error_messages={'required': 'ticker is required', 'validator_failed': 'Invalid ticker'}
    )
    interval = fields.Str(
        required=False,
        validate=validate.OneOf(['1m', '5m', '15m', '30m', '1h', '1d']),
        missing='1h'
    )
    limit = fields.Int(
        required=False,
        validate=validate.Range(min=1, max=1000),
        missing=100
    )
    offset = fields.Int(
        required=False,
        validate=validate.Range(min=0),
        missing=0
    )

class HistoricalDataQuerySchema(Schema):
    """Schema for historical data queries."""
    ticker = fields.Str(required=True)
    start_date = fields.DateTime(required=True, format='%Y-%m-%d')
    end_date = fields.DateTime(required=True, format='%Y-%m-%d')
    interval = fields.Str(
        required=False,
        validate=validate.OneOf(['1m', '5m', '1h', '1d']),
        missing='1h'
    )

class MarketStatusQuerySchema(Schema):
    """Schema for market status queries."""
    ticker = fields.Str(
        required=True,
        validate=validate.OneOf(['NQ=F', 'ES=F', '^FTSE'])
    )
    timestamp = fields.DateTime(
        required=False,
        format='%Y-%m-%dT%H:%M:%SZ'
    )

# Add more schemas for other endpoints...
```

### 1.3.2: Create Validation Middleware

**File:** Create `/nasdaq_predictor/api/validation_middleware.py`

```python
"""
Middleware for request validation using Marshmallow schemas.
"""

from functools import wraps
from flask import request, jsonify
from marshmallow import ValidationError

def validate_request(schema_class):
    """
    Decorator to validate request parameters against schema.

    Usage:
        @app.route('/api/predictions')
        @validate_request(PredictionQuerySchema())
        def get_predictions():
            # request.validated_data contains validated parameters
            ticker = request.validated_data['ticker']
            ...
    """
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            schema = schema_class

            # Get validation source (query params or JSON body)
            data = request.args.to_dict() if request.method == 'GET' else request.get_json()

            if data is None:
                data = {}

            try:
                validated_data = schema.load(data)
                request.validated_data = validated_data
                return f(*args, **kwargs)

            except ValidationError as err:
                return jsonify({
                    'success': False,
                    'error': 'Validation failed',
                    'errors': err.messages
                }), 400

        return decorated_function
    return decorator
```

### 1.3.3: Apply Validation to Routes

**Files to Modify:** All in `/nasdaq_predictor/api/routes/`

**Example - prediction_routes.py:**

```python
from nasdaq_predictor.api.validation_schemas import PredictionQuerySchema
from nasdaq_predictor.api.validation_middleware import validate_request

@prediction_bp.route('/<ticker>/block', methods=['GET'])
@limiter.limit('100/hour')
@validate_request(PredictionQuerySchema())
def get_block_predictions(ticker):
    """Get 7-block predictions for ticker."""
    # Access validated data
    validated = request.validated_data

    interval = validated.get('interval', '1h')
    limit = validated.get('limit', 100)

    # Implementation...
    pass
```

**Success Criteria:**
- ✅ Schemas defined for all endpoints
- ✅ Validation middleware applied to all routes
- ✅ Invalid requests return 400 with error details
- ✅ Valid requests pass through successfully

---

## 1️⃣.4 DATA VALIDATION LAYER

**Priority:** P0 | **Effort:** 6-8 hours | **Impact:** CRITICAL (prevents corrupt data)

### 1.4.1: Create Data Quality Validator

**File:** Create `/nasdaq_predictor/core/data_quality_validator.py`

```python
"""
Data quality validation for OHLC data before storage.
Ensures data integrity and prevents corrupt values in database.
"""

from typing import Dict, List, Tuple
from datetime import datetime
import logging

logger = logging.getLogger(__name__)

class OHLCValidator:
    """Validates OHLC (Open, High, Low, Close) data."""

    def __init__(self, ticker: str):
        self.ticker = ticker
        self.validation_errors = []

    def validate_bar(self, bar: Dict) -> Tuple[bool, List[str]]:
        """
        Validate a single OHLC bar.

        Args:
            bar: Dictionary with keys: open, high, low, close, volume, timestamp

        Returns:
            (is_valid: bool, errors: List[str])
        """
        errors = []

        # Check for required fields
        required_fields = ['open', 'high', 'low', 'close', 'volume', 'timestamp']
        for field in required_fields:
            if field not in bar:
                errors.append(f"Missing field: {field}")

        if errors:
            return False, errors

        # Extract values
        o = bar['open']
        h = bar['high']
        l = bar['low']
        c = bar['close']
        v = bar['volume']

        # Check for NaN values
        if any(val != val for val in [o, h, l, c, v]):  # NaN check (NaN != NaN)
            errors.append("Contains NaN values")
            return False, errors

        # Check for negative values
        if o < 0 or h < 0 or l < 0 or c < 0:
            errors.append(f"Negative prices found: O={o}, H={h}, L={l}, C={c}")
            return False, errors

        if v < 0:
            errors.append(f"Negative volume: {v}")
            return False, errors

        # OHLC constraint: H >= max(O,C) and L <= min(O,C)
        max_oc = max(o, c)
        min_oc = min(o, c)

        if h < max_oc:
            errors.append(f"High {h} < max(O,C) {max_oc}")

        if l > min_oc:
            errors.append(f"Low {l} > min(O,C) {min_oc}")

        # Check for extreme outliers (>50% change)
        if o > 0:
            pct_change = abs((c - o) / o) * 100
            if pct_change > 50:
                logger.warning(f"{self.ticker}: Extreme price change {pct_change:.1f}%")
                # Don't fail, but log warning

        if errors:
            return False, errors

        return True, []

    def validate_batch(self, bars: List[Dict]) -> Tuple[bool, List[str], int]:
        """
        Validate a batch of OHLC bars.

        Returns:
            (all_valid: bool, errors: List[str], valid_count: int)
        """
        total_errors = []
        valid_count = 0

        for i, bar in enumerate(bars):
            is_valid, errors = self.validate_bar(bar)

            if is_valid:
                valid_count += 1
            else:
                total_errors.append(f"Bar {i}: {', '.join(errors)}")

        all_valid = len(total_errors) == 0
        return all_valid, total_errors, valid_count
```

### 1.4.2: Integrate Validator into Data Fetcher

**File:** Modify `/nasdaq_predictor/services/data_fetcher_service.py`

Find the function that saves data (likely `sync_all_tickers()` or similar):

```python
# At the top of the file, add import
from nasdaq_predictor.core.data_quality_validator import OHLCValidator

# In the data saving function, add validation before database insert:

def fetch_and_store_ticker_data(self, ticker: str) -> Dict:
    """Fetch data from yfinance and store with validation."""
    try:
        # Fetch data...
        raw_data = yf.download(ticker, ...)
        bars = self._convert_to_bars(raw_data)

        # VALIDATE before storing
        validator = OHLCValidator(ticker)
        is_valid, errors, valid_count = validator.validate_batch(bars)

        if not is_valid:
            logger.error(f"Data validation failed for {ticker}:")
            for error in errors:
                logger.error(f"  - {error}")

            # Filter out invalid bars
            valid_bars = []
            for bar in bars:
                is_valid_bar, _ = validator.validate_bar(bar)
                if is_valid_bar:
                    valid_bars.append(bar)

            bars = valid_bars
            logger.info(f"Storing {len(bars)} valid bars (removed {len(bars) - valid_count} invalid)")

        # Store valid data
        if bars:
            self.repository.insert_bars(ticker, bars)
            return {'success': True, 'stored': len(bars), 'failed': len(bars) - valid_count}
        else:
            return {'success': False, 'error': 'No valid bars after validation'}

    except Exception as e:
        logger.error(f"Error fetching {ticker}: {e}")
        raise
```

### 1.4.3: Test Data Validation

**File:** Create `tests/test_data_quality.py`

```python
"""Tests for data quality validation."""

import pytest
from nasdaq_predictor.core.data_quality_validator import OHLCValidator

def test_valid_bar():
    """Test validation of valid OHLC bar."""
    validator = OHLCValidator('NQ=F')

    bar = {
        'open': 100.0,
        'high': 105.0,
        'low': 99.0,
        'close': 103.0,
        'volume': 1000000,
        'timestamp': '2025-11-15T10:00:00Z'
    }

    is_valid, errors = validator.validate_bar(bar)
    assert is_valid == True
    assert len(errors) == 0

def test_invalid_bar_nan():
    """Test rejection of NaN values."""
    validator = OHLCValidator('NQ=F')

    bar = {
        'open': float('nan'),
        'high': 105.0,
        'low': 99.0,
        'close': 103.0,
        'volume': 1000000,
        'timestamp': '2025-11-15T10:00:00Z'
    }

    is_valid, errors = validator.validate_bar(bar)
    assert is_valid == False
    assert 'NaN' in str(errors)

def test_invalid_bar_ohlc_constraint():
    """Test rejection of OHLC constraint violations."""
    validator = OHLCValidator('NQ=F')

    bar = {
        'open': 100.0,
        'high': 95.0,  # High < Low, violates constraint
        'low': 99.0,
        'close': 103.0,
        'volume': 1000000,
        'timestamp': '2025-11-15T10:00:00Z'
    }

    is_valid, errors = validator.validate_bar(bar)
    assert is_valid == False
    assert any('High' in str(e) for e in errors)
```

**Success Criteria:**
- ✅ Validator detects NaN values
- ✅ Validator enforces OHLC constraints
- ✅ Invalid data rejected before database insert
- ✅ Unit tests pass
- ✅ No corrupt data in database

---

## 🔴 PHASE 2: API & ERROR HANDLING (Days 5-7)

### Goal: Standardize API responses, add error consistency

---

## 2️⃣.1 STANDARDIZED ERROR RESPONSES

**Priority:** P0 | **Effort:** 4-6 hours | **Impact:** HIGH (client integration)

### 2.1.1: Create Response Format Classes

**File:** Create `/nasdaq_predictor/api/response_models.py`

```python
"""
Standardized API response models for all endpoints.
All API responses should follow these formats.
"""

from typing import Any, Dict, List, Optional
from enum import Enum
from datetime import datetime

class ResponseStatus(str, Enum):
    """Standard response status values."""
    SUCCESS = "success"
    ERROR = "error"
    PARTIAL = "partial"  # Some data succeeded, some failed

class ErrorCode(str, Enum):
    """Standard error codes."""
    VALIDATION_ERROR = "VALIDATION_ERROR"
    NOT_FOUND = "NOT_FOUND"
    UNAUTHORIZED = "UNAUTHORIZED"
    RATE_LIMIT = "RATE_LIMIT"
    INTERNAL_ERROR = "INTERNAL_ERROR"
    SERVICE_UNAVAILABLE = "SERVICE_UNAVAILABLE"
    INVALID_REQUEST = "INVALID_REQUEST"

class ApiResponse:
    """Base response model."""

    def __init__(
        self,
        status: ResponseStatus,
        data: Optional[Dict[str, Any]] = None,
        error: Optional[Dict[str, Any]] = None,
        metadata: Optional[Dict[str, Any]] = None
    ):
        self.status = status
        self.data = data or {}
        self.error = error
        self.metadata = metadata or {
            'timestamp': datetime.utcnow().isoformat(),
            'version': '1.0'
        }

    def to_dict(self) -> Dict:
        """Convert to JSON-serializable dictionary."""
        response = {
            'success': self.status == ResponseStatus.SUCCESS,
            'status': self.status.value,
            'data': self.data,
            'metadata': self.metadata
        }
        if self.error:
            response['error'] = self.error
        return response

class SuccessResponse(ApiResponse):
    """Response for successful requests."""

    def __init__(self, data: Dict[str, Any], metadata: Optional[Dict] = None):
        super().__init__(
            status=ResponseStatus.SUCCESS,
            data=data,
            metadata=metadata
        )

class ErrorResponse(ApiResponse):
    """Response for error requests."""

    def __init__(
        self,
        code: ErrorCode,
        message: str,
        details: Optional[Dict] = None,
        metadata: Optional[Dict] = None
    ):
        error_dict = {
            'code': code.value,
            'message': message,
            'details': details or {}
        }
        super().__init__(
            status=ResponseStatus.ERROR,
            error=error_dict,
            metadata=metadata
        )

class PaginatedResponse(ApiResponse):
    """Response for paginated data."""

    def __init__(
        self,
        items: List[Dict],
        total: int,
        limit: int,
        offset: int,
        metadata: Optional[Dict] = None
    ):
        pagination = {
            'total': total,
            'limit': limit,
            'offset': offset,
            'has_next': (offset + limit) < total
        }

        data = {
            'items': items,
            'pagination': pagination
        }

        combined_metadata = {'pagination': pagination}
        if metadata:
            combined_metadata.update(metadata)

        super().__init__(
            status=ResponseStatus.SUCCESS,
            data=data,
            metadata=combined_metadata
        )
```

### 2.1.2: Create Response Decorator

**File:** Create `/nasdaq_predictor/api/response_decorator.py`

```python
"""
Decorator to standardize all API responses.
Wraps endpoints to ensure consistent response format.
"""

from functools import wraps
from flask import jsonify
from nasdaq_predictor.api.response_models import (
    SuccessResponse, ErrorResponse, ErrorCode
)

def standardize_response(f):
    """
    Decorator to standardize API response format.

    Usage:
        @app.route('/api/endpoint')
        @standardize_response
        def endpoint():
            return {'data': value}  # Returns wrapped response
    """
    @wraps(f)
    def decorated_function(*args, **kwargs):
        try:
            result = f(*args, **kwargs)

            # If result is tuple (data, status_code), unpack it
            if isinstance(result, tuple):
                data, status_code = result
            else:
                data = result
                status_code = 200

            # If already a response object, return as-is
            if isinstance(data, (SuccessResponse, ErrorResponse)):
                return jsonify(data.to_dict()), status_code

            # Wrap in success response
            response = SuccessResponse(data=data)
            return jsonify(response.to_dict()), status_code

        except Exception as e:
            # Catch unexpected errors
            error_response = ErrorResponse(
                code=ErrorCode.INTERNAL_ERROR,
                message=str(e)
            )
            return jsonify(error_response.to_dict()), 500

    return decorated_function
```

### 2.1.3: Apply to All Routes

**Files to Modify:** All route files in `/nasdaq_predictor/api/routes/`

**Pattern:**

```python
# Example modification to prediction_routes.py

from nasdaq_predictor.api.response_decorator import standardize_response
from nasdaq_predictor.api.response_models import ErrorResponse, ErrorCode

@prediction_bp.route('/<ticker>/block', methods=['GET'])
@limiter.limit('100/hour')
@validate_request(PredictionQuerySchema())
@standardize_response  # ADD THIS
def get_block_predictions(ticker):
    """Get 7-block predictions for ticker."""
    try:
        # Implementation...
        predictions = service.get_predictions(ticker)

        return {
            'ticker': ticker,
            'predictions': predictions,
            'count': len(predictions)
        }

    except ValueError as e:
        error = ErrorResponse(
            code=ErrorCode.INVALID_REQUEST,
            message=str(e)
        )
        return error.to_dict(), 400

    except Exception as e:
        error = ErrorResponse(
            code=ErrorCode.INTERNAL_ERROR,
            message=f"Failed to get predictions: {str(e)}"
        )
        return error.to_dict(), 500
```

**Apply to all endpoints in:**
- `prediction_routes.py`
- `market_status_routes.py`
- `historical_data_routes.py`
- `scheduler_metrics_routes.py`
- Any other route files

### 2.1.4: Test Error Responses

**File:** Create `tests/test_api_responses.py`

```python
"""Tests for standardized API responses."""

import pytest
import json
from app import create_app

@pytest.fixture
def client():
    app = create_app()
    app.config['TESTING'] = True
    return app.test_client()

def test_success_response_format(client):
    """Test success response has correct format."""
    response = client.get('/api/predictions/NQ=F/block?interval=1h')

    assert response.status_code in [200, 404]
    data = json.loads(response.data)

    # Check required fields
    assert 'success' in data
    assert 'status' in data
    assert 'data' in data
    assert 'metadata' in data
    assert 'timestamp' in data['metadata']

def test_error_response_format(client):
    """Test error response has correct format."""
    # Request with invalid ticker
    response = client.get('/api/predictions/INVALID/block')

    # Should get either 404 or validation error
    assert response.status_code in [400, 404, 422]
    data = json.loads(response.data)

    assert 'success' in data
    assert data['success'] == False
    assert 'error' in data
    assert 'code' in data['error']
    assert 'message' in data['error']

def test_validation_error_format(client):
    """Test validation error response format."""
    # Request without required parameters
    response = client.get('/api/predictions/NQ=F/block')

    data = json.loads(response.data)
    assert data['success'] == False
    assert 'VALIDATION_ERROR' in data['error']['code']
```

**Success Criteria:**
- ✅ All endpoints return standardized format
- ✅ Success responses include status, data, metadata
- ✅ Error responses include code, message, details
- ✅ Unit tests pass
- ✅ Client can parse all responses consistently

---

## 2️⃣.2 CORS & SECURITY HEADERS

**Priority:** P0 | **Effort:** 2-3 hours | **Impact:** CRITICAL (production security)

### 2.2.1: Add CORS Configuration

**File:** Modify `/nasdaq_predictor/config/app_config.py` or create new file `/nasdaq_predictor/config/cors_config.py`

```python
"""
CORS and security header configuration for different environments.
"""

import os
from typing import Dict, List

class CORSConfig:
    """CORS configuration by environment."""

    # Development - permissive
    DEVELOPMENT = {
        'origins': ['http://localhost:3000', 'http://localhost:5000', 'http://localhost:8080'],
        'methods': ['GET', 'POST', 'PUT', 'DELETE', 'OPTIONS'],
        'allow_headers': ['Content-Type', 'Authorization'],
        'expose_headers': ['X-Total-Count', 'X-RateLimit-Remaining'],
        'supports_credentials': True,
        'max_age': 3600
    }

    # Staging - moderate
    STAGING = {
        'origins': [
            'https://staging.nasdaq-predictor.com',
            'https://dashboard-staging.nasdaq-predictor.com'
        ],
        'methods': ['GET', 'POST', 'PUT', 'DELETE', 'OPTIONS'],
        'allow_headers': ['Content-Type', 'Authorization', 'X-API-Key'],
        'expose_headers': ['X-Total-Count', 'X-RateLimit-Remaining'],
        'supports_credentials': True,
        'max_age': 7200
    }

    # Production - strict
    PRODUCTION = {
        'origins': [
            'https://nasdaq-predictor.com',
            'https://dashboard.nasdaq-predictor.com'
        ],
        'methods': ['GET', 'POST', 'OPTIONS'],
        'allow_headers': ['Content-Type', 'Authorization', 'X-API-Key'],
        'expose_headers': ['X-Total-Count', 'X-RateLimit-Remaining'],
        'supports_credentials': False,
        'max_age': 86400  # 24 hours
    }

    @staticmethod
    def get_config() -> Dict:
        """Get CORS config for current environment."""
        env = os.getenv('FLASK_ENV', 'development')

        if env == 'production':
            return CORSConfig.PRODUCTION
        elif env == 'staging':
            return CORSConfig.STAGING
        else:
            return CORSConfig.DEVELOPMENT

class SecurityHeadersConfig:
    """Security headers for all responses."""

    HEADERS = {
        'Strict-Transport-Security': 'max-age=31536000; includeSubDomains',
        'X-Content-Type-Options': 'nosniff',
        'X-Frame-Options': 'DENY',
        'X-XSS-Protection': '1; mode=block',
        'Content-Security-Policy': (
            "default-src 'self'; "
            "script-src 'self' 'unsafe-inline' cdn.jsdelivr.net; "
            "style-src 'self' 'unsafe-inline' cdn.jsdelivr.net; "
            "img-src 'self' data: https:; "
            "font-src 'self' cdn.jsdelivr.net"
        ),
        'Referrer-Policy': 'strict-origin-when-cross-origin',
        'Permissions-Policy': 'geolocation=(), microphone=(), camera=()'
    }
```

### 2.2.2: Initialize CORS in Flask App

**File:** Modify `/nasdaq_predictor/app.py` (or create in create_app function)

```python
# At top of file
from flask_cors import CORS
from nasdaq_predictor.config.cors_config import CORSConfig, SecurityHeadersConfig

def create_app():
    """Create Flask app with CORS and security headers."""
    app = Flask(__name__)

    # ... existing app setup ...

    # Initialize CORS
    cors_config = CORSConfig.get_config()
    CORS(
        app,
        origins=cors_config['origins'],
        methods=cors_config['methods'],
        allow_headers=cors_config['allow_headers'],
        expose_headers=cors_config['expose_headers'],
        supports_credentials=cors_config['supports_credentials'],
        max_age=cors_config['max_age']
    )

    # Add security headers to all responses
    @app.after_request
    def set_security_headers(response):
        """Add security headers to response."""
        for header, value in SecurityHeadersConfig.HEADERS.items():
            response.headers[header] = value
        return response

    # ... rest of app setup ...

    return app
```

### 2.2.3: Test CORS Configuration

**File:** Create `tests/test_cors.py`

```python
"""Tests for CORS configuration."""

import pytest
from app import create_app

@pytest.fixture
def client():
    app = create_app()
    app.config['TESTING'] = True
    return app.test_client()

def test_cors_headers_present(client):
    """Test that CORS headers are in response."""
    response = client.get('/api/predictions/NQ=F/block')

    # Check CORS headers
    assert 'Access-Control-Allow-Origin' in response.headers or response.status_code in [404, 400]
    assert 'Vary' in response.headers or response.status_code in [404, 400]

def test_security_headers_present(client):
    """Test that security headers are in response."""
    response = client.get('/')

    # Check security headers
    assert 'X-Content-Type-Options' in response.headers
    assert 'X-Frame-Options' in response.headers
    assert 'X-XSS-Protection' in response.headers

def test_cors_preflight(client):
    """Test CORS preflight request."""
    response = client.options(
        '/api/predictions/NQ=F/block',
        headers={
            'Origin': 'http://localhost:3000',
            'Access-Control-Request-Method': 'GET'
        }
    )

    # Should return 200 or 204 for preflight
    assert response.status_code in [200, 204]
```

**Success Criteria:**
- ✅ CORS configuration loaded based on environment
- ✅ All API responses include CORS headers
- ✅ Security headers present in all responses
- ✅ Preflight requests handled correctly
- ✅ Unit tests pass

---

## 🟡 PHASE 3: SCHEDULING & MONITORING (Days 8-11)

### Goal: Implement market-aware scheduling, distributed locking, comprehensive monitoring

---

## 3️⃣.1 MARKET-AWARE SCHEDULING DECORATORS

**Priority:** P1 | **Effort:** 4-6 hours | **Impact:** MEDIUM (resource efficiency)

### 3.1.1: Create Scheduling Decorators

**File:** Create `/nasdaq_predictor/scheduler/decorators.py`

```python
"""
Decorators for scheduled jobs with retry logic, market awareness, and error handling.

Reference: Full implementation in SCHEDULING_JOBS_EXPERT report sections 4-6.
"""

import functools
import time
import logging
from typing import Callable, List
from datetime import datetime

logger = logging.getLogger(__name__)

def with_exponential_backoff(
    max_attempts: int = 3,
    initial_delay_seconds: float = 60,
    backoff_multiplier: float = 2.0,
    max_delay_seconds: float = 3600
):
    """Retry decorator with exponential backoff."""
    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            for attempt in range(1, max_attempts + 1):
                try:
                    logger.info(f"Attempt {attempt}/{max_attempts}: {func.__name__}")
                    start = datetime.utcnow()
                    result = func(*args, **kwargs)
                    duration = (datetime.utcnow() - start).total_seconds()
                    logger.info(f"✓ {func.__name__} succeeded ({duration:.2f}s)")
                    return result

                except Exception as e:
                    if attempt == max_attempts:
                        logger.error(f"✗ {func.__name__} failed after {max_attempts} attempts: {e}")
                        raise

                    delay = min(
                        initial_delay_seconds * (backoff_multiplier ** (attempt - 1)),
                        max_delay_seconds
                    )
                    logger.warning(f"Retrying in {delay}s... ({type(e).__name__}: {e})")
                    time.sleep(delay)

        return wrapper
    return decorator

def market_aware(monitored_tickers: List[str] = None, skip_if_closed: bool = True):
    """Execute job only during trading hours."""
    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            if not monitored_tickers:
                return func(*args, **kwargs)

            from datetime import datetime as dt
            import pytz
            from nasdaq_predictor.utils.market_status import get_market_status

            current_time = dt.now(pytz.UTC)
            market_statuses = {}
            any_open = False

            for ticker in monitored_tickers:
                status = get_market_status(ticker, current_time)
                market_statuses[ticker] = status.status
                if status.status == 'OPEN':
                    any_open = True

            logger.info(f"Market check for {func.__name__}: {market_statuses}")

            if not any_open:
                if skip_if_closed:
                    logger.info(f"Skipping {func.__name__}: markets closed")
                    return {'skipped': True, 'reason': 'market_closed'}
                else:
                    raise RuntimeError(f"Cannot execute {func.__name__}: markets closed")

            return func(*args, **kwargs)

        return wrapper
    return decorator
```

### 3.1.2: Update Job Definitions

**File:** Modify `/nasdaq_predictor/scheduler/jobs.py`

Add imports at top:
```python
from nasdaq_predictor.scheduler.decorators import (
    with_exponential_backoff,
    market_aware
)
```

Update job functions with decorators:
```python
@_require_app_context
@market_aware(monitored_tickers=['NQ=F', 'ES=F'], skip_if_closed=True)
@with_exponential_backoff(max_attempts=3, initial_delay_seconds=60)
@tracking_service.track_job_execution('market_data_sync', 'Market Data Sync')
def fetch_and_store_market_data():
    """Market data sync with retry and market awareness."""
    logger.info("=" * 80)
    logger.info(f"JOB: Market Data Sync started at {datetime.utcnow().isoformat()}")

    sync_service = current_app.container.resolve('data_sync_service')
    results = sync_service.sync_all_tickers()

    logger.info(f"✓ Synced: {results}")
    return results

@_require_app_context
@market_aware(monitored_tickers=['NQ=F', 'ES=F'], skip_if_closed=True)
@with_exponential_backoff(max_attempts=3, initial_delay_seconds=60)
@tracking_service.track_job_execution('prediction_calculation', 'Prediction Calculation')
def calculate_and_store_predictions():
    """Calculate predictions with retry and market awareness."""
    logger.info("=" * 80)
    logger.info(f"JOB: Prediction Calculation started")

    prediction_service = current_app.container.resolve('block_prediction_service')
    results = prediction_service.calculate_all_predictions()

    logger.info(f"✓ Predictions calculated: {len(results)} tickers")
    return results
```

Apply to all job functions: `verify_prediction_accuracy()`, `generate_hourly_predictions()`, `verify_intraday_predictions()`

**Success Criteria:**
- ✅ Decorators applied to all data/market jobs
- ✅ Jobs retry on transient errors
- ✅ Jobs skip when markets closed
- ✅ Cleanup jobs always run (no market awareness)
- ✅ Logs show decorator activity

---

## 3️⃣.2 CRON EXPRESSION UPDATE WITH SECONDS PRECISION

**Priority:** P1 | **Effort:** 2-3 hours | **Impact:** MEDIUM (timing precision)

### 3.2.1: Update Scheduler Job Registration

**File:** Modify `/nasdaq_predictor/scheduler/__init__.py`

Find the `_register_jobs()` function and update cron expressions:

```python
def _register_jobs(scheduler: BackgroundScheduler):
    """Register all scheduled jobs with market-aware cron expressions."""

    # ===== MARKET DATA SYNC (Every 90 seconds) =====
    scheduler.add_job(
        fetch_and_store_market_data,
        'interval',
        seconds=90,
        id='market_data_sync',
        name='Market Data Sync',
        replace_existing=True,
        max_instances=1,
        coalesce=True
    )

    # ===== PREDICTION CALCULATION (Every 15 min, with seconds precision) =====
    # Runs at :42 and :51 seconds past :08, :23, :38, :53 minutes
    # During trading hours (Mon-Fri, 13:30-20:00 UTC = 9:30 AM - 4 PM ET)
    scheduler.add_job(
        calculate_and_store_predictions,
        'cron',
        day_of_week='0-4',      # Monday-Friday
        hour='13-19',           # 13:30-19:59 UTC
        minute='8,23,38,53',    # Every ~15 minutes
        second='42,51',         # Specific seconds for precision
        id='prediction_calculation',
        name='Prediction Calculation',
        replace_existing=True,
        max_instances=1,
        coalesce=True
    )
    logger.info("Registered: prediction_calculation at :08/:23/:38/:53:42/:51 UTC")

    # ===== VERIFICATION (5-min offset after predictions) =====
    scheduler.add_job(
        verify_prediction_accuracy,
        'cron',
        day_of_week='0-4',
        hour='13-19',
        minute='13,28,43,58',   # 5-min after predictions
        second='0',
        id='verification',
        name='Prediction Verification',
        replace_existing=True,
        max_instances=1,
        coalesce=True
    )

    # ===== HOURLY PREDICTIONS =====
    scheduler.add_job(
        generate_hourly_predictions,
        'cron',
        day_of_week='0-4',
        hour='13-19',
        minute='13,28,43,58',
        second='0',
        id='hourly_predictions',
        name='Hourly Intraday Predictions',
        replace_existing=True,
        max_instances=1,
        coalesce=True
    )

    # ===== INTRADAY VERIFICATION (10-min offset) =====
    scheduler.add_job(
        verify_intraday_predictions,
        'cron',
        day_of_week='0-4',
        hour='13-19',
        minute='18,33,48,3',    # 10-min offset
        second='0',
        id='intraday_verification',
        name='Intraday Prediction Verification',
        replace_existing=True,
        max_instances=1,
        coalesce=True
    )

    # ===== CLEANUP (Daily, off-peak) =====
    scheduler.add_job(
        cleanup_old_data,
        'cron',
        hour=2,
        minute=0,
        second=0,
        id='data_cleanup',
        name='Data Cleanup',
        replace_existing=True,
        max_instances=1
    )

    # ===== FIBONACCI PIVOTS (Daily) =====
    scheduler.add_job(
        calculate_fibonacci_pivots,
        'cron',
        hour=0,
        minute=5,
        second=0,
        id='fibonacci_pivots',
        name='Fibonacci Pivot Calculation',
        replace_existing=True,
        max_instances=1
    )

    logger.info("✓ All jobs registered with market-aware cron expressions")
```

**Success Criteria:**
- ✅ All cron expressions updated with seconds precision
- ✅ Market hours properly configured (13:30-20:00 UTC = 9:30 AM - 4 PM ET)
- ✅ Jobs execute at correct times
- ✅ Logs show job execution with proper intervals

---

## 3️⃣.3 MONITORING ENDPOINTS

**Priority:** P1 | **Effort:** 4-6 hours | **Impact:** MEDIUM (operational visibility)

### 3.3.1: Create Monitoring Routes

**File:** Modify `/nasdaq_predictor/api/routes/scheduler_metrics_routes.py` or create new

```python
"""
Scheduler monitoring and health check endpoints.
"""

from flask import Blueprint, jsonify, current_app
from datetime import datetime
import logging

scheduler_bp = Blueprint('scheduler', __name__, url_prefix='/api/scheduler')
logger = logging.getLogger(__name__)

@scheduler_bp.route('/metrics', methods=['GET'])
def get_scheduler_metrics():
    """
    Get detailed scheduler metrics for all jobs.

    Response format:
    {
        'success': True,
        'data': {
            'timestamp': '2025-11-15T...',
            'scheduler': {
                'running': True,
                'jobs_count': 7
            },
            'jobs': {
                'market_data_sync': {
                    'name': 'Market Data Sync',
                    'status': 'SUCCESS',
                    'success_rate': 99.5,
                    'avg_duration_s': 5.2,
                    'last_execution': '2025-11-15T14:30:00Z',
                    'total_executions': 200,
                    'failed_executions': 1,
                    'last_error': null
                },
                ...
            }
        },
        'metadata': {'timestamp': '...'}
    }
    """
    try:
        from nasdaq_predictor.services.scheduler_job_tracking_service import (
            SchedulerJobTrackingService
        )

        tracking_service = current_app.container.resolve('scheduler_job_tracking_service')
        scheduler = current_app.scheduler

        # Get all jobs from scheduler
        jobs = scheduler.get_jobs()

        metrics = {
            'timestamp': datetime.utcnow().isoformat(),
            'scheduler': {
                'running': scheduler.running,
                'jobs_count': len(jobs)
            },
            'jobs': {}
        }

        # Collect metrics for each job
        for job in jobs:
            job_metrics = tracking_service.get_job_status(job.id)

            metrics['jobs'][job.id] = {
                'name': job_metrics.get('job_name'),
                'status': job_metrics.get('status'),
                'success_rate': job_metrics.get('success_rate'),
                'avg_duration_s': job_metrics.get('avg_duration'),
                'last_execution': job_metrics.get('last_execution_at'),
                'total_executions': job_metrics.get('total_executions'),
                'failed_executions': job_metrics.get('failed_executions'),
                'last_error': job_metrics.get('last_error_message'),
                'next_run': job.next_run_time.isoformat() if job.next_run_time else None
            }

        return jsonify({
            'success': True,
            'data': metrics
        }), 200

    except Exception as e:
        logger.error(f"Error getting scheduler metrics: {e}", exc_info=True)
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@scheduler_bp.route('/health', methods=['GET'])
def scheduler_health():
    """
    Health check for scheduler system.

    Returns degraded/unhealthy if jobs failing or not executing.
    """
    try:
        from nasdaq_predictor.services.scheduler_job_tracking_service import (
            SchedulerJobTrackingService
        )

        tracking_service = current_app.container.resolve('scheduler_job_tracking_service')
        scheduler = current_app.scheduler

        if not scheduler or not scheduler.running:
            return jsonify({
                'success': False,
                'health': 'unhealthy',
                'error': 'Scheduler not running'
            }), 503

        # Check for failing jobs (2+ consecutive failures)
        metrics = tracking_service.get_all_job_statuses()
        failing_jobs = []

        for job_id, job_status in metrics.get('jobs', {}).items():
            if job_status.get('failed_executions', 0) >= 2:
                failing_jobs.append({
                    'job_id': job_id,
                    'failures': job_status.get('failed_executions'),
                    'error': job_status.get('last_error_message')
                })

        # Determine overall health
        if failing_jobs:
            health = 'degraded'
        else:
            health = 'healthy'

        return jsonify({
            'success': True,
            'health': health,
            'scheduler_running': scheduler.running,
            'jobs_count': len(scheduler.get_jobs()),
            'failing_jobs': failing_jobs,
            'timestamp': datetime.utcnow().isoformat()
        }), 200

    except Exception as e:
        logger.error(f"Scheduler health check error: {e}", exc_info=True)
        return jsonify({
            'success': False,
            'health': 'unknown',
            'error': str(e)
        }), 500

@scheduler_bp.route('/jobs/<job_id>/status', methods=['GET'])
def job_status(job_id):
    """Get status for specific job."""
    try:
        tracking_service = current_app.container.resolve('scheduler_job_tracking_service')
        status = tracking_service.get_job_status(job_id)

        if not status:
            return jsonify({
                'success': False,
                'error': f'Job {job_id} not found'
            }), 404

        return jsonify({
            'success': True,
            'data': status
        }), 200

    except Exception as e:
        logger.error(f"Error getting job status: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500
```

### 3.3.2: Register Monitoring Routes

**File:** Modify `/nasdaq_predictor/app.py`

```python
# In create_app() function, add:

from nasdaq_predictor.api.routes.scheduler_metrics_routes import scheduler_bp

def create_app():
    app = Flask(__name__)

    # ... existing setup ...

    # Register monitoring routes
    app.register_blueprint(scheduler_bp)

    return app
```

### 3.3.3: Test Monitoring Endpoints

**File:** Create `tests/test_scheduler_monitoring.py`

```python
"""Tests for scheduler monitoring endpoints."""

import pytest
import json
from app import create_app

@pytest.fixture
def client():
    app = create_app()
    app.config['TESTING'] = True
    return app.test_client()

def test_metrics_endpoint(client):
    """Test scheduler metrics endpoint returns data."""
    response = client.get('/api/scheduler/metrics')

    # Could be 200 or 500 if scheduler not initialized in test
    assert response.status_code in [200, 500]
    data = json.loads(response.data)

    if response.status_code == 200:
        assert 'success' in data
        assert 'data' in data
        assert 'jobs' in data['data']

def test_health_endpoint(client):
    """Test scheduler health endpoint."""
    response = client.get('/api/scheduler/health')

    assert response.status_code in [200, 503]
    data = json.loads(response.data)

    assert 'health' in data
    assert data['health'] in ['healthy', 'degraded', 'unhealthy', 'unknown']
```

**Success Criteria:**
- ✅ `/api/scheduler/metrics` endpoint returns job metrics
- ✅ `/api/scheduler/health` endpoint shows system health
- ✅ Endpoints include execution counts, timing, errors
- ✅ Unit tests pass
- ✅ Can detect failing jobs from metrics

---

## 🟡 PHASE 4: TESTING INFRASTRUCTURE (Days 12-16)

### Goal: Establish comprehensive testing framework

**Note:** This is a large phase. Reference `COMPREHENSIVE_TESTING_STRATEGY.md` for detailed test cases.

---

## 4️⃣.1 TEST SETUP & FIXTURES

**Priority:** P1 | **Effort:** 8-10 hours | **Impact:** VERY HIGH (prevents bugs)

### 4.1.1: Create Test Fixtures

**File:** Modify `/tests/conftest.py`

```python
"""
Pytest configuration and shared fixtures for all tests.
"""

import pytest
from datetime import datetime, timedelta
import pytz
from unittest.mock import Mock, MagicMock

# ===== FIXTURES FOR MARKET DATA =====

@pytest.fixture
def sample_ohlc_bar():
    """Sample valid OHLC bar."""
    return {
        'open': 100.0,
        'high': 105.0,
        'low': 99.0,
        'close': 103.0,
        'volume': 1000000,
        'timestamp': datetime.now(pytz.UTC)
    }

@pytest.fixture
def sample_ohlc_bars_24h():
    """24 hours of OHLC data (intraday)."""
    bars = []
    base_time = datetime.now(pytz.UTC).replace(hour=13, minute=30)  # Market open ET
    price = 100.0

    for i in range(24):
        bar_time = base_time + timedelta(hours=i)
        bars.append({
            'open': price,
            'high': price * 1.02,
            'low': price * 0.98,
            'close': price * 1.01,
            'volume': 1000000 + i * 10000,
            'timestamp': bar_time
        })
        price = price * 1.01

    return bars

@pytest.fixture
def mock_yfinance_normal():
    """Mock yfinance with normal market data."""
    mock = MagicMock()
    mock.download.return_value = Mock(
        iterrows=lambda: [
            (0, Mock(Open=100.0, High=105.0, Low=99.0, Close=103.0, Volume=1000000))
        ]
    )
    return mock

@pytest.fixture
def mock_yfinance_error():
    """Mock yfinance returning error."""
    mock = MagicMock()
    mock.download.side_effect = Exception("Connection timeout")
    return mock

# ===== FIXTURES FOR DATABASE =====

@pytest.fixture
def mock_supabase_client():
    """Mock Supabase client."""
    mock = MagicMock()
    mock.table.return_value.select.return_value.execute.return_value = Mock(data=[])
    mock.table.return_value.insert.return_value.execute.return_value = Mock(data=[{'id': '123'}])
    return mock

# ===== FIXTURES FOR SERVICES =====

@pytest.fixture
def mock_data_sync_service():
    """Mock data sync service."""
    mock = MagicMock()
    mock.sync_all_tickers.return_value = {
        'NQ=F': 1440,
        'ES=F': 1440,
        '^FTSE': 1440
    }
    return mock

@pytest.fixture
def mock_prediction_service():
    """Mock prediction service."""
    mock = MagicMock()
    mock.calculate_all_predictions.return_value = [
        {
            'ticker': 'NQ=F',
            'blocks': [
                {'block': 1, 'direction': 'UP', 'confidence': 0.75},
                {'block': 2, 'direction': 'DOWN', 'confidence': 0.65},
            ]
        }
    ]
    return mock

# ===== FIXTURES FOR APP CONTEXT =====

@pytest.fixture
def app():
    """Create Flask app for testing."""
    from app import create_app

    app = create_app()
    app.config['TESTING'] = True

    with app.app_context():
        yield app

@pytest.fixture
def client(app):
    """Flask test client."""
    return app.test_client()

@pytest.fixture
def app_context(app):
    """Flask app context."""
    with app.app_context():
        yield
```

### 4.1.2: Create Test Utilities

**File:** Create `/tests/test_utils.py`

```python
"""
Utility functions for testing.
"""

from datetime import datetime
import pytz

def create_test_bar(open_price=100.0, high=105.0, low=99.0, close=103.0, volume=1000000, hours_ago=0):
    """Create a test OHLC bar."""
    base_time = datetime.now(pytz.UTC)
    bar_time = base_time.replace(hour=base_time.hour - hours_ago)

    return {
        'open': open_price,
        'high': high,
        'low': low,
        'close': close,
        'volume': volume,
        'timestamp': bar_time
    }

def assert_valid_response(response, status_code=200):
    """Assert response has valid format."""
    assert response.status_code == status_code

    data = response.get_json()
    assert 'success' in data
    assert 'metadata' in data

    if status_code == 200:
        assert data['success'] == True
        assert 'data' in data
    else:
        assert data['success'] == False
        assert 'error' in data

def assert_error_response(response, error_code, status_code):
    """Assert response is properly formatted error."""
    assert response.status_code == status_code
    data = response.get_json()
    assert data['success'] == False
    assert data['error']['code'] == error_code
```

**Success Criteria:**
- ✅ Fixtures created for all common test scenarios
- ✅ Mocks for yfinance, Supabase, services
- ✅ Flask app and client fixtures available
- ✅ Test utilities reduce boilerplate

---

## 4️⃣.2 CRITICAL PATH TESTS

**Priority:** P1 | **Effort:** 12-16 hours | **Impact:** VERY HIGH

### 4.2.1: Financial Calculation Tests

**File:** Create `/tests/unit/analysis/test_financial_calculations.py`

Reference: `COMPREHENSIVE_TESTING_STRATEGY.md` Section 3 for full test suite

```python
"""Tests for financial calculations and signal processing."""

import pytest
from nasdaq_predictor.analysis.signals import (
    calculate_volatility,
    calculate_early_bias,
    calculate_block_direction
)

class TestVolatilityCalculation:
    """Volatility calculation tests."""

    def test_volatility_normal_conditions(self, sample_ohlc_bars_24h):
        """Test volatility calculation with normal market data."""
        volatility = calculate_volatility(sample_ohlc_bars_24h)

        assert isinstance(volatility, float)
        assert 0 <= volatility <= 100  # Volatility percentage

    def test_volatility_zero_volume(self):
        """Test volatility with zero volume bars."""
        bars = [
            {'open': 100, 'high': 100, 'low': 100, 'close': 100, 'volume': 0},
            {'open': 100, 'high': 100, 'low': 100, 'close': 100, 'volume': 0},
        ]

        volatility = calculate_volatility(bars)
        assert volatility == 0

    def test_volatility_flash_crash(self):
        """Test volatility detection with flash crash."""
        bars = [
            {'open': 100, 'high': 105, 'low': 99, 'close': 103, 'volume': 1000000},
            {'open': 103, 'high': 80, 'low': 80, 'close': 85, 'volume': 500000},  # Flash crash
            {'open': 85, 'high': 102, 'low': 85, 'close': 101, 'volume': 2000000},  # Recovery
        ]

        volatility = calculate_volatility(bars)
        assert volatility > 30  # High volatility during flash crash

class TestBlockDirection:
    """Block direction prediction tests."""

    def test_uptrend_strong(self, sample_ohlc_bars_24h):
        """Test UP direction detection in strong uptrend."""
        direction = calculate_block_direction(sample_ohlc_bars_24h)
        assert direction == 'UP'

    def test_downtrend(self):
        """Test DOWN direction detection in downtrend."""
        bars = []
        price = 100.0

        for i in range(10):
            bars.append({
                'open': price,
                'high': price * 1.01,
                'low': price * 0.99,
                'close': price * 0.99,  # Closing down
                'volume': 1000000
            })
            price *= 0.99  # Downtrend

        direction = calculate_block_direction(bars)
        assert direction == 'DOWN'

    def test_neutral_sideways(self):
        """Test NEUTRAL direction in sideways market."""
        bars = [
            {'open': 100, 'high': 101, 'low': 99, 'close': 100.5, 'volume': 1000000},
            {'open': 100.5, 'high': 101.5, 'low': 99.5, 'close': 100.2, 'volume': 1000000},
            {'open': 100.2, 'high': 101, 'low': 99, 'close': 100.3, 'volume': 1000000},
        ]

        direction = calculate_block_direction(bars)
        assert direction == 'NEUTRAL'
```

For complete test suite, see `COMPREHENSIVE_TESTING_STRATEGY.md`

---

## 4️⃣.3 API ENDPOINT TESTS

**Priority:** P1 | **Effort:** 8-10 hours | **Impact:** HIGH

### 4.3.1: Prediction Endpoint Tests

**File:** Create `/tests/integration/test_api_predictions.py`

```python
"""Tests for prediction API endpoints."""

import pytest
import json
from tests.test_utils import assert_valid_response, assert_error_response

class TestPredictionEndpoints:
    """Prediction API endpoint tests."""

    def test_get_block_predictions_valid(self, client):
        """Test getting block predictions with valid ticker."""
        response = client.get('/api/predictions/NQ=F/block?interval=1h&limit=10')

        assert_valid_response(response, 200)
        data = response.get_json()

        assert 'items' in data['data']
        assert 'pagination' in data['data']
        assert data['data']['pagination']['limit'] == 10

    def test_get_block_predictions_invalid_ticker(self, client):
        """Test error handling for invalid ticker."""
        response = client.get('/api/predictions/INVALID/block')

        assert response.status_code == 400
        data = response.get_json()
        assert data['success'] == False
        assert 'VALIDATION_ERROR' in data['error']['code']

    def test_get_block_predictions_missing_params(self, client):
        """Test validation of required parameters."""
        response = client.get('/api/predictions/block')  # Missing ticker

        assert response.status_code == 400
        data = response.get_json()
        assert 'ticker' in str(data['error'])

    def test_get_block_predictions_rate_limit(self, client):
        """Test rate limiting on endpoint."""
        # Make requests up to limit
        for i in range(101):
            response = client.get(f'/api/predictions/NQ=F/block?_={i}')

            if i < 100:
                assert response.status_code in [200, 404]
            else:
                # 101st request should be rate limited
                assert response.status_code == 429
```

---

## 4️⃣.4 DATABASE TESTS

**Priority:** P1 | **Effort:** 6-8 hours | **Impact:** HIGH

### 4.4.1: Repository Tests

**File:** Create `/tests/unit/database/test_prediction_repository.py`

```python
"""Tests for prediction repository."""

import pytest
from unittest.mock import Mock, patch
from nasdaq_predictor.database.repositories.prediction_repository import PredictionRepository

class TestPredictionRepository:
    """Prediction repository tests."""

    @pytest.fixture
    def repository(self):
        """Create repository with mock client."""
        mock_client = Mock()
        return PredictionRepository(mock_client)

    def test_insert_prediction(self, repository):
        """Test inserting prediction record."""
        prediction = {
            'ticker': 'NQ=F',
            'block': 1,
            'direction': 'UP',
            'confidence': 0.75
        }

        # Mock successful insert
        repository.client.table.return_value.insert.return_value.execute.return_value = Mock(
            data=[{'id': '123', **prediction}]
        )

        result = repository.insert_prediction(prediction)
        assert result is not None
        assert result['id'] == '123'

    def test_get_predictions_by_ticker(self, repository):
        """Test retrieving predictions by ticker."""
        mock_data = [
            {'id': '1', 'ticker': 'NQ=F', 'block': 1, 'direction': 'UP'},
            {'id': '2', 'ticker': 'NQ=F', 'block': 2, 'direction': 'DOWN'},
        ]

        repository.client.table.return_value.select.return_value.eq.return_value.execute.return_value = Mock(
            data=mock_data
        )

        results = repository.get_predictions_by_ticker('NQ=F')
        assert len(results) == 2
        assert all(p['ticker'] == 'NQ=F' for p in results)
```

---

## 🔵 PHASE 5: PERFORMANCE OPTIMIZATION (Days 17-22)

### Goal: Optimize database queries, caching, data fetching

Reference: `DATABASE_REVIEW_EXECUTIVE_SUMMARY.txt` and `YAHOO_FINANCE_REVIEW_SUMMARY.txt`

---

## 5️⃣.1 DATABASE OPTIMIZATION

**Priority:** P2 | **Effort:** 16-20 hours | **Impact:** VERY HIGH (5-10x speedup)

### 5.1.1: Add Database Indexes

**File:** Create `/scripts/add_database_indexes.sql`

```sql
-- Add missing indexes for common queries

-- Market data table indexes
CREATE INDEX IF NOT EXISTS idx_market_data_ticker_timestamp
ON market_data(ticker, timestamp DESC);

CREATE INDEX IF NOT EXISTS idx_market_data_ticker_interval
ON market_data(ticker, interval, timestamp DESC);

-- Prediction table indexes
CREATE INDEX IF NOT EXISTS idx_predictions_ticker_timestamp
ON predictions(ticker, created_at DESC);

CREATE INDEX IF NOT EXISTS idx_predictions_block_confidence
ON predictions(block, confidence DESC);

-- Reference levels indexes
CREATE INDEX IF NOT EXISTS idx_reference_levels_ticker
ON reference_levels(ticker, level_type);

-- Scheduler job execution indexes
CREATE INDEX IF NOT EXISTS idx_job_execution_status
ON scheduler_job_execution(job_id, status, created_at DESC);

CREATE INDEX IF NOT EXISTS idx_job_execution_error
ON scheduler_job_execution(error_message) WHERE status = 'FAILURE';
```

**Apply to database:**
```bash
# Connect to Supabase and run:
psql postgresql://[user]:[password]@[host]/[database] < /scripts/add_database_indexes.sql
```

### 5.1.2: Implement Caching Layer

**File:** Create `/nasdaq_predictor/services/cache_service.py` (if not exists)

```python
"""
Caching service for frequently accessed data.
Uses Redis for distributed caching.
"""

import redis
import json
from typing import Optional, Any
from datetime import timedelta
import logging

logger = logging.getLogger(__name__)

class CacheService:
    """Redis-backed caching service."""

    def __init__(self, redis_url: str = 'redis://localhost:6379'):
        self.redis = redis.from_url(redis_url)
        self.hit_count = 0
        self.miss_count = 0

    def get(self, key: str) -> Optional[Any]:
        """Get value from cache."""
        try:
            data = self.redis.get(key)
            if data:
                self.hit_count += 1
                logger.debug(f"Cache HIT: {key}")
                return json.loads(data)
            else:
                self.miss_count += 1
                logger.debug(f"Cache MISS: {key}")
                return None
        except Exception as e:
            logger.error(f"Cache get error: {e}")
            return None

    def set(self, key: str, value: Any, expire: Optional[timedelta] = None) -> bool:
        """Set value in cache."""
        try:
            data = json.dumps(value)
            if expire:
                self.redis.setex(key, expire, data)
            else:
                self.redis.set(key, data)
            logger.debug(f"Cache SET: {key}")
            return True
        except Exception as e:
            logger.error(f"Cache set error: {e}")
            return False

    def delete(self, key: str) -> bool:
        """Delete value from cache."""
        try:
            self.redis.delete(key)
            logger.debug(f"Cache DELETE: {key}")
            return True
        except Exception as e:
            logger.error(f"Cache delete error: {e}")
            return False

    def clear_pattern(self, pattern: str) -> int:
        """Clear all keys matching pattern."""
        try:
            keys = self.redis.keys(pattern)
            if keys:
                return self.redis.delete(*keys)
            return 0
        except Exception as e:
            logger.error(f"Cache clear error: {e}")
            return 0

    def get_hit_rate(self) -> float:
        """Get cache hit rate percentage."""
        total = self.hit_count + self.miss_count
        if total == 0:
            return 0.0
        return (self.hit_count / total) * 100
```

### 5.1.3: Use Caching in Services

**File:** Modify prediction/data services to use cache

```python
# Example in block_prediction_service.py

def get_block_predictions(self, ticker: str, hours: int = 24):
    """Get block predictions with caching."""
    cache_key = f"predictions:{ticker}:{hours}h"

    # Try cache first
    cached = self.cache_service.get(cache_key)
    if cached:
        return cached

    # Fetch from database
    predictions = self.repository.get_predictions(ticker, hours)

    # Store in cache for 1 hour
    self.cache_service.set(
        cache_key,
        predictions,
        expire=timedelta(hours=1)
    )

    return predictions
```

---

## 5️⃣.2 CONCURRENT DATA FETCHING

**Priority:** P2 | **Effort:** 4-6 hours | **Impact:** MEDIUM (3x faster sync)

### 5.2.1: Implement Concurrent Ticker Fetching

**File:** Modify `/nasdaq_predictor/services/data_fetcher_service.py`

```python
"""
Enhanced data fetcher with concurrent multi-ticker support.
"""

import asyncio
from concurrent.futures import ThreadPoolExecutor
import logging

logger = logging.getLogger(__name__)

class ConcurrentDataFetcherService:
    """Fetch data for multiple tickers concurrently."""

    def __init__(self, max_workers: int = 3):
        self.executor = ThreadPoolExecutor(max_workers=max_workers)
        self.max_workers = max_workers

    def sync_all_tickers(self, tickers: list = None) -> dict:
        """Sync market data for all tickers concurrently."""
        if not tickers:
            tickers = ['NQ=F', 'ES=F', '^FTSE']

        logger.info(f"Starting concurrent sync for {len(tickers)} tickers")
        start_time = datetime.utcnow()

        # Submit all fetch tasks
        futures = {
            ticker: self.executor.submit(self._fetch_ticker, ticker)
            for ticker in tickers
        }

        results = {}
        errors = {}

        # Collect results as they complete
        for ticker, future in futures.items():
            try:
                result = future.result(timeout=30)  # 30s timeout per ticker
                results[ticker] = result
                logger.info(f"✓ {ticker}: {result} records")
            except Exception as e:
                errors[ticker] = str(e)
                logger.error(f"✗ {ticker}: {e}")

        duration = (datetime.utcnow() - start_time).total_seconds()
        logger.info(f"Concurrent sync completed in {duration:.2f}s")

        return {
            'success': len(errors) == 0,
            'results': results,
            'errors': errors,
            'duration_seconds': duration
        }

    def _fetch_ticker(self, ticker: str) -> int:
        """Fetch data for single ticker."""
        logger.info(f"Fetching {ticker}...")
        # Actual fetch logic...
        return 1440  # Return record count
```

---

## 🟣 PHASE 6: UI/UX MODERNIZATION (Days 23-28)

### Goal: Mobile-responsive dashboard, auto-refresh, advanced filtering

Reference: `UI_UX_REVIEW_REPORT.md`

---

## 6️⃣.1 BOOTSTRAP 5 MODERNIZATION

**Priority:** P2 | **Effort:** 20-24 hours | **Impact:** MEDIUM (improved UX)

**Key Tasks (Reference UI_UX_REVIEW_REPORT.md sections 6-7):**

1. Update base template to Bootstrap 5
2. Create responsive grid layout
3. Implement mobile navigation (bottom nav)
4. Add dark mode toggle
5. Create reusable card components
6. Implement confidence score visualization
7. Add performance badges

---

## 6️⃣.2 AUTO-REFRESH MECHANISM

**Priority:** P2 | **Effort:** 6-8 hours | **Impact:** MEDIUM

Create `/static/js/dashboard-auto-refresh.js` with:
- Graceful data refresh every 60s
- Error recovery with exponential backoff
- Partial DOM updates (not full re-render)
- Graceful degradation if API unavailable

---

## 6️⃣.3 ADVANCED FILTERING

**Priority:** P2 | **Effort:** 8-10 hours | **Impact:** LOW

Create filter system for:
- Multiple ticker selection
- Date range filtering
- Confidence threshold filtering
- Direction filter (UP/DOWN/NEUTRAL)
- localStorage persistence

---

## ✅ PHASE 7: VALIDATION & POLISH (Ongoing)

### Task 7.1: Run Full Test Suite
```bash
pytest tests/ -v --cov=nasdaq_predictor --cov-report=html
```

### Task 7.2: Code Quality Checks
```bash
black nasdaq_predictor/
flake8 nasdaq_predictor/
mypy nasdaq_predictor/ --config-file mypy.ini
```

### Task 7.3: Create Deployment Checklist
- [ ] All tests passing
- [ ] Code coverage >= 90%
- [ ] No security vulnerabilities
- [ ] Database migrations tested
- [ ] Environment variables configured
- [ ] Monitoring endpoints verified
- [ ] Rate limiting configured
- [ ] CORS properly set for environment
- [ ] Backup procedures documented
- [ ] Rollback plan prepared

---

## 📊 IMPLEMENTATION TRACKING

Use this template to track progress:

```markdown
# Implementation Progress

## Phase 0: Setup ✅
- [x] Environment verification
- [x] Review reports
- [x] Backup state

## Phase 1: Critical Foundations
- [ ] DI Container fixes (Task 1.1)
- [ ] Rate Limiting (Task 1.2)
- [ ] Input Validation (Task 1.3)
- [ ] Data Quality Validation (Task 1.4)

## Phase 2: API & Error Handling
- [ ] Standardized Responses (Task 2.1)
- [ ] CORS Configuration (Task 2.2)

## Phase 3: Scheduling & Monitoring
- [ ] Market-Aware Decorators (Task 3.1)
- [ ] Cron Expressions (Task 3.2)
- [ ] Monitoring Endpoints (Task 3.3)

... [continue for all phases]
```

---

## 🆘 TROUBLESHOOTING

| Issue | Solution |
|-------|----------|
| Import errors after changes | `pip install -e .` and `python -m pytest --collect-only` |
| Database migration fails | Check Supabase connection, verify SQL syntax |
| Rate limiting not working | Ensure Redis running: `redis-cli ping` |
| Tests failing after changes | Run `pytest tests/ -v` to see specific failures |
| Scheduler jobs not executing | Check logs: `tail -f app.log \| grep scheduler` |

---

## ✅ SUCCESS CRITERIA

### Phase 1 Complete When:
- ✅ All services resolve from DI container
- ✅ API rate limiting active and enforced
- ✅ All endpoints validate input
- ✅ No corrupt data in database
- ✅ CORS headers present on all responses

### Phase 2 Complete When:
- ✅ All responses follow standard format
- ✅ All errors have consistent structure
- ✅ Security headers configured
- ✅ CORS working for environment

### Phase 3 Complete When:
- ✅ Market-aware decorators applied to market jobs
- ✅ Cron expressions execute at correct times
- ✅ Monitoring endpoints return metrics
- ✅ Health check detects failing jobs

### Full Implementation Complete When:
- ✅ All phases 1-7 complete
- ✅ 90%+ test coverage
- ✅ 0 critical security issues
- ✅ Performance benchmarks met
- ✅ Production deployment successful

---

## 📞 NEXT STEPS FOR AGENT

1. **Read and understand** this entire document
2. **Start with Phase 0** - Setup & validation
3. **Progress through phases sequentially**
4. **Execute each task completely** before moving to next
5. **Run tests after each phase** to validate changes
6. **Commit changes to git** after each task
7. **Update tracking** as you complete tasks

When user says "Read the START_HERE file and begin implementation", you have everything needed to execute systematically.

---

**Last Updated:** 2025-11-15
**Total Phases:** 7
**Estimated Duration:** 8-12 weeks (1 developer, full-time)
**Current Status:** Ready for Implementation
