"""Session context adapter — normalizes SDK session forms for the memory layer."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from dreaming_memory.types import SessionType

# Maps common aliases from dreaming plugin / multi-agent docs to canonical SessionType.
_SESSION_ALIASES: dict[str, SessionType] = {
    "cursor": SessionType.CURSOR,
    "claude": SessionType.CLAUDE,
    "codex": SessionType.CODEX,
    "opencode": SessionType.OPENCODE,
    "grok": SessionType.GROK,
    "factory": SessionType.GROK,
    "sdk_local": SessionType.SDK_LOCAL,
    "sdk_cloud": SessionType.SDK_CLOUD,
    "dream_eval": SessionType.DREAM_EVAL,
    "dream-eval": SessionType.DREAM_EVAL,
    "dream_live": SessionType.DREAM_LIVE,
    "dream": SessionType.DREAM_LIVE,
    "live": SessionType.DREAM_LIVE,
    "eval": SessionType.DREAM_EVAL,
    "generic": SessionType.GENERIC,
}


_SKIP_KEYS = frozenset({
    "session_id", "transcript_hash", "hash", "run_id",
    "session_type", "platform", "source", "agent_id", "agent",
})


def resolve_session_type(raw: str | SessionType | None) -> SessionType:
    if raw is None:
        return SessionType.GENERIC
    if isinstance(raw, SessionType):
        return raw
    key = raw.strip().lower().replace(" ", "_")
    return _SESSION_ALIASES.get(key, SessionType.GENERIC)


@dataclass
class SessionContext:
    """Normalized session handle passed into AgentMemory write/read calls."""

    session_id: str
    session_type: SessionType = SessionType.GENERIC
    agent_id: str = "default"
    metadata: dict[str, Any] = field(default_factory=dict)

    @classmethod
    def from_sdk_payload(cls, payload: dict[str, Any]) -> SessionContext:
        """Build from dream-index session entry or agent run payload."""
        session_id = (
            payload.get("session_id")
            or payload.get("transcript_hash")
            or payload.get("hash")
            or payload.get("run_id")
            or "unknown"
        )
        raw_type = payload.get("session_type") or payload.get("platform") or payload.get("source")
        agent_id = payload.get("agent_id") or payload.get("agent") or "default"
        meta = {k: v for k, v in payload.items() if k not in _SKIP_KEYS}
        return cls(
            session_id=str(session_id),
            session_type=resolve_session_type(raw_type),
            agent_id=str(agent_id),
            metadata=meta,
        )

    @classmethod
    def for_dream_eval(cls, run_id: str, agent_id: str = "dream-evaluator") -> SessionContext:
        return cls(session_id=run_id, session_type=SessionType.DREAM_EVAL, agent_id=agent_id)

    @classmethod
    def for_dream_live(
        cls, transcript_hash: str, agent_id: str = "dream-curator"
    ) -> SessionContext:
        return cls(
            session_id=transcript_hash,
            session_type=SessionType.DREAM_LIVE,
            agent_id=agent_id,
        )
