"""
Rate limiting configuration for API endpoints.
Prevents API abuse and throttling from upstream providers.

Configuration defines rate limits for different endpoint categories:
- Public endpoints: General API access
- Authenticated endpoints: Premium/protected routes
- Internal jobs: Background job execution limits

Supports both in-memory storage (for testing) and Redis-backed storage (production).
"""

import os
import logging
from typing import Dict, Optional

logger = logging.getLogger(__name__)


class RateLimiterConfig:
    """Configuration for different rate limit tiers."""

    # ===== PUBLIC ENDPOINTS (loose limits) =====
    # These are endpoints accessible without authentication
    PUBLIC_LIMITS = {
        'default': '100/hour',        # Default limit for unspecified endpoints
        'dashboard': '50/hour',        # Dashboard endpoint
        'health': '1000/hour',        # Health check (frequently called)
        'scheduler_status': '100/hour' # Scheduler status endpoint
    }

    # ===== AUTHENTICATED ENDPOINTS (stricter limits) =====
    # These endpoints require API key or authentication
    AUTH_LIMITS = {
        'predictions': '500/hour',     # Prediction data endpoints
        'historical': '200/hour',      # Historical data requests
        'data': '1000/hour',          # Market data endpoints
        'market_status': '300/hour'    # Market status endpoints
    }

    # ===== INTERNAL JOBS (very strict - prevent runaway jobs) =====
    # These limits are for internal/background job execution
    INTERNAL_LIMITS = {
        'market_data_sync': '720/day',      # Every 90 seconds = 960/day, but capped at 720
        'predictions': '96/day',             # Every 15 minutes = 96/day
        'verification': '96/day',            # Every 15 minutes = 96/day
        'cleanup': '24/day'                  # Once per hour maximum
    }

    # ===== STORAGE BACKEND CONFIGURATION =====
    # Redis URL for distributed rate limiting
    REDIS_URL = os.getenv('REDIS_URL', 'redis://localhost:6379')

    # Use in-memory storage for testing (when REDIS_URL is not available)
    USE_IN_MEMORY = os.getenv('RATE_LIMITER_IN_MEMORY', 'false').lower() == 'true'

    # Storage backend selection
    STORAGE_URL = REDIS_URL if not USE_IN_MEMORY else None

    # ===== RATE LIMITER BEHAVIOR =====
    # Moving window strategy for better accuracy
    STRATEGY = 'moving-window'

    # Default exemptions (endpoints that should not be rate limited)
    EXEMPT_ENDPOINTS = [
        '/api/health',
        '/health',
        '/',
        '/api/swagger',
        '/api/swagger.json'
    ]

    # Storage configuration
    DEFAULT_LIMITS = ['200/hour']  # Default limit if none specified

    # Key function: use client IP for rate limiting
    KEY_FUNC = 'get_remote_address'

    @staticmethod
    def get_storage_uri() -> Optional[str]:
        """Get the storage URI for rate limiter backend.

        Returns:
            Redis URL for production, None for in-memory storage (testing)
        """
        if RateLimiterConfig.USE_IN_MEMORY:
            logger.info("Rate limiter using in-memory storage (testing mode)")
            return None

        return RateLimiterConfig.STORAGE_URL

    @staticmethod
    def get_limit_for_endpoint(endpoint: str, is_authenticated: bool = False) -> str:
        """Get rate limit string for a specific endpoint.

        Args:
            endpoint: The API endpoint (e.g., 'predictions', 'market_status')
            is_authenticated: Whether the request is authenticated

        Returns:
            Rate limit string (e.g., '100/hour')
        """
        if is_authenticated and endpoint in RateLimiterConfig.AUTH_LIMITS:
            return RateLimiterConfig.AUTH_LIMITS[endpoint]
        elif endpoint in RateLimiterConfig.PUBLIC_LIMITS:
            return RateLimiterConfig.PUBLIC_LIMITS[endpoint]
        else:
            return RateLimiterConfig.PUBLIC_LIMITS.get('default', '100/hour')


class RateLimiterStatus:
    """Helper class to track rate limiter status."""

    def __init__(self):
        """Initialize rate limiter status."""
        self.enabled = True
        self.backend = "redis" if RateLimiterConfig.get_storage_uri() else "memory"
        self.default_limits = RateLimiterConfig.DEFAULT_LIMITS
        self.strategy = RateLimiterConfig.STRATEGY

    def to_dict(self) -> Dict:
        """Convert to dictionary for logging/monitoring."""
        return {
            'enabled': self.enabled,
            'backend': self.backend,
            'strategy': self.strategy,
            'default_limits': self.default_limits
        }


def init_rate_limiter(app):
    """Initialize rate limiter for Flask app.

    Args:
        app: Flask application instance

    Returns:
        Initialized Limiter instance

    Example:
        >>> from flask import Flask
        >>> from nasdaq_predictor.config.rate_limiter_config import init_rate_limiter
        >>> app = Flask(__name__)
        >>> limiter = init_rate_limiter(app)
    """
    try:
        from flask_limiter import Limiter
        from flask_limiter.util import get_remote_address

        # Initialize limiter
        limiter = Limiter(
            app=app,
            key_func=get_remote_address,
            storage_uri=RateLimiterConfig.get_storage_uri(),
            default_limits=RateLimiterConfig.DEFAULT_LIMITS,
            strategy=RateLimiterConfig.STRATEGY,
            in_memory_fallback_enabled=True  # Fallback to in-memory if Redis unavailable
        )

        # Log status
        status = RateLimiterStatus()
        logger.info(f"✓ Rate limiter initialized: {status.to_dict()}")

        return limiter

    except ImportError as e:
        logger.error(f"✗ Failed to import Flask-Limiter: {e}")
        logger.warning("Rate limiting not available - install Flask-Limiter")
        return None
    except Exception as e:
        logger.error(f"✗ Failed to initialize rate limiter: {e}")
        return None
