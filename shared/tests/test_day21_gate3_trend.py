from datetime import datetime, timedelta, timezone

from shared.platform.migration_templates.day21_gate3_trend import build_day21_trend_report


def _report(hours_ago: int, status: str):
    run_ts = (datetime.now(timezone.utc) - timedelta(hours=hours_ago)).isoformat()
    return {
        "run_id": f"r{hours_ago}",
        "run_ts": run_ts,
        "summary": {
            "status": status,
        },
    }


def test_day21_trend_ready_when_latest_pass():
    trend = build_day21_trend_report(
        reports=[_report(2, "NO_GO"), _report(1, "PASS")],
        window_hours=24,
    )

    assert trend["summary"]["status"] == "READY"
    assert trend["summary"]["pass_runs"] == 1
    assert trend["summary"]["last_transition_to_pass_at"] is not None


def test_day21_trend_monitoring_when_latest_no_go():
    trend = build_day21_trend_report(
        reports=[_report(2, "PASS"), _report(1, "NO_GO")],
        window_hours=24,
    )

    assert trend["summary"]["status"] == "MONITORING"
    assert trend["summary"]["no_go_runs"] == 1
