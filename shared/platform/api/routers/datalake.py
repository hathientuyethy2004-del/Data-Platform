from __future__ import annotations

from datetime import datetime, timezone

from fastapi import APIRouter, Depends, Request

from ..auth import require_role
from ..deps import ok_response

router = APIRouter(
    prefix='/api/v1/datalake',
    tags=['datalake'],
    dependencies=[Depends(require_role('viewer'))],
)


@router.get('/datasets')
def datasets(request: Request) -> dict:
    data = [
        {
            'id': 'web-gold-hourly',
            'product_id': 'web-user-analytics',
            'layer': 'gold',
            'table_name': 'hourly_metrics',
            'freshness_seconds': 120,
        }
    ]
    return ok_response(data, request)


@router.get('/datasets/{dataset_id}')
def dataset_detail(dataset_id: str, request: Request) -> dict:
    now = datetime.now(timezone.utc).isoformat()
    data = {
        'id': dataset_id,
        'product_id': 'web-user-analytics',
        'layer': 'gold',
        'table_name': 'hourly_metrics',
        'row_count': 1200042,
        'partitions': ['date=2026-02-20', 'date=2026-02-21'],
        'last_update': now,
        'schema_version': 'v1',
    }
    return ok_response(data, request)


@router.get('/datasets/{dataset_id}/quality')
def dataset_quality(dataset_id: str, request: Request) -> dict:
    data = {
        'dataset_id': dataset_id,
        'quality_score': 99.2,
        'checks_passed': 12,
        'checks_failed': 1,
    }
    return ok_response(data, request)
