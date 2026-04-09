from __future__ import annotations

import time
from pathlib import Path

from drissionpage_mcp.adapters.drission_page import DrissionPageAdapter
from drissionpage_mcp.models import ToolResult
from drissionpage_mcp.services.browser_session import BrowserSession


class PageService:
    def _page(
        self,
        session: BrowserSession,
        tab_id: str | None = None,
    ) -> DrissionPageAdapter:
        return session.adapter.get_page(tab_id)

    def _result(
        self,
        start: float,
        message: str,
        session: BrowserSession,
        *,
        tab_id: str | None = None,
        url: str | None = None,
        **data: object,
    ) -> ToolResult:
        return ToolResult(
            ok=True,
            message=message,
            session_id=session.session_id,
            tab_id=tab_id or session.adapter.current_tab_id(),
            url=url,
            elapsed_ms=int((time.perf_counter() - start) * 1000),
            data=data,
        )

    def navigate(self, session: BrowserSession, url: str, tab_id: str | None = None) -> ToolResult:
        start = time.perf_counter()
        page = self._page(session, tab_id)
        page.navigate(url)
        return self._result(
            start,
            "Navigated successfully.",
            session,
            tab_id=tab_id,
            url=page.get_url(),
        )

    def refresh(self, session: BrowserSession, tab_id: str | None = None) -> ToolResult:
        start = time.perf_counter()
        self._page(session, tab_id).refresh()
        return self._result(start, "Page refreshed.", session, tab_id=tab_id)

    def go_back(self, session: BrowserSession, tab_id: str | None = None) -> ToolResult:
        start = time.perf_counter()
        self._page(session, tab_id).go_back()
        return self._result(start, "Navigated back.", session, tab_id=tab_id)

    def go_forward(self, session: BrowserSession, tab_id: str | None = None) -> ToolResult:
        start = time.perf_counter()
        self._page(session, tab_id).go_forward()
        return self._result(start, "Navigated forward.", session, tab_id=tab_id)

    def get_url(self, session: BrowserSession, tab_id: str | None = None) -> ToolResult:
        start = time.perf_counter()
        url = self._page(session, tab_id).get_url()
        return self._result(start, "Fetched current URL.", session, tab_id=tab_id, url=url)

    def get_html(self, session: BrowserSession, tab_id: str | None = None) -> ToolResult:
        start = time.perf_counter()
        html = self._page(session, tab_id).get_html()
        return self._result(start, "Fetched page HTML.", session, tab_id=tab_id, html=html)

    def get_text(self, session: BrowserSession, tab_id: str | None = None) -> ToolResult:
        start = time.perf_counter()
        text = self._page(session, tab_id).get_text()
        return self._result(start, "Fetched page text.", session, tab_id=tab_id, text=text)

    def screenshot(
        self,
        session: BrowserSession,
        tab_id: str | None = None,
        *,
        output_path: str = "screenshots",
        file_name: str = "page.png",
        full_page: bool = False,
    ) -> ToolResult:
        start = time.perf_counter()
        Path(output_path).mkdir(parents=True, exist_ok=True)
        path = self._page(session, tab_id).screenshot(output_path, file_name, full_page)
        return self._result(start, "Saved screenshot.", session, tab_id=tab_id, screenshot_path=path)

    def find(self, session: BrowserSession, selector: str, tab_id: str | None = None) -> ToolResult:
        start = time.perf_counter()
        element = self._page(session, tab_id).find_element(selector)
        return self._result(
            start,
            "Found element.",
            session,
            tab_id=tab_id,
            selector=selector,
            text=element.text,
        )

    def click(self, session: BrowserSession, selector: str, tab_id: str | None = None) -> ToolResult:
        start = time.perf_counter()
        self._page(session, tab_id).find_element(selector).click()
        return self._result(start, "Clicked element.", session, tab_id=tab_id, selector=selector)

    def type_text(
        self,
        session: BrowserSession,
        selector: str,
        value: str,
        *,
        clear: bool = False,
        tab_id: str | None = None,
    ) -> ToolResult:
        start = time.perf_counter()
        self._page(session, tab_id).find_element(selector).type_text(value, clear=clear)
        return self._result(
            start,
            "Typed text into element.",
            session,
            tab_id=tab_id,
            selector=selector,
        )

    def wait_for_element(
        self,
        session: BrowserSession,
        selector: str,
        *,
        timeout_s: float,
        tab_id: str | None = None,
    ) -> ToolResult:
        start = time.perf_counter()
        element = self._page(session, tab_id).wait_for_element(selector, timeout_s)
        return self._result(
            start,
            "Element is available.",
            session,
            tab_id=tab_id,
            selector=selector,
            text=element.text,
        )

    def wait_time(self, session: BrowserSession, seconds: float, tab_id: str | None = None) -> ToolResult:
        start = time.perf_counter()
        time.sleep(seconds)
        return self._result(start, "Wait completed.", session, tab_id=tab_id, seconds=seconds)
