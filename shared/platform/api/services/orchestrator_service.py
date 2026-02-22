from __future__ import annotations

from pathlib import Path
from typing import Any

from ...orchestrator import PlatformOrchestrator


def _orchestrator() -> PlatformOrchestrator:
    return PlatformOrchestrator(workspace_root=Path('/workspaces/Data-Platform'))


def get_platform_status() -> dict[str, Any]:
    return _orchestrator().architecture_status()


def get_products() -> list[dict[str, Any]]:
    status = get_platform_status()
    products = []
    for item in status.get('products', []):
        products.append(
            {
                'id': item['name'],
                'display_name': item['name'].replace('-', ' ').title(),
                'owner_team': f"team-{item['name']}",
                'environment': 'dev',
                'health_status': 'healthy' if item.get('architecture_complete') else 'warning',
                'data_freshness_seconds': 120,
                'sla_compliance_pct_24h': 99.9,
                'last_test': None,
            }
        )
    return products


def get_product_detail(product_id: str) -> dict[str, Any]:
    products = get_products()
    for product in products:
        if product['id'] == product_id:
            return {
                **product,
                'description': f"Operational view for {product['display_name']}.",
                'sla_target_pct': 99.9,
            }
    raise KeyError(product_id)


def run_product_test(product_id: str) -> dict[str, Any]:
    result = _orchestrator().run_product_tests(product_id)
    return {
        'execution_id': f"test_{product_id}",
        'status': result.get('status', 'unknown'),
    }


def run_product_demo(product_id: str) -> dict[str, Any]:
    result = _orchestrator().run_demo_if_available(product_id)
    return {
        'execution_id': f"demo_{product_id}",
        'status': result.get('status', 'unknown'),
    }
