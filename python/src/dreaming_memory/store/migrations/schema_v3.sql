-- Schema version 3: Materialized views for dashboard metrics
-- Eliminates 7+ sequential queries in metrics() method

-- Dashboard metrics view: aggregated counts by day, source, type, agent
CREATE MATERIALIZED VIEW IF NOT EXISTS mv_dashboard_metrics AS
SELECT
    DATE_TRUNC('day', created_at) AS day,
    source,
    memory_type,
    session_type,
    agent_id,
    COUNT(*) AS count
FROM agent_memory
GROUP BY 1, 2, 3, 4, 5;

CREATE UNIQUE INDEX IF NOT EXISTS idx_mv_dashboard_metrics
    ON mv_dashboard_metrics (day, source, memory_type, session_type, agent_id);

-- Recent activity view: last 15 records for dashboard
CREATE MATERIALIZED VIEW IF NOT EXISTS mv_recent_activity AS
SELECT
    id,
    agent_id,
    session_id,
    session_type,
    memory_type,
    source,
    created_at,
    content
FROM agent_memory
ORDER BY created_at DESC
LIMIT 15;

CREATE UNIQUE INDEX IF NOT EXISTS idx_mv_recent_activity ON mv_recent_activity (id);

-- Triage decisions count
CREATE MATERIALIZED VIEW IF NOT EXISTS mv_triage_count AS
SELECT
    COUNT(*) AS total
FROM agent_memory
WHERE memory_type = 'decision'
  AND metadata ? 'triage';

-- Mark version 3 as applied
INSERT INTO schema_version (version, description)
VALUES (3, 'Materialized views for dashboard metrics')
ON CONFLICT (version) DO NOTHING;
