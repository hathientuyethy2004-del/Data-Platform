import json
from pathlib import Path

from shared.platform.migration_templates.day16_observation_watcher import sync_day16_transition


def _report(status: str):
    return {
        "run_id": "day16_test_run",
        "run_ts": "2026-02-21T00:00:00+00:00",
        "summary": {"status": status},
        "scope": "test",
    }


def test_sync_day16_transition_hold_to_ready_logs_event(tmp_path: Path):
    report_path = tmp_path / "DAY16_OBSERVATION_REPORT.json"
    state_path = tmp_path / "history" / "DAY16_OBSERVATION_STATE.json"
    transition_log_path = tmp_path / "history" / "DAY16_OBSERVATION_TRANSITIONS.jsonl"

    state_path.parent.mkdir(parents=True, exist_ok=True)
    state_path.write_text(
        json.dumps(
            {
                "last_day16_status": "HOLD",
                "day17_unlocked_timestamp": None,
                "last_transition_at": None,
            }
        ),
        encoding="utf-8",
    )

    report = _report("READY_FOR_DAY17")
    report_path.write_text(json.dumps(report), encoding="utf-8")

    transition = sync_day16_transition(
        day16_report_path=report_path,
        day16_report=report,
        state_path=state_path,
        transition_log_path=transition_log_path,
    )

    assert transition["transition_logged"] is True
    assert transition["transition_type"] == "hold_to_ready_for_day17"
    assert transition_log_path.exists()


def test_sync_day16_transition_no_log_when_stays_hold(tmp_path: Path):
    report_path = tmp_path / "DAY16_OBSERVATION_REPORT.json"
    state_path = tmp_path / "history" / "DAY16_OBSERVATION_STATE.json"
    transition_log_path = tmp_path / "history" / "DAY16_OBSERVATION_TRANSITIONS.jsonl"

    report = _report("HOLD")
    report_path.write_text(json.dumps(report), encoding="utf-8")

    transition = sync_day16_transition(
        day16_report_path=report_path,
        day16_report=report,
        state_path=state_path,
        transition_log_path=transition_log_path,
    )

    assert transition["transition_logged"] is False
    assert transition["transition_type"] == "none"
