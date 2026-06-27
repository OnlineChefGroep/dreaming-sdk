---
name: dream-eval
description: Agent-agnostic faithfulness evaluation for agent memory — scoring, deterministic gates, and metrics. Works with any memory backend (Postgres, LanceDB, knowledge graphs).
---

# dream-eval

Faithfulness evaluation framework for agent memory quality scoring.

## Usage

### Python API

```python
from dream_eval.scoring import compute_faithfulness
from dream_eval.types import ProposedItem, LabeledItem

proposed = [ProposedItem(id="pref-1", category="pref", content={"key": "ci-merge-gate"})]
labels = [LabeledItem(id="pref-1", category="pref", content={"key": "ci-merge-gate"})]

report = compute_faithfulness(proposed, labels)
print(report.faithfulness_score)  # 1.0
```

### CLI

```bash
# Score an eval report
dream-eval score --report eval/results/run-1/eval-report.json

# Check for secret leaks
dream-eval gates --text "output to check"

# Check hash determinism
dream-eval gates --file input.txt

# List recent runs
dream-eval list --limit 10
```

### Deterministic Gates

These are **hard stops** — if either fails, the eval must stop:

| Gate | What it checks |
|------|----------------|
| `secret_leak` | Forbidden patterns (API keys, DSNs) in evaluator output |
| `hash_determinism` | BOM/CRLF normalization produces consistent SHA-256 hashes |

## Installation

```bash
pip install dream-eval

# With Postgres backend
pip install dream-eval[postgres]

# With MCP server
pip install dream-eval[mcp]
```

## Architecture

dream-eval is **backend-agnostic**. The `MemoryBackend` abstract class defines the interface:

```python
class MemoryBackend(ABC):
    def load_eval_report(self, run_id: str) -> EvalReport | None: ...
    def load_labels(self, corpus_path: str | None = None) -> Labels: ...
    def save_eval_result(self, result: EvalResult) -> None: ...
    def list_runs(self, limit: int = 50) -> list[dict[str, Any]]: ...
```

Built-in backends:
- `JsonFileBackend` — reads/writes to `eval/results/<run_id>/`
- `PostgresBackend` — stores in `agent_memory` table alongside other memory records

## MCP Server

```bash
# Run as MCP server
dream-eval-mcp

# Or via uvx
uvx dream-eval[mcp]
```

Exposes tools: `dream_score`, `dream_check_secrets`, `dream_check_hash`, `dream_metrics_schema`.
