from datetime import datetime, timedelta, timezone

from shared.platform.migration_templates.day7_gate_runner import evaluate_gate


def _smoke_report(status: str = "PASS"):
    return {"overall_status": status}


def _day6_report(status: str = "PASS"):
    return {"result": {"status": status}}


def _baseline_report(hours_ago: int, critical_issues: int = 0):
    run_ts = (datetime.now(timezone.utc) - timedelta(hours=hours_ago)).isoformat()
    return {
        "run_ts": run_ts,
        "summary": {
            "overall_status": "PASS",
            "critical_issues": critical_issues,
        },
        "issues": [],
    }


def test_gate_passes_when_stability_reached_and_no_critical_issues():
    report, code = evaluate_gate(
        baseline_report=_baseline_report(hours_ago=25, critical_issues=0),
        smoke_report=_smoke_report("PASS"),
        day6_regression_report=_day6_report("PASS"),
        min_stability_hours=24,
    )

    assert code == 0
    assert report["summary"]["status"] == "PASS"
    assert report["summary"]["allow_move_to_week2"] is True
    assert report["summary"]["remaining_hours_to_gate"] == 0.0
    assert report["checks"]["dual_run_staging_stable_24h"]["remaining_hours_to_gate"] == 0.0
    assert report["summary"]["estimated_pass_at_utc"]


def test_gate_fails_when_stability_window_not_enough():
    report, code = evaluate_gate(
        baseline_report=_baseline_report(hours_ago=1, critical_issues=0),
        smoke_report=_smoke_report("PASS"),
        day6_regression_report=_day6_report("PASS"),
        min_stability_hours=24,
    )

    assert code == 2
    assert report["summary"]["status"] == "FAIL"
    assert report["checks"]["dual_run_staging_stable_24h"]["status"] == "FAIL"
    assert report["summary"]["remaining_hours_to_gate"] > 0
    assert report["checks"]["dual_run_staging_stable_24h"]["estimated_pass_at_utc"]
