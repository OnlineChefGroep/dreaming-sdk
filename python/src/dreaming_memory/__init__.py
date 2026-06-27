"""Agent-agnostic memory extension — Postgres-backed agent memory."""

from dreaming_memory.agent_memory import AgentMemory
from dreaming_memory.config import FleetConfig
from dreaming_memory.session import SessionContext
from dreaming_memory.types import MemoryRecord, MemorySource, MemoryType, SessionType

__all__ = [
    "AgentMemory",
    "FleetConfig",
    "MemoryRecord",
    "MemorySource",
    "MemoryType",
    "SessionContext",
    "SessionType",
]

__version__ = "0.2.0"
