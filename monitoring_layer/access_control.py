"""
Simple token-based Access Control for development/testing.

Usage:
  acl = get_access_control()
  acl.add_user('alice-token', ['serve:query','serve:read'])
  acl.check_permission('alice-token','serve:query') -> True/False

This implementation persists to `monitoring_data/access_control.json`.
In production, replace with a proper identity provider and secret storage.
"""
from typing import Dict, List, Optional
import threading
import json
from pathlib import Path


class AccessControl:
    def __init__(self, storage_path: Optional[str] = None):
        self.lock = threading.Lock()
        self.storage_path = Path(storage_path or "monitoring_data")
        self.storage_path.mkdir(parents=True, exist_ok=True)
        self.file = self.storage_path / "access_control.json"
        self._data: Dict[str, List[str]] = {}
        self._load()

    def _load(self):
        if self.file.exists():
            try:
                with open(self.file, 'r') as f:
                    self._data = json.load(f)
            except Exception:
                self._data = {}

    def _save(self):
        try:
            with open(self.file, 'w') as f:
                json.dump(self._data, f, indent=2)
        except Exception:
            pass

    def add_user(self, token: str, permissions: List[str]):
        with self.lock:
            self._data[token] = permissions
            self._save()

    def remove_user(self, token: str):
        with self.lock:
            if token in self._data:
                del self._data[token]
                self._save()

    def check_permission(self, token: str, permission: str) -> bool:
        if not token:
            return False
        perms = self._data.get(token, [])
        return permission in perms


# Singleton helper
_acl: Optional[AccessControl] = None


def get_access_control(storage_path: Optional[str] = None) -> AccessControl:
    global _acl
    if _acl is None:
        _acl = AccessControl(storage_path=storage_path)
    return _acl
