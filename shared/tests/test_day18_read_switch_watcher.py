from pathlib import Path

from shared.platform.migration_templates.day18_read_switch_watcher import update_day18_19_checklist


def _checklist_text():
    return "\n".join(
        [
            "# Checklist",
            "### Ngày 18-19",
            "- [ ] Tăng read switch 30% rồi 50% nếu đạt SLO.",
            "- [ ] Validate freshness và tính đúng business metrics.",
            "",
            "### Ngày 20",
            "- [ ] Placeholder",
        ]
    ) + "\n"


def test_update_day18_keeps_unchecked_when_blocked(tmp_path: Path):
    checklist = tmp_path / "MIGRATION_CHECKLIST_30_DAYS.md"
    checklist.write_text(_checklist_text(), encoding="utf-8")

    report = {
        "summary": {"status": "BLOCKED"},
        "read_switch": {"applied": False},
        "monitoring": {"overall_status": "PASS"},
    }

    changed, _ = update_day18_19_checklist(checklist, report)

    assert changed is False


def test_update_day18_marks_when_switched_and_monitoring_pass(tmp_path: Path):
    checklist = tmp_path / "MIGRATION_CHECKLIST_30_DAYS.md"
    checklist.write_text(_checklist_text(), encoding="utf-8")

    report = {
        "summary": {"status": "READ_SWITCHED_30"},
        "read_switch": {"applied": True},
        "monitoring": {"overall_status": "PASS"},
    }

    changed, _ = update_day18_19_checklist(checklist, report)

    assert changed is True
    updated = checklist.read_text(encoding="utf-8")
    assert "- [x] Tăng read switch 30% rồi 50% nếu đạt SLO." in updated
    assert "- [x] Validate freshness và tính đúng business metrics." in updated
