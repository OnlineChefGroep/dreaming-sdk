# Agent instructions for `cursor-dreaming-sdk`

You are working on the **integration kit** for the Cursor dreaming plugin. This
repository holds exportable orchestration patterns, automation templates,
multi-agent skill bundles, the Python agent-memory extension, and documentation
so that any agent host (Cursor IDE, `@cursor/sdk`, OpenCode/Codex, Claude,
Grok/Factory, CI/webhook consumers) can run the same dream-eval pipeline.

## Core architectural boundaries

1. **Integration kit, NOT a fork.** This repository is **not** a fork or copy of
   the dreaming plugin. The plugin is an external local install that lives at
   `~/.cursor/plugins/local/dreaming/`. This repo only documents and wires how to
   call it. Never vendor the plugin's source here.

2. **Soul isolation.** The `dream-judge` and `dream-curator` subagents must
   **NEVER** read `soul.md`. Only the `dream-evaluator` subagent is allowed to use
   the soul to interpret signal. `soul.md` resides inside the dreaming plugin
   install directory or the target repo's `.cursor/dreaming/` directory — never in
   this SDK repo.

3. **Read/write boundaries.**
   - **Evaluator:** read-only (reads the soul + corpus, emits judgments only).
   - **Judge:** read-only (scores against labels; must not read `soul.md`).
   - **Curator:** the only role that **writes** (mutates `AGENTS.md` / memory).

4. **Eval isolation.** Golden evaluations must write **exclusively** to
   `eval/results/<run_id>/`. They must **never** mutate the live
   `~/.cursor/dreaming/` memory or its index. Eval runs are pure, side-effect-free
   with respect to live state.

## Canonical hashing

Always use the following rules when hashing transcripts and state, so hashes are
reproducible across platforms:

1. Strip the UTF-8 BOM if present.
2. Normalize line endings: CRLF → LF.
3. Compute SHA-256 and emit the **hex** digest prefixed with `sha256:`
   (e.g. `sha256:9f86d0...`).

## State & safety

- **Never commit:**
  - The live `~/.cursor/dreaming/dream-index.json`.
  - `dream-decisions.jsonl` containing live outcomes.
  - Session transcripts containing PII.
  - Secrets (API keys, DSNs, webhook URLs).
- **Locations:**
  - Global live state: `~/.cursor/dreaming/` — index, decision log, dream reports.
  - Plugin: `~/.cursor/plugins/local/dreaming/` — CLI, eval corpus, schemas.
  - Repo override: `<repo>/.cursor/dreaming/`.
  - Eval output: `eval/results/<run_id>/` only — generated artifacts, not committed
    unless they are pinned canonical baselines.

## Python memory extension (`python/`)

- Backed by a **Postgres SSOT** (single source of truth).
- Uses **`uv`** for dependency management.
- Always run `uv sync --extra dev` before running tests, lint, or the CLI (the dev
  tooling — `pytest`, `ruff` — lives in the `dev` **extra**, not a `--dev` group).
- All memory records must be **JSON-serializable**.

## Quality & evaluation

- Faithfulness baseline is **0.63** (as of 2026-06-15). Treat regressions below
  this baseline as a quality alarm.
- Deterministic gates (`secret_leak`, `hash_determinism`) are **hard stops** — if
  either fails the eval must stop and report prominently; do not proceed.
- When modifying evaluator prompts, you **MUST** re-run a golden eval pass to check
  for faithfulness drift before merging.
