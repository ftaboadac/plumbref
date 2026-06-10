from __future__ import annotations


def test_mcp_server_import_does_not_require_runtime_import() -> None:
    """MCP server module imports without starting the stdio server."""
    import plumbref.mcp_server

    assert plumbref.mcp_server.run_mcp_server
