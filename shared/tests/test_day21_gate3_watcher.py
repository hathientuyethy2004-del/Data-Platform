from pathlib import Path

from shared.platform.migration_templates.day21_gate3_watcher import update_checklist


def _checklist_text():
    return "\n".join(
        [
            "# Checklist",
            "### Ngày 21 (Gate 3)",
            "- [ ] Gate tuần 3: 80% ổn định >= 72h.",
            "- [ ] Compare report pass >= 99.5% bản ghi trong ngưỡng cho phép.",
            "- [ ] Duyệt full cutover tuần 4.",
            "",
            "### Ngày 22-24",
            "- [ ] Placeholder",
        ]
    ) + "\n"


def test_update_day21_checklist_marks_partial_for_no_go(tmp_path: Path):
    checklist = tmp_path / "MIGRATION_CHECKLIST_30_DAYS.md"
    checklist.write_text(_checklist_text(), encoding="utf-8")

    statuses = {
        "traffic_80_stable_72h": False,
        "compare_pass_rate_99_5": True,
        "approve_full_cutover_week4": False,
    }
    changed, _ = update_checklist(checklist, statuses)

    assert changed is True
    updated = checklist.read_text(encoding="utf-8")
    assert "- [ ] Gate tuần 3: 80% ổn định >= 72h." in updated
    assert "- [x] Compare report pass >= 99.5% bản ghi trong ngưỡng cho phép." in updated
    assert "- [ ] Duyệt full cutover tuần 4." in updated


def test_update_day21_checklist_marks_all_when_pass(tmp_path: Path):
    checklist = tmp_path / "MIGRATION_CHECKLIST_30_DAYS.md"
    checklist.write_text(_checklist_text(), encoding="utf-8")

    statuses = {
        "traffic_80_stable_72h": True,
        "compare_pass_rate_99_5": True,
        "approve_full_cutover_week4": True,
    }
    changed, _ = update_checklist(checklist, statuses)

    assert changed is True
    updated = checklist.read_text(encoding="utf-8")
    assert "- [x] Gate tuần 3: 80% ổn định >= 72h." in updated
    assert "- [x] Compare report pass >= 99.5% bản ghi trong ngưỡng cho phép." in updated
    assert "- [x] Duyệt full cutover tuần 4." in updated
