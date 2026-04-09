# DrissionPage MCP v0 Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build the v0 release of a `stdio`-based DrissionPage MCP server with a default persistent session, optional ephemeral sessions, safe-by-default policy checks, core browser tools, introspection tools, and deterministic tests.

**Architecture:** The implementation keeps MCP registration thin and pushes behavior into focused services and adapters. `FastMCP` owns transport and tool registration, `BrowserRegistry` manages session lifecycle, `PageService` coordinates read/write browser actions, and a small policy layer blocks dangerous behavior before DrissionPage is touched.

**Tech Stack:** Python 3.11+, `mcp[cli]`, `DrissionPage`, `pytest`, `pytest-asyncio`, `ruff`

---

## Scope

This plan implements `v0` from the approved spec only.

Included in this plan:

- `stdio` transport
- one default persistent session
- optional ephemeral sessions
- core tools
- introspection tools
- structured results and errors
- safe-mode defaults
- unit, integration, and local E2E tests

Explicitly deferred to later plans:

- `browser_attach`
- `browser_tabs`
- cookie and storage export/import
- `run_js`
- DOM snapshotting
- `Streamable HTTP`

## File Structure

Create these files and keep their responsibilities narrow:

- `pyproject.toml`: packaging, dependencies, pytest config, CLI entry point
- `.gitignore`: local cache, environment, screenshot, and download exclusions
- `README.md`: install, run, config, safety, and testing instructions
- `src/drissionpage_mcp/__init__.py`: package version
- `src/drissionpage_mcp/config.py`: typed config objects and TOML loading
- `src/drissionpage_mcp/errors.py`: normalized tool error codes and exception type
- `src/drissionpage_mcp/models.py`: typed result payloads and browser/session models
- `src/drissionpage_mcp/policies.py`: safe-mode checks and domain gating
- `src/drissionpage_mcp/dependencies.py`: dependency assembly for the server
- `src/drissionpage_mcp/server.py`: `FastMCP` server factory and CLI entry point
- `src/drissionpage_mcp/adapters/drission_browser.py`: browser launch and tab selection wrapper
- `src/drissionpage_mcp/adapters/drission_page.py`: page-level navigation, extraction, and screenshot wrapper
- `src/drissionpage_mcp/adapters/drission_element.py`: element-level click/type/text wrapper
- `src/drissionpage_mcp/services/browser_session.py`: one session record
- `src/drissionpage_mcp/services/browser_registry.py`: session create/get/close lifecycle
- `src/drissionpage_mcp/services/page_service.py`: policy-aware browser actions returning structured results
- `src/drissionpage_mcp/tools/core.py`: v0 core tool handlers and MCP registration
- `src/drissionpage_mcp/tools/introspection.py`: capability, policy, and state tools
- `tests/unit/test_config.py`: config default coverage
- `tests/unit/test_policies.py`: safety policy coverage
- `tests/unit/test_browser_registry.py`: session lifecycle coverage
- `tests/unit/test_page_service.py`: page service read/write coverage with fakes
- `tests/integration/test_tool_handlers.py`: tool-layer behavior coverage
- `tests/e2e/conftest.py`: local static site server fixture
- `tests/e2e/site/index.html`: deterministic browser fixture page
- `tests/e2e/test_local_browser_flow.py`: real browser happy-path flow

## Task 1: Bootstrap The Package And Config Loader

**Files:**
- Create: `.gitignore`
- Create: `pyproject.toml`
- Create: `README.md`
- Create: `src/drissionpage_mcp/__init__.py`
- Create: `src/drissionpage_mcp/config.py`
- Create: `src/drissionpage_mcp/server.py`
- Create: `tests/unit/test_config.py`

- [ ] **Step 1: Write the failing test**

```python
# tests/unit/test_config.py
from drissionpage_mcp.config import load_config


def test_load_config_returns_safe_defaults() -> None:
    config = load_config()

    assert config.server_name == "DrissionPage MCP"
    assert config.safety.mode == "safe"
    assert config.safety.allow_run_js is False
    assert config.safety.allow_browser_attach is False
    assert config.browser.persistent_on_startup is True
    assert config.browser.headless is False
```

- [ ] **Step 2: Run test to verify it fails**

Run: `uv run pytest tests/unit/test_config.py -v`
Expected: FAIL with `ModuleNotFoundError: No module named 'drissionpage_mcp'`

- [ ] **Step 3: Write minimal implementation**

```toml
# pyproject.toml
[build-system]
requires = ["hatchling"]
build-backend = "hatchling.build"

[project]
name = "drissionpage-mcp"
version = "0.1.0"
description = "General-purpose MCP server built on DrissionPage"
readme = "README.md"
requires-python = ">=3.11"
dependencies = [
  "mcp[cli]>=1.9.4,<2",
  "DrissionPage>=4.1.1.2,<5",
]

[project.optional-dependencies]
dev = [
  "pytest>=8.3,<9",
  "pytest-asyncio>=0.24,<1",
  "ruff>=0.11,<1",
]

[project.scripts]
drissionpage-mcp = "drissionpage_mcp.server:main"

[tool.pytest.ini_options]
pythonpath = ["src"]
testpaths = ["tests"]
asyncio_mode = "auto"

[tool.ruff]
line-length = 100
target-version = "py311"
```

```gitignore
# .gitignore
.pytest_cache/
.ruff_cache/
.venv/
__pycache__/
*.pyc
downloads/
screenshots/
```

````markdown
# README.md
# DrissionPage MCP

`DrissionPage MCP` is a general-purpose MCP server for local LLM agents that need browser automation over `stdio`.

## Install

```bash
uv sync --extra dev
```

## Run

```bash
uv run drissionpage-mcp
```

## Notes

- v0 ships only the safe core browser tools and introspection tools.
- Dangerous capabilities such as browser attach and arbitrary JavaScript execution are intentionally deferred.
- Review the upstream `DrissionPage` usage terms before distributing this project or using it commercially.
````

```python
# src/drissionpage_mcp/__init__.py
__version__ = "0.1.0"
```

```python
# src/drissionpage_mcp/config.py
from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Any
import tomllib


@dataclass(frozen=True, slots=True)
class SafetyConfig:
    mode: str = "safe"
    allow_run_js: bool = False
    allow_browser_attach: bool = False
    allow_file_upload: bool = False
    allow_download: bool = True
    allowed_domains: tuple[str, ...] = ()
    download_dir: str = "./downloads"
    default_timeout_ms: int = 10_000


@dataclass(frozen=True, slots=True)
class BrowserConfig:
    persistent_on_startup: bool = True
    headless: bool = False
    browser_path: str | None = None


@dataclass(frozen=True, slots=True)
class ServerConfig:
    server_name: str = "DrissionPage MCP"
    safety: SafetyConfig = field(default_factory=SafetyConfig)
    browser: BrowserConfig = field(default_factory=BrowserConfig)


def _tuple_from_value(value: Any) -> tuple[str, ...]:
    if value is None:
        return ()
    if isinstance(value, (list, tuple)):
        return tuple(str(item) for item in value)
    return (str(value),)


def load_config(path: str | Path | None = None) -> ServerConfig:
    config_path = Path(path) if path is not None else Path("drissionpage_mcp.toml")
    if not config_path.exists():
        return ServerConfig()

    raw = tomllib.loads(config_path.read_text(encoding="utf-8"))
    safety_raw = raw.get("safety", {})
    browser_raw = raw.get("browser", {})

    safety = SafetyConfig(
        mode=str(safety_raw.get("mode", "safe")),
        allow_run_js=bool(safety_raw.get("allow_run_js", False)),
        allow_browser_attach=bool(safety_raw.get("allow_browser_attach", False)),
        allow_file_upload=bool(safety_raw.get("allow_file_upload", False)),
        allow_download=bool(safety_raw.get("allow_download", True)),
        allowed_domains=_tuple_from_value(safety_raw.get("allowed_domains")),
        download_dir=str(safety_raw.get("download_dir", "./downloads")),
        default_timeout_ms=int(safety_raw.get("default_timeout_ms", 10_000)),
    )
    browser = BrowserConfig(
        persistent_on_startup=bool(browser_raw.get("persistent_on_startup", True)),
        headless=bool(browser_raw.get("headless", False)),
        browser_path=browser_raw.get("browser_path"),
    )
    return ServerConfig(
        server_name=str(raw.get("server_name", "DrissionPage MCP")),
        safety=safety,
        browser=browser,
    )
```

```python
# src/drissionpage_mcp/server.py
from __future__ import annotations

from mcp.server.fastmcp import FastMCP

from drissionpage_mcp.config import load_config


def create_server(config_path: str | None = None) -> FastMCP:
    config = load_config(config_path)
    return FastMCP(
        config.server_name,
        instructions="Use the available tools to automate a local browser safely.",
    )


def main() -> None:
    create_server().run()
```

- [ ] **Step 4: Run test to verify it passes**

Run: `uv run pytest tests/unit/test_config.py -v`
Expected: PASS with `1 passed`

- [ ] **Step 5: Commit**

```bash
git add .gitignore pyproject.toml README.md src/drissionpage_mcp/__init__.py src/drissionpage_mcp/config.py src/drissionpage_mcp/server.py tests/unit/test_config.py
git commit -m "chore: bootstrap drissionpage mcp package"
```

## Task 2: Add Structured Errors, Results, And Policy Checks

**Files:**
- Create: `src/drissionpage_mcp/errors.py`
- Create: `src/drissionpage_mcp/models.py`
- Create: `src/drissionpage_mcp/policies.py`
- Create: `tests/unit/test_policies.py`

- [ ] **Step 1: Write the failing test**

```python
# tests/unit/test_policies.py
import pytest

from drissionpage_mcp.config import SafetyConfig
from drissionpage_mcp.errors import ErrorCode, ToolError
from drissionpage_mcp.policies import PolicyEngine


def test_policy_blocks_run_js_when_disabled() -> None:
    engine = PolicyEngine(SafetyConfig(allow_run_js=False))

    with pytest.raises(ToolError) as caught:
        engine.require_run_js_allowed()

    assert caught.value.code is ErrorCode.POLICY_BLOCKED


def test_policy_rejects_url_outside_allowlist() -> None:
    engine = PolicyEngine(SafetyConfig(allowed_domains=("example.com",)))

    with pytest.raises(ToolError) as caught:
        engine.require_url_allowed("https://openai.com")

    assert caught.value.code is ErrorCode.POLICY_BLOCKED
```

- [ ] **Step 2: Run test to verify it fails**

Run: `uv run pytest tests/unit/test_policies.py -v`
Expected: FAIL with `ModuleNotFoundError` for `drissionpage_mcp.errors` or `drissionpage_mcp.policies`

- [ ] **Step 3: Write minimal implementation**

```python
# src/drissionpage_mcp/errors.py
from __future__ import annotations

from dataclasses import dataclass, field
from enum import StrEnum


class ErrorCode(StrEnum):
    BROWSER_LAUNCH_FAILED = "BROWSER_LAUNCH_FAILED"
    SESSION_NOT_FOUND = "SESSION_NOT_FOUND"
    TAB_NOT_FOUND = "TAB_NOT_FOUND"
    NAVIGATION_FAILED = "NAVIGATION_FAILED"
    ELEMENT_NOT_FOUND = "ELEMENT_NOT_FOUND"
    ACTION_TIMEOUT = "ACTION_TIMEOUT"
    DOWNLOAD_TIMEOUT = "DOWNLOAD_TIMEOUT"
    POLICY_BLOCKED = "POLICY_BLOCKED"
    UNSUPPORTED_OPERATION = "UNSUPPORTED_OPERATION"


@dataclass(slots=True)
class ToolError(Exception):
    code: ErrorCode
    message: str
    retryable: bool = False
    context: dict[str, object] = field(default_factory=dict)

    def __str__(self) -> str:
        return f"{self.code}: {self.message}"
```

```python
# src/drissionpage_mcp/models.py
from __future__ import annotations

from dataclasses import asdict, dataclass, field
from typing import Any, Literal


SessionMode = Literal["persistent", "ephemeral"]


@dataclass(slots=True)
class TabInfo:
    tab_id: str
    title: str
    url: str


@dataclass(slots=True)
class BrowserState:
    session_id: str
    mode: SessionMode
    current_tab_id: str | None
    tabs: list[TabInfo] = field(default_factory=list)


@dataclass(slots=True)
class ToolResult:
    ok: bool
    message: str
    session_id: str | None = None
    tab_id: str | None = None
    url: str | None = None
    elapsed_ms: int | None = None
    data: dict[str, Any] = field(default_factory=dict)
    error_code: str | None = None
    retryable: bool | None = None

    def to_dict(self) -> dict[str, Any]:
        payload = asdict(self)
        extra = payload.pop("data")
        payload.update(extra)
        return {key: value for key, value in payload.items() if value not in (None, {}, [])}
```

```python
# src/drissionpage_mcp/policies.py
from __future__ import annotations

from urllib.parse import urlparse

from drissionpage_mcp.config import SafetyConfig
from drissionpage_mcp.errors import ErrorCode, ToolError


class PolicyEngine:
    def __init__(self, config: SafetyConfig) -> None:
        self._config = config

    def require_run_js_allowed(self) -> None:
        if not self._config.allow_run_js:
            raise ToolError(
                code=ErrorCode.POLICY_BLOCKED,
                message="run_js is disabled in safe mode.",
            )

    def require_browser_attach_allowed(self) -> None:
        if not self._config.allow_browser_attach:
            raise ToolError(
                code=ErrorCode.POLICY_BLOCKED,
                message="browser_attach is disabled in safe mode.",
            )

    def require_url_allowed(self, url: str) -> None:
        if not self._config.allowed_domains:
            return

        hostname = (urlparse(url).hostname or "").lower()
        if hostname in self._config.allowed_domains:
            return

        raise ToolError(
            code=ErrorCode.POLICY_BLOCKED,
            message=f"URL '{url}' is outside the configured allowlist.",
            context={"url": url},
        )
```

- [ ] **Step 4: Run test to verify it passes**

Run: `uv run pytest tests/unit/test_policies.py -v`
Expected: PASS with `2 passed`

- [ ] **Step 5: Commit**

```bash
git add src/drissionpage_mcp/errors.py src/drissionpage_mcp/models.py src/drissionpage_mcp/policies.py tests/unit/test_policies.py
git commit -m "feat: add policy and result primitives"
```

## Task 3: Add Browser Sessions And Registry Lifecycle

**Files:**
- Create: `src/drissionpage_mcp/services/browser_session.py`
- Create: `src/drissionpage_mcp/services/browser_registry.py`
- Create: `src/drissionpage_mcp/adapters/drission_browser.py`
- Create: `tests/unit/test_browser_registry.py`

- [ ] **Step 1: Write the failing test**

```python
# tests/unit/test_browser_registry.py
from drissionpage_mcp.config import BrowserConfig
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
```

- [ ] **Step 2: Run test to verify it fails**

Run: `uv run pytest tests/unit/test_browser_registry.py -v`
Expected: FAIL with `ModuleNotFoundError` for `drissionpage_mcp.services.browser_registry`

- [ ] **Step 3: Write minimal implementation**

```python
# src/drissionpage_mcp/services/browser_session.py
from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from drissionpage_mcp.models import SessionMode


@dataclass(slots=True)
class BrowserSession:
    session_id: str
    mode: SessionMode
    adapter: Any
    is_default: bool = False
```

```python
# src/drissionpage_mcp/services/browser_registry.py
from __future__ import annotations

from collections.abc import Callable
from uuid import uuid4

from drissionpage_mcp.config import BrowserConfig
from drissionpage_mcp.errors import ErrorCode, ToolError
from drissionpage_mcp.services.browser_session import BrowserSession


class BrowserRegistry:
    def __init__(
        self,
        adapter_factory: Callable[[str], object],
        browser_config: BrowserConfig,
    ) -> None:
        self._adapter_factory = adapter_factory
        self._browser_config = browser_config
        self._sessions: dict[str, BrowserSession] = {}

    def ensure_default_session(self) -> BrowserSession:
        if "default" in self._sessions:
            return self._sessions["default"]

        session = BrowserSession(
            session_id="default",
            mode="persistent",
            adapter=self._adapter_factory("persistent"),
            is_default=True,
        )
        self._sessions["default"] = session
        return session

    def create_session(self, mode: str = "ephemeral") -> BrowserSession:
        session_id = f"session-{uuid4().hex[:8]}"
        session = BrowserSession(
            session_id=session_id,
            mode=mode,
            adapter=self._adapter_factory(mode),
            is_default=False,
        )
        self._sessions[session_id] = session
        return session

    def get_session(self, session_id: str | None = None) -> BrowserSession:
        key = session_id or "default"
        if key == "default":
            return self.ensure_default_session()
        if key not in self._sessions:
            raise ToolError(
                code=ErrorCode.SESSION_NOT_FOUND,
                message=f"Session '{key}' does not exist.",
                context={"session_id": key},
            )
        return self._sessions[key]

    def close_session(self, session_id: str) -> None:
        if session_id == "default":
            raise ToolError(
                code=ErrorCode.UNSUPPORTED_OPERATION,
                message="The default session cannot be closed.",
                context={"session_id": session_id},
            )
        session = self.get_session(session_id)
        session.adapter.close()
        del self._sessions[session_id]

    def all_sessions(self) -> list[BrowserSession]:
        if self._browser_config.persistent_on_startup and "default" not in self._sessions:
            self.ensure_default_session()
        return list(self._sessions.values())
```

```python
# src/drissionpage_mcp/adapters/drission_browser.py
from __future__ import annotations

from DrissionPage import Chromium, ChromiumOptions

from drissionpage_mcp.adapters.drission_page import DrissionPageAdapter
from drissionpage_mcp.config import BrowserConfig, SafetyConfig
from drissionpage_mcp.errors import ErrorCode, ToolError
from drissionpage_mcp.models import BrowserState, TabInfo


class DrissionBrowserAdapter:
    def __init__(self, browser: Chromium, mode: str) -> None:
        self._browser = browser
        self._mode = mode

    @classmethod
    def launch(
        cls,
        browser_config: BrowserConfig,
        safety_config: SafetyConfig,
        mode: str,
    ) -> "DrissionBrowserAdapter":
        try:
            options = ChromiumOptions(read_file=False)
            if browser_config.browser_path:
                options.set_browser_path(browser_config.browser_path)
            options.set_download_path(safety_config.download_dir)
            if browser_config.headless:
                options.headless(True)
            browser = Chromium(addr_or_opts=options)
        except Exception as error:  # pragma: no cover
            raise ToolError(
                code=ErrorCode.BROWSER_LAUNCH_FAILED,
                message=f"Unable to start Chromium: {error}",
            ) from error

        return cls(browser, mode)

    def close(self) -> None:
        self._browser.quit()

    def get_page(self, tab_id: str | None = None) -> DrissionPageAdapter:
        tab = self._browser.latest_tab if tab_id is None else self._browser.get_tab(tab_id)
        return DrissionPageAdapter(tab)

    def current_tab_id(self) -> str | None:
        tab = self._browser.latest_tab
        return str(getattr(tab, "tab_id", "")) or None

    def state(self, session_id: str) -> BrowserState:
        tabs = [
            TabInfo(
                tab_id=str(getattr(tab, "tab_id", "")),
                title=str(getattr(tab, "title", "")),
                url=str(getattr(tab, "url", "")),
            )
            for tab in self._browser.get_tabs()
        ]
        return BrowserState(
            session_id=session_id,
            mode=self._mode,
            current_tab_id=self.current_tab_id(),
            tabs=tabs,
        )
```

- [ ] **Step 4: Run test to verify it passes**

Run: `uv run pytest tests/unit/test_browser_registry.py -v`
Expected: PASS with `2 passed`

- [ ] **Step 5: Commit**

```bash
git add src/drissionpage_mcp/services/browser_session.py src/drissionpage_mcp/services/browser_registry.py src/drissionpage_mcp/adapters/drission_browser.py tests/unit/test_browser_registry.py
git commit -m "feat: add browser session lifecycle"
```

## Task 4: Add Page And Element Adapters Plus The Page Service

**Files:**
- Create: `src/drissionpage_mcp/adapters/drission_page.py`
- Create: `src/drissionpage_mcp/adapters/drission_element.py`
- Create: `src/drissionpage_mcp/services/page_service.py`
- Create: `tests/unit/test_page_service.py`

- [ ] **Step 1: Write the failing test**

```python
# tests/unit/test_page_service.py
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

    def get_screenshot(self, path: str | None = None, name: str | None = None, full_page: bool = False) -> str:
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
```

- [ ] **Step 2: Run test to verify it fails**

Run: `uv run pytest tests/unit/test_page_service.py -v`
Expected: FAIL with `ModuleNotFoundError` for `drissionpage_mcp.services.page_service`

- [ ] **Step 3: Write minimal implementation**

```python
# src/drissionpage_mcp/adapters/drission_element.py
from __future__ import annotations


class DrissionElementAdapter:
    def __init__(self, element: object) -> None:
        self._element = element

    @property
    def text(self) -> str:
        return str(getattr(self._element, "text", ""))

    def click(self) -> None:
        self._element.click()

    def type_text(self, value: str, clear: bool = False) -> None:
        if clear and hasattr(self._element, "clear"):
            self._element.clear()
        self._element.input(value)
```

```python
# src/drissionpage_mcp/adapters/drission_page.py
from __future__ import annotations

import time

from drissionpage_mcp.adapters.drission_element import DrissionElementAdapter
from drissionpage_mcp.errors import ErrorCode, ToolError


class DrissionPageAdapter:
    def __init__(self, page: object) -> None:
        self._page = page

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

    def screenshot(self, path: str | None = None, name: str | None = None, full_page: bool = False) -> str:
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
```

```python
# src/drissionpage_mcp/services/page_service.py
from __future__ import annotations

import time
from pathlib import Path

from drissionpage_mcp.models import ToolResult
from drissionpage_mcp.services.browser_session import BrowserSession


class PageService:
    def _page(self, session: BrowserSession, tab_id: str | None = None):
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
        return self._result(start, "Navigated successfully.", session, tab_id=tab_id, url=url)

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
        page = self._page(session, tab_id)
        url = page.get_url()
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
        return self._result(start, "Found element.", session, tab_id=tab_id, selector=selector, text=element.text)

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
        return self._result(start, "Typed text into element.", session, tab_id=tab_id, selector=selector)

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
        return self._result(start, "Element is available.", session, tab_id=tab_id, selector=selector, text=element.text)

    def wait_time(self, session: BrowserSession, seconds: float, tab_id: str | None = None) -> ToolResult:
        start = time.perf_counter()
        time.sleep(seconds)
        return self._result(start, "Wait completed.", session, tab_id=tab_id, seconds=seconds)
```

- [ ] **Step 4: Run test to verify it passes**

Run: `uv run pytest tests/unit/test_page_service.py -v`
Expected: PASS with `2 passed`

- [ ] **Step 5: Commit**

```bash
git add src/drissionpage_mcp/adapters/drission_page.py src/drissionpage_mcp/adapters/drission_element.py src/drissionpage_mcp/services/page_service.py tests/unit/test_page_service.py
git commit -m "feat: add page service and drission adapters"
```

## Task 5: Wire Core MCP Tools And Introspection Tools

**Files:**
- Create: `src/drissionpage_mcp/dependencies.py`
- Create: `src/drissionpage_mcp/tools/core.py`
- Create: `src/drissionpage_mcp/tools/introspection.py`
- Modify: `src/drissionpage_mcp/server.py`
- Create: `tests/integration/test_tool_handlers.py`

- [ ] **Step 1: Write the failing test**

```python
# tests/integration/test_tool_handlers.py
from drissionpage_mcp.config import BrowserConfig, SafetyConfig, ServerConfig
from drissionpage_mcp.dependencies import ToolDependencies
from drissionpage_mcp.models import BrowserState, TabInfo
from drissionpage_mcp.policies import PolicyEngine
from drissionpage_mcp.services.browser_registry import BrowserRegistry
from drissionpage_mcp.services.page_service import PageService
from drissionpage_mcp.tools.core import build_core_handlers
from drissionpage_mcp.tools.introspection import build_introspection_handlers


class FakePage:
    def __init__(self) -> None:
        self.url = "https://example.com"
        self.html = "<html><body>Example</body></html>"

    def get(self, url: str) -> None:
        self.url = url

    def refresh(self) -> None:
        return None

    def back(self) -> None:
        return None

    def forward(self) -> None:
        return None

    def ele(self, selector: str):
        class Element:
            text = "Example"

            def click(self) -> None:
                return None

            def clear(self) -> None:
                return None

            def input(self, text: str) -> None:
                return None

        return Element()

    def get_screenshot(self, path: str | None = None, name: str | None = None, full_page: bool = False) -> str:
        return f"{path}/{name}"


class FakeBrowser:
    def __init__(self) -> None:
        self.page = FakePage()

    def close(self) -> None:
        return None

    def get_page(self, tab_id: str | None = None) -> FakePage:
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
    config = ServerConfig(
        safety=SafetyConfig(),
        browser=BrowserConfig(),
    )
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
```

- [ ] **Step 2: Run test to verify it fails**

Run: `uv run pytest tests/integration/test_tool_handlers.py -v`
Expected: FAIL with `ModuleNotFoundError` for `drissionpage_mcp.dependencies` or `drissionpage_mcp.tools.core`

- [ ] **Step 3: Write minimal implementation**

```python
# src/drissionpage_mcp/dependencies.py
from __future__ import annotations

from dataclasses import dataclass

from drissionpage_mcp.adapters.drission_browser import DrissionBrowserAdapter
from drissionpage_mcp.config import ServerConfig
from drissionpage_mcp.policies import PolicyEngine
from drissionpage_mcp.services.browser_registry import BrowserRegistry
from drissionpage_mcp.services.page_service import PageService


@dataclass(frozen=True, slots=True)
class ToolDependencies:
    config: ServerConfig
    policy: PolicyEngine
    registry: BrowserRegistry
    page_service: PageService


def build_dependencies(config: ServerConfig) -> ToolDependencies:
    policy = PolicyEngine(config.safety)

    def adapter_factory(mode: str) -> DrissionBrowserAdapter:
        return DrissionBrowserAdapter.launch(config.browser, config.safety, mode)

    registry = BrowserRegistry(adapter_factory, config.browser)
    if config.browser.persistent_on_startup:
        registry.ensure_default_session()

    return ToolDependencies(
        config=config,
        policy=policy,
        registry=registry,
        page_service=PageService(),
    )
```

```python
# src/drissionpage_mcp/tools/core.py
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


def _handle_errors(callback: Callable[..., Any], *args: Any, **kwargs: Any) -> dict[str, Any]:
    try:
        result = callback(*args, **kwargs)
        return result.to_dict()
    except ToolError as error:
        return {
            "ok": False,
            "error_code": error.code.value,
            "message": error.message,
            "retryable": error.retryable,
            **error.context,
        }


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
            return {"ok": True, "message": "Closed session.", "session_id": session_id}
        except ToolError as error:
            return {
                "ok": False,
                "error_code": error.code.value,
                "message": error.message,
                "retryable": error.retryable,
                **error.context,
            }

    def page_navigate(url: str, session_id: str | None = None, tab_id: str | None = None) -> dict[str, Any]:
        def action() -> Any:
            deps.policy.require_url_allowed(url)
            session = deps.registry.get_session(session_id)
            return deps.page_service.navigate(session, url, tab_id)

        return _handle_errors(action)

    def page_refresh(session_id: str | None = None, tab_id: str | None = None) -> dict[str, Any]:
        session = deps.registry.get_session(session_id)
        return _handle_errors(deps.page_service.refresh, session, tab_id)

    def page_go_back(session_id: str | None = None, tab_id: str | None = None) -> dict[str, Any]:
        session = deps.registry.get_session(session_id)
        return _handle_errors(deps.page_service.go_back, session, tab_id)

    def page_go_forward(session_id: str | None = None, tab_id: str | None = None) -> dict[str, Any]:
        session = deps.registry.get_session(session_id)
        return _handle_errors(deps.page_service.go_forward, session, tab_id)

    def page_get_url(session_id: str | None = None, tab_id: str | None = None) -> dict[str, Any]:
        session = deps.registry.get_session(session_id)
        return _handle_errors(deps.page_service.get_url, session, tab_id)

    def page_get_html(session_id: str | None = None, tab_id: str | None = None) -> dict[str, Any]:
        session = deps.registry.get_session(session_id)
        return _handle_errors(deps.page_service.get_html, session, tab_id)

    def page_get_text(session_id: str | None = None, tab_id: str | None = None) -> dict[str, Any]:
        session = deps.registry.get_session(session_id)
        return _handle_errors(deps.page_service.get_text, session, tab_id)

    def page_screenshot(
        session_id: str | None = None,
        tab_id: str | None = None,
        output_path: str = "screenshots",
        file_name: str = "page.png",
        full_page: bool = False,
    ) -> dict[str, Any]:
        session = deps.registry.get_session(session_id)
        return _handle_errors(
            deps.page_service.screenshot,
            session,
            tab_id,
            output_path=output_path,
            file_name=file_name,
            full_page=full_page,
        )

    def element_find(selector: str, session_id: str | None = None, tab_id: str | None = None) -> dict[str, Any]:
        session = deps.registry.get_session(session_id)
        return _handle_errors(deps.page_service.find, session, selector, tab_id)

    def element_click(selector: str, session_id: str | None = None, tab_id: str | None = None) -> dict[str, Any]:
        session = deps.registry.get_session(session_id)
        return _handle_errors(deps.page_service.click, session, selector, tab_id)

    def element_type(
        selector: str,
        text: str,
        session_id: str | None = None,
        tab_id: str | None = None,
        clear: bool = False,
    ) -> dict[str, Any]:
        session = deps.registry.get_session(session_id)
        return _handle_errors(deps.page_service.type_text, session, selector, text, clear=clear, tab_id=tab_id)

    def wait_for_element(
        selector: str,
        session_id: str | None = None,
        tab_id: str | None = None,
        timeout_s: float = 10.0,
    ) -> dict[str, Any]:
        session = deps.registry.get_session(session_id)
        return _handle_errors(deps.page_service.wait_for_element, session, selector, timeout_s=timeout_s, tab_id=tab_id)

    def wait_time(seconds: float, session_id: str | None = None, tab_id: str | None = None) -> dict[str, Any]:
        session = deps.registry.get_session(session_id)
        return _handle_errors(deps.page_service.wait_time, session, seconds, tab_id)

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
```

```python
# src/drissionpage_mcp/tools/introspection.py
from __future__ import annotations

from collections.abc import Callable
from typing import Any

from mcp.server.fastmcp import FastMCP

from drissionpage_mcp.dependencies import ToolDependencies
from drissionpage_mcp.tools.core import CORE_TOOL_NAMES


INTROSPECTION_TOOL_NAMES = (
    "server_get_capabilities",
    "server_get_policy",
    "browser_get_state",
)


def build_introspection_handlers(deps: ToolDependencies) -> dict[str, Callable[..., dict[str, Any]]]:
    def server_get_capabilities() -> dict[str, Any]:
        return {
            "ok": True,
            "message": "Capabilities fetched.",
            "tools": list(CORE_TOOL_NAMES + INTROSPECTION_TOOL_NAMES),
            "transport": "stdio",
            "planned_future_tools": [
                "browser_attach",
                "browser_tabs",
                "cookies_export",
                "cookies_import",
                "storage_export",
                "run_js",
                "page_get_dom_snapshot",
            ],
        }

    def server_get_policy() -> dict[str, Any]:
        safety = deps.config.safety
        return {
            "ok": True,
            "message": "Policy fetched.",
            "mode": safety.mode,
            "allow_run_js": safety.allow_run_js,
            "allow_browser_attach": safety.allow_browser_attach,
            "allow_file_upload": safety.allow_file_upload,
            "allow_download": safety.allow_download,
            "allowed_domains": list(safety.allowed_domains),
            "default_timeout_ms": safety.default_timeout_ms,
            "download_dir": safety.download_dir,
        }

    def browser_get_state(session_id: str | None = None) -> dict[str, Any]:
        session = deps.registry.get_session(session_id)
        state = session.adapter.state(session.session_id)
        return {
            "ok": True,
            "message": "Browser state fetched.",
            "session_id": state.session_id,
            "mode": state.mode,
            "current_tab_id": state.current_tab_id,
            "tabs": [
                {"tab_id": tab.tab_id, "title": tab.title, "url": tab.url}
                for tab in state.tabs
            ],
        }

    return {
        "server_get_capabilities": server_get_capabilities,
        "server_get_policy": server_get_policy,
        "browser_get_state": browser_get_state,
    }


def register_introspection_tools(mcp: FastMCP, deps: ToolDependencies) -> None:
    handlers = build_introspection_handlers(deps)

    @mcp.tool(name="server_get_capabilities")
    def server_get_capabilities() -> dict[str, Any]:
        return handlers["server_get_capabilities"]()

    @mcp.tool(name="server_get_policy")
    def server_get_policy() -> dict[str, Any]:
        return handlers["server_get_policy"]()

    @mcp.tool(name="browser_get_state")
    def browser_get_state(session_id: str | None = None) -> dict[str, Any]:
        return handlers["browser_get_state"](session_id)
```

```python
# src/drissionpage_mcp/server.py
from __future__ import annotations

from mcp.server.fastmcp import FastMCP

from drissionpage_mcp.config import load_config
from drissionpage_mcp.dependencies import build_dependencies
from drissionpage_mcp.tools.core import register_core_tools
from drissionpage_mcp.tools.introspection import register_introspection_tools


def create_server(config_path: str | None = None) -> FastMCP:
    config = load_config(config_path)
    deps = build_dependencies(config)
    server = FastMCP(
        config.server_name,
        instructions="Use the available tools to control a local browser through DrissionPage.",
    )
    register_core_tools(server, deps)
    register_introspection_tools(server, deps)
    return server


def main() -> None:
    create_server().run()
```

- [ ] **Step 4: Run test to verify it passes**

Run: `uv run pytest tests/integration/test_tool_handlers.py -v`
Expected: PASS with `2 passed`

- [ ] **Step 5: Commit**

```bash
git add src/drissionpage_mcp/dependencies.py src/drissionpage_mcp/tools/core.py src/drissionpage_mcp/tools/introspection.py src/drissionpage_mcp/server.py tests/integration/test_tool_handlers.py
git commit -m "feat: wire core mcp tools"
```

## Task 6: Add Deterministic Local E2E Coverage And Final Docs

**Files:**
- Create: `tests/e2e/conftest.py`
- Create: `tests/e2e/site/index.html`
- Create: `tests/e2e/test_local_browser_flow.py`
- Modify: `README.md`

- [ ] **Step 1: Write the failing test**

```python
# tests/e2e/test_local_browser_flow.py
from pathlib import Path

import pytest

from drissionpage_mcp.config import BrowserConfig, SafetyConfig, ServerConfig
from drissionpage_mcp.dependencies import build_dependencies
from drissionpage_mcp.tools.core import build_core_handlers


@pytest.mark.e2e
def test_local_page_flow(live_site_url: str, tmp_path: Path) -> None:
    config = ServerConfig(
        safety=SafetyConfig(download_dir=str(tmp_path / "downloads")),
        browser=BrowserConfig(persistent_on_startup=True, headless=True),
    )
    deps = build_dependencies(config)
    handlers = build_core_handlers(deps)

    navigate = handlers["page_navigate"](live_site_url)
    type_text = handlers["element_type"]("#name", "Codex", None, None, True)
    click = handlers["element_click"]("#echo")
    text = handlers["page_get_text"]()
    screenshot = handlers["page_screenshot"](None, None, str(tmp_path), "page.png", False)

    assert navigate["ok"] is True
    assert type_text["ok"] is True
    assert click["ok"] is True
    assert text["ok"] is True
    assert screenshot["ok"] is True
    assert "Codex" in text["text"]
```

- [ ] **Step 2: Run test to verify it fails**

Run: `uv run pytest tests/e2e/test_local_browser_flow.py -v`
Expected: FAIL because `live_site_url` fixture does not exist yet

- [ ] **Step 3: Write minimal implementation**

```python
# tests/e2e/conftest.py
from __future__ import annotations

from functools import partial
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from threading import Thread

import pytest


class QuietHandler(SimpleHTTPRequestHandler):
    def log_message(self, format: str, *args) -> None:  # pragma: no cover
        return None


@pytest.fixture(scope="session")
def live_site_url() -> str:
    site_root = Path(__file__).parent / "site"
    handler = partial(QuietHandler, directory=str(site_root))
    server = ThreadingHTTPServer(("127.0.0.1", 0), handler)
    thread = Thread(target=server.serve_forever, daemon=True)
    thread.start()
    try:
        host, port = server.server_address
        yield f"http://{host}:{port}/index.html"
    finally:
        server.shutdown()
        server.server_close()
        thread.join(timeout=5)
```

```html
<!-- tests/e2e/site/index.html -->
<!doctype html>
<html lang="en">
  <head>
    <meta charset="utf-8">
    <title>DrissionPage MCP Fixture</title>
  </head>
  <body>
    <main>
      <h1>DrissionPage MCP Fixture</h1>
      <label for="name">Name</label>
      <input id="name" type="text" />
      <button id="echo" type="button">Echo</button>
      <p id="result"></p>
    </main>
    <script>
      const button = document.getElementById("echo");
      const input = document.getElementById("name");
      const result = document.getElementById("result");
      button.addEventListener("click", () => {
        result.textContent = input.value;
      });
    </script>
  </body>
</html>
```

````markdown
# README.md
# DrissionPage MCP

`DrissionPage MCP` is a general-purpose MCP server for local LLM agents that need browser automation over `stdio`.

## Install

```bash
uv sync --extra dev
```

## Run

```bash
uv run drissionpage-mcp
```

## Configuration

Create `drissionpage_mcp.toml` in the repository root when you want to override defaults.

```toml
server_name = "DrissionPage MCP"

[safety]
mode = "safe"
allow_run_js = false
allow_browser_attach = false
allow_file_upload = false
allow_download = true
download_dir = "./downloads"
default_timeout_ms = 10000

[browser]
persistent_on_startup = true
headless = false
```

## v0 Tools

- `session_create`
- `session_close`
- `page_navigate`
- `page_refresh`
- `page_go_back`
- `page_go_forward`
- `page_get_url`
- `page_get_html`
- `page_get_text`
- `page_screenshot`
- `element_find`
- `element_click`
- `element_type`
- `wait_for_element`
- `wait_time`
- `server_get_capabilities`
- `server_get_policy`
- `browser_get_state`

## Test

```bash
uv run pytest tests/unit tests/integration -v
uv run pytest tests/e2e/test_local_browser_flow.py -v
```

## Notes

- v0 ships only the safe core browser tools and introspection tools.
- Dangerous capabilities such as browser attach and arbitrary JavaScript execution are intentionally deferred.
- Review the upstream `DrissionPage` usage terms before distributing this project or using it commercially.
````

- [ ] **Step 4: Run test to verify it passes**

Run: `uv run pytest tests/unit tests/integration tests/e2e/test_local_browser_flow.py -v`
Expected: PASS with all unit, integration, and E2E tests green on a machine with a usable Chromium-family browser

- [ ] **Step 5: Commit**

```bash
git add README.md tests/e2e/conftest.py tests/e2e/site/index.html tests/e2e/test_local_browser_flow.py
git commit -m "test: add deterministic local browser coverage"
```

## Final Verification

- [ ] Run: `uv run pytest tests/unit tests/integration -v`
- [ ] Expected: PASS
- [ ] Run: `uv run pytest tests/e2e/test_local_browser_flow.py -v`
- [ ] Expected: PASS on a machine with a Chromium-family browser available to DrissionPage
- [ ] Run: `uv run python -c "from drissionpage_mcp.server import create_server; print(create_server().name)"`
- [ ] Expected: prints `DrissionPage MCP`

## Notes For The Implementer

- Keep tool functions thin. Put branching behavior in services, not MCP decorators.
- Do not expose raw DrissionPage objects outside adapters.
- Preserve `safe` defaults even if it is tempting to add shortcuts during implementation.
- If a later change adds `browser_attach`, `run_js`, or cookies/storage tools, write a new plan for `v1` instead of sneaking them into this implementation.
