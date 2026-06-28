"""Postgres-backed agent memory store.

Sprint 1 governance methods (CHEF-1004, CHEF-1005, CHEF-1006):
- write_evidence — persist evidence supporting a memory claim
- write_verifier_result — attach verification result to a memory
- write_curator_decision — create initial curator decision
- get_active_curator_decision — retrieve active decision for a memory
- update_curator_decision — update decision (state transition)
- find_active_by_dedupe_key — idempotent write lookup
"""

from __future__ import annotations

import json
from typing import Any
from urllib.parse import parse_qs, urlparse, urlunparse
from uuid import UUID

from psycopg.rows import dict_row
from psycopg_pool import ConnectionPool

from dreaming_memory.config import FleetConfig
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


def _normalize_dsn(dsn: str) -> str:
    """Ensure DSN has sslmode=require for encrypted connections."""
    parsed = urlparse(dsn)
    query = parse_qs(parsed.query)
    if "sslmode" not in query:
        query["sslmode"] = ["require"]
    new_query = "&".join(f"{k}={v}" for k, vals in query.items() for v in vals)
    normalized = urlunparse(
        (
            parsed.scheme,
            parsed.netloc,
            parsed.path,
            parsed.params,
            new_query,
            parsed.fragment,
        ),
    )
    return normalized


class AgentMemoryStore:
    """CRUD for agent_memory table — Postgres SSOT."""

    def __init__(self, dsn: str | None = None, *, min_size: int = 2, max_size: int = 20) -> None:
        raw_dsn = dsn or FleetConfig.load().database_url
        if not raw_dsn:
            raise ValueError(
                "No database DSN configured. Set AGENT_MEMORY_DATABASE_URL or DATABASE_URL "
                "in your environment or .env file."
            )
        self.dsn = _normalize_dsn(raw_dsn)
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

    # ------------------------------------------------------------------
    # CHEF-1006: Idempotent write lookup
    # ------------------------------------------------------------------

    def find_active_by_dedupe_key(self, dedupe_key: str) -> MemoryRecord | None:
        """Find an active (non-rolled-back) memory record by dedupe_key."""
        with self._pool.connection() as conn:
            row = conn.execute(
                """
                SELECT am.* FROM agent_memory am
                JOIN curator_decisions cd ON cd.memory_id = am.id
                WHERE am.metadata->>'dedupe_key' = %s
                  AND cd.state NOT IN ('rolled_back')
                ORDER BY am.created_at DESC
                LIMIT 1
                """,
                (dedupe_key,),
            ).fetchone()
        return self._row_to_record(row) if row else None

    # ------------------------------------------------------------------
    # CHEF-1004: Evidence
    # ------------------------------------------------------------------

    @staticmethod
    def _parse_json_field(value: Any) -> dict[str, Any]:
        if isinstance(value, str):
            return json.loads(value)
        return value or {}

    def write_evidence(self, evidence: Evidence) -> Evidence:
        with self._pool.connection() as conn:
            row = conn.execute(
                """
                INSERT INTO evidence (memory_id, evidence_type, source_url, source_id,
                                     excerpt, confidence, captured_at, metadata)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s::jsonb)
                RETURNING *
                """,
                (
                    str(evidence.memory_id),
                    evidence.evidence_type.value,
                    evidence.source_url,
                    evidence.source_id,
                    evidence.excerpt,
                    evidence.confidence,
                    evidence.captured_at,
                    json.dumps(evidence.metadata),
                ),
            ).fetchone()
            conn.commit()
        return Evidence(
            id=row["id"],
            memory_id=row["memory_id"],
            evidence_type=EvidenceType(row["evidence_type"]),
            source_url=row["source_url"],
            source_id=row["source_id"],
            excerpt=row["excerpt"],
            confidence=row["confidence"],
            captured_at=row["captured_at"],
            metadata=self._parse_json_field(row["metadata"]),
        )

    def get_evidence_for_memory(self, memory_id: UUID) -> list[Evidence]:
        with self._pool.connection() as conn:
            rows = conn.execute(
                "SELECT * FROM evidence WHERE memory_id = %s ORDER BY created_at",
                (str(memory_id),),
            ).fetchall()
        return [
            Evidence(
                id=r["id"],
                memory_id=r["memory_id"],
                evidence_type=EvidenceType(r["evidence_type"]),
                source_url=r["source_url"],
                source_id=r["source_id"],
                excerpt=r["excerpt"],
                confidence=r["confidence"],
                captured_at=r["captured_at"],
                metadata=self._parse_json_field(r["metadata"]),
            )
            for r in rows
        ]

    # ------------------------------------------------------------------
    # CHEF-1004: Verifier results
    # ------------------------------------------------------------------

    def write_verifier_result(self, result: VerifierResult) -> VerifierResult:
        with self._pool.connection() as conn:
            row = conn.execute(
                """
                INSERT INTO verifier_results (memory_id, status, score, evidence_refs,
                                              rationale, checked_at, checked_by, metadata)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s::jsonb)
                RETURNING *
                """,
                (
                    str(result.memory_id),
                    result.status.value,
                    result.score,
                    [str(ref) for ref in result.evidence_refs],
                    result.rationale,
                    result.checked_at,
                    result.checked_by,
                    json.dumps(result.metadata),
                ),
            ).fetchone()
            conn.commit()
        return VerifierResult(
            id=row["id"],
            memory_id=row["memory_id"],
            status=VerifierStatus(row["status"]),
            score=row["score"],
            evidence_refs=[UUID(ref) for ref in (row["evidence_refs"] or [])],
            rationale=row["rationale"],
            checked_at=row["checked_at"],
            checked_by=row["checked_by"],
            metadata=self._parse_json_field(row["metadata"]),
        )

    def get_verifier_results_for_memory(self, memory_id: UUID) -> list[VerifierResult]:
        with self._pool.connection() as conn:
            rows = conn.execute(
                "SELECT * FROM verifier_results WHERE memory_id = %s ORDER BY checked_at",
                (str(memory_id),),
            ).fetchall()
        return [
            VerifierResult(
                id=r["id"],
                memory_id=r["memory_id"],
                status=VerifierStatus(r["status"]),
                score=r["score"],
                evidence_refs=[UUID(ref) for ref in (r["evidence_refs"] or [])],
                rationale=r["rationale"],
                checked_at=r["checked_at"],
                checked_by=r["checked_by"],
                metadata=self._parse_json_field(r["metadata"]),
            )
            for r in rows
        ]

    # ------------------------------------------------------------------
    # CHEF-1005: Curator decisions
    # ------------------------------------------------------------------

    def write_curator_decision(self, decision: CuratorDecision) -> CuratorDecision:
        with self._pool.connection() as conn:
            row = conn.execute(
                """
                INSERT INTO curator_decisions (memory_id, state, decided_at, decided_by,
                                              rationale, previous_state, transitions, metadata)
                VALUES (%s, %s, %s, %s, %s, %s, %s::jsonb, %s::jsonb)
                RETURNING *
                """,
                (
                    str(decision.memory_id),
                    decision.state.value,
                    decision.decided_at,
                    decision.decided_by,
                    decision.rationale,
                    decision.previous_state.value if decision.previous_state else None,
                    json.dumps(decision.transitions),
                    json.dumps(decision.metadata),
                ),
            ).fetchone()
            conn.commit()
        return self._row_to_curator_decision(row)

    def get_active_curator_decision(self, memory_id: UUID) -> CuratorDecision | None:
        with self._pool.connection() as conn:
            row = conn.execute(
                """
                SELECT * FROM curator_decisions
                WHERE memory_id = %s
                  AND state NOT IN ('rejected', 'edited', 'rolled_back')
                ORDER BY decided_at DESC
                LIMIT 1
                """,
                (str(memory_id),),
            ).fetchone()
        return self._row_to_curator_decision(row) if row else None

    def update_curator_decision(
        self, memory_id: UUID, decision: CuratorDecision
    ) -> CuratorDecision:
        with self._pool.connection() as conn:
            row = conn.execute(
                """
                UPDATE curator_decisions SET
                    state = %s,
                    decided_at = %s,
                    decided_by = %s,
                    rationale = %s,
                    previous_state = %s,
                    transitions = %s::jsonb,
                    metadata = %s::jsonb
                WHERE memory_id = %s
                  AND state NOT IN ('rejected', 'edited', 'rolled_back')
                RETURNING *
                """,
                (
                    decision.state.value,
                    decision.decided_at,
                    decision.decided_by,
                    decision.rationale,
                    decision.previous_state.value if decision.previous_state else None,
                    json.dumps(decision.transitions),
                    json.dumps(decision.metadata),
                    str(memory_id),
                ),
            ).fetchone()
            conn.commit()
        return self._row_to_curator_decision(row)

    def get_curator_decisions_by_state(
        self, state: CuratorState, limit: int = 50
    ) -> list[CuratorDecision]:
        with self._pool.connection() as conn:
            rows = conn.execute(
                """
                SELECT * FROM curator_decisions
                WHERE state = %s
                ORDER BY decided_at DESC
                LIMIT %s
                """,
                (state.value, limit),
            ).fetchall()
        return [self._row_to_curator_decision(r) for r in rows]

    def curator_metrics(self, days: int = 14) -> dict[str, Any]:
        """Aggregate curator lifecycle metrics for the dashboard."""
        with self._pool.connection() as conn:
            by_state = conn.execute(
                "SELECT state, count(*) AS n FROM curator_decisions GROUP BY state ORDER BY n DESC"
            ).fetchall()
            total = sum(r["n"] for r in by_state)
            recent = conn.execute(
                """
                SELECT to_char(date_trunc('day', decided_at), 'YYYY-MM-DD') AS day,
                       state, count(*) AS n
                FROM curator_decisions
                WHERE decided_at >= now() - make_interval(days => %s)
                GROUP BY 1, 2 ORDER BY 1
                """,
                (days,),
            ).fetchall()
        return {
            "total": total,
            "by_state": [{"state": r["state"], "count": r["n"]} for r in by_state],
            "per_day": [{"day": r["day"], "state": r["state"], "count": r["n"]} for r in recent],
        }

    @staticmethod
    def _row_to_curator_decision(row: dict[str, Any]) -> CuratorDecision:
        transitions = row["transitions"]
        if isinstance(transitions, str):
            transitions = json.loads(transitions)
        metadata = row["metadata"]
        if isinstance(metadata, str):
            metadata = json.loads(metadata)
        prev_state = row.get("previous_state")
        return CuratorDecision(
            id=row["id"],
            memory_id=row["memory_id"],
            state=CuratorState(row["state"]),
            decided_at=row["decided_at"],
            decided_by=row["decided_by"],
            rationale=row["rationale"],
            previous_state=CuratorState(prev_state) if prev_state else None,
            transitions=transitions,
            metadata=metadata,
        )

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
