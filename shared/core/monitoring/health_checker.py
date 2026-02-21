from __future__ import annotations

from datetime import datetime, timezone
from typing import Any, Dict


class HealthChecker:
    def __init__(self, component: str):
        self.component = component

    def healthy(self, details: Dict[str, Any] | None = None) -> Dict[str, Any]:
        return {
            "component": self.component,
            "status": "healthy",
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "details": details or {},
        }

    def degraded(self, reason: str, details: Dict[str, Any] | None = None) -> Dict[str, Any]:
        payload = self.healthy(details)
        payload["status"] = "degraded"
        payload["reason"] = reason
        return payload
