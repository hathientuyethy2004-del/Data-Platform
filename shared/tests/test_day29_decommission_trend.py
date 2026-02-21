from datetime import datetime, timedelta, timezone

from shared.platform.migration_templates.day29_decommission_trend import build_day29_trend_report


def _report(hours_ago: int, status: str):
    run_ts = (datetime.now(timezone.utc) - timedelta(hours=hours_ago)).isoformat()
    return {
        "run_id": f"r{hours_ago}",
        "run_ts": run_ts,
        "summary": {
            "status": status,
        },
    }


def test_day29_trend_ready_when_latest_decommissioned():
    trend = build_day29_trend_report(
        reports=[_report(2, "BLOCKED"), _report(1, "DECOMMISSIONED_WITH_BACKUP")],
        window_hours=24,
    )

    assert trend["summary"]["status"] == "READY"
    assert trend["summary"]["decommissioned_with_backup_runs"] == 1
    assert trend["summary"]["last_transition_to_decommissioned_with_backup_at"] is not None


def test_day29_trend_monitoring_when_latest_blocked():
    trend = build_day29_trend_report(
        reports=[_report(2, "DECOMMISSIONED_WITH_BACKUP"), _report(1, "BLOCKED")],
        window_hours=24,
    )

    assert trend["summary"]["status"] == "MONITORING"
    assert trend["summary"]["blocked_runs"] == 1
