from __future__ import annotations

import argparse
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, Tuple

SECTION_HEADER = "### Ngày 30 (Go-Live Closure)"
LINE_ACCEPTANCE = "Ký biên bản nghiệm thu kỹ thuật."
LINE_LESSONS = "Tổng kết lessons learned."
LINE_OPTIMIZATION = "Chuyển sang phase tối ưu chi phí/hiệu năng."


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


def update_day30_checklist(checklist_path: Path, report: Dict[str, Any]) -> Tuple[bool, str]:
    summary_status = str(report.get("summary", {}).get("status", "")).upper()
    checks = report.get("checks", {})

    acceptance_done = (
        summary_status == "GO_LIVE_CLOSED"
        and str(checks.get("technical_acceptance_signed", {}).get("status", "FAIL")).upper() == "PASS"
    )
    lessons_done = (
        summary_status == "GO_LIVE_CLOSED"
        and str(checks.get("lessons_learned_published", {}).get("status", "FAIL")).upper() == "PASS"
    )
    optimization_done = (
        summary_status == "GO_LIVE_CLOSED"
        and str(checks.get("optimization_phase_kickoff", {}).get("status", "FAIL")).upper() == "PASS"
    )

    lines = checklist_path.read_text(encoding="utf-8").splitlines()

    start = None
    end = len(lines)
    for idx, line in enumerate(lines):
        if line.strip() == SECTION_HEADER:
            start = idx
            break

    if start is None:
        return False, "Day 30 section not found"

    for idx in range(start + 1, len(lines)):
        if lines[idx].startswith("### "):
            end = idx
            break

    changed = False
    for idx in range(start + 1, end):
        stripped = lines[idx].strip()
        if stripped.startswith("- [") and LINE_ACCEPTANCE in stripped:
            new_line = _replace_checkbox(lines[idx], acceptance_done)
            if new_line != lines[idx]:
                lines[idx] = new_line
                changed = True
        if stripped.startswith("- [") and LINE_LESSONS in stripped:
            new_line = _replace_checkbox(lines[idx], lessons_done)
            if new_line != lines[idx]:
                lines[idx] = new_line
                changed = True
        if stripped.startswith("- [") and LINE_OPTIMIZATION in stripped:
            new_line = _replace_checkbox(lines[idx], optimization_done)
            if new_line != lines[idx]:
                lines[idx] = new_line
                changed = True

    if changed:
        checklist_path.write_text("\n".join(lines) + "\n", encoding="utf-8")
        return True, "Checklist Day 30 updated"

    return False, "No checklist changes needed"


def write_watcher_report(output: Path, checklist_updated: bool, message: str, status: str) -> None:
    now = datetime.now(timezone.utc)
    payload = {
        "run_id": f"day30_watcher_{now.strftime('%Y%m%dT%H%M%SZ')}",
        "run_ts": now.isoformat(),
        "day30_status": status,
        "checklist_updated": checklist_updated,
        "message": message,
    }
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(payload, indent=2), encoding="utf-8")


def main() -> int:
    parser = argparse.ArgumentParser(description="Auto-update Day 30 checklist from closure report")
    parser.add_argument(
        "--report",
        default="documentation/migration/reports/DAY30_CLOSURE_REPORT.json",
        help="Path to Day 30 closure report",
    )
    parser.add_argument(
        "--checklist",
        default="documentation/migration/MIGRATION_CHECKLIST_30_DAYS.md",
        help="Path to migration checklist",
    )
    parser.add_argument(
        "--output",
        default="documentation/migration/reports/DAY30_WATCHER_RESULT.json",
        help="Path to watcher result report",
    )

    args = parser.parse_args()

    report = _read_json(Path(args.report))
    status = str(report.get("summary", {}).get("status", "UNKNOWN")).upper()

    changed, message = update_day30_checklist(Path(args.checklist), report)
    write_watcher_report(Path(args.output), changed, message, status)

    print(f"[DONE] day30 watcher report: {args.output}")
    print(f"[STATUS] day30_status={status} checklist_updated={changed}")
    print(f"[INFO] {message}")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
