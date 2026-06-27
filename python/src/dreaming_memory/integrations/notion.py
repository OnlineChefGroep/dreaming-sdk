"""Notion API client — lightweight read/write for agent memory."""

from __future__ import annotations

import os
from typing import Any

import httpx

from dreaming_memory.session import SessionContext
from dreaming_memory.store.postgres import AgentMemoryStore
from dreaming_memory.types import MemoryRecord, MemorySource, MemoryType

NOTION_API = "https://api.notion.com/v1"
NOTION_VERSION = "2022-06-28"


class NotionClient:
    """Minimal Notion REST client for pages and blocks."""

    def __init__(self, token: str | None = None) -> None:
        self.token = token or os.environ.get("NOTION_API_KEY") or os.environ.get("NOTION_TOKEN", "")
        if not self.token:
            raise ValueError("NOTION_API_KEY or NOTION_TOKEN required")

    def _headers(self) -> dict[str, str]:
        return {
            "Authorization": f"Bearer {self.token}",
            "Notion-Version": NOTION_VERSION,
            "Content-Type": "application/json",
        }

    def get_page(self, page_id: str) -> dict[str, Any]:
        resp = httpx.get(f"{NOTION_API}/pages/{page_id}", headers=self._headers(), timeout=30.0)
        resp.raise_for_status()
        return resp.json()

    def get_page_blocks(self, page_id: str) -> list[dict[str, Any]]:
        blocks: list[dict[str, Any]] = []
        cursor: str | None = None
        while True:
            params: dict[str, str] = {}
            if cursor:
                params["start_cursor"] = cursor
            resp = httpx.get(
                f"{NOTION_API}/blocks/{page_id}/children",
                headers=self._headers(),
                params=params,
                timeout=30.0,
            )
            resp.raise_for_status()
            data = resp.json()
            blocks.extend(data.get("results", []))
            if not data.get("has_more"):
                break
            cursor = data.get("next_cursor")
        return blocks

    def append_paragraph(self, page_id: str, text: str) -> dict[str, Any]:
        payload = {
            "children": [
                {
                    "object": "block",
                    "type": "paragraph",
                    "paragraph": {
                        "rich_text": [{"type": "text", "text": {"content": text[:2000]}}],
                    },
                }
            ]
        }
        resp = httpx.patch(
            f"{NOTION_API}/blocks/{page_id}/children",
            headers=self._headers(),
            json=payload,
            timeout=30.0,
        )
        resp.raise_for_status()
        return resp.json()

    @staticmethod
    def extract_title(page: dict[str, Any]) -> str:
        props = page.get("properties", {})
        for prop in props.values():
            if prop.get("type") != "title":
                continue
            parts = prop.get("title", [])
            return "".join(p.get("plain_text", "") for p in parts)
        return page.get("id", "untitled")

    @staticmethod
    def blocks_to_text(blocks: list[dict[str, Any]]) -> str:
        lines: list[str] = []
        for block in blocks:
            btype = block.get("type")
            data = block.get(btype, {})
            rich = data.get("rich_text", [])
            text = "".join(t.get("plain_text", "") for t in rich)
            if text:
                lines.append(text)
        return "\n".join(lines)


class NotionMemoryBridge:
    """Sync Notion pages ↔ agent_memory."""

    def __init__(self, store: AgentMemoryStore, client: NotionClient | None = None) -> None:
        self.store = store
        self.client = client or NotionClient()

    def ingest_page(self, page_id: str, session: SessionContext) -> MemoryRecord:
        page = self.client.get_page(page_id)
        blocks = self.client.get_page_blocks(page_id)
        title = self.client.extract_title(page)
        body = self.client.blocks_to_text(blocks)
        return self.store.write(
            MemoryRecord(
                agent_id=session.agent_id,
                session_id=session.session_id,
                session_type=session.session_type,
                memory_type=MemoryType.PAGE_SNAPSHOT,
                source=MemorySource.NOTION,
                content={"page_id": page_id, "title": title, "body": body[:8000]},
                metadata={
                    "notion_url": page.get("url"),
                    "last_edited": page.get("last_edited_time"),
                },
            )
        )

    def append_from_memory(self, session: SessionContext, page_id: str, text: str) -> MemoryRecord:
        result = self.client.append_paragraph(page_id, text)
        return self.store.write(
            MemoryRecord(
                agent_id=session.agent_id,
                session_id=session.session_id,
                session_type=session.session_type,
                memory_type=MemoryType.OBSERVATION,
                source=MemorySource.NOTION,
                content={"page_id": page_id, "appended_text": text},
                metadata={"notion_append_result": result.get("object")},
            )
        )
