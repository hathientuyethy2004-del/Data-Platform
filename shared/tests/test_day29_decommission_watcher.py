from pathlib import Path

from shared.platform.migration_templates.day29_decommission_watcher import update_day29_checklist


def _checklist_text():
    return "\n".join(
        [
            "# Checklist",
            "### Ngày 29",
            "- [ ] Decommission có kiểm soát: cron/job cũ, route cũ, config cũ.",
            "- [ ] Backup config + runbook + rollback snapshot cuối.",
            "",
            "### Ngày 30 (Go-Live Closure)",
            "- [ ] Placeholder",
        ]
    ) + "\n"


def test_update_day29_keeps_unchecked_when_blocked(tmp_path: Path):
    checklist = tmp_path / "MIGRATION_CHECKLIST_30_DAYS.md"
    checklist.write_text(_checklist_text(), encoding="utf-8")

    report = {
        "summary": {"status": "BLOCKED"},
        "checks": {
            "legacy_cron_removed": {"status": "FAIL"},
            "legacy_jobs_disabled": {"status": "FAIL"},
            "legacy_routes_disabled": {"status": "FAIL"},
            "legacy_configs_archived": {"status": "FAIL"},
            "backup_config_done": {"status": "FAIL"},
            "runbook_finalized": {"status": "FAIL"},
            "rollback_snapshot_created": {"status": "FAIL"},
        },
    }

    changed, _ = update_day29_checklist(checklist, report)
    assert changed is False


def test_update_day29_marks_done_when_decommission_completed(tmp_path: Path):
    checklist = tmp_path / "MIGRATION_CHECKLIST_30_DAYS.md"
    checklist.write_text(_checklist_text(), encoding="utf-8")

    report = {
        "summary": {"status": "DECOMMISSIONED_WITH_BACKUP"},
        "checks": {
            "legacy_cron_removed": {"status": "PASS"},
            "legacy_jobs_disabled": {"status": "PASS"},
            "legacy_routes_disabled": {"status": "PASS"},
            "legacy_configs_archived": {"status": "PASS"},
            "backup_config_done": {"status": "PASS"},
            "runbook_finalized": {"status": "PASS"},
            "rollback_snapshot_created": {"status": "PASS"},
        },
    }

    changed, _ = update_day29_checklist(checklist, report)
    assert changed is True

    updated = checklist.read_text(encoding="utf-8")
    assert "- [x] Decommission có kiểm soát: cron/job cũ, route cũ, config cũ." in updated
    assert "- [x] Backup config + runbook + rollback snapshot cuối." in updated
