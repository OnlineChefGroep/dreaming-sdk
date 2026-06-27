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


# --- cli: fail-fast on missing explicit labels path ---


def test_load_labels_missing_explicit_path():

    from dream_eval.cli import _load_labels
    with patch("sys.argv", ["dream-eval"]):
        try:
            _load_labels(labels_path="/nonexistent/labels.json")
            raise AssertionError("Should have raised SystemExit")
        except SystemExit as e:
            assert e.code == 1


# --- cli: fail-fast on missing corpus-derived labels ---


def test_load_labels_missing_corpus_path():
    import tempfile

    from dream_eval.cli import _load_labels
    with tempfile.TemporaryDirectory() as tmpdir:
        try:
            _load_labels(corpus_path=tmpdir)
            raise AssertionError("Should have raised SystemExit")
        except SystemExit as e:
            assert e.code == 1


# --- cli: fail-fast on missing explicit report path ---


def test_load_eval_report_missing_explicit_path():
    from dream_eval.cli import _load_eval_report
    try:
        _load_eval_report(report_path="/nonexistent/report.json")
        raise AssertionError("Should have raised SystemExit")
    except SystemExit as e:
        assert e.code == 1


# --- nli: verify_claim with mocked model ---


def test_nli_verify_claim_with_mock_model():
    mock_model = MagicMock()
    mock_model.predict.return_value = 0.8

    with patch("dream_eval.nli._model", mock_model):
        from dream_eval.nli import verify_claim
        supported, score = verify_claim("claim text", "context text")
        assert supported is True
        assert score == 0.8


# --- nli: verify_claim below threshold ---


def test_nli_verify_claim_below_threshold():
    mock_model = MagicMock()
    mock_model.predict.return_value = 0.3

    with patch("dream_eval.nli._model", mock_model):
        from dream_eval.nli import verify_claim
        supported, score = verify_claim("claim", "context", threshold=0.5)
        assert supported is False
        assert score == 0.3


# --- nli: verify_content_nli with missing key ---


def test_nli_verify_content_nli_missing_key():
    mock_model = MagicMock()
    mock_model.predict.return_value = 0.9

    with patch("dream_eval.nli._model", mock_model):
        from dream_eval.nli import verify_content_nli
        item = ProposedItem(id="a", category="pref", content={"x": "v"})
        label = LabeledItem(id="a", category="pref", content={"missing": "v"})
        supported, score = verify_content_nli(item, label)
        assert supported is False
        assert score == 0.0


# --- nli: verify_content_nli with empty label text ---


def test_nli_verify_content_nli_empty_text():
    mock_model = MagicMock()
    mock_model.predict.return_value = 0.9

    with patch("dream_eval.nli._model", mock_model):
        from dream_eval.nli import verify_content_nli
        item = ProposedItem(id="a", category="pref", content={"k": "v"})
        label = LabeledItem(id="a", category="pref", content={"k": ""})
        supported, score = verify_content_nli(item, label)
        assert supported is False
        assert score == 0.0


# --- nli: verify_content_nli first unsupported stops ---


def test_nli_verify_content_nli_first_unsupported():
    mock_model = MagicMock()
    mock_model.predict.return_value = 0.2

    with patch("dream_eval.nli._model", mock_model):
        from dream_eval.nli import verify_content_nli
        item = ProposedItem(id="a", category="pref", content={"k1": "v1", "k2": "v2"})
        label = LabeledItem(id="a", category="pref", content={"k1": "v1", "k2": "v2"})
        supported, score = verify_content_nli(item, label, threshold=0.5)
        assert supported is False
        assert score == 0.2


# --- backends: PostgresBackend delegation ---


def test_postgres_backend_delegation():
    mock_impl = MagicMock()
    mock_impl.load_eval_report.return_value = EvalResult(
        run_id="test", date="2026-01-01", mode=EvalMode.GOLDEN
    )
    mock_impl.list_runs.return_value = [{"run_id": "r1"}]

    from dream_eval.backends import PostgresBackend
    backend = PostgresBackend.__new__(PostgresBackend)
    backend._impl = mock_impl

    report = backend.load_eval_report("test")
    assert report is not None
    assert report.run_id == "test"

    backend.load_labels("/tmp")
    mock_impl.load_labels.assert_called_once_with("/tmp")

    backend.save_eval_result(EvalResult(run_id="x", date="2026-01-01", mode=EvalMode.GOLDEN))
    mock_impl.save_eval_result.assert_called_once()

    runs = backend.list_runs(limit=5)
    assert len(runs) == 1
    mock_impl.list_runs.assert_called_once_with(5)


# --- gates: check_secret_leak with matching pattern ---


def test_gates_secret_leak_match():
    from dream_eval.gates import check_secret_leak
    result = check_secret_leak("my password is secret123", ["secret123"])
    assert result.status == GateStatus.FAIL
    assert "matched_patterns" in result.details


# --- gates: check_secret_leak with invalid regex ---


def test_gates_secret_leak_invalid_regex():
    from dream_eval.gates import check_secret_leak
    result = check_secret_leak("hello world", ["[invalid"])
    assert result.status == GateStatus.PASS


# --- gates: check_hash_determinism mismatch ---


def test_gates_hash_mismatch():
    from dream_eval.gates import check_hash_determinism
    result = check_hash_determinism("hello", "sha256:wrong")
    assert result.status == GateStatus.FAIL
    assert "expected" in result.details


# --- scoring: compute_faithfulness with items ---


def test_scoring_with_items():
    from dream_eval.scoring import compute_faithfulness
    proposed = [ProposedItem(id="a", category="pref", content={"key": "value"})]
    labels = [LabeledItem(id="a", category="pref", content={"key": "value"})]
    report = compute_faithfulness(proposed, labels)
    assert report.faithfulness_score == 1.0
    assert report.items_proposed == 1
