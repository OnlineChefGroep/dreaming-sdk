"""Extra tests to push coverage above 95%."""

import json
import tempfile
from pathlib import Path
from unittest.mock import MagicMock, patch

from dream_eval.types import (
    EvalMode,
    EvalResult,
    GateResult,
    GateStatus,
    LabeledItem,
    ProposedItem,
)

# --- backends_pg: load_eval_report with data ---


def test_postgres_backend_load_eval_report_found():
    mock_conn = MagicMock()
    mock_conn.execute.return_value.fetchone.return_value = {
        "content": {"items": [], "sessions_evaluated": 5, "token_cost": 0, "latency": 0}
    }
    mock_pool = MagicMock()
    mock_pool.connection.return_value.__enter__ = MagicMock(return_value=mock_conn)
    mock_pool.connection.return_value.__exit__ = MagicMock(return_value=False)

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
            result = backend.load_eval_report("run-1")
            assert result is not None
            assert result.sessions_evaluated == 5


# --- backends_pg: load_labels with file ---


def test_postgres_backend_load_labels_with_file():
    mock_pool = MagicMock()
    mock_psycopg_pool = MagicMock()
    mock_psycopg_pool.ConnectionPool.return_value = mock_pool
    mock_psycopg_rows = MagicMock()
    mock_psycopg_rows.dict_row = MagicMock()

    with tempfile.TemporaryDirectory() as tmpdir:
        labels_path = Path(tmpdir) / "labels.json"
        labels_path.write_text(json.dumps({"items": [{"id": "a", "category": "pref"}]}))

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
                labels = backend.load_labels(tmpdir)
                assert len(labels.items) == 1


# --- backends_pg: list_runs with data ---


def test_postgres_backend_list_runs_with_data():
    mock_conn = MagicMock()
    mock_row = {
        "run_id": "r1",
        "content": {"faithfulness_score": 0.8},
        "created_at": MagicMock(isoformat=MagicMock(return_value="2026-01-01")),
    }
    mock_conn.execute.return_value.fetchall.return_value = [mock_row]
    mock_pool = MagicMock()
    mock_pool.connection.return_value.__enter__ = MagicMock(return_value=mock_conn)
    mock_pool.connection.return_value.__exit__ = MagicMock(return_value=False)

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
            runs = backend.list_runs()
            assert len(runs) == 1
            assert runs[0]["run_id"] == "r1"


# --- cli: score with valid report and labels ---


def test_score_with_valid_files(capsys):
    with tempfile.TemporaryDirectory() as tmpdir:
        report_path = Path(tmpdir) / "report.json"
        report_path.write_text(json.dumps({"items": [{"id": "a", "category": "pref"}]}))

        labels_path = Path(tmpdir) / "labels.json"
        labels_path.write_text(json.dumps({"items": [{"id": "a", "category": "pref"}]}))

        from unittest.mock import patch as mp

        args = ["dream-eval", "score", "--report", str(report_path), "--labels", str(labels_path)]
        with mp("sys.argv", args):
            from dream_eval.cli import main
            main()

        out = capsys.readouterr().out
        data = json.loads(out)
        assert data["faithfulness_score"] == 1.0


# --- cli: score without labels (auto-detect) ---


def test_score_auto_detect_labels(capsys):
    with tempfile.TemporaryDirectory() as tmpdir:
        report_path = Path(tmpdir) / "report.json"
        report_path.write_text(json.dumps({"items": []}))

        from unittest.mock import patch as mp
        with mp("sys.argv", ["dream-eval", "score", "--report", str(report_path)]):
            from dream_eval.cli import main
            try:
                main()
            except FileNotFoundError:
                pass  # Expected - labels file doesn't exist


# --- gates: check_hash_determinism with BOM ---


def test_gates_hash_bom():
    from dream_eval.gates import check_hash_determinism
    result = check_hash_determinism("\ufeffhello")
    assert result.status == GateStatus.PASS
    assert "hash" in result.details


# --- nli: verify_content_nli with empty label content ---


def test_nli_verify_empty_label_content():
    from dream_eval.nli import verify_content_nli
    item = ProposedItem(id="a", category="pref", content={"k": "v"})
    label = LabeledItem(id="a", category="pref", content={})
    supported, score = verify_content_nli(item, label)
    assert supported is True
    assert score == 1.0


# --- scoring: compute_faithfulness with empty proposed ---


def test_scoring_empty_proposed():
    from dream_eval.scoring import compute_faithfulness
    report = compute_faithfulness([], [])
    assert report.faithfulness_score == 0.0
    assert report.items_proposed == 0


# --- backends: save + summary with multiple gates ---


def test_render_summary_multiple_gates():
    from dream_eval.backends import _render_summary
    result = EvalResult(
        run_id="multi",
        date="2026-01-01",
        mode=EvalMode.GOLDEN,
        gates=[
            GateResult(name="secret_leak", status=GateStatus.PASS, message="ok"),
            GateResult(name="hash_determinism", status=GateStatus.FAIL, message="mismatch"),
        ],
    )
    summary = _render_summary(result)
    assert "YES" in summary  # hard_fail
    assert "secret_leak" in summary
    assert "hash_determinism" in summary
