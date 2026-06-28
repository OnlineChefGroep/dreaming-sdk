"""Agent-agnostic memory extension — Postgres-backed agent memory."""

from dreaming_memory.agent_memory import AgentMemory
from dreaming_memory.config import FleetConfig
from dreaming_memory.session import SessionContext
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

__all__ = [
    "AgentMemory",
    "CuratorDecision",
    "CuratorState",
    "Evidence",
    "EvidenceType",
    "FleetConfig",
    "MemoryRecord",
    "MemorySource",
    "MemoryType",
    "SessionContext",
    "SessionType",
    "VerifierResult",
    "VerifierStatus",
]

__version__ = "0.2.0"
