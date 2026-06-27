-- Schema version 2: Add schema_version tracking table
-- This migration adds a table to track which schema versions have been applied.

CREATE TABLE IF NOT EXISTS schema_version (
    version     INTEGER PRIMARY KEY,
    applied_at  TIMESTAMPTZ NOT NULL DEFAULT now(),
    description TEXT
);

-- Mark version 1 as applied (for existing databases)
INSERT INTO schema_version (version, description)
VALUES (1, 'Initial schema')
ON CONFLICT (version) DO NOTHING;
