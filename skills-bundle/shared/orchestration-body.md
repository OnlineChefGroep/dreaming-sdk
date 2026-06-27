# Dream eval loop — orchestration body (shared)

Platform SKILL.md files include this document by reference. Do not duplicate the 6-step loop in per-platform files.

## Purpose

Unattended quality gate for agent memory faithfulness evaluation. Runs deterministic tests, golden corpus eval, faithfulness scoring, and metrics tracking. **Does not** apply memory or mutate live state.

## Resource paths

All paths relative to repo root.

| Resource | Path |
|----------|------|
| Golden corpus | `eval/golden-corpus/` |
| Pinned soul | `eval/soul-snapshot.md` |
| Eval output | `eval/results/<run_id>/` |
| dream-eval CLI | `uvx dream-eval` (or `cd dream-eval && uv run dream-eval`) |

## Prerequisites

```bash
# Install dream-eval
pip install dream-eval
# Or from monorepo
cd dream-eval && uv sync --extra dev
```

## 6-step loop

### Step 0 — Resolve run identity + pin soul

1. Generate `run_id` as filename-safe ISO8601 stem (e.g. `2026-06-15T09-00-00Z`).
2. SHA-256 `eval/soul-snapshot.md` (canonical: strip BOM, CRLF→LF) → `soul_version`.
3. `mkdir eval/results/<run_id>/`.

### Step 1 — Deterministic gates

```shell
# Check for secret leaks
uvx dream-eval gates --text "$(cat eval/golden-corpus/transcripts/*.jsonl)"

# Or from monorepo
cd dream-eval && uv run dream-eval gates --text "$(cat eval/golden-corpus/transcripts/*.jsonl)"
```

If `status: "fail"` (secret_leak) → **STOP**. Report failure first.

Then delegate to **dream-evaluator** (readonly):

- Isolated eval workspace (temp copy of golden corpus + pinned soul).
- Produces dream report over golden transcripts.
- Record `token_cost`, `latency`.
- **Never** write to live state.

### Step 2 — Faithfulness scoring

Delegate to **dream-judge** (readonly):

**Inputs:** report, `eval/golden-corpus/transcripts/`, `eval/golden-corpus/labels.json`
**Forbidden:** `soul.md` (any path)

**Command:**

```shell
# Create eval report from proposed items
cat > /tmp/eval-report.json << 'EOF'
{
  "items": [
    {"id": "pref-minimal-deps", "category": "pref", "content": {"key": "prefer-minimal-dependencies", "value": "true"}},
    {"id": "rule-no-secrets", "category": "rule", "content": {"key": "never-commit-secrets", "value": "true"}}
  ]
}
EOF

# Score against labels
uvx dream-eval score --report /tmp/eval-report.json --labels eval/golden-corpus/labels.json
```

**Outputs:** `faithfulness_score`, `precision`, `recall`, `recurrence_calibration`, flags.

### Step 3 — Decision metrics

For golden-only runs, acceptance/regret may be `null` — note "no live outcomes this run".

### Step 4 — Merge metrics

Write `eval/results/<run_id>/metrics.json` — all 25 keys, canonical names. See `shared/metrics-schema.md`.

### Step 5 — Summary

Write `eval/results/<run_id>/summary.md`:

```markdown
# Dream eval <run_id>

**Gates:** secret-leak <pass|FAIL>

- Faithfulness: <faithfulness_score>
- Precision / Recall: <precision> / <recall>
- Recurrence calibration: <recurrence_calibration>
- Items proposed: <items_proposed> · token cost: <token_cost> · latency: <latency>

Top flags:
- <flags or "none">
```

Return summary to caller. Lead with hard failures if any gate failed.

## Guardrails

- Eval writes **only** `eval/results/<run_id>/`.
- `dream-judge` must **never** read `soul.md`.
- Use canonical metric names verbatim.

## Experiment contract

- **Hypothesis:** Weekly eval catches faithfulness drift before production runs.
- **Primary metric:** Days between regression introduction and detection.
- **Guardrail:** False-positive hard-stop rate < 20%.
- **Stop:** No regressions caught after 4 weekly runs → on-demand only.
- **Baseline:** faithfulness **0.75**.

## Further reading

- Handoff tables: `shared/chain-reference.md`
- Metrics keys: `shared/metrics-schema.md`
