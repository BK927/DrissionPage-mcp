import pytest

from drissionpage_mcp.config import BrowserConfig
from drissionpage_mcp.adapters.drission_browser import DrissionBrowserAdapter
from drissionpage_mcp.config import SafetyConfig
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


def test_registry_raises_for_missing_session_lookup() -> None:
    registry = BrowserRegistry(lambda mode: FakeAdapter(mode), BrowserConfig())

    with pytest.raises(ToolError) as error_info:
        registry.get_session("missing")

    assert error_info.value.code is ErrorCode.SESSION_NOT_FOUND


def test_registry_close_session_closes_ephemeral_and_removes_it() -> None:
    registry = BrowserRegistry(lambda mode: FakeAdapter(mode), BrowserConfig())
    session = registry.create_session("ephemeral")

    registry.close_session(session.session_id)

    assert session.adapter.closed is True
    with pytest.raises(ToolError) as error_info:
        registry.get_session(session.session_id)
    assert error_info.value.code is ErrorCode.SESSION_NOT_FOUND


def test_registry_all_sessions_creates_default_when_persistent_startup_enabled() -> None:
    registry = BrowserRegistry(lambda mode: FakeAdapter(mode), BrowserConfig())

    sessions = registry.all_sessions()

    assert len(sessions) == 1
    assert sessions[0].session_id == "default"
    assert sessions[0].is_default is True


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
    assert hasattr(page, "raw_page") is False


def test_browser_adapter_normalizes_missing_tab_errors() -> None:
    adapter = DrissionBrowserAdapter(FakeBrowser(), "ephemeral")

    with pytest.raises(ToolError) as error_info:
        adapter.get_page("missing")

    assert error_info.value.code is ErrorCode.TAB_NOT_FOUND
    assert error_info.value.context == {"tab_id": "missing"}


class FakeChromiumOptions:
    instances: list["FakeChromiumOptions"] = []

    def __init__(self, read_file: bool = True) -> None:
        self.read_file = read_file
        self.browser_path: str | None = None
        self.download_path: str | None = None
        self.headless_calls: list[bool] = []
        self.auto_port_calls: list[tuple[bool, object]] = []
        self.local_port: int | None = None
        FakeChromiumOptions.instances.append(self)

    def set_browser_path(self, browser_path: str) -> None:
        self.browser_path = browser_path

    def set_download_path(self, download_path: str) -> None:
        self.download_path = download_path

    def headless(self, on_off: bool) -> None:
        self.headless_calls.append(on_off)

    def auto_port(self, on_off: bool = True, scope: object = None) -> None:
        self.auto_port_calls.append((on_off, scope))


class FakeChromium:
    instances: list["FakeChromium"] = []

    def __init__(self, addr_or_opts: FakeChromiumOptions) -> None:
        self.addr_or_opts = addr_or_opts
        FakeChromium.instances.append(self)

    def quit(self) -> None:
        return None


def test_browser_adapter_launch_enables_session_isolation(monkeypatch: pytest.MonkeyPatch) -> None:
    FakeChromiumOptions.instances.clear()
    FakeChromium.instances.clear()
    monkeypatch.setattr(
        "drissionpage_mcp.adapters.drission_browser.ChromiumOptions",
        FakeChromiumOptions,
    )
    monkeypatch.setattr(
        "drissionpage_mcp.adapters.drission_browser.Chromium",
        FakeChromium,
    )

    adapter = DrissionBrowserAdapter.launch(
        BrowserConfig(headless=True, browser_path="C:/Chrome/chrome.exe"),
        SafetyConfig(download_dir="./downloads"),
        "ephemeral",
    )

    options = FakeChromiumOptions.instances[0]
    assert options.read_file is False
    assert options.browser_path == "C:/Chrome/chrome.exe"
    assert options.download_path == "./downloads"
    assert options.headless_calls == [True]
    assert options.auto_port_calls == [(True, None)]
    assert FakeChromium.instances[0].addr_or_opts is options
    assert adapter._browser is FakeChromium.instances[0]
