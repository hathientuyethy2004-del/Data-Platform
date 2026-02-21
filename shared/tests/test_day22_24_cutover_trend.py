from datetime import datetime, timedelta, timezone

from shared.platform.migration_templates.day22_24_cutover_trend import build_day22_24_trend_report


def _report(hours_ago: int, status: str):
    run_ts = (datetime.now(timezone.utc) - timedelta(hours=hours_ago)).isoformat()
    return {
        "run_id": f"r{hours_ago}",
        "run_ts": run_ts,
        "summary": {
            "status": status,
        },
    }


def test_day22_24_trend_ready_when_latest_applied():
    trend = build_day22_24_trend_report(
        reports=[_report(2, "BLOCKED"), _report(1, "WRITE_LOAD_100_SHADOW_READ")],
        window_hours=24,
    )

    assert trend["summary"]["status"] == "READY"
    assert trend["summary"]["write_load_100_shadow_read_runs"] == 1
    assert trend["summary"]["last_transition_to_write_load_100_shadow_read_at"] is not None


def test_day22_24_trend_monitoring_when_latest_blocked():
    trend = build_day22_24_trend_report(
        reports=[_report(2, "WRITE_LOAD_100_SHADOW_READ"), _report(1, "BLOCKED")],
        window_hours=24,
    )

    assert trend["summary"]["status"] == "MONITORING"
    assert trend["summary"]["blocked_runs"] == 1
