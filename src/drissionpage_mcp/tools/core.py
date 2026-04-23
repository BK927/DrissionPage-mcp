from __future__ import annotations

import logging
from collections.abc import Callable
from typing import Any

from mcp.server.fastmcp import FastMCP

from drissionpage_mcp.dependencies import ToolDependencies
from drissionpage_mcp.errors import ErrorCode, ToolError
from drissionpage_mcp.models import ToolResult

logger = logging.getLogger(__name__)


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


def _handle_tool_errors(
    tool_name: str, callback: Callable[[], dict[str, Any]]
) -> dict[str, Any]:
    logger.info("tool_start tool=%s", tool_name)
    try:
        result = callback()
    except ToolError as error:
        logger.warning("tool_error tool=%s code=%s message=%s", tool_name, error.code, error.message)
        return _error_payload(error)
    logger.info("tool_complete tool=%s", tool_name)
    return result


def _handle_result(
    tool_name: str, callback: Callable[..., ToolResult], *args: Any, **kwargs: Any
) -> dict[str, Any]:
    logger.info("tool_start tool=%s", tool_name)
    try:
        result = callback(*args, **kwargs)
        logger.info(
            "tool_complete tool=%s elapsed_ms=%s session_id=%s tab_id=%s",
            tool_name,
            result.elapsed_ms,
            result.session_id,
            result.tab_id,
        )
        return result.to_dict()
    except ToolError as error:
        logger.warning("tool_error tool=%s code=%s message=%s", tool_name, error.code, error.message)
        return _error_payload(error)


def build_core_handlers(deps: ToolDependencies) -> dict[str, Callable[..., dict[str, Any]]]:
    max_wait_time_s = deps.config.safety.max_wait_time_s

    def session_create(mode: str = "ephemeral") -> dict[str, Any]:
        def action() -> dict[str, Any]:
            session = deps.registry.create_session(mode)
            return {
                "ok": True,
                "message": "Created session.",
                "session_id": session.session_id,
                "mode": session.mode,
            }

        return _handle_tool_errors("session_create", action)

    def session_close(session_id: str) -> dict[str, Any]:
        def action() -> dict[str, Any]:
            deps.registry.close_session(session_id)
            return {
                "ok": True,
                "message": "Closed session.",
                "session_id": session_id,
            }

        return _handle_tool_errors("session_close", action)

    def page_navigate(url: str, session_id: str | None = None, tab_id: str | None = None) -> dict[str, Any]:
        def action() -> ToolResult:
            deps.policy.require_url_allowed(url)
            session = deps.registry.get_session(session_id)
            return deps.page_service.navigate(session, url, tab_id)

        return _handle_result("page_navigate", action)

    def page_refresh(session_id: str | None = None, tab_id: str | None = None) -> dict[str, Any]:
        def action() -> ToolResult:
            session = deps.registry.get_session(session_id)
            return deps.page_service.refresh(session, tab_id)

        return _handle_result("page_refresh", action)

    def page_go_back(session_id: str | None = None, tab_id: str | None = None) -> dict[str, Any]:
        def action() -> ToolResult:
            session = deps.registry.get_session(session_id)
            return deps.page_service.go_back(session, tab_id)

        return _handle_result("page_go_back", action)

    def page_go_forward(session_id: str | None = None, tab_id: str | None = None) -> dict[str, Any]:
        def action() -> ToolResult:
            session = deps.registry.get_session(session_id)
            return deps.page_service.go_forward(session, tab_id)

        return _handle_result("page_go_forward", action)

    def page_get_url(session_id: str | None = None, tab_id: str | None = None) -> dict[str, Any]:
        def action() -> ToolResult:
            session = deps.registry.get_session(session_id)
            return deps.page_service.get_url(session, tab_id)

        return _handle_result("page_get_url", action)

    def page_get_html(session_id: str | None = None, tab_id: str | None = None) -> dict[str, Any]:
        def action() -> ToolResult:
            session = deps.registry.get_session(session_id)
            return deps.page_service.get_html(session, tab_id)

        return _handle_result("page_get_html", action)

    def page_get_text(session_id: str | None = None, tab_id: str | None = None) -> dict[str, Any]:
        def action() -> ToolResult:
            session = deps.registry.get_session(session_id)
            return deps.page_service.get_text(session, tab_id)

        return _handle_result("page_get_text", action)

    def page_screenshot(
        session_id: str | None = None,
        tab_id: str | None = None,
        output_path: str = "screenshots",
        file_name: str = "page.png",
        full_page: bool = False,
    ) -> dict[str, Any]:
        def action() -> ToolResult:
            session = deps.registry.get_session(session_id)
            return deps.page_service.screenshot(
                session,
                tab_id,
                output_path=output_path,
                file_name=file_name,
                full_page=full_page,
            )

        return _handle_result("page_screenshot", action)

    def element_find(selector: str, session_id: str | None = None, tab_id: str | None = None) -> dict[str, Any]:
        def action() -> ToolResult:
            session = deps.registry.get_session(session_id)
            return deps.page_service.find(session, selector, tab_id)

        return _handle_result("element_find", action)

    def element_click(selector: str, session_id: str | None = None, tab_id: str | None = None) -> dict[str, Any]:
        def action() -> ToolResult:
            session = deps.registry.get_session(session_id)
            return deps.page_service.click(session, selector, tab_id)

        return _handle_result("element_click", action)

    def element_type(
        selector: str,
        text: str,
        session_id: str | None = None,
        tab_id: str | None = None,
        clear: bool = False,
    ) -> dict[str, Any]:
        def action() -> ToolResult:
            session = deps.registry.get_session(session_id)
            return deps.page_service.type_text(session, selector, text, clear=clear, tab_id=tab_id)

        return _handle_result("element_type", action)

    def wait_for_element(
        selector: str,
        session_id: str | None = None,
        tab_id: str | None = None,
        timeout_s: float = 10.0,
    ) -> dict[str, Any]:
        def action() -> ToolResult:
            _check_wait_bounds("timeout_s", timeout_s, max_wait_time_s)
            session = deps.registry.get_session(session_id)
            return deps.page_service.wait_for_element(session, selector, timeout_s=timeout_s, tab_id=tab_id)

        return _handle_result("wait_for_element", action)

    def wait_time(seconds: float, session_id: str | None = None, tab_id: str | None = None) -> dict[str, Any]:
        def action() -> ToolResult:
            _check_wait_bounds("seconds", seconds, max_wait_time_s)
            session = deps.registry.get_session(session_id)
            return deps.page_service.wait_time(session, seconds, tab_id)

        return _handle_result("wait_time", action)

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


def _check_wait_bounds(field_name: str, value: float, upper: float) -> None:
    if not isinstance(value, (int, float)) or isinstance(value, bool):
        raise ToolError(
            code=ErrorCode.INVALID_ARGUMENT,
            message=f"{field_name} must be a number.",
            context={field_name: value},
        )
    if value < 0:
        raise ToolError(
            code=ErrorCode.INVALID_ARGUMENT,
            message=f"{field_name} must be non-negative.",
            context={field_name: value},
        )
    if value > upper:
        raise ToolError(
            code=ErrorCode.INVALID_ARGUMENT,
            message=f"{field_name} exceeds max_wait_time_s ({upper}).",
            context={field_name: value, "max_wait_time_s": upper},
        )


def register_core_tools(mcp: FastMCP, deps: ToolDependencies) -> None:
    handlers = build_core_handlers(deps)

    @mcp.tool(name="session_create")
    def session_create(mode: str = "ephemeral") -> dict[str, Any]:
        """Create a new browser session and return its session_id. Use mode='ephemeral' for a temporary session that is discarded on close, or mode='persistent' to reuse a named profile across calls."""
        return handlers["session_create"](mode)

    @mcp.tool(name="session_close")
    def session_close(session_id: str) -> dict[str, Any]:
        """Close a non-default browser session identified by session_id, releasing its resources. The default session cannot be closed with this tool."""
        return handlers["session_close"](session_id)

    @mcp.tool(name="page_navigate")
    def page_navigate(url: str, session_id: str | None = None, tab_id: str | None = None) -> dict[str, Any]:
        """Navigate the browser to the given URL and return the final URL after any redirects. The URL must be permitted by the server's safety policy."""
        return handlers["page_navigate"](url, session_id, tab_id)

    @mcp.tool(name="page_refresh")
    def page_refresh(session_id: str | None = None, tab_id: str | None = None) -> dict[str, Any]:
        """Reload the current page, equivalent to pressing F5. Use this to re-fetch content after a server-side change or to recover from a stale page state."""
        return handlers["page_refresh"](session_id, tab_id)

    @mcp.tool(name="page_go_back")
    def page_go_back(session_id: str | None = None, tab_id: str | None = None) -> dict[str, Any]:
        """Navigate one step back in the browser's history, equivalent to clicking the Back button. Returns an error if there is no previous page."""
        return handlers["page_go_back"](session_id, tab_id)

    @mcp.tool(name="page_go_forward")
    def page_go_forward(session_id: str | None = None, tab_id: str | None = None) -> dict[str, Any]:
        """Navigate one step forward in the browser's history, equivalent to clicking the Forward button. Returns an error if there is no next page."""
        return handlers["page_go_forward"](session_id, tab_id)

    @mcp.tool(name="page_get_url")
    def page_get_url(session_id: str | None = None, tab_id: str | None = None) -> dict[str, Any]:
        """Return the current URL of the active tab. Use this to confirm navigation completed or to capture the final URL after redirects."""
        return handlers["page_get_url"](session_id, tab_id)

    @mcp.tool(name="page_get_html")
    def page_get_html(session_id: str | None = None, tab_id: str | None = None) -> dict[str, Any]:
        """Return the full HTML source of the current page. Use this when you need the raw markup for parsing, scraping, or inspecting element structure."""
        return handlers["page_get_html"](session_id, tab_id)

    @mcp.tool(name="page_get_text")
    def page_get_text(session_id: str | None = None, tab_id: str | None = None) -> dict[str, Any]:
        """Return the visible text content of the current page, stripped of HTML tags. Prefer this over page_get_html when you only need readable text, not markup."""
        return handlers["page_get_text"](session_id, tab_id)

    @mcp.tool(name="page_screenshot")
    def page_screenshot(
        session_id: str | None = None,
        tab_id: str | None = None,
        output_path: str = "screenshots",
        file_name: str = "page.png",
        full_page: bool = False,
    ) -> dict[str, Any]:
        """Capture a screenshot of the current page and save it under download_dir/output_path. output_path must be a relative subpath; absolute paths or '..' escapes are rejected."""
        return handlers["page_screenshot"](session_id, tab_id, output_path, file_name, full_page)

    @mcp.tool(name="element_find")
    def element_find(selector: str, session_id: str | None = None, tab_id: str | None = None) -> dict[str, Any]:
        """Find a DOM element using a CSS selector and return its tag, text, attributes, and position. Use this to inspect an element before deciding whether to click or type into it."""
        return handlers["element_find"](selector, session_id, tab_id)

    @mcp.tool(name="element_click")
    def element_click(selector: str, session_id: str | None = None, tab_id: str | None = None) -> dict[str, Any]:
        """Click the first element matching the given CSS selector. Use wait_for_element first if the element may not be present yet."""
        return handlers["element_click"](selector, session_id, tab_id)

    @mcp.tool(name="element_type")
    def element_type(
        selector: str,
        text: str,
        session_id: str | None = None,
        tab_id: str | None = None,
        clear: bool = False,
    ) -> dict[str, Any]:
        """Type text into the input or textarea element matching the CSS selector. Set clear=True to erase existing content before typing; defaults to appending."""
        return handlers["element_type"](selector, text, session_id, tab_id, clear)

    @mcp.tool(name="wait_for_element")
    def wait_for_element(
        selector: str,
        session_id: str | None = None,
        tab_id: str | None = None,
        timeout_s: float = 10.0,
    ) -> dict[str, Any]:
        """Wait up to timeout_s seconds for an element matching the CSS selector to appear in the DOM. timeout_s must be between 0 and safety.max_wait_time_s."""
        return handlers["wait_for_element"](selector, session_id, tab_id, timeout_s)

    @mcp.tool(name="wait_time")
    def wait_time(seconds: float, session_id: str | None = None, tab_id: str | None = None) -> dict[str, Any]:
        """Pause execution for a fixed number of seconds. seconds must be between 0 and safety.max_wait_time_s. Prefer wait_for_element when possible."""
        return handlers["wait_time"](seconds, session_id, tab_id)
