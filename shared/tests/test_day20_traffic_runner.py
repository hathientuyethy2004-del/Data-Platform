from shared.platform.migration_templates.day20_traffic_runner import evaluate_day20_traffic


def _day19(status: str = "READ_SWITCHED_50", applied: bool = True):
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


def _env(target: int = 80, current: int = 50, audit: bool = True):
    value = "true" if audit else "false"
    return {
        "TOTAL_TRAFFIC_PERCENT": str(target),
        "CURRENT_TOTAL_TRAFFIC_PERCENT": str(current),
        "PERMISSION_AUDIT_PASS": value,
        "SECRET_ROTATION_CHECK_PASS": value,
        "RATE_LIMIT_AUDIT_PASS": value,
    }


def test_day20_traffic_applies_when_prereqs_pass():
    report = evaluate_day20_traffic(
        day19_report=_day19("READ_SWITCHED_50", True),
        day15_scale_report=_day15(50),
        env20=_env(80, 50, True),
    )

    assert report["summary"]["status"] == "TRAFFIC_80_APPLIED"
    assert report["traffic"]["applied"] is True
    assert report["traffic"]["effective_total_percent"] == 80


def test_day20_traffic_blocked_when_day19_not_switched():
    report = evaluate_day20_traffic(
        day19_report=_day19("BLOCKED", False),
        day15_scale_report=_day15(50),
        env20=_env(80, 50, True),
    )

    assert report["summary"]["status"] == "BLOCKED"
    assert "day19_read_switch_50_required" in report["traffic"]["blockers"]


def test_day20_traffic_blocked_when_audit_fails():
    report = evaluate_day20_traffic(
        day19_report=_day19("READ_SWITCHED_50", True),
        day15_scale_report=_day15(50),
        env20=_env(80, 50, False),
    )

    assert report["summary"]["status"] == "BLOCKED"
    assert "permission_audit_passed" in report["traffic"]["blockers"]
