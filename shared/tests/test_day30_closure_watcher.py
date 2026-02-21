from pathlib import Path

from shared.platform.migration_templates.day30_closure_watcher import update_day30_checklist


def _checklist_text():
    return "\n".join(
        [
            "# Checklist",
            "### Ngày 30 (Go-Live Closure)",
            "- [ ] Ký biên bản nghiệm thu kỹ thuật.",
            "- [ ] Tổng kết lessons learned.",
            "- [ ] Chuyển sang phase tối ưu chi phí/hiệu năng.",
            "",
            "## Exit Criteria (bắt buộc)",
            "- [ ] Placeholder",
        ]
    ) + "\n"


def test_update_day30_keeps_unchecked_when_blocked(tmp_path: Path):
    checklist = tmp_path / "MIGRATION_CHECKLIST_30_DAYS.md"
    checklist.write_text(_checklist_text(), encoding="utf-8")

    report = {
        "summary": {"status": "BLOCKED"},
        "checks": {
            "technical_acceptance_signed": {"status": "FAIL"},
            "lessons_learned_published": {"status": "FAIL"},
            "optimization_phase_kickoff": {"status": "FAIL"},
        },
    }

    changed, _ = update_day30_checklist(checklist, report)
    assert changed is False


def test_update_day30_marks_done_when_closure_completed(tmp_path: Path):
    checklist = tmp_path / "MIGRATION_CHECKLIST_30_DAYS.md"
    checklist.write_text(_checklist_text(), encoding="utf-8")

    report = {
        "summary": {"status": "GO_LIVE_CLOSED"},
        "checks": {
            "technical_acceptance_signed": {"status": "PASS"},
            "lessons_learned_published": {"status": "PASS"},
            "optimization_phase_kickoff": {"status": "PASS"},
        },
    }

    changed, _ = update_day30_checklist(checklist, report)
    assert changed is True

    updated = checklist.read_text(encoding="utf-8")
    assert "- [x] Ký biên bản nghiệm thu kỹ thuật." in updated
    assert "- [x] Tổng kết lessons learned." in updated
    assert "- [x] Chuyển sang phase tối ưu chi phí/hiệu năng." in updated
