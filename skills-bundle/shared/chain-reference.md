# Dream Pipeline — Chain Reference (portable)

Trimmed from `~/.cursor/skills/dream-eval-loop/chain-reference.md` for multi-agent distribution.

---

## Eval loop (dream-eval-loop)

Unattended. Writes only `eval/results/<run_id>/`. Never mutates live state.

```text
dream-eval-loop (orchestrator)
  Step 0: run_id + soul_version + mkdir eval/results/<run_id>/
  Step 1: node cli/dream.mjs test --json → hard_fail → STOP
          dream-evaluator (readonly) → dream report
  Step 2: dream-judge (readonly, NO soul.md) → scoring JSON
  Step 3: node cli/dream.mjs decisions --json
  Step 4: write metrics.json
  Step 5: write summary.md → return to caller
```

### Handoffs (eval)

| From | To | Mechanism |
|------|----|-----------|
| Cron / chat / SDK | dream-eval-loop | prompt |
| dream-eval-loop | cli/dream.mjs test | shell |
| dream-eval-loop | dream-evaluator | subagent (readonly) |
| dream-eval-loop | dream-judge | subagent (readonly) |
| dream-eval-loop | cli/dream.mjs decisions | shell |
| dream-eval-loop | eval/results/ | file write |

### Entry points

| Surface | Driver |
|---------|--------|
| Cursor Automation | cron → dream-eval-loop |
| Chat | `/dream-eval` or skill trigger |
| Cursor SDK | `sdk/run-dream-cloud.ts` |
| Claude / Codex / OpenCode / Grok | skill trigger + shell CLI |
| CLI prep | `node cli/dream.mjs eval --dry-run` |

---

## Live dream loop (/dream)

Interactive. Writes `~/.cursor/dreaming/`, may update AGENTS.md. User must approve apply.

```text
dreaming (orchestrator)
  Step 0: resolve soul
  Step 1: dreaming-index-scope → pending list
  Step 2: dream-evaluator (readonly) → report
  Step 3: write report + present highlights
  ── dry-run STOPS HERE ──
  Step 4: user steering
  Step 5: dream-curator (write, NO soul.md)
  Step 6: update dream-index.json
```

---

## Subagent boundaries

| Subagent | Eval loop | Live dream | Readonly | Reads soul.md |
|----------|-----------|------------|----------|---------------|
| dream-evaluator | Yes | Yes | Yes | Yes (pinned snapshot) |
| dream-judge | Yes | No | Yes | **Never** |
| dream-curator | **No** | Yes | No (write) | **Never** |

---

## Nightly dry-run (optional automation)

```text
node cli/dream.mjs status --json → pending < 5 → skip
pending >= 5 → scope → evaluator → write report (no apply)
```

---

## Debugging

| Symptom | Check |
|---------|-------|
| secret_leak hard stop | `eval/golden-corpus/labels.json` forbidden strings |
| hash_determinism fail | `lib/canonical-hash.mjs` CRLF/BOM |
| judge reads soul.md | Boundary violation — fix subagent prompt |
| metrics shape mismatch | `shared/metrics-schema.md` |
