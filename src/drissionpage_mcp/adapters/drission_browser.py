from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from DrissionPage import Chromium, ChromiumOptions
from DrissionPage import errors as drission_errors

from drissionpage_mcp.config import BrowserConfig, SafetyConfig
from drissionpage_mcp.errors import ErrorCode, ToolError
from drissionpage_mcp.models import BrowserState, TabInfo


@dataclass(slots=True)
class _FallbackPageAdapter:
    tab_id: str | None
    title: str
    url: str


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
    ) -> DrissionBrowserAdapter:
        try:
            options = ChromiumOptions(read_file=False)
            # Avoid reusing the default DevTools endpoint across logical sessions.
            options.auto_port()
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
        try:
            self._browser.quit()
        except ToolError:
            raise
        except Exception as error:
            raise ToolError(
                code=ErrorCode.BROWSER_CLOSE_FAILED,
                message=f"Unable to close Chromium: {error}",
            ) from error

    def _tab_not_found(self, tab_id: str | None) -> ToolError:
        label = "current tab" if tab_id is None else f"tab '{tab_id}'"
        return ToolError(
            code=ErrorCode.TAB_NOT_FOUND,
            message=f"Unable to resolve {label}.",
            context={"tab_id": tab_id},
        )

    def _select_tab(self, tab_id: str | None = None) -> Any:
        try:
            tab = self._browser.latest_tab if tab_id is None else self._browser.get_tab(tab_id)
        except Exception as error:
            if isinstance(error, (drission_errors.TargetNotFoundError, KeyError, IndexError)):
                raise self._tab_not_found(tab_id) from error
            raise
        if tab is None:
            raise self._tab_not_found(tab_id)
        return tab

    def get_page(self, tab_id: str | None = None) -> Any:
        tab = self._select_tab(tab_id)
        try:
            from drissionpage_mcp.adapters.drission_page import DrissionPageAdapter
        except ModuleNotFoundError as error:
            if error.name != "drissionpage_mcp.adapters.drission_page":
                raise
            return _FallbackPageAdapter(
                tab_id=str(getattr(tab, "tab_id", "")) or None,
                title=str(getattr(tab, "title", "")),
                url=str(getattr(tab, "url", "")),
            )
        return DrissionPageAdapter(tab)

    def current_tab_id(self) -> str | None:
        try:
            tab = self._browser.latest_tab
        except Exception as error:
            if isinstance(error, (drission_errors.TargetNotFoundError, KeyError, IndexError)):
                return None
            raise
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
