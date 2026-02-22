from __future__ import annotations

from fastapi import APIRouter, Depends, Request

from ..auth import require_role
from ..deps import ok_response
from ..services.monitoring_service import open_alerts, recent_executions
from ..services.orchestrator_service import get_products

router = APIRouter(
    prefix='/api/v1/dashboard',
    tags=['dashboard'],
    dependencies=[Depends(require_role('viewer'))],
)


@router.get('/summary')
def summary(request: Request) -> dict:
    products = get_products()
    healthy_products = sum(1 for product in products if product['health_status'] == 'healthy')
    payload = {
        'products_total': len(products),
        'healthy_products': healthy_products,
        'failing_checks': len(products) - healthy_products,
        'sla_compliance_pct_24h': 99.9,
        'api_p95_latency_ms': 250,
        'products': products,
    }
    return ok_response(payload, request)


@router.get('/alerts')
def alerts(request: Request) -> dict:
    return ok_response(open_alerts(), request)


@router.get('/executions')
def executions(request: Request) -> dict:
    return ok_response(recent_executions(), request)
