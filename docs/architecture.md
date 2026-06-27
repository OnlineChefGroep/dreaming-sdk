# Dreaming architecture — deep dive

This document describes the persistent state model, schemas, hashing rules, and subagent boundaries for the dreaming evaluation framework.

---

## Design principles

1. **Soul is the evaluation lens, not config.** `soul.md` shapes how the evaluator interprets recurrence and signal — it is never passed to the judge or curator.
2. **Readonly vs write is fixed.** Evaluator and judge are readonly. Curator is write-only and consumes approved action blocks.
3. **Eval is measurement-only.** Golden eval writes exclusively to `eval/results/<run_id>/`. No live state mutation.
4. **Deterministic work is code.** Hashing, schema validation, secret-leak gates, and decision aggregation run in the dream-eval CLI — not LLM subagents.
5. **Session identity is stable.** Canonical hashing (strip BOM, CRLF→LF, SHA-256) ensures the same transcript hashes identically on Windows and Unix.

---

## Soul

| Artifact | Path | Used by |
|----------|------|---------|
| Live soul | `assets/soul.md` (plugin) or repo-local `.cursor/dreaming/soul.md` | Live `/dream`, evaluator |
| Pinned snapshot | `eval/soul-snapshot.md` | Golden eval only |

Each run records `soul_version = sha256:<hex>` of the active soul. Eval runs pin `eval/soul-snapshot.md` so scores are comparable week-over-week.

**Hard rule:** `dream-judge` and `dream-curator` must **never** read `soul.md`. The judge scores faithfulness against transcripts and labels; the curator applies typed YAML action blocks from an approved report.

---

## Dream index

**Path:** `~/.cursor/dreaming/dream-index.json` (or `<repo>/.cursor/dreaming/dream-index.json` when repo-local wins).

**Schema:** `schema/dream-index.schema.json` (JSON Schema v1).

The index tracks:

- **Sessions** — transcript hashes, status (`pending`, `processed`, `skipped`, `archived`), tags, timestamps.
- **Runs** — `RunEntry` records with `soul_version`, items applied, and hash pairs for conflict detection.

CLI commands that **reconcile** the index (`status`, `scope`, `index`) mutate live state. They are used by the live dream loop and nightly dry-run — **not** by the golden eval loop, which uses an isolated temp index.

Resolution order for soul and index:

1. Repo-local `.cursor/dreaming/` (when present)
2. Global `~/.cursor/dreaming/`

Override via env: `DREAMING_DIR` (Phase 1 npm).

---

## Decisions log (W1)

**Path:** `~/.cursor/dreaming/dream-decisions.jsonl`  
**Schema:** `schema/dream-decisions.schema.json` (`DreamDecisionEntry` v1)

One JSON object per line. Required fields: `schema_version`, `run_id`, `item_id`, `category`, `outcome`, `logged_at`.

| Categories | `pref`, `workflow`, `skill`, `subagent`, `rule`, `stale` |
| Outcomes | `proposed`, `accepted`, `rejected`, `edited`, `deferred`, `rolled_back`, `reinforced` |

The curator appends decision rows in the same transaction as memory writes. During golden eval, rows may be appended as `proposed` for schema validation; acceptance/regret rates come from live outcomes via `dream decisions --json`.

---

## Subagents

| Subagent | Eval loop | Live `/dream` | Readonly | Reads soul.md |
|----------|-----------|---------------|----------|---------------|
| dream-evaluator | Step 1 | Step 2 | Yes | Yes |
| dream-judge | Step 2 | — | Yes | **Never** |
| dream-curator | — | Step 5 | No (write) | **Never** |

**Evaluator** produces the 9-section dream report per `reference/dream-evaluator-output-spec.md`, with typed YAML action blocks.

**Judge** returns `faithfulness_score`, `precision`, `recall`, `recurrence_calibration`, and flag lists. Compares report claims against `eval/golden-corpus/labels.json` and cited transcripts.

**Curator** merges approved items into scope-routed targets (`global` → `~/.cursor/AGENTS.md`, `repo` → `<repo>/.cursor/AGENTS.md`), creates skills/subagents/rules, and logs W1 decisions with hash-before/after conflict guards.

---

## Canonical hashing

Implementation: `lib/canonical-hash.mjs`

```
1. Strip UTF-8 BOM if present
2. Normalize CRLF → LF
3. SHA-256 → hex prefixed with "sha256:"
```

Used for: session transcript identity, soul versioning, `agents_md_hash_before` / `_after` conflict detection.

The `hash_determinism` test in `cli/dream.mjs test` is a **hard stop** — eval cannot proceed if hashing is non-deterministic.

---

## Schemas

| Schema | File | Validates |
|--------|------|-----------|
| Dream index | `schema/dream-index.schema.json` | `dream-index.json` |
| Decision entry | `schema/dream-decisions.schema.json` | Each line of `dream-decisions.jsonl` |
| Metrics (Phase 1) | Planned in npm package | `eval/results/<run_id>/metrics.json` |

Validators: `lib/validators.mjs` (dependency-free).

---

## Eval workspace isolation

Golden eval creates:

```
eval/results/<run_id>/
  metrics.json      ← 25-key canonical shape
  summary.md        ← Slack/Notion-ready template
```

The evaluator runs in a temp copy of the golden corpus with a throwaway index and pinned `eval/soul-snapshot.md`. Live `~/.cursor/dreaming/` is never touched.

---

## Hooks

| Hook | File | Event | Role |
|------|------|-------|------|
| dreaming-stop | `hooks/dreaming-stop.ts` | `stop` | Advisory nudge toward `/dream` when pending ≥ threshold |

The hook does not trigger eval or automations. Diagnostics: `dreaming-hook-health` skill.

---

## Path resolution summary

| Path | Scope | Override |
|------|-------|----------|
| `~/.cursor/dreaming/` | Org/user global | `DREAMING_DIR` |
| `~/.cursor/plugins/local/dreaming/` | Plugin install | `DREAM_PLUGIN_ROOT` |
| `<repo>/.cursor/dreaming/` | Repo-local (W2) | Preferred over global when present |
| `eval/results/<run_id>/` | Per-run artifacts | Repo-relative in cloud CI |

**Fleet note:** Dreaming state stays on developer machines (e.g. sofie). Do not sync live index or decision logs to shared data nodes.

---

## References

| Artifact | Path |
|----------|------|
| Plugin README | `~/.cursor/plugins/local/dreaming/README.md` |
| Evaluator output spec | `reference/dream-evaluator-output-spec.md` |
| Plugin plan (run flow) | `reference/dream-plugin-plan.md` |
| v3 refactor notes | `docs/REFACTOR-v3-plan.md` |
| Chain reference | [skills-bundle/shared/chain-reference.md](../skills-bundle/shared/chain-reference.md) |
