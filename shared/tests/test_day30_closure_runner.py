from shared.platform.migration_templates.day30_closure_runner import evaluate_day30_closure


def _day29(status: str = "DECOMMISSIONED_WITH_BACKUP", applied: bool = True):
    return {
        "summary": {
            "status": status,
        },
        "decommission": {
            "applied": applied,
        },
    }


def _env(
    acceptance: bool = True,
    lessons: bool = True,
    optimization: bool = True,
):
    return {
        "TECHNICAL_ACCEPTANCE_SIGNED": "true" if acceptance else "false",
        "LESSONS_LEARNED_PUBLISHED": "true" if lessons else "false",
        "OPTIMIZATION_PHASE_KICKOFF": "true" if optimization else "false",
    }


def test_day30_closure_passes_when_all_checks_pass():
    report = evaluate_day30_closure(
        day29_report=_day29("DECOMMISSIONED_WITH_BACKUP", True),
        env30=_env(),
    )

    assert report["summary"]["status"] == "GO_LIVE_CLOSED"
    assert report["summary"]["migration_closed"] is True
    assert report["closure"]["blockers"] == []


def test_day30_closure_blocked_when_day29_not_ready():
    report = evaluate_day30_closure(
        day29_report=_day29("BLOCKED", False),
        env30=_env(),
    )

    assert report["summary"]["status"] == "BLOCKED"
    assert "day29_decommission_required" in report["closure"]["blockers"]


def test_day30_closure_blocked_when_acceptance_not_signed():
    report = evaluate_day30_closure(
        day29_report=_day29("DECOMMISSIONED_WITH_BACKUP", True),
        env30=_env(acceptance=False),
    )

    assert report["summary"]["status"] == "BLOCKED"
    assert "technical_acceptance_signed" in report["closure"]["blockers"]
