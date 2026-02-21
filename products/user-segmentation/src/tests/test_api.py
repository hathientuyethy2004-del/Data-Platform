from fastapi.testclient import TestClient

from src.monitoring.health_checks import SegmentServiceMonitor
from src.serving.api_handlers import app, classify_segment, SegmentRequest


client = TestClient(app)


def test_health_endpoint_ok():
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json()["status"] == "healthy"


def test_classify_endpoint_returns_segment():
    response = client.post(
        "/segments/classify",
        json={
            "user_id": "u-1",
            "recency_days": 12,
            "frequency": 7,
            "monetary": 1500.0,
        },
    )
    assert response.status_code == 200
    payload = response.json()
    assert payload["segment"] == "VIP"


def test_monitor_health_degraded_when_model_not_ready():
    monitor = SegmentServiceMonitor()
    payload = monitor.health(model_ready=False)
    assert payload["status"] == "degraded"


def test_classify_segment_function_directly():
    result = classify_segment(
        SegmentRequest(user_id="u-2", recency_days=140, frequency=1, monetary=20)
    )
    assert result.segment == "Dormant"
