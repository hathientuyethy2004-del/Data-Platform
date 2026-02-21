from pathlib import Path

from shared.platform.migration_templates.day28_freeze_watcher import update_day28_checklist


def _checklist_text():
    return "\n".join(
        [
            "# Checklist",
            "### Ngày 28",
            "- [ ] Freeze thay đổi lớn, theo dõi ổn định 24h.",
            "- [ ] Chốt báo cáo post-cutover.",
            "",
            "### Ngày 29",
            "- [ ] Placeholder",
        ]
    ) + "\n"


def test_update_day28_keeps_unchecked_when_blocked(tmp_path: Path):
    checklist = tmp_path / "MIGRATION_CHECKLIST_30_DAYS.md"
    checklist.write_text(_checklist_text(), encoding="utf-8")

    report = {
        "summary": {"status": "BLOCKED"},
        "checks": {
            "freeze_window_enabled": {"status": "FAIL"},
            "freeze_observed_24h": {"status": "FAIL"},
            "no_critical_changes": {"status": "FAIL"},
            "post_cutover_report_ready": {"status": "FAIL"},
        },
    }

    changed, _ = update_day28_checklist(checklist, report)
    assert changed is False


def test_update_day28_marks_done_when_freeze_finalized(tmp_path: Path):
    checklist = tmp_path / "MIGRATION_CHECKLIST_30_DAYS.md"
    checklist.write_text(_checklist_text(), encoding="utf-8")

    report = {
        "summary": {"status": "FREEZE_LOCKED_REPORT_FINALIZED"},
        "checks": {
            "freeze_window_enabled": {"status": "PASS"},
            "freeze_observed_24h": {"status": "PASS"},
            "no_critical_changes": {"status": "PASS"},
            "post_cutover_report_ready": {"status": "PASS"},
        },
    }

    changed, _ = update_day28_checklist(checklist, report)
    assert changed is True

    updated = checklist.read_text(encoding="utf-8")
    assert "- [x] Freeze thay đổi lớn, theo dõi ổn định 24h." in updated
    assert "- [x] Chốt báo cáo post-cutover." in updated
