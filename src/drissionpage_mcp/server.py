from __future__ import annotations

from mcp.server.fastmcp import FastMCP

from drissionpage_mcp.config import load_config


def create_server(config_path: str | None = None) -> FastMCP:
    config = load_config(config_path)
    return FastMCP(
        config.server_name,
        instructions="Use the available tools to automate a local browser safely.",
    )


def main() -> None:
    create_server().run()
