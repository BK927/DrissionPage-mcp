from __future__ import annotations

from collections.abc import Callable
from typing import Any

from mcp.server.fastmcp import FastMCP

from drissionpage_mcp.dependencies import ToolDependencies
from drissionpage_mcp.errors import ToolError
from drissionpage_mcp.tools.core import CORE_TOOL_NAMES


INTROSPECTION_TOOL_NAMES = (
    "server_get_capabilities",
    "server_get_policy",
    "browser_get_state",
)


def _error_payload(error: ToolError) -> dict[str, Any]:
    return {
        "ok": False,
        "error_code": error.code.value,
        "message": error.message,
        "retryable": error.retryable,
        **error.context,
    }


def build_introspection_handlers(deps: ToolDependencies) -> dict[str, Callable[..., dict[str, Any]]]:
    def server_get_capabilities() -> dict[str, Any]:
        return {
            "ok": True,
            "message": "Capabilities fetched.",
            "tools": list(CORE_TOOL_NAMES + INTROSPECTION_TOOL_NAMES),
            "transport": "stdio",
            "planned_future_tools": [
                "browser_attach",
                "browser_tabs",
                "cookies_export",
                "cookies_import",
                "storage_export",
                "run_js",
                "page_get_dom_snapshot",
            ],
        }

    def server_get_policy() -> dict[str, Any]:
        safety = deps.config.safety
        return {
            "ok": True,
            "message": "Policy fetched.",
            "mode": safety.mode,
            "allow_run_js": safety.allow_run_js,
            "allow_browser_attach": safety.allow_browser_attach,
            "allow_file_upload": safety.allow_file_upload,
            "allow_download": safety.allow_download,
            "allowed_domains": list(safety.allowed_domains),
            "default_timeout_ms": safety.default_timeout_ms,
            "download_dir": safety.download_dir,
        }

    def browser_get_state(session_id: str | None = None) -> dict[str, Any]:
        try:
            session = deps.registry.get_session(session_id)
            state = session.adapter.state(session.session_id)
        except ToolError as error:
            return _error_payload(error)
        return {
            "ok": True,
            "message": "Browser state fetched.",
            "session_id": state.session_id,
            "mode": state.mode,
            "current_tab_id": state.current_tab_id,
            "tabs": [{"tab_id": tab.tab_id, "title": tab.title, "url": tab.url} for tab in state.tabs],
        }

    return {
        "server_get_capabilities": server_get_capabilities,
        "server_get_policy": server_get_policy,
        "browser_get_state": browser_get_state,
    }


def register_introspection_tools(mcp: FastMCP, deps: ToolDependencies) -> None:
    handlers = build_introspection_handlers(deps)

    @mcp.tool(name="server_get_capabilities")
    def server_get_capabilities() -> dict[str, Any]:
        return handlers["server_get_capabilities"]()

    @mcp.tool(name="server_get_policy")
    def server_get_policy() -> dict[str, Any]:
        return handlers["server_get_policy"]()

    @mcp.tool(name="browser_get_state")
    def browser_get_state(session_id: str | None = None) -> dict[str, Any]:
        return handlers["browser_get_state"](session_id)
