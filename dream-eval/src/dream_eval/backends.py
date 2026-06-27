"""Memory backend adapters — abstract interface for different storage systems."""

from __future__ import annotations

from abc import ABC, abstractmethod
from pathlib import Path
from typing import Any

from dream_eval.types import EvalReport, EvalResult, Labels


class MemoryBackend(ABC):
    """Abstract interface for memory backends.

    dream-eval is backend-agnostic: implement this interface to plug in
    Postgres, LanceDB, knowledge graphs, or any other storage system.
    """

    @abstractmethod
    def load_eval_report(self, run_id: str) -> EvalReport | None:
        """Load an evaluator report by run ID."""

    @abstractmethod
    def load_labels(self, corpus_path: str | None = None) -> Labels:
        """Load golden corpus labels."""

    @abstractmethod
    def save_eval_result(self, result: EvalResult) -> None:
        """Persist an eval result (gates + scoring)."""

    @abstractmethod
    def list_runs(self, limit: int = 50) -> list[dict[str, Any]]:
        """List recent eval runs with summary info."""


class JsonFileBackend(MemoryBackend):
    """Simple file-based backend for local eval runs.

    Reads/writes to eval/results/<run_id>/ directories.
    """

    def __init__(self, results_dir: str = "eval/results") -> None:
        self.results_dir = Path(results_dir)

    def load_eval_report(self, run_id: str) -> EvalReport | None:
        import json

        path = self.results_dir / run_id / "eval-report.json"
        if not path.exists():
            return None
        data = json.loads(path.read_text(encoding="utf-8"))
        return EvalReport.model_validate(data)

    def load_labels(self, corpus_path: str | None = None) -> Labels:
        import json

        base = Path(corpus_path) if corpus_path else self.results_dir.parent / "golden-corpus"
        labels_file = base / "labels.json"
        if not labels_file.exists():
            return Labels()
        data = json.loads(labels_file.read_text(encoding="utf-8"))
        return Labels.model_validate(data)

    def save_eval_result(self, result: EvalResult) -> None:
        import json

        out_dir = self.results_dir / result.run_id
        out_dir.mkdir(parents=True, exist_ok=True)

        metrics_path = out_dir / "metrics.json"
        metrics_path.write_text(
            json.dumps(result.to_metrics_dict(), indent=2, default=str),
            encoding="utf-8",
        )

        summary = _render_summary(result)
        summary_path = out_dir / "summary.md"
        summary_path.write_text(summary, encoding="utf-8")

    def list_runs(self, limit: int = 50) -> list[dict[str, Any]]:
        import json

        runs: list[dict[str, Any]] = []
        if not self.results_dir.exists():
            return runs

        for d in sorted(self.results_dir.iterdir(), reverse=True):
            if not d.is_dir():
                continue
            metrics_file = d / "metrics.json"
            if metrics_file.exists():
                data = json.loads(metrics_file.read_text(encoding="utf-8"))
                runs.append({
                    "run_id": d.name,
                    "faithfulness": data.get("faithfulness_score"),
                    "secret_leak": data.get("secret_leak_test"),
                })
            if len(runs) >= limit:
                break
        return runs


class PostgresBackend(MemoryBackend):
    """Postgres-backed eval results storage.

    Stores eval results in the agent_memory table alongside other memory records.
    Requires psycopg[binary] >= 3.2.
    """

    def __init__(self, dsn: str | None = None) -> None:
        from dream_eval.backends_pg import PostgresEvalBackend

        self._impl = PostgresEvalBackend(dsn)

    def load_eval_report(self, run_id: str) -> EvalReport | None:
        return self._impl.load_eval_report(run_id)

    def load_labels(self, corpus_path: str | None = None) -> Labels:
        return self._impl.load_labels(corpus_path)

    def save_eval_result(self, result: EvalResult) -> None:
        self._impl.save_eval_result(result)

    def list_runs(self, limit: int = 50) -> list[dict[str, Any]]:
        return self._impl.list_runs(limit)


def _render_summary(result: EvalResult) -> str:
    """Render eval result as markdown summary."""
    gate_lines = []
    for g in result.gates:
        icon = {"pass": "OK", "fail": "FAIL", "warn": "WARN", "skip": "SKIP"}.get(
            g.status.value, "?"
        )
        gate_lines.append(f"| {g.name} | {icon} | {g.message} |")

    f = result.faithfulness
    gates_table = "\n".join(gate_lines) if gate_lines else "| (none) | - | - |"

    violations = ""
    if f.recurrence_violations:
        violations = "## Recurrence Violations\n" + "".join(
            f"- {v}\n" for v in f.recurrence_violations
        )

    return f"""# Eval Summary — {result.run_id}

**Mode:** {result.mode.value}
**Date:** {result.date.isoformat()}
**Hard fail:** {"YES" if result.hard_fail else "no"}

## Deterministic Gates

| Gate | Status | Message |
|------|--------|---------|
{gates_table}

## Faithfulness

| Metric | Value |
|--------|-------|
| Faithfulness | {f.faithfulness_score:.3f} |
| Precision | {f.precision:.3f} |
| Recall | {f.recall:.3f} |
| Recurrence calibration | {f.recurrence_calibration:.3f} |
| Items proposed | {f.items_proposed} |
| Fully supported | {f.items_fully_supported} |
| Partially supported | {f.items_partially_supported} |
| Unsupported | {f.items_unsupported} |

{violations}
"""
