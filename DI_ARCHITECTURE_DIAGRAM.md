# NASDAQ Predictor - Dependency Injection Architecture Diagram

## Service Layer Composition

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                         DEPENDENCY INJECTION CONTAINER                       │
│                                                                               │
│  Lifecycle Management:                                                        │
│  - Singletons: 23 services (shared across app)                              │
│  - Lazy Instantiation: On-demand service creation                           │
│  - Factory Pattern: Lambda factories for each service                       │
│                                                                               │
│  ┌───────────────────────────────────────────────────────────────────────┐  │
│  │                    INFRASTRUCTURE LAYER                                │  │
│  │                                                                         │  │
│  │  ┌──────────────────┐                                                  │  │
│  │  │ SupabaseClient   │ (Singleton - Database Connection)               │  │
│  │  └─────────┬────────┘                                                  │  │
│  │            │                                                            │  │
│  │            │ shared by all repositories                                │  │
│  │            ▼                                                            │  │
│  └───────────────────────────────────────────────────────────────────────┘  │
│                                                                               │
│  ┌───────────────────────────────────────────────────────────────────────┐  │
│  │                      REPOSITORY LAYER (9 Repos)                        │  │
│  │                                                                         │  │
│  │  All extend BaseRepository (Abstract CRUD)                             │  │
│  │                                                                         │  │
│  │  ┌─────────────────────┐   ┌──────────────────────┐                   │  │
│  │  │ TickerRepository    │   │ MarketDataRepository │                   │  │
│  │  │ - Ticker lookup     │   │ - OHLC data storage  │                   │  │
│  │  │ - Symbol → UUID     │   │ - Bar queries        │                   │  │
│  │  └─────────────────────┘   └──────────────────────┘                   │  │
│  │                                                                         │  │
│  │  ┌─────────────────────┐   ┌──────────────────────┐                   │  │
│  │  │ PredictionRepo      │   │ IntradayPredRepo     │                   │  │
│  │  │ - Daily predictions │   │ - 9am/10am preds     │                   │  │
│  │  └─────────────────────┘   └──────────────────────┘                   │  │
│  │                                                                         │  │
│  │  ┌─────────────────────┐   ┌──────────────────────┐                   │  │
│  │  │ BlockPredictionRepo │   │ ReferenceLevelsRepo  │                   │  │
│  │  │ - 7-block preds     │   │ - Trading levels     │                   │  │
│  │  └─────────────────────┘   └──────────────────────┘                   │  │
│  │                                                                         │  │
│  │  ┌─────────────────────┐   ┌──────────────────────┐                   │  │
│  │  │ FibonacciPivotRepo  │   │ SchedulerJobRepo     │                   │  │
│  │  │ - Fibonacci levels  │   │ - Job execution logs │                   │  │
│  │  └─────────────────────┘   └──────────────────────┘                   │  │
│  └───────────────────────────────────────────────────────────────────────┘  │
│                                                                               │
│  ┌───────────────────────────────────────────────────────────────────────┐  │
│  │                       DATA FETCHER LAYER                               │  │
│  │                                                                         │  │
│  │  ┌──────────────────────────────────────────────────────────┐         │  │
│  │  │ YahooFinanceDataFetcher (Singleton)                      │         │  │
│  │  │  - Fetch historical OHLC data                            │         │  │
│  │  │  - Supabase fallback for cached data                     │         │  │
│  │  │  - Rate limiting and error handling                      │         │  │
│  │  │                                                           │         │  │
│  │  │  Dependencies:                                            │         │  │
│  │  │  └─ MarketDataRepository (for Supabase queries)          │         │  │
│  │  └──────────────────────────────────────────────────────────┘         │  │
│  └───────────────────────────────────────────────────────────────────────┘  │
│                                                                               │
│  ┌───────────────────────────────────────────────────────────────────────┐  │
│  │                    BUSINESS LOGIC SERVICES                             │  │
│  │                                                                         │  │
│  │  ┌────────────────────────────────────────────────────────┐           │  │
│  │  │ BlockPredictionService (684 LOC) - CORE SERVICE        │           │  │
│  │  │  - 7-block hourly prediction generation                │           │  │
│  │  │  - Volatility calculation                              │           │  │
│  │  │  - Block segmentation & analysis                       │           │  │
│  │  │                                                         │           │  │
│  │  │  Dependencies:                                          │           │  │
│  │  │  ├─ YahooFinanceDataFetcher                            │           │  │
│  │  │  ├─ BlockPredictionRepository                          │           │  │
│  │  │  ├─ TickerRepository                                   │           │  │
│  │  │  └─ MarketStatusService (⚠️ MANUAL INIT)               │           │  │
│  │  └────────────────────────────────────────────────────────┘           │  │
│  │                                                                         │  │
│  │  ┌────────────────────────────────────────────────────────┐           │  │
│  │  │ DataSyncService (698 LOC)                              │           │  │
│  │  │  - Market data synchronization to Supabase             │           │  │
│  │  │  - Reference level calculation                         │           │  │
│  │  │  - Prediction generation                               │           │  │
│  │  │                                                         │           │  │
│  │  │  Dependencies: 5 repos + data fetcher                  │           │  │
│  │  └────────────────────────────────────────────────────────┘           │  │
│  │                                                                         │  │
│  │  ┌────────────────────────────────────────────────────────┐           │  │
│  │  │ CacheService (246 LOC)                                 │           │  │
│  │  │  - Database-first caching (< 5 min freshness)          │           │  │
│  │  │  - Formatted response retrieval                        │           │  │
│  │  │                                                         │           │  │
│  │  │  Dependencies: 5 repositories                          │           │  │
│  │  └────────────────────────────────────────────────────────┘           │  │
│  │                                                                         │  │
│  │  ┌────────────────────────────────────────────────────────┐           │  │
│  │  │ PredictionCalculationService (193 LOC)                 │           │  │
│  │  │  - Fresh yfinance calculations                         │           │  │
│  │  │                                                         │           │  │
│  │  │  Dependencies: YahooFinanceDataFetcher                 │           │  │
│  │  └────────────────────────────────────────────────────────┘           │  │
│  │                                                                         │  │
│  │  ┌────────────────────────────────────────────────────────┐           │  │
│  │  │ IntradayPredictionService (368 LOC)                    │           │  │
│  │  │ VerificationService (355 LOC)                          │           │  │
│  │  │ AccuracyService (369 LOC)                              │           │  │
│  │  │ FormattingService (364 LOC)                            │           │  │
│  │  │ IntradayVerificationService (303 LOC)                  │           │  │
│  │  │ BlockVerificationService (423 LOC)                     │           │  │
│  │  └────────────────────────────────────────────────────────┘           │  │
│  └───────────────────────────────────────────────────────────────────────┘  │
│                                                                               │
│  ┌───────────────────────────────────────────────────────────────────────┐  │
│  │                   ORCHESTRATION SERVICES                               │  │
│  │                                                                         │  │
│  │  ┌────────────────────────────────────────────────────────┐           │  │
│  │  │ AggregationService (328 LOC)                           │           │  │
│  │  │  - Multi-ticker batch processing                       │           │  │
│  │  │  - Market summary generation                           │           │  │
│  │  │                                                         │           │  │
│  │  │  Dependencies:                                          │           │  │
│  │  │  ├─ CacheService                                        │           │  │
│  │  │  ├─ PredictionCalculationService                       │           │  │
│  │  │  ├─ FormattingService                                  │           │  │
│  │  │  ├─ TickerRepository                                   │           │  │
│  │  │  └─ IntradayPredictionRepository                       │           │  │
│  │  └────────────────────────────────────────────────────────┘           │  │
│  │                                                                         │  │
│  │  ┌────────────────────────────────────────────────────────┐           │  │
│  │  │ MarketAnalysisService (190 LOC) - FACADE               │           │  │
│  │  │  - Single entry point for market analysis              │           │  │
│  │  │  - Delegates to specialized services                   │           │  │
│  │  │                                                         │           │  │
│  │  │  Dependencies:                                          │           │  │
│  │  │  ├─ CacheService                                        │           │  │
│  │  │  ├─ PredictionCalculationService                       │           │  │
│  │  │  ├─ FormattingService                                  │           │  │
│  │  │  └─ AggregationService                                 │           │  │
│  │  └────────────────────────────────────────────────────────┘           │  │
│  └───────────────────────────────────────────────────────────────────────┘  │
│                                                                               │
│  ┌───────────────────────────────────────────────────────────────────────┐  │
│  │              MISSING FROM CONTAINER (Critical Issue)                   │  │
│  │                                                                         │  │
│  │  ⚠️  MarketStatusService (422 LOC)                                     │  │
│  │      - Market hours detection                                          │  │
│  │      - Trading session identification                                  │  │
│  │      - Currently: Manually instantiated in services                    │  │
│  │      - Fix: Register as singleton with proper DI                       │  │
│  │                                                                         │  │
│  │  ⚠️  SchedulerJobTrackingService (406 LOC)                             │  │
│  │      - Job execution tracking & metrics                                │  │
│  │      - Currently: Self-instantiates repository                         │  │
│  │      - Fix: Inject SchedulerJobExecutionRepository                     │  │
│  └───────────────────────────────────────────────────────────────────────┘  │
│                                                                               │
│  ┌───────────────────────────────────────────────────────────────────────┐  │
│  │                      SCHEDULER LAYER                                   │  │
│  │                                                                         │  │
│  │  ┌────────────────────────────────────────────────────────┐           │  │
│  │  │ APScheduler (Background Jobs)                          │           │  │
│  │  │  - Market data sync (every 15 min)                     │           │  │
│  │  │  - Prediction calculation (every 15 min)               │           │  │
│  │  │  - Prediction verification (every 15 min)              │           │  │
│  │  │  - Data cleanup (daily)                                │           │  │
│  │  │                                                         │           │  │
│  │  │  Dependencies:                                          │           │  │
│  │  │  ├─ DataSyncService                                    │           │  │
│  │  │  ├─ IntradayPredictionService                          │           │  │
│  │  │  ├─ VerificationService                                │           │  │
│  │  │  └─ prediction_service (⚠️ LEGACY - not found)         │           │  │
│  │  └────────────────────────────────────────────────────────┘           │  │
│  └───────────────────────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────────────────────┘


                                      ▲
                                      │
                                      │ container.resolve('service_name')
                                      │
                  ┌───────────────────┴──────────────────────┐
                  │                                           │
┌─────────────────────────────────┐     ┌───────────────────────────────────┐
│       API Routes (Flask)         │     │     Scheduler Jobs (APScheduler)  │
│                                  │     │                                   │
│  - /api/block-predictions/*      │     │  - market_data_sync               │
│  - /api/market/data              │     │  - prediction_calculation         │
│  - /api/predictions/*            │     │  - prediction_verification        │
│  - /api/scheduler/*              │     │  - data_cleanup                   │
└──────────────────────────────────┘     └───────────────────────────────────┘
```

## Service Dependency Resolution Example

**When API calls `container.resolve('block_prediction_service')`:**

```
1. Container checks if 'block_prediction_service' already instantiated (singleton cache)
   └─ If yes: Return cached instance
   └─ If no: Continue to step 2

2. Container calls factory function: _init_block_prediction_service(container)
   └─ Factory function executes:
   
   def _init_block_prediction_service(container):
       return BlockPredictionService(
           fetcher=container.resolve("data_fetcher"),           # Resolve dependency 1
           block_prediction_repo=container.resolve("block_prediction_repository"),  # Resolve dependency 2
           ticker_repo=container.resolve("ticker_repository"),  # Resolve dependency 3
       )

3. For each dependency, recursive resolution occurs:

   container.resolve("data_fetcher")
   ├─ Check singleton cache → Miss
   ├─ Call _init_data_fetcher(container)
   │   └─ return YahooFinanceDataFetcher(
   │          market_data_repo=container.resolve("market_data_repository")
   │      )
   ├─ Resolve "market_data_repository"
   │   ├─ Check singleton cache → Miss
   │   ├─ Call _init_market_data_repository()
   │   │   └─ return MarketDataRepository()
   │   │       └─ Supabase client injected via BaseRepository.__init__
   │   └─ Cache MarketDataRepository instance
   ├─ Create YahooFinanceDataFetcher instance
   └─ Cache YahooFinanceDataFetcher instance

   container.resolve("block_prediction_repository")
   ├─ Check singleton cache → Miss
   ├─ Call _init_block_prediction_repository()
   │   └─ return BlockPredictionRepository()
   └─ Cache instance

   container.resolve("ticker_repository")
   ├─ Check singleton cache → Hit (already resolved by another service)
   └─ Return cached TickerRepository instance

4. All dependencies resolved, create BlockPredictionService:
   service = BlockPredictionService(
       fetcher=<YahooFinanceDataFetcher instance>,
       block_prediction_repo=<BlockPredictionRepository instance>,
       ticker_repo=<TickerRepository instance>
   )

5. Cache BlockPredictionService instance (singleton)

6. Return service to caller
```

**Total resolution chain depth: 3 levels**
```
BlockPredictionService
├─ YahooFinanceDataFetcher
│  └─ MarketDataRepository
│     └─ SupabaseClient (implicit via BaseRepository)
├─ BlockPredictionRepository
│  └─ SupabaseClient (implicit via BaseRepository)
└─ TickerRepository
   └─ SupabaseClient (implicit via BaseRepository)
```

**Singleton sharing:**
- SupabaseClient: Shared across all 9 repositories (single database connection)
- YahooFinanceDataFetcher: Shared across all prediction services
- Repositories: Shared across all services (connection pooling)

## Critical Issues Summary

| Issue | Severity | Location | Impact |
|-------|----------|----------|--------|
| MarketStatusService not in DI | HIGH | container.py | Cannot mock in tests, hard-coded dependency |
| SchedulerJobTrackingService not in DI | HIGH | container.py | Self-instantiates repository, violates DI |
| Fallback instantiation in services | MEDIUM | BlockPredictionService line 59 | Defeats DI purpose, allows None injection |
| No circular dependency detection | MEDIUM | Container.resolve() | Runtime failures possible |
| Legacy prediction_service registration | LOW | container.py line 211 | Dead code, cleanup needed |
| Configuration not injected | MEDIUM | All services | Cannot override config in tests |

## Refactoring Priority

**Phase 1 (Week 1):**
1. Register MarketStatusService in container
2. Register SchedulerJobTrackingService in container
3. Remove fallback instantiation patterns
4. Add circular dependency detection

**Phase 2 (Week 2-3):**
5. Implement configuration injection
6. Create test container fixtures
7. Add service builder pattern for tests
8. Document all service dependencies

**Phase 3 (Week 4+):**
9. Implement interface-based DI
10. Add scope management (singleton, scoped, transient)
11. Create integration test infrastructure
12. Performance monitoring and optimization

