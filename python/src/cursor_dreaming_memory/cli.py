#!/usr/bin/env python3
"""CLI for agent memory — schema init, query, Linear/Notion ingest."""

from __future__ import annotations

import argparse
import json
import sys

from cursor_dreaming_memory import AgentMemory, FleetConfig, SessionContext
from cursor_dreaming_memory.types import MemorySource, MemoryType, SessionType


def _print_records(records: list) -> None:
    for r in records:
        print(json.dumps(r.model_dump(mode="json"), default=str))


def _doctor() -> None:
    """Print config presence + Postgres connectivity (no secret values)."""
    config = FleetConfig.load()
    status = config.status()
    print(json.dumps({"config": status, "redacted": config.redacted()}, indent=2))
    try:
        store = AgentMemory(config=config, enable_sentry=False).store
        with store._conn() as conn:
            conn.execute("SELECT 1")
        print('{"postgres": "ok"}')
    except Exception as exc:  # noqa: BLE001
        print(json.dumps({"postgres": "error", "detail": str(exc)}))


def main() -> None:
    parser = argparse.ArgumentParser(description="cursor-dreaming-sdk agent memory CLI")
    sub = parser.add_subparsers(dest="command", required=True)

    sub.add_parser("init", help="Apply Postgres schema")
    sub.add_parser("doctor", help="Show config presence + DB connectivity")

    p_remember = sub.add_parser("remember", help="Write a memory record")
    p_remember.add_argument("--agent", default="default")
    p_remember.add_argument("--session-id", required=True)
    p_remember.add_argument("--session-type", default="generic")
    p_remember.add_argument("--type", dest="memory_type", default="observation")
    p_remember.add_argument("--source", default="sdk")
    p_remember.add_argument("--content", required=True, help="JSON object")

    p_recall = sub.add_parser("recall", help="Query memory records")
    p_recall.add_argument("--agent")
    p_recall.add_argument("--session-id")
    p_recall.add_argument("--session-type")
    p_recall.add_argument("--type", dest="memory_type")
    p_recall.add_argument("--source")
    p_recall.add_argument("--limit", type=int, default=20)

    p_linear = sub.add_parser("linear-ingest", help="Ingest Linear issue into memory")
    p_linear.add_argument("issue_id")
    p_linear.add_argument("--session-id", default="linear-sync")
    p_linear.add_argument("--session-type", default="cursor")

    p_notion = sub.add_parser("notion-ingest", help="Ingest Notion page into memory")
    p_notion.add_argument("page_id")
    p_notion.add_argument("--session-id", default="notion-sync")
    p_notion.add_argument("--session-type", default="cursor")

    args = parser.parse_args()

    if args.command == "doctor":
        _doctor()
        return

    memory = AgentMemory()

    if args.command == "init":
        memory.ensure_schema()
        print("Schema applied.")
        return

    if args.command == "remember":
        ctx = SessionContext(
            session_id=args.session_id,
            session_type=SessionType(args.session_type),
            agent_id=args.agent,
        )
        record = memory.remember(
            ctx,
            MemoryType(args.memory_type),
            json.loads(args.content),
            source=MemorySource(args.source),
        )
        _print_records([record])
        return

    if args.command == "recall":
        records = memory.recall(
            agent_id=args.agent,
            session_id=args.session_id,
            session_type=SessionType(args.session_type) if args.session_type else None,
            memory_type=MemoryType(args.memory_type) if args.memory_type else None,
            source=MemorySource(args.source) if args.source else None,
            limit=args.limit,
        )
        _print_records(records)
        return

    if args.command == "linear-ingest":
        ctx = SessionContext(
            session_id=args.session_id,
            session_type=SessionType(args.session_type),
        )
        record = memory.linear.ingest_issue(args.issue_id, ctx)
        _print_records([record])
        return

    if args.command == "notion-ingest":
        ctx = SessionContext(
            session_id=args.session_id,
            session_type=SessionType(args.session_type),
        )
        record = memory.notion.ingest_page(args.page_id, ctx)
        _print_records([record])
        return

    parser.print_help()
    sys.exit(2)


if __name__ == "__main__":
    main()
