from __future__ import annotations

from collections import defaultdict
from typing import Any, Dict, Iterable, List


def compute_daily_active_users(events: Iterable[Dict[str, Any]]) -> List[Dict[str, Any]]:
    users_by_date = defaultdict(set)
    for event in events:
        event_date = str(event.get("event_date") or str(event.get("timestamp", ""))[:10])
        user_id = event.get("user_id")
        if event_date and user_id:
            users_by_date[event_date].add(user_id)

    return [
        {"date": date, "dau": len(users)}
        for date, users in sorted(users_by_date.items())
    ]
