"""Mem0 adapter skeleton (CHEF-1008).

Demonstrates how an external memory engine (Mem0) gets wrapped by the
dreaming-sdk trust layer. This is a structural proof — not yet wired to
a live Mem0 instance.

The pattern:
1. Mem0 handles storage/retrieval (its own DB, vectors, graph)
2. This adapter implements MemoryEngine for basic CRUD
3. Governance is layered on top via the trust pipeline

For backends that don't natively support governance, the adapter stores
evidence/verifier/curator data in a sidecar Postgres or SQLite table.

Usage (future):
    from dreaming_memory.store.mem0_adapter import Mem0Adapter
    adapter = Mem0Adapter(api_key="...", project_id="...")
    memory = AgentMemory(store=adapter)
"""

from __future__ import annotations

from typing import Any
from uuid import UUID

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


class Mem0Adapter:
    """Mem0 adapter implementing MemoryEngine + GovernanceEngine.

    Governance data is stored in a sidecar table (evidence, verifier_results,
    curator_decisions) since Mem0 doesn't natively support trust pipelines.

    Status: SKELETON — interface defined, methods raise NotImplementedError.
    """

    def __init__(
        self,
        api_key: str = "",
        project_id: str = "",
        *,
        governance_dsn: str | None = None,
    ) -> None:
        self._api_key = api_key
        self._project_id = project_id
        self._governance_dsn = governance_dsn
        # Future: self._client = Mem0Client(api_key, project_id)
        # Future: self._gov_store = AgentMemoryStore(governance_dsn)

    # ------------------------------------------------------------------
    # MemoryEngine
    # ------------------------------------------------------------------

    def write(self, record: MemoryRecord) -> MemoryRecord:
        raise NotImplementedError("Mem0 write — plug in mem0 client.add()")

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
        raise NotImplementedError("Mem0 query — plug in mem0 client.search()")

    def get(self, memory_id: UUID) -> MemoryRecord | None:
        raise NotImplementedError("Mem0 get — plug in mem0 client.get()")

    def update_content(
        self, memory_id: UUID, content: dict[str, Any]
    ) -> MemoryRecord | None:
        raise NotImplementedError("Mem0 update — plug in mem0 client.update()")

    def find_active_by_dedupe_key(self, dedupe_key: str) -> MemoryRecord | None:
        raise NotImplementedError("Mem0 dedupe — search by metadata dedupe_key")

    def ensure_schema(self) -> None:
        pass  # Mem0 manages its own schema

    def close(self) -> None:
        pass

    # ------------------------------------------------------------------
    # GovernanceEngine — stored in sidecar Postgres
    # ------------------------------------------------------------------

    def write_evidence(self, evidence: Evidence) -> Evidence:
        raise NotImplementedError("Governance sidecar — write_evidence")

    def get_evidence_for_memory(self, memory_id: UUID) -> list[Evidence]:
        raise NotImplementedError("Governance sidecar — get_evidence")

    def write_verifier_result(self, result: VerifierResult) -> VerifierResult:
        raise NotImplementedError("Governance sidecar — write_verifier_result")

    def get_verifier_results_for_memory(self, memory_id: UUID) -> list[VerifierResult]:
        raise NotImplementedError("Governance sidecar — get_verifier_results")

    def write_curator_decision(self, decision: CuratorDecision) -> CuratorDecision:
        raise NotImplementedError("Governance sidecar — write_curator_decision")

    def get_active_curator_decision(
        self, memory_id: UUID
    ) -> CuratorDecision | None:
        raise NotImplementedError("Governance sidecar — get_active_curator_decision")

    def update_curator_decision(
        self, memory_id: UUID, decision: CuratorDecision
    ) -> CuratorDecision:
        raise NotImplementedError("Governance sidecar — update_curator_decision")

    def get_curator_decisions_by_state(
        self, state: CuratorState, limit: int = 50
    ) -> list[CuratorDecision]:
        raise NotImplementedError("Governance sidecar — get_decisions_by_state")

    def curator_metrics(self, days: int = 14) -> dict[str, Any]:
        raise NotImplementedError("Governance sidecar — curator_metrics")
