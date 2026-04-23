from __future__ import annotations

from pathlib import Path
from typing import Any

import pytest

from drissionpage_mcp.adapters.drission_element import DrissionElementAdapter
from drissionpage_mcp.adapters.drission_page import DrissionPageAdapter
from drissionpage_mcp.errors import ErrorCode, ToolError
from drissionpage_mcp.models import ToolResult
from drissionpage_mcp.services.browser_session import BrowserSession
from drissionpage_mcp.services.page_service import PageService


class FakeElementAdapter:
    def __init__(self, page: "FakePageAdapter") -> None:
        self._page = page

    @property
    def text(self) -> str:
        return self._page.result_text

    def click(self) -> None:
        self._page.result_text = self._page.typed_text

    def clear(self) -> None:
        self._page.typed_text = ""

    def input(self, text: str) -> None:
        self._page.typed_text += text

    def type_text(self, text: str, clear: bool = False) -> None:
        if clear:
            self.clear()
        self.input(text)


class FakePageAdapter:
    def __init__(self) -> None:
        self.url = "about:blank"
        self.html = "<html><body>Hello</body></html>"
        self.typed_text = ""
        self.result_text = ""
        self.screenshot_path = ""

    def navigate(self, url: str) -> None:
        self.url = "https://example.com/canonical" if url == "https://example.com" else url

    def refresh(self) -> None:
        return None

    def go_back(self) -> None:
        return None

    def go_forward(self) -> None:
        return None

    def get_url(self) -> str:
        return self.url

    def get_html(self) -> str:
        return self.html

    def get_text(self) -> str:
        return "Hello"

    def screenshot(
        self,
        path: str | None = None,
        name: str | None = None,
        full_page: bool = False,
    ) -> str:
        self.screenshot_path = f"{path}/{name}" if path and name else "memory.png"
        return self.screenshot_path

    def find_element(self, selector: str) -> FakeElementAdapter:
        if selector not in {"#echo", "#name", "#result"}:
            raise ToolError(
                code=ErrorCode.ELEMENT_NOT_FOUND,
                message=f"No element matched selector: {selector}",
                retryable=True,
                context={"selector": selector},
            )
        return FakeElementAdapter(self)

    def wait_for_element(self, selector: str, timeout_s: float) -> FakeElementAdapter:
        if selector != "#echo":
            raise ToolError(
                code=ErrorCode.ACTION_TIMEOUT,
                message=f"Timed out waiting for selector: {selector}",
                retryable=True,
                context={"selector": selector, "timeout_s": timeout_s},
            )
        return FakeElementAdapter(self)


class FalseyMissingElement:
    def __bool__(self) -> bool:
        return False

    @property
    def text(self) -> str:
        raise RuntimeError("missing element text should not be accessed")


class FakeRawPage:
    def __init__(self, elements: dict[str, list[Any]]) -> None:
        self._elements = {selector: list(values) for selector, values in elements.items()}
        self.calls: list[tuple[str, float | None]] = []
        self.url = "about:blank"
        self.html = "<html><body>Hello</body></html>"

    def get(self, url: str) -> None:
        self.url = url

    def refresh(self) -> None:
        return None

    def back(self) -> None:
        return None

    def forward(self) -> None:
        return None

    def ele(self, selector: str, timeout: float | None = None):
        self.calls.append((selector, timeout))
        values = self._elements.get(selector, [])
        if not values:
            return None
        if len(values) == 1:
            return values[0]
        return values.pop(0)

    def get_screenshot(
        self,
        path: str | None = None,
        name: str | None = None,
        full_page: bool = False,
    ) -> str:
        return f"{path}/{name}" if path and name else "memory.png"


class FakeBrowserAdapter:
    def __init__(self, page: object) -> None:
        self.page = page

    def get_page(self, tab_id: str | None = None) -> object:
        return self.page

    def current_tab_id(self) -> str:
        return "tab-1"


class BrokenRawPage(FakeRawPage):
    def __init__(self) -> None:
        super().__init__({})

    def get(self, url: str) -> None:
        raise RuntimeError("navigation exploded")

    def get_screenshot(
        self,
        path: str | None = None,
        name: str | None = None,
        full_page: bool = False,
    ) -> str:
        raise RuntimeError("screenshot exploded")

    def refresh(self) -> None:
        raise RuntimeError("refresh exploded")

    def back(self) -> None:
        raise RuntimeError("back exploded")

    def forward(self) -> None:
        raise RuntimeError("forward exploded")


class BrokenLookupPage(FakeRawPage):
    def __init__(self) -> None:
        super().__init__({})

    def ele(self, selector: str, timeout: float | None = None):
        raise RuntimeError(f"lookup exploded for {selector}")


class BrokenRawElement:
    @property
    def text(self) -> str:
        return ""

    def click(self) -> None:
        raise RuntimeError("click exploded")

    def clear(self) -> None:
        return None

    def input(self, text: str) -> None:
        raise RuntimeError("type exploded")


class BrokenReadElement:
    @property
    def text(self) -> str:
        raise RuntimeError("text exploded")


def test_page_service_navigate_reports_actual_url_and_metadata() -> None:
    session = BrowserSession("default", "persistent", FakeBrowserAdapter(FakePageAdapter()), is_default=True)
    service = PageService(".")

    result = service.navigate(session, "https://example.com")

    assert isinstance(result, ToolResult)
    assert result.ok is True
    assert result.url == "https://example.com/canonical"
    assert result.session_id == "default"
    assert result.tab_id == "tab-1"
    assert result.message == "Navigated successfully."


def test_page_service_click_and_type_include_payload_fields() -> None:
    session = BrowserSession("default", "persistent", FakeBrowserAdapter(FakePageAdapter()), is_default=True)
    service = PageService(".")

    type_result = service.type_text(session, "#name", "Codex", clear=True)
    click_result = service.click(session, "#echo")
    find_result = service.find(session, "#result")

    assert type_result.ok is True
    assert type_result.data["selector"] == "#name"
    assert click_result.ok is True
    assert click_result.data["selector"] == "#echo"
    assert find_result.ok is True
    assert find_result.data["selector"] == "#result"
    assert find_result.data["text"] == "Codex"


def test_page_service_get_text_returns_text_payload() -> None:
    session = BrowserSession("default", "persistent", FakeBrowserAdapter(FakePageAdapter()), is_default=True)
    service = PageService(".")

    result = service.get_text(session)

    assert result.ok is True
    assert result.data["text"] == "Hello"
    assert result.message == "Fetched page text."


def test_page_service_missing_selector_raises_structured_tool_error() -> None:
    session = BrowserSession("default", "persistent", FakeBrowserAdapter(FakePageAdapter()), is_default=True)
    service = PageService(".")

    with pytest.raises(ToolError) as error_info:
        service.find(session, "#missing")

    assert error_info.value.code == ErrorCode.ELEMENT_NOT_FOUND
    assert error_info.value.context["selector"] == "#missing"


def test_drission_page_adapter_find_element_treats_falsey_none_element_as_missing() -> None:
    page = FakeRawPage({"#missing": [FalseyMissingElement()]})
    adapter = DrissionPageAdapter(page)

    with pytest.raises(ToolError) as error_info:
        adapter.find_element("#missing")

    assert error_info.value.code == ErrorCode.ELEMENT_NOT_FOUND
    assert error_info.value.context["selector"] == "#missing"


def test_drission_page_adapter_lookup_wraps_raw_lookup_errors() -> None:
    adapter = DrissionPageAdapter(BrokenLookupPage())

    with pytest.raises(ToolError) as error_info:
        adapter.find_element("#boom")

    assert error_info.value.code == ErrorCode.ELEMENT_NOT_FOUND
    assert error_info.value.context["selector"] == "#boom"


def test_drission_page_adapter_wraps_navigation_errors() -> None:
    adapter = DrissionPageAdapter(BrokenRawPage())

    with pytest.raises(ToolError) as error_info:
        adapter.navigate("https://example.com")

    assert error_info.value.code == ErrorCode.NAVIGATION_FAILED
    assert error_info.value.context["url"] == "https://example.com"


def test_drission_page_adapter_wraps_screenshot_errors() -> None:
    adapter = DrissionPageAdapter(BrokenRawPage())

    with pytest.raises(ToolError) as error_info:
        adapter.screenshot("shots", "page.png", False)

    assert error_info.value.code == ErrorCode.ACTION_TIMEOUT
    assert error_info.value.context["path"] == "shots"
    assert error_info.value.context["name"] == "page.png"


def test_drission_page_adapter_wraps_refresh_errors() -> None:
    adapter = DrissionPageAdapter(BrokenRawPage())

    with pytest.raises(ToolError) as error_info:
        adapter.refresh()

    assert error_info.value.code == ErrorCode.NAVIGATION_FAILED
    assert error_info.value.context["action"] == "refresh"


def test_drission_page_adapter_wraps_back_errors() -> None:
    adapter = DrissionPageAdapter(BrokenRawPage())

    with pytest.raises(ToolError) as error_info:
        adapter.go_back()

    assert error_info.value.code == ErrorCode.NAVIGATION_FAILED
    assert error_info.value.context["action"] == "back"


def test_drission_page_adapter_wraps_forward_errors() -> None:
    adapter = DrissionPageAdapter(BrokenRawPage())

    with pytest.raises(ToolError) as error_info:
        adapter.go_forward()

    assert error_info.value.code == ErrorCode.NAVIGATION_FAILED
    assert error_info.value.context["action"] == "forward"


def test_drission_page_adapter_get_text_treats_falsey_body_as_missing() -> None:
    page = FakeRawPage({"tag:body": [FalseyMissingElement()]})
    adapter = DrissionPageAdapter(page)

    with pytest.raises(ToolError) as error_info:
        adapter.get_text()

    assert error_info.value.code == ErrorCode.ELEMENT_NOT_FOUND
    assert error_info.value.context["selector"] == "tag:body"


def test_drission_page_adapter_wait_for_element_checks_once_at_zero_timeout() -> None:
    page = FakeRawPage({"#echo": [FakeElementAdapter(FakePageAdapter())]})
    adapter = DrissionPageAdapter(page)

    element = adapter.wait_for_element("#echo", timeout_s=0)

    assert element.text == ""
    assert page.calls == [("#echo", 0)]


def test_drission_page_adapter_wait_for_element_times_out_with_zero_timeout_after_one_check() -> None:
    page = FakeRawPage({"#missing": [FalseyMissingElement()]})
    adapter = DrissionPageAdapter(page)

    with pytest.raises(ToolError) as error_info:
        adapter.wait_for_element("#missing", timeout_s=0)

    assert error_info.value.code == ErrorCode.ACTION_TIMEOUT
    assert error_info.value.context["selector"] == "#missing"
    assert page.calls == [("#missing", 0)]


def test_drission_element_adapter_wraps_click_errors() -> None:
    adapter = DrissionElementAdapter(BrokenRawElement())

    with pytest.raises(ToolError) as error_info:
        adapter.click()

    assert error_info.value.code == ErrorCode.ACTION_TIMEOUT
    assert error_info.value.context["action"] == "click"


def test_drission_element_adapter_wraps_text_read_errors() -> None:
    adapter = DrissionElementAdapter(BrokenReadElement())

    with pytest.raises(ToolError) as error_info:
        _ = adapter.text

    assert error_info.value.code == ErrorCode.ACTION_TIMEOUT
    assert error_info.value.context["action"] == "read_text"


def test_drission_element_adapter_wraps_type_errors() -> None:
    adapter = DrissionElementAdapter(BrokenRawElement())

    with pytest.raises(ToolError) as error_info:
        adapter.type_text("Codex", clear=False)

    assert error_info.value.code == ErrorCode.ACTION_TIMEOUT
    assert error_info.value.context["action"] == "type_text"
    assert error_info.value.context["clear"] is False


def test_page_service_screenshot_writes_under_download_dir(tmp_path: Path) -> None:
    session = BrowserSession("default", "persistent", FakeBrowserAdapter(FakePageAdapter()), is_default=True)
    service = PageService(tmp_path)

    result = service.screenshot(session, output_path="shots", file_name="page.png")

    assert result.ok is True
    expected_dir = (tmp_path / "shots").resolve()
    assert expected_dir.is_dir()
    assert result.data["screenshot_path"] == f"{expected_dir}/page.png"


def test_page_service_screenshot_rejects_absolute_output_path(tmp_path: Path) -> None:
    session = BrowserSession("default", "persistent", FakeBrowserAdapter(FakePageAdapter()), is_default=True)
    service = PageService(tmp_path)

    with pytest.raises(ToolError) as error_info:
        service.screenshot(session, output_path=str(tmp_path / "escape"))

    assert error_info.value.code is ErrorCode.INVALID_ARGUMENT


def test_page_service_screenshot_rejects_parent_escape(tmp_path: Path) -> None:
    session = BrowserSession("default", "persistent", FakeBrowserAdapter(FakePageAdapter()), is_default=True)
    service = PageService(tmp_path)

    with pytest.raises(ToolError) as error_info:
        service.screenshot(session, output_path="../outside")

    assert error_info.value.code is ErrorCode.INVALID_ARGUMENT


def test_page_service_screenshot_rejects_path_separator_in_file_name(tmp_path: Path) -> None:
    session = BrowserSession("default", "persistent", FakeBrowserAdapter(FakePageAdapter()), is_default=True)
    service = PageService(tmp_path)

    with pytest.raises(ToolError) as error_info:
        service.screenshot(session, output_path="shots", file_name="../escape.png")

    assert error_info.value.code is ErrorCode.INVALID_ARGUMENT
    assert error_info.value.context == {"file_name": "../escape.png"}


def test_page_service_screenshot_rejects_empty_file_name(tmp_path: Path) -> None:
    session = BrowserSession("default", "persistent", FakeBrowserAdapter(FakePageAdapter()), is_default=True)
    service = PageService(tmp_path)

    with pytest.raises(ToolError) as error_info:
        service.screenshot(session, output_path="shots", file_name="")

    assert error_info.value.code is ErrorCode.INVALID_ARGUMENT


def test_drission_page_adapter_wait_for_element_delegates_timeout_to_lookup() -> None:
    page = FakeRawPage({"#echo": [FakeElementAdapter(FakePageAdapter())]})
    adapter = DrissionPageAdapter(page)

    adapter.wait_for_element("#echo", timeout_s=3.5)

    assert page.calls == [("#echo", 3.5)]


def test_drission_page_adapter_wait_for_element_clamps_negative_timeout() -> None:
    page = FakeRawPage({"#echo": [FakeElementAdapter(FakePageAdapter())]})
    adapter = DrissionPageAdapter(page)

    adapter.wait_for_element("#echo", timeout_s=-1)

    assert page.calls == [("#echo", 0)]
