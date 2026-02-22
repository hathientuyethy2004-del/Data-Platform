from __future__ import annotations

from pydantic import BaseModel


class DatasetSummary(BaseModel):
    id: str
    product_id: str
    layer: str
    table_name: str
    freshness_seconds: int


class DatasetQuality(BaseModel):
    dataset_id: str
    quality_score: float
    checks_passed: int
    checks_failed: int
