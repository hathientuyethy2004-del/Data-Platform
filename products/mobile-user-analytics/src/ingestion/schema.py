from __future__ import annotations

from datetime import datetime
from enum import Enum
from typing import Any, Dict

from pydantic import BaseModel, Field


class MobileEventType(str, Enum):
    APP_OPEN = "app_open"
    SCREEN_VIEW = "screen_view"
    PURCHASE = "purchase"
    CRASH = "crash"


class MobileEvent(BaseModel):
    event_id: str
    user_id: str
    session_id: str
    event_type: MobileEventType
    timestamp: datetime
    app_version: str
    device_os: str
    metadata: Dict[str, Any] = Field(default_factory=dict)
