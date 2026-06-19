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

    # DB Check
    try:
        store = AgentMemory(config=config, enable_sentry=False).store
        with store._conn() as conn:
            conn.execute("SELECT 1")
        print('{"postgres": "ok"}')
    except Exception as exc:  # noqa: BLE001
        print(json.dumps({"postgres": "error", "detail": str(exc)}))

    # Linear Check
    if config.linear_api_key:
        try:
            from cursor_dreaming_memory.integrations.linear import LinearClient
            client = LinearClient(api_key=config.linear_api_key)
            client.gql("query { viewer { id } }")
            print('{"linear": "ok"}')
        except Exception as exc: # noqa: BLE001
            print(json.dumps({"linear": "error", "detail": str(exc)}))
    else:
        print('{"linear": "missing_api_key"}')

    # Notion Check
    if config.notion_api_key or config.notion_token:
        try:
            from cursor_dreaming_memory.integrations.notion import NotionMemoryBridge
            from cursor_dreaming_memory.store.postgres import AgentMemoryStore
            # Simple check if we can initialize it
            _ = NotionMemoryBridge(AgentMemoryStore(config.database_url))
            print('{"notion": "wired"}')
        except Exception as exc: # noqa: BLE001
            print(json.dumps({"notion": "error", "detail": str(exc)}))
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

    p_export = sub.add_parser("export", help="Export session memory as Markdown")
    p_export.add_argument("--session-id", required=True)
    p_export.add_argument("--agent")
    p_export.add_argument("--output", help="Output filename")

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

    p_slack = sub.add_parser("slack-report", help="Report eval results to Slack")
    p_slack.add_argument("--run-id")
    p_slack.add_argument("--metrics-json", help="Path to metrics.json")

    args = parser.parse_args()

    if args.command == "doctor":
        _doctor()
        return

    if args.command == "metrics":
        from cursor_dreaming_memory.store.postgres import AgentMemoryStore

        print(json.dumps(AgentMemoryStore().metrics(days=args.days), indent=2, default=str))
        return

    if args.command == "serve":
        from cursor_dreaming_memory.dashboard import serve

        serve(host=args.host, port=args.port)
        return

    if args.command == "export":
        records = memory.recall(session_id=args.session_id, agent_id=args.agent, limit=100)
        lines = [f"# Session Memory Export: {args.session_id}\n"]
        for r in records:
            lines.append(f"## {r.memory_type.value} ({r.created_at})")
            lines.append(f"**Source:** {r.source.value}")
            lines.append("```json")
            lines.append(json.dumps(r.content, indent=2))
            lines.append("```\n")

        md = "\n".join(lines)
        if args.output:
            with open(args.output, "w", encoding="utf-8") as f:
                f.write(md)
            print(f"Exported to {args.output}")
        else:
            print(md)
        return

    if args.command == "triage":
        from cursor_dreaming_memory.triage import AutoTriage

        results = AutoTriage().run(
            state=args.state, limit=args.limit, apply=args.apply, comment=args.comment
        )
        for r in results:
            print(json.dumps(r.to_content(), default=str))
        print(f"# triaged {len(results)} issue(s); apply={args.apply}")
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

    if args.command == "slack-report":
        from cursor_dreaming_memory.integrations.slack import SlackClient

        metrics = {}
        if args.metrics_json:
            with open(args.metrics_json, encoding="utf-8") as f:
                metrics = json.load(f)

        SlackClient().report_eval_result(metrics, run_id=args.run_id)
        print("Slack report sent.")
        return

    parser.print_help()
    sys.exit(2)


if __name__ == "__main__":
    main()
