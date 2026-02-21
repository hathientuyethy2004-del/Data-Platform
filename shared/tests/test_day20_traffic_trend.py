from datetime import datetime, timedelta, timezone

from shared.platform.migration_templates.day20_traffic_trend import build_day20_trend_report


def _report(hours_ago: int, status: str):
    run_ts = (datetime.now(timezone.utc) - timedelta(hours=hours_ago)).isoformat()
    return {
        "run_id": f"r{hours_ago}",
        "run_ts": run_ts,
        "summary": {
            "status": status,
        },
    }


def test_day20_trend_ready_when_latest_applied():
    trend = build_day20_trend_report(
        reports=[_report(2, "BLOCKED"), _report(1, "TRAFFIC_80_APPLIED")],
        window_hours=24,
    )

    assert trend["summary"]["status"] == "READY"
    assert trend["summary"]["traffic_80_applied_runs"] == 1
    assert trend["summary"]["last_transition_to_traffic_80_applied_at"] is not None


def test_day20_trend_monitoring_when_latest_blocked():
    trend = build_day20_trend_report(
        reports=[_report(2, "TRAFFIC_80_APPLIED"), _report(1, "BLOCKED")],
        window_hours=24,
    )

    assert trend["summary"]["status"] == "MONITORING"
    assert trend["summary"]["blocked_runs"] == 1
