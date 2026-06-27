#!/usr/bin/env python3
"""CLI for agent memory — schema init, query, Linear/Notion ingest."""

from __future__ import annotations

import argparse
import json
import sys

from dreaming_memory import AgentMemory, FleetConfig, SessionContext
from dreaming_memory.types import MemoryRecord, MemorySource, MemoryType, SessionType


def _print_records(records: list[MemoryRecord]) -> None:
    for r in records:
        print(json.dumps(r.model_dump(mode="json"), default=str))


def _enum_value(value: object) -> object:
    """Return the underlying value for StrEnum members, pass others through."""
    return value.value if hasattr(value, "value") else value


def render_export_markdown(session_id: str, records: list[MemoryRecord]) -> str:
    """Render memory records for a session as Markdown (pure, DB-free)."""
    lines: list[str] = [f"# Memory export — {session_id}", ""]
    if not records:
        lines.append("_No memory records found._")
        return "\n".join(lines) + "\n"
    for r in records:
        memory_type = _enum_value(r.memory_type)
        source = _enum_value(r.source)
        created = r.created_at.isoformat() if r.created_at else "unknown"
        lines.append(f"## {memory_type} ({created})")
        lines.append(f"**Source:** {source}")
        lines.append("")
        lines.append("```json")
        lines.append(json.dumps(r.content, indent=2, default=str, ensure_ascii=False))
        lines.append("```")
        lines.append("")
    return "\n".join(lines).rstrip() + "\n"


def _doctor() -> None:
    """Print config presence + Postgres/Linear/Notion connectivity (no secret values)."""
    import httpx
    import psycopg

    config = FleetConfig.load()
    status = config.status()
    print(json.dumps({"config": status, "redacted": config.redacted()}, indent=2))
    try:
        memory = AgentMemory(config=config, enable_sentry=False)
        with memory.store._pool.connection() as conn:
            conn.execute("SELECT 1")
        memory.store.close()
        print('{"postgres": "ok"}')
    except psycopg.Error:
        print('{"postgres": "error", "detail": "connection failed"}')

    if config.linear_api_key:
        try:
            from dreaming_memory.integrations.linear import LinearClient

            client = LinearClient(api_key=config.linear_api_key)
            client.gql("query { viewer { id } }")
            print('{"linear": "ok"}')
        except httpx.HTTPError:
            print('{"linear": "error", "detail": "connection failed"}')
    else:
        print('{"linear": "missing_api_key"}')

    if config.notion_api_key:
        try:
            from dreaming_memory.integrations.notion import NotionMemoryBridge
            from dreaming_memory.store.postgres import AgentMemoryStore

            NotionMemoryBridge(AgentMemoryStore(config.database_url))
            print('{"notion": "wired"}')
        except httpx.HTTPError:
            print('{"notion": "error", "detail": "connection failed"}')
    else:
        print('{"notion": "missing_api_key"}')


def main() -> None:
    parser = argparse.ArgumentParser(description="cursor-dreaming-sdk agent memory CLI")
    sub = parser.add_subparsers(dest="command", required=True)

    sub.add_parser("init", help="Apply Postgres schema")
    sub.add_parser("doctor", help="Show config presence + DB connectivity")

    p_metrics = sub.add_parser("metrics", help="Print aggregated metrics as JSON")
    p_metrics.add_argument("--days", type=int, default=14)

    p_triage = sub.add_parser("triage", help="Auto-triage untriaged Linear issues")
    p_triage.add_argument("--state", default=None, help="Filter by workflow state name")
    p_triage.add_argument("--limit", type=int, default=50)
    p_triage.add_argument("--apply", action="store_true", help="Write priority/labels to Linear")
    p_triage.add_argument("--comment", action="store_true", help="Post rationale comment")

    p_serve = sub.add_parser("serve", help="Run the metrics dashboard")
    p_serve.add_argument("--host", default="0.0.0.0")
    p_serve.add_argument("--port", type=int, default=8787)

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

    p_export = sub.add_parser("export", help="Export a session's memory as Markdown")
    p_export.add_argument("--session-id", required=True)
    p_export.add_argument("--agent", default=None)
    p_export.add_argument("--output", default=None, help="Write Markdown to this file")

    p_slack = sub.add_parser("slack-report", help="Post an eval report to Slack")
    p_slack.add_argument("--run-id", default=None)
    p_slack.add_argument("--metrics-json", default=None, help="Path to metrics JSON file")

    args = parser.parse_args()

    if args.command == "doctor":
        _doctor()
        return

    if args.command == "metrics":
        from dreaming_memory.store.postgres import AgentMemoryStore

        with AgentMemoryStore() as store:
            print(json.dumps(store.metrics(days=args.days), indent=2, default=str))
        return

    if args.command == "serve":
        from dreaming_memory.dashboard import serve

        serve(host=args.host, port=args.port)
        return

    if args.command == "triage":
        from dreaming_memory.triage import AutoTriage

        with AutoTriage() as triage:
            results = triage.run(
                state=args.state, limit=args.limit, apply=args.apply, comment=args.comment
            )
            for r in results:
                print(json.dumps(r.to_content(), default=str))
            print(f"# triaged {len(results)} issue(s); apply={args.apply}")
        return

    if args.command == "slack-report":
        from dreaming_memory.integrations.slack import SlackClient

        metrics: dict = {}
        if args.metrics_json:
            with open(args.metrics_json, encoding="utf-8") as fh:
                metrics = json.load(fh)
        sent = SlackClient().report_eval_result(metrics, run_id=args.run_id)
        if sent:
            print(json.dumps({"slack": "sent", "run_id": args.run_id}))
        else:
            print(json.dumps({"slack": "skipped", "reason": "no SLACK_WEBHOOK_URL configured"}))
        return

    if args.command == "export":
        # Initialize the store/memory BEFORE use; do not rely on the shared
        # `memory = AgentMemory()` defined later in this function.
        with AgentMemory() as memory:
            records = memory.recall(
                session_id=args.session_id,
                agent_id=args.agent,
                limit=100,
            )
            markdown = render_export_markdown(args.session_id, records)
            if args.output:
                with open(args.output, "w", encoding="utf-8") as fh:
                    fh.write(markdown)
                print(json.dumps({
                    "export": "written", "path": args.output, "records": len(records)
                }))
            else:
                print(markdown)
        return

    with AgentMemory() as memory:
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
