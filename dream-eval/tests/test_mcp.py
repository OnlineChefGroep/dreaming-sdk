"""Tests for dream-eval MCP server."""

import json

from dream_eval.mcp.server import METRICS_SCHEMA, TOOL_DEFINITIONS, handle_tool


def test_handle_tool_dream_score():
    args = {
        "proposed": [{"id": "a", "category": "pref", "content": {"key": "val"}}],
        "labels": [{"id": "a", "category": "pref", "content": {"key": "val"}}],
    }
    result = json.loads(handle_tool("dream_score", args))
    assert result["faithfulness_score"] == 1.0


def test_handle_tool_dream_check_secrets_no_patterns():
    result = json.loads(handle_tool("dream_check_secrets", {"text": "clean"}))
    assert result["status"] == "pass"


def test_handle_tool_dream_check_secrets_explicit_empty_skips():
    result = json.loads(handle_tool(
        "dream_check_secrets", {"text": "clean", "forbidden_patterns": []}
    ))
    assert result["status"] == "skip"


def test_handle_tool_dream_check_secrets_with_patterns():
    result = json.loads(handle_tool(
        "dream_check_secrets",
        {"text": "clean", "forbidden_patterns": [r"sk-.*"]},
    ))
    assert result["status"] == "pass"


def test_handle_tool_dream_check_secrets_fail():
    result = json.loads(handle_tool(
        "dream_check_secrets",
        {"text": "sk-abc123", "forbidden_patterns": [r"sk-.*"]},
    ))
    assert result["status"] == "fail"


def test_handle_tool_dream_check_hash():
    result = json.loads(handle_tool("dream_check_hash", {"content": "hello"}))
    assert result["status"] == "pass"
    assert "hash" in result["details"]


def test_handle_tool_dream_check_hash_with_expected():
    from dream_eval.gates import _canonical_hash
    expected = _canonical_hash("hello")
    result = json.loads(handle_tool(
        "dream_check_hash", {"content": "hello", "expected_hash": expected}
    ))
    assert result["status"] == "pass"


def test_handle_tool_dream_check_hash_mismatch():
    result = json.loads(handle_tool(
        "dream_check_hash", {"content": "hello", "expected_hash": "sha256:wrong"}
    ))
    assert result["status"] == "fail"


def test_handle_tool_dream_metrics_schema():
    result = json.loads(handle_tool("dream_metrics_schema", {}))
    assert "faithfulness_score" in result


def test_handle_tool_unknown():
    result = json.loads(handle_tool("unknown_tool", {}))
    assert "error" in result


def test_tool_definitions_count():
    assert len(TOOL_DEFINITIONS) == 4


def test_metrics_schema_keys():
    assert len(METRICS_SCHEMA) == 26


def test_handle_tool_dream_score_mismatch():
    args = {
        "proposed": [{"id": "a", "category": "pref", "content": {"key": "x"}}],
        "labels": [{"id": "a", "category": "pref", "content": {"key": "y"}}],
    }
    result = json.loads(handle_tool("dream_score", args))
    assert result["faithfulness_score"] == 0.0
