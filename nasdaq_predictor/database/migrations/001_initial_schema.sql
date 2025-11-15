-- NQP Database Schema Migration
-- Version: 001
-- Description: Initial schema for NQP (NASDAQ Predictor) application
-- Created: 2025-01-11
-- Purpose: Store tickers, market data, predictions, signals, and reference levels

-- Enable UUID extension
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- ============================================================================
-- TABLE: tickers
-- Description: Store ticker symbols and metadata
-- Purpose: Extensible ticker configuration (NQ=F, ES=F, etc.)
-- ============================================================================
CREATE TABLE tickers (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    symbol VARCHAR(20) UNIQUE NOT NULL,
    name VARCHAR(100) NOT NULL,
    type VARCHAR(20) NOT NULL CHECK (type IN ('futures', 'index', 'stock', 'etf')),
    enabled BOOLEAN DEFAULT true,
    trading_hours_start TIME,
    trading_hours_end TIME,
    timezone VARCHAR(50) DEFAULT 'UTC',
    metadata JSONB DEFAULT '{}',
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- Index for fast enabled ticker lookups
CREATE INDEX idx_tickers_enabled ON tickers(enabled) WHERE enabled = true;
CREATE INDEX idx_tickers_symbol ON tickers(symbol);

-- ============================================================================
-- TABLE: market_data
-- Description: Store raw OHLC (Open, High, Low, Close) price data
-- Purpose: Historical price data for analysis and backtesting
-- ============================================================================
CREATE TABLE market_data (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    ticker_id UUID NOT NULL REFERENCES tickers(id) ON DELETE CASCADE,
    timestamp TIMESTAMPTZ NOT NULL,
    open NUMERIC(12,2) NOT NULL,
    high NUMERIC(12,2) NOT NULL,
    low NUMERIC(12,2) NOT NULL,
    close NUMERIC(12,2) NOT NULL,
    volume BIGINT,
    interval VARCHAR(10) NOT NULL CHECK (interval IN ('1m', '5m', '15m', '30m', '1h', '4h', '1d', '1w', '1M')),
    source VARCHAR(50) DEFAULT 'yfinance',
    metadata JSONB DEFAULT '{}',
    created_at TIMESTAMPTZ DEFAULT NOW(),

    -- Ensure no duplicate data points
    UNIQUE(ticker_id, timestamp, interval)
);

-- Indexes for fast time-series queries
CREATE INDEX idx_market_data_ticker_timestamp ON market_data(ticker_id, timestamp DESC);
CREATE INDEX idx_market_data_ticker_interval_timestamp ON market_data(ticker_id, interval, timestamp DESC);
CREATE INDEX idx_market_data_timestamp ON market_data(timestamp DESC);

-- ============================================================================
-- TABLE: reference_levels
-- Description: Store calculated reference price levels
-- Purpose: Daily snapshots of all 11 reference levels for signal generation
-- ============================================================================
CREATE TABLE reference_levels (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    ticker_id UUID NOT NULL REFERENCES tickers(id) ON DELETE CASCADE,
    timestamp TIMESTAMPTZ NOT NULL,

    -- Core reference levels (original 9)
    daily_open NUMERIC(12,2),
    hourly_open NUMERIC(12,2),
    four_hourly_open NUMERIC(12,2),
    thirty_min_open NUMERIC(12,2),
    prev_day_high NUMERIC(12,2),
    prev_day_low NUMERIC(12,2),
    prev_week_open NUMERIC(12,2),
    weekly_open NUMERIC(12,2),
    monthly_open NUMERIC(12,2),

    -- New morning reference levels
    seven_am_open NUMERIC(12,2),
    eight_thirty_am_open NUMERIC(12,2),

    -- Additional data
    current_price NUMERIC(12,2),
    ny_time TIMESTAMPTZ,
    london_time TIMESTAMPTZ,

    metadata JSONB DEFAULT '{}',
    created_at TIMESTAMPTZ DEFAULT NOW(),

    -- One set of reference levels per ticker per timestamp
    UNIQUE(ticker_id, timestamp)
);

-- Indexes for fast lookups
CREATE INDEX idx_reference_levels_ticker_timestamp ON reference_levels(ticker_id, timestamp DESC);
CREATE INDEX idx_reference_levels_timestamp ON reference_levels(timestamp DESC);

-- ============================================================================
-- TABLE: predictions
-- Description: Store prediction results
-- Purpose: Track all predictions with confidence and accuracy
-- ============================================================================
CREATE TABLE predictions (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    ticker_id UUID NOT NULL REFERENCES tickers(id) ON DELETE CASCADE,
    timestamp TIMESTAMPTZ NOT NULL,

    -- Prediction details
    prediction VARCHAR(20) NOT NULL CHECK (prediction IN ('BULLISH', 'BEARISH', 'NEUTRAL')),
    confidence NUMERIC(5,2) NOT NULL CHECK (confidence >= 0 AND confidence <= 100),
    weighted_score NUMERIC(5,4) NOT NULL CHECK (weighted_score >= 0 AND weighted_score <= 1),

    -- Signal counts
    bullish_count INT NOT NULL CHECK (bullish_count >= 0),
    bearish_count INT NOT NULL CHECK (bearish_count >= 0),
    total_signals INT NOT NULL CHECK (total_signals > 0),

    -- Accuracy tracking
    actual_result VARCHAR(20) CHECK (actual_result IN ('CORRECT', 'WRONG', 'PENDING', NULL)),
    actual_price_change NUMERIC(12,2),
    verification_timestamp TIMESTAMPTZ,

    -- Additional context
    market_status VARCHAR(20),
    volatility_level VARCHAR(20),
    session VARCHAR(50),

    metadata JSONB DEFAULT '{}',
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- Indexes for analytics and queries
CREATE INDEX idx_predictions_ticker_timestamp ON predictions(ticker_id, timestamp DESC);
CREATE INDEX idx_predictions_timestamp ON predictions(timestamp DESC);
CREATE INDEX idx_predictions_actual_result ON predictions(actual_result) WHERE actual_result IS NOT NULL;
CREATE INDEX idx_predictions_ticker_accuracy ON predictions(ticker_id, actual_result) WHERE actual_result IN ('CORRECT', 'WRONG');

-- ============================================================================
-- TABLE: signals
-- Description: Store individual signal breakdowns per prediction
-- Purpose: Detailed analysis of which reference levels triggered which signals
-- ============================================================================
CREATE TABLE signals (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    prediction_id UUID NOT NULL REFERENCES predictions(id) ON DELETE CASCADE,

    -- Signal details
    reference_level_name VARCHAR(50) NOT NULL,
    reference_level_value NUMERIC(12,2) NOT NULL,
    current_price NUMERIC(12,2) NOT NULL,

    -- Signal calculation
    signal INT NOT NULL CHECK (signal IN (0, 1)),  -- 0=BEARISH, 1=BULLISH
    weight NUMERIC(5,4) NOT NULL CHECK (weight >= 0 AND weight <= 1),
    weighted_contribution NUMERIC(5,4) NOT NULL,

    -- Distance from reference level
    distance NUMERIC(12,2) NOT NULL,
    distance_percentage NUMERIC(5,2),

    -- Status
    status VARCHAR(20) NOT NULL CHECK (status IN ('BULLISH', 'BEARISH', 'N/A')),

    metadata JSONB DEFAULT '{}',
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- Indexes for signal analysis
CREATE INDEX idx_signals_prediction_id ON signals(prediction_id);
CREATE INDEX idx_signals_reference_level ON signals(reference_level_name);
CREATE INDEX idx_signals_status ON signals(status);

-- ============================================================================
-- TABLE: intraday_predictions
-- Description: Store hourly intraday predictions (9am, 10am, etc.)
-- Purpose: Track specific hourly predictions with time-decay confidence
-- ============================================================================
CREATE TABLE intraday_predictions (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    ticker_id UUID NOT NULL REFERENCES tickers(id) ON DELETE CASCADE,
    prediction_id UUID REFERENCES predictions(id) ON DELETE SET NULL,

    -- Time window
    target_hour INT NOT NULL CHECK (target_hour >= 0 AND target_hour <= 23),
    target_timestamp TIMESTAMPTZ NOT NULL,
    prediction_made_at TIMESTAMPTZ NOT NULL,

    -- Prediction
    prediction VARCHAR(20) NOT NULL CHECK (prediction IN ('BULLISH', 'BEARISH', 'NEUTRAL')),
    base_confidence NUMERIC(5,2) NOT NULL,
    decay_factor NUMERIC(5,4) NOT NULL,
    final_confidence NUMERIC(5,2) NOT NULL,

    -- Reference prices
    reference_price NUMERIC(12,2) NOT NULL,
    target_close_price NUMERIC(12,2),

    -- Accuracy
    actual_result VARCHAR(20) CHECK (actual_result IN ('CORRECT', 'WRONG', 'PENDING', NULL)),
    verified_at TIMESTAMPTZ,

    metadata JSONB DEFAULT '{}',
    created_at TIMESTAMPTZ DEFAULT NOW(),

    UNIQUE(ticker_id, target_timestamp, target_hour)
);

-- Indexes for intraday predictions
CREATE INDEX idx_intraday_predictions_ticker_target ON intraday_predictions(ticker_id, target_timestamp DESC);
CREATE INDEX idx_intraday_predictions_target_hour ON intraday_predictions(target_hour);

-- ============================================================================
-- TABLE: session_ranges
-- Description: Store ICT killzone session ranges
-- Purpose: Track high/low ranges for Asia, London, NY sessions
-- ============================================================================
CREATE TABLE session_ranges (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    ticker_id UUID NOT NULL REFERENCES tickers(id) ON DELETE CASCADE,
    date DATE NOT NULL,
    session_name VARCHAR(50) NOT NULL CHECK (session_name IN ('Asia', 'London', 'NY AM', 'NY PM', 'Full Day')),

    -- Session times
    session_start TIMESTAMPTZ NOT NULL,
    session_end TIMESTAMPTZ NOT NULL,

    -- Price range
    high NUMERIC(12,2),
    low NUMERIC(12,2),
    open NUMERIC(12,2),
    close NUMERIC(12,2),
    range_points NUMERIC(12,2),

    -- Volatility
    volatility_percentage NUMERIC(5,2),
    volatility_level VARCHAR(20) CHECK (volatility_level IN ('LOW', 'MODERATE', 'HIGH', 'EXTREME')),

    metadata JSONB DEFAULT '{}',
    created_at TIMESTAMPTZ DEFAULT NOW(),

    UNIQUE(ticker_id, date, session_name)
);

-- Indexes for session analysis
CREATE INDEX idx_session_ranges_ticker_date ON session_ranges(ticker_id, date DESC);
CREATE INDEX idx_session_ranges_session_name ON session_ranges(session_name);

-- ============================================================================
-- FUNCTIONS: Automatic timestamp updates
-- ============================================================================
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- Triggers for automatic updated_at
CREATE TRIGGER update_tickers_updated_at BEFORE UPDATE ON tickers
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_predictions_updated_at BEFORE UPDATE ON predictions
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

-- ============================================================================
-- SEED DATA: Initial tickers
-- ============================================================================
INSERT INTO tickers (symbol, name, type, enabled, timezone) VALUES
    ('NQ=F', 'NASDAQ-100 Futures', 'futures', true, 'America/New_York'),
    ('ES=F', 'S&P 500 Futures', 'futures', true, 'America/New_York'),
    ('^FTSE', 'FTSE 100 Index', 'index', true, 'Europe/London')
ON CONFLICT (symbol) DO NOTHING;

-- ============================================================================
-- VIEWS: Useful analytics views
-- ============================================================================

-- View: Latest predictions with accuracy
CREATE OR REPLACE VIEW v_latest_predictions AS
SELECT
    t.symbol,
    t.name,
    p.timestamp,
    p.prediction,
    p.confidence,
    p.weighted_score,
    p.bullish_count,
    p.total_signals,
    p.actual_result,
    p.market_status,
    p.volatility_level,
    p.created_at
FROM predictions p
JOIN tickers t ON p.ticker_id = t.id
ORDER BY p.timestamp DESC;

-- View: Prediction accuracy by ticker
CREATE OR REPLACE VIEW v_prediction_accuracy AS
SELECT
    t.symbol,
    t.name,
    COUNT(*) as total_predictions,
    SUM(CASE WHEN p.actual_result = 'CORRECT' THEN 1 ELSE 0 END) as correct_predictions,
    SUM(CASE WHEN p.actual_result = 'WRONG' THEN 1 ELSE 0 END) as wrong_predictions,
    ROUND(
        100.0 * SUM(CASE WHEN p.actual_result = 'CORRECT' THEN 1 ELSE 0 END) /
        NULLIF(SUM(CASE WHEN p.actual_result IN ('CORRECT', 'WRONG') THEN 1 ELSE 0 END), 0),
        2
    ) as accuracy_percentage,
    AVG(p.confidence) as avg_confidence
FROM predictions p
JOIN tickers t ON p.ticker_id = t.id
WHERE p.actual_result IN ('CORRECT', 'WRONG')
GROUP BY t.id, t.symbol, t.name;

-- View: Signal performance by reference level
CREATE OR REPLACE VIEW v_signal_performance AS
SELECT
    s.reference_level_name,
    COUNT(*) as total_signals,
    AVG(s.weight) as avg_weight,
    SUM(CASE WHEN s.signal = 1 THEN 1 ELSE 0 END) as bullish_count,
    SUM(CASE WHEN s.signal = 0 THEN 1 ELSE 0 END) as bearish_count,
    AVG(s.distance_percentage) as avg_distance_percentage
FROM signals s
JOIN predictions p ON s.prediction_id = p.id
WHERE p.actual_result IN ('CORRECT', 'WRONG')
GROUP BY s.reference_level_name
ORDER BY avg_weight DESC;

-- ============================================================================
-- COMMENTS: Table and column documentation
-- ============================================================================
COMMENT ON TABLE tickers IS 'Stores ticker symbols and metadata for extensible ticker management';
COMMENT ON TABLE market_data IS 'Raw OHLC price data from yfinance with multiple timeframe support';
COMMENT ON TABLE reference_levels IS 'Calculated reference price levels (11 total) for signal generation';
COMMENT ON TABLE predictions IS 'Prediction results with confidence, accuracy tracking, and metadata';
COMMENT ON TABLE signals IS 'Individual signal breakdowns showing which reference levels triggered signals';
COMMENT ON TABLE intraday_predictions IS 'Hourly intraday predictions (9am, 10am) with time-decay confidence';
COMMENT ON TABLE session_ranges IS 'ICT killzone session ranges (Asia, London, NY) with volatility';

-- ============================================================================
-- GRANTS: Set permissions (adjust based on your security needs)
-- ============================================================================
-- Note: In Supabase, you'll need to configure Row Level Security (RLS) policies
-- through the Supabase dashboard for proper security

-- ============================================================================
-- END OF MIGRATION
-- ============================================================================
