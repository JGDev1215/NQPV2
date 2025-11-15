# Fibonacci Pivot Points Implementation

## Overview
Implementation of Fibonacci-based pivot point calculations across multiple timeframes (daily, weekly, monthly) with automated scheduling, database storage, and a dedicated UI page.

**Date Started:** November 12, 2025
**Status:** In Progress (Backend Complete, Frontend Pending)

---

## Requirements

### Core Features
1. ✅ Calculate Fibonacci pivot points using the formula:
   - Pivot Point (PP) = (High + Low + Close) / 3
   - Resistance levels: R1 (0.382), R2 (0.618), R3 (1.000)
   - Support levels: S1 (0.382), S2 (0.618), S3 (1.000)

2. ✅ Support multiple timeframes:
   - Daily pivots
   - Weekly pivots
   - Monthly pivots

3. ✅ Store calculations in Supabase database
4. ✅ Automated daily calculation via scheduler
5. ⏳ API endpoints for frontend access
6. ⏳ Dedicated UI page showing:
   - All pivot levels for each ticker
   - Highlighting of 2 closest levels to current price
   - Tab navigation between tickers (NQ=F, ES=F, ^FTSE)

---

## Implementation Progress

### Phase 1: Backend Core ✅ COMPLETE

#### 1.1 Database Schema ✅
**File:** `nasdaq_predictor/database/migrations/005_add_fibonacci_pivots.sql`

**Table Structure:**
```sql
CREATE TABLE fibonacci_pivots (
    id SERIAL PRIMARY KEY,
    ticker_symbol VARCHAR(20) NOT NULL,
    timeframe VARCHAR(10) NOT NULL,
    calculation_date TIMESTAMP WITH TIME ZONE NOT NULL,

    -- Source OHLC data
    period_high DECIMAL(12, 4) NOT NULL,
    period_low DECIMAL(12, 4) NOT NULL,
    period_close DECIMAL(12, 4) NOT NULL,

    -- Pivot levels
    pivot_point DECIMAL(12, 4) NOT NULL,
    resistance_1 DECIMAL(12, 4) NOT NULL,
    resistance_2 DECIMAL(12, 4) NOT NULL,
    resistance_3 DECIMAL(12, 4) NOT NULL,
    support_1 DECIMAL(12, 4) NOT NULL,
    support_2 DECIMAL(12, 4) NOT NULL,
    support_3 DECIMAL(12, 4) NOT NULL,

    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),

    UNIQUE(ticker_symbol, timeframe, calculation_date)
);
```

**Indexes Created:**
- `idx_fib_pivots_ticker` - Fast ticker lookup
- `idx_fib_pivots_timeframe` - Timeframe filtering
- `idx_fib_pivots_date` - Date-based queries
- `idx_fib_pivots_ticker_timeframe` - Combined ticker/timeframe lookup

#### 1.2 Calculation Module ✅
**File:** `nasdaq_predictor/analysis/fibonacci_pivots.py`

**Key Components:**
- `FibonacciPivotLevels` dataclass - Structured pivot data
- `FibonacciPivotCalculator` class - Core calculation logic
- `calculate_pivots()` - Pure calculation function
- `fetch_ohlc_data()` - yfinance integration
- `calculate_for_ticker()` - Complete ticker calculation
- `find_closest_levels()` - Identifies nearest pivot levels to current price

**Features:**
- Supports all 3 timeframes (daily, weekly, monthly)
- Fetches OHLC data from yfinance
- Calculates 7 pivot levels per timeframe
- Finds N closest levels to any given price
- Type-safe with dataclasses
- Comprehensive logging

#### 1.3 Data Model ✅
**File:** `nasdaq_predictor/database/models/fibonacci_pivot.py`

**FibonacciPivot Dataclass:**
- All pivot level fields
- `to_dict()` method for JSON serialization
- `from_row()` class method for DB deserialization
- Optional fields for id, created_at, updated_at

#### 1.4 Database Repository ✅
**File:** `nasdaq_predictor/database/repositories/fibonacci_pivot_repository.py`

**Repository Methods:**
- `insert_or_update()` - Upsert pivot calculations
- `get_latest()` - Get most recent pivots for ticker/timeframe
- `get_all_latest()` - Get latest for all timeframes
- `get_historical()` - Historical pivots with date range
- `delete_old_records()` - Cleanup old data
- `bulk_insert()` - Batch insertion for efficiency

#### 1.5 Scheduler Integration ✅
**Files Modified:**
- `nasdaq_predictor/scheduler/jobs.py` - Added `calculate_fibonacci_pivots()` function
- `nasdaq_predictor/scheduler/__init__.py` - Registered job with APScheduler

**Schedule:** Daily at 00:05 UTC

**Job Logic:**
1. Iterates through all tickers (NQ=F, ES=F, ^FTSE)
2. Calculates pivots for all 3 timeframes
3. Stores results in database with upsert
4. Logs success/failure for each calculation
5. Returns summary statistics

---

### Phase 2: API Layer ⏳ IN PROGRESS

#### 2.1 API Endpoints ⏳
**File:** `nasdaq_predictor/api/routes.py`

**Endpoints to Add:**
```python
GET /fibonacci-pivots
    → Render fibonacci_pivots.html page

GET /api/fibonacci-pivots/<ticker>
    → Get all timeframes with closest levels highlighted
    Response: {
        ticker, current_price, timeframes: {
            daily: {...}, weekly: {...}, monthly: {...}
        }
    }

GET /api/fibonacci-pivots/<ticker>/<timeframe>
    → Get specific ticker/timeframe combination
```

---

### Phase 3: Frontend UI ⏳ PENDING

#### 3.1 HTML Template ⏳
**File:** `templates/fibonacci_pivots.html`

**Layout:**
- Header with navigation back to dashboard
- Ticker tabs (NQ=F, ES=F, ^FTSE)
- For each ticker:
  - Current price display
  - Daily pivots section
  - Weekly pivots section
  - Monthly pivots section
- Visual price ladder showing all levels
- Highlighting for 2 closest levels

#### 3.2 JavaScript Logic ⏳
**File:** `static/js/fibonacci_pivots.js`

**Functions:**
- `fetchFibonacciPivots(ticker)` - API call to get pivot data
- `renderPivotLevels(ticker, timeframe, data)` - Render pivot table
- `highlightClosestLevels(levels, currentPrice)` - Mark closest 2 levels
- `switchTickerTab(ticker)` - Tab switching logic
- `formatPriceLevel(level)` - Price formatting
- `calculateDistance(price, currentPrice)` - Distance calculation

#### 3.3 Navigation Integration ⏳
**Files to Modify:**
- `templates/index.html` - Add "Fibonacci Pivots" tab to header navigation
- `templates/history.html` - Add "Fibonacci Pivots" tab for consistency

---

## Technical Specifications

### Fibonacci Ratios Used
- **0.382** - Fibonacci ratio (38.2%)
- **0.618** - Golden ratio (61.8%)
- **1.000** - 100% of price range

### Formula Details
```python
pivot_point = (high + low + close) / 3
price_range = high - low

resistance_1 = pivot_point + (0.382 × price_range)
resistance_2 = pivot_point + (0.618 × price_range)
resistance_3 = pivot_point + (1.000 × price_range)

support_1 = pivot_point - (0.382 × price_range)
support_2 = pivot_point - (0.618 × price_range)
support_3 = pivot_point - (1.000 × price_range)
```

### Data Flow
```
yfinance API → FibonacciPivotCalculator
    ↓
Calculate 7 pivot levels per timeframe
    ↓
FibonacciPivotRepository.insert_or_update()
    ↓
Supabase fibonacci_pivots table
    ↓
API Endpoint (/api/fibonacci-pivots/<ticker>)
    ↓
Frontend (fibonacci_pivots.html + fibonacci_pivots.js)
```

---

## Testing Plan

### Backend Testing
- [x] Test pivot calculation accuracy
- [x] Test OHLC data fetching for all timeframes
- [x] Test database upsert functionality
- [ ] Test scheduler job execution
- [ ] Test API endpoint responses

### Frontend Testing
- [ ] Test ticker tab switching
- [ ] Test data loading and display
- [ ] Test closest level highlighting
- [ ] Test responsive design on mobile
- [ ] Test error handling (no data scenarios)

---

## Files Created

### Backend
1. `nasdaq_predictor/database/migrations/005_add_fibonacci_pivots.sql` - DB schema
2. `nasdaq_predictor/analysis/fibonacci_pivots.py` - Calculation module (500+ lines)
3. `nasdaq_predictor/database/models/fibonacci_pivot.py` - Data model
4. `nasdaq_predictor/database/repositories/fibonacci_pivot_repository.py` - Repository (300+ lines)

### Modified
1. `nasdaq_predictor/scheduler/jobs.py` - Added `calculate_fibonacci_pivots()` function
2. `nasdaq_predictor/scheduler/__init__.py` - Registered new job

### Frontend (Pending)
1. `templates/fibonacci_pivots.html` - UI page
2. `static/js/fibonacci_pivots.js` - Frontend logic
3. `templates/index.html` - Navigation tab
4. `templates/history.html` - Navigation tab

---

## Usage Examples

### Manual Calculation
```python
from nasdaq_predictor.analysis.fibonacci_pivots import FibonacciPivotCalculator

calculator = FibonacciPivotCalculator()
pivots = calculator.calculate_for_ticker('NQ=F', 'daily')

print(f"Pivot Point: {pivots.pivot_point:.2f}")
print(f"R1: {pivots.resistance_1:.2f}")
print(f"S1: {pivots.support_1:.2f}")

# Find closest levels
closest = pivots.find_closest_levels(current_price=19234.50, count=2)
for level in closest:
    print(f"{level['name']}: {level['price']:.2f} (distance: {level['distance']:.2f})")
```

### Database Operations
```python
from nasdaq_predictor.database.repositories.fibonacci_pivot_repository import FibonacciPivotRepository

repo = FibonacciPivotRepository()

# Get latest pivots for NQ=F daily
pivots = repo.get_latest('NQ=F', 'daily')

# Get all timeframes
all_pivots = repo.get_all_latest('NQ=F')
print(all_pivots['daily'])
print(all_pivots['weekly'])
print(all_pivots['monthly'])

# Cleanup old records (keep last 90 days)
deleted_count = repo.delete_old_records(days_to_keep=90)
```

---

## Next Steps

### Immediate (Phase 2)
1. ⏳ Add API endpoints to `routes.py`
2. ⏳ Test API responses with Postman/curl

### Short-term (Phase 3)
1. ⏳ Create `fibonacci_pivots.html` template
2. ⏳ Implement `fibonacci_pivots.js` logic
3. ⏳ Add navigation tabs to existing pages
4. ⏳ Test full end-to-end workflow

### Future Enhancements
- [ ] Visual chart with horizontal pivot lines
- [ ] Historical pivot comparison
- [ ] Alert system for price approaching pivots
- [ ] Export pivot levels to CSV
- [ ] Mobile-optimized UI

---

## Known Issues & Limitations

1. **Market Hours Dependency**
   - Daily pivots require previous day's close
   - Weekly pivots update on Monday
   - Monthly pivots update on 1st of month

2. **Data Availability**
   - Depends on yfinance API uptime
   - Historical data may be incomplete for some periods
   - Weekend/holiday data gaps handled gracefully

3. **Timezone Considerations**
   - All calculations in UTC
   - Scheduler runs at 00:05 UTC to ensure daily data available

---

## References

- **Fibonacci Pivot Points**: Traditional pivot point calculation with Fibonacci ratios
- **yfinance Documentation**: https://pypi.org/project/yfinance/
- **APScheduler**: https://apscheduler.readthedocs.io/

---

**Last Updated:** November 12, 2025 (Backend Phase Complete)
**Contributors:** Claude Code AI Assistant
**Status:** ✅ Backend Complete | ⏳ Frontend In Progress
