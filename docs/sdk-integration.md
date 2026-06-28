# SDK integration — dream-eval / dreaming pipeline

How the dreaming plugin eval loop is consumed by Cursor SDK, OpenCode/Codex, generic HTTP/webhook callers, and future npm packages — without duplicating logic that belongs in the plugin.

**Plugin SSOT:** `~/.cursor/plugins/local/dreaming/`  
**Integration kit:** [OnlineChefGroep/cursor-dreaming-sdk](https://github.com/OnlineChefGroep/cursor-dreaming-sdk)

---

## Scope

The dreaming plugin is the source of truth for:

- CLI driver (`cli/dream.mjs`, `cli/dream-test.mjs`)
- Golden corpus, pinned soul, JSON schemas
- Subagent specs (`dream-evaluator`, `dream-judge`, `dream-curator`)
- Skills (`dream-eval`, `dream-eval-loop`, `dreaming`)
- SDK driver (`sdk/run-dream-cloud.ts`)

The export repo **dreaming-sdk** holds integration artifacts — automation templates, SDK examples, schema copies, and docs — not a fork of the plugin. Consumers install the plugin locally and use the SDK repo for orchestration patterns.

| Layer | Lives in | Exportable? |
|-------|----------|-------------|
| Plugin runtime | `~/.cursor/plugins/local/dreaming/` | Phase 0–1: extract CLI only |
| Orchestrator skills | `~/.cursor/skills/dream-eval-loop/` | Copy/sync to repo `skills-bundle/` |
| Automation prefill | `automations.json` | Yes → repo `automations/` |
| SDK driver | plugin `sdk/run-dream-cloud.ts` | Yes → repo `sdk/` (thin wrapper) |
| Golden corpus + soul snapshot | plugin `eval/` | Commit subset for cloud CI |
| Live state | `~/.cursor/dreaming/` | **Never** exported |

---

## Consumer surfaces

### Cursor SDK (`@cursor/sdk`)

**Pattern:** `sdk/run-dream-cloud.ts` sends a fixed prompt naming `dream-eval` / `dream-eval-loop`; the agent runs the 6-step loop and writes `eval/results/<run_id>/`.

| Mode | Command | When |
|------|---------|------|
| Local | `node --experimental-strip-types sdk/run-dream-cloud.ts` | Uses caller's `~/.cursor/dreaming/` and plugin path |
| Cloud | `REPO_URL=https://github.com/org/repo node … --cloud` | Fresh VM clone; **must** commit eval inputs |

**Env vars:** `CURSOR_API_KEY`, `CURSOR_MODEL`, `REPO_URL` (cloud), `EVAL_TIMEOUT_MS`, `EVAL_MAX_RETRIES`, `EVAL_RETRY_BASE_MS`.

**Exit codes:** `0` success · `1` startup failed (`CursorAgentError`) · `2` run failed (error/timeout).

**Scheduled eval:** GitHub Actions cron, Cursor Automation, or local cron on fleet nodes (sofie, chefgroep).

### OpenCode / Codex / Claude / Grok (skill-only)

No SDK required. Install skills from [skills-bundle/](../skills-bundle/):

| Skill | Role |
|-------|------|
| `dream-eval-loop` | Unattended eval orchestrator (6 steps) |
| `dream-eval` | Canonical metrics + loop spec |
| `dream-evaluator` | Readonly report generation (plugin subagent) |
| `dream-judge` | Faithfulness scoring (never reads `soul.md`) |

**Invocation:** "Apply the dream-eval-loop skill to run one golden corpus evaluation pass."

**Limitation:** Non-Cursor hosts have no Automation UI; use cron + shell or GitHub Actions.

Full platform matrix: [multi-agent.md](./multi-agent.md).

### Generic HTTP / webhook (Phase 3)

A small service (or GitHub `repository_dispatch`) accepts:

```json
{
  "mode": "golden",
  "run_id": "optional-iso-stem",
  "callback_url": "https://…/dream-eval-result"
}
```

Response artifacts: `metrics.json`, `summary.md`, optional run id.

**Interim:** GitHub Action receives webhook → runs `run-dream-cloud.ts` → uploads artifacts → POSTs summary to Slack/Notion.

### Cursor Automations (cron)

Prefill payloads in `~/.cursor/skills/dream-eval-loop/automations.json` and repo `automations/`:

| Key | Schedule | Purpose |
|-----|----------|---------|
| `dream_eval_weekly` | `0 9 * * 1` (Mon 09:00) | Full golden eval via `dream-eval-loop` |
| `dream_nightly_dryrun` | `0 0 * * *` | Pending ≥ 5 → dry-run report, no apply |

Open via MCP `cursor-app-control.open_automation` with `prefillWorkflowData` = object body (no `_comment` wrapper). See [operations.md](./operations.md).

---

## CLI API surface

Entry: `node cli/dream.mjs <command> [--json]`

| Subcommand | Purpose | Key JSON fields |
|------------|---------|-----------------|
| `test` | Deterministic gates | `hard_fail`, per-test pass/fail |
| `eval` | Prepare `eval/results/<run_id>/` | `run_id`, `corpus_path`, `prepared` |
| `status` | Reconcile index, pending counts | `pending`, `last_dream` |
| `scope` | In-scope pending sessions | `in_scope[]`, `--focus` filter |
| `index` | Index summary | `status_counts`, `runs` |
| `decisions` | W1 acceptance/regret | `rates`, `acceptance_rate_overall` |

**Hard-stop gates:** `secret_leak`, `hash_determinism` → `hard_fail: true` stops the eval loop.

Full JSON shapes: [skills-bundle/shared/cli-contract.md](../skills-bundle/shared/cli-contract.md).

### `metrics.json` (25 top-level keys)

Canonical shape — downstream dashboards parse these names verbatim. Full reference: [skills-bundle/shared/metrics-schema.md](../skills-bundle/shared/metrics-schema.md) and [eval-quality.md](./eval-quality.md).

### Decision log

One JSON object per line. Schema: `schema/dream-decisions.schema.json`. CLI aggregation: `dream decisions --json`.

---

## Multi-tenant paths

| Path | Scope | Override |
|------|-------|----------|
| `~/.cursor/dreaming/` | Org/user global | `DREAMING_DIR` |
| `~/.cursor/plugins/local/dreaming/` | Plugin install | `DREAM_PLUGIN_ROOT` |
| Repo `.cursor/dreaming/` | Repo-local (W2) | Preferred over global |
| `eval/results/<run_id>/` | Per-run artifacts | Repo-relative in cloud CI |

**Rule:** Eval loop writes **only** `eval/results/<run_id>/`. Live `/dream` writes global/repo memory via `dream-curator`.

---

## Package boundaries

```
dreaming plugin (local install, not npm)
  cli/ · lib/ · skills/ · schema/ · eval/ · hooks/ · sdk/
        │
        ▼ documents + thin wrappers
@onlinechefgroep/dream-cli (Phase 1 npm, optional)
        │
        ▼
dreaming-sdk repo
  automations/ · sdk/examples · skills-bundle/ · docs/
```

**Stay in plugin:** subagent prompts, golden corpus content, hook, canonical-hash lib.  
**Export to repo:** automation JSON, SDK example, JSON Schema copies, integration docs, CI templates.

---

## Phased rollout

### Phase 0 — Extract CLI (current)

- [x] `cli/dream.mjs` subcommands documented
- [x] `dream-eval-loop` skill + `automations.json`
- [x] Live eval baseline (`2026-06-15T07-17-00Z`, faithfulness 0.63)
- [x] Docs + skills bundle in `dreaming-sdk`
- [ ] Copy golden corpus subset into SDK repo for cloud CI

### Phase 1 — npm `@onlinechefgroep/dream-cli`

- Thin wrapper around `cli/dream.mjs` + schemas (no bundled LLM)
- `bin: dream` → delegates to plugin if present
- JSON Schema validation for `metrics.json` (dev dependency `ajv`)
- Python shim optional

### Phase 2 — Automation templates + CI

- Commit `automations/*.json` with templateId mapping
- GitHub Action: weekly SDK run → artifact upload
- Slack/Notion post step on `summary.md`

### Phase 3 — Webhook API

- `POST /v1/dream/eval` → queue run → return `run_id`
- `GET /v1/dream/eval/:run_id` → metrics + signed artifact URLs
- Optional MCP wrapper for headless agents without shell

Multi-agent distribution phases: [multi-agent.md](./multi-agent.md).

---

## Eval loop vs live dream loop

| | Eval loop | Live `/dream` |
|--|-----------|---------------|
| Trigger | Cron, SDK, `/dream-eval` | Chat, hook nudge |
| Writes | `eval/results/<run_id>/` only | `~/.cursor/dreaming/`, AGENTS.md |
| Subagents | evaluator + judge | evaluator + curator |
| User | Unattended | Must approve apply |

---

## Experiment contract (weekly gate)

- **Hypothesis:** Weekly automated eval catches faithfulness drift before production `/dream` runs.
- **Primary metric:** Days between regression introduction and detection.
- **Guardrail:** False-positive hard-stop rate < 20%.
- **Stop condition:** No regressions caught after 4 weekly runs → revert to on-demand only.
- **Baseline:** faithfulness **0.63** — alert if week-over-week Δ > 0.10 down.

---

## References

| Artifact | Path |
|----------|------|
| Plugin root | `~/.cursor/plugins/local/dreaming/` |
| SDK driver | `sdk/run-dream-cloud.ts` |
| Eval loop skill | `~/.cursor/skills/dream-eval-loop/SKILL.md` |
| Chain reference | [skills-bundle/shared/chain-reference.md](../skills-bundle/shared/chain-reference.md) |
| Target repo | https://github.com/OnlineChefGroep/cursor-dreaming-sdk |
