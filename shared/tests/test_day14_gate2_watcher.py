from pathlib import Path

from shared.platform.migration_templates.day14_gate2_watcher import update_checklist


def _checklist_text():
    return "\n".join(
        [
            "# Checklist",
            "### Ngày 14 (Gate 2)",
            "- [ ] Gate tuần 2: 20% canary ổn định >= 48h.",
            "- [ ] Không có incident Sev-1/Sev-2.",
            "- [ ] Duyệt tăng tỷ lệ tuần 3.",
            "",
            "### Ngày 15-16",
            "- [ ] Placeholder",
        ]
    ) + "\n"


def test_update_day14_checklist_marks_partial_for_no_go(tmp_path: Path):
    checklist = tmp_path / "MIGRATION_CHECKLIST_30_DAYS.md"
    checklist.write_text(_checklist_text(), encoding="utf-8")

    statuses = {
        "canary_20_stable_48h": False,
        "no_sev1_sev2": True,
        "approve_scale_week3": False,
    }
    changed, _ = update_checklist(checklist, statuses)

    assert changed is True
    updated = checklist.read_text(encoding="utf-8")
    assert "- [ ] Gate tuần 2: 20% canary ổn định >= 48h." in updated
    assert "- [x] Không có incident Sev-1/Sev-2." in updated
    assert "- [ ] Duyệt tăng tỷ lệ tuần 3." in updated


def test_update_day14_checklist_marks_all_when_pass(tmp_path: Path):
    checklist = tmp_path / "MIGRATION_CHECKLIST_30_DAYS.md"
    checklist.write_text(_checklist_text(), encoding="utf-8")

    statuses = {
        "canary_20_stable_48h": True,
        "no_sev1_sev2": True,
        "approve_scale_week3": True,
    }
    changed, _ = update_checklist(checklist, statuses)

    assert changed is True
    updated = checklist.read_text(encoding="utf-8")
    assert "- [x] Gate tuần 2: 20% canary ổn định >= 48h." in updated
    assert "- [x] Không có incident Sev-1/Sev-2." in updated
    assert "- [x] Duyệt tăng tỷ lệ tuần 3." in updated
