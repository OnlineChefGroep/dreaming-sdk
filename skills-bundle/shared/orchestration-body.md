# Dream eval loop — orchestration body (shared)

Platform SKILL.md files include this document by reference. Do not duplicate the 6-step loop in per-platform files.

## Purpose

Unattended quality gate for the dreaming plugin. Runs deterministic tests, golden corpus eval, faithfulness scoring, and metrics tracking. **Does not** apply memory or mutate `AGENTS.md` or `~/.cursor/dreaming/`.

## Plugin root

All paths relative to `~/.cursor/plugins/local/dreaming/` unless noted.

| Resource | Path |
|----------|------|
| Golden corpus | `eval/golden-corpus/` |
| Pinned soul | `eval/soul-snapshot.md` |
| Schemas | `schema/dream-index.schema.json`, `schema/dream-decisions.schema.json` |
| CLI | `cli/dream.mjs` |
| Eval output | `eval/results/<run_id>/` |
| Decision log (read-only) | `~/.cursor/dreaming/dream-decisions.jsonl` |

## 6-step loop

### Step 0 — Resolve run identity + pin soul

1. Generate `run_id` as filename-safe ISO8601 stem (e.g. `2026-06-15T09-00-00Z`).
2. SHA-256 `eval/soul-snapshot.md` (canonical: strip BOM, CRLF→LF) → `soul_version`.
3. `mkdir eval/results/<run_id>/`.

### Step 1 — Deterministic gates + report

```shell
cd ~/.cursor/plugins/local/dreaming
node cli/dream.mjs test --json
```

If `hard_fail: true` (secret_leak or hash_determinism) → **STOP**. Report failure first.

Then delegate to **dream-evaluator** (readonly):

- Isolated eval workspace (temp copy of golden corpus + throwaway index + pinned soul).
- Produces dream report over golden transcripts.
- Record `token_cost`, `latency`.
- **Never** write to live `~/.cursor/dreaming/`.

### Step 2 — Faithfulness scoring

Delegate to **dream-judge** (readonly):

**Inputs:** report, `eval/golden-corpus/transcripts/`, `~/.cursor/AGENTS.md`, `eval/golden-corpus/labels.json`  
**Forbidden:** `soul.md` (any path)

**Outputs:** `faithfulness_score`, `precision`, `recall`, `recurrence_calibration`, flags.

### Step 3 — Decision metrics

```shell
node cli/dream.mjs decisions --json
```

Golden-only runs: acceptance/regret may be `null` — note "no live outcomes this run".

### Step 4 — Merge metrics

Write `eval/results/<run_id>/metrics.json` — all 25 keys, canonical names. See `shared/metrics-schema.md`.

### Step 5 — Summary

Write `eval/results/<run_id>/summary.md`:

```markdown
# Dream eval <run_id>

**Gates:** secret-leak <pass|FAIL> · privilege <pass|FAIL> · schema <pass|FAIL>

- Faithfulness: <faithfulness_score>
- Precision / Recall: <precision> / <recall>
- Recurrence calibration: <recurrence_calibration>
- Acceptance rate (overall): <acceptance_rate.overall or "n/a">
- Regret rate: <regret_rate or "n/a">
- Items proposed: <items_proposed> · token cost: <token_cost> · latency: <latency>

Top flags:
- <flags or "none">
```

Return summary to caller. Lead with hard failures if any gate failed.

## Guardrails

- Eval writes **only** `eval/results/<run_id>/`.
- `dream-judge` and `dream-curator` must **never** read `soul.md`.
- `dream-curator` is **not** used in the eval loop.
- Do not call `status`/`scope`/`index` during golden eval (they reconcile live index).
- Use canonical metric names verbatim.

## Experiment contract

- **Hypothesis:** Weekly eval catches faithfulness drift before production `/dream` runs.
- **Primary metric:** Days between regression introduction and detection.
- **Guardrail:** False-positive hard-stop rate < 20%.
- **Stop:** No regressions caught after 4 weekly runs → on-demand only.
- **Baseline:** faithfulness **0.63** (run `2026-06-15T07-17-00Z`).

## Further reading

- Handoff tables: `shared/chain-reference.md`
- CLI JSON shapes: `shared/cli-contract.md`
- Metrics keys: `shared/metrics-schema.md`
