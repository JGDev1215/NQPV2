-- Migration: Add Fibonacci Pivot Points Table
-- Description: Creates table to store Fibonacci-based pivot point calculations
-- Date: 2025-11-12
-- Author: NQP System

-- Create fibonacci_pivots table
CREATE TABLE IF NOT EXISTS fibonacci_pivots (
    id SERIAL PRIMARY KEY,
    ticker_symbol VARCHAR(20) NOT NULL,
    timeframe VARCHAR(10) NOT NULL,  -- 'daily', 'weekly', 'monthly'
    calculation_date TIMESTAMP WITH TIME ZONE NOT NULL,

    -- Source OHLC data used for calculation
    period_high DECIMAL(12, 4) NOT NULL,
    period_low DECIMAL(12, 4) NOT NULL,
    period_close DECIMAL(12, 4) NOT NULL,

    -- Calculated pivot levels
    pivot_point DECIMAL(12, 4) NOT NULL,
    resistance_1 DECIMAL(12, 4) NOT NULL,
    resistance_2 DECIMAL(12, 4) NOT NULL,
    resistance_3 DECIMAL(12, 4) NOT NULL,
    support_1 DECIMAL(12, 4) NOT NULL,
    support_2 DECIMAL(12, 4) NOT NULL,
    support_3 DECIMAL(12, 4) NOT NULL,

    -- Metadata
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),

    -- Ensure unique combination of ticker, timeframe, and date
    CONSTRAINT unique_fib_pivot UNIQUE(ticker_symbol, timeframe, calculation_date)
);

-- Create indexes for efficient querying
CREATE INDEX IF NOT EXISTS idx_fib_pivots_ticker
    ON fibonacci_pivots(ticker_symbol);

CREATE INDEX IF NOT EXISTS idx_fib_pivots_timeframe
    ON fibonacci_pivots(timeframe);

CREATE INDEX IF NOT EXISTS idx_fib_pivots_date
    ON fibonacci_pivots(calculation_date DESC);

CREATE INDEX IF NOT EXISTS idx_fib_pivots_ticker_timeframe
    ON fibonacci_pivots(ticker_symbol, timeframe, calculation_date DESC);

-- Create function to automatically update updated_at timestamp
CREATE OR REPLACE FUNCTION update_fib_pivots_updated_at()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- Create trigger to call the update function
CREATE TRIGGER trigger_update_fib_pivots_timestamp
    BEFORE UPDATE ON fibonacci_pivots
    FOR EACH ROW
    EXECUTE FUNCTION update_fib_pivots_updated_at();

-- Add comments for documentation
COMMENT ON TABLE fibonacci_pivots IS 'Stores Fibonacci-based pivot point calculations for market instruments across multiple timeframes';
COMMENT ON COLUMN fibonacci_pivots.ticker_symbol IS 'Market instrument symbol (e.g., NQ=F, ES=F, ^FTSE)';
COMMENT ON COLUMN fibonacci_pivots.timeframe IS 'Calculation timeframe: daily, weekly, or monthly';
COMMENT ON COLUMN fibonacci_pivots.calculation_date IS 'Date when pivots were calculated (end of period)';
COMMENT ON COLUMN fibonacci_pivots.pivot_point IS 'Central pivot point: (High + Low + Close) / 3';
COMMENT ON COLUMN fibonacci_pivots.resistance_1 IS 'First resistance: PP + 0.382 × (High - Low)';
COMMENT ON COLUMN fibonacci_pivots.resistance_2 IS 'Second resistance: PP + 0.618 × (High - Low)';
COMMENT ON COLUMN fibonacci_pivots.resistance_3 IS 'Third resistance: PP + 1.000 × (High - Low)';
COMMENT ON COLUMN fibonacci_pivots.support_1 IS 'First support: PP - 0.382 × (High - Low)';
COMMENT ON COLUMN fibonacci_pivots.support_2 IS 'Second support: PP - 0.618 × (High - Low)';
COMMENT ON COLUMN fibonacci_pivots.support_3 IS 'Third support: PP - 1.000 × (High - Low)';

-- Grant permissions (adjust as needed for your environment)
-- GRANT SELECT, INSERT, UPDATE ON fibonacci_pivots TO your_app_user;
-- GRANT USAGE, SELECT ON SEQUENCE fibonacci_pivots_id_seq TO your_app_user;
