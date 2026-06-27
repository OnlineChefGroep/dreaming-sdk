"""Last tests to push coverage to 95%."""

import json
import tempfile
from pathlib import Path
from unittest.mock import MagicMock, patch

from dream_eval.types import (
    EvalMode,
    EvalResult,
    FaithfulnessReport,
    GateResult,
    GateStatus,
    LabeledItem,
    ProposedItem,
)


# --- backends: save creates metrics.json with proper content ---


def test_save_metrics_json_content():
    with tempfile.TemporaryDirectory() as tmpdir:
        from dream_eval.backends import JsonFileBackend
        backend = JsonFileBackend(results_dir=tmpdir)
        result = EvalResult(
            run_id="test",
            date="2026-01-01",
            mode=EvalMode.GOLDEN,
            faithfulness=FaithfulnessReport(faithfulness_score=0.9),
        )
        backend.save_eval_result(result)

        metrics_path = Path(tmpdir) / "test" / "metrics.json"
        data = json.loads(metrics_path.read_text())
        assert data["faithfulness_score"] == 0.9
        assert data["run_id"] == "test"


# --- backends: save creates summary with gates table ---


def test_save_summary_content():
    with tempfile.TemporaryDirectory() as tmpdir:
        from dream_eval.backends import JsonFileBackend
        backend = JsonFileBackend(results_dir=tmpdir)
        result = EvalResult(
            run_id="test",
            date="2026-01-01",
            mode=EvalMode.GOLDEN,
            gates=[GateResult(name="secret_leak", status=GateStatus.PASS, message="ok")],
        )
        backend.save_eval_result(result)

        summary_path = Path(tmpdir) / "test" / "summary.md"
        content = summary_path.read_text()
        assert "test" in content
        assert "secret_leak" in content


# --- mcp/server: _make_handler returns callable ---


def test_make_handler():
    from dream_eval.mcp.server import _make_handler
    handler = _make_handler("dream_metrics_schema")
    result = handler()
    data = json.loads(result)
    assert "faithfulness_score" in data


# --- mli: verify_claim with empty strings ---


def test_nli_verify_claim_empty_strings():
    from dream_eval.nli import verify_content_nli
    item = ProposedItem(id="a", category="pref", content={"k": ""})
    label = LabeledItem(id="a", category="pref", content={"k": ""})
    supported, score = verify_content_nli(item, label)
    assert supported is False


# --- gates: check_hash_determinism consistency ---


def test_gates_hash_consistency():
    from dream_eval.gates import check_hash_determinism
    r1 = check_hash_determinism("hello world")
    r2 = check_hash_determinism("hello world")
    assert r1.details["hash"] == r2.details["hash"]


# --- scoring: fuzzy matching with case differences ---


def test_scoring_fuzzy_case_insensitive():
    from dream_eval.scoring import compute_faithfulness
    proposed = [ProposedItem(id="a", category="pref", content={"k": "Hello World"})]
    labels = [LabeledItem(id="a", category="pref", content={"k": "hello world"})]
    report = compute_faithfulness(proposed, labels, fuzzy=True, threshold=0.8)
    assert report.faithfulness_score == 1.0
