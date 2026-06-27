"""Postgres-backed agent memory store."""

from __future__ import annotations

import json
from typing import Any
from uuid import UUID

from psycopg.rows import dict_row
from psycopg_pool import ConnectionPool

from dreaming_memory.config import FleetConfig
from dreaming_memory.types import MemoryRecord, MemorySource, MemoryType, SessionType


class AgentMemoryStore:
    """CRUD for agent_memory table — Postgres SSOT."""

    def __init__(self, dsn: str | None = None, *, min_size: int = 2, max_size: int = 20) -> None:
        self.dsn = dsn or FleetConfig.load().database_url
        if not self.dsn:
            raise ValueError(
                "No database DSN configured. Set AGENT_MEMORY_DATABASE_URL or DATABASE_URL "
                "in your environment or .env file."
            )
        self._pool = ConnectionPool(
            self.dsn,
            min_size=min_size,
            max_size=max_size,
            max_waiting=100,
            kwargs={"row_factory": dict_row},
        )

    def close(self) -> None:
        self._pool.close()

    def __enter__(self) -> AgentMemoryStore:
        return self

    def __exit__(self, *exc: Any) -> None:
        self.close()

    def ensure_schema(self, schema_path: str | None = None) -> None:
        """Apply schema migrations in order. Idempotent."""
        from pathlib import Path

        with self._pool.connection() as conn:
            # Create schema_version table if it doesn't exist
            conn.execute("""
                CREATE TABLE IF NOT EXISTS schema_version (
                    version     INTEGER PRIMARY KEY,
                    applied_at  TIMESTAMPTZ NOT NULL DEFAULT now(),
                    description TEXT
                )
            """)
            conn.commit()

            # Get applied versions
            rows = conn.execute("SELECT version FROM schema_version ORDER BY version").fetchall()
            applied = {r["version"] for r in rows}

            if schema_path:
                # Legacy single-file mode
                with open(schema_path, encoding="utf-8") as f:
                    sql = f.read()
                conn.execute(sql)
                conn.commit()
                return

            # Find migration files
            migrations_dir = Path(__file__).with_name("migrations")
            if not migrations_dir.exists():
                # Fallback to legacy schema.sql
                local = Path(__file__).with_name("schema.sql")
                if local.exists():
                    sql = local.read_text(encoding="utf-8")
                    conn.execute(sql)
                    conn.commit()
                return

            # Apply pending migrations
            for migration_file in sorted(migrations_dir.glob("schema_v*.sql")):
                version_str = migration_file.stem.replace("schema_v", "")
                try:
                    version = int(version_str)
                except ValueError:
                    continue

                if version in applied:
                    continue

                sql = migration_file.read_text(encoding="utf-8")
                conn.execute(sql)
                conn.execute(
                    "INSERT INTO schema_version (version, description) VALUES (%s, %s)",
                    (version, f"Applied from {migration_file.name}"),
                )
                conn.commit()

    def write(self, record: MemoryRecord) -> MemoryRecord:
        with self._pool.connection() as conn:
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
        with self._pool.connection() as conn:
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
        with self._pool.connection() as conn:
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

    def metrics(self, days: int = 14) -> dict[str, Any]:
        """Aggregate counts for the metrics dashboard (one connection, multiple queries)."""
        with self._pool.connection() as conn:
            total = conn.execute("SELECT count(*) AS n FROM agent_memory").fetchone()["n"]

            def group(col: str) -> list[dict[str, Any]]:
                rows = conn.execute(
                    f"SELECT {col} AS key, count(*) AS n FROM agent_memory "
                    f"GROUP BY {col} ORDER BY n DESC"
                ).fetchall()
                return [{"key": r["key"], "count": r["n"]} for r in rows]

            by_source = group("source")
            by_type = group("memory_type")
            by_session_type = group("session_type")
            by_agent = conn.execute(
                "SELECT agent_id AS key, count(*) AS n FROM agent_memory "
                "GROUP BY agent_id ORDER BY n DESC LIMIT 10"
            ).fetchall()
            per_day = conn.execute(
                """
                SELECT to_char(date_trunc('day', created_at), 'YYYY-MM-DD') AS day,
                       count(*) AS n
                FROM agent_memory
                WHERE created_at >= now() - make_interval(days => %s)
                GROUP BY 1 ORDER BY 1
                """,
                (days,),
            ).fetchall()
            recent = conn.execute(
                """
                SELECT id, agent_id, session_id, session_type, memory_type, source,
                       created_at, content
                FROM agent_memory ORDER BY created_at DESC LIMIT 15
                """
            ).fetchall()
            triage_total = conn.execute(
                "SELECT count(*) AS n FROM agent_memory "
                "WHERE memory_type = 'decision' AND metadata ? 'triage'"
            ).fetchone()["n"]
            last_activity = conn.execute(
                "SELECT max(created_at) AS ts FROM agent_memory"
            ).fetchone()["ts"]

        def _preview(c: Any) -> str:
            if isinstance(c, dict):
                for k in ("identifier", "title", "note", "event", "body", "host"):
                    if k in c:
                        return str(c[k])[:80]
            return str(c)[:80]

        return {
            "total": total,
            "last_activity": last_activity.isoformat() if last_activity else None,
            "by_source": by_source,
            "by_memory_type": by_type,
            "by_session_type": by_session_type,
            "by_agent": [{"key": r["key"], "count": r["n"]} for r in by_agent],
            "per_day": [{"day": r["day"], "count": r["n"]} for r in per_day],
            "triage_decisions": triage_total,
            "recent": [
                {
                    "id": str(r["id"]),
                    "agent_id": r["agent_id"],
                    "session_id": r["session_id"],
                    "session_type": r["session_type"],
                    "memory_type": r["memory_type"],
                    "source": r["source"],
                    "created_at": r["created_at"].isoformat(),
                    "preview": _preview(r["content"]),
                }
                for r in recent
            ],
        }

    def update_content(self, memory_id: UUID, content: dict[str, Any]) -> MemoryRecord | None:
        with self._pool.connection() as conn:
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
