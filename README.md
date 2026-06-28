# dreaming-sdk

[![CI](https://github.com/OnlineChefGroep/dreaming-sdk/actions/workflows/ci.yml/badge.svg)](https://github.com/OnlineChefGroep/dreaming-sdk/actions/workflows/ci.yml)
[![CodeQL](https://github.com/OnlineChefGroep/dreaming-sdk/actions/workflows/codeql.yml/badge.svg)](https://github.com/OnlineChefGroep/dreaming-sdk/actions/workflows/codeql.yml)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](./LICENSE)
[![PyPI dream-eval](https://img.shields.io/pypi/v/dream-eval.svg)](https://pypi.org/project/dream-eval/)
[![PyPI dreaming-memory](https://img.shields.io/pypi/v/dreaming-memory.svg)](https://pypi.org/project/dreaming-memory/)

**Agent-agnostic faithfulness evaluation framework for agent memory quality scoring.**

Two Python packages for evaluating and storing agent memory:

- **`dream-eval`** — standalone faithfulness evaluation (scoring, gates, MCP server)
- **`dreaming-memory`** — Postgres-backed agent memory with integrations

---

## Quick start

### Install

```bash
# dream-eval (evaluation framework)
pip install dream-eval

# dreaming-memory (agent memory storage)
pip install dreaming-memory

# Or both
pip install dream-eval dreaming-memory
```

### Evaluate faithfulness

```python
from dream_eval.scoring import compute_faithfulness
from dream_eval.types import ProposedItem, LabeledItem

proposed = [
    ProposedItem(id="pref-1", category="pref", content={"key": "dark_mode"}),
    ProposedItem(id="rule-1", category="rule", content={"key": "no_secrets"}),
]
labels = [
    LabeledItem(id="pref-1", category="pref", content={"key": "dark_mode"}),
    LabeledItem(id="rule-1", category="rule", content={"key": "no_secrets"}),
]

report = compute_faithfulness(proposed, labels)
print(f"Faithfulness: {report.faithfulness_score}")
```

### CLI

```bash
# Run deterministic gates
dream-eval gates --text "output to check"

# Score an eval report
dream-eval score --report eval/results/run-1/eval-report.json

# List recent runs
dream-eval list --limit 10
```

---

## What's in this repo

| Package | Description | PyPI |
|---------|-------------|------|
| `dream-eval/` | Faithfulness scoring, deterministic gates, MCP server | [dream-eval](https://pypi.org/project/dream-eval/) |
| `python/` | Agent memory with Postgres, Linear, Notion integrations | [dreaming-memory](https://pypi.org/project/dreaming-memory/) |
| `eval/` | Golden corpus + soul snapshot for evaluation | — |
| `skills-bundle/` | Multi-agent skill definitions | — |
| `.github/` | CI/CD workflows | — |

---

## dream-eval

Standalone faithfulness evaluation framework. Works with any memory backend.

### Features

- **Scoring modes:** exact (fast), fuzzy (difflib), NLI (HHEM-2.1-Open)
- **Deterministic gates:** secret_leak, hash_determinism
- **Backends:** JsonFile, Postgres
- **MCP server:** Claude/Copilot/etc integration
- **Agent Skills:** `.claude-plugin`, `.codex-plugin`, `.cursor-plugin`

### Install extras

```bash
pip install dream-eval           # Core
pip install dream-eval[nli]      # + NLI verification
pip install dream-eval[postgres] # + Postgres backend
pip install dream-eval[mcp]      # + MCP server
```

---

## dreaming-memory

Agent memory extension with Postgres SSOT.

### Features

- **Postgres-backed storage** with connection pooling
- **Linear/Notion/Cloudflare integrations**
- **Dashboard** with metrics
- **CLI** for all operations

### Quick start

```python
from dreaming_memory import AgentMemory, SessionContext
from dreaming_memory.types import MemoryType, MemorySource

with AgentMemory() as memory:
    memory.ensure_schema()
    ctx = SessionContext.for_dream_eval("run-001")
    memory.remember(ctx, MemoryType.OBSERVATION, {"key": "value"})
```

---

## Golden corpus

The `eval/` directory contains resources for faithfulness evaluation:

- `eval/golden-corpus/` — labeled transcripts for scoring
- `eval/soul-snapshot.md` — pinned evaluation lens
- `eval/results/` — evaluation run outputs

### Run evaluation

```bash
cd dream-eval
uv run dream-eval gates --text "$(cat eval/golden-corpus/transcripts/*.jsonl)"
uv run dream-eval score --report report.json --labels eval/golden-corpus/labels.json
```

---

## Multi-agent install

Agent Skills for cross-agent adoption:

| Platform | Plugin |
|----------|--------|
| Claude | `.claude-plugin/` |
| Codex | `.codex-plugin/` |
| Cursor | `.cursor-plugin/` |

---

## Development

```bash
# Clone
git clone https://github.com/OnlineChefGroep/dreaming-sdk.git
cd dreaming-sdk

# Setup dream-eval
cd dream-eval && uv sync --extra dev

# Setup dreaming-memory
cd python && uv sync --extra dev

# Run tests
cd dream-eval && uv run pytest -q
cd python && uv run pytest -q
```

---

## Repo layout

```text
dreaming-sdk/
├── README.md
├── LICENSE (MIT)
├── CONTRIBUTING.md
├── SECURITY.md
├── eval/
│   ├── golden-corpus/    ← labeled transcripts
│   ├── soul-snapshot.md  ← evaluation lens
│   └── results/         ← eval outputs
├── dream-eval/           ← faithfulness evaluation
│   ├── src/dream_eval/
│   ├── tests/
│   └── .claude-plugin/
├── python/               ← agent memory
│   ├── src/dreaming_memory/
│   └── tests/
├── skills-bundle/        ← multi-agent skills
└── .github/workflows/    ← CI/CD
```

---

## License

MIT — see [LICENSE](./LICENSE).
