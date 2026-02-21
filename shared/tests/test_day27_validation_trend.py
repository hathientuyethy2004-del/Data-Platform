from datetime import datetime, timedelta, timezone

from shared.platform.migration_templates.day27_validation_trend import build_day27_trend_report


def _report(hours_ago: int, status: str):
    run_ts = (datetime.now(timezone.utc) - timedelta(hours=hours_ago)).isoformat()
    return {
        "run_id": f"r{hours_ago}",
        "run_ts": run_ts,
        "summary": {
            "status": status,
        },
    }


def test_day27_trend_ready_when_latest_validated():
    trend = build_day27_trend_report(
        reports=[_report(2, "BLOCKED"), _report(1, "VALIDATED_FOR_FREEZE")],
        window_hours=24,
    )

    assert trend["summary"]["status"] == "READY"
    assert trend["summary"]["validated_for_freeze_runs"] == 1
    assert trend["summary"]["last_transition_to_validated_for_freeze_at"] is not None


def test_day27_trend_monitoring_when_latest_blocked():
    trend = build_day27_trend_report(
        reports=[_report(2, "VALIDATED_FOR_FREEZE"), _report(1, "BLOCKED")],
        window_hours=24,
    )

    assert trend["summary"]["status"] == "MONITORING"
    assert trend["summary"]["blocked_runs"] == 1
