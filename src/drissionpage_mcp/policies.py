from __future__ import annotations

import logging
from urllib.parse import urlparse

from drissionpage_mcp.config import SafetyConfig
from drissionpage_mcp.errors import ErrorCode, ToolError

logger = logging.getLogger(__name__)


class PolicyEngine:
    def __init__(self, config: SafetyConfig) -> None:
        self._config = config
        self._allowed_domains = tuple(
            domain.strip().lower() for domain in config.allowed_domains if domain.strip()
        )

    def require_run_js_allowed(self) -> None:
        if not self._config.allow_run_js:
            logger.warning("policy_rejected action=run_js reason=disabled")
            raise ToolError(
                code=ErrorCode.POLICY_BLOCKED,
                message="run_js is disabled in safe mode.",
            )

    def require_browser_attach_allowed(self) -> None:
        if not self._config.allow_browser_attach:
            logger.warning("policy_rejected action=browser_attach reason=disabled")
            raise ToolError(
                code=ErrorCode.POLICY_BLOCKED,
                message="browser_attach is disabled in safe mode.",
            )

    def require_url_allowed(self, url: str) -> None:
        if not self._allowed_domains:
            return

        hostname = (urlparse(url).hostname or "").lower()
        if hostname in self._allowed_domains:
            return

        logger.warning(
            "policy_rejected action=navigate url=%s allowed_domains=%s",
            url,
            list(self._allowed_domains),
        )
        raise ToolError(
            code=ErrorCode.POLICY_BLOCKED,
            message=f"URL '{url}' is outside the configured allowlist.",
            context={"url": url},
        )
