from __future__ import annotations

from dataclasses import asdict, dataclass, field
from typing import Any, Literal


SessionMode = Literal["persistent", "ephemeral"]


@dataclass(slots=True)
class TabInfo:
    tab_id: str
    title: str
    url: str


@dataclass(slots=True)
class BrowserState:
    session_id: str
    mode: SessionMode
    current_tab_id: str | None
    tabs: list[TabInfo] = field(default_factory=list)


@dataclass(slots=True)
class ToolResult:
    ok: bool
    message: str
    session_id: str | None = None
    tab_id: str | None = None
    url: str | None = None
    elapsed_ms: int | None = None
    data: dict[str, Any] = field(default_factory=dict)
    error_code: str | None = None
    retryable: bool | None = None

    def to_dict(self) -> dict[str, Any]:
        payload = asdict(self)
        extra = payload.pop("data")
        payload.update(extra)
        return {key: value for key, value in payload.items() if value not in (None, {}, [])}
