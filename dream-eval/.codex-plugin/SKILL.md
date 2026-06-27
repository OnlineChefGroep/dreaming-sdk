---
name: dream-eval
description: Agent-agnostic faithfulness evaluation for agent memory — scoring, deterministic gates, and metrics. Works with any memory backend.
---

# dream-eval (Codex)

Faithfulness evaluation framework for agent memory quality scoring.

## Trigger

```
Apply the dream-eval skill to score agent memory faithfulness.
```

## Usage

```bash
# Score an eval report
uvx dream-eval score --report eval/results/run-1/eval-report.json

# Check for secret leaks
uvx dream-eval gates --text "output to check"

# Check hash determinism
uvx dream-eval gates --file input.txt

# List recent runs
uvx dream-eval list --limit 10
```

## Python API

```python
from dream_eval.scoring import compute_faithfulness
from dream_eval.types import ProposedItem, LabeledItem

proposed = [ProposedItem(id="pref-1", category="pref", content={"key": "ci-merge-gate"})]
labels = [LabeledItem(id="pref-1", category="pref", content={"key": "ci-merge-gate"})]

report = compute_faithfulness(proposed, labels)
print(report.faithfulness_score)  # 1.0
```

## Deterministic Gates

| Gate | What it checks |
|------|----------------|
| `secret_leak` | Forbidden patterns (API keys, DSNs) in evaluator output |
| `hash_determinism` | BOM/CRLF normalization produces consistent SHA-256 hashes |
