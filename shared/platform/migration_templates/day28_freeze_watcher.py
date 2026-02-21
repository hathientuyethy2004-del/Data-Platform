from __future__ import annotations

import argparse
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, Tuple

SECTION_HEADER = "### Ngày 28"
LINE_FREEZE = "Freeze thay đổi lớn, theo dõi ổn định 24h."
LINE_REPORT = "Chốt báo cáo post-cutover."


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


def update_day28_checklist(checklist_path: Path, report: Dict[str, Any]) -> Tuple[bool, str]:
    summary_status = str(report.get("summary", {}).get("status", "")).upper()
    checks = report.get("checks", {})

    freeze_done = (
        summary_status == "FREEZE_LOCKED_REPORT_FINALIZED"
        and str(checks.get("freeze_window_enabled", {}).get("status", "FAIL")).upper() == "PASS"
        and str(checks.get("freeze_observed_24h", {}).get("status", "FAIL")).upper() == "PASS"
        and str(checks.get("no_critical_changes", {}).get("status", "FAIL")).upper() == "PASS"
    )
    report_done = (
        summary_status == "FREEZE_LOCKED_REPORT_FINALIZED"
        and str(checks.get("post_cutover_report_ready", {}).get("status", "FAIL")).upper() == "PASS"
    )

    lines = checklist_path.read_text(encoding="utf-8").splitlines()

    start = None
    end = len(lines)
    for idx, line in enumerate(lines):
        if line.strip() == SECTION_HEADER:
            start = idx
            break

    if start is None:
        return False, "Day 28 section not found"

    for idx in range(start + 1, len(lines)):
        if lines[idx].startswith("### "):
            end = idx
            break

    changed = False
    for idx in range(start + 1, end):
        stripped = lines[idx].strip()
        if stripped.startswith("- [") and LINE_FREEZE in stripped:
            new_line = _replace_checkbox(lines[idx], freeze_done)
            if new_line != lines[idx]:
                lines[idx] = new_line
                changed = True
        if stripped.startswith("- [") and LINE_REPORT in stripped:
            new_line = _replace_checkbox(lines[idx], report_done)
            if new_line != lines[idx]:
                lines[idx] = new_line
                changed = True

    if changed:
        checklist_path.write_text("\n".join(lines) + "\n", encoding="utf-8")
        return True, "Checklist Day 28 updated"

    return False, "No checklist changes needed"


def write_watcher_report(output: Path, checklist_updated: bool, message: str, status: str) -> None:
    now = datetime.now(timezone.utc)
    payload = {
        "run_id": f"day28_watcher_{now.strftime('%Y%m%dT%H%M%SZ')}",
        "run_ts": now.isoformat(),
        "day28_status": status,
        "checklist_updated": checklist_updated,
        "message": message,
    }
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(payload, indent=2), encoding="utf-8")


def main() -> int:
    parser = argparse.ArgumentParser(description="Auto-update Day 28 checklist from freeze report")
    parser.add_argument(
        "--report",
        default="documentation/migration/reports/DAY28_FREEZE_REPORT.json",
        help="Path to Day 28 freeze report",
    )
    parser.add_argument(
        "--checklist",
        default="documentation/migration/MIGRATION_CHECKLIST_30_DAYS.md",
        help="Path to migration checklist",
    )
    parser.add_argument(
        "--output",
        default="documentation/migration/reports/DAY28_WATCHER_RESULT.json",
        help="Path to watcher result report",
    )

    args = parser.parse_args()

    report = _read_json(Path(args.report))
    status = str(report.get("summary", {}).get("status", "UNKNOWN")).upper()

    changed, message = update_day28_checklist(Path(args.checklist), report)
    write_watcher_report(Path(args.output), changed, message, status)

    print(f"[DONE] day28 watcher report: {args.output}")
    print(f"[STATUS] day28_status={status} checklist_updated={changed}")
    print(f"[INFO] {message}")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
