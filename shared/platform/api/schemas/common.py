from __future__ import annotations

from typing import Any, Literal

from pydantic import BaseModel


HealthStatus = Literal["healthy", "warning", "critical", "skipped", "unknown"]


class MetaModel(BaseModel):
    request_id: str
    timestamp: str


class ErrorModel(BaseModel):
    code: str
    message: str
    details: dict[str, Any] = {}


class ErrorEnvelope(BaseModel):
    error: ErrorModel
    meta: MetaModel
