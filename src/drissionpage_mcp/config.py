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
