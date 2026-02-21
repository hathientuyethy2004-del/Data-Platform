from datetime import datetime, timedelta, timezone

from shared.platform.migration_templates.day16_observation_trend import build_day16_trend_report


def _report(hours_ago: int, status: str):
    run_ts = (datetime.now(timezone.utc) - timedelta(hours=hours_ago)).isoformat()
    return {
        "run_id": f"r{hours_ago}",
        "run_ts": run_ts,
        "summary": {
            "status": status,
        },
    }


def test_day16_trend_ready_when_latest_ready():
    trend = build_day16_trend_report(
        reports=[_report(2, "HOLD"), _report(1, "READY_FOR_DAY17")],
        window_hours=24,
    )

    assert trend["summary"]["total_runs"] == 2
    assert trend["summary"]["ready_runs"] == 1
    assert trend["summary"]["status"] == "READY"


def test_day16_trend_monitoring_when_latest_not_ready():
    trend = build_day16_trend_report(
        reports=[_report(2, "READY_FOR_DAY17"), _report(1, "HOLD")],
        window_hours=24,
    )

    assert trend["summary"]["total_runs"] == 2
    assert trend["summary"]["hold_runs"] == 1
    assert trend["summary"]["status"] == "MONITORING"
