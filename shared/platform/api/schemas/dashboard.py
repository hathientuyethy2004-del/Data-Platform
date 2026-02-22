from __future__ import annotations

from pydantic import BaseModel

from .products import ProductSummary


class DashboardSummary(BaseModel):
    products_total: int
    healthy_products: int
    failing_checks: int
    sla_compliance_pct_24h: float
    api_p95_latency_ms: int
    products: list[ProductSummary]
