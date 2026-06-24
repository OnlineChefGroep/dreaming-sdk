# Quickstart for contributors

This guide gets a new contributor from a clean checkout to a verified local change.

## 1. Prerequisites

- Node.js 20 or newer
- Python 3.11 or newer
- `uv` for Python dependency management
- Git

Install `uv` if needed:

```bash
curl -LsSf https://astral.sh/uv/install.sh | sh
export PATH="$HOME/.local/bin:$PATH"
```

## 2. Clone and inspect

```bash
git clone https://github.com/OnlineChefGroep/cursor-dreaming-sdk.git
cd cursor-dreaming-sdk
```

Read these before making architectural changes:

- [../README.md](../README.md) - repository overview
- [../AGENTS.md](../AGENTS.md) - AI/contributor boundaries
- [architecture.md](./architecture.md) - dream loop architecture
- [agent-memory.md](./agent-memory.md) - Python memory extension

## 3. Set up local dependencies

```bash
make setup
```

Equivalent manual command:

```bash
cd python
uv sync --extra dev
```

## 4. Run the full local gate

```bash
make check
```

If you do not have `make`, run the individual commands:

```bash
node --check bin/dream.js
node --experimental-strip-types --check sdk/run-dream-cloud.ts
npm test
cd python
uv run ruff check .
uv run pytest -q
```

## 5. Work safely

- Do not vendor the local dreaming plugin into this repository.
- Do not commit live `~/.cursor/dreaming/` state, transcripts, PII, API keys, DSNs, or
  webhook URLs.
- Golden eval outputs belong under `eval/results/<run_id>/` and should only be
  committed when they are explicit canonical baselines.
- When changing evaluator prompts or scoring behavior, run a golden eval pass and
  compare faithfulness against the current baseline.

## 6. Open a pull request

1. Use a focused branch.
2. Follow Conventional Commits (`feat(scope):`, `fix(scope):`, `docs:`).
3. Fill the pull request template.
4. Confirm CI, CodeQL, dependency review, and automated reviewers are green.
