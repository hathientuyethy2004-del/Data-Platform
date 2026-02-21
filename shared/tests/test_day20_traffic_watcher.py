from pathlib import Path

from shared.platform.migration_templates.day20_traffic_watcher import update_day20_checklist


def _checklist_text():
    return "\n".join(
        [
            "# Checklist",
            "### Ngày 20",
            "- [ ] Tăng tổng traffic lên 80% (write + read tùy dịch vụ).",
            "- [ ] Audit lại permission, secret rotation, rate limiting.",
            "",
            "### Ngày 21 (Gate 3)",
            "- [ ] Placeholder",
        ]
    ) + "\n"


def test_update_day20_keeps_unchecked_when_blocked(tmp_path: Path):
    checklist = tmp_path / "MIGRATION_CHECKLIST_30_DAYS.md"
    checklist.write_text(_checklist_text(), encoding="utf-8")

    report = {
        "summary": {"status": "BLOCKED"},
        "traffic": {"applied": False},
        "checks": {
            "permission_audit_passed": {"status": "PASS"},
            "secret_rotation_checked": {"status": "PASS"},
            "rate_limiting_audit_passed": {"status": "PASS"},
        },
    }

    changed, _ = update_day20_checklist(checklist, report)

    assert changed is False


def test_update_day20_marks_when_traffic_and_audit_pass(tmp_path: Path):
    checklist = tmp_path / "MIGRATION_CHECKLIST_30_DAYS.md"
    checklist.write_text(_checklist_text(), encoding="utf-8")

    report = {
        "summary": {"status": "TRAFFIC_80_APPLIED"},
        "traffic": {"applied": True},
        "checks": {
            "permission_audit_passed": {"status": "PASS"},
            "secret_rotation_checked": {"status": "PASS"},
            "rate_limiting_audit_passed": {"status": "PASS"},
        },
    }

    changed, _ = update_day20_checklist(checklist, report)

    assert changed is True
    updated = checklist.read_text(encoding="utf-8")
    assert "- [x] Tăng tổng traffic lên 80% (write + read tùy dịch vụ)." in updated
    assert "- [x] Audit lại permission, secret rotation, rate limiting." in updated
