from shared.platform.migration_templates.day15_scale_runner import evaluate_day15_scale


def _day14(status: str = "PASS", approved: bool = True):
    return {
        "summary": {
            "status": status,
            "approve_scale_week3": approved,
        }
    }


def _day10(current_percent: int = 20):
    return {
        "rollout": {
            "effective_percent": current_percent,
        }
    }


def _env(target: int = 50, compare_hourly: str = "true", read_from_oss: str = "false"):
    return {
        "OSS_CANARY_WRITE_PERCENT": str(target),
        "DUAL_RUN_COMPARE_HOURLY": compare_hourly,
        "READ_FROM_OSS_SERVING": read_from_oss,
    }


def test_day15_scale_applies_when_gate2_passed():
    report = evaluate_day15_scale(
        day14_report=_day14("PASS", True),
        day10_report=_day10(20),
        env15=_env(50, "true", "false"),
    )

    assert report["summary"]["status"] == "SCALED_TO_50"
    assert report["rollout"]["applied"] is True
    assert report["rollout"]["effective_percent"] == 50


def test_day15_scale_blocked_when_gate2_no_go():
    report = evaluate_day15_scale(
        day14_report=_day14("NO_GO", False),
        day10_report=_day10(20),
        env15=_env(50, "true", "false"),
    )

    assert report["summary"]["status"] == "BLOCKED"
    assert report["rollout"]["applied"] is False
    assert "gate2_pass_required" in report["rollout"]["blockers"]
