from __future__ import annotations


class DrissionElementAdapter:
    def __init__(self, element: object) -> None:
        self._element = element

    @property
    def text(self) -> str:
        return str(getattr(self._element, "text", ""))

    def click(self) -> None:
        self._element.click()

    def type_text(self, value: str, clear: bool = False) -> None:
        if clear and hasattr(self._element, "clear"):
            self._element.clear()
        self._element.input(value)
