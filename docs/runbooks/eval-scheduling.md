# Runbook — eval scheduling & memory sync

Scheduled jobs that keep the memory layer fresh and run dream-eval on the fleet.

## Jobs

| Job | Where | Schedule | Command |
|-----|-------|----------|---------|
| Linear → memory sync | bc-scan-arm | hourly | `dream-memory` Prefect flow |
| Notion → memory sync | bc-scan-arm | daily 06:00 | `prefect_flow.py` (Notion pages) |
| dream-eval golden run | sofie / CI | Mon 09:00 | `node cli/dream.mjs` via `dream-eval-loop` skill |
| Nightly dry-run | sofie | daily 00:00 | pending ≥ 5 → evaluator dry-run |

## Option A — cron (simplest)

On `bc-scan-arm` (`crontab -e`):

```cron
# Linear issue sync into agent_memory every hour
0 * * * * . ~/.agent-memory.env && cd ~/Orgchefgroep/dreaming-sdk/python && SYNC_ISSUES=CHEF-308,CHEF-330 ~/.local/bin/uv run python deploy/oci/prefect_flow.py >> ~/agent-memory-sync.log 2>&1
```

## Option B — systemd timer

See `python/deploy/oci/README.md` § systemd. Create `agent-memory-sync.timer`:

```ini
# /etc/systemd/system/agent-memory-sync.timer
[Unit]
Description=Hourly Linear→memory sync
[Timer]
OnCalendar=hourly
Persistent=true
[Install]
WantedBy=timers.target
```

```bash
sudo systemctl enable --now agent-memory-sync.timer
```

## Option C — Prefect (when scaling)

```bash
uv sync --extra prefect
uv run prefect server start          # or Prefect Cloud
uv run python deploy/oci/prefect_flow.py
```

Deploy the flow with a cron schedule via `flow.serve(cron="0 * * * *")`.

## dream-eval scheduling

Reuse existing automations (no change):

| File | Schedule |
|------|----------|
| `automations/dream_eval_weekly.json` | Mon 09:00 |
| `automations/dream_nightly_dryrun.json` | daily 00:00 |

Eval metrics can be written into memory for the dashboard:

```bash
dream-memory remember --session-id "$RUN_ID" --session-type dream_eval \
  --type observation --source sdk \
  --content "$(node cli/dream.mjs eval --json)"
```

## Verify

```bash
ssh bc-scan-arm 'cd ~/Orgchefgroep/dreaming-sdk/python && uv run dream-memory recall --source linear --limit 5'
tail -f ~/agent-memory-sync.log   # on bc-scan-arm
```
