# cursor-dreaming-memory

Lightweight agent memory extension for **dreaming-sdk** (Utrecht Data OS / CHEF-308).

## Install

```bash
cd python
uv sync --extra dev
uv run dream-memory init   # requires Postgres
```

Optional semantic layer:

```bash
uv sync --extra semantic
```

## Quick start

```python
from cursor_dreaming_memory import AgentMemory, SessionContext
from cursor_dreaming_memory.types import MemoryType, MemorySource

memory = AgentMemory()
memory.ensure_schema()

ctx = SessionContext.for_dream_eval("2026-06-15T09-00-00Z")
memory.remember(ctx, MemoryType.OBSERVATION, {"faithfulness": 0.63}, source=MemorySource.SDK)
```

## CLI

```bash
dream-memory init
dream-memory remember --session-id run-1 --content '{"note":"hello"}'
dream-memory recall --session-id run-1
dream-memory linear-ingest CHEF-308
dream-memory notion-ingest <page_id>
dream-memory export --session-id run-1 --output run-1.md
dream-memory slack-report --run-id run-1 --metrics-json metrics.json
dream-memory doctor
```

- `export` writes a session's memory records as Markdown (`--output` to a file, or stdout).
- `slack-report` posts an eval report to Slack via `SLACK_WEBHOOK_URL` (no-op if unset).
- `doctor` reports config presence plus Postgres, Linear, and Notion connectivity.

## Example flow

```bash
uv run python examples/linear_memory_flow.py --issue CHEF-308 --comment
```

See [docs/agent-memory.md](../docs/agent-memory.md) for architecture and OCI deployment.
