from shared.platform.migration_templates.day25_26_read_cutover_runner import evaluate_day25_26_read_cutover


def _day22_24(status: str = "WRITE_LOAD_100_SHADOW_READ", applied: bool = True):
    return {
        "summary": {
            "status": status,
        },
        "cutover": {
            "applied": applied,
        },
    }


def _day21(status: str = "PASS", approve: bool = True):
    return {
        "summary": {
            "status": status,
            "approve_full_cutover_week4": approve,
        }
    }


def _env(target: int = 100, current: int = 50, jobs: bool = True, routes: bool = True, configs: bool = True):
    return {
        "READ_SWITCH_PERCENT": str(target),
        "CURRENT_READ_SWITCH_PERCENT": str(current),
        "LEGACY_JOBS_DISABLED": "true" if jobs else "false",
        "LEGACY_ROUTES_DISABLED": "true" if routes else "false",
        "LEGACY_CONFIGS_ARCHIVED": "true" if configs else "false",
    }


def test_day25_26_read_cutover_applies_when_prereqs_pass():
    report = evaluate_day25_26_read_cutover(
        day22_24_report=_day22_24("WRITE_LOAD_100_SHADOW_READ", True),
        day21_report=_day21("PASS", True),
        env25_26=_env(100, 50, True, True, True),
    )

    assert report["summary"]["status"] == "READ_PATH_100_LEGACY_DRAINING"
    assert report["read_cutover"]["applied"] is True
    assert report["read_cutover"]["effective_read_switch_percent"] == 100


def test_day25_26_read_cutover_blocked_when_day22_24_not_ready():
    report = evaluate_day25_26_read_cutover(
        day22_24_report=_day22_24("BLOCKED", False),
        day21_report=_day21("PASS", True),
        env25_26=_env(100, 50, True, True, True),
    )

    assert report["summary"]["status"] == "BLOCKED"
    assert "day22_24_cutover_required" in report["read_cutover"]["blockers"]


def test_day25_26_read_cutover_blocked_when_legacy_not_drained():
    report = evaluate_day25_26_read_cutover(
        day22_24_report=_day22_24("WRITE_LOAD_100_SHADOW_READ", True),
        day21_report=_day21("PASS", True),
        env25_26=_env(100, 50, jobs=False, routes=True, configs=True),
    )

    assert report["summary"]["status"] == "BLOCKED"
    assert "legacy_jobs_disabled" in report["read_cutover"]["blockers"]
