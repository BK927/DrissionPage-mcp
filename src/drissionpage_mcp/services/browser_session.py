from __future__ import annotations

from dataclasses import dataclass
from typing import Protocol, runtime_checkable

from drissionpage_mcp.models import BrowserState, SessionMode


@runtime_checkable
class BrowserAdapter(Protocol):
    def close(self) -> None: ...
    def get_page(self, tab_id: str | None = None) -> object: ...
    def current_tab_id(self) -> str | None: ...
    def state(self, session_id: str) -> BrowserState: ...


@dataclass(slots=True)
class BrowserSession:
    session_id: str
    mode: SessionMode
    adapter: BrowserAdapter
    is_default: bool = False
