from __future__ import annotations

from drissionpage_mcp.errors import ErrorCode, ToolError


class DrissionElementAdapter:
    def __init__(self, element: object) -> None:
        self._element = element

    @property
    def text(self) -> str:
        return str(getattr(self._element, "text", ""))

    def click(self) -> None:
        try:
            self._element.click()
        except ToolError:
            raise
        except Exception as error:
            raise ToolError(
                code=ErrorCode.ACTION_TIMEOUT,
                message=f"Unable to click element: {error}",
                retryable=True,
                context={"action": "click"},
            ) from error

    def type_text(self, value: str, clear: bool = False) -> None:
        try:
            if clear and hasattr(self._element, "clear"):
                self._element.clear()
            self._element.input(value)
        except ToolError:
            raise
        except Exception as error:
            raise ToolError(
                code=ErrorCode.ACTION_TIMEOUT,
                message=f"Unable to type into element: {error}",
                retryable=True,
                context={"action": "type_text", "clear": clear},
            ) from error
