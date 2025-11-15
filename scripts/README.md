# NQP Utility Scripts

This directory contains utility scripts for the NASDAQ Prediction Platform (NQP). These scripts are used for development, testing, data management, and manual operations.

## Available Scripts

### 1. `trigger_sync.py`

**Purpose**: Manually trigger market data synchronization and prediction calculation.

**Description**: This script is used to manually seed tickers into the database and trigger the data sync and prediction jobs outside of the regular scheduler. Useful for testing and initial setup.

**What it does**:
- Seeds initial tickers (NQ=F, ES=F, ^FTSE) into the database if they don't exist
- Manually triggers the market data sync job
- Manually triggers the prediction calculation job
- Logs detailed output for debugging

**Usage**:
```bash
python scripts/trigger_sync.py
```

**Prerequisites**:
- `.env` file must be configured with Supabase credentials
- Database must be initialized

**When to use**:
- Initial setup and testing
- Manual sync when scheduler is not available
- Debugging data sync issues
- Testing prediction calculations

**Output**: Creates/updates market data and predictions in the database

---

### 2. `backfill_24h_predictions.py`

**Purpose**: Generate historical prediction data for the last 24 hours.

**Description**: This script backfills the `intraday_predictions` table with historical predictions, useful for populating historical data or recovering from data loss.

**What it does**:
- Fetches historical market data for specified tickers
- Calculates reference levels and signals for each data point
- Generates intraday predictions at specified time intervals
- Stores predictions in the database
- Supports dry-run mode to preview changes without database modifications

**Usage**:
```bash
# Default: NQ=F, ES=F for last 24 hours
python scripts/backfill_24h_predictions.py

# Specify custom tickers
python scripts/backfill_24h_predictions.py --tickers NQ=F ES=F ^FTSE

# Look back more hours
python scripts/backfill_24h_predictions.py --hours-back 48

# Dry run (preview without database changes)
python scripts/backfill_24h_predictions.py --dry-run

# Combined options
python scripts/backfill_24h_predictions.py --tickers NQ=F --hours-back 24 --dry-run
```

**Command-line Options**:
- `--tickers`: Comma-separated list of tickers (default: NQ=F,ES=F)
- `--hours-back`: Number of hours to backfill (default: 24)
- `--dry-run`: Preview changes without writing to database

**Prerequisites**:
- `.env` file must be configured
- Database must be initialized
- yfinance must be accessible

**When to use**:
- Recovering from prediction data loss
- Populating historical predictions for new tickers
- Testing prediction generation logic
- Analyzing historical prediction accuracy

**Expected Output**:
- Console logs showing progress
- Database entries for each generated prediction
- Summary of created predictions

---

### 3. `test_implementation.py`

**Purpose**: Verify implementation and test core functionality.

**Description**: This test script validates that the system is working correctly, including reference levels calculation, data sync, and prediction verification.

**What it does**:
- Tests reference levels calculation with real data
- Verifies prediction storage and retrieval
- Tests accuracy calculation for predictions
- Validates the prediction verification system
- Generates detailed output showing calculation steps

**Usage**:
```bash
python scripts/test_implementation.py
```

**Prerequisites**:
- `.env` file must be configured
- Database must be initialized
- Scheduler must have been running for at least 30 minutes to accumulate real data

**When to use**:
- Initial deployment validation
- Debugging calculation issues
- Verifying changes to prediction logic
- Performance testing
- After database migrations

**Test Coverage**:
1. Reference Levels - Validates real data calculations
2. Market Data - Checks data storage and retrieval
3. Prediction Verification - Tests accuracy calculations
4. Signal Analysis - Verifies signal generation

**Expected Output**:
- Test results for each component
- Calculated values (reference levels, signals, accuracy)
- Timing information for performance analysis
- Detailed logs for debugging

---

### 4. `app_backup.py`

**Status**: ⚠️ **LEGACY** - Old monolithic Flask application

**Description**: This is a backup of the original monolithic Flask application before refactoring into microservices architecture. It contains the original prediction engine and API structure.

**Do NOT Use**: This file is kept only as a reference. The current application uses the refactored structure in `nasdaq_predictor/`.

**Why it exists**:
- Reference for understanding the original design
- Potential source for recovering legacy logic if needed
- Historical documentation

**Note for migration**: This file is a candidate for deletion once the refactored implementation is fully validated in production.

---

## Common Tasks

### Running a Complete Test Suite
```bash
# Seed data
python scripts/trigger_sync.py

# Wait 30 minutes for scheduler to accumulate data, then test
python scripts/test_implementation.py

# Backfill historical predictions for analysis
python scripts/backfill_24h_predictions.py --hours-back 48
```

### Recovering from Data Loss
```bash
# Backfill the last 24-48 hours of predictions
python scripts/backfill_24h_predictions.py --hours-back 48

# Verify data integrity
python scripts/test_implementation.py
```

### Testing New Tickers
```bash
# Add and sync for a new ticker
python scripts/trigger_sync.py

# Generate predictions for the new ticker
python scripts/backfill_24h_predictions.py --tickers NEW_TICKER
```

### Development/Debugging
```bash
# Dry run to preview changes
python scripts/backfill_24h_predictions.py --dry-run

# Check implementation without changes
python scripts/test_implementation.py
```

---

## Prerequisites

All scripts require:
- Python 3.8+
- `.env` file in project root with Supabase credentials
- Database initialized with schema
- Dependencies installed: `pip install -r requirements.txt`

### Environment Setup

```bash
# Create .env file with:
SUPABASE_URL=your_supabase_url
SUPABASE_KEY=your_supabase_key
SUPABASE_PASSWORD=your_database_password
```

---

## Troubleshooting

### Module Import Errors
- Ensure you're running scripts from the project root directory
- Check that `PYTHONPATH` includes the project directory
- Verify virtual environment is activated

### Database Connection Errors
- Verify `.env` file has correct Supabase credentials
- Check database is running and accessible
- Ensure tables exist (run `database/init_db.py`)

### Data Sync Issues
- Check scheduler logs for errors
- Run `trigger_sync.py` to manually test sync
- Verify yfinance can fetch data for tickers

### Prediction Calculation Errors
- Ensure market data has been synced first
- Check for NaN values in OHLC data
- Verify ticker is enabled in database

---

## Future Improvements

These scripts could be enhanced with:
- Command-line progress bars
- Database transaction rollback on errors
- Logging to files (not just console)
- Configuration file support
- Integration test framework
- Performance benchmarking tools

---

## Related Files

- Main application: `nasdaq_predictor/`
- Database models: `nasdaq_predictor/database/models/`
- Configuration: `nasdaq_predictor/config/`
- Scheduler: `nasdaq_predictor/scheduler/`

---

**Last Updated**: Phase 2.3 (Script Organization)
