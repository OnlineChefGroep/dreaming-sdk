#!/usr/bin/env python3
"""
Prefect flow: scheduled Linear → agent_memory ingest.

Usage:
    uv sync --extra prefect
    uv run python deploy/oci/prefect_flow.py

Set SYNC_ISSUES=CHEF-308,GROEP-155 to override default issue list.
"""

from __future__ import annotations

import os

from cursor_dreaming_memory import AgentMemory, SessionContext
from cursor_dreaming_memory.types import SessionType


def sync_linear_issues() -> int:
    issues = os.environ.get("SYNC_ISSUES", "CHEF-308").split(",")
    memory = AgentMemory()
    memory.ensure_schema()
    count = 0
    for issue_id in issues:
        issue_id = issue_id.strip()
        if not issue_id:
            continue
        ctx = SessionContext(
            session_id=f"prefect-sync-{issue_id}",
            session_type=SessionType.CURSOR,
            agent_id="prefect-linear-sync",
        )
        memory.linear.ingest_issue(issue_id, ctx)
        count += 1
    return count


def main() -> None:
    try:
        from prefect import flow

        @flow(name="agent-memory-linear-sync")
        def linear_sync_flow() -> int:
            return sync_linear_issues()

        linear_sync_flow()
    except ImportError:
        # Run without Prefect if extra not installed
        n = sync_linear_issues()
        print(f"Synced {n} issues")


if __name__ == "__main__":
    main()
