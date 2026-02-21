from pathlib import Path

from shared.platform.migration_templates.day27_validation_watcher import update_day27_checklist


def _checklist_text():
    return "\n".join(
        [
            "# Checklist",
            "### Ngày 27",
            "- [ ] Chạy full regression + performance suite.",
            "- [ ] Verify dashboard SLO, alert, audit logs.",
            "",
            "### Ngày 28",
            "- [ ] Placeholder",
        ]
    ) + "\n"


def test_update_day27_keeps_unchecked_when_blocked(tmp_path: Path):
    checklist = tmp_path / "MIGRATION_CHECKLIST_30_DAYS.md"
    checklist.write_text(_checklist_text(), encoding="utf-8")

    report = {
        "summary": {"status": "BLOCKED"},
        "checks": {
            "full_regression_suite_passed": {"status": "FAIL"},
            "performance_suite_passed": {"status": "FAIL"},
            "performance_guardrails": {"status": "FAIL"},
            "slo_dashboard_passed": {"status": "FAIL"},
            "alerts_verified": {"status": "FAIL"},
            "audit_logs_verified": {"status": "FAIL"},
        },
    }

    changed, _ = update_day27_checklist(checklist, report)
    assert changed is False


def test_update_day27_marks_done_when_validated(tmp_path: Path):
    checklist = tmp_path / "MIGRATION_CHECKLIST_30_DAYS.md"
    checklist.write_text(_checklist_text(), encoding="utf-8")

    report = {
        "summary": {"status": "VALIDATED_FOR_FREEZE"},
        "checks": {
            "full_regression_suite_passed": {"status": "PASS"},
            "performance_suite_passed": {"status": "PASS"},
            "performance_guardrails": {"status": "PASS"},
            "slo_dashboard_passed": {"status": "PASS"},
            "alerts_verified": {"status": "PASS"},
            "audit_logs_verified": {"status": "PASS"},
        },
    }

    changed, _ = update_day27_checklist(checklist, report)
    assert changed is True

    updated = checklist.read_text(encoding="utf-8")
    assert "- [x] Chạy full regression + performance suite." in updated
    assert "- [x] Verify dashboard SLO, alert, audit logs." in updated
