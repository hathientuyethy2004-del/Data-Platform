from shared.platform.migration_templates.day22_24_cutover_runner import evaluate_day22_24_cutover


def _day21(status: str = "PASS", approve: bool = True):
    return {
        "summary": {
            "status": status,
            "approve_full_cutover_week4": approve,
        }
    }


def _day20(effective_total_percent: int = 80):
    return {
        "traffic": {
            "effective_total_percent": effective_total_percent,
        }
    }


def _env(target: int = 100, current: int = 80, shadow_enabled: bool = True, shadow_days: int = 3):
    return {
        "WRITE_LOAD_PERCENT": str(target),
        "CURRENT_WRITE_LOAD_PERCENT": str(current),
        "SHADOW_READ_LEGACY_ENABLED": "true" if shadow_enabled else "false",
        "SHADOW_READ_WINDOW_DAYS": str(shadow_days),
    }


def test_day22_24_cutover_applies_when_prereqs_pass():
    report = evaluate_day22_24_cutover(
        day21_report=_day21("PASS", True),
        day20_report=_day20(80),
        env22_24=_env(100, 80, True, 3),
    )

    assert report["summary"]["status"] == "WRITE_LOAD_100_SHADOW_READ"
    assert report["cutover"]["applied"] is True
    assert report["cutover"]["effective_write_load_percent"] == 100


def test_day22_24_cutover_blocked_when_day21_not_passed():
    report = evaluate_day22_24_cutover(
        day21_report=_day21("NO_GO", False),
        day20_report=_day20(80),
        env22_24=_env(100, 80, True, 3),
    )

    assert report["summary"]["status"] == "BLOCKED"
    assert "day21_gate3_pass_required" in report["cutover"]["blockers"]


def test_day22_24_cutover_blocked_when_shadow_window_invalid():
    report = evaluate_day22_24_cutover(
        day21_report=_day21("PASS", True),
        day20_report=_day20(80),
        env22_24=_env(100, 80, True, 5),
    )

    assert report["summary"]["status"] == "BLOCKED"
    assert "shadow_read_window_2_3_days" in report["cutover"]["blockers"]
