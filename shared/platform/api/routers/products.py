from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, Query, Request

from ..auth import AuthUser, require_role
from ..deps import ok_response
from ..services.orchestrator_service import (
    get_product_detail,
    get_products,
    run_product_demo,
    run_product_test,
)

router = APIRouter(
    prefix='/api/v1/products',
    tags=['products'],
    dependencies=[Depends(require_role('viewer'))],
)


@router.get('')
def list_products(
    request: Request,
    environment: str | None = Query(default=None),
    status: str | None = Query(default=None),
    owner_team: str | None = Query(default=None),
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=50, ge=1, le=200),
) -> dict:
    rows = get_products()
    if environment:
        rows = [row for row in rows if row.get('environment') == environment]
    if status:
        rows = [row for row in rows if row.get('health_status') == status]
    if owner_team:
        rows = [row for row in rows if row.get('owner_team') == owner_team]

    offset = (page - 1) * page_size
    paged = rows[offset : offset + page_size]
    return ok_response(paged, request)


@router.get('/{product_id}')
def product_detail(product_id: str, request: Request) -> dict:
    try:
        detail = get_product_detail(product_id)
    except KeyError as error:
        raise HTTPException(status_code=404, detail=f'Product {product_id} not found') from error
    return ok_response(detail, request)


@router.get('/{product_id}/health')
def product_health(product_id: str, request: Request) -> dict:
    try:
        detail = get_product_detail(product_id)
    except KeyError as error:
        raise HTTPException(status_code=404, detail=f'Product {product_id} not found') from error
    health = {
        'product_id': product_id,
        'status': detail['health_status'],
        'checks': [
            {'name': 'architecture', 'status': detail['health_status']},
        ],
    }
    return ok_response(health, request)


@router.post('/{product_id}/tests/run')
def run_test(
    product_id: str,
    request: Request,
    user: AuthUser = Depends(require_role('operator')),
) -> dict:
    try:
        get_product_detail(product_id)
    except KeyError as error:
        raise HTTPException(status_code=404, detail=f'Product {product_id} not found') from error

    result = run_product_test(product_id)
    result['triggered_by'] = user.subject
    return ok_response(result, request)


@router.post('/{product_id}/demos/run')
def run_demo(
    product_id: str,
    request: Request,
    user: AuthUser = Depends(require_role('operator')),
) -> dict:
    try:
        get_product_detail(product_id)
    except KeyError as error:
        raise HTTPException(status_code=404, detail=f'Product {product_id} not found') from error

    result = run_product_demo(product_id)
    result['triggered_by'] = user.subject
    return ok_response(result, request)


@router.get('/{product_id}/tests/runs')
def tests_runs(product_id: str, request: Request) -> dict:
    rows = [{'execution_id': f'test_{product_id}_latest', 'status': 'success', 'passed': 1, 'failed': 0}]
    return ok_response(rows, request)


@router.get('/{product_id}/pipelines/runs')
def pipeline_runs(product_id: str, request: Request) -> dict:
    rows = [{'pipeline': 'ingestion', 'status': 'success', 'duration_seconds': 12.4}]
    return ok_response(rows, request)


@router.get('/{product_id}/apis/metrics')
def api_metrics(product_id: str, request: Request) -> dict:
    metrics = {'product_id': product_id, 'error_rate_pct': 0.2, 'p95_latency_ms': 280}
    return ok_response(metrics, request)


@router.get('/{product_id}/monitoring/sla')
def monitoring_sla(product_id: str, request: Request) -> dict:
    result = {'product_id': product_id, 'sla_compliance_pct_24h': 99.9}
    return ok_response(result, request)


@router.get('/{product_id}/config/effective')
def effective_config(product_id: str, request: Request) -> dict:
    config = {'product_id': product_id, 'environment': 'dev', 'source': 'default'}
    return ok_response(config, request)
