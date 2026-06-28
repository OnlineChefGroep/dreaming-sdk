"""Tests for Sprint 2 adapter contract and in-memory proof (CHEF-1007, CHEF-1008).

Verifies:
- MemoryEngine and GovernanceEngine Protocol compliance
- InMemoryAdapter satisfies both protocols
- Full governance lifecycle through the adapter interface
- Adapter is usable as a drop-in replacement for AgentMemoryStore
"""

from __future__ import annotations

from uuid import uuid4

from dreaming_memory.store.adapter import GovernanceEngine, MemoryEngine
from dreaming_memory.store.in_memory import InMemoryAdapter
from dreaming_memory.types import (
    CuratorDecision,
    CuratorState,
    Evidence,
    EvidenceType,
    MemoryRecord,
    MemorySource,
    MemoryType,
    SessionType,
    VerifierResult,
    VerifierStatus,
)

# ------------------------------------------------------------------
# Protocol compliance
# ------------------------------------------------------------------

def test_in_memory_adapter_satisfies_memory_engine():
    adapter = InMemoryAdapter()
    assert isinstance(adapter, MemoryEngine)


def test_in_memory_adapter_satisfies_governance_engine():
    adapter = InMemoryAdapter()
    assert isinstance(adapter, GovernanceEngine)


def test_in_memory_adapter_satisfies_both_protocols():
    adapter = InMemoryAdapter()
    assert isinstance(adapter, MemoryEngine)
    assert isinstance(adapter, GovernanceEngine)


# ------------------------------------------------------------------
# MemoryEngine operations
# ------------------------------------------------------------------

def _make_record(**overrides) -> MemoryRecord:
    defaults = dict(
        agent_id="agent-1",
        session_id="session-1",
        session_type=SessionType.GENERIC,
        memory_type=MemoryType.OBSERVATION,
        content={"key": "value"},
        source=MemorySource.SDK,
    )
    defaults.update(overrides)
    return MemoryRecord(**defaults)


def test_write_assigns_id():
    adapter = InMemoryAdapter()
    record = adapter.write(_make_record())
    assert record.id is not None


def test_write_preserves_existing_id():
    adapter = InMemoryAdapter()
    rid = uuid4()
    record = adapter.write(_make_record(id=rid))
    assert record.id == rid


def test_get_returns_written_record():
    adapter = InMemoryAdapter()
    record = adapter.write(_make_record())
    fetched = adapter.get(record.id)
    assert fetched is not None
    assert fetched.id == record.id
    assert fetched.content == {"key": "value"}


def test_get_nonexistent_returns_none():
    adapter = InMemoryAdapter()
    assert adapter.get(uuid4()) is None


def test_query_filters_by_agent_id():
    adapter = InMemoryAdapter()
    adapter.write(_make_record(agent_id="a1"))
    adapter.write(_make_record(agent_id="a2"))
    adapter.write(_make_record(agent_id="a1"))

    results = adapter.query(agent_id="a1")
    assert len(results) == 2


def test_query_filters_by_memory_type():
    adapter = InMemoryAdapter()
    adapter.write(_make_record(memory_type=MemoryType.FACT))
    adapter.write(_make_record(memory_type=MemoryType.OBSERVATION))

    results = adapter.query(memory_type=MemoryType.FACT)
    assert len(results) == 1


def test_query_respects_limit():
    adapter = InMemoryAdapter()
    for _ in range(10):
        adapter.write(_make_record())
    results = adapter.query(limit=3)
    assert len(results) == 3


def test_update_content():
    adapter = InMemoryAdapter()
    record = adapter.write(_make_record())
    updated = adapter.update_content(record.id, {"new": "data"})
    assert updated is not None
    assert updated.content == {"new": "data"}


def test_update_content_nonexistent():
    adapter = InMemoryAdapter()
    assert adapter.update_content(uuid4(), {}) is None


def test_find_active_by_dedupe_key():
    adapter = InMemoryAdapter()
    record = adapter.write(_make_record(metadata={"dedupe_key": "dk-1"}))
    found = adapter.find_active_by_dedupe_key("dk-1")
    assert found is not None
    assert found.id == record.id


def test_find_active_by_dedupe_key_excludes_rolled_back():
    adapter = InMemoryAdapter()
    record = adapter.write(_make_record(metadata={"dedupe_key": "dk-2"}))
    # Simulate rolled_back
    decision = CuratorDecision(
        memory_id=record.id,
        state=CuratorState.ROLLED_BACK,
        decided_by="test",
    )
    adapter.write_curator_decision(decision)
    found = adapter.find_active_by_dedupe_key("dk-2")
    assert found is None


# ------------------------------------------------------------------
# GovernanceEngine operations
# ------------------------------------------------------------------

def test_write_and_get_evidence():
    adapter = InMemoryAdapter()
    memory = adapter.write(_make_record())
    ev = Evidence(
        evidence_type=EvidenceType.TRANSCRIPT,
        source_url="https://example.com",
        excerpt="test",
    )
    ev.memory_id = memory.id
    stored = adapter.write_evidence(ev)
    assert stored.id is not None

    results = adapter.get_evidence_for_memory(memory.id)
    assert len(results) == 1
    assert results[0].evidence_type == EvidenceType.TRANSCRIPT


def test_write_and_get_verifier_result():
    adapter = InMemoryAdapter()
    memory = adapter.write(_make_record())
    vr = VerifierResult(
        status=VerifierStatus.PASS,
        score=0.95,
        rationale="Looks good",
        checked_by="v1",
    )
    vr.memory_id = memory.id
    stored = adapter.write_verifier_result(vr)
    assert stored.id is not None

    results = adapter.get_verifier_results_for_memory(memory.id)
    assert len(results) == 1
    assert results[0].score == 0.95


def test_write_and_get_curator_decision():
    adapter = InMemoryAdapter()
    memory = adapter.write(_make_record())
    cd = CuratorDecision(
        memory_id=memory.id,
        state=CuratorState.PROPOSED,
        decided_by="agent-1",
    )
    stored = adapter.write_curator_decision(cd)
    assert stored.id is not None

    active = adapter.get_active_curator_decision(memory.id)
    assert active is not None
    assert active.state == CuratorState.PROPOSED


def test_update_curator_decision():
    adapter = InMemoryAdapter()
    memory = adapter.write(_make_record())
    cd = CuratorDecision(
        memory_id=memory.id,
        state=CuratorState.PROPOSED,
        decided_by="agent-1",
    )
    adapter.write_curator_decision(cd)

    updated = CuratorDecision(
        memory_id=memory.id,
        state=CuratorState.REVIEWING,
        previous_state=CuratorState.PROPOSED,
        decided_by="c1",
    )
    adapter.update_curator_decision(memory.id, updated)

    active = adapter.get_active_curator_decision(memory.id)
    assert active is not None
    assert active.state == CuratorState.REVIEWING


def test_get_curator_decisions_by_state():
    adapter = InMemoryAdapter()
    m1 = adapter.write(_make_record())
    m2 = adapter.write(_make_record())
    adapter.write_curator_decision(
        CuratorDecision(memory_id=m1.id, state=CuratorState.PROPOSED)
    )
    adapter.write_curator_decision(
        CuratorDecision(memory_id=m2.id, state=CuratorState.PROPOSED)
    )
    results = adapter.get_curator_decisions_by_state(CuratorState.PROPOSED)
    assert len(results) == 2


def test_curator_metrics():
    adapter = InMemoryAdapter()
    m = adapter.write(_make_record())
    adapter.write_curator_decision(
        CuratorDecision(memory_id=m.id, state=CuratorState.PROPOSED)
    )
    metrics = adapter.curator_metrics()
    assert metrics["total"] == 1
    assert len(metrics["by_state"]) == 1
    assert metrics["by_state"][0]["state"] == "proposed"


# ------------------------------------------------------------------
# Full lifecycle through adapter interface
# ------------------------------------------------------------------

def test_full_governance_lifecycle():
    adapter = InMemoryAdapter()

    # Write
    record = adapter.write(_make_record())

    # Evidence
    ev = Evidence(evidence_type=EvidenceType.LOG, excerpt="score 0.82")
    ev.memory_id = record.id
    adapter.write_evidence(ev)
    assert len(adapter.get_evidence_for_memory(record.id)) == 1

    # Verifier
    vr = VerifierResult(status=VerifierStatus.PASS, score=0.9, checked_by="v1")
    vr.memory_id = record.id
    adapter.write_verifier_result(vr)
    assert len(adapter.get_verifier_results_for_memory(record.id)) == 1

    # Curator: proposed → reviewing → accepted
    adapter.write_curator_decision(
        CuratorDecision(memory_id=record.id, state=CuratorState.PROPOSED)
    )
    adapter.update_curator_decision(
        record.id,
        CuratorDecision(
            memory_id=record.id,
            state=CuratorState.REVIEWING,
            previous_state=CuratorState.PROPOSED,
        ),
    )
    adapter.update_curator_decision(
        record.id,
        CuratorDecision(
            memory_id=record.id,
            state=CuratorState.ACCEPTED,
            previous_state=CuratorState.REVIEWING,
        ),
    )
    active = adapter.get_active_curator_decision(record.id)
    assert active is not None
    assert active.state == CuratorState.ACCEPTED

    # Idempotent write
    existing = adapter.find_active_by_dedupe_key(record.metadata.get("dedupe_key", ""))
    # No dedupe_key set, so None
    assert existing is None


# ------------------------------------------------------------------
# Cleanup
# ------------------------------------------------------------------

def test_close_clears_state():
    adapter = InMemoryAdapter()
    adapter.write(_make_record())
    adapter.close()
    assert adapter.query() == []
