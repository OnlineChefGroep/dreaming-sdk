# Agent memory layer (CHEF-308)

Lightweight development memory for **dreaming-sdk**, backed by Postgres with optional LanceDB semantic search. Designed for Oracle Cloud Ampere A1 and future dashboard integration.

## Architecture

```
dreaming-sdk session forms
        │
        ▼
  SessionContext (normalize session_id, session_type, agent_id)
        │
        ▼
   AgentMemory facade
   ├── AgentMemoryStore (Postgres SSOT — agent_memory table)
   ├── SemanticMemoryStore (optional LanceDB via embedding_ref)
   ├── LinearMemoryBridge (issues + comments ↔ memory)
   └── NotionMemoryBridge (pages ↔ memory)
```

Postgres is the **single source of truth**. LanceDB stores vectors only; each row links back via `memory_type=embedding_ref` and `metadata.lance_memory_id`.

## Session type mapping

Compatible with all SDK / multi-agent surfaces ([multi-agent.md](./multi-agent.md)):

| SDK surface | `session_type` |
|-------------|----------------|
| Cursor IDE | `cursor` |
| Claude Code | `claude` |
| Codex | `codex` |
| OpenCode | `opencode` |
| Grok/Factory | `grok` |
| SDK local (`run-dream-cloud.ts`) | `sdk_local` |
| SDK cloud | `sdk_cloud` |
| Golden eval (`dream eval`) | `dream_eval` |
| Live `/dream` | `dream_live` |
| Unknown | `generic` |

Use `SessionContext.from_sdk_payload()` to normalize dream-index entries, agent run payloads, or transcript hashes.

## Postgres schema

Table `agent_memory`:

| Column | Type | Description |
|--------|------|-------------|
| `id` | UUID | Primary key |
| `agent_id` | TEXT | Agent identifier |
| `session_id` | TEXT | Run id, transcript hash, or external ref |
| `session_type` | TEXT | SDK session form |
| `memory_type` | TEXT | `fact`, `observation`, `issue_snapshot`, … |
| `content` | JSONB | Structured payload |
| `source` | TEXT | `linear`, `notion`, `tool`, `user`, `sdk` |
| `created_at` / `updated_at` | TIMESTAMPTZ | Audit |
| `metadata` | JSONB | External ids, labels, embedding refs |

Apply schema:

```bash
cd python && uv run dream-memory init
```

## Linear integration

Aligned with `utrecht-data-os/scripts/linear_api.py`:

- **Read:** `memory.linear.ingest_issue("CHEF-308", ctx)` — stores issue + comments
- **Write:** `memory.linear.create_issue_from_memory(ctx, title, desc)`
- **Comment:** `memory.linear.comment_from_memory(ctx, issue_id, body)`

Requires `LINEAR_API_KEY` (and optionally `LINEAR_TEAM_ID`).

## Notion integration

- **Read:** `memory.notion.ingest_page(page_id, ctx)`
- **Write:** `memory.notion.append_from_memory(ctx, page_id, text)`

Requires `NOTION_API_KEY` or `NOTION_TOKEN`.

## Semantic memory (optional)

```bash
pip install cursor-dreaming-memory[semantic]
export LANCE_DB_URI=./data/lancedb   # or s3://bucket/path for R2
```

```python
record = memory.remember(ctx, MemoryType.FACT, {"text": "..."})
memory.index_semantic(record, "searchable text", vector=[...])
hits = memory.search_semantic(query_vector)
```

## Deployment status (live)

Postgres SSOT runs in Docker on the Ampere A1 node `bc-scan-arm`, reachable over
Tailscale at `100.68.121.19:5432` (db `agent_memory`, user `agentmem`). Bound to
localhost + Tailscale only — no public exposure.

| Concern | Where |
|---------|-------|
| OCI provisioning / compose | [python/deploy/oci/README.md](../python/deploy/oci/README.md) |
| Fleet env + CLI wiring | [python/deploy/fleet/README.md](../python/deploy/fleet/README.md) |
| Ops (backup, rotate, troubleshoot) | [runbooks/memory-ops.md](./runbooks/memory-ops.md) |
| Eval & sync scheduling | [runbooks/eval-scheduling.md](./runbooks/eval-scheduling.md) |
| Agent CLI usage contract | [skills-bundle/shared/agent-memory.md](../skills-bundle/shared/agent-memory.md) |

Secrets resolve from `~/.openclaude/.env` (sofie) and `~/.agent-memory.env` (nodes)
via `FleetConfig.load()` / `load_fleet_secrets()`.

## Integrations status

| Integration | Status |
|-------------|--------|
| Postgres SSOT | live on bc-scan-arm |
| Linear (team `CHEF`) | connected |
| Notion | token valid; share pages with the integration to ingest |
| Cloudflare R2 (semantic) | wired, optional — set `R2_ACCESS_KEY_ID` / `R2_SECRET_ACCESS_KEY` |
| Sentry | wired, optional — set `SENTRY_DSN` |

## Dashboard readiness

All records are JSON-serializable via `MemoryRecord.model_dump()`. Query by `session_type`, `source`, or `memory_type` for dashboard filters. No heavy graph DB in development phase.

## Package location

```
dreaming-sdk/python/
  src/cursor_dreaming_memory/
  examples/linear_memory_flow.py
  deploy/oci/
  tests/
```

## Fleet config & secrets

`FleetConfig` (in `config.py`) resolves secrets from `os.environ` → fleet env
file (`~/.openclaude/.env` or `~/.config/agent-memory/.env`). It never writes
secrets to the repo. Check status safely:

```bash
dream-memory doctor   # prints presence booleans + redacted values + DB ping
```

Supported integrations wired through config:

| Integration | Keys | Module |
|-------------|------|--------|
| Postgres SSOT | `AGENT_MEMORY_DATABASE_URL` | `store/postgres.py`, `store/oci.py` |
| Linear | `LINEAR_API_KEY`, `LINEAR_TEAM_ID` | `integrations/linear.py` |
| Notion | `NOTION_API_KEY` / `NOTION_TOKEN` | `integrations/notion.py` |
| Cloudflare R2 | `CLOUDFLARE_*`, `R2_*` | `integrations/cloudflare.py` |
| Sentry | `SENTRY_DSN`, `SENTRY_ENVIRONMENT` | `observability/sentry.py` |
| Upstash Redis | `UPSTASH_REDIS_REST_URL/TOKEN` | (config only, optional cache) |

## Runbooks

- [oci-postgres-bootstrap.md](./runbooks/oci-postgres-bootstrap.md) — OCI A1 Postgres SSOT
- [fleet-agent-wiring.md](./runbooks/fleet-agent-wiring.md) — connect all agent CLIs across the fleet
- [eval-scheduling.md](./runbooks/eval-scheduling.md) — systemd timers + Prefect sync

## Related docs

- [architecture.md](./architecture.md) — dreaming plugin state model
- [sdk-integration.md](./sdk-integration.md) — session / eval loop boundaries
- [multi-agent.md](./multi-agent.md) — platform session forms
