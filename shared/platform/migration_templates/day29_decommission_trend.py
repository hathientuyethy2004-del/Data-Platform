from __future__ import annotations

import argparse
import json
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any, Dict, List


def _parse_iso(ts: str) -> datetime:
    raw = ts.strip()
    if raw.endswith("Z"):
        raw = raw[:-1] + "+00:00"
    parsed = datetime.fromisoformat(raw)
    if parsed.tzinfo is None:
        parsed = parsed.replace(tzinfo=timezone.utc)
    return parsed.astimezone(timezone.utc)


def _load_reports(history_dir: Path, latest_file: Path) -> List[Dict[str, Any]]:
    reports: List[Dict[str, Any]] = []

    for path in sorted(history_dir.glob("DAY29_DECOMMISSION_REPORT_*.json")):
        reports.append(json.loads(path.read_text(encoding="utf-8")))

    if latest_file.exists():
        latest = json.loads(latest_file.read_text(encoding="utf-8"))
        latest_run_id = str(latest.get("run_id", ""))
        known_run_ids = {str(item.get("run_id", "")) for item in reports}
        if latest_run_id and latest_run_id not in known_run_ids:
            reports.append(latest)

    return reports


def build_day29_trend_report(reports: List[Dict[str, Any]], window_hours: int) -> Dict[str, Any]:
    now = datetime.now(timezone.utc)
    cutoff = now - timedelta(hours=window_hours)

    in_window: List[Dict[str, Any]] = []
    for report in reports:
        run_ts = report.get("run_ts")
        if not run_ts:
            continue
        try:
            run_dt = _parse_iso(str(run_ts))
        except ValueError:
            continue
        if run_dt >= cutoff:
            in_window.append(report)

    total = len(in_window)
    decommissioned_count = 0
    blocked_count = 0

    last_transition_to_decommissioned_at = None
    prev_status = None

    for report in in_window:
        status = str(report.get("summary", {}).get("status", "BLOCKED")).upper()
        run_ts = str(report.get("run_ts", ""))

        if status == "DECOMMISSIONED_WITH_BACKUP":
            decommissioned_count += 1
        elif status == "BLOCKED":
            blocked_count += 1

        if prev_status == "BLOCKED" and status == "DECOMMISSIONED_WITH_BACKUP":
            last_transition_to_decommissioned_at = run_ts

        prev_status = status

    latest = in_window[-1] if in_window else None
    latest_status = str((latest or {}).get("summary", {}).get("status", "UNKNOWN")).upper()

    return {
        "run_id": f"day29_trend_{now.strftime('%Y%m%dT%H%M%SZ')}",
        "run_ts": now.isoformat(),
        "window_hours": window_hours,
        "summary": {
            "total_runs": total,
            "decommissioned_with_backup_runs": decommissioned_count,
            "blocked_runs": blocked_count,
            "decommissioned_rate_pct": round((decommissioned_count / total) * 100, 2) if total else 0.0,
            "latest_status": latest_status,
            "status": "READY" if total > 0 and latest_status == "DECOMMISSIONED_WITH_BACKUP" else "MONITORING",
            "last_transition_to_decommissioned_with_backup_at": last_transition_to_decommissioned_at,
        },
        "latest_snapshot": latest,
        "notes": [
            "Tracks Day 29 decommission progression in last 24h.",
            "last_transition_to_decommissioned_with_backup_at shows first timestamp of latest BLOCKED -> DECOMMISSIONED_WITH_BACKUP transition.",
        ],
    }


def main() -> int:
    parser = argparse.ArgumentParser(description="Build Day 29 decommission trend report from hourly history")
    parser.add_argument(
        "--history-dir",
        default="documentation/migration/reports/history",
        help="Directory containing DAY29_DECOMMISSION_REPORT_*.json snapshots",
    )
    parser.add_argument(
        "--latest-file",
        default="documentation/migration/reports/DAY29_DECOMMISSION_REPORT.json",
        help="Path to latest Day 29 decommission report",
    )
    parser.add_argument(
        "--window-hours",
        default=24,
        type=int,
        help="Time window to aggregate trend",
    )
    parser.add_argument(
        "--output",
        default="documentation/migration/reports/DAY29_DECOMMISSION_TREND_24H.json",
        help="Path for trend output JSON",
    )

    args = parser.parse_args()

    reports = _load_reports(Path(args.history_dir), Path(args.latest_file))
    trend = build_day29_trend_report(reports=reports, window_hours=args.window_hours)

    output_path = Path(args.output)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(json.dumps(trend, indent=2), encoding="utf-8")

    print(f"[DONE] day29 trend report: {output_path}")
    print(f"[STATUS] trend={trend['summary']['status']} runs={trend['summary']['total_runs']}")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
