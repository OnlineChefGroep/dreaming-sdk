# Runbook — agent memory operations

## Architecture (deployed)

```text
<dev-orchestration-host>
   │  private mesh network
   ▼
<agent-memory-host> ── Docker ── agent-memory-pg
   │
   ├── vector services
   └── local inference services
```

Keep concrete hostnames, private addresses, tailnet names, and runtime credentials in the private ops repo or runtime env files only.

## Common tasks

### Health check

```bash
ssh <agent-memory-host> 'docker exec agent-memory-pg pg_isready -U agentmem'
uv run python -c "from dreaming_memory import AgentMemory; print(AgentMemory(enable_sentry=False).config.redacted())"
```

### Apply / migrate schema

```bash
uv run dream-memory init
```

### Inspect data

```bash
ssh <agent-memory-host> "docker exec agent-memory-pg psql -U agentmem -d agent_memory -c \
  'SELECT session_type, source, count(*) FROM agent_memory GROUP BY 1,2 ORDER BY 3 DESC;'"
```

### Backup

```bash
ssh <agent-memory-host> 'docker exec agent-memory-pg pg_dump -U agentmem agent_memory | gzip' \
  > backups/agent_memory_$(date +%F).sql.gz
```

### Restore

```bash
gunzip -c backups/agent_memory_YYYY-MM-DD.sql.gz | \
  ssh <agent-memory-host> 'docker exec -i agent-memory-pg psql -U agentmem -d agent_memory'
```

## Troubleshooting

| Symptom | Cause | Fix |
|---------|-------|-----|
| `connection refused` | container down / not on private mesh | `ssh <agent-memory-host> 'cd ~/agent-memory && docker compose up -d'` |
| Notion 401 | token invalid | refresh `NOTION_API_KEY`, re-run env sync |
| Notion ingest empty | integration not invited to page | share page with the Notion integration |
| Linear "team not found" | wrong team ID | set `LINEAR_TEAM_ID=<team-uuid>` |
| LanceDB disabled | extra not installed | `uv sync --extra semantic` |

## Security notes

- Postgres should bind only to localhost and private mesh addresses, never public interfaces.
- Runtime credentials live in private env files and must not be committed.
- R2 / Sentry optional; disabled until tokens provided.
