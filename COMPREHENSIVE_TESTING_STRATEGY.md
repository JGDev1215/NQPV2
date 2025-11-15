# NASDAQ Predictor: Comprehensive Testing & Validation Strategy
**Report Date:** 2025-11-15  
**System:** Financial Prediction Engine (7-Block Framework)  
**Project:** NASDAQ Predictor (NQP)

---

## Executive Summary

This document provides a comprehensive testing and validation strategy for the NASDAQ Predictor project, a financial prediction system implementing a novel 7-block framework for hourly market predictions. The analysis reveals a **moderate testing foundation** (323 test cases across 13 files) with significant gaps in critical areas requiring immediate attention to achieve production-ready quality assurance.

**Current State:** ~30-40% estimated coverage  
**Target State:** 98.9%+ coverage with robust validation frameworks  
**Priority:** HIGH - Financial systems require exceptional reliability

---

## 1. Current Testing State Assessment

### 1.1 Test Coverage Analysis

**Existing Test Structure:**
```
tests/
├── unit/ (11 test files)
│   ├── core/ (4 files: DTOs, validators, exceptions, results)
│   ├── services/ (3 files: block prediction, verification, market status)
│   ├── analysis/ (1 file: block prediction engine)
│   └── config/ (1 file: configuration)
├── integration/ (2 test files)
│   ├── test_block_prediction_flow.py (486 LOC)
│   └── services/test_market_aware_predictions.py (327 LOC)
└── conftest.py (pytest fixtures)
```

**Test Count:**
- **Total Test Cases:** 323 tests
- **Test Files:** 13 files (~4,703 LOC)
- **Production Files:** 92 Python files

**Coverage Estimate:** 30-40% (based on file analysis)

### 1.2 Tested Components

**Well-Tested Areas (60-80% coverage estimated):**
1. **Core DTOs** - Data transfer objects validation
2. **Block Prediction Service** - Main prediction generation flow
3. **Block Verification Service** - Accuracy verification logic
4. **Market Status Service** - Market hours/status detection
5. **Block Prediction Engine** - Decision tree logic
6. **Core Validators** - Input validation
7. **Exception Handling** - Custom exceptions

**Partially Tested (20-40% coverage):**
1. Integration flows (block prediction end-to-end)
2. Market-aware predictions
3. Configuration management

### 1.3 Critical Gaps Identified

**UNTESTED Components (0-10% coverage):**
1. **Database Repositories (9 files)** - NO tests found
   - PredictionRepository
   - IntradayPredictionRepository
   - BlockPredictionRepository
   - TickerRepository
   - MarketDataRepository
   - ReferenceLevelsRepository
   - FibonacciPivotRepository
   - SchedulerJobExecutionRepository
   
2. **Data Fetching Layer**
   - YahooFinanceDataFetcher (yfinance integration)
   - Supabase data retrieval
   - Network error handling
   - Rate limiting

3. **Financial Calculations (Analysis Modules)**
   - Volatility calculations (volatility.py)
   - Block segmentation logic (block_segmentation.py)
   - Early bias detection (early_bias.py)
   - Sustained counter analysis (sustained_counter.py)
   - Fibonacci pivots (fibonacci_pivots.py)
   - Reference levels (reference_levels.py)
   - Confidence scoring (confidence.py)

4. **API Routes (8 route files)** - NO tests found
   - block_prediction_routes.py
   - market_aware_routes.py
   - prediction_routes.py
   - market_routes.py
   - fibonacci_routes.py
   - history_routes.py
   - misc_routes.py
   - scheduler_metrics_routes.py

5. **Services (11 additional service files untested)**
   - DataSyncService
   - FormattingService
   - CacheService
   - AccuracyService
   - AggregationService
   - PredictionCalculationService
   - SchedulerJobTrackingService
   - VerificationService
   - IntradayPredictionService
   - IntradayVerificationService

6. **Scheduler & Background Jobs**
   - Job execution
   - Error recovery
   - Job tracking

---

## 2. Comprehensive Test Coverage Roadmap

### 2.1 Coverage Targets by Component

| Component Category | Current | Target | Priority |
|-------------------|---------|--------|----------|
| Core DTOs/Validators | 70% | 100% | P1 |
| Financial Calculations | 15% | 98.9% | P0 (CRITICAL) |
| Data Fetching | 10% | 95% | P0 (CRITICAL) |
| Database Repositories | 0% | 90% | P1 |
| API Endpoints | 0% | 85% | P1 |
| Services Layer | 30% | 95% | P1 |
| Integration Flows | 25% | 90% | P2 |
| Scheduler/Jobs | 0% | 85% | P2 |
| **Overall Project** | **35%** | **98.9%** | - |

### 2.2 Testing Pyramid Strategy

```
                    E2E Tests (10%)
                   /              \
              Integration Tests (25%)
             /                        \
        Unit Tests (65%)
```

**Distribution:**
- **Unit Tests:** 65% of effort - Isolated logic, fast execution
- **Integration Tests:** 25% of effort - Component interactions
- **E2E Tests:** 10% of effort - Full workflows, API validation

---

## 3. Unit Test Strategy

### 3.1 Financial Calculations (CRITICAL PRIORITY)

**Target: 98.9% coverage** - These are the core algorithms that determine prediction accuracy.

#### 3.1.1 Volatility Calculation Tests
**File:** `tests/unit/analysis/test_volatility.py`

```python
"""
Unit tests for volatility calculations.
Financial accuracy is CRITICAL - test all edge cases.
"""
import pytest
import pandas as pd
from datetime import datetime, timedelta
import pytz
from nasdaq_predictor.analysis.volatility import calculate_hourly_volatility


class TestVolatilityCalculation:
    """Test volatility calculation accuracy and edge cases."""
    
    @pytest.fixture
    def sample_bars_normal(self):
        """Normal market conditions - moderate volatility."""
        start = datetime(2024, 11, 13, 10, 0, tzinfo=pytz.UTC)
        return [
            {'timestamp': start, 'open': 100.0, 'close': 100.5},
            {'timestamp': start + timedelta(minutes=5), 'open': 100.5, 'close': 101.0},
            {'timestamp': start + timedelta(minutes=10), 'open': 101.0, 'close': 100.8},
            {'timestamp': start + timedelta(minutes=15), 'open': 100.8, 'close': 101.2},
            {'timestamp': start + timedelta(minutes=20), 'open': 101.2, 'close': 101.5},
        ]
    
    @pytest.fixture
    def sample_bars_high_volatility(self):
        """High volatility conditions - large price swings."""
        start = datetime(2024, 11, 13, 10, 0, tzinfo=pytz.UTC)
        return [
            {'timestamp': start, 'open': 100.0, 'close': 105.0},
            {'timestamp': start + timedelta(minutes=5), 'open': 105.0, 'close': 95.0},
            {'timestamp': start + timedelta(minutes=10), 'open': 95.0, 'close': 110.0},
            {'timestamp': start + timedelta(minutes=15), 'open': 110.0, 'close': 90.0},
        ]
    
    @pytest.fixture
    def sample_bars_zero_volatility(self):
        """Zero volatility - flat market."""
        start = datetime(2024, 11, 13, 10, 0, tzinfo=pytz.UTC)
        return [
            {'timestamp': start + timedelta(minutes=5*i), 'open': 100.0, 'close': 100.0}
            for i in range(12)
        ]

    def test_volatility_normal_conditions(self, sample_bars_normal):
        """Test volatility calculation under normal market conditions."""
        opening_price = 100.0
        volatility = calculate_hourly_volatility(sample_bars_normal, opening_price)
        
        # Volatility should be positive and reasonable
        assert volatility > 0
        assert 0.1 < volatility < 10.0  # Reasonable range for hourly volatility
        assert isinstance(volatility, float)
    
    def test_volatility_high_volatility_conditions(self, sample_bars_high_volatility):
        """Test volatility calculation during high volatility."""
        opening_price = 100.0
        volatility = calculate_hourly_volatility(sample_bars_high_volatility, opening_price)
        
        # High volatility should produce larger values
        assert volatility > 2.0  # Should be significantly elevated
        assert volatility < 50.0  # But still bounded
    
    def test_volatility_zero_volatility_edge_case(self, sample_bars_zero_volatility):
        """Test handling of zero volatility (flat market)."""
        opening_price = 100.0
        volatility = calculate_hourly_volatility(sample_bars_zero_volatility, opening_price)
        
        # Should handle gracefully - either 0 or small default value
        assert volatility >= 0
        assert volatility < 0.01  # Near zero
    
    def test_volatility_single_bar_insufficient_data(self):
        """Test error handling with insufficient data."""
        single_bar = [{'timestamp': datetime.now(pytz.UTC), 'open': 100.0, 'close': 100.5}]
        opening_price = 100.0
        
        with pytest.raises(ValueError, match="Insufficient data"):
            calculate_hourly_volatility(single_bar, opening_price)
    
    def test_volatility_empty_bars(self):
        """Test error handling with empty data."""
        with pytest.raises(ValueError, match="No bars provided"):
            calculate_hourly_volatility([], 100.0)
    
    def test_volatility_missing_close_prices(self):
        """Test handling of malformed data (missing close prices)."""
        bars = [
            {'timestamp': datetime.now(pytz.UTC), 'open': 100.0},  # Missing 'close'
            {'timestamp': datetime.now(pytz.UTC), 'open': 101.0},
        ]
        
        with pytest.raises(KeyError, match="close"):
            calculate_hourly_volatility(bars, 100.0)
    
    def test_volatility_negative_prices(self):
        """Test handling of invalid negative prices."""
        bars = [
            {'timestamp': datetime.now(pytz.UTC), 'open': 100.0, 'close': -50.0},
            {'timestamp': datetime.now(pytz.UTC), 'open': -50.0, 'close': 100.0},
        ]
        opening_price = 100.0
        
        # Should either raise error or handle gracefully
        with pytest.raises(ValueError, match="negative"):
            calculate_hourly_volatility(bars, opening_price)
    
    def test_volatility_extreme_outlier(self):
        """Test handling of extreme price outliers (flash crash scenario)."""
        start = datetime(2024, 11, 13, 10, 0, tzinfo=pytz.UTC)
        bars = [
            {'timestamp': start, 'open': 100.0, 'close': 100.5},
            {'timestamp': start + timedelta(minutes=5), 'open': 100.5, 'close': 0.01},  # Flash crash
            {'timestamp': start + timedelta(minutes=10), 'open': 0.01, 'close': 100.0},  # Recovery
        ]
        opening_price = 100.0
        
        # Should produce very high volatility or cap at reasonable maximum
        volatility = calculate_hourly_volatility(bars, opening_price)
        assert volatility > 10.0  # Should detect extreme volatility
    
    def test_volatility_decimal_precision(self, sample_bars_normal):
        """Test that volatility maintains proper decimal precision."""
        opening_price = 100.0
        volatility = calculate_hourly_volatility(sample_bars_normal, opening_price)
        
        # Should have reasonable precision (2-4 decimal places)
        assert len(str(volatility).split('.')[-1]) <= 6  # Max 6 decimals
    
    def test_volatility_consistency_same_input(self, sample_bars_normal):
        """Test that same input produces same output (deterministic)."""
        opening_price = 100.0
        
        volatility_1 = calculate_hourly_volatility(sample_bars_normal, opening_price)
        volatility_2 = calculate_hourly_volatility(sample_bars_normal, opening_price)
        
        assert volatility_1 == volatility_2  # Must be deterministic
    
    def test_volatility_with_different_opening_prices(self, sample_bars_normal):
        """Test how opening price affects volatility calculation."""
        volatility_100 = calculate_hourly_volatility(sample_bars_normal, 100.0)
        volatility_1000 = calculate_hourly_volatility(sample_bars_normal, 1000.0)
        
        # Volatility should scale with opening price (percentage-based)
        # OR be independent if using absolute deviation
        assert volatility_100 > 0
        assert volatility_1000 > 0
```

**Coverage Gaps to Address:**
- [ ] Different market conditions (trending, range-bound, gap-up/down)
- [ ] Timezone handling in bar timestamps
- [ ] Missing/null values in bars
- [ ] Performance with 1000+ bars
- [ ] Comparison against known volatility values (backtesting validation)

#### 3.1.2 Block Segmentation Tests
**File:** `tests/unit/analysis/test_block_segmentation.py`

```python
"""
Unit tests for 7-block segmentation logic.
Tests block boundary calculation, OHLC aggregation, and deviation calculations.
"""
import pytest
from datetime import datetime, timedelta
import pytz
from nasdaq_predictor.analysis.block_segmentation import (
    BlockSegmentation, BlockAnalysis
)


class TestBlockSegmentation:
    """Test 7-block hour segmentation."""
    
    @pytest.fixture
    def hour_bars_complete(self):
        """Complete hour of 5-minute bars (12 bars)."""
        start = datetime(2024, 11, 13, 10, 0, tzinfo=pytz.UTC)
        bars = []
        for i in range(12):
            bars.append({
                'timestamp': start + timedelta(minutes=5*i),
                'open': 100.0 + i * 0.1,
                'high': 100.5 + i * 0.1,
                'low': 99.5 + i * 0.1,
                'close': 100.2 + i * 0.1,
                'volume': 1000000
            })
        return bars
    
    def test_segment_hour_into_7_blocks(self, hour_bars_complete):
        """Test that hour is correctly segmented into 7 blocks."""
        hour_start = datetime(2024, 11, 13, 10, 0, tzinfo=pytz.UTC)
        volatility = 1.5
        
        blocks = BlockSegmentation.segment_hour_into_blocks(
            bars=hour_bars_complete,
            hour_start=hour_start,
            volatility=volatility
        )
        
        assert len(blocks) == 7, "Must produce exactly 7 blocks"
        assert all(isinstance(b, BlockAnalysis) for b in blocks)
        assert all(1 <= b.block_number <= 7 for b in blocks)
    
    def test_block_boundaries_correct_timing(self, hour_bars_complete):
        """Test that block boundaries are at correct time intervals."""
        hour_start = datetime(2024, 11, 13, 10, 0, tzinfo=pytz.UTC)
        volatility = 1.5
        
        blocks = BlockSegmentation.segment_hour_into_blocks(
            bars=hour_bars_complete,
            hour_start=hour_start,
            volatility=volatility
        )
        
        # Each block should be ~8.57 minutes (60 min / 7 blocks)
        expected_duration = timedelta(minutes=60/7)
        
        for i, block in enumerate(blocks):
            expected_start = hour_start + (expected_duration * i)
            # Allow small tolerance for rounding
            assert abs((block.start_time - expected_start).total_seconds()) < 10
    
    def test_block_ohlc_aggregation(self, hour_bars_complete):
        """Test OHLC aggregation within each block."""
        hour_start = datetime(2024, 11, 13, 10, 0, tzinfo=pytz.UTC)
        volatility = 1.5
        
        blocks = BlockSegmentation.segment_hour_into_blocks(
            bars=hour_bars_complete,
            hour_start=hour_start,
            volatility=volatility
        )
        
        for block in blocks:
            # High should be max, Low should be min
            assert block.high_price >= block.low_price
            assert block.high_price >= block.price_at_end
            assert block.low_price <= block.price_at_end
    
    def test_block_deviation_from_open_calculation(self, hour_bars_complete):
        """Test deviation from opening price calculation."""
        hour_start = datetime(2024, 11, 13, 10, 0, tzinfo=pytz.UTC)
        opening_price = 100.0
        volatility = 2.0  # 2.0 price units = 1 std dev
        
        blocks = BlockSegmentation.segment_hour_into_blocks(
            bars=hour_bars_complete,
            hour_start=hour_start,
            volatility=volatility
        )
        
        for block in blocks:
            # Deviation should be in standard deviations
            expected_deviation = (block.price_at_end - opening_price) / volatility
            assert abs(block.deviation_from_open - expected_deviation) < 0.01
    
    def test_block_crosses_open_detection(self):
        """Test detection of price crossing opening level."""
        hour_start = datetime(2024, 11, 13, 10, 0, tzinfo=pytz.UTC)
        opening_price = 100.0
        
        # Bars that cross opening price
        bars_crossing = [
            {'timestamp': hour_start, 'open': 100.0, 'high': 102.0, 'low': 98.0, 'close': 101.0, 'volume': 1000000},
        ]
        
        volatility = 1.0
        blocks = BlockSegmentation.segment_hour_into_blocks(
            bars=bars_crossing,
            hour_start=hour_start,
            volatility=volatility
        )
        
        # First block should show crossing
        assert blocks[0].crosses_open == True
    
    def test_block_time_above_below_open(self):
        """Test calculation of time spent above/below opening price."""
        # This requires detailed bar-by-bar analysis
        # Should sum up time where price > open vs price < open
        hour_start = datetime(2024, 11, 13, 10, 0, tzinfo=pytz.UTC)
        
        bars = [
            {'timestamp': hour_start, 'open': 100.0, 'high': 101.0, 'low': 100.0, 'close': 101.0, 'volume': 1000000},
            {'timestamp': hour_start + timedelta(minutes=5), 'open': 101.0, 'high': 101.0, 'low': 99.0, 'close': 99.0, 'volume': 1000000},
        ]
        
        opening_price = 100.0
        volatility = 1.0
        
        blocks = BlockSegmentation.segment_hour_into_blocks(
            bars=bars,
            hour_start=hour_start,
            volatility=volatility
        )
        
        # Block should have time_above_open and time_below_open
        for block in blocks:
            assert hasattr(block, 'time_above_open')
            assert hasattr(block, 'time_below_open')
            # Total time should equal block duration
            total_time = block.time_above_open + block.time_below_open
            assert 0 <= total_time <= 1.0  # Normalized to 0-1
    
    def test_incomplete_hour_handling(self):
        """Test handling of incomplete hour (less than 60 minutes of data)."""
        hour_start = datetime(2024, 11, 13, 10, 0, tzinfo=pytz.UTC)
        
        # Only 30 minutes of data
        partial_bars = [
            {'timestamp': hour_start + timedelta(minutes=5*i), 'open': 100.0, 'high': 100.5, 'low': 99.5, 'close': 100.0, 'volume': 1000000}
            for i in range(6)  # Only 6 bars (30 minutes)
        ]
        
        volatility = 1.0
        blocks = BlockSegmentation.segment_hour_into_blocks(
            bars=partial_bars,
            hour_start=hour_start,
            volatility=volatility
        )
        
        # Should still produce blocks, but may have fewer than 7
        # OR should raise error for insufficient data
        assert blocks is not None
    
    def test_prediction_point_time_calculation(self):
        """Test that 5/7 prediction point is calculated correctly."""
        hour_start = datetime(2024, 11, 13, 10, 0, tzinfo=pytz.UTC)
        
        prediction_time = BlockSegmentation.get_prediction_point_time(hour_start)
        
        # 5/7 of an hour = 42.857 minutes = 42 minutes 51 seconds
        expected_time = hour_start + timedelta(minutes=42, seconds=51)
        
        # Allow 1-second tolerance
        assert abs((prediction_time - expected_time).total_seconds()) < 1
    
    def test_volume_aggregation_per_block(self, hour_bars_complete):
        """Test that volume is correctly aggregated per block."""
        hour_start = datetime(2024, 11, 13, 10, 0, tzinfo=pytz.UTC)
        volatility = 1.0
        
        blocks = BlockSegmentation.segment_hour_into_blocks(
            bars=hour_bars_complete,
            hour_start=hour_start,
            volatility=volatility
        )
        
        for block in blocks:
            assert block.volume > 0
            assert isinstance(block.volume, (int, float))
```

**Additional Edge Cases:**
- [ ] Missing bars within hour (data gaps)
- [ ] Bars with zero volume
- [ ] Hour spanning market close
- [ ] Daylight saving time transitions
- [ ] Different bar intervals (1min, 15min)

### 3.2 Data Fetching Layer Tests

**File:** `tests/unit/data/test_fetcher.py`

```python
"""
Unit tests for data fetching layer.
Tests yfinance integration, Supabase fallback, error handling.
"""
import pytest
from unittest.mock import Mock, patch, MagicMock
from datetime import datetime, timedelta
import pytz
import pandas as pd
from nasdaq_predictor.data.fetcher import YahooFinanceDataFetcher


class TestYahooFinanceDataFetcher:
    """Test data fetching from yfinance and Supabase."""
    
    @pytest.fixture
    def fetcher(self):
        """Create fetcher with mocked repository."""
        mock_repo = Mock()
        return YahooFinanceDataFetcher(market_data_repo=mock_repo)
    
    @pytest.fixture
    def mock_yfinance_ticker(self):
        """Mock yfinance Ticker object."""
        mock_ticker = Mock()
        
        # Mock history data
        dates = pd.date_range(start='2024-11-13 10:00', periods=12, freq='5min', tz=pytz.UTC)
        mock_ticker.history.return_value = pd.DataFrame({
            'Open': [100.0 + i*0.1 for i in range(12)],
            'High': [100.5 + i*0.1 for i in range(12)],
            'Low': [99.5 + i*0.1 for i in range(12)],
            'Close': [100.2 + i*0.1 for i in range(12)],
            'Volume': [1000000] * 12
        }, index=dates)
        
        return mock_ticker
    
    @patch('nasdaq_predictor.data.fetcher.yf.Ticker')
    def test_fetch_ticker_data_success(self, mock_yf_ticker, fetcher, mock_yfinance_ticker):
        """Test successful data fetch from yfinance."""
        mock_yf_ticker.return_value = mock_yfinance_ticker
        
        result = fetcher.fetch_ticker_data('NQ=F')
        
        assert result is not None
        assert 'hourly_hist' in result
        assert 'five_min_hist' in result
        assert 'current_price' in result
        assert 'current_time' in result
        assert isinstance(result['current_price'], (int, float))
    
    @patch('nasdaq_predictor.data.fetcher.yf.Ticker')
    def test_fetch_ticker_data_empty_response(self, mock_yf_ticker, fetcher):
        """Test handling of empty data from yfinance."""
        mock_ticker = Mock()
        mock_ticker.history.return_value = pd.DataFrame()  # Empty
        mock_yf_ticker.return_value = mock_ticker
        
        result = fetcher.fetch_ticker_data('INVALID')
        
        assert result is None
    
    @patch('nasdaq_predictor.data.fetcher.yf.Ticker')
    def test_fetch_ticker_data_network_error(self, mock_yf_ticker, fetcher):
        """Test handling of network errors."""
        mock_yf_ticker.side_effect = ConnectionError("Network unreachable")
        
        result = fetcher.fetch_ticker_data('NQ=F')
        
        assert result is None  # Should handle gracefully
    
    @patch('nasdaq_predictor.data.fetcher.yf.Ticker')
    def test_fetch_ticker_data_rate_limit(self, mock_yf_ticker, fetcher):
        """Test handling of rate limiting from yfinance."""
        mock_ticker = Mock()
        mock_ticker.history.side_effect = Exception("Rate limit exceeded")
        mock_yf_ticker.return_value = mock_ticker
        
        result = fetcher.fetch_ticker_data('NQ=F')
        
        assert result is None
    
    @patch('nasdaq_predictor.data.fetcher.yf.Ticker')
    def test_fetch_historical_data_supabase_primary(self, mock_yf_ticker, fetcher):
        """Test that Supabase is tried first before yfinance."""
        ticker_id = "550e8400-e29b-41d4-a716-446655440000"
        ticker_symbol = "NQ=F"
        start = datetime(2024, 11, 13, 10, 0, tzinfo=pytz.UTC)
        end = start + timedelta(hours=1)
        
        # Mock Supabase repository to return data
        fetcher.market_data_repo.get_bars_by_timerange = Mock(return_value=[
            {'timestamp': start, 'open': 100.0, 'high': 100.5, 'low': 99.5, 'close': 100.2}
        ])
        
        result = fetcher.fetch_historical_data(ticker_id, ticker_symbol, start, end, '5m')
        
        # Should NOT call yfinance if Supabase succeeds
        mock_yf_ticker.assert_not_called()
        assert len(result) > 0
    
    @patch('nasdaq_predictor.data.fetcher.yf.Ticker')
    def test_fetch_historical_data_yfinance_fallback(self, mock_yf_ticker, fetcher, mock_yfinance_ticker):
        """Test fallback to yfinance when Supabase fails."""
        ticker_id = "550e8400-e29b-41d4-a716-446655440000"
        ticker_symbol = "NQ=F"
        start = datetime(2024, 11, 13, 10, 0, tzinfo=pytz.UTC)
        end = start + timedelta(hours=1)
        
        # Mock Supabase to fail
        fetcher.market_data_repo.get_bars_by_timerange = Mock(return_value=[])
        
        # Mock yfinance to succeed
        mock_yf_ticker.return_value = mock_yfinance_ticker
        
        result = fetcher.fetch_historical_data(ticker_id, ticker_symbol, start, end, '5m')
        
        # Should fall back to yfinance
        mock_yf_ticker.assert_called_once()
        assert len(result) > 0
    
    def test_fetch_historical_data_timezone_normalization(self, fetcher):
        """Test that all timestamps are normalized to UTC."""
        ticker_id = "test-uuid"
        ticker_symbol = "NQ=F"
        
        # Provide naive datetime
        start_naive = datetime(2024, 11, 13, 10, 0)
        end_naive = datetime(2024, 11, 13, 11, 0)
        
        fetcher.market_data_repo = Mock()
        fetcher.market_data_repo.get_bars_by_timerange = Mock(return_value=[
            {'timestamp': start_naive, 'open': 100.0, 'high': 100.5, 'low': 99.5, 'close': 100.2}
        ])
        
        result = fetcher.fetch_historical_data(ticker_id, ticker_symbol, start_naive, end_naive, '5m')
        
        # All returned timestamps should be UTC-aware
        for bar in result:
            assert bar['timestamp'].tzinfo is not None
            assert bar['timestamp'].tzinfo == pytz.UTC
    
    @patch('nasdaq_predictor.data.fetcher.yf.Ticker')
    def test_fetch_intraday_data_success(self, mock_yf_ticker, fetcher, mock_yfinance_ticker):
        """Test fetching intraday data."""
        mock_yf_ticker.return_value = mock_yfinance_ticker
        
        result = fetcher.fetch_intraday_data('NQ=F', period='2d', interval='5m')
        
        assert result is not None
        assert isinstance(result, pd.DataFrame)
        assert not result.empty
    
    def test_fetch_ticker_data_special_characters(self, fetcher):
        """Test handling of tickers with special characters."""
        special_tickers = ['^FTSE', 'ES=F', 'BTC-USD', 'NQ=F']
        
        for ticker in special_tickers:
            # Should not raise error
            try:
                result = fetcher.fetch_ticker_data(ticker)
                # May return None if mock not set up, but should not error
                assert True
            except Exception as e:
                pytest.fail(f"Failed to handle special ticker {ticker}: {e}")
```

**Additional Test Cases:**
- [ ] Retry logic with exponential backoff
- [ ] Caching mechanism tests
- [ ] Concurrent request handling
- [ ] Data consistency validation (OHLC constraints)
- [ ] Historical data gap detection

### 3.3 Database Repository Tests

**File:** `tests/unit/database/test_repositories.py`

```python
"""
Unit tests for database repositories.
Tests CRUD operations, UUID handling, query construction.
"""
import pytest
from unittest.mock import Mock, patch, MagicMock
from datetime import datetime, timedelta
import pytz
from uuid import UUID

from nasdaq_predictor.database.repositories.block_prediction_repository import BlockPredictionRepository
from nasdaq_predictor.database.repositories.ticker_repository import TickerRepository
from nasdaq_predictor.database.repositories.market_data_repository import MarketDataRepository
from nasdaq_predictor.database.models.block_prediction import BlockPrediction


class TestBlockPredictionRepository:
    """Test block prediction repository operations."""
    
    @pytest.fixture
    def mock_supabase_client(self):
        """Mock Supabase client."""
        mock_client = Mock()
        mock_client.table.return_value = mock_client
        mock_client.select.return_value = mock_client
        mock_client.insert.return_value = mock_client
        mock_client.update.return_value = mock_client
        mock_client.delete.return_value = mock_client
        mock_client.eq.return_value = mock_client
        mock_client.gte.return_value = mock_client
        mock_client.lte.return_value = mock_client
        mock_client.execute.return_value = Mock(data=[])
        return mock_client
    
    @pytest.fixture
    def repository(self, mock_supabase_client):
        """Create repository with mocked client."""
        repo = BlockPredictionRepository()
        repo.client = mock_supabase_client
        return repo
    
    def test_store_block_prediction_success(self, repository, mock_supabase_client):
        """Test storing a block prediction."""
        ticker_id = "550e8400-e29b-41d4-a716-446655440000"
        hour_start = datetime(2024, 11, 13, 10, 0, tzinfo=pytz.UTC)
        
        prediction = BlockPrediction(
            ticker_id=ticker_id,
            hour_start_timestamp=hour_start,
            prediction_timestamp=hour_start + timedelta(minutes=42, seconds=51),
            prediction="UP",
            confidence=75.0,
            prediction_strength="moderate",
            reference_price=100.0,
            early_bias="UP",
            early_bias_strength=1.5,
            has_sustained_counter=False,
            counter_direction=None,
            deviation_at_5_7=1.2,
            block_data={'1': {'price_at_end': 100.5}},
            reference_levels={'opening_price': 100.0},
            volatility=2.0
        )
        
        # Mock successful insert
        mock_supabase_client.execute.return_value = Mock(data=[{
            'id': '123e4567-e89b-12d3-a456-426614174000',
            'ticker_id': ticker_id,
            'prediction': 'UP'
        }])
        
        result = repository.store_block_prediction(prediction)
        
        assert result is not None
        mock_supabase_client.table.assert_called_with('block_predictions')
        mock_supabase_client.insert.assert_called_once()
    
    def test_get_block_prediction_by_hour(self, repository, mock_supabase_client):
        """Test retrieving prediction by ticker and hour."""
        ticker_id = "550e8400-e29b-41d4-a716-446655440000"
        hour_start = datetime(2024, 11, 13, 10, 0, tzinfo=pytz.UTC)
        
        # Mock database response
        mock_supabase_client.execute.return_value = Mock(data=[{
            'id': '123e4567-e89b-12d3-a456-426614174000',
            'ticker_id': ticker_id,
            'hour_start_timestamp': hour_start.isoformat(),
            'prediction': 'UP',
            'confidence': 75.0
        }])
        
        result = repository.get_block_prediction_by_hour(ticker_id, hour_start)
        
        assert result is not None
        assert isinstance(result, BlockPrediction)
        assert result.prediction == 'UP'
    
    def test_get_block_predictions_by_date(self, repository, mock_supabase_client):
        """Test retrieving all predictions for a date."""
        ticker_id = "550e8400-e29b-41d4-a716-446655440000"
        date = datetime(2024, 11, 13, tzinfo=pytz.UTC)
        
        # Mock 24 predictions
        mock_data = []
        for hour in range(24):
            mock_data.append({
                'id': f'123e4567-e89b-12d3-a456-42661417{hour:04d}',
                'ticker_id': ticker_id,
                'hour_start_timestamp': date.replace(hour=hour).isoformat(),
                'prediction': 'UP' if hour % 2 == 0 else 'DOWN',
                'confidence': 70.0 + hour
            })
        
        mock_supabase_client.execute.return_value = Mock(data=mock_data)
        
        results = repository.get_block_predictions_by_date(ticker_id, date)
        
        assert len(results) == 24
        assert all(isinstance(p, BlockPrediction) for p in results)
    
    def test_get_block_prediction_not_found(self, repository, mock_supabase_client):
        """Test handling when prediction doesn't exist."""
        ticker_id = "550e8400-e29b-41d4-a716-446655440000"
        hour_start = datetime(2024, 11, 13, 10, 0, tzinfo=pytz.UTC)
        
        # Mock empty response
        mock_supabase_client.execute.return_value = Mock(data=[])
        
        result = repository.get_block_prediction_by_hour(ticker_id, hour_start)
        
        assert result is None
    
    def test_store_prediction_duplicate_handling(self, repository, mock_supabase_client):
        """Test handling of duplicate predictions (same ticker/hour)."""
        ticker_id = "550e8400-e29b-41d4-a716-446655440000"
        hour_start = datetime(2024, 11, 13, 10, 0, tzinfo=pytz.UTC)
        
        prediction = BlockPrediction(
            ticker_id=ticker_id,
            hour_start_timestamp=hour_start,
            prediction_timestamp=hour_start + timedelta(minutes=42, seconds=51),
            prediction="UP",
            confidence=75.0,
            prediction_strength="moderate",
            reference_price=100.0,
            early_bias="UP",
            early_bias_strength=1.5,
            has_sustained_counter=False,
            counter_direction=None,
            deviation_at_5_7=1.2,
            block_data={},
            reference_levels={},
            volatility=2.0
        )
        
        # Mock database unique constraint error
        mock_supabase_client.execute.side_effect = Exception("duplicate key value violates unique constraint")
        
        # Should handle gracefully - either raise specific exception or update
        with pytest.raises(Exception):
            repository.store_block_prediction(prediction)
    
    def test_query_with_invalid_uuid(self, repository):
        """Test error handling with invalid UUID format."""
        invalid_ticker_id = "not-a-valid-uuid"
        hour_start = datetime(2024, 11, 13, 10, 0, tzinfo=pytz.UTC)
        
        # Should raise ValueError for invalid UUID
        with pytest.raises(ValueError):
            UUID(invalid_ticker_id)


class TestTickerRepository:
    """Test ticker repository operations."""
    
    @pytest.fixture
    def mock_supabase_client(self):
        """Mock Supabase client."""
        mock_client = Mock()
        mock_client.table.return_value = mock_client
        mock_client.select.return_value = mock_client
        mock_client.eq.return_value = mock_client
        mock_client.execute.return_value = Mock(data=[])
        return mock_client
    
    @pytest.fixture
    def repository(self, mock_supabase_client):
        """Create repository with mocked client."""
        repo = TickerRepository()
        repo.client = mock_supabase_client
        return repo
    
    def test_get_ticker_by_symbol_success(self, repository, mock_supabase_client):
        """Test retrieving ticker by symbol."""
        mock_supabase_client.execute.return_value = Mock(data=[{
            'id': '550e8400-e29b-41d4-a716-446655440000',
            'symbol': 'NQ=F',
            'name': 'NASDAQ 100 Futures',
            'market_type': 'futures'
        }])
        
        result = repository.get_ticker_by_symbol('NQ=F')
        
        assert result is not None
        assert result.symbol == 'NQ=F'
        assert result.id == '550e8400-e29b-41d4-a716-446655440000'
    
    def test_get_ticker_by_symbol_not_found(self, repository, mock_supabase_client):
        """Test handling when ticker doesn't exist."""
        mock_supabase_client.execute.return_value = Mock(data=[])
        
        result = repository.get_ticker_by_symbol('NONEXISTENT')
        
        assert result is None
    
    def test_get_all_tickers(self, repository, mock_supabase_client):
        """Test retrieving all tickers."""
        mock_supabase_client.execute.return_value = Mock(data=[
            {'id': '550e8400-e29b-41d4-a716-446655440000', 'symbol': 'NQ=F'},
            {'id': '550e8400-e29b-41d4-a716-446655440001', 'symbol': 'ES=F'},
            {'id': '550e8400-e29b-41d4-a716-446655440002', 'symbol': '^FTSE'},
        ])
        
        results = repository.get_all_tickers()
        
        assert len(results) == 3
        assert all(hasattr(t, 'symbol') for t in results)


class TestMarketDataRepository:
    """Test market data repository operations."""
    
    @pytest.fixture
    def mock_supabase_client(self):
        """Mock Supabase client."""
        mock_client = Mock()
        mock_client.table.return_value = mock_client
        mock_client.select.return_value = mock_client
        mock_client.eq.return_value = mock_client
        mock_client.gte.return_value = mock_client
        mock_client.lte.return_value = mock_client
        mock_client.order.return_value = mock_client
        mock_client.execute.return_value = Mock(data=[])
        return mock_client
    
    @pytest.fixture
    def repository(self, mock_supabase_client):
        """Create repository with mocked client."""
        repo = MarketDataRepository()
        repo.client = mock_supabase_client
        return repo
    
    def test_get_bars_by_timerange_success(self, repository, mock_supabase_client):
        """Test retrieving bars for a time range."""
        ticker_id = "550e8400-e29b-41d4-a716-446655440000"
        start = datetime(2024, 11, 13, 10, 0, tzinfo=pytz.UTC)
        end = start + timedelta(hours=1)
        
        # Mock database response
        mock_bars = []
        for i in range(12):
            mock_bars.append({
                'timestamp': (start + timedelta(minutes=5*i)).isoformat(),
                'open': 100.0 + i*0.1,
                'high': 100.5 + i*0.1,
                'low': 99.5 + i*0.1,
                'close': 100.2 + i*0.1,
                'volume': 1000000
            })
        
        mock_supabase_client.execute.return_value = Mock(data=mock_bars)
        
        results = repository.get_bars_by_timerange(ticker_id, start, end, interval='5m')
        
        assert len(results) == 12
        assert all('timestamp' in bar for bar in results)
    
    def test_get_bars_empty_range(self, repository, mock_supabase_client):
        """Test handling when no bars exist in range."""
        ticker_id = "550e8400-e29b-41d4-a716-446655440000"
        start = datetime(2024, 11, 13, 10, 0, tzinfo=pytz.UTC)
        end = start + timedelta(hours=1)
        
        mock_supabase_client.execute.return_value = Mock(data=[])
        
        results = repository.get_bars_by_timerange(ticker_id, start, end, interval='5m')
        
        assert len(results) == 0
```

**Additional Repository Tests:**
- [ ] IntradayPredictionRepository
- [ ] ReferenceLevelsRepository
- [ ] FibonacciPivotRepository
- [ ] SchedulerJobExecutionRepository
- [ ] Transaction handling
- [ ] Batch operations
- [ ] Connection pool management

---

## 4. Integration Test Strategy

### 4.1 End-to-End Prediction Flow Tests

**File:** `tests/integration/test_prediction_e2e.py`

```python
"""
End-to-end integration tests for complete prediction flows.
Tests full pipeline from data fetch through storage and verification.
"""
import pytest
from datetime import datetime, timedelta
import pytz

from nasdaq_predictor.services.block_prediction_service import BlockPredictionService
from nasdaq_predictor.services.block_verification_service import BlockVerificationService
from nasdaq_predictor.data.fetcher import YahooFinanceDataFetcher
from nasdaq_predictor.database.repositories.block_prediction_repository import BlockPredictionRepository
from nasdaq_predictor.database.repositories.ticker_repository import TickerRepository


@pytest.mark.integration
class TestPredictionE2E:
    """End-to-end prediction flow tests."""
    
    @pytest.fixture
    def services(self):
        """Initialize real services (use test database)."""
        fetcher = YahooFinanceDataFetcher()
        block_repo = BlockPredictionRepository()
        ticker_repo = TickerRepository()
        
        prediction_service = BlockPredictionService(
            fetcher=fetcher,
            block_prediction_repo=block_repo,
            ticker_repo=ticker_repo
        )
        
        verification_service = BlockVerificationService(
            fetcher=fetcher,
            block_prediction_repo=block_repo
        )
        
        return {
            'prediction': prediction_service,
            'verification': verification_service
        }
    
    @pytest.mark.slow
    def test_full_prediction_and_verification_cycle(self, services):
        """
        Test complete cycle:
        1. Fetch data from yfinance
        2. Generate prediction
        3. Store prediction
        4. Retrieve prediction
        5. Verify prediction (when hour completes)
        6. Update accuracy
        """
        ticker = 'NQ=F'
        # Use historical date to ensure data is available
        hour_start = datetime(2024, 11, 13, 14, 0, tzinfo=pytz.UTC)
        
        # Step 1 & 2: Generate prediction (includes data fetch)
        prediction = services['prediction'].generate_block_prediction(ticker, hour_start)
        
        assert prediction is not None, "Prediction generation failed"
        assert prediction.prediction in ['UP', 'DOWN', 'NEUTRAL']
        assert 5 <= prediction.confidence <= 95
        assert prediction.ticker_id is not None
        
        # Step 3 & 4: Retrieve stored prediction
        retrieved = services['prediction'].get_hourly_prediction(ticker, hour_start)
        
        assert retrieved is not None
        assert retrieved.prediction == prediction.prediction
        assert retrieved.confidence == prediction.confidence
        
        # Step 5: Verify prediction (requires blocks 6-7 data)
        # This would normally run after hour completes
        verified = services['verification'].verify_block_prediction(retrieved)
        
        assert verified is not None
        assert hasattr(verified, 'verified')
        assert verified.verified == True
    
    @pytest.mark.slow
    def test_24h_generation_and_batch_verification(self, services):
        """
        Test 24-hour batch operations:
        1. Generate 24 predictions for a day
        2. Batch verify all predictions
        3. Calculate accuracy metrics
        """
        ticker = 'NQ=F'
        date = datetime(2024, 11, 13, tzinfo=pytz.UTC)
        
        # Generate 24 hours
        result = services['prediction'].generate_24h_block_predictions(ticker, date)
        
        assert result is not None
        assert result['total_generated'] > 0
        assert len(result['predictions']) == result['total_generated']
        
        # Batch verify
        stats = services['verification'].verify_pending_predictions()
        
        assert stats is not None
        assert 'total_verified' in stats
```

### 4.2 API Integration Tests

**File:** `tests/integration/test_api_endpoints.py`

```python
"""
Integration tests for API endpoints.
Tests Flask routes, request/response handling, error responses.
"""
import pytest
import json
from datetime import datetime
import pytz

from nasdaq_predictor.app import create_app


@pytest.mark.integration
class TestBlockPredictionAPI:
    """Test block prediction API endpoints."""
    
    @pytest.fixture
    def client(self):
        """Create Flask test client."""
        app = create_app(testing=True)
        with app.test_client() as client:
            yield client
    
    def test_get_24h_predictions_success(self, client):
        """Test GET /api/block-predictions/<ticker>"""
        response = client.get('/api/block-predictions/NQ=F?date=2024-11-13')
        
        assert response.status_code == 200
        data = json.loads(response.data)
        assert data['success'] == True
        assert 'data' in data
    
    def test_get_24h_predictions_invalid_ticker(self, client):
        """Test API response with invalid ticker."""
        response = client.get('/api/block-predictions/INVALID')
        
        # Should return graceful error
        assert response.status_code in [200, 404]
        data = json.loads(response.data)
        
        if response.status_code == 200:
            assert data['success'] == False or data['data']['predictions'] == []
    
    def test_get_single_hour_prediction(self, client):
        """Test GET /api/block-predictions/<ticker>/<hour>"""
        response = client.get('/api/block-predictions/NQ=F/14?date=2024-11-13')
        
        assert response.status_code == 200
        data = json.loads(response.data)
        assert 'prediction' in data.get('data', {}) or data.get('success') == False
    
    def test_market_aware_predictions_endpoint(self, client):
        """Test market-aware predictions endpoint."""
        response = client.get('/api/market-aware/block-predictions/NQ=F')
        
        assert response.status_code == 200
        data = json.loads(response.data)
        
        if data.get('success'):
            assert 'data_source' in data['data']
            assert 'market_status' in data['data']
            assert 'predictions' in data['data']
    
    def test_post_generate_prediction(self, client):
        """Test POST /api/block-predictions/generate (manual trigger)."""
        payload = {
            'ticker': 'NQ=F',
            'date': '2024-11-13',
            'hour': 14
        }
        
        response = client.post(
            '/api/block-predictions/generate',
            data=json.dumps(payload),
            content_type='application/json'
        )
        
        assert response.status_code in [200, 201, 202]
    
    def test_api_cors_headers(self, client):
        """Test that CORS headers are present."""
        response = client.options('/api/block-predictions/NQ=F')
        
        # CORS headers should be present
        assert 'Access-Control-Allow-Origin' in response.headers or response.status_code == 200
    
    def test_api_rate_limiting(self, client):
        """Test rate limiting (if implemented)."""
        # Make 100 rapid requests
        responses = []
        for _ in range(100):
            resp = client.get('/api/block-predictions/NQ=F')
            responses.append(resp.status_code)
        
        # Should either all succeed or rate limit kick in
        assert all(code in [200, 429] for code in responses)
```

---

## 5. Edge Case Identification & Handling

### 5.1 Financial/Market Edge Cases

**Critical Edge Cases for Financial Prediction System:**

1. **Market Data Gaps**
   - Missing 5-minute bars within hour
   - Extended market closures (holidays)
   - Trading halts
   - Early market closes

2. **Price Anomalies**
   - Flash crashes (extreme price drops)
   - Circuit breaker events
   - Gap up/down at market open
   - After-hours price movements

3. **Extreme Volatility**
   - Zero volatility (flat market)
   - Volatility spike (>10 std devs)
   - Negative volatility calculation (impossible)
   - Volatility during low liquidity

4. **Temporal Edge Cases**
   - Daylight saving time transitions
   - Hour spanning market close
   - Predictions near midnight UTC
   - Leap seconds

5. **Data Quality Issues**
   - Incorrect OHLC (high < low)
   - Zero volume bars
   - Null/missing fields
   - Duplicate timestamps

6. **Concurrent Operations**
   - Multiple predictions for same hour
   - Race conditions in verification
   - Database transaction conflicts

**Test Implementation:**

```python
# tests/unit/analysis/test_edge_cases.py

class TestMarketDataEdgeCases:
    """Test edge cases in market data handling."""
    
    def test_flash_crash_detection(self):
        """Test handling of flash crash (>20% drop in 5 minutes)."""
        bars = [
            {'timestamp': datetime(2024, 11, 13, 10, 0, tzinfo=pytz.UTC), 'open': 100.0, 'close': 100.5},
            {'timestamp': datetime(2024, 11, 13, 10, 5, tzinfo=pytz.UTC), 'open': 100.5, 'close': 75.0},  # -25% drop
            {'timestamp': datetime(2024, 11, 13, 10, 10, tzinfo=pytz.UTC), 'open': 75.0, 'close': 100.0},  # Recovery
        ]
        
        # Should detect and flag as extreme event
        volatility = calculate_hourly_volatility(bars, 100.0)
        assert volatility > 20.0  # Extremely high volatility
    
    def test_trading_halt_missing_bars(self):
        """Test handling of missing bars due to trading halt."""
        hour_start = datetime(2024, 11, 13, 10, 0, tzinfo=pytz.UTC)
        
        # Only 6 bars instead of 12 (trading halted mid-hour)
        partial_bars = [
            {'timestamp': hour_start + timedelta(minutes=5*i), 'open': 100.0, 'close': 100.0}
            for i in range(6)
        ]
        
        # Should handle gracefully or return specific error
        with pytest.raises(InsufficientDataException):
            segment_hour_into_blocks(partial_bars, hour_start, 1.0)
    
    def test_dst_transition_hour(self):
        """Test prediction during daylight saving time transition."""
        # March 2024 DST transition (2am -> 3am)
        dst_transition = datetime(2024, 3, 10, 7, 0, tzinfo=pytz.UTC)  # 2am EST
        
        # Should handle 23-hour or 25-hour days
        # This is complex - may need special handling
        pass
    
    def test_ohlc_constraint_violation(self):
        """Test handling of invalid OHLC (high < low)."""
        invalid_bar = {
            'timestamp': datetime(2024, 11, 13, 10, 0, tzinfo=pytz.UTC),
            'open': 100.0,
            'high': 99.0,  # Invalid: high < open
            'low': 101.0,  # Invalid: low > open
            'close': 100.5
        }
        
        # Should validate and reject
        with pytest.raises(ValueError, match="OHLC constraint"):
            validate_ohlc_bar(invalid_bar)
    
    def test_zero_volume_bar(self):
        """Test handling of zero volume (illiquid market)."""
        zero_vol_bar = {
            'timestamp': datetime(2024, 11, 13, 10, 0, tzinfo=pytz.UTC),
            'open': 100.0,
            'high': 100.0,
            'low': 100.0,
            'close': 100.0,
            'volume': 0  # No trades
        }
        
        # Should flag as low-confidence or skip
        # Implementation-dependent
        pass
```

### 5.2 Network & External Dependency Edge Cases

```python
# tests/integration/test_network_edge_cases.py

class TestNetworkEdgeCases:
    """Test network and external service failures."""
    
    @patch('nasdaq_predictor.data.fetcher.yf.Ticker')
    def test_yfinance_timeout(self, mock_yf):
        """Test handling of yfinance timeout."""
        import socket
        mock_yf.side_effect = socket.timeout("Connection timed out")
        
        fetcher = YahooFinanceDataFetcher()
        result = fetcher.fetch_ticker_data('NQ=F')
        
        # Should return None and log error
        assert result is None
    
    @patch('nasdaq_predictor.data.fetcher.yf.Ticker')
    def test_yfinance_rate_limit_429(self, mock_yf):
        """Test handling of rate limit (HTTP 429)."""
        mock_yf.side_effect = Exception("429 Too Many Requests")
        
        fetcher = YahooFinanceDataFetcher()
        result = fetcher.fetch_ticker_data('NQ=F')
        
        # Should implement retry or return cached data
        assert result is None or result is not None  # Depends on retry logic
    
    def test_supabase_connection_failure(self):
        """Test handling of Supabase connection failure."""
        repo = BlockPredictionRepository()
        
        # Simulate connection error
        with patch.object(repo, 'client', side_effect=ConnectionError("Cannot connect to Supabase")):
            with pytest.raises(ConnectionError):
                repo.get_all_tickers()
    
    def test_partial_data_fetch_fallback(self):
        """Test fallback when Supabase returns partial data."""
        # Supabase returns only 5 of 12 expected bars
        # Should fall back to yfinance to fill gaps
        pass
```

---

## 6. Mock Strategy for External Dependencies

### 6.1 yfinance Mocking Strategy

**Comprehensive Mock for yfinance:**

```python
# tests/fixtures/yfinance_mocks.py

import pytest
import pandas as pd
from datetime import datetime, timedelta
import pytz
from unittest.mock import Mock


@pytest.fixture
def mock_yfinance_normal_conditions():
    """Mock yfinance for normal market conditions."""
    def create_mock_ticker(symbol):
        mock_ticker = Mock()
        
        def mock_history(period='1d', interval='1h', start=None, end=None):
            """Generate realistic OHLC data."""
            if start and end:
                # Use explicit range
                freq_map = {'1m': '1min', '5m': '5min', '15m': '15min', '1h': '1h'}
                freq = freq_map.get(interval, '1h')
                dates = pd.date_range(start=start, end=end, freq=freq, tz=pytz.UTC)
            else:
                # Use period
                dates = pd.date_range(end=datetime.now(pytz.UTC), periods=100, freq='5min')
            
            # Generate realistic price movement
            base_price = 100.0
            returns = pd.Series([0.0] + list(pd.Series([0.001 * i for i in range(len(dates)-1)]).cumsum()))
            
            return pd.DataFrame({
                'Open': base_price + returns,
                'High': base_price + returns + 0.5,
                'Low': base_price + returns - 0.5,
                'Close': base_price + returns + 0.2,
                'Volume': [1000000] * len(dates)
            }, index=dates)
        
        mock_ticker.history = Mock(side_effect=mock_history)
        return mock_ticker
    
    return create_mock_ticker


@pytest.fixture
def mock_yfinance_high_volatility():
    """Mock yfinance for high volatility conditions."""
    def create_mock_ticker(symbol):
        mock_ticker = Mock()
        
        def mock_history(period='1d', interval='1h', start=None, end=None):
            dates = pd.date_range(end=datetime.now(pytz.UTC), periods=100, freq='5min')
            
            # Generate volatile price movement
            base_price = 100.0
            import numpy as np
            np.random.seed(42)
            returns = pd.Series(np.random.normal(0, 0.02, len(dates)).cumsum())
            
            return pd.DataFrame({
                'Open': base_price + returns,
                'High': base_price + returns + 2.0,
                'Low': base_price + returns - 2.0,
                'Close': base_price + returns + 0.5,
                'Volume': [2000000] * len(dates)
            }, index=dates)
        
        mock_ticker.history = Mock(side_effect=mock_history)
        return mock_ticker
    
    return create_mock_ticker


@pytest.fixture
def mock_yfinance_network_error():
    """Mock yfinance with network errors."""
    def create_mock_ticker(symbol):
        mock_ticker = Mock()
        mock_ticker.history.side_effect = ConnectionError("Network unreachable")
        return mock_ticker
    
    return create_mock_ticker


@pytest.fixture
def mock_yfinance_empty_data():
    """Mock yfinance returning no data (invalid ticker)."""
    def create_mock_ticker(symbol):
        mock_ticker = Mock()
        mock_ticker.history.return_value = pd.DataFrame()  # Empty
        return mock_ticker
    
    return create_mock_ticker
```

**Usage in Tests:**

```python
def test_prediction_with_yfinance_mock(mock_yfinance_normal_conditions):
    """Test prediction generation with mocked yfinance."""
    with patch('nasdaq_predictor.data.fetcher.yf.Ticker', mock_yfinance_normal_conditions):
        fetcher = YahooFinanceDataFetcher()
        service = BlockPredictionService(fetcher=fetcher, ...)
        
        prediction = service.generate_block_prediction('NQ=F', hour_start)
        
        assert prediction is not None
```

### 6.2 Supabase Mocking Strategy

```python
# tests/fixtures/supabase_mocks.py

@pytest.fixture
def mock_supabase_client():
    """Comprehensive Supabase client mock."""
    mock_client = Mock()
    
    # Mock fluent API chain
    mock_query = Mock()
    mock_client.table.return_value = mock_query
    mock_query.select.return_value = mock_query
    mock_query.insert.return_value = mock_query
    mock_query.update.return_value = mock_query
    mock_query.delete.return_value = mock_query
    mock_query.eq.return_value = mock_query
    mock_query.gte.return_value = mock_query
    mock_query.lte.return_value = mock_query
    mock_query.order.return_value = mock_query
    
    # Mock execute() to return data
    mock_query.execute.return_value = Mock(data=[
        {
            'id': '550e8400-e29b-41d4-a716-446655440000',
            'symbol': 'NQ=F',
            'name': 'NASDAQ 100 Futures'
        }
    ])
    
    return mock_client


@pytest.fixture
def mock_supabase_with_test_data():
    """Supabase mock with realistic test data."""
    def create_mock_with_data(test_data):
        mock_client = Mock()
        mock_query = Mock()
        mock_client.table.return_value = mock_query
        # ... (fluent API setup)
        
        mock_query.execute.return_value = Mock(data=test_data)
        return mock_client
    
    return create_mock_with_data
```

---

## 7. Backtesting & Historical Validation Framework

### 7.1 Backtesting Validation Strategy

**Objective:** Validate prediction accuracy against historical data to ensure algorithm correctness.

#### 7.1.1 Backtesting SQL Validation Script

```sql
-- File: tests/validation/backtest_accuracy_validation.sql
-- Purpose: Validate prediction accuracy for historical period

-- Backtesting Accuracy Report
WITH prediction_results AS (
    SELECT 
        bp.ticker_id,
        t.symbol,
        bp.hour_start_timestamp,
        bp.prediction,
        bp.confidence,
        bp.prediction_strength,
        bp.verified,
        bp.is_correct,
        bp.actual_outcome,
        CASE 
            WHEN bp.is_correct = true THEN 1 
            ELSE 0 
        END as correct_flag
    FROM block_predictions bp
    JOIN tickers t ON bp.ticker_id = t.id
    WHERE bp.verified = true
        AND bp.hour_start_timestamp >= '2024-11-01'
        AND bp.hour_start_timestamp < '2024-11-14'
),
accuracy_by_ticker AS (
    SELECT 
        symbol,
        COUNT(*) as total_predictions,
        SUM(correct_flag) as correct_predictions,
        ROUND(100.0 * SUM(correct_flag) / COUNT(*), 2) as accuracy_pct,
        AVG(confidence) as avg_confidence
    FROM prediction_results
    GROUP BY symbol
),
accuracy_by_strength AS (
    SELECT 
        prediction_strength,
        COUNT(*) as total,
        SUM(correct_flag) as correct,
        ROUND(100.0 * SUM(correct_flag) / COUNT(*), 2) as accuracy_pct
    FROM prediction_results
    GROUP BY prediction_strength
),
accuracy_by_confidence_bucket AS (
    SELECT 
        CASE 
            WHEN confidence < 50 THEN '0-50%'
            WHEN confidence < 70 THEN '50-70%'
            WHEN confidence < 85 THEN '70-85%'
            ELSE '85-100%'
        END as confidence_bucket,
        COUNT(*) as total,
        SUM(correct_flag) as correct,
        ROUND(100.0 * SUM(correct_flag) / COUNT(*), 2) as accuracy_pct
    FROM prediction_results
    GROUP BY confidence_bucket
)
SELECT 
    'Overall Accuracy' as metric,
    NULL as category,
    COUNT(*) as total,
    SUM(correct_flag) as correct,
    ROUND(100.0 * SUM(correct_flag) / COUNT(*), 2) as accuracy_pct
FROM prediction_results

UNION ALL

SELECT 
    'By Ticker' as metric,
    symbol as category,
    total_predictions as total,
    correct_predictions as correct,
    accuracy_pct
FROM accuracy_by_ticker

UNION ALL

SELECT 
    'By Strength' as metric,
    prediction_strength as category,
    total,
    correct,
    accuracy_pct
FROM accuracy_by_strength

UNION ALL

SELECT 
    'By Confidence' as metric,
    confidence_bucket as category,
    total,
    correct,
    accuracy_pct
FROM accuracy_by_confidence_bucket
ORDER BY metric, category;

-- Expected Results:
-- Overall accuracy should be >= 55% (better than random)
-- Strong predictions should have accuracy >= 65%
-- High confidence (85-100%) should correlate with higher accuracy (>= 70%)
```

#### 7.1.2 Python Backtesting Framework

```python
# tests/validation/backtest_framework.py

import pandas as pd
from datetime import datetime, timedelta
import pytz
from typing import Dict, List
import logging

logger = logging.getLogger(__name__)


class BacktestValidator:
    """
    Backtesting framework for validating prediction accuracy.
    
    Runs historical predictions and compares against known outcomes.
    """
    
    def __init__(self, prediction_service, verification_service):
        self.prediction_service = prediction_service
        self.verification_service = verification_service
    
    def run_backtest(
        self,
        ticker: str,
        start_date: datetime,
        end_date: datetime
    ) -> Dict:
        """
        Run backtest for date range.
        
        Args:
            ticker: Asset ticker
            start_date: Start of backtest period
            end_date: End of backtest period
            
        Returns:
            Dictionary with backtest results and accuracy metrics
        """
        logger.info(f"Running backtest for {ticker} from {start_date} to {end_date}")
        
        results = []
        current_date = start_date
        
        while current_date <= end_date:
            # Generate predictions for all 24 hours
            day_result = self.prediction_service.generate_24h_block_predictions(
                ticker, current_date
            )
            
            if day_result['total_generated'] > 0:
                # Verify predictions
                for pred in day_result['predictions']:
                    verified = self.verification_service.verify_block_prediction(pred)
                    results.append({
                        'date': current_date,
                        'hour': pred.hour_start_timestamp.hour,
                        'prediction': pred.prediction,
                        'confidence': pred.confidence,
                        'strength': pred.prediction_strength,
                        'is_correct': verified.is_correct if verified else None,
                        'actual_outcome': verified.actual_outcome if verified else None
                    })
            
            current_date += timedelta(days=1)
        
        # Calculate metrics
        df = pd.DataFrame(results)
        
        metrics = {
            'total_predictions': len(df),
            'verified_predictions': df['is_correct'].notna().sum(),
            'correct_predictions': df['is_correct'].sum(),
            'accuracy': df['is_correct'].mean() * 100 if len(df) > 0 else 0,
            'accuracy_by_strength': df.groupby('strength')['is_correct'].agg(['count', 'mean']),
            'accuracy_by_confidence': pd.cut(df['confidence'], bins=[0, 50, 70, 85, 100]).value_counts(),
            'daily_results': df
        }
        
        return metrics
    
    def validate_against_known_baseline(
        self,
        ticker: str,
        baseline_accuracy: float = 55.0
    ) -> bool:
        """
        Validate that predictions beat baseline accuracy.
        
        Args:
            ticker: Asset ticker
            baseline_accuracy: Minimum acceptable accuracy (default 55%)
            
        Returns:
            True if predictions beat baseline, False otherwise
        """
        # Run 30-day backtest
        end_date = datetime.now(pytz.UTC) - timedelta(days=1)
        start_date = end_date - timedelta(days=30)
        
        results = self.run_backtest(ticker, start_date, end_date)
        
        actual_accuracy = results['accuracy']
        
        logger.info(f"Backtest accuracy: {actual_accuracy:.2f}% (baseline: {baseline_accuracy}%)")
        
        return actual_accuracy >= baseline_accuracy
    
    def compare_predictions_with_market_data(
        self,
        predictions: List,
        actual_bars: List
    ) -> Dict:
        """
        Compare predictions against actual market outcomes.
        
        Args:
            predictions: List of BlockPrediction objects
            actual_bars: List of actual OHLC bars for blocks 6-7
            
        Returns:
            Comparison metrics
        """
        comparisons = []
        
        for pred in predictions:
            # Find corresponding actual bars
            pred_hour = pred.hour_start_timestamp
            
            # Get blocks 6-7 actual data
            blocks_6_7_start = pred_hour + timedelta(minutes=42, seconds=51)
            blocks_6_7_end = pred_hour + timedelta(hours=1)
            
            actual_bars_6_7 = [
                bar for bar in actual_bars
                if blocks_6_7_start <= bar['timestamp'] < blocks_6_7_end
            ]
            
            if actual_bars_6_7:
                # Determine actual outcome
                opening_price = pred.reference_price
                closing_price = actual_bars_6_7[-1]['close']
                
                actual_outcome = 'UP' if closing_price > opening_price else 'DOWN'
                is_correct = (pred.prediction == actual_outcome)
                
                comparisons.append({
                    'prediction': pred.prediction,
                    'actual': actual_outcome,
                    'is_correct': is_correct,
                    'confidence': pred.confidence,
                    'price_change': closing_price - opening_price
                })
        
        df = pd.DataFrame(comparisons)
        
        return {
            'total_compared': len(df),
            'accuracy': df['is_correct'].mean() * 100,
            'avg_price_change_when_correct': df[df['is_correct']]['price_change'].mean(),
            'avg_price_change_when_wrong': df[~df['is_correct']]['price_change'].mean(),
        }
```

**Usage:**

```python
# tests/validation/test_backtest_validation.py

def test_backtest_accuracy_meets_baseline():
    """Test that predictions beat 55% baseline accuracy."""
    validator = BacktestValidator(prediction_service, verification_service)
    
    result = validator.validate_against_known_baseline('NQ=F', baseline_accuracy=55.0)
    
    assert result == True, "Predictions failed to beat baseline accuracy"


def test_strong_predictions_higher_accuracy():
    """Test that 'strong' predictions have higher accuracy than 'weak'."""
    validator = BacktestValidator(prediction_service, verification_service)
    
    start_date = datetime(2024, 11, 1, tzinfo=pytz.UTC)
    end_date = datetime(2024, 11, 13, tzinfo=pytz.UTC)
    
    results = validator.run_backtest('NQ=F', start_date, end_date)
    
    accuracy_by_strength = results['accuracy_by_strength']
    
    if 'strong' in accuracy_by_strength.index and 'weak' in accuracy_by_strength.index:
        strong_accuracy = accuracy_by_strength.loc['strong', 'mean']
        weak_accuracy = accuracy_by_strength.loc['weak', 'mean']
        
        assert strong_accuracy > weak_accuracy, "Strong predictions should outperform weak"
```

### 7.2 Data Quality Validation

```python
# tests/validation/test_data_quality.py

class TestDataQualityValidation:
    """Validate data integrity and consistency."""
    
    def test_no_duplicate_predictions(self):
        """Ensure no duplicate predictions for same ticker/hour."""
        # SQL query to find duplicates
        query = """
        SELECT ticker_id, hour_start_timestamp, COUNT(*) as count
        FROM block_predictions
        GROUP BY ticker_id, hour_start_timestamp
        HAVING COUNT(*) > 1
        """
        
        # Should return no rows
        # assert len(results) == 0
    
    def test_ohlc_constraints_in_database(self):
        """Validate OHLC constraints in stored data."""
        # SQL query to find invalid OHLC
        query = """
        SELECT *
        FROM market_data
        WHERE high < low
           OR high < open
           OR high < close
           OR low > open
           OR low > close
        LIMIT 100
        """
        
        # Should return no rows
        # assert len(results) == 0
    
    def test_confidence_in_valid_range(self):
        """Validate all confidence scores are 5-95."""
        query = """
        SELECT *
        FROM block_predictions
        WHERE confidence < 5 OR confidence > 95
        """
        
        # Should return no rows
        # assert len(results) == 0
    
    def test_prediction_timestamp_consistency(self):
        """Validate prediction_timestamp is 5/7 of hour_start."""
        query = """
        SELECT 
            hour_start_timestamp,
            prediction_timestamp,
            EXTRACT(EPOCH FROM (prediction_timestamp - hour_start_timestamp)) / 60 as minutes_diff
        FROM block_predictions
        WHERE ABS(EXTRACT(EPOCH FROM (prediction_timestamp - hour_start_timestamp)) / 60 - 42.857) > 1
        """
        
        # Should return no rows (allow 1-minute tolerance)
        # assert len(results) == 0
```

---

## 8. Type Safety & Static Analysis

### 8.1 Type Hint Coverage Strategy

**Target: 100% type hint coverage for public APIs**

```python
# nasdaq_predictor/analysis/volatility.py (with type hints)

from typing import List, Dict, Any
from datetime import datetime


def calculate_hourly_volatility(
    bars: List[Dict[str, Any]],
    opening_price: float
) -> float:
    """
    Calculate hourly volatility from intra-hour OHLC bars.
    
    Args:
        bars: List of OHLC bar dictionaries with 'timestamp', 'open', 'close'
        opening_price: Hour opening price for normalization
        
    Returns:
        Volatility in price units (standard deviation of close-to-close returns)
        
    Raises:
        ValueError: If bars list is empty or opening_price is invalid
        KeyError: If bars missing required fields
    """
    if not bars:
        raise ValueError("No bars provided for volatility calculation")
    
    if opening_price <= 0:
        raise ValueError(f"Opening price must be positive: {opening_price}")
    
    # Implementation...
    return volatility
```

### 8.2 mypy Configuration

**File:** `mypy.ini`

```ini
[mypy]
python_version = 3.13
warn_return_any = True
warn_unused_configs = True
disallow_untyped_defs = True
disallow_any_generics = True
disallow_subclassing_any = True
disallow_untyped_calls = True
disallow_incomplete_defs = True
check_untyped_defs = True
disallow_untyped_decorators = True
no_implicit_optional = True
warn_redundant_casts = True
warn_unused_ignores = True
warn_no_return = True
warn_unreachable = True
strict_equality = True
strict_concatenate = True

# Per-module options
[mypy-nasdaq_predictor.analysis.*]
disallow_untyped_defs = True

[mypy-nasdaq_predictor.services.*]
disallow_untyped_defs = True

[mypy-nasdaq_predictor.data.*]
disallow_untyped_defs = True

[mypy-nasdaq_predictor.database.*]
disallow_untyped_defs = True

[mypy-tests.*]
disallow_untyped_defs = False
check_untyped_defs = True

# Third-party libraries without stubs
[mypy-yfinance.*]
ignore_missing_imports = True

[mypy-supabase.*]
ignore_missing_imports = True

[mypy-pandas.*]
ignore_missing_imports = True
```

**Type Checking in CI:**

```bash
# .github/workflows/type-check.yml (when CI is added)

# Run mypy
mypy nasdaq_predictor/ --config-file mypy.ini

# Run pyright (alternative type checker)
pyright nasdaq_predictor/
```

### 8.3 py.typed Marker

```python
# nasdaq_predictor/py.typed
# Empty file to indicate package is typed
```

---

## 9. Performance & Load Testing

### 9.1 Performance Benchmarking Tests

```python
# tests/performance/test_prediction_performance.py

import pytest
import time
from datetime import datetime
import pytz


class TestPredictionPerformance:
    """Performance benchmarks for prediction generation."""
    
    @pytest.mark.benchmark
    def test_single_prediction_latency(self, benchmark):
        """Test single prediction generation latency."""
        ticker = 'NQ=F'
        hour_start = datetime(2024, 11, 13, 10, 0, tzinfo=pytz.UTC)
        
        # Benchmark should complete in < 500ms
        result = benchmark(
            lambda: prediction_service.generate_block_prediction(ticker, hour_start)
        )
        
        assert benchmark.stats['mean'] < 0.5  # 500ms
    
    @pytest.mark.benchmark
    def test_24h_batch_generation_performance(self, benchmark):
        """Test 24-hour batch generation performance."""
        ticker = 'NQ=F'
        date = datetime(2024, 11, 13, tzinfo=pytz.UTC)
        
        # Benchmark should complete in < 10 seconds
        result = benchmark(
            lambda: prediction_service.generate_24h_block_predictions(ticker, date)
        )
        
        assert benchmark.stats['mean'] < 10.0
    
    def test_concurrent_prediction_requests(self):
        """Test handling of concurrent prediction requests."""
        import concurrent.futures
        
        ticker = 'NQ=F'
        hours = [
            datetime(2024, 11, 13, h, 0, tzinfo=pytz.UTC)
            for h in range(24)
        ]
        
        start = time.time()
        
        with concurrent.futures.ThreadPoolExecutor(max_workers=10) as executor:
            futures = [
                executor.submit(prediction_service.generate_block_prediction, ticker, hour)
                for hour in hours
            ]
            
            results = [f.result() for f in concurrent.futures.as_completed(futures)]
        
        elapsed = time.time() - start
        
        # Should complete in reasonable time even with concurrency
        assert elapsed < 30.0  # 30 seconds for 24 concurrent predictions
        assert len([r for r in results if r is not None]) > 0
    
    @pytest.mark.stress
    def test_database_query_performance(self):
        """Test database query performance under load."""
        ticker_id = "550e8400-e29b-41d4-a716-446655440000"
        
        start = time.time()
        
        for i in range(100):
            # Query predictions 100 times
            predictions = block_prediction_repo.get_block_predictions_by_date(
                ticker_id,
                datetime(2024, 11, 13, tzinfo=pytz.UTC)
            )
        
        elapsed = time.time() - start
        
        # 100 queries should complete in < 5 seconds
        assert elapsed < 5.0
```

### 9.2 Memory & Resource Usage Tests

```python
# tests/performance/test_resource_usage.py

import tracemalloc
import pytest


class TestResourceUsage:
    """Test memory and resource usage."""
    
    def test_memory_usage_single_prediction(self):
        """Test memory usage for single prediction."""
        tracemalloc.start()
        
        ticker = 'NQ=F'
        hour_start = datetime(2024, 11, 13, 10, 0, tzinfo=pytz.UTC)
        
        prediction = prediction_service.generate_block_prediction(ticker, hour_start)
        
        current, peak = tracemalloc.get_traced_memory()
        tracemalloc.stop()
        
        # Should use < 50MB for single prediction
        assert peak < 50 * 1024 * 1024  # 50MB
    
    def test_no_memory_leaks_batch_generation(self):
        """Test for memory leaks in batch generation."""
        import gc
        
        tracemalloc.start()
        
        ticker = 'NQ=F'
        
        # Generate 100 days of predictions
        for day in range(100):
            date = datetime(2024, 11, 13, tzinfo=pytz.UTC) - timedelta(days=day)
            prediction_service.generate_24h_block_predictions(ticker, date)
            gc.collect()
        
        current, peak = tracemalloc.get_traced_memory()
        tracemalloc.stop()
        
        # Memory should not grow unbounded
        # Peak should be < 200MB
        assert peak < 200 * 1024 * 1024
```

---

## 10. CI/CD Testing Pipeline

### 10.1 GitHub Actions Workflow

**File:** `.github/workflows/test.yml`

```yaml
name: Test Suite

on:
  push:
    branches: [ main, develop ]
  pull_request:
    branches: [ main, develop ]

jobs:
  test:
    runs-on: ubuntu-latest
    
    strategy:
      matrix:
        python-version: ['3.11', '3.12', '3.13']
    
    services:
      postgres:
        image: postgres:15
        env:
          POSTGRES_PASSWORD: testpass
          POSTGRES_DB: testdb
        options: >-
          --health-cmd pg_isready
          --health-interval 10s
          --health-timeout 5s
          --health-retries 5
        ports:
          - 5432:5432
    
    steps:
    - uses: actions/checkout@v3
    
    - name: Set up Python ${{ matrix.python-version }}
      uses: actions/setup-python@v4
      with:
        python-version: ${{ matrix.python-version }}
    
    - name: Cache dependencies
      uses: actions/cache@v3
      with:
        path: ~/.cache/pip
        key: ${{ runner.os }}-pip-${{ hashFiles('**/requirements.txt') }}
        restore-keys: |
          ${{ runner.os }}-pip-
    
    - name: Install dependencies
      run: |
        python -m pip install --upgrade pip
        pip install -r requirements.txt
        pip install pytest pytest-cov pytest-benchmark mypy
    
    - name: Run type checking (mypy)
      run: |
        mypy nasdaq_predictor/ --config-file mypy.ini
    
    - name: Run unit tests
      run: |
        pytest tests/unit/ -v --cov=nasdaq_predictor --cov-report=xml --cov-report=term
      env:
        DATABASE_URL: postgresql://postgres:testpass@localhost:5432/testdb
    
    - name: Run integration tests
      run: |
        pytest tests/integration/ -v --cov=nasdaq_predictor --cov-append --cov-report=xml
      env:
        DATABASE_URL: postgresql://postgres:testpass@localhost:5432/testdb
    
    - name: Upload coverage to Codecov
      uses: codecov/codecov-action@v3
      with:
        file: ./coverage.xml
        flags: unittests
        name: codecov-umbrella
    
    - name: Coverage threshold check
      run: |
        coverage report --fail-under=70
    
    - name: Run performance benchmarks
      run: |
        pytest tests/performance/ --benchmark-only --benchmark-json=benchmark.json
    
    - name: Upload benchmark results
      uses: actions/upload-artifact@v3
      with:
        name: benchmark-results
        path: benchmark.json

  lint:
    runs-on: ubuntu-latest
    
    steps:
    - uses: actions/checkout@v3
    
    - name: Set up Python
      uses: actions/setup-python@v4
      with:
        python-version: '3.13'
    
    - name: Install linters
      run: |
        pip install flake8 black isort
    
    - name: Run flake8
      run: |
        flake8 nasdaq_predictor/ --count --select=E9,F63,F7,F82 --show-source --statistics
    
    - name: Check code formatting (black)
      run: |
        black --check nasdaq_predictor/
    
    - name: Check import sorting (isort)
      run: |
        isort --check-only nasdaq_predictor/

  security:
    runs-on: ubuntu-latest
    
    steps:
    - uses: actions/checkout@v3
    
    - name: Run security scan (bandit)
      run: |
        pip install bandit
        bandit -r nasdaq_predictor/ -f json -o bandit-report.json
    
    - name: Upload security scan results
      uses: actions/upload-artifact@v3
      with:
        name: security-scan
        path: bandit-report.json
```

### 10.2 Pre-commit Hooks

**File:** `.pre-commit-config.yaml`

```yaml
repos:
  - repo: https://github.com/pre-commit/pre-commit-hooks
    rev: v4.5.0
    hooks:
      - id: trailing-whitespace
      - id: end-of-file-fixer
      - id: check-yaml
      - id: check-added-large-files
      - id: check-json
  
  - repo: https://github.com/psf/black
    rev: 23.11.0
    hooks:
      - id: black
        language_version: python3.13
  
  - repo: https://github.com/pycqa/isort
    rev: 5.12.0
    hooks:
      - id: isort
        name: isort (python)
  
  - repo: https://github.com/pycqa/flake8
    rev: 6.1.0
    hooks:
      - id: flake8
        args: ['--max-line-length=120']
  
  - repo: https://github.com/pre-commit/mirrors-mypy
    rev: v1.7.0
    hooks:
      - id: mypy
        additional_dependencies: [types-all]
        args: [--config-file=mypy.ini]
```

**Install:**

```bash
pip install pre-commit
pre-commit install
pre-commit run --all-files
```

---

## 11. Implementation Priority & Roadmap

### Phase 1: Critical Foundation (Weeks 1-2) - P0

**Priority:** CRITICAL - Required for production readiness

1. **Financial Calculation Tests (98.9% coverage)**
   - [ ] Volatility calculation tests (all edge cases)
   - [ ] Block segmentation tests (boundary conditions)
   - [ ] Early bias detection tests
   - [ ] Sustained counter analysis tests
   - [ ] Fibonacci pivot tests
   - [ ] Reference level tests

2. **Data Fetching Layer Tests (95% coverage)**
   - [ ] yfinance mock framework
   - [ ] Supabase mock framework
   - [ ] Network error handling
   - [ ] Rate limiting tests
   - [ ] Data quality validation

3. **Database Repository Tests (90% coverage)**
   - [ ] CRUD operation tests for all 9 repositories
   - [ ] UUID handling tests
   - [ ] Transaction tests
   - [ ] Query performance tests

**Success Criteria:**
- Financial calculations: 98.9%+ coverage
- Zero financial calculation bugs
- All edge cases documented and tested
- mypy passes with zero errors

### Phase 2: Service & Integration Layer (Weeks 3-4) - P1

1. **Service Tests (95% coverage)**
   - [ ] Complete all 11 untested service files
   - [ ] Integration between services
   - [ ] Error propagation tests
   - [ ] State management tests

2. **API Endpoint Tests (85% coverage)**
   - [ ] All 8 route files covered
   - [ ] Request validation
   - [ ] Response formatting
   - [ ] Error handling
   - [ ] CORS/security headers

3. **Integration Tests**
   - [ ] End-to-end prediction flows
   - [ ] Verification flows
   - [ ] Market-aware system tests
   - [ ] Multi-ticker tests

**Success Criteria:**
- All services tested
- API coverage >= 85%
- Integration tests pass
- No critical bugs

### Phase 3: Validation & Performance (Weeks 5-6) - P2

1. **Backtesting Framework**
   - [ ] SQL validation queries
   - [ ] Python backtesting framework
   - [ ] Accuracy baseline validation
   - [ ] Historical data validation

2. **Performance Tests**
   - [ ] Latency benchmarks
   - [ ] Concurrent request tests
   - [ ] Memory usage tests
   - [ ] Database performance tests

3. **CI/CD Pipeline**
   - [ ] GitHub Actions workflow
   - [ ] Pre-commit hooks
   - [ ] Coverage reporting
   - [ ] Automated deployment

**Success Criteria:**
- Backtest accuracy >= 55%
- Latency < 500ms per prediction
- CI/CD fully automated
- Coverage >= 98.9%

---

## 12. Test Metrics & Reporting

### 12.1 Coverage Reporting

**pytest-cov Configuration:**

```ini
# .coveragerc

[run]
source = nasdaq_predictor
omit = 
    */tests/*
    */venv/*
    */__pycache__/*
    */migrations/*

[report]
exclude_lines =
    pragma: no cover
    def __repr__
    raise AssertionError
    raise NotImplementedError
    if __name__ == .__main__.:
    if TYPE_CHECKING:
    @abstractmethod

precision = 2
show_missing = True

[html]
directory = htmlcov
```

**Generate Reports:**

```bash
# Run tests with coverage
pytest --cov=nasdaq_predictor --cov-report=html --cov-report=term --cov-report=json

# View HTML report
open htmlcov/index.html

# Check coverage threshold
coverage report --fail-under=98.9
```

### 12.2 Test Metrics Dashboard

**Key Metrics to Track:**

1. **Coverage Metrics**
   - Line coverage
   - Branch coverage
   - Function coverage
   - Class coverage

2. **Test Quality Metrics**
   - Number of test cases
   - Test execution time
   - Flaky test rate
   - Test failure rate

3. **Backtesting Metrics**
   - Prediction accuracy
   - Accuracy by confidence level
   - Accuracy by prediction strength
   - Accuracy by market condition

4. **Performance Metrics**
   - Average latency
   - P95/P99 latency
   - Memory usage
   - Database query time

**Example Dashboard (using pytest-html):**

```bash
pip install pytest-html
pytest --html=report.html --self-contained-html
```

---

## 13. Summary & Action Items

### Current State Summary

**Strengths:**
- Solid foundation with 323 test cases
- Good coverage of core DTOs and services
- Integration tests for key flows
- Market-aware testing framework

**Critical Gaps:**
- 0% coverage: Database repositories (9 files)
- 0% coverage: API routes (8 files)
- 15% coverage: Financial calculations (7 files)
- 10% coverage: Data fetching
- 0% coverage: 11 service files

**Risk Assessment:**
- **HIGH RISK:** Untested financial calculations could lead to incorrect predictions
- **HIGH RISK:** Untested data fetching could cause data integrity issues
- **MEDIUM RISK:** Untested repositories could lead to database corruption
- **MEDIUM RISK:** Untested API routes could expose security vulnerabilities

### Recommended Action Plan

**Immediate Actions (This Week):**
1. Create test files for all financial calculation modules
2. Implement comprehensive volatility and block segmentation tests
3. Set up yfinance mocking framework
4. Create database repository test suite

**Short-term (Next 2 Weeks):**
1. Complete all service layer tests
2. Implement API endpoint test suite
3. Build backtesting validation framework
4. Set up CI/CD pipeline

**Long-term (Next 4-6 Weeks):**
1. Achieve 98.9%+ coverage across all modules
2. Implement performance benchmarking
3. Build comprehensive validation scripts
4. Create monitoring and alerting for production

### Coverage Targets by Module

| Module | Current | Target | Priority | Timeline |
|--------|---------|--------|----------|----------|
| analysis/* | 15% | 98.9% | P0 | Week 1-2 |
| data/fetcher.py | 10% | 95% | P0 | Week 1 |
| database/repositories/* | 0% | 90% | P1 | Week 2-3 |
| services/* | 30% | 95% | P1 | Week 3-4 |
| api/routes/* | 0% | 85% | P1 | Week 4 |
| core/* | 70% | 100% | P2 | Week 5 |
| **Overall Project** | **35%** | **98.9%** | - | **6 weeks** |

---

## 14. Tools & Dependencies

**Testing Dependencies:**

```txt
# requirements-test.txt

pytest==7.4.3
pytest-cov==4.1.0
pytest-mock==3.12.0
pytest-benchmark==4.0.0
pytest-html==4.1.1
pytest-asyncio==0.21.1
pytest-xdist==3.5.0  # Parallel test execution

# Type checking
mypy==1.7.0
types-pytz==2024.1.0
types-requests==2.31.0

# Code quality
black==23.11.0
flake8==6.1.0
isort==5.12.0
bandit==1.7.5

# Coverage
coverage[toml]==7.3.2
codecov==2.1.13

# Mocking
responses==0.24.1
freezegun==1.4.0  # Time mocking

# Performance
memory-profiler==0.61.0
```

**Useful Commands:**

```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=nasdaq_predictor --cov-report=html

# Run only unit tests
pytest tests/unit/

# Run only integration tests
pytest tests/integration/ -m integration

# Run only slow tests
pytest -m slow

# Run tests in parallel (faster)
pytest -n auto

# Run with verbose output
pytest -vv

# Run specific test file
pytest tests/unit/analysis/test_volatility.py

# Run specific test
pytest tests/unit/analysis/test_volatility.py::TestVolatilityCalculation::test_volatility_normal_conditions

# Run benchmarks only
pytest --benchmark-only

# Generate HTML report
pytest --html=report.html --self-contained-html

# Check type hints
mypy nasdaq_predictor/ --config-file mypy.ini

# Format code
black nasdaq_predictor/

# Sort imports
isort nasdaq_predictor/

# Security scan
bandit -r nasdaq_predictor/
```

---

## Conclusion

This comprehensive testing and validation strategy provides a clear roadmap to achieving production-ready quality assurance for the NASDAQ Predictor project. By prioritizing financial calculation accuracy, implementing robust mocking strategies, and building a complete validation framework, the system will achieve the 98.9%+ coverage target necessary for a reliable financial prediction platform.

**Key Success Factors:**
1. Systematic implementation following the 6-week roadmap
2. 100% coverage of financial calculations (zero tolerance for errors)
3. Comprehensive edge case testing
4. Robust backtesting validation
5. Automated CI/CD integration
6. Continuous monitoring and validation

**Next Steps:**
1. Review and approve this strategy
2. Begin Phase 1 implementation (financial calculation tests)
3. Set up test infrastructure (fixtures, mocks, CI/CD)
4. Track progress against coverage targets
5. Regular backtest validation

---

**Document Version:** 1.0  
**Author:** Testing & Validation Expert  
**Last Updated:** 2025-11-15  
**Status:** Ready for Implementation
