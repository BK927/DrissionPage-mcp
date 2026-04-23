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
    screenshot = handlers["page_screenshot"](None, None, "shots", "page.png", False)

    assert navigate["ok"] is True
    assert type_text["ok"] is True
    assert click["ok"] is True
    assert text["ok"] is True
    assert screenshot["ok"] is True
    assert "Codex" in text["text"]
