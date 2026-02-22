from __future__ import annotations

from fastapi import APIRouter, Depends, Request

from ..auth import AuthUser, require_role
from ..deps import ok_response
from ..services.gateway_service import list_services
from ..services.monitoring_service import recent_executions
from ..services.orchestrator_service import get_platform_status

router = APIRouter(
    prefix='/api/v1/platform',
    tags=['platform'],
    dependencies=[Depends(require_role('viewer'))],
)


@router.get('/status')
def status(request: Request) -> dict:
    snapshot = get_platform_status()
    payload = {
        'products_total': snapshot.get('products_total', 0),
        'products_complete': snapshot.get('products_complete', 0),
        'products_incomplete': snapshot.get('products_incomplete', 0),
        'platform_components': snapshot.get('platform_components', {}),
    }
    return ok_response(payload, request)


@router.get('/services')
def services(request: Request) -> dict:
    return ok_response(list_services(), request)


@router.get('/executions')
def executions(request: Request) -> dict:
    return ok_response(recent_executions(), request)


@router.post('/actions/{action}')
def run_action(
    action: str,
    request: Request,
    user: AuthUser = Depends(require_role('admin')),
) -> dict:
    result = {'action': action, 'status': 'accepted', 'triggered_by': user.subject}
    return ok_response(result, request)
