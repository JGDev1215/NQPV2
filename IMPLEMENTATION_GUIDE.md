# NASDAQ Predictor UI/UX Modernization - Implementation Guide

**Quick Reference for Developers**
**Duration**: 4-5 weeks
**Priority Level**: High
**Effort**: ~280 person-hours

---

## Quick Start Checklist

### Phase 1: Design System & Foundation (Week 1)
- [ ] Create `/static/scss/` directory structure
- [ ] Create `variables.scss` with design tokens
- [ ] Create `components.scss` for Bootstrap overrides
- [ ] Update `styles.css` to import SCSS files
- [ ] Add font-weight utilities to Bootstrap
- [ ] Test responsive breakpoints on actual devices

**Key Files to Create**:
```
static/scss/
├── _variables.scss      (Design tokens)
├── _components.scss     (Component styles)
├── _responsive.scss     (Responsive utilities)
├── _animations.scss     (Micro-interactions)
└── main.scss           (Aggregator - compiles to styles.css)
```

### Phase 2: Component Redesign (Week 2-3)
- [ ] Update `templates/index.html` - Ticker card redesign
- [ ] Update `templates/block_predictions.html` - Bootstrap navbar
- [ ] Update `templates/history.html` - Responsive tables
- [ ] Create `static/js/card-renderer.js` - Component rendering
- [ ] Add Bootstrap utilities: `d-none`, `d-md-block`, etc.
- [ ] Test on mobile/tablet/desktop browsers

**Key Files to Modify**:
```
templates/
├── index.html           (Landing dashboard)
├── block_predictions.html
├── history.html
└── fibonacci_pivots.html

static/js/
├── app.js              (Update: use new card renderer)
└── card-renderer.js    (New: Bootstrap card component logic)
```

### Phase 3: Auto-Refresh System (Week 3-4)
- [ ] Create `static/js/refresh-manager.js`
- [ ] Implement `DashboardAutoRefresh` class
- [ ] Add error handling and retry logic
- [ ] Create `static/css/animations.css` for transitions
- [ ] Test with throttled network (DevTools)
- [ ] Implement loading skeleton screens

**Key Files to Create**:
```
static/js/
├── refresh-manager.js   (New: Auto-refresh logic)
└── skeleton-loader.js   (New: Loading states)

static/css/
└── animations.css       (New: Micro-interactions)
```

### Phase 4: Filtering System (Week 4-5)
- [ ] Create `static/js/filter-manager.js`
- [ ] Implement `FilterManager` class
- [ ] Update `templates/index.html` - Add filter sidebar/offcanvas
- [ ] Add localStorage persistence
- [ ] Create filter UI components
- [ ] Test filter state persistence across page reloads

**Key Files to Create**:
```
static/js/
└── filter-manager.js    (New: Filter logic)

templates/
├── _filters.html        (New: Filter UI partial)
└── index.html          (Updated: integrate filters)
```

### Phase 5: Visual Enhancements (Week 5-6)
- [ ] Integrate Chart.js library
- [ ] Create `static/js/chart-manager.js`
- [ ] Add confidence trend chart
- [ ] Add accuracy trend chart
- [ ] Implement dark mode toggle
- [ ] Add accessibility ARIA labels

**Key Files to Create**:
```
static/js/
├── chart-manager.js     (New: Chart.js integration)
└── theme-manager.js     (New: Dark mode)

static/css/
└── dark-mode.css        (New: Dark theme variables)
```

---

## Implementation Details

### Design Tokens Reference

**Copy this into `static/scss/_variables.scss`:**

```scss
// ============================================
// COLOR PALETTE
// ============================================

// Primary Brand
$primary: #667eea;
$primary-dark: #5568d3;
$primary-light: #f0f4ff;

// Semantic Colors
$success: #10b981;
$success-light: #d1fae5;
$danger: #ef4444;
$danger-light: #fee2e2;
$warning: #f59e0b;
$warning-light: #fef3c7;
$info: #3b82f6;
$info-light: #dbeafe;

// Market Status
$market-open: #10b981;
$market-closed: #ef4444;
$market-premarket: #f59e0b;
$market-afterhours: #f59e0b;

// Confidence Levels
$confidence-low: #ef4444;
$confidence-mid: #f59e0b;
$confidence-high: #10b981;

// Grayscale
$gray-50: #f9fafb;
$gray-100: #f3f4f6;
$gray-200: #e5e7eb;
$gray-300: #d1d5db;
$gray-500: #6b7280;
$gray-700: #374151;
$gray-900: #111827;

// ============================================
// TYPOGRAPHY
// ============================================

$font-family-base: 'Inter', -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif;
$font-size-base: 0.9375rem;

$h1-font-size: 2.5rem;
$h2-font-size: 1.875rem;
$h3-font-size: 1.5rem;
$h4-font-size: 1.25rem;
$h5-font-size: 1rem;
$h6-font-size: 0.875rem;

// ============================================
// SPACING
// ============================================

$spacer: 1rem;

$spacing-xs: 0.25rem;
$spacing-sm: 0.5rem;
$spacing-md: 1rem;
$spacing-lg: 1.5rem;
$spacing-xl: 2rem;
$spacing-2xl: 3rem;

// ============================================
// BREAKPOINTS
// ============================================

$breakpoint-2xs: 320px;
$breakpoint-xs: 480px;
$breakpoint-sm: 640px;
$breakpoint-md: 768px;
$breakpoint-lg: 1024px;
$breakpoint-xl: 1280px;
$breakpoint-2xl: 1536px;

// ============================================
// SHADOWS
// ============================================

$box-shadow-sm: 0 1px 2px 0 rgb(0 0 0 / 0.05);
$box-shadow: 0 4px 6px -1px rgb(0 0 0 / 0.1);
$box-shadow-md: 0 10px 15px -3px rgb(0 0 0 / 0.1);
$box-shadow-lg: 0 20px 25px -5px rgb(0 0 0 / 0.1);

// ============================================
// BORDER RADIUS
// ============================================

$border-radius: 0.5rem;
$border-radius-lg: 0.75rem;
$border-radius-xl: 1rem;

// ============================================
// Z-INDEX
// ============================================

$zindex-dropdown: 1000;
$zindex-sticky: 1020;
$zindex-fixed: 1030;
$zindex-modal-backdrop: 1040;
$zindex-modal: 1050;
$zindex-popover: 1060;
$zindex-tooltip: 1070;
```

### Mobile-First Grid Strategy

**Copy this into `static/scss/_responsive.scss`:**

```scss
// ============================================
// RESPONSIVE GRID UTILITIES
// ============================================

// Ticker Grid (Cards)
.ticker-grid {
  display: grid;
  gap: 1rem;
  
  // 320px+ (default: single column)
  grid-template-columns: 1fr;
  
  // 480px+ (2 columns)
  @media (min-width: $breakpoint-xs) {
    grid-template-columns: repeat(2, 1fr);
  }
  
  // 768px+ (2 columns)
  @media (min-width: $breakpoint-md) {
    grid-template-columns: repeat(2, 1fr);
    gap: 1.25rem;
  }
  
  // 1024px+ (3 columns)
  @media (min-width: $breakpoint-lg) {
    grid-template-columns: repeat(auto-fit, minmax(380px, 1fr));
    gap: 1.5rem;
  }
}

// 7-Block Timeline Responsive
.blocks-timeline {
  // Mobile: 2 columns x 3.5 rows
  @media (max-width: $breakpoint-md) {
    display: grid;
    grid-template-columns: repeat(2, 1fr);
    gap: 0.5rem;
  }
  
  // Tablet & Desktop: Flex row
  @media (min-width: $breakpoint-lg) {
    display: flex;
    gap: 0.75rem;
  }
}

// Confidence Progress Bar Responsive
.progress {
  height: 2rem;
  
  @media (min-width: $breakpoint-md) {
    height: 2.5rem;
  }
}

// Table Responsive
.table-responsive {
  @media (max-width: $breakpoint-md) {
    // Hide table on mobile, show card layout
  }
}

// Padding Adjustments
.ticker-card {
  padding: 1rem;
  
  @media (min-width: $breakpoint-md) {
    padding: 1.25rem;
  }
  
  @media (min-width: $breakpoint-lg) {
    padding: 1.5rem;
  }
}
```

### Confidence Bar Enhancement

**Copy this into `static/css/components.css`:**

```css
/* Enhanced Confidence Progress Bar */
.progress {
  background-color: #e5e7eb;
  border-radius: 0.5rem;
  height: 2.5rem;
  overflow: hidden;
  position: relative;
}

.progress-bar {
  display: flex;
  align-items: center;
  justify-content: flex-start;
  padding: 0 1rem;
  transition: width 0.5s cubic-bezier(0.4, 0, 0.2, 1);
  background-size: 200% 200%;
}

/* Confidence Level Colors */
.progress-bar.confidence-low {
  background: linear-gradient(90deg, #ef4444, #f87171);
}

.progress-bar.confidence-mid {
  background: linear-gradient(90deg, #f59e0b, #fbbf24);
}

.progress-bar.confidence-high {
  background: linear-gradient(90deg, #10b981, #34d399);
}

/* Animated Gradient Pulse */
.progress-bar.gradient-pulse {
  animation: gradient-pulse 2s ease-in-out infinite;
}

@keyframes gradient-pulse {
  0%, 100% {
    background-position: 0% center;
  }
  50% {
    background-position: 100% center;
  }
}

/* Confidence Percentage Text */
.confidence-percentage {
  color: white;
  font-weight: 700;
  font-size: 0.9rem;
  text-shadow: 0 1px 2px rgba(0, 0, 0, 0.2);
  margin-left: auto;
  margin-right: 0.5rem;
}

/* Confidence Strength Badge */
.confidence-strength-badge {
  font-weight: 600;
  text-transform: uppercase;
  letter-spacing: 0.05em;
  font-size: 0.75rem;
}

.confidence-strength-badge.strong {
  background-color: #d1fae5;
  color: #047857;
}

.confidence-strength-badge.moderate {
  background-color: #fef3c7;
  color: #b45309;
}

.confidence-strength-badge.weak {
  background-color: #fee2e2;
  color: #b91c1c;
}
```

### Auto-Refresh Manager Implementation

**Create `static/js/refresh-manager.js`:**

```javascript
/**
 * Dashboard Auto-Refresh Manager
 * Handles graceful data updates with smooth transitions
 */

class DashboardAutoRefresh {
  constructor(options = {}) {
    this.refreshInterval = options.refreshInterval || 60000; // 60 seconds
    this.isRefreshing = false;
    this.nextRefreshTime = null;
    this.countdownInterval = null;
    this.lastSuccessfulFetch = null;
    this.retryCount = 0;
    this.maxRetries = 3;
  }

  /**
   * Initialize auto-refresh
   */
  async init() {
    console.log('[AutoRefresh] Initializing with interval:', this.refreshInterval);
    await this.fetchAndUpdateData();
    this.startCountdownTimer();
    this.scheduleNextRefresh();
  }

  /**
   * Fetch data and update UI gracefully
   */
  async fetchAndUpdateData() {
    if (this.isRefreshing) {
      console.log('[AutoRefresh] Refresh already in progress');
      return;
    }

    this.isRefreshing = true;
    this.updateStatusIndicator('loading');

    try {
      const response = await fetch('/api/market-data', {
        headers: {
          'Accept': 'application/json',
          'Cache-Control': 'no-cache'
        }
      });

      if (!response.ok) {
        throw new Error(`HTTP ${response.status}: ${response.statusText}`);
      }

      const data = await response.json();
      
      // Merge data with existing DOM (no full refresh)
      this.mergeAndUpdateCards(data);

      this.lastSuccessfulFetch = new Date();
      this.updateStatusIndicator('success');
      this.retryCount = 0;

      console.log('[AutoRefresh] Data updated at', this.lastSuccessfulFetch.toLocaleTimeString());

    } catch (error) {
      console.error('[AutoRefresh] Error:', error);
      this.handleError(error);
    } finally {
      this.isRefreshing = false;
    }
  }

  /**
   * Merge new data with existing cards (incremental update)
   */
  mergeAndUpdateCards(newData) {
    Object.entries(newData).forEach(([ticker, tickerData]) => {
      const card = document.querySelector(`[data-ticker="${ticker}"]`);
      if (!card) return;

      // Update only fields that changed
      this.updateCardField(card, 'price', tickerData.current_price);
      this.updateCardField(card, 'prediction', tickerData.prediction);
      this.updateConfidenceBar(card, tickerData.confidence, tickerData.prediction);
      this.updateMarketStatus(card, tickerData.market_status);
      this.updateMetrics(card, tickerData);
    });
  }

  /**
   * Update individual card field with animation
   */
  updateCardField(card, field, value) {
    const element = card.querySelector(`[data-field="${field}"]`);
    if (!element || element.textContent === String(value)) return;

    element.classList.add('updating');
    element.textContent = value;

    setTimeout(() => {
      element.classList.remove('updating');
    }, 300);
  }

  /**
   * Update confidence bar with smooth transition
   */
  updateConfidenceBar(card, confidence, prediction) {
    const bar = card.querySelector('.progress-bar');
    if (!bar) return;

    const newWidth = Math.min(100, confidence);
    const currentWidth = parseFloat(bar.style.width) || 0;

    if (newWidth !== currentWidth) {
      bar.style.width = newWidth + '%';
      
      // Update confidence color class
      bar.classList.remove('confidence-low', 'confidence-mid', 'confidence-high');
      if (newWidth < 50) {
        bar.classList.add('confidence-low');
      } else if (newWidth < 75) {
        bar.classList.add('confidence-mid');
      } else {
        bar.classList.add('confidence-high');
      }

      // Update percentage text
      const percentageEl = bar.querySelector('.confidence-percentage');
      if (percentageEl) {
        percentageEl.textContent = Math.round(newWidth) + '%';
      }
    }
  }

  /**
   * Update market status indicator
   */
  updateMarketStatus(card, status) {
    const statusEl = card.querySelector('.market-status-badge');
    if (!statusEl || statusEl.textContent === status) return;

    statusEl.textContent = status;
    statusEl.classList.remove('open', 'closed', 'premarket', 'afterhours');
    statusEl.classList.add(status.toLowerCase().replace(/[^a-z]/g, ''));
  }

  /**
   * Update quick metrics
   */
  updateMetrics(card, data) {
    if (data.daily_accuracy) {
      const { correct, wrong } = data.daily_accuracy;
      const total = correct + wrong;
      const rate = Math.round((correct / total) * 100);
      
      const accuracyEl = card.querySelector('[data-metric="accuracy"]');
      if (accuracyEl) {
        accuracyEl.textContent = `${correct}/${total}`;
        // Update nearby percentage display if exists
      }
    }
  }

  /**
   * Handle fetch error with retry logic
   */
  handleError(error) {
    this.updateStatusIndicator('error');

    if (this.retryCount < this.maxRetries) {
      this.retryCount++;
      const delay = Math.pow(2, this.retryCount) * 1000; // Exponential backoff
      console.log(`[AutoRefresh] Retrying in ${delay}ms (attempt ${this.retryCount}/${this.maxRetries})`);
      
      setTimeout(() => {
        this.fetchAndUpdateData();
      }, delay);
    } else {
      console.error('[AutoRefresh] Max retries exceeded');
      this.showErrorMessage('Failed to fetch market data. Please refresh the page.');
    }
  }

  /**
   * Start countdown timer display
   */
  startCountdownTimer() {
    if (this.countdownInterval) clearInterval(this.countdownInterval);

    this.countdownInterval = setInterval(() => {
      if (!this.nextRefreshTime) return;

      const now = Date.now();
      const secondsUntilRefresh = Math.ceil((this.nextRefreshTime - now) / 1000);

      if (secondsUntilRefresh > 0) {
        const display = `Next: ${secondsUntilRefresh}s`;
        const countdownEl = document.getElementById('countdown-timer');
        if (countdownEl) {
          countdownEl.textContent = display;
          
          // Add "imminent" class when < 10 seconds
          const refreshEl = document.getElementById('refresh-info');
          if (secondsUntilRefresh <= 10) {
            refreshEl?.classList.add('refresh-imminent');
          } else {
            refreshEl?.classList.remove('refresh-imminent');
          }
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
   * Update status indicator UI
   */
  updateStatusIndicator(state) {
    const dot = document.getElementById('data-freshness-dot');
    const badge = document.getElementById('update-type');
    const lastUpdate = document.getElementById('last-update-time');

    if (!dot) return;

    // Remove all status classes
    dot.classList.remove('fresh', 'moderate', 'stale', 'updating');

    switch (state) {
      case 'loading':
        dot.classList.add('updating');
        if (badge) badge.textContent = 'FETCHING...';
        break;

      case 'success':
        dot.classList.add('fresh');
        if (badge) badge.textContent = 'LIVE';
        if (lastUpdate && this.lastSuccessfulFetch) {
          lastUpdate.textContent = `Last: ${this.lastSuccessfulFetch.toLocaleTimeString()}`;
        }
        break;

      case 'error':
        dot.classList.add('stale');
        if (badge) badge.textContent = 'ERROR';
        break;
    }
  }

  /**
   * Display error message to user
   */
  showErrorMessage(message) {
    // Create toast notification
    const toast = document.createElement('div');
    toast.className = 'alert alert-danger alert-dismissible fade show position-fixed';
    toast.style.cssText = 'top: 20px; right: 20px; z-index: 1050; max-width: 400px;';
    toast.innerHTML = `
      ${message}
      <button type="button" class="btn-close" data-bs-dismiss="alert"></button>
    `;
    document.body.appendChild(toast);

    setTimeout(() => {
      toast.remove();
    }, 5000);
  }

  /**
   * Cleanup on page unload
   */
  destroy() {
    if (this.countdownInterval) {
      clearInterval(this.countdownInterval);
    }
    console.log('[AutoRefresh] Destroyed');
  }
}

// Initialize on page load
document.addEventListener('DOMContentLoaded', () => {
  const dashboard = new DashboardAutoRefresh({
    refreshInterval: 60000 // 60 seconds
  });

  dashboard.init();

  // Cleanup on unload
  window.addEventListener('beforeunload', () => {
    dashboard.destroy();
  });

  // Expose globally for debugging
  window.dashboardRefresh = dashboard;
});
```

### Filter Manager Implementation

**Create `static/js/filter-manager.js`:**

```javascript
/**
 * Dashboard Filter Manager
 * Handles filtering, state persistence, and UI updates
 */

class FilterManager {
  constructor() {
    this.activeFilters = {
      ticker: 'all',
      predictions: ['BULLISH', 'BEARISH', 'NEUTRAL'],
      minConfidence: 0,
      dateRange: 'today'
    };

    this.init();
  }

  /**
   * Initialize filter event listeners
   */
  init() {
    this.bindTickerFilters();
    this.bindPredictionFilters();
    this.bindConfidenceFilter();
    this.bindDateRangeFilter();
    this.bindButtonHandlers();
    this.loadPersistedFilters();
  }

  /**
   * Bind ticker filter radio buttons
   */
  bindTickerFilters() {
    document.querySelectorAll('[name="ticker"]').forEach(el => {
      el.addEventListener('change', (e) => {
        this.activeFilters.ticker = e.target.value;
        this.applyFilters();
      });
    });
  }

  /**
   * Bind prediction checkboxes
   */
  bindPredictionFilters() {
    const predictions = ['BULLISH', 'BEARISH', 'NEUTRAL'];
    predictions.forEach(pred => {
      const checkbox = document.getElementById(`pred-${pred.toLowerCase()}`);
      if (checkbox) {
        checkbox.addEventListener('change', () => {
          this.activeFilters.predictions = predictions.filter(p => {
            return document.getElementById(`pred-${p.toLowerCase()}`).checked;
          });
          this.applyFilters();
        });
      }
    });
  }

  /**
   * Bind confidence slider
   */
  bindConfidenceFilter() {
    const slider = document.getElementById('confidence-slider');
    const value = document.getElementById('confidence-value');

    if (slider) {
      slider.addEventListener('input', (e) => {
        this.activeFilters.minConfidence = parseInt(e.target.value);
        if (value) value.textContent = e.target.value + '%';
        this.applyFilters();
      });
    }
  }

  /**
   * Bind date range filter
   */
  bindDateRangeFilter() {
    document.querySelectorAll('[name="daterange"]').forEach(el => {
      el.addEventListener('change', (e) => {
        this.activeFilters.dateRange = e.target.value;
        
        // Show/hide custom date picker
        const customPicker = document.getElementById('custom-date-picker');
        if (customPicker) {
          customPicker.style.display = e.target.value === 'custom' ? 'block' : 'none';
        }
        
        this.applyFilters();
      });
    });
  }

  /**
   * Bind action buttons
   */
  bindButtonHandlers() {
    document.getElementById('apply-filters')?.addEventListener('click', () => {
      this.persistFilters();
    });

    document.getElementById('reset-filters')?.addEventListener('click', () => {
      this.resetFilters();
    });
  }

  /**
   * Apply all active filters to dashboard
   */
  applyFilters() {
    const filtered = this.filterTickerCards();
    this.displayFilteredResults(filtered);
    this.displayActiveFilterTags();
  }

  /**
   * Filter ticker cards based on active filters
   */
  filterTickerCards() {
    const cards = document.querySelectorAll('.ticker-card');
    return Array.from(cards).filter(card => {
      const ticker = card.dataset.ticker;
      const prediction = card.dataset.prediction?.toUpperCase();
      const confidence = parseFloat(card.dataset.confidence) || 0;

      // Ticker filter
      if (this.activeFilters.ticker !== 'all' && ticker !== this.activeFilters.ticker) {
        return false;
      }

      // Prediction filter
      if (prediction && !this.activeFilters.predictions.includes(prediction)) {
        return false;
      }

      // Confidence filter
      if (confidence < this.activeFilters.minConfidence) {
        return false;
      }

      return true;
    });
  }

  /**
   * Display/hide filtered results
   */
  displayFilteredResults(filteredCards) {
    document.querySelectorAll('.ticker-card').forEach(card => {
      if (filteredCards.includes(card)) {
        card.style.display = '';
        card.classList.remove('filtered-out');
      } else {
        card.style.display = 'none';
        card.classList.add('filtered-out');
      }
    });

    // Show empty state if needed
    if (filteredCards.length === 0) {
      this.showEmptyState('No predictions match your filters');
    } else {
      this.hideEmptyState();
    }
  }

  /**
   * Display active filter tags
   */
  displayActiveFilterTags() {
    const container = document.getElementById('active-filters');
    const tags = document.getElementById('filter-tags');

    if (!container || !tags) return;

    const activeFilterStrings = [];

    if (this.activeFilters.ticker !== 'all') {
      activeFilterStrings.push(`Ticker: ${this.activeFilters.ticker}`);
    }

    if (this.activeFilters.predictions.length < 3) {
      activeFilterStrings.push(`Predictions: ${this.activeFilters.predictions.join(', ')}`);
    }

    if (this.activeFilters.minConfidence > 0) {
      activeFilterStrings.push(`Confidence: ${this.activeFilters.minConfidence}%+`);
    }

    if (activeFilterStrings.length > 0) {
      container.style.display = 'block';
      tags.innerHTML = activeFilterStrings
        .map(tag => `<span class="badge bg-primary">${tag}</span>`)
        .join('');
    } else {
      container.style.display = 'none';
    }
  }

  /**
   * Persist filters to localStorage
   */
  persistFilters() {
    localStorage.setItem('dashboardFilters', JSON.stringify(this.activeFilters));
    console.log('[FilterManager] Filters persisted:', this.activeFilters);
  }

  /**
   * Load persisted filters from localStorage
   */
  loadPersistedFilters() {
    const persisted = localStorage.getItem('dashboardFilters');
    if (persisted) {
      this.activeFilters = { ...this.activeFilters, ...JSON.parse(persisted) };
      this.applyFilters();
      console.log('[FilterManager] Filters restored:', this.activeFilters);
    }
  }

  /**
   * Reset all filters to defaults
   */
  resetFilters() {
    this.activeFilters = {
      ticker: 'all',
      predictions: ['BULLISH', 'BEARISH', 'NEUTRAL'],
      minConfidence: 0,
      dateRange: 'today'
    };

    // Reset UI elements
    document.querySelectorAll('[name="ticker"]').forEach(el => {
      el.checked = el.value === 'all';
    });

    document.querySelectorAll('input[name="prediction"]').forEach(el => {
      el.checked = true;
    });

    const slider = document.getElementById('confidence-slider');
    if (slider) slider.value = 0;

    document.getElementById('confidence-value').textContent = '0%';

    this.applyFilters();
    localStorage.removeItem('dashboardFilters');
    console.log('[FilterManager] Filters reset');
  }

  /**
   * Show empty state message
   */
  showEmptyState(message) {
    let emptyEl = document.getElementById('empty-state');
    if (!emptyEl) {
      emptyEl = document.createElement('div');
      emptyEl.id = 'empty-state';
      emptyEl.className = 'col-12 mt-4';
      
      const grid = document.querySelector('.ticker-grid');
      if (grid && grid.parentElement) {
        grid.parentElement.appendChild(emptyEl);
      }
    }

    emptyEl.innerHTML = `
      <div class="alert alert-info text-center py-5">
        <h5>No Results Found</h5>
        <p class="text-muted mb-0">${message}</p>
      </div>
    `;
  }

  /**
   * Hide empty state message
   */
  hideEmptyState() {
    document.getElementById('empty-state')?.remove();
  }
}

// Initialize on page load
document.addEventListener('DOMContentLoaded', () => {
  const filterManager = new FilterManager();
  window.filterManager = filterManager; // Expose for debugging
});
```

---

## Testing Checklist

### Responsive Design Testing
- [ ] **Mobile (iPhone 12/13 - 390x844)**
  - [ ] Single column ticker layout
  - [ ] 7-block timeline stacks to 2 rows
  - [ ] Buttons/inputs remain 44x44px+ touch targets
  - [ ] No horizontal scrolling for essential content
  - [ ] Font sizes readable (min 16px body text)

- [ ] **Tablet (iPad - 810x1080)**
  - [ ] 2-column ticker grid
  - [ ] Full 7-block timeline visible
  - [ ] Filter sidebar converts to offcanvas
  - [ ] Table data readable

- [ ] **Desktop (1920x1080)**
  - [ ] 3-column ticker grid
  - [ ] Sidebar filter visible
  - [ ] All details panels render cleanly

### Functionality Testing
- [ ] Auto-refresh triggers every 60 seconds
- [ ] Countdown timer displays and updates correctly
- [ ] Filters persist across page reloads
- [ ] Confidence bar transitions smoothly
- [ ] Market status badge updates in real-time
- [ ] Error messages display on failed API calls
- [ ] Retry logic kicks in on network errors

### Accessibility Testing
- [ ] Keyboard navigation (Tab, Shift+Tab) works throughout
- [ ] Focus indicators visible on all interactive elements
- [ ] ARIA labels present for icon buttons
- [ ] Color contrast minimum 4.5:1 on all text
- [ ] Screen reader announces status updates
- [ ] Form labels properly associated with inputs

### Performance Testing
- [ ] Lighthouse score 85+
- [ ] First Contentful Paint < 1.5s
- [ ] Largest Contentful Paint < 2.5s
- [ ] Cumulative Layout Shift < 0.1
- [ ] Auto-refresh doesn't cause DOM thrashing

---

## Deployment Checklist

- [ ] All tests passing (unit, integration, e2e)
- [ ] Staging environment validated
- [ ] CSS/JS minified and optimized
- [ ] Cache headers configured properly
- [ ] Error tracking enabled (Sentry, etc.)
- [ ] Analytics instrumented
- [ ] Rollback plan documented
- [ ] Team trained on new components

---

## Quick Command Reference

```bash
# Compile SCSS to CSS
sass static/scss/main.scss static/css/styles.css

# Watch SCSS for changes
sass --watch static/scss:static/css

# Run performance audit
lighthouse http://localhost:5000

# Run accessibility audit
npx axe-core http://localhost:5000

# Run responsive design tests
npm run test:responsive
```

---

## Key Metrics to Track

After deployment, monitor these metrics:

- **User Engagement**: Time on page, interaction rates
- **Performance**: Page load time, interaction to paint
- **Conversion**: Click-through rates on key actions
- **Errors**: JavaScript errors, failed API calls
- **Accessibility**: Screen reader usage, keyboard navigation patterns
- **Mobile**: Device/OS breakdown, screen size distribution

---

**Document Updated**: November 15, 2025
**Status**: Ready for Implementation

