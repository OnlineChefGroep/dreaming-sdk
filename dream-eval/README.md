# dream-eval

[![PyPI version](https://img.shields.io/pypi/v/dream-eval.svg)](https://pypi.org/project/dream-eval/)
[![Python](https://img.shields.io/pypi/pyversions/dream-eval.svg)](https://pypi.org/project/dream-eval/)
[![License](https://img.shields.io/pypi/l/dream-eval.svg)](https://github.com/OnlineChefGroep/dreaming-sdk/blob/main/dream-eval/LICENSE)
[![Tests](https://img.shields.io/badge/tests-132%20passing-brightgreen)](https://github.com/OnlineChefGroep/dreaming-sdk/actions)
[![Coverage](https://img.shields.io/badge/coverage-94%25-brightgreen)](https://github.com/OnlineChefGroep/dreaming-sdk)

Agent-agnostic faithfulness evaluation framework for agent memory quality scoring.

## What it does

dream-eval implements the **evaluator → judge → curator** pipeline pattern:

- **Evaluator** reads transcripts + soul (interpretive lens), proposes items
- **Judge** scores against labels WITHOUT reading soul (enforcing objectivity)
- **Curator** writes results (enforcing separation of concerns)

This pattern is unique in the agent memory space — no competitor (mem0, Cognee, LangMem) offers automated faithfulness evaluation.

## Install

```bash
pip install dream-eval

# With NLI claim verification (HHEM-2.1-Open)
pip install dream-eval[nli]

# With Postgres backend
pip install dream-eval[postgres]

# With MCP server
pip install dream-eval[mcp]
```

## Quick start

```python
from dream_eval.scoring import compute_faithfulness
from dream_eval.types import ProposedItem, LabeledItem

proposed = [
    ProposedItem(id="pref-1", category="pref", content={"key": "dark_mode"}),
    ProposedItem(id="workflow-1", category="workflow", content={"key": "ci_merge"}),
]
labels = [
    LabeledItem(id="pref-1", category="pref"),
    LabeledItem(id="workflow-1", category="workflow"),
]

report = compute_faithfulness(proposed, labels)
print(f"Faithfulness: {report.faithfulness_score}")
```

### Fuzzy matching

```python
# Handles inflection, case differences, minor rewording
report = compute_faithfulness(proposed, labels, fuzzy=True, threshold=0.85)
```

### NLI verification

```python
# Uses HHEM-2.1-Open for semantic similarity (requires dream-eval[nli])
report = compute_faithfulness(proposed, labels, nli=True)
```

## CLI

```bash
# Run deterministic gates
dream-eval gates --text "output to check" --file input.txt

# Score an eval report
dream-eval score --report eval/results/run-1/eval-report.json

# List recent runs
dream-eval list --limit 10
```

## Deterministic gates

These fail the eval regardless of LLM scores:

- **secret_leak** — checks for forbidden patterns (API keys, tokens, passwords)
- **hash_determinism** — verifies BOM/CRLF normalization produces stable hashes

## MCP server

```bash
# Run as MCP server
dream-eval-mcp
```

Exposes tools: `dream_score`, `dream_check_secrets`, `dream_check_hash`, `dream_metrics_schema`.

## Memory backend adapter

dream-eval works with any memory backend via `MemoryBackend`:

```python
from dream_eval.backends import MemoryBackend

class MyBackend(MemoryBackend):
    def load_eval_report(self, run_id):
        ...

    def load_labels(self, corpus_path=None):
        ...

    def save_eval_result(self, result):
        ...

    def list_runs(self, limit=50):
        ...
```

Built-in backends:
- `JsonFileBackend` — reads/writes to `eval/results/<run_id>/`
- `PostgresBackend` — stores in `agent_memory` table alongside other memory records

## Architecture

```
dream-eval/
├── src/dream_eval/
│   ├── __init__.py      # Package exports
│   ├── types.py         # Pydantic models (EvalResult, FaithfulnessReport, etc.)
│   ├── scoring.py       # Faithfulness, precision, recall algorithms
│   ├── gates.py         # Deterministic gates (secret_leak, hash_determinism)
│   ├── backends.py      # MemoryBackend ABC + JsonFileBackend
│   ├── backends_pg.py   # PostgresBackend
│   ├── nli.py           # NLI claim verification (HHEM-2.1-Open)
│   ├── mcp/server.py    # MCP server for Claude/Copilot/etc
│   └── cli.py           # CLI entry point
└── tests/               # 132 tests, 94% coverage
```

## License

MIT
