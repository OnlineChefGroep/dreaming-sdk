"""Tests for dream-eval MCP server create_server and main."""

from unittest.mock import MagicMock, patch


def test_main():
    with patch("dream_eval.mcp.server.create_server") as mock_create:
        mock_server = MagicMock()
        mock_create.return_value = mock_server

        from dream_eval.mcp.server import main
        main()
        mock_server.run.assert_called_once()
