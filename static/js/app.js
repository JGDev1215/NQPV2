/**
 * Global Market Predictor - Main Application JavaScript
 * Handles data fetching, rendering, and user interactions
 */

// Ticker configuration with metadata
const TICKER_CONFIG = {
    'NQ=F': { name: 'NASDAQ-100 E-mini Futures (NQ=F)', type: 'futures', icon: '📈', category: 'us-futures' },
    'ES=F': { name: 'S&P 500 E-mini Futures (ES=F)', type: 'futures', icon: '📊', category: 'us-futures' },
    '^FTSE': { name: 'FTSE 100 (^FTSE)', type: 'index', icon: '🇬🇧', category: 'indices' }

    // ============================================
    // CRYPTOCURRENCY TICKERS - ON ICE
    // Backend code remains functional but not displayed in UI
    // ============================================
    // 'BTC-USD': { name: 'Bitcoin (BTC-USD)', type: 'crypto', icon: '₿', category: 'crypto' },
    // 'SOL-USD': { name: 'Solana (SOL-USD)', type: 'crypto', icon: '◎', category: 'crypto' },
    // 'ADA-USD': { name: 'Cardano (ADA-USD)', type: 'crypto', icon: '₳', category: 'crypto' }
};

/**
 * Format price with proper decimal places
 * @param {number} price - Price to format
 * @returns {string} Formatted price string
 */
function formatPrice(price) {
    if (price === null || price === undefined) return 'N/A';
    return price.toLocaleString('en-US', {
        minimumFractionDigits: 2,
        maximumFractionDigits: 2
    });
}

/**
 * Create HTML for a ticker card
 * @param {string} symbol - Ticker symbol
 * @param {object} data - Ticker data from API
 * @returns {string} HTML string for the card
 */
function createTickerCard(symbol, data) {
    // Handle error states
    if (!data || data.error) {
        return `
            <div class="ticker-card error-card">
                <strong>${symbol}</strong>
                <br>Error: ${data?.error || 'No data available'}
            </div>
        `;
    }

    const config = TICKER_CONFIG[symbol] || {
        name: symbol,
        type: 'unknown',
        icon: '📉',
        category: 'other'
    };

    const predictionClass = data.prediction === 'BULLISH' ? 'bullish' : 'bearish';
    const marketStatusClass = data.market_status.toLowerCase().replace(/[^a-z]/g, '');
    const confidenceWidth = Math.min(100, data.confidence);
    const predictionIcon = data.prediction === 'BULLISH' ? '📈' : '📉';

    return `
        <div class="ticker-card">
            <div class="ticker-header">
                <div class="ticker-symbol">
                    <span class="ticker-icon">${config.icon}</span>
                    ${symbol}
                    <span class="ticker-type-badge ${config.type}">${config.type}</span>
                </div>
                <span class="market-status-badge ${marketStatusClass}">${data.market_status}</span>
            </div>

            <div class="ticker-name">${config.name}</div>
            <div class="ticker-price">${formatPrice(data.current_price)}</div>

            <span class="prediction-badge ${predictionClass}">
                ${predictionIcon} ${data.prediction}
            </span>

            <div class="confidence-bar-container">
                <div class="confidence-bar ${predictionClass}" style="width: ${confidenceWidth}%;">
                    <span class="confidence-value">${data.confidence.toFixed(1)}%</span>
                </div>
            </div>

            <div class="quick-metrics">
                <div class="metric-box" title="Bullish signals out of total reference levels analyzed">
                    <div class="metric-label">Signals ℹ️</div>
                    <div class="metric-value">${data.bullish_count}/${data.total_signals}</div>
                </div>
                <div class="metric-box" title="Weighted prediction score (0-1 scale). Higher = more bullish">
                    <div class="metric-label">Score ℹ️</div>
                    <div class="metric-value">${data.weighted_score.toFixed(2)}</div>
                </div>
                ${data.daily_accuracy && ['NQ=F', 'ES=F', 'BTC-USD', '^FTSE'].includes(symbol) ? `
                    <div class="metric-box daily-accuracy" title="Today's prediction accuracy: correct predictions / total verified predictions">
                        <div class="metric-label">Today ℹ️</div>
                        <div class="metric-value">${data.daily_accuracy.correct}/${data.daily_accuracy.correct + data.daily_accuracy.wrong} (${data.daily_accuracy.accuracy_rate.toFixed(0)}%)</div>
                    </div>
                ` : ''}
            </div>

            ${data.volatility ? `
                <div class="volatility-indicator ${data.volatility.level.toLowerCase()}" title="Hourly price movement range as percentage. Higher = more volatile market">
                    📊 Volatility: ${data.volatility.level} (±${data.volatility.hourly_range_pct}%) ℹ️
                </div>
            ` : ''}

            <div class="signal-summary">
                <strong>Key Levels:</strong>
                ${data.midnight_open ? `Midnight: ${formatPrice(data.midnight_open)}` : ''}
                ${data.ny_open ? `| NY Open: ${formatPrice(data.ny_open)}` : ''}
            </div>

            <button class="expand-btn" onclick="toggleDetails('${symbol}')">
                <span id="${symbol}-toggle-text">View Details</span>
            </button>

            <div class="details-panel" id="${symbol}-details">
                ${createReferenceLevelsTable(data.reference_levels, data.signals_detail, symbol)}
                ${createIntradayPredictionsTable(data.intraday_predictions, symbol)}
                ${createPredictionHistoryTable(data.daily_accuracy, symbol)}

                <p style="font-size: 0.75rem; color: #6c757d; text-align: center; margin-top: 15px;">
                    Source: ${data.source || 'yfinance'} |
                    ${data.data_age_minutes ? `Data age: ${data.data_age_minutes.toFixed(1)}min` : 'Fresh data'}
                </p>
            </div>
        </div>
    `;
}

/**
 * Format reference levels table HTML
 * @param {object} referenceLevels - Reference levels data from API
 * @param {object} signalsDetail - Signals detail for each level
 * @param {string} symbol - Ticker symbol
 * @returns {string} HTML string for reference levels table
 */
function createReferenceLevelsTable(referenceLevels, signalsDetail, symbol) {
    if (!referenceLevels) return '';

    const levels = [];

    // Level names mapping
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

    // Helper to check if a level is a kill zone
    const isKillZone = (key) => {
        return key.includes('kill_zone');
    };

    // Process single-price levels
    if (referenceLevels.single_price) {
        Object.entries(referenceLevels.single_price).forEach(([key, value]) => {
            if (value !== null && value !== undefined) {
                const signal = signalsDetail?.[key];
                levels.push({
                    name: levelNames[key] || key,
                    type: 'single',
                    price: value,
                    signal: signal?.status || 'N/A',
                    distance: signal?.distance || null,
                    isKillZone: isKillZone(key)
                });
            }
        });
    }

    // Process range-based levels
    if (referenceLevels.ranges) {
        Object.entries(referenceLevels.ranges).forEach(([key, range]) => {
            if (range && range.high !== null && range.low !== null) {
                const signal = signalsDetail?.[key];
                levels.push({
                    name: levelNames[key] || key,
                    type: 'range',
                    high: range.high,
                    low: range.low,
                    signal: signal?.status || 'N/A',
                    distance: signal?.distance || null,
                    isKillZone: isKillZone(key)
                });
            }
        });
    }

    if (levels.length === 0) return '';

    let html = `
        <div class="reference-levels-container">
            <h4 style="margin: 0 0 10px 0; font-size: 0.85rem; color: #495057;">
                📊 Reference Levels (${levels.length})
            </h4>
            <table class="reference-levels-table">
                <thead>
                    <tr>
                        <th>Level</th>
                        <th>Price</th>
                        <th>Signal</th>
                        <th>Distance</th>
                    </tr>
                </thead>
                <tbody>
    `;

    levels.forEach((level, index) => {
        const rowClasses = [
            index >= 5 ? 'hidden-row' : '',
            level.isKillZone ? 'kill-zone' : ''
        ].filter(c => c).join(' ');
        const signalClass = level.signal.toLowerCase();

        let priceHtml;
        if (level.type === 'single') {
            priceHtml = `<span class="level-price">${formatPrice(level.price)}</span>`;
        } else {
            priceHtml = `
                <div class="level-range">
                    <span class="range-high">H: ${formatPrice(level.high)}</span>
                    <span class="range-low">L: ${formatPrice(level.low)}</span>
                </div>
            `;
        }

        const distanceHtml = level.distance !== null
            ? `<span class="distance-value">${Math.abs(level.distance).toFixed(2)}</span>`
            : '<span class="distance-value">-</span>';

        html += `
            <tr class="${rowClasses}" id="${symbol}-level-${index}">
                <td class="level-name">${level.name}</td>
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

    if (levels.length > 5) {
        html += `
            <button class="show-more-btn" onclick="toggleReferenceLevels('${symbol}')">
                <span id="${symbol}-toggle-levels-text">Show All ${levels.length} Levels</span>
            </button>
        `;
    }

    html += `</div>`;

    return html;
}

/**
 * Toggle reference levels visibility
 * @param {string} symbol - Ticker symbol
 */
function toggleReferenceLevels(symbol) {
    // Escape special characters in symbol for CSS selectors (e.g., 'ES=F', '^FTSE')
    const escapedSymbol = CSS.escape(symbol);

    const hiddenRows = document.querySelectorAll(`#${escapedSymbol}-details .hidden-row`);
    const toggleText = document.getElementById(`${escapedSymbol}-toggle-levels-text`);

    const isShowing = hiddenRows[0]?.classList.contains('show');

    hiddenRows.forEach(row => {
        if (isShowing) {
            row.classList.remove('show');
        } else {
            row.classList.add('show');
        }
    });

    if (toggleText) {
        const totalLevels = document.querySelectorAll(`#${escapedSymbol}-details .reference-levels-table tbody tr`).length;
        toggleText.textContent = isShowing
            ? `Show All ${totalLevels} Levels`
            : 'Show Less';
    }
}

/**
 * Create intraday predictions table HTML (9am and 10am predictions)
 * @param {object} eodPredictions - End-of-day predictions data from API
 * @param {string} symbol - Ticker symbol
 * @returns {string} HTML string for intraday predictions table
 */
function createIntradayPredictionsTable(eodPredictions, symbol) {
    if (!eodPredictions) return '';

    let html = `
        <div class="intraday-predictions-container">
            <h4 style="margin: 0 0 10px 0; font-size: 0.85rem; color: #495057;">
                ⏰ Intraday Predictions (9am/10am)
            </h4>
            <table class="intraday-predictions-table">
                <thead>
                    <tr>
                        <th>Window</th>
                        <th>Prediction</th>
                        <th>Confidence</th>
                        <th>Status</th>
                        <th>Result</th>
                        <th>Ref Open</th>
                        <th>Target Close</th>
                    </tr>
                </thead>
                <tbody>
    `;

    // 9am prediction row
    if (eodPredictions.nine_am) {
        const pred = eodPredictions.nine_am;
        const predIcon = pred.prediction === 'BULLISH' ? '📈' : '📉';
        const predClass = pred.prediction === 'BULLISH' ? 'bullish-pred' : 'bearish-pred';
        const statusClass = `status-${pred.status.toLowerCase().replace('_', '-')}`;

        let resultBadge = '-';
        if (pred.actual_result === 'CORRECT') {
            resultBadge = '<span class="result-badge result-correct">✓ CORRECT</span>';
        } else if (pred.actual_result === 'WRONG') {
            resultBadge = '<span class="result-badge result-wrong">✗ WRONG</span>';
        }

        html += `
            <tr>
                <td class="window-label">9am → 10am</td>
                <td class="${predClass}">${predIcon} ${pred.prediction}</td>
                <td>
                    <div class="confidence-display">
                        <strong>${pred.confidence.toFixed(1)}%</strong>
                        ${pred.decay_factor < 1.0 ? `<small style="display:block;color:#888;">(×${pred.decay_factor.toFixed(2)})</small>` : ''}
                    </div>
                </td>
                <td><span class="prediction-status-badge ${statusClass}">${pred.status}</span></td>
                <td>${resultBadge}</td>
                <td>${pred.reference_open !== null ? formatPrice(pred.reference_open) : '-'}</td>
                <td>${pred.target_close !== null ? formatPrice(pred.target_close) : '-'}</td>
            </tr>
        `;
    }

    // 10am prediction row
    if (eodPredictions.ten_am) {
        const pred = eodPredictions.ten_am;
        const predIcon = pred.prediction === 'BULLISH' ? '📈' : '📉';
        const predClass = pred.prediction === 'BULLISH' ? 'bullish-pred' : 'bearish-pred';
        const statusClass = `status-${pred.status.toLowerCase().replace('_', '-')}`;

        let resultBadge = '-';
        if (pred.actual_result === 'CORRECT') {
            resultBadge = '<span class="result-badge result-correct">✓ CORRECT</span>';
        } else if (pred.actual_result === 'WRONG') {
            resultBadge = '<span class="result-badge result-wrong">✗ WRONG</span>';
        }

        html += `
            <tr>
                <td class="window-label">10am → 11am</td>
                <td class="${predClass}">${predIcon} ${pred.prediction}</td>
                <td>
                    <div class="confidence-display">
                        <strong>${pred.confidence.toFixed(1)}%</strong>
                        ${pred.decay_factor < 1.0 ? `<small style="display:block;color:#888;">(×${pred.decay_factor.toFixed(2)})</small>` : ''}
                    </div>
                </td>
                <td><span class="prediction-status-badge ${statusClass}">${pred.status}</span></td>
                <td>${resultBadge}</td>
                <td>${pred.reference_open !== null ? formatPrice(pred.reference_open) : '-'}</td>
                <td>${pred.target_close !== null ? formatPrice(pred.target_close) : '-'}</td>
            </tr>
        `;
    }

    html += `
                </tbody>
            </table>
            <div class="prediction-meta" style="margin-top: 8px; font-size: 0.7rem; color: #6c757d; text-align: center;">
                Current Window: <strong>${eodPredictions.current_time_window || 'N/A'}</strong>
                ${eodPredictions.predictions_locked ?
                  ` | 🔒 Locked at ${eodPredictions.predictions_locked_at}` :
                  ' | 🔓 Active'}
            </div>
        </div>
    `;

    return html;
}

/**
 * Toggle details panel for a ticker
 * @param {string} symbol - Ticker symbol
 */
function toggleDetails(symbol) {
    const panel = document.getElementById(`${symbol}-details`);
    const toggleText = document.getElementById(`${symbol}-toggle-text`);

    if (panel.classList.contains('show')) {
        panel.classList.remove('show');
        toggleText.textContent = 'View Details';
    } else {
        panel.classList.add('show');
        toggleText.textContent = 'Hide Details';
    }
}

/**
 * Create prediction history table HTML (24-hour history with verification)
 * @param {object} dailyAccuracy - Daily accuracy stats
 * @param {string} symbol - Ticker symbol
 * @returns {string} HTML string for the prediction history table
 */
function createPredictionHistoryTable(dailyAccuracy, symbol) {
    // Only show history for NQ=F, ES=F, BTC-USD, ^FTSE
    if (!['NQ=F', 'ES=F', 'BTC-USD', '^FTSE'].includes(symbol)) {
        return '';
    }

    // Always show the history container - data will be loaded asynchronously
    // dailyAccuracy only shows TODAY's predictions, but 24h endpoint has yesterday's data too

    // Determine accuracy badge class (from today's data if available)
    const accuracyRate = (dailyAccuracy && dailyAccuracy.accuracy_rate) || 0;
    let accuracyClass = '';
    if (accuracyRate >= 70) {
        accuracyClass = 'high-accuracy';
    } else if (accuracyRate < 50) {
        accuracyClass = 'low-accuracy';
    }

    // Format accuracy display (today only)
    let accuracyDisplay = 'No data today';
    if (dailyAccuracy && dailyAccuracy.total > 0) {
        const verified = dailyAccuracy.correct + dailyAccuracy.wrong;
        accuracyDisplay = verified > 0
            ? `${accuracyRate.toFixed(1)}% (${dailyAccuracy.correct}/${verified})`
            : 'Pending';
    }

    let html = `
        <div class="prediction-history-container">
            <div class="history-header">
                <h4 class="history-title">📊 24-Hour Prediction History</h4>
                <div class="history-accuracy-badge ${accuracyClass}">
                    Today's Accuracy: ${accuracyDisplay}
                </div>
            </div>

            <div id="${symbol}-history-loading" style="text-align: center; color: white; padding: 20px;">
                <div class="spinner-border spinner-border-sm" role="status">
                    <span class="visually-hidden">Loading...</span>
                </div>
                <p style="margin-top: 10px; font-size: 0.8rem;">Loading prediction history...</p>
            </div>

            <div id="${symbol}-history-content" style="display: none;"></div>
        </div>
    `;

    // Fetch history data asynchronously
    setTimeout(() => fetchPredictionHistory(symbol), 100);

    return html;
}

/**
 * Get timezone for a ticker symbol
 * @param {string} symbol - Ticker symbol
 * @returns {string} Timezone identifier
 */
function getTickerTimezone(symbol) {
    const TIMEZONE_MAP = {
        'NQ=F': 'America/New_York',  // US indices display in NY time
        'ES=F': 'America/New_York',
        '^FTSE': 'Europe/London'      // UK indices display in UK time
    };
    return TIMEZONE_MAP[symbol] || 'America/New_York';
}

/**
 * Format hour with timezone-specific display
 * @param {number} hour - Hour (0-23)
 * @param {string} symbol - Ticker symbol for timezone
 * @returns {string} Formatted hour with timezone
 */
function formatHourWithTimezone(hour, symbol) {
    const hour12 = hour === 0 ? 12 : (hour > 12 ? hour - 12 : hour);
    const ampm = hour < 12 ? 'AM' : 'PM';

    // Get timezone abbreviation
    const timezone = getTickerTimezone(symbol);
    const tzAbbrev = timezone === 'Europe/London' ? 'GMT' : 'ET';

    return `${hour12}:00 ${ampm} ${tzAbbrev}`;
}

/**
 * Fetch and render prediction history for a ticker
 * @param {string} symbol - Ticker symbol
 */
function fetchPredictionHistory(symbol) {
    // URL encode the ticker symbol (important for symbols with special chars like ^FTSE)
    const encodedSymbol = encodeURIComponent(symbol);
    fetch(`/api/predictions/${encodedSymbol}/history-24h`)
        .then(response => response.json())
        .then(result => {
            if (!result.success) {
                throw new Error(result.error || 'Failed to load history');
            }

            // API returns data in result.data (wrapped by ResponseHandler)
            const predictions = result.data || result.predictions || [];
            renderPredictionHistoryTable(symbol, predictions);
        })
        .catch(error => {
            console.error(`Error fetching history for ${symbol}:`, error);
            const loadingDiv = document.getElementById(`${symbol}-history-loading`);
            if (loadingDiv) {
                loadingDiv.innerHTML = `<p style="color: #ffffff; text-align: center;">Failed to load history</p>`;
            }
        });
}

/**
 * Render prediction history table with data
 * @param {string} symbol - Ticker symbol
 * @param {array} predictions - Array of prediction objects
 */
function renderPredictionHistoryTable(symbol, predictions) {
    const loadingDiv = document.getElementById(`${symbol}-history-loading`);
    const contentDiv = document.getElementById(`${symbol}-history-content`);

    if (!contentDiv) return;

    if (predictions.length === 0) {
        contentDiv.innerHTML = '<p style="text-align: center; color: white;">No predictions found today.</p>';
        loadingDiv.style.display = 'none';
        contentDiv.style.display = 'block';
        return;
    }

    // Separate market hours from extended hours (timezone-aware)
    const isMarketHour = (hour, symbol) => {
        if (symbol === '^FTSE') return hour >= 8 && hour <= 16;  // 8am-4pm GMT for UK
        return hour >= 9 && hour <= 16;  // 9am-4pm ET for US
    };

    const keyPredictions = predictions.filter(p => isMarketHour(p.target_hour, symbol));
    const otherPredictions = predictions.filter(p => !isMarketHour(p.target_hour, symbol));

    let htmlOutput = '';

    // Render Key Predictions (Market Hours) if they exist
    if (keyPredictions.length > 0) {
        htmlOutput += `
            <div class="key-predictions-section" style="margin-bottom: 20px;">
                <h5 style="color: #ffc107; margin-bottom: 12px; font-size: 0.9rem;">⭐ Market Hours Predictions</h5>
                <div class="key-predictions-grid" style="display: grid; grid-template-columns: repeat(auto-fit, minmax(200px, 1fr)); gap: 12px;">
        `;

        keyPredictions.forEach(pred => {
            const predIcon = pred.prediction === 'BULLISH' ? '📈' : '📉';
            const predClass = pred.prediction === 'BULLISH' ? 'bullish-pred' : 'bearish-pred';

            let resultBadge = '<span class="history-result-badge result-pending" style="font-size: 0.7rem;">PENDING</span>';
            if (pred.actual_result === 'CORRECT') {
                resultBadge = '<span class="history-result-badge result-correct" style="font-size: 0.7rem;">✓ CORRECT</span>';
            } else if (pred.actual_result === 'WRONG') {
                resultBadge = '<span class="history-result-badge result-wrong" style="font-size: 0.7rem;">✗ WRONG</span>';
            }

            const hourLabel = formatHourWithTimezone(pred.target_hour, symbol);

            htmlOutput += `
                <div class="key-prediction-card" style="background: rgba(255,255,255,0.05); border-radius: 8px; padding: 12px; border: 1px solid rgba(255,255,255,0.1);">
                    <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 8px;">
                        <span style="font-weight: 600; color: #ffc107; font-size: 0.85rem;">${hourLabel}</span>
                        ${resultBadge}
                    </div>
                    <div class="${predClass}" style="font-size: 1.1rem; font-weight: 600; margin-bottom: 6px;">
                        ${predIcon} ${pred.prediction}
                    </div>
                    <div style="font-size: 0.75rem; color: #aaa;">
                        Confidence: <strong>${pred.confidence.toFixed(1)}%</strong>
                    </div>
                </div>
            `;
        });

        htmlOutput += `
                </div>
            </div>
        `;
    }

    // Render Extended Hours Table (non-market hours)
    if (otherPredictions.length > 0) {
        htmlOutput += `
            <div class="other-predictions-section">
                <h5 style="color: #aaa; margin-bottom: 12px; font-size: 0.85rem;">📋 Extended Hours (0-23 Full Coverage)</h5>
                <table class="prediction-history-table">
                    <thead>
                        <tr>
                            <th>Hour</th>
                            <th>Prediction</th>
                            <th>Conf</th>
                            <th>Result</th>
                            <th>Change</th>
                        </tr>
                    </thead>
                    <tbody>
        `;

        otherPredictions.forEach((pred, index) => {
            const predIcon = pred.prediction === 'BULLISH' ? '📈' : '📉';
            const predClass = pred.prediction === 'BULLISH' ? 'bullish-pred' : 'bearish-pred';

            // Result badge
            let resultBadge = '<span class="history-result-badge result-pending">PENDING</span>';
            if (pred.actual_result === 'CORRECT') {
                resultBadge = '<span class="history-result-badge result-correct">✓</span>';
            } else if (pred.actual_result === 'WRONG') {
                resultBadge = '<span class="history-result-badge result-wrong">✗</span>';
            }

            // Price change
            let priceChangeHtml = '-';
            if (pred.actual_price_change !== null && pred.actual_price_change !== undefined) {
                const changeClass = pred.actual_price_change >= 0 ? 'positive' : 'negative';
                const changeSign = pred.actual_price_change >= 0 ? '+' : '';
                priceChangeHtml = `<span class="history-price-change ${changeClass}">${changeSign}${pred.actual_price_change.toFixed(2)}</span>`;
            }

            // Hide rows after the first 12
            const rowClass = index >= 12 ? 'history-hidden-row' : '';

            // Format hour label with timezone
            const hourLabel = formatHourWithTimezone(pred.target_hour, symbol);

            htmlOutput += `
                <tr class="${rowClass}">
                    <td class="history-time">${hourLabel}</td>
                    <td class="history-prediction ${predClass}">${predIcon} ${pred.prediction}</td>
                    <td class="history-confidence">${pred.confidence.toFixed(1)}%</td>
                    <td>${resultBadge}</td>
                    <td>${priceChangeHtml}</td>
                </tr>
            `;
        });

        htmlOutput += `
                    </tbody>
                </table>
        `;

        // Add "Show More" button if there are more than 12 predictions
        if (otherPredictions.length > 12) {
            htmlOutput += `
                <button class="show-more-history-btn" onclick="togglePredictionHistory('${symbol}')">
                    <span id="${symbol}-toggle-history-text">Show All ${otherPredictions.length} Predictions ▼</span>
                </button>
            `;
        }

        htmlOutput += `
            </div>
        `;
    }

    contentDiv.innerHTML = htmlOutput;
    loadingDiv.style.display = 'none';
    contentDiv.style.display = 'block';
}

/**
 * Toggle prediction history visibility (show/hide additional rows)
 * @param {string} symbol - Ticker symbol
 */
function togglePredictionHistory(symbol) {
    const escapedSymbol = CSS.escape(symbol);
    const hiddenRows = document.querySelectorAll(`#${escapedSymbol}-history-content .history-hidden-row`);
    const toggleText = document.getElementById(`${escapedSymbol}-toggle-history-text`);

    if (!hiddenRows.length) return;

    const isShowing = hiddenRows[0].classList.contains('show');

    hiddenRows.forEach(row => {
        if (isShowing) {
            row.classList.remove('show');
        } else {
            row.classList.add('show');
        }
    });

    if (toggleText) {
        const totalRows = document.querySelectorAll(`#${escapedSymbol}-history-content .prediction-history-table tbody tr`).length;
        toggleText.textContent = isShowing
            ? `Show All ${totalRows} Predictions ▼`
            : 'Show Less ▲';
    }
}

/**
 * Render all tickers into their respective sections
 * @param {object} data - All ticker data from API
 */
function renderTickers(data) {
    const usFuturesGrid = document.getElementById('us-futures-grid');
    const indicesGrid = document.getElementById('indices-grid');
    const cryptoGrid = document.getElementById('crypto-grid');

    if (usFuturesGrid) usFuturesGrid.innerHTML = '';
    if (indicesGrid) indicesGrid.innerHTML = '';
    if (cryptoGrid) cryptoGrid.innerHTML = '';

    Object.keys(data).forEach(symbol => {
        const config = TICKER_CONFIG[symbol];
        if (!config) return;

        const card = createTickerCard(symbol, data[symbol]);

        if (config.category === 'us-futures' && usFuturesGrid) {
            usFuturesGrid.innerHTML += card;
        } else if (config.category === 'indices' && indicesGrid) {
            indicesGrid.innerHTML += card;
        } else if (config.category === 'crypto' && cryptoGrid) {
            cryptoGrid.innerHTML += card;
        }
    });
}

/**
 * Global state for intelligent refresh
 */
let refreshState = {
    countdownSeconds: 0,
    nextRefreshTime: null,
    nextUpdateType: null,
    countdownInterval: null,
    refreshTimeout: null,
    dataFreshness: 'fresh',
    lastDataTimestamp: null
};

/**
 * Update data freshness indicator
 */
function updateFreshnessIndicator(freshness, dataAge) {
    const indicator = document.getElementById('data-freshness-dot');
    const lastUpdateElement = document.getElementById('last-update-time');

    if (indicator) {
        indicator.className = `status-indicator ${freshness}`;
    }

    if (lastUpdateElement && dataAge !== null) {
        const ageMinutes = Math.floor(dataAge / 60);
        const ageSeconds = Math.floor(dataAge % 60);
        if (ageMinutes > 0) {
            lastUpdateElement.textContent = `Last: ${ageMinutes}m ${ageSeconds}s ago`;
        } else {
            lastUpdateElement.textContent = `Last: ${ageSeconds}s ago`;
        }
    }
}

/**
 * Update countdown timer and next update type
 */
function updateCountdownDisplay() {
    if (refreshState.countdownSeconds <= 0) {
        return;
    }

    const minutes = Math.floor(refreshState.countdownSeconds / 60);
    const seconds = refreshState.countdownSeconds % 60;
    const timerElement = document.getElementById('countdown-timer');
    const updateTypeElement = document.getElementById('update-type');
    const refreshInfo = document.getElementById('refresh-info');

    if (timerElement) {
        timerElement.textContent = `${minutes}:${seconds.toString().padStart(2, '0')}`;
    }

    if (updateTypeElement && refreshState.nextUpdateType) {
        const typeLabel = refreshState.nextUpdateType === 'market_data' ? 'Market Data' : 'Prediction';
        updateTypeElement.textContent = `(${typeLabel})`;
    }

    // Add pulsing animation when refresh is imminent (< 30 seconds)
    if (refreshInfo) {
        if (refreshState.countdownSeconds < 30) {
            refreshInfo.classList.add('refresh-imminent');
        } else {
            refreshInfo.classList.remove('refresh-imminent');
        }
    }

    refreshState.countdownSeconds--;
}

/**
 * Start countdown timer
 */
function startCountdown(seconds, updateType) {
    // Clear existing countdown
    if (refreshState.countdownInterval) {
        clearInterval(refreshState.countdownInterval);
    }

    refreshState.countdownSeconds = seconds;
    refreshState.nextUpdateType = updateType;

    // Update immediately
    updateCountdownDisplay();

    // Update every second
    refreshState.countdownInterval = setInterval(() => {
        updateCountdownDisplay();
        if (refreshState.countdownSeconds <= 0) {
            clearInterval(refreshState.countdownInterval);
        }
    }, 1000);
}

/**
 * Schedule next refresh based on scheduler timing
 */
function scheduleNextRefresh(nextUpdateSeconds, updateType) {
    // Clear existing timeout
    if (refreshState.refreshTimeout) {
        clearTimeout(refreshState.refreshTimeout);
    }

    if (!nextUpdateSeconds || nextUpdateSeconds < 0) {
        console.warn('Invalid next update time, falling back to 15 minute refresh');
        nextUpdateSeconds = 900; // 15 minutes fallback
    }

    // Ensure minimum 60 second interval
    const refreshSeconds = Math.max(60, nextUpdateSeconds);

    console.log(`Scheduling refresh in ${refreshSeconds} seconds (${updateType || 'unknown'} update)`);

    // Start countdown
    startCountdown(refreshSeconds, updateType);

    // Schedule actual refresh
    refreshState.refreshTimeout = setTimeout(() => {
        refreshDataWithSync();
    }, refreshSeconds * 1000);
}

/**
 * Fetch market data and update freshness indicators
 */
function fetchData() {
    fetch('/api/data')
        .then(response => {
            if (!response.ok) {
                throw new Error(`HTTP ${response.status}: ${response.statusText}`);
            }
            return response.json();
        })
        .then(result => {
            if (result.error) {
                throw new Error(result.error_detail || result.error);
            }

            document.getElementById('loading').style.display = 'none';
            document.getElementById('content').style.display = 'block';

            // Update freshness indicator
            refreshState.dataFreshness = result.freshness || 'fresh';
            refreshState.lastDataTimestamp = result.data_timestamp;
            updateFreshnessIndicator(result.freshness || 'fresh', result.cache_age || 0);

            renderTickers(result.data);

            // Return result for chaining
            return result;
        })
        .catch(error => {
            document.getElementById('loading').style.display = 'none';
            document.getElementById('content').innerHTML = `
                <div class="error-card">
                    <strong>Error:</strong> Failed to fetch data. ${error.message}
                </div>
            `;
            throw error;
        });
}

/**
 * Coordinated refresh: fetch data + reschedule next refresh
 */
function refreshDataWithSync() {
    console.log('Refreshing data with intelligent sync...');

    // Show updating indicator
    const refreshInfo = document.getElementById('refresh-info');
    if (refreshInfo) {
        refreshInfo.classList.add('updating');
    }

    fetch('/api/data')
        .then(response => response.json())
        .then(result => {
            if (result.error) {
                throw new Error(result.error);
            }

            // Update UI
            renderTickers(result.data);

            // Update freshness
            refreshState.dataFreshness = result.freshness || 'fresh';
            refreshState.lastDataTimestamp = result.data_timestamp;
            updateFreshnessIndicator(result.freshness || 'fresh', result.cache_age || 0);

            // Remove updating indicator
            if (refreshInfo) {
                refreshInfo.classList.remove('updating');
            }

            // Schedule next refresh based on API response
            if (result.next_update_in_seconds) {
                scheduleNextRefresh(result.next_update_in_seconds, result.next_update_type);
            } else {
                // Fallback: try to get timing from scheduler endpoint
                fetchSchedulerTiming();
            }
        })
        .catch(error => {
            console.error('Refresh failed:', error);
            if (refreshInfo) {
                refreshInfo.classList.remove('updating');
            }
            // Fallback to 15 minute refresh on error
            scheduleNextRefresh(900, 'fallback');
        });
}

/**
 * Fetch scheduler timing for intelligent refresh
 */
function fetchSchedulerTiming() {
    fetch('/api/scheduler/next-update')
        .then(response => response.json())
        .then(result => {
            if (result.success && result.seconds_until_refresh) {
                scheduleNextRefresh(result.seconds_until_refresh, result.job_type);
            } else {
                console.warn('Could not get scheduler timing, using default 15 min refresh');
                scheduleNextRefresh(900, 'default');
            }
        })
        .catch(error => {
            console.error('Failed to fetch scheduler timing:', error);
            scheduleNextRefresh(900, 'error');
        });
}

/**
 * Initialize application with intelligent refresh
 */
function init() {
    console.log('Initializing NQP with intelligent refresh system...');

    // Initial data fetch
    fetchData();

    // Get initial scheduler timing and start intelligent refresh
    fetchSchedulerTiming();

    // Update freshness indicator periodically (every 5 seconds)
    setInterval(() => {
        if (refreshState.lastDataTimestamp) {
            const now = new Date();
            const dataTime = new Date(refreshState.lastDataTimestamp);
            const ageSeconds = (now - dataTime) / 1000;

            // Recalculate freshness status
            let freshness = 'fresh';
            if (ageSeconds >= 600) { // 10 minutes
                freshness = 'stale';
            } else if (ageSeconds >= 120) { // 2 minutes
                freshness = 'moderate';
            }

            updateFreshnessIndicator(freshness, ageSeconds);
        }
    }, 5000);
}

// Start application when DOM is ready
if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', init);
} else {
    init();
}
