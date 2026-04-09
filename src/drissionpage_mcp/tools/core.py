from __future__ import annotations

from collections.abc import Callable
from typing import Any

from mcp.server.fastmcp import FastMCP

from drissionpage_mcp.dependencies import ToolDependencies
from drissionpage_mcp.errors import ToolError


CORE_TOOL_NAMES = (
    "session_create",
    "session_close",
    "page_navigate",
    "page_refresh",
    "page_go_back",
    "page_go_forward",
    "page_get_url",
    "page_get_html",
    "page_get_text",
    "page_screenshot",
    "element_find",
    "element_click",
    "element_type",
    "wait_for_element",
    "wait_time",
)


def _error_payload(error: ToolError) -> dict[str, Any]:
    return {
        "ok": False,
        "error_code": error.code.value,
        "message": error.message,
        "retryable": error.retryable,
        **error.context,
    }


def _handle_errors(callback: Callable[..., Any], *args: Any, **kwargs: Any) -> dict[str, Any]:
    try:
        result = callback(*args, **kwargs)
        return result.to_dict()
    except ToolError as error:
        return _error_payload(error)


def build_core_handlers(deps: ToolDependencies) -> dict[str, Callable[..., dict[str, Any]]]:
    def session_create(mode: str = "ephemeral") -> dict[str, Any]:
        session = deps.registry.create_session(mode)
        return {
            "ok": True,
            "message": "Created session.",
            "session_id": session.session_id,
            "mode": session.mode,
        }

    def session_close(session_id: str) -> dict[str, Any]:
        try:
            deps.registry.close_session(session_id)
        except ToolError as error:
            return _error_payload(error)
        return {"ok": True, "message": "Closed session.", "session_id": session_id}

    def page_navigate(url: str, session_id: str | None = None, tab_id: str | None = None) -> dict[str, Any]:
        def action() -> Any:
            deps.policy.require_url_allowed(url)
            session = deps.registry.get_session(session_id)
            return deps.page_service.navigate(session, url, tab_id)

        return _handle_errors(action)

    def page_refresh(session_id: str | None = None, tab_id: str | None = None) -> dict[str, Any]:
        def action() -> Any:
            session = deps.registry.get_session(session_id)
            return deps.page_service.refresh(session, tab_id)

        return _handle_errors(action)

    def page_go_back(session_id: str | None = None, tab_id: str | None = None) -> dict[str, Any]:
        def action() -> Any:
            session = deps.registry.get_session(session_id)
            return deps.page_service.go_back(session, tab_id)

        return _handle_errors(action)

    def page_go_forward(session_id: str | None = None, tab_id: str | None = None) -> dict[str, Any]:
        def action() -> Any:
            session = deps.registry.get_session(session_id)
            return deps.page_service.go_forward(session, tab_id)

        return _handle_errors(action)

    def page_get_url(session_id: str | None = None, tab_id: str | None = None) -> dict[str, Any]:
        def action() -> Any:
            session = deps.registry.get_session(session_id)
            return deps.page_service.get_url(session, tab_id)

        return _handle_errors(action)

    def page_get_html(session_id: str | None = None, tab_id: str | None = None) -> dict[str, Any]:
        def action() -> Any:
            session = deps.registry.get_session(session_id)
            return deps.page_service.get_html(session, tab_id)

        return _handle_errors(action)

    def page_get_text(session_id: str | None = None, tab_id: str | None = None) -> dict[str, Any]:
        def action() -> Any:
            session = deps.registry.get_session(session_id)
            return deps.page_service.get_text(session, tab_id)

        return _handle_errors(action)

    def page_screenshot(
        session_id: str | None = None,
        tab_id: str | None = None,
        output_path: str = "screenshots",
        file_name: str = "page.png",
        full_page: bool = False,
    ) -> dict[str, Any]:
        def action() -> Any:
            session = deps.registry.get_session(session_id)
            return deps.page_service.screenshot(
                session,
                tab_id,
                output_path=output_path,
                file_name=file_name,
                full_page=full_page,
            )

        return _handle_errors(action)

    def element_find(selector: str, session_id: str | None = None, tab_id: str | None = None) -> dict[str, Any]:
        def action() -> Any:
            session = deps.registry.get_session(session_id)
            return deps.page_service.find(session, selector, tab_id)

        return _handle_errors(action)

    def element_click(selector: str, session_id: str | None = None, tab_id: str | None = None) -> dict[str, Any]:
        def action() -> Any:
            session = deps.registry.get_session(session_id)
            return deps.page_service.click(session, selector, tab_id)

        return _handle_errors(action)

    def element_type(
        selector: str,
        text: str,
        session_id: str | None = None,
        tab_id: str | None = None,
        clear: bool = False,
    ) -> dict[str, Any]:
        def action() -> Any:
            session = deps.registry.get_session(session_id)
            return deps.page_service.type_text(session, selector, text, clear=clear, tab_id=tab_id)

        return _handle_errors(action)

    def wait_for_element(
        selector: str,
        session_id: str | None = None,
        tab_id: str | None = None,
        timeout_s: float = 10.0,
    ) -> dict[str, Any]:
        def action() -> Any:
            session = deps.registry.get_session(session_id)
            return deps.page_service.wait_for_element(session, selector, timeout_s=timeout_s, tab_id=tab_id)

        return _handle_errors(action)

    def wait_time(seconds: float, session_id: str | None = None, tab_id: str | None = None) -> dict[str, Any]:
        def action() -> Any:
            session = deps.registry.get_session(session_id)
            return deps.page_service.wait_time(session, seconds, tab_id)

        return _handle_errors(action)

    return {
        "session_create": session_create,
        "session_close": session_close,
        "page_navigate": page_navigate,
        "page_refresh": page_refresh,
        "page_go_back": page_go_back,
        "page_go_forward": page_go_forward,
        "page_get_url": page_get_url,
        "page_get_html": page_get_html,
        "page_get_text": page_get_text,
        "page_screenshot": page_screenshot,
        "element_find": element_find,
        "element_click": element_click,
        "element_type": element_type,
        "wait_for_element": wait_for_element,
        "wait_time": wait_time,
    }


def register_core_tools(mcp: FastMCP, deps: ToolDependencies) -> None:
    handlers = build_core_handlers(deps)

    @mcp.tool(name="session_create")
    def session_create(mode: str = "ephemeral") -> dict[str, Any]:
        return handlers["session_create"](mode)

    @mcp.tool(name="session_close")
    def session_close(session_id: str) -> dict[str, Any]:
        return handlers["session_close"](session_id)

    @mcp.tool(name="page_navigate")
    def page_navigate(url: str, session_id: str | None = None, tab_id: str | None = None) -> dict[str, Any]:
        return handlers["page_navigate"](url, session_id, tab_id)

    @mcp.tool(name="page_refresh")
    def page_refresh(session_id: str | None = None, tab_id: str | None = None) -> dict[str, Any]:
        return handlers["page_refresh"](session_id, tab_id)

    @mcp.tool(name="page_go_back")
    def page_go_back(session_id: str | None = None, tab_id: str | None = None) -> dict[str, Any]:
        return handlers["page_go_back"](session_id, tab_id)

    @mcp.tool(name="page_go_forward")
    def page_go_forward(session_id: str | None = None, tab_id: str | None = None) -> dict[str, Any]:
        return handlers["page_go_forward"](session_id, tab_id)

    @mcp.tool(name="page_get_url")
    def page_get_url(session_id: str | None = None, tab_id: str | None = None) -> dict[str, Any]:
        return handlers["page_get_url"](session_id, tab_id)

    @mcp.tool(name="page_get_html")
    def page_get_html(session_id: str | None = None, tab_id: str | None = None) -> dict[str, Any]:
        return handlers["page_get_html"](session_id, tab_id)

    @mcp.tool(name="page_get_text")
    def page_get_text(session_id: str | None = None, tab_id: str | None = None) -> dict[str, Any]:
        return handlers["page_get_text"](session_id, tab_id)

    @mcp.tool(name="page_screenshot")
    def page_screenshot(
        session_id: str | None = None,
        tab_id: str | None = None,
        output_path: str = "screenshots",
        file_name: str = "page.png",
        full_page: bool = False,
    ) -> dict[str, Any]:
        return handlers["page_screenshot"](session_id, tab_id, output_path, file_name, full_page)

    @mcp.tool(name="element_find")
    def element_find(selector: str, session_id: str | None = None, tab_id: str | None = None) -> dict[str, Any]:
        return handlers["element_find"](selector, session_id, tab_id)

    @mcp.tool(name="element_click")
    def element_click(selector: str, session_id: str | None = None, tab_id: str | None = None) -> dict[str, Any]:
        return handlers["element_click"](selector, session_id, tab_id)

    @mcp.tool(name="element_type")
    def element_type(
        selector: str,
        text: str,
        session_id: str | None = None,
        tab_id: str | None = None,
        clear: bool = False,
    ) -> dict[str, Any]:
        return handlers["element_type"](selector, text, session_id, tab_id, clear)

    @mcp.tool(name="wait_for_element")
    def wait_for_element(
        selector: str,
        session_id: str | None = None,
        tab_id: str | None = None,
        timeout_s: float = 10.0,
    ) -> dict[str, Any]:
        return handlers["wait_for_element"](selector, session_id, tab_id, timeout_s)

    @mcp.tool(name="wait_time")
    def wait_time(seconds: float, session_id: str | None = None, tab_id: str | None = None) -> dict[str, Any]:
        return handlers["wait_time"](seconds, session_id, tab_id)
