from __future__ import annotations

import argparse
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, Tuple

DAY14_HEADER = "### Ngày 14 (Gate 2)"

TARGETS = {
    "Gate tuần 2: 20% canary ổn định >= 48h.": "canary_20_stable_48h",
    "Không có incident Sev-1/Sev-2.": "no_sev1_sev2",
    "Duyệt tăng tỷ lệ tuần 3.": "approve_scale_week3",
}


def _read_json(path: Path) -> Dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def _read_json_or_default(path: Path, default: Dict[str, Any]) -> Dict[str, Any]:
    if not path.exists():
        return dict(default)
    return json.loads(path.read_text(encoding="utf-8"))


def _append_jsonl(path: Path, payload: Dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a", encoding="utf-8") as fp:
        fp.write(json.dumps(payload, ensure_ascii=False) + "\n")


def _replace_checkbox(line: str, checked: bool) -> str:
    marker = "[x]" if checked else "[ ]"
    stripped = line.lstrip()
    indent = line[: len(line) - len(stripped)]
    if stripped.startswith("- [x] ") or stripped.startswith("- [ ] "):
        content = stripped[6:]
        return f"{indent}- {marker} {content}"
    return line


def _evaluate_day14_status(report: Dict[str, Any]) -> Dict[str, bool]:
    checks = report.get("checks", {})
    summary = report.get("summary", {})

    canary_pass = str(checks.get("canary_20_stable_48h", {}).get("status", "")).upper() == "PASS"
    sev_pass = str(checks.get("no_sev1_sev2", {}).get("status", "")).upper() == "PASS"
    approve = str(summary.get("status", "")).upper() == "PASS" and bool(summary.get("approve_scale_week3", False))

    return {
        "canary_20_stable_48h": canary_pass,
        "no_sev1_sev2": sev_pass,
        "approve_scale_week3": approve,
    }


def update_checklist(checklist_path: Path, statuses: Dict[str, bool]) -> Tuple[bool, str]:
    lines = checklist_path.read_text(encoding="utf-8").splitlines()

    start = None
    end = len(lines)
    for idx, line in enumerate(lines):
        if line.strip() == DAY14_HEADER:
            start = idx
            break

    if start is None:
        return False, "Day 14 section not found"

    for idx in range(start + 1, len(lines)):
        if lines[idx].startswith("### "):
            end = idx
            break

    changed = False
    for idx in range(start + 1, end):
        line = lines[idx]
        stripped = line.strip()
        for sentence, key in TARGETS.items():
            if stripped.startswith("- [") and sentence in stripped:
                new_line = _replace_checkbox(line, statuses[key])
                if new_line != line:
                    lines[idx] = new_line
                    changed = True

    if changed:
        checklist_path.write_text("\n".join(lines) + "\n", encoding="utf-8")
        return True, "Checklist Day 14 updated"

    return False, "No checklist changes needed"


def sync_transition_audit(
    gate_report_path: Path,
    gate_report: Dict[str, Any],
    state_path: Path,
    transition_log_path: Path,
) -> Dict[str, Any]:
    now = datetime.now(timezone.utc)
    current_status = str(gate_report.get("summary", {}).get("status", "UNKNOWN")).upper()
    run_id = str(gate_report.get("run_id", ""))
    run_ts = str(gate_report.get("run_ts", now.isoformat()))

    prev_state = _read_json_or_default(
        state_path,
        {
            "last_gate_status": "UNKNOWN",
            "gate2_passed_timestamp": None,
            "last_transition_at": None,
        },
    )

    previous_status = str(prev_state.get("last_gate_status", "UNKNOWN")).upper()
    gate2_passed_ts = prev_state.get("gate2_passed_timestamp")
    transition_logged = False
    transition_type = "none"

    if previous_status == "NO_GO" and current_status == "PASS":
        transition_logged = True
        transition_type = "no_go_to_pass"
        gate2_passed_ts = run_ts
        _append_jsonl(
            transition_log_path,
            {
                "event": "GATE2_STATUS_TRANSITION",
                "transition": "NO_GO_TO_PASS",
                "at": run_ts,
                "run_id": run_id,
                "previous_status": previous_status,
                "current_status": current_status,
                "gate": gate_report.get("gate", "WEEK2_GATE2"),
            },
        )

    if current_status == "PASS" and not gate2_passed_ts:
        gate2_passed_ts = run_ts

    gate_report.setdefault("audit", {})
    gate_report["audit"]["gate2_passed_timestamp"] = gate2_passed_ts
    gate_report["audit"]["status_transition"] = {
        "previous": previous_status,
        "current": current_status,
        "type": transition_type,
        "logged": transition_logged,
    }
    gate_report_path.write_text(json.dumps(gate_report, indent=2), encoding="utf-8")

    next_state = {
        "last_gate_status": current_status,
        "gate2_passed_timestamp": gate2_passed_ts,
        "last_transition_at": run_ts if transition_logged else prev_state.get("last_transition_at"),
        "last_seen_run_id": run_id,
        "updated_at": now.isoformat(),
    }
    state_path.parent.mkdir(parents=True, exist_ok=True)
    state_path.write_text(json.dumps(next_state, indent=2), encoding="utf-8")

    return {
        "previous_status": previous_status,
        "current_status": current_status,
        "transition_logged": transition_logged,
        "transition_type": transition_type,
        "gate2_passed_timestamp": gate2_passed_ts,
        "state_file": str(state_path),
        "transition_log_file": str(transition_log_path),
    }


def _write_watcher_report(output: Path, statuses: Dict[str, bool], changed: bool, message: str) -> None:
    now = datetime.now(timezone.utc)
    payload = {
        "run_id": f"day14_watcher_{now.strftime('%Y%m%dT%H%M%SZ')}",
        "run_ts": now.isoformat(),
        "statuses": statuses,
        "checklist_updated": changed,
        "message": message,
    }
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(payload, indent=2), encoding="utf-8")


def main() -> int:
    parser = argparse.ArgumentParser(description="Auto-update Day 14 checklist from Gate 2 report")
    parser.add_argument(
        "--gate-report",
        default="documentation/migration/reports/DAY14_GATE2_REPORT.json",
        help="Path to Day 14 gate report JSON",
    )
    parser.add_argument(
        "--checklist",
        default="documentation/migration/MIGRATION_CHECKLIST_30_DAYS.md",
        help="Path to migration checklist markdown",
    )
    parser.add_argument(
        "--output",
        default="documentation/migration/reports/DAY14_WATCHER_RESULT.json",
        help="Path to watcher result JSON",
    )
    parser.add_argument(
        "--state-file",
        default="documentation/migration/reports/history/DAY14_GATE2_STATE.json",
        help="Path to watcher state JSON",
    )
    parser.add_argument(
        "--transition-log",
        default="documentation/migration/reports/history/DAY14_GATE2_TRANSITIONS.jsonl",
        help="Path to watcher transition JSONL audit log",
    )

    args = parser.parse_args()

    gate_report_path = Path(args.gate_report)
    gate_report = _read_json(gate_report_path)

    transition_info = sync_transition_audit(
        gate_report_path=gate_report_path,
        gate_report=gate_report,
        state_path=Path(args.state_file),
        transition_log_path=Path(args.transition_log),
    )

    gate_report = _read_json(gate_report_path)
    statuses = _evaluate_day14_status(gate_report)
    changed, message = update_checklist(Path(args.checklist), statuses)
    _write_watcher_report(Path(args.output), statuses, changed, message)

    watcher_output = _read_json(Path(args.output))
    watcher_output["transition"] = transition_info
    Path(args.output).write_text(json.dumps(watcher_output, indent=2), encoding="utf-8")

    print(f"[DONE] day14 watcher report: {args.output}")
    print(
        "[STATUS] "
        f"stable_48h={statuses['canary_20_stable_48h']} "
        f"no_sev1_2={statuses['no_sev1_sev2']} "
        f"approve_week3={statuses['approve_scale_week3']}"
    )
    print(f"[INFO] {message}")
    if transition_info["transition_logged"]:
        print(
            "[AUDIT] transition NO_GO->PASS logged "
            f"at={transition_info['gate2_passed_timestamp']}"
        )

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
