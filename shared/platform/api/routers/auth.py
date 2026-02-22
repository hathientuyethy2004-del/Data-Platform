from __future__ import annotations

from fastapi import APIRouter, Depends, Request
from pydantic import BaseModel

from ..auth import AuthUser, authenticate_token, get_current_user, revoke_token
from ..deps import ok_response

router = APIRouter(prefix='/api/v1/auth', tags=['auth'])


class LoginPayload(BaseModel):
    token: str


@router.post('/login')
def login(payload: LoginPayload, request: Request) -> dict:
    user = authenticate_token(payload.token.strip())
    profile = {
        'subject': user.subject,
        'role': user.role,
        'token_type': 'bearer',
    }
    return ok_response(profile, request)


@router.get('/session')
def session(request: Request, user: AuthUser = Depends(get_current_user)) -> dict:
    profile = {
        'subject': user.subject,
        'role': user.role,
        'token_type': 'bearer',
    }
    return ok_response(profile, request)


@router.post('/logout')
def logout(request: Request, user: AuthUser = Depends(get_current_user)) -> dict:
    revoke_token(user.token)
    return ok_response({'status': 'logged_out'}, request)
