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
    allowed_domains: tuple[str, ...] = ()
    download_dir: str = "./downloads"
    default_timeout_ms: int = 10_000
    max_wait_time_s: float = 60.0


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


class ConfigError(Exception):
    pass


def _tuple_from_value(value: Any) -> tuple[str, ...]:
    if value is None:
        return ()
    if isinstance(value, (list, tuple)):
        return tuple(str(item) for item in value)
    return (str(value),)


def _strict_bool(value: Any, field_name: str, default: bool) -> bool:
    if value is None:
        return default
    if isinstance(value, bool):
        return value
    raise TypeError(f"{field_name} must be a boolean")


def _positive_number(value: Any, field_name: str, default: float) -> float:
    if value is None:
        return default
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        raise TypeError(f"{field_name} must be a number")
    if value <= 0:
        raise ValueError(f"{field_name} must be greater than zero")
    return float(value)


def load_config(path: str | Path | None = None) -> ServerConfig:
    config_path = Path(path) if path is not None else Path("drissionpage_mcp.toml")
    if not config_path.exists():
        defaults = SafetyConfig()
        return ServerConfig(
            safety=SafetyConfig(
                mode=defaults.mode,
                allow_run_js=defaults.allow_run_js,
                allow_browser_attach=defaults.allow_browser_attach,
                allowed_domains=defaults.allowed_domains,
                download_dir=str(Path(defaults.download_dir).resolve()),
                default_timeout_ms=defaults.default_timeout_ms,
                max_wait_time_s=defaults.max_wait_time_s,
            )
        )

    try:
        raw = tomllib.loads(config_path.read_text(encoding="utf-8"))
    except tomllib.TOMLDecodeError as error:
        raise ConfigError(f"Failed to parse config at {config_path}: {error}") from error

    safety_raw = raw.get("safety", {})
    browser_raw = raw.get("browser", {})

    download_dir_raw = str(safety_raw.get("download_dir", "./downloads"))
    safety = SafetyConfig(
        mode=str(safety_raw.get("mode", "safe")),
        allow_run_js=_strict_bool(safety_raw.get("allow_run_js"), "safety.allow_run_js", False),
        allow_browser_attach=_strict_bool(
            safety_raw.get("allow_browser_attach"), "safety.allow_browser_attach", False
        ),
        allowed_domains=_tuple_from_value(safety_raw.get("allowed_domains")),
        download_dir=str(Path(download_dir_raw).resolve()),
        default_timeout_ms=int(safety_raw.get("default_timeout_ms", 10_000)),
        max_wait_time_s=_positive_number(
            safety_raw.get("max_wait_time_s"), "safety.max_wait_time_s", 60.0
        ),
    )
    browser = BrowserConfig(
        persistent_on_startup=_strict_bool(
            browser_raw.get("persistent_on_startup"),
            "browser.persistent_on_startup",
            True,
        ),
        headless=_strict_bool(browser_raw.get("headless"), "browser.headless", False),
        browser_path=browser_raw.get("browser_path"),
    )
    return ServerConfig(
        server_name=str(raw.get("server_name", "DrissionPage MCP")),
        safety=safety,
        browser=browser,
    )
