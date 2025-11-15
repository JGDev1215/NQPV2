/**
 * Global Market Predictor - 24-Hour History Page
 * Displays prediction history and reference levels for all instruments
 */

// Active instruments (matching main dashboard)
const TICKERS = ['NQ=F', 'ES=F', '^FTSE'];
const TICKER_NAMES = {
    'NQ=F': 'NASDAQ-100 E-mini Futures',
    'ES=F': 'S&P 500 E-mini Futures',
    '^FTSE': 'FTSE 100 Index'
};

// Global data storage
let marketData = {};
let predictionHistory = {};

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
 * Get timezone for a ticker symbol
 * @param {string} symbol - Ticker symbol
 * @returns {string} Timezone abbreviation
 */
function getTickerTimezoneSuffix(symbol) {
    return symbol === '^FTSE' ? 'GMT' : 'ET';
}

/**
 * Format time from hour number (0-23) to readable format with timezone
 */
function formatHour(hour, ticker) {
    const hour12 = hour === 0 ? 12 : (hour > 12 ? hour - 12 : hour);
    const ampm = hour < 12 ? 'AM' : 'PM';
    const tzAbbrev = ticker ? getTickerTimezoneSuffix(ticker) : 'ET';
    return `${hour12}:00 ${ampm} ${tzAbbrev}`;
}

/**
 * Fetch market data for reference levels
 */
async function fetchMarketData() {
    try {
        const response = await fetch('/api/data');
        const result = await response.json();

        if (result.error) {
            throw new Error(result.error);
        }

        marketData = result.data;
        return marketData;
    } catch (error) {
        console.error('Error fetching market data:', error);
        throw error;
    }
}

/**
 * Fetch prediction history for a ticker
 */
async function fetchPredictionHistory(ticker) {
    try {
        // URL encode the ticker symbol (important for symbols with special chars like ^FTSE)
        const encodedTicker = encodeURIComponent(ticker);
        const response = await fetch(`/api/predictions/${encodedTicker}/history-24h`);
        const result = await response.json();

        if (!result.success) {
            throw new Error(result.error || 'Failed to load history');
        }

        // API returns data in result.data (wrapped by ResponseHandler)
        const predictions = result.data || result.predictions || [];
        predictionHistory[ticker] = predictions;
        return predictions;
    } catch (error) {
        console.error(`Error fetching history for ${ticker}:`, error);
        return [];
    }
}

/**
 * Render reference levels table for a ticker
 */
function renderReferenceLevels(ticker, containerId) {
    const container = document.getElementById(containerId);
    if (!container) return;

    const tickerData = marketData[ticker];
    if (!tickerData || !tickerData.reference_levels) {
        container.innerHTML = '<p style="color: #6c757d;">No reference levels available</p>';
        return;
    }

    const levels = tickerData.reference_levels;
    const signals = tickerData.signals_detail || {};

    // Collect all levels
    const allLevels = [];

    // Single-price levels
    if (levels.single_price) {
        Object.entries(levels.single_price).forEach(([key, value]) => {
            if (value !== null && value !== undefined) {
                const signal = signals[key];
                allLevels.push({
                    name: formatLevelName(key),
                    type: 'single',
                    price: value,
                    signal: signal?.status || 'N/A',
                    distance: signal?.distance || null
                });
            }
        });
    }

    // Range-based levels
    if (levels.ranges) {
        Object.entries(levels.ranges).forEach(([key, range]) => {
            if (range && range.high !== null && range.low !== null) {
                const signal = signals[key];
                allLevels.push({
                    name: formatLevelName(key),
                    type: 'range',
                    high: range.high,
                    low: range.low,
                    signal: signal?.status || 'N/A',
                    distance: signal?.distance || null
                });
            }
        });
    }

    if (allLevels.length === 0) {
        container.innerHTML = '<p style="color: #6c757d;">No reference levels available</p>';
        return;
    }

    // Build table HTML
    let html = `
        <table class="history-table">
            <thead>
                <tr>
                    <th>Level Name</th>
                    <th>Price / Range</th>
                    <th>Signal</th>
                    <th>Distance</th>
                </tr>
            </thead>
            <tbody>
    `;

    allLevels.forEach(level => {
        const signalClass = level.signal.toLowerCase().replace(/\//g, '');

        let priceHtml;
        if (level.type === 'single') {
            priceHtml = `<span style="font-family: 'Courier New', monospace;">${formatPrice(level.price)}</span>`;
        } else {
            priceHtml = `
                <div style="font-family: 'Courier New', monospace; font-size: 0.85rem;">
                    <div style="color: #4caf50;">H: ${formatPrice(level.high)}</div>
                    <div style="color: #f44336;">L: ${formatPrice(level.low)}</div>
                </div>
            `;
        }

        const distanceHtml = level.distance !== null
            ? `<span style="font-family: 'Courier New', monospace;">${Math.abs(level.distance).toFixed(2)}</span>`
            : '-';

        html += `
            <tr>
                <td style="font-weight: 500;">${level.name}</td>
                <td>${priceHtml}</td>
                <td><span class="signal-badge ${signalClass}">${level.signal}</span></td>
                <td>${distanceHtml}</td>
            </tr>
        `;
    });

    html += `
            </tbody>
        </table>
    `;

    container.innerHTML = html;
}

/**
 * Render prediction history table for a ticker
 */
function renderPredictionHistory(ticker, containerId) {
    const container = document.getElementById(containerId);
    if (!container) return;

    const predictions = predictionHistory[ticker] || [];

    if (predictions.length === 0) {
        container.innerHTML = '<p style="color: #6c757d; text-align: center;">No predictions found for the last 24 hours</p>';
        return;
    }

    // Sort by target_hour descending (most recent first)
    const sortedPredictions = [...predictions].sort((a, b) => b.target_hour - a.target_hour);

    let html = `
        <table class="history-table">
            <thead>
                <tr>
                    <th>Time</th>
                    <th>Prediction</th>
                    <th>Confidence</th>
                    <th>Result</th>
                    <th>Price Change</th>
                    <th>Ref Open</th>
                    <th>Target Close</th>
                </tr>
            </thead>
            <tbody>
    `;

    sortedPredictions.forEach(pred => {
        const predIcon = pred.prediction === 'BULLISH' ? '📈' : '📉';
        const predClass = pred.prediction === 'BULLISH' ? 'bullish-pred' : 'bearish-pred';

        // Result badge
        let resultBadge = '<span class="history-result-badge result-pending">PENDING</span>';
        if (pred.actual_result === 'CORRECT') {
            resultBadge = '<span class="history-result-badge result-correct">✓ CORRECT</span>';
        } else if (pred.actual_result === 'WRONG') {
            resultBadge = '<span class="history-result-badge result-wrong">✗ WRONG</span>';
        }

        // Price change
        let priceChangeHtml = '-';
        if (pred.actual_price_change !== null && pred.actual_price_change !== undefined) {
            const changeClass = pred.actual_price_change >= 0 ? 'positive' : 'negative';
            const changeSign = pred.actual_price_change >= 0 ? '+' : '';
            priceChangeHtml = `<span class="history-price-change ${changeClass}" style="font-family: 'Courier New', monospace;">${changeSign}${pred.actual_price_change.toFixed(2)}</span>`;
        }

        html += `
            <tr>
                <td style="font-weight: 600; font-family: 'Courier New', monospace;">${formatHour(pred.target_hour, ticker)}</td>
                <td class="${predClass}" style="font-weight: 600;">${predIcon} ${pred.prediction}</td>
                <td style="font-weight: 600;">${pred.confidence.toFixed(1)}%</td>
                <td>${resultBadge}</td>
                <td>${priceChangeHtml}</td>
                <td style="font-family: 'Courier New', monospace;">${pred.reference_price !== null ? formatPrice(pred.reference_price) : '-'}</td>
                <td style="font-family: 'Courier New', monospace;">${pred.target_close_price !== null ? formatPrice(pred.target_close_price) : '-'}</td>
            </tr>
        `;
    });

    html += `
            </tbody>
        </table>
    `;

    container.innerHTML = html;
}

/**
 * Render combined view for all tickers
 */
function renderAllTickersView() {
    // Reference Levels - Combined
    const refLevelsContainer = document.getElementById('all-reference-levels');
    let refLevelsHtml = '';

    TICKERS.forEach(ticker => {
        refLevelsHtml += `
            <div style="margin-bottom: 30px;">
                <h4 style="color: #667eea; margin-bottom: 15px;">${TICKER_NAMES[ticker]}</h4>
                <div id="all-ref-${ticker}"></div>
            </div>
        `;
    });

    refLevelsContainer.innerHTML = refLevelsHtml;

    // Render each ticker's reference levels
    TICKERS.forEach(ticker => {
        renderReferenceLevels(ticker, `all-ref-${ticker}`);
    });

    // Predictions - Combined
    const predictionsContainer = document.getElementById('all-predictions');
    let predictionsHtml = '';

    TICKERS.forEach(ticker => {
        predictionsHtml += `
            <div style="margin-bottom: 30px;">
                <h4 style="color: #667eea; margin-bottom: 15px;">${TICKER_NAMES[ticker]}</h4>
                <div id="all-pred-${ticker}"></div>
            </div>
        `;
    });

    predictionsContainer.innerHTML = predictionsHtml;

    // Render each ticker's predictions
    TICKERS.forEach(ticker => {
        renderPredictionHistory(ticker, `all-pred-${ticker}`);
    });
}

/**
 * Format level name for display
 */
function formatLevelName(key) {
    const levelNames = {
        'daily_open_midnight': 'Daily Open (Midnight)',
        'ny_open_0830': '8:30 AM NY Open',
        'thirty_min_open': '30-Min Open',
        'ny_open_0700': '7:00 AM NY Open',
        'four_hour_open': '4-Hour Open',
        'weekly_open': 'Weekly Open',
        'hourly_open': 'Hourly Open',
        'previous_hourly_open': 'Previous Hour Open',
        'previous_week_open': 'Previous Week Open',
        'previous_day_high': 'Previous Day High',
        'previous_day_low': 'Previous Day Low',
        'monthly_open': 'Monthly Open',
        'range_0700_0715': '7:00-7:15 AM Range',
        'range_0830_0845': '8:30-8:45 AM Range',
        'asian_kill_zone': 'Asian Kill Zone',
        'london_kill_zone': 'London Kill Zone',
        'ny_am_kill_zone': 'NY AM Kill Zone',
        'ny_pm_kill_zone': 'NY PM Kill Zone'
    };

    return levelNames[key] || key.replace(/_/g, ' ').replace(/\b\w/g, l => l.toUpperCase());
}

/**
 * Export data to CSV
 */
function exportToCSV(ticker) {
    let csvContent = '';
    let filename = '';

    if (ticker === 'all') {
        // Export all tickers
        csvContent = 'Ticker,Time,Prediction,Confidence,Result,Price Change,Ref Open,Target Close\n';

        TICKERS.forEach(tick => {
            const predictions = predictionHistory[tick] || [];
            predictions.forEach(pred => {
                csvContent += `${tick},${formatHour(pred.target_hour)},${pred.prediction},${pred.confidence.toFixed(1)}%,${pred.actual_result || 'PENDING'},${pred.actual_price_change?.toFixed(2) || '-'},${pred.reference_price?.toFixed(2) || '-'},${pred.target_close_price?.toFixed(2) || '-'}\n`;
            });
        });

        filename = 'all_predictions_24h.csv';
    } else {
        // Export single ticker
        csvContent = 'Time,Prediction,Confidence,Result,Price Change,Ref Open,Target Close\n';

        const predictions = predictionHistory[ticker] || [];
        predictions.forEach(pred => {
            csvContent += `${formatHour(pred.target_hour)},${pred.prediction},${pred.confidence.toFixed(1)}%,${pred.actual_result || 'PENDING'},${pred.actual_price_change?.toFixed(2) || '-'},${pred.reference_price?.toFixed(2) || '-'},${pred.target_close_price?.toFixed(2) || '-'}\n`;
        });

        filename = `${ticker.replace(/[^a-zA-Z0-9]/g, '_')}_predictions_24h.csv`;
    }

    // Create download link
    const blob = new Blob([csvContent], { type: 'text/csv;charset=utf-8;' });
    const link = document.createElement('a');
    const url = URL.createObjectURL(blob);

    link.setAttribute('href', url);
    link.setAttribute('download', filename);
    link.style.visibility = 'hidden';

    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
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
            contents.forEach(c => c.classList.remove('active'));

            const targetContent = document.getElementById(`content-${ticker}`);
            if (targetContent) {
                targetContent.classList.add('active');
            }
        });
    });
}

/**
 * Load all data and render the page
 */
async function loadHistoryPage() {
    try {
        console.log('Loading 24-hour history page...');

        // Fetch market data
        await fetchMarketData();

        // Fetch prediction history for all tickers
        await Promise.all(TICKERS.map(ticker => fetchPredictionHistory(ticker)));

        // Render all views
        renderAllTickersView();

        TICKERS.forEach(ticker => {
            renderReferenceLevels(ticker, `${ticker}-reference-levels`);
            renderPredictionHistory(ticker, `${ticker}-predictions`);
        });

        // Hide loading, show content
        document.getElementById('loading').style.display = 'none';
        document.getElementById('content-all').style.display = 'block';

        console.log('History page loaded successfully');
    } catch (error) {
        console.error('Error loading history page:', error);
        document.getElementById('loading').innerHTML = `
            <div style="color: #dc3545; text-align: center;">
                <h3>Error Loading Data</h3>
                <p>${error.message}</p>
                <button class="btn btn-primary" onclick="location.reload()">Retry</button>
            </div>
        `;
    }
}

/**
 * Initialize the history page
 */
function init() {
    console.log('Initializing 24-hour history page...');
    initializeTabs();
    loadHistoryPage();
}

// Start when DOM is ready
if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', init);
} else {
    init();
}
