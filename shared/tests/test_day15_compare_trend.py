from datetime import datetime, timedelta, timezone

from shared.platform.migration_templates.day15_compare_trend import build_day15_compare_trend_report


def _report(hours_ago: int, compare_ok: bool, rollout_status: str = "BLOCKED"):
    run_ts = (datetime.now(timezone.utc) - timedelta(hours=hours_ago)).isoformat()
    return {
        "run_id": f"r{hours_ago}",
        "run_ts": run_ts,
        "checks": {
            "dual_run_compare_hourly_enabled": {
                "status": "PASS" if compare_ok else "FAIL",
            }
        },
        "rollout": {
            "status": rollout_status,
        },
    }


def test_day15_compare_trend_pass_when_all_compare_checks_pass():
    reports = [
        _report(hours_ago=1, compare_ok=True, rollout_status="BLOCKED"),
        _report(hours_ago=2, compare_ok=True, rollout_status="SCALED_TO_50"),
    ]

    trend = build_day15_compare_trend_report(reports, window_hours=24)

    assert trend["summary"]["status"] == "PASS"
    assert trend["summary"]["total_runs"] == 2
    assert trend["summary"]["compare_fail_runs"] == 0


def test_day15_compare_trend_monitoring_when_compare_fails_exist():
    reports = [
        _report(hours_ago=1, compare_ok=True, rollout_status="BLOCKED"),
        _report(hours_ago=2, compare_ok=False, rollout_status="BLOCKED"),
    ]

    trend = build_day15_compare_trend_report(reports, window_hours=24)

    assert trend["summary"]["status"] == "MONITORING"
    assert trend["summary"]["total_runs"] == 2
    assert trend["summary"]["compare_fail_runs"] == 1
