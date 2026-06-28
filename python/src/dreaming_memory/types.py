"""Shared types for agent memory — aligned with dreaming-sdk session forms.

Sprint 1 additions:
- Evidence source model (CHEF-1004)
- Verifier result model (CHEF-1004)
- Curator decision state machine (CHEF-1005)
- External reference constraints (CHEF-1006)
"""

from __future__ import annotations

from datetime import datetime
from enum import StrEnum
from typing import Any
from uuid import UUID

from pydantic import BaseModel, Field


class SessionType(StrEnum):
    """Session forms supported by dreaming-sdk and multi-agent surfaces."""

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


# ---------------------------------------------------------------------------
# CHEF-1004: Evidence source and verifier result models
# ---------------------------------------------------------------------------


class EvidenceType(StrEnum):
    """Where evidence for a memory claim originates."""

    TRANSCRIPT = "transcript"
    LOG = "log"
    DOCUMENT = "document"
    API_RESPONSE = "api_response"
    DATABASE_RECORD = "database_record"
    USER_INPUT = "user_input"
    AGENT_OUTPUT = "agent_output"
    EXTERNAL = "external"


class Evidence(BaseModel):
    """A single piece of evidence supporting a memory claim.

    Attached to MemoryRecord.metadata["evidence"] as a list.
    """

    id: UUID | None = None
    memory_id: UUID | None = None
    evidence_type: EvidenceType
    source_url: str | None = None
    source_id: str | None = None
    excerpt: str = ""
    confidence: float = Field(default=1.0, ge=0.0, le=1.0)
    captured_at: datetime | None = None
    metadata: dict[str, Any] = Field(default_factory=dict)

    model_config = {"extra": "forbid"}


class VerifierStatus(StrEnum):
    """Outcome of a verification pass on a memory claim."""

    PASS = "pass"
    FAIL = "fail"
    PARTIAL = "partial"
    SKIP = "skip"
    PENDING = "pending"


class VerifierResult(BaseModel):
    """Machine-readable result from the verifier subagent.

    Stored in agent_memory.metadata["verifier"] when a memory is proposed
    through the governance pipeline.
    """

    id: UUID | None = None
    memory_id: UUID | None = None
    status: VerifierStatus
    score: float = Field(default=0.0, ge=0.0, le=1.0)
    evidence_refs: list[UUID] = Field(default_factory=list)
    rationale: str = ""
    checked_at: datetime | None = None
    checked_by: str = ""
    metadata: dict[str, Any] = Field(default_factory=dict)

    model_config = {"extra": "forbid"}


# ---------------------------------------------------------------------------
# CHEF-1005: Curator decision state machine
# ---------------------------------------------------------------------------


class CuratorState(StrEnum):
    """Lifecycle states for the curator decision on a memory."""

    PROPOSED = "proposed"
    REVIEWING = "reviewing"
    ACCEPTED = "accepted"
    REJECTED = "rejected"
    EDITED = "edited"
    DEFERRED = "deferred"
    ROLLED_BACK = "rolled_back"


class CuratorDecision(BaseModel):
    """Curator decision driving the memory governance lifecycle.

    State machine:
        proposed → reviewing → accepted | rejected | edited | deferred
        deferred → reviewing
        accepted → rolled_back

    Stored in agent_memory.metadata["curator"].
    """

    id: UUID | None = None
    memory_id: UUID | None = None
    state: CuratorState = CuratorState.PROPOSED
    decided_at: datetime | None = None
    decided_by: str = ""
    rationale: str = ""
    previous_state: CuratorState | None = None
    transitions: list[dict[str, Any]] = Field(default_factory=list)
    metadata: dict[str, Any] = Field(default_factory=dict)

    model_config = {"extra": "forbid"}


# Valid transitions for the curator state machine.
# Keys are current state, values are valid next states.
CURATOR_VALID_TRANSITIONS: dict[CuratorState, list[CuratorState]] = {
    CuratorState.PROPOSED: [CuratorState.REVIEWING],
    CuratorState.REVIEWING: [
        CuratorState.ACCEPTED,
        CuratorState.REJECTED,
        CuratorState.EDITED,
        CuratorState.DEFERRED,
    ],
    CuratorState.DEFERRED: [CuratorState.REVIEWING],
    CuratorState.ACCEPTED: [CuratorState.ROLLED_BACK],
    CuratorState.REJECTED: [],
    CuratorState.EDITED: [],
    CuratorState.ROLLED_BACK: [],
}
