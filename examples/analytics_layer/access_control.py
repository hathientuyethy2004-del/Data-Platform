"""
Access Control for Analytics Layer
Simple RBAC that integrates with platform identity in real deployments.
"""
from typing import Dict, List
from dataclasses import dataclass, asdict
from datetime import datetime
import threading


@dataclass
class Role:
    name: str
    permissions: List[str]
    created_at: str


class AccessControl:
    def __init__(self):
        self.roles: Dict[str, Role] = {}
        self.user_roles: Dict[str, List[str]] = {}
        self.lock = threading.Lock()

    def create_role(self, name: str, permissions: List[str]) -> Role:
        role = Role(name=name, permissions=permissions, created_at=datetime.now().isoformat())
        with self.lock:
            self.roles[name] = role
        return role

    def assign_role(self, user: str, role: str) -> bool:
        with self.lock:
            if role not in self.roles:
                return False
            if user not in self.user_roles:
                self.user_roles[user] = []
            if role not in self.user_roles[user]:
                self.user_roles[user].append(role)
            return True

    def check_permission(self, user: str, permission: str) -> bool:
        with self.lock:
            roles = self.user_roles.get(user, [])
            for r in roles:
                role = self.roles.get(r)
                if role and permission in role.permissions:
                    return True
        return False


_access_control: AccessControl = None

def get_access_control() -> AccessControl:
    global _access_control
    if _access_control is None:
        _access_control = AccessControl()
    return _access_control
