"""Memory engine adapter contract v1 (CHEF-1007).

Defines the Protocol that any memory backend must implement to be usable
by the dreaming-sdk trust/governance layer.

The contract is split into two layers:
- MemoryEngine — core storage/retrieval (write, query, get, update)
- GovernanceEngine — trust pipeline (evidence, verifier, curator)

A backend implements both protocols. The trust layer only depends on the
protocols, never on concrete implementations.

Usage:
    from dreaming_memory.store.adapter import MemoryEngine, GovernanceEngine

    class MyMem0Adapter(MemoryEngine, GovernanceEngine):
        ...
"""

from __future__ import annotations

from typing import Any, Protocol, runtime_checkable
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


@runtime_checkable
class MemoryEngine(Protocol):
    """Core storage/retrieval contract for memory backends.

    Any backend that can store and retrieve MemoryRecords satisfies this.
    """

    def write(self, record: MemoryRecord) -> MemoryRecord:
        """Persist a memory record, returning it with an assigned id."""
        ...

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
        """Query memory records with optional filters."""
        ...

    def get(self, memory_id: UUID) -> MemoryRecord | None:
        """Retrieve a single memory record by id."""
        ...

    def update_content(
        self, memory_id: UUID, content: dict[str, Any]
    ) -> MemoryRecord | None:
        """Update the content field of a memory record."""
        ...

    def find_active_by_dedupe_key(self, dedupe_key: str) -> MemoryRecord | None:
        """Find an active memory record by dedupe key (for idempotent writes)."""
        ...

    def ensure_schema(self) -> None:
        """Create tables/indexes if they don't exist."""
        ...

    def close(self) -> None:
        """Release resources."""
        ...


@runtime_checkable
class GovernanceEngine(Protocol):
    """Trust pipeline contract — evidence, verifier results, curator decisions.

    A backend that supports the governance lifecycle implements this.
    Backends that don't support governance (e.g. simple key-value stores)
    can return empty lists / None for all methods.
    """

    def write_evidence(self, evidence: Evidence) -> Evidence:
        """Persist a piece of evidence supporting a memory claim."""
        ...

    def get_evidence_for_memory(self, memory_id: UUID) -> list[Evidence]:
        """Retrieve all evidence for a given memory."""
        ...

    def write_verifier_result(self, result: VerifierResult) -> VerifierResult:
        """Persist a verifier result for a memory."""
        ...

    def get_verifier_results_for_memory(self, memory_id: UUID) -> list[VerifierResult]:
        """Retrieve all verifier results for a given memory."""
        ...

    def write_curator_decision(self, decision: CuratorDecision) -> CuratorDecision:
        """Persist the initial curator decision for a proposed memory."""
        ...

    def get_active_curator_decision(
        self, memory_id: UUID
    ) -> CuratorDecision | None:
        """Get the active (non-terminal) curator decision for a memory."""
        ...

    def update_curator_decision(
        self, memory_id: UUID, decision: CuratorDecision
    ) -> CuratorDecision:
        """Update the curator decision (state transition)."""
        ...

    def get_curator_decisions_by_state(
        self, state: CuratorState, limit: int = 50
    ) -> list[CuratorDecision]:
        """List curator decisions in a given state."""
        ...

    def curator_metrics(self, days: int = 14) -> dict[str, Any]:
        """Aggregate curator lifecycle metrics."""
        ...
