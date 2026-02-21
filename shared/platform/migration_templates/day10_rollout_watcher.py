from __future__ import annotations

import argparse
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, Tuple

DAY10_HEADER = "### Ngày 10"
DAY10_CANARY_LINE = "Tăng canary lên 20% nếu error rate và mismatch trong ngưỡng."


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


def update_day10_checklist(checklist_path: Path, rollout_report: Dict[str, Any]) -> Tuple[bool, str]:
    rollout_status = str(rollout_report.get("summary", {}).get("status", "")).upper()
    should_check = rollout_status == "ROLLED_OUT"

    lines = checklist_path.read_text(encoding="utf-8").splitlines()

    start = None
    end = len(lines)
    for idx, line in enumerate(lines):
        if line.strip() == DAY10_HEADER:
            start = idx
            break

    if start is None:
        return False, "Day 10 section not found"

    for idx in range(start + 1, len(lines)):
        if lines[idx].startswith("### "):
            end = idx
            break

    changed = False
    for idx in range(start + 1, end):
        stripped = lines[idx].strip()
        if stripped.startswith("- [") and DAY10_CANARY_LINE in stripped:
            new_line = _replace_checkbox(lines[idx], should_check)
            if new_line != lines[idx]:
                lines[idx] = new_line
                changed = True
            break

    if changed:
        checklist_path.write_text("\n".join(lines) + "\n", encoding="utf-8")
        return True, "Checklist Day 10 updated"

    return False, "No checklist changes needed"


def write_watcher_report(output: Path, checklist_updated: bool, message: str, rollout_status: str) -> None:
    now = datetime.now(timezone.utc)
    payload = {
        "run_id": f"day10_watcher_{now.strftime('%Y%m%dT%H%M%SZ')}",
        "run_ts": now.isoformat(),
        "rollout_status": rollout_status,
        "checklist_updated": checklist_updated,
        "message": message,
    }
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(payload, indent=2), encoding="utf-8")


def main() -> int:
    parser = argparse.ArgumentParser(description="Auto-update Day 10 checklist from rollout report")
    parser.add_argument(
        "--rollout-report",
        default="documentation/migration/reports/DAY10_ROLLOUT_REPORT.json",
        help="Path to Day 10 rollout report",
    )
    parser.add_argument(
        "--checklist",
        default="documentation/migration/MIGRATION_CHECKLIST_30_DAYS.md",
        help="Path to migration checklist",
    )
    parser.add_argument(
        "--output",
        default="documentation/migration/reports/DAY10_WATCHER_RESULT.json",
        help="Path to watcher result report",
    )

    args = parser.parse_args()

    rollout_report = _read_json(Path(args.rollout_report))
    rollout_status = str(rollout_report.get("summary", {}).get("status", "UNKNOWN")).upper()

    changed, message = update_day10_checklist(Path(args.checklist), rollout_report)
    write_watcher_report(Path(args.output), changed, message, rollout_status)

    print(f"[DONE] day10 watcher report: {args.output}")
    print(f"[STATUS] rollout_status={rollout_status} checklist_updated={changed}")
    print(f"[INFO] {message}")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
