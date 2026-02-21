from datetime import datetime, timezone

from fastapi.testclient import TestClient

from src.ingestion.consumer import MobileEventsConsumer
from src.serving.api_handlers import app
from src.storage.gold_metrics import compute_daily_active_users


client = TestClient(app)


def test_consumer_accepts_valid_event():
    consumer = MobileEventsConsumer()
    result = consumer.process_event(
        {
            "event_id": "evt-1",
            "user_id": "u-1",
            "session_id": "s-1",
            "event_type": "app_open",
            "timestamp": datetime.now(timezone.utc),
            "app_version": "1.0.0",
            "device_os": "ios",
        }
    )
    assert result["status"] == "accepted"


def test_compute_dau_basic():
    rows = compute_daily_active_users(
        [
            {"event_date": "2026-02-21", "user_id": "u-1"},
            {"event_date": "2026-02-21", "user_id": "u-2"},
            {"event_date": "2026-02-21", "user_id": "u-2"},
        ]
    )
    assert rows == [{"date": "2026-02-21", "dau": 2}]


def test_health_endpoint_ok():
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json()["status"] == "healthy"
