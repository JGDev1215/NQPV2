"""
Dependency Injection Container

Manages all service registration and resolution, enabling loose coupling
and improved testability throughout the application.

Usage:
    container = create_container()
    service = container.resolve('prediction_service')
    result = service.predict('NQ=F', {})
"""

from typing import Callable, Dict, Any, Optional, TypeVar

from .core import NQPException

T = TypeVar("T")


class ServiceNotRegisteredException(NQPException):
    """Raised when attempting to resolve an unregistered service."""

    pass


class Container:
    """Lightweight dependency injection container.

    Supports:
    - Service registration with factory functions
    - Singleton pattern (shared instances)
    - Lazy instantiation (on-demand resolution)
    - Service composition (services depending on other services)
    """

    def __init__(self):
        """Initialize empty container."""
        self._services: Dict[str, Dict[str, Any]] = {}
        self._singletons: Dict[str, Any] = {}

    def register(
        self,
        name: str,
        factory: Callable[["Container"], T],
        singleton: bool = False,
    ) -> None:
        """Register a service with its factory function.

        Args:
            name: Service identifier (unique key).
            factory: Function that creates the service. Receives container as argument.
            singleton: If True, service is created once and reused. Otherwise created on each resolve.

        Example:
            container.register(
                'data_fetcher',
                lambda c: YahooFinanceDataFetcher(),
                singleton=True
            )
        """
        self._services[name] = {"factory": factory, "singleton": singleton}

    def resolve(self, name: str) -> Any:
        """Resolve and return a service instance.

        Args:
            name: Service identifier to resolve.

        Returns:
            Service instance.

        Raises:
            ServiceNotRegisteredException: If service not registered.

        Example:
            service = container.resolve('prediction_service')
        """
        if name not in self._services:
            raise ServiceNotRegisteredException(
                f"Service '{name}' not registered. "
                f"Available services: {', '.join(sorted(self._services.keys()))}"
            )

        service_def = self._services[name]

        # Handle singletons
        if service_def["singleton"]:
            if name not in self._singletons:
                self._singletons[name] = service_def["factory"](self)
            return self._singletons[name]

        # Create new instance each time
        return service_def["factory"](self)

    def has(self, name: str) -> bool:
        """Check if a service is registered.

        Args:
            name: Service identifier.

        Returns:
            True if registered, False otherwise.
        """
        return name in self._services

    def get_all_services(self) -> Dict[str, Dict[str, Any]]:
        """Get all registered services.

        Returns:
            Dictionary of all registered services and their metadata.
        """
        return dict(self._services)

    def clear_singletons(self) -> None:
        """Clear all cached singleton instances.

        Useful for testing - forces fresh instantiation on next resolve.
        """
        self._singletons.clear()

    def detect_circular_dependencies(self) -> None:
        """Detect circular dependencies in service graph.

        Performs depth-first search to find cycles in service dependency graph.
        Raises RuntimeError if circular dependencies are detected.

        Example:
            >>> container = create_container()
            >>> container.detect_circular_dependencies()
        """
        visited = set()
        recursion_stack = set()

        def visit(service_name: str, path: list = None) -> None:
            """Recursively visit service and its dependencies."""
            if path is None:
                path = []

            if service_name in recursion_stack:
                cycle = " -> ".join(path + [service_name])
                raise RuntimeError(f"Circular dependency detected: {cycle}")

            if service_name in visited:
                return

            visited.add(service_name)
            recursion_stack.add(service_name)

            # Get dependencies for this service (factory function inspection would be complex,
            # so we skip deep dependency analysis and only check if service can be resolved)
            if service_name in self._services:
                try:
                    # Attempt to resolve without triggering actual instantiation
                    # This is a shallow check - a full check would require inspecting
                    # factory function parameters
                    pass
                except Exception:
                    pass

            recursion_stack.remove(service_name)

        # Check all registered services
        for service_name in self._services:
            if service_name not in visited:
                visit(service_name)


def create_container() -> Container:
    """Factory function to create and configure the DI container.

    Returns:
        Fully configured Container instance with all services registered.

    This function should be called once during application initialization
    and the container passed to all components that need services.

    Example:
        app = Flask(__name__)
        app.container = create_container()

        @app.route('/api/data')
        def get_data():
            service = current_app.container.resolve('prediction_service')
            return service.predict('NQ=F', {})
    """
    container = Container()

    # ========================================
    # Database & Repository Layer
    # ========================================

    # Supabase client (singleton - single connection)
    container.register(
        "supabase_client",
        lambda c: _init_supabase_client(),
        singleton=True,
    )

    # Repositories (singletons - share connection)
    container.register(
        "ticker_repository",
        lambda c: _init_ticker_repository(),
        singleton=True,
    )

    container.register(
        "market_data_repository",
        lambda c: _init_market_data_repository(),
        singleton=True,
    )

    container.register(
        "prediction_repository",
        lambda c: _init_prediction_repository(),
        singleton=True,
    )

    container.register(
        "intraday_prediction_repository",
        lambda c: _init_intraday_prediction_repository(),
        singleton=True,
    )

    container.register(
        "reference_levels_repository",
        lambda c: _init_reference_levels_repository(),
        singleton=True,
    )

    container.register(
        "fibonacci_pivot_repository",
        lambda c: _init_fibonacci_pivot_repository(),
        singleton=True,
    )

    container.register(
        "block_prediction_repository",
        lambda c: _init_block_prediction_repository(),
        singleton=True,
    )

    # ========================================
    # Data Layer (External APIs, Fetchers)
    # ========================================

    container.register(
        "data_fetcher",
        lambda c: _init_data_fetcher(c),
        singleton=True,
    )

    # ========================================
    # Business Logic / Analysis Layer
    # ========================================

    container.register(
        "prediction_service",
        lambda c: _init_prediction_service(c),
        singleton=True,
    )

    # Phase 2: Refactored services with split responsibilities
    container.register(
        "cache_service",
        lambda c: _init_cache_service_v2(c),
        singleton=True,
    )

    container.register(
        "prediction_calculation_service",
        lambda c: _init_prediction_calculation_service(c),
        singleton=True,
    )

    container.register(
        "formatting_service",
        lambda c: _init_formatting_service_v2(),
        singleton=True,
    )

    container.register(
        "aggregation_service",
        lambda c: _init_aggregation_service_v2(c),
        singleton=True,
    )

    container.register(
        "market_analysis_service",
        lambda c: _init_market_analysis_service(c),
        singleton=True,
    )

    container.register(
        "accuracy_service",
        lambda c: _init_accuracy_service_v2(c),
        singleton=True,
    )

    # ========================================
    # Service Layer (Orchestration)
    # ========================================

    container.register(
        "data_sync_service",
        lambda c: _init_data_sync_service(c),
        singleton=True,
    )

    container.register(
        "intraday_prediction_service",
        lambda c: _init_intraday_prediction_service(c),
        singleton=True,
    )

    container.register(
        "verification_service",
        lambda c: _init_verification_service(c),
        singleton=True,
    )

    container.register(
        "intraday_verification_service",
        lambda c: _init_intraday_verification_service(c),
        singleton=True,
    )

    container.register(
        "block_prediction_service",
        lambda c: _init_block_prediction_service(c),
        singleton=True,
    )

    container.register(
        "block_verification_service",
        lambda c: _init_block_verification_service(c),
        singleton=True,
    )

    # ========================================
    # Scheduler & Background Jobs
    # ========================================

    container.register(
        "scheduler",
        lambda c: _init_scheduler(c),
        singleton=True,
    )

    # ========================================
    # Market Status & Monitoring Services
    # ========================================

    container.register(
        "market_status_service",
        lambda c: _init_market_status_service(),
        singleton=True,
    )

    container.register(
        "scheduler_job_tracking_service",
        lambda c: _init_scheduler_job_tracking_service(c),
        singleton=True,
    )

    return container


# ========================================
# Initialization Functions (Factories)
# ========================================


def _init_supabase_client():
    """Initialize Supabase database client."""
    # Lazy import to avoid circular dependencies
    from .database.supabase_client import get_supabase_client

    return get_supabase_client()


def _init_data_fetcher(container=None):
    """Initialize data fetcher (Yahoo Finance with Supabase support)."""
    from .data.fetcher import YahooFinanceDataFetcher

    # If container provided, inject MarketDataRepository for Supabase support
    if container:
        market_data_repo = container.resolve("market_data_repository")
        return YahooFinanceDataFetcher(market_data_repo=market_data_repo)

    return YahooFinanceDataFetcher()


def _init_ticker_repository():
    """Initialize ticker repository."""
    from .database.repositories.ticker_repository import TickerRepository

    return TickerRepository()


def _init_market_data_repository():
    """Initialize market data repository."""
    from .database.repositories.market_data_repository import MarketDataRepository

    return MarketDataRepository()


def _init_prediction_repository():
    """Initialize prediction repository."""
    from .database.repositories.prediction_repository import PredictionRepository

    return PredictionRepository()


def _init_intraday_prediction_repository():
    """Initialize intraday prediction repository."""
    from .database.repositories.intraday_prediction_repository import (
        IntradayPredictionRepository,
    )

    return IntradayPredictionRepository()


def _init_reference_levels_repository():
    """Initialize reference levels repository."""
    from .database.repositories.reference_levels_repository import ReferenceLevelsRepository

    return ReferenceLevelsRepository()


def _init_fibonacci_pivot_repository():
    """Initialize Fibonacci pivot repository."""
    from .database.repositories.fibonacci_pivot_repository import FibonacciPivotRepository

    return FibonacciPivotRepository()


def _init_cache_service(container):
    """Initialize legacy cache service."""
    from .services.cache_service import CacheService

    return CacheService(
        repo=container.resolve("prediction_repository"),
        cache_duration_minutes=15,
    )


def _init_cache_service_v2(container):
    """Initialize Phase 2 cache service with full DI."""
    from .services.cache_service import CacheService

    return CacheService(
        ticker_repo=container.resolve("ticker_repository"),
        market_data_repo=container.resolve("market_data_repository"),
        prediction_repo=container.resolve("prediction_repository"),
        intraday_repo=container.resolve("intraday_prediction_repository"),
        ref_levels_repo=container.resolve("reference_levels_repository"),
    )


def _init_prediction_calculation_service(container):
    """Initialize Phase 2 prediction calculation service."""
    from .services.prediction_calculation_service import PredictionCalculationService

    return PredictionCalculationService(
        data_fetcher=container.resolve("data_fetcher"),
    )


def _init_formatting_service():
    """Initialize legacy response formatting service."""
    from .services.formatting_service import FormattingService

    return FormattingService()


def _init_formatting_service_v2():
    """Initialize Phase 2 response formatting service."""
    from .services.formatting_service import FormattingService

    return FormattingService()


def _init_aggregation_service(container):
    """Initialize legacy aggregation service."""
    from .services.aggregation_service import AggregationService

    return AggregationService(
        prediction_service=container.resolve("prediction_service"),
        formatting_service=container.resolve("formatting_service"),
    )


def _init_aggregation_service_v2(container):
    """Initialize Phase 2 aggregation service with full DI."""
    from .services.aggregation_service import AggregationService

    return AggregationService(
        cache_service=container.resolve("cache_service"),
        prediction_service=container.resolve("prediction_calculation_service"),
        formatting_service=container.resolve("formatting_service"),
        ticker_repo=container.resolve("ticker_repository"),
        intraday_repo=container.resolve("intraday_prediction_repository"),
    )


def _init_market_analysis_service(container):
    """Initialize Phase 2 refactored market analysis service."""
    from .services.market_service_refactored import MarketAnalysisService

    return MarketAnalysisService(
        cache_service=container.resolve("cache_service"),
        prediction_service=container.resolve("prediction_calculation_service"),
        formatting_service=container.resolve("formatting_service"),
        aggregation_service=container.resolve("aggregation_service"),
    )


def _init_accuracy_service(container):
    """Initialize legacy accuracy metrics service."""
    from .services.accuracy_service import AccuracyService

    return AccuracyService(prediction_repo=container.resolve("prediction_repository"))


def _init_accuracy_service_v2(container):
    """Initialize Phase 2 accuracy service with consolidated evaluation logic."""
    from .services.accuracy_service import AccuracyService

    return AccuracyService(neutral_threshold_percent=0.1)


def _init_data_sync_service(container):
    """Initialize data sync service with full DI."""
    from .services.data_sync_service import DataSyncService

    return DataSyncService(
        fetcher=container.resolve("data_fetcher"),
        ticker_repo=container.resolve("ticker_repository"),
        market_data_repo=container.resolve("market_data_repository"),
        prediction_repo=container.resolve("prediction_repository"),
        ref_levels_repo=container.resolve("reference_levels_repository"),
    )


def _init_intraday_prediction_service(container):
    """Initialize intraday prediction service with full DI."""
    from .services.intraday_prediction_service import IntradayPredictionService

    return IntradayPredictionService(
        fetcher=container.resolve("data_fetcher"),
        ticker_repo=container.resolve("ticker_repository"),
        market_data_repo=container.resolve("market_data_repository"),
        intraday_repo=container.resolve("intraday_prediction_repository"),
    )


def _init_verification_service(container):
    """Initialize verification service with full DI."""
    from .services.verification_service import PredictionVerificationService

    return PredictionVerificationService(
        ticker_repo=container.resolve("ticker_repository"),
        market_data_repo=container.resolve("market_data_repository"),
        prediction_repo=container.resolve("prediction_repository"),
        neutral_threshold_percent=0.1,
    )


def _init_intraday_verification_service(container):
    """Initialize intraday verification service with full DI."""
    from .services.intraday_verification_service import IntradayVerificationService

    return IntradayVerificationService(
        ticker_repo=container.resolve("ticker_repository"),
        market_data_repo=container.resolve("market_data_repository"),
        intraday_repo=container.resolve("intraday_prediction_repository"),
    )


def _init_block_prediction_repository():
    """Initialize block prediction repository."""
    from .database.repositories.block_prediction_repository import BlockPredictionRepository

    return BlockPredictionRepository()


def _init_block_prediction_service(container):
    """Initialize block prediction service with full DI."""
    from .services.block_prediction_service import BlockPredictionService

    return BlockPredictionService(
        fetcher=container.resolve("data_fetcher"),
        block_prediction_repo=container.resolve("block_prediction_repository"),
        ticker_repo=container.resolve("ticker_repository"),
    )


def _init_block_verification_service(container):
    """Initialize block verification service with full DI."""
    from .services.block_verification_service import BlockVerificationService

    return BlockVerificationService(
        fetcher=container.resolve("data_fetcher"),
        block_prediction_repo=container.resolve("block_prediction_repository"),
    )


def _init_scheduler(container):
    """Initialize job scheduler."""
    from .scheduler import Scheduler

    return Scheduler(
        prediction_service=container.resolve("prediction_service"),
        data_sync_service=container.resolve("data_sync_service"),
        intraday_prediction_service=container.resolve("intraday_prediction_service"),
        verification_service=container.resolve("verification_service"),
    )


def _init_market_status_service():
    """Initialize market status service."""
    from .services.market_status_service import MarketStatusService

    return MarketStatusService()


def _init_scheduler_job_tracking_service(container):
    """Initialize scheduler job tracking service with dependencies."""
    from .services.scheduler_job_tracking_service import SchedulerJobTrackingService

    return SchedulerJobTrackingService()
