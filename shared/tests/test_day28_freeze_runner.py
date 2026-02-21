from shared.platform.migration_templates.day28_freeze_runner import evaluate_day28_freeze


def _day27(status: str = "VALIDATED_FOR_FREEZE", applied: bool = True):
    return {
        "summary": {
            "status": status,
        },
        "validation": {
            "applied": applied,
        },
    }


def _env(
    freeze_enabled: bool = True,
    observed_hours: int = 24,
    critical_changes: bool = False,
    slo_stable: bool = True,
    no_sev: bool = True,
    post_report_ready: bool = True,
):
    return {
        "FREEZE_WINDOW_ENABLED": "true" if freeze_enabled else "false",
        "FREEZE_OBSERVED_HOURS": str(observed_hours),
        "CRITICAL_CHANGES_DETECTED": "true" if critical_changes else "false",
        "SLO_STABLE_24H": "true" if slo_stable else "false",
        "NO_SEV1_SEV2_24H": "true" if no_sev else "false",
        "POST_CUTOVER_REPORT_READY": "true" if post_report_ready else "false",
    }


def test_day28_freeze_passes_when_all_checks_pass():
    report = evaluate_day28_freeze(
        day27_report=_day27("VALIDATED_FOR_FREEZE", True),
        env28=_env(),
    )

    assert report["summary"]["status"] == "FREEZE_LOCKED_REPORT_FINALIZED"
    assert report["summary"]["ready_for_day29"] is True
    assert report["freeze"]["blockers"] == []


def test_day28_freeze_blocked_when_day27_not_validated():
    report = evaluate_day28_freeze(
        day27_report=_day27("BLOCKED", False),
        env28=_env(),
    )

    assert report["summary"]["status"] == "BLOCKED"
    assert "day27_validated_required" in report["freeze"]["blockers"]


def test_day28_freeze_blocked_when_freeze_window_not_24h():
    report = evaluate_day28_freeze(
        day27_report=_day27("VALIDATED_FOR_FREEZE", True),
        env28=_env(observed_hours=8),
    )

    assert report["summary"]["status"] == "BLOCKED"
    assert "freeze_observed_24h" in report["freeze"]["blockers"]
