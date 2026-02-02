-- =============================================================================
-- Migration: Add Conversation Sessions Table
-- Version: 0.3.0
-- Description: Database-backed conversation session storage (replaces in-memory dict)
-- =============================================================================

-- -----------------------------------------------------------------------------
-- ENUM: Conversation workflow states
-- -----------------------------------------------------------------------------
CREATE TYPE conversation_state_enum AS ENUM (
    'EXPLORING',            -- Understanding user intent, asking clarifying questions
    'DEEP_UNDERSTANDING',   -- Asking WHY questions, researching context
    'MULTI_SKILL_DETECTED', -- Multiple skills needed, presenting breakdown
    'CONFIRMING',           -- Presenting confirmation summary before creation
    'READY',                -- User confirmed, ready to create skill
    'CREATING',             -- Executing skill creation workflow
    'TDD_RED_PHASE',        -- Running baseline tests without skill
    'TDD_GREEN_PHASE',      -- Verifying skill works with tests
    'TDD_REFACTOR_PHASE',   -- Closing loopholes, re-testing
    'REVIEWING',            -- Presenting skill for user feedback
    'REVISING',             -- Processing feedback and regenerating
    'CHECKLIST_COMPLETE',   -- TDD checklist fully complete
    'COMPLETE'              -- Skill approved, saved, ready for next
);

-- -----------------------------------------------------------------------------
-- TABLE: conversation_sessions
-- -----------------------------------------------------------------------------
CREATE TABLE conversation_sessions (
    -- Primary key
    session_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),

    -- User context
    user_id VARCHAR(128) NOT NULL DEFAULT 'default',

    -- Workflow state
    state conversation_state_enum NOT NULL DEFAULT 'EXPLORING',
    task_description TEXT,
    taxonomy_path VARCHAR(512),

    -- Multi-skill support
    multi_skill_queue TEXT[] DEFAULT '{}',
    current_skill_index INTEGER DEFAULT 0,

    -- Conversation data (JSONB for flexibility)
    messages JSONB DEFAULT '[]',
    collected_examples JSONB DEFAULT '[]',

    -- Draft data
    skill_draft JSONB,
    skill_metadata_draft JSONB,

    -- TDD workflow
    checklist_state JSONB DEFAULT '{}',

    -- Pending confirmations
    pending_confirmation JSONB,

    -- Deep understanding phase
    deep_understanding JSONB,
    current_understanding TEXT,

    -- User problem/goals
    user_problem TEXT,
    user_goals TEXT[],

    -- Research context
    research_context JSONB,

    -- Session metadata
    metadata JSONB DEFAULT '{}',

    -- Timestamps
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    last_activity_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    expires_at TIMESTAMPTZ DEFAULT NOW() + INTERVAL '24 hours',

    -- Optional job association
    job_id UUID REFERENCES jobs(job_id) ON DELETE SET NULL
);

-- -----------------------------------------------------------------------------
-- INDEXES
-- -----------------------------------------------------------------------------

-- User lookup
CREATE INDEX idx_sessions_user ON conversation_sessions(user_id);

-- State filtering
CREATE INDEX idx_sessions_state ON conversation_sessions(state);

-- Time-based queries
CREATE INDEX idx_sessions_created_at ON conversation_sessions(created_at DESC);
CREATE INDEX idx_sessions_last_activity ON conversation_sessions(last_activity_at DESC);

-- Expiration cleanup
CREATE INDEX idx_sessions_expires_at ON conversation_sessions(expires_at)
    WHERE expires_at IS NOT NULL;

-- Active sessions per user
CREATE INDEX idx_sessions_active ON conversation_sessions(user_id, last_activity_at DESC)
    WHERE state NOT IN ('COMPLETE');

-- Job association
CREATE INDEX idx_sessions_job ON conversation_sessions(job_id)
    WHERE job_id IS NOT NULL;

-- -----------------------------------------------------------------------------
-- TRIGGER: Auto-update updated_at timestamp
-- -----------------------------------------------------------------------------
CREATE TRIGGER trigger_sessions_updated_at
    BEFORE UPDATE ON conversation_sessions
    FOR EACH ROW
    EXECUTE FUNCTION update_last_modified();

-- -----------------------------------------------------------------------------
-- VIEW: Active sessions summary
-- -----------------------------------------------------------------------------
CREATE VIEW active_sessions_view AS
SELECT
    cs.session_id,
    cs.user_id,
    cs.state,
    cs.task_description,
    cs.taxonomy_path,
    jsonb_array_length(cs.messages) as message_count,
    cs.created_at,
    cs.last_activity_at,
    cs.expires_at,
    cs.job_id
FROM conversation_sessions cs
WHERE cs.state != 'COMPLETE'
    AND (cs.expires_at IS NULL OR cs.expires_at > NOW())
ORDER BY cs.last_activity_at DESC;

-- -----------------------------------------------------------------------------
-- FUNCTION: Cleanup expired sessions
-- -----------------------------------------------------------------------------
CREATE OR REPLACE FUNCTION cleanup_expired_sessions()
RETURNS INTEGER AS $$
DECLARE
    deleted_count INTEGER;
BEGIN
    DELETE FROM conversation_sessions
    WHERE expires_at IS NOT NULL
        AND expires_at < NOW();

    GET DIAGNOSTICS deleted_count = ROW_COUNT;
    RETURN deleted_count;
END;
$$ LANGUAGE plpgsql;

-- =============================================================================
-- MIGRATION COMPLETE
-- =============================================================================
