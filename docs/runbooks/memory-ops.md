# Runbook — agent memory operations

## Architecture (deployed)

```text
<dev-orchestration-host>
   │  private mesh network
   ▼
<agent-memory-host> ── Docker ── agent-memory-pg (Postgres 16, port 5432)
   │                         volume: agent_memory_pg
   ├── vector services
   └── local inference services
```

DSN template: `postgresql://agentmem:***@<private-host-or-ip>:5432/agent_memory`

Keep concrete hostnames, private IPs, tailnet names, and credentials in the private ops repo or
runtime env files only.

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

### Rotate Postgres password

```bash
NEW=$(openssl rand -hex 24)
ssh <agent-memory-host> "docker exec agent-memory-pg psql -U agentmem -d agent_memory -c \"ALTER USER agentmem PASSWORD '$NEW';\""
# update AGENT_MEMORY_DATABASE_URL in the private env source, then sync runtime env files
```

## Troubleshooting

| Symptom | Cause | Fix |
|---------|-------|-----|
| `connection refused` | container down / not on private mesh | `ssh <agent-memory-host> 'cd ~/agent-memory && docker compose up -d'` |
| Notion 401 | token invalid | refresh `NOTION_API_KEY`, re-run env sync |
| Notion ingest empty | integration not invited to page | share page with the Notion integration |
| Linear "team not found" | wrong team key | set `LINEAR_TEAM_KEY=CHEF` |
| LanceDB disabled | extra not installed | `uv sync --extra semantic` |

## Security notes

- Postgres should bind only to localhost and private mesh addresses, never public interfaces.
- Secrets live in private runtime env files; never commit concrete credentials or DSNs.
- R2 / Sentry optional; disabled until tokens provided.
