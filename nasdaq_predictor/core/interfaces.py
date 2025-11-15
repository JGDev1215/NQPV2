"""
Abstract interfaces defining contracts for major components.

These interfaces ensure that implementations can be swapped out (e.g., for testing)
without changing the code that uses them. They document the expected behavior
of each component.
"""

from abc import ABC, abstractmethod
from datetime import datetime
from typing import Any, Dict, List, Optional, TypeVar

T = TypeVar("T")


class IDataFetcher(ABC):
    """Abstract interface for market data fetching."""

    @abstractmethod
    def fetch_ohlc(
        self, symbol: str, interval: str, start_date: Optional[datetime] = None
    ) -> Dict[str, Any]:
        """Fetch OHLC data for a symbol.

        Args:
            symbol: Ticker symbol (e.g., 'NQ=F').
            interval: Time interval (e.g., '1h', '1d').
            start_date: Optional start date for historical data.

        Returns:
            Dictionary containing OHLC data.

        Raises:
            DataFetchException: If fetch fails.
        """
        pass

    @abstractmethod
    def get_current_price(self, symbol: str) -> float:
        """Get the current price for a symbol.

        Args:
            symbol: Ticker symbol.

        Returns:
            Current price as float.

        Raises:
            DataFetchException: If fetch fails.
        """
        pass


class IRepository(ABC):
    """Generic repository interface for data access.

    All data repositories should implement this interface to provide
    consistent CRUD operations.
    """

    @abstractmethod
    def insert(self, entity: Dict[str, Any]) -> Any:
        """Insert a new record.

        Args:
            entity: Entity data as dictionary.

        Returns:
            Created entity with generated ID.

        Raises:
            DatabaseException: If insert fails.
        """
        pass

    @abstractmethod
    def select(self, filters: Dict[str, Any]) -> Optional[Any]:
        """Select a single record matching filters.

        Args:
            filters: Dictionary of field:value filters.

        Returns:
            Entity if found, None otherwise.

        Raises:
            DatabaseException: If query fails.
        """
        pass

    @abstractmethod
    def select_all(self, filters: Optional[Dict[str, Any]] = None) -> List[Any]:
        """Select all records matching optional filters.

        Args:
            filters: Optional dictionary of filters.

        Returns:
            List of matching entities.

        Raises:
            DatabaseException: If query fails.
        """
        pass

    @abstractmethod
    def update(self, id: Any, data: Dict[str, Any]) -> Any:
        """Update a record.

        Args:
            id: Entity ID.
            data: Dictionary of fields to update.

        Returns:
            Updated entity.

        Raises:
            DatabaseException: If update fails.
        """
        pass

    @abstractmethod
    def delete(self, id: Any) -> bool:
        """Delete a record.

        Args:
            id: Entity ID.

        Returns:
            True if deleted, False if not found.

        Raises:
            DatabaseException: If delete fails.
        """
        pass

    @abstractmethod
    def count(self, filters: Optional[Dict[str, Any]] = None) -> int:
        """Count records matching optional filters.

        Args:
            filters: Optional dictionary of filters.

        Returns:
            Count of matching records.

        Raises:
            DatabaseException: If count fails.
        """
        pass


class IPredictionService(ABC):
    """Interface for prediction calculation services."""

    @abstractmethod
    def predict(self, symbol: str, market_data: Dict[str, Any]) -> Dict[str, Any]:
        """Generate a prediction for a symbol.

        Args:
            symbol: Ticker symbol.
            market_data: Dictionary containing market data (OHLC, etc.).

        Returns:
            Prediction result dictionary containing:
                - prediction: 'BULLISH' or 'BEARISH'
                - confidence: float 0-100
                - weighted_score: float 0-1.0
                - reference_levels: dict of all reference points
                - signals: dict of individual signals

        Raises:
            AnalysisException: If prediction fails.
        """
        pass

    @abstractmethod
    def analyze_all(self, tickers: List[str]) -> Dict[str, Dict[str, Any]]:
        """Generate predictions for multiple symbols.

        Args:
            tickers: List of ticker symbols.

        Returns:
            Dictionary mapping symbols to their predictions.

        Raises:
            AnalysisException: If analysis fails.
        """
        pass


class ICacheService(ABC):
    """Interface for caching services."""

    @abstractmethod
    def get(self, key: str) -> Optional[Any]:
        """Retrieve a value from cache.

        Args:
            key: Cache key.

        Returns:
            Cached value if found and not stale, None otherwise.

        Raises:
            CacheException: If cache operation fails.
        """
        pass

    @abstractmethod
    def set(self, key: str, value: Any, ttl_seconds: int) -> bool:
        """Store a value in cache.

        Args:
            key: Cache key.
            value: Value to cache.
            ttl_seconds: Time-to-live in seconds.

        Returns:
            True if successful.

        Raises:
            CacheException: If cache operation fails.
        """
        pass

    @abstractmethod
    def delete(self, key: str) -> bool:
        """Remove a value from cache.

        Args:
            key: Cache key.

        Returns:
            True if deleted, False if not found.

        Raises:
            CacheException: If cache operation fails.
        """
        pass

    @abstractmethod
    def clear(self) -> bool:
        """Clear all cache entries.

        Returns:
            True if successful.

        Raises:
            CacheException: If cache operation fails.
        """
        pass


class IDataProcessor(ABC):
    """Interface for data processing/transformation."""

    @abstractmethod
    def process(self, raw_data: Any) -> Any:
        """Transform raw data to processed format.

        Args:
            raw_data: Raw input data.

        Returns:
            Processed data.

        Raises:
            AnalysisException: If processing fails.
        """
        pass


class IScheduler(ABC):
    """Interface for job scheduling."""

    @abstractmethod
    def start(self) -> bool:
        """Start the scheduler.

        Returns:
            True if started successfully.

        Raises:
            SchedulerException: If start fails.
        """
        pass

    @abstractmethod
    def stop(self) -> bool:
        """Stop the scheduler.

        Returns:
            True if stopped successfully.

        Raises:
            SchedulerException: If stop fails.
        """
        pass

    @abstractmethod
    def add_job(
        self, job_id: str, func: callable, trigger: str, **trigger_args
    ) -> bool:
        """Add a scheduled job.

        Args:
            job_id: Unique job identifier.
            func: Function to execute.
            trigger: Trigger type ('cron', 'interval', etc.).
            **trigger_args: Trigger-specific arguments.

        Returns:
            True if job added successfully.

        Raises:
            SchedulerException: If add fails.
        """
        pass

    @abstractmethod
    def remove_job(self, job_id: str) -> bool:
        """Remove a scheduled job.

        Args:
            job_id: Job identifier.

        Returns:
            True if removed, False if not found.

        Raises:
            SchedulerException: If remove fails.
        """
        pass

    @abstractmethod
    def get_jobs(self) -> List[Dict[str, Any]]:
        """Get list of scheduled jobs.

        Returns:
            List of job information dictionaries.

        Raises:
            SchedulerException: If retrieval fails.
        """
        pass


class ILogger(ABC):
    """Interface for logging services."""

    @abstractmethod
    def debug(self, message: str, **kwargs) -> None:
        """Log debug message."""
        pass

    @abstractmethod
    def info(self, message: str, **kwargs) -> None:
        """Log info message."""
        pass

    @abstractmethod
    def warning(self, message: str, **kwargs) -> None:
        """Log warning message."""
        pass

    @abstractmethod
    def error(self, message: str, exception: Optional[Exception] = None, **kwargs) -> None:
        """Log error message."""
        pass

    @abstractmethod
    def critical(self, message: str, exception: Optional[Exception] = None, **kwargs) -> None:
        """Log critical message."""
        pass


class IDatabase(ABC):
    """Interface for database connections."""

    @abstractmethod
    def connect(self) -> bool:
        """Establish database connection.

        Returns:
            True if connection successful.

        Raises:
            DatabaseException: If connection fails.
        """
        pass

    @abstractmethod
    def disconnect(self) -> bool:
        """Close database connection.

        Returns:
            True if disconnected successfully.

        Raises:
            DatabaseException: If disconnection fails.
        """
        pass

    @abstractmethod
    def is_connected(self) -> bool:
        """Check if database is connected.

        Returns:
            True if connected, False otherwise.
        """
        pass

    @abstractmethod
    def execute(self, query: str, params: Optional[Dict] = None) -> List[Dict]:
        """Execute a database query.

        Args:
            query: SQL query string.
            params: Optional query parameters.

        Returns:
            List of result dictionaries.

        Raises:
            DatabaseException: If query fails.
        """
        pass
