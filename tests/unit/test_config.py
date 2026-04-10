from pathlib import Path

import pytest

from drissionpage_mcp.config import load_config


def test_load_config_returns_safe_defaults() -> None:
    config = load_config(Path("missing-drissionpage-mcp.toml"))

    assert config.server_name == "DrissionPage MCP"
    assert config.safety.mode == "safe"
    assert config.safety.allow_run_js is False
    assert config.safety.allow_browser_attach is False
    assert config.browser.persistent_on_startup is True
    assert config.browser.headless is False


def test_load_config_parses_boolean_values_strictly(tmp_path: Path) -> None:
    config_path = tmp_path / "drissionpage_mcp.toml"
    config_path.write_text(
        """
server_name = "Custom"

[safety]
allow_run_js = true
allow_browser_attach = false

[browser]
persistent_on_startup = false
headless = true
""".strip(),
        encoding="utf-8",
    )

    config = load_config(config_path)

    assert config.server_name == "Custom"
    assert config.safety.allow_run_js is True
    assert config.safety.allow_browser_attach is False
    assert config.browser.persistent_on_startup is False
    assert config.browser.headless is True


def test_load_config_rejects_string_booleans(tmp_path: Path) -> None:
    config_path = tmp_path / "drissionpage_mcp.toml"
    config_path.write_text(
        """
[safety]
allow_run_js = "false"
""".strip(),
        encoding="utf-8",
    )

    with pytest.raises(TypeError, match="allow_run_js"):
        load_config(config_path)
