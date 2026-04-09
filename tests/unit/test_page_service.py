from __future__ import annotations

from drissionpage_mcp.models import ToolResult
from drissionpage_mcp.services.browser_session import BrowserSession
from drissionpage_mcp.services.page_service import PageService


class FakeElement:
    def __init__(self, page: "FakePage") -> None:
        self._page = page

    @property
    def text(self) -> str:
        return self._page.button_text

    def click(self) -> None:
        self._page.result_text = self._page.typed_text

    def clear(self) -> None:
        self._page.typed_text = ""

    def input(self, text: str) -> None:
        self._page.typed_text += text


class FakePage:
    def __init__(self) -> None:
        self.url = "about:blank"
        self.html = "<html><body>Hello</body></html>"
        self.button_text = "Echo"
        self.typed_text = ""
        self.result_text = ""
        self.screenshot_path = ""

    def get(self, url: str) -> None:
        self.url = url

    def refresh(self) -> None:
        return None

    def back(self) -> None:
        return None

    def forward(self) -> None:
        return None

    def ele(self, selector: str):
        if selector in ("#echo", "#name", "#result", "tag:body"):
            return FakeElement(self)
        return None

    def get_screenshot(
        self,
        path: str | None = None,
        name: str | None = None,
        full_page: bool = False,
    ) -> str:
        self.screenshot_path = f"{path}/{name}" if path and name else "memory.png"
        return self.screenshot_path


class FakeAdapter:
    def __init__(self) -> None:
        self.page = FakePage()

    def get_page(self, tab_id: str | None = None) -> FakePage:
        return self.page

    def current_tab_id(self) -> str:
        return "tab-1"


def test_page_service_navigate_and_extract_text() -> None:
    session = BrowserSession("default", "persistent", FakeAdapter(), is_default=True)
    service = PageService()

    result = service.navigate(session, "https://example.com")

    assert isinstance(result, ToolResult)
    assert result.ok is True
    assert result.url == "https://example.com"


def test_page_service_click_and_type() -> None:
    session = BrowserSession("default", "persistent", FakeAdapter(), is_default=True)
    service = PageService()

    type_result = service.type_text(session, "#name", "Codex", clear=True)
    click_result = service.click(session, "#echo")

    assert type_result.ok is True
    assert click_result.ok is True
