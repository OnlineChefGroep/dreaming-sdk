"""Tests for dreaming-memory MCP server (CHEF-1009).

Tests the tool handler logic without requiring a live MCP connection.
Uses InMemoryAdapter as the backend for fast, isolated tests.
"""

from __future__ import annotations

import json
from unittest.mock import patch

from dreaming_memory.mcp.server import _tool_defs, handle_tool
from dreaming_memory.store.in_memory import InMemoryAdapter
from dreaming_memory.types import (
    MemorySource,
    MemoryType,
    SessionType,
)


def test_tool_definitions_are_valid():
    """All tool definitions have required fields."""
    for td in _tool_defs:
        assert "name" in td
        assert "description" in td
        assert "inputSchema" in td
        assert td["inputSchema"]["type"] == "object"


def test_tool_names_unique():
    names = [td["name"] for td in _tool_defs]
    assert len(names) == len(set(names))


def test_handle_unknown_tool():
    result = handle_tool("nonexistent_tool", {})
    parsed = json.loads(result)
    assert "error" in parsed


@patch("dreaming_memory.mcp.server._get_store")
def test_memory_write(mock_get_store):
    adapter = InMemoryAdapter()
    mock_get_store.return_value = adapter

    result = handle_tool("memory_write", {
        "agent_id": "test-agent",
        "session_id": "test-session",
        "memory_type": "observation",
        "content": {"key": "value"},
    })
    parsed = json.loads(result)
    assert "id" in parsed
    assert "created_at" in parsed


@patch("dreaming_memory.mcp.server._get_store")
def test_memory_recall(mock_get_store):
    adapter = InMemoryAdapter()
    mock_get_store.return_value = adapter

    # Write some records first
    adapter.write(
        __import__("dreaming_memory.types", fromlist=["MemoryRecord"]).MemoryRecord(
            agent_id="a1", session_id="s1",
            session_type=SessionType.GENERIC,
            memory_type=MemoryType.OBSERVATION,
            content={"x": 1}, source=MemorySource.SDK,
        )
    )

    result = handle_tool("memory_recall", {"agent_id": "a1"})
    parsed = json.loads(result)
    assert parsed["total"] == 1
    assert parsed["items"][0]["agent_id"] == "a1"


@patch("dreaming_memory.mcp.server._get_store")
def test_memory_propose(mock_get_store):
    adapter = InMemoryAdapter()
    mock_get_store.return_value = adapter

    result = handle_tool("memory_propose", {
        "agent_id": "agent-1",
        "session_id": "sess-1",
        "memory_type": "observation",
        "content": {"faithfulness": 0.8},
        "evidence": [
            {"evidence_type": "transcript", "excerpt": "score 0.8", "confidence": 0.9}
        ],
    })
    parsed = json.loads(result)
    assert "memory_id" in parsed
    assert parsed["state"] == "proposed"
    assert parsed["evidence_count"] == 1


@patch("dreaming_memory.mcp.server._get_store")
def test_memory_verify(mock_get_store):
    adapter = InMemoryAdapter()
    mock_get_store.return_value = adapter

    # First propose a memory
    propose_result = json.loads(handle_tool("memory_propose", {
        "agent_id": "agent-1",
        "session_id": "sess-1",
        "memory_type": "observation",
        "content": {},
        "evidence": [{"evidence_type": "log"}],
    }))
    mid = propose_result["memory_id"]

    result = handle_tool("memory_verify", {
        "memory_id": mid,
        "status": "pass",
        "score": 0.95,
        "rationale": "Looks good",
        "checked_by": "v1",
    })
    parsed = json.loads(result)
    assert parsed["status"] == "pass"
    assert parsed["score"] == 0.95


@patch("dreaming_memory.mcp.server._get_store")
def test_memory_curate_valid_transition(mock_get_store):
    adapter = InMemoryAdapter()
    mock_get_store.return_value = adapter

    propose_result = json.loads(handle_tool("memory_propose", {
        "agent_id": "agent-1",
        "session_id": "sess-1",
        "memory_type": "observation",
        "content": {},
        "evidence": [{"evidence_type": "log"}],
    }))
    mid = propose_result["memory_id"]

    result = handle_tool("memory_curate", {
        "memory_id": mid,
        "new_state": "reviewing",
        "decided_by": "c1",
        "rationale": "Reviewing",
    })
    parsed = json.loads(result)
    assert parsed["state"] == "reviewing"
    assert parsed["previous"] == "proposed"


@patch("dreaming_memory.mcp.server._get_store")
def test_memory_curate_invalid_transition(mock_get_store):
    adapter = InMemoryAdapter()
    mock_get_store.return_value = adapter

    propose_result = json.loads(handle_tool("memory_propose", {
        "agent_id": "agent-1",
        "session_id": "sess-1",
        "memory_type": "observation",
        "content": {},
        "evidence": [{"evidence_type": "log"}],
    }))
    mid = propose_result["memory_id"]

    result = handle_tool("memory_curate", {
        "memory_id": mid,
        "new_state": "accepted",  # invalid: must go through reviewing
    })
    parsed = json.loads(result)
    assert "error" in parsed
    assert "Invalid transition" in parsed["error"]


@patch("dreaming_memory.mcp.server._get_store")
def test_memory_governance(mock_get_store):
    adapter = InMemoryAdapter()
    mock_get_store.return_value = adapter

    propose_result = json.loads(handle_tool("memory_propose", {
        "agent_id": "agent-1",
        "session_id": "sess-1",
        "memory_type": "observation",
        "content": {"x": 1},
        "evidence": [{"evidence_type": "transcript", "excerpt": "test"}],
    }))
    mid = propose_result["memory_id"]

    result = handle_tool("memory_governance", {"memory_id": mid})
    parsed = json.loads(result)
    assert parsed["memory"]["id"] == mid
    assert len(parsed["evidence"]) == 1
    assert parsed["curator_decision"]["state"] == "proposed"


@patch("dreaming_memory.mcp.server._get_store")
def test_memory_metrics(mock_get_store):
    adapter = InMemoryAdapter()
    mock_get_store.return_value = adapter

    result = handle_tool("memory_metrics", {"days": 7})
    parsed = json.loads(result)
    assert "memory" in parsed
    assert "governance" in parsed
