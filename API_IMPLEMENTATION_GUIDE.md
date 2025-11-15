# NASDAQ Predictor API - Implementation Guide

## Quick Reference: Step-by-Step Implementation

### Step 1: Add Request ID Support (Day 1-2)

**File:** `nasdaq_predictor/api/handlers/response_handler.py`

```python
import uuid
from flask import request as flask_request

class ResponseHandler:
    """Enhanced with request ID support"""
    
    @staticmethod
    def _get_request_id() -> str:
        """Get or generate request ID from headers"""
        request_id = flask_request.headers.get('X-Request-ID')
        if not request_id:
            request_id = f"req_{uuid.uuid4().hex[:12]}"
        return request_id
    
    # Update all methods to include request_id in meta
    # Add to every response: 'request_id': ResponseHandler._get_request_id()
```

### Step 2: Fix Error Response Consistency (Day 2-3)

**Issues to fix:**

1. Scheduler metrics uses raw `jsonify()` instead of ResponseHandler
   - BEFORE: `return jsonify({'error': str(e)}), 500`
   - AFTER: `return ResponseHandler.error('INTERNAL_ERROR', str(e), 500)`

2. Market aware routes call non-existent `ErrorHandler.bad_request()`
   - BEFORE: `return ErrorHandler.bad_request("Invalid format")`
   - AFTER: `return ResponseHandler.error('VALIDATION_ERROR', 'Invalid format', 400)`

3. Inconsistent error field naming
   - BEFORE: Some use `error_message`, some use `message`
   - AFTER: All use `error.code`, `error.message`, `error.type` structure

### Step 3: Implement Validation Handler (Day 3-4)

**New file:** `nasdaq_predictor/api/handlers/validation_handler.py`

Key functions:
- `validate_ticker(ticker: str) -> str`
- `validate_date(date_str: str) -> datetime`
- `validate_pagination(page: int, page_size: int) -> tuple`
- `validate_hour(hour: int) -> int`
- `validate_job_id(job_id: str) -> str`

Apply to ALL endpoints that accept parameters.

### Step 4: Add Rate Limiting (Day 5-6)

**New file:** `nasdaq_predictor/api/middleware/rate_limiting.py`

```bash
pip install Flask-Limiter redis
```

Configure:
- Free tier: 100 req/hour
- Basic tier: 1000 req/hour  
- Premium tier: 10000 req/hour

### Step 5: Update OpenAPI Specification (Day 7-10)

Split monolithic openapi.yaml:
- `openapi/paths/*.yaml` - Endpoint definitions
- `openapi/components/schemas/*.yaml` - Data models
- `openapi/components/responses/*.yaml` - Response templates

### Step 6: Implement Versioning (Day 11-12)

Create v1 blueprints:
- Move endpoints to `/api/v1/*` paths
- Add deprecation headers
- Plan v2 structure

### Step 7: Add Security Headers (Day 13-14)

Implement CORS and security headers middleware.

---

## Testing Checklist

**Validation Testing:**
- [ ] Invalid ticker format returns 400
- [ ] Invalid date format returns 400
- [ ] Future dates rejected appropriately
- [ ] Pagination limits enforced (max 100)

**Response Format Testing:**
- [ ] All responses include `request_id`
- [ ] All responses include `timestamp`
- [ ] Error responses have standardized structure
- [ ] Pagination responses include pagination metadata

**Rate Limiting Testing:**
- [ ] Rate limit headers present in responses
- [ ] 429 status returned when limit exceeded
- [ ] Different tiers have different limits

**Documentation Testing:**
- [ ] All endpoints documented in OpenAPI
- [ ] Examples accurate and complete
- [ ] Error responses documented
- [ ] Swagger UI loads without errors

---

## Deployment Checklist

**Before Going to Production:**
- [ ] All endpoints have rate limiting configured
- [ ] All endpoints have input validation
- [ ] CORS configured for allowed origins
- [ ] Security headers implemented
- [ ] Request logging enabled
- [ ] Error tracking (Sentry/NewRelic) configured
- [ ] Cache headers set appropriately
- [ ] Database connection pooling configured
- [ ] Monitoring/alerting for 5xx errors
- [ ] Load testing completed
- [ ] Security audit completed

