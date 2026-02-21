import os

import pytest
from fastapi import HTTPException

from shared.platform.api_gateway import APIGateway


def test_gateway_health_has_summary(monkeypatch: pytest.MonkeyPatch):
    monkeypatch.setenv(
        "PLATFORM_PRODUCT_SERVICES_JSON",
        '[{"name": "svc-a", "base_url": "http://localhost:9999"}]',
    )
    gateway = APIGateway()

    def fake_service_health(_: str):
        return {"service": "svc-a", "status": "up", "healthy": True}

    monkeypatch.setattr(gateway, "service_health", fake_service_health)
    payload = gateway.gateway_health()

    assert "summary" in payload
    assert payload["summary"]["services_total"] == 1
    assert payload["summary"]["services_enabled"] == 1
    assert payload["summary"]["services_healthy"] == 1


def test_gateway_request_raises_after_retries(monkeypatch: pytest.MonkeyPatch):
    monkeypatch.setenv("PLATFORM_GATEWAY_MAX_RETRIES", "1")
    gateway = APIGateway()

    class DummyURLError(Exception):
        reason = "connection refused"

    def raise_error(*args, **kwargs):
        raise __import__("urllib.error").error.URLError("connection refused")

    monkeypatch.setattr(__import__("urllib.request").request, "urlopen", raise_error)

    with pytest.raises(HTTPException) as exc:
        gateway._request("GET", "http://localhost:9999/health", {}, None)

    assert exc.value.status_code == 502


def teardown_module(module):
    os.environ.pop("PLATFORM_PRODUCT_SERVICES_JSON", None)
