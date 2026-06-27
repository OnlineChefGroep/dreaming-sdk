"""MCP server for dream-eval — exposes eval tools to any MCP-compatible agent."""

from dream_eval.mcp.server import create_server

__all__ = ["create_server"]
