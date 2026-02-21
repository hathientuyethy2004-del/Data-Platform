from shared.platform.migration_templates.day18_read_switch_runner import evaluate_day18_read_switch


def _day17(status: str = "READ_SWITCHED_10", applied: bool = True):
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


def _env(target: int = 30, current: int = 10):
    return {
        "READ_SWITCH_PERCENT": str(target),
        "CURRENT_READ_SWITCH_PERCENT": str(current),
    }


def test_day18_read_switch_applies_when_prereqs_pass():
    report = evaluate_day18_read_switch(
        day17_report=_day17("READ_SWITCHED_10", True),
        day15_scale_report=_day15(50),
        env18=_env(30, 10),
    )

    assert report["summary"]["status"] == "READ_SWITCHED_30"
    assert report["read_switch"]["applied"] is True
    assert report["read_switch"]["effective_percent"] == 30


def test_day18_read_switch_blocked_when_day17_not_switched():
    report = evaluate_day18_read_switch(
        day17_report=_day17("BLOCKED", False),
        day15_scale_report=_day15(50),
        env18=_env(30, 10),
    )

    assert report["summary"]["status"] == "BLOCKED"
    assert "day17_read_switch_10_required" in report["read_switch"]["blockers"]


def test_day18_read_switch_blocked_when_day15_not_50():
    report = evaluate_day18_read_switch(
        day17_report=_day17("READ_SWITCHED_10", True),
        day15_scale_report=_day15(20),
        env18=_env(30, 10),
    )

    assert report["summary"]["status"] == "BLOCKED"
    assert "day15_write_scale_50_required" in report["read_switch"]["blockers"]
