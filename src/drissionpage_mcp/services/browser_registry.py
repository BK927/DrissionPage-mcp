from __future__ import annotations

import logging
from collections.abc import Callable
from uuid import uuid4

from drissionpage_mcp.config import BrowserConfig
from drissionpage_mcp.errors import ErrorCode, ToolError
from drissionpage_mcp.models import SessionMode
from drissionpage_mcp.services.browser_session import BrowserSession

logger = logging.getLogger(__name__)


class BrowserRegistry:
    def __init__(
        self,
        adapter_factory: Callable[[SessionMode], object],
        browser_config: BrowserConfig,
    ) -> None:
        self._adapter_factory = adapter_factory
        self._browser_config = browser_config
        self._sessions: dict[str, BrowserSession] = {}

    def ensure_default_session(self) -> BrowserSession:
        if "default" in self._sessions:
            return self._sessions["default"]

        session = BrowserSession(
            session_id="default",
            mode="persistent",
            adapter=self._adapter_factory("persistent"),
            is_default=True,
        )
        self._sessions["default"] = session
        return session

    def create_session(self, mode: SessionMode = "ephemeral") -> BrowserSession:
        session_id = f"session-{uuid4().hex[:8]}"
        session = BrowserSession(
            session_id=session_id,
            mode=mode,
            adapter=self._adapter_factory(mode),
        )
        self._sessions[session_id] = session
        logger.info("session_created session_id=%s mode=%s", session_id, mode)
        return session

    def get_session(self, session_id: str | None = None) -> BrowserSession:
        key = session_id or "default"
        if key == "default":
            return self.ensure_default_session()
        if key not in self._sessions:
            raise ToolError(
                code=ErrorCode.SESSION_NOT_FOUND,
                message=f"Session '{key}' does not exist.",
                context={"session_id": key},
            )
        return self._sessions[key]

    def close_session(self, session_id: str) -> None:
        if session_id == "default":
            raise ToolError(
                code=ErrorCode.UNSUPPORTED_OPERATION,
                message="The default session cannot be closed.",
                context={"session_id": session_id},
            )

        session = self.get_session(session_id)
        try:
            session.adapter.close()
        except ToolError:
            raise
        except Exception as error:
            logger.warning("session_close_failed session_id=%s error=%s", session_id, error)
            raise ToolError(
                code=ErrorCode.BROWSER_CLOSE_FAILED,
                message=f"Unable to close session '{session_id}': {error}",
                context={"session_id": session_id},
            ) from error
        del self._sessions[session_id]
        logger.info("session_closed session_id=%s", session_id)

    def all_sessions(self) -> list[BrowserSession]:
        if self._browser_config.persistent_on_startup and "default" not in self._sessions:
            self.ensure_default_session()
        return list(self._sessions.values())
