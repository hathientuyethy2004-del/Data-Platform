from __future__ import annotations

from datetime import datetime, timezone

from fastapi import APIRouter, Depends, Query, Request

from ..auth import require_role
from ..deps import ok_response

router = APIRouter(
    prefix='/api/v1/governance',
    tags=['governance'],
    dependencies=[Depends(require_role('viewer'))],
)


@router.get('/access-logs')
def access_logs(request: Request) -> dict:
    now = datetime.now(timezone.utc).isoformat()
    rows = [{'user': 'operator', 'resource': 'web-user-analytics', 'action': 'read', 'timestamp': now}]
    return ok_response(rows, request)


@router.get('/lineage')
def lineage(request: Request, entity_id: str | None = Query(default=None)) -> dict:
    graph = {
        'nodes': ['topic_web_events', 'web_bronze', 'web_silver', 'web_gold_hourly'],
        'edges': [
            ['topic_web_events', 'web_bronze'],
            ['web_bronze', 'web_silver'],
            ['web_silver', 'web_gold_hourly'],
        ],
    }
    if entity_id:
        graph = {
            'nodes': [node for node in graph['nodes'] if entity_id in node],
            'edges': [edge for edge in graph['edges'] if entity_id in edge[0] or entity_id in edge[1]],
        }
    return ok_response(graph, request)


@router.get('/policies')
def policies(request: Request) -> dict:
    rows = [{'id': 'retention-001', 'name': 'PII retention', 'status': 'active'}]
    return ok_response(rows, request)


@router.get('/incidents')
def incidents(request: Request) -> dict:
    now = datetime.now(timezone.utc).isoformat()
    rows = [{'id': 'inc-001', 'severity': 'warning', 'title': 'Freshness lag', 'status': 'open', 'created_at': now}]
    return ok_response(rows, request)
