"""
Simple in-memory + file-backed cache for serving layer
"""
import threading
import json
from pathlib import Path
from typing import Any, Optional
from dataclasses import dataclass, asdict
from datetime import datetime, timedelta


@dataclass
class CacheEntry:
    key: str
    value: Any
    created_at: str
    ttl_seconds: int = 300

    def is_expired(self) -> bool:
        return (datetime.fromisoformat(self.created_at) + timedelta(seconds=self.ttl_seconds)) < datetime.now()


class SimpleCache:
    def __init__(self, storage_path: str = "serving_data/cache", default_ttl: int = 300):
        self.lock = threading.Lock()
        self.store = {}
        self.storage = Path(storage_path)
        self.storage.mkdir(parents=True, exist_ok=True)
        self.default_ttl = default_ttl
        self._load()

    def set(self, key: str, value: Any, ttl_seconds: Optional[int] = None):
        ttl = ttl_seconds if ttl_seconds is not None else self.default_ttl
        entry = CacheEntry(key=key, value=value, created_at=datetime.now().isoformat(), ttl_seconds=ttl)
        with self.lock:
            self.store[key] = entry
            self._persist_key(key)
        return True

    def get(self, key: str) -> Optional[Any]:
        with self.lock:
            entry = self.store.get(key)
            if not entry:
                return None
            if entry.is_expired():
                del self.store[key]
                self._delete_key(key)
                return None
            return entry.value

    def invalidate(self, key: str):
        with self.lock:
            if key in self.store:
                del self.store[key]
                self._delete_key(key)
        return True

    def _persist_key(self, key: str):
        try:
            entry = self.store[key]
            path = self.storage / f"{key}.json"
            with open(path, 'w') as f:
                json.dump(asdict(entry), f, default=str)
        except Exception:
            pass

    def _delete_key(self, key: str):
        try:
            path = self.storage / f"{key}.json"
            if path.exists():
                path.unlink()
        except Exception:
            pass

    def _load(self):
        for p in self.storage.glob("*.json"):
            try:
                with open(p, 'r') as f:
                    data = json.load(f)
                    entry = CacheEntry(**data)
                    if not entry.is_expired():
                        self.store[entry.key] = entry
                    else:
                        p.unlink()
            except Exception:
                pass


_cache: Optional[SimpleCache] = None

def get_cache(storage_path: str = "serving_data/cache", default_ttl: int = 300) -> SimpleCache:
    global _cache
    if _cache is None:
        _cache = SimpleCache(storage_path, default_ttl)
    return _cache
