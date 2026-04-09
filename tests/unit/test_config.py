from drissionpage_mcp.config import load_config


def test_load_config_returns_safe_defaults() -> None:
    config = load_config()

    assert config.server_name == "DrissionPage MCP"
    assert config.safety.mode == "safe"
    assert config.safety.allow_run_js is False
    assert config.safety.allow_browser_attach is False
    assert config.browser.persistent_on_startup is True
    assert config.browser.headless is False
