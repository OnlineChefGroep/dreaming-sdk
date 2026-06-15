"""Lightweight agent memory extension for cursor-dreaming-sdk."""

from cursor_dreaming_memory.agent_memory import AgentMemory
from cursor_dreaming_memory.config import FleetConfig
from cursor_dreaming_memory.session import SessionContext
from cursor_dreaming_memory.types import MemoryRecord, MemorySource, MemoryType, SessionType

__all__ = [
    "AgentMemory",
    "FleetConfig",
    "MemoryRecord",
    "MemorySource",
    "MemoryType",
    "SessionContext",
    "SessionType",
]

__version__ = "0.1.0"
