from __future__ import annotations

from datetime import datetime, timezone


def open_alerts() -> list[dict[str, str]]:
    now = datetime.now(timezone.utc).isoformat()
    return [
        {
            'id': 'al_001',
            'severity': 'warning',
            'source': 'operational-metrics',
            'title': 'Data freshness lag above threshold',
            'status': 'open',
            'created_at': now,
            'last_seen_at': now,
        }
    ]


def recent_executions() -> list[dict[str, str]]:
    now = datetime.now(timezone.utc).isoformat()
    return [
        {
            'execution_id': 'exe_001',
            'scope': 'product',
            'target': 'web-user-analytics',
            'type': 'test_run',
            'status': 'success',
            'started_at': now,
            'finished_at': now,
            'duration_seconds': '1.2',
            'triggered_by': 'system',
        }
    ]
