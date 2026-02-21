from shared.platform.migration_templates.day19_read_switch_runner import evaluate_day19_read_switch


def _day18(status: str = "READ_SWITCHED_30", applied: bool = True):
    return {
        "summary": {
            "status": status,
        },
        "read_switch": {
            "applied": applied,
        },
    }


def _day15(effective_percent: int = 50):
    return {
        "rollout": {
            "effective_percent": effective_percent,
        }
    }


def _env(target: int = 50, current: int = 30):
    return {
        "READ_SWITCH_PERCENT": str(target),
        "CURRENT_READ_SWITCH_PERCENT": str(current),
    }


def test_day19_read_switch_applies_when_prereqs_pass():
    report = evaluate_day19_read_switch(
        day18_report=_day18("READ_SWITCHED_30", True),
        day15_scale_report=_day15(50),
        env19=_env(50, 30),
    )

    assert report["summary"]["status"] == "READ_SWITCHED_50"
    assert report["read_switch"]["applied"] is True
    assert report["read_switch"]["effective_percent"] == 50


def test_day19_read_switch_blocked_when_day18_not_switched():
    report = evaluate_day19_read_switch(
        day18_report=_day18("BLOCKED", False),
        day15_scale_report=_day15(50),
        env19=_env(50, 30),
    )

    assert report["summary"]["status"] == "BLOCKED"
    assert "day18_read_switch_30_required" in report["read_switch"]["blockers"]


def test_day19_read_switch_blocked_when_day15_not_50():
    report = evaluate_day19_read_switch(
        day18_report=_day18("READ_SWITCHED_30", True),
        day15_scale_report=_day15(20),
        env19=_env(50, 30),
    )

    assert report["summary"]["status"] == "BLOCKED"
    assert "day15_write_scale_50_required" in report["read_switch"]["blockers"]
