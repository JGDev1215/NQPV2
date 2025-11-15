# NASDAQ Predictor - Comprehensive UI/UX Review & Modernization Roadmap

**Project**: Global Market Predictor Dashboard
**Date**: November 15, 2025
**Reviewed By**: Claude Code (Senior UI/Frontend Architect)
**Current Stack**: Flask Backend + HTML/CSS/JavaScript Frontend + Bootstrap 5.3.2

---

## Executive Summary

The NASDAQ Predictor project has a **functional but dated** UI/UX design that requires modernization to meet 2025 standards. The current implementation demonstrates good foundational structure with Bootstrap 5 integration, but suffers from:

1. **Suboptimal responsive design** - Mobile experience shows cramped layouts and oversized typography
2. **Weak visual hierarchy** - Confidence scores and prediction confidence not prominently featured
3. **Inefficient real-time update handling** - No WebSocket integration, basic polling mechanism
4. **Inconsistent component patterns** - Mixed inline styles and CSS with minimal design tokens
5. **Limited accessibility features** - Minimal ARIA labels, color-dependent indicators
6. **Outdated interactive patterns** - Inline hover effects instead of modern micro-interactions
7. **Poor filter/navigation UX** - Limited filtering on prediction history, no saved filter states
8. **Weak data visualization approach** - Confidence bars present but underutilized for visual confidence communication

**Opportunity Level**: HIGH - Modern redesign would significantly improve usability and user engagement

---

## 1. Current State Assessment

### 1.1 Technology Stack
```
Frontend:
- HTML5 (semantic structure partially implemented)
- CSS3 with custom styles + Bootstrap 5.3.2
- Vanilla JavaScript (ES6+ compatible)
- Google Inter font family (good choice for dashboards)
- No charting library (candidate: Chart.js, Plotly.js, or Apex Charts)

Backend:
- Flask (modular architecture with blueprints)
- APScheduler (background jobs for real-time updates)
- No WebSocket implementation (uses HTTP polling)

Data Flow:
- Fetch API for data retrieval
- REST endpoints for predictions, history, block analysis
- 15-minute prediction generation cycles
- 60-second data refresh intervals
```

### 1.2 Current UI Components Inventory

#### Landing Page (`index.html`)
- **Header**: Gradient background, navigation links as inline buttons
- **Market Status Indicator**: Data freshness dot with countdown timer
- **Ticker Grid**: Responsive 3-column grid (auto-fit, minmax 350px)
- **Ticker Cards**: Price display, prediction badge, confidence bar, quick metrics (2-column grid)
- **Status Badges**: Market status (OPEN, CLOSED, PREMARKET, AFTERHOURS)
- **Expandable Details**: View Details button reveals reference levels, intraday predictions, history

#### Block Predictions Page (`block_predictions.html`)
- **Ticker Tabs**: Button-style navigation for instrument selection
- **7-Block Timeline**: Horizontal visual blocks showing analysis (1-5) vs prediction (6-7) periods
- **Prediction Badge**: Bullish/Bearish/Neutral with gradient backgrounds
- **Analysis Details**: Grid-based detail cards below timeline
- **Countdown Container**: Highlights next prediction generation time
- **Decision Tree Path**: Displays analysis decision logic

#### History Page (`history.html`)
- **Page Header**: Gradient background with navigation
- **Ticker Tabs**: Filter prediction history by instrument
- **Reference Levels Section**: Detailed table with signal analysis
- **Intraday Predictions Table**: 9am/10am window predictions with status badges
- **Prediction History Table**: 24-hour prediction history with accuracy metrics

### 1.3 Responsive Design Assessment

#### Mobile (< 480px)
**Issues:**
- Header h1 scales to 1.4rem (acceptable but could be improved)
- Ticker cards stack to single column (correct approach)
- 7-block timeline still uses 7-column layout (TOO CRAMPED - should be 2-3 rows)
- Quick metrics remain 2-column (too narrow for small screens)
- Tables become unreadable on phones (no horizontal scroll or card layout)

#### Tablet (480px - 768px)
**Issues:**
- Grid layout still 1 column (should expand to 2 columns)
- Ticker tabs become vertical stack (good) but buttons are full-width
- Header wraps awkwardly

#### Desktop (768px+)
**Strengths:**
- Clean 3-column ticker grid
- Good whitespace usage
- Tab-based navigation works well
**Weaknesses:**
- Ticker cards at 350px minimum are undersized for detailed data
- No tablet optimizations (should be 2-column)

### 1.4 Data Visualization Assessment

**Current Approach:**
- Confidence bars (linear progress bars) - basic but effective
- Prediction badges (bullish/bearish) - good color coding
- Block timeline blocks (colored squares) - visual but small
- Tables for detailed data - not visual, hard to scan

**Missing:**
- Time-series charts for intraday trends
- Confidence trend visualization
- Prediction accuracy trend charts
- Reference level distance visualization
- No Chart.js, Plotly, or canvas-based visualizations

### 1.5 Real-Time Update Mechanism

**Current Implementation:**
```javascript
// Polling-based (from app.js)
- Initial data fetch on page load
- Auto-refresh interval (appears to be 60 seconds based on refresh-status display)
- Manual countdown timer display
- No WebSocket support
```

**Issues:**
- Heavy on bandwidth (entire ticker data fetched every 60 seconds)
- UI flashing during updates (no graceful transitions)
- No incremental updates (replaces entire card instead of updating changed fields)
- Countdown timer in header not synchronized with actual fetch cycle
- No error recovery or retry logic visible

### 1.6 Visual Hierarchy & Confidence Score Presentation

**Current Approach:**
- Price is largest (2rem gradient text) - CORRECT
- Prediction badge prominent - CORRECT
- Confidence bar shows percentage - GOOD but could be enhanced
- Quick metrics small (2-column boxes) - SUBOPTIMAL positioning

**Issues:**
- Confidence bar is only ~20px tall (hard to see at glance)
- Confidence percentage text is tiny (0.65rem)
- No color-coded confidence levels (just percentage number)
- Accuracy metrics relegated to expandable details (should be visible on card)
- Daily accuracy hidden in expandable section (critical metric!)

**Recommended Enhancement:**
- Make confidence section 1.5-2x taller
- Add color gradient to confidence bar (red < 50%, yellow 50-75%, green > 75%)
- Display confidence in large, bold text (not just percentage)
- Show accuracy badge on main card
- Add visual confidence indicator (stars, circles, or segments)

### 1.7 Market Status Awareness

**Current Implementation:**
- Status indicator dot (green/orange/red) with pulsing animation
- Text badge (OPEN, CLOSED, PREMARKET, AFTERHOURS)
- Last update timestamp
- Countdown to next update

**Strengths:**
- Multiple indicators provide redundancy
- Pulsing animation catches attention
- Clear status messaging

**Weaknesses:**
- Market hours not displayed (what time does market close today?)
- No timezone indicator at global scale
- Kill zones not visually called out in market-aware way
- Pre-market/after-hours data quality not differentiated

### 1.8 Filter and Navigation Systems

**Current Implementation:**
- Ticker tabs (radio-button style, one active at a time)
- "View Details" expandable button per card
- Back links for navigation between pages
- No date/time range filters on history page
- No metric visibility toggles
- No saved filter preferences

**Weaknesses:**
- Limited to ticker filtering only
- No way to compare multiple tickers side-by-side
- No date range picker on history page
- No accuracy threshold filter
- No confidence score filter
- Filter state not preserved on page reload
- No "favorites" or metric selection

---

## 2. Bootstrap 5 Modernization Recommendations

### 2.1 Design System Implementation

#### Color Palette (Updated for 2025 with WCAG AA Compliance)
```css
/* Primary Brand Colors */
--primary-gradient: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
--primary-dark: #1e3c72;
--primary-light: #f0f4ff;

/* Semantic Colors */
--bullish: #10b981;      /* Green (from Tailwind) */
--bearish: #ef4444;      /* Red (from Tailwind) */
--neutral: #8b5cf6;      /* Purple for neutral */
--warning: #f59e0b;      /* Amber for caution */
--info: #3b82f6;         /* Blue for information */

/* Confidence Thresholds */
--confidence-low: #ef4444;     /* < 50% */
--confidence-mid: #f59e0b;     /* 50-75% */
--confidence-high: #10b981;    /* > 75% */

/* Market Status */
--market-open: #10b981;        /* Green */
--market-closed: #ef4444;      /* Red */
--market-premarket: #f59e0b;   /* Orange */
--market-afterhours: #f59e0b;  /* Orange */

/* Grayscale (Accessible) */
--gray-50: #f9fafb;
--gray-100: #f3f4f6;
--gray-200: #e5e7eb;
--gray-300: #d1d5db;
--gray-500: #6b7280;
--gray-700: #374151;
--gray-900: #111827;
```

#### Typography Scale (Bootstrap 5 Extended)
```css
/* Headings */
h1 { font-size: 2.5rem; font-weight: 800; letter-spacing: -0.02em; }
h2 { font-size: 1.875rem; font-weight: 700; }
h3 { font-size: 1.5rem; font-weight: 700; }
h4 { font-size: 1.25rem; font-weight: 600; }
h5 { font-size: 1rem; font-weight: 600; }
h6 { font-size: 0.875rem; font-weight: 600; }

/* Body Text */
body { font-size: 0.9375rem (15px); line-height: 1.6; }
small { font-size: 0.8125rem; }
.text-xs { font-size: 0.75rem; }
.text-2xs { font-size: 0.625rem; }

/* Monospace (for prices, technical data) */
.font-mono { font-family: 'Courier New', monospace; }
```

#### Spacing System (8px grid)
```css
$spacing-xs: 0.25rem;   /* 4px */
$spacing-sm: 0.5rem;    /* 8px */
$spacing-md: 1rem;      /* 16px */
$spacing-lg: 1.5rem;    /* 24px */
$spacing-xl: 2rem;      /* 32px */
$spacing-2xl: 3rem;     /* 48px */

/* Apply to cards */
.card { padding: $spacing-lg; gap: $spacing-md; }
.card-compact { padding: $spacing-md; }
```

#### Breakpoint Strategy
```scss
// Bootstrap 5 standard breakpoints + additions
$breakpoint-2xs: 320px;   /* Small phones */
$breakpoint-xs: 480px;    /* Phones */
$breakpoint-sm: 640px;    /* Large phones */
$breakpoint-md: 768px;    /* Tablets */
$breakpoint-lg: 1024px;   /* Laptops */
$breakpoint-xl: 1280px;   /* Desktops */
$breakpoint-2xl: 1536px;  /* Large desktops */
```

### 2.2 Component Redesign (Bootstrap 5 Integration)

#### Ticker Card Redesign
```html
<!-- BEFORE (Current) -->
<div class="ticker-card">
  <div class="ticker-header">
    <span class="ticker-symbol">📈 NQ=F <span class="ticker-type-badge">futures</span></span>
    <span class="market-status-badge open">OPEN</span>
  </div>
  <div class="ticker-name">NASDAQ-100 E-mini</div>
  <div class="ticker-price">19,485.50</div>
  <span class="prediction-badge bullish">📈 BULLISH</span>
  <div class="confidence-bar-container">
    <div class="confidence-bar bullish" style="width: 78%;">78%</div>
  </div>
  <!-- Quick metrics, details button, expandable panel... -->
</div>

<!-- AFTER (Modernized with Bootstrap 5 Card Component) -->
<article class="card card-prediction h-100 border-0 shadow-sm" role="region" aria-label="NQ=F NASDAQ Prediction">
  <!-- Card Header Section -->
  <div class="card-header bg-light border-bottom">
    <div class="row align-items-center g-2">
      <div class="col">
        <h3 class="h5 mb-0">
          <span class="ticker-icon" aria-hidden="true">📈</span>
          <strong>NQ=F</strong>
          <span class="badge bg-info-subtle text-info-emphasis ms-2 small">FUTURES</span>
        </h3>
        <p class="text-muted small mb-0">NASDAQ-100 E-mini Futures</p>
      </div>
      <div class="col-auto">
        <span class="badge bg-success rounded-pill px-3 py-2" role="status">
          <span class="spinner-grow spinner-grow-sm me-1" role="status">
            <span class="visually-hidden">Live</span>
          </span>
          OPEN
        </span>
      </div>
    </div>
  </div>

  <!-- Card Body: Price & Primary Prediction -->
  <div class="card-body">
    <!-- Price Section -->
    <div class="mb-4">
      <p class="text-muted small text-uppercase letter-spacing-sm mb-1">Current Price</p>
      <h2 class="h3 mb-2">
        <span class="price-value">19,485.50</span>
        <span class="badge bg-success-subtle text-success-emphasis small">+0.48%</span>
      </h2>
    </div>

    <!-- Prediction & Confidence (Enhanced Visual Hierarchy) -->
    <div class="prediction-section mb-4">
      <div class="d-flex align-items-center gap-2 mb-3">
        <span class="badge bg-success-subtle text-success-emphasis py-2 px-3 font-weight-bold">
          📈 BULLISH
        </span>
        <span class="small text-muted">(Next 1h)</span>
      </div>

      <!-- Confidence Indicator (Enhanced from 20px to 60px) -->
      <div class="confidence-display mb-3">
        <p class="text-muted small text-uppercase letter-spacing-sm mb-2">Prediction Confidence</p>
        <div class="progress mb-2" role="progressbar" aria-label="Prediction confidence: 78%" style="height: 2.5rem;">
          <div class="progress-bar bg-success gradient-pulse" style="width: 78%;">
            <span class="confidence-percentage fw-bold">78%</span>
          </div>
        </div>
        <p class="text-muted small">Strong bullish confidence with multiple confirming signals</p>
      </div>

      <!-- Today's Accuracy Badge (Now Visible!) -->
      <div class="row g-2 mb-3">
        <div class="col-6">
          <div class="stat-card bg-light rounded p-3">
            <p class="text-muted small text-uppercase letter-spacing-sm mb-1">Today Accuracy</p>
            <p class="h5 mb-0"><strong>6/8</strong> <span class="small text-success">(75%)</span></p>
          </div>
        </div>
        <div class="col-6">
          <div class="stat-card bg-light rounded p-3">
            <p class="text-muted small text-uppercase letter-spacing-sm mb-1">Signal Count</p>
            <p class="h5 mb-0"><strong>7/9</strong> <span class="small text-info">signals</span></p>
          </div>
        </div>
      </div>

      <!-- Volatility Indicator -->
      <div class="alert alert-info alert-sm small mb-0" role="status">
        📊 <strong>Volatility:</strong> Moderate (±1.2%) | Data Age: 2.3 minutes
      </div>
    </div>
  </div>

  <!-- Card Footer: Actions -->
  <div class="card-footer bg-light border-top">
    <button class="btn btn-sm btn-outline-primary w-100" data-bs-toggle="collapse" data-bs-target="#details-nqf">
      <span class="collapse-toggle-icon">+</span> View Details
    </button>
  </div>

  <!-- Collapsible Details Section -->
  <div class="collapse" id="details-nqf">
    <div class="card-body border-top">
      <!-- Reference Levels Tab Content -->
      <ul class="nav nav-tabs mb-3" role="tablist">
        <li class="nav-item" role="presentation">
          <button class="nav-link active" data-bs-toggle="tab" data-bs-target="#levels-nqf">Levels</button>
        </li>
        <li class="nav-item" role="presentation">
          <button class="nav-link" data-bs-toggle="tab" data-bs-target="#intraday-nqf">Intraday</button>
        </li>
        <li class="nav-item" role="presentation">
          <button class="nav-link" data-bs-toggle="tab" data-bs-target="#history-nqf">History (24h)</button>
        </li>
      </ul>

      <!-- Tab Content -->
      <div class="tab-content">
        <div class="tab-pane fade show active" id="levels-nqf" role="tabpanel">
          <!-- Reference Levels Table (Responsive) -->
          <div class="table-responsive">
            <table class="table table-sm table-hover mb-0">
              <thead class="table-light">
                <tr>
                  <th>Level</th>
                  <th>Price</th>
                  <th>Signal</th>
                  <th class="text-end">Distance</th>
                </tr>
              </thead>
              <tbody>
                <tr>
                  <td><strong>Daily Open</strong></td>
                  <td><code>19,450.00</code></td>
                  <td><span class="badge bg-success-subtle text-success">Bullish</span></td>
                  <td class="text-end"><code>+35.50</code></td>
                </tr>
                <!-- More rows... -->
              </tbody>
            </table>
          </div>
        </div>
        <!-- Other tab panes... -->
      </div>

      <!-- Metadata Footer -->
      <hr>
      <p class="text-muted small text-center mb-0">
        Source: yfinance | Last update: 2 minutes ago
      </p>
    </div>
  </div>
</article>
```

#### Header/Navigation Redesign
```html
<!-- BEFORE (Current) -->
<div class="header">
  <div class="container">
    <div style="display: flex; justify-content: space-between;">
      <h1>🌍 Global Market Predictor</h1>
      <div style="display: flex; gap: 10px;">
        <a href="/history">📊 Predictions</a>
        <a href="/block-predictions">🔮 Block Predictions</a>
      </div>
    </div>
    <div class="refresh-status">...countdown timer...</div>
  </div>
</div>

<!-- AFTER (Bootstrap 5 Navbar Component) -->
<nav class="navbar navbar-dark bg-gradient shadow-sm sticky-top" aria-label="Main">
  <div class="container-fluid">
    <!-- Brand -->
    <a class="navbar-brand fw-bold h5 mb-0" href="/">
      <span class="me-2" aria-hidden="true">🌍</span>
      Global Market Predictor
    </a>

    <!-- Refresh Status (Moved to navbar right) -->
    <div class="d-flex align-items-center gap-3">
      <!-- Status Indicator -->
      <div class="refresh-indicator small text-light d-none d-md-flex align-items-center gap-2">
        <span class="status-dot fresh" role="status" aria-label="Data fresh"></span>
        <span class="countdown-display" aria-live="polite">Next: 58s</span>
      </div>

      <!-- Navbar Toggler for Mobile -->
      <button class="navbar-toggler" type="button" data-bs-toggle="offcanvas" 
              data-bs-target="#navbarOffcanvas" aria-controls="navbarOffcanvas">
        <span class="navbar-toggler-icon"></span>
      </button>
    </div>
  </div>

  <!-- Offcanvas Navigation for Mobile -->
  <div class="offcanvas offcanvas-end" tabindex="-1" id="navbarOffcanvas">
    <div class="offcanvas-header">
      <h5>Navigation</h5>
      <button type="button" class="btn-close" data-bs-dismiss="offcanvas"></button>
    </div>
    <div class="offcanvas-body">
      <ul class="navbar-nav ms-auto">
        <li class="nav-item">
          <a class="nav-link" href="/">Dashboard</a>
        </li>
        <li class="nav-item">
          <a class="nav-link" href="/history">Prediction History</a>
        </li>
        <li class="nav-item">
          <a class="nav-link" href="/block-predictions">Block Analysis</a>
        </li>
        <li class="nav-item">
          <a class="nav-link" href="/fibonacci-pivots">Fibonacci Pivots</a>
        </li>
      </ul>
    </div>
  </div>
</nav>
```

---

## 3. Mobile-First Responsive Design Strategy

### 3.1 Breakpoint-Specific Layouts

```scss
// Mobile-First Grid Strategy
.ticker-grid {
  // 320px+ (default: single column)
  display: grid;
  grid-template-columns: 1fr;
  gap: 1rem;

  // 480px+ (2 columns)
  @media (min-width: 480px) {
    grid-template-columns: repeat(2, 1fr);
  }

  // 768px+ (tablets: 2 columns)
  @media (min-width: 768px) {
    grid-template-columns: repeat(2, 1fr);
  }

  // 1024px+ (desktops: 3 columns)
  @media (min-width: 1024px) {
    grid-template-columns: repeat(auto-fit, minmax(380px, 1fr));
  }
}

// 7-Block Timeline Responsive
.blocks-timeline {
  // Mobile: stack in 2 rows (3.5 blocks each)
  @media (max-width: 480px) {
    display: grid;
    grid-template-columns: repeat(2, 1fr);
    gap: 0.5rem;

    .block {
      padding: 0.75rem 0.5rem;
      font-size: 0.7rem;
    }
  }

  // Tablet: 1 row but smaller blocks
  @media (max-width: 768px) {
    gap: 0.5rem;
  }

  // Desktop: full width
  @media (min-width: 1024px) {
    display: flex;
    gap: 0.75rem;
  }
}

// Card responsiveness
.ticker-card {
  // Mobile: tight padding
  @media (max-width: 480px) {
    padding: 1rem;

    .card-header { padding: 0.75rem; }
    .card-body { padding: 1rem; }
    .card-footer { padding: 0.75rem; }
  }

  // Tablet: normal padding
  @media (min-width: 768px) {
    padding: 1.25rem;
  }

  // Desktop: generous padding
  @media (min-width: 1024px) {
    padding: 1.5rem;
  }
}
```

### 3.2 Touch-Friendly Design (Mobile)

**Button/Tap Target Sizing:**
```css
/* Minimum 44x44px for touch targets (WCAG Mobile) */
.btn, .btn-sm {
  min-height: 44px;
  min-width: 44px;
  padding: 0.75rem 1rem;
}

/* Adjust for mobile */
@media (max-width: 768px) {
  .btn { min-height: 48px; } /* Larger on mobile */
}
```

**Bottom Navigation Pattern (Mobile):**
```html
<!-- Mobile Bottom Navigation (replaces top navbar on small screens) -->
<nav class="navbar navbar-light bg-light fixed-bottom d-lg-none border-top" aria-label="Mobile navigation">
  <div class="container-fluid d-flex justify-content-around gap-2">
    <a href="/" class="nav-link text-center small active">
      <span class="d-block h5 mb-1">📊</span>
      Dashboard
    </a>
    <a href="/history" class="nav-link text-center small">
      <span class="d-block h5 mb-1">📈</span>
      History
    </a>
    <a href="/block-predictions" class="nav-link text-center small">
      <span class="d-block h5 mb-1">🔮</span>
      Blocks
    </a>
    <a href="/fibonacci-pivots" class="nav-link text-center small">
      <span class="d-block h5 mb-1">📐</span>
      Pivots
    </a>
  </div>
</nav>
```

### 3.3 Table Responsiveness (Mobile Cards)

```html
<!-- BEFORE: Table (unreadable on mobile) -->
<table class="prediction-history-table">
  <thead>
    <tr>
      <th>Time</th>
      <th>Prediction</th>
      <th>Confidence</th>
      <th>Actual</th>
      <th>Result</th>
    </tr>
  </thead>
  <tbody>
    <tr>
      <td>09:00 ET</td>
      <td>BULLISH</td>
      <td>78%</td>
      <td>UP</td>
      <td><span class="badge bg-success">CORRECT</span></td>
    </tr>
  </tbody>
</table>

<!-- AFTER: Responsive Table (Bootstrap Utility) -->
<div class="table-responsive-sm">
  <table class="table table-hover">
    <!-- Standard table on tablet+ -->
  </table>
</div>

<!-- OR: Card Layout for Mobile -->
<div class="prediction-cards d-block d-md-none">
  <article class="card mb-2 border-start border-success border-4">
    <div class="card-body">
      <div class="row g-2 small">
        <div class="col-6">
          <p class="text-muted mb-1">Time</p>
          <strong>09:00 ET</strong>
        </div>
        <div class="col-6">
          <p class="text-muted mb-1">Prediction</p>
          <span class="badge bg-success">BULLISH</span>
        </div>
        <div class="col-6">
          <p class="text-muted mb-1">Confidence</p>
          <strong>78%</strong>
        </div>
        <div class="col-6">
          <p class="text-muted mb-1">Result</p>
          <span class="badge bg-success">CORRECT</span>
        </div>
      </div>
    </div>
  </article>
</div>
```

---

## 4. Auto-Refresh & Real-Time Data Handling

### 4.1 Improved Polling Architecture

```javascript
/**
 * Enhanced Auto-Refresh System with Graceful Updates
 * - Prevents API thrashing
 * - Smooth DOM updates
 * - Error recovery
 * - User feedback
 */

class DashboardAutoRefresh {
  constructor(refreshInterval = 60000) { // 60 seconds
    this.refreshInterval = refreshInterval;
    this.isRefreshing = false;
    this.nextRefreshTime = null;
    this.countdownInterval = null;
    this.lastSuccessfulFetch = null;
  }

  /**
   * Initialize auto-refresh with countdown timer
   */
  async init() {
    await this.fetchAndUpdateData();
    this.startCountdownTimer();
    this.scheduleNextRefresh();
  }

  /**
   * Fetch data and update UI with graceful transitions
   */
  async fetchAndUpdateData() {
    if (this.isRefreshing) return;

    this.isRefreshing = true;
    this.updateUI({ state: 'loading' });

    try {
      // Fetch data
      const response = await fetch('/api/market-data');
      const data = await response.json();

      if (!response.ok) throw new Error(data.error || 'API Error');

      // Graceful update: merge with existing data
      this.mergeAndUpdateCards(data);

      // Update status
      this.lastSuccessfulFetch = new Date();
      this.updateUI({ state: 'success', time: this.lastSuccessfulFetch });

      // Log successful update
      console.log('[Auto-Refresh] Data updated at', this.lastSuccessfulFetch);

    } catch (error) {
      console.error('[Auto-Refresh] Error:', error);
      this.updateUI({ state: 'error', message: error.message });

      // Retry after 10 seconds on error
      setTimeout(() => this.fetchAndUpdateData(), 10000);
    } finally {
      this.isRefreshing = false;
    }
  }

  /**
   * Merge new data with existing DOM, only updating changed fields
   * Prevents unnecessary re-renders and flashing
   */
  mergeAndUpdateCards(newData) {
    Object.entries(newData).forEach(([ticker, tickerData]) => {
      const card = document.querySelector(`[data-ticker="${ticker}"]`);
      if (!card) return;

      // Update only changed fields with smooth transitions
      this.updateCardField(card, 'price', tickerData.current_price);
      this.updateCardField(card, 'prediction', tickerData.prediction);
      this.updateConfidenceBar(card, tickerData.confidence, tickerData.prediction);
      this.updateMetrics(card, tickerData);
    });
  }

  /**
   * Update individual card field with smooth transition
   */
  updateCardField(card, field, value) {
    const element = card.querySelector(`[data-field="${field}"]`);
    if (!element) return;

    const currentValue = element.textContent;
    if (currentValue === String(value)) return; // No change

    // Smooth transition
    element.classList.add('updating');
    element.textContent = value;

    setTimeout(() => {
      element.classList.remove('updating');
    }, 500);
  }

  /**
   * Update confidence bar with animation
   */
  updateConfidenceBar(card, confidence, prediction) {
    const bar = card.querySelector('.confidence-bar');
    const percentage = card.querySelector('.confidence-percentage');

    if (!bar || !percentage) return;

    const newWidth = Math.min(100, confidence);
    const oldWidth = parseFloat(bar.style.width);

    if (newWidth !== oldWidth) {
      bar.style.transition = 'width 0.5s ease';
      bar.style.width = newWidth + '%';
      percentage.textContent = confidence.toFixed(1) + '%';
    }
  }

  /**
   * Update metrics box
   */
  updateMetrics(card, data) {
    const metricsBox = card.querySelector('.quick-metrics');
    if (!metricsBox) return;

    // Update signal count
    const signalsElement = metricsBox.querySelector('[data-metric="signals"]');
    if (signalsElement) {
      signalsElement.textContent = `${data.bullish_count}/${data.total_signals}`;
    }

    // Update daily accuracy if available
    if (data.daily_accuracy) {
      const accuracyElement = metricsBox.querySelector('[data-metric="accuracy"]');
      if (accuracyElement) {
        const { correct, wrong } = data.daily_accuracy;
        const rate = ((correct / (correct + wrong)) * 100).toFixed(0);
        accuracyElement.textContent = `${correct}/${correct + wrong} (${rate}%)`;
      }
    }
  }

  /**
   * Start countdown timer (e.g., "Next refresh in 47 seconds")
   */
  startCountdownTimer() {
    if (this.countdownInterval) clearInterval(this.countdownInterval);

    this.countdownInterval = setInterval(() => {
      const now = Date.now();
      const secondsUntilRefresh = Math.ceil((this.nextRefreshTime - now) / 1000);

      if (secondsUntilRefresh > 0) {
        const display = `Next: ${secondsUntilRefresh}s`;
        const countdownEl = document.getElementById('countdown-timer');
        if (countdownEl) countdownEl.textContent = display;

        // Trigger "imminent" state at 10 seconds
        if (secondsUntilRefresh <= 10) {
          document.getElementById('refresh-info')?.classList.add('refresh-imminent');
        } else {
          document.getElementById('refresh-info')?.classList.remove('refresh-imminent');
        }
      }
    }, 1000);
  }

  /**
   * Schedule next refresh
   */
  scheduleNextRefresh() {
    this.nextRefreshTime = Date.now() + this.refreshInterval;
    setTimeout(() => {
      this.fetchAndUpdateData();
      this.startCountdownTimer();
      this.scheduleNextRefresh();
    }, this.refreshInterval);
  }

  /**
   * Update UI status indicators
   */
  updateUI({ state, time, message }) {
    const statusDot = document.getElementById('data-freshness-dot');
    const updateTypeEl = document.getElementById('update-type');
    const lastUpdateEl = document.getElementById('last-update-time');

    if (state === 'loading') {
      statusDot?.classList.add('updating');
      updateTypeEl?.textContent = 'FETCHING...';
    } else if (state === 'success') {
      statusDot?.classList.remove('updating');
      statusDot?.classList.remove('moderate', 'stale');
      statusDot?.classList.add('fresh');
      updateTypeEl?.textContent = 'LIVE';
      if (time) {
        lastUpdateEl?.textContent = `Last: ${time.toLocaleTimeString()}`;
      }
    } else if (state === 'error') {
      statusDot?.classList.add('stale');
      updateTypeEl?.textContent = 'ERROR';
      if (message) {
        statusDot?.title = message;
      }
    }
  }

  /**
   * Stop auto-refresh (cleanup)
   */
  destroy() {
    if (this.countdownInterval) clearInterval(this.countdownInterval);
  }
}

// Initialize on page load
document.addEventListener('DOMContentLoaded', () => {
  const dashboard = new DashboardAutoRefresh(60000); // 60 second refresh
  dashboard.init();

  // Cleanup on page unload
  window.addEventListener('beforeunload', () => dashboard.destroy());
});
```

### 4.2 WebSocket Alternative (Future Enhancement)

```javascript
/**
 * WebSocket-based Real-Time Updates (For future implementation)
 * Reduces bandwidth, enables true real-time updates
 */

class WebSocketDashboard {
  constructor(url = 'ws://localhost:5000/ws/market-data') {
    this.url = url;
    this.socket = null;
    this.reconnectAttempts = 0;
    this.maxReconnectAttempts = 5;
  }

  connect() {
    this.socket = new WebSocket(this.url);

    this.socket.onopen = () => {
      console.log('[WebSocket] Connected');
      this.reconnectAttempts = 0;
      document.getElementById('data-freshness-dot')?.classList.add('fresh');
    };

    this.socket.onmessage = (event) => {
      const data = JSON.parse(event.data);
      this.handleDataUpdate(data);
    };

    this.socket.onerror = (error) => {
      console.error('[WebSocket] Error:', error);
      document.getElementById('data-freshness-dot')?.classList.add('stale');
    };

    this.socket.onclose = () => {
      console.log('[WebSocket] Disconnected');
      this.attemptReconnect();
    };
  }

  handleDataUpdate(data) {
    // Update specific ticker data only (not entire page refresh)
    const { ticker, current_price, prediction, confidence } = data;
    const card = document.querySelector(`[data-ticker="${ticker}"]`);

    if (card) {
      // Update fields with micro-animations
      card.querySelector('[data-field="price"]').textContent = current_price;
      card.querySelector('[data-field="prediction"]').textContent = prediction;
      // ... other updates
    }
  }

  attemptReconnect() {
    if (this.reconnectAttempts < this.maxReconnectAttempts) {
      this.reconnectAttempts++;
      const delay = Math.pow(2, this.reconnectAttempts) * 1000; // Exponential backoff
      console.log(`[WebSocket] Reconnecting in ${delay}ms...`);
      setTimeout(() => this.connect(), delay);
    }
  }
}
```

---

## 5. Visual Hierarchy & Component Redesign

### 5.1 Confidence Score Enhancement

**Current State:**
- Confidence bar: 20px tall, percentage text small (0.65rem)
- Hard to assess confidence at glance
- No color-coded confidence levels

**Redesigned Approach:**

```html
<!-- Enhanced Confidence Section (Bootstrap 5) -->
<section class="confidence-section py-3">
  <!-- Label -->
  <div class="d-flex justify-content-between align-items-center mb-2">
    <h5 class="small text-uppercase letter-spacing-sm text-muted mb-0">
      Prediction Confidence
    </h5>
    <span class="confidence-strength-badge badge bg-success-subtle text-success-emphasis px-2">
      Strong
    </span>
  </div>

  <!-- Large Progress Bar (2.5rem height for readability) -->
  <div class="progress mb-2" role="progressbar" aria-label="Confidence: 78%" style="height: 2.5rem;">
    <div class="progress-bar bg-success" style="width: 78%;">
      <span class="fw-bold fs-6 text-white ms-2">78%</span>
    </div>
  </div>

  <!-- Confidence Interpretation -->
  <p class="small text-muted mb-0">
    Strong bullish confidence. 7 out of 9 reference levels confirm directional bias.
  </p>

  <!-- Confidence Gauge Alternative (using SVG/Canvas) -->
  <div class="confidence-gauge mt-3">
    <svg viewBox="0 0 200 120" style="width: 100%; height: 80px;">
      <!-- Arc-based gauge: Red (0-33), Yellow (33-66), Green (66-100) -->
      <circle cx="100" cy="100" r="80" fill="none" stroke="#ddd" stroke-width="20"/>
      <circle cx="100" cy="100" r="80" fill="none" stroke="#10b981" stroke-width="20"
              stroke-dasharray="180 540" stroke-dashoffset="-180" opacity="0.8"/>
      <!-- Needle at 78% -->
      <line x1="100" y1="100" x2="100" y2="25" stroke="#333" stroke-width="3"/>
      <circle cx="100" cy="100" r="6" fill="#333"/>
    </svg>
    <p class="text-center small text-muted mt-2">
      78% confidence | 7/9 signals bullish
    </p>
  </div>
</section>
```

**CSS for Color-Coded Confidence:**
```css
.progress-bar {
  transition: background-color 0.3s ease, width 0.5s ease;

  /* Confidence level colors */
  &.confidence-low { background: linear-gradient(90deg, #ef4444, #f87171); }
  &.confidence-mid { background: linear-gradient(90deg, #f59e0b, #fbbf24); }
  &.confidence-high { background: linear-gradient(90deg, #10b981, #34d399); }
}

/* Animated gradient pulse for real-time feel */
@keyframes gradient-pulse {
  0%, 100% { background-position: 0% center; }
  50% { background-position: 100% center; }
}

.gradient-pulse {
  background-size: 200% 200%;
  animation: gradient-pulse 2s ease-in-out infinite;
}
```

### 5.2 Market Status Indicator Redesign

```html
<!-- Enhanced Market Status (Bootstrap Badge + Spinner) -->
<div class="market-status-section d-flex align-items-center gap-2">
  <!-- Live Status Badge -->
  <div class="badge bg-success-subtle text-success-emphasis px-3 py-2 small fw-bold">
    <span class="spinner-grow spinner-grow-sm me-2" role="status">
      <span class="visually-hidden">Market is live</span>
    </span>
    MARKET OPEN
  </div>

  <!-- Market Hours Popover -->
  <button class="btn btn-sm btn-link small text-muted" 
          data-bs-toggle="popover" 
          data-bs-title="Market Hours"
          data-bs-content="Opens: 09:30 AM ET | Closes: 4:00 PM ET">
    Info
  </button>

  <!-- Market Status Details (Collapsible) -->
  <div class="market-details collapse" id="marketDetails">
    <div class="card card-body small mt-2">
      <div class="row g-2 text-center">
        <div class="col-auto">
          <p class="text-muted mb-1 small">Status</p>
          <p class="mb-0"><strong class="text-success">OPEN</strong></p>
        </div>
        <div class="col-auto border-start border-end">
          <p class="text-muted mb-1 small">Time to Close</p>
          <p class="mb-0"><strong>3h 45m</strong></p>
        </div>
        <div class="col-auto">
          <p class="text-muted mb-1 small">Next Event</p>
          <p class="mb-0"><strong>4:00 PM Close</strong></p>
        </div>
      </div>
    </div>
  </div>
</div>

<!-- Pre-Market/After-Hours Indicator -->
<div class="badge bg-warning-subtle text-warning-emphasis px-3 py-2 small">
  <span class="spinner-grow spinner-grow-sm me-2" role="status">
    <span class="visually-hidden">Market is in pre-market</span>
  </span>
  PRE-MARKET (7:00 AM - 9:30 AM)
</div>

<!-- Market Closed Indicator -->
<div class="badge bg-danger-subtle text-danger-emphasis px-3 py-2 small">
  <span class="pulse-dot" aria-hidden="true"></span>
  MARKET CLOSED
</div>
```

---

## 6. Interactive Filtering System Enhancements

### 6.1 Advanced Filter UI (Bootstrap 5 Offcanvas/Sidebar)

```html
<!-- Filter Panel (Desktop: Sidebar, Mobile: Offcanvas) -->
<aside class="filter-panel d-none d-lg-block bg-light p-3 border-end"
       style="width: 280px; max-height: 100vh; overflow-y: auto;">
  <h5 class="mb-3">Filters</h5>

  <!-- Ticker Filter -->
  <div class="filter-section mb-3">
    <h6 class="small text-uppercase text-muted mb-2">Instrument</h6>
    <div class="btn-group-vertical w-100 gap-2" role="group">
      <input type="radio" class="btn-check" name="ticker" id="ticker-all" value="all" checked>
      <label class="btn btn-outline-primary text-start" for="ticker-all">
        All Instruments
      </label>

      <input type="radio" class="btn-check" name="ticker" id="ticker-nqf" value="NQ=F">
      <label class="btn btn-outline-primary text-start" for="ticker-nqf">
        📈 NASDAQ-100 (NQ=F)
      </label>

      <input type="radio" class="btn-check" name="ticker" id="ticker-esf" value="ES=F">
      <label class="btn btn-outline-primary text-start" for="ticker-esf">
        📊 S&P 500 (ES=F)
      </label>

      <input type="radio" class="btn-check" name="ticker" id="ticker-ftse" value="^FTSE">
      <label class="btn btn-outline-primary text-start" for="ticker-ftse">
        🇬🇧 FTSE 100 (^FTSE)
      </label>
    </div>
  </div>

  <!-- Prediction Filter -->
  <div class="filter-section mb-3">
    <h6 class="small text-uppercase text-muted mb-2">Prediction</h6>
    <div class="btn-group-vertical w-100 gap-2" role="group">
      <input type="checkbox" class="btn-check" id="pred-bullish" value="BULLISH" checked>
      <label class="btn btn-outline-success text-start small" for="pred-bullish">
        📈 Bullish
      </label>

      <input type="checkbox" class="btn-check" id="pred-bearish" value="BEARISH" checked>
      <label class="btn btn-outline-danger text-start small" for="pred-bearish">
        📉 Bearish
      </label>

      <input type="checkbox" class="btn-check" id="pred-neutral" value="NEUTRAL" checked>
      <label class="btn btn-outline-secondary text-start small" for="pred-neutral">
        ➡️ Neutral
      </label>
    </div>
  </div>

  <!-- Confidence Filter -->
  <div class="filter-section mb-3">
    <h6 class="small text-uppercase text-muted mb-2">Min. Confidence</h6>
    <input type="range" class="form-range" id="confidence-slider" min="0" max="100" value="0" step="5">
    <div class="d-flex justify-content-between small text-muted mt-1">
      <span>0%</span>
      <span id="confidence-value" class="fw-bold text-primary">0%</span>
      <span>100%</span>
    </div>
  </div>

  <!-- Date Range Filter (History Page) -->
  <div class="filter-section mb-3">
    <h6 class="small text-uppercase text-muted mb-2">Date Range</h6>
    <div class="btn-group-vertical w-100 gap-2 small" role="group">
      <input type="radio" class="btn-check" name="daterange" id="range-today" value="today" checked>
      <label class="btn btn-outline-secondary text-start" for="range-today">Today</label>

      <input type="radio" class="btn-check" name="daterange" id="range-7days" value="7days">
      <label class="btn btn-outline-secondary text-start" for="range-7days">Last 7 Days</label>

      <input type="radio" class="btn-check" name="daterange" id="range-30days" value="30days">
      <label class="btn btn-outline-secondary text-start" for="range-30days">Last 30 Days</label>

      <input type="radio" class="btn-check" name="daterange" id="range-custom" value="custom">
      <label class="btn btn-outline-secondary text-start" for="range-custom">Custom Range</label>
    </div>

    <!-- Custom Date Picker (Hidden by default) -->
    <div class="mt-2" id="custom-date-picker" style="display: none;">
      <input type="date" class="form-control form-control-sm mb-2" id="date-from">
      <input type="date" class="form-control form-control-sm" id="date-to">
    </div>
  </div>

  <!-- Accuracy Filter -->
  <div class="filter-section mb-3">
    <h6 class="small text-uppercase text-muted mb-2">Accuracy Result</h6>
    <div class="btn-group-vertical w-100 gap-2 small" role="group">
      <input type="checkbox" class="btn-check" id="result-correct" value="correct" checked>
      <label class="btn btn-outline-success text-start" for="result-correct">
        ✓ Correct
      </label>

      <input type="checkbox" class="btn-check" id="result-wrong" value="wrong" checked>
      <label class="btn btn-outline-danger text-start" for="result-wrong">
        ✗ Wrong
      </label>

      <input type="checkbox" class="btn-check" id="result-pending" value="pending" checked>
      <label class="btn btn-outline-warning text-start" for="result-pending">
        ⏳ Pending
      </label>
    </div>
  </div>

  <!-- Filter Actions -->
  <div class="d-grid gap-2 mt-4">
    <button class="btn btn-primary btn-sm" id="apply-filters">Apply Filters</button>
    <button class="btn btn-outline-secondary btn-sm" id="reset-filters">Reset All</button>
  </div>

  <!-- Active Filters Display -->
  <div class="mt-3 pt-3 border-top" id="active-filters" style="display: none;">
    <h6 class="small text-muted mb-2">Active Filters</h6>
    <div id="filter-tags" class="d-flex flex-wrap gap-2"></div>
  </div>
</aside>

<!-- Mobile Filter Button (Offcanvas Trigger) -->
<button class="btn btn-outline-primary btn-sm d-lg-none" data-bs-toggle="offcanvas" 
        data-bs-target="#filterOffcanvas">
  🔽 Filters
</button>

<!-- Filter Offcanvas (Mobile) -->
<div class="offcanvas offcanvas-end" tabindex="-1" id="filterOffcanvas">
  <div class="offcanvas-header">
    <h5 class="offcanvas-title">Filters</h5>
    <button type="button" class="btn-close" data-bs-dismiss="offcanvas"></button>
  </div>
  <div class="offcanvas-body">
    <!-- Repeat filter sections here for mobile -->
  </div>
</div>
```

### 6.2 Filter Logic JavaScript

```javascript
/**
 * Filter Management System
 */
class FilterManager {
  constructor() {
    this.activeFilters = {
      ticker: 'all',
      predictions: ['BULLISH', 'BEARISH', 'NEUTRAL'],
      minConfidence: 0,
      dateRange: 'today',
      customDates: null,
      resultStatus: ['correct', 'wrong', 'pending']
    };

    this.init();
  }

  init() {
    // Bind filter change events
    document.querySelectorAll('[name="ticker"]').forEach(el => {
      el.addEventListener('change', () => this.updateFilter('ticker', el.value));
    });

    document.getElementById('confidence-slider')?.addEventListener('input', (e) => {
      document.getElementById('confidence-value').textContent = e.target.value + '%';
      this.updateFilter('minConfidence', parseInt(e.target.value));
    });

    // Date range filter
    document.querySelectorAll('[name="daterange"]').forEach(el => {
      el.addEventListener('change', () => {
        this.updateFilter('dateRange', el.value);
        document.getElementById('custom-date-picker').style.display =
          el.value === 'custom' ? 'block' : 'none';
      });
    });

    // Apply/Reset buttons
    document.getElementById('apply-filters')?.addEventListener('click', () => this.applyFilters());
    document.getElementById('reset-filters')?.addEventListener('click', () => this.resetFilters());

    // Load persisted filters from localStorage
    this.loadPersistedFilters();
  }

  /**
   * Update individual filter
   */
  updateFilter(key, value) {
    this.activeFilters[key] = value;
    this.displayActiveFilters();
  }

  /**
   * Apply all active filters to the dashboard
   */
  applyFilters() {
    const filtered = this.filterTickerCards();
    this.displayFilteredResults(filtered);
    this.persistFilters();
  }

  /**
   * Filter ticker cards based on active filters
   */
  filterTickerCards() {
    const cards = document.querySelectorAll('.ticker-card');
    return Array.from(cards).filter(card => {
      const ticker = card.dataset.ticker;
      const prediction = card.dataset.prediction;
      const confidence = parseFloat(card.dataset.confidence);

      // Check ticker filter
      if (this.activeFilters.ticker !== 'all' && ticker !== this.activeFilters.ticker) {
        return false;
      }

      // Check prediction filter
      if (!this.activeFilters.predictions.includes(prediction)) {
        return false;
      }

      // Check confidence filter
      if (confidence < this.activeFilters.minConfidence) {
        return false;
      }

      return true;
    });
  }

  /**
   * Display filtered results and hide others
   */
  displayFilteredResults(filteredCards) {
    document.querySelectorAll('.ticker-card').forEach(card => {
      card.style.display = filteredCards.includes(card) ? 'block' : 'none';
    });

    // Show empty state if no results
    if (filteredCards.length === 0) {
      this.showEmptyState('No predictions match your filters');
    } else {
      this.hideEmptyState();
    }
  }

  /**
   * Display active filter tags
   */
  displayActiveFilters() {
    const filterContainer = document.getElementById('filter-tags');
    if (!filterContainer) return;

    const tags = [];

    if (this.activeFilters.ticker !== 'all') {
      tags.push(`Ticker: ${this.activeFilters.ticker}`);
    }

    if (this.activeFilters.minConfidence > 0) {
      tags.push(`Confidence: ${this.activeFilters.minConfidence}%+`);
    }

    filterContainer.innerHTML = tags.map(tag =>
      `<span class="badge bg-primary">${tag} <button type="button" class="btn-close btn-close-white ms-1" aria-label="Remove"></button></span>`
    ).join('');
  }

  /**
   * Persist filters to localStorage
   */
  persistFilters() {
    localStorage.setItem('dashboardFilters', JSON.stringify(this.activeFilters));
  }

  /**
   * Load persisted filters from localStorage
   */
  loadPersistedFilters() {
    const persisted = localStorage.getItem('dashboardFilters');
    if (persisted) {
      this.activeFilters = { ...this.activeFilters, ...JSON.parse(persisted) };
      this.applyFilters();
    }
  }

  /**
   * Reset all filters
   */
  resetFilters() {
    this.activeFilters = {
      ticker: 'all',
      predictions: ['BULLISH', 'BEARISH', 'NEUTRAL'],
      minConfidence: 0,
      dateRange: 'today',
      customDates: null,
      resultStatus: ['correct', 'wrong', 'pending']
    };

    // Reset UI
    document.querySelectorAll('.btn-check').forEach(el => {
      el.checked = el.defaultChecked;
    });
    document.getElementById('confidence-slider').value = 0;
    document.getElementById('confidence-value').textContent = '0%';

    this.applyFilters();
    localStorage.removeItem('dashboardFilters');
  }

  showEmptyState(message) {
    let emptyEl = document.getElementById('empty-state');
    if (!emptyEl) {
      emptyEl = document.createElement('div');
      emptyEl.id = 'empty-state';
      document.querySelector('.ticker-grid').parentElement.appendChild(emptyEl);
    }
    emptyEl.innerHTML = `
      <div class="alert alert-info text-center py-5">
        <h5>No Results</h5>
        <p>${message}</p>
      </div>
    `;
  }

  hideEmptyState() {
    document.getElementById('empty-state')?.remove();
  }
}

// Initialize on page load
document.addEventListener('DOMContentLoaded', () => {
  new FilterManager();
});
```

---

## 7. Comprehensive Wireframes & Layout Improvements

### 7.1 Mobile Layout (320px - 480px)

```
┌─────────────────────────────────────────────────┐
│ 🌍 Global Predictor                         ☰   │ (Sticky Header/Navbar)
│ Next: 45s │ ●                                   │
└─────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────┐
│ 📈 NQ=F                         [LIVE] [FUTURES]│
│ NASDAQ-100                                      │
│                                                 │
│ 19,485.50 [+0.48%]                              │
│                                                 │
│ [📈 BULLISH]                     Next 1h        │
│ Prediction Confidence                           │
│ ███████████░░░░░░░░░ 78%                        │
│ Strong bullish confidence                       │
│                                                 │
│ │ Today │ │ Signals │                           │
│ │ 6/8   │ │ 7/9     │                           │
│ │ 75%   │ │         │                           │
│                                                 │
│ [+] View Details                                │
│                                                 │
│ 📊 Volatility: Moderate (±1.2%)                │
└─────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────┐
│ 📊 ES=F                         [LIVE] [FUTURES]│
│ S&P 500                                         │
│ ... (similar card)                              │
└─────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────┐
│ 🇬🇧 ^FTSE                       [OPEN] [INDEX]  │
│ FTSE 100                                        │
│ ... (similar card)                              │
└─────────────────────────────────────────────────┘

┌──┬──────────────────────────────┬──┬────────────┐
│📊│      Dashboard               │📈│   History  │ (Bottom Nav)
│  │                              │  │            │
│🔮│      Block Analysis          │📐│   Pivots   │
└──┴──────────────────────────────┴──┴────────────┘
```

### 7.2 Tablet Layout (768px)

```
┌────────────────────────────────────────────────────────────────┐
│ 🌍 Global Market Predictor              Status: ● LIVE 45s     │
└────────────────────────────────────────────────────────────────┘

┌─────────────────────────────┬─────────────────────────────┐
│  📈 NQ=F (NASDAQ-100)       │  📊 ES=F (S&P 500)          │
│  ┌───────────────────────┐  │  ┌───────────────────────┐  │
│  │ 19,485.50             │  │  │ 5,895.32              │  │
│  │ [📈 BULLISH] [LIVE]   │  │  │ [📈 BULLISH] [LIVE]   │  │
│  │                       │  │  │                       │  │
│  │ Confidence            │  │  │ Confidence            │  │
│  │ █████████░░░░ 78%     │  │  │ ██████░░░░░░ 65%      │  │
│  │                       │  │  │                       │  │
│  │ ┌─────────┬─────────┐ │  │  │ ┌─────────┬─────────┐ │  │
│  │ │Today    │Signals  │ │  │  │ │Today    │Signals  │ │  │
│  │ │6/8 75%  │7/9      │ │  │  │ │5/8 63%  │6/9      │ │  │
│  │ └─────────┴─────────┘ │  │  │ └─────────┴─────────┘ │  │
│  │                       │  │  │                       │  │
│  │ [+] View Details      │  │  │ [+] View Details      │  │
│  └───────────────────────┘  │  └───────────────────────┘  │
└─────────────────────────────┴─────────────────────────────┘

┌─────────────────────────────────────────────────────────────┐
│  🇬🇧 ^FTSE (FTSE 100)                                        │
│  ┌───────────────────────┐                                  │
│  │ 8,245.67              │                                  │
│  │ [📉 BEARISH] [OPEN]   │                                  │
│  │ Confidence: 55% (Moderate)                              │
│  │ [+] View Details      │                                  │
│  └───────────────────────┘                                  │
└─────────────────────────────────────────────────────────────┘
```

### 7.3 Desktop Layout (1024px+)

```
┌──────────────────────────────────────────────────────────────────────────────┐
│ 🌍 Global Market Predictor                    Status: ● LIVE (Next: 45s)     │
│ Multi-Asset Dashboard - Real-Time Predictions                                 │
└──────────────────────────────────────────────────────────────────────────────┘

┌─────────────────────────────────┐
│ FILTERS                         │  ┌────────────────────┬────────────────────┬────────────────────┐
│                                 │  │ 📈 NQ=F            │ 📊 ES=F            │ 🇬🇧 ^FTSE         │
│ Instrument                      │  │ NASDAQ-100         │ S&P 500            │ FTSE 100           │
│ ☑ All (4)                       │  │ ┌─────────────────┐│ ┌─────────────────┐│ ┌─────────────────┐│
│ ☑ NASDAQ (NQ=F)                 │  │ │ Price: 19,485.5 ││ │ Price: 5,895.32 ││ │ Price: 8,245.67 ││
│ ☑ S&P 500 (ES=F)                │  │ │                 ││ │                 ││ │                 ││
│ ☑ FTSE 100 (^FTSE)              │  │ │ Status: [LIVE]  ││ │ Status: [LIVE]  ││ │ Status: [OPEN]  ││
│                                 │  │ │                 ││ │                 ││ │                 ││
│ Prediction                      │  │ │ 📈 BULLISH      ││ │ 📈 BULLISH      ││ │ 📉 BEARISH      ││
│ ☑ Bullish                       │  │ │ Conf: 78%       ││ │ Conf: 65%       ││ │ Conf: 55%       ││
│ ☑ Bearish                       │  │ │                 ││ │                 ││ │                 ││
│ ☑ Neutral                       │  │ │ Today: 6/8 75%  ││ │ Today: 5/8 63%  ││ │ Today: 4/8 50%  ││
│                                 │  │ │ Signals: 7/9    ││ │ Signals: 6/9    ││ │ Signals: 4/9    ││
│ Min Confidence                  │  │ │                 ││ │                 ││ │                 ││
│ [0%] ────●─────── [100%]        │  │ │ [Details ▼]     ││ │ [Details ▼]     ││ │ [Details ▼]     ││
│ (Show: 0%+)                     │  │ └─────────────────┘│ └─────────────────┘│ └─────────────────┘│
│                                 │  └────────────────────┴────────────────────┴────────────────────┘
│ [Apply] [Reset]                 │
└─────────────────────────────────┘  ┌────────────────────────────────────────────────────────────┐
                                     │ EXPANDABLE DETAIL PANELS (Initially Hidden)                │
                                     │                                                            │
                                     │ • Reference Levels (Table)                                 │
                                     │ • Intraday Predictions (Tabs: 9am/10am Analysis)          │
                                     │ • 24h Prediction History (Scrollable Table)               │
                                     └────────────────────────────────────────────────────────────┘
```

### 7.4 Block Predictions Page Wireframe

```
MOBILE (Mobile-first):
┌──────────────────┐
│ 🔮 7-Block       │
│ Analysis         │
│ Intraday hourly  │
│ predictions      │
│                  │
│ [All Instruments]│ (Tab: selected)
│ [NQ=F]   [ES=F]  │
│ [^FTSE]          │
│                  │
│ ╔════════════════╗
│ ║ 9:00 AM ET     ║ (Block analysis for 1 hour)
│ ║ Early: BULLISH ║
│ ║ Strength: 75%  ║
│ ║                ║
│ ║ B1 B2 B3       ║ (7 blocks in 2 rows)
│ ║ B4 B5 B6       ║
│ ║ B7             ║
│ ║                ║
│ ║ Trend: UP      ║
│ ║ Deviation: +2σ ║
│ ║ Probability: 81%║
│ ╚════════════════╝
│                  │
│ (More hours...)  │
│                  │
│ Next prediction  │
│ in 8:42 minutes  │
└──────────────────┘

DESKTOP:
┌─────────────────────────────────────────────────────┐
│ 🔮 7-Block Prediction Analysis                      │
│ Intraday hourly predictions using block framework  │
│                                                     │
│ [All ▾] [NQ=F] [ES=F] [^FTSE]  (Tabs)             │
└─────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────┐
│ ⏱ Next Prediction Generation in 8:42               │
│ (Countdown timer with generating state)            │
└─────────────────────────────────────────────────────┘

┌──────────────────────────────────────────────────────────────────┐
│ 9:00 AM ET - NASDAQ-100 (NQ=F)                    Early: BULLISH │
│ ┌────────────────────────────────────────────────────────────┐  │
│ │ B1    B2    B3    B4    B5  | B6    B7                    │  │
│ │ ▓▓▓░  ▓▓▓░  ▓▓▓░  ▓▓░░  ▓░░░  ▓▓░░  ▓░░░                │  │
│ │ 19.5K 19.51K 19.52K 19.53K 19.54K 19.55K 19.56K           │  │
│ │ +0.2σ +0.5σ +0.8σ +1.2σ +1.5σ +1.2σ +0.9σ               │  │
│ │                                                            │  │
│ │ Legend: [═══ Analysis Period (1-5)] [- - Predict (6-7)]  │  │
│ └────────────────────────────────────────────────────────────┘  │
│                                                                  │
│ ┌────────────────────────────────────────────────────────────┐  │
│ │ Early Bias: BULLISH (75%)      Final Trend: UP            │  │
│ │ Deviation: +2.3 sigma         Probability: 81%            │  │
│ │ Strength Score: 0.81           Decision Path: U→U→U→D→U   │  │
│ └────────────────────────────────────────────────────────────┘  │
└──────────────────────────────────────────────────────────────────┘

(Repeat for each hour: 10am, 11am, 12pm, 1pm, 2pm, 3pm, 4pm)
```

---

## 8. Accessibility Compliance Checklist

### WCAG 2.1 AA Standards Implementation

```markdown
## Navigation & Structure
- [x] Use semantic HTML (header, nav, main, article, section, aside)
- [x] Proper heading hierarchy (h1, h2, h3... no skipped levels)
- [x] Landmark roles for page regions
- [x] Skip to main content link (for screen readers)
- [x] Consistent navigation patterns across pages

## Color & Contrast
- [x] Text contrast minimum 4.5:1 (normal), 3:1 (large)
- [x] Don't rely on color alone for meaning (use icons/patterns too)
- [x] Color-blind safe palette (avoid red/green only combinations)
- [x] Status indicators use icons + text + color

## Forms & Inputs
- [x] Label every form control (explicit association)
- [x] Error messages associated with inputs
- [x] Required field indicators
- [x] Keyboard-accessible date pickers
- [x] Error validation on submit (not on blur)

## Interactive Components
- [x] All clickable elements have min 44x44px touch target
- [x] Keyboard navigation (Tab, Shift+Tab, Enter, Space, Arrows)
- [x] Focus indicators visible (not just hover)
- [x] No keyboard traps
- [x] Modals/dialogs can be closed with Escape key

## Dynamic Content
- [x] ARIA live regions for real-time data updates
- [x] ARIA labels for icon-only buttons
- [x] Status messages announced to screen readers
- [x] Loading states indicated to assistive tech

## Media & Content
- [x] Data tables have headers (th, scope attribute)
- [x] Images have alt text (descriptive, not "image of...")
- [x] Charts have text alternatives or descriptions
- [x] Captions for any audio/video (future feature)

## Mobile Considerations
- [x] Responsive design works on all sizes
- [x] Readable font size (min 16px for body on mobile)
- [x] Touch-friendly spacing and controls
- [x] No horizontal scrolling for essential content
- [x] Orientation locking only when essential
```

---

## 9. Implementation Priority Roadmap

### Phase 1: Foundation (Week 1-2)
**Goal**: Establish design system and basic responsive improvements

- [ ] Create SCSS variable file for design tokens (colors, spacing, typography)
- [ ] Convert inline styles to utility classes (Bootstrap 5)
- [ ] Implement improved mobile breakpoints (2xs, xs, sm additions)
- [ ] Enhance confidence bar visualization (taller, better color coding)
- [ ] Add Bootstrap 5 card components to ticker cards
- [ ] Implement responsive navbar with offcanvas (mobile)

**Files to Create/Modify:**
- `static/scss/variables.scss` - Design tokens
- `static/scss/components.scss` - Component overrides
- `templates/base.html` - Layout template
- `static/css/styles.css` - Consolidated styles

### Phase 2: Component Redesign (Week 2-3)
**Goal**: Modernize card layouts and interactive components

- [ ] Redesign ticker card with Bootstrap card component structure
- [ ] Implement tabbed details panel (Reference Levels, Intraday, History)
- [ ] Enhanced market status indicator with spinner
- [ ] Improved confidence gauge with color transitions
- [ ] Responsive tables with card fallback for mobile
- [ ] Add ARIA labels and semantic HTML

**Files to Modify:**
- `templates/index.html`
- `static/js/app.js` - Update card rendering
- `static/css/styles.css` - Component styles

### Phase 3: Auto-Refresh & Real-Time (Week 3-4)
**Goal**: Improve data update mechanisms

- [ ] Implement `DashboardAutoRefresh` class with graceful updates
- [ ] Update countdown timer with better synchronization
- [ ] Add error handling and retry logic
- [ ] Implement smooth transitions on data changes
- [ ] Add loading skeleton screens
- [ ] Real-time status indicators (ARIA live regions)

**Files to Create/Modify:**
- `static/js/refresh-manager.js` - New auto-refresh system
- `static/js/app.js` - Integration
- `templates/index.html` - Skeleton screens

### Phase 4: Advanced Filtering (Week 4-5)
**Goal**: Implement filter system with persistence

- [ ] Build filter UI with sidebar/offcanvas pattern
- [ ] Implement `FilterManager` class
- [ ] Add localStorage persistence for filters
- [ ] Create filter tags/chips display
- [ ] Add date range picker
- [ ] Empty state UI for no results

**Files to Create/Modify:**
- `static/js/filter-manager.js` - New filter system
- `templates/index.html` - Filter UI
- `templates/history.html` - History filters

### Phase 5: Visual Enhancements (Week 5-6)
**Goal**: Add chart.js visualizations and micro-interactions

- [ ] Integrate Chart.js for confidence trends
- [ ] Add historical accuracy trend chart
- [ ] Implement reference level distance visualization
- [ ] Add micro-animations (confidence bar pulse, updates)
- [ ] Dark mode toggle with system preference detection
- [ ] Accessibility audit and fixes

**Files to Create/Modify:**
- `static/js/chart-manager.js` - Chart.js integration
- `static/css/animations.css` - Micro-interactions
- `templates/index.html`, `block_predictions.html`, `history.html`

### Phase 6: WebSocket Implementation (Week 6-7, Future)
**Goal**: Implement true real-time updates

- [ ] Setup Flask-SocketIO for WebSocket support
- [ ] Implement `WebSocketDashboard` class
- [ ] Incremental updates protocol
- [ ] Reconnection logic with exponential backoff
- [ ] Fallback to polling if WebSocket unavailable

**Files to Create/Modify:**
- `app.py` - Add SocketIO integration
- `static/js/websocket-dashboard.js` - New file

### Phase 7: Testing & Optimization (Week 7-8)
**Goal**: Ensure quality and performance

- [ ] Unit tests for FilterManager, DashboardAutoRefresh
- [ ] Responsive design testing (mobile, tablet, desktop)
- [ ] Accessibility testing with WAVE, Axe, NVDA
- [ ] Performance testing (Lighthouse, PageSpeed)
- [ ] Load testing for concurrent users
- [ ] Cross-browser compatibility

### Phase 8: Deployment & Monitoring (Week 8)
**Goal**: Roll out changes with monitoring

- [ ] Staging environment testing
- [ ] A/B testing (optional: old vs new UI)
- [ ] Analytics integration for UX metrics
- [ ] Error tracking (Sentry, etc.)
- [ ] Performance monitoring
- [ ] User feedback collection

---

## 10. Code Implementation Examples

### 10.1 Bootstrap 5 Card Component (index.html)

```html
<!-- Modernized Ticker Card using Bootstrap 5 -->
<article class="card card-prediction h-100 border-0 shadow-sm" 
         data-ticker="NQ=F" 
         data-prediction="BULLISH" 
         data-confidence="78"
         role="region" 
         aria-label="NQ=F NASDAQ Prediction">
  
  <!-- Card Header: Symbol & Market Status -->
  <div class="card-header bg-light border-bottom d-flex justify-content-between align-items-center">
    <div>
      <h3 class="h5 mb-0 d-flex align-items-center gap-2">
        <span aria-hidden="true">📈</span>
        <strong>NQ=F</strong>
        <span class="badge bg-info-subtle text-info-emphasis small">FUTURES</span>
      </h3>
      <p class="text-muted small mb-0">NASDAQ-100 E-mini Futures</p>
    </div>
    <span class="badge bg-success rounded-pill px-3 py-2 d-flex align-items-center gap-2">
      <span class="spinner-grow spinner-grow-sm" role="status" aria-label="Live"></span>
      OPEN
    </span>
  </div>

  <!-- Card Body: Data Display -->
  <div class="card-body">
    <!-- Price Section -->
    <div class="mb-4">
      <p class="text-muted small text-uppercase letter-spacing-sm mb-1">
        Current Price
      </p>
      <h2 class="h3 mb-2 d-flex justify-content-between align-items-baseline">
        <span class="price-value" data-field="price">19,485.50</span>
        <span class="badge bg-success-subtle text-success-emphasis small">+0.48%</span>
      </h2>
    </div>

    <!-- Prediction Section -->
    <div class="prediction-section mb-4">
      <h4 class="h6 text-uppercase text-muted letter-spacing-sm mb-2">
        Next Hour Prediction
      </h4>
      
      <div class="d-flex align-items-center gap-2 mb-3">
        <span class="badge bg-success-subtle text-success-emphasis py-2 px-3 fw-bold" 
              data-field="prediction">
          📈 BULLISH
        </span>
        <span class="small text-muted">(Next 1h)</span>
      </div>

      <!-- Enhanced Confidence Display -->
      <div class="confidence-display mb-3">
        <p class="text-muted small text-uppercase letter-spacing-sm mb-2">
          Prediction Confidence
        </p>
        <div class="progress mb-2" role="progressbar" aria-label="Prediction confidence: 78%">
          <div class="progress-bar bg-success gradient-pulse" style="width: 78%;">
            <span class="confidence-percentage fw-bold small text-white">78%</span>
          </div>
        </div>
        <p class="text-muted small mb-0">
          Strong bullish confidence with 7 out of 9 reference levels confirming bias
        </p>
      </div>

      <!-- Metrics Grid -->
      <div class="row g-2 mb-3">
        <div class="col-6">
          <div class="stat-card bg-light rounded p-3">
            <p class="text-muted small text-uppercase letter-spacing-sm mb-1">
              Today Accuracy
            </p>
            <p class="h6 mb-0">
              <strong data-metric="accuracy">6/8</strong>
              <span class="small text-success">(75%)</span>
            </p>
          </div>
        </div>
        <div class="col-6">
          <div class="stat-card bg-light rounded p-3">
            <p class="text-muted small text-uppercase letter-spacing-sm mb-1">
              Bullish Signals
            </p>
            <p class="h6 mb-0">
              <strong data-metric="signals">7/9</strong>
              <span class="small text-primary">signals</span>
            </p>
          </div>
        </div>
      </div>

      <!-- Volatility Info -->
      <div class="alert alert-info alert-sm small mb-0 d-flex justify-content-between align-items-center">
        <span>📊 <strong>Volatility:</strong> Moderate (±1.2%)</span>
        <span class="text-muted small">2 min ago</span>
      </div>
    </div>
  </div>

  <!-- Card Footer: Action Button -->
  <div class="card-footer bg-light border-top">
    <button class="btn btn-sm btn-outline-primary w-100" 
            type="button"
            data-bs-toggle="collapse" 
            data-bs-target="#details-NQ=F"
            aria-expanded="false"
            aria-controls="details-NQ=F">
      <span class="collapse-toggle-icon">+</span> View Details
    </button>
  </div>

  <!-- Collapsible Details Section -->
  <div class="collapse" id="details-NQ=F">
    <div class="card-body border-top">
      <!-- Tabbed Content -->
      <ul class="nav nav-tabs mb-3" role="tablist">
        <li class="nav-item" role="presentation">
          <button class="nav-link active" 
                  id="levels-tab-NQ=F" 
                  data-bs-toggle="tab" 
                  data-bs-target="#levels-NQ=F"
                  type="button" 
                  role="tab" 
                  aria-controls="levels-NQ=F"
                  aria-selected="true">
            Reference Levels
          </button>
        </li>
        <li class="nav-item" role="presentation">
          <button class="nav-link" 
                  id="intraday-tab-NQ=F" 
                  data-bs-toggle="tab" 
                  data-bs-target="#intraday-NQ=F"
                  type="button" 
                  role="tab" 
                  aria-controls="intraday-NQ=F"
                  aria-selected="false">
            Intraday (9am/10am)
          </button>
        </li>
        <li class="nav-item" role="presentation">
          <button class="nav-link" 
                  id="history-tab-NQ=F" 
                  data-bs-toggle="tab" 
                  data-bs-target="#history-NQ=F"
                  type="button" 
                  role="tab" 
                  aria-controls="history-NQ=F"
                  aria-selected="false">
            24h History
          </button>
        </li>
      </ul>

      <!-- Tab Content -->
      <div class="tab-content">
        <!-- Reference Levels Tab -->
        <div class="tab-pane fade show active" 
             id="levels-NQ=F" 
             role="tabpanel" 
             aria-labelledby="levels-tab-NQ=F">
          <div class="table-responsive">
            <table class="table table-sm table-hover table-striped mb-0">
              <thead class="table-light">
                <tr>
                  <th scope="col">Level</th>
                  <th scope="col">Price</th>
                  <th scope="col">Signal</th>
                  <th scope="col" class="text-end">Distance</th>
                </tr>
              </thead>
              <tbody>
                <tr>
                  <td><strong>Daily Open</strong></td>
                  <td><code class="small">19,450.00</code></td>
                  <td><span class="badge bg-success-subtle text-success">Bullish</span></td>
                  <td class="text-end"><code class="small">+35.50</code></td>
                </tr>
                <!-- More rows dynamically inserted -->
              </tbody>
            </table>
          </div>
        </div>

        <!-- Intraday Predictions Tab -->
        <div class="tab-pane fade" 
             id="intraday-NQ=F" 
             role="tabpanel" 
             aria-labelledby="intraday-tab-NQ=F">
          <!-- Intraday content -->
        </div>

        <!-- 24h History Tab -->
        <div class="tab-pane fade" 
             id="history-NQ=F" 
             role="tabpanel" 
             aria-labelledby="history-tab-NQ=F">
          <!-- History content -->
        </div>
      </div>

      <!-- Metadata -->
      <hr class="my-3">
      <p class="text-muted small text-center mb-0">
        Source: yfinance | Last update: <time datetime="2025-11-15T14:32:00">2 minutes ago</time>
      </p>
    </div>
  </div>
</article>
```

### 10.2 Responsive Navbar (Bootstrap 5 Offcanvas)

```html
<!-- Modern Sticky Navbar with Offcanvas Navigation -->
<nav class="navbar navbar-dark bg-gradient-primary shadow-sm sticky-top" 
     aria-label="Main navigation">
  <div class="container-fluid">
    <!-- Brand -->
    <a class="navbar-brand fw-bold h5 mb-0 text-white" href="/">
      <span aria-hidden="true">🌍</span>
      Global Market Predictor
    </a>

    <!-- Data Freshness Indicator (Desktop only) -->
    <div class="d-none d-md-flex align-items-center gap-3 text-white-50 small">
      <div class="d-flex align-items-center gap-2">
        <span class="status-dot fresh" role="status" aria-label="Data is fresh"></span>
        <span aria-live="polite" aria-atomic="true">
          <span id="countdown-timer">Next: 45s</span>
        </span>
      </div>
    </div>

    <!-- Navbar Toggler (Mobile only) -->
    <button class="navbar-toggler border-0" 
            type="button" 
            data-bs-toggle="offcanvas" 
            data-bs-target="#navbarOffcanvas"
            aria-controls="navbarOffcanvas"
            aria-label="Toggle navigation">
      <span class="navbar-toggler-icon"></span>
    </button>
  </div>

  <!-- Offcanvas Navigation (Mobile) -->
  <div class="offcanvas offcanvas-end" tabindex="-1" id="navbarOffcanvas" aria-labelledby="navbarOffcanvasLabel">
    <div class="offcanvas-header">
      <h5 class="offcanvas-title" id="navbarOffcanvasLabel">Navigation</h5>
      <button type="button" class="btn-close" data-bs-dismiss="offcanvas" aria-label="Close"></button>
    </div>
    <div class="offcanvas-body">
      <ul class="navbar-nav ms-auto">
        <li class="nav-item">
          <a class="nav-link active" href="/" aria-current="page">
            <span aria-hidden="true">📊</span> Dashboard
          </a>
        </li>
        <li class="nav-item">
          <a class="nav-link" href="/history">
            <span aria-hidden="true">📈</span> Prediction History
          </a>
        </li>
        <li class="nav-item">
          <a class="nav-link" href="/block-predictions">
            <span aria-hidden="true">🔮</span> Block Analysis
          </a>
        </li>
        <li class="nav-item">
          <a class="nav-link" href="/fibonacci-pivots">
            <span aria-hidden="true">📐</span> Fibonacci Pivots
          </a>
        </li>
      </ul>
    </div>
  </div>
</nav>

<!-- Bottom Navigation (Mobile only) - Sticky for easy navigation -->
<nav class="navbar navbar-light bg-light border-top fixed-bottom d-lg-none" 
     aria-label="Mobile bottom navigation">
  <div class="container-fluid d-flex justify-content-around">
    <a href="/" class="nav-link text-center small active" aria-current="page">
      <span class="d-block h5 mb-1">📊</span>
      <span class="d-block small">Dashboard</span>
    </a>
    <a href="/history" class="nav-link text-center small">
      <span class="d-block h5 mb-1">📈</span>
      <span class="d-block small">History</span>
    </a>
    <a href="/block-predictions" class="nav-link text-center small">
      <span class="d-block h5 mb-1">🔮</span>
      <span class="d-block small">Blocks</span>
    </a>
    <a href="/fibonacci-pivots" class="nav-link text-center small">
      <span class="d-block h5 mb-1">📐</span>
      <span class="d-block small">Pivots</span>
    </a>
  </div>
</nav>

<!-- Add padding to prevent content hiding behind fixed navbar -->
<style>
  @media (max-width: 991.98px) {
    body {
      padding-bottom: 60px; /* Height of bottom navbar */
    }
  }
</style>
```

---

## 11. Performance Optimization Recommendations

### 11.1 Front-End Performance

```javascript
// 1. Lazy Loading for Expandable Details
const observer = new IntersectionObserver((entries) => {
  entries.forEach(entry => {
    if (entry.isIntersecting) {
      loadDetailsPanel(entry.target);
      observer.unobserve(entry.target);
    }
  });
});

document.querySelectorAll('.collapse').forEach(el => {
  observer.observe(el);
});

// 2. Debounced Window Resize Handler
let resizeTimeout;
window.addEventListener('resize', () => {
  clearTimeout(resizeTimeout);
  resizeTimeout = setTimeout(() => {
    updateResponsiveLayout();
  }, 250); // Wait 250ms after resize stops
});

// 3. CSS Containment for Performance
.ticker-card {
  contain: layout style paint;
}

// 4. Resource Hints
<link rel="preconnect" href="https://cdn.jsdelivr.net">
<link rel="prefetch" href="/api/market-data">
<link rel="dns-prefetch" href="//fonts.googleapis.com">

// 5. Critical CSS Inlining
<style>
  /* Critical above-the-fold styles only */
  .header, .navbar, .ticker-grid { /* Critical */ }
</style>
```

### 11.2 Back-End API Optimization

```python
# Reduce payload size
@app.route('/api/market-data')
def get_market_data():
    # Only send changed fields
    return {
        'ticker': 'NQ=F',
        'current_price': 19485.50,
        'prediction': 'BULLISH',
        'confidence': 78.5,
        'updated_at': datetime.now().isoformat()
        # Don't send full data on every request
    }

# Implement caching
from flask_caching import Cache
cache = Cache(app, config={'CACHE_TYPE': 'simple'})

@app.route('/api/reference-levels/<ticker>')
@cache.cached(timeout=300)  # Cache for 5 minutes
def get_reference_levels(ticker):
    return reference_levels_service.get_levels(ticker)

# Pagination for large data sets
@app.route('/api/prediction-history/<ticker>')
def get_history(ticker):
    page = request.args.get('page', 1, type=int)
    per_page = request.args.get('per_page', 20, type=int)
    
    history = PredictionHistory.query.filter_by(ticker=ticker)\
        .paginate(page=page, per_page=per_page)
    
    return jsonify({
        'data': [h.to_dict() for h in history.items],
        'total': history.total,
        'pages': history.pages,
        'current_page': page
    })
```

---

## 12. Conclusion & Next Steps

### Summary of Recommendations

The NASDAQ Predictor dashboard has a solid foundation but requires modernization to meet 2025 UX standards. The primary improvements needed are:

1. **Design System**: Establish reusable design tokens and component library
2. **Responsive Design**: Implement mobile-first approach with better tablet support
3. **Visual Hierarchy**: Enhance confidence score prominence and visual communication
4. **Real-Time Updates**: Improve auto-refresh with graceful transitions and error handling
5. **Accessibility**: Ensure WCAG 2.1 AA compliance across all pages
6. **Filtering**: Add advanced filtering with state persistence
7. **Data Visualization**: Integrate Chart.js for trend visualization

### Immediate Action Items (High Priority)

1. **Week 1**: Create design system (variables.scss, design tokens)
2. **Week 2**: Redesign ticker cards with Bootstrap 5 components
3. **Week 3**: Implement improved auto-refresh mechanism
4. **Week 4**: Add filter system with localStorage persistence
5. **Week 5**: Visual enhancements (Chart.js integration, micro-animations)

### Estimated Effort

- **Design System & Foundation**: 1 week
- **Component Redesign**: 2 weeks
- **Auto-Refresh & Filtering**: 2 weeks
- **Visual Enhancements & Testing**: 2 weeks
- **Total**: 4-5 weeks for complete modernization

### Success Metrics

- Lighthouse Score: 85+
- Mobile usability: 95+ score
- Accessibility: WCAG 2.1 AA compliance
- Page load time: < 2 seconds
- User engagement: Track via analytics

---

**Report Generated**: November 15, 2025
**Reviewed By**: Claude Code - Senior UI/Frontend Architect
**Status**: Ready for Implementation

