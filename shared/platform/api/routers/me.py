from __future__ import annotations

from fastapi import APIRouter, Depends, Request
from pydantic import BaseModel

from ..auth import AuthUser, require_role
from ..deps import ok_response

router = APIRouter(
    prefix='/api/v1/me',
    tags=['me'],
    dependencies=[Depends(require_role('viewer'))],
)


class PreferencesUpdate(BaseModel):
    default_environment: str | None = None
    timezone: str | None = None
    locale: str | None = None
    notifications_enabled: bool | None = None


PREFERENCES: dict[str, object] = {
    'default_environment': 'dev',
    'timezone': 'UTC',
    'locale': 'en-US',
    'notifications_enabled': True,
}


@router.get('/preferences')
def get_preferences(request: Request) -> dict:
    return ok_response(PREFERENCES, request)


@router.get('/profile')
def get_profile(request: Request, user: AuthUser = Depends(require_role('viewer'))) -> dict:
    return ok_response({'subject': user.subject, 'role': user.role}, request)


@router.patch('/preferences')
def patch_preferences(
    payload: PreferencesUpdate,
    request: Request,
    _user: AuthUser = Depends(require_role('admin')),
) -> dict:
    updates = payload.model_dump(exclude_none=True)
    PREFERENCES.update(updates)
    return ok_response(PREFERENCES, request)
