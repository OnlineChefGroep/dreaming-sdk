# `metrics.json` schema

Written to `eval/results/<run_id>/metrics.json` at eval loop Step 4.  
**25 top-level keys** — names are canonical; dashboards parse verbatim.

---

## Full shape

```json
{
  "run_id": "2026-06-14T00-00-00Z",
  "date": "2026-06-14T00:00:00Z",
  "mode": "golden",
  "sessions_evaluated": 0,
  "items_proposed": 0,
  "accepted": 0,
  "rejected": 0,
  "edited": 0,
  "deferred": 0,
  "rolled_back": {
    "pref": 0,
    "workflow": 0,
    "skill": 0,
    "subagent": 0,
    "rule": 0
  },
  "acceptance_rate": {
    "overall": null,
    "pref": null,
    "workflow": null,
    "skill": null,
    "subagent": null,
    "rule": null
  },
  "precision": 0.0,
  "recall": 0.0,
  "recurrence_calibration": 0.0,
  "faithfulness_score": 0.0,
  "secret_leak_test": "pass",
  "regret_rate": null,
  "token_cost": 0,
  "latency": 0,
  "soul_version": "sha256:…",
  "agents_md_hash_before": null,
  "agents_md_hash_after": null
}
```

---

## Field reference

| Field | Type | Source |
|-------|------|--------|
| `run_id` | string | Step 0 ISO stem |
| `date` | ISO8601 | Run timestamp |
| `mode` | `"golden"` \| `"live"` | Eval mode |
| `sessions_evaluated` | int | Corpus session count |
| `items_proposed` | int | Evaluator report |
| `accepted` / `rejected` / `edited` / `deferred` | int | Live outcomes; 0 in golden |
| `rolled_back` | per-category int | Decision log |
| `acceptance_rate` | float \| null per category | `dream decisions --json` |
| `precision` / `recall` | float [0,1] | dream-judge |
| `recurrence_calibration` | float | dream-judge |
| `faithfulness_score` | float [0,1] | dream-judge |
| `secret_leak_test` | `"pass"` \| `"fail"` | `dream test` |
| `regret_rate` | float \| null | `dream decisions --json` |
| `token_cost` / `latency` | number | Evaluator run |
| `soul_version` | `sha256:<hex>` | Pinned soul snapshot |
| `agents_md_hash_before` / `_after` | string \| null | null in golden-only |

---

## Golden-only conventions

- `acceptance_rate.*` and `regret_rate` → `null` when no human outcomes
- `agents_md_hash_before` / `_after` → `null`
- `mode` → `"golden"`

---

## Baseline (SSOT)

| Run | Faithfulness |
|-----|--------------|
| `2026-06-15T07-17-00Z` | **0.63** |

**Target:** **0.75** — alert if week-over-week faithfulness drops by > 0.10.

---

## Decision log (`dream-decisions.jsonl`)

One JSON object per line. Schema: `schema/dream-decisions.schema.json`.

**Required:** `schema_version`, `run_id`, `item_id`, `category`, `outcome`, `logged_at`

**Categories:** `pref`, `workflow`, `skill`, `subagent`, `rule`, `stale`  
**Outcomes:** `proposed`, `accepted`, `rejected`, `edited`, `deferred`, `rolled_back`, `reinforced`
