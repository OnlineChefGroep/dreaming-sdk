"""In-memory adapter proof (CHEF-1008).

Implements MemoryEngine + GovernanceEngine entirely in-memory.
Useful as:
- Proof that the adapter contract is satisfiable
- Test double for unit tests (no Postgres required)
- Reference implementation for building real adapters (Mem0, Zep, etc.)
"""

from __future__ import annotations

from datetime import UTC, datetime
from typing import Any
from uuid import UUID, uuid4

from dreaming_memory.types import (
    CuratorDecision,
    CuratorState,
    Evidence,
    MemoryRecord,
    MemorySource,
    MemoryType,
    SessionType,
    VerifierResult,
)


class InMemoryAdapter:
    """Fully in-memory implementation of MemoryEngine + GovernanceEngine.

    Usage:
        adapter = InMemoryAdapter()
        record = adapter.write(MemoryRecord(
            agent_id="a1", session_id="s1",
            session_type=SessionType.GENERIC,
            memory_type=MemoryType.OBSERVATION,
            content={"key": "val"}, source=MemorySource.SDK,
        ))
    """

    def __init__(self) -> None:
        self._records: dict[str, MemoryRecord] = {}
        self._evidence: dict[str, list[Evidence]] = {}
        self._verifier_results: dict[str, list[VerifierResult]] = {}
        self._curator_decisions: dict[str, list[CuratorDecision]] = {}

    # ------------------------------------------------------------------
    # MemoryEngine
    # ------------------------------------------------------------------

    def write(self, record: MemoryRecord) -> MemoryRecord:
        if record.id is None:
            record = record.model_copy(update={"id": uuid4()})
        if record.created_at is None:
            record = record.model_copy(update={"created_at": datetime.now(UTC)})
        self._records[str(record.id)] = record
        return record

    def query(
        self,
        *,
        agent_id: str | None = None,
        session_id: str | None = None,
        session_type: SessionType | None = None,
        memory_type: MemoryType | None = None,
        source: MemorySource | None = None,
        limit: int = 50,
    ) -> list[MemoryRecord]:
        results = []
        for r in self._records.values():
            if agent_id and r.agent_id != agent_id:
                continue
            if session_id and r.session_id != session_id:
                continue
            if session_type and r.session_type != session_type:
                continue
            if memory_type and r.memory_type != memory_type:
                continue
            if source and r.source != source:
                continue
            results.append(r)
        return results[:limit]

    def get(self, memory_id: UUID) -> MemoryRecord | None:
        return self._records.get(str(memory_id))

    def update_content(
        self, memory_id: UUID, content: dict[str, Any]
    ) -> MemoryRecord | None:
        rec = self._records.get(str(memory_id))
        if rec is None:
            return None
        updated = rec.model_copy(update={"content": content})
        self._records[str(memory_id)] = updated
        return updated

    def find_active_by_dedupe_key(self, dedupe_key: str) -> MemoryRecord | None:
        for rec in self._records.values():
            if rec.metadata.get("dedupe_key") != dedupe_key:
                continue
            # Check if any decision is in a terminal state
            decisions = self._curator_decisions.get(str(rec.id), [])
            terminal = {
                CuratorState.REJECTED, CuratorState.EDITED, CuratorState.ROLLED_BACK
            }
            if any(d.state in terminal for d in decisions):
                continue
            return rec
        return None

    def ensure_schema(self) -> None:
        pass  # no-op for in-memory

    def close(self) -> None:
        self._records.clear()
        self._evidence.clear()
        self._verifier_results.clear()
        self._curator_decisions.clear()

    # ------------------------------------------------------------------
    # GovernanceEngine
    # ------------------------------------------------------------------

    def write_evidence(self, evidence: Evidence) -> Evidence:
        if evidence.id is None:
            evidence = evidence.model_copy(update={"id": uuid4()})
        if evidence.captured_at is None:
            evidence = evidence.model_copy(
                update={"captured_at": datetime.now(UTC)}
            )
        key = str(evidence.memory_id)
        self._evidence.setdefault(key, []).append(evidence)
        return evidence

    def get_evidence_for_memory(self, memory_id: UUID) -> list[Evidence]:
        return list(self._evidence.get(str(memory_id), []))

    def write_verifier_result(self, result: VerifierResult) -> VerifierResult:
        if result.id is None:
            result = result.model_copy(update={"id": uuid4()})
        if result.checked_at is None:
            result = result.model_copy(
                update={"checked_at": datetime.now(UTC)}
            )
        key = str(result.memory_id)
        self._verifier_results.setdefault(key, []).append(result)
        return result

    def get_verifier_results_for_memory(self, memory_id: UUID) -> list[VerifierResult]:
        return list(self._verifier_results.get(str(memory_id), []))

    def write_curator_decision(self, decision: CuratorDecision) -> CuratorDecision:
        if decision.id is None:
            decision = decision.model_copy(update={"id": uuid4()})
        if decision.decided_at is None:
            decision = decision.model_copy(
                update={"decided_at": datetime.now(UTC)}
            )
        key = str(decision.memory_id)
        self._curator_decisions.setdefault(key, []).append(decision)
        return decision

    def get_active_curator_decision(
        self, memory_id: UUID
    ) -> CuratorDecision | None:
        decisions = self._curator_decisions.get(str(memory_id), [])
        terminal = {CuratorState.REJECTED, CuratorState.EDITED, CuratorState.ROLLED_BACK}
        for d in reversed(decisions):
            if d.state not in terminal:
                return d
        return None

    def update_curator_decision(
        self, memory_id: UUID, decision: CuratorDecision
    ) -> CuratorDecision:
        key = str(memory_id)
        decisions = self._curator_decisions.get(key, [])
        # Replace the last active decision
        for i in range(len(decisions) - 1, -1, -1):
            if decisions[i].state not in {
                CuratorState.REJECTED, CuratorState.EDITED, CuratorState.ROLLED_BACK
            }:
                decisions[i] = decision
                break
        else:
            decisions.append(decision)
        self._curator_decisions[key] = decisions
        return decision

    def get_curator_decisions_by_state(
        self, state: CuratorState, limit: int = 50
    ) -> list[CuratorDecision]:
        results = []
        for decisions in self._curator_decisions.values():
            for d in decisions:
                if d.state == state:
                    results.append(d)
                    if len(results) >= limit:
                        return results
        return results

    def curator_metrics(self, days: int = 14) -> dict[str, Any]:
        all_decisions = []
        for decisions in self._curator_decisions.values():
            all_decisions.extend(decisions)

        by_state: dict[str, int] = {}
        for d in all_decisions:
            by_state[d.state.value] = by_state.get(d.state.value, 0) + 1

        return {
            "total": len(all_decisions),
            "by_state": [{"state": s, "count": c} for s, c in by_state.items()],
            "per_day": [],
        }

    def metrics(self, days: int = 14) -> dict[str, Any]:
        """Aggregate memory record metrics (by source, type, agent, recent)."""
        records = list(self._records.values())
        total = len(records)

        by_source: dict[str, int] = {}
        by_type: dict[str, int] = {}
        by_agent: dict[str, int] = {}
        for r in records:
            by_source[r.source.value] = by_source.get(r.source.value, 0) + 1
            by_type[r.memory_type.value] = by_type.get(r.memory_type.value, 0) + 1
            by_agent[r.agent_id] = by_agent.get(r.agent_id, 0) + 1

        return {
            "total": total,
            "by_source": [{"key": k, "count": v} for k, v in by_source.items()],
            "by_memory_type": [{"key": k, "count": v} for k, v in by_type.items()],
            "by_agent": [{"key": k, "count": v} for k, v in by_agent.items()],
            "by_session_type": [],
            "recent": [],
            "per_day": [],
            "last_activity": None,
            "triage_decisions": 0,
        }
