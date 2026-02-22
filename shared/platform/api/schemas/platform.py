from __future__ import annotations

from pydantic import BaseModel


class PlatformServiceStatus(BaseModel):
    name: str
    base_url: str
    status: str


class PlatformStatus(BaseModel):
    products_total: int
    products_complete: int
    products_incomplete: int
