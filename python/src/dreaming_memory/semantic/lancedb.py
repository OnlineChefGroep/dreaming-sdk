"""Optional LanceDB semantic layer — links to Postgres via embedding_ref metadata."""

from __future__ import annotations

import os
from typing import Any
from uuid import UUID


class SemanticMemoryStore:
    """Lightweight vector store. Disabled when lancedb is not installed."""

    def __init__(
        self,
        uri: str | None = None,
        table_name: str = "agent_memory_embeddings",
    ) -> None:
        self.uri = uri or os.environ.get("LANCE_DB_URI", "./data/lancedb")
        self.table_name = table_name
        self._db = None
        self._table = None

    @property
    def enabled(self) -> bool:
        try:
            import lancedb  # noqa: F401
        except ImportError:
            return False
        return True

    def _ensure_table(self) -> Any:
        if not self.enabled:
            raise RuntimeError(
                "lancedb not installed — pip install cursor-dreaming-memory[semantic]"
            )
        import lancedb

        if self._db is None:
            self._db = lancedb.connect(self.uri)
        if self._table is None:
            try:
                self._table = self._db.open_table(self.table_name)
            except Exception:
                self._table = self._db.create_table(
                    self.table_name,
                    data=[{
                        "memory_id": "placeholder",
                        "text": "placeholder",
                        "vector": [0.0] * 384,
                    }],
                    exist_ok=True,
                )
                self._table.delete("memory_id = 'placeholder'")
        return self._table

    def index_memory(
        self,
        memory_id: UUID,
        text: str,
        vector: list[float],
        metadata: dict[str, Any] | None = None,
    ) -> None:
        table = self._ensure_table()
        row = {
            "memory_id": str(memory_id),
            "text": text,
            "vector": vector,
            "metadata": metadata or {},
        }
        table.add([row])

    def search(self, vector: list[float], limit: int = 10) -> list[dict[str, Any]]:
        table = self._ensure_table()
        return table.search(vector).limit(limit).to_list()
