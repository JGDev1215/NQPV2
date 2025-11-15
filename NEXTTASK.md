# NQP Refactoring - Remaining Phases

**Status**: Phase 1 Complete ✅ | Phase 2-5 Pending

**Last Updated**: Post Phase 1 Completion
**Commit**: 9e0c86b - "Fix critical ticker ID mismatch in data sync and block prediction services"

---

## Phase 2: Remove Duplication (MEDIUM PRIORITY)

### Objective
Eliminate code duplication and consolidate duplicate implementations to improve maintainability and reduce confusion.

### Tasks

#### 2.1 Consolidate Market Services
- **Files**:
  - `nasdaq_predictor/services/market_service.py` (legacy)
  - `nasdaq_predictor/services/market_service_refactored.py` (new)
- **Action**:
  - [ ] Review both implementations for functional differences
  - [ ] Determine which implementation is actively used
  - [ ] Merge features from both versions into single implementation
  - [ ] Update container.py to reference only one service
  - [ ] Remove legacy market_service.py file
- **Acceptance Criteria**: Only one MarketService exists, all tests pass

#### 2.2 Complete Ticker Repository Migration
- **Files**:
  - `nasdaq_predictor/database/repositories/ticker_repository.py`
  - `nasdaq_predictor/database/repositories/ticker_repository_refactored.py`
- **Action**:
  - [ ] Determine if refactored version is drop-in replacement
  - [ ] If yes: Replace old version and update all imports
  - [ ] If no: Document differences and merge features
  - [ ] Remove duplicate file
  - [ ] Update container.py registrations
- **Acceptance Criteria**: Single TickerRepository exists and is used everywhere

#### 2.3 Clean Up Root-Level Utility Scripts
- **Files to organize**:
  - `app_backup.py` (909 lines - old monolithic version)
  - `backfill_24h_predictions.py` (utility script)
  - `test_implementation.py` (test script)
  - `trigger_sync.py` (manual sync trigger)
- **Action**:
  - [ ] Create `/scripts` directory in project root
  - [ ] Move all utility scripts to `/scripts`
  - [ ] Update any documentation referencing these scripts
  - [ ] Add README in `/scripts` explaining each utility
  - [ ] Consider removing obsolete scripts (e.g., app_backup.py)
- **Acceptance Criteria**: Root directory clean, utilities organized and documented

#### 2.4 Identify and Remove Dead Code
- **Investigation Areas**:
  - Legacy imports and unused dependencies
  - Commented-out code blocks
  - TODO comments indicating incomplete features
  - Duplicate model definitions (database vs domain models)
- **Action**:
  - [ ] Scan for unused imports using automated tools
  - [ ] Document any legacy code that must be kept
  - [ ] Remove safely identifiable dead code
  - [ ] Add explanatory comments for legacy code that must stay
- **Acceptance Criteria**: No obvious dead code remains, codebase is cleaner

---

## Phase 3: Performance Optimization (HIGH PRIORITY)

### Objective
Improve data sync reliability, performance, and scheduler coordination.

### Tasks

#### 3.1 Optimize Data Sync Flow
- **File**: `nasdaq_predictor/services/data_sync_service.py`
- **Current Issues**:
  - Line 159-160: Generic exceptions without context
  - Validation thresholds arbitrary (e.g., 100 minute bars = 1.5 hrs)
  - No data quality metrics tracking
- **Action**:
  - [ ] Implement job-level locking to prevent concurrent sync runs
  - [ ] Replace arbitrary validation thresholds with configurable values
  - [ ] Add data quality metrics tracking (completeness %, freshness)
  - [ ] Optimize retry logic timing (currently 10s, 20s delays)
  - [ ] Log quality metrics for monitoring
- **Performance Targets**:
  - Sync time < 30 seconds for 3 tickers
  - Data completeness >= 95%
  - Freshness < 5 minutes
- **Acceptance Criteria**: Sync runs reliably without overlaps, metrics tracked

#### 3.2 Fix Scheduler Timing Coordination
- **Current Issue**: 6-minute offset between sync (:00, :30) and prediction (:08, :38) not guaranteed
- **Files**:
  - `nasdaq_predictor/config/scheduler_config.py`
  - `nasdaq_predictor/scheduler/jobs.py`
- **Action**:
  - [ ] Implement freshness validation before prediction calculation
  - [ ] Add retry logic if market data is stale
  - [ ] Increase offset to 8-10 minutes for safety margin
  - [ ] Add scheduler logs to track job execution gaps
  - [ ] Consider event-driven triggers for predictions after data sync
- **Acceptance Criteria**: Predictions never execute with stale data (<5 min old)

#### 3.3 Add Timeout Configuration for External API Calls
- **File**: `nasdaq_predictor/data/fetcher.py`
- **Current Issue**: yfinance calls can hang indefinitely
- **Action**:
  - [ ] Add global timeout setting to config (default: 30 seconds)
  - [ ] Add request-level timeouts in YahooFinanceDataFetcher
  - [ ] Implement exponential backoff with max retries
  - [ ] Add timeout exceeded logging and metrics
  - [ ] Test timeout behavior with network simulation
- **Acceptance Criteria**: All external calls timeout gracefully after configured duration

#### 3.4 Standardize Ticker ID Usage in Read Paths
- **Files Affected**:
  - `nasdaq_predictor/data/fetcher.py:172`
  - `nasdaq_predictor/database/repositories/*`
- **Current Issue**: Query paths still mix symbol and UUID usage
- **Action**:
  - [ ] Audit all database queries for ticker_id consistency
  - [ ] Update fetcher to resolve symbol to UUID before queries
  - [ ] Update verification services (lines 222, 387) to use UUID
  - [ ] Add helper method for symbol->UUID resolution
  - [ ] Document ticker_id usage in architecture guide
- **Acceptance Criteria**: All database queries use UUID consistently

---

## Phase 4: Error Handling & Robustness (HIGH PRIORITY)

### Objective
Improve system reliability with comprehensive error handling and recovery mechanisms.

### Tasks

#### 4.1 Implement Database Retry Logic
- **Action**:
  - [ ] Create retry decorator with exponential backoff
  - [ ] Add transient error detection (connection timeouts, temporary locks)
  - [ ] Implement jitter to prevent thundering herd
  - [ ] Add retry metrics (attempts, successes, failures)
  - [ ] Test with simulated database failures
- **Retry Strategy**:
  - Max retries: 3
  - Base delay: 100ms
  - Max delay: 5 seconds
  - Exponential backoff: 2x multiplier
- **Files to Update**:
  - All repository files in `nasdaq_predictor/database/repositories/`
- **Acceptance Criteria**: Transient failures recover automatically, metrics tracked

#### 4.2 Implement Typed Exception Hierarchy
- **File**: `nasdaq_predictor/core/exceptions.py` (expand existing)
- **New Exception Classes**:
  - `DataFetchError` - yfinance/data retrieval failures
  - `DataValidationError` - OHLC validation failures
  - `SchedulerError` - Job execution errors
  - `DatabaseError` - Repository/Supabase errors
  - `ConfigurationError` - Invalid config parameters
  - `TimeoutError` - Request/operation timeouts
- **Action**:
  - [ ] Define exception hierarchy with helpful messages
  - [ ] Replace generic `Exception` raises with typed exceptions
  - [ ] Update exception handlers to catch specific types
  - [ ] Add exception logging with context
  - [ ] Document exception handling patterns
- **Acceptance Criteria**: All exceptions are typed and handled appropriately

#### 4.3 Standardize Logging and Add Monitoring Hooks
- **Current Issue**: Inconsistent logging levels (debug/info/warning mix)
- **Action**:
  - [ ] Define logging standards (when to use each level)
  - [ ] Convert to structured logging with context
  - [ ] Add logging to critical paths (data sync, predictions, errors)
  - [ ] Create metrics for key operations (sync time, prediction time, errors)
  - [ ] Add hooks for external monitoring (Sentry, DataDog, etc.)
- **Logging Standards**:
  - DEBUG: Detailed diagnostic info for developers
  - INFO: Key milestones (sync started, prediction generated)
  - WARNING: Recoverable issues (stale data, retry needed)
  - ERROR: Failures requiring attention
- **Acceptance Criteria**: Logs are structured, metrics exportable, monitoring hooks in place

#### 4.4 Add Graceful Degradation
- **Action**:
  - [ ] Implement fallback behavior if yfinance is down
  - [ ] Cache old predictions for serving stale data temporarily
  - [ ] Add circuit breaker for persistent external service failures
  - [ ] Document degradation scenarios and impact
- **Acceptance Criteria**: Service continues operating (with reduced functionality) when external APIs fail

---

## Phase 5: Code Organization & Documentation (MEDIUM PRIORITY)

### Objective
Improve code maintainability, consistency, and documentation.

### Tasks

#### 5.1 Standardize Import Patterns
- **Current Issue**: Mix of relative imports (`from ..services`) and absolute imports
- **Decision**: Use absolute imports throughout
- **Action**:
  - [ ] Audit all imports across codebase
  - [ ] Convert relative imports to absolute
  - [ ] Document import convention in ARCHITECTURE.md
  - [ ] Add linter rule to enforce convention
- **Acceptance Criteria**: All imports follow absolute pattern, linter configured

#### 5.2 Consolidate Verification Services
- **Current State**: 3 separate verification services
  - `prediction_verification_service.py`
  - `intraday_verification_service.py`
  - `block_verification_service.py`
- **Action**:
  - [ ] Analyze common patterns across services
  - [ ] Create base `VerificationService` class with common logic
  - [ ] Implement specialized verification methods
  - [ ] Update container.py and routes to use consolidated service
  - [ ] Remove duplicate files
- **Acceptance Criteria**: Single VerificationService with specialized methods

#### 5.3 Create Architecture Documentation
- **File**: Create `ARCHITECTURE.md` in project root
- **Contents**:
  - [ ] System overview diagram (ASCII or reference)
  - [ ] Data flow diagrams (sync, prediction, verification)
  - [ ] Service layer organization and responsibilities
  - [ ] Database schema overview
  - [ ] Scheduler job execution timeline
  - [ ] API endpoint organization
  - [ ] Dependency injection container structure
  - [ ] Configuration management
  - [ ] Error handling and recovery patterns
  - [ ] Import conventions
  - [ ] Coding standards and patterns
- **Acceptance Criteria**: Comprehensive architecture guide exists and is current

#### 5.4 Move Utility Scripts and Add Documentation
- **File**: Create `/scripts/README.md`
- **Contents**:
  - [ ] List of available utilities
  - [ ] Purpose and usage of each script
  - [ ] Prerequisites and dependencies
  - [ ] Examples of common operations
  - [ ] Troubleshooting tips
- **Scripts to Document**:
  - `backfill_24h_predictions.py` - Bulk prediction generation
  - `test_implementation.py` - Testing utilities
  - `trigger_sync.py` - Manual sync triggering
- **Acceptance Criteria**: All utilities documented with examples

#### 5.5 Configuration Management Improvements
- **File**: `nasdaq_predictor/config/`
- **Action**:
  - [ ] Move hardcoded thresholds to config files
  - [ ] Add validation with enforcement (not just logging)
  - [ ] Create config profiles (dev, staging, prod)
  - [ ] Document all configuration options
  - [ ] Add config loading from environment
- **Hardcoded Values to Externalize**:
  - BlockPredictionEngine thresholds (STRONG_THRESHOLD = 2.0)
  - Validation thresholds (minimum bar counts)
  - Retry delays and max retries
  - Timeout durations
  - Cache freshness thresholds
- **Acceptance Criteria**: All major configuration is externalized and validated

#### 5.6 Test Coverage Expansion
- **Action**:
  - [ ] Add unit tests for service layer (target: 80% coverage)
  - [ ] Add integration tests for data flow
  - [ ] Add scheduler job tests
  - [ ] Add error handling tests (retry logic, timeouts)
  - [ ] Add end-to-end tests for critical paths
- **Acceptance Criteria**: Test coverage >= 80% for services, integration tests for all flows

---

## Implementation Roadmap

### Priority Order
1. **Phase 1** (Complete) ✅ - Critical bugs fix
2. **Phase 3** (Next) - Performance/reliability critical for production
3. **Phase 2** - Code cleanup improves maintainability
4. **Phase 4** - Error handling improves robustness
5. **Phase 5** - Documentation and organization polish

### Estimated Effort
- Phase 2: 2-3 days
- Phase 3: 3-4 days
- Phase 4: 3-5 days
- Phase 5: 2-3 days
- **Total**: ~2-3 weeks for complete refactoring

---

## Success Criteria (All Phases Complete)

- [ ] All critical bugs fixed (Phase 1)
- [ ] No duplicate code or services (Phase 2)
- [ ] Data sync reliable with <30s execution time (Phase 3)
- [ ] Scheduler timing coordinated with no stale data issues (Phase 3)
- [ ] All external calls have timeouts (Phase 3)
- [ ] Transient database errors recover automatically (Phase 4)
- [ ] All exceptions are typed with helpful messages (Phase 4)
- [ ] Logging is structured and metrics are tracked (Phase 4)
- [ ] Graceful degradation when external services fail (Phase 4)
- [ ] Consistent import patterns throughout (Phase 5)
- [ ] Comprehensive architecture documentation (Phase 5)
- [ ] All utilities documented with examples (Phase 5)
- [ ] Configuration is externalized and validated (Phase 5)
- [ ] Test coverage >= 80% for services (Phase 5)

---

## Notes

### Known Blockers
- None identified - Phase 1 critical fix enables proceeding with remaining phases

### Dependencies
- Phase 2 should complete before Phase 5 (cleaner code easier to document)
- Phase 3 and 4 can be done in parallel
- Phase 5 can start after Phase 2

### Monitoring During Refactoring
- Keep eye on data sync execution times during Phase 3
- Monitor error rates during Phase 4 error handling changes
- Run full test suite after each phase completion

---

## Commands Reference

### Phase 2 Tasks
```bash
# Find duplicate code
find . -name "*.py" | xargs wc -l | sort -rn

# Check service imports
grep -r "from.*market_service" nasdaq_predictor/

# Check ticker repo usage
grep -r "TickerRepository" nasdaq_predictor/
```

### Phase 3 Tasks
```bash
# Monitor sync execution time
# In scheduler logs, look for "sync completed" messages

# Check data freshness
# In prediction logs, look for "data age" metrics
```

### Phase 4 Tasks
```bash
# Find bare exception handlers
grep -r "except:" nasdaq_predictor/

# Find generic Exception raises
grep -r "raise Exception" nasdaq_predictor/
```

### Phase 5 Tasks
```bash
# Check import patterns
grep -r "from \." nasdaq_predictor/ | head -20

# Test coverage
pytest --cov=nasdaq_predictor tests/
```

---

## Questions to Address

- [ ] Should `market_service.py` or `market_service_refactored.py` be kept?
- [ ] Are `app_backup.py` and other root scripts still needed?
- [ ] What monitoring/alerting system should metrics integrate with?
- [ ] Should database retry logic be automatic or manual?
- [ ] What is acceptable max timeout duration for external APIs?

---

**Last Updated**: Phase 1 Complete
**Next Phase**: Phase 2 (Remove Duplication)
**Estimated Start**: When Phase 1 is stable in production
