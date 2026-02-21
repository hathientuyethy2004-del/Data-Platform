from pathlib import Path
import json

from shared.platform.migration_templates.day10_rollout_watcher import update_day10_checklist


def _checklist_text():
    return "\n".join(
        [
            "# Checklist",
            "### Ngày 10",
            "- [ ] Tăng canary lên 20% nếu error rate và mismatch trong ngưỡng.",
            "- [x] Chạy load test peak hour + backpressure test.",
            "",
            "### Ngày 11-12",
            "- [ ] Placeholder",
        ]
    ) + "\n"


def test_update_day10_checklist_marks_canary_when_rolled_out(tmp_path: Path):
    checklist = tmp_path / "MIGRATION_CHECKLIST_30_DAYS.md"
    checklist.write_text(_checklist_text(), encoding="utf-8")

    rollout_report = {"summary": {"status": "ROLLED_OUT"}}
    changed, _ = update_day10_checklist(checklist, rollout_report)

    assert changed is True
    updated = checklist.read_text(encoding="utf-8")
    assert "- [x] Tăng canary lên 20% nếu error rate và mismatch trong ngưỡng." in updated


def test_update_day10_checklist_keeps_unchecked_when_blocked(tmp_path: Path):
    checklist = tmp_path / "MIGRATION_CHECKLIST_30_DAYS.md"
    checklist.write_text(_checklist_text(), encoding="utf-8")

    rollout_report = {"summary": {"status": "BLOCKED"}}
    changed, _ = update_day10_checklist(checklist, rollout_report)

    assert changed is False
    updated = checklist.read_text(encoding="utf-8")
    assert "- [ ] Tăng canary lên 20% nếu error rate và mismatch trong ngưỡng." in updated


def test_update_day10_checklist_unchecks_if_status_back_to_blocked(tmp_path: Path):
    checklist = tmp_path / "MIGRATION_CHECKLIST_30_DAYS.md"
    checklist.write_text(
        _checklist_text().replace(
            "- [ ] Tăng canary lên 20% nếu error rate và mismatch trong ngưỡng.",
            "- [x] Tăng canary lên 20% nếu error rate và mismatch trong ngưỡng.",
        ),
        encoding="utf-8",
    )

    rollout_report = {"summary": {"status": "BLOCKED"}}
    changed, _ = update_day10_checklist(checklist, rollout_report)

    assert changed is True
    updated = checklist.read_text(encoding="utf-8")
    assert "- [ ] Tăng canary lên 20% nếu error rate và mismatch trong ngưỡng." in updated
