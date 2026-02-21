from __future__ import annotations

from datetime import datetime, timezone
from typing import Any, Dict


class SegmentServiceMonitor:
    def __init__(self, product: str = "user-segmentation"):
        self.product = product

    def health(self, model_ready: bool = True) -> Dict[str, Any]:
        status = "healthy" if model_ready else "degraded"
        return {
            "product": self.product,
            "status": status,
            "model_ready": model_ready,
            "timestamp": datetime.now(timezone.utc).isoformat(),
        }
