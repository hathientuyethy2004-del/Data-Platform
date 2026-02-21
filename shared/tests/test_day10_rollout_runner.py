from shared.platform.migration_templates.day10_rollout_runner import evaluate_day10_rollout


def _day9(status: str, blockers=None):
    return {
        "summary": {
            "status": status,
            "blockers": blockers or [],
        }
    }


def _day8(current_percent: int = 10):
    return {"config": {"oss_canary_write_percent": current_percent}}


def _env(target: int = 20, read_from_oss: str = "false"):
    return {
        "OSS_CANARY_WRITE_PERCENT": str(target),
        "READ_FROM_OSS_SERVING": read_from_oss,
        "DUAL_RUN_ENABLED": "true",
        "DUAL_RUN_COMPARE_ENABLED": "true",
    }


def test_day10_rollout_applies_when_day9_go():
    report = evaluate_day10_rollout(
        day9_report=_day9("GO"),
        env10=_env(20, "false"),
        current_day8_status=_day8(10),
    )

    assert report["summary"]["status"] == "ROLLED_OUT"
    assert report["rollout"]["applied"] is True
    assert report["rollout"]["effective_percent"] == 20
    assert report["load_backpressure"]["overall_status"] == "PASS"


def test_day10_rollout_blocked_when_day9_no_go():
    report = evaluate_day10_rollout(
        day9_report=_day9("NO_GO", blockers=["gate1_week1_passed"]),
        env10=_env(20, "false"),
        current_day8_status=_day8(10),
    )

    assert report["summary"]["status"] == "BLOCKED"
    assert report["rollout"]["applied"] is False
    assert report["rollout"]["effective_percent"] == 10
    assert "gate1_week1_passed" in report["rollout"]["blockers"]
