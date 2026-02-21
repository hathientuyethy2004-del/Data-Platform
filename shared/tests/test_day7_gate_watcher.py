from pathlib import Path
import json

from shared.platform.migration_templates.day7_gate_watcher import (
    generate_day7_closure_if_needed,
    sync_gate_transition_audit,
    update_checklist,
)


def test_update_checklist_marks_day7_items_when_pass(tmp_path: Path):
    checklist = tmp_path / "MIGRATION_CHECKLIST_30_DAYS.md"
    checklist.write_text(
        "\n".join(
            [
                "# Checklist",
                "### Ngày 7 (Gate 1)",
                "- [ ] Gate tuần 1: dual-run staging ổn định >= 24h.",
                "- [x] Không có mismatch critical.",
                "- [ ] Cho phép sang tuần 2.",
                "",
                "### Ngày 8-9",
                "- [ ] Placeholder",
            ]
        )
        + "\n",
        encoding="utf-8",
    )

    statuses = {
        "gate_week1_stable_24h": True,
        "no_critical_mismatch": True,
        "allow_move_week2": True,
    }

    changed, _ = update_checklist(checklist, statuses)
    assert changed is True

    updated = checklist.read_text(encoding="utf-8")
    assert "- [x] Gate tuần 1: dual-run staging ổn định >= 24h." in updated
    assert "- [x] Không có mismatch critical." in updated
    assert "- [x] Cho phép sang tuần 2." in updated


def test_update_checklist_keeps_day7_unchecked_when_not_ready(tmp_path: Path):
    checklist = tmp_path / "MIGRATION_CHECKLIST_30_DAYS.md"
    checklist.write_text(
        "\n".join(
            [
                "# Checklist",
                "### Ngày 7 (Gate 1)",
                "- [ ] Gate tuần 1: dual-run staging ổn định >= 24h.",
                "- [x] Không có mismatch critical.",
                "- [ ] Cho phép sang tuần 2.",
                "",
                "### Ngày 8-9",
                "- [ ] Placeholder",
            ]
        )
        + "\n",
        encoding="utf-8",
    )

    statuses = {
        "gate_week1_stable_24h": False,
        "no_critical_mismatch": True,
        "allow_move_week2": False,
    }

    changed, _ = update_checklist(checklist, statuses)
    assert changed is False

    updated = checklist.read_text(encoding="utf-8")
    assert "- [ ] Gate tuần 1: dual-run staging ổn định >= 24h." in updated
    assert "- [x] Không có mismatch critical." in updated
    assert "- [ ] Cho phép sang tuần 2." in updated


def test_sync_gate_transition_logs_fail_to_pass(tmp_path: Path):
    gate_report_path = tmp_path / "DAY7_GATE1_REPORT.json"
    state_path = tmp_path / "history" / "DAY7_GATE1_STATE.json"
    transition_log_path = tmp_path / "history" / "DAY7_GATE1_TRANSITIONS.jsonl"

    gate_report = {
        "run_id": "r-001",
        "run_ts": "2026-02-21T12:30:00+00:00",
        "gate": "WEEK1_GATE1",
        "summary": {"status": "PASS", "allow_move_to_week2": True},
        "checks": {},
    }
    gate_report_path.write_text(json.dumps(gate_report), encoding="utf-8")
    state_path.parent.mkdir(parents=True, exist_ok=True)
    state_path.write_text(
        json.dumps(
            {
                "last_gate_status": "FAIL",
                "gate_passed_timestamp": None,
                "last_transition_at": None,
            }
        ),
        encoding="utf-8",
    )

    info = sync_gate_transition_audit(
        gate_report_path=gate_report_path,
        gate_report=gate_report,
        state_path=state_path,
        transition_log_path=transition_log_path,
    )

    assert info["transition_logged"] is True
    assert info["transition_type"] == "fail_to_pass"
    assert info["gate_passed_timestamp"] == "2026-02-21T12:30:00+00:00"

    updated_report = json.loads(gate_report_path.read_text(encoding="utf-8"))
    assert updated_report["audit"]["gate_passed_timestamp"] == "2026-02-21T12:30:00+00:00"

    log_lines = transition_log_path.read_text(encoding="utf-8").strip().splitlines()
    assert len(log_lines) == 1
    log_event = json.loads(log_lines[0])
    assert log_event["transition"] == "FAIL_TO_PASS"


def test_sync_gate_transition_does_not_log_without_transition(tmp_path: Path):
    gate_report_path = tmp_path / "DAY7_GATE1_REPORT.json"
    state_path = tmp_path / "history" / "DAY7_GATE1_STATE.json"
    transition_log_path = tmp_path / "history" / "DAY7_GATE1_TRANSITIONS.jsonl"

    gate_report = {
        "run_id": "r-002",
        "run_ts": "2026-02-21T12:45:00+00:00",
        "gate": "WEEK1_GATE1",
        "summary": {"status": "FAIL", "allow_move_to_week2": False},
        "checks": {},
    }
    gate_report_path.write_text(json.dumps(gate_report), encoding="utf-8")

    info = sync_gate_transition_audit(
        gate_report_path=gate_report_path,
        gate_report=gate_report,
        state_path=state_path,
        transition_log_path=transition_log_path,
    )

    assert info["transition_logged"] is False
    assert info["transition_type"] == "none"
    assert transition_log_path.exists() is False


def test_sync_gate_transition_two_runs_fail_then_pass_logs_exactly_one_event(tmp_path: Path):
    gate_report_path = tmp_path / "DAY7_GATE1_REPORT.json"
    state_path = tmp_path / "history" / "DAY7_GATE1_STATE.json"
    transition_log_path = tmp_path / "history" / "DAY7_GATE1_TRANSITIONS.jsonl"

    first_run_fail = {
        "run_id": "r-100",
        "run_ts": "2026-02-21T13:00:00+00:00",
        "gate": "WEEK1_GATE1",
        "summary": {"status": "FAIL", "allow_move_to_week2": False},
        "checks": {},
    }
    gate_report_path.write_text(json.dumps(first_run_fail), encoding="utf-8")

    first_info = sync_gate_transition_audit(
        gate_report_path=gate_report_path,
        gate_report=first_run_fail,
        state_path=state_path,
        transition_log_path=transition_log_path,
    )

    assert first_info["transition_logged"] is False
    assert transition_log_path.exists() is False

    second_run_pass = {
        "run_id": "r-101",
        "run_ts": "2026-02-21T13:10:00+00:00",
        "gate": "WEEK1_GATE1",
        "summary": {"status": "PASS", "allow_move_to_week2": True},
        "checks": {},
    }
    gate_report_path.write_text(json.dumps(second_run_pass), encoding="utf-8")

    second_info = sync_gate_transition_audit(
        gate_report_path=gate_report_path,
        gate_report=second_run_pass,
        state_path=state_path,
        transition_log_path=transition_log_path,
    )

    assert second_info["transition_logged"] is True
    assert second_info["transition_type"] == "fail_to_pass"
    assert second_info["gate_passed_timestamp"] == "2026-02-21T13:10:00+00:00"

    log_lines = transition_log_path.read_text(encoding="utf-8").strip().splitlines()
    assert len(log_lines) == 1
    transition_event = json.loads(log_lines[0])
    assert transition_event["transition"] == "FAIL_TO_PASS"
    assert transition_event["previous_status"] == "FAIL"
    assert transition_event["current_status"] == "PASS"


def test_generate_day7_closure_when_fail_to_pass_transition(tmp_path: Path):
    closure_path = tmp_path / "DAY7_GATE1_CLOSURE.md"
    gate_report = {
        "run_id": "r-200",
        "run_ts": "2026-02-21T13:30:00+00:00",
        "gate": "WEEK1_GATE1",
        "summary": {
            "status": "PASS",
            "allow_move_to_week2": True,
            "reason": "All Gate 1 checks passed",
        },
        "checks": {
            "dual_run_staging_stable_24h": {"status": "PASS"},
            "no_critical_mismatch": {"status": "PASS"},
            "prerequisite_smoke_and_regression": {"status": "PASS"},
        },
    }
    transition_info = {
        "transition_logged": True,
        "transition_type": "fail_to_pass",
        "current_status": "PASS",
        "gate_passed_timestamp": "2026-02-21T13:30:00+00:00",
    }

    generated, _ = generate_day7_closure_if_needed(
        gate_report=gate_report,
        transition_info=transition_info,
        closure_path=closure_path,
    )

    assert generated is True
    content = closure_path.read_text(encoding="utf-8")
    assert "# DAY7 Gate 1 Closure" in content
    assert "Gate Passed Timestamp (UTC): 2026-02-21T13:30:00+00:00" in content
    assert "Handoff decision: Approved to proceed to Week 2" in content


def test_generate_day7_closure_not_created_without_transition(tmp_path: Path):
    closure_path = tmp_path / "DAY7_GATE1_CLOSURE.md"
    gate_report = {"summary": {"status": "FAIL"}, "checks": {}}
    transition_info = {
        "transition_logged": False,
        "transition_type": "none",
        "current_status": "FAIL",
        "gate_passed_timestamp": None,
    }

    generated, _ = generate_day7_closure_if_needed(
        gate_report=gate_report,
        transition_info=transition_info,
        closure_path=closure_path,
    )

    assert generated is False
    assert closure_path.exists() is False
