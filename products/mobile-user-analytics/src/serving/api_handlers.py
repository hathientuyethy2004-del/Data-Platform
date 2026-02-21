from __future__ import annotations

from datetime import datetime, timezone
from typing import Any, Dict, List

from fastapi import FastAPI

from src.storage.gold_metrics import compute_daily_active_users


app = FastAPI(title="Mobile User Analytics API", version="0.1.0")


@app.get("/health")
def health() -> Dict[str, Any]:
    return {
        "status": "healthy",
        "product": "mobile-user-analytics",
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }


@app.post("/metrics/dau")
def dau(events: List[Dict[str, Any]]) -> Dict[str, Any]:
    return {
        "status": "ok",
        "results": compute_daily_active_users(events),
    }
