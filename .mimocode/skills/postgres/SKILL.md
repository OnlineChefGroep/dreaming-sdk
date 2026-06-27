---
name: postgres
description: Postgres database expert for schema, migrations, connection pooling, and queries
tools: read, edit, bash, grep, glob
model: standard
---

# Postgres Subagent

Expert for all Postgres-related work in cursor-dreaming-sdk.

## Responsibilities

- Schema design and migrations
- Connection pooling configuration
- Query optimization
- Index management
- Database health checks

## Key Files

- `python/src/cursor_dreaming_memory/store/postgres.py` — Main store with ConnectionPool
- `python/src/cursor_dreaming_memory/store/schema.sql` — Legacy schema (deprecated)
- `python/src/cursor_dreaming_memory/store/migrations/` — Versioned migrations
- `python/src/cursor_dreaming_memory/config.py` — FleetConfig with database_url

## Patterns

### Connection Pooling
```python
from psycopg_pool import ConnectionPool
from psycopg.rows import dict_row

self._pool = ConnectionPool(
    dsn,
    min_size=1,
    max_size=10,
    kwargs={"row_factory": dict_row},
)

with self._pool.connection() as conn:
    conn.execute("SELECT 1")
```

### Schema Migrations
- Versioned files in `store/migrations/schema_v{N}.sql`
- Tracked by `schema_version` table
- Applied automatically by `ensure_schema()`

### Query Building
- Use parameterized queries (never string interpolation)
- JSONB operations with `::jsonb` cast
- GIN indexes for content/metadata searches

## Commands

```bash
# Run migrations
cd /home/sofie/orgchefgroep/cursor-dreaming-sdk/python && uv run dream-memory init

# Check schema version
cd /home/sofie/orgchefgroep/cursor-dreaming-sdk/python && uv run dream-memory metrics
```
