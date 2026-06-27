#!/usr/bin/env python3
"""
Example agent flow: dream-eval session → memory → Linear comment.

Run (requires Postgres + LINEAR_API_KEY):
    cd python && uv run python examples/linear_memory_flow.py --issue CHEF-308
"""

from __future__ import annotations

import argparse
import os

from dreaming_memory import AgentMemory, SessionContext
from dreaming_memory.types import MemorySource, MemoryType


def main() -> None:
    parser = argparse.ArgumentParser(description="Dream-eval memory + Linear flow")
    parser.add_argument("--issue", default="CHEF-308", help="Linear issue to ingest")
    parser.add_argument("--run-id", default="2026-06-15T09-00-00Z", help="Dream eval run_id")
    parser.add_argument("--comment", action="store_true", help="Post summary comment back to Linear")
    args = parser.parse_args()

    memory = AgentMemory()
    memory.ensure_schema()

    # 1. Dream-eval session context (compatible with sdk/run-dream-cloud.ts run_id)
    ctx = SessionContext.for_dream_eval(args.run_id, agent_id="dream-evaluator")

    # 2. Record eval observation in Postgres SSOT
    obs = memory.remember(
        ctx,
        MemoryType.OBSERVATION,
        {
            "event": "eval_complete",
            "faithfulness": 0.63,
            "note": "Baseline from golden corpus — memory layer active",
        },
        source=MemorySource.SDK,
        metadata={"che_f": args.issue},
    )
    print(f"Wrote observation {obs.id}")

    # 3. Ingest linked Linear issue (if API key present)
    if os.environ.get("LINEAR_API_KEY"):
        issue_record = memory.linear.ingest_issue(args.issue, ctx)
        print(f"Ingested {issue_record.content.get('identifier')}: {issue_record.content.get('title')}")

        if args.comment:
            summary = (
                f"[dream-memory] Eval run `{args.run_id}` recorded. "
                f"Faithfulness baseline 0.63. Memory id: `{obs.id}`"
            )
            comment_record = memory.linear.comment_from_memory(ctx, args.issue, summary)
            print(f"Posted comment, memory id {comment_record.id}")
    else:
        print("LINEAR_API_KEY not set — skipping Linear ingest")

    # 4. Recall session memories (dashboard-ready JSON)
    records = memory.recall_session(ctx)
    print(f"Session has {len(records)} memory records")


if __name__ == "__main__":
    main()
