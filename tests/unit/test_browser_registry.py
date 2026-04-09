from drissionpage_mcp.config import BrowserConfig
from drissionpage_mcp.adapters.drission_browser import DrissionBrowserAdapter
from drissionpage_mcp.errors import ErrorCode, ToolError
from drissionpage_mcp.services.browser_registry import BrowserRegistry


class FakeAdapter:
    def __init__(self, label: str) -> None:
        self.label = label
        self.closed = False

    def close(self) -> None:
        self.closed = True


def test_registry_creates_default_and_ephemeral_sessions() -> None:
    counter = {"value": 0}

    def factory(mode: str) -> FakeAdapter:
        counter["value"] += 1
        return FakeAdapter(f"{mode}-{counter['value']}")

    registry = BrowserRegistry(factory, BrowserConfig())

    default_session = registry.ensure_default_session()
    ephemeral_session = registry.create_session("ephemeral")

    assert default_session.is_default is True
    assert default_session.mode == "persistent"
    assert ephemeral_session.mode == "ephemeral"


def test_registry_rejects_closing_default_session() -> None:
    registry = BrowserRegistry(lambda mode: FakeAdapter(mode), BrowserConfig())
    registry.ensure_default_session()

    try:
        registry.close_session("default")
    except ToolError as error:
        assert error.code is ErrorCode.UNSUPPORTED_OPERATION
    else:
        raise AssertionError("Expected ToolError when closing default session")


class FakeTab:
    def __init__(self, tab_id: str, title: str, url: str) -> None:
        self.tab_id = tab_id
        self.title = title
        self.url = url


class FakeBrowser:
    def __init__(self) -> None:
        self.latest_tab = FakeTab("tab-1", "Latest", "https://example.com/latest")
        self._tabs = {
            "tab-1": self.latest_tab,
            "tab-2": FakeTab("tab-2", "Other", "https://example.com/other"),
        }

    def get_tab(self, tab_id: str) -> FakeTab:
        return self._tabs[tab_id]

    def get_tabs(self) -> list[FakeTab]:
        return list(self._tabs.values())

    def quit(self) -> None:
        return None


def test_browser_adapter_get_page_returns_functional_wrapper_without_task4_module() -> None:
    adapter = DrissionBrowserAdapter(FakeBrowser(), "ephemeral")

    page = adapter.get_page("tab-2")

    assert page.tab_id == "tab-2"
    assert page.title == "Other"
    assert page.url == "https://example.com/other"
