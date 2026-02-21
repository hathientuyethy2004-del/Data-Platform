from pathlib import Path

from shared.platform.migration_templates.day17_read_switch_watcher import update_day17_checklist


def _checklist_text():
    return "\n".join(
        [
            "# Checklist",
            "### Ngày 17",
            "- [ ] Bật read switch 10% sang OSS cho endpoint/pipeline đã ổn định.",
            "- [ ] Theo dõi latency p95/p99 và error rate.",
            "",
            "### Ngày 18-19",
            "- [ ] Placeholder",
        ]
    ) + "\n"


def test_update_day17_keeps_unchecked_when_blocked(tmp_path: Path):
    checklist = tmp_path / "MIGRATION_CHECKLIST_30_DAYS.md"
    checklist.write_text(_checklist_text(), encoding="utf-8")

    report = {
        "summary": {"status": "BLOCKED"},
        "read_switch": {"applied": False},
        "monitoring": {"overall_status": "PASS"},
    }

    changed, _ = update_day17_checklist(checklist, report)

    assert changed is False
    updated = checklist.read_text(encoding="utf-8")
    assert "- [ ] Bật read switch 10% sang OSS cho endpoint/pipeline đã ổn định." in updated
    assert "- [ ] Theo dõi latency p95/p99 và error rate." in updated


def test_update_day17_marks_all_when_switched_and_monitoring_pass(tmp_path: Path):
    checklist = tmp_path / "MIGRATION_CHECKLIST_30_DAYS.md"
    checklist.write_text(_checklist_text(), encoding="utf-8")

    report = {
        "summary": {"status": "READ_SWITCHED_10"},
        "read_switch": {"applied": True},
        "monitoring": {"overall_status": "PASS"},
    }

    changed, _ = update_day17_checklist(checklist, report)

    assert changed is True
    updated = checklist.read_text(encoding="utf-8")
    assert "- [x] Bật read switch 10% sang OSS cho endpoint/pipeline đã ổn định." in updated
    assert "- [x] Theo dõi latency p95/p99 và error rate." in updated
