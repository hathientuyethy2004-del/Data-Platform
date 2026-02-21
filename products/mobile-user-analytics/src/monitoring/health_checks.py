from __future__ import annotations

from datetime import datetime, timezone
from typing import Any, Dict


def service_health(consumer_ready: bool = True, api_ready: bool = True) -> Dict[str, Any]:
    is_healthy = consumer_ready and api_ready
    return {
        "status": "healthy" if is_healthy else "degraded",
        "product": "mobile-user-analytics",
        "consumer_ready": consumer_ready,
        "api_ready": api_ready,
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }
