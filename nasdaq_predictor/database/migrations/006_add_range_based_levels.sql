-- Migration: Add Range-Based Reference Levels to reference_levels Table
-- Description: Extends the reference_levels table to store range-based levels (kill zones, time ranges)
-- Date: 2025-11-12
-- Author: NQP System
-- Purpose: Store high/low pairs for ICT kill zones and specific time ranges

-- Add range-based level columns to reference_levels table
-- Each range has a high and low value

-- 7:00-7:15 AM NY Range
ALTER TABLE reference_levels
ADD COLUMN IF NOT EXISTS range_0700_0715_high NUMERIC(12,2),
ADD COLUMN IF NOT EXISTS range_0700_0715_low NUMERIC(12,2);

-- 8:30-8:45 AM NY Range
ALTER TABLE reference_levels
ADD COLUMN IF NOT EXISTS range_0830_0845_high NUMERIC(12,2),
ADD COLUMN IF NOT EXISTS range_0830_0845_low NUMERIC(12,2);

-- Asian Kill Zone (1:00-5:00 AM UTC)
ALTER TABLE reference_levels
ADD COLUMN IF NOT EXISTS asian_kill_zone_high NUMERIC(12,2),
ADD COLUMN IF NOT EXISTS asian_kill_zone_low NUMERIC(12,2);

-- London Kill Zone (7:00-10:00 AM UTC)
ALTER TABLE reference_levels
ADD COLUMN IF NOT EXISTS london_kill_zone_high NUMERIC(12,2),
ADD COLUMN IF NOT EXISTS london_kill_zone_low NUMERIC(12,2);

-- NY AM Kill Zone (1:30-4:00 PM UTC / 8:30-11:00 AM ET)
ALTER TABLE reference_levels
ADD COLUMN IF NOT EXISTS ny_am_kill_zone_high NUMERIC(12,2),
ADD COLUMN IF NOT EXISTS ny_am_kill_zone_low NUMERIC(12,2);

-- NY PM Kill Zone (5:30-8:00 PM UTC / 1:30-4:00 PM ET)
ALTER TABLE reference_levels
ADD COLUMN IF NOT EXISTS ny_pm_kill_zone_high NUMERIC(12,2),
ADD COLUMN IF NOT EXISTS ny_pm_kill_zone_low NUMERIC(12,2);

-- Add indexes for querying range-based levels
CREATE INDEX IF NOT EXISTS idx_reference_levels_range_0700_0715
    ON reference_levels(range_0700_0715_high, range_0700_0715_low)
    WHERE range_0700_0715_high IS NOT NULL;

CREATE INDEX IF NOT EXISTS idx_reference_levels_range_0830_0845
    ON reference_levels(range_0830_0845_high, range_0830_0845_low)
    WHERE range_0830_0845_high IS NOT NULL;

CREATE INDEX IF NOT EXISTS idx_reference_levels_asian_kz
    ON reference_levels(asian_kill_zone_high, asian_kill_zone_low)
    WHERE asian_kill_zone_high IS NOT NULL;

CREATE INDEX IF NOT EXISTS idx_reference_levels_london_kz
    ON reference_levels(london_kill_zone_high, london_kill_zone_low)
    WHERE london_kill_zone_high IS NOT NULL;

CREATE INDEX IF NOT EXISTS idx_reference_levels_ny_am_kz
    ON reference_levels(ny_am_kill_zone_high, ny_am_kill_zone_low)
    WHERE ny_am_kill_zone_high IS NOT NULL;

CREATE INDEX IF NOT EXISTS idx_reference_levels_ny_pm_kz
    ON reference_levels(ny_pm_kill_zone_high, ny_pm_kill_zone_low)
    WHERE ny_pm_kill_zone_high IS NOT NULL;

-- Update table comment
COMMENT ON TABLE reference_levels IS 'Calculated reference price levels (single-price and range-based) for signal generation';

-- Add column comments for documentation
COMMENT ON COLUMN reference_levels.range_0700_0715_high IS 'High of 7:00-7:15 AM NY time range';
COMMENT ON COLUMN reference_levels.range_0700_0715_low IS 'Low of 7:00-7:15 AM NY time range';
COMMENT ON COLUMN reference_levels.range_0830_0845_high IS 'High of 8:30-8:45 AM NY time range';
COMMENT ON COLUMN reference_levels.range_0830_0845_low IS 'Low of 8:30-8:45 AM NY time range';
COMMENT ON COLUMN reference_levels.asian_kill_zone_high IS 'High of Asian Kill Zone (1:00-5:00 AM UTC)';
COMMENT ON COLUMN reference_levels.asian_kill_zone_low IS 'Low of Asian Kill Zone (1:00-5:00 AM UTC)';
COMMENT ON COLUMN reference_levels.london_kill_zone_high IS 'High of London Kill Zone (7:00-10:00 AM UTC)';
COMMENT ON COLUMN reference_levels.london_kill_zone_low IS 'Low of London Kill Zone (7:00-10:00 AM UTC)';
COMMENT ON COLUMN reference_levels.ny_am_kill_zone_high IS 'High of NY AM Kill Zone (1:30-4:00 PM UTC / 8:30-11:00 AM ET)';
COMMENT ON COLUMN reference_levels.ny_am_kill_zone_low IS 'Low of NY AM Kill Zone (1:30-4:00 PM UTC / 8:30-11:00 AM ET)';
COMMENT ON COLUMN reference_levels.ny_pm_kill_zone_high IS 'High of NY PM Kill Zone (5:30-8:00 PM UTC / 1:30-4:00 PM ET)';
COMMENT ON COLUMN reference_levels.ny_pm_kill_zone_low IS 'Low of NY PM Kill Zone (5:30-8:00 PM UTC / 1:30-4:00 PM ET)';

-- ============================================================================
-- END OF MIGRATION
-- ============================================================================
