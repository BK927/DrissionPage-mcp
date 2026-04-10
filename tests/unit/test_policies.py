import pytest

from drissionpage_mcp.config import SafetyConfig
from drissionpage_mcp.errors import ErrorCode, ToolError
from drissionpage_mcp.policies import PolicyEngine


def test_policy_blocks_run_js_when_disabled() -> None:
    engine = PolicyEngine(SafetyConfig(allow_run_js=False))

    with pytest.raises(ToolError) as caught:
        engine.require_run_js_allowed()

    assert caught.value.code is ErrorCode.POLICY_BLOCKED


def test_policy_blocks_browser_attach_when_disabled() -> None:
    engine = PolicyEngine(SafetyConfig(allow_browser_attach=False))

    with pytest.raises(ToolError) as caught:
        engine.require_browser_attach_allowed()

    assert caught.value.code is ErrorCode.POLICY_BLOCKED


def test_policy_rejects_url_outside_allowlist() -> None:
    engine = PolicyEngine(SafetyConfig(allowed_domains=("example.com",)))

    with pytest.raises(ToolError) as caught:
        engine.require_url_allowed("https://openai.com")

    assert caught.value.code is ErrorCode.POLICY_BLOCKED


def test_policy_allows_url_on_allowlist() -> None:
    engine = PolicyEngine(SafetyConfig(allowed_domains=("example.com",)))

    engine.require_url_allowed("https://example.com/path")


def test_policy_allows_any_url_without_allowlist() -> None:
    engine = PolicyEngine(SafetyConfig())

    engine.require_url_allowed("https://openai.com")


def test_policy_normalizes_allowlist_domains() -> None:
    engine = PolicyEngine(SafetyConfig(allowed_domains=(" EXAMPLE.COM ",)))

    engine.require_url_allowed("https://example.com")
