from shared.platform.migration_templates.day16_observation_runner import evaluate_day16_observation


def _day15_scale(status: str = "SCALED_TO_50", applied: bool = True, effective_percent: int = 50):
    return {
        "summary": {"status": status},
        "rollout": {
            "applied": applied,
            "effective_percent": effective_percent,
        },
    }


def _day15_trend(status: str = "PASS", runs: int = 8, pass_rate: float = 100.0):
    return {
        "summary": {
            "status": status,
            "total_runs": runs,
            "compare_pass_rate_pct": pass_rate,
        }
    }


def _cron(status: str = "PASS", day14: str = "PASS", day15: str = "PASS"):
    return {
        "status": status,
        "checks": {
            "day14_gate2_hourly": {"status": day14},
            "day15_compare_hourly": {"status": day15},
        },
    }


def test_day16_ready_when_all_conditions_met():
    report = evaluate_day16_observation(
        day15_scale_report=_day15_scale(),
        day15_trend_report=_day15_trend(),
        cron_health_report=_cron(),
        min_trend_runs=6,
        min_compare_pass_rate_pct=99.0,
    )

    assert report["summary"]["status"] == "READY_FOR_DAY17"
    assert report["summary"]["ready_for_day17_read_switch"] is True
    assert report["summary"]["blockers"] == []


def test_day16_hold_when_day15_not_scaled_to_50():
    report = evaluate_day16_observation(
        day15_scale_report=_day15_scale(status="BLOCKED", applied=False, effective_percent=20),
        day15_trend_report=_day15_trend(),
        cron_health_report=_cron(),
        min_trend_runs=6,
        min_compare_pass_rate_pct=99.0,
    )

    assert report["summary"]["status"] == "HOLD"
    assert "day15_scaled_to_50" in report["summary"]["blockers"]


def test_day16_hold_when_trend_not_enough_runs():
    report = evaluate_day16_observation(
        day15_scale_report=_day15_scale(),
        day15_trend_report=_day15_trend(status="PASS", runs=2, pass_rate=100.0),
        cron_health_report=_cron(),
        min_trend_runs=6,
        min_compare_pass_rate_pct=99.0,
    )

    assert report["summary"]["status"] == "HOLD"
    assert "day15_compare_trend_stable" in report["summary"]["blockers"]
