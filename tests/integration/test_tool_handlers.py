from __future__ import annotations

from drissionpage_mcp.config import BrowserConfig, SafetyConfig, ServerConfig
from drissionpage_mcp.dependencies import ToolDependencies
from drissionpage_mcp.models import BrowserState, TabInfo
from drissionpage_mcp.policies import PolicyEngine
from drissionpage_mcp.services.browser_registry import BrowserRegistry
from drissionpage_mcp.services.page_service import PageService
from drissionpage_mcp.tools.core import build_core_handlers
from drissionpage_mcp.tools.introspection import build_introspection_handlers


class FakePageAdapter:
    def __init__(self) -> None:
        self.url = "https://example.com"
        self.html = "<html><body>Example</body></html>"

    def navigate(self, url: str) -> None:
        self.url = url

    def refresh(self) -> None:
        return None

    def back(self) -> None:
        return None

    def forward(self) -> None:
        return None

    def get_url(self) -> str:
        return self.url

    def get_html(self) -> str:
        return self.html

    def get_text(self) -> str:
        return "Example"

    def find_element(self, selector: str):
        class Element:
            text = "Example"

            def click(self) -> None:
                return None

            def clear(self) -> None:
                return None

            def input(self, text: str) -> None:
                return None

        return Element()

    def screenshot(
        self,
        path: str | None = None,
        name: str | None = None,
        full_page: bool = False,
    ) -> str:
        return f"{path}/{name}"


class FakeBrowser:
    def __init__(self) -> None:
        self.page = FakePageAdapter()

    def close(self) -> None:
        return None

    def get_page(self, tab_id: str | None = None) -> FakePageAdapter:
        return self.page

    def current_tab_id(self) -> str:
        return "tab-1"

    def state(self, session_id: str) -> BrowserState:
        return BrowserState(
            session_id=session_id,
            mode="persistent",
            current_tab_id="tab-1",
            tabs=[TabInfo(tab_id="tab-1", title="Example", url=self.page.url)],
        )


def build_dependencies() -> ToolDependencies:
    config = ServerConfig(safety=SafetyConfig(), browser=BrowserConfig())
    registry = BrowserRegistry(lambda mode: FakeBrowser(), config.browser)
    registry.ensure_default_session()
    return ToolDependencies(
        config=config,
        policy=PolicyEngine(config.safety),
        registry=registry,
        page_service=PageService(),
    )


def test_core_handler_returns_structured_url_payload() -> None:
    handlers = build_core_handlers(build_dependencies())

    result = handlers["page_get_url"]()

    assert result["ok"] is True
    assert result["url"] == "https://example.com"


def test_introspection_reports_v0_capabilities() -> None:
    handlers = build_introspection_handlers(build_dependencies())

    result = handlers["server_get_capabilities"]()

    assert result["ok"] is True
    assert "page_navigate" in result["tools"]
    assert "server_get_policy" in result["tools"]
    assert "browser_attach" not in result["tools"]
