-- =============================================================================
-- Migration: 005_add_hitl_columns_to_jobs
-- Description: Add hitl_type and hitl_data columns to jobs table
-- =============================================================================

-- Add hitl_type column to jobs table
ALTER TABLE jobs 
ADD COLUMN IF NOT EXISTS hitl_type VARCHAR(32) DEFAULT NULL;

-- Add hitl_data column to jobs table (JSONB for flexibility)
ALTER TABLE jobs 
ADD COLUMN IF NOT EXISTS hitl_data JSONB DEFAULT NULL;

-- Create index for hitl_type lookups
CREATE INDEX IF NOT EXISTS idx_jobs_hitl_type ON jobs(hitl_type) 
WHERE hitl_type IS NOT NULL;

-- Add comment explaining columns
COMMENT ON COLUMN jobs.hitl_type IS 'Type of HITL interaction: clarify, confirm, preview, validate, etc.';
COMMENT ON COLUMN jobs.hitl_data IS 'HITL-specific data including questions, prompts, and context';
