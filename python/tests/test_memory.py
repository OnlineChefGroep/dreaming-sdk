"""Unit tests for dreaming-memory (no external services required)."""

from __future__ import annotations

import pytest

from dreaming_memory.session import SessionContext, resolve_session_type
from dreaming_memory.types import MemoryRecord, MemorySource, MemoryType, SessionType


def test_resolve_session_type_aliases() -> None:
    assert resolve_session_type("dream-eval") == SessionType.DREAM_EVAL
    assert resolve_session_type("factory") == SessionType.GROK
    assert resolve_session_type("unknown_platform") == SessionType.GENERIC


def test_session_context_from_sdk_payload() -> None:
    ctx = SessionContext.from_sdk_payload({
        "transcript_hash": "sha256:abc123",
        "platform": "codex",
        "agent_id": "dream-evaluator",
        "tags": ["golden"],
    })
    assert ctx.session_id == "sha256:abc123"
    assert ctx.session_type == SessionType.CODEX
    assert ctx.agent_id == "dream-evaluator"
    assert ctx.metadata == {"tags": ["golden"]}


def test_session_context_dream_eval() -> None:
    ctx = SessionContext.for_dream_eval("2026-06-15T09-00-00Z")
    assert ctx.session_type == SessionType.DREAM_EVAL
    assert ctx.session_id == "2026-06-15T09-00-00Z"


def test_memory_record_model() -> None:
    record = MemoryRecord(
        agent_id="agent-1",
        session_id="sess-1",
        session_type=SessionType.CURSOR,
        memory_type=MemoryType.FACT,
        content={"key": "value"},
        source=MemorySource.USER,
    )
    assert record.memory_type == MemoryType.FACT
    dumped = record.model_dump()
    assert dumped["source"] == "user"


def test_fleet_config_status_keys() -> None:
    from dreaming_memory import FleetConfig

    config = FleetConfig(database_url="postgresql://u:p@h:5432/db")
    status = config.status()
    assert set(status) == {"database_url", "linear", "notion", "cloudflare", "sentry", "upstash"}
    assert status["database_url"] is True
    redacted = config.redacted()
    assert "***" in redacted["database_url"]


def test_fleet_config_env_override(monkeypatch: pytest.MonkeyPatch) -> None:
    from dreaming_memory import FleetConfig

    monkeypatch.setenv("AGENT_MEMORY_DATABASE_URL", "postgresql://x:y@z:5432/agent_memory")
    monkeypatch.setenv("LINEAR_API_KEY", "lin_api_test")
    config = FleetConfig.load()
    assert config.database_url.endswith("/agent_memory")
    assert config.linear_api_key == "lin_api_test"


def test_init_sentry_noop_without_dsn(monkeypatch: pytest.MonkeyPatch) -> None:
    from dreaming_memory import FleetConfig
    from dreaming_memory.observability import init_sentry

    monkeypatch.delenv("SENTRY_DSN", raising=False)
    config = FleetConfig(database_url="postgresql://u:p@h:5432/db", sentry_dsn=None)
    assert init_sentry(config) is False


def test_oci_build_dsn() -> None:
    from dreaming_memory.store.oci import build_dsn

    dsn = build_dsn("bc-monitor", password="secret")
    assert dsn == "postgresql://postgres:secret@100.78.210.57:5432/agent_memory"


def test_semantic_store_disabled_without_lancedb(monkeypatch: pytest.MonkeyPatch) -> None:
    from dreaming_memory.semantic.lancedb import SemanticMemoryStore

    store = SemanticMemoryStore()
    # When lancedb not installed, enabled is False
    try:
        import lancedb  # noqa: F401
        assert store.enabled is True
    except ImportError:
        assert store.enabled is False
