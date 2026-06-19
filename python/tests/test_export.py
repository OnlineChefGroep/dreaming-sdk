"""Unit tests for the CLI export Markdown renderer (no DB required)."""

from __future__ import annotations

from datetime import datetime

from cursor_dreaming_memory.cli import render_export_markdown
from cursor_dreaming_memory.types import MemoryRecord, MemorySource, MemoryType, SessionType


def _record() -> MemoryRecord:
    return MemoryRecord(
        agent_id="agent-1",
        session_id="sess-1",
        session_type=SessionType.CURSOR,
        memory_type=MemoryType.FACT,
        content={"key": "value", "n": 1},
        source=MemorySource.USER,
        created_at=datetime(2026, 6, 15, 9, 0, 0),
    )


def test_render_export_markdown_with_records() -> None:
    md = render_export_markdown("sess-1", [_record()])
    assert md.startswith("# Memory export — sess-1")
    assert "## fact (2026-06-15 09:00:00)" in md
    assert "**Source:** user" in md
    assert "```json" in md
    assert '"key": "value"' in md


def test_render_export_markdown_empty() -> None:
    md = render_export_markdown("sess-empty", [])
    assert "# Memory export — sess-empty" in md
    assert "_No memory records found._" in md
