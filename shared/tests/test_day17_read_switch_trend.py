from datetime import datetime, timedelta, timezone

from shared.platform.migration_templates.day17_read_switch_trend import build_day17_trend_report


def _report(hours_ago: int, status: str):
    run_ts = (datetime.now(timezone.utc) - timedelta(hours=hours_ago)).isoformat()
    return {
        "run_id": f"r{hours_ago}",
        "run_ts": run_ts,
        "summary": {
            "status": status,
        },
    }


def test_day17_trend_ready_when_latest_switched():
    trend = build_day17_trend_report(
        reports=[_report(2, "BLOCKED"), _report(1, "READ_SWITCHED_10")],
        window_hours=24,
    )

    assert trend["summary"]["status"] == "READY"
    assert trend["summary"]["read_switched_10_runs"] == 1
    assert trend["summary"]["last_transition_to_read_switched_10_at"] is not None


def test_day17_trend_monitoring_when_latest_blocked():
    trend = build_day17_trend_report(
        reports=[_report(2, "READ_SWITCHED_10"), _report(1, "BLOCKED")],
        window_hours=24,
    )

    assert trend["summary"]["status"] == "MONITORING"
    assert trend["summary"]["blocked_runs"] == 1
