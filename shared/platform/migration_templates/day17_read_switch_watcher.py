from __future__ import annotations

import argparse
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, Tuple

DAY17_HEADER = "### Ngày 17"
DAY17_SWITCH_LINE = "Bật read switch 10% sang OSS cho endpoint/pipeline đã ổn định."
DAY17_MONITOR_LINE = "Theo dõi latency p95/p99 và error rate."


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


def update_day17_checklist(checklist_path: Path, report: Dict[str, Any]) -> Tuple[bool, str]:
    summary_status = str(report.get("summary", {}).get("status", "")).upper()
    read_switch = report.get("read_switch", {})
    monitoring = report.get("monitoring", {})

    should_check_switch = summary_status == "READ_SWITCHED_10" and bool(read_switch.get("applied", False))
    should_check_monitor = should_check_switch and str(monitoring.get("overall_status", "")).upper() == "PASS"

    lines = checklist_path.read_text(encoding="utf-8").splitlines()

    start = None
    end = len(lines)
    for idx, line in enumerate(lines):
        if line.strip() == DAY17_HEADER:
            start = idx
            break

    if start is None:
        return False, "Day 17 section not found"

    for idx in range(start + 1, len(lines)):
        if lines[idx].startswith("### "):
            end = idx
            break

    changed = False
    for idx in range(start + 1, end):
        stripped = lines[idx].strip()
        if stripped.startswith("- [") and DAY17_SWITCH_LINE in stripped:
            new_line = _replace_checkbox(lines[idx], should_check_switch)
            if new_line != lines[idx]:
                lines[idx] = new_line
                changed = True
        if stripped.startswith("- [") and DAY17_MONITOR_LINE in stripped:
            new_line = _replace_checkbox(lines[idx], should_check_monitor)
            if new_line != lines[idx]:
                lines[idx] = new_line
                changed = True

    if changed:
        checklist_path.write_text("\n".join(lines) + "\n", encoding="utf-8")
        return True, "Checklist Day 17 updated"

    return False, "No checklist changes needed"


def write_watcher_report(output: Path, checklist_updated: bool, message: str, day17_status: str) -> None:
    now = datetime.now(timezone.utc)
    payload = {
        "run_id": f"day17_watcher_{now.strftime('%Y%m%dT%H%M%SZ')}",
        "run_ts": now.isoformat(),
        "day17_status": day17_status,
        "checklist_updated": checklist_updated,
        "message": message,
    }
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(payload, indent=2), encoding="utf-8")


def main() -> int:
    parser = argparse.ArgumentParser(description="Auto-update Day 17 checklist from read switch report")
    parser.add_argument(
        "--report",
        default="documentation/migration/reports/DAY17_READ_SWITCH_REPORT.json",
        help="Path to Day 17 read switch report",
    )
    parser.add_argument(
        "--checklist",
        default="documentation/migration/MIGRATION_CHECKLIST_30_DAYS.md",
        help="Path to migration checklist",
    )
    parser.add_argument(
        "--output",
        default="documentation/migration/reports/DAY17_WATCHER_RESULT.json",
        help="Path to watcher result report",
    )

    args = parser.parse_args()

    report = _read_json(Path(args.report))
    day17_status = str(report.get("summary", {}).get("status", "UNKNOWN")).upper()

    changed, message = update_day17_checklist(Path(args.checklist), report)
    write_watcher_report(Path(args.output), changed, message, day17_status)

    print(f"[DONE] day17 watcher report: {args.output}")
    print(f"[STATUS] day17_status={day17_status} checklist_updated={changed}")
    print(f"[INFO] {message}")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
