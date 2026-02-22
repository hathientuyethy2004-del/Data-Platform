from __future__ import annotations

import pytest
from fastapi.testclient import TestClient

from shared.platform.api.main import app


@pytest.fixture
def client() -> TestClient:
    return TestClient(app)


def auth_headers(token: str = 'viewer-token', request_id: str = 'req_contract_test') -> dict[str, str]:
    return {
        'Authorization': f'Bearer {token}',
        'X-Request-ID': request_id,
    }


@pytest.mark.parametrize(
    'path',
    [
        '/api/v1/alerts?status=open&limit=5',
        '/api/v1/executions?limit=5',
        '/api/v1/products?page=1&page_size=2',
        '/api/v1/governance/lineage?entity_id=web',
        '/api/v1/datalake/datasets',
    ],
)
def test_success_endpoints_follow_standard_envelope(client: TestClient, path: str):
    response = client.get(path, headers=auth_headers())

    assert response.status_code == 200
    payload = response.json()
    assert 'data' in payload
    assert 'meta' in payload
    assert payload['meta']['request_id'] == 'req_contract_test'
    assert isinstance(payload['meta']['timestamp'], str)


def test_products_not_found_returns_standard_error_envelope(client: TestClient):
    response = client.get('/api/v1/products/not-existing-product', headers=auth_headers())

    assert response.status_code == 404
    payload = response.json()
    assert payload['error']['code'] == 'NOT_FOUND'
    assert isinstance(payload['error']['message'], str)
    assert 'meta' in payload


def test_datalake_dataset_detail_contains_metadata_fields(client: TestClient):
    response = client.get('/api/v1/datalake/datasets/web-gold-hourly', headers=auth_headers())

    assert response.status_code == 200
    dataset = response.json()['data']
    assert 'row_count' in dataset
    assert 'partitions' in dataset
    assert 'last_update' in dataset
    assert 'schema_version' in dataset


def test_validation_error_envelope_for_invalid_query_param(client: TestClient):
    response = client.get('/api/v1/alerts?limit=0', headers=auth_headers())

    assert response.status_code == 422
    payload = response.json()
    assert payload['error']['code'] == 'VALIDATION_ERROR'
    assert payload['error']['message'] == 'Request validation failed'
    assert 'errors' in payload['error']['details']
    assert 'meta' in payload


def test_unauthorized_without_token_returns_standard_error(client: TestClient):
    response = client.get('/api/v1/alerts')

    assert response.status_code == 401
    payload = response.json()
    assert payload['error']['code'] == 'UNAUTHORIZED'
    assert 'meta' in payload


def test_unauthorized_with_invalid_token_returns_standard_error(client: TestClient):
    response = client.get('/api/v1/alerts', headers=auth_headers(token='invalid-token'))

    assert response.status_code == 401
    payload = response.json()
    assert payload['error']['code'] == 'UNAUTHORIZED'
    assert 'meta' in payload


def test_forbidden_action_for_viewer_returns_standard_error(client: TestClient):
    response = client.post('/api/v1/platform/actions/health-check', headers=auth_headers(token='viewer-token'))

    assert response.status_code == 403
    payload = response.json()
    assert payload['error']['code'] == 'FORBIDDEN'
    assert 'meta' in payload
