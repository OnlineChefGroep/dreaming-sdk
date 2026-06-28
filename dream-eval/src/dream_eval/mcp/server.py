"""dream-eval MCP server — exposes scoring and gates as MCP tools.

Run with:
    uv run dream-eval-mcp

Or via uvx:
    uvx dream-eval[mcp]
"""

from __future__ import annotations

import json
from typing import Any

from dream_eval.gates import check_hash_determinism, check_secret_leak
from dream_eval.scoring import compute_faithfulness
from dream_eval.types import LabeledItem, ProposedItem

TOOL_DEFINITIONS = [
    {
        "name": "dream_score",
        "description": (
            "Score evaluator output against golden corpus labels. "
            "Returns faithfulness, precision, recall, and recurrence metrics."
        ),
        "inputSchema": {
            "type": "object",
            "properties": {
                "proposed": {
                    "type": "array",
                    "description": "List of proposed items from evaluator",
                    "items": {
                        "type": "object",
                        "properties": {
                            "id": {"type": "string"},
                            "category": {"type": "string"},
                            "content": {"type": "object"},
                            "recurrence": {"type": "integer", "default": 1},
                        },
                        "required": ["id", "category"],
                    },
                },
                "labels": {
                    "type": "array",
                    "description": "Ground truth labels from golden corpus",
                    "items": {
                        "type": "object",
                        "properties": {
                            "id": {"type": "string"},
                            "category": {"type": "string"},
                            "content": {"type": "object"},
                            "max_recurrence": {"type": "integer"},
                        },
                        "required": ["id", "category"],
                    },
                },
            },
            "required": ["proposed", "labels"],
        },
    },
    {
        "name": "dream_check_secrets",
        "description": (
            "Check text for leaked secrets "
            "(API keys, DSNs, passwords). Returns pass/fail."
        ),
        "inputSchema": {
            "type": "object",
            "properties": {
                "text": {"type": "string", "description": "Text to scan"},
                "forbidden_patterns": {
                    "type": "array",
                    "items": {"type": "string"},
                    "description": "Regex patterns indicating a secret leak",
                },
            },
            "required": ["text"],
        },
    },
    {
        "name": "dream_check_hash",
        "description": (
            "Verify content produces a deterministic hash "
            "after BOM/CRLF normalization."
        ),
        "inputSchema": {
            "type": "object",
            "properties": {
                "content": {"type": "string", "description": "Content to hash"},
                "expected_hash": {
                    "type": "string",
                    "description": "Expected sha256:hex hash (optional)",
                },
            },
            "required": ["content"],
        },
    },
    {
        "name": "dream_metrics_schema",
        "description": "Return the 25-key canonical metrics.json schema.",
        "inputSchema": {
            "type": "object",
            "properties": {},
        },
    },
]


METRICS_SCHEMA = {
    "run_id": "string (ISO stem) [required]",
    "date": "ISO8601",
    "timestamp": "ISO8601",
    "mode": "golden | live",
    "sessions_evaluated": "int",
    "items_proposed": "int",
    "accepted": "int",
    "rejected": "int",
    "edited": "int",
    "deferred": "int",
    "rolled_back": {"pref": "int", "workflow": "int", "skill": "int",
                     "subagent": "int", "rule": "int"},
    "acceptance_rate": {"overall": "float|null", "per_category": "float|null"},
    "precision": "float [0,1]",
    "recall": "float [0,1]",
    "recurrence_calibration": "float [0,1]",
    "faithfulness_score": "float [0,1] [required]",
    "faithfulness": "float [0,1]",
    "secret_leak_test": "pass | fail | warn | skip",
    "gates": "{gate_name: bool, ...}",
    "hard_fail": "bool",
    "regret_rate": "float|null",
    "token_cost": "int",
    "latency": "float",
    "soul_version": "sha256:<hex>",
    "agents_md_hash_before": "string|null",
    "agents_md_hash_after": "string|null",
}


def _make_handler(tool_name: str) -> Any:
    """Create a handler function bound to a specific tool name."""

    def handler(**kwargs: Any) -> str:
        return handle_tool(tool_name, kwargs)

    return handler


def handle_tool(name: str, arguments: dict[str, Any]) -> str:
    """Route MCP tool call to the appropriate function."""
    if name == "dream_score":
        proposed = [ProposedItem(**item) for item in arguments["proposed"]]
        labels = [LabeledItem(**lab) for lab in arguments["labels"]]
        report = compute_faithfulness(proposed, labels)
        return json.dumps(report.model_dump(mode="json"), default=str)

    if name == "dream_check_secrets":
        result = check_secret_leak(
            arguments["text"],
            forbidden_patterns=arguments.get("forbidden_patterns"),
        )
        return json.dumps(result.model_dump(mode="json"), default=str)

    if name == "dream_check_hash":
        result = check_hash_determinism(
            arguments["content"],
            expected_hash=arguments.get("expected_hash"),
        )
        return json.dumps(result.model_dump(mode="json"), default=str)

    if name == "dream_metrics_schema":
        return json.dumps(METRICS_SCHEMA, indent=2)

    return json.dumps({"error": f"Unknown tool: {name}"})


def create_server() -> Any:
    """Create an MCP server instance.

    Requires `mcp` package: pip install dream-eval[mcp]
    """
    try:
        from mcp.server.fastmcp import FastMCP
    except ImportError as exc:
        raise ImportError(
            "MCP server requires the `mcp` package. "
            "Install with: pip install dream-eval[mcp]"
        ) from exc

    mcp = FastMCP(
        "dream-eval",
        version="0.2.0",
        description="Agent-agnostic faithfulness evaluation for agent memory",
    )

    for tool_def in TOOL_DEFINITIONS:
        mcp.tool(
            name=tool_def["name"],
            description=tool_def["description"],
        )(_make_handler(tool_def["name"]))

    return mcp


def main() -> None:
    """Entry point for `dream-eval-mcp` CLI."""
    server = create_server()
    server.run()


if __name__ == "__main__":
    main()
