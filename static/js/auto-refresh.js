/**
 * Auto-refresh mechanism with intelligent scheduling and error recovery
 *
 * Features:
 * - Automatic refresh at scheduled intervals
 * - Intelligent backoff on errors
 * - Visual progress indicator
 * - Browser tab visibility detection
 * - Network status monitoring
 * - Configurable refresh intervals
 */

class AutoRefreshManager {
    constructor(options = {}) {
        this.options = {
            baseInterval: options.baseInterval || 300000, // 5 minutes
            minInterval: options.minInterval || 30000,    // 30 seconds
            maxInterval: options.maxInterval || 3600000,  // 1 hour
            backoffMultiplier: options.backoffMultiplier || 1.5,
            maxRetries: options.maxRetries || 3,
            ...options
        };

        this.refreshTimer = null;
        this.countdownTimer = null;
        this.currentInterval = this.options.baseInterval;
        this.consecutiveErrors = 0;
        this.isOnline = navigator.onLine;
        this.isPageVisible = !document.hidden;
        this.lastRefreshTime = null;
        this.nextRefreshTime = null;

        this.initializeEventListeners();
        this.scheduleNextRefresh();
    }

    initializeEventListeners() {
        // Monitor online/offline status
        window.addEventListener('online', () => this.onOnline());
        window.addEventListener('offline', () => this.onOffline());

        // Monitor page visibility
        document.addEventListener('visibilitychange', () => this.onVisibilityChange());

        // Refresh on page focus
        window.addEventListener('focus', () => this.onPageFocus());
    }

    scheduleNextRefresh() {
        this.nextRefreshTime = new Date(Date.now() + this.currentInterval);
        console.log(`Next refresh scheduled in ${this.currentInterval / 1000}s at ${this.nextRefreshTime.toLocaleTimeString()}`);

        // Clear existing timers
        if (this.refreshTimer) clearTimeout(this.refreshTimer);
        if (this.countdownTimer) clearInterval(this.countdownTimer);

        // Start countdown
        this.startCountdown();

        // Schedule refresh
        this.refreshTimer = setTimeout(() => this.executeRefresh(), this.currentInterval);
    }

    startCountdown() {
        const updateCountdown = () => {
            const now = new Date();
            const secondsUntilRefresh = Math.max(0, Math.ceil((this.nextRefreshTime - now) / 1000));
            const minutes = Math.floor(secondsUntilRefresh / 60);
            const seconds = secondsUntilRefresh % 60;

            const countdownText = `${minutes}:${seconds.toString().padStart(2, '0')}`;
            const countdownElement = document.getElementById('countdown-timer');

            if (countdownElement) {
                countdownElement.textContent = countdownText;
            }

            if (secondsUntilRefresh <= 0) {
                clearInterval(this.countdownTimer);
            }
        };

        updateCountdown(); // Update immediately
        this.countdownTimer = setInterval(updateCountdown, 1000);
    }

    async executeRefresh() {
        if (!this.isOnline) {
            console.warn('Offline - skipping refresh');
            return;
        }

        if (!this.isPageVisible) {
            console.log('Page not visible - rescheduling refresh');
            this.scheduleNextRefresh();
            return;
        }

        console.log('Executing auto-refresh...');
        this.updateRefreshIndicator('refreshing');

        try {
            // Call the main app refresh function
            if (typeof window.refreshData === 'function') {
                await window.refreshData();
                this.onRefreshSuccess();
            }
        } catch (error) {
            console.error('Refresh error:', error);
            this.onRefreshError(error);
        }
    }

    onRefreshSuccess() {
        this.consecutiveErrors = 0;
        this.currentInterval = this.options.baseInterval; // Reset to base interval
        this.lastRefreshTime = new Date();

        // Update UI
        const lastUpdateElement = document.getElementById('last-update-time');
        if (lastUpdateElement) {
            lastUpdateElement.textContent = `Last: ${this.lastRefreshTime.toLocaleTimeString()}`;
        }

        this.updateRefreshIndicator('fresh');
        this.scheduleNextRefresh();
    }

    onRefreshError(error) {
        this.consecutiveErrors++;
        console.error(`Refresh error ${this.consecutiveErrors}/${this.options.maxRetries}:`, error);

        if (this.consecutiveErrors >= this.options.maxRetries) {
            // Max retries reached - switch to longer interval
            this.currentInterval = Math.min(
                this.currentInterval * this.options.backoffMultiplier,
                this.options.maxInterval
            );
            this.consecutiveErrors = 0;
            console.warn(`Max retries reached. Backing off to ${this.currentInterval / 1000}s interval`);
        } else {
            // Exponential backoff
            this.currentInterval = Math.min(
                this.currentInterval * this.options.backoffMultiplier,
                this.options.maxInterval
            );
        }

        this.updateRefreshIndicator('error');
        this.scheduleNextRefresh();
    }

    updateRefreshIndicator(status) {
        const indicator = document.getElementById('data-freshness-dot');
        if (!indicator) return;

        // Remove all status classes
        indicator.classList.remove('fresh', 'refreshing', 'stale', 'error');

        // Add current status class
        switch (status) {
            case 'fresh':
                indicator.classList.add('fresh');
                break;
            case 'refreshing':
                indicator.classList.add('refreshing');
                break;
            case 'stale':
                indicator.classList.add('stale');
                break;
            case 'error':
                indicator.classList.add('error');
                break;
        }
    }

    onOnline() {
        console.log('Back online - resuming auto-refresh');
        this.isOnline = true;
        this.consecutiveErrors = 0;
        this.currentInterval = this.options.baseInterval;
        this.updateRefreshIndicator('fresh');
        this.scheduleNextRefresh();
    }

    onOffline() {
        console.warn('Internet connection lost');
        this.isOnline = false;
        this.updateRefreshIndicator('stale');
        if (this.refreshTimer) clearTimeout(this.refreshTimer);
        if (this.countdownTimer) clearInterval(this.countdownTimer);
    }

    onVisibilityChange() {
        this.isPageVisible = !document.hidden;
        if (this.isPageVisible) {
            console.log('Page became visible');
            this.onPageFocus();
        } else {
            console.log('Page hidden');
        }
    }

    onPageFocus() {
        if (!this.isOnline) return;

        const timeSinceLastRefresh = this.lastRefreshTime ?
            (Date.now() - this.lastRefreshTime) / 1000 :
            Infinity;

        // Refresh if data is stale (older than base interval)
        if (timeSinceLastRefresh > (this.options.baseInterval / 1000)) {
            console.log('Data is stale - refreshing immediately');
            clearTimeout(this.refreshTimer);
            clearInterval(this.countdownTimer);
            this.executeRefresh();
        }
    }

    stop() {
        console.log('Stopping auto-refresh');
        if (this.refreshTimer) clearTimeout(this.refreshTimer);
        if (this.countdownTimer) clearInterval(this.countdownTimer);
    }

    start() {
        console.log('Starting auto-refresh');
        this.consecutiveErrors = 0;
        this.currentInterval = this.options.baseInterval;
        this.scheduleNextRefresh();
    }

    setInterval(interval) {
        console.log(`Changing refresh interval to ${interval / 1000}s`);
        this.options.baseInterval = interval;
        this.currentInterval = interval;
        clearTimeout(this.refreshTimer);
        clearInterval(this.countdownTimer);
        this.scheduleNextRefresh();
    }
}

// Initialize when DOM is ready
document.addEventListener('DOMContentLoaded', () => {
    // Create global auto-refresh manager
    window.autoRefreshManager = new AutoRefreshManager({
        baseInterval: 300000, // 5 minutes
        backoffMultiplier: 1.5,
        maxRetries: 3
    });

    console.log('Auto-refresh manager initialized');
});
