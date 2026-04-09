from drissionpage_mcp.config import BrowserConfig
from drissionpage_mcp.errors import ErrorCode, ToolError
from drissionpage_mcp.services.browser_registry import BrowserRegistry


class FakeAdapter:
    def __init__(self, label: str) -> None:
        self.label = label
        self.closed = False

    def close(self) -> None:
        self.closed = True


def test_registry_creates_default_and_ephemeral_sessions() -> None:
    counter = {"value": 0}

    def factory(mode: str) -> FakeAdapter:
        counter["value"] += 1
        return FakeAdapter(f"{mode}-{counter['value']}")

    registry = BrowserRegistry(factory, BrowserConfig())

    default_session = registry.ensure_default_session()
    ephemeral_session = registry.create_session("ephemeral")

    assert default_session.is_default is True
    assert default_session.mode == "persistent"
    assert ephemeral_session.mode == "ephemeral"


def test_registry_rejects_closing_default_session() -> None:
    registry = BrowserRegistry(lambda mode: FakeAdapter(mode), BrowserConfig())
    registry.ensure_default_session()

    try:
        registry.close_session("default")
    except ToolError as error:
        assert error.code is ErrorCode.UNSUPPORTED_OPERATION
    else:
        raise AssertionError("Expected ToolError when closing default session")
