from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from drissionpage_mcp.models import SessionMode


@dataclass(slots=True)
class BrowserSession:
    session_id: str
    mode: SessionMode
    adapter: Any
    is_default: bool = False
