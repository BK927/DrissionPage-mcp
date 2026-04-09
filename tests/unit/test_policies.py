import pytest

from drissionpage_mcp.config import SafetyConfig
from drissionpage_mcp.errors import ErrorCode, ToolError
from drissionpage_mcp.policies import PolicyEngine


def test_policy_blocks_run_js_when_disabled() -> None:
    engine = PolicyEngine(SafetyConfig(allow_run_js=False))

    with pytest.raises(ToolError) as caught:
        engine.require_run_js_allowed()

    assert caught.value.code is ErrorCode.POLICY_BLOCKED


def test_policy_rejects_url_outside_allowlist() -> None:
    engine = PolicyEngine(SafetyConfig(allowed_domains=("example.com",)))

    with pytest.raises(ToolError) as caught:
        engine.require_url_allowed("https://openai.com")

    assert caught.value.code is ErrorCode.POLICY_BLOCKED
