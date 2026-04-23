from __future__ import annotations

from drissionpage_mcp.errors import ErrorCode, ToolError


def test_tool_error_to_payload_serializes_code_and_context() -> None:
    error = ToolError(
        code=ErrorCode.INVALID_ARGUMENT,
        message="bad value",
        retryable=False,
        context={"field": "seconds", "value": -1},
    )

    payload = error.to_payload()

    assert payload == {
        "ok": False,
        "error_code": "INVALID_ARGUMENT",
        "message": "bad value",
        "retryable": False,
        "field": "seconds",
        "value": -1,
    }


def test_tool_error_to_payload_handles_empty_context() -> None:
    error = ToolError(
        code=ErrorCode.POLICY_BLOCKED,
        message="blocked",
        retryable=True,
    )

    payload = error.to_payload()

    assert payload == {
        "ok": False,
        "error_code": "POLICY_BLOCKED",
        "message": "blocked",
        "retryable": True,
    }
