# NASDAQ Predictor Service Architecture & Dependency Injection Analysis

**Generated:** 2025-11-15  
**System:** NQP (NASDAQ Predictor) - Market Prediction Platform  
**Analysis Scope:** Full service layer, DI container, repository pattern, and orchestration flows

---

## Executive Summary

The NASDAQ Predictor implements a **mature dependency injection architecture** using a custom lightweight container with singleton pattern support. The system demonstrates **good separation of concerns** with 14 service classes, 9 repositories, and clear layering between data access, business logic, and API layers.

### Key Strengths
- Clean DI container implementation with lazy instantiation
- Consistent constructor injection across all services
- Well-defined repository pattern with base class abstraction
- Market-aware architecture with dedicated status service
- Comprehensive job tracking and scheduler integration

### Areas for Improvement
- **Missing DI registrations** for MarketStatusService and SchedulerJobTrackingService
- **Circular dependency risks** in service composition
- **Inconsistent service initialization** patterns (some services self-instantiate dependencies)
- **Facade pattern underutilization** (MarketAnalysisService delegates everything)
- **Configuration injection** could be more explicit
- **Testing complexity** due to deep dependency chains

---

## 1. Current Service Inventory

### Service Layer (14 Services - 5,349 total LOC)

| Service | LOC | Primary Responsibility | DI Status | Lifecycle |
|---------|-----|----------------------|-----------|-----------|
| **BlockPredictionService** | 684 | 7-block hourly prediction generation | ✅ Registered | Singleton |
| **DataSyncService** | 698 | Market data synchronization to Supabase | ✅ Registered | Singleton |
| **BlockVerificationService** | 423 | Block prediction verification | ✅ Registered | Singleton |
| **MarketStatusService** | 422 | Market hours/status detection | ❌ Not Registered | Manual Init |
| **SchedulerJobTrackingService** | 406 | Job execution tracking & metrics | ❌ Not Registered | Manual Init |
| **IntradayPredictionService** | 368 | 9am/10am intraday forecasts | ✅ Registered | Singleton |
| **AccuracyService** | 369 | Prediction accuracy evaluation | ✅ Registered | Singleton |
| **FormattingService** | 364 | Response formatting | ✅ Registered | Singleton |
| **VerificationService** | 355 | Daily prediction verification | ✅ Registered | Singleton |
| **AggregationService** | 328 | Multi-ticker batch processing | ✅ Registered | Singleton |
| **IntradayVerificationService** | 303 | Intraday prediction verification | ✅ Registered | Singleton |
| **CacheService** | 246 | Database-first caching | ✅ Registered | Singleton |
| **PredictionCalculationService** | 193 | Fresh yfinance calculations | ✅ Registered | Singleton |
| **MarketAnalysisService** | 190 | Facade/orchestrator for analysis | ✅ Registered | Singleton |

**Total Service LOC:** 5,349 lines

### Repository Layer (9 Repositories)

| Repository | Table | Purpose | Inheritance |
|------------|-------|---------|-------------|
| **PredictionRepository** | predictions | Daily prediction storage | BaseRepository |
| **IntradayPredictionRepository** | intraday_predictions | 9am/10am predictions | BaseRepository |
| **BlockPredictionRepository** | block_predictions | 7-block hourly predictions | BaseRepository |
| **TickerRepository** | tickers | Instrument configuration | BaseRepository |
| **MarketDataRepository** | market_data | OHLC bar storage | BaseRepository |
| **ReferenceLevelsRepository** | reference_levels | Trading levels | BaseRepository |
| **FibonacciPivotRepository** | fibonacci_pivots | Fib levels | BaseRepository |
| **SchedulerJobExecutionRepository** | scheduler_job_executions | Job tracking | BaseRepository |
| **BaseRepository** | - | Abstract CRUD operations | ABC |

All repositories are **registered as singletons** in the DI container and share a common Supabase client.

---

## 2. Dependency Injection Container Architecture

### 2.1 Container Implementation

**File:** `/Users/soonjeongguan/Desktop/Repository/CLAUDECODE/NQP/nasdaq_predictor/container.py`

```python
class Container:
    """Lightweight dependency injection container."""
    
    def __init__(self):
        self._services: Dict[str, Dict[str, Any]] = {}
        self._singletons: Dict[str, Any] = {}
    
    def register(self, name: str, factory: Callable, singleton: bool = False):
        """Register service with factory function."""
        self._services[name] = {"factory": factory, "singleton": singleton}
    
    def resolve(self, name: str) -> Any:
        """Resolve service instance (lazy instantiation)."""
        if singleton and cached:
            return self._singletons[name]
        return self._services[name]["factory"](self)
```

**Features:**
- ✅ Lazy instantiation (services created on first resolve)
- ✅ Singleton pattern support (shared instances)
- ✅ Factory function composition (services can depend on other services)
- ✅ Service discovery (`has()`, `get_all_services()`)
- ✅ Test support (`clear_singletons()`)

**Limitations:**
- ❌ No circular dependency detection
- ❌ No scope management beyond singleton/transient
- ❌ No automatic wiring (requires manual factory functions)
- ❌ No configuration injection helpers

### 2.2 Registered Services (23 Services)

```python
# Database Layer
supabase_client                    # Singleton - Supabase connection
ticker_repository                  # Singleton
market_data_repository             # Singleton
prediction_repository              # Singleton
intraday_prediction_repository     # Singleton
reference_levels_repository        # Singleton
fibonacci_pivot_repository         # Singleton
block_prediction_repository        # Singleton

# Data Layer
data_fetcher                       # Singleton - YahooFinanceDataFetcher

# Business Logic Layer
prediction_service                 # Singleton - LEGACY (not found in codebase)
cache_service                      # Singleton
prediction_calculation_service     # Singleton
formatting_service                 # Singleton
aggregation_service                # Singleton
market_analysis_service            # Singleton
accuracy_service                   # Singleton

# Orchestration Layer
data_sync_service                  # Singleton
intraday_prediction_service        # Singleton
verification_service               # Singleton
intraday_verification_service      # Singleton
block_prediction_service           # Singleton
block_verification_service         # Singleton

# Scheduler
scheduler                          # Singleton - APScheduler instance
```

### 2.3 Missing Registrations (Critical)

Two services are instantiated manually instead of via DI:

1. **MarketStatusService** (422 LOC)
   - Used by: BlockPredictionService, API routes
   - Current pattern: `MarketStatusService()` in constructors
   - **Risk:** Cannot be mocked in tests, configuration not injectable

2. **SchedulerJobTrackingService** (406 LOC)
   - Used by: Scheduler jobs
   - Current pattern: `SchedulerJobTrackingService()` in job decorators
   - **Risk:** Cannot swap repository implementation

**Recommendation:** Register both as singletons with proper dependency injection.

---

## 3. Service Dependency Mapping

### 3.1 Dependency Graph

```
┌─────────────────────────────────────────────────────────────────┐
│                      API Layer (Flask Routes)                    │
└────────────────────────────┬────────────────────────────────────┘
                             │
                             ▼
┌─────────────────────────────────────────────────────────────────┐
│                  Facade Service (Orchestration)                  │
│                                                                   │
│  MarketAnalysisService                                           │
│  ├─ CacheService                                                 │
│  ├─ PredictionCalculationService                                 │
│  ├─ FormattingService                                            │
│  └─ AggregationService                                           │
└────────────────────────────┬────────────────────────────────────┘
                             │
                             ▼
┌─────────────────────────────────────────────────────────────────┐
│                   Business Logic Services                        │
│                                                                   │
│  BlockPredictionService                                          │
│  ├─ YahooFinanceDataFetcher                                      │
│  ├─ BlockPredictionRepository                                    │
│  ├─ TickerRepository                                             │
│  └─ MarketStatusService (⚠️ Manual Init)                        │
│                                                                   │
│  DataSyncService                                                 │
│  ├─ YahooFinanceDataFetcher                                      │
│  ├─ TickerRepository                                             │
│  ├─ MarketDataRepository                                         │
│  ├─ PredictionRepository                                         │
│  └─ ReferenceLevelsRepository                                    │
│                                                                   │
│  IntradayPredictionService                                       │
│  ├─ YahooFinanceDataFetcher                                      │
│  ├─ TickerRepository                                             │
│  ├─ MarketDataRepository                                         │
│  └─ IntradayPredictionRepository                                 │
│                                                                   │
│  CacheService                                                    │
│  ├─ TickerRepository                                             │
│  ├─ MarketDataRepository                                         │
│  ├─ PredictionRepository                                         │
│  ├─ IntradayPredictionRepository                                 │
│  └─ ReferenceLevelsRepository                                    │
└────────────────────────────┬────────────────────────────────────┘
                             │
                             ▼
┌─────────────────────────────────────────────────────────────────┐
│                    Repository Layer (Data Access)                │
│                                                                   │
│  All repositories extend BaseRepository                          │
│  └─ Supabase Client (Singleton)                                  │
└─────────────────────────────────────────────────────────────────┘
```

### 3.2 Service Dependency Matrix

| Service | Dependencies | Depth |
|---------|-------------|-------|
| **MarketAnalysisService** | 4 services (cache, prediction_calc, formatting, aggregation) | 3 |
| **AggregationService** | 5 deps (cache, prediction, formatting, ticker_repo, intraday_repo) | 2 |
| **BlockPredictionService** | 4 deps (fetcher, block_repo, ticker_repo, market_status) | 2 |
| **DataSyncService** | 5 deps (fetcher, 4 repositories) | 1 |
| **CacheService** | 5 deps (5 repositories) | 1 |
| **IntradayPredictionService** | 4 deps (fetcher, 3 repositories) | 1 |
| **VerificationService** | 3 deps (3 repositories) | 1 |
| **FormattingService** | 0 deps (pure utility) | 0 |
| **AccuracyService** | 0 deps (stateless utility) | 0 |

**Deepest Dependency Chain:** API → MarketAnalysisService → AggregationService → CacheService → Repositories (4 levels)

### 3.3 Circular Dependency Analysis

**Potential Risks Identified:**

1. **AggregationService ↔ PredictionCalculationService**
   - Aggregation uses prediction_calculation for fresh data
   - No circular reference currently, but tight coupling

2. **Scheduler ↔ Services**
   - Scheduler depends on: prediction_service, data_sync, intraday_prediction, verification
   - Services may need scheduler status (currently avoided by separation)

3. **MarketStatusService Usage Pattern**
   - Not in container, instantiated directly in BlockPredictionService constructor
   - Creates hidden dependency that cannot be tracked by container

**Mitigation:** All current dependencies are acyclic due to strict service layer separation.

---

## 4. Service Architecture Assessment

### 4.1 SOLID Principles Compliance

#### Single Responsibility Principle (SRP) - ✅ GOOD

| Service | Single Responsibility | Violation? |
|---------|----------------------|------------|
| BlockPredictionService | 7-block prediction generation | ✅ Focused |
| DataSyncService | Market data sync to Supabase | ✅ Focused |
| CacheService | Database-first caching | ✅ Focused |
| MarketAnalysisService | Facade/orchestration | ✅ Appropriate delegation |
| SchedulerJobTrackingService | Job execution tracking | ✅ Focused |

**Assessment:** Services are well-focused with clear boundaries. The previous refactoring (Phase 2) successfully split monolithic services.

#### Open/Closed Principle (OCP) - ⚠️ PARTIAL

**Extensibility Analysis:**

- ✅ **Repository layer:** Can add new repositories without modifying BaseRepository
- ✅ **Service layer:** Can add new services without modifying container
- ❌ **Data fetcher:** YahooFinanceDataFetcher is concrete, not interface-based
- ❌ **Market status:** No interface for market status detection (hard to add new markets)

**Recommendation:** Introduce interfaces for external dependencies:
```python
class IDataFetcher(ABC):
    @abstractmethod
    def fetch_historical_data(...) -> List[Dict]: pass

class IMarketStatusProvider(ABC):
    @abstractmethod
    def get_market_status(...) -> MarketStatusInfo: pass
```

#### Liskov Substitution Principle (LSP) - ✅ GOOD

**Repository Substitution:**
- All repositories extend BaseRepository
- Liskov-compliant: any BaseRepository subclass can be substituted
- Type safety maintained through TypeVar usage

**Service Substitution:**
- Services are concrete classes, not interfaces
- No polymorphic service substitution currently used

#### Interface Segregation Principle (ISP) - ⚠️ PARTIAL

**Analysis:**

- ✅ **Repositories:** Each repository has focused interface (no bloat)
- ❌ **Services:** No explicit interfaces defined
- ❌ **Container:** Single `resolve()` method - could benefit from typed resolution

**Recommendation:** Define focused service interfaces:
```python
class IPredictionService(Protocol):
    def generate_block_prediction(...) -> BlockPrediction: ...

class ICacheService(Protocol):
    def get_cached_prediction(...) -> Optional[Dict]: ...
```

#### Dependency Inversion Principle (DIP) - ⚠️ PARTIAL

**Current State:**

- ✅ **High-level modules:** Services depend on abstractions (BaseRepository)
- ❌ **External dependencies:** Concrete YahooFinanceDataFetcher instead of abstraction
- ❌ **Configuration:** Services directly import config modules (not injected)
- ⚠️ **Market status:** MarketStatusService instantiated directly (violates DIP)

**Violations:**

1. **BlockPredictionService line 59:**
   ```python
   self.market_status_service = market_status_service or MarketStatusService()
   ```
   Should always receive injected instance.

2. **SchedulerJobTrackingService line 31:**
   ```python
   self.repository = SchedulerJobExecutionRepository()
   ```
   Should be constructor-injected.

3. **All services import config:**
   ```python
   from ..config.scheduler_config import SchedulerConfig
   ```
   Should inject configuration objects.

### 4.2 Design Patterns in Use

| Pattern | Implementation | Quality |
|---------|---------------|---------|
| **Dependency Injection** | Container with factory functions | ✅ Good |
| **Repository Pattern** | BaseRepository + domain repos | ✅ Excellent |
| **Singleton Pattern** | Container-managed singletons | ✅ Good |
| **Factory Pattern** | `_init_*()` factory functions | ✅ Good |
| **Facade Pattern** | MarketAnalysisService | ⚠️ Thin delegation |
| **Decorator Pattern** | `@track_job_execution` | ✅ Excellent |
| **Service Locator** | API routes use `container.resolve()` | ⚠️ Anti-pattern risk |

**Service Locator Anti-Pattern Risk:**

Current pattern in API routes:
```python
service = current_app.container.resolve('block_prediction_service')
```

**Issues:**
- Hidden dependencies (not visible in function signature)
- Harder to test (must mock container)
- Runtime errors if service not registered

**Better approach:**
```python
@inject
def get_24h_predictions(ticker, block_prediction_service: BlockPredictionService):
    predictions = block_prediction_service.get_hourly_predictions_24h(ticker, date)
```

---

## 5. Service Initialization & Resolution Chains

### 5.1 Factory Function Pattern

**Example: BlockPredictionService initialization**

```python
def _init_block_prediction_service(container):
    """Initialize block prediction service with full DI."""
    from .services.block_prediction_service import BlockPredictionService
    
    return BlockPredictionService(
        fetcher=container.resolve("data_fetcher"),
        block_prediction_repo=container.resolve("block_prediction_repository"),
        ticker_repo=container.resolve("ticker_repository"),
    )
```

**Resolution Chain:**
1. API calls `container.resolve('block_prediction_service')`
2. Container calls `_init_block_prediction_service(container)`
3. Factory resolves dependencies:
   - `data_fetcher` → `_init_data_fetcher()` → YahooFinanceDataFetcher
   - `block_prediction_repository` → `_init_block_prediction_repository()` → BlockPredictionRepository
   - `ticker_repository` → `_init_ticker_repository()` → TickerRepository
4. BlockPredictionService instance created with injected dependencies
5. If singleton, cached in `_singletons` dict

### 5.2 Initialization Order (Bootstrap Sequence)

**Container creation in app.py:**

```python
# 1. Create container
app.container = create_container()

# 2. Lazy instantiation - nothing created yet

# 3. First API request triggers resolution
service = container.resolve('block_prediction_service')

# 4. Cascade resolution:
#    - Resolves 'data_fetcher' (singleton, created once)
#    - Resolves 'block_prediction_repository' (singleton, created once)
#    - Resolves 'ticker_repository' (singleton, created once)
#    - Creates BlockPredictionService instance
#    - Caches as singleton

# 5. Subsequent requests reuse singleton
```

**Initialization Timing:**
- ✅ **Lazy:** Services created on-demand (not at container creation)
- ✅ **Cached:** Singletons reused across requests
- ⚠️ **Eager:** No warm-up possible (first request pays initialization cost)

### 5.3 Resolution Chain Documentation

**Level 0 (Infrastructure):**
```
supabase_client (singleton)
```

**Level 1 (Repositories):**
```
ticker_repository
market_data_repository
prediction_repository
intraday_prediction_repository
reference_levels_repository
fibonacci_pivot_repository
block_prediction_repository
└─ Depends on: supabase_client (implicit via BaseRepository)
```

**Level 2 (Data Fetchers):**
```
data_fetcher
└─ Depends on: market_data_repository
```

**Level 3 (Core Services):**
```
cache_service
├─ ticker_repository
├─ market_data_repository
├─ prediction_repository
├─ intraday_prediction_repository
└─ reference_levels_repository

prediction_calculation_service
└─ data_fetcher

block_prediction_service
├─ data_fetcher
├─ block_prediction_repository
├─ ticker_repository
└─ market_status_service (⚠️ manual init)

data_sync_service
├─ data_fetcher
├─ ticker_repository
├─ market_data_repository
├─ prediction_repository
└─ reference_levels_repository
```

**Level 4 (Orchestration Services):**
```
aggregation_service
├─ cache_service
├─ prediction_calculation_service
├─ formatting_service
├─ ticker_repository
└─ intraday_prediction_repository

market_analysis_service (Facade)
├─ cache_service
├─ prediction_calculation_service
├─ formatting_service
└─ aggregation_service
```

**Level 5 (Background Jobs):**
```
scheduler
├─ prediction_service (⚠️ LEGACY - not found)
├─ data_sync_service
├─ intraday_prediction_service
└─ verification_service
```

---

## 6. Testing & Mock-ability Analysis

### 6.1 Current Test Structure

**Test files found:**
```
tests/unit/test_container.py
tests/unit/services/test_market_status_service.py
tests/unit/services/test_block_prediction_service.py
tests/unit/services/test_block_verification_service.py
tests/integration/services/test_market_aware_predictions.py
```

### 6.2 Mock-ability Assessment

| Component | Mock-ability | Challenges |
|-----------|-------------|------------|
| **Repositories** | ✅ Easy | BaseRepository interface, constructor-injected |
| **Data Fetcher** | ✅ Medium | Concrete class, but injected |
| **Services (DI)** | ✅ Easy | All constructor-injected |
| **MarketStatusService** | ❌ Hard | Self-instantiated in constructors |
| **SchedulerJobTrackingService** | ❌ Hard | Self-instantiated |
| **Configuration** | ❌ Hard | Imported directly, not injected |

### 6.3 Testing Infrastructure Improvements

**Current Issues:**

1. **Manual mock setup required:**
   ```python
   # Must mock every dependency manually
   mock_fetcher = Mock(spec=YahooFinanceDataFetcher)
   mock_repo = Mock(spec=BlockPredictionRepository)
   mock_ticker_repo = Mock(spec=TickerRepository)
   
   service = BlockPredictionService(
       fetcher=mock_fetcher,
       block_prediction_repo=mock_repo,
       ticker_repo=mock_ticker_repo
   )
   ```

2. **MarketStatusService cannot be mocked:**
   ```python
   # BlockPredictionService.__init__ line 59
   self.market_status_service = market_status_service or MarketStatusService()
   
   # If None passed, creates real instance (test isolation broken)
   ```

3. **Container testing complexity:**
   ```python
   # Must create full container with all dependencies
   container = create_container()
   container.clear_singletons()  # Reset between tests
   ```

**Recommended Improvements:**

1. **Test container fixture:**
   ```python
   @pytest.fixture
   def test_container():
       """Create container with mock dependencies."""
       container = Container()
       
       # Register mocks
       container.register('data_fetcher', lambda c: Mock(spec=YahooFinanceDataFetcher), singleton=True)
       container.register('ticker_repository', lambda c: Mock(spec=TickerRepository), singleton=True)
       # ... register all mocks
       
       yield container
       container.clear_singletons()
   ```

2. **Service builder pattern for tests:**
   ```python
   class BlockPredictionServiceBuilder:
       def __init__(self):
           self.fetcher = Mock(spec=YahooFinanceDataFetcher)
           self.repo = Mock(spec=BlockPredictionRepository)
           self.ticker_repo = Mock(spec=TickerRepository)
           self.market_status = Mock(spec=MarketStatusService)
       
       def with_fetcher(self, fetcher):
           self.fetcher = fetcher
           return self
       
       def build(self):
           return BlockPredictionService(
               fetcher=self.fetcher,
               block_prediction_repo=self.repo,
               ticker_repo=self.ticker_repo,
               market_status_service=self.market_status
           )
   ```

3. **Mandatory DI (no fallback instantiation):**
   ```python
   # BAD (current):
   self.market_status_service = market_status_service or MarketStatusService()
   
   # GOOD (strict DI):
   if market_status_service is None:
       raise ValueError("market_status_service must be provided")
   self.market_status_service = market_status_service
   ```

---

## 7. Configuration Management

### 7.1 Current Configuration Pattern

**Configuration modules:**
```
nasdaq_predictor/config/
├── __init__.py
├── database_config.py
├── market_config.py
├── scheduler_config.py
└── settings.py
```

**Usage pattern (problematic):**
```python
# Services import config directly
from ..config.scheduler_config import SchedulerConfig

class SchedulerJobTrackingService:
    def __init__(self):
        self.tracking_enabled = SchedulerConfig.TRACK_JOB_EXECUTION
        self.history_enabled = SchedulerConfig.TRACK_EXECUTION_HISTORY
```

**Issues:**
- ❌ Cannot override config in tests
- ❌ Tight coupling to specific config module
- ❌ Hard to swap config sources (env vars, files, etc.)

### 7.2 Recommended Configuration Injection

**Approach 1: Config objects via DI**

```python
# 1. Define config dataclass
@dataclass
class SchedulerConfig:
    track_execution: bool
    track_history: bool
    job_timeout: int

# 2. Register in container
container.register(
    'scheduler_config',
    lambda c: SchedulerConfig(
        track_execution=os.getenv('TRACK_EXECUTION', 'true') == 'true',
        track_history=os.getenv('TRACK_HISTORY', 'true') == 'true',
        job_timeout=int(os.getenv('JOB_TIMEOUT', '300'))
    ),
    singleton=True
)

# 3. Inject into services
def _init_scheduler_job_tracking_service(container):
    config = container.resolve('scheduler_config')
    return SchedulerJobTrackingService(config=config)

# 4. Use in service
class SchedulerJobTrackingService:
    def __init__(self, config: SchedulerConfig):
        self.config = config
```

**Approach 2: Options pattern**

```python
class BlockPredictionOptions:
    def __init__(self, enable_caching: bool = True, cache_ttl: int = 300):
        self.enable_caching = enable_caching
        self.cache_ttl = cache_ttl

class BlockPredictionService:
    def __init__(
        self,
        fetcher: YahooFinanceDataFetcher,
        block_prediction_repo: BlockPredictionRepository,
        ticker_repo: TickerRepository,
        options: Optional[BlockPredictionOptions] = None
    ):
        self.options = options or BlockPredictionOptions()
```

---

## 8. Orchestration Patterns & Complex Flows

### 8.1 Current Orchestration Flow

**Example: 24-hour block prediction generation**

```
User Request: POST /api/block-predictions/generate
    │
    ▼
API Route (block_prediction_routes.py)
    │
    ├─ container.resolve('block_prediction_service')
    │
    ▼
BlockPredictionService.generate_24h_block_predictions()
    │
    ├─ Loop 24 hours (0-23)
    │   │
    │   ├─ BlockPredictionService.generate_block_prediction()
    │   │   │
    │   │   ├─ _resolve_ticker_uuid_strict()
    │   │   │   └─ TickerRepository.get_ticker_by_symbol()
    │   │   │
    │   │   ├─ _fetch_hourly_bars()
    │   │   │   └─ YahooFinanceDataFetcher.fetch_historical_data()
    │   │   │       └─ MarketDataRepository.get_bars() (Supabase fallback)
    │   │   │
    │   │   ├─ calculate_hourly_volatility() (analysis module)
    │   │   │
    │   │   ├─ BlockSegmentation.segment_hour_into_blocks()
    │   │   │
    │   │   ├─ BlockPredictionEngine.generate_block_prediction()
    │   │   │
    │   │   └─ BlockPredictionRepository.store_block_prediction()
    │   │
    │   └─ Collect results
    │
    ▼
Return {predictions, generated, skipped_future, skipped_no_data}
```

**Orchestration Characteristics:**
- ✅ Service layer handles business logic orchestration
- ✅ Repository layer isolated to data access
- ✅ Analysis modules (volatility, segmentation) are stateless utilities
- ⚠️ No transaction management (each repository call is independent)
- ⚠️ No rollback mechanism if partial batch fails

### 8.2 Facade Pattern Analysis

**MarketAnalysisService as Facade:**

```python
class MarketAnalysisService:
    """Facade for market analysis operations."""
    
    def __init__(self, cache_service, prediction_service, formatting_service, aggregation_service):
        self.cache_service = cache_service
        self.prediction_service = prediction_service
        self.formatting_service = formatting_service
        self.aggregation_service = aggregation_service
    
    def process_ticker_data(self, ticker_symbol: str):
        # Try cache first
        cached = self.cache_service.get_cached_prediction(ticker_symbol)
        if cached:
            return cached
        
        # Calculate fresh
        fresh = self.prediction_service.calculate_fresh_data(ticker_symbol)
        return fresh
    
    def get_market_data(self, tickers):
        # Delegate to aggregation
        return self.aggregation_service.analyze_all_tickers(tickers)
    
    def get_market_summary(self, tickers):
        # Delegate to aggregation
        return self.aggregation_service.get_market_summary(tickers)
```

**Assessment:**
- ⚠️ **Thin delegation:** All methods just call underlying services
- ⚠️ **Limited orchestration:** No complex multi-service coordination
- ✅ **Single entry point:** Good for API consumers
- ❌ **Questionable value:** Could API routes call services directly?

**Recommendation:**
- Keep facade if it adds cross-cutting concerns (logging, auth, rate limiting)
- Consider removing if it's just pass-through delegation
- Add value through transaction coordination or error handling

### 8.3 Missing Orchestration Patterns

**1. Unit of Work Pattern**

Currently, multi-repository operations have no transaction coordination:

```python
# Example: DataSyncService stores to multiple tables
def sync_ticker_data(self, ticker_id, ticker_symbol):
    # Store market data
    self.market_data_repo.store_market_data(bars)
    
    # Store reference levels
    self.ref_levels_repo.store_reference_levels(levels)
    
    # Store prediction
    self.prediction_repo.store_prediction(prediction)
    
    # If prediction.store fails, market_data and ref_levels are orphaned
```

**Recommendation:** Implement Unit of Work for transactional consistency.

**2. Saga Pattern**

For long-running operations (24-hour batch generation), no compensation logic:

```python
# If hour 15 fails, hours 0-14 are stored but batch is incomplete
result = generate_24h_block_predictions(ticker, date)
# result['generated'] = [0,1,2,...,14]  # Partial success
# result['skipped_no_data'] = [15,16,17,...,23]  # Failures
```

**Recommendation:** Add compensation/retry logic or idempotent generation.

---

## 9. Service Lifecycle & Scope Management

### 9.1 Current Lifecycle Strategy

**All services are singletons:**

```python
container.register('block_prediction_service', _init_block_prediction_service, singleton=True)
container.register('data_sync_service', _init_data_sync_service, singleton=True)
# ... all services registered as singleton=True
```

**Implications:**

✅ **Performance:**
- Services created once, reused across requests
- Shared repository connections (connection pooling)
- Lower memory overhead

⚠️ **State management:**
- Services must be stateless or thread-safe
- Shared state can cause race conditions
- No per-request scoping

❌ **Testing:**
- Singletons persist across tests
- Must call `container.clear_singletons()` between tests
- Hard to isolate test state

### 9.2 Recommended Lifecycle Scopes

| Service | Current | Recommended | Reason |
|---------|---------|-------------|--------|
| **Repositories** | Singleton | Singleton | Stateless, connection pooling |
| **DataFetcher** | Singleton | Singleton | Stateless, rate limiting benefits |
| **CacheService** | Singleton | Singleton | In-memory cache state |
| **FormattingService** | Singleton | Singleton | Stateless utility |
| **BlockPredictionService** | Singleton | **Scoped** | May hold request-specific state |
| **DataSyncService** | Singleton | **Scoped** | Long-running operations |
| **MarketStatusService** | Not registered | Singleton | Stateless utility |
| **SchedulerJobTrackingService** | Not registered | Singleton | Shared metrics state |

**Scoped Services Pattern:**

```python
class Container:
    def register_scoped(self, name: str, factory: Callable):
        """Register service with per-request scope."""
        self._services[name] = {"factory": factory, "scope": "request"}
    
    def resolve_scoped(self, name: str, scope_id: str):
        """Resolve service with scope isolation."""
        if scope_id not in self._scoped_instances:
            self._scoped_instances[scope_id] = {}
        
        if name not in self._scoped_instances[scope_id]:
            self._scoped_instances[scope_id][name] = self._services[name]["factory"](self)
        
        return self._scoped_instances[scope_id][name]
    
    def clear_scope(self, scope_id: str):
        """Clear scoped instances (e.g., at end of request)."""
        self._scoped_instances.pop(scope_id, None)
```

**Usage in Flask:**

```python
@app.before_request
def before_request():
    g.scope_id = str(uuid.uuid4())

@app.teardown_request
def teardown_request(exception=None):
    app.container.clear_scope(g.scope_id)

@app.route('/api/predictions/<ticker>')
def get_prediction(ticker):
    service = app.container.resolve_scoped('block_prediction_service', g.scope_id)
    return service.generate_prediction(ticker)
```

---

## 10. Circular Dependency Detection & Prevention

### 10.1 Current Risk Assessment

**No active circular dependencies detected**, but several high-risk patterns:

**Risk 1: Service Cross-Dependencies**
```
AggregationService → PredictionCalculationService
PredictionCalculationService → (potential future) AggregationService
```
Currently safe, but adding reverse dependency would create cycle.

**Risk 2: Scheduler Bidirectional Reference**
```
Scheduler → [multiple services]
Services → (future need) SchedulerStatus/Control
```
Currently avoided by keeping scheduler as global singleton.

**Risk 3: Repository Circular References**
```
PredictionRepository → (potential) TickerRepository
TickerRepository → (potential) PredictionRepository
```
BaseRepository pattern prevents this by enforcing single-table focus.

### 10.2 Detection Strategy

**Recommended: Add circular dependency detection to container**

```python
class Container:
    def __init__(self):
        self._services = {}
        self._singletons = {}
        self._resolution_stack = []  # Track current resolution chain
    
    def resolve(self, name: str) -> Any:
        # Check for circular dependency
        if name in self._resolution_stack:
            cycle = ' → '.join(self._resolution_stack + [name])
            raise CircularDependencyException(
                f"Circular dependency detected: {cycle}"
            )
        
        # Push to resolution stack
        self._resolution_stack.append(name)
        
        try:
            # ... normal resolution logic ...
            result = self._services[name]["factory"](self)
        finally:
            # Pop from resolution stack
            self._resolution_stack.pop()
        
        return result
```

**Testing circular dependencies:**

```python
def test_no_circular_dependencies():
    """Verify container has no circular dependencies."""
    container = create_container()
    
    # Try to resolve every registered service
    for service_name in container.get_all_services():
        try:
            container.resolve(service_name)
            container.clear_singletons()  # Reset for next test
        except CircularDependencyException as e:
            pytest.fail(f"Circular dependency in {service_name}: {e}")
```

### 10.3 Prevention Guidelines

**1. Dependency Direction Rules**

```
API Layer
   ↓ (can depend on)
Service Layer (Orchestration)
   ↓ (can depend on)
Service Layer (Business Logic)
   ↓ (can depend on)
Repository Layer
   ↓ (can depend on)
Infrastructure Layer
```

**Never reverse dependencies** (lower layer depending on higher layer).

**2. Event-Driven Decoupling**

For bidirectional communication needs:

```python
# BAD: Service A depends on Service B, Service B depends on Service A
class ServiceA:
    def __init__(self, service_b: ServiceB):
        self.service_b = service_b

class ServiceB:
    def __init__(self, service_a: ServiceA):  # CIRCULAR!
        self.service_a = service_a

# GOOD: Use event bus for decoupling
class ServiceA:
    def __init__(self, event_bus: EventBus):
        self.event_bus = event_bus
    
    def do_something(self):
        self.event_bus.publish('service_a.event', data)

class ServiceB:
    def __init__(self, event_bus: EventBus):
        self.event_bus = event_bus
        self.event_bus.subscribe('service_a.event', self.handle_event)
    
    def handle_event(self, data):
        # React to ServiceA events without direct dependency
        pass
```

**3. Interface Segregation**

Split interfaces to break cycles:

```python
# BAD: Shared interface creates cycle risk
class IUserService:
    def get_user(self, id): pass
    def notify_order(self, user_id, order): pass  # Used by OrderService

class IOrderService:
    def create_order(self, user_id): pass
    def get_user_orders(self, user_id): pass  # Uses UserService

# GOOD: Segregate interfaces
class IUserReader:
    def get_user(self, id): pass

class IOrderNotificationHandler:
    def notify_order(self, user_id, order): pass

# OrderService depends only on IUserReader (no cycle)
# UserService implements IOrderNotificationHandler (no cycle)
```

---

## 11. Refactoring Plan

### Phase 1: Fix Critical DI Gaps (Priority: HIGH)

**1.1 Register Missing Services**

```python
# Add to container.py

def _init_market_status_service(container):
    """Initialize market status service."""
    from .services.market_status_service import MarketStatusService
    return MarketStatusService()

def _init_scheduler_job_tracking_service(container):
    """Initialize scheduler job tracking service with DI."""
    from .services.scheduler_job_tracking_service import SchedulerJobTrackingService
    return SchedulerJobTrackingService(
        repository=container.resolve('scheduler_job_execution_repository')
    )

# Register
container.register('market_status_service', _init_market_status_service, singleton=True)
container.register('scheduler_job_tracking_service', _init_scheduler_job_tracking_service, singleton=True)
```

**1.2 Update Service Constructors**

```python
# BlockPredictionService - remove fallback instantiation
class BlockPredictionService:
    def __init__(
        self,
        fetcher: YahooFinanceDataFetcher,
        block_prediction_repo: BlockPredictionRepository,
        ticker_repo: TickerRepository,
        market_status_service: MarketStatusService  # Mandatory, no default
    ):
        if market_status_service is None:
            raise ValueError("market_status_service must be provided")
        
        self.fetcher = fetcher
        self.block_prediction_repo = block_prediction_repo
        self.ticker_repo = ticker_repo
        self.market_status_service = market_status_service

# SchedulerJobTrackingService - inject repository
class SchedulerJobTrackingService:
    def __init__(self, repository: SchedulerJobExecutionRepository):
        if repository is None:
            raise ValueError("repository must be provided")
        
        self.repository = repository
        self.tracking_enabled = SchedulerConfig.TRACK_JOB_EXECUTION
        self.history_enabled = SchedulerConfig.TRACK_EXECUTION_HISTORY
```

**1.3 Update Factory Functions**

```python
def _init_block_prediction_service(container):
    """Initialize block prediction service with full DI."""
    from .services.block_prediction_service import BlockPredictionService
    
    return BlockPredictionService(
        fetcher=container.resolve("data_fetcher"),
        block_prediction_repo=container.resolve("block_prediction_repository"),
        ticker_repo=container.resolve("ticker_repository"),
        market_status_service=container.resolve("market_status_service")  # Now injected
    )
```

**Expected Impact:**
- ✅ All services fully DI-managed
- ✅ Improved testability (can mock MarketStatusService)
- ✅ Consistent initialization pattern
- ⚠️ Breaking change (must update all call sites)

---

### Phase 2: Configuration Injection (Priority: MEDIUM)

**2.1 Create Configuration Objects**

```python
# nasdaq_predictor/config/service_configs.py

from dataclasses import dataclass
from typing import Optional

@dataclass
class CacheServiceConfig:
    """Configuration for CacheService."""
    cache_duration_minutes: int = 5
    enable_cache: bool = True

@dataclass
class BlockPredictionConfig:
    """Configuration for BlockPredictionService."""
    bar_interval_minutes: int = 5
    enable_market_status_check: bool = True
    strict_ticker_resolution: bool = True

@dataclass
class SchedulerJobTrackingConfig:
    """Configuration for SchedulerJobTrackingService."""
    track_execution: bool = True
    track_history: bool = True
    failure_alert_threshold: int = 2

@dataclass
class DataSyncConfig:
    """Configuration for DataSyncService."""
    batch_size: int = 100
    retry_attempts: int = 3
    timeout_seconds: int = 300
```

**2.2 Register Configs in Container**

```python
def _init_cache_service_config(container):
    """Initialize cache service configuration."""
    from .config.service_configs import CacheServiceConfig
    import os
    
    return CacheServiceConfig(
        cache_duration_minutes=int(os.getenv('CACHE_DURATION_MINUTES', '5')),
        enable_cache=os.getenv('ENABLE_CACHE', 'true').lower() == 'true'
    )

# Register config
container.register('cache_service_config', _init_cache_service_config, singleton=True)

# Update service factory to inject config
def _init_cache_service_v2(container):
    from .services.cache_service import CacheService
    
    return CacheService(
        ticker_repo=container.resolve("ticker_repository"),
        market_data_repo=container.resolve("market_data_repository"),
        prediction_repo=container.resolve("prediction_repository"),
        intraday_repo=container.resolve("intraday_prediction_repository"),
        ref_levels_repo=container.resolve("reference_levels_repository"),
        config=container.resolve("cache_service_config")  # Inject config
    )
```

**2.3 Update Service Constructors**

```python
# CacheService with injected config
class CacheService:
    def __init__(
        self,
        ticker_repo: TickerRepository,
        market_data_repo: MarketDataRepository,
        prediction_repo: PredictionRepository,
        intraday_repo: IntradayPredictionRepository,
        ref_levels_repo: ReferenceLevelsRepository,
        config: Optional[CacheServiceConfig] = None
    ):
        self.ticker_repo = ticker_repo
        self.market_data_repo = market_data_repo
        self.prediction_repo = prediction_repo
        self.intraday_repo = intraday_repo
        self.ref_levels_repo = ref_levels_repo
        
        # Use injected config or defaults
        self.config = config or CacheServiceConfig()
        
        # Configuration values now come from config object
        self.CACHE_DURATION_MINUTES = self.config.cache_duration_minutes
```

**Expected Impact:**
- ✅ Testable configuration (can inject test configs)
- ✅ Environment-agnostic services
- ✅ Centralized config management
- ✅ Type-safe configuration values

---

### Phase 3: Interface-Based DI (Priority: MEDIUM)

**3.1 Define Service Interfaces**

```python
# nasdaq_predictor/interfaces/services.py

from abc import ABC, abstractmethod
from typing import List, Dict, Any, Optional
from datetime import datetime

class IDataFetcher(ABC):
    """Interface for market data fetching."""
    
    @abstractmethod
    def fetch_historical_data(
        self,
        ticker_id: str,
        ticker_symbol: str,
        start: datetime,
        end: datetime,
        interval: str
    ) -> List[Dict[str, Any]]:
        """Fetch historical OHLC data."""
        pass

class IMarketStatusProvider(ABC):
    """Interface for market status detection."""
    
    @abstractmethod
    def get_market_status(self, ticker: str, at_time: Optional[datetime] = None):
        """Get market status for ticker."""
        pass
    
    @abstractmethod
    def is_market_open(self, ticker: str, at_time: Optional[datetime] = None) -> bool:
        """Quick check if market is open."""
        pass

class IPredictionService(ABC):
    """Interface for prediction generation."""
    
    @abstractmethod
    def generate_block_prediction(self, ticker: str, hour_start: datetime):
        """Generate block prediction for specific hour."""
        pass
    
    @abstractmethod
    def get_hourly_prediction(self, ticker: str, hour_start: datetime):
        """Retrieve stored prediction."""
        pass
```

**3.2 Implement Interfaces**

```python
# Existing classes implement interfaces
class YahooFinanceDataFetcher(IDataFetcher):
    """Yahoo Finance implementation of IDataFetcher."""
    
    def fetch_historical_data(self, ticker_id, ticker_symbol, start, end, interval):
        # Existing implementation
        pass

class MarketStatusService(IMarketStatusProvider):
    """Market status implementation."""
    
    def get_market_status(self, ticker, at_time=None):
        # Existing implementation
        pass
    
    def is_market_open(self, ticker, at_time=None):
        # Existing implementation
        pass
```

**3.3 Use Interfaces in Service Constructors**

```python
# Services depend on interfaces, not concrete classes
class BlockPredictionService:
    def __init__(
        self,
        fetcher: IDataFetcher,  # Interface, not concrete class
        block_prediction_repo: BlockPredictionRepository,
        ticker_repo: TickerRepository,
        market_status_service: IMarketStatusProvider  # Interface
    ):
        self.fetcher = fetcher
        self.block_prediction_repo = block_prediction_repo
        self.ticker_repo = ticker_repo
        self.market_status_service = market_status_service
```

**Expected Impact:**
- ✅ Improved testability (easy to create test doubles)
- ✅ Open/Closed principle compliance
- ✅ Decoupled from concrete implementations
- ✅ Easier to swap implementations (e.g., AlpacaDataFetcher, AlphaVantageDataFetcher)

---

### Phase 4: Scope Management (Priority: LOW)

**4.1 Add Scoped Lifecycle Support**

```python
# Container enhancement for scoped services
class Container:
    def __init__(self):
        self._services = {}
        self._singletons = {}
        self._scoped_instances = {}  # scope_id -> {service_name -> instance}
    
    def register(self, name: str, factory: Callable, lifecycle: str = 'transient'):
        """Register service with lifecycle: singleton, scoped, or transient."""
        self._services[name] = {"factory": factory, "lifecycle": lifecycle}
    
    def begin_scope(self, scope_id: str):
        """Begin a new scope (e.g., request scope)."""
        self._scoped_instances[scope_id] = {}
    
    def end_scope(self, scope_id: str):
        """End scope and cleanup scoped instances."""
        self._scoped_instances.pop(scope_id, None)
    
    def resolve(self, name: str, scope_id: Optional[str] = None):
        """Resolve service with lifecycle awareness."""
        service_def = self._services[name]
        lifecycle = service_def["lifecycle"]
        
        if lifecycle == "singleton":
            if name not in self._singletons:
                self._singletons[name] = service_def["factory"](self)
            return self._singletons[name]
        
        elif lifecycle == "scoped":
            if scope_id is None:
                raise ValueError(f"Scoped service '{name}' requires scope_id")
            
            if scope_id not in self._scoped_instances:
                self._scoped_instances[scope_id] = {}
            
            if name not in self._scoped_instances[scope_id]:
                self._scoped_instances[scope_id][name] = service_def["factory"](self)
            
            return self._scoped_instances[scope_id][name]
        
        else:  # transient
            return service_def["factory"](self)
```

**4.2 Flask Integration**

```python
# app.py - add scope management
@app.before_request
def before_request():
    """Begin request scope."""
    g.scope_id = str(uuid.uuid4())
    app.container.begin_scope(g.scope_id)

@app.teardown_request
def teardown_request(exception=None):
    """End request scope."""
    if hasattr(g, 'scope_id'):
        app.container.end_scope(g.scope_id)

# API routes use scoped resolution
@app.route('/api/predictions/<ticker>')
def get_prediction(ticker):
    service = app.container.resolve('block_prediction_service', scope_id=g.scope_id)
    return service.generate_prediction(ticker)
```

**4.3 Service Registration with Scopes**

```python
# Singleton services (shared across all requests)
container.register('ticker_repository', _init_ticker_repository, lifecycle='singleton')
container.register('market_status_service', _init_market_status_service, lifecycle='singleton')
container.register('cache_service', _init_cache_service, lifecycle='singleton')

# Scoped services (per-request instances)
container.register('block_prediction_service', _init_block_prediction_service, lifecycle='scoped')
container.register('data_sync_service', _init_data_sync_service, lifecycle='scoped')

# Transient services (new instance every time)
container.register('formatting_service', _init_formatting_service, lifecycle='transient')
```

**Expected Impact:**
- ✅ Better request isolation
- ✅ Reduced singleton state issues
- ✅ Clearer service lifecycle semantics
- ⚠️ Increased complexity (must manage scopes)

---

### Phase 5: Circular Dependency Detection (Priority: MEDIUM)

**5.1 Add Detection to Container**

```python
class CircularDependencyException(Exception):
    """Raised when circular dependency detected."""
    pass

class Container:
    def __init__(self):
        self._services = {}
        self._singletons = {}
        self._resolution_stack = []  # Track current resolution path
    
    def resolve(self, name: str):
        """Resolve service with circular dependency detection."""
        if name in self._resolution_stack:
            cycle_path = ' → '.join(self._resolution_stack + [name])
            raise CircularDependencyException(
                f"Circular dependency detected: {cycle_path}\n"
                f"Service '{name}' is already being resolved in the current chain."
            )
        
        self._resolution_stack.append(name)
        
        try:
            service_def = self._services[name]
            
            if service_def["singleton"]:
                if name not in self._singletons:
                    self._singletons[name] = service_def["factory"](self)
                result = self._singletons[name]
            else:
                result = service_def["factory"](self)
            
            return result
        
        finally:
            self._resolution_stack.pop()
```

**5.2 Add Startup Validation**

```python
# app.py - validate container on startup
def validate_container(container: Container):
    """Validate container has no circular dependencies."""
    logger.info("Validating DI container...")
    
    services = container.get_all_services()
    errors = []
    
    for service_name in services:
        try:
            logger.debug(f"  Validating {service_name}...")
            container.resolve(service_name)
            container.clear_singletons()  # Reset for next validation
        except CircularDependencyException as e:
            errors.append(str(e))
            logger.error(f"  ✗ {service_name}: {e}")
        except Exception as e:
            errors.append(f"{service_name}: {str(e)}")
            logger.warning(f"  ⚠ {service_name}: {e}")
    
    if errors:
        raise RuntimeError(
            f"Container validation failed with {len(errors)} errors:\n" +
            '\n'.join(errors)
        )
    
    logger.info(f"✓ Container validated successfully ({len(services)} services)")

# Run validation at startup
with app.app_context():
    try:
        validate_container(app.container)
    except RuntimeError as e:
        logger.error(f"Container validation failed: {e}")
        sys.exit(1)
```

**Expected Impact:**
- ✅ Early detection of circular dependencies
- ✅ Fail-fast on misconfiguration
- ✅ Improved developer experience
- ✅ Prevents runtime resolution failures

---

### Phase 6: Enhance Testing Infrastructure (Priority: MEDIUM)

**6.1 Test Container Factory**

```python
# tests/fixtures/container.py

import pytest
from unittest.mock import Mock
from nasdaq_predictor.container import Container
from nasdaq_predictor.interfaces.services import IDataFetcher, IMarketStatusProvider

@pytest.fixture
def mock_container():
    """Create container with mocked dependencies for testing."""
    container = Container()
    
    # Mock repositories
    container.register(
        'ticker_repository',
        lambda c: Mock(name='TickerRepository'),
        singleton=True
    )
    container.register(
        'market_data_repository',
        lambda c: Mock(name='MarketDataRepository'),
        singleton=True
    )
    container.register(
        'block_prediction_repository',
        lambda c: Mock(name='BlockPredictionRepository'),
        singleton=True
    )
    
    # Mock external services
    container.register(
        'data_fetcher',
        lambda c: Mock(spec=IDataFetcher, name='DataFetcher'),
        singleton=True
    )
    container.register(
        'market_status_service',
        lambda c: Mock(spec=IMarketStatusProvider, name='MarketStatusService'),
        singleton=True
    )
    
    # Register real services with mocked dependencies
    from nasdaq_predictor.services.block_prediction_service import BlockPredictionService
    container.register(
        'block_prediction_service',
        lambda c: BlockPredictionService(
            fetcher=c.resolve('data_fetcher'),
            block_prediction_repo=c.resolve('block_prediction_repository'),
            ticker_repo=c.resolve('ticker_repository'),
            market_status_service=c.resolve('market_status_service')
        ),
        singleton=False  # Create fresh instance for each test
    )
    
    yield container
    container.clear_singletons()
```

**6.2 Service Builder Pattern**

```python
# tests/builders/service_builders.py

from unittest.mock import Mock
from nasdaq_predictor.services.block_prediction_service import BlockPredictionService

class BlockPredictionServiceBuilder:
    """Builder for BlockPredictionService with sensible test defaults."""
    
    def __init__(self):
        self.fetcher = Mock(name='DataFetcher')
        self.block_repo = Mock(name='BlockPredictionRepository')
        self.ticker_repo = Mock(name='TickerRepository')
        self.market_status = Mock(name='MarketStatusService')
    
    def with_fetcher(self, fetcher):
        """Override data fetcher."""
        self.fetcher = fetcher
        return self
    
    def with_ticker_repo(self, ticker_repo):
        """Override ticker repository."""
        self.ticker_repo = ticker_repo
        return self
    
    def with_market_status(self, market_status):
        """Override market status service."""
        self.market_status = market_status
        return self
    
    def build(self) -> BlockPredictionService:
        """Build service instance."""
        return BlockPredictionService(
            fetcher=self.fetcher,
            block_prediction_repo=self.block_repo,
            ticker_repo=self.ticker_repo,
            market_status_service=self.market_status
        )

# Usage in tests
def test_block_prediction_with_custom_fetcher():
    custom_fetcher = Mock()
    custom_fetcher.fetch_historical_data.return_value = [...]
    
    service = (BlockPredictionServiceBuilder()
               .with_fetcher(custom_fetcher)
               .build())
    
    result = service.generate_block_prediction('NQ=F', datetime.now())
    assert result is not None
```

**6.3 Integration Test Support**

```python
# tests/fixtures/integration_container.py

@pytest.fixture(scope='session')
def integration_container():
    """
    Create container with real dependencies for integration tests.
    
    Uses test database, real repositories, but mocked external APIs.
    """
    container = Container()
    
    # Real database connection (test DB)
    import os
    os.environ['SUPABASE_URL'] = 'https://test.supabase.co'
    os.environ['SUPABASE_KEY'] = 'test-key'
    
    # Real repositories (connected to test DB)
    from nasdaq_predictor.database.repositories.ticker_repository import TickerRepository
    container.register('ticker_repository', lambda c: TickerRepository(), singleton=True)
    
    # ... register other real repositories ...
    
    # Mock external APIs (yfinance, etc.)
    container.register(
        'data_fetcher',
        lambda c: Mock(spec=IDataFetcher),
        singleton=True
    )
    
    # Real services with real dependencies
    from nasdaq_predictor.services.block_prediction_service import BlockPredictionService
    container.register(
        'block_prediction_service',
        lambda c: BlockPredictionService(
            fetcher=c.resolve('data_fetcher'),
            block_prediction_repo=c.resolve('block_prediction_repository'),
            ticker_repo=c.resolve('ticker_repository'),
            market_status_service=c.resolve('market_status_service')
        ),
        singleton=False
    )
    
    return container

# Integration test example
def test_end_to_end_prediction_flow(integration_container):
    """Test complete prediction flow with real database."""
    service = integration_container.resolve('block_prediction_service')
    
    # Mock fetcher to return test data
    fetcher = integration_container.resolve('data_fetcher')
    fetcher.fetch_historical_data.return_value = get_test_bars()
    
    # Execute
    result = service.generate_block_prediction('NQ=F', datetime(2025, 1, 15, 10, 0))
    
    # Verify stored in database
    stored = service.get_hourly_prediction('NQ=F', datetime(2025, 1, 15, 10, 0))
    assert stored is not None
    assert stored.prediction in ['BULLISH', 'BEARISH', 'NEUTRAL']
```

**Expected Impact:**
- ✅ Easier test setup
- ✅ Reduced test boilerplate
- ✅ Better separation of unit/integration tests
- ✅ Reusable test fixtures

---

## 12. Service Orchestration Diagrams

### 12.1 Current Service Dependency Graph

```
┌──────────────────────────────────────────────────────────────────────┐
│                       API Layer (Flask Routes)                        │
│                                                                        │
│  /api/block-predictions/<ticker>                                      │
│  /api/block-predictions/generate                                      │
│  /api/market/data                                                     │
└────────────────────────────┬─────────────────────────────────────────┘
                             │
                             │ container.resolve(...)
                             │
                             ▼
┌──────────────────────────────────────────────────────────────────────┐
│                      Service Layer (Orchestration)                    │
│                                                                        │
│  ┌────────────────────────────────────────────────────────┐          │
│  │ MarketAnalysisService (Facade - 190 LOC)               │          │
│  │  Responsibilities:                                      │          │
│  │  - Route requests to cache or calculation              │          │
│  │  - Coordinate batch processing                         │          │
│  │  - Provide high-level market analysis API              │          │
│  │                                                         │          │
│  │  Dependencies:                                          │          │
│  │  ├─ CacheService                                        │          │
│  │  ├─ PredictionCalculationService                       │          │
│  │  ├─ FormattingService                                  │          │
│  │  └─ AggregationService                                 │          │
│  └─────────┬──────────────────────────────────────────────┘          │
│            │                                                           │
│            │ delegates to                                             │
│            ▼                                                           │
│  ┌────────────────────────────────────────────────────────┐          │
│  │ AggregationService (328 LOC)                           │          │
│  │  Responsibilities:                                      │          │
│  │  - Multi-ticker batch processing                       │          │
│  │  - Market summary generation                           │          │
│  │  - Ticker-level orchestration                          │          │
│  │                                                         │          │
│  │  Dependencies:                                          │          │
│  │  ├─ CacheService (database-first)                      │          │
│  │  ├─ PredictionCalculationService (fresh calc)          │          │
│  │  ├─ FormattingService (response formatting)            │          │
│  │  ├─ TickerRepository (ticker lookup)                   │          │
│  │  └─ IntradayPredictionRepository (intraday data)       │          │
│  └─────────┬──────────────────────────────────────────────┘          │
│            │                                                           │
└────────────┼───────────────────────────────────────────────────────────┘
             │
             │ uses
             ▼
┌──────────────────────────────────────────────────────────────────────┐
│                   Business Logic Services                             │
│                                                                        │
│  ┌────────────────────────────────────────────────────────┐          │
│  │ BlockPredictionService (684 LOC) - 7-Block Framework   │          │
│  │  Responsibilities:                                      │          │
│  │  - Generate 7-block hourly predictions                 │          │
│  │  - Fetch intra-hour OHLC bars                          │          │
│  │  - Calculate volatility                                │          │
│  │  - Apply BlockPredictionEngine                         │          │
│  │  - Store predictions                                   │          │
│  │                                                         │          │
│  │  Dependencies:                                          │          │
│  │  ├─ YahooFinanceDataFetcher (market data)              │          │
│  │  ├─ BlockPredictionRepository (storage)                │          │
│  │  ├─ TickerRepository (ticker resolution)               │          │
│  │  └─ MarketStatusService (⚠️ manual init)               │          │
│  └────────────────────────────────────────────────────────┘          │
│                                                                        │
│  ┌────────────────────────────────────────────────────────┐          │
│  │ DataSyncService (698 LOC) - Market Data Sync           │          │
│  │  Responsibilities:                                      │          │
│  │  - Sync market data to Supabase                        │          │
│  │  - Calculate predictions                               │          │
│  │  - Store reference levels                              │          │
│  │  - Multi-ticker orchestration                          │          │
│  │                                                         │          │
│  │  Dependencies:                                          │          │
│  │  ├─ YahooFinanceDataFetcher                            │          │
│  │  ├─ TickerRepository                                   │          │
│  │  ├─ MarketDataRepository                               │          │
│  │  ├─ PredictionRepository                               │          │
│  │  └─ ReferenceLevelsRepository                          │          │
│  └────────────────────────────────────────────────────────┘          │
│                                                                        │
│  ┌────────────────────────────────────────────────────────┐          │
│  │ CacheService (246 LOC) - Database-First Caching        │          │
│  │  Responsibilities:                                      │          │
│  │  - Retrieve cached predictions from DB                 │          │
│  │  - Check prediction freshness (< 5 min)                │          │
│  │  - Format cached responses                             │          │
│  │                                                         │          │
│  │  Dependencies:                                          │          │
│  │  ├─ TickerRepository                                   │          │
│  │  ├─ MarketDataRepository                               │          │
│  │  ├─ PredictionRepository                               │          │
│  │  ├─ IntradayPredictionRepository                       │          │
│  │  └─ ReferenceLevelsRepository                          │          │
│  └────────────────────────────────────────────────────────┘          │
│                                                                        │
│  ┌────────────────────────────────────────────────────────┐          │
│  │ MarketStatusService (422 LOC) - ⚠️ Not in Container    │          │
│  │  Responsibilities:                                      │          │
│  │  - Market hours detection                              │          │
│  │  - Trading session identification                      │          │
│  │  - Next event calculation                              │          │
│  │  - Last trading date resolution                        │          │
│  │                                                         │          │
│  │  Dependencies: NONE (reads from config)                │          │
│  └────────────────────────────────────────────────────────┘          │
│                                                                        │
│  ┌────────────────────────────────────────────────────────┐          │
│  │ IntradayPredictionService (368 LOC)                    │          │
│  │ VerificationService (355 LOC)                          │          │
│  │ AccuracyService (369 LOC)                              │          │
│  │ FormattingService (364 LOC)                            │          │
│  └────────────────────────────────────────────────────────┘          │
└────────────────────────────┬─────────────────────────────────────────┘
                             │
                             │ uses
                             ▼
┌──────────────────────────────────────────────────────────────────────┐
│                   Repository Layer (Data Access)                      │
│                                                                        │
│  ┌────────────────────────────────────────────────────────┐          │
│  │ BaseRepository (Abstract CRUD)                         │          │
│  │  Provides:                                             │          │
│  │  - select(filters)                                     │          │
│  │  - select_all(filters)                                 │          │
│  │  - insert(data)                                        │          │
│  │  - update(id, data)                                    │          │
│  │  - delete(id)                                          │          │
│  │                                                         │          │
│  │  Subclasses implement:                                 │          │
│  │  - _map_response(data) -> Entity                       │          │
│  └────────────────────────────────────────────────────────┘          │
│                       ▲                                               │
│                       │ extends                                       │
│           ┌───────────┴───────────┐                                  │
│           │                       │                                  │
│  ┌────────┴────────┐   ┌──────────┴──────────┐                      │
│  │ TickerRepo      │   │ MarketDataRepo      │                      │
│  │ (tickers)       │   │ (market_data)       │                      │
│  └─────────────────┘   └─────────────────────┘                      │
│                                                                        │
│  ┌─────────────────┐   ┌─────────────────────┐                      │
│  │ PredictionRepo  │   │ IntradayPredRepo    │                      │
│  │ (predictions)   │   │ (intraday_pred)     │                      │
│  └─────────────────┘   └─────────────────────┘                      │
│                                                                        │
│  ┌─────────────────┐   ┌─────────────────────┐                      │
│  │ BlockPredRepo   │   │ RefLevelsRepo       │                      │
│  │ (block_pred)    │   │ (reference_levels)  │                      │
│  └─────────────────┘   └─────────────────────┘                      │
│                                                                        │
│  ┌─────────────────┐   ┌─────────────────────┐                      │
│  │ FibonacciRepo   │   │ SchedulerJobRepo    │                      │
│  │ (fib_pivots)    │   │ (scheduler_jobs)    │                      │
│  └─────────────────┘   └─────────────────────┘                      │
│                                                                        │
│  All repositories share:                                              │
│  └─ SupabaseClient (Singleton connection)                            │
└──────────────────────────────────────────────────────────────────────┘
                             │
                             ▼
┌──────────────────────────────────────────────────────────────────────┐
│                    Infrastructure Layer                               │
│                                                                        │
│  SupabaseClient                                                       │
│  └─ PostgreSQL Database (Supabase)                                   │
│                                                                        │
│  YahooFinanceDataFetcher                                              │
│  └─ yfinance API (External)                                          │
└──────────────────────────────────────────────────────────────────────┘
```

### 12.2 Scheduler Orchestration Flow

```
┌──────────────────────────────────────────────────────────────────────┐
│                    APScheduler (Background Jobs)                      │
│                                                                        │
│  Job 1: Market Data Sync (Every 15 min during market hours)          │
│  ├─ Trigger: Cron(minutes=2,17,32,47)                                │
│  ├─ Tracked by: SchedulerJobTrackingService                          │
│  └─ Execution Flow:                                                  │
│      1. SchedulerJobTrackingService.track_job_execution() decorator  │
│      2. DataSyncService.sync_all_tickers()                           │
│         ├─ For each enabled ticker:                                  │
│         │   ├─ Fetch OHLC data (yfinance → Supabase fallback)        │
│         │   ├─ Calculate reference levels                            │
│         │   ├─ Generate predictions                                  │
│         │   ├─ Store to Supabase                                     │
│         │   └─ Log results                                           │
│         └─ Return sync summary                                       │
│      3. SchedulerJobTrackingService updates metrics                  │
│         ├─ Store execution record (duration, status, errors)         │
│         ├─ Update job metrics (success rate, avg duration)           │
│         └─ Create failure alerts if 2+ consecutive failures          │
│                                                                        │
│  Job 2: Prediction Calculation (Every 15 min, offset by 3 min)       │
│  ├─ Trigger: Cron(minutes=5,20,35,50)                                │
│  ├─ Tracked by: SchedulerJobTrackingService                          │
│  └─ Execution Flow:                                                  │
│      1. Decorator tracks start time                                  │
│      2. IntradayPredictionService.generate_predictions()             │
│         ├─ Generate 9am prediction                                   │
│         ├─ Generate 10am prediction                                  │
│         └─ Store to database                                         │
│      3. Metrics updated                                              │
│                                                                        │
│  Job 3: Prediction Verification (Every 15 min, offset by 5 min)      │
│  ├─ Trigger: Cron(minutes=7,22,37,52)                                │
│  ├─ Tracked by: SchedulerJobTrackingService                          │
│  └─ Execution Flow:                                                  │
│      1. Decorator tracks execution                                   │
│      2. VerificationService.verify_predictions()                     │
│         ├─ Fetch predictions awaiting verification                   │
│         ├─ Get actual market outcomes                                │
│         ├─ Compare prediction vs actual                              │
│         └─ Update prediction records with results                    │
│      3. Metrics updated                                              │
│                                                                        │
│  Job 4: Data Cleanup (Daily at 02:00 UTC)                            │
│  ├─ Trigger: Cron(hour=2, minute=0)                                  │
│  └─ Execution Flow:                                                  │
│      1. Delete old market data (> 90 days)                           │
│      2. Delete old predictions (> 365 days)                          │
│      3. Archive job execution logs (> 30 days)                       │
│      4. Vacuum database tables                                       │
└──────────────────────────────────────────────────────────────────────┘
          │
          │ Uses
          ▼
┌──────────────────────────────────────────────────────────────────────┐
│              SchedulerJobTrackingService (406 LOC)                    │
│              ⚠️ Not in DI Container (manually instantiated)           │
│                                                                        │
│  Decorator: @track_job_execution(job_id, job_name)                   │
│  ├─ Before execution:                                                │
│  │   ├─ Create JobExecution record (status=RUNNING)                 │
│  │   └─ Record start time                                            │
│  ├─ Execute job function                                             │
│  └─ After execution:                                                 │
│      ├─ Calculate duration                                           │
│      ├─ Update JobExecution (status, duration, records_processed)    │
│      ├─ Update JobMetrics (success_rate, avg_duration, etc.)         │
│      └─ If failure:                                                  │
│          ├─ Check consecutive failures                               │
│          └─ Create FailedJobAlert if threshold reached               │
│                                                                        │
│  Storage:                                                             │
│  └─ SchedulerJobExecutionRepository                                  │
│      ├─ scheduler_job_executions table (execution history)           │
│      ├─ scheduler_job_metrics table (aggregated metrics)             │
│      └─ scheduler_failed_job_alerts table (failure alerts)           │
└──────────────────────────────────────────────────────────────────────┘
```

### 12.3 Block Prediction Generation Flow

```
┌──────────────────────────────────────────────────────────────────────┐
│  API Request: POST /api/block-predictions/generate                   │
│  Body: {ticker: "NQ=F", date: "2025-01-15"}                          │
└────────────────────────────┬─────────────────────────────────────────┘
                             │
                             ▼
┌──────────────────────────────────────────────────────────────────────┐
│  Flask Route Handler (block_prediction_routes.py)                    │
│  ├─ URL decode ticker                                                │
│  ├─ Parse date parameter                                             │
│  └─ container.resolve('block_prediction_service')                    │
└────────────────────────────┬─────────────────────────────────────────┘
                             │
                             ▼
┌──────────────────────────────────────────────────────────────────────┐
│  BlockPredictionService.generate_24h_block_predictions()             │
│  ├─ Input: ticker="NQ=F", date=2025-01-15                            │
│  └─ Loop: for hour in range(24):                                     │
│      ├─ hour_start = date + timedelta(hours=hour)                   │
│      ├─ Skip if hour_start > now (future hours)                     │
│      └─ Call generate_block_prediction(ticker, hour_start)           │
└────────────────────────────┬─────────────────────────────────────────┘
                             │
                             ▼
┌──────────────────────────────────────────────────────────────────────┐
│  BlockPredictionService.generate_block_prediction()                  │
│  (Single hour prediction generation)                                 │
│                                                                        │
│  Step 1: Resolve Ticker UUID                                         │
│  ├─ _resolve_ticker_uuid_strict("NQ=F")                              │
│  │   ├─ TickerRepository.get_ticker_by_symbol("NQ=F")                │
│  │   ├─ Returns UUID: "abc-123-def"                                  │
│  │   └─ If not found: raise TickerNotFoundException                 │
│  └─ ticker_uuid = "abc-123-def"                                      │
│                                                                        │
│  Step 2: Fetch Hourly OHLC Bars                                      │
│  ├─ _fetch_hourly_bars(ticker_uuid, "NQ=F", hour_start)              │
│  │   ├─ hour_end = hour_start + 1 hour                               │
│  │   ├─ YahooFinanceDataFetcher.fetch_historical_data()              │
│  │   │   ├─ Try Supabase: MarketDataRepository.get_bars()            │
│  │   │   └─ Fallback: yfinance.download(interval='5m')               │
│  │   └─ Filter bars within hour: [bar1, bar2, ..., bar12]            │
│  └─ bars = List[Dict] (12x 5-minute bars for 1 hour)                 │
│                                                                        │
│  Step 3: Calculate Volatility                                        │
│  ├─ opening_price = bars[0]['open']                                  │
│  ├─ calculate_hourly_volatility(bars, opening_price)                 │
│  │   └─ Returns volatility in points (e.g., 15.3)                    │
│  └─ volatility = 15.3                                                │
│                                                                        │
│  Step 4: Segment Hour into 7 Blocks                                  │
│  ├─ BlockSegmentation.segment_hour_into_blocks(bars, hour_start)     │
│  │   ├─ Block 1: 00:00 - 08:34 (513 seconds)                         │
│  │   ├─ Block 2: 08:34 - 17:08                                       │
│  │   ├─ Block 3: 17:08 - 25:42                                       │
│  │   ├─ Block 4: 25:42 - 34:17                                       │
│  │   ├─ Block 5: 34:17 - 42:51 (Prediction Point)                    │
│  │   ├─ Block 6: 42:51 - 51:25                                       │
│  │   └─ Block 7: 51:25 - 60:00                                       │
│  └─ blocks = [BlockAnalysis1, ..., BlockAnalysis7]                   │
│                                                                        │
│  Step 5: Extract Blocks 1-5 for Prediction                           │
│  ├─ blocks_1_5 = blocks[0:5]                                         │
│  └─ Blocks 6-7 are future (prediction targets)                       │
│                                                                        │
│  Step 6: Generate Prediction using Decision Trees                    │
│  ├─ BlockPredictionEngine.generate_block_prediction()                │
│  │   ├─ Analyze early bias (blocks 1-2)                              │
│  │   ├─ Detect sustained counter-moves (blocks 3-5)                  │
│  │   ├─ Calculate deviation at block 5 end                           │
│  │   ├─ Apply decision tree logic                                    │
│  │   └─ Return prediction result                                     │
│  └─ prediction_result = {                                            │
│        "prediction": "BULLISH",                                       │
│        "confidence": 72.5,                                            │
│        "strength": "STRONG",                                          │
│        "early_bias": "UP",                                            │
│        "early_bias_strength": "STRONG",                               │
│        "has_sustained_counter": False,                                │
│        "counter_direction": None,                                     │
│        "deviation_at_5_7": 12.4                                       │
│      }                                                                │
│                                                                        │
│  Step 7: Create BlockPrediction Object                               │
│  ├─ _create_block_prediction(ticker_uuid, hour_start, ...)           │
│  │   ├─ Format block data for storage                                │
│  │   ├─ Calculate prediction timestamp (5/7 point)                   │
│  │   └─ Build BlockPrediction instance                               │
│  └─ block_prediction = BlockPrediction(...)                          │
│                                                                        │
│  Step 8: Store in Database                                           │
│  ├─ BlockPredictionRepository.store_block_prediction(block_prediction)│
│  │   └─ INSERT INTO block_predictions (...)                          │
│  └─ Returns stored prediction                                        │
└────────────────────────────┬─────────────────────────────────────────┘
                             │
                             ▼
┌──────────────────────────────────────────────────────────────────────┐
│  Return to API:                                                       │
│  {                                                                    │
│    "predictions": [BlockPrediction1, ..., BlockPrediction24],        │
│    "generated": [0, 1, 2, ..., 14],  // Hours with data              │
│    "skipped_future": [15, 16, ..., 23],  // Future hours             │
│    "skipped_no_data": [],  // Hours without data                     │
│    "total_generated": 15                                              │
│  }                                                                    │
└──────────────────────────────────────────────────────────────────────┘
```

---

## 13. Best Practices & Maintenance Guidelines

### 13.1 Service Development Guidelines

**When creating a new service:**

1. **Define clear responsibility**
   - Service should have single, focused purpose
   - Name should describe what it does (e.g., `BlockPredictionService`, not `PredictionManager`)

2. **Use constructor injection**
   ```python
   class MyService:
       def __init__(self, dependency1: IDependency1, dependency2: IDependency2):
           if dependency1 is None or dependency2 is None:
               raise ValueError("Dependencies must be provided")
           self.dependency1 = dependency1
           self.dependency2 = dependency2
   ```

3. **Avoid service locator pattern**
   ```python
   # BAD
   def my_method(self):
       service = container.resolve('other_service')  # Hidden dependency
   
   # GOOD
   def __init__(self, other_service: IOtherService):
       self.other_service = other_service
   
   def my_method(self):
       self.other_service.do_something()
   ```

4. **Register in container**
   ```python
   # container.py
   def _init_my_service(container):
       from .services.my_service import MyService
       return MyService(
           dependency1=container.resolve('dependency1'),
           dependency2=container.resolve('dependency2')
       )
   
   container.register('my_service', _init_my_service, singleton=True)
   ```

5. **Write tests first**
   ```python
   def test_my_service():
       mock_dep1 = Mock(spec=IDependency1)
       mock_dep2 = Mock(spec=IDependency2)
       
       service = MyService(mock_dep1, mock_dep2)
       
       result = service.do_something()
       
       assert result is not None
       mock_dep1.method.assert_called_once()
   ```

### 13.2 Dependency Management

**Adding a new dependency to existing service:**

1. Update constructor signature
2. Update factory function in `container.py`
3. Update all tests with new mock
4. Validate no circular dependencies introduced

**Example:**
```python
# Before
class BlockPredictionService:
    def __init__(self, fetcher, repo):
        self.fetcher = fetcher
        self.repo = repo

# After - adding market_status
class BlockPredictionService:
    def __init__(self, fetcher, repo, market_status):
        self.fetcher = fetcher
        self.repo = repo
        self.market_status = market_status

# Update factory
def _init_block_prediction_service(container):
    return BlockPredictionService(
        fetcher=container.resolve('data_fetcher'),
        repo=container.resolve('block_prediction_repository'),
        market_status=container.resolve('market_status_service')  # NEW
    )

# Update tests
def test_block_prediction():
    service = BlockPredictionService(
        fetcher=Mock(),
        repo=Mock(),
        market_status=Mock()  # NEW
    )
```

### 13.3 Testing Strategy

**Unit Tests:**
- Test services in isolation with mocked dependencies
- Use builder pattern for complex service setup
- Focus on business logic, not infrastructure

**Integration Tests:**
- Test service composition with real dependencies
- Use test container with test database
- Mock only external APIs (yfinance, etc.)

**Container Tests:**
- Validate all services can be resolved
- Check for circular dependencies
- Verify singleton behavior

**Example test structure:**
```
tests/
├── unit/
│   ├── services/
│   │   ├── test_block_prediction_service.py
│   │   ├── test_data_sync_service.py
│   │   └── ...
│   ├── repositories/
│   │   └── test_ticker_repository.py
│   └── test_container.py
├── integration/
│   ├── test_prediction_flow.py
│   └── test_data_sync_flow.py
├── fixtures/
│   ├── container.py  # Mock container fixture
│   └── builders.py   # Service builders
└── conftest.py
```

### 13.4 Performance Monitoring

**Track service performance:**

1. **Add timing decorators**
   ```python
   import time
   import functools
   
   def track_performance(func):
       @functools.wraps(func)
       def wrapper(*args, **kwargs):
           start = time.time()
           result = func(*args, **kwargs)
           duration = time.time() - start
           
           logger.info(f"{func.__name__} took {duration:.2f}s")
           
           # Optional: Send to metrics service
           metrics.record('service.duration', duration, tags={'method': func.__name__})
           
           return result
       return wrapper
   
   class MyService:
       @track_performance
       def expensive_operation(self):
           # ... implementation ...
           pass
   ```

2. **Monitor dependency resolution time**
   ```python
   class Container:
       def resolve(self, name: str):
           start = time.time()
           result = self._resolve_internal(name)
           duration = time.time() - start
           
           if duration > 1.0:  # Slow resolution
               logger.warning(f"Slow resolution: {name} took {duration:.2f}s")
           
           return result
   ```

3. **Use SchedulerJobTrackingService metrics**
   - All scheduled jobs automatically tracked
   - Monitor success rates, average duration, failures
   - Set alerts on consecutive failures

### 13.5 Scaling Considerations

**As system grows:**

1. **Split large services**
   - If service exceeds ~500 LOC, consider splitting
   - Extract focused sub-services
   - Use composition over inheritance

2. **Consider async/await for I/O-bound operations**
   ```python
   class AsyncDataFetcher:
       async def fetch_historical_data(self, ticker, start, end):
           async with aiohttp.ClientSession() as session:
               async with session.get(url) as response:
                   return await response.json()
   ```

3. **Implement caching strategically**
   - Use CacheService for database-backed caching
   - Consider Redis for distributed caching
   - Implement cache invalidation strategy

4. **Add rate limiting**
   ```python
   from ratelimit import limits, sleep_and_retry
   
   class YahooFinanceDataFetcher:
       @sleep_and_retry
       @limits(calls=2000, period=3600)  # 2000 calls per hour
       def fetch_historical_data(self, ...):
           # ... implementation ...
           pass
   ```

5. **Monitor resource usage**
   - Track memory usage of singleton services
   - Monitor database connection pool
   - Use profiling tools (cProfile, memory_profiler)

---

## 14. Critical Issues & Immediate Action Items

### Priority 1 - CRITICAL (Fix Immediately)

1. **Register MarketStatusService in DI container**
   - Location: `/Users/soonjeongguan/Desktop/Repository/CLAUDECODE/NQP/nasdaq_predictor/container.py`
   - Action: Add factory function and registration
   - Impact: Enables testing and proper lifecycle management
   - Estimated effort: 30 minutes

2. **Register SchedulerJobTrackingService in DI container**
   - Location: Same as above
   - Action: Inject SchedulerJobExecutionRepository
   - Impact: Consistent dependency management
   - Estimated effort: 30 minutes

3. **Remove fallback instantiation in BlockPredictionService**
   - Location: `/Users/soonjeongguan/Desktop/Repository/CLAUDECODE/NQP/nasdaq_predictor/services/block_prediction_service.py` line 59
   - Current: `self.market_status_service = market_status_service or MarketStatusService()`
   - Action: Make parameter required, no default
   - Impact: Strict DI enforcement
   - Estimated effort: 15 minutes

4. **Add circular dependency detection to Container**
   - Location: Container.resolve() method
   - Action: Track resolution stack, detect cycles
   - Impact: Prevents runtime resolution failures
   - Estimated effort: 1 hour

### Priority 2 - HIGH (Fix This Sprint)

5. **Validate container on application startup**
   - Location: `/Users/soonjeongguan/Desktop/Repository/CLAUDECODE/NQP/app.py`
   - Action: Resolve all services during bootstrap to detect misconfigurations
   - Impact: Fail-fast on startup instead of runtime
   - Estimated effort: 1 hour

6. **Remove legacy `prediction_service` registration**
   - Location: container.py line 211
   - Issue: Registered but service not found in codebase
   - Action: Remove registration or implement missing service
   - Impact: Clean up dead code
   - Estimated effort: 30 minutes

7. **Create test container fixture**
   - Location: New file `tests/fixtures/container.py`
   - Action: Provide mock container for all tests
   - Impact: Consistent test setup, reduced boilerplate
   - Estimated effort: 2 hours

8. **Add configuration injection**
   - Location: All services that import config modules
   - Action: Create config dataclasses, inject via DI
   - Impact: Testable configuration, environment-agnostic services
   - Estimated effort: 4 hours

### Priority 3 - MEDIUM (Next Sprint)

9. **Implement interface-based DI**
   - Location: New file `nasdaq_predictor/interfaces/services.py`
   - Action: Define IDataFetcher, IMarketStatusProvider, etc.
   - Impact: Improved testability, OCP compliance
   - Estimated effort: 4 hours

10. **Add scope management to Container**
    - Location: Container class
    - Action: Support singleton, scoped, transient lifecycles
    - Impact: Better request isolation
    - Estimated effort: 3 hours

11. **Create service builder pattern for tests**
    - Location: New file `tests/builders/service_builders.py`
    - Action: Implement builders for all services
    - Impact: Easier test setup
    - Estimated effort: 3 hours

12. **Document all service dependencies in docstrings**
    - Location: All service constructors
    - Action: Add comprehensive docstrings with dependency explanations
    - Impact: Better developer onboarding
    - Estimated effort: 2 hours

---

## 15. Conclusion

The NASDAQ Predictor demonstrates a **solid foundation** in dependency injection architecture with a custom lightweight container, well-defined service layer, and comprehensive repository pattern. The system has successfully evolved from a monolithic structure to a modular service-oriented architecture.

### Key Achievements

✅ **Mature DI Container:** Custom implementation with singleton support, lazy instantiation, and service composition  
✅ **Clean Service Layer:** 14 focused services with clear responsibilities  
✅ **Repository Pattern:** Excellent abstraction with BaseRepository eliminating code duplication  
✅ **Market-Aware Architecture:** Sophisticated market status detection and timezone handling  
✅ **Job Tracking:** Comprehensive scheduler monitoring with metrics and alerts

### Critical Improvements Needed

1. Register missing services (MarketStatusService, SchedulerJobTrackingService)
2. Add circular dependency detection
3. Implement configuration injection
4. Enhance testing infrastructure with fixtures and builders
5. Move towards interface-based DI for better abstraction

### Architecture Quality Score

| Dimension | Score | Comments |
|-----------|-------|----------|
| **DI Implementation** | 8/10 | Solid container, but missing 2 services |
| **SOLID Compliance** | 7/10 | Good SRP/LSP, needs better DIP/OCP |
| **Testability** | 6/10 | Mockable but requires better fixtures |
| **Maintainability** | 8/10 | Clear structure, good documentation |
| **Scalability** | 7/10 | Well-architected for growth |
| **Overall** | **7.2/10** | **Production-ready with room for improvement** |

This architecture is **production-ready** and demonstrates mature software engineering practices. The recommended refactoring plan will address the identified gaps and position the system for future growth and maintainability.

---

**End of Report**
