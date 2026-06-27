"""Extended tests for dreaming-memory CLI."""

import json
from unittest.mock import MagicMock, patch

from dreaming_memory.cli import _enum_value, render_export_markdown
from dreaming_memory.types import MemoryRecord, MemorySource, MemoryType, SessionType


def test_enum_value_enum():
    assert _enum_value(MemoryType.OBSERVATION) == "observation"


def test_enum_value_string():
    assert _enum_value("hello") == "hello"


def test_render_export_empty():
    result = render_export_markdown("session-1", [])
    assert "session-1" in result
    assert "No memory records found" in result


def test_render_export_with_records():
    records = [
        MemoryRecord(
            id=None,
            agent_id="agent",
            session_id="session",
            session_type=SessionType.GENERIC,
            memory_type=MemoryType.OBSERVATION,
            content={"key": "value"},
            source=MemorySource.SDK,
        )
    ]
    result = render_export_markdown("session-1", records)
    assert "observation" in result
    assert "sdk" in result


def test_print_records(capsys):
    from dreaming_memory.cli import _print_records
    records = [
        MemoryRecord(
            id=None,
            agent_id="agent",
            session_id="session",
            session_type=SessionType.GENERIC,
            memory_type=MemoryType.OBSERVATION,
            content={"key": "value"},
            source=MemorySource.SDK,
        )
    ]
    _print_records(records)
    out = capsys.readouterr().out
    data = json.loads(out)
    assert data["agent_id"] == "agent"


def test_cli_main_help(capsys):
    from unittest.mock import patch
    with patch("sys.argv", ["dream-memory"]):
        try:
            from dreaming_memory.cli import main
            main()
        except SystemExit:
            pass


def test_cli_init(capsys):
    with patch("dreaming_memory.cli.AgentMemory") as MockMemory:
        mock_memory = MagicMock()
        MockMemory.return_value.__enter__ = MagicMock(return_value=mock_memory)
        MockMemory.return_value.__exit__ = MagicMock(return_value=False)
        with patch("sys.argv", ["dream-memory", "init"]):
            from dreaming_memory.cli import main
            main()
        mock_memory.ensure_schema.assert_called_once()


def test_cli_metrics(capsys):
    import dreaming_memory.store.postgres as pg_mod
    mock_store = MagicMock()
    mock_store.metrics.return_value = {"total": 10}
    mock_context = MagicMock()
    mock_context.__enter__ = MagicMock(return_value=mock_store)
    mock_context.__exit__ = MagicMock(return_value=False)

    mock_store_cls = MagicMock(return_value=mock_context)
    original = pg_mod.AgentMemoryStore
    pg_mod.AgentMemoryStore = mock_store_cls
    try:
        with patch("sys.argv", ["dream-memory", "metrics"]):
            from dreaming_memory.cli import main
            main()
        out = capsys.readouterr().out
        data = json.loads(out)
        assert data["total"] == 10
    finally:
        pg_mod.AgentMemoryStore = original


def test_cli_remember(capsys):
    with patch("dreaming_memory.cli.AgentMemory") as MockMemory:
        mock_memory = MagicMock()
        mock_memory.remember.return_value = MemoryRecord(
            id=None,
            agent_id="agent",
            session_id="session",
            session_type=SessionType.GENERIC,
            memory_type=MemoryType.OBSERVATION,
            content={"key": "value"},
            source=MemorySource.SDK,
        )
        MockMemory.return_value.__enter__ = MagicMock(return_value=mock_memory)
        MockMemory.return_value.__exit__ = MagicMock(return_value=False)
        argv = ["dream-memory", "remember", "--session-id", "s1", "--content", '{"k":"v"}']
        with patch("sys.argv", argv):
            from dreaming_memory.cli import main
            main()
        mock_memory.remember.assert_called_once()


def test_cli_recall(capsys):
    with patch("dreaming_memory.cli.AgentMemory") as MockMemory:
        mock_memory = MagicMock()
        mock_memory.recall.return_value = []
        MockMemory.return_value.__enter__ = MagicMock(return_value=mock_memory)
        MockMemory.return_value.__exit__ = MagicMock(return_value=False)
        with patch("sys.argv", ["dream-memory", "recall"]):
            from dreaming_memory.cli import main
            main()
        mock_memory.recall.assert_called_once()


def test_cli_doctor(capsys):
    with patch("dreaming_memory.cli._doctor") as mock_doctor:
        with patch("sys.argv", ["dream-memory", "doctor"]):
            from dreaming_memory.cli import main
            main()
        mock_doctor.assert_called_once()
