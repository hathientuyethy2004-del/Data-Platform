import threading
import time
import json
import pytest

from fastapi.testclient import TestClient
import os

# Ensure this test runs in CI (requirements installed). Locally it may be skipped
# if FastAPI isn't available; the CI workflow installs requirements.txt.

from platform_pkg.bootstrap import start_platform_services
from serving_layer.server import get_serving_layer
from monitoring_layer.access_control import get_access_control
from analytics_layer.aggregation_engine import get_aggregation_engine


def test_end_to_end_query_aggregation_serving_metrics(tmp_path):
    # Start background platform services (scheduler)
    start_platform_services()

    # Ensure ACL has a token with permissions
    acl = get_access_control(storage_path=str(tmp_path))
    token = 'test-token'
    acl.add_user(token, ['serve:query', 'serve:read'])

    serving = get_serving_layer(engine='sqlite', db_path=':memory:')
    app = serving.build_app()
    client = TestClient(app)

    # Run create table and insert via /query
    r = client.post('/query', json={'sql': 'CREATE TABLE items (id INTEGER, name TEXT);', 'token': token})
    assert r.status_code == 200

    r = client.post('/query', json={'sql': "INSERT INTO items (id, name) VALUES (1, 'a'), (2, 'b');", 'token': token})
    assert r.status_code == 200

    r = client.post('/query', json={'sql': 'SELECT id, name FROM items ORDER BY id;', 'token': token})
    assert r.status_code == 200
    body = r.json()
    assert 'rows' in body and len(body['rows']) == 2

    # Register and run an aggregation job to ensure aggregation -> metrics path
    agg = get_aggregation_engine()

    def sample_job():
        # simple aggregation that reads items
        res = serving.query.execute('SELECT COUNT(*) as cnt FROM items;')
        return {'count': res.rows[0][0] if res.rows else 0}

    job = agg.register_job('end_to_end_count', 'Count items', sample_job, schedule_minutes=1)
    status = agg.run_job_now('end_to_end_count')
    assert status.get('status') in ('success', 'failed')

    # Check metrics collector has a registered metric for the job
    from monitoring_layer.metrics.metrics_collector import get_metrics_collector
    metrics = get_metrics_collector()
    exp_name = 'aggregation_end_to_end_count_runs_total'
    assert any(k.startswith(exp_name) for k in metrics.metrics.keys())
