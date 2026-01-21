-- =============================================================================
-- Skills-Fleet Taxonomy Seed Data
-- Description: Initial taxonomy categories for skill organization
-- =============================================================================

-- =============================================================================
-- ROOT CATEGORIES
-- =============================================================================

-- Development
INSERT INTO taxonomy_categories (path, name, description, parent_id, level, sort_order) VALUES
('development', 'Development', 'Software development and programming skills', NULL, 0, 1),
('operations', 'Operations', 'DevOps, infrastructure, and deployment', NULL, 0, 2),
('data', 'Data', 'Data engineering, analytics, and ML', NULL, 0, 3),
('communication', 'Communication', 'Communication and collaboration skills', NULL, 0, 4),
('research', 'Research', 'Research and analysis capabilities', NULL, 0, 5);

-- =============================================================================
-- DEVELOPMENT SUB-CATEGORIES
-- =============================================================================

-- Languages
INSERT INTO taxonomy_categories (path, name, description, parent_id, level, sort_order) VALUES
('development/languages', 'Languages', 'Programming languages',
 (SELECT category_id FROM taxonomy_categories WHERE path = 'development'), 1, 1),
('development/languages/python', 'Python', 'Python programming',
 (SELECT category_id FROM taxonomy_categories WHERE path = 'development/languages'), 2, 1),
('development/languages/typescript', 'TypeScript', 'TypeScript programming',
 (SELECT category_id FROM taxonomy_categories WHERE path = 'development/languages'), 2, 2),
('development/languages/javascript', 'JavaScript', 'JavaScript programming',
 (SELECT category_id FROM taxonomy_categories WHERE path = 'development/languages'), 2, 3),
('development/languages/go', 'Go', 'Go programming',
 (SELECT category_id FROM taxonomy_categories WHERE path = 'development/languages'), 2, 4),
('development/languages/rust', 'Rust', 'Rust programming',
 (SELECT category_id FROM taxonomy_categories WHERE path = 'development/languages'), 2, 5);

-- Frameworks
INSERT INTO taxonomy_categories (path, name, description, parent_id, level, sort_order) VALUES
('development/frameworks', 'Frameworks', 'Web and application frameworks',
 (SELECT category_id FROM taxonomy_categories WHERE path = 'development'), 1, 2),
('development/frameworks/fastapi', 'FastAPI', 'FastAPI framework',
 (SELECT category_id FROM taxonomy_categories WHERE path = 'development/frameworks'), 2, 1),
('development/frameworks/react', 'React', 'React framework',
 (SELECT category_id FROM taxonomy_categories WHERE path = 'development/frameworks'), 2, 2),
('development/frameworks/dspy', 'DSPy', 'DSPy framework for programmatic prompting',
 (SELECT category_id FROM taxonomy_categories WHERE path = 'development/frameworks'), 2, 3);

-- Practices
INSERT INTO taxonomy_categories (path, name, description, parent_id, level, sort_order) VALUES
('development/practices', 'Practices', 'Development practices and methodologies',
 (SELECT category_id FROM taxonomy_categories WHERE path = 'development'), 1, 3),
('development/practices/tdd', 'Test-Driven Development', 'TDD workflow and practices',
 (SELECT category_id FROM taxonomy_categories WHERE path = 'development/practices'), 2, 1),
('development/practices/testing', 'Testing', 'Testing strategies and frameworks',
 (SELECT category_id FROM taxonomy_categories WHERE path = 'development/practices'), 2, 2),
('development/practices/refactoring', 'Refactoring', 'Code refactoring techniques',
 (SELECT category_id FROM taxonomy_categories WHERE path = 'development/practices'), 2, 3),
('development/practices/code-review', 'Code Review', 'Code review practices',
 (SELECT category_id FROM taxonomy_categories WHERE path = 'development/practices'), 2, 4);

-- =============================================================================
-- OPERATIONS SUB-CATEGORIES
-- =============================================================================

INSERT INTO taxonomy_categories (path, name, description, parent_id, level, sort_order) VALUES
('operations/deployment', 'Deployment', 'Deployment strategies and tools',
 (SELECT category_id FROM taxonomy_categories WHERE path = 'operations'), 1, 1),
('operations/deployment/docker', 'Docker', 'Containerization with Docker',
 (SELECT category_id FROM taxonomy_categories WHERE path = 'operations/deployment'), 2, 1),
('operations/deployment/kubernetes', 'Kubernetes', 'Kubernetes orchestration',
 (SELECT category_id FROM taxonomy_categories WHERE path = 'operations/deployment'), 2, 2),
('operations/monitoring', 'Monitoring', 'Monitoring and observability',
 (SELECT category_id FROM taxonomy_categories WHERE path = 'operations'), 1, 2),
('operations/cicd', 'CI/CD', 'Continuous integration and deployment',
 (SELECT category_id FROM taxonomy_categories WHERE path = 'operations'), 1, 3);

-- =============================================================================
-- DATA SUB-CATEGORIES
-- =============================================================================

INSERT INTO taxonomy_categories (path, name, description, parent_id, level, sort_order) VALUES
('data/analytics', 'Analytics', 'Data analytics and visualization',
 (SELECT category_id FROM taxonomy_categories WHERE path = 'data'), 1, 1),
('data/ml', 'Machine Learning', 'Machine learning and AI',
 (SELECT category_id FROM taxonomy_categories WHERE path = 'data'), 1, 2),
('data/databases', 'Databases', 'Database design and management',
 (SELECT category_id FROM taxonomy_categories WHERE path = 'data'), 1, 3),
('data/databases/postgresql', 'PostgreSQL', 'PostgreSQL database',
 (SELECT category_id FROM taxonomy_categories WHERE path = 'data/databases'), 2, 1),
('data/databases/redis', 'Redis', 'Redis caching',
 (SELECT category_id FROM taxonomy_categories WHERE path = 'data/databases'), 2, 2);

-- =============================================================================
-- COMMUNICATION SUB-CATEGORIES
-- =============================================================================

INSERT INTO taxonomy_categories (path, name, description, parent_id, level, sort_order) VALUES
('communication/documentation', 'Documentation', 'Technical documentation',
 (SELECT category_id FROM taxonomy_categories WHERE path = 'communication'), 1, 1),
('communication/collaboration', 'Collaboration', 'Team collaboration tools',
 (SELECT category_id FROM taxonomy_categories WHERE path = 'communication'), 1, 2),
('communication/presentation', 'Presentation', 'Presentation skills',
 (SELECT category_id FROM taxonomy_categories WHERE path = 'communication'), 1, 3);

-- =============================================================================
-- RESEARCH SUB-CATEGORIES
-- =============================================================================

INSERT INTO taxonomy_categories (path, name, description, parent_id, level, sort_order) VALUES
('research/analysis', 'Analysis', 'Analytical research',
 (SELECT category_id FROM taxonomy_categories WHERE path = 'research'), 1, 1),
('research/investigation', 'Investigation', 'Investigative research',
 (SELECT category_id FROM taxonomy_categories WHERE path = 'research'), 1, 2),
('research/synthesis', 'Synthesis', 'Research synthesis',
 (SELECT category_id FROM taxonomy_categories WHERE path = 'research'), 1, 3);

-- =============================================================================
-- UPDATE CLOSURE TABLE
-- =============================================================================
-- This trigger will automatically update the closure table
-- But we need to call it manually since the data was inserted
SELECT update_dependency_closure();  -- Note: This function name is for dependencies, we need taxonomy closure

-- Actually, let's build the taxonomy closure table directly
INSERT INTO taxonomy_closure (ancestor_id, descendant_id, depth)
WITH RECURSIVE category_tree AS (
    -- Base case: each category is its own ancestor with depth 0
    SELECT category_id, category_id, 0
    FROM taxonomy_categories

    UNION ALL

    -- Recursive case: find all descendants
    SELECT
        ct.ancestor_id,
        tc.category_id,
        ct.depth + 1
    FROM category_tree ct
    JOIN taxonomy_categories tc ON tc.parent_id = ct.descendant_id
    WHERE ct.ancestor_id != tc.category_id  -- Prevent cycles
)
SELECT DISTINCT ancestor_id, descendant_id, depth
FROM category_tree
ORDER BY ancestor_id, depth;

-- =============================================================================
-- VERIFICATION QUERY
-- =============================================================================
-- Run this to verify the taxonomy was seeded correctly:
-- SELECT path, name, level FROM taxonomy_categories ORDER BY path;
