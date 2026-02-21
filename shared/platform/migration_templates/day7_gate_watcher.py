from __future__ import annotations

import argparse
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, Tuple

DAY7_HEADER = "### Ngày 7 (Gate 1)"

TARGETS = {
    "Gate tuần 1: dual-run staging ổn định >= 24h.": "gate_week1_stable_24h",
    "Không có mismatch critical.": "no_critical_mismatch",
    "Cho phép sang tuần 2.": "allow_move_week2",
}


def _read_json_or_default(path: Path, default: Dict[str, Any]) -> Dict[str, Any]:
    if not path.exists():
        return dict(default)
    return json.loads(path.read_text(encoding="utf-8"))


def _append_jsonl(path: Path, payload: Dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a", encoding="utf-8") as fp:
        fp.write(json.dumps(payload, ensure_ascii=False) + "\n")


def _read_report(path: Path) -> Dict:
    return json.loads(path.read_text(encoding="utf-8"))


def _evaluate_day7_status(report: Dict) -> Dict[str, bool]:
    summary = report.get("summary", {})
    checks = report.get("checks", {})

    gate_pass = str(summary.get("status", "")).upper() == "PASS"
    stable_pass = str(
        checks.get("dual_run_staging_stable_24h", {}).get("status", "")
    ).upper() == "PASS"
    no_critical_pass = str(
        checks.get("no_critical_mismatch", {}).get("status", "")
    ).upper() == "PASS"
    allow_week2 = bool(summary.get("allow_move_to_week2", False))

    return {
        "gate_week1_stable_24h": stable_pass,
        "no_critical_mismatch": no_critical_pass,
        "allow_move_week2": gate_pass and allow_week2,
    }


def _replace_checkbox(line: str, checked: bool) -> str:
    marker = "[x]" if checked else "[ ]"
    stripped = line.lstrip()
    indent = line[: len(line) - len(stripped)]
    if stripped.startswith("- [x] ") or stripped.startswith("- [ ] "):
        content = stripped[6:]
        return f"{indent}- {marker} {content}"
    return line


def update_checklist(checklist_path: Path, statuses: Dict[str, bool]) -> Tuple[bool, str]:
    text = checklist_path.read_text(encoding="utf-8")
    lines = text.splitlines()

    start = None
    end = len(lines)
    for idx, line in enumerate(lines):
        if line.strip() == DAY7_HEADER:
            start = idx
            break

    if start is None:
        return False, "Day 7 section not found"

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
        return True, "Checklist updated"

    return False, "No checklist changes needed"


def _write_watcher_report(output: Path, statuses: Dict[str, bool], changed: bool, message: str) -> None:
    now = datetime.now(timezone.utc)
    payload = {
        "run_id": f"day7_watcher_{now.strftime('%Y%m%dT%H%M%SZ')}",
        "run_ts": now.isoformat(),
        "statuses": statuses,
        "checklist_updated": changed,
        "message": message,
    }
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(payload, indent=2), encoding="utf-8")


def sync_gate_transition_audit(
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
            "gate_passed_timestamp": None,
            "last_transition_at": None,
        },
    )

    previous_status = str(prev_state.get("last_gate_status", "UNKNOWN")).upper()
    existing_passed_ts = prev_state.get("gate_passed_timestamp")

    transition_logged = False
    transition_type = "none"

    if previous_status == "FAIL" and current_status == "PASS":
        transition_logged = True
        transition_type = "fail_to_pass"
        existing_passed_ts = run_ts
        _append_jsonl(
            transition_log_path,
            {
                "event": "GATE_STATUS_TRANSITION",
                "transition": "FAIL_TO_PASS",
                "at": run_ts,
                "run_id": run_id,
                "previous_status": previous_status,
                "current_status": current_status,
                "gate": gate_report.get("gate", "WEEK1_GATE1"),
            },
        )

    if current_status == "PASS" and not existing_passed_ts:
        existing_passed_ts = run_ts

    gate_report.setdefault("audit", {})
    gate_report["audit"]["gate_passed_timestamp"] = existing_passed_ts
    gate_report["audit"]["status_transition"] = {
        "previous": previous_status,
        "current": current_status,
        "type": transition_type,
        "logged": transition_logged,
    }
    gate_report_path.write_text(json.dumps(gate_report, indent=2), encoding="utf-8")

    next_state = {
        "last_gate_status": current_status,
        "gate_passed_timestamp": existing_passed_ts,
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
        "gate_passed_timestamp": existing_passed_ts,
        "state_file": str(state_path),
        "transition_log_file": str(transition_log_path),
    }


def generate_day7_closure_if_needed(
    gate_report: Dict[str, Any],
    transition_info: Dict[str, Any],
    closure_path: Path,
) -> Tuple[bool, str]:
    if not (
        bool(transition_info.get("transition_logged"))
        and str(transition_info.get("transition_type", "")).lower() == "fail_to_pass"
        and str(transition_info.get("current_status", "")).upper() == "PASS"
    ):
        return False, "No closure generated (gate not transitioned from FAIL to PASS)"

    summary = gate_report.get("summary", {})
    checks = gate_report.get("checks", {})
    run_id = gate_report.get("run_id", "")
    run_ts = gate_report.get("run_ts", "")
    passed_ts = transition_info.get("gate_passed_timestamp")

    closure_content = "\n".join(
        [
            "# DAY7 Gate 1 Closure",
            "",
            f"Generated at: {datetime.now(timezone.utc).isoformat()}",
            f"Gate: {gate_report.get('gate', 'WEEK1_GATE1')}",
            f"Run ID: {run_id}",
            f"Run Timestamp (UTC): {run_ts}",
            f"Gate Passed Timestamp (UTC): {passed_ts}",
            "",
            "## Gate Result",
            f"- Status: {summary.get('status')}",
            f"- Allow move to Week 2: {summary.get('allow_move_to_week2')}",
            f"- Reason: {summary.get('reason')}",
            "",
            "## Check Summary",
            f"- dual_run_staging_stable_24h: {checks.get('dual_run_staging_stable_24h', {}).get('status')}",
            f"- no_critical_mismatch: {checks.get('no_critical_mismatch', {}).get('status')}",
            f"- prerequisite_smoke_and_regression: {checks.get('prerequisite_smoke_and_regression', {}).get('status')}",
            "",
            "## Audit/Handoff",
            "- Transition type: FAIL_TO_PASS",
            "- Handoff decision: Approved to proceed to Week 2",
            "- Source report: documentation/migration/reports/DAY7_GATE1_REPORT.json",
            "- Source transitions log: documentation/migration/reports/history/DAY7_GATE1_TRANSITIONS.jsonl",
            "",
        ]
    )

    closure_path.parent.mkdir(parents=True, exist_ok=True)
    closure_path.write_text(closure_content, encoding="utf-8")
    return True, f"Closure generated at {closure_path}"


def main() -> int:
    parser = argparse.ArgumentParser(description="Auto-update Day 7 checklist from gate report")
    parser.add_argument(
        "--gate-report",
        default="documentation/migration/reports/DAY7_GATE1_REPORT.json",
        help="Path to Day 7 gate report JSON",
    )
    parser.add_argument(
        "--checklist",
        default="documentation/migration/MIGRATION_CHECKLIST_30_DAYS.md",
        help="Path to migration checklist markdown",
    )
    parser.add_argument(
        "--output",
        default="documentation/migration/reports/DAY7_WATCHER_RESULT.json",
        help="Path to watcher result JSON",
    )
    parser.add_argument(
        "--state-file",
        default="documentation/migration/reports/history/DAY7_GATE1_STATE.json",
        help="Path to watcher state JSON",
    )
    parser.add_argument(
        "--transition-log",
        default="documentation/migration/reports/history/DAY7_GATE1_TRANSITIONS.jsonl",
        help="Path to watcher transition JSONL audit log",
    )
    parser.add_argument(
        "--closure-output",
        default="documentation/migration/DAY7_GATE1_CLOSURE.md",
        help="Path to Day 7 closure markdown (generated on FAIL->PASS transition)",
    )

    args = parser.parse_args()

    gate_report_path = Path(args.gate_report)
    gate_report = _read_report(gate_report_path)
    transition_info = sync_gate_transition_audit(
        gate_report_path=gate_report_path,
        gate_report=gate_report,
        state_path=Path(args.state_file),
        transition_log_path=Path(args.transition_log),
    )
    gate_report = _read_report(gate_report_path)
    statuses = _evaluate_day7_status(gate_report)
    closure_generated, closure_message = generate_day7_closure_if_needed(
        gate_report=gate_report,
        transition_info=transition_info,
        closure_path=Path(args.closure_output),
    )

    changed, message = update_checklist(Path(args.checklist), statuses)
    _write_watcher_report(Path(args.output), statuses, changed, message)

    watcher_output = _read_report(Path(args.output))
    watcher_output["transition"] = transition_info
    watcher_output["closure"] = {
        "generated": closure_generated,
        "message": closure_message,
        "file": args.closure_output,
    }
    Path(args.output).write_text(json.dumps(watcher_output, indent=2), encoding="utf-8")

    print(f"[DONE] watcher result: {args.output}")
    print(
        "[STATUS] "
        f"stable_24h={statuses['gate_week1_stable_24h']} "
        f"no_critical={statuses['no_critical_mismatch']} "
        f"allow_week2={statuses['allow_move_week2']}"
    )
    print(f"[INFO] {message}")
    print(f"[INFO] {closure_message}")
    if transition_info["transition_logged"]:
        print(
            "[AUDIT] transition FAIL->PASS logged "
            f"at={transition_info['gate_passed_timestamp']}"
        )

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
