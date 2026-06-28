---
name: schema-migrator
description: Handle database schema migrations safely
model: standard
context: none
---

# Schema Migrator Subagent

Focused subagent for database schema changes.

## Responsibilities

- Create versioned migration files
- Apply migrations safely
- Verify schema state
- Rollback if needed

## Spawn Pattern

```
actor({
  operation: "run",
  subagent_type: "general",
  description: "Create migration for new column",
  prompt: "Create schema_v3.sql to add 'tags' column...",
  context: "none"
})
```

## Migration Pattern

```sql
-- schema_v{N}.sql
-- Description of what this migration does

-- DDL statements with IF NOT EXISTS
ALTER TABLE agent_memory ADD COLUMN IF NOT EXISTS tags JSONB DEFAULT '[]';

-- Indexes
CREATE INDEX IF NOT EXISTS idx_agent_memory_tags ON agent_memory USING gin (tags);
```

## Safety Rules

1. **Always use IF NOT EXISTS** — Idempotent migrations
2. **Never drop columns** — Add new, deprecate old
3. **Track in schema_version** — Auto-inserted by ensure_schema()
4. **Test rollback** — Every migration should be reversible

## Commands

```bash
# Apply pending migrations
cd /home/sofie/orgchefgroep/cursor-dreaming-sdk/python && uv run dream-memory init

# Check current version
cd /home/sofie/orgchefgroep/cursor-dreaming-sdk/python && uv run dream-memory metrics
```

## File Locations

- Migrations: `python/src/dreaming_memory/store/migrations/`
- Current schema: `python/src/dreaming_memory/store/schema.sql` (legacy)
