"""Tests for Sprint 1 governance pipeline (CHEF-1004/1005/1006).

Covers: Evidence, VerifierResult, CuratorDecision types,
state machine transitions, idempotent writes, and AgentMemory governance methods.
"""

from __future__ import annotations

from unittest.mock import MagicMock
from uuid import uuid4

import pytest

from dreaming_memory.types import (
    CURATOR_VALID_TRANSITIONS,
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
# Type instantiation
# ------------------------------------------------------------------

def test_evidence_instantiation():
    ev = Evidence(
        evidence_type=EvidenceType.TRANSCRIPT,
        source_url="https://run.example.com/run/abc",
        source_id="abc",
        excerpt="faithfulness 0.63",
        confidence=0.9,
    )
    assert ev.evidence_type == EvidenceType.TRANSCRIPT
    assert ev.confidence == 0.9
    assert ev.metadata == {}


def test_verifier_result_instantiation():
    vr = VerifierResult(
        status=VerifierStatus.PASS,
        score=1.0,
        evidence_refs=[uuid4()],
        rationale="All checks passed",
        checked_by="agent-1",
    )
    assert vr.status == VerifierStatus.PASS
    assert vr.score == 1.0
    assert len(vr.evidence_refs) == 1


def test_curator_decision_instantiation():
    cd = CuratorDecision(
        memory_id=uuid4(),
        state=CuratorState.PROPOSED,
        decided_by="agent-1",
        rationale="Auto-proposed",
    )
    assert cd.state == CuratorState.PROPOSED
    assert cd.transitions == []
    assert cd.previous_state is None


# ------------------------------------------------------------------
# State machine
# ------------------------------------------------------------------

def test_curator_valid_transitions_cover_all_states():
    for state in CuratorState:
        assert state in CURATOR_VALID_TRANSITIONS, f"Missing transitions for {state}"


def test_valid_transition_proposed_to_reviewing():
    valid = CURATOR_VALID_TRANSITIONS[CuratorState.PROPOSED]
    assert CuratorState.REVIEWING in valid


def test_valid_transition_reviewing_to_accepted():
    valid = CURATOR_VALID_TRANSITIONS[CuratorState.REVIEWING]
    assert CuratorState.ACCEPTED in valid


def test_valid_transition_reviewing_to_rejected():
    valid = CURATOR_VALID_TRANSITIONS[CuratorState.REVIEWING]
    assert CuratorState.REJECTED in valid


def test_valid_transition_reviewing_to_edited():
    valid = CURATOR_VALID_TRANSITIONS[CuratorState.REVIEWING]
    assert CuratorState.EDITED in valid


def test_valid_transition_reviewing_to_deferred():
    valid = CURATOR_VALID_TRANSITIONS[CuratorState.REVIEWING]
    assert CuratorState.DEFERRED in valid


def test_valid_transition_deferred_to_reviewing():
    valid = CURATOR_VALID_TRANSITIONS[CuratorState.DEFERRED]
    assert CuratorState.REVIEWING in valid


def test_valid_transition_accepted_to_rolled_back():
    valid = CURATOR_VALID_TRANSITIONS[CuratorState.ACCEPTED]
    assert CuratorState.ROLLED_BACK in valid


def test_rolled_back_is_terminal():
    valid = CURATOR_VALID_TRANSITIONS[CuratorState.ROLLED_BACK]
    assert valid == []


def test_rejected_is_terminal():
    valid = CURATOR_VALID_TRANSITIONS[CuratorState.REJECTED]
    assert valid == []


def test_edited_is_terminal():
    valid = CURATOR_VALID_TRANSITIONS[CuratorState.EDITED]
    assert valid == []


def test_invalid_transition_proposed_to_accepted():
    valid = CURATOR_VALID_TRANSITIONS[CuratorState.PROPOSED]
    assert CuratorState.ACCEPTED not in valid


def test_invalid_transition_accepted_to_proposed():
    valid = CURATOR_VALID_TRANSITIONS[CuratorState.ACCEPTED]
    assert CuratorState.PROPOSED not in valid


# ------------------------------------------------------------------
# AgentMemory governance methods
# ------------------------------------------------------------------

class TestAgentMemoryPropose:
    def test_propose_writes_record_evidence_and_decision(self):
        from dreaming_memory.agent_memory import AgentMemory
        from dreaming_memory.session import SessionContext

        mock_store = MagicMock()
        memory = AgentMemory(store=mock_store, enable_sentry=False)

        record_id = uuid4()
        mock_store.write.return_value = MemoryRecord(
            id=record_id,
            agent_id="test-agent",
            session_id="test-session",
            session_type=SessionType.GENERIC,
            memory_type=MemoryType.OBSERVATION,
            content={"key": "value"},
            source=MemorySource.SDK,
        )

        ctx = SessionContext(
            session_id="test-session",
            session_type=SessionType.GENERIC,
        )
        evidence = [
            Evidence(
                evidence_type=EvidenceType.TRANSCRIPT,
                source_url="https://run.example.com/run/abc",
                excerpt="faithfulness 0.63",
                confidence=0.9,
            )
        ]

        memory.propose(
            ctx, MemoryType.OBSERVATION, {"key": "value"}, evidence
        )

        mock_store.write.assert_called_once()
        mock_store.write_evidence.assert_called_once()
        mock_store.write_curator_decision.assert_called_once()
        # Check the record passed to store.write has curator.state set
        written_record = mock_store.write.call_args[0][0]
        assert written_record.metadata.get("curator.state") == "proposed"

    def test_propose_with_empty_evidence(self):
        from dreaming_memory.agent_memory import AgentMemory
        from dreaming_memory.session import SessionContext

        mock_store = MagicMock()
        memory = AgentMemory(store=mock_store, enable_sentry=False)

        record_id = uuid4()
        mock_store.write.return_value = MemoryRecord(
            id=record_id,
            agent_id="test-agent",
            session_id="test-session",
            session_type=SessionType.GENERIC,
            memory_type=MemoryType.OBSERVATION,
            content={},
            source=MemorySource.SDK,
        )

        ctx = SessionContext(
            session_id="test-session",
            session_type=SessionType.GENERIC,
        )
        memory.propose(ctx, MemoryType.OBSERVATION, {}, [])

        mock_store.write.assert_called_once()
        mock_store.write_evidence.assert_not_called()
        mock_store.write_curator_decision.assert_called_once()


class TestAgentMemoryVerify:
    def test_verify_writes_verifier_result(self):
        from dreaming_memory.agent_memory import AgentMemory

        mock_store = MagicMock()
        memory = AgentMemory(store=mock_store, enable_sentry=False)
        memory_id = uuid4()

        result = VerifierResult(
            status=VerifierStatus.PASS,
            score=1.0,
            rationale="All checks passed",
            checked_by="agent-1",
        )

        mock_store.write_verifier_result.return_value = result
        returned = memory.verify(memory_id, result)

        mock_store.write_verifier_result.assert_called_once()
        assert returned.status == VerifierStatus.PASS


class TestAgentMemoryCurate:
    def test_curate_valid_transition(self):
        from dreaming_memory.agent_memory import AgentMemory

        mock_store = MagicMock()
        memory = AgentMemory(store=mock_store, enable_sentry=False)
        memory_id = uuid4()

        current_decision = CuratorDecision(
            memory_id=memory_id,
            state=CuratorState.PROPOSED,
            decided_by="agent-1",
        )
        mock_store.get_active_curator_decision.return_value = current_decision

        updated_decision = CuratorDecision(
            memory_id=memory_id,
            state=CuratorState.REVIEWING,
            previous_state=CuratorState.PROPOSED,
            decided_by="verifier-1",
            rationale="Reviewing OK",
        )
        mock_store.update_curator_decision.return_value = updated_decision

        result = memory.curate(
            memory_id,
            CuratorState.REVIEWING,
            decided_by="verifier-1",
            rationale="Reviewing OK",
        )

        mock_store.update_curator_decision.assert_called_once()
        assert result.state == CuratorState.REVIEWING

    def test_curate_invalid_transition_raises(self):
        from dreaming_memory.agent_memory import AgentMemory

        mock_store = MagicMock()
        memory = AgentMemory(store=mock_store, enable_sentry=False)
        memory_id = uuid4()

        current_decision = CuratorDecision(
            memory_id=memory_id,
            state=CuratorState.PROPOSED,
            decided_by="agent-1",
        )
        mock_store.get_active_curator_decision.return_value = current_decision

        with pytest.raises(ValueError, match="Invalid transition"):
            memory.curate(
                memory_id,
                CuratorState.ACCEPTED,
                decided_by="agent-1",
            )

    def test_curate_no_decision_raises(self):
        from dreaming_memory.agent_memory import AgentMemory

        mock_store = MagicMock()
        memory = AgentMemory(store=mock_store, enable_sentry=False)
        memory_id = uuid4()
        mock_store.get_active_curator_decision.return_value = None

        with pytest.raises(ValueError, match="No active curator decision"):
            memory.curate(memory_id, CuratorState.REVIEWING)

    def test_curate_records_transition_history(self):
        from dreaming_memory.agent_memory import AgentMemory

        mock_store = MagicMock()
        memory = AgentMemory(store=mock_store, enable_sentry=False)
        memory_id = uuid4()

        current_decision = CuratorDecision(
            memory_id=memory_id,
            state=CuratorState.PROPOSED,
            decided_by="agent-1",
            transitions=[],
        )
        mock_store.get_active_curator_decision.return_value = current_decision

        updated_decision = CuratorDecision(
            memory_id=memory_id,
            state=CuratorState.REVIEWING,
            previous_state=CuratorState.PROPOSED,
            decided_by="verifier-1",
            rationale="Reviewing OK",
        )
        mock_store.update_curator_decision.return_value = updated_decision

        memory.curate(
            memory_id,
            CuratorState.REVIEWING,
            decided_by="verifier-1",
            rationale="Reviewing OK",
        )

        call_args = mock_store.update_curator_decision.call_args
        updated = call_args[0][1]
        assert len(updated.transitions) == 1
        assert updated.transitions[0]["from"] == "proposed"
        assert updated.transitions[0]["to"] == "reviewing"


class TestAgentMemoryIdempotentWrite:
    def test_write_idempotent_returns_existing_if_found(self):
        from dreaming_memory.agent_memory import AgentMemory

        mock_store = MagicMock()
        memory = AgentMemory(store=mock_store, enable_sentry=False)

        existing = MemoryRecord(
            id=uuid4(),
            agent_id="test-agent",
            session_id="test-session",
            session_type=SessionType.GENERIC,
            memory_type=MemoryType.OBSERVATION,
            content={"key": "existing"},
            source=MemorySource.SDK,
        )
        mock_store.find_active_by_dedupe_key.return_value = existing

        new_record = MemoryRecord(
            agent_id="test-agent",
            session_id="test-session",
            session_type=SessionType.GENERIC,
            memory_type=MemoryType.OBSERVATION,
            content={"key": "new"},
            source=MemorySource.SDK,
        )

        result = memory.write_idempotent(new_record, dedupe_key="unique-key")

        assert result is existing
        mock_store.write.assert_not_called()

    def test_write_idempotent_writes_new_if_not_found(self):
        from dreaming_memory.agent_memory import AgentMemory

        mock_store = MagicMock()
        memory = AgentMemory(store=mock_store, enable_sentry=False)
        mock_store.find_active_by_dedupe_key.return_value = None

        new_record = MemoryRecord(
            agent_id="test-agent",
            session_id="test-session",
            session_type=SessionType.GENERIC,
            memory_type=MemoryType.OBSERVATION,
            content={"key": "new"},
            source=MemorySource.SDK,
        )

        written = MemoryRecord(
            id=uuid4(),
            agent_id="test-agent",
            session_id="test-session",
            session_type=SessionType.GENERIC,
            memory_type=MemoryType.OBSERVATION,
            content={"key": "new"},
            source=MemorySource.SDK,
        )
        mock_store.write.return_value = written

        result = memory.write_idempotent(new_record, dedupe_key="unique-key")

        assert result is written
        mock_store.write.assert_called_once()
        call_args = mock_store.write.call_args
        written_record = call_args[0][0]
        assert written_record.metadata.get("dedupe_key") == "unique-key"
