from __future__ import annotations

import time

from drissionpage_mcp.adapters.drission_element import DrissionElementAdapter
from drissionpage_mcp.errors import ErrorCode, ToolError


class DrissionPageAdapter:
    def __init__(self, page: object) -> None:
        self._page = page

    @property
    def tab_id(self) -> str | None:
        return str(getattr(self._page, "tab_id", "")) or None

    @property
    def title(self) -> str:
        return str(getattr(self._page, "title", ""))

    @property
    def url(self) -> str:
        return self.get_url()

    def navigate(self, url: str) -> None:
        self._page.get(url)

    def refresh(self) -> None:
        self._page.refresh()

    def go_back(self) -> None:
        self._page.back()

    def go_forward(self) -> None:
        self._page.forward()

    def get_url(self) -> str:
        return str(getattr(self._page, "url", ""))

    def get_html(self) -> str:
        return str(getattr(self._page, "html", ""))

    def get_text(self) -> str:
        body = self._page.ele("tag:body")
        return "" if body is None else str(getattr(body, "text", ""))

    def screenshot(
        self,
        path: str | None = None,
        name: str | None = None,
        full_page: bool = False,
    ) -> str:
        return str(self._page.get_screenshot(path=path, name=name, full_page=full_page))

    def find_element(self, selector: str) -> DrissionElementAdapter:
        element = self._page.ele(selector)
        if element is None:
            raise ToolError(
                code=ErrorCode.ELEMENT_NOT_FOUND,
                message=f"No element matched selector: {selector}",
                retryable=True,
                context={"selector": selector},
            )
        return DrissionElementAdapter(element)

    def wait_for_element(self, selector: str, timeout_s: float) -> DrissionElementAdapter:
        deadline = time.monotonic() + timeout_s
        while time.monotonic() < deadline:
            element = self._page.ele(selector)
            if element is not None:
                return DrissionElementAdapter(element)
            time.sleep(0.1)
        raise ToolError(
            code=ErrorCode.ACTION_TIMEOUT,
            message=f"Timed out waiting for selector: {selector}",
            retryable=True,
            context={"selector": selector, "timeout_s": timeout_s},
        )
