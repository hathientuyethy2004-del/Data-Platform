from __future__ import annotations

import argparse
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, Tuple

DAY21_HEADER = "### Ngày 21 (Gate 3)"

TARGETS = {
    "Gate tuần 3: 80% ổn định >= 72h.": "traffic_80_stable_72h",
    "Compare report pass >= 99.5% bản ghi trong ngưỡng cho phép.": "compare_pass_rate_99_5",
    "Duyệt full cutover tuần 4.": "approve_full_cutover_week4",
}


def _read_json(path: Path) -> Dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def _replace_checkbox(line: str, checked: bool) -> str:
    marker = "[x]" if checked else "[ ]"
    stripped = line.lstrip()
    indent = line[: len(line) - len(stripped)]
    if stripped.startswith("- [x] ") or stripped.startswith("- [ ] "):
        content = stripped[6:]
        return f"{indent}- {marker} {content}"
    return line


def _evaluate_day21_status(report: Dict[str, Any]) -> Dict[str, bool]:
    checks = report.get("checks", {})
    summary = report.get("summary", {})

    stable_72h = str(checks.get("traffic_80_stable_72h", {}).get("status", "")).upper() == "PASS"
    compare_ok = str(checks.get("compare_pass_rate_99_5", {}).get("status", "")).upper() == "PASS"
    approve = str(summary.get("status", "")).upper() == "PASS" and bool(summary.get("approve_full_cutover_week4", False))

    return {
        "traffic_80_stable_72h": stable_72h,
        "compare_pass_rate_99_5": compare_ok,
        "approve_full_cutover_week4": approve,
    }


def update_checklist(checklist_path: Path, statuses: Dict[str, bool]) -> Tuple[bool, str]:
    lines = checklist_path.read_text(encoding="utf-8").splitlines()

    start = None
    end = len(lines)
    for idx, line in enumerate(lines):
        if line.strip() == DAY21_HEADER:
            start = idx
            break

    if start is None:
        return False, "Day 21 section not found"

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
        return True, "Checklist Day 21 updated"

    return False, "No checklist changes needed"


def _write_watcher_report(output: Path, statuses: Dict[str, bool], changed: bool, message: str) -> None:
    now = datetime.now(timezone.utc)
    payload = {
        "run_id": f"day21_watcher_{now.strftime('%Y%m%dT%H%M%SZ')}",
        "run_ts": now.isoformat(),
        "statuses": statuses,
        "checklist_updated": changed,
        "message": message,
    }
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(payload, indent=2), encoding="utf-8")


def main() -> int:
    parser = argparse.ArgumentParser(description="Auto-update Day 21 checklist from Gate 3 report")
    parser.add_argument(
        "--gate-report",
        default="documentation/migration/reports/DAY21_GATE3_REPORT.json",
        help="Path to Day 21 gate report JSON",
    )
    parser.add_argument(
        "--checklist",
        default="documentation/migration/MIGRATION_CHECKLIST_30_DAYS.md",
        help="Path to migration checklist markdown",
    )
    parser.add_argument(
        "--output",
        default="documentation/migration/reports/DAY21_WATCHER_RESULT.json",
        help="Path to watcher result JSON",
    )

    args = parser.parse_args()

    gate_report = _read_json(Path(args.gate_report))
    statuses = _evaluate_day21_status(gate_report)
    changed, message = update_checklist(Path(args.checklist), statuses)
    _write_watcher_report(Path(args.output), statuses, changed, message)

    print(f"[DONE] day21 watcher report: {args.output}")
    print(
        "[STATUS] "
        f"stable_72h={statuses['traffic_80_stable_72h']} "
        f"compare_99_5={statuses['compare_pass_rate_99_5']} "
        f"approve_week4={statuses['approve_full_cutover_week4']}"
    )
    print(f"[INFO] {message}")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
