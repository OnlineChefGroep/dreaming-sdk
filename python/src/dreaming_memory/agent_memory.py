"""High-level facade for agents — Postgres SSOT + optional semantic + integrations."""

from __future__ import annotations

from typing import Any
from uuid import UUID

from dreaming_memory.config import FleetConfig
from dreaming_memory.integrations.cloudflare import CloudflareR2
from dreaming_memory.integrations.linear import LinearMemoryBridge
from dreaming_memory.integrations.notion import NotionMemoryBridge
from dreaming_memory.observability import sentry
from dreaming_memory.semantic.lancedb import SemanticMemoryStore
from dreaming_memory.session import SessionContext
from dreaming_memory.store.postgres import AgentMemoryStore
from dreaming_memory.types import MemoryRecord, MemorySource, MemoryType, SessionType


class AgentMemory:
    """
    Main entry point for agent memory within dreaming-sdk.

    Usage:
        memory = AgentMemory()
        memory.ensure_schema()
        ctx = SessionContext.for_dream_eval("2026-06-15T09-00-00Z")
        memory.remember(ctx, MemoryType.OBSERVATION, {"note": "faithfulness 0.63"}, source=MemorySource.SDK)
    """

    def __init__(
        self,
        store: AgentMemoryStore | None = None,
        semantic: SemanticMemoryStore | None = None,
        linear: LinearMemoryBridge | None = None,
        notion: NotionMemoryBridge | None = None,
        config: FleetConfig | None = None,
        enable_sentry: bool = True,
    ) -> None:
        self.config = config or FleetConfig.load()
        self.store = store or AgentMemoryStore(self.config.database_url)
        self.semantic = semantic
        self._linear = linear
        self._notion = notion
        self._cloudflare: CloudflareR2 | None = None
        if enable_sentry:
            sentry.init_sentry(self.config)

    def close(self) -> None:
        self.store.close()

    def __enter__(self) -> AgentMemory:
        return self

    def __exit__(self, *exc: Any) -> None:
        self.close()

    @property
    def cloudflare(self) -> CloudflareR2:
        if self._cloudflare is None:
            self._cloudflare = CloudflareR2(self.config)
        return self._cloudflare

    def ensure_schema(self) -> None:
        self.store.ensure_schema()

    @property
    def linear(self) -> LinearMemoryBridge:
        if self._linear is None:
            self._linear = LinearMemoryBridge(self.store)
        return self._linear

    @property
    def notion(self) -> NotionMemoryBridge:
        if self._notion is None:
            self._notion = NotionMemoryBridge(self.store)
        return self._notion

    def remember(
        self,
        session: SessionContext,
        memory_type: MemoryType,
        content: dict[str, Any],
        *,
        source: MemorySource = MemorySource.SDK,
        metadata: dict[str, Any] | None = None,
    ) -> MemoryRecord:
        record = MemoryRecord(
            agent_id=session.agent_id,
            session_id=session.session_id,
            session_type=session.session_type,
            memory_type=memory_type,
            content=content,
            source=source,
            metadata={**(session.metadata or {}), **(metadata or {})},
        )
        sentry.breadcrumb(
            f"remember {memory_type.value}",
            data={"session_type": session.session_type.value, "source": source.value},
        )
        return self.store.write(record)

    def recall(
        self,
        *,
        agent_id: str | None = None,
        session_id: str | None = None,
        session_type: SessionType | None = None,
        memory_type: MemoryType | None = None,
        source: MemorySource | None = None,
        limit: int = 50,
    ) -> list[MemoryRecord]:
        return self.store.query(
            agent_id=agent_id,
            session_id=session_id,
            session_type=session_type,
            memory_type=memory_type,
            source=source,
            limit=limit,
        )

    def recall_session(self, session: SessionContext, limit: int = 50) -> list[MemoryRecord]:
        return self.recall(
            agent_id=session.agent_id,
            session_id=session.session_id,
            session_type=session.session_type,
            limit=limit,
        )

    def index_semantic(
        self,
        record: MemoryRecord,
        text: str,
        vector: list[float],
    ) -> MemoryRecord | None:
        if self.semantic is None:
            raise RuntimeError("semantic store not configured — pass SemanticMemoryStore() to AgentMemory")
        if not self.semantic.enabled:
            return None
        if record.id is None:
            raise ValueError("record must have an id before indexing into semantic store")
        self.semantic.index_memory(
            record.id, text, vector, metadata={"source": record.source.value}
        )
        ref = MemoryRecord(
            agent_id=record.agent_id,
            session_id=record.session_id,
            session_type=record.session_type,
            memory_type=MemoryType.EMBEDDING_REF,
            source=MemorySource.SDK,
            content={"text_preview": text[:500], "parent_id": str(record.id)},
            metadata={"lance_table": self.semantic.table_name},
        )
        return self.store.write(ref)

    def search_semantic(self, vector: list[float], limit: int = 10) -> list[dict[str, Any]]:
        if self.semantic is None or not self.semantic.enabled:
            return []
        return self.semantic.search(vector, limit=limit)

    def get(self, memory_id: UUID) -> MemoryRecord | None:
        return self.store.get(memory_id)
