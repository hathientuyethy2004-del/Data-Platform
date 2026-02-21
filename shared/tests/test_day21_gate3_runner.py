from datetime import datetime, timedelta, timezone

from shared.platform.migration_templates.day21_gate3_runner import evaluate_gate3


def _day20(hours_ago: int, status: str = "TRAFFIC_80_APPLIED", applied: bool = True, effective_percent: int = 80):
    run_ts = (datetime.now(timezone.utc) - timedelta(hours=hours_ago)).isoformat()
    return {
        "run_ts": run_ts,
        "summary": {
            "status": status,
        },
        "traffic": {
            "applied": applied,
            "effective_total_percent": effective_percent,
        },
    }


def _compare_trend(pass_rate: float = 100.0, total_runs: int = 5):
    return {
        "summary": {
            "compare_pass_rate_pct": pass_rate,
            "total_runs": total_runs,
        }
    }


def test_gate3_pass_when_all_conditions_met():
    report = evaluate_gate3(
        day20_report=_day20(hours_ago=80, status="TRAFFIC_80_APPLIED", applied=True, effective_percent=80),
        day15_compare_trend=_compare_trend(pass_rate=100.0, total_runs=6),
        min_stability_hours=72,
        min_compare_pass_rate_pct=99.5,
    )

    assert report["summary"]["status"] == "PASS"
    assert report["summary"]["approve_full_cutover_week4"] is True
    assert report["summary"]["blockers"] == []


def test_gate3_no_go_when_not_enough_stability_hours():
    report = evaluate_gate3(
        day20_report=_day20(hours_ago=2, status="TRAFFIC_80_APPLIED", applied=True, effective_percent=80),
        day15_compare_trend=_compare_trend(pass_rate=100.0, total_runs=6),
        min_stability_hours=72,
        min_compare_pass_rate_pct=99.5,
    )

    assert report["summary"]["status"] == "NO_GO"
    assert "traffic_80_stable_72h" in report["summary"]["blockers"]


def test_gate3_no_go_when_compare_rate_below_threshold():
    report = evaluate_gate3(
        day20_report=_day20(hours_ago=80, status="TRAFFIC_80_APPLIED", applied=True, effective_percent=80),
        day15_compare_trend=_compare_trend(pass_rate=98.2, total_runs=6),
        min_stability_hours=72,
        min_compare_pass_rate_pct=99.5,
    )

    assert report["summary"]["status"] == "NO_GO"
    assert "compare_pass_rate_99_5" in report["summary"]["blockers"]
