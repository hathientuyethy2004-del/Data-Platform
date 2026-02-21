from __future__ import annotations

import argparse
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, Tuple

SECTION_HEADER = "### Ngày 20"
LINE_TRAFFIC = "Tăng tổng traffic lên 80% (write + read tùy dịch vụ)."
LINE_AUDIT = "Audit lại permission, secret rotation, rate limiting."


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


def update_day20_checklist(checklist_path: Path, report: Dict[str, Any]) -> Tuple[bool, str]:
    summary_status = str(report.get("summary", {}).get("status", "")).upper()
    traffic = report.get("traffic", {})

    checks = report.get("checks", {})
    audit_checks_pass = all(
        str(checks.get(name, {}).get("status", "FAIL")).upper() == "PASS"
        for name in ["permission_audit_passed", "secret_rotation_checked", "rate_limiting_audit_passed"]
    )

    should_check_traffic = summary_status == "TRAFFIC_80_APPLIED" and bool(traffic.get("applied", False))
    should_check_audit = should_check_traffic and audit_checks_pass

    lines = checklist_path.read_text(encoding="utf-8").splitlines()

    start = None
    end = len(lines)
    for idx, line in enumerate(lines):
        if line.strip() == SECTION_HEADER:
            start = idx
            break

    if start is None:
        return False, "Day 20 section not found"

    for idx in range(start + 1, len(lines)):
        if lines[idx].startswith("### "):
            end = idx
            break

    changed = False
    for idx in range(start + 1, end):
        stripped = lines[idx].strip()
        if stripped.startswith("- [") and LINE_TRAFFIC in stripped:
            new_line = _replace_checkbox(lines[idx], should_check_traffic)
            if new_line != lines[idx]:
                lines[idx] = new_line
                changed = True
        if stripped.startswith("- [") and LINE_AUDIT in stripped:
            new_line = _replace_checkbox(lines[idx], should_check_audit)
            if new_line != lines[idx]:
                lines[idx] = new_line
                changed = True

    if changed:
        checklist_path.write_text("\n".join(lines) + "\n", encoding="utf-8")
        return True, "Checklist Day 20 updated"

    return False, "No checklist changes needed"


def write_watcher_report(output: Path, checklist_updated: bool, message: str, day20_status: str) -> None:
    now = datetime.now(timezone.utc)
    payload = {
        "run_id": f"day20_watcher_{now.strftime('%Y%m%dT%H%M%SZ')}",
        "run_ts": now.isoformat(),
        "day20_status": day20_status,
        "checklist_updated": checklist_updated,
        "message": message,
    }
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(payload, indent=2), encoding="utf-8")


def main() -> int:
    parser = argparse.ArgumentParser(description="Auto-update Day 20 checklist from traffic report")
    parser.add_argument(
        "--report",
        default="documentation/migration/reports/DAY20_TRAFFIC_REPORT.json",
        help="Path to Day 20 traffic report",
    )
    parser.add_argument(
        "--checklist",
        default="documentation/migration/MIGRATION_CHECKLIST_30_DAYS.md",
        help="Path to migration checklist",
    )
    parser.add_argument(
        "--output",
        default="documentation/migration/reports/DAY20_WATCHER_RESULT.json",
        help="Path to watcher result report",
    )

    args = parser.parse_args()

    report = _read_json(Path(args.report))
    day20_status = str(report.get("summary", {}).get("status", "UNKNOWN")).upper()

    changed, message = update_day20_checklist(Path(args.checklist), report)
    write_watcher_report(Path(args.output), changed, message, day20_status)

    print(f"[DONE] day20 watcher report: {args.output}")
    print(f"[STATUS] day20_status={day20_status} checklist_updated={changed}")
    print(f"[INFO] {message}")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
