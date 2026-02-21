from __future__ import annotations

from typing import Dict, Iterable


class AccessController:
    def __init__(self, role_permissions: Dict[str, Iterable[str]]):
        self.role_permissions = {
            role: set(permissions) for role, permissions in role_permissions.items()
        }

    def is_allowed(self, role: str, permission: str) -> bool:
        permissions = self.role_permissions.get(role, set())
        return permission in permissions or "*" in permissions
