"""Tests for dreaming-memory Postgres store."""

import sys
from unittest.mock import MagicMock, patch

from dreaming_memory.types import MemoryRecord, MemorySource, MemoryType, SessionType


def test_agent_memory_store_init():
    mock_pool = MagicMock()
    mock_psycopg_pool = MagicMock()
    mock_psycopg_pool.ConnectionPool.return_value = mock_pool
    mock_psycopg_rows = MagicMock()
    mock_psycopg_rows.dict_row = MagicMock()

    with patch.dict(sys.modules, {
        "psycopg_pool": mock_psycopg_pool,
        "psycopg.rows": mock_psycopg_rows,
    }):
        if "dreaming_memory.store.postgres" in sys.modules:
            del sys.modules["dreaming_memory.store.postgres"]

        with patch.dict("os.environ", {"DATABASE_URL": "postgresql://test"}):
            from dreaming_memory.store.postgres import AgentMemoryStore
            store = AgentMemoryStore()
            assert store._pool is mock_pool


def test_agent_memory_store_no_dsn():
    with patch.dict("os.environ", {}, clear=True):
        from dreaming_memory.store.postgres import AgentMemoryStore
        try:
            AgentMemoryStore()
        except ValueError as e:
            assert "No database DSN" in str(e)


def test_agent_memory_store_context_manager():
    mock_pool = MagicMock()
    mock_psycopg_pool = MagicMock()
    mock_psycopg_pool.ConnectionPool.return_value = mock_pool
    mock_psycopg_rows = MagicMock()
    mock_psycopg_rows.dict_row = MagicMock()

    with patch.dict(sys.modules, {
        "psycopg_pool": mock_psycopg_pool,
        "psycopg.rows": mock_psycopg_rows,
    }):
        if "dreaming_memory.store.postgres" in sys.modules:
            del sys.modules["dreaming_memory.store.postgres"]

        with patch.dict("os.environ", {"DATABASE_URL": "postgresql://test"}):
            from dreaming_memory.store.postgres import AgentMemoryStore
            with AgentMemoryStore() as store:
                pass
            store._pool.close.assert_called_once()


def test_agent_memory_store_write():
    from uuid import uuid4
    mock_conn = MagicMock()
    mock_conn.execute.return_value.fetchone.return_value = {
        "id": uuid4(),
        "agent_id": "agent",
        "session_id": "session",
        "session_type": "generic",
        "memory_type": "observation",
        "content": {"key": "value"},
        "source": "sdk",
        "created_at": MagicMock(isoformat=MagicMock(return_value="2026-01-01")),
        "updated_at": MagicMock(isoformat=MagicMock(return_value="2026-01-01")),
        "metadata": {},
    }
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
        if "dreaming_memory.store.postgres" in sys.modules:
            del sys.modules["dreaming_memory.store.postgres"]

        with patch.dict("os.environ", {"DATABASE_URL": "postgresql://test"}):
            from dreaming_memory.store.postgres import AgentMemoryStore
            store = AgentMemoryStore()
            record = MemoryRecord(
                agent_id="agent",
                session_id="session",
                session_type=SessionType.GENERIC,
                memory_type=MemoryType.OBSERVATION,
                content={"key": "value"},
                source=MemorySource.SDK,
            )
            result = store.write(record)
            assert result.agent_id == "agent"


def test_agent_memory_store_get():
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
        if "dreaming_memory.store.postgres" in sys.modules:
            del sys.modules["dreaming_memory.store.postgres"]

        with patch.dict("os.environ", {"DATABASE_URL": "postgresql://test"}):
            from dreaming_memory.store.postgres import AgentMemoryStore
            store = AgentMemoryStore()
            result = store.get("nonexistent")
            assert result is None


def test_agent_memory_store_query():
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
        if "dreaming_memory.store.postgres" in sys.modules:
            del sys.modules["dreaming_memory.store.postgres"]

        with patch.dict("os.environ", {"DATABASE_URL": "postgresql://test"}):
            from dreaming_memory.store.postgres import AgentMemoryStore
            store = AgentMemoryStore()
            results = store.query()
            assert results == []


def test_agent_memory_store_metrics():
    mock_conn = MagicMock()

    # Make execute return different results for different queries
    def execute_side_effect(sql, *args):
        result = MagicMock()
        # Handle both str and psycopg.sql.Composed/SQL objects
        sql_str = str(sql).lower()
        if "count(*)" in sql_str and "max" not in sql_str and "metadata" not in sql_str:
            result.fetchone.return_value = {"n": 10}
        elif "max" in sql_str:
            result.fetchone.return_value = {"ts": None}
        elif "metadata" in sql_str:
            result.fetchone.return_value = {"n": 5}
        elif "recent" in sql_str or "order by created_at desc limit" in sql_str:
            result.fetchall.return_value = []
        else:
            result.fetchall.return_value = [{"key": "sdk", "n": 5}]
        return result

    mock_conn.execute.side_effect = execute_side_effect
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
        if "dreaming_memory.store.postgres" in sys.modules:
            del sys.modules["dreaming_memory.store.postgres"]

        with patch.dict("os.environ", {"DATABASE_URL": "postgresql://test"}):
            from dreaming_memory.store.postgres import AgentMemoryStore
            store = AgentMemoryStore()
            result = store.metrics()
            assert result["total"] == 10
