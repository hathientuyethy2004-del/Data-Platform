from shared.platform.migration_templates.day29_decommission_runner import evaluate_day29_decommission


def _day28(status: str = "FREEZE_LOCKED_REPORT_FINALIZED", applied: bool = True):
    return {
        "summary": {
            "status": status,
        },
        "freeze": {
            "applied": applied,
        },
    }


def _env(
    cron: bool = True,
    jobs: bool = True,
    routes: bool = True,
    configs: bool = True,
    backup: bool = True,
    runbook: bool = True,
    snapshot: bool = True,
    dry_run: bool = True,
):
    return {
        "LEGACY_CRON_REMOVED": "true" if cron else "false",
        "LEGACY_JOBS_DISABLED": "true" if jobs else "false",
        "LEGACY_ROUTES_DISABLED": "true" if routes else "false",
        "LEGACY_CONFIGS_ARCHIVED": "true" if configs else "false",
        "BACKUP_CONFIG_DONE": "true" if backup else "false",
        "RUNBOOK_FINALIZED": "true" if runbook else "false",
        "ROLLBACK_SNAPSHOT_CREATED": "true" if snapshot else "false",
        "DECOMMISSION_DRY_RUN_PASS": "true" if dry_run else "false",
    }


def test_day29_decommission_passes_when_all_checks_pass():
    report = evaluate_day29_decommission(
        day28_report=_day28("FREEZE_LOCKED_REPORT_FINALIZED", True),
        env29=_env(),
    )

    assert report["summary"]["status"] == "DECOMMISSIONED_WITH_BACKUP"
    assert report["summary"]["ready_for_day30"] is True
    assert report["decommission"]["blockers"] == []


def test_day29_decommission_blocked_when_day28_not_ready():
    report = evaluate_day29_decommission(
        day28_report=_day28("BLOCKED", False),
        env29=_env(),
    )

    assert report["summary"]["status"] == "BLOCKED"
    assert "day28_freeze_required" in report["decommission"]["blockers"]


def test_day29_decommission_blocked_when_backup_not_done():
    report = evaluate_day29_decommission(
        day28_report=_day28("FREEZE_LOCKED_REPORT_FINALIZED", True),
        env29=_env(backup=False),
    )

    assert report["summary"]["status"] == "BLOCKED"
    assert "backup_config_done" in report["decommission"]["blockers"]
