from shared.platform.migration_templates.day17_read_switch_runner import evaluate_day17_read_switch


def _day16(status: str = "READY_FOR_DAY17", ready: bool = True):
    return {
        "summary": {
            "status": status,
            "ready_for_day17_read_switch": ready,
        }
    }


def _day15(effective_percent: int = 50):
    return {
        "rollout": {
            "effective_percent": effective_percent,
        }
    }


def _env(target: int = 10, current: int = 0):
    return {
        "READ_SWITCH_PERCENT": str(target),
        "CURRENT_READ_SWITCH_PERCENT": str(current),
        "READ_FROM_OSS_SERVING": "true",
    }


def test_day17_read_switch_applies_when_ready_and_healthy():
    report = evaluate_day17_read_switch(
        day16_report=_day16("READY_FOR_DAY17", True),
        day15_scale_report=_day15(50),
        env17=_env(10, 0),
    )

    assert report["summary"]["status"] == "READ_SWITCHED_10"
    assert report["read_switch"]["applied"] is True
    assert report["read_switch"]["effective_percent"] == 10


def test_day17_read_switch_blocked_when_day16_hold():
    report = evaluate_day17_read_switch(
        day16_report=_day16("HOLD", False),
        day15_scale_report=_day15(50),
        env17=_env(10, 0),
    )

    assert report["summary"]["status"] == "BLOCKED"
    assert report["read_switch"]["applied"] is False
    assert "day16_ready_required" in report["read_switch"]["blockers"]


def test_day17_read_switch_blocked_when_write_scale_below_50():
    report = evaluate_day17_read_switch(
        day16_report=_day16("READY_FOR_DAY17", True),
        day15_scale_report=_day15(20),
        env17=_env(10, 0),
    )

    assert report["summary"]["status"] == "BLOCKED"
    assert "day15_write_scale_50_required" in report["read_switch"]["blockers"]
