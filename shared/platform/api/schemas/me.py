from __future__ import annotations

from typing import Literal

from pydantic import BaseModel


class UserPreferences(BaseModel):
    default_environment: Literal["dev", "staging", "prod"]
    timezone: str
    locale: str
    notifications_enabled: bool
