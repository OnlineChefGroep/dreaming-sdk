"""Postgres-backed agent memory store."""

from __future__ import annotations

import json
from collections.abc import Iterator
from contextlib import contextmanager
from typing import Any
from uuid import UUID

import psycopg
from psycopg.rows import dict_row

from cursor_dreaming_memory.config import FleetConfig
from cursor_dreaming_memory.types import MemoryRecord, MemorySource, MemoryType, SessionType

DEFAULT_DSN = "postgresql://postgres:postgres@localhost:5432/agent_memory"


class AgentMemoryStore:
    """CRUD for agent_memory table — Postgres SSOT."""

    def __init__(self, dsn: str | None = None) -> None:
        self.dsn = dsn or FleetConfig.load().database_url or DEFAULT_DSN

    @contextmanager
    def _conn(self) -> Iterator[psycopg.Connection]:
        with psycopg.connect(self.dsn, row_factory=dict_row) as conn:
            yield conn

    def ensure_schema(self, schema_path: str | None = None) -> None:
        if schema_path:
            sql = open(schema_path, encoding="utf-8").read()
        else:
            from pathlib import Path

            local = Path(__file__).with_name("schema.sql")
            if local.exists():
                sql = local.read_text(encoding="utf-8")
            else:
                from importlib.resources import files

                pkg = files("cursor_dreaming_memory.store")
                sql = pkg.joinpath("schema.sql").read_text(encoding="utf-8")
        with self._conn() as conn:
            conn.execute(sql)
            conn.commit()

    def write(self, record: MemoryRecord) -> MemoryRecord:
        with self._conn() as conn:
            row = conn.execute(
                """
                INSERT INTO agent_memory (
                    agent_id, session_id, session_type, memory_type,
                    content, source, metadata
                )
                VALUES (%s, %s, %s, %s, %s::jsonb, %s, %s::jsonb)
                RETURNING *
                """,
                (
                    record.agent_id,
                    record.session_id,
                    record.session_type.value,
                    record.memory_type.value,
                    json.dumps(record.content),
                    record.source.value,
                    json.dumps(record.metadata),
                ),
            ).fetchone()
            conn.commit()
        return self._row_to_record(row)

    def get(self, memory_id: UUID) -> MemoryRecord | None:
        with self._conn() as conn:
            row = conn.execute(
                "SELECT * FROM agent_memory WHERE id = %s",
                (memory_id,),
            ).fetchone()
        return self._row_to_record(row) if row else None

    def query(
        self,
        *,
        agent_id: str | None = None,
        session_id: str | None = None,
        session_type: SessionType | None = None,
        memory_type: MemoryType | None = None,
        source: MemorySource | None = None,
        limit: int = 50,
        offset: int = 0,
    ) -> list[MemoryRecord]:
        clauses: list[str] = []
        params: list[Any] = []
        if agent_id:
            clauses.append("agent_id = %s")
            params.append(agent_id)
        if session_id:
            clauses.append("session_id = %s")
            params.append(session_id)
        if session_type:
            clauses.append("session_type = %s")
            params.append(session_type.value)
        if memory_type:
            clauses.append("memory_type = %s")
            params.append(memory_type.value)
        if source:
            clauses.append("source = %s")
            params.append(source.value)
        where = f"WHERE {' AND '.join(clauses)}" if clauses else ""
        params.extend([limit, offset])
        with self._conn() as conn:
            rows = conn.execute(
                f"""
                SELECT * FROM agent_memory
                {where}
                ORDER BY created_at DESC
                LIMIT %s OFFSET %s
                """,
                params,
            ).fetchall()
        return [self._row_to_record(r) for r in rows]

    def update_content(self, memory_id: UUID, content: dict[str, Any]) -> MemoryRecord | None:
        with self._conn() as conn:
            row = conn.execute(
                """
                UPDATE agent_memory SET content = %s::jsonb
                WHERE id = %s RETURNING *
                """,
                (json.dumps(content), memory_id),
            ).fetchone()
            conn.commit()
        return self._row_to_record(row) if row else None

    @staticmethod
    def _row_to_record(row: dict[str, Any] | None) -> MemoryRecord:
        if row is None:
            raise ValueError("empty row")
        content = row["content"]
        if not isinstance(content, dict):
            content = json.loads(content)
        metadata = row["metadata"]
        if not isinstance(metadata, dict):
            metadata = json.loads(metadata)
        return MemoryRecord(
            id=row["id"],
            agent_id=row["agent_id"],
            session_id=row["session_id"],
            session_type=SessionType(row["session_type"]),
            memory_type=MemoryType(row["memory_type"]),
            content=content,
            source=MemorySource(row["source"]),
            created_at=row["created_at"],
            updated_at=row["updated_at"],
            metadata=metadata,
        )
