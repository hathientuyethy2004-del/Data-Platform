from __future__ import annotations

from datetime import timezone
from typing import Any, Dict


def normalize_event(event: Dict[str, Any]) -> Dict[str, Any]:
    normalized = dict(event)
    timestamp = normalized.get("timestamp")
    if hasattr(timestamp, "astimezone"):
        normalized["timestamp"] = timestamp.astimezone(timezone.utc).isoformat()
    normalized["event_date"] = normalized.get("timestamp", "")[:10]
    normalized["event_type"] = str(normalized.get("event_type", "")).lower()
    return normalized
