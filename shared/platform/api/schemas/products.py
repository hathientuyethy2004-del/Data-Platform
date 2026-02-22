from __future__ import annotations

from typing import Literal

from pydantic import BaseModel

from .common import HealthStatus


class ProductLastTest(BaseModel):
    status: Literal["success", "failed", "running", "skipped"]
    passed: int
    failed: int
    completed_at: str


class ProductSummary(BaseModel):
    id: str
    display_name: str
    owner_team: str
    environment: Literal["dev", "staging", "prod"]
    health_status: HealthStatus
    data_freshness_seconds: int
    sla_compliance_pct_24h: float
    last_test: ProductLastTest | None = None


class ProductDetail(BaseModel):
    id: str
    display_name: str
    owner_team: str
    environment: Literal["dev", "staging", "prod"]
    health_status: HealthStatus
    description: str
    sla_target_pct: float
