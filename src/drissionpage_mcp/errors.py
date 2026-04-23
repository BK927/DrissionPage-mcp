from __future__ import annotations

from dataclasses import dataclass, field
from enum import StrEnum


class ErrorCode(StrEnum):
    BROWSER_LAUNCH_FAILED = "BROWSER_LAUNCH_FAILED"
    BROWSER_CLOSE_FAILED = "BROWSER_CLOSE_FAILED"
    SESSION_NOT_FOUND = "SESSION_NOT_FOUND"
    TAB_NOT_FOUND = "TAB_NOT_FOUND"
    NAVIGATION_FAILED = "NAVIGATION_FAILED"
    ELEMENT_NOT_FOUND = "ELEMENT_NOT_FOUND"
    ACTION_TIMEOUT = "ACTION_TIMEOUT"
    INVALID_ARGUMENT = "INVALID_ARGUMENT"
    POLICY_BLOCKED = "POLICY_BLOCKED"
    UNSUPPORTED_OPERATION = "UNSUPPORTED_OPERATION"


@dataclass(slots=True)
class ToolError(Exception):
    code: ErrorCode
    message: str
    retryable: bool = False
    context: dict[str, object] = field(default_factory=dict)

    def __str__(self) -> str:
        return f"{self.code}: {self.message}"

    def to_payload(self) -> dict[str, object]:
        return {
            "ok": False,
            "error_code": self.code.value,
            "message": self.message,
            "retryable": self.retryable,
            **self.context,
        }
