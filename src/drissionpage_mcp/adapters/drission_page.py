from __future__ import annotations

import time

from drissionpage_mcp.adapters.drission_element import DrissionElementAdapter
from drissionpage_mcp.errors import ErrorCode, ToolError


class DrissionPageAdapter:
    def __init__(self, page: object) -> None:
        self._page = page

    def _lookup(self, selector: str, *, timeout: float = 0) -> object | None:
        try:
            element = self._page.ele(selector, timeout=timeout)
        except ToolError:
            raise
        except Exception as error:
            raise ToolError(
                code=ErrorCode.ELEMENT_NOT_FOUND,
                message=f"Unable to resolve selector '{selector}': {error}",
                retryable=True,
                context={"selector": selector, "timeout_s": timeout},
            ) from error
        return element if element else None

    def _navigation_failed(self, action: str, error: Exception) -> ToolError:
        return ToolError(
            code=ErrorCode.NAVIGATION_FAILED,
            message=f"Unable to {action} page: {error}",
            retryable=True,
            context={"action": action},
        )

    def _element_not_found(self, selector: str) -> ToolError:
        return ToolError(
            code=ErrorCode.ELEMENT_NOT_FOUND,
            message=f"No element matched selector: {selector}",
            retryable=True,
            context={"selector": selector},
        )

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
        try:
            self._page.get(url)
        except ToolError:
            raise
        except Exception as error:
            raise ToolError(
                code=ErrorCode.NAVIGATION_FAILED,
                message=f"Unable to navigate to '{url}': {error}",
                retryable=True,
                context={"url": url},
            ) from error

    def refresh(self) -> None:
        try:
            self._page.refresh()
        except ToolError:
            raise
        except Exception as error:
            raise self._navigation_failed("refresh", error) from error

    def go_back(self) -> None:
        try:
            self._page.back()
        except ToolError:
            raise
        except Exception as error:
            raise self._navigation_failed("back", error) from error

    def go_forward(self) -> None:
        try:
            self._page.forward()
        except ToolError:
            raise
        except Exception as error:
            raise self._navigation_failed("forward", error) from error

    def get_url(self) -> str:
        return str(getattr(self._page, "url", ""))

    def get_html(self) -> str:
        return str(getattr(self._page, "html", ""))

    def get_text(self) -> str:
        return self.find_element("tag:body").text

    def screenshot(
        self,
        path: str | None = None,
        name: str | None = None,
        full_page: bool = False,
    ) -> str:
        try:
            return str(self._page.get_screenshot(path=path, name=name, full_page=full_page))
        except ToolError:
            raise
        except Exception as error:
            raise ToolError(
                code=ErrorCode.ACTION_TIMEOUT,
                message=f"Unable to capture screenshot: {error}",
                retryable=True,
                context={"action": "screenshot", "path": path, "name": name, "full_page": full_page},
            ) from error

    def find_element(self, selector: str) -> DrissionElementAdapter:
        element = self._lookup(selector)
        if element is None:
            raise self._element_not_found(selector)
        return DrissionElementAdapter(element)

    def wait_for_element(self, selector: str, timeout_s: float) -> DrissionElementAdapter:
        deadline = time.monotonic() + max(timeout_s, 0)
        while True:
            element = self._lookup(selector, timeout=0)
            if element is not None:
                return DrissionElementAdapter(element)
            if time.monotonic() >= deadline:
                break
            time.sleep(min(0.1, max(0.0, deadline - time.monotonic())))
        raise ToolError(
            code=ErrorCode.ACTION_TIMEOUT,
            message=f"Timed out waiting for selector: {selector}",
            retryable=True,
            context={"selector": selector, "timeout_s": timeout_s},
        )
