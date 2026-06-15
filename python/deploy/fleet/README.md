# Fleet deployment — agent memory

Connect every code-agent CLI on the fleet (Cursor, Codex, Claude, OpenCode, Grok)
to the shared Postgres memory layer.

## Topology

| Node | Shape | Role |
|------|-------|------|
| `bc-scan-arm` | A1.Flex (ARM, 23GB) | **Memory SSOT** — Postgres + vector (qdrant/weaviate) + llama.cpp |
| `bc-scan-2` | A1.Flex (ARM) | Inference / inventory worker |
| `bc-scan-1` | E2.1.Micro (x86) | Scanner |
| `bc-monitor` | E2.1.Micro (x86) | Monitoring |
| `sofie` (this host) | local | Dev + orchestration |

Postgres SSOT: `postgresql://agentmem:***@100.68.121.19:5432/agent_memory` (Tailscale).

## 1. Sync env to all nodes

```bash
cd python/deploy/fleet
./sync-env.sh                 # all nodes
./sync-env.sh bc-scan-arm     # single node
```

This ships only the memory-related keys to `~/.agent-memory.env` on each node and
sources it from `~/.bashrc`.

## 2. Install the package on a node

```bash
./install-agent-memory.sh bc-scan-2
```

## 3. Wire code-agent CLIs

Each agent CLI inherits the DSN + keys because its shell sources `~/.agent-memory.env`.
Agents call memory three ways:

| Surface | How |
|---------|-----|
| Python | `from cursor_dreaming_memory import AgentMemory` |
| CLI | `dream-memory remember/recall/linear-ingest/notion-ingest` |
| Skill | `skills-bundle/shared/agent-memory.md` (drop into any agent skills dir) |

`session_type` is auto-detected per agent (cursor / codex / claude / opencode / grok)
via `SessionContext.from_sdk_payload()`.

## 4. Verify

```bash
ssh bc-scan-arm 'cd ~/Orgchefgroep/cursor-dreaming-sdk/python && uv run dream-memory recall --limit 5'
```
