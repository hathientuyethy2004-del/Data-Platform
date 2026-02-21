from datetime import datetime, timedelta, timezone

from shared.platform.migration_templates.day8_canary_trend import build_day8_trend_report


def _report(hours_ago: int, status: str = "PASS"):
    run_ts = (datetime.now(timezone.utc) - timedelta(hours=hours_ago)).isoformat()
    return {
        "run_id": f"r-{hours_ago}-{status}",
        "run_ts": run_ts,
        "summary": {"status": status},
        "checks": {
            "canary_write_percent_is_10": {"status": "PASS"},
            "read_path_stays_legacy": {"status": "PASS"},
            "dual_run_compare_enabled": {"status": "PASS"},
            "canary_distribution_sanity": {"status": "PASS"},
        },
    }


def test_day8_trend_pass_when_all_runs_pass_in_window():
    reports = [_report(1, "PASS"), _report(2, "PASS")]
    trend = build_day8_trend_report(reports=reports, window_hours=24)

    assert trend["summary"]["total_runs"] == 2
    assert trend["summary"]["fail_runs"] == 0
    assert trend["summary"]["status"] == "PASS"


def test_day8_trend_monitoring_when_has_fail_in_window():
    reports = [_report(1, "PASS"), _report(2, "FAIL")]
    trend = build_day8_trend_report(reports=reports, window_hours=24)

    assert trend["summary"]["total_runs"] == 2
    assert trend["summary"]["fail_runs"] == 1
    assert trend["summary"]["status"] == "MONITORING"
