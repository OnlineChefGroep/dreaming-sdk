-- agent_memory: unified insight layer for dreaming-sdk (CHEF-308)
-- Postgres remains single source of truth; LanceDB holds optional embedding refs.

CREATE EXTENSION IF NOT EXISTS "pgcrypto";

CREATE TABLE IF NOT EXISTS agent_memory (
    id          UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    agent_id    TEXT NOT NULL,
    session_id  TEXT NOT NULL,
    session_type TEXT NOT NULL,
    memory_type TEXT NOT NULL,
    content     JSONB NOT NULL DEFAULT '{}',
    source      TEXT NOT NULL,
    created_at  TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at  TIMESTAMPTZ NOT NULL DEFAULT now(),
    metadata    JSONB NOT NULL DEFAULT '{}'
);

CREATE INDEX IF NOT EXISTS idx_agent_memory_agent_id ON agent_memory (agent_id);
CREATE INDEX IF NOT EXISTS idx_agent_memory_session ON agent_memory (session_id, session_type);
CREATE INDEX IF NOT EXISTS idx_agent_memory_type ON agent_memory (memory_type);
CREATE INDEX IF NOT EXISTS idx_agent_memory_source ON agent_memory (source);
CREATE INDEX IF NOT EXISTS idx_agent_memory_created ON agent_memory (created_at DESC);
CREATE INDEX IF NOT EXISTS idx_agent_memory_content_gin ON agent_memory USING gin (content);
CREATE INDEX IF NOT EXISTS idx_agent_memory_metadata_gin ON agent_memory USING gin (metadata);

-- Lightweight trigger to keep updated_at fresh
CREATE OR REPLACE FUNCTION agent_memory_set_updated_at()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = now();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

DROP TRIGGER IF EXISTS trg_agent_memory_updated_at ON agent_memory;
CREATE TRIGGER trg_agent_memory_updated_at
    BEFORE UPDATE ON agent_memory
    FOR EACH ROW EXECUTE PROCEDURE agent_memory_set_updated_at();
