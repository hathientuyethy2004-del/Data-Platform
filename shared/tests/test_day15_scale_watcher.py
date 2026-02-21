from pathlib import Path

from shared.platform.migration_templates.day15_scale_watcher import update_day15_checklist


def _checklist_text():
    return "\n".join(
        [
            "# Checklist",
            "### Ngày 15-16",
            "- [ ] Tăng tỷ lệ write/load OSS lên 50%.",
            "- [ ] Giữ dual-run compare tự động mỗi giờ.",
            "",
            "### Ngày 17",
            "- [ ] Placeholder",
        ]
    ) + "\n"


def test_update_day15_checklist_marks_compare_when_blocked(tmp_path: Path):
    checklist = tmp_path / "MIGRATION_CHECKLIST_30_DAYS.md"
    checklist.write_text(_checklist_text(), encoding="utf-8")

    scale_report = {
        "summary": {"status": "BLOCKED"},
        "rollout": {"applied": False},
        "checks": {
            "dual_run_compare_hourly_enabled": {"status": "PASS"},
        },
    }

    changed, _ = update_day15_checklist(checklist, scale_report)

    assert changed is True
    updated = checklist.read_text(encoding="utf-8")
    assert "- [ ] Tăng tỷ lệ write/load OSS lên 50%." in updated
    assert "- [x] Giữ dual-run compare tự động mỗi giờ." in updated


def test_update_day15_checklist_marks_all_when_scaled(tmp_path: Path):
    checklist = tmp_path / "MIGRATION_CHECKLIST_30_DAYS.md"
    checklist.write_text(_checklist_text(), encoding="utf-8")

    scale_report = {
        "summary": {"status": "SCALED_TO_50"},
        "rollout": {"applied": True},
        "checks": {
            "dual_run_compare_hourly_enabled": {"status": "PASS"},
        },
    }

    changed, _ = update_day15_checklist(checklist, scale_report)

    assert changed is True
    updated = checklist.read_text(encoding="utf-8")
    assert "- [x] Tăng tỷ lệ write/load OSS lên 50%." in updated
    assert "- [x] Giữ dual-run compare tự động mỗi giờ." in updated
