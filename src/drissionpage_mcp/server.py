from __future__ import annotations

import logging
import sys

from mcp.server.fastmcp import FastMCP

from drissionpage_mcp.config import ConfigError, ServerConfig, load_config
from drissionpage_mcp.dependencies import ToolDependencies, build_dependencies
from drissionpage_mcp.tools.core import register_core_tools
from drissionpage_mcp.tools.introspection import register_introspection_tools


def build_server(config: ServerConfig) -> tuple[FastMCP, ToolDependencies]:
    deps = build_dependencies(config)
    server = FastMCP(
        config.server_name,
        instructions="Use the available tools to control a local browser through DrissionPage.",
    )
    register_core_tools(server, deps)
    register_introspection_tools(server, deps)
    return server, deps


def create_server(config_path: str | None = None) -> FastMCP:
    config = load_config(config_path)
    server, _ = build_server(config)
    return server


def main() -> None:
    logging.basicConfig(
        stream=sys.stderr,
        level=logging.INFO,
        format="%(asctime)s %(levelname)s %(name)s %(message)s",
    )
    try:
        config = load_config(None)
    except ConfigError as error:
        print(f"drissionpage-mcp: {error}", file=sys.stderr)
        raise SystemExit(2) from error
    server, deps = build_server(config)
    try:
        server.run()
    finally:
        deps.registry.close_all()
