-- =============================================================================
-- Skills-Fleet Database Schema Migration
-- Version: 1.0.0
-- Description: Complete schema for skills management, taxonomy, jobs, and analytics
-- Database: PostgreSQL 17+
-- =============================================================================

-- =============================================================================
-- PART 1: ENUM TYPES
-- =============================================================================

-- Skill lifecycle and classification
CREATE TYPE skill_status_enum AS ENUM (
    'draft',           -- Initial creation state
    'active',          -- Published and available
    'deprecated',      -- Superseded but maintained
    'archived'         -- No longer maintained
);

CREATE TYPE skill_type_enum AS ENUM (
    'cognitive',       -- Thinking/reasoning skills
    'technical',       -- Technical implementation
    'domain',          -- Domain-specific knowledge
    'tool',            -- External tool usage
    'mcp',             -- Model Context Protocol
    'specialization',  -- Specialized capabilities
    'task_focus',      -- Task-specific focus
    'memory'           -- Memory-related skills
);

CREATE TYPE skill_weight_enum AS ENUM (
    'lightweight',     -- Minimal resource usage
    'medium',          -- Moderate resource usage
    'heavyweight'      -- High resource usage
);

CREATE TYPE load_priority_enum AS ENUM (
    'always',          -- Load in every session
    'task_specific',   -- Load for relevant tasks
    'on_demand',       -- Load only when requested
    'dormant'          -- Rarely load
);

CREATE TYPE skill_style_enum AS ENUM (
    'navigation_hub',  -- Short SKILL.md + subdirs
    'comprehensive',   -- Long self-contained
    'minimal'          -- Focused single-purpose
);

-- Relationships
CREATE TYPE dependency_type_enum AS ENUM (
    'required',        -- Hard prerequisite
    'recommended',     -- Soft recommendation
    'conflict'         -- Mutually exclusive
);

-- Jobs and workflow
CREATE TYPE job_status_enum AS ENUM (
    'pending',         -- Queued but not started
    'running',         -- Currently processing
    'pending_hitl',    -- Awaiting human input
    'completed',       -- Finished successfully
    'failed',          -- Failed with error
    'cancelled'        -- Cancelled by user
);

CREATE TYPE hitl_type_enum AS ENUM (
    'clarify',         -- Ask clarifying questions
    'confirm',         -- Confirm understanding
    'preview',         -- Preview content
    'validate',        -- Validate result
    'deep_understanding',
    'tdd_red',
    'tdd_green',
    'tdd_refactor'
);

CREATE TYPE checklist_phase_enum AS ENUM (
    'red',             -- Write failing test
    'green',           -- Verify skill works
    'refactor'         -- Close loopholes
);

-- Validation
CREATE TYPE validation_status_enum AS ENUM (
    'passed',
    'failed',
    'warnings'
);

CREATE TYPE severity_enum AS ENUM (
    'critical',
    'warning',
    'info'
);

-- File management
CREATE TYPE file_type_enum AS ENUM (
    'reference',       -- Technical documentation
    'guide',           -- How-to tutorials
    'template',        -- Code templates
    'script',          -- Utility scripts
    'example',         -- Usage demos
    'asset',           -- Static files
    'test'             -- Test cases
);

-- =============================================================================
-- PART 2: CORE TABLES
-- =============================================================================

-- -----------------------------------------------------------------------------
-- SKILLS TABLE - Primary entity
-- -----------------------------------------------------------------------------
CREATE TABLE skills (
    -- Primary key
    skill_id SERIAL PRIMARY KEY,

    -- Identity
    skill_path VARCHAR(512) NOT NULL UNIQUE,
    name VARCHAR(64) NOT NULL,
    description TEXT NOT NULL,

    -- Versioning
    version VARCHAR(20) NOT NULL DEFAULT '1.0.0',
    parent_version_id INTEGER REFERENCES skills(skill_id),

    -- Classification
    type skill_type_enum NOT NULL,
    weight skill_weight_enum NOT NULL DEFAULT 'medium',
    load_priority load_priority_enum NOT NULL DEFAULT 'task_specific',
    status skill_status_enum NOT NULL DEFAULT 'draft',
    skill_style skill_style_enum,

    -- Content
    skill_content TEXT NOT NULL,
    scope TEXT,

    -- Timestamps
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    last_modified TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    published_at TIMESTAMPTZ,

    -- Evolution tracking
    change_summary TEXT,
    integrity_hash VARCHAR(64),

    -- Performance metadata (JSONB for flexibility)
    performance_stats JSONB DEFAULT '{}',

    -- Full-text search vector (automatically updated)
    search_vector tsvector GENERATED ALWAYS AS (
        setweight(to_tsvector('english', coalesce(name, '')), 'A') ||
        setweight(to_tsvector('english', coalesce(description, '')), 'B') ||
        setweight(to_tsvector('english', coalesce(skill_content, '')), 'C')
    ) STORED,

    -- Constraints
    CONSTRAINT skill_path_format CHECK (
        skill_path ~ '^[a-z0-9_-]+(?:/[a-z0-9_-]+)*$'
    ),
    CONSTRAINT name_kebab_case CHECK (
        name ~ '^[a-z0-9]+(-[a-z0-9]+)*$'
    ),
    CONSTRAINT version_format CHECK (
        version ~ '^\d+\.\d+\.\d+$'
    ),
    CONSTRAINT valid_parent_version CHECK (
        parent_version_id IS NULL OR parent_version_id != skill_id
    )
);

-- Indexes for skills
CREATE INDEX idx_skills_path ON skills(skill_path);
CREATE INDEX idx_skills_status ON skills(status);
CREATE INDEX idx_skills_type ON skills(type);
CREATE INDEX idx_skills_version_lookup ON skills(skill_path, version);
CREATE INDEX idx_skills_parent_version ON skills(parent_version_id);
CREATE INDEX idx_skills_created_at ON skills(created_at DESC);
CREATE INDEX idx_skills_published_at ON skills(published_at DESC) WHERE published_at IS NOT NULL;

-- Full-text search index
CREATE INDEX idx_skills_search ON skills USING GIN(search_vector);

-- Composite indexes for common queries
CREATE INDEX idx_skills_status_type ON skills(status, type) WHERE status = 'active';
CREATE INDEX idx_skills_status_priority ON skills(status, load_priority) WHERE status = 'active';

-- Trigger to update last_modified
CREATE OR REPLACE FUNCTION update_last_modified()
RETURNS TRIGGER AS $$
BEGIN
    NEW.last_modified = NOW();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER trigger_skills_last_modified
    BEFORE UPDATE ON skills
    FOR EACH ROW
    EXECUTE FUNCTION update_last_modified();

-- =============================================================================
-- PART 3: TAXONOMY & ORGANIZATION
-- =============================================================================

-- -----------------------------------------------------------------------------
-- TAXONOMY CATEGORIES - Hierarchical organization
-- -----------------------------------------------------------------------------
CREATE TABLE taxonomy_categories (
    category_id SERIAL PRIMARY KEY,
    path VARCHAR(512) NOT NULL UNIQUE,
    name VARCHAR(128) NOT NULL,
    description TEXT,
    parent_id INTEGER REFERENCES taxonomy_categories(category_id),
    level INTEGER NOT NULL DEFAULT 0,
    sort_order INTEGER DEFAULT 0,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),

    CONSTRAINT category_no_loop CHECK (
        parent_id IS NULL OR parent_id != category_id
    )
);

CREATE INDEX idx_taxonomy_path ON taxonomy_categories(path);
CREATE INDEX idx_taxonomy_parent ON taxonomy_categories(parent_id);
CREATE INDEX idx_taxonomy_level ON taxonomy_categories(level);

-- Closure table for efficient tree queries
CREATE TABLE taxonomy_closure (
    ancestor_id INTEGER NOT NULL REFERENCES taxonomy_categories(category_id) ON DELETE CASCADE,
    descendant_id INTEGER NOT NULL REFERENCES taxonomy_categories(category_id) ON DELETE CASCADE,
    depth INTEGER NOT NULL,
    PRIMARY KEY (ancestor_id, descendant_id)
);

CREATE INDEX idx_taxonomy_closure_ancestor ON taxonomy_closure(ancestor_id);
CREATE INDEX idx_taxonomy_closure_descendant ON taxonomy_closure(descendant_id);
CREATE INDEX idx_taxonomy_closure_depth ON taxonomy_closure(depth);

-- -----------------------------------------------------------------------------
-- SKILL-TAXONOMY MAPPING - Many-to-many relationship
-- -----------------------------------------------------------------------------
CREATE TABLE skill_categories (
    skill_id INTEGER NOT NULL REFERENCES skills(skill_id) ON DELETE CASCADE,
    category_id INTEGER NOT NULL REFERENCES taxonomy_categories(category_id) ON DELETE CASCADE,
    is_primary BOOLEAN NOT NULL DEFAULT FALSE,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    PRIMARY KEY (skill_id, category_id)
);

CREATE INDEX idx_skill_categories_skill ON skill_categories(skill_id);
CREATE INDEX idx_skill_categories_category ON skill_categories(category_id);
CREATE INDEX idx_skill_categories_primary ON skill_categories(is_primary) WHERE is_primary = TRUE;

-- -----------------------------------------------------------------------------
-- ALIASES - Legacy path support
-- -----------------------------------------------------------------------------
CREATE TABLE skill_aliases (
    alias_id SERIAL PRIMARY KEY,
    skill_id INTEGER NOT NULL REFERENCES skills(skill_id) ON DELETE CASCADE,
    alias_path VARCHAR(512) NOT NULL,
    reason TEXT,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),

    UNIQUE (skill_id, alias_path),
    CONSTRAINT alias_path_format CHECK (
        alias_path ~ '^[a-z0-9_.-]+(?:/[a-z0-9_.-]+)*$'
    )
);

CREATE INDEX idx_skill_aliases_path ON skill_aliases(alias_path);
CREATE INDEX idx_skill_aliases_skill ON skill_aliases(skill_id);

-- -----------------------------------------------------------------------------
-- FACETS - Multi-dimensional filtering
-- -----------------------------------------------------------------------------
CREATE TABLE skill_facets (
    skill_id INTEGER NOT NULL REFERENCES skills(skill_id) ON DELETE CASCADE,
    facet_key VARCHAR(64) NOT NULL,
    facet_value VARCHAR(256) NOT NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    PRIMARY KEY (skill_id, facet_key, facet_value)
);

CREATE INDEX idx_skill_facets_key_value ON skill_facets(facet_key, facet_value);
CREATE INDEX idx_skill_facets_skill ON skill_facets(skill_id);

-- Facet lookup table for validation
CREATE TABLE facet_definitions (
    facet_key VARCHAR(64) PRIMARY KEY,
    allowed_values TEXT[],
    description TEXT,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- =============================================================================
-- PART 4: CAPABILITIES & DEPENDENCIES
-- =============================================================================

-- -----------------------------------------------------------------------------
-- CAPABILITIES - What skills can do
-- -----------------------------------------------------------------------------
CREATE TABLE capabilities (
    capability_id SERIAL PRIMARY KEY,
    skill_id INTEGER NOT NULL REFERENCES skills(skill_id) ON DELETE CASCADE,
    name VARCHAR(128) NOT NULL,
    description TEXT NOT NULL,
    test_criteria TEXT,
    sort_order INTEGER DEFAULT 0,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),

    UNIQUE (skill_id, name)
);

CREATE INDEX idx_capabilities_skill ON capabilities(skill_id);
CREATE INDEX idx_capabilities_name ON capabilities(name);

-- -----------------------------------------------------------------------------
-- DEPENDENCIES - Skill dependency graph
-- -----------------------------------------------------------------------------
CREATE TABLE skill_dependencies (
    dependency_id SERIAL PRIMARY KEY,
    dependent_id INTEGER NOT NULL REFERENCES skills(skill_id) ON DELETE CASCADE,
    dependency_skill_id INTEGER NOT NULL REFERENCES skills(skill_id) ON DELETE CASCADE,
    dependency_type dependency_type_enum NOT NULL,
    justification TEXT,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),

    UNIQUE (dependent_id, dependency_skill_id),
    CONSTRAINT no_self_dependency CHECK (
        dependent_id != dependency_skill_id
    )
);

CREATE INDEX idx_dependencies_dependent ON skill_dependencies(dependent_id);
CREATE INDEX idx_dependencies_dependency ON skill_dependencies(dependency_skill_id);
CREATE INDEX idx_dependencies_type ON skill_dependencies(dependency_type);

-- Closure table for dependency graph traversal
CREATE TABLE dependency_closure (
    ancestor_id INTEGER NOT NULL REFERENCES skills(skill_id),
    descendant_id INTEGER NOT NULL REFERENCES skills(skill_id),
    min_depth INTEGER NOT NULL,
    dependency_types TEXT[],
    PRIMARY KEY (ancestor_id, descendant_id)
);

CREATE INDEX idx_dependency_closure_ancestor ON dependency_closure(ancestor_id);
CREATE INDEX idx_dependency_closure_descendant ON dependency_closure(descendant_id);

-- -----------------------------------------------------------------------------
-- SEE ALSO - Cross-references
-- -----------------------------------------------------------------------------
CREATE TABLE skill_references (
    source_skill_id INTEGER NOT NULL REFERENCES skills(skill_id) ON DELETE CASCADE,
    target_skill_id INTEGER NOT NULL REFERENCES skills(skill_id) ON DELETE CASCADE,
    reference_type VARCHAR(32) NOT NULL DEFAULT 'see_also',
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    PRIMARY KEY (source_skill_id, target_skill_id),
    CONSTRAINT no_self_reference CHECK (
        source_skill_id != target_skill_id
    )
);

CREATE INDEX idx_skill_references_source ON skill_references(source_skill_id);
CREATE INDEX idx_skill_references_target ON skill_references(target_skill_id);

-- =============================================================================
-- PART 5: DISCOVERY & SEARCH
-- =============================================================================

-- -----------------------------------------------------------------------------
-- KEYWORDS - Search terms
-- -----------------------------------------------------------------------------
CREATE TABLE skill_keywords (
    skill_id INTEGER NOT NULL REFERENCES skills(skill_id) ON DELETE CASCADE,
    keyword VARCHAR(128) NOT NULL,
    weight FLOAT DEFAULT 1.0,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    PRIMARY KEY (skill_id, keyword)
);

CREATE INDEX idx_skill_keywords_keyword ON skill_keywords(keyword);
CREATE INDEX idx_skill_keywords_skill ON skill_keywords(skill_id);

-- -----------------------------------------------------------------------------
-- TAGS - User-defined tags
-- -----------------------------------------------------------------------------
CREATE TABLE skill_tags (
    skill_id INTEGER NOT NULL REFERENCES skills(skill_id) ON DELETE CASCADE,
    tag VARCHAR(64) NOT NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    PRIMARY KEY (skill_id, tag)
);

CREATE INDEX idx_skill_tags_tag ON skill_tags(tag);
CREATE INDEX idx_skill_tags_skill ON skill_tags(skill_id);

-- Tag popularity tracking
CREATE TABLE tag_stats (
    tag VARCHAR(64) PRIMARY KEY,
    usage_count INTEGER DEFAULT 0,
    last_used_at TIMESTAMPTZ,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- =============================================================================
-- PART 6: SKILL FILES & ASSETS
-- =============================================================================

-- -----------------------------------------------------------------------------
-- SKILL FILES - Associated files and resources
-- -----------------------------------------------------------------------------
CREATE TABLE skill_files (
    file_id SERIAL PRIMARY KEY,
    skill_id INTEGER NOT NULL REFERENCES skills(skill_id) ON DELETE CASCADE,
    file_type file_type_enum NOT NULL,
    relative_path VARCHAR(512) NOT NULL,
    filename VARCHAR(256) NOT NULL,
    content TEXT,
    binary_data BYTEA,
    file_size_bytes INTEGER,
    checksum VARCHAR(64),
    description TEXT,
    sort_order INTEGER DEFAULT 0,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),

    UNIQUE (skill_id, relative_path)
);

CREATE INDEX idx_skill_files_skill ON skill_files(skill_id);
CREATE INDEX idx_skill_files_type ON skill_files(file_type);
CREATE INDEX idx_skill_files_path ON skill_files(relative_path);

-- -----------------------------------------------------------------------------
-- ALLOWED TOOLS - Tools a skill can use
-- -----------------------------------------------------------------------------
CREATE TABLE skill_allowed_tools (
    skill_id INTEGER NOT NULL REFERENCES skills(skill_id) ON DELETE CASCADE,
    tool_name VARCHAR(64) NOT NULL,
    required BOOLEAN NOT NULL DEFAULT FALSE,
    description TEXT,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    PRIMARY KEY (skill_id, tool_name)
);

CREATE INDEX idx_skill_allowed_tools_tool ON skill_allowed_tools(tool_name);
CREATE INDEX idx_skill_allowed_tools_skill ON skill_allowed_tools(skill_id);

-- =============================================================================
-- PART 7: JOBS & WORKFLOW
-- =============================================================================

-- -----------------------------------------------------------------------------
-- JOBS - Background job tracking
-- -----------------------------------------------------------------------------
CREATE TABLE jobs (
    job_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    status job_status_enum NOT NULL DEFAULT 'pending',
    job_type VARCHAR(64) NOT NULL DEFAULT 'skill_creation',

    -- User context
    user_id VARCHAR(128) NOT NULL DEFAULT 'default',
    user_context JSONB DEFAULT '{}',

    -- Task description
    task_description TEXT NOT NULL,
    task_description_refined TEXT,

    -- Progress tracking
    current_phase VARCHAR(64),
    progress_message TEXT,
    progress_percent INTEGER DEFAULT 0,

    -- Results
    result JSONB,
    error TEXT,
    error_stack TEXT,

    -- Draft lifecycle
    intended_taxonomy_path VARCHAR(512),
    draft_path TEXT,
    final_path TEXT,
    promoted BOOLEAN NOT NULL DEFAULT FALSE,

    -- Validation results
    validation_passed BOOLEAN,
    validation_status validation_status_enum,
    validation_score FLOAT,

    -- Timestamps
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    started_at TIMESTAMPTZ,
    completed_at TIMESTAMPTZ,

    -- Metadata
    metadata JSONB DEFAULT '{}'
);

CREATE INDEX idx_jobs_status ON jobs(status);
CREATE INDEX idx_jobs_user ON jobs(user_id);
CREATE INDEX idx_jobs_created_at ON jobs(created_at DESC);
CREATE INDEX idx_jobs_type ON jobs(job_type);
CREATE INDEX idx_jobs_promoted ON jobs(promoted) WHERE promoted = FALSE;
CREATE INDEX idx_jobs_polling ON jobs(user_id, created_at DESC)
    WHERE status IN ('pending', 'running', 'pending_hitl');

CREATE TRIGGER trigger_jobs_updated_at
    BEFORE UPDATE ON jobs
    FOR EACH ROW
    EXECUTE FUNCTION update_last_modified();

-- -----------------------------------------------------------------------------
-- HITL INTERACTIONS - Human-in-the-Loop tracking
-- -----------------------------------------------------------------------------
CREATE TABLE hitl_interactions (
    interaction_id SERIAL PRIMARY KEY,
    job_id UUID NOT NULL REFERENCES jobs(job_id) ON DELETE CASCADE,
    interaction_type hitl_type_enum NOT NULL,
    round_number INTEGER NOT NULL DEFAULT 1,
    prompt_data JSONB NOT NULL,
    response_data JSONB,
    responded_at TIMESTAMPTZ,
    status VARCHAR(32) NOT NULL DEFAULT 'pending',
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    timeout_at TIMESTAMPTZ,
    metadata JSONB DEFAULT '{}'
);

CREATE INDEX idx_hitl_job ON hitl_interactions(job_id);
CREATE INDEX idx_hitl_type ON hitl_interactions(interaction_type);
CREATE INDEX idx_hitl_status ON hitl_interactions(status);
CREATE INDEX idx_hitl_created_at ON hitl_interactions(created_at DESC);

-- -----------------------------------------------------------------------------
-- DEEP UNDERSTANDING STATE
-- -----------------------------------------------------------------------------
CREATE TABLE deep_understanding_state (
    state_id SERIAL PRIMARY KEY,
    job_id UUID NOT NULL REFERENCES jobs(job_id) ON DELETE CASCADE,
    questions_asked JSONB DEFAULT '[]',
    answers JSONB DEFAULT '[]',
    research_performed JSONB DEFAULT '[]',
    understanding_summary TEXT,
    user_problem TEXT,
    user_goals TEXT[],
    readiness_score FLOAT DEFAULT 0.0,
    complete BOOLEAN NOT NULL DEFAULT FALSE,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),

    UNIQUE (job_id)
);

-- -----------------------------------------------------------------------------
-- TDD WORKFLOW STATE
-- -----------------------------------------------------------------------------
CREATE TABLE tdd_workflow_state (
    state_id SERIAL PRIMARY KEY,
    job_id UUID NOT NULL REFERENCES jobs(job_id) ON DELETE CASCADE,
    phase VARCHAR(32),
    baseline_tests_run BOOLEAN NOT NULL DEFAULT FALSE,
    compliance_tests_run BOOLEAN NOT NULL DEFAULT FALSE,
    rationalizations_identified TEXT[],
    checklist_state JSONB NOT NULL DEFAULT '{}',
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),

    UNIQUE (job_id)
);

-- =============================================================================
-- PART 8: VALIDATION & QUALITY
-- =============================================================================

-- -----------------------------------------------------------------------------
-- VALIDATION REPORTS
-- -----------------------------------------------------------------------------
CREATE TABLE validation_reports (
    report_id SERIAL PRIMARY KEY,
    skill_id INTEGER REFERENCES skills(skill_id) ON DELETE SET NULL,
    job_id UUID REFERENCES jobs(job_id) ON DELETE SET NULL,
    status validation_status_enum NOT NULL,
    passed BOOLEAN NOT NULL,
    score FLOAT NOT NULL CHECK (score BETWEEN 0 AND 1),
    errors TEXT[],
    warnings TEXT[],
    checks_performed TEXT[],
    quality_score FLOAT,
    completeness_score FLOAT,
    compliance_score FLOAT,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),

    CONSTRAINT validation_target_check CHECK (
        (skill_id IS NOT NULL)::integer + (job_id IS NOT NULL)::integer >= 1
    )
);

CREATE INDEX idx_validation_reports_skill ON validation_reports(skill_id);
CREATE INDEX idx_validation_reports_job ON validation_reports(job_id);
CREATE INDEX idx_validation_reports_status ON validation_reports(status);
CREATE INDEX idx_validation_reports_created_at ON validation_reports(created_at DESC);

-- -----------------------------------------------------------------------------
-- VALIDATION CHECKS
-- -----------------------------------------------------------------------------
CREATE TABLE validation_checks (
    check_id SERIAL PRIMARY KEY,
    report_id INTEGER NOT NULL REFERENCES validation_reports(report_id) ON DELETE CASCADE,
    check_name VARCHAR(128) NOT NULL,
    check_description TEXT,
    severity severity_enum NOT NULL DEFAULT 'info',
    passed BOOLEAN NOT NULL DEFAULT TRUE,
    required BOOLEAN NOT NULL DEFAULT TRUE,
    message TEXT,
    error_details TEXT,
    category VARCHAR(64),
    sort_order INTEGER DEFAULT 0
);

CREATE INDEX idx_validation_checks_report ON validation_checks(report_id);
CREATE INDEX idx_validation_checks_severity ON validation_checks(severity);
CREATE INDEX idx_validation_checks_category ON validation_checks(category);

-- -----------------------------------------------------------------------------
-- TEST COVERAGE
-- -----------------------------------------------------------------------------
CREATE TABLE skill_test_coverage (
    coverage_id SERIAL PRIMARY KEY,
    skill_id INTEGER NOT NULL REFERENCES skills(skill_id) ON DELETE CASCADE,
    total_tests INTEGER DEFAULT 0,
    passing_tests INTEGER DEFAULT 0,
    failing_tests INTEGER DEFAULT 0,
    skipped_tests INTEGER DEFAULT 0,
    coverage_percent FLOAT,
    unit_tests INTEGER DEFAULT 0,
    integration_tests INTEGER DEFAULT 0,
    e2e_tests INTEGER DEFAULT 0,
    last_run_at TIMESTAMPTZ,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),

    UNIQUE (skill_id, created_at)
);

CREATE INDEX idx_test_coverage_skill ON skill_test_coverage(skill_id);
CREATE INDEX idx_test_coverage_created_at ON skill_test_coverage(created_at DESC);

-- =============================================================================
-- PART 9: ANALYTICS & USAGE TRACKING
-- =============================================================================

-- -----------------------------------------------------------------------------
-- USAGE EVENTS
-- -----------------------------------------------------------------------------
CREATE TABLE usage_events (
    event_id BIGSERIAL PRIMARY KEY,
    skill_id INTEGER NOT NULL REFERENCES skills(skill_id),
    user_id VARCHAR(128) NOT NULL,
    task_id UUID,
    success BOOLEAN NOT NULL DEFAULT TRUE,
    duration_ms INTEGER,
    error_type VARCHAR(64),
    session_id UUID,
    metadata JSONB DEFAULT '{}',
    occurred_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX idx_usage_events_skill ON usage_events(skill_id);
CREATE INDEX idx_usage_events_user ON usage_events(user_id);
CREATE INDEX idx_usage_events_occurred_at ON usage_events(occurred_at DESC);
CREATE INDEX idx_usage_events_task ON usage_events(task_id) WHERE task_id IS NOT NULL;
CREATE INDEX idx_usage_events_skill_time ON usage_events(skill_id, occurred_at DESC);

-- -----------------------------------------------------------------------------
-- SKILL STATISTICS - Materialized view
-- -----------------------------------------------------------------------------
CREATE MATERIALIZED VIEW skill_statistics AS
SELECT
    s.skill_id,
    s.skill_path,
    s.name,
    s.status,
    s.type,
    s.weight,
    s.created_at,
    s.published_at,
    COALESCE(COUNT(DISTINCT ue.user_id), 0) as unique_users,
    COALESCE(COUNT(ue.event_id), 0) as total_uses,
    COALESCE(AVG(ue.success::integer), 0) as success_rate,
    COALESCE(AVG(ue.duration_ms), 0) as avg_duration_ms,
    (SELECT COUNT(*) FROM skill_dependencies WHERE dependent_id = s.skill_id) as dependency_count,
    (SELECT COUNT(*) FROM skill_dependencies WHERE dependency_skill_id = s.skill_id) as dependent_count,
    (SELECT COUNT(*) FROM validation_reports WHERE skill_id = s.skill_id) as validation_count,
    (SELECT MAX(score) FROM validation_reports WHERE skill_id = s.skill_id) as max_validation_score,
    (SELECT COUNT(*) FROM skill_files WHERE skill_id = s.skill_id) as file_count,
    NOW() as last_updated
FROM skills s
LEFT JOIN usage_events ue ON ue.skill_id = s.skill_id
    AND ue.occurred_at > NOW() - INTERVAL '30 days'
GROUP BY s.skill_id, s.skill_path, s.name, s.status, s.type, s.weight, s.created_at, s.published_at
WITH DATA;

CREATE UNIQUE INDEX idx_skill_statistics_id ON skill_statistics(skill_id);
CREATE INDEX idx_skill_statistics_status ON skill_statistics(status);
CREATE INDEX idx_skill_statistics_uses ON skill_statistics(total_uses DESC);

-- -----------------------------------------------------------------------------
-- OPTIMIZATION JOBS
-- -----------------------------------------------------------------------------
CREATE TABLE optimization_jobs (
    job_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    optimizer VARCHAR(64) NOT NULL,
    auto_config VARCHAR(32) NOT NULL DEFAULT 'medium',
    max_bootstrapped_demos INTEGER NOT NULL DEFAULT 4,
    max_labeled_demos INTEGER NOT NULL DEFAULT 4,
    trainset_file TEXT,
    training_skills TEXT[],
    status VARCHAR(32) NOT NULL DEFAULT 'pending',
    result_score FLOAT,
    optimized_program_path TEXT,
    training_time_seconds INTEGER,
    validation_metrics JSONB,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    started_at TIMESTAMPTZ,
    completed_at TIMESTAMPTZ,
    error TEXT,
    error_stack TEXT
);

CREATE INDEX idx_optimization_jobs_status ON optimization_jobs(status);
CREATE INDEX idx_optimization_jobs_created_at ON optimization_jobs(created_at DESC);
CREATE INDEX idx_optimization_jobs_optimizer ON optimization_jobs(optimizer);

-- =============================================================================
-- PART 10: VIEWS FOR COMMON QUERIES
-- =============================================================================

-- Active skills with all metadata
CREATE VIEW active_skills_view AS
SELECT
    s.skill_id,
    s.skill_path,
    s.name,
    s.description,
    s.version,
    s.type,
    s.weight,
    s.load_priority,
    s.skill_style,
    s.status,
    s.skill_content,
    s.scope,
    s.created_at,
    s.last_modified,
    s.published_at,
    ARRAY(
        SELECT DISTINCT keyword FROM skill_keywords
        WHERE skill_id = s.skill_id
        ORDER BY keyword
    ) as keywords,
    ARRAY(
        SELECT tag FROM skill_tags
        WHERE skill_id = s.skill_id
        ORDER BY tag
    ) as tags,
    ARRAY(
        SELECT c.name FROM capabilities c
        WHERE c.skill_id = s.skill_id
        ORDER BY c.sort_order
    ) as capabilities,
    (
        SELECT json_agg(json_build_object(
            'skill_id', d2.skill_path,
            'type', sd.dependency_type,
            'justification', sd.justification
        ))
        FROM skill_dependencies sd
        JOIN skills d2 ON sd.dependency_skill_id = d2.skill_id
        WHERE sd.dependent_id = s.skill_id
    ) as dependencies,
    (
        SELECT json_build_object(
            'passed', vr.passed,
            'score', vr.score,
            'status', vr.status,
            'created_at', vr.created_at
        )
        FROM validation_reports vr
        WHERE vr.skill_id = s.skill_id
        ORDER BY vr.created_at DESC
        LIMIT 1
    ) as latest_validation
FROM skills s
WHERE s.status = 'active';

-- Draft skills awaiting promotion
CREATE VIEW draft_skills_view AS
SELECT
    j.job_id,
    j.user_id,
    j.task_description,
    j.intended_taxonomy_path,
    j.draft_path,
    j.validation_passed,
    j.validation_score,
    j.created_at,
    j.updated_at,
    j.result->'metadata' as skill_metadata
FROM jobs j
WHERE j.status = 'completed'
    AND j.promoted = FALSE
    AND j.draft_path IS NOT NULL
ORDER BY j.created_at DESC;

-- Popular skills
CREATE VIEW popular_skills_view AS
SELECT
    s.skill_id,
    s.skill_path,
    s.name,
    s.description,
    s.type,
    s.weight,
    s.published_at,
    ss.total_uses,
    ss.unique_users,
    ss.success_rate,
    ss.avg_duration_ms,
    ROW_NUMBER() OVER (ORDER BY ss.total_uses DESC) as popularity_rank
FROM skills s
JOIN skill_statistics ss ON s.skill_id = ss.skill_id
WHERE s.status = 'active'
    AND ss.total_uses > 0
ORDER BY ss.total_uses DESC;

-- Skills needing attention
CREATE VIEW skills_attention_view AS
SELECT
    s.skill_id,
    s.skill_path,
    s.name,
    s.status,
    s.type,
    CASE
        WHEN s.status = 'deprecated' THEN 'deprecated'
        WHEN EXISTS (
            SELECT 1 FROM validation_reports vr
            WHERE vr.skill_id = s.skill_id AND vr.status = 'failed'
            ORDER BY vr.created_at DESC LIMIT 1
        ) THEN 'validation_failed'
        WHEN s.created_at < NOW() - INTERVAL '6 months' THEN 'outdated'
        WHEN NOT EXISTS (
            SELECT 1 FROM usage_events ue
            WHERE ue.skill_id = s.skill_id
            AND ue.occurred_at > NOW() - INTERVAL '90 days'
        ) THEN 'unused'
        ELSE NULL
    END as attention_flag,
    (SELECT vr.created_at FROM validation_reports vr WHERE vr.skill_id = s.skill_id ORDER BY vr.created_at DESC LIMIT 1) as last_validated_at,
    (SELECT ue.occurred_at FROM usage_events ue WHERE ue.skill_id = s.skill_id ORDER BY ue.occurred_at DESC LIMIT 1) as last_used_at
FROM skills s
WHERE s.status IN ('active', 'deprecated')
ORDER BY s.created_at DESC;

-- =============================================================================
-- PART 11: FUNCTIONS & MAINTENANCE
-- =============================================================================

-- Function to refresh materialized view
CREATE OR REPLACE FUNCTION refresh_skill_statistics()
RETURNS void AS $$
BEGIN
    REFRESH MATERIALIZED VIEW CONCURRENTLY skill_statistics;
END;
$$ LANGUAGE plpgsql;

-- Function to update dependency closure table
CREATE OR REPLACE FUNCTION update_dependency_closure()
RETURNS void AS $$
BEGIN
    -- Clear existing closure
    TRUNCATE TABLE dependency_closure;

    -- Rebuild closure table
    INSERT INTO dependency_closure (ancestor_id, descendant_id, min_depth, dependency_types)
    WITH RECURSIVE dep_tree AS (
        -- Base case: direct dependencies
        SELECT
            dependent_id as ancestor_id,
            dependency_skill_id as descendant_id,
            1 as min_depth,
            ARRAY[dependency_type::text] as dependency_types
        FROM skill_dependencies

        UNION ALL

        -- Recursive case: transitive dependencies
        SELECT
            dt.ancestor_id,
            sd.dependency_skill_id,
            dt.min_depth + 1,
            dt.dependency_types || sd.dependency_type::text
        FROM dep_tree dt
        JOIN skill_dependencies sd ON dt.descendant_id = sd.dependent_id
        WHERE dt.ancestor_id != sd.dependency_skill_id
           AND NOT EXISTS (
               SELECT 1 FROM dependency_closure dc
               WHERE dc.ancestor_id = dt.ancestor_id
               AND dc.descendant_id = sd.dependency_skill_id
           )
    )
    SELECT DISTINCT ON (ancestor_id, descendant_id)
        ancestor_id, descendant_id, min_depth, dependency_types
    FROM dep_tree;
END;
$$ LANGUAGE plpgsql;

-- =============================================================================
-- PART 12: SAMPLE DATA (OPTIONAL)
-- =============================================================================

-- Insert some initial facet definitions
INSERT INTO facet_definitions (facet_key, allowed_values, description) VALUES
    ('lang', ARRAY['python', 'typescript', 'javascript', 'go', 'rust'], 'Programming language'),
    ('domain', ARRAY['web', 'data', 'ml', 'devops', 'mobile'], 'Technical domain'),
    ('type', ARRAY['pattern', 'framework', 'library', 'tool'], 'Skill type'),
    ('maturity', ARRAY['experimental', 'stable', 'deprecated'], 'Maturity level');

-- =============================================================================
-- MIGRATION COMPLETE
-- =============================================================================

-- Grant permissions (adjust as needed)
-- GRANT ALL PRIVILEGES ON ALL TABLES IN SCHEMA public TO your_app_user;
-- GRANT ALL PRIVILEGES ON ALL SEQUENCES IN SCHEMA public TO your_app_user;
-- GRANT EXECUTE ON ALL FUNCTIONS IN SCHEMA public TO your_app_user;
