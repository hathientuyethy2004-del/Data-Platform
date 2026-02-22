from __future__ import annotations

from typing import Any


PRODUCT_SERVICE_REGISTRY: list[dict[str, Any]] = [
    {'name': 'web-user-analytics', 'base_url': 'http://localhost:8002', 'status': 'unknown'},
    {'name': 'operational-metrics', 'base_url': 'http://localhost:8003', 'status': 'unknown'},
    {'name': 'compliance-auditing', 'base_url': 'http://localhost:8004', 'status': 'unknown'},
    {'name': 'user-segmentation', 'base_url': 'http://localhost:8005', 'status': 'unknown'},
    {'name': 'mobile-user-analytics', 'base_url': 'http://localhost:8006', 'status': 'unknown'},
]


def list_services() -> list[dict[str, Any]]:
    return PRODUCT_SERVICE_REGISTRY
