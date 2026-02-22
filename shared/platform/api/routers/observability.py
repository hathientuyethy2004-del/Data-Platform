from __future__ import annotations

from fastapi import APIRouter, Depends, Query, Request

from ..auth import require_role
from ..deps import ok_response
from ..services.monitoring_service import open_alerts, recent_executions

router = APIRouter(
    prefix='/api/v1',
    tags=['observability'],
    dependencies=[Depends(require_role('viewer'))],
)


@router.get('/alerts')
def alerts(
    request: Request,
    status: str | None = Query(default=None),
    limit: int = Query(default=20, ge=1, le=200),
) -> dict:
    rows = open_alerts()
    if status:
        rows = [row for row in rows if str(row.get('status')) == status]
    return ok_response(rows[:limit], request)


@router.get('/executions')
def executions(
    request: Request,
    limit: int = Query(default=20, ge=1, le=200),
) -> dict:
    return ok_response(recent_executions()[:limit], request)
