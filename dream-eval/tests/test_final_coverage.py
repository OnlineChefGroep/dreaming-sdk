"""Final tests to push coverage above 95%."""

import json
import tempfile
from pathlib import Path
from unittest.mock import MagicMock, patch

from dream_eval.scoring import compute_faithfulness
from dream_eval.types import (
    EvalMode,
    EvalResult,
    GateStatus,
    LabeledItem,
    ProposedItem,
)

# --- backends: save + list_runs with non-directory entries ---


def test_list_runs_skips_files():
    with tempfile.TemporaryDirectory() as tmpdir:
        # Create a file (not directory) in results dir
        results_dir = Path(tmpdir) / "eval"
        results_dir.mkdir()
        (results_dir / "not-a-dir.txt").write_text("hello")

        from dream_eval.backends import JsonFileBackend
        backend = JsonFileBackend(results_dir=str(results_dir))
        runs = backend.list_runs()
        assert runs == []


# --- backends: render_summary with empty gates ---


def test_render_summary_empty_gates():
    from dream_eval.backends import _render_summary
    result = EvalResult(
        run_id="empty",
        date="2026-01-01",
        mode=EvalMode.GOLDEN,
        gates=[],
    )
    summary = _render_summary(result)
    assert "(none)" in summary


# --- cli: run with corpus arg ---


def test_run_with_corpus(capsys):
    with tempfile.TemporaryDirectory() as tmpdir:
        labels_path = Path(tmpdir) / "labels.json"
        labels_path.write_text(json.dumps({"items": []}))
        with patch("sys.argv", [
            "dream-eval", "run", "--corpus", tmpdir,
            "--output-dir", tmpdir, "--threshold", "0",
        ]):
            from dream_eval.cli import main
            main()
        out = capsys.readouterr().out
        data = json.loads(out)
        assert "run_id" in data


# --- mcp/server: handle_tool with empty proposed ---


def test_handle_tool_dream_score_empty():
    from dream_eval.mcp.server import handle_tool
    result = json.loads(handle_tool("dream_score", {"proposed": [], "labels": []}))
    assert result["faithfulness_score"] == 0.0


# --- mcp/server: handle_tool dream_check_hash with content only ---


def test_handle_tool_hash_no_expected():
    from dream_eval.mcp.server import handle_tool
    result = json.loads(handle_tool("dream_check_hash", {"content": "test"}))
    assert result["status"] == "pass"
    assert "hash" in result["details"]


# --- nli: verify_claim with threshold boundary ---


def test_nli_verify_claim_threshold_boundary():
    with patch("dream_eval.nli._get_model") as mock_get:
        mock_model = MagicMock()
        mock_model.predict.return_value = 0.5  # exactly at threshold
        mock_get.return_value = mock_model

        from dream_eval.nli import verify_claim
        supported, score = verify_claim("claim", "context", threshold=0.5)
        assert supported is True
        assert score == 0.5


# --- scoring: compute_faithfulness with recurrence violations ---


def test_scoring_recurrence_violations():
    proposed = [ProposedItem(id="a", category="pref", recurrence=10)]
    labels = [LabeledItem(id="a", category="pref", max_recurrence=3)]
    report = compute_faithfulness(proposed, labels)
    assert len(report.recurrence_violations) == 1
    assert report.items_partially_supported == 1


# --- gates: check_hash_determinism with mismatch ---


def test_gates_hash_mismatch():
    from dream_eval.gates import check_hash_determinism
    result = check_hash_determinism("hello", expected_hash="sha256:wrong")
    assert result.status == GateStatus.FAIL


# --- backends_pg: load_labels with nonexistent file ---


def test_postgres_load_labels_nonexistent_file():
    mock_pool = MagicMock()
    mock_psycopg_pool = MagicMock()
    mock_psycopg_pool.ConnectionPool.return_value = mock_pool
    mock_psycopg_rows = MagicMock()
    mock_psycopg_rows.dict_row = MagicMock()

    with patch.dict("sys.modules", {
        "psycopg_pool": mock_psycopg_pool,
        "psycopg.rows": mock_psycopg_rows,
    }):
        import sys
        if "dream_eval.backends_pg" in sys.modules:
            del sys.modules["dream_eval.backends_pg"]

        with patch.dict("os.environ", {"DATABASE_URL": "postgresql://test"}):
            from dream_eval.backends_pg import PostgresEvalBackend
            backend = PostgresEvalBackend()
            labels = backend.load_labels("/nonexistent/path")
            assert labels.items == []
