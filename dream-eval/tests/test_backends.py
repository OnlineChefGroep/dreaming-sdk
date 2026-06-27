"""Tests for dream-eval backends."""

import json
import tempfile
from pathlib import Path

from dream_eval.backends import JsonFileBackend, _render_summary
from dream_eval.types import (
    EvalMode,
    EvalResult,
    FaithfulnessReport,
    GateResult,
    GateStatus,
)


def _make_result(**overrides) -> EvalResult:
    defaults = dict(
        run_id="test-run",
        date="2026-06-27T00:00:00Z",
        mode=EvalMode.GOLDEN,
        gates=[GateResult(name="secret_leak", status=GateStatus.PASS, message="ok")],
        faithfulness=FaithfulnessReport(
            faithfulness_score=0.85,
            precision=0.9,
            recall=0.8,
            recurrence_calibration=1.0,
            items_proposed=10,
            items_fully_supported=8,
            items_partially_supported=1,
            items_unsupported=1,
        ),
    )
    defaults.update(overrides)
    return EvalResult(**defaults)


# --- JsonFileBackend ---


def test_json_backend_save_creates_files():
    with tempfile.TemporaryDirectory() as tmpdir:
        backend = JsonFileBackend(results_dir=tmpdir)
        result = _make_result()
        backend.save_eval_result(result)

        run_dir = Path(tmpdir) / "test-run"
        assert run_dir.exists()
        assert (run_dir / "metrics.json").exists()
        assert (run_dir / "summary.md").exists()


def test_json_backend_load_nonexistent():
    with tempfile.TemporaryDirectory() as tmpdir:
        backend = JsonFileBackend(results_dir=tmpdir)
        assert backend.load_eval_report("nope") is None


def test_json_backend_load_existing():
    with tempfile.TemporaryDirectory() as tmpdir:
        run_dir = Path(tmpdir) / "my-run"
        run_dir.mkdir()
        (run_dir / "eval-report.json").write_text(json.dumps({
            "items": [],
            "sessions_evaluated": 5,
        }), encoding="utf-8")

        backend = JsonFileBackend(results_dir=tmpdir)
        report = backend.load_eval_report("my-run")
        assert report is not None
        assert report.sessions_evaluated == 5


def test_json_backend_list_runs():
    with tempfile.TemporaryDirectory() as tmpdir:
        backend = JsonFileBackend(results_dir=tmpdir)
        backend.save_eval_result(_make_result(run_id="run-1"))
        backend.save_eval_result(_make_result(run_id="run-2"))

        runs = backend.list_runs(limit=10)
        assert len(runs) == 2
        ids = {r["run_id"] for r in runs}
        assert ids == {"run-1", "run-2"}


def test_json_backend_list_runs_empty():
    with tempfile.TemporaryDirectory() as tmpdir:
        backend = JsonFileBackend(results_dir=tmpdir)
        assert backend.list_runs() == []


def test_json_backend_list_runs_limit():
    with tempfile.TemporaryDirectory() as tmpdir:
        backend = JsonFileBackend(results_dir=tmpdir)
        for i in range(5):
            backend.save_eval_result(_make_result(run_id=f"run-{i}"))
        runs = backend.list_runs(limit=2)
        assert len(runs) == 2


def test_json_backend_list_runs_nonexistent_dir():
    backend = JsonFileBackend(results_dir="/nonexistent/path")
    assert backend.list_runs() == []


def test_json_backend_load_labels():
    with tempfile.TemporaryDirectory() as tmpdir:
        labels_path = Path(tmpdir) / "labels.json"
        labels_path.write_text(json.dumps({"items": []}), encoding="utf-8")

        backend = JsonFileBackend(results_dir=tmpdir)
        labels = backend.load_labels(tmpdir)
        assert labels.items == []


def test_json_backend_load_labels_missing():
    with tempfile.TemporaryDirectory() as tmpdir:
        backend = JsonFileBackend(results_dir=tmpdir)
        labels = backend.load_labels("/nonexistent")
        assert labels.items == []


def test_json_backend_load_labels_default():
    with tempfile.TemporaryDirectory() as tmpdir:
        backend = JsonFileBackend(results_dir=tmpdir)
        labels = backend.load_labels()
        assert labels.items == []


# --- _render_summary ---


def test_render_summary_basic():
    result = _make_result()
    summary = _render_summary(result)
    assert "test-run" in summary
    assert "golden" in summary
    assert "0.850" in summary


def test_render_summary_with_violations():
    result = _make_result(
        faithfulness=FaithfulnessReport(
            faithfulness_score=0.5,
            items_proposed=2,
            items_fully_supported=1,
            items_unsupported=1,
            recurrence_violations=["pref-1: claimed 5, max 3"],
        )
    )
    summary = _render_summary(result)
    assert "Recurrence Violations" in summary
    assert "pref-1" in summary


def test_render_summary_no_violations():
    result = _make_result()
    summary = _render_summary(result)
    assert "Recurrence Violations" not in summary


def test_render_summary_hard_fail():
    result = _make_result(
        gates=[GateResult(name="secret_leak", status=GateStatus.FAIL, message="leaked")]
    )
    summary = _render_summary(result)
    assert "YES" in summary


def test_render_summary_no_hard_fail():
    result = _make_result()
    summary = _render_summary(result)
    assert "no" in summary.lower()
