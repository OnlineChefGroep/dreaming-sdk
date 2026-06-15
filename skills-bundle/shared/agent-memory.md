# Agent Memory — shared usage contract

Portable instructions for any code-agent CLI (Cursor, Codex, Claude, OpenCode, Grok)
to read/write the shared Postgres memory layer.

## Prerequisites

The host shell sources `~/.agent-memory.env` (provides `AGENT_MEMORY_DATABASE_URL`,
`LINEAR_API_KEY`, `NOTION_API_KEY`, etc.). Package installed via `uv sync` in
`cursor-dreaming-sdk/python`.

## Write a memory

```bash
dream-memory remember \
  --agent "$AGENT_NAME" \
  --session-id "$SESSION_ID" \
  --session-type codex \
  --type observation \
  --source sdk \
  --content '{"note":"refactored auth module","files":3}'
```

## Recall memory

```bash
dream-memory recall --session-id "$SESSION_ID" --limit 10
dream-memory recall --agent "$AGENT_NAME" --type decision
```

## Linear / Notion

```bash
dream-memory linear-ingest CHEF-308       # store issue + comments as memory
dream-memory notion-ingest <page_id>      # store page snapshot
```

## Python

```python
from cursor_dreaming_memory import AgentMemory, SessionContext
from cursor_dreaming_memory.types import MemoryType, MemorySource

memory = AgentMemory()                      # auto-loads fleet secrets + DSN
ctx = SessionContext.from_sdk_payload({"session_id": SID, "platform": "codex"})
memory.remember(ctx, MemoryType.DECISION, {"choice": "use psycopg3"}, source=MemorySource.SDK)
recent = memory.recall_session(ctx)
```

## Session types

`cursor · claude · codex · opencode · grok · sdk_local · sdk_cloud · dream_eval · dream_live · generic`

Always set `session_type` to the host agent so the dashboard can filter per surface.

## Rules

- Postgres is the single source of truth. Do not cache memory elsewhere.
- Keep `content` JSON small and structured (no full transcripts — use refs).
- Never write secrets into `content` or `metadata`.
