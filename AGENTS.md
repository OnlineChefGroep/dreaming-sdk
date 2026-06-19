# Agent instructions for cursor-dreaming-sdk

You are working on the integration kit for the Cursor dreaming plugin. This repository manages orchestration patterns, multi-agent skills, and documentation.

## Core Architectural Boundaries

1.  **Plugin vs. SDK:** This repository is NOT a fork of the dreaming plugin. The plugin lives at `~/.cursor/plugins/local/dreaming/`. This repo holds integration artifacts.
2.  **Soul Isolation:** The `dream-judge` and `dream-curator` subagents must **NEVER** read `soul.md`. Only the `dream-evaluator` uses the soul to interpret signal.
3.  **Read-only vs. Write:**
    *   **Evaluator & Judge:** Read-only.
    *   **Curator:** Write-only (mutates `AGENTS.md` and memory).
4.  **Eval Isolation:** Golden evaluations must write exclusively to `eval/results/<run_id>/`. They must never mutate live memory or the index.

## Canonical Hashing

Always use the following rules for hashing transcripts and state:
1.  Strip UTF-8 BOM if present.
2.  Normalize CRLF → LF.
3.  SHA-256 → hex prefixed with `sha256:`.

## State & Safety

- **Never Commit:**
    - Live `~/.cursor/dreaming/dream-index.json`.
    - `dream-decisions.jsonl` containing live outcomes.
    - Session transcripts containing PII.
    - Secrets (API keys, DSNs).
- **Locations:**
    - Global state: `~/.cursor/dreaming/`.
    - Repo override: `<repo>/.cursor/dreaming/`.

## Python Memory Extension (`python/`)

- Backed by Postgres SSOT.
- Uses `uv` for dependency management.
- Always run `uv sync` before running tests or the CLI.
- All records must be JSON-serializable.

## Quality & Evaluation

- Faithfulness baseline is **0.63** (as of 2026-06-15).
- Deterministic gates (`secret_leak`, `hash_determinism`) are hard stops.
- When modifying evaluator prompts, you MUST run a golden eval pass to check for faithfulness drift.
