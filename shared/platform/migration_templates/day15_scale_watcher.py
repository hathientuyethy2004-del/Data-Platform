from __future__ import annotations

import argparse
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, Tuple

DAY15_HEADER = "### Ngày 15-16"
DAY15_SCALE_LINE = "Tăng tỷ lệ write/load OSS lên 50%."
DAY15_COMPARE_LINE = "Giữ dual-run compare tự động mỗi giờ."


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


def update_day15_checklist(checklist_path: Path, scale_report: Dict[str, Any]) -> Tuple[bool, str]:
    rollout = scale_report.get("rollout", {})
    checks = scale_report.get("checks", {})
    summary_status = str(scale_report.get("summary", {}).get("status", "")).upper()

    should_check_scale = summary_status == "SCALED_TO_50" and bool(rollout.get("applied", False))
    should_check_compare = str(checks.get("dual_run_compare_hourly_enabled", {}).get("status", "")).upper() == "PASS"

    lines = checklist_path.read_text(encoding="utf-8").splitlines()

    start = None
    end = len(lines)
    for idx, line in enumerate(lines):
        if line.strip() == DAY15_HEADER:
            start = idx
            break

    if start is None:
        return False, "Day 15-16 section not found"

    for idx in range(start + 1, len(lines)):
        if lines[idx].startswith("### "):
            end = idx
            break

    changed = False
    for idx in range(start + 1, end):
        stripped = lines[idx].strip()
        if stripped.startswith("- [") and DAY15_SCALE_LINE in stripped:
            new_line = _replace_checkbox(lines[idx], should_check_scale)
            if new_line != lines[idx]:
                lines[idx] = new_line
                changed = True
        if stripped.startswith("- [") and DAY15_COMPARE_LINE in stripped:
            new_line = _replace_checkbox(lines[idx], should_check_compare)
            if new_line != lines[idx]:
                lines[idx] = new_line
                changed = True

    if changed:
        checklist_path.write_text("\n".join(lines) + "\n", encoding="utf-8")
        return True, "Checklist Day 15-16 updated"

    return False, "No checklist changes needed"


def write_watcher_report(output: Path, checklist_updated: bool, message: str, day15_status: str) -> None:
    now = datetime.now(timezone.utc)
    payload = {
        "run_id": f"day15_watcher_{now.strftime('%Y%m%dT%H%M%SZ')}",
        "run_ts": now.isoformat(),
        "day15_status": day15_status,
        "checklist_updated": checklist_updated,
        "message": message,
    }
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(payload, indent=2), encoding="utf-8")


def main() -> int:
    parser = argparse.ArgumentParser(description="Auto-update Day 15-16 checklist from scale report")
    parser.add_argument(
        "--scale-report",
        default="documentation/migration/reports/DAY15_SCALE_REPORT.json",
        help="Path to Day 15 scale report",
    )
    parser.add_argument(
        "--checklist",
        default="documentation/migration/MIGRATION_CHECKLIST_30_DAYS.md",
        help="Path to migration checklist",
    )
    parser.add_argument(
        "--output",
        default="documentation/migration/reports/DAY15_WATCHER_RESULT.json",
        help="Path to watcher result report",
    )

    args = parser.parse_args()

    scale_report = _read_json(Path(args.scale_report))
    day15_status = str(scale_report.get("summary", {}).get("status", "UNKNOWN")).upper()

    changed, message = update_day15_checklist(Path(args.checklist), scale_report)
    write_watcher_report(Path(args.output), changed, message, day15_status)

    print(f"[DONE] day15 watcher report: {args.output}")
    print(f"[STATUS] day15_status={day15_status} checklist_updated={changed}")
    print(f"[INFO] {message}")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
