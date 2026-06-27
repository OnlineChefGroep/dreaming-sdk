# dream-eval

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
```

## Quick start

```python
from dream_eval import compute_faithfulness
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

## CLI

```bash
# Score evaluator report against labels
dream-eval score --report report.json --labels labels.json

# Run deterministic gates
dream-eval gate --labels labels.json --output evaluator_output.txt

# Export to metrics.json format
dream-eval export --input eval_result.json --output metrics.json
```

## Deterministic gates

These fail the eval regardless of LLM scores:

- **secret_leak** — checks for forbidden patterns (API keys, tokens, passwords)
- **hash_determinism** — verifies BOM/CRLF normalization produces stable hashes

## Memory backend adapter

dream-eval works with any memory backend via `BaseMemoryBackend`:

```python
from dream_eval.adapter import BaseMemoryBackend

class MyBackend(BaseMemoryBackend):
    def read_transcripts(self, corpus_path=None):
        # Read from your storage
        ...

    def read_labels(self, labels_path=None):
        # Read ground truth labels
        ...

    def write_eval_result(self, result):
        # Write evaluation results
        ...
```

Built-in `DictMemoryBackend` for testing.

## Architecture

```
dream-eval/
├── src/dream_eval/
│   ├── __init__.py      # Package exports
│   ├── types.py         # Pydantic models (EvalResult, FaithfulnessReport, etc.)
│   ├── scoring.py       # Faithfulness, precision, recall algorithms
│   ├── gates.py         # Deterministic gates (secret_leak, hash_determinism)
│   ├── adapter.py       # Abstract BaseMemoryBackend + DictMemoryBackend
│   └── cli.py           # CLI entry point
└── tests/               # Test suite
```

## License

MIT
