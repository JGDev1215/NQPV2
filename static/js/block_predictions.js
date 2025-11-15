/**
 * Block Predictions Page JavaScript
 * Handles 7-block analysis visualization and display
 */

// Active instruments
const TICKERS = ['NQ=F', 'ES=F', '^FTSE'];
const TICKER_NAMES = {
    'NQ=F': 'NASDAQ-100 E-mini Futures',
    'ES=F': 'S&P 500 E-mini Futures',
    '^FTSE': 'FTSE 100 Index'
};

// Global data storage
let blockPredictions = {};
let countdownInterval = null;
const PREDICTION_INTERVAL_MINUTES = 15; // Predictions generated every 15 minutes

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
 * Get timezone suffix for ticker
 */
function getTickerTimezoneSuffix(symbol) {
    return symbol === '^FTSE' ? 'GMT' : 'ET';
}

/**
 * Format hour to readable format
 */
function formatHour(hour, ticker) {
    const hour12 = hour === 0 ? 12 : (hour > 12 ? hour - 12 : hour);
    const ampm = hour < 12 ? 'AM' : 'PM';
    const tzAbbrev = getTickerTimezoneSuffix(ticker);
    return `${hour12}:00 ${ampm} ${tzAbbrev}`;
}

/**
 * Fetch block predictions for a ticker
 */
async function fetchBlockPredictions(ticker) {
    try {
        const encodedTicker = encodeURIComponent(ticker);
        const response = await fetch(`/api/block-predictions/${encodedTicker}`);
        const result = await response.json();

        if (!result.success) {
            console.warn(`No block predictions for ${ticker}`);
            return [];
        }

        const predictions = result.data?.predictions || [];
        blockPredictions[ticker] = predictions;
        return predictions;
    } catch (error) {
        console.error(`Error fetching block predictions for ${ticker}:`, error);
        return [];
    }
}

/**
 * Get prediction color/class based on direction
 */
function getPredictionClass(prediction) {
    if (!prediction) return 'neutral';
    const pred = prediction.toLowerCase();
    if (pred === 'up') return 'bullish';
    if (pred === 'down') return 'bearish';
    return 'neutral';
}

/**
 * Get direction text
 */
function getDirectionText(prediction) {
    if (!prediction) return 'NEUTRAL';
    const pred = prediction.toUpperCase();
    return pred === 'UP' ? 'BULLISH' : (pred === 'DOWN' ? 'BEARISH' : 'NEUTRAL');
}

/**
 * Render 7-block timeline visualization
 */
function renderBlockTimeline(blocks) {
    if (!blocks || blocks.length === 0) {
        return '<p style="color: #6c757d; text-align: center;">No block data available</p>';
    }

    let html = '<div class="blocks-timeline">';

    blocks.forEach(block => {
        const blockNum = block.block_number || 0;
        const isAnalysisPeriod = blockNum <= 5;
        const isPredictionPeriod = blockNum > 5;

        // Determine color based on deviation
        let blockClass = 'neutral';
        const deviation = parseFloat(block.deviation_from_open) || 0;
        if (deviation > 0) blockClass = 'bullish';
        else if (deviation < 0) blockClass = 'bearish';

        if (isAnalysisPeriod) blockClass += ' analysis-period';
        if (isPredictionPeriod) blockClass += ' prediction-period';

        const closePriceText = formatPrice(block.close_price);
        const deviationText = `${deviation >= 0 ? '+' : ''}${deviation.toFixed(2)}σ`;

        html += `
            <div class="block ${blockClass}">
                <span class="block-number">B${blockNum}</span>
                <span class="block-price">${closePriceText}</span>
                <span class="block-deviation">${deviationText}</span>
            </div>
        `;
    });

    html += '</div>';

    // Add legend
    html += `
        <div style="font-size: 0.85rem; color: #6c757d; margin-top: 8px;">
            <span style="margin-right: 15px;"><span style="border: 3px solid #667eea; padding: 2px 6px; border-radius: 3px;">Blocks 1-5</span> Analysis Period</span>
            <span><span style="border: 3px dashed #667eea; padding: 2px 6px; border-radius: 3px;">Blocks 6-7</span> Prediction Period</span>
        </div>
    `;

    return html;
}

/**
 * Render analysis details for an hour
 */
function renderAnalysisDetails(prediction) {
    if (!prediction) {
        return '<p style="color: #6c757d;">No analysis data available</p>';
    }

    const earlyBias = prediction.early_bias || 'N/A';
    const earlyBiasClass = earlyBias === 'UP' ? 'bullish-text' : (earlyBias === 'DOWN' ? 'bearish-text' : '');
    const earlyBiasStrength = prediction.early_bias_strength || 0;

    const hasCounter = prediction.has_sustained_counter ? 'Yes' : 'No';
    const counterDirection = prediction.counter_direction || 'N/A';
    const counterClass = counterDirection === 'UP' ? 'bullish-text' : (counterDirection === 'DOWN' ? 'bearish-text' : '');

    const deviation = prediction.deviation_at_5_7 || 0;
    const deviationClass = deviation > 0 ? 'bullish-text' : (deviation < 0 ? 'bearish-text' : '');

    const strength = prediction.strength || 'N/A';
    const decisionPath = prediction.decision_tree_path || 'N/A';

    const confidence = prediction.confidence || 0;

    let html = '<div class="analysis-details">';

    html += `
        <div class="detail-item">
            <div class="detail-label">Early Bias</div>
            <div class="detail-value ${earlyBiasClass}">${earlyBias}</div>
            <div style="font-size: 0.8rem; color: #6c757d; margin-top: 3px;">Strength: ${earlyBiasStrength.toFixed(2)}σ</div>
        </div>

        <div class="detail-item">
            <div class="detail-label">Sustained Counter</div>
            <div class="detail-value">${hasCounter}</div>
            <div style="font-size: 0.8rem; color: #6c757d; margin-top: 3px;">Direction: ${counterDirection}</div>
        </div>

        <div class="detail-item">
            <div class="detail-label">5/7 Deviation</div>
            <div class="detail-value ${deviationClass}">${deviation >= 0 ? '+' : ''}${deviation.toFixed(2)}σ</div>
            <div style="font-size: 0.8rem; color: #6c757d; margin-top: 3px;">Strength: ${strength}</div>
        </div>

        <div class="detail-item">
            <div class="detail-label">Confidence</div>
            <div class="detail-value">${confidence.toFixed(1)}%</div>
            <div style="font-size: 0.8rem; color: #6c757d; margin-top: 3px;">Tree Path: ${decisionPath}</div>
        </div>
    `;

    html += '</div>';

    // Add decision tree details
    html += `
        <div class="decision-path">
            <strong>Decision Tree Details:</strong><br/>
            Early Bias: <strong>${earlyBias} (${earlyBiasStrength.toFixed(2)}σ)</strong><br/>
            Counter Detected: <strong>${hasCounter}</strong> ${hasCounter === 'Yes' ? `(Direction: ${counterDirection})` : ''}<br/>
            Deviation at 5/7: <strong>${deviation >= 0 ? '+' : ''}${deviation.toFixed(2)}σ (${strength})</strong>
        </div>
    `;

    return html;
}

/**
 * Render hourly prediction row
 */
function renderHourlyPrediction(hour, ticker, prediction) {
    if (!prediction) {
        return '';
    }

    const hourDisplay = formatHour(hour, ticker);
    const predictionDir = getDirectionText(prediction.prediction);
    const predictionClass = getPredictionClass(prediction.prediction);
    const confidence = prediction.confidence || 0;

    const blocks = prediction.blocks || [];
    const blockTimeline = renderBlockTimeline(blocks);
    const analysisDetails = renderAnalysisDetails(prediction);

    const actualResult = prediction.actual_result;
    let accuracyHtml = '';
    if (actualResult) {
        const accuracyClass = actualResult === 'CORRECT' ? 'correct' : 'wrong';
        accuracyHtml = `<span class="accuracy-badge ${accuracyClass}">${actualResult}</span>`;
    } else {
        accuracyHtml = '<span class="accuracy-badge pending">Pending</span>';
    }

    let html = `
        <div class="block-hour-row">
            <div class="block-hour-header">
                <div>
                    <strong>${hourDisplay}</strong> ${accuracyHtml}
                </div>
                <span class="prediction-badge ${predictionClass}">${predictionDir} • ${confidence.toFixed(1)}%</span>
            </div>

            ${blockTimeline}
            ${analysisDetails}
        </div>
    `;

    return html;
}

/**
 * Render all hourly predictions for a ticker
 */
function renderTickerPredictions(ticker, predictions) {
    if (!predictions || predictions.length === 0) {
        const isAllTicker = ticker === 'all';
        return `
            <div class="empty-state">
                <div style="margin-bottom: 30px;">
                    <h3 style="color: #667eea; margin-bottom: 15px;">🔄 No Predictions Available Yet</h3>
                    <p style="color: #495057; margin-bottom: 20px;">
                        Block predictions are generated automatically throughout the trading day using the latest market data from Supabase.
                    </p>
                </div>

                <div style="background: linear-gradient(135deg, #667eea15 0%, #764ba215 100%); border-left: 4px solid #667eea; padding: 20px; border-radius: 8px; margin-bottom: 25px;">
                    <div style="margin-bottom: 15px;">
                        <strong style="color: #667eea;">⏱️ Next Prediction In:</strong>
                        <div style="font-size: 2rem; font-weight: 700; color: #667eea; font-family: 'Courier New', monospace; margin-top: 10px;">
                            <span id="countdown-timer">00:00</span>
                            <span id="prediction-generating" style="display: none; margin-left: 10px; font-size: 1rem; color: #11998e;">
                                ✨ Generating...
                            </span>
                        </div>
                        <p style="color: #6c757d; font-size: 0.9rem; margin-top: 10px;">
                            Predictions are generated at minutes 2, 17, 32, and 47 of every trading hour.
                        </p>
                    </div>
                </div>

                <div style="display: flex; gap: 10px; justify-content: center; flex-wrap: wrap;">
                    <button id="generate-btn" onclick="generatePredictionsNow()"
                        style="background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); color: white; border: none; padding: 12px 24px; border-radius: 8px; font-weight: 600; cursor: pointer; transition: all 0.3s ease;"
                        onmouseover="this.style.transform='translateY(-2px)'; this.style.boxShadow='0 4px 12px rgba(102, 126, 234, 0.4)';"
                        onmouseout="this.style.transform='translateY(0)'; this.style.boxShadow='none';">
                        🔄 Generate Predictions Now
                    </button>
                    <a href="/"
                        style="background: rgba(102, 126, 234, 0.1); color: #667eea; border: 2px solid #667eea; padding: 12px 24px; border-radius: 8px; font-weight: 600; text-decoration: none; transition: all 0.3s ease; display: inline-block;"
                        onmouseover="this.style.background='rgba(102, 126, 234, 0.2)';"
                        onmouseout="this.style.background='rgba(102, 126, 234, 0.1)';">
                        ← Back to Dashboard
                    </a>
                </div>

                <p style="color: #6c757d; font-size: 0.85rem; margin-top: 25px;">
                    💡 Latest data is continuously synced from market feeds. Once sufficient data is available, the first prediction will be generated automatically.
                </p>
            </div>
        `;
    }

    let html = '';

    // Sort predictions by target hour
    const sortedPreds = [...predictions].sort((a, b) =>
        (a.target_hour || 0) - (b.target_hour || 0)
    );

    sortedPreds.forEach(pred => {
        const hour = pred.target_hour || 0;
        html += renderHourlyPrediction(hour, ticker, pred);
    });

    return html;
}

/**
 * Render content for a ticker
 */
function renderTickerContent(ticker) {
    const containerId = `content-${ticker}`;
    const container = document.getElementById(containerId);
    if (!container) return;

    const predictions = blockPredictions[ticker] || [];
    container.innerHTML = renderTickerPredictions(ticker, predictions);
}

/**
 * Render content for "All" tab
 */
async function renderAllContent() {
    const container = document.getElementById('content-all');
    if (!container) return;

    // Check if there are any predictions across all tickers
    const hasAnyPredictions = TICKERS.some(ticker => {
        const preds = blockPredictions[ticker] || [];
        return preds.length > 0;
    });

    // If no predictions exist anywhere, show the countdown view
    if (!hasAnyPredictions) {
        container.innerHTML = renderTickerPredictions('all', []);
        return;
    }

    let html = '';

    for (const ticker of TICKERS) {
        const predictions = blockPredictions[ticker] || [];

        html += `
            <div style="margin-bottom: 40px;">
                <h2 style="color: #667eea; font-weight: 700; margin-bottom: 20px; border-bottom: 2px solid #667eea; padding-bottom: 10px;">
                    ${TICKER_NAMES[ticker]}
                </h2>
                ${renderTickerPredictions(ticker, predictions)}
            </div>
        `;
    }

    container.innerHTML = html;
}

/**
 * Calculate time until next prediction
 */
function getNextPredictionTime() {
    const now = new Date();
    const minutes = now.getMinutes();
    const seconds = now.getSeconds();

    // Predictions at: 2, 17, 32, 47 minutes of every hour
    const predictionMinutes = [2, 17, 32, 47];
    let nextMinute = predictionMinutes.find(m => m > minutes);

    if (!nextMinute) {
        // Move to next hour
        nextMinute = predictionMinutes[0];
        now.setHours(now.getHours() + 1);
    }

    now.setMinutes(nextMinute);
    now.setSeconds(0);
    return now;
}

/**
 * Format time duration as MM:SS
 */
function formatTimeRemaining(ms) {
    const totalSeconds = Math.floor(ms / 1000);
    const minutes = Math.floor(totalSeconds / 60);
    const seconds = totalSeconds % 60;
    return `${String(minutes).padStart(2, '0')}:${String(seconds).padStart(2, '0')}`;
}

/**
 * Update countdown timer
 */
function updateCountdownTimer() {
    const nextTime = getNextPredictionTime();
    const now = new Date();
    const timeRemaining = nextTime - now;

    const timerElement = document.getElementById('countdown-timer');
    const generatingElement = document.getElementById('prediction-generating');

    if (timerElement) {
        timerElement.textContent = formatTimeRemaining(timeRemaining);
    }

    // Show "Generating..." when less than 10 seconds away
    if (generatingElement && timeRemaining < 10000) {
        generatingElement.style.display = 'inline-block';
    } else if (generatingElement) {
        generatingElement.style.display = 'none';
    }
}

/**
 * Start countdown timer that updates every second
 */
function startCountdownTimer() {
    updateCountdownTimer();
    if (countdownInterval) clearInterval(countdownInterval);

    countdownInterval = setInterval(() => {
        updateCountdownTimer();
    }, 1000);
}

/**
 * Trigger manual prediction generation
 */
async function generatePredictionsNow() {
    const btn = document.getElementById('generate-btn');
    if (btn) {
        btn.disabled = true;
        btn.innerHTML = '⏳ Generating...';
    }

    try {
        const response = await fetch('/api/block-predictions/generate', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                tickers: TICKERS
            })
        });

        const result = await response.json();

        if (result.success) {
            const totalGenerated = result.data?.summary?.total_generated || 0;

            if (totalGenerated > 0) {
                // Predictions were generated - reload to show them
                setTimeout(() => {
                    location.reload();
                }, 1500);
            } else {
                // No predictions generated - show detailed error
                if (btn) {
                    btn.disabled = false;
                    btn.innerHTML = '🔄 Generate Predictions Now';
                }

                // Get detailed error information from first ticker's generation result
                const firstTicker = Object.keys(result.data.generations)[0];
                const tickerData = result.data.generations[firstTicker];

                let errorTitle = '';
                let errorMessage = '';
                let errorRecommendation = '';

                if (tickerData.status === 'failed') {
                    // Exception occurred during generation
                    errorTitle = '⚠️ Generation Error';
                    errorMessage = `
                        <p>An error occurred while generating block predictions.</p>
                        <p><strong>Error:</strong> ${tickerData.error || 'Unknown error'}</p>
                        <p><strong>Type:</strong> ${tickerData.error_type || 'Unknown'}</p>
                    `;
                    errorRecommendation = `
                        <p style="color: #6c757d; font-size: 0.9rem; margin-top: 15px;">
                            <strong>Next Steps:</strong> Check application logs for more details about what went wrong.
                        </p>
                    `;
                } else if (tickerData.skipped_no_data && tickerData.skipped_no_data.length > 0) {
                    // Missing historical data
                    const noDataHours = tickerData.skipped_no_data.join(', ');
                    const generatedHours = tickerData.generated_hours && tickerData.generated_hours.length > 0
                        ? tickerData.generated_hours.join(', ')
                        : 'None';

                    errorTitle = '⚠️ Historical Data Unavailable';
                    errorMessage = `
                        <p>The database does not have sufficient historical OHLC bar data to generate predictions.</p>
                        <p><strong>Missing data for hours:</strong> ${noDataHours}</p>
                        <p><strong>Data available for hours:</strong> ${generatedHours}</p>
                        <p style="color: #6c757d; font-size: 0.9rem; margin-top: 10px;">
                            Block predictions require at least 10 five-minute bars per hour for reliable analysis.
                        </p>
                    `;
                    errorRecommendation = `
                        <p style="color: #6c757d; font-size: 0.9rem; margin-top: 15px;">
                            <strong>Next Steps:</strong>
                        </p>
                        <ul style="color: #6c757d; font-size: 0.9rem;">
                            <li>Wait for the next data sync job (runs every 90 seconds at :02, :17, :32, :47)</li>
                            <li>Check if the market has opened and data is being collected</li>
                            <li>Verify that the data sync scheduler is enabled in the application</li>
                            <li>Try again in 1-2 minutes once more data has been synced</li>
                        </ul>
                    `;
                } else if (tickerData.skipped_future && tickerData.skipped_future.length === 24) {
                    // All hours are in the future (date selection issue)
                    errorTitle = '⚠️ Future Date Selected';
                    errorMessage = `
                        <p>Cannot generate block predictions for future dates or hours.</p>
                        <p>Historical data is required for prediction analysis. Block predictions can only be generated for hours that have already passed.</p>
                    `;
                    errorRecommendation = `
                        <p style="color: #6c757d; font-size: 0.9rem; margin-top: 15px;">
                            <strong>Next Steps:</strong> Select today's date or a past date with available historical data.
                        </p>
                    `;
                } else {
                    // Unknown error state
                    errorTitle = '⚠️ No Predictions Generated';
                    errorMessage = `
                        <p>Unable to generate block predictions for the selected date and tickers.</p>
                    `;
                    errorRecommendation = `
                        <p style="color: #6c757d; font-size: 0.9rem; margin-top: 15px;">
                            <strong>Debug Info:</strong>
                        </p>
                        <pre style="color: #6c757d; font-size: 0.85rem; background: #f5f5f5; padding: 10px; border-radius: 4px; overflow-x: auto;">
${JSON.stringify(tickerData, null, 2)}
                        </pre>
                    `;
                }

                // Show detailed error message
                const container = document.getElementById('content-all');
                if (container) {
                    container.innerHTML = `
                        <div class="empty-state">
                            <div style="background: linear-gradient(135deg, #ff6b6b15 0%, #ee5a6f15 100%); border-left: 4px solid #ff6b6b; padding: 20px; border-radius: 8px; margin-bottom: 25px;">
                                <strong style="color: #ff6b6b;">${errorTitle}</strong>
                                ${errorMessage}
                                ${errorRecommendation}
                            </div>

                            <div style="display: flex; gap: 10px; justify-content: center; flex-wrap: wrap;">
                                <button id="generate-btn" onclick="generatePredictionsNow()"
                                    style="background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); color: white; border: none; padding: 12px 24px; border-radius: 8px; font-weight: 600; cursor: pointer; transition: all 0.3s ease;"
                                    onmouseover="this.style.transform='translateY(-2px)'; this.style.boxShadow='0 4px 12px rgba(102, 126, 234, 0.4)';"
                                    onmouseout="this.style.transform='translateY(0)'; this.style.boxShadow='none';">
                                    🔄 Try Again
                                </button>
                                <a href="/"
                                    style="background: rgba(102, 126, 234, 0.1); color: #667eea; border: 2px solid #667eea; padding: 12px 24px; border-radius: 8px; font-weight: 600; text-decoration: none; transition: all 0.3s ease; display: inline-block;"
                                    onmouseover="this.style.background='rgba(102, 126, 234, 0.2)';"
                                    onmouseout="this.style.background='rgba(102, 126, 234, 0.1)';">
                                    ← Back to Dashboard
                                </a>
                            </div>
                        </div>
                    `;
                }
            }
        } else {
            if (btn) {
                btn.disabled = false;
                btn.innerHTML = '🔄 Generate Predictions Now';
            }
            alert('Error generating predictions: ' + (result.message || 'Unknown error'));
        }
    } catch (error) {
        console.error('Error generating predictions:', error);
        if (btn) {
            btn.disabled = false;
            btn.innerHTML = '🔄 Generate Predictions Now';
        }
        alert('Failed to connect to server');
    }
}

/**
 * Initialize page
 */
async function initializePage() {
    // Fetch data for all tickers
    for (const ticker of TICKERS) {
        await fetchBlockPredictions(ticker);
    }

    // Render initial content
    renderAllContent();
    TICKERS.forEach(ticker => renderTickerContent(ticker));

    // Hide loading, show content
    const loading = document.getElementById('loading');
    const allContent = document.getElementById('content-all');
    if (loading) loading.style.display = 'none';
    if (allContent) allContent.style.display = 'block';

    // Setup tab switching
    setupTabSwitching();

    // Start countdown timer for next prediction
    startCountdownTimer();
}

/**
 * Setup ticker tab switching
 */
function setupTabSwitching() {
    const tabs = document.querySelectorAll('.ticker-tab');

    tabs.forEach(tab => {
        tab.addEventListener('click', () => {
            // Remove active class from all tabs
            tabs.forEach(t => t.classList.remove('active'));
            // Add active class to clicked tab
            tab.classList.add('active');

            // Hide all content
            const contents = document.querySelectorAll('.ticker-content');
            contents.forEach(c => c.classList.remove('active'));
            contents.forEach(c => c.style.display = 'none');

            // Show selected content
            const ticker = tab.dataset.ticker;
            const contentId = `content-${ticker}`;
            const content = document.getElementById(contentId);
            if (content) {
                content.classList.add('active');
                content.style.display = 'block';
            }
        });
    });
}

// Initialize on page load
document.addEventListener('DOMContentLoaded', initializePage);
