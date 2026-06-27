"""Tests for dream-eval Postgres backend (mocked)."""

import sys
from unittest.mock import MagicMock, patch

from dream_eval.types import EvalMode, EvalResult


def _make_result() -> EvalResult:
    return EvalResult(run_id="pg-test", date="2026-01-01", mode=EvalMode.GOLDEN)


def test_postgres_backend_no_dsn():
    with patch.dict("os.environ", {}, clear=True):
        from dream_eval.backends_pg import PostgresEvalBackend
        try:
            PostgresEvalBackend()
            assert False, "Should have raised ValueError"
        except ValueError as e:
            assert "No database DSN" in str(e)


def test_postgres_backend_init():
    mock_conn = MagicMock()
    mock_pool = MagicMock()
    mock_pool.connection.return_value.__enter__ = MagicMock(return_value=mock_conn)
    mock_pool.connection.return_value.__exit__ = MagicMock(return_value=False)

    mock_psycopg_pool = MagicMock()
    mock_psycopg_pool.ConnectionPool.return_value = mock_pool

    mock_psycopg_rows = MagicMock()
    mock_psycopg_rows.dict_row = MagicMock()

    with patch.dict(sys.modules, {
        "psycopg_pool": mock_psycopg_pool,
        "psycopg.rows": mock_psycopg_rows,
    }):
        # Need to reimport to pick up the mock
        if "dream_eval.backends_pg" in sys.modules:
            del sys.modules["dream_eval.backends_pg"]

        with patch.dict("os.environ", {"DATABASE_URL": "postgresql://test"}):
            from dream_eval.backends_pg import PostgresEvalBackend
            backend = PostgresEvalBackend()
            assert backend._pool is mock_pool


def test_postgres_backend_context_manager():
    mock_pool = MagicMock()
    mock_psycopg_pool = MagicMock()
    mock_psycopg_pool.ConnectionPool.return_value = mock_pool

    mock_psycopg_rows = MagicMock()
    mock_psycopg_rows.dict_row = MagicMock()

    with patch.dict(sys.modules, {
        "psycopg_pool": mock_psycopg_pool,
        "psycopg.rows": mock_psycopg_rows,
    }):
        if "dream_eval.backends_pg" in sys.modules:
            del sys.modules["dream_eval.backends_pg"]

        with patch.dict("os.environ", {"DATABASE_URL": "postgresql://test"}):
            from dream_eval.backends_pg import PostgresEvalBackend
            with PostgresEvalBackend() as backend:
                pass
            backend._pool.close.assert_called_once()


def test_postgres_backend_save():
    mock_conn = MagicMock()
    mock_pool = MagicMock()
    mock_pool.connection.return_value.__enter__ = MagicMock(return_value=mock_conn)
    mock_pool.connection.return_value.__exit__ = MagicMock(return_value=False)

    mock_psycopg_pool = MagicMock()
    mock_psycopg_pool.ConnectionPool.return_value = mock_pool

    mock_psycopg_rows = MagicMock()
    mock_psycopg_rows.dict_row = MagicMock()

    with patch.dict(sys.modules, {
        "psycopg_pool": mock_psycopg_pool,
        "psycopg.rows": mock_psycopg_rows,
    }):
        if "dream_eval.backends_pg" in sys.modules:
            del sys.modules["dream_eval.backends_pg"]

        with patch.dict("os.environ", {"DATABASE_URL": "postgresql://test"}):
            from dream_eval.backends_pg import PostgresEvalBackend
            backend = PostgresEvalBackend()
            backend.save_eval_result(_make_result())
            mock_conn.execute.assert_called()


def test_postgres_backend_load_eval_report_not_found():
    mock_conn = MagicMock()
    mock_conn.execute.return_value.fetchone.return_value = None
    mock_pool = MagicMock()
    mock_pool.connection.return_value.__enter__ = MagicMock(return_value=mock_conn)
    mock_pool.connection.return_value.__exit__ = MagicMock(return_value=False)

    mock_psycopg_pool = MagicMock()
    mock_psycopg_pool.ConnectionPool.return_value = mock_pool

    mock_psycopg_rows = MagicMock()
    mock_psycopg_rows.dict_row = MagicMock()

    with patch.dict(sys.modules, {
        "psycopg_pool": mock_psycopg_pool,
        "psycopg.rows": mock_psycopg_rows,
    }):
        if "dream_eval.backends_pg" in sys.modules:
            del sys.modules["dream_eval.backends_pg"]

        with patch.dict("os.environ", {"DATABASE_URL": "postgresql://test"}):
            from dream_eval.backends_pg import PostgresEvalBackend
            backend = PostgresEvalBackend()
            result = backend.load_eval_report("nonexistent")
            assert result is None


def test_postgres_backend_load_labels_no_path():
    mock_pool = MagicMock()
    mock_psycopg_pool = MagicMock()
    mock_psycopg_pool.ConnectionPool.return_value = mock_pool

    mock_psycopg_rows = MagicMock()
    mock_psycopg_rows.dict_row = MagicMock()

    with patch.dict(sys.modules, {
        "psycopg_pool": mock_psycopg_pool,
        "psycopg.rows": mock_psycopg_rows,
    }):
        if "dream_eval.backends_pg" in sys.modules:
            del sys.modules["dream_eval.backends_pg"]

        with patch.dict("os.environ", {"DATABASE_URL": "postgresql://test"}):
            from dream_eval.backends_pg import PostgresEvalBackend
            backend = PostgresEvalBackend()
            labels = backend.load_labels()
            assert labels.items == []


def test_postgres_backend_list_runs():
    mock_conn = MagicMock()
    mock_conn.execute.return_value.fetchall.return_value = []
    mock_pool = MagicMock()
    mock_pool.connection.return_value.__enter__ = MagicMock(return_value=mock_conn)
    mock_pool.connection.return_value.__exit__ = MagicMock(return_value=False)

    mock_psycopg_pool = MagicMock()
    mock_psycopg_pool.ConnectionPool.return_value = mock_pool

    mock_psycopg_rows = MagicMock()
    mock_psycopg_rows.dict_row = MagicMock()

    with patch.dict(sys.modules, {
        "psycopg_pool": mock_psycopg_pool,
        "psycopg.rows": mock_psycopg_rows,
    }):
        if "dream_eval.backends_pg" in sys.modules:
            del sys.modules["dream_eval.backends_pg"]

        with patch.dict("os.environ", {"DATABASE_URL": "postgresql://test"}):
            from dream_eval.backends_pg import PostgresEvalBackend
            backend = PostgresEvalBackend()
            runs = backend.list_runs()
            assert runs == []
