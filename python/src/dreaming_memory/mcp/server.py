"""dreaming-memory MCP server — exposes memory + governance as MCP tools (CHEF-1009).

Run with:
    uv run dream-memory-mcp

Tools:
- memory_write — store a memory record
- memory_recall — query memory records with filters
- memory_propose — propose a memory with evidence for governance
- memory_verify — attach a verifier result to a proposed memory
- memory_curate — drive the curator state machine
- memory_governance — get governance detail for a memory
- memory_metrics — get trust metrics and curator lifecycle stats
"""

from __future__ import annotations

import json
from typing import Any

from dreaming_memory.config import FleetConfig
from dreaming_memory.store.postgres import AgentMemoryStore
from dreaming_memory.types import (
    CURATOR_VALID_TRANSITIONS,
    CuratorDecision,
    CuratorState,
    Evidence,
    EvidenceType,
    MemoryRecord,
    MemorySource,
    MemoryType,
    SessionType,
    VerifierResult,
    VerifierStatus,
)

_tool_defs = [
    {
        "name": "memory_write",
        "description": "Store a memory record in the Postgres SSOT.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "agent_id": {"type": "string"},
                "session_id": {"type": "string"},
                "session_type": {
                    "type": "string",
                    "enum": [s.value for s in SessionType],
                    "default": "generic",
                },
                "memory_type": {
                    "type": "string",
                    "enum": [m.value for m in MemoryType],
                },
                "content": {"type": "object", "description": "JSONB content"},
                "source": {
                    "type": "string",
                    "enum": [s.value for s in MemorySource],
                    "default": "sdk",
                },
                "metadata": {"type": "object", "default": {}},
            },
            "required": ["agent_id", "session_id", "memory_type", "content"],
        },
    },
    {
        "name": "memory_recall",
        "description": "Query memory records with optional filters.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "agent_id": {"type": "string"},
                "session_id": {"type": "string"},
                "memory_type": {"type": "string"},
                "source": {"type": "string"},
                "limit": {"type": "integer", "default": 20},
            },
        },
    },
    {
        "name": "memory_propose",
        "description": (
            "Propose a memory with evidence for the governance pipeline. "
            "Creates the memory, writes evidence, and sets curator state to PROPOSED."
        ),
        "inputSchema": {
            "type": "object",
            "properties": {
                "agent_id": {"type": "string"},
                "session_id": {"type": "string"},
                "memory_type": {"type": "string", "enum": [m.value for m in MemoryType]},
                "content": {"type": "object"},
                "evidence": {
                    "type": "array",
                    "items": {
                        "type": "object",
                        "properties": {
                            "evidence_type": {
                                "type": "string",
                                "enum": [e.value for e in EvidenceType],
                            },
                            "source_url": {"type": "string"},
                            "excerpt": {"type": "string", "default": ""},
                            "confidence": {
                                "type": "number",
                                "default": 1.0,
                                "minimum": 0,
                                "maximum": 1,
                            },
                        },
                        "required": ["evidence_type"],
                    },
                },
            },
            "required": ["agent_id", "session_id", "memory_type", "content", "evidence"],
        },
    },
    {
        "name": "memory_verify",
        "description": "Attach a verifier result to a proposed memory.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "memory_id": {"type": "string", "description": "UUID of the memory"},
                "status": {
                    "type": "string",
                    "enum": [s.value for s in VerifierStatus],
                },
                "score": {
                    "type": "number",
                    "minimum": 0,
                    "maximum": 1,
                    "default": 0.0,
                },
                "rationale": {"type": "string", "default": ""},
                "checked_by": {"type": "string", "default": ""},
            },
            "required": ["memory_id", "status"],
        },
    },
    {
        "name": "memory_curate",
        "description": (
            "Drive the curator state machine for a memory. "
            "Valid transitions: proposed→reviewing, reviewing→accepted|rejected|edited|deferred, "
            "deferred→reviewing, accepted→rolled_back."
        ),
        "inputSchema": {
            "type": "object",
            "properties": {
                "memory_id": {"type": "string", "description": "UUID of the memory"},
                "new_state": {
                    "type": "string",
                    "enum": [s.value for s in CuratorState],
                },
                "decided_by": {"type": "string", "default": ""},
                "rationale": {"type": "string", "default": ""},
            },
            "required": ["memory_id", "new_state"],
        },
    },
    {
        "name": "memory_governance",
        "description": "Get governance detail for a specific memory (evidence, verifier, curator).",
        "inputSchema": {
            "type": "object",
            "properties": {
                "memory_id": {"type": "string", "description": "UUID of the memory"},
            },
            "required": ["memory_id"],
        },
    },
    {
        "name": "memory_metrics",
        "description": "Get trust metrics and curator lifecycle stats.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "days": {"type": "integer", "default": 14},
            },
        },
    },
]

_store: AgentMemoryStore | None = None


def _get_store() -> AgentMemoryStore:
    global _store  # noqa: PLW0603
    if _store is None:
        config = FleetConfig.load()
        _store = AgentMemoryStore(config.database_url)
    return _store


def handle_tool(name: str, arguments: dict[str, Any]) -> str:
    """Route MCP tool call to the appropriate function."""
    store = _get_store()

    if name == "memory_write":
        record = MemoryRecord(
            agent_id=arguments["agent_id"],
            session_id=arguments["session_id"],
            session_type=SessionType(arguments.get("session_type", "generic")),
            memory_type=MemoryType(arguments["memory_type"]),
            content=arguments["content"],
            source=MemorySource(arguments.get("source", "sdk")),
            metadata=arguments.get("metadata", {}),
        )
        result = store.write(record)
        return json.dumps({
            "id": str(result.id),
            "created_at": str(result.created_at),
        })

    if name == "memory_recall":
        results = store.query(
            agent_id=arguments.get("agent_id"),
            session_id=arguments.get("session_id"),
            memory_type=(
                MemoryType(arguments["memory_type"])
                if arguments.get("memory_type")
                else None
            ),
            source=(
                MemorySource(arguments["source"])
                if arguments.get("source")
                else None
            ),
            limit=arguments.get("limit", 20),
        )
        return json.dumps({
            "items": [
                {
                    "id": str(r.id),
                    "memory_type": r.memory_type.value,
                    "agent_id": r.agent_id,
                    "content": r.content,
                    "created_at": str(r.created_at),
                }
                for r in results
            ],
            "total": len(results),
        })

    if name == "memory_propose":
        record = MemoryRecord(
            agent_id=arguments["agent_id"],
            session_id=arguments["session_id"],
            session_type=SessionType("generic"),
            memory_type=MemoryType(arguments["memory_type"]),
            content=arguments["content"],
            source=MemorySource.SDK,
            metadata={"curator.state": "proposed"},
        )
        record = store.write(record)

        # Write evidence
        for ev_data in arguments["evidence"]:
            ev = Evidence(
                evidence_type=EvidenceType(ev_data["evidence_type"]),
                source_url=ev_data.get("source_url"),
                excerpt=ev_data.get("excerpt", ""),
                confidence=ev_data.get("confidence", 1.0),
            )
            ev.memory_id = record.id
            store.write_evidence(ev)

        # Write initial curator decision
        decision = CuratorDecision(
            memory_id=record.id,
            state=CuratorState.PROPOSED,
            decided_by=arguments.get("agent_id", ""),
            rationale="Proposed via MCP",
        )
        store.write_curator_decision(decision)

        return json.dumps({
            "memory_id": str(record.id),
            "state": "proposed",
            "evidence_count": len(arguments["evidence"]),
        })

    if name == "memory_verify":
        from uuid import UUID
        mid = UUID(arguments["memory_id"])
        vr = VerifierResult(
            status=VerifierStatus(arguments["status"]),
            score=arguments.get("score", 0.0),
            rationale=arguments.get("rationale", ""),
            checked_by=arguments.get("checked_by", ""),
        )
        result = store.write_verifier_result(vr)
        return json.dumps({
            "id": str(result.id),
            "status": result.status.value,
            "score": result.score,
        })

    if name == "memory_curate":
        from uuid import UUID
        mid = UUID(arguments["memory_id"])
        new_state = CuratorState(arguments["new_state"])

        current = store.get_active_curator_decision(mid)
        if current is None:
            return json.dumps({"error": f"No active decision for memory {arguments['memory_id']}"})

        valid = CURATOR_VALID_TRANSITIONS.get(current.state, [])
        if new_state not in valid:
            return json.dumps({
                "error": f"Invalid transition: {current.state.value} → {new_state.value}",
                "valid": [s.value for s in valid],
            })

        updated = CuratorDecision(
            memory_id=mid,
            state=new_state,
            decided_by=arguments.get("decided_by", ""),
            rationale=arguments.get("rationale", ""),
            previous_state=current.state,
            transitions=current.transitions + [{
                "from": current.state.value,
                "to": new_state.value,
                "by": arguments.get("decided_by", ""),
                "rationale": arguments.get("rationale", ""),
            }],
        )
        store.update_curator_decision(mid, updated)
        return json.dumps({
            "memory_id": str(mid),
            "state": new_state.value,
            "previous": current.state.value,
        })

    if name == "memory_governance":
        from uuid import UUID
        mid = UUID(arguments["memory_id"])
        record = store.get(mid)
        evidence = store.get_evidence_for_memory(mid)
        verifier = store.get_verifier_results_for_memory(mid)
        decision = store.get_active_curator_decision(mid)

        return json.dumps({
            "memory": {
                "id": str(mid),
                "memory_type": record.memory_type.value if record else None,
                "agent_id": record.agent_id if record else None,
            },
            "evidence": [
                {
                    "type": e.evidence_type.value,
                    "excerpt": e.excerpt[:200],
                    "confidence": e.confidence,
                }
                for e in evidence
            ],
            "verifier_results": [
                {"status": v.status.value, "score": v.score, "rationale": v.rationale}
                for v in verifier
            ],
            "curator_decision": {
                "state": decision.state.value if decision else None,
                "transitions": len(decision.transitions) if decision else 0,
            } if decision else None,
        })

    if name == "memory_metrics":
        days = arguments.get("days", 14)
        metrics = store.metrics(days=days)
        gov = store.curator_metrics(days=days)
        return json.dumps({
            "memory": metrics,
            "governance": gov,
        })

    return json.dumps({"error": f"Unknown tool: {name}"})


def create_server() -> Any:
    """Create an MCP server instance.

    Requires `mcp` package: pip install dreaming-memory[mcp]
    """
    try:
        from mcp.server.fastmcp import FastMCP
    except ImportError as exc:
        raise ImportError(
            "MCP server requires the `mcp` package. "
            "Install with: pip install dreaming-memory[mcp]"
        ) from exc

    mcp = FastMCP(
        "dreaming-memory",
        version="0.2.0",
        description="Memory trust layer — governance, evidence, and curator workflows",
    )

    for tool_def in _tool_defs:
        mcp.tool(
            name=tool_def["name"],
            description=tool_def["description"],
        )(_make_handler(tool_def["name"]))

    return mcp


def _make_handler(tool_name: str) -> Any:
    def handler(**kwargs: Any) -> str:
        return handle_tool(tool_name, kwargs)
    return handler


def main() -> None:
    """Entry point for `dream-memory-mcp` CLI."""
    server = create_server()
    server.run()


if __name__ == "__main__":
    main()
