# Eval quality — golden corpus, metrics, and judge faithfulness

How dream-eval measures quality, what the baseline numbers mean, and known evaluator/judge weaknesses to track during weekly gates.

---

## Golden corpus

**Location:** `~/.cursor/plugins/local/dreaming/eval/golden-corpus/`

| Artifact | Path | Purpose |
|----------|------|---------|
| Transcripts | `transcripts/*.jsonl` | Labeled session excerpts for eval |
| Labels | `labels.json` | Expected items, recurrence counts, forbidden secrets |
| Pinned soul | `eval/soul-snapshot.md` | Reproducible eval lens (SHA-256 recorded as `soul_version`) |

The evaluator runs in an **isolated workspace** — temp copy of corpus + throwaway index. Live `~/.cursor/dreaming/` is never read for writes during golden eval.

**Secret-leak gate:** `labels.json` includes `.secret_leak.forbidden` patterns. Any match in evaluator output triggers `hard_fail` in `dream test`.

---

## Eval loop outputs

Each run writes to `eval/results/<run_id>/`:

| File | Contents |
|------|----------|
| `metrics.json` | 25-key canonical metrics (see below) |
| `summary.md` | Gates, headline scores, top flags — Slack/Notion-ready |

Full schema: [skills-bundle/shared/metrics-schema.md](../skills-bundle/shared/metrics-schema.md).

---

## Key metrics

| Metric | Source | Range | Golden-only note |
|--------|--------|-------|------------------|
| `faithfulness_score` | dream-judge | [0, 1] | Primary quality signal |
| `precision` | dream-judge | [0, 1] | Proposed vs labeled items |
| `recall` | dream-judge | [0, 1] | Labeled items found |
| `recurrence_calibration` | dream-judge | [0, 1] | Claimed vs true recurrence counts |
| `acceptance_rate.*` | `dream decisions --json` | float or null | null when no live outcomes |
| `regret_rate` | `dream decisions --json` | float or null | null in golden-only |
| `secret_leak_test` | `dream test` | pass/fail | Hard stop on fail |

---

## Baseline (SSOT)

| Run ID | Date | Faithfulness | Notes |
|--------|------|--------------|-------|
| `2026-06-15T07-17-00Z` | 2026-06-15 | **0.63** | First full golden pass after v3 refactor |

**Alert threshold:** week-over-week faithfulness drop > **0.10**.

**Experiment contract:** If no regressions are caught after 4 weekly runs, or false-positive hard-stop rate exceeds 20%, simplify to on-demand eval only. See [sdk-integration.md](./sdk-integration.md).

---

## Judge faithfulness methodology

`dream-judge` is readonly and **never reads `soul.md`**. It receives:

- Evaluator dream report
- Cited transcripts from `eval/golden-corpus/transcripts/`
- Current `~/.cursor/AGENTS.md` (redundancy checks)
- `eval/golden-corpus/labels.json`

**Faithfulness** = items with fully supported claims / total proposed items.

The judge also emits recurrence violations, specificity flags, and redundancy flags surfaced in `summary.md` under "Top flags".

---

## Known weaknesses (2026-06-15 baseline)

Document these as **known limitations** — not regressions — until evaluator/judge prompts or label schema are updated.

### 1. Recurrence inflation (mirror double-count)

**Symptom:** Faithfulness **0.63** on run `2026-06-15T07-17-00Z` with recurrence violations on **3 items**.

**Cause:** When the same preference appears in multiple transcript mirrors (e.g. CI-merge-gate preference cited across 5 sessions), the evaluator may aggregate recurrence counts that the judge treats as inflated relative to per-label ground truth.

**Impact:** Lowers `faithfulness_score` and `recurrence_calibration` without indicating a secret-leak or hash failure.

**Mitigation (planned):**

- Tighten evaluator synthesis pass to dedupe cross-session mirrors before assigning `recurrence` in action blocks
- Extend `labels.json` with explicit `max_recurrence` per item id
- Judge: score recurrence against deduplicated source sets, not raw action-block integers

### 2. Golden-only null acceptance rates

Acceptance and regret rates are `null` in golden runs. Dashboards must not treat null as zero.

### 3. Cloud eval missing live decision log

Cloud SDK runs on a fresh clone without `~/.cursor/dreaming/dream-decisions.jsonl`. Step 3 (`dream decisions --json`) may return empty rates — expected for CI-only golden runs.

---

## Deterministic gates (hard stops)

These failures **stop the eval loop** regardless of LLM scores:

| Test | Meaning |
|------|---------|
| `hash_determinism` | BOM/CRLF normalization broken — check `lib/canonical-hash.mjs` |
| `secret_leak` | Forbidden pattern in evaluator output vs `labels.json` |

All other tests (`index_schema_conformance`, `decisions_schema_conformance`) warn but do not set `hard_fail`.

---

## Quality workflow

1. **Weekly:** Cursor Automation runs `dream-eval-loop` (Mon 09:00).
2. **Compare:** `faithfulness_score` vs baseline 0.63; alert on Δ > 0.10 down.
3. **Inspect flags:** Recurrence violations, specificity, redundancy in `summary.md`.
4. **If hard_fail:** Fix deterministic issue before tuning prompts.
5. **If faithfulness drift only:** Check known weaknesses above before changing soul or corpus.

---

## References

| Artifact | Path |
|----------|------|
| Live baseline report | `~/.cursor/dreaming/dreams/2026-06-15T07-17-00Z.md` |
| Evaluator output spec | `reference/dream-evaluator-output-spec.md` |
| Metrics schema | [skills-bundle/shared/metrics-schema.md](../skills-bundle/shared/metrics-schema.md) |
| CLI contract | [skills-bundle/shared/cli-contract.md](../skills-bundle/shared/cli-contract.md) |
