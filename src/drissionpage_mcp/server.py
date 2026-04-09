from __future__ import annotations

from mcp.server.fastmcp import FastMCP

from drissionpage_mcp.config import load_config
from drissionpage_mcp.dependencies import build_dependencies
from drissionpage_mcp.tools.core import register_core_tools
from drissionpage_mcp.tools.introspection import register_introspection_tools


def create_server(config_path: str | None = None) -> FastMCP:
    config = load_config(config_path)
    deps = build_dependencies(config)
    server = FastMCP(
        config.server_name,
        instructions="Use the available tools to control a local browser through DrissionPage.",
    )
    register_core_tools(server, deps)
    register_introspection_tools(server, deps)
    return server


def main() -> None:
    create_server().run()
