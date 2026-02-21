from datetime import datetime, timedelta, timezone

from shared.platform.migration_templates.day28_freeze_trend import build_day28_trend_report


def _report(hours_ago: int, status: str):
    run_ts = (datetime.now(timezone.utc) - timedelta(hours=hours_ago)).isoformat()
    return {
        "run_id": f"r{hours_ago}",
        "run_ts": run_ts,
        "summary": {
            "status": status,
        },
    }


def test_day28_trend_ready_when_latest_finalized():
    trend = build_day28_trend_report(
        reports=[_report(2, "BLOCKED"), _report(1, "FREEZE_LOCKED_REPORT_FINALIZED")],
        window_hours=24,
    )

    assert trend["summary"]["status"] == "READY"
    assert trend["summary"]["freeze_locked_report_finalized_runs"] == 1
    assert trend["summary"]["last_transition_to_freeze_locked_report_finalized_at"] is not None


def test_day28_trend_monitoring_when_latest_blocked():
    trend = build_day28_trend_report(
        reports=[_report(2, "FREEZE_LOCKED_REPORT_FINALIZED"), _report(1, "BLOCKED")],
        window_hours=24,
    )

    assert trend["summary"]["status"] == "MONITORING"
    assert trend["summary"]["blocked_runs"] == 1
