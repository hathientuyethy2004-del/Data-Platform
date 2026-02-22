from __future__ import annotations

from dataclasses import dataclass
from typing import Literal

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer


Role = Literal["viewer", "operator", "admin"]


@dataclass(frozen=True)
class AuthUser:
    subject: str
    role: Role
    token: str


bearer_scheme = HTTPBearer(auto_error=False)

_TOKEN_ROLE_MAP: dict[str, Role] = {
    "viewer-token": "viewer",
    "operator-token": "operator",
    "admin-token": "admin",
}

_REVOKED_TOKENS: set[str] = set()

_ROLE_PRIORITY: dict[Role, int] = {
    "viewer": 1,
    "operator": 2,
    "admin": 3,
}


def _resolve_role_from_token(token: str) -> Role | None:
    return _TOKEN_ROLE_MAP.get(token)


def authenticate_token(token: str) -> AuthUser:
    if token in _REVOKED_TOKENS:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token has been revoked",
        )

    role = _resolve_role_from_token(token)
    if role is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid bearer token",
        )
    return AuthUser(subject=f"user:{role}", role=role, token=token)


def revoke_token(token: str) -> None:
    _REVOKED_TOKENS.add(token)


def get_current_user(
    credentials: HTTPAuthorizationCredentials | None = Depends(bearer_scheme),
) -> AuthUser:
    if credentials is None or credentials.scheme.lower() != "bearer":
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Missing or invalid bearer token",
        )

    token = credentials.credentials
    return authenticate_token(token)


def require_role(min_role: Role):
    def dependency(user: AuthUser = Depends(get_current_user)) -> AuthUser:
        if _ROLE_PRIORITY[user.role] < _ROLE_PRIORITY[min_role]:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Insufficient role. Required: {min_role}",
            )
        return user

    return dependency
