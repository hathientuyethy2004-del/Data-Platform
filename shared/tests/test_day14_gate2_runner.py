from datetime import datetime, timedelta, timezone

from shared.platform.migration_templates.day14_gate2_runner import evaluate_gate2


def _day10(hours_ago: int, applied: bool = True, percent: int = 20):
    run_ts = (datetime.now(timezone.utc) - timedelta(hours=hours_ago)).isoformat()
    return {
        "run_ts": run_ts,
        "rollout": {
            "applied": applied,
            "effective_percent": percent,
        },
    }


def _day13(status: str = "PASS", integrity: bool = True):
    return {
        "summary": {
            "status": status,
            "integrity_passed": integrity,
        }
    }


def test_gate2_pass_when_all_conditions_met():
    report = evaluate_gate2(
        day10_report=_day10(hours_ago=60, applied=True, percent=20),
        day13_report=_day13("PASS", True),
        incidents=[],
        min_stability_hours=48,
    )

    assert report["summary"]["status"] == "PASS"
    assert report["summary"]["approve_scale_week3"] is True
    assert report["summary"]["blockers"] == []


def test_gate2_no_go_when_not_enough_hours():
    report = evaluate_gate2(
        day10_report=_day10(hours_ago=4, applied=True, percent=20),
        day13_report=_day13("PASS", True),
        incidents=[],
        min_stability_hours=48,
    )

    assert report["summary"]["status"] == "NO_GO"
    assert "canary_20_stable_48h" in report["summary"]["blockers"]


def test_gate2_no_go_when_sev1_present():
    incident = {
        "ts": datetime.now(timezone.utc).isoformat(),
        "severity": "SEV-1",
        "title": "Test incident",
    }
    report = evaluate_gate2(
        day10_report=_day10(hours_ago=60, applied=True, percent=20),
        day13_report=_day13("PASS", True),
        incidents=[incident],
        min_stability_hours=48,
    )

    assert report["summary"]["status"] == "NO_GO"
    assert "no_sev1_sev2" in report["summary"]["blockers"]
