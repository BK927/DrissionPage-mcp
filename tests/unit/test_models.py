from drissionpage_mcp.models import ToolResult


def test_tool_result_to_dict_preserves_extra_payload_and_canonical_fields() -> None:
    result = ToolResult(
        ok=True,
        message="done",
        session_id="session-1",
        data={
            "tab_id": "payload-tab",
            "items": [],
            "meta": {},
        },
    )

    payload = result.to_dict()

    assert payload["ok"] is True
    assert payload["message"] == "done"
    assert payload["session_id"] == "session-1"
    assert payload["items"] == []
    assert payload["meta"] == {}


def test_tool_result_to_dict_does_not_overwrite_canonical_fields() -> None:
    result = ToolResult(
        ok=False,
        message="failed",
        tab_id="canonical-tab",
        data={"tab_id": "payload-tab", "error": "boom"},
    )

    payload = result.to_dict()

    assert payload["tab_id"] == "canonical-tab"
    assert payload["error"] == "boom"
