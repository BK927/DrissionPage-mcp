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
        page_service=PageService(config.safety.download_dir),
    )
