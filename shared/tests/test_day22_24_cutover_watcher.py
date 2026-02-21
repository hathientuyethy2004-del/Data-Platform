from pathlib import Path

from shared.platform.migration_templates.day22_24_cutover_watcher import update_day22_24_checklist


def _checklist_text():
    return "\n".join(
        [
            "# Checklist",
            "### Ngày 22-24",
            "- [ ] Cutover 100% write/load sang OSS.",
            "- [ ] Giữ shadow read từ legacy thêm 2-3 ngày để so sánh.",
            "",
            "### Ngày 25-26",
            "- [ ] Placeholder",
        ]
    ) + "\n"


def test_update_day22_24_keeps_unchecked_when_blocked(tmp_path: Path):
    checklist = tmp_path / "MIGRATION_CHECKLIST_30_DAYS.md"
    checklist.write_text(_checklist_text(), encoding="utf-8")

    report = {
        "summary": {"status": "BLOCKED"},
        "cutover": {
            "applied": False,
            "shadow_read_legacy_enabled": True,
            "shadow_read_window_days": 3,
        },
    }

    changed, _ = update_day22_24_checklist(checklist, report)

    assert changed is False


def test_update_day22_24_marks_when_cutover_and_shadow_pass(tmp_path: Path):
    checklist = tmp_path / "MIGRATION_CHECKLIST_30_DAYS.md"
    checklist.write_text(_checklist_text(), encoding="utf-8")

    report = {
        "summary": {"status": "WRITE_LOAD_100_SHADOW_READ"},
        "cutover": {
            "applied": True,
            "shadow_read_legacy_enabled": True,
            "shadow_read_window_days": 3,
        },
    }

    changed, _ = update_day22_24_checklist(checklist, report)

    assert changed is True
    updated = checklist.read_text(encoding="utf-8")
    assert "- [x] Cutover 100% write/load sang OSS." in updated
    assert "- [x] Giữ shadow read từ legacy thêm 2-3 ngày để so sánh." in updated
