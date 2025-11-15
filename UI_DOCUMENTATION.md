# Global Market Predictor - UI Documentation

**Version:** 2.0
**Date:** 2025-11-12
**Purpose:** Reference document to preserve UI layout and prevent accidental removal of features

---

## 📱 Page Structure

### **Main Pages**
1. **Dashboard** (`/`) - Primary multi-asset prediction interface
2. **Fibonacci Pivots** (`/fibonacci-pivots`) - Support/resistance levels

---

## 🏠 Dashboard Page (`/`)

### Header Section

#### Title & Navigation
```
🌍 Global Market Predictor          [📐 Fib Pivots]
Multi-Asset Dashboard - Futures & Indices
```

**Components:**
- Main title with globe emoji
- Single navigation button: "📐 Fib Pivots"
- Subtitle text
- Data freshness indicator with countdown timer

#### Refresh Status Bar
```
[●] Next update: --:-- [Badge] Last: --
```
- Green dot indicator when data is fresh
- Countdown timer to next update
- Update type badge (Smart/Force)
- Last update timestamp

---

### Ticker Cards Layout

#### Section Organization
1. **US Futures Section**
   - Header: "📊 US Futures"
   - Subtitle: "E-mini Contracts (Globex)"
   - Grid of futures cards: NQ=F, ES=F, RTY=F, YM=F

2. **Global Indices Section**
   - Header: "🌐 Global Indices"
   - Subtitle: "Major Market Indices & Volatility"
   - Grid of index cards: ^FTSE, ^N225, ^VIX

3. **Cryptocurrency Section** ⚠️
   - **STATUS: HIDDEN (Commented out)**
   - Backend code functional but not displayed
   - Cards: BTC-USD, SOL-USD, ADA-USD

---

### 📊 Ticker Card Components

Each ticker card displays the following elements:

#### 1. Card Header
```
[Symbol]  [Name]          [●] [Status Badge]
[Current Price]           [Prediction Badge]
```

**Elements:**
- **Symbol** (e.g., NQ=F)
- **Full Name** (e.g., NASDAQ-100 E-mini Futures)
- **Status Indicator**
  - 🟢 Green = Market Open
  - 🟡 Yellow = Pre-market
  - 🔴 Red = Market Closed
  - 🌙 Moon = Overnight
- **Status Text** (e.g., "OPEN", "CLOSED")
- **Current Price** (large, bold)
- **Prediction Badge**
  - 🟢 Green = BULLISH
  - 🔴 Red = BEARISH
  - 🟡 Yellow = NEUTRAL

#### 2. Quick Metrics Row
```
[Signals ℹ️]  [Score ℹ️]  [Today ℹ️]  [Volatility ⚠️]
```

**Metrics (left to right):**
1. **Signals** - Bullish count / Total signals (e.g., "8/12")
2. **Score** - Weighted prediction score 0-1 scale (e.g., "0.67")
3. **Today** - Daily accuracy percentage (NQ=F, ES=F, BTC-USD, ^FTSE only)
   - Format: "correct/total (percentage%)"
   - Color-coded: Green (70%+), Yellow (50-70%), Red (<50%)
4. **Volatility** - Hourly range percentage
   - Badge colors: Red (High), Yellow (Moderate), Green (Low)

#### 3. Session Times Row
```
[NY Open: $XX,XXX.XX]  [UK: HH:MM | NY: HH:MM | Tokyo: HH:MM]
```

**Elements:**
- **NY Open Price** - 8:30am ET reference price
- **Current Times** - UK (London), NY (Eastern), Tokyo timezones

#### 4. View More Button
```
[▼ View More]
```
- Expandable dropdown toggle
- Reveals detailed analysis sections below

---

### 📈 Dropdown Details (Expanded View)

When "View More" is clicked, three detailed sections appear:

#### Section 1: Reference Levels Table

**Header:** `📊 Reference Levels (X levels)`

**Table Columns:**
| Level Name | Price | Signal | Distance |
|------------|-------|--------|----------|

**Reference Levels Displayed:**
- **Single Price Levels:**
  - Daily Open (Midnight)
  - NY Open (8:30am)
  - 30-Min Open
  - NY Open (7:00am)
  - 4-Hour Open
  - Weekly Open
  - Hourly Open
  - Previous Hourly Open
  - Previous Week Open
  - Previous Day High
  - Previous Day Low
  - Monthly Open

- **Range-Based Levels:**
  - 7:00-7:15am Range (High/Low)
  - 8:30-8:45am Range (High/Low)
  - Asian Kill Zone (High/Low)
  - London Kill Zone (High/Low)
  - NY AM Kill Zone (High/Low)
  - NY PM Kill Zone (High/Low)

**Signal Indicators:**
- 🟢 Green = Bullish signal
- 🔴 Red = Bearish signal
- ⚪ Gray = Neutral signal

**Features:**
- Color-coded rows based on signal
- Distance from current price
- "Show All X Levels" button if >5 levels

---

#### Section 2: Intraday Predictions Table

**Header:** `⏰ Intraday Predictions (9am/10am)`

**Table Columns:**
| Target | Prediction | Confidence | Ref Open | Target Close | Result | Status | Time |
|--------|------------|------------|----------|--------------|--------|--------|------|

**Predictions Shown:**
1. **9am Prediction**
   - Target time: 9:00am ET → 10:00am ET
   - Reference: 7:00am open price

2. **10am Prediction**
   - Target time: 10:00am ET → 11:00am ET
   - Reference: 8:30am open price

**Data Fields:**
- **Prediction:** BULLISH, BEARISH, or NEUTRAL
- **Confidence:** Percentage with decay factor applied
- **Reference Open:** Starting price for prediction
- **Target Close:** Actual closing price at target hour
- **Result:** CORRECT ✓, WRONG ✗, or PENDING ⏳
- **Status:** ACTIVE or VERIFIED
- **Time Until Target:** Countdown or "PASSED"

**Color Coding:**
- Green row = Correct prediction
- Red row = Wrong prediction
- Yellow row = Pending verification

---

#### Section 3: 24-Hour Prediction History

**Header:** `📊 24-Hour Prediction History`

**Sub-header:**
- Today's Accuracy badge (color-coded)
- Format: "XX.X% (correct/verified)"

**Table Columns:**
| Time | Hour | Price | Prediction | Confidence | Result |
|------|------|-------|------------|------------|--------|

**Features:**
- Shows last 24 hours of hourly predictions
- Color-coded result badges:
  - 🟢 Green = CORRECT
  - 🔴 Red = WRONG
  - 🟡 Yellow = PENDING
- Scrollable container
- Auto-loads from `/api/24h-history/{symbol}` endpoint

**Display Rules:**
- Only shown for: NQ=F, ES=F, BTC-USD, ^FTSE
- Data refreshes with page load
- Sorted by time descending (newest first)

---

## 📐 Fibonacci Pivots Page (`/fibonacci-pivots`)

### Page Header
```
[← Dashboard]

📐 Fibonacci Pivot Points
Support and resistance levels calculated using Fibonacci ratios
Formula: PP = (H+L+C)/3 | R/S levels at 38.2%, 61.8%, and 100% of range
```

---

### Ticker Tabs
```
[📈 NQ=F (NASDAQ-100)]  [📊 ES=F (S&P 500)]  [🇬🇧 ^FTSE (FTSE 100)]
```

**Features:**
- Active tab highlighted with gradient
- Click to switch between tickers
- Smooth fade transition

---

### Current Price Banner
```
[NASDAQ-100 E-mini Futures]         [$25,XXX.XX]
Current Market Price
```

**Elements:**
- Ticker full name
- Current market price (large, gradient text)
- Subtitle label

---

### Pivot Levels Display

Each ticker shows **3 timeframe sections:**

#### 1. Daily Pivots
**Header:** `📅 Daily Pivots`

#### 2. Weekly Pivots
**Header:** `📆 Weekly Pivots`

#### 3. Monthly Pivots
**Header:** `🗓️ Monthly Pivots`

---

### Pivot Ladder (for each timeframe)

**Levels Displayed (top to bottom):**
```
R3 - Resistance 3 (100%)    [Price]  [Distance]  [⭐ Closest]
R2 - Resistance 2 (61.8%)   [Price]  [Distance]
R1 - Resistance 1 (38.2%)   [Price]  [Distance]
PP - Pivot Point             [Price]  [Distance]
S1 - Support 1 (38.2%)       [Price]  [Distance]
S2 - Support 2 (61.8%)       [Price]  [Distance]  [⭐ Closest]
S3 - Support 3 (100%)        [Price]  [Distance]
```

**Visual Styling:**
- **Resistance levels:** Red-tinted background
- **Support levels:** Green-tinted background
- **Pivot Point:** Yellow-tinted background, bold
- **Closest levels:** Blue border, star badge

**Distance Indicator:**
- Shows +/- distance from current price
- Positive = Price above current
- Negative = Price below current

---

### Calculation Source Box

At bottom of each timeframe:
```
Calculation Source:
High: XX,XXX.XX | Low: XX,XXX.XX | Close: XX,XXX.XX
Updated: YYYY-MM-DD HH:MM:SS
```

**Shows:**
- Source OHLC data used for calculation
- Timestamp of calculation

---

## 🎨 Color Scheme & Styling

### Primary Colors
- **Background Gradient:** Blue to purple (`#1e3c72` → `#2a5298` → `#7e22ce`)
- **Card Background:** White with shadow
- **Text Primary:** Dark gray (`#495057`)
- **Text Secondary:** Medium gray (`#6c757d`)

### Signal Colors
- **Bullish/Green:** `#28a745`
- **Bearish/Red:** `#dc3545`
- **Neutral/Yellow:** `#ffc107`
- **Info/Blue:** `#667eea`

### Status Indicators
- **Open/Active:** Green (`#28a745`)
- **Closed:** Red (`#dc3545`)
- **Pre-market:** Yellow (`#ffc107`)
- **Overnight:** Gray (`#6c757d`)

### Volatility Badges
- **Low:** Green background
- **Moderate:** Yellow background
- **High:** Red background

---

## 📊 Key Data Points - Must Display

### Dashboard - Per Ticker Card

#### Always Visible (Card):
1. ✅ Symbol (e.g., NQ=F)
2. ✅ Full name (e.g., NASDAQ-100 E-mini Futures)
3. ✅ Current price (large, prominent)
4. ✅ Market status (Open/Closed) with colored indicator
5. ✅ Prediction badge (Bullish/Bearish/Neutral)
6. ✅ Signals count (bullish/total)
7. ✅ Weighted score
8. ✅ Daily accuracy (for NQ=F, ES=F, BTC-USD, ^FTSE)
9. ✅ Volatility level
10. ✅ NY Open price
11. ✅ Session times (UK, NY, Tokyo)

#### Expandable (Dropdown):
12. ✅ Reference levels table (12+ levels)
13. ✅ Intraday predictions (9am/10am)
14. ✅ 24-hour prediction history (for select tickers)

### Fibonacci Pivots - Per Ticker

1. ✅ Current market price
2. ✅ Daily pivot levels (7 levels)
3. ✅ Weekly pivot levels (7 levels)
4. ✅ Monthly pivot levels (7 levels)
5. ✅ Closest level indicators
6. ✅ Distance calculations
7. ✅ Source OHLC data
8. ✅ Calculation timestamp

---

## ⚠️ Important Rules

### DO NOT REMOVE:
- ❌ Any metric boxes (Signals, Score, Today, Volatility)
- ❌ Reference levels table
- ❌ Intraday predictions table
- ❌ 24-hour history table
- ❌ Session times row
- ❌ Market status indicators
- ❌ Fibonacci pivot calculations
- ❌ Closest level highlighting

### Optional Elements:
- ✅ Cryptocurrency section (currently hidden by design)
- ✅ Additional tickers can be added to existing sections

### Consistency Requirements:
- All tickers must show same dropdown structure
- NQ=F, ES=F, BTC-USD, ^FTSE must all have 24h history
- All tickers must have reference levels
- All tickers must have intraday predictions (9am/10am)

---

## 🔧 Technical Notes

### Tickers Configuration

**Currently Active:**
- **US Futures:** NQ=F, ES=F, RTY=F, YM=F
- **Global Indices:** ^FTSE, ^N225, ^VIX
- **Crypto (hidden):** BTC-USD, SOL-USD, ADA-USD

**24h History Enabled For:**
- NQ=F, ES=F, BTC-USD, ^FTSE

### Data Refresh
- Auto-refresh countdown timer in header
- Smart refresh vs Force refresh
- Data freshness indicator (green dot)

### Responsive Design
- Cards stack on mobile
- Tables scroll horizontally on small screens
- Touch-friendly buttons and tabs

---

## 📝 Future Enhancement Areas

### Potential Additions (without removing current UI):
1. Additional timeframes for Fibonacci pivots
2. More tickers in each section
3. Additional reference levels
4. Historical accuracy charts
5. Alert/notification system
6. Custom watchlists

### Areas to Avoid Changing:
1. Core prediction display structure
2. Reference levels table format
3. Intraday predictions layout
4. Color scheme and branding
5. Navigation structure

---

## 🎯 UI Checklist for Changes

Before deploying any UI changes, verify:

- [ ] All metric boxes still present (Signals, Score, Today, Volatility)
- [ ] Reference levels table intact with all levels
- [ ] Intraday predictions showing 9am and 10am
- [ ] 24h history displaying for correct tickers
- [ ] Fibonacci pivots showing all 3 timeframes
- [ ] Color coding consistent (green/red/yellow)
- [ ] Market status indicators working
- [ ] Session times displaying correctly
- [ ] Navigation links functional
- [ ] Dropdown "View More" working
- [ ] Tab switching working on Fib page

---

**END OF DOCUMENTATION**

*This document serves as the definitive reference for the Global Market Predictor UI.*
*Any changes should be documented here to maintain design consistency.*
