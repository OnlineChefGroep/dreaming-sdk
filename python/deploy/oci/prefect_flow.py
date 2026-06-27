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

from dreaming_memory import AgentMemory, SessionContext
from dreaming_memory.types import SessionType


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


def run_auto_triage() -> int:
    """Auto-triage untriaged Linear issues. Set TRIAGE_APPLY=1 to write back."""
    from dreaming_memory.triage import AutoTriage

    apply = os.environ.get("TRIAGE_APPLY", "0") == "1"
    state = os.environ.get("TRIAGE_STATE") or None
    results = AutoTriage().run(state=state, limit=100, apply=apply, comment=apply)
    return len(results)


def main() -> None:
    try:
        from prefect import flow, task

        @task
        def _sync() -> int:
            return sync_linear_issues()

        @task
        def _triage() -> int:
            return run_auto_triage()

        @flow(name="agent-memory-sync-triage")
        def memory_flow() -> None:
            print(f"Synced {_sync()} issues")
            print(f"Triaged {_triage()} issues")

        memory_flow()
    except ImportError:
        # Run without Prefect if extra not installed
        print(f"Synced {sync_linear_issues()} issues")
        print(f"Triaged {run_auto_triage()} issues")


if __name__ == "__main__":
    main()
