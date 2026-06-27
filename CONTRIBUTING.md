# Contributing to cursor-dreaming-sdk

Thanks for your interest in improving **cursor-dreaming-sdk** — the integration kit
for the Cursor dreaming plugin eval loop. This guide explains how to set up the
project, run the checks, and submit changes.

## Project overview

This repository is an integration kit with two Python packages:

- **`dream-eval/`** — standalone faithfulness evaluation framework (PyPI: `dream-eval`)
- **`python/`** — agent memory extension with Postgres SSOT (PyPI: `dreaming-memory`)

- Start with the [README](./README.md) for the high-level picture.
- Read the [`docs/`](./docs/) directory for architecture, SDK integration,
  multi-agent install paths, eval quality, and operations.
- Read [AGENTS.md](./AGENTS.md) for the architectural boundaries that **all**
  contributors — especially automated/AI contributors — must respect.

## Prerequisites

- **Python** 3.11+
- **[uv](https://docs.astral.sh/uv/)** for Python dependency management

## Setting up the Python packages

### dream-eval

```bash
cd dream-eval
uv sync --extra dev
```

### dreaming-memory

```bash
cd python
uv sync --extra dev
```

### Running tests

```bash
# dream-eval
cd dream-eval && uv run pytest -q

# dreaming-memory
cd python && uv run pytest -q

# Both packages
cd dream-eval && uv run pytest -q && cd ../python && uv run pytest -q
```

### Running lint

```bash
# dream-eval
cd dream-eval && uv run ruff check src/ tests/

# dreaming-memory
cd python && uv run ruff check src/ tests/
```

Both must pass before a change is ready for review. CI runs the same commands
(see [`.github/workflows/ci.yml`](./.github/workflows/ci.yml)).

For the full local quality gate (Python, Node, package checks, workflow YAML parse):

```bash
make check
```

## Branch naming

Use short, descriptive, kebab-case branch names prefixed by type, e.g.:

- `feat/agent-memory-batching`
- `fix/doctor-notion-attribute`
- `docs/sdk-integration-update`

## Commit message convention

We follow [Conventional Commits](https://www.conventionalcommits.org/). The repo
history uses prefixes such as:

- `feat(scope): ...` — a new feature
- `fix(scope): ...` — a bug fix
- `docs: ...` — documentation only
- `chore: ...`, `refactor: ...`, `test: ...`, `ci: ...` — as appropriate

The `(scope)` is optional but encouraged (e.g. `feat(memory):`, `fix(cli):`).

## Pull request process

1. Fork (or branch) and open your PR against **`main`**.
2. Make sure tests and lint pass locally (`uv run pytest -q`, `uv run ruff check .`).
3. Ensure CI is green.
4. Fill out the [pull request template](./.github/PULL_REQUEST_TEMPLATE.md)
   completely.
5. Keep PRs focused — one logical change per PR where possible.

Automated reviewers run on PRs (including **Sentry** and **kilo-code-bot**).
Please address their feedback alongside human review comments.

## Boundaries for automated / AI contributors

Automated and AI contributors must respect the boundaries documented in
[AGENTS.md](./AGENTS.md). In particular:

- **Soul isolation** — never read from or write to live `~/.cursor/dreaming/`
  soul state during eval work.
- **Eval isolation** — eval output belongs in `eval/results/<run_id>/` only and
  must never mutate live memory.
- **Never commit secrets or PII** — no DSNs, API keys, tokens, or PII
  transcripts in commits, history, or fixtures.

## Code of conduct

By participating, you agree to abide by our
[Code of Conduct](./CODE_OF_CONDUCT.md).
