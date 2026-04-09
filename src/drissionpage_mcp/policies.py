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
