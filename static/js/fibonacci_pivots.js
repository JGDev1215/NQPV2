/**
 * Global Market Predictor - Fibonacci Pivot Points Page
 * Displays Fibonacci-based support and resistance levels
 */

// Active tickers
const TICKERS = ['NQ=F', 'ES=F', '^FTSE'];
const TICKER_NAMES = {
    'NQ=F': 'NASDAQ-100 E-mini Futures',
    'ES=F': 'S&P 500 E-mini Futures',
    '^FTSE': 'FTSE 100 Index'
};

// Global data storage
let pivotData = {};

/**
 * Format price with proper decimal places
 */
function formatPrice(price) {
    if (price === null || price === undefined) return 'N/A';
    return price.toLocaleString('en-US', {
        minimumFractionDigits: 2,
        maximumFractionDigits: 2
    });
}

/**
 * Format distance value
 */
function formatDistance(distance) {
    if (distance === null || distance === undefined) return '';
    const sign = distance >= 0 ? '+' : '';
    return `${sign}${distance.toFixed(2)}`;
}

/**
 * Fetch Fibonacci pivot data for a ticker
 */
async function fetchFibonacciPivots(ticker) {
    try {
        // URL encode the ticker symbol (important for symbols with special chars like ^FTSE)
        const encodedTicker = encodeURIComponent(ticker);
        const response = await fetch(`/api/fibonacci-pivots/${encodedTicker}`);
        const result = await response.json();

        if (!result.success) {
            throw new Error(result.error || 'Failed to load pivot data');
        }

        // API response wraps data in a 'data' field, so extract it
        const pivotResponse = {
            ...result,
            timeframes: result.data  // Move 'data' to 'timeframes'
        };

        pivotData[ticker] = pivotResponse;
        return pivotResponse;
    } catch (error) {
        console.error(`Error fetching pivots for ${ticker}:`, error);
        throw error;
    }
}

/**
 * Render pivot ladder for a specific timeframe
 */
function renderPivotLadder(timeframeData, currentPrice) {
    if (!timeframeData || !timeframeData.available) {
        return `
            <div class="no-data-message">
                <strong>No pivot data available</strong>
                <p style="margin-top: 10px; font-size: 0.9rem;">
                    ${timeframeData?.error || 'Pivots will be calculated at the next scheduled job (daily at 00:05 UTC)'}
                </p>
            </div>
        `;
    }

    // Build array of all levels with metadata
    const levels = [
        {
            name: 'R3',
            fullName: 'Resistance 3 (100%)',
            price: timeframeData.resistance_3,
            type: 'resistance',
            level: 3
        },
        {
            name: 'R2',
            fullName: 'Resistance 2 (61.8%)',
            price: timeframeData.resistance_2,
            type: 'resistance',
            level: 2
        },
        {
            name: 'R1',
            fullName: 'Resistance 1 (38.2%)',
            price: timeframeData.resistance_1,
            type: 'resistance',
            level: 1
        },
        {
            name: 'PP',
            fullName: 'Pivot Point',
            price: timeframeData.pivot_point,
            type: 'pivot-point',
            level: 0
        },
        {
            name: 'S1',
            fullName: 'Support 1 (38.2%)',
            price: timeframeData.support_1,
            type: 'support',
            level: -1
        },
        {
            name: 'S2',
            fullName: 'Support 2 (61.8%)',
            price: timeframeData.support_2,
            type: 'support',
            level: -2
        },
        {
            name: 'S3',
            fullName: 'Support 3 (100%)',
            price: timeframeData.support_3,
            type: 'support',
            level: -3
        }
    ];

    // Calculate distances and find closest
    levels.forEach(level => {
        level.distance = currentPrice - level.price;
        level.absDistance = Math.abs(level.distance);
    });

    // Get closest 2 levels
    const closestLevelNames = timeframeData.closest_levels
        ? timeframeData.closest_levels.map(cl => cl.name)
        : [];

    // Build HTML
    let html = '<div class="pivot-ladder">';

    levels.forEach(level => {
        const isClosest = closestLevelNames.includes(level.name);
        const closestClass = isClosest ? 'closest' : '';

        html += `
            <div class="pivot-level ${level.type} ${closestClass}">
                <div class="level-name">
                    <span style="min-width: 50px;">${level.name}</span>
                    <span style="color: #6c757d; font-size: 0.85rem;">${level.fullName}</span>
                    ${isClosest ? '<span class="closest-badge">⭐ Closest</span>' : ''}
                </div>
                <div style="display: flex; align-items: center; gap: 15px;">
                    <span class="level-distance">${formatDistance(level.distance)}</span>
                    <span class="level-price">${formatPrice(level.price)}</span>
                </div>
            </div>
        `;
    });

    html += '</div>';

    // Add source data info
    const calcDate = new Date(timeframeData.calculation_date);
    html += `
        <div style="margin-top: 15px; padding: 12px; background: #f8f9fa; border-radius: 8px; font-size: 0.8rem; color: #6c757d;">
            <strong>Calculation Source:</strong><br>
            High: ${formatPrice(timeframeData.period_high)} |
            Low: ${formatPrice(timeframeData.period_low)} |
            Close: ${formatPrice(timeframeData.period_close)}<br>
            <strong>Updated:</strong> ${calcDate.toLocaleString()}
        </div>
    `;

    return html;
}

/**
 * Render all timeframes for a ticker
 */
function renderTickerPivots(ticker, data) {
    // Use querySelector with escaped ID for special characters
    const escapedTicker = CSS.escape(ticker);
    const container = document.querySelector(`#content-${escapedTicker}`);
    if (!container) return;

    const currentPrice = data.current_price;

    let html = `
        <!-- Current Price Banner -->
        <div class="current-price-banner">
            <div>
                <div class="current-price-label">${TICKER_NAMES[ticker]}</div>
                <div style="font-size: 0.85rem; color: #6c757d; margin-top: 5px;">Current Market Price</div>
            </div>
            <div class="current-price-value">${formatPrice(currentPrice)}</div>
        </div>
    `;

    // Daily Pivots
    html += `
        <div class="timeframe-section">
            <div class="timeframe-title">
                📅 Daily Pivots
            </div>
            ${renderPivotLadder(data.timeframes.daily, currentPrice)}
        </div>
    `;

    // Weekly Pivots
    html += `
        <div class="timeframe-section">
            <div class="timeframe-title">
                📆 Weekly Pivots
            </div>
            ${renderPivotLadder(data.timeframes.weekly, currentPrice)}
        </div>
    `;

    // Monthly Pivots
    html += `
        <div class="timeframe-section">
            <div class="timeframe-title">
                🗓️ Monthly Pivots
            </div>
            ${renderPivotLadder(data.timeframes.monthly, currentPrice)}
        </div>
    `;

    container.innerHTML = html;
}

/**
 * Show error message
 */
function showError(message) {
    const errorContainer = document.getElementById('error-container');
    errorContainer.innerHTML = `
        <div class="error-message">
            <h3>Error Loading Pivot Data</h3>
            <p>${message}</p>
            <button class="btn btn-primary" onclick="location.reload()">Retry</button>
        </div>
    `;
    errorContainer.style.display = 'block';
}

/**
 * Initialize tab switching
 */
function initializeTabs() {
    const tabs = document.querySelectorAll('.ticker-tab');

    tabs.forEach(tab => {
        tab.addEventListener('click', () => {
            const ticker = tab.getAttribute('data-ticker');

            // Update active tab
            tabs.forEach(t => t.classList.remove('active'));
            tab.classList.add('active');

            // Show corresponding content
            const contents = document.querySelectorAll('.ticker-content');
            contents.forEach(c => {
                c.classList.remove('active');
                c.style.display = 'none';
            });

            // Use querySelector with escaped ID for special characters
            const escapedTicker = CSS.escape(ticker);
            const targetContent = document.querySelector(`#content-${escapedTicker}`);
            if (targetContent) {
                targetContent.classList.add('active');
                targetContent.style.display = 'block';
            }
        });
    });
}

/**
 * Load pivot data for all tickers
 */
async function loadAllPivots() {
    try {
        console.log('Loading Fibonacci pivots for all tickers...');

        // Fetch data for all tickers in parallel
        const promises = TICKERS.map(ticker => fetchFibonacciPivots(ticker));
        const results = await Promise.all(promises);

        // Render each ticker
        TICKERS.forEach((ticker, index) => {
            if (results[index]) {
                renderTickerPivots(ticker, results[index]);
            }
        });

        // Hide loading, show first ticker content
        document.getElementById('loading').style.display = 'none';

        // Use querySelector with escaped ID for the first ticker
        const firstTicker = TICKERS[0];
        const escapedFirstTicker = CSS.escape(firstTicker);
        const firstContent = document.querySelector(`#content-${escapedFirstTicker}`);
        if (firstContent) {
            firstContent.style.display = 'block';
        }

        console.log('Fibonacci pivots loaded successfully');

    } catch (error) {
        console.error('Error loading pivots:', error);
        document.getElementById('loading').style.display = 'none';
        showError(error.message || 'Failed to load pivot data. Please try again later.');
    }
}

/**
 * Initialize the page
 */
function init() {
    console.log('Initializing Fibonacci Pivots page...');
    initializeTabs();
    loadAllPivots();
}

// Start when DOM is ready
if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', init);
} else {
    init();
}
