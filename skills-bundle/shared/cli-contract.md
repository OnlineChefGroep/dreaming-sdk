# Dream CLI contract (`cli/dream.mjs`)

Platform-agnostic. Entry point for all agent surfaces.

**Plugin root:** `~/.cursor/plugins/local/dreaming/`  
**Invocation:** `node cli/dream.mjs <command> [options] [--json]`

---

## Global options

| Flag | Effect |
|------|--------|
| `--json` | Machine-readable stdout |
| `--dry-run` | Preview without side effects (`eval` only) |
| `--help`, `-h` | Command help |

**Exit codes:** `0` ok · `1` runtime error · `2` usage error · `test` inherits suite exit

---

## Subcommands

### `test`

Deterministic gates. **Eval loop Step 1.**

```shell
node cli/dream.mjs test --json
```

| Test | Hard stop? |
|------|------------|
| `hash_determinism` | Yes (`hard_fail`) |
| `secret_leak` | Yes (`hard_fail`) |
| `index_schema_conformance` | No |
| `decisions_schema_conformance` | No |

**Key JSON fields:**

```json
{
  "hard_fail": false,
  "tests": {
    "hash_determinism": { "pass": true },
    "secret_leak": { "pass": true }
  }
}
```

---

### `eval`

Validate corpus and prepare results directory. **Eval loop Step 0.**

```shell
node cli/dream.mjs eval --corpus eval/golden-corpus --run 2026-06-15T09-00-00Z --json
```

| Option | Default |
|--------|---------|
| `--corpus` | `eval/golden-corpus` |
| `--out` | `eval/results` |
| `--run` | generated ISO stem |
| `--dry-run` | plan only |

**Key JSON fields:**

```json
{
  "run_id": "2026-06-15T09-00-00Z",
  "corpus_path": ".../eval/golden-corpus",
  "corpus_present": true,
  "out_dir": ".../eval/results/2026-06-15T09-00-00Z",
  "prepared": true,
  "steps": ["..."]
}
```

Does **not** run LLM scoring — orchestrator skill handles evaluator + judge.

---

### `decisions`

Acceptance/regret from W1 decision log. **Eval loop Step 3.** Read-only.

```shell
node cli/dream.mjs decisions --json
node cli/dream.mjs decisions --category pref --json
```

**Key JSON fields:**

```json
{
  "decisions_present": true,
  "rows": 42,
  "rates": {
    "pref": { "acceptance_rate": 0.85, "regret_rate": 0.1 }
  },
  "acceptance_rate_overall": 0.82,
  "regret_rate_overall": 0.08
}
```

---

### `status`

Reconciles live index, then reports pending counts. **Nightly dry-run only — not golden eval.**

```shell
node cli/dream.mjs status --json
```

**Key JSON fields:** `pending`, `last_dream`, `pending_by_tag`, `index_updated`

---

### `scope`

Reconciles index, lists pending sessions. **Nightly dry-run only.**

```shell
node cli/dream.mjs scope --focus utrecht --json
```

**Key JSON fields:** `in_scope[]`, `total_pending`, `focus`

---

### `index`

Index summary after reconcile. **Diagnostics only — not golden eval.**

```shell
node cli/dream.mjs index --json
```

**Key JSON fields:** `status_counts`, `runs`, `last_dream`

---

## Environment overrides (Phase 1 npm)

| Variable | Default |
|----------|---------|
| `DREAM_PLUGIN_ROOT` | `~/.cursor/plugins/local/dreaming` |
| `DREAMING_DIR` | `~/.cursor/dreaming` |

---

## Eval vs live CLI usage

| Command | Golden eval loop | Live `/dream` | Nightly dry-run |
|---------|------------------|---------------|-----------------|
| `test` | Yes | Optional | No |
| `eval` | Yes | No | No |
| `decisions` | Yes | After apply | No |
| `status` | **No** | Yes | Yes (gate) |
| `scope` | **No** | Yes | Yes |
| `index` | **No** | Diagnostics | No |
