-- Schema version 4: Memory governance tables (CHEF-1004, CHEF-1005, CHEF-1006)
-- Adds evidence, verifier_results, and curator_decisions tables.

-- Evidence: immutable append-only log of evidence supporting memory claims
CREATE TABLE IF NOT EXISTS evidence (
    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    memory_id       UUID NOT NULL REFERENCES agent_memory(id) ON DELETE CASCADE,
    evidence_type   TEXT NOT NULL,
    source_url      TEXT,
    source_id       TEXT,
    excerpt         TEXT NOT NULL DEFAULT '',
    confidence      DOUBLE PRECISION NOT NULL DEFAULT 1.0,
    captured_at     TIMESTAMPTZ NOT NULL DEFAULT now(),
    created_at      TIMESTAMPTZ NOT NULL DEFAULT now(),
    metadata        JSONB NOT NULL DEFAULT '{}'
);

CREATE INDEX IF NOT EXISTS idx_evidence_memory_id ON evidence (memory_id);
CREATE INDEX IF NOT EXISTS idx_evidence_type ON evidence (evidence_type);

-- Verifier results: machine-readable verification outcomes for memory claims
CREATE TABLE IF NOT EXISTS verifier_results (
    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    memory_id       UUID NOT NULL REFERENCES agent_memory(id) ON DELETE CASCADE,
    status          TEXT NOT NULL DEFAULT 'pending',
    score           DOUBLE PRECISION NOT NULL DEFAULT 0.0,
    evidence_refs   UUID[] NOT NULL DEFAULT '{}',
    rationale       TEXT NOT NULL DEFAULT '',
    checked_at      TIMESTAMPTZ NOT NULL DEFAULT now(),
    checked_by      TEXT NOT NULL DEFAULT '',
    metadata        JSONB NOT NULL DEFAULT '{}'
);

CREATE INDEX IF NOT EXISTS idx_verifier_results_memory_id ON verifier_results (memory_id);
CREATE INDEX IF NOT EXISTS idx_verifier_results_status ON verifier_results (status);

-- Curator decisions: lifecycle state machine for memory governance
CREATE TABLE IF NOT EXISTS curator_decisions (
    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    memory_id       UUID NOT NULL REFERENCES agent_memory(id) ON DELETE CASCADE,
    state           TEXT NOT NULL DEFAULT 'proposed',
    decided_at      TIMESTAMPTZ NOT NULL DEFAULT now(),
    decided_by      TEXT NOT NULL DEFAULT '',
    rationale       TEXT NOT NULL DEFAULT '',
    previous_state  TEXT,
    transitions     JSONB NOT NULL DEFAULT '[]',
    metadata        JSONB NOT NULL DEFAULT '{}'
);

CREATE INDEX IF NOT EXISTS idx_curator_decisions_memory_id ON curator_decisions (memory_id);
CREATE INDEX IF NOT EXISTS idx_curator_decisions_state ON curator_decisions (state);

-- Idempotency: prevent duplicate active memory on re-ingestion (CHEF-1006)
-- A partial unique index ensures at most one non-rolled-back curator decision per memory.
CREATE UNIQUE INDEX IF NOT EXISTS idx_curator_decisions_active
    ON curator_decisions (memory_id)
    WHERE state IN ('proposed', 'reviewing', 'accepted', 'edited', 'deferred');

-- Mark version 4 as applied
INSERT INTO schema_version (version, description)
VALUES (4, 'Memory governance tables: evidence, verifier_results, curator_decisions')
ON CONFLICT (version) DO NOTHING;
