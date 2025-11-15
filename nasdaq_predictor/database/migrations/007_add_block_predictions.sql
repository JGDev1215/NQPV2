-- Migration: Add Block Predictions Table
-- Description: Creates table to store 7-block hourly predictions for market analysis
-- Date: 2025-11-14
-- Author: NQP System

-- Create block_predictions table
CREATE TABLE IF NOT EXISTS block_predictions (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    ticker_id UUID NOT NULL REFERENCES tickers(id) ON DELETE CASCADE,

    -- Time tracking
    hour_start_timestamp TIMESTAMP WITH TIME ZONE NOT NULL,
    prediction_timestamp TIMESTAMP WITH TIME ZONE NOT NULL,

    -- Core prediction data
    prediction VARCHAR(20) NOT NULL CHECK (prediction IN ('UP', 'DOWN', 'NEUTRAL')),
    confidence NUMERIC(5, 2) NOT NULL CHECK (confidence >= 0 AND confidence <= 100),
    prediction_strength VARCHAR(20) NOT NULL CHECK (prediction_strength IN ('weak', 'moderate', 'strong')),
    reference_price NUMERIC(12, 4) NOT NULL,

    -- Early bias analysis (blocks 1-2)
    early_bias VARCHAR(20) NOT NULL CHECK (early_bias IN ('UP', 'DOWN', 'NEUTRAL')),
    early_bias_strength NUMERIC(10, 4) NOT NULL,

    -- Sustained counter analysis (blocks 3-5)
    has_sustained_counter BOOLEAN NOT NULL DEFAULT FALSE,
    counter_direction VARCHAR(20) CHECK (counter_direction IS NULL OR counter_direction IN ('UP', 'DOWN', 'NEUTRAL')),

    -- Block and reference data (JSON columns for flexibility)
    block_data JSONB DEFAULT '{}',
    reference_levels JSONB DEFAULT '{}',
    deviation_at_5_7 NUMERIC(10, 4) NOT NULL DEFAULT 0,
    volatility NUMERIC(10, 4) NOT NULL DEFAULT 0,

    -- Verification fields (filled at hour end)
    blocks_6_7_close NUMERIC(12, 4),
    actual_result VARCHAR(20) CHECK (actual_result IS NULL OR actual_result IN ('CORRECT', 'WRONG', 'PENDING')),
    verified_at TIMESTAMP WITH TIME ZONE,

    -- Metadata
    metadata JSONB DEFAULT '{}',
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),

    -- Ensure unique combination of ticker and hour
    CONSTRAINT unique_block_prediction UNIQUE(ticker_id, hour_start_timestamp)
);

-- Create indexes for efficient querying
CREATE INDEX IF NOT EXISTS idx_block_predictions_ticker_id
    ON block_predictions(ticker_id);

CREATE INDEX IF NOT EXISTS idx_block_predictions_hour_start
    ON block_predictions(hour_start_timestamp DESC);

CREATE INDEX IF NOT EXISTS idx_block_predictions_ticker_hour
    ON block_predictions(ticker_id, hour_start_timestamp DESC);

CREATE INDEX IF NOT EXISTS idx_block_predictions_prediction
    ON block_predictions(prediction);

CREATE INDEX IF NOT EXISTS idx_block_predictions_verified
    ON block_predictions(actual_result) WHERE actual_result IS NOT NULL;

CREATE INDEX IF NOT EXISTS idx_block_predictions_created_at
    ON block_predictions(created_at DESC);

-- Create index on confidence for analysis queries
CREATE INDEX IF NOT EXISTS idx_block_predictions_confidence
    ON block_predictions(confidence DESC);

-- Create function to automatically update timestamps
CREATE OR REPLACE FUNCTION update_block_predictions_verified_at()
RETURNS TRIGGER AS $$
BEGIN
    IF NEW.verified_at IS NULL AND NEW.actual_result IS NOT NULL THEN
        NEW.verified_at = NOW();
    END IF;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- Create trigger to set verified_at when actual_result is set
CREATE TRIGGER trigger_set_block_predictions_verified_at
    BEFORE UPDATE ON block_predictions
    FOR EACH ROW
    WHEN (OLD.actual_result IS NULL AND NEW.actual_result IS NOT NULL)
    EXECUTE FUNCTION update_block_predictions_verified_at();

-- Add comments for documentation
COMMENT ON TABLE block_predictions IS 'Stores 7-block hourly predictions for market instruments. Each hour is divided into 7 blocks (~8.57 min each). Prediction is made at 5/7 point (~42.86 min). Verification at hour end.';

COMMENT ON COLUMN block_predictions.id IS 'Unique identifier (UUID)';
COMMENT ON COLUMN block_predictions.ticker_id IS 'Foreign key reference to tickers table';
COMMENT ON COLUMN block_predictions.hour_start_timestamp IS 'Start of the hour being analyzed (UTC)';
COMMENT ON COLUMN block_predictions.prediction_timestamp IS 'When prediction was made (at 5/7 point of hour)';

COMMENT ON COLUMN block_predictions.prediction IS 'Prediction result: UP, DOWN, or NEUTRAL';
COMMENT ON COLUMN block_predictions.confidence IS 'Confidence level 0-100 percentage';
COMMENT ON COLUMN block_predictions.prediction_strength IS 'Strength classification: weak, moderate, or strong';
COMMENT ON COLUMN block_predictions.reference_price IS 'Opening price of the hour';

COMMENT ON COLUMN block_predictions.early_bias IS 'Direction from blocks 1-2 analysis: UP, DOWN, or NEUTRAL';
COMMENT ON COLUMN block_predictions.early_bias_strength IS 'Magnitude of early bias in standard deviations';

COMMENT ON COLUMN block_predictions.has_sustained_counter IS 'Whether reversal pattern was detected in blocks 3-5';
COMMENT ON COLUMN block_predictions.counter_direction IS 'Direction if counter pattern exists: UP, DOWN, or NEUTRAL';

COMMENT ON COLUMN block_predictions.block_data IS 'JSONB with detailed OHLC data for blocks 1-7';
COMMENT ON COLUMN block_predictions.reference_levels IS 'JSONB snapshot of reference levels at prediction point';
COMMENT ON COLUMN block_predictions.deviation_at_5_7 IS 'Price deviation at prediction point in standard deviations';
COMMENT ON COLUMN block_predictions.volatility IS 'Calculated hourly volatility';

COMMENT ON COLUMN block_predictions.blocks_6_7_close IS 'Closing price of block 7 (filled during verification)';
COMMENT ON COLUMN block_predictions.actual_result IS 'Verification outcome: CORRECT, WRONG, or PENDING';
COMMENT ON COLUMN block_predictions.verified_at IS 'Timestamp when verification occurred';

COMMENT ON COLUMN block_predictions.metadata IS 'Additional metadata stored as JSONB';
COMMENT ON COLUMN block_predictions.created_at IS 'When the prediction record was created';
