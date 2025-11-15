/**
 * Advanced filtering system for predictions dashboard
 *
 * Features:
 * - Filter by confidence level
 * - Filter by prediction direction (UP, DOWN, NEUTRAL)
 * - Filter by date range
 * - Real-time filter application
 * - Filter persistence (localStorage)
 * - Filter UI management
 */

class FilterManager {
    constructor(options = {}) {
        this.options = {
            storageKey: 'nqp_filters',
            ...options
        };

        this.filters = {
            confidence: { min: 0, max: 100 },
            direction: null,
            dateRange: { start: null, end: null }
        };

        this.callbacks = {
            onFilterChange: options.onFilterChange || (() => {})
        };

        this.loadFiltersFromStorage();
        this.initializeUI();
    }

    initializeUI() {
        this.createFilterPanel();
        this.attachEventListeners();
    }

    createFilterPanel() {
        const filterHtml = `
            <div class="card filter-panel" style="margin: 20px 0; padding: 20px; background: rgba(255, 255, 255, 0.05); border: 1px solid rgba(255, 255, 255, 0.1);">
                <h5 style="color: white; margin-bottom: 15px; font-weight: 600;">
                    🔍 Filters
                    <button id="clear-filters-btn" class="btn btn-sm btn-outline-danger" style="float: right;">Clear All</button>
                </h5>

                <div class="row">
                    <!-- Confidence Filter -->
                    <div class="col-md-4">
                        <label for="confidence-slider" style="color: rgba(255, 255, 255, 0.7); display: block; margin-bottom: 10px;">
                            Confidence: <span id="confidence-value" style="color: #00d4ff; font-weight: 600;">0%</span> - <span id="confidence-max-value" style="color: #00d4ff; font-weight: 600;">100%</span>
                        </label>
                        <div style="display: flex; gap: 10px;">
                            <input type="range" id="confidence-min" class="form-range" min="0" max="100" value="0" style="flex: 1;">
                            <input type="range" id="confidence-max" class="form-range" min="0" max="100" value="100" style="flex: 1;">
                        </div>
                    </div>

                    <!-- Direction Filter -->
                    <div class="col-md-4">
                        <label style="color: rgba(255, 255, 255, 0.7); display: block; margin-bottom: 10px;">Direction</label>
                        <div style="display: flex; gap: 8px;">
                            <button class="btn btn-sm direction-filter" data-direction="UP" style="flex: 1; background: rgba(76, 175, 80, 0.2); color: #4CAF50; border: 1px solid #4CAF50;">📈 UP</button>
                            <button class="btn btn-sm direction-filter" data-direction="DOWN" style="flex: 1; background: rgba(244, 67, 54, 0.2); color: #F44336; border: 1px solid #F44336;">📉 DOWN</button>
                            <button class="btn btn-sm direction-filter" data-direction="NEUTRAL" style="flex: 1; background: rgba(255, 193, 7, 0.2); color: #FFC107; border: 1px solid #FFC107;">➡️ NEUTRAL</button>
                            <button class="btn btn-sm direction-filter" data-direction="ALL" style="flex: 1; background: rgba(255, 255, 255, 0.1); color: white; border: 1px solid rgba(255, 255, 255, 0.3);">All</button>
                        </div>
                    </div>

                    <!-- Date Range Filter -->
                    <div class="col-md-4">
                        <label style="color: rgba(255, 255, 255, 0.7); display: block; margin-bottom: 10px;">Date Range</label>
                        <div style="display: flex; gap: 8px;">
                            <input type="date" id="date-start" class="form-control form-control-sm" style="flex: 1;">
                            <span style="color: rgba(255, 255, 255, 0.5); padding: 5px;">to</span>
                            <input type="date" id="date-end" class="form-control form-control-sm" style="flex: 1;">
                        </div>
                    </div>
                </div>

                <!-- Filter Summary -->
                <div id="filter-summary" style="margin-top: 15px; padding: 10px; background: rgba(255, 255, 255, 0.05); border-radius: 4px; color: rgba(255, 255, 255, 0.7); font-size: 0.9rem; display: none;">
                    Active filters: <span id="active-filters-list" style="color: #00d4ff; font-weight: 600;"></span>
                </div>
            </div>
        `;

        const container = document.querySelector('.container');
        if (container && !document.getElementById('filter-panel')) {
            const div = document.createElement('div');
            div.id = 'filter-panel';
            div.innerHTML = filterHtml;
            container.insertBefore(div, container.firstChild);
        }
    }

    attachEventListeners() {
        // Confidence slider listeners
        const minConfidence = document.getElementById('confidence-min');
        const maxConfidence = document.getElementById('confidence-max');
        const confidenceValue = document.getElementById('confidence-value');
        const confidenceMaxValue = document.getElementById('confidence-max-value');

        if (minConfidence && maxConfidence) {
            minConfidence.addEventListener('input', (e) => {
                this.filters.confidence.min = parseInt(e.target.value);
                confidenceValue.textContent = `${this.filters.confidence.min}%`;
                this.applyFilters();
            });

            maxConfidence.addEventListener('input', (e) => {
                this.filters.confidence.max = parseInt(e.target.value);
                confidenceMaxValue.textContent = `${this.filters.confidence.max}%`;
                this.applyFilters();
            });
        }

        // Direction filter listeners
        const directionButtons = document.querySelectorAll('.direction-filter');
        directionButtons.forEach(btn => {
            btn.addEventListener('click', () => {
                // Toggle selection
                const direction = btn.dataset.direction;

                if (direction === 'ALL') {
                    this.filters.direction = null;
                    directionButtons.forEach(b => b.style.opacity = '0.6');
                    btn.style.opacity = '1';
                } else {
                    this.filters.direction = this.filters.direction === direction ? null : direction;
                    directionButtons.forEach(b => {
                        if (b.dataset.direction === 'ALL') {
                            b.style.opacity = '0.6';
                        } else if (b.dataset.direction === this.filters.direction) {
                            b.style.opacity = '1';
                        } else {
                            b.style.opacity = '0.6';
                        }
                    });
                }

                this.applyFilters();
            });
        });

        // Date range listeners
        const dateStart = document.getElementById('date-start');
        const dateEnd = document.getElementById('date-end');

        if (dateStart && dateEnd) {
            dateStart.addEventListener('change', () => {
                this.filters.dateRange.start = dateStart.value;
                this.applyFilters();
            });

            dateEnd.addEventListener('change', () => {
                this.filters.dateRange.end = dateEnd.value;
                this.applyFilters();
            });
        }

        // Clear filters button
        const clearBtn = document.getElementById('clear-filters-btn');
        if (clearBtn) {
            clearBtn.addEventListener('click', () => this.clearFilters());
        }
    }

    applyFilters() {
        this.updateFilterSummary();
        this.callbacks.onFilterChange(this.filters);
        this.saveFiltersToStorage();
    }

    updateFilterSummary() {
        const summary = [];

        if (this.filters.confidence.min > 0 || this.filters.confidence.max < 100) {
            summary.push(`Confidence: ${this.filters.confidence.min}%-${this.filters.confidence.max}%`);
        }

        if (this.filters.direction) {
            summary.push(`Direction: ${this.filters.direction}`);
        }

        if (this.filters.dateRange.start || this.filters.dateRange.end) {
            const start = this.filters.dateRange.start || 'Any';
            const end = this.filters.dateRange.end || 'Any';
            summary.push(`Date: ${start} to ${end}`);
        }

        const summaryElement = document.getElementById('filter-summary');
        const summaryList = document.getElementById('active-filters-list');

        if (summary.length > 0) {
            summaryElement.style.display = 'block';
            summaryList.textContent = summary.join(' | ');
        } else {
            summaryElement.style.display = 'none';
        }
    }

    clearFilters() {
        this.filters = {
            confidence: { min: 0, max: 100 },
            direction: null,
            dateRange: { start: null, end: null }
        };

        // Reset UI
        const minConfidence = document.getElementById('confidence-min');
        const maxConfidence = document.getElementById('confidence-max');
        const confidenceValue = document.getElementById('confidence-value');
        const confidenceMaxValue = document.getElementById('confidence-max-value');
        const dateStart = document.getElementById('date-start');
        const dateEnd = document.getElementById('date-end');
        const directionButtons = document.querySelectorAll('.direction-filter');

        if (minConfidence) minConfidence.value = 0;
        if (maxConfidence) maxConfidence.value = 100;
        if (confidenceValue) confidenceValue.textContent = '0%';
        if (confidenceMaxValue) confidenceMaxValue.textContent = '100%';
        if (dateStart) dateStart.value = '';
        if (dateEnd) dateEnd.value = '';

        directionButtons.forEach(btn => {
            btn.style.opacity = btn.dataset.direction === 'ALL' ? '1' : '0.6';
        });

        this.applyFilters();
    }

    saveFiltersToStorage() {
        localStorage.setItem(this.options.storageKey, JSON.stringify(this.filters));
    }

    loadFiltersFromStorage() {
        const stored = localStorage.getItem(this.options.storageKey);
        if (stored) {
            this.filters = JSON.parse(stored);
        }
    }

    filterData(items) {
        return items.filter(item => {
            // Confidence filter
            const confidence = item.confidence || 0;
            if (confidence < this.filters.confidence.min || confidence > this.filters.confidence.max) {
                return false;
            }

            // Direction filter
            if (this.filters.direction && item.direction !== this.filters.direction) {
                return false;
            }

            // Date range filter
            if (this.filters.dateRange.start || this.filters.dateRange.end) {
                const itemDate = new Date(item.timestamp || item.created_at);
                if (this.filters.dateRange.start) {
                    const startDate = new Date(this.filters.dateRange.start);
                    if (itemDate < startDate) return false;
                }
                if (this.filters.dateRange.end) {
                    const endDate = new Date(this.filters.dateRange.end);
                    if (itemDate > endDate) return false;
                }
            }

            return true;
        });
    }

    getActiveFilterCount() {
        let count = 0;
        if (this.filters.confidence.min > 0 || this.filters.confidence.max < 100) count++;
        if (this.filters.direction) count++;
        if (this.filters.dateRange.start || this.filters.dateRange.end) count++;
        return count;
    }
}

// Initialize when DOM is ready
document.addEventListener('DOMContentLoaded', () => {
    window.filterManager = new FilterManager({
        onFilterChange: (filters) => {
            console.log('Filters changed:', filters);
            // Trigger data refresh with new filters
            if (typeof window.refreshDataWithFilters === 'function') {
                window.refreshDataWithFilters(filters);
            }
        }
    });

    console.log('Filter manager initialized');
});
