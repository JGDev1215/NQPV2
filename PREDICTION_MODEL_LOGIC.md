# OpenPredict: Prediction Model Logic

## Table of Contents
1. [Overview](#overview)
2. [The 7-Block Framework](#the-7-block-framework)
3. [Core Concepts](#core-concepts)
4. [Step-by-Step Prediction Process](#step-by-step-prediction-process)
5. [Decision Trees](#decision-trees)
6. [Configuration Parameters](#configuration-parameters)
7. [Examples](#examples)
8. [Technical Details](#technical-details)

---

## Overview

OpenPredict uses a **7-block time division framework** to predict price movement direction (UP, DOWN, or NEUTRAL) at the **5/7 point** of a trading period, before the final 2/7 completes.

### Key Principles

- **Early Bias Detection**: Captures initial directional momentum from blocks 1-2
- **Mid-Period Reversal Detection**: Identifies sustained counter-moves in blocks 3-5
- **Early Prediction**: Locks in predictions at 71.4% through the period
- **Normalized Analysis**: All price movements measured in standard deviations (volatility-adjusted)

### Supported Timeframes

- **1-hour (1h)**: 60 minutes → prediction locked at ~42.9 minutes
- **2-hour (2h)**: 120 minutes → prediction locked at ~85.7 minutes
- **4-hour (4h)**: 240 minutes → prediction locked at ~171.4 minutes
- **Custom (10AM-12PM ET)**: 120 minutes trading hours only

---

## The 7-Block Framework

### Period Division

Each trading period is divided into **7 equal time blocks**:

```
Period Timeline (Example: 2-hour = 120 minutes):

├─ Block 1: 0-17.1m       (14.3% of period)
├─ Block 2: 17.1-34.3m    (14.3% of period)
├─ Block 3: 34.3-51.4m    (14.3% of period)
├─ Block 4: 51.4-68.6m    (14.3% of period)
├─ Block 5: 68.6-85.7m    (14.3% of period)
│ ↑ PREDICTION LOCKED HERE AT 5/7 POINT (71.4%)
├─ Block 6: 85.7-102.9m   (14.3% of period) ← Unknown
└─ Block 7: 102.9-120m    (14.3% of period) ← Unknown
```

### Block Analysis Zones

| Blocks | Name | Purpose | Analysis |
|--------|------|---------|----------|
| 1-2 | **Early Zone** | Detect initial bias | First 28.6% of period |
| 3-5 | **Mid-Pivot Zone** | Detect reversals | Blocks 34.3% to 71.4% |
| 6-7 | **Unknown Zone** | Not analyzed | After prediction point |

---

## Core Concepts

### 1. Volatility (Standard Deviation)

**Purpose**: Normalize price movements across different market conditions

**Calculation**:
```python
closes = [bar.close for bar in bars]
returns = (closes[i] - closes[i-1]) / closes[i-1]
volatility = std_dev(returns) × mean(closes)

# Fallback if no volatility
if volatility == 0:
    volatility = open_price × 0.01  # 1% of opening price
```

**Example**:
```
Opening Price: 5000
Returns std dev: 0.5%
Volatility = 0.005 × 5000 = 25 points

This means:
- 1 standard deviation = 25 points movement
- 2 standard deviations = 50 points movement
```

**Usage**: All price deviations are measured as: `deviation = (price - open) / volatility`

---

### 2. Block Analysis

For each block (1-5), four metrics are calculated:

**a) Price at Block End**
```python
price_at_end = last_close_in_block
```

**b) Deviation from Open** (in standard deviations)
```python
deviation = (price_at_end - open_price) / volatility

# Interpretation:
# deviation < -0.5  → Below open (negative bias)
# -0.5 to +0.5      → Near open (neutral zone)
# deviation > +0.5  → Above open (positive bias)
```

**c) Open Crossing**
```python
crosses_open = (block_low <= open_price <= block_high)

# True if price moved through the opening level
# Indicates contested equilibrium
```

**d) Time Above/Below Open**
```python
time_above = bars_above_open / total_bars_in_block
time_below = bars_below_open / total_bars_in_block

# Range: 0.0 to 1.0 (0% to 100% of block time)
# Example: 0.6 = 60% of block time spent above open
```

### 3. Prediction Directions

```python
enum PredictionDirection:
    UP      = "up"      # Price expected to rise
    DOWN    = "down"    # Price expected to fall
    NEUTRAL = "neutral" # No clear direction
```

### 4. Strength Levels

```python
"weak"      # Small deviation (< 1.0 std dev)
"moderate"  # Medium deviation (1.0-2.0 std devs)
"strong"    # Large deviation (> 2.0 std devs)
```

---

## Step-by-Step Prediction Process

### Step 1: Data Collection (analyze_period)

```python
period_end = period_start + 120 minutes  # For 2h timeframe
prediction_point = period_start + 85.7 minutes  # 5/7 point

# Collect all bars from period start until 5/7 point
analysis_bars = [bar for bar in bars if bar.timestamp < prediction_point]
```

**Example**:
```
Period: 2024-11-13 10:00 to 12:00
Prediction Point: 2024-11-13 11:25:42 (5/7 = 85.7 minutes)
Analysis Bars: All bars from 10:00 to 11:25:42
```

---

### Step 2: Calculate Volatility

```python
volatility = calculate_volatility(analysis_bars)

# Using close-to-close returns
# This normalizes the analysis to current market conditions
```

**Impact**: Higher volatility → larger required deviations for significance

---

### Step 3: Analyze Blocks 1-5

```python
for block in 1 to 5:
    block_bars = bars[block_start:block_end]

    # Calculate 4 metrics
    price_at_end = block_bars[-1].close
    deviation = (price_at_end - open_price) / volatility
    crosses_open = (min(block) <= open <= max(block))
    time_above = count(close > open) / len(block_bars)
    time_below = 1.0 - time_above
```

**Data Structure**:
```python
BlockAnalysis(
    block_number: int,           # 1-7
    price_at_end: float,         # Close price at block end
    deviation_from_open: float,  # In standard deviations
    crosses_open: bool,          # Did it cross opening level?
    time_above_open: float,      # Fraction above open
    time_below_open: float       # Fraction below open
)
```

---

### Step 4: Determine Early Bias (Blocks 1-2)

**Purpose**: Identify initial directional momentum

**Algorithm**:

```
INPUT: Block 1, Block 2, open_price, volatility

1. Get price at end of Block 2
   deviation_block_2 = (price_end_2 - open_price) / volatility

2. Check if price returned to open
   returned_to_open = Block1.crosses_open OR Block2.crosses_open

3. Classify bias:
```

**Decision Tree**:

```
START: deviation_block_2
│
├─ |deviation| < 0.5
│  └─ NEUTRAL, strength = |deviation|
│
├─ deviation > 0 AND NOT returned_to_open
│  └─ UP, strength = deviation
│
├─ deviation > 0 AND returned_to_open
│  └─ UP, strength = deviation × 0.5  (Reduced - price tested open)
│
├─ deviation < 0 AND NOT returned_to_open
│  └─ DOWN, strength = |deviation|
│
└─ deviation < 0 AND returned_to_open
   └─ DOWN, strength = |deviation| × 0.5
```

**Interpretation**:

| Deviation | Crosses Open | Result | Strength Multiplier |
|-----------|---|--------|---|
| +1.5 | No | UP | 1.0x |
| +1.5 | Yes | UP | 0.5x |
| -1.5 | No | DOWN | 1.0x |
| -1.5 | Yes | DOWN | 0.5x |
| ±0.3 | Any | NEUTRAL | 0.3x |

**Why Reduce Strength When Price Crosses Open?**
- Indicates the move was not conviction-driven
- Price was tested and rejected multiple times
- Suggests weak momentum despite directional bias

---

### Step 5: Check for Sustained Counter-Moves (Blocks 3-5)

**Purpose**: Detect mid-period reversals (potential trend changes)

**Algorithm**:

```
INPUT: Block3, Block4, Block5, open_price, early_bias

For EACH mid-pivot block:

  If early_bias == UP:
    IF (block.price_at_end < open_price) AND
       (block.time_below_open >= 0.5):
      ✓ Sustained counter DOWN detected
      Return (True, DOWN)

  If early_bias == DOWN:
    IF (block.price_at_end > open_price) AND
       (block.time_above_open >= 0.5):
      ✓ Sustained counter UP detected
      Return (True, UP)

If no counter in any mid-pivot block:
  Return (False, None)
```

**Thresholds**:
- `0.5`: Time threshold = 50% of block must be on opposite side of open
- Checks BOTH price level (at end) AND time allocation (during block)

**Example Scenarios**:

```
Scenario 1: UP early bias + sustained DOWN counter
- Block 3: price_at_end = 4990 (BELOW open)
           time_below_open = 0.65 (65%) ✓
→ Counter detected! Predict DOWN

Scenario 2: UP early bias but no sustained counter
- Block 3: price_at_end = 4998 (below), time_below = 0.45 (45%)
- Block 4: price_at_end = 5001 (above), time_above = 0.55 (55%)
- Block 5: price_at_end = 5008 (above), time_above = 0.70 (70%)
→ No sustained counter, continue with UP
```

---

### Step 6: Get Deviation at 5/7 Point

```python
price_at_5_7 = blocks[-1].price_at_end  # Last bar of Block 5
deviation_at_5_7 = (price_at_5_7 - open_price) / volatility
```

This confirms the current position relative to opening price.

---

### Step 7: Generate Final Prediction

**Purpose**: Combine all signals into a single actionable prediction

**Input Variables**:
- `early_bias`: UP, DOWN, or NEUTRAL (from Step 4)
- `early_bias_strength`: Magnitude (in std devs)
- `has_sustained_counter`: True or False (from Step 5)
- `counter_direction`: UP or DOWN (if counter exists)
- `deviation_at_5_7`: Current deviation (in std devs)

---

## Decision Trees

### Decision Tree 1: Reversal Detected (`has_sustained_counter == True`)

```
┌─ has_sustained_counter == True?
│
└─ YES
   ├─ Is price near open at 5/7?
   │  ├─ |deviation_at_5_7| < 0.5
   │  │  └─ NEUTRAL, "weak"
   │  │     (Reversal underway but not decisive)
   │  │
   │  └─ |deviation_at_5_7| >= 0.5
   │     ├─ |deviation_at_5_7| < 2.0
   │     │  └─ counter_direction, "moderate"
   │     │
   │     └─ |deviation_at_5_7| >= 2.0
   │        └─ counter_direction, "strong"
```

**Example**:
```
early_bias = UP
sustained_counter = DOWN detected in block 3
deviation_at_5_7 = +0.2 (still slightly above open)
→ NEUTRAL, "weak" (counter detected but not decisive yet)

early_bias = UP
sustained_counter = DOWN detected in block 3
deviation_at_5_7 = -1.5 (moved below open)
→ DOWN, "moderate" (reversal confirmed)
```

---

### Decision Tree 2: No Sustained Counter, Early Bias = NEUTRAL

```
┌─ early_bias == NEUTRAL?
│
└─ YES
   ├─ Is price still near open at 5/7?
   │  ├─ |deviation_at_5_7| < 0.5
   │  │  └─ NEUTRAL, "weak"
   │  │     (No bias developed)
   │  │
   │  └─ |deviation_at_5_7| >= 0.5
   │     └─ Developed bias by 5/7
   │        ├─ deviation_at_5_7 > 0 → UP
   │        └─ deviation_at_5_7 < 0 → DOWN
   │           ├─ |deviation_at_5_7| < 2.0
   │           │  └─ developed_direction, "moderate"
   │           │
   │           └─ |deviation_at_5_7| >= 2.0
   │              └─ developed_direction, "strong"
```

**Example**:
```
early_bias = NEUTRAL (blocks 1-2 inconclusive)
deviation_at_5_7 = -1.8 (clear move down by block 5)
→ DOWN, "moderate" (bias developed mid-period)

early_bias = NEUTRAL
deviation_at_5_7 = +0.3 (still near open)
→ NEUTRAL, "weak" (no direction emerged)
```

---

### Decision Tree 3: Continuation (Early Bias ≠ NEUTRAL, No Counter)

```
┌─ early_bias == UP or DOWN?
│
└─ YES (has early bias)
   └─ No sustained counter detected
      ├─ Is deviation at 5/7 strong?
      │  ├─ |deviation_at_5_7| >= 2.0
      │  │  └─ early_bias, "strong"
      │  │     (Momentum building)
      │  │
      │  └─ |deviation_at_5_7| < 2.0
      │     ├─ early_bias_strength >= 1.0
      │     │  └─ early_bias, "moderate"
      │     │     (Momentum holding)
      │     │
      │     └─ early_bias_strength < 1.0
      │        └─ early_bias, "weak"
      │           (Weak early momentum)
```

**Example**:
```
early_bias = UP, strength = 1.2
has_sustained_counter = False
deviation_at_5_7 = +2.5
→ UP, "strong" (momentum accelerating)

early_bias = UP, strength = 0.8
has_sustained_counter = False
deviation_at_5_7 = +0.7
→ UP, "weak" (early momentum fading)
```

---

## Configuration Parameters

### From `config/settings.py`

```python
# Block Structure
BLOCK_DIVISIONS = 7                    # Always 7 blocks
PREDICTION_POINT = 5 / 7              # 5/7 = 0.714... = 71.4%

# Deviation Thresholds
DEVIATION_THRESHOLD = 2.0              # 2.0 standard deviations
SUSTAINED_COUNTER_THRESHOLD = 0.5      # 50% of block time

# Timeframes (in minutes)
TIMEFRAMES = {
    "2h": 120,
    "4h": 240,
    "custom_10am_12pm": 120           # Special trading hours slot
}

# Data Aggregation
TIMEZONE = "US/Eastern"               # ET for market hours
MIN_DATA_COMPLETENESS = 0.05          # 5% threshold for backtesting
```

### Threshold Interpretation

**DEVIATION_THRESHOLD = 2.0**
- Separates "moderate" from "strong" predictions
- 2.0 std devs in volatility-adjusted terms

**SUSTAINED_COUNTER_THRESHOLD = 0.5**
- Requires 50% of block time on opposite side of open
- Prevents false signals from brief touches
- Creates convincing reversal evidence

---

## Examples

### Example 1: UP Continuation (Strong)

**Market Data** (ES Futures, 2h period 10:00-12:00):
```
Opening Price: 5000
Volatility: 25 points (1 std dev = 25 points)

Block 1 (0-17m):   Close 5015, Time above open: 85%
Block 2 (17-34m):  Close 5028, Time above open: 95%
Block 3 (34-51m):  Close 5032, Time above open: 90%
Block 4 (51-69m):  Close 5030, Time above open: 85%
Block 5 (69-86m):  Close 5035, Time above open: 88%
```

**Analysis**:

**Step 1**: Volatility = 25 points

**Step 2**: Block Analysis
| Block | Close | Deviation | Crosses Open | Time Above |
|-------|-------|-----------|---|---|
| 1 | 5015 | +0.60 | No | 85% |
| 2 | 5028 | +1.12 | No | 95% |
| 3 | 5032 | +1.28 | No | 90% |
| 4 | 5030 | +1.20 | No | 85% |
| 5 | 5035 | +1.40 | No | 88% |

**Step 3**: Early Bias (Blocks 1-2)
```
deviation_block_2 = +1.12 std dev
returned_to_open = False (no crosses)
→ Early Bias: UP, strength = 1.12
```

**Step 4**: Sustained Counter Check (Blocks 3-5)
```
Block 3: price = 5032 (above), time_above = 90%
Block 4: price = 5030 (above), time_above = 85%
Block 5: price = 5035 (above), time_above = 88%
→ No counter detected (all above open)
```

**Step 5**: Deviation at 5/7
```
deviation_at_5_7 = +1.40 std dev
```

**Step 6**: Generate Prediction
```
early_bias = UP, strength = 1.12
sustained_counter = False
deviation_at_5_7 = +1.40

Path: Continuation (early_bias ≠ NEUTRAL, no counter)
- |deviation_at_5_7| = 1.40 < 2.0 ✓
- early_bias_strength = 1.12 >= 1.0 ✓
→ Prediction: UP, "moderate"

Confidence: Momentum sustained through block 5
```

---

### Example 2: UP Early Bias with DOWN Reversal

**Market Data** (Same 2h period):
```
Block 1 (0-17m):   Close 5015, Time above open: 85%
Block 2 (17-34m):  Close 5028, Time above open: 95%
Block 3 (34-51m):  Close 5012, Time below open: 65% ← Counter!
Block 4 (51-69m):  Close 4995, Time below open: 70% ← Counter continues
Block 5 (69-86m):  Close 5001, Time above open: 60%
```

**Analysis**:

**Early Bias** (Blocks 1-2): UP, strength = 1.12 ✓

**Sustained Counter Check** (Blocks 3-5):
```
Block 3: price = 5012 (below), time_below = 65% (>50%) ✓
→ Sustained counter DOWN detected!
```

**Deviation at 5/7**:
```
deviation_at_5_7 = (5001 - 5000) / 25 = +0.04 std dev
```

**Generate Prediction**:
```
has_sustained_counter = True
counter_direction = DOWN
deviation_at_5_7 = +0.04

Path: Reversal detected
- |deviation_at_5_7| = 0.04 < 0.5 ✓
→ Prediction: NEUTRAL, "weak"

Interpretation: Counter-move detected, but price hasn't moved below
open yet at prediction point. Reversal underway but not confirmed.
```

---

### Example 3: Neutral Early, Develops UP Bias

**Market Data**:
```
Block 1 (0-17m):   Close 5002, Time above: 55%, Crosses open: Yes
Block 2 (17-34m):  Close 4998, Time above: 45%, Crosses open: Yes
Block 3 (34-51m):  Close 5010, Time above: 70%
Block 4 (51-69m):  Close 5020, Time above: 85%
Block 5 (69-86m):  Close 5025, Time above: 90%
```

**Analysis**:

**Early Bias** (Blocks 1-2):
```
deviation_block_2 = (4998 - 5000) / 25 = -0.08 std dev
|deviation| = 0.08 < 0.5
→ Early Bias: NEUTRAL, strength = 0.08
```

**Sustained Counter Check**: N/A (no early bias)

**Deviation at 5/7**:
```
deviation_at_5_7 = (5025 - 5000) / 25 = +1.0 std dev
```

**Generate Prediction**:
```
early_bias = NEUTRAL
deviation_at_5_7 = +1.0

Path: Neutral early, develops bias by 5/7
- |deviation_at_5_7| = 1.0 >= 0.5 ✓
- Developed bias: deviation > 0 → UP
- |1.0| = 1.0 < 2.0 → "moderate"
→ Prediction: UP, "moderate"

Interpretation: First half inconclusive, but clear upside developed
by 5/7 point. Trend beginning mid-period.
```

---

## Technical Details

### Data Structures

```python
class BlockAnalysis(BaseModel):
    block_number: int                    # 1-7
    start_time: datetime                 # Block start timestamp
    end_time: datetime                   # Block end timestamp
    price_at_end: float                  # Closing price of block
    deviation_from_open: float           # (close - open) / volatility
    crosses_open: bool                   # Did high/low cross open?
    time_above_open: float               # Fraction [0, 1]
    time_below_open: float               # Fraction [0, 1]


class PredictionAnalysis(BaseModel):
    symbol: str                          # Asset symbol (e.g., "ES=F")
    timeframe_minutes: int               # 120, 240, etc.
    period_start: datetime               # Period start time
    period_end: datetime                 # Period end time
    open_price: float                    # Opening price (equilibrium)
    price_at_5_7: float                  # Price at prediction point

    # Early bias analysis
    early_bias: PredictionDirection      # UP, DOWN, NEUTRAL
    early_bias_strength: float           # Magnitude (std devs)

    # Counter-move analysis
    has_sustained_counter: bool          # True if reversal signal found
    counter_direction: Optional[PredictionDirection]

    # Final deviation
    deviation_at_5_7: float              # Current position (std devs)

    # Prediction
    prediction: PredictionDirection      # UP, DOWN, NEUTRAL
    prediction_strength: str             # "weak", "moderate", "strong"
    prediction_locked_at: datetime       # Timestamp of 5/7 point

    blocks: List[BlockAnalysis]          # All 5 blocks analyzed
```

### Time-Based Calculations

**Block Duration Formula**:
```python
block_duration = timeframe_minutes / 7
```

Examples:
```
1h timeframe:   60 / 7 = 8.57 minutes per block
2h timeframe:   120 / 7 = 17.14 minutes per block
4h timeframe:   240 / 7 = 34.29 minutes per block
```

**Prediction Point Formula**:
```python
prediction_point_minutes = timeframe_minutes * (5/7)
```

Examples:
```
1h timeframe:   60 * 5/7 = 42.86 minutes (~42m 51s)
2h timeframe:   120 * 5/7 = 85.71 minutes (~85m 43s)
4h timeframe:   240 * 5/7 = 171.43 minutes (~171m 26s)
```

### Bar Aggregation Within Blocks

For each block, OHLC data is aggregated:

```python
block_bars = [b for b in all_bars
              if block_start <= b.timestamp < block_end]

block_aggregation = {
    "open_price": block_bars[0].open,
    "high": max(b.high for b in block_bars),
    "low": min(b.low for b in block_bars),
    "close_price": block_bars[-1].close,
    "volume": sum(b.volume for b in block_bars)
}
```

---

## Backtesting Integration

The prediction model integrates with the backtester as follows:

```python
# 1. Backtester generates periods
periods = backtester._generate_test_periods(...)

# 2. For each period, collect OHLC bars
bars = supabase.fetch_aggregated_bars(
    symbol=symbol,
    start_time=period_start,
    end_time=period_end,
    bar_size_minutes=aggregation_minutes
)

# 3. Run prediction analysis at 5/7 point
analysis = prediction_engine.analyze_period(
    bars=bars,
    period_start=period_start,
    timeframe_minutes=timeframe_minutes
)

# 4. Wait for period completion (get actual result)
actual_bars = [b for b in bars if period_start <= b < period_end]
actual_direction = aggregator.aggregate_bars(...).get_direction()

# 5. Compare prediction vs actual
prediction_correct = (analysis.prediction == actual_direction)
```

---

## Performance Optimization

### Lookback Window

- **Previous**: 4 hours of historical data per period
- **Current**: 1 hour of historical data per period
- **Impact**: 4x faster volatility calculations, same accuracy

### Pagination

- **Issue**: Supabase 1000-row default limit
- **Solution**: Fetch data in 1000-row batches using `.range(offset, limit)`
- **Impact**: Can now fetch multi-day backtests without truncation

### Data Validation

```python
# Check if sufficient data before analysis
expected_bars = (timeframe_minutes * 24 * 60) / aggregation_minutes
data_coverage = len(actual_bars) / expected_bars

if data_coverage < 0.8:
    print(f"WARNING: Data coverage only {data_coverage*100:.1f}%")
```

---

## Summary

The OpenPredict prediction model combines:

1. **Statistical Analysis**: Volatility-normalized deviations
2. **Temporal Pattern Recognition**: 5-block early zone vs 3-block mid-pivot
3. **Reversal Detection**: Sustained counter-move validation
4. **Early Prediction**: Locks direction at 71.4% through period
5. **Confidence Grading**: Weak/Moderate/Strong based on deviation magnitude

This creates a probabilistic framework for predicting directional bias before the period completes, enabling analysis of mid-period reversals before they fully develop.
