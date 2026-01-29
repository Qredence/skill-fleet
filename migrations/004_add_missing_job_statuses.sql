-- =============================================================================
-- Migration: 004_add_missing_job_statuses
-- Description: Add missing job status enum values for HITL workflow
-- =============================================================================

-- Add missing status values to job_status_enum
-- Note: PostgreSQL requires ALTER TYPE to add enum values

-- Add 'pending_user_input' status
ALTER TYPE job_status_enum ADD VALUE IF NOT EXISTS 'pending_user_input';

-- Add 'pending_review' status
ALTER TYPE job_status_enum ADD VALUE IF NOT EXISTS 'pending_review';

-- Verify the changes
COMMENT ON TYPE job_status_enum IS 'Extended job statuses including HITL states: pending, running, pending_hitl, pending_user_input, pending_review, completed, failed, cancelled';
