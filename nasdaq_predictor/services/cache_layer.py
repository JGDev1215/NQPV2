"""
Advanced caching layer for frequently accessed data.

Provides:
- Multi-level caching (memory + Redis)
- Cache invalidation strategies
- Cache statistics and monitoring
- TTL-based automatic expiration

Supports:
- Market data caching
- Prediction caching
- Market status caching
- Statistics caching
"""

import logging
import time
import json
from typing import Any, Optional, Callable, Dict
from datetime import datetime, timedelta
from functools import wraps
import hashlib

logger = logging.getLogger(__name__)


class CacheLevel:
    """Cache levels for multi-tier caching."""
    MEMORY = 'memory'      # In-memory cache (fastest, limited size)
    REDIS = 'redis'        # Redis cache (shared, persistent)
    DATABASE = 'database'  # Database (slowest, source of truth)


class CacheConfig:
    """Cache configuration for different data types."""

    # Market data cache (frequently accessed, changes often)
    MARKET_DATA = {
        'ttl': 300,  # 5 minutes
        'max_size': 1000,
        'invalidate_on': ['data_sync']
    }

    # Predictions cache (less frequent updates)
    PREDICTIONS = {
        'ttl': 3600,  # 1 hour
        'max_size': 500,
        'invalidate_on': ['prediction_calculation']
    }

    # Market status cache (rarely changes during market hours)
    MARKET_STATUS = {
        'ttl': 600,  # 10 minutes
        'max_size': 100,
        'invalidate_on': ['market_status_change']
    }

    # Statistics cache (stable data)
    STATISTICS = {
        'ttl': 7200,  # 2 hours
        'max_size': 200,
        'invalidate_on': []
    }


class MemoryCache:
    """Simple in-memory cache with TTL and size limits."""

    def __init__(self, max_size: int = 1000):
        """Initialize memory cache.

        Args:
            max_size: Maximum number of items to store
        """
        self.max_size = max_size
        self._cache: Dict[str, Dict[str, Any]] = {}
        self._hits = 0
        self._misses = 0

    def get(self, key: str) -> Optional[Any]:
        """Get value from cache.

        Args:
            key: Cache key

        Returns:
            Cached value or None if not found/expired
        """
        if key not in self._cache:
            self._misses += 1
            return None

        entry = self._cache[key]

        # Check expiration
        if entry['expires_at'] < time.time():
            del self._cache[key]
            self._misses += 1
            return None

        self._hits += 1
        return entry['value']

    def set(self, key: str, value: Any, ttl: int = 3600):
        """Set value in cache.

        Args:
            key: Cache key
            value: Value to cache
            ttl: Time-to-live in seconds
        """
        # Evict oldest entry if at max size
        if len(self._cache) >= self.max_size:
            oldest_key = min(
                self._cache.keys(),
                key=lambda k: self._cache[k]['created_at']
            )
            del self._cache[oldest_key]
            logger.debug(f"Evicted cache entry: {oldest_key}")

        self._cache[key] = {
            'value': value,
            'created_at': time.time(),
            'expires_at': time.time() + ttl
        }

    def delete(self, key: str):
        """Delete cache entry.

        Args:
            key: Cache key
        """
        if key in self._cache:
            del self._cache[key]

    def clear(self):
        """Clear all cache entries."""
        self._cache.clear()
        self._hits = 0
        self._misses = 0

    def get_stats(self) -> Dict[str, Any]:
        """Get cache statistics.

        Returns:
            Cache hit/miss statistics
        """
        total = self._hits + self._misses
        hit_rate = (self._hits / total * 100) if total > 0 else 0

        return {
            'size': len(self._cache),
            'max_size': self.max_size,
            'hits': self._hits,
            'misses': self._misses,
            'total': total,
            'hit_rate': hit_rate
        }


class RedisCache:
    """Redis-backed cache for distributed caching."""

    def __init__(self, redis_client=None):
        """Initialize Redis cache.

        Args:
            redis_client: Redis client instance (optional)
        """
        self.client = redis_client
        self.available = redis_client is not None
        self._hits = 0
        self._misses = 0

    def get(self, key: str) -> Optional[Any]:
        """Get value from Redis cache.

        Args:
            key: Cache key

        Returns:
            Cached value or None if not found
        """
        if not self.available:
            return None

        try:
            value = self.client.get(key)
            if value is None:
                self._misses += 1
                return None

            self._hits += 1
            return json.loads(value)

        except Exception as e:
            logger.error(f"Redis get error: {e}")
            self._misses += 1
            return None

    def set(self, key: str, value: Any, ttl: int = 3600):
        """Set value in Redis cache.

        Args:
            key: Cache key
            value: Value to cache
            ttl: Time-to-live in seconds
        """
        if not self.available:
            return

        try:
            self.client.setex(
                key,
                ttl,
                json.dumps(value, default=str)
            )
        except Exception as e:
            logger.error(f"Redis set error: {e}")

    def delete(self, key: str):
        """Delete cache entry from Redis.

        Args:
            key: Cache key
        """
        if not self.available:
            return

        try:
            self.client.delete(key)
        except Exception as e:
            logger.error(f"Redis delete error: {e}")

    def clear_pattern(self, pattern: str):
        """Clear all keys matching pattern.

        Args:
            pattern: Redis key pattern (e.g., 'market_data:*')
        """
        if not self.available:
            return

        try:
            keys = self.client.keys(pattern)
            if keys:
                self.client.delete(*keys)
        except Exception as e:
            logger.error(f"Redis clear pattern error: {e}")

    def get_stats(self) -> Dict[str, Any]:
        """Get Redis cache statistics.

        Returns:
            Cache statistics
        """
        if not self.available:
            return {'available': False}

        total = self._hits + self._misses
        hit_rate = (self._hits / total * 100) if total > 0 else 0

        try:
            info = self.client.info()
            return {
                'available': True,
                'hits': self._hits,
                'misses': self._misses,
                'total': total,
                'hit_rate': hit_rate,
                'memory_usage': info.get('used_memory_human', 'N/A')
            }
        except Exception as e:
            logger.error(f"Failed to get Redis stats: {e}")
            return {'available': True, 'error': str(e)}


class CacheManager:
    """Unified cache manager with memory + Redis tiers."""

    def __init__(self, redis_client=None):
        """Initialize cache manager.

        Args:
            redis_client: Redis client instance (optional)
        """
        self.memory_cache = MemoryCache(max_size=1000)
        self.redis_cache = RedisCache(redis_client)

    def get(self, key: str, cache_type: str = 'market_data') -> Optional[Any]:
        """Get value from cache with fallback.

        Tries memory cache first, then Redis.

        Args:
            key: Cache key
            cache_type: Type of cache (for logging)

        Returns:
            Cached value or None
        """
        # Try memory cache first (fastest)
        value = self.memory_cache.get(key)
        if value is not None:
            logger.debug(f"Cache hit (memory): {key}")
            return value

        # Try Redis (if available)
        if self.redis_cache.available:
            value = self.redis_cache.get(key)
            if value is not None:
                logger.debug(f"Cache hit (Redis): {key}")
                # Populate memory cache from Redis
                self.memory_cache.set(key, value)
                return value

        logger.debug(f"Cache miss: {key}")
        return None

    def set(
        self,
        key: str,
        value: Any,
        cache_type: str = 'market_data',
        ttl: Optional[int] = None
    ):
        """Set value in cache (both memory and Redis).

        Args:
            key: Cache key
            value: Value to cache
            cache_type: Type of cache (determines TTL if not specified)
            ttl: Custom TTL in seconds (uses cache_type default if None)
        """
        # Get TTL from cache config
        if ttl is None:
            config = getattr(CacheConfig, cache_type.upper(), None)
            ttl = config['ttl'] if config else 3600

        # Set in both caches
        self.memory_cache.set(key, value, ttl)
        if self.redis_cache.available:
            self.redis_cache.set(key, value, ttl)

        logger.debug(f"Cache set: {key} (TTL: {ttl}s)")

    def invalidate(self, pattern: str = None, cache_type: str = None):
        """Invalidate cache entries.

        Args:
            pattern: Wildcard pattern (e.g., 'market_data:*')
            cache_type: Cache type to invalidate (e.g., 'market_data')
        """
        if pattern:
            # Invalidate by pattern
            self.memory_cache.clear()  # Clear memory (can't pattern match easily)
            if self.redis_cache.available:
                self.redis_cache.clear_pattern(pattern)
            logger.info(f"Invalidated cache pattern: {pattern}")

        if cache_type:
            # Invalidate by type
            prefix = cache_type.lower()
            pattern = f"{prefix}:*"
            self.invalidate(pattern)

    def get_stats(self) -> Dict[str, Any]:
        """Get cache statistics from all tiers.

        Returns:
            Combined cache statistics
        """
        return {
            'memory': self.memory_cache.get_stats(),
            'redis': self.redis_cache.get_stats()
        }


def cached(cache_type: str = 'market_data', ttl: Optional[int] = None):
    """Decorator for caching function results.

    Args:
        cache_type: Type of cache (determines TTL if not specified)
        ttl: Custom TTL in seconds

    Example:
        @cached(cache_type='market_data', ttl=300)
        def get_market_data(ticker):
            return fetch_data(ticker)
    """
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            # Generate cache key from function name and arguments
            key_parts = [func.__name__]
            key_parts.extend(str(arg) for arg in args)
            key_parts.extend(f"{k}={v}" for k, v in sorted(kwargs.items()))
            key = hashlib.md5("|".join(key_parts).encode()).hexdigest()

            # Try to get from cache
            from nasdaq_predictor.services.cache_layer import _cache_manager
            cached_value = _cache_manager.get(key, cache_type)
            if cached_value is not None:
                return cached_value

            # Call function and cache result
            result = func(*args, **kwargs)
            _cache_manager.set(key, result, cache_type, ttl)
            return result

        return wrapper
    return decorator


# Global cache manager instance
_cache_manager: Optional[CacheManager] = None


def init_cache_manager(redis_client=None) -> CacheManager:
    """Initialize global cache manager.

    Args:
        redis_client: Redis client instance (optional)

    Returns:
        Cache manager instance
    """
    global _cache_manager
    _cache_manager = CacheManager(redis_client)
    logger.info(f"✓ Cache manager initialized (Redis: {_cache_manager.redis_cache.available})")
    return _cache_manager


def get_cache_manager() -> CacheManager:
    """Get global cache manager instance.

    Returns:
        Cache manager instance
    """
    global _cache_manager
    if _cache_manager is None:
        _cache_manager = CacheManager()
    return _cache_manager
