from shared.platform.migration_templates.day9_readiness_runner import evaluate_day9_readiness


def _day8_status(ready: bool):
    return {"summary": {"day8_canary_ready": ready}}


def _day8_trend(total_runs: int, fail_runs: int, pass_rate: float):
    return {
        "summary": {
            "total_runs": total_runs,
            "fail_runs": fail_runs,
            "overall_pass_rate_pct": pass_rate,
        }
    }


def _day7_gate(status: str):
    return {
        "summary": {
            "status": status,
            "remaining_hours_to_gate": 0 if status == "PASS" else 5.0,
            "estimated_pass_at_utc": "2026-02-22T00:00:00+00:00",
        }
    }


def test_day9_go_when_all_checks_pass():
    report = evaluate_day9_readiness(
        day8_status=_day8_status(True),
        day8_trend=_day8_trend(total_runs=8, fail_runs=0, pass_rate=100.0),
        day7_gate=_day7_gate("PASS"),
        min_trend_runs=6,
        required_pass_rate_pct=99.0,
    )

    assert report["summary"]["status"] == "GO"
    assert report["summary"]["ready_for_day10_canary_20"] is True
    assert report["summary"]["blockers"] == []


def test_day9_no_go_when_gate_or_trend_not_ready():
    report = evaluate_day9_readiness(
        day8_status=_day8_status(True),
        day8_trend=_day8_trend(total_runs=2, fail_runs=1, pass_rate=50.0),
        day7_gate=_day7_gate("FAIL"),
        min_trend_runs=6,
        required_pass_rate_pct=99.0,
    )

    assert report["summary"]["status"] == "NO_GO"
    assert report["summary"]["ready_for_day10_canary_20"] is False
    assert "trend_has_minimum_runs" in report["summary"]["blockers"]
    assert "trend_has_no_fail_runs" in report["summary"]["blockers"]
    assert "gate1_week1_passed" in report["summary"]["blockers"]
