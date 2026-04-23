from pathlib import Path

import pytest

from drissionpage_mcp.config import ConfigError, load_config


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


def test_load_config_resolves_default_download_dir() -> None:
    config = load_config(Path("missing-drissionpage-mcp.toml"))

    resolved = Path(config.safety.download_dir)
    assert resolved.is_absolute()


def test_load_config_resolves_configured_download_dir(tmp_path: Path) -> None:
    config_path = tmp_path / "drissionpage_mcp.toml"
    config_path.write_text(
        f"""
[safety]
download_dir = "{tmp_path.as_posix()}/shots"
""".strip(),
        encoding="utf-8",
    )

    config = load_config(config_path)

    assert Path(config.safety.download_dir) == (tmp_path / "shots").resolve()


def test_load_config_raises_config_error_for_malformed_toml(tmp_path: Path) -> None:
    config_path = tmp_path / "drissionpage_mcp.toml"
    config_path.write_text("this = is = not = toml", encoding="utf-8")

    with pytest.raises(ConfigError, match="Failed to parse config"):
        load_config(config_path)


def test_load_config_parses_max_wait_time(tmp_path: Path) -> None:
    config_path = tmp_path / "drissionpage_mcp.toml"
    config_path.write_text(
        """
[safety]
max_wait_time_s = 5.5
""".strip(),
        encoding="utf-8",
    )

    config = load_config(config_path)

    assert config.safety.max_wait_time_s == 5.5


def test_load_config_rejects_non_positive_max_wait_time(tmp_path: Path) -> None:
    config_path = tmp_path / "drissionpage_mcp.toml"
    config_path.write_text(
        """
[safety]
max_wait_time_s = 0
""".strip(),
        encoding="utf-8",
    )

    with pytest.raises(ValueError, match="max_wait_time_s"):
        load_config(config_path)
