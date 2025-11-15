# Phase 1 Implementation Guide: Rate Limiting and Error Handling

**Timeline:** Week 1-2
**Priority:** CRITICAL
**Goal:** Prevent API throttling and implement adaptive error handling

---

## File 1: Create Rate Limiter Module

**File Path:** `nasdaq_predictor/data/rate_limiter.py`

```python
"""
Rate limiting and circuit breaker for Yahoo Finance API
Implements token bucket with exponential backoff and circuit breaker pattern
"""

import time
import random
import logging
from typing import Dict, Optional
from enum import Enum

logger = logging.getLogger(__name__)


class RateLimitState(Enum):
    """States for rate limiting"""
    AVAILABLE = "available"
    LIMITED = "limited"
    CIRCUIT_OPEN = "circuit_open"


class APIError(Enum):
    """Error type classification"""
    RATE_LIMITED = "rate_limited"
    TEMPORARY_NETWORK = "temporary_network"
    PERMANENT = "permanent"
    UNKNOWN = "unknown"


def classify_error(status_code: Optional[int], error_msg: str) -> APIError:
    """
    Classify error type based on HTTP status and message
    
    Args:
        status_code: HTTP status code
        error_msg: Error message
    
    Returns:
        APIError type
    """
    if status_code == 429:
        return APIError.RATE_LIMITED
    
    if status_code in [502, 503, 504]:
        return APIError.TEMPORARY_NETWORK
    
    if status_code in [404, 400, 401, 403]:
        return APIError.PERMANENT
    
    if "timeout" in error_msg.lower() or "connection" in error_msg.lower():
        return APIError.TEMPORARY_NETWORK
    
    return APIError.UNKNOWN


class AdaptiveRateLimiter:
    """
    Implements adaptive rate limiting with exponential backoff and circuit breaker
    
    Features:
    - Token bucket for rate limiting
    - Exponential backoff for failures (1s, 2s, 4s, 8s, 16s, 32s, 60s)
    - Circuit breaker pattern (open after 3 failures)
    - Random jitter to prevent thundering herd
    - Per-ticker state tracking
    """
    
    def __init__(
        self,
        min_interval_s: float = 1.0,
        max_backoff_s: float = 60.0,
        circuit_failure_threshold: int = 3,
        circuit_reset_timeout_s: int = 300
    ):
        """
        Initialize rate limiter
        
        Args:
            min_interval_s: Minimum seconds between requests
            max_backoff_s: Maximum backoff seconds
            circuit_failure_threshold: Failures before circuit opens
            circuit_reset_timeout_s: Seconds before circuit resets
        """
        self.min_interval_s = min_interval_s
        self.max_backoff_s = max_backoff_s
        self.circuit_failure_threshold = circuit_failure_threshold
        self.circuit_reset_timeout_s = circuit_reset_timeout_s
        
        # Per-ticker state
        self.last_request_time: Dict[str, float] = {}
        self.consecutive_failures: Dict[str, int] = {}
        self.circuit_open_until: Dict[str, float] = {}
        self.backoff_level: Dict[str, int] = {}
        
        # Statistics for monitoring
        self.stats = {
            'total_requests': 0,
            'successful': 0,
            'rate_limited': 0,
            'network_errors': 0,
            'permanent_errors': 0
        }
    
    def is_available(self, ticker: str) -> bool:
        """
        Check if ticker is available for request
        
        Args:
            ticker: Ticker symbol
        
        Returns:
            True if request can proceed, False if rate-limited
        """
        current_time = time.time()
        
        # Check circuit breaker
        if ticker in self.circuit_open_until:
            if current_time < self.circuit_open_until[ticker]:
                logger.debug(f"Circuit breaker open for {ticker}")
                return False
            else:
                # Reset circuit after timeout
                logger.info(f"Circuit breaker reset for {ticker}")
                del self.circuit_open_until[ticker]
                self.consecutive_failures[ticker] = 0
                self.backoff_level[ticker] = 0
        
        # Check rate limit (token bucket)
        if ticker in self.last_request_time:
            elapsed = current_time - self.last_request_time[ticker]
            required_interval = self._get_required_interval(ticker)
            
            if elapsed < required_interval:
                logger.debug(
                    f"Rate limit for {ticker}: waiting "
                    f"{required_interval - elapsed:.1f}s"
                )
                return False
        
        return True
    
    def wait_if_needed(self, ticker: str):
        """
        Wait if rate limited, blocking until available
        
        Args:
            ticker: Ticker symbol
        """
        while not self.is_available(ticker):
            required = self._get_required_interval(ticker)
            last_time = self.last_request_time.get(ticker, time.time())
            elapsed = time.time() - last_time
            wait_time = required - elapsed
            
            if wait_time > 0:
                logger.info(f"Rate limiting {ticker}, waiting {wait_time:.1f}s")
                time.sleep(min(wait_time, 1.0))  # Sleep in 1s increments
    
    def record_request(self, ticker: str):
        """
        Record that a request was made
        
        Args:
            ticker: Ticker symbol
        """
        self.last_request_time[ticker] = time.time()
        self.stats['total_requests'] += 1
    
    def record_success(self, ticker: str):
        """
        Record successful API call, reset failure counters
        
        Args:
            ticker: Ticker symbol
        """
        self.consecutive_failures[ticker] = 0
        self.backoff_level[ticker] = 0
        self.stats['successful'] += 1
        logger.debug(f"Success for {ticker}, reset backoff")
    
    def record_failure(self, ticker: str, error_type: APIError = APIError.UNKNOWN):
        """
        Record API failure and potentially adjust rate limiting
        
        Args:
            ticker: Ticker symbol
            error_type: Type of error that occurred
        """
        # Update statistics
        if error_type == APIError.RATE_LIMITED:
            self.stats['rate_limited'] += 1
            # Increase backoff level more aggressively for rate limits
            self.backoff_level[ticker] = self.backoff_level.get(ticker, 0) + 2
        elif error_type == APIError.TEMPORARY_NETWORK:
            self.stats['network_errors'] += 1
            self.backoff_level[ticker] = self.backoff_level.get(ticker, 0) + 1
        elif error_type == APIError.PERMANENT:
            self.stats['permanent_errors'] += 1
            # Don't increase backoff for permanent errors
        
        # Increment failure counter
        self.consecutive_failures[ticker] = self.consecutive_failures.get(ticker, 0) + 1
        
        # Open circuit if threshold exceeded
        if self.consecutive_failures[ticker] >= self.circuit_failure_threshold:
            self.circuit_open_until[ticker] = time.time() + self.circuit_reset_timeout_s
            logger.warning(
                f"Circuit breaker opened for {ticker} after "
                f"{self.consecutive_failures[ticker]} consecutive failures"
            )
        else:
            backoff = self._get_required_interval(ticker)
            logger.warning(
                f"Failure for {ticker}: backoff={backoff:.1f}s, "
                f"consecutive={self.consecutive_failures[ticker]}"
            )
    
    def _get_required_interval(self, ticker: str) -> float:
        """
        Calculate required interval based on backoff level
        
        Exponential backoff: 2^level seconds, capped at max_backoff_s
        Includes random jitter to prevent thundering herd
        
        Args:
            ticker: Ticker symbol
        
        Returns:
            Seconds to wait before next request
        """
        backoff_level = self.backoff_level.get(ticker, 0)
        
        # Exponential: 2^level seconds, capped at max_backoff_s
        base_interval = min(2 ** backoff_level, self.max_backoff_s)
        
        # Add jitter: +/- 20%
        jitter = base_interval * 0.2 * random.uniform(-1, 1)
        final_interval = base_interval + jitter
        
        return max(self.min_interval_s, final_interval)
    
    def get_stats(self) -> Dict[str, int]:
        """
        Get rate limiter statistics
        
        Returns:
            Dictionary with stats
        """
        return {
            **self.stats,
            'success_rate': (self.stats['successful'] / self.stats['total_requests'] * 100
                           if self.stats['total_requests'] > 0 else 0)
        }
    
    def reset_all(self):
        """Reset all rate limiter state (use for testing or emergency)"""
        self.last_request_time.clear()
        self.consecutive_failures.clear()
        self.circuit_open_until.clear()
        self.backoff_level.clear()
        logger.warning("Rate limiter state reset")


# Global instance for use throughout app
_rate_limiter: Optional[AdaptiveRateLimiter] = None


def get_rate_limiter() -> AdaptiveRateLimiter:
    """Get or create global rate limiter instance"""
    global _rate_limiter
    if _rate_limiter is None:
        _rate_limiter = AdaptiveRateLimiter()
    return _rate_limiter
```

---

## File 2: Update Fetcher to Use Rate Limiter

**File Path:** `nasdaq_predictor/data/fetcher.py` (MODIFY)

Add to imports:
```python
from .rate_limiter import get_rate_limiter, classify_error
```

Modify `fetch_ticker_data()` method:
```python
def fetch_ticker_data(self, ticker_symbol: str) -> Optional[Dict[str, Any]]:
    """
    Fetch all required data for a ticker symbol with rate limiting
    
    Args:
        ticker_symbol: Ticker symbol to fetch
    
    Returns:
        Dictionary containing all interval data, or None on failure
    """
    rate_limiter = get_rate_limiter()
    
    try:
        # Wait if rate limited
        rate_limiter.wait_if_needed(ticker_symbol)
        rate_limiter.record_request(ticker_symbol)
        
        ticker = yf.Ticker(ticker_symbol)
        
        # Fetch hourly data
        hourly_hist = ticker.history(period=HIST_PERIOD_HOURLY, interval=HIST_INTERVAL_HOURLY)
        if hourly_hist.empty:
            logger.warning(f"No hourly data available for {ticker_symbol}")
            rate_limiter.record_failure(ticker_symbol)
            return None
        
        # Filter to only trading session hours
        hourly_hist = filter_trading_session_data(hourly_hist, ticker_symbol, self.trading_sessions)
        if hourly_hist.empty:
            logger.warning(f"No hourly data in trading session for {ticker_symbol}")
            rate_limiter.record_failure(ticker_symbol)
            return None
        
        # Fetch remaining intervals with rate limiting
        minute_hist = ticker.history(period=HIST_PERIOD_MINUTE, interval=HIST_INTERVAL_MINUTE)
        minute_hist = filter_trading_session_data(minute_hist, ticker_symbol, self.trading_sessions)
        
        # ... similar for other intervals ...
        
        # Record success
        rate_limiter.record_success(ticker_symbol)
        
        return {
            'hourly_hist': hourly_hist,
            'minute_hist': minute_hist,
            # ... other intervals ...
        }
    
    except Exception as e:
        # Extract error code if possible
        error_code = self._extract_http_error_code(e)
        error_type = classify_error(error_code, str(e))
        rate_limiter.record_failure(ticker_symbol, error_type)
        
        logger.error(f"Error fetching data for {ticker_symbol}: {str(e)}", exc_info=True)
        return None

def _extract_http_error_code(self, exception: Exception) -> Optional[int]:
    """Extract HTTP error code from exception"""
    error_str = str(exception)
    # Try to parse HTTP error codes from exception message
    if "429" in error_str:
        return 429
    if "503" in error_str or "502" in error_str:
        return 503
    if "timeout" in error_str.lower():
        return 408  # Request timeout
    return None
```

---

## File 3: Integrate into DataSyncService

**File Path:** `nasdaq_predictor/services/data_sync_service.py` (MODIFY)

Add import:
```python
from ..data.rate_limiter import get_rate_limiter, classify_error, APIError
```

Modify retry logic (lines 128-157):
```python
def sync_ticker_data(self, ticker_id: str, symbol: str) -> Dict[str, Any]:
    """
    Sync market data for a specific ticker with adaptive retry logic.
    
    Uses rate limiter for intelligent backoff on failures.
    """
    logger.info(f"Syncing market data for {symbol}...")
    rate_limiter = get_rate_limiter()
    
    # Fetch data with rate limiting
    max_initial_retries = 2  # Just for initialization, rate limiter handles retries
    
    data = None
    for attempt in range(max_initial_retries):
        try:
            # Wait if rate limited
            rate_limiter.wait_if_needed(symbol)
            rate_limiter.record_request(symbol)
            
            data = self.fetcher.fetch_ticker_data(symbol)
            
            if data:
                rate_limiter.record_success(symbol)
                break
            
            # No data but no error - could be data unavailable
            logger.warning(f"No data from yfinance for {symbol}")
            
        except Exception as e:
            error_type = APIError.UNKNOWN
            if "429" in str(e):
                error_type = APIError.RATE_LIMITED
            elif "timeout" in str(e).lower() or "connection" in str(e).lower():
                error_type = APIError.TEMPORARY_NETWORK
            
            rate_limiter.record_failure(symbol, error_type)
            
            if attempt < max_initial_retries - 1:
                # Rate limiter will handle backoff through wait_if_needed()
                logger.warning(
                    f"Error fetching data for {symbol}: {e}, "
                    f"retrying with adaptive backoff..."
                )
            else:
                raise Exception(
                    f"Failed to fetch data for {symbol} after {max_initial_retries} attempts: {e}"
                )
    
    if not data:
        raise Exception(f"No data returned from yfinance for {symbol}")
    
    # Validate and store data
    # ... rest of method unchanged ...
```

---

## Integration Testing

**File Path:** `tests/unit/data/test_rate_limiter.py` (NEW)

```python
"""Unit tests for rate limiter"""

import time
import pytest
from nasdaq_predictor.data.rate_limiter import (
    AdaptiveRateLimiter,
    APIError,
    classify_error
)


class TestAdaptiveRateLimiter:
    
    def test_rate_limiting_enforces_minimum_interval(self):
        """Rate limiter should enforce minimum interval between requests"""
        limiter = AdaptiveRateLimiter(min_interval_s=0.1)
        
        # First request
        assert limiter.is_available("NQ=F")
        limiter.record_request("NQ=F")
        
        # Immediate second request should be blocked
        assert not limiter.is_available("NQ=F")
        
        # After minimum interval, should be available
        time.sleep(0.15)
        assert limiter.is_available("NQ=F")
    
    def test_exponential_backoff_on_failures(self):
        """Backoff level should increase exponentially on failures"""
        limiter = AdaptiveRateLimiter(min_interval_s=0.01)
        
        # Record failures and check backoff increases
        for i in range(3):
            limiter.record_failure("NQ=F", APIError.RATE_LIMITED)
            expected_backoff_level = (i + 1) * 2  # Rate limit = 2x increment
            assert limiter.backoff_level["NQ=F"] == expected_backoff_level
    
    def test_circuit_breaker_opens_after_threshold(self):
        """Circuit breaker should open after failure threshold"""
        limiter = AdaptiveRateLimiter(circuit_failure_threshold=2)
        
        # First failure
        assert limiter.is_available("NQ=F")
        limiter.record_failure("NQ=F")
        assert limiter.is_available("NQ=F")
        
        # Second failure - circuit should open
        limiter.record_failure("NQ=F")
        assert not limiter.is_available("NQ=F")  # Circuit open
    
    def test_circuit_breaker_resets_after_timeout(self):
        """Circuit breaker should reset after timeout"""
        limiter = AdaptiveRateLimiter(circuit_failure_threshold=2, circuit_reset_timeout_s=0.1)
        
        # Open circuit
        limiter.record_failure("NQ=F")
        limiter.record_failure("NQ=F")
        assert not limiter.is_available("NQ=F")
        
        # Wait for reset
        time.sleep(0.15)
        assert limiter.is_available("NQ=F")
    
    def test_success_resets_backoff_level(self):
        """Successful request should reset backoff level"""
        limiter = AdaptiveRateLimiter()
        
        # Create some backoff
        limiter.record_failure("NQ=F", APIError.RATE_LIMITED)
        assert limiter.backoff_level["NQ=F"] > 0
        
        # Success should reset
        limiter.record_success("NQ=F")
        assert limiter.backoff_level["NQ=F"] == 0
        assert limiter.consecutive_failures["NQ=F"] == 0
    
    def test_error_classification(self):
        """Error classification should work correctly"""
        assert classify_error(429, "") == APIError.RATE_LIMITED
        assert classify_error(502, "") == APIError.TEMPORARY_NETWORK
        assert classify_error(503, "") == APIError.TEMPORARY_NETWORK
        assert classify_error(404, "") == APIError.PERMANENT
        assert classify_error(None, "timeout") == APIError.TEMPORARY_NETWORK
```

---

## Configuration Updates

**File Path:** `nasdaq_predictor/config/database_config.py` (MODIFY)

Add to DatabaseConfig class:
```python
# ========================================================================
# Rate Limiting Settings (for yfinance API throttling protection)
# ========================================================================

# Minimum seconds between API requests
RATE_LIMIT_MIN_INTERVAL_SECONDS: float = float(os.getenv('RATE_LIMIT_MIN_INTERVAL', '1.0'))

# Maximum backoff seconds (cap for exponential backoff)
RATE_LIMIT_MAX_BACKOFF_SECONDS: float = float(os.getenv('RATE_LIMIT_MAX_BACKOFF', '60.0'))

# Consecutive failures before circuit breaker opens
RATE_LIMIT_CIRCUIT_THRESHOLD: int = int(os.getenv('RATE_LIMIT_CIRCUIT_THRESHOLD', '3'))

# Seconds before circuit breaker resets
RATE_LIMIT_CIRCUIT_RESET_SECONDS: int = int(os.getenv('RATE_LIMIT_CIRCUIT_RESET', '300'))

# Enable rate limiting (true in production)
RATE_LIMITING_ENABLED: bool = os.getenv('RATE_LIMITING_ENABLED', 'true').lower() == 'true'
```

Add to .env.example:
```
# Rate Limiting Configuration
RATE_LIMIT_MIN_INTERVAL=1.0              # Minimum seconds between API calls
RATE_LIMIT_MAX_BACKOFF=60.0              # Maximum backoff (prevents infinite waits)
RATE_LIMIT_CIRCUIT_THRESHOLD=3           # Open circuit after 3 failures
RATE_LIMIT_CIRCUIT_RESET=300             # Reset circuit after 5 minutes
RATE_LIMITING_ENABLED=true               # Enable rate limiting in production
```

---

## Deployment Notes

1. **Testing:** Deploy to staging first, monitor for 24 hours
2. **Monitoring:** Watch rate limiter statistics and circuit breaker activations
3. **Rollback:** Keep previous version of data_sync_service.py for quick rollback
4. **Documentation:** Update API usage documentation with rate limit information

---

## Success Criteria

- [ ] No 429 errors logged after 24-hour testing period
- [ ] API success rate > 99%
- [ ] Circuit breaker opens < 1x per week in production
- [ ] Average backoff < 2 seconds under normal conditions
- [ ] Rate limiter statistics available in logs

