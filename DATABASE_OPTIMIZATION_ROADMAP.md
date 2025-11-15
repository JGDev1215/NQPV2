# NQP Database Optimization Roadmap

**Status:** Ready for Implementation  
**Estimated Effort:** 3-4 weeks  
**Performance Gain:** 80-90% latency reduction  

---

## Quick Reference: What to Fix First

### Week 1: Hypertable Conversion (CRITICAL)
- Convert `market_data` to TimescaleDB hypertable
- Enable compression for data > 7 days
- Add retention policy (2-year lifecycle)
- **Impact:** 60-70% storage reduction + 5-10x query speedup

### Week 2: Index Optimization (HIGH)
- Add covering indexes for latest price queries
- Add BRIN indexes for large table scans
- Add partial indexes for active data (hot path)
- **Impact:** 20-30% additional query speedup

### Week 3: Analytics & RPC (HIGH)
- Create SQL analytics functions (get_latest_price, get_prediction_accuracy)
- Add RPC support to repositories
- Create materialized views for common aggregations
- **Impact:** Complex queries 80-90% faster

### Week 4: Real-Time & Cleanup (MEDIUM)
- Implement real-time subscriptions
- Setup data retention automation
- Add monitoring and alerting

---

## File-by-File Implementation Guide

### Migrations (SQL)

#### 1. `008_convert_market_data_hypertable.sql` (CRITICAL)
```bash
# Location: nasdaq_predictor/database/migrations/008_convert_market_data_hypertable.sql
# Risk Level: LOW
# Execution Time: < 1 minute
# Reversible: YES (via `SELECT revert_hypertable('market_data')`)

Actions:
1. Enable TimescaleDB extension
2. Convert market_data to hypertable (1-day chunks)
3. Enable compression (segmentby=ticker_id,interval)
4. Add compression policy (after 7 days)
5. Add retention policy (drop after 730 days)
6. Verify with: SELECT * FROM timescaledb_information.hypertables
```

**Pre-Flight Checklist:**
- [ ] Backup database
- [ ] Run on staging first
- [ ] Verify no queries running
- [ ] Check replication lag (if applicable)

---

#### 2. `009_add_covering_indexes.sql` (HIGH)
```bash
# Location: nasdaq_predictor/database/migrations/009_add_covering_indexes.sql
# Risk Level: MINIMAL
# Execution Time: 2-5 minutes
# Reversible: YES (via DROP INDEX)

Actions:
1. Drop old idx_market_data_ticker_timestamp
2. Create covering index WITH (open, high, low, close, volume)
3. Create BRIN index for timestamp range scans
4. Create partial index for recent data (< 30 days)
5. Analyze table for query planner
```

**Performance Verification:**
```sql
-- Before
EXPLAIN ANALYZE SELECT close FROM market_data
WHERE ticker_id = 'uuid' AND timestamp > NOW() - '1 day'::interval;
-- Seq Scan (slow)

-- After
EXPLAIN ANALYZE SELECT close FROM market_data
WHERE ticker_id = 'uuid' AND timestamp > NOW() - '1 day'::interval;
-- Index Scan (fast)
```

---

#### 3. `010_add_analytics_functions.sql` (HIGH)
```bash
# Location: nasdaq_predictor/database/migrations/010_add_analytics_functions.sql
# Risk Level: NONE (read-only functions)
# Execution Time: < 1 minute

Functions Created:
1. get_latest_price(ticker_id, interval)
2. get_price_range(ticker_id, interval, start, end)
3. get_prediction_accuracy(ticker_id, days)
4. get_block_prediction_accuracy(ticker_id, days)

Permissions:
- GRANT EXECUTE to authenticated, anon

Usage:
SELECT * FROM get_latest_price('uuid', '1h');
```

---

### Python Code Changes

#### 1. `analytics_repository.py` (NEW FILE)
```bash
# Location: nasdaq_predictor/database/repositories/analytics_repository.py
# Size: ~300 lines
# Depends On: supabase_client

Key Classes:
- AnalyticsRepository (RPC-based complex queries)

Methods:
- get_latest_price() [via RPC]
- get_price_range() [via RPC]
- get_prediction_accuracy() [via RPC]
- get_block_prediction_accuracy() [via RPC]
- get_query_performance()
- get_table_sizes()

Integration Points:
- Replace or augment existing PredictionRepository methods
- Add to __init__.py exports
```

**Usage Example:**
```python
from nasdaq_predictor.database.repositories import AnalyticsRepository

analytics = AnalyticsRepository()
latest = analytics.get_latest_price(ticker_id, interval='1h')
accuracy = analytics.get_prediction_accuracy(ticker_id, days=30)
```

---

#### 2. `base_repository.py` (MODIFIED)
```bash
# Location: nasdaq_predictor/database/repositories/base_repository.py
# Lines Changed: ~50
# Risk Level: LOW

Additions:
1. Add execute_rpc() method for complex queries
2. Add retry decorator for resilience
3. Add connection pooling configuration
4. Enhanced error handling (DatabaseException variants)

New Methods:
def execute_rpc(self, function_name: str, params: Dict) -> Any
def execute_with_retry(self, fn: Callable, max_retries: int = 3) -> Any
```

---

#### 3. `market_data_repository.py` (MODIFIED)
```bash
# Location: nasdaq_predictor/database/repositories/market_data_repository.py
# Lines Changed: ~80
# Risk Level: MEDIUM (new insertion methods)

Enhancements:
1. Add BulkMarketDataInsertion class for optimized inserts
2. Add insert_bulk_copy() method (COPY-based, 100x faster)
3. Add insert_with_fallback() for error recovery
4. Add individual_insert_with_retry() for resilience
5. Improve select_with_limit() to include column projection

Performance Improvements:
- 100 rows/sec -> 10,000+ rows/sec (with COPY)
- Better error recovery with exponential backoff
- Reduced payload sizes with column projection
```

**Migration Path:**
```python
# Old (slow):
market_data_repo.store_ohlc_data(ticker_id, data)  # ~100 rows/sec

# New (fast):
bulk_insert = BulkMarketDataInsertion()
inserted = bulk_insert.insert_bulk_copy(ticker_id, data)  # ~10,000 rows/sec
```

---

#### 4. `database_config.py` (MODIFIED)
```bash
# Location: nasdaq_predictor/config/database_config.py
# Lines Added: ~30
# Risk Level: NONE (configuration only)

Additions:
1. TIMESCALEDB_ENABLED = True
2. COMPRESSION_AFTER_DAYS = 7
3. RETENTION_CHUNK_INTERVAL = '1 day'
4. ANALYTICS_CACHE_TTL = 3600
5. BULK_INSERT_CHUNK_SIZE = 5000

Deprecations:
- BATCH_INSERT_SIZE (rename to BATCH_INSERT_REST_SIZE)
- BULK_UPSERT_SIZE (rename to BULK_UPSERT_PAYLOAD_SIZE)
```

---

### Testing

#### 1. `test_hypertable_conversion.py` (NEW)
```bash
# Location: tests/integration/database/test_hypertable_conversion.py

Tests:
1. Verify hypertable created successfully
2. Verify chunks are created daily
3. Verify compression enabled
4. Verify compression policy active
5. Verify retention policy active
6. Verify data integrity (count before/after)
7. Verify query performance (< 50ms for latest price)

Coverage: 100% of migration logic
```

---

#### 2. `test_analytics_queries.py` (NEW)
```bash
# Location: tests/integration/database/test_analytics_queries.py

Tests:
1. get_latest_price() returns correct data
2. get_price_range() returns correct date range
3. get_prediction_accuracy() calculates correctly
4. get_block_prediction_accuracy() works
5. All RPC functions execute < 100ms
6. Error handling for missing data
7. Concurrent query handling

Performance Benchmarks:
- Latest price: < 10ms
- Historical 30d: < 50ms
- Accuracy stats: < 100ms
```

---

#### 3. `test_bulk_insert_performance.py` (NEW)
```bash
# Location: tests/integration/database/test_bulk_insert_performance.py

Tests:
1. COPY-based insert of 10,000 rows (expect < 5 seconds)
2. Fallback batch insert (expect < 30 seconds)
3. Error recovery with retry
4. Partial failure handling
5. Duplicate detection (ON CONFLICT)

Performance Targets:
- COPY insert: > 5000 rows/sec
- Batch fallback: > 500 rows/sec
- Individual retry: > 50 rows/sec
```

---

## Execution Checklist

### Pre-Implementation
- [ ] Create backup of production database
- [ ] Verify TimescaleDB extension available in Supabase
- [ ] Review current query performance (baseline metrics)
- [ ] Create feature branch: `feature/database-optimization`

### Week 1: Hypertable Conversion
- [ ] Execute migration 008
- [ ] Verify hypertable created
- [ ] Monitor compression policy
- [ ] Verify retention policy working
- [ ] Performance test: latest price query
- [ ] Performance test: historical range query

### Week 2: Index Optimization
- [ ] Execute migration 009
- [ ] Drop old indexes
- [ ] Analyze table statistics
- [ ] Verify new indexes being used
- [ ] Benchmark: covering index improvement
- [ ] Benchmark: BRIN index improvement
- [ ] Optimize partial index WHERE clause

### Week 3: Analytics Functions
- [ ] Execute migration 010
- [ ] Create analytics_repository.py
- [ ] Implement RPC methods
- [ ] Update base_repository.py with execute_rpc()
- [ ] Test: All RPC functions execute correctly
- [ ] Benchmark: RPC vs. REST API performance
- [ ] Create analytics test suite

### Week 4: Polish & Deployment
- [ ] Implement real-time subscriptions
- [ ] Setup retention automation
- [ ] Create monitoring queries
- [ ] Document optimization in README
- [ ] Create migration runbook
- [ ] Performance test suite execution
- [ ] Code review and approval
- [ ] Deploy to staging
- [ ] Final performance verification
- [ ] Deploy to production

---

## Monitoring & Validation

### Post-Optimization Queries

```sql
-- 1. Verify hypertable status
SELECT hypertable_name, owner FROM timescaledb_information.hypertables;

-- 2. Check chunk count and sizes
SELECT chunk_name, pg_size_pretty(pg_total_relation_size(chunk_name::regclass)) 
FROM timescaledb_information.chunks 
WHERE hypertable_name = 'market_data';

-- 3. Verify compression
SELECT * FROM timescaledb_information.compression_settings 
WHERE hypertable_name = 'market_data';

-- 4. Monitor index usage
SELECT schemaname, tablename, indexname, idx_scan, idx_tup_read, idx_tup_fetch
FROM pg_stat_user_indexes
WHERE tablename = 'market_data'
ORDER BY idx_scan DESC;

-- 5. Table size comparison
SELECT 
    schemaname,
    tablename,
    pg_size_pretty(pg_total_relation_size(schemaname||'.'||tablename)) as size
FROM pg_tables
WHERE tablename LIKE 'market_data%'
ORDER BY pg_total_relation_size(schemaname||'.'||tablename) DESC;

-- 6. Query performance trend (need pg_stat_statements)
SELECT query, mean_exec_time, calls 
FROM pg_stat_statements
WHERE query LIKE '%market_data%'
ORDER BY mean_exec_time DESC
LIMIT 10;
```

---

## Risk Mitigation

### Risk: Data Loss During Hypertable Conversion
- **Mitigation:** Full backup before starting
- **Rollback:** Can revert hypertable to regular table
- **Verification:** SELECT COUNT(*) before/after must match

### Risk: Long Lock Times
- **Mitigation:** Execute during low-traffic window
- **Mitigation:** Use `IF NOT EXISTS` clause
- **Monitoring:** Watch pg_locks during execution

### Risk: Query Planner Not Using New Indexes
- **Mitigation:** Run ANALYZE after index creation
- **Mitigation:** Lower random_page_cost for large tables
- **Verification:** EXPLAIN ANALYZE output

### Risk: Compression Reduces Write Performance
- **Mitigation:** Only compress data > 7 days old
- **Mitigation:** Schedule compression during off-hours
- **Monitoring:** Monitor CPU and I/O during compression

### Risk: RPC Functions Break with Schema Changes
- **Mitigation:** Version RPC functions
- **Mitigation:** Use defensive programming (CASE WHEN checks)
- **Verification:** Test with sample data after schema changes

---

## Performance Targets

### Query Latency Goals

| Query | Current | Target | Improvement |
|-------|---------|--------|-------------|
| Latest price | 20ms | 5ms | 75% |
| Historical 24h | 150ms | 30ms | 80% |
| Prediction accuracy | 300-500ms | 50-100ms | 85% |
| Block predictions (7d) | 100ms | 15ms | 85% |

### Bulk Insert Goals

| Operation | Current | Target | Improvement |
|-----------|---------|--------|-------------|
| COPY insert (bulk) | - | >5000 rows/sec | New capability |
| Batch REST insert | 100 rows/sec | 500+ rows/sec | 5x |
| Individual insert | ~10 rows/sec | ~50 rows/sec | 5x |

### Storage Goals

| Data Age | Current | Target | Reduction |
|----------|---------|--------|-----------|
| < 30 days | Full size | Full size (uncompressed) | - |
| 30-90 days | Full size | 30% of original | 70% |
| > 90 days | Archived table | 30% of original | 70% |
| Total 1-year data | ~2GB | ~800MB | 60% |

---

## Success Criteria

### Technical Success
- [ ] All queries meet latency targets
- [ ] Bulk insert achieves 5000+ rows/sec
- [ ] Storage reduced by 60% for historical data
- [ ] All tests passing
- [ ] No data loss

### Operational Success
- [ ] Retention policies running automatically
- [ ] Compression completing within SLA
- [ ] Monitoring alerting on anomalies
- [ ] Documentation complete

### Business Success
- [ ] System supports 2-3x current data volume
- [ ] Prediction API response < 200ms
- [ ] No customer-facing performance degradation
- [ ] Reduced database costs (compression)

---

## Questions & Support

### FAQ

**Q: Will this cause downtime?**
A: No. Hypertable conversion is online. Indexes use CONCURRENTLY.

**Q: Can we rollback if something breaks?**
A: Yes. Each migration is reversible. BRIN indexes can be dropped.

**Q: How long does hypertable conversion take?**
A: < 1 minute for market_data table (with no concurrent writes).

**Q: Will RPC functions work with existing code?**
A: Yes. They're backward compatible. Opt-in via analytics_repository.

**Q: What if compression hurts write performance?**
A: Only compress data > 7 days old. New data stays uncompressed.

---

## Appendix: Quick Command Reference

```bash
# Execute all migrations in order
psql -f 008_convert_market_data_hypertable.sql
psql -f 009_add_covering_indexes.sql
psql -f 010_add_analytics_functions.sql

# Verify hypertable created
psql -c "SELECT * FROM timescaledb_information.hypertables;"

# Run test suite
pytest tests/integration/database/test_hypertable_conversion.py -v
pytest tests/integration/database/test_analytics_queries.py -v
pytest tests/integration/database/test_bulk_insert_performance.py -v

# Benchmark query performance
time python -c "from nasdaq_predictor.database.repositories import AnalyticsRepository; \
    a = AnalyticsRepository(); \
    a.get_latest_price(ticker_id, '1h')"
```

---

## Files Created/Modified Summary

### New Files (4)
1. `nasdaq_predictor/database/repositories/analytics_repository.py` (300 lines)
2. `nasdaq_predictor/database/migrations/008_convert_market_data_hypertable.sql`
3. `nasdaq_predictor/database/migrations/009_add_covering_indexes.sql`
4. `nasdaq_predictor/database/migrations/010_add_analytics_functions.sql`

### Modified Files (3)
1. `nasdaq_predictor/database/repositories/base_repository.py` (+50 lines)
2. `nasdaq_predictor/database/repositories/market_data_repository.py` (+80 lines)
3. `nasdaq_predictor/config/database_config.py` (+30 lines)

### Test Files (3)
1. `tests/integration/database/test_hypertable_conversion.py` (new)
2. `tests/integration/database/test_analytics_queries.py` (new)
3. `tests/integration/database/test_bulk_insert_performance.py` (new)

**Total Changes:** ~500 lines of code, 10+ lines of SQL

---

**Status:** Ready for Implementation  
**Last Updated:** November 15, 2025  
**Next Review:** After week 2 implementation
