from __future__ import annotations

import argparse
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, Tuple

SECTION_HEADER = "### Ngày 22-24"
LINE_CUTOVER = "Cutover 100% write/load sang OSS."
LINE_SHADOW_READ = "Giữ shadow read từ legacy thêm 2-3 ngày để so sánh."


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


def update_day22_24_checklist(checklist_path: Path, report: Dict[str, Any]) -> Tuple[bool, str]:
    summary_status = str(report.get("summary", {}).get("status", "")).upper()
    cutover = report.get("cutover", {})

    cutover_applied = summary_status == "WRITE_LOAD_100_SHADOW_READ" and bool(cutover.get("applied", False))
    shadow_window_days = int(cutover.get("shadow_read_window_days", 0) or 0)
    shadow_read_enabled = bool(cutover.get("shadow_read_legacy_enabled", False))

    should_check_cutover = cutover_applied
    should_check_shadow = cutover_applied and shadow_read_enabled and 2 <= shadow_window_days <= 3

    lines = checklist_path.read_text(encoding="utf-8").splitlines()

    start = None
    end = len(lines)
    for idx, line in enumerate(lines):
        if line.strip() == SECTION_HEADER:
            start = idx
            break

    if start is None:
        return False, "Day 22-24 section not found"

    for idx in range(start + 1, len(lines)):
        if lines[idx].startswith("### "):
            end = idx
            break

    changed = False
    for idx in range(start + 1, end):
        stripped = lines[idx].strip()
        if stripped.startswith("- [") and LINE_CUTOVER in stripped:
            new_line = _replace_checkbox(lines[idx], should_check_cutover)
            if new_line != lines[idx]:
                lines[idx] = new_line
                changed = True
        if stripped.startswith("- [") and LINE_SHADOW_READ in stripped:
            new_line = _replace_checkbox(lines[idx], should_check_shadow)
            if new_line != lines[idx]:
                lines[idx] = new_line
                changed = True

    if changed:
        checklist_path.write_text("\n".join(lines) + "\n", encoding="utf-8")
        return True, "Checklist Day 22-24 updated"

    return False, "No checklist changes needed"


def write_watcher_report(output: Path, checklist_updated: bool, message: str, status: str) -> None:
    now = datetime.now(timezone.utc)
    payload = {
        "run_id": f"day22_24_watcher_{now.strftime('%Y%m%dT%H%M%SZ')}",
        "run_ts": now.isoformat(),
        "day22_24_status": status,
        "checklist_updated": checklist_updated,
        "message": message,
    }
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(payload, indent=2), encoding="utf-8")


def main() -> int:
    parser = argparse.ArgumentParser(description="Auto-update Day 22-24 checklist from cutover report")
    parser.add_argument(
        "--report",
        default="documentation/migration/reports/DAY22_24_CUTOVER_REPORT.json",
        help="Path to Day 22-24 cutover report",
    )
    parser.add_argument(
        "--checklist",
        default="documentation/migration/MIGRATION_CHECKLIST_30_DAYS.md",
        help="Path to migration checklist",
    )
    parser.add_argument(
        "--output",
        default="documentation/migration/reports/DAY22_24_WATCHER_RESULT.json",
        help="Path to watcher result report",
    )

    args = parser.parse_args()

    report = _read_json(Path(args.report))
    status = str(report.get("summary", {}).get("status", "UNKNOWN")).upper()

    changed, message = update_day22_24_checklist(Path(args.checklist), report)
    write_watcher_report(Path(args.output), changed, message, status)

    print(f"[DONE] day22_24 watcher report: {args.output}")
    print(f"[STATUS] day22_24_status={status} checklist_updated={changed}")
    print(f"[INFO] {message}")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
