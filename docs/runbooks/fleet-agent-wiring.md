# Runbook — wire agent memory into the whole fleet

Connect every code-agent CLI (Cursor, Codex, Claude, OpenCode, Grok/Factory) on
each fleet host to the **shared OCI Postgres SSOT**, with Linear / Notion /
Cloudflare / Sentry available via fleet config.

## Fleet (OCI eu-amsterdam-1, Tailscale mesh)

| Host | Shape | Tailscale IP | Role |
|------|-------|--------------|------|
| `bc-monitor` | A1.Flex | 100.78.210.57 | Monitor / scheduler (timers) |
| `bc-scan-arm` | A1.Flex | 100.68.121.19 | **Postgres SSOT** (`agent_memory`) |
| `bc-scan-2` | A1.Flex | 100.65.83.86 | Agent worker |
| `bc-scan-1` | E2.1.Micro | 100.104.37.70 | Light worker |
| sofie (control) | local | — | Dev + deploy origin |

Postgres SSOT DSN (read at runtime, never committed):
`postgresql://agentmem:***@100.68.121.19:5432/agent_memory`

## Secret model

Single source: `~/.openclaude/.env` on the control node. Each fleet host gets a
local `~/.config/agent-memory/.env` (chmod 600) with the same keys. The Python
`FleetConfig` loader reads env → fleet file, never writing secrets to the repo.

Keys: `AGENT_MEMORY_DATABASE_URL`, `LINEAR_API_KEY`, `NOTION_API_KEY`,
`CLOUDFLARE_API_TOKEN`, `CLOUDFLARE_ACCOUNT_ID`, `SENTRY_DSN`,
`SENTRY_ENVIRONMENT`, optional `UPSTASH_REDIS_REST_URL/TOKEN`, `R2_*`.

## Deploy to all hosts

```bash
cd /home/sofie/orgchefgroep/dreaming-sdk
for h in bc-monitor bc-scan-arm bc-scan-2; do
  rsync -az --delete python/ "$h:~/cursor-dreaming-memory/"
  ssh "$h" 'bash ~/cursor-dreaming-memory/deploy/fleet/install-memory.sh'
done
```

Fill each host's `~/.config/agent-memory/.env`, then verify:

```bash
ssh bc-scan-2 'cd ~/cursor-dreaming-memory && FLEET_ENV_FILE=~/.config/agent-memory/.env uv run dream-memory doctor'
```

Expect `{"postgres": "ok"}`.

## Connect code-agent CLIs

Each agent CLI calls the memory layer the same way (platform-agnostic):

```bash
# Write a memory from any agent session
uv run --project ~/cursor-dreaming-memory dream-memory remember \
  --agent codex --session-id "$SESSION_ID" --session-type codex \
  --type observation --content '{"note":"..."}'

# Recall for a session
uv run --project ~/cursor-dreaming-memory dream-memory recall --session-id "$SESSION_ID"
```

`session_type` accepts every SDK form: `cursor`, `claude`, `codex`, `opencode`,
`grok`, `sdk_local`, `sdk_cloud`, `dream_eval`, `dream_live`, `generic`.

### Optional: shell alias on each host

```bash
echo 'alias mem="uv run --project ~/cursor-dreaming-memory dream-memory"' >> ~/.bashrc
```

Then any agent or human runs `mem remember ...`, `mem recall ...`, `mem doctor`.

## Verify the whole fleet writes to one DB

```bash
mem remember --session-id fleet-check --session-type generic \
  --content "{\"host\":\"$(hostname)\"}"
# From control node:
mem recall --session-id fleet-check    # should list rows from every host
```

## Rollback

- Stop timers: `ssh <host> 'systemctl --user disable --now agent-memory-eval.timer'`
- Remove host secrets: `ssh <host> 'rm ~/.config/agent-memory/.env'`
- Postgres stays on `bc-scan-arm`; no data loss from disabling clients.
