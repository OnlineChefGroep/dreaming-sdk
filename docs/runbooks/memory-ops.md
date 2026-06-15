# Runbook — agent memory operations

## Architecture (deployed)

```
sofie (dev/orchestration)
   │  Tailscale
   ▼
bc-scan-arm  ── Docker ── agent-memory-pg (Postgres 16, port 5432)
   │                       volume: agent_memory_pg
   ├── qdrant / weaviate (existing vector services)
   └── llama.cpp (existing inference)
```

DSN (Tailscale): `postgresql://agentmem:***@100.68.121.19:5432/agent_memory`

## Common tasks

### Health check

```bash
ssh bc-scan-arm 'docker exec agent-memory-pg pg_isready -U agentmem'
uv run python -c "from cursor_dreaming_memory import AgentMemory; print(AgentMemory(enable_sentry=False).config.redacted())"
```

### Apply / migrate schema

```bash
uv run dream-memory init
```

### Inspect data

```bash
ssh bc-scan-arm "docker exec agent-memory-pg psql -U agentmem -d agent_memory -c \
  'SELECT session_type, source, count(*) FROM agent_memory GROUP BY 1,2 ORDER BY 3 DESC;'"
```

### Backup

```bash
ssh bc-scan-arm 'docker exec agent-memory-pg pg_dump -U agentmem agent_memory | gzip' \
  > backups/agent_memory_$(date +%F).sql.gz
```

### Restore

```bash
gunzip -c backups/agent_memory_YYYY-MM-DD.sql.gz | \
  ssh bc-scan-arm 'docker exec -i agent-memory-pg psql -U agentmem -d agent_memory'
```

### Rotate Postgres password

```bash
NEW=$(openssl rand -hex 24)
ssh bc-scan-arm "docker exec agent-memory-pg psql -U agentmem -d agent_memory -c \"ALTER USER agentmem PASSWORD '$NEW';\""
# update ~/.openclaude/.env AGENT_MEMORY_DATABASE_URL then re-run sync-env.sh
```

## Troubleshooting

| Symptom | Cause | Fix |
|---------|-------|-----|
| `connection refused` | container down / not on tailnet | `ssh bc-scan-arm 'cd ~/agent-memory && docker compose up -d'` |
| Notion 401 | token invalid | refresh `NOTION_API_KEY`, re-run `sync-env.sh` |
| Notion ingest empty | integration not invited to page | share page with the Notion integration |
| Linear "team not found" | wrong team key | set `LINEAR_TEAM_KEY=CHEF` |
| LanceDB disabled | extra not installed | `uv sync --extra semantic` |

## Security notes

- Postgres binds to `127.0.0.1` + Tailscale IP only (no public exposure).
- Secrets live in `~/.openclaude/.env` (sofie) and `~/.agent-memory.env` (nodes); never committed.
- R2 / Sentry optional; disabled until tokens provided.
