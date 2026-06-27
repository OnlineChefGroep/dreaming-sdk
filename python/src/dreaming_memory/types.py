"""Shared types for agent memory — aligned with cursor-dreaming-sdk session forms."""

from __future__ import annotations

from datetime import datetime
from enum import StrEnum
from typing import Any
from uuid import UUID

from pydantic import BaseModel, Field


class SessionType(StrEnum):
    """Session forms supported by cursor-dreaming-sdk and multi-agent surfaces."""

    CURSOR = "cursor"
    CLAUDE = "claude"
    CODEX = "codex"
    OPENCODE = "opencode"
    GROK = "grok"
    SDK_LOCAL = "sdk_local"
    SDK_CLOUD = "sdk_cloud"
    DREAM_EVAL = "dream_eval"
    DREAM_LIVE = "dream_live"
    GENERIC = "generic"


class MemoryType(StrEnum):
    """Structured memory categories stored in Postgres JSONB."""

    FACT = "fact"
    OBSERVATION = "observation"
    DECISION = "decision"
    ISSUE_SNAPSHOT = "issue_snapshot"
    COMMENT = "comment"
    PAGE_SNAPSHOT = "page_snapshot"
    TOOL_RESULT = "tool_result"
    EMBEDDING_REF = "embedding_ref"
    TRANSCRIPT_REF = "transcript_ref"


class MemorySource(StrEnum):
    LINEAR = "linear"
    NOTION = "notion"
    TOOL = "tool"
    USER = "user"
    SDK = "sdk"


class MemoryRecord(BaseModel):
    """Row shape for agent_memory — mirrors Postgres schema."""

    id: UUID | None = None
    agent_id: str
    session_id: str
    session_type: SessionType
    memory_type: MemoryType
    content: dict[str, Any] = Field(default_factory=dict)
    source: MemorySource
    created_at: datetime | None = None
    updated_at: datetime | None = None
    metadata: dict[str, Any] = Field(default_factory=dict)

    model_config = {"extra": "forbid"}
