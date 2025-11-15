# Testing Strategy Quick Reference

## Current State
- **Test Files:** 13 files (~4,703 LOC)
- **Test Cases:** 323 tests
- **Production Files:** 92 Python files
- **Estimated Coverage:** 30-40%

## Critical Gaps (0% Coverage)
1. Database Repositories (9 files)
2. API Routes (8 files)
3. Financial Calculations (7 files at ~15%)
4. Data Fetching (~10%)
5. Additional Services (11 files)

## Priority Actions

### Week 1-2: Financial Calculations (P0 - CRITICAL)
```bash
# Create these test files
tests/unit/analysis/test_volatility.py
tests/unit/analysis/test_block_segmentation.py
tests/unit/analysis/test_early_bias.py
tests/unit/analysis/test_sustained_counter.py
tests/unit/analysis/test_fibonacci_pivots.py
tests/unit/analysis/test_reference_levels.py
tests/unit/analysis/test_confidence.py
```

**Target:** 98.9% coverage on financial calculations

### Week 2-3: Data & Database (P1)
```bash
# Create these test files
tests/unit/data/test_fetcher.py
tests/unit/database/test_repositories.py
tests/fixtures/yfinance_mocks.py
tests/fixtures/supabase_mocks.py
```

### Week 3-4: Services & API (P1)
```bash
# Create these test files
tests/unit/services/test_*.py (for all 11 missing services)
tests/integration/test_api_endpoints.py
```

### Week 5-6: Validation & CI/CD (P2)
```bash
# Create validation framework
tests/validation/backtest_framework.py
tests/validation/backtest_accuracy_validation.sql
tests/performance/test_prediction_performance.py

# Set up CI/CD
.github/workflows/test.yml
.pre-commit-config.yaml
mypy.ini
.coveragerc
```

## Quick Commands

### Run Tests
```bash
# All tests with coverage
pytest --cov=nasdaq_predictor --cov-report=html --cov-report=term

# Only unit tests
pytest tests/unit/ -v

# Only integration tests
pytest tests/integration/ -v

# Specific test file
pytest tests/unit/analysis/test_volatility.py -v

# Parallel execution (faster)
pytest -n auto
```

### Type Checking
```bash
# Run mypy
mypy nasdaq_predictor/ --config-file mypy.ini
```

### Coverage
```bash
# Generate coverage report
coverage report --show-missing

# HTML report
coverage html
open htmlcov/index.html

# Check threshold
coverage report --fail-under=98.9
```

### Code Quality
```bash
# Format code
black nasdaq_predictor/

# Sort imports
isort nasdaq_predictor/

# Lint
flake8 nasdaq_predictor/

# Security scan
bandit -r nasdaq_predictor/
```

## Coverage Targets

| Module | Current | Target | Timeline |
|--------|---------|--------|----------|
| analysis/* | 15% | 98.9% | Week 1-2 |
| data/fetcher.py | 10% | 95% | Week 1 |
| database/repositories/* | 0% | 90% | Week 2-3 |
| services/* | 30% | 95% | Week 3-4 |
| api/routes/* | 0% | 85% | Week 4 |
| **Overall** | **35%** | **98.9%** | **6 weeks** |

## Critical Edge Cases to Test

### Financial
- Flash crashes (>20% price drops)
- Zero volatility (flat markets)
- Negative prices
- Extreme outliers
- Missing data gaps
- OHLC constraint violations

### Temporal
- DST transitions
- Market hours spanning midnight
- Hour at market close
- Leap seconds

### Network
- yfinance timeouts
- Rate limiting (429 errors)
- Supabase connection failures
- Partial data fetches

### Data Quality
- Duplicate predictions
- Invalid UUIDs
- Missing bar fields
- Zero volume bars

## Validation SQL Queries

```sql
-- Find duplicate predictions
SELECT ticker_id, hour_start_timestamp, COUNT(*) 
FROM block_predictions 
GROUP BY ticker_id, hour_start_timestamp 
HAVING COUNT(*) > 1;

-- Find invalid OHLC
SELECT * FROM market_data 
WHERE high < low OR high < open OR high < close;

-- Check confidence range
SELECT * FROM block_predictions 
WHERE confidence < 5 OR confidence > 95;

-- Backtest accuracy
SELECT 
    COUNT(*) as total,
    SUM(CASE WHEN is_correct THEN 1 ELSE 0 END) as correct,
    ROUND(100.0 * SUM(CASE WHEN is_correct THEN 1 ELSE 0 END) / COUNT(*), 2) as accuracy_pct
FROM block_predictions 
WHERE verified = true;
```

## Test Dependencies

```bash
pip install pytest pytest-cov pytest-mock pytest-benchmark pytest-html
pip install mypy types-pytz types-requests
pip install black flake8 isort bandit
pip install responses freezegun memory-profiler
```

## Pre-commit Setup

```bash
pip install pre-commit
pre-commit install
pre-commit run --all-files
```

## CI/CD Checklist

- [ ] GitHub Actions workflow created
- [ ] Pre-commit hooks configured
- [ ] mypy configuration set up
- [ ] Coverage reporting integrated
- [ ] Codecov integration
- [ ] Benchmark tracking
- [ ] Security scanning (bandit)
- [ ] Performance tests

## Success Criteria

### Phase 1 (Week 2)
- [ ] Financial calculations: 98.9%+ coverage
- [ ] Zero financial calculation bugs found
- [ ] All edge cases documented and tested
- [ ] mypy passes with zero errors

### Phase 2 (Week 4)
- [ ] All services tested (95%+ coverage)
- [ ] API coverage >= 85%
- [ ] Integration tests pass
- [ ] No critical bugs

### Phase 3 (Week 6)
- [ ] Backtest accuracy >= 55%
- [ ] Latency < 500ms per prediction
- [ ] CI/CD fully automated
- [ ] Overall coverage >= 98.9%

## Resources

- Full Strategy: `/Users/soonjeongguan/Desktop/Repository/CLAUDECODE/NQP/COMPREHENSIVE_TESTING_STRATEGY.md`
- Test Files: `tests/`
- Production Code: `nasdaq_predictor/`
- Coverage Reports: `htmlcov/`

---
**Last Updated:** 2025-11-15
