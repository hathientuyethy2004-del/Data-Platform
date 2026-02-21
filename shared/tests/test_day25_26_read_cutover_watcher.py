from pathlib import Path

from shared.platform.migration_templates.day25_26_read_cutover_watcher import update_day25_26_checklist


def _checklist_text():
    return "\n".join(
        [
            "# Checklist",
            "### Ngày 25-26",
            "- [ ] Cutover 100% read path sang OSS.",
            "- [ ] Đóng dần tài nguyên legacy không còn sử dụng.",
            "",
            "### Ngày 27",
            "- [ ] Placeholder",
        ]
    ) + "\n"


def test_update_day25_26_keeps_unchecked_when_blocked(tmp_path: Path):
    checklist = tmp_path / "MIGRATION_CHECKLIST_30_DAYS.md"
    checklist.write_text(_checklist_text(), encoding="utf-8")

    report = {
        "summary": {"status": "BLOCKED"},
        "read_cutover": {
            "applied": False,
            "legacy_jobs_disabled": True,
            "legacy_routes_disabled": True,
            "legacy_configs_archived": True,
        },
    }

    changed, _ = update_day25_26_checklist(checklist, report)

    assert changed is False


def test_update_day25_26_marks_when_read_cutover_and_legacy_drain_pass(tmp_path: Path):
    checklist = tmp_path / "MIGRATION_CHECKLIST_30_DAYS.md"
    checklist.write_text(_checklist_text(), encoding="utf-8")

    report = {
        "summary": {"status": "READ_PATH_100_LEGACY_DRAINING"},
        "read_cutover": {
            "applied": True,
            "legacy_jobs_disabled": True,
            "legacy_routes_disabled": True,
            "legacy_configs_archived": True,
        },
    }

    changed, _ = update_day25_26_checklist(checklist, report)

    assert changed is True
    updated = checklist.read_text(encoding="utf-8")
    assert "- [x] Cutover 100% read path sang OSS." in updated
    assert "- [x] Đóng dần tài nguyên legacy không còn sử dụng." in updated
