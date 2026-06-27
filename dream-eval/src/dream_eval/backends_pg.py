"""Postgres backend for dream-eval — stores eval results alongside agent memory."""

from __future__ import annotations

import json
from typing import Any

from dream_eval.types import EvalReport, EvalResult, Labels


class PostgresEvalBackend:
    """Stores eval results in the agent_memory table.

    Uses the existing agent_memory schema — eval results are stored as
    memory_type='decision' with metadata['dream_eval']=True.

    Requires psycopg[binary] >= 3.2 and a running Postgres instance.
    """

    def __init__(self, dsn: str | None = None) -> None:
        import os

        if dsn is None:
            dsn = os.environ.get("AGENT_MEMORY_DATABASE_URL") or os.environ.get(
                "DATABASE_URL"
            )
        if not dsn:
            raise ValueError(
                "No database DSN configured. Set AGENT_MEMORY_DATABASE_URL or DATABASE_URL."
            )
        from psycopg.rows import dict_row
        from psycopg_pool import ConnectionPool

        self._pool = ConnectionPool(
            dsn, min_size=1, max_size=5, kwargs={"row_factory": dict_row}
        )

    def close(self) -> None:
        self._pool.close()

    def __enter__(self) -> PostgresEvalBackend:
        return self

    def __exit__(self, *exc: Any) -> None:
        self.close()

    def save_eval_result(self, result: EvalResult) -> None:
        """Persist eval result as a memory record."""
        with self._pool.connection() as conn:
            conn.execute(
                """
                INSERT INTO agent_memory (
                    agent_id, session_id, session_type, memory_type,
                    content, source, metadata
                ) VALUES (%s, %s, %s, %s, %s::jsonb, %s, %s::jsonb)
                """,
                (
                    "dream-eval",
                    result.run_id,
                    "dream_eval",
                    "decision",
                    json.dumps(result.to_metrics_dict()),
                    "sdk",
                    json.dumps({"dream_eval": True, "mode": result.mode.value}),
                ),
            )
            conn.commit()

    def load_eval_report(self, run_id: str) -> EvalReport | None:
        """Load eval report from agent_memory by session_id."""
        with self._pool.connection() as conn:
            row = conn.execute(
                """
                SELECT content FROM agent_memory
                WHERE session_id = %s AND metadata ? 'dream_eval'
                ORDER BY created_at DESC LIMIT 1
                """,
                (run_id,),
            ).fetchone()
        if not row:
            return None
        content = row["content"]
        if isinstance(content, str):
            content = json.loads(content)
        return EvalReport(
            items=[],
            sessions_evaluated=content.get("sessions_evaluated", 0),
            token_cost=content.get("token_cost", 0),
            latency=content.get("latency", 0),
        )

    def load_labels(self, corpus_path: str | None = None) -> Labels:
        """Load labels from a JSON file. Falls back to empty labels."""
        from pathlib import Path

        if corpus_path is None:
            return Labels()

        labels_file = Path(corpus_path) / "labels.json"
        if not labels_file.exists():
            return Labels()

        data = json.loads(labels_file.read_text(encoding="utf-8"))
        return Labels.model_validate(data)

    def list_runs(self, limit: int = 50) -> list[dict[str, Any]]:
        """List recent eval runs from agent_memory."""
        with self._pool.connection() as conn:
            rows = conn.execute(
                """
                SELECT session_id AS run_id, content, created_at
                FROM agent_memory
                WHERE metadata ? 'dream_eval'
                ORDER BY created_at DESC
                LIMIT %s
                """,
                (limit,),
            ).fetchall()

        runs: list[dict[str, Any]] = []
        for row in rows:
            content = row["content"]
            if isinstance(content, str):
                content = json.loads(content)
            runs.append({
                "run_id": row["run_id"],
                "faithfulness": content.get("faithfulness_score"),
                "secret_leak": content.get("secret_leak_test"),
                "date": row["created_at"].isoformat() if row["created_at"] else None,
            })
        return runs
