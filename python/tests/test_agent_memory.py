"""Tests for dreaming-memory agent_memory module."""

from unittest.mock import MagicMock

from dreaming_memory.session import SessionContext
from dreaming_memory.types import MemoryRecord, MemorySource, MemoryType, SessionType


def test_agent_memory_init():
    mock_store = MagicMock()
    from dreaming_memory.agent_memory import AgentMemory
    memory = AgentMemory(store=mock_store, enable_sentry=False)
    assert memory.store is mock_store


def test_agent_memory_context_manager():
    mock_store = MagicMock()
    from dreaming_memory.agent_memory import AgentMemory
    with AgentMemory(store=mock_store, enable_sentry=False) as memory:
        assert memory is not None
    mock_store.close.assert_called_once()


def test_agent_memory_close():
    mock_store = MagicMock()
    from dreaming_memory.agent_memory import AgentMemory
    memory = AgentMemory(store=mock_store, enable_sentry=False)
    memory.close()
    mock_store.close.assert_called_once()


def test_agent_memory_ensure_schema():
    mock_store = MagicMock()
    from dreaming_memory.agent_memory import AgentMemory
    memory = AgentMemory(store=mock_store, enable_sentry=False)
    memory.ensure_schema()
    mock_store.ensure_schema.assert_called_once()


def test_agent_memory_remember():
    from uuid import uuid4
    mock_store = MagicMock()
    mock_store.write.return_value = MemoryRecord(
        id=uuid4(),
        agent_id="test-agent",
        session_id="test-session",
        session_type=SessionType.GENERIC,
        memory_type=MemoryType.OBSERVATION,
        content={"key": "value"},
        source=MemorySource.SDK,
    )
    from dreaming_memory.agent_memory import AgentMemory
    memory = AgentMemory(store=mock_store, enable_sentry=False)

    ctx = SessionContext(session_id="test-session", session_type=SessionType.GENERIC)
    record = memory.remember(ctx, MemoryType.OBSERVATION, {"key": "value"})
    assert record is not None
    mock_store.write.assert_called_once()


def test_agent_memory_recall():
    mock_store = MagicMock()
    mock_store.query.return_value = []
    from dreaming_memory.agent_memory import AgentMemory
    memory = AgentMemory(store=mock_store, enable_sentry=False)

    results = memory.recall(agent_id="test-agent")
    assert results == []
    mock_store.query.assert_called_once()


def test_agent_memory_recall_session():
    mock_store = MagicMock()
    mock_store.query.return_value = []
    from dreaming_memory.agent_memory import AgentMemory
    memory = AgentMemory(store=mock_store, enable_sentry=False)

    ctx = SessionContext(session_id="test-session", session_type=SessionType.GENERIC)
    results = memory.recall_session(ctx)
    assert results == []


def test_agent_memory_get():
    mock_store = MagicMock()
    mock_store.get.return_value = None
    from dreaming_memory.agent_memory import AgentMemory
    memory = AgentMemory(store=mock_store, enable_sentry=False)

    result = memory.get("test-id")
    assert result is None
    mock_store.get.assert_called_once()


def test_agent_memory_linear_property():
    mock_store = MagicMock()
    from dreaming_memory.agent_memory import AgentMemory
    memory = AgentMemory(store=mock_store, enable_sentry=False)
    # Linear bridge is lazy-loaded
    assert memory._linear is None


def test_agent_memory_notion_property():
    mock_store = MagicMock()
    from dreaming_memory.agent_memory import AgentMemory
    memory = AgentMemory(store=mock_store, enable_sentry=False)
    assert memory._notion is None
