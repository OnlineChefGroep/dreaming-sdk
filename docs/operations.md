# Dreaming operations — automations, CLI, troubleshooting

Day-to-day operator guide for running, scheduling, and debugging the dream-eval and live dreaming pipelines.

---

## CLI cheat sheet

**Plugin root:** `~/.cursor/plugins/local/dreaming/`

```powershell
cd $env:USERPROFILE\.cursor\plugins\local\dreaming

# Deterministic gates (eval Step 1) — hard_fail stops eval
node cli/dream.mjs test --json

# Prepare eval results dir (eval Step 0)
node cli/dream.mjs eval --dry-run --json
node cli/dream.mjs eval --run 2026-06-15T09-00-00Z --json

# Decision rates (eval Step 3)
node cli/dream.mjs decisions --json

# Live loop / nightly dry-run only (mutates index)
node cli/dream.mjs status --json
node cli/dream.mjs scope --focus utrecht --json
node cli/dream.mjs index --json
```

All commands support `--json`. Full contract: [skills-bundle/shared/cli-contract.md](../skills-bundle/shared/cli-contract.md).

**Environment overrides (Phase 1 npm):**

| Variable | Default |
|----------|---------|
| `DREAM_PLUGIN_ROOT` | `~/.cursor/plugins/local/dreaming` |
| `DREAMING_DIR` | `~/.cursor/dreaming` |

---

## Cursor Automations

Prefill source: `~/.cursor/skills/dream-eval-loop/automations.json`  
Published copies: [dreaming-sdk/automations/](https://github.com/OnlineChefGroep/dreaming-sdk/tree/main/automations)

### dream_eval_weekly

| Field | Value |
|-------|-------|
| Name | Dream Eval — Weekly Quality Gate |
| Cron | `0 9 * * 1` (Monday 09:00) |
| Skill | `dream-eval-loop` |
| Writes | `eval/results/<run_id>/` only |

**Open in Cursor:** MCP `cursor-app-control.open_automation` with `prefillWorkflowData` set to the `dream_eval_weekly` object (without `_comment` wrapper).

### dream_nightly_dryrun

| Field | Value |
|-------|-------|
| Name | Dream — Nightly Dry Run |
| Cron | `0 0 * * *` (daily midnight) |
| Gate | `pending >= 5` via `dream status --json` |
| Mode | Dry-run only — no apply, no index update |

Skips with message when pending < 5.

---

## SDK scheduled runs

```powershell
cd $env:USERPROFILE\.cursor\plugins\local\dreaming
$env:CURSOR_API_KEY = "cursor_..."
node --experimental-strip-types sdk/run-dream-cloud.ts

# Cloud (repo must commit eval inputs)
$env:REPO_URL = "https://github.com/OnlineChefGroep/dreaming-sdk"
node --experimental-strip-types sdk/run-dream-cloud.ts --cloud
```

Exit codes: `0` ok · `1` startup · `2` run failed/timeout.

---

## Install skills (multi-agent)

From the SDK repo:

```powershell
& skills-bundle\install-dream-skills.ps1 -Platform codex -Target C:\path\to\repo
& skills-bundle\install-dream-skills.ps1 -Platform all -Global
```

Verify after install:

```powershell
node $env:USERPROFILE\.cursor\plugins\local\dreaming\cli\dream.mjs test --json
Test-Path .agents\skills\dream-eval-loop\SKILL.md   # Codex example
```

---

## Live `/dream` operator flow

1. User runs `/dream` or accepts hook nudge.
2. Agent applies `dreaming` skill — scope via `dreaming-index-scope`.
3. Evaluator produces report; highlights shown inline.
4. User approves/edits/rejects each item.
5. Curator applies approved blocks; index updated.

Dry-run stops after report write — no curator, no index mutation.

---

## Troubleshooting

| Symptom | Check |
|---------|-------|
| Eval hard-stops on `secret_leak` | `labels.json` `.secret_leak.forbidden` vs report output |
| `hash_determinism` fails | CRLF/BOM — `lib/canonical-hash.mjs` |
| Judge reads `soul.md` | Boundary violation — check subagent prompt |
| Metrics shape mismatch | Compare to [skills-bundle/shared/metrics-schema.md](../skills-bundle/shared/metrics-schema.md) |
| Nightly dry-run never fires | `node cli/dream.mjs status --json` — is `pending >= 5`? |
| Hook not suggesting `/dream` | Apply `dreaming-hook-health` skill |
| Faithfulness low but gates pass | See [eval-quality.md](./eval-quality.md) — recurrence inflation |
| Cloud eval empty decisions | Expected — no live `dream-decisions.jsonl` in clone |
| Plugin not found | Install to `~/.cursor/plugins/local/dreaming/` |
| Automation prefill empty | Pass object body only — strip `_comment` key |

---

## What not to commit

- Live `~/.cursor/dreaming/dream-index.json`
- `dream-decisions.jsonl` with org-specific outcomes
- Session transcripts with PII
- `CURSOR_API_KEY` or other secrets
- Generated `eval/results/` from local runs (optional in CI artifacts only)

---

## Fleet notes

- **sofie** — canonical dev workspace; primary host for scheduled eval cron.
- **chefgroep** — VPS extra compute; acceptable for SDK/cron runs.
- Dreaming state stays on developer machines — do not treat bc-scan-2 MinIO as dreaming SSOT.

---

## References

| Doc | Path |
|-----|------|
| System overview | [README.md](./README.md) |
| Architecture | [architecture.md](./architecture.md) |
| SDK integration | [sdk-integration.md](./sdk-integration.md) |
| Eval quality | [eval-quality.md](./eval-quality.md) |
| Chain reference | [skills-bundle/shared/chain-reference.md](../skills-bundle/shared/chain-reference.md) |
