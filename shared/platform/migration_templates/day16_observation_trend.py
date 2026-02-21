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

    for path in sorted(history_dir.glob("DAY16_OBSERVATION_REPORT_*.json")):
        reports.append(json.loads(path.read_text(encoding="utf-8")))

    if latest_file.exists():
        latest = json.loads(latest_file.read_text(encoding="utf-8"))
        latest_run_id = str(latest.get("run_id", ""))
        known_run_ids = {str(item.get("run_id", "")) for item in reports}
        if latest_run_id and latest_run_id not in known_run_ids:
            reports.append(latest)

    return reports


def build_day16_trend_report(reports: List[Dict[str, Any]], window_hours: int) -> Dict[str, Any]:
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
    ready_count = 0
    hold_count = 0
    for report in in_window:
        status = str(report.get("summary", {}).get("status", "HOLD")).upper()
        if status == "READY_FOR_DAY17":
            ready_count += 1
        else:
            hold_count += 1

    latest = in_window[-1] if in_window else None
    latest_status = str((latest or {}).get("summary", {}).get("status", "UNKNOWN")).upper()

    return {
        "run_id": f"day16_trend_{now.strftime('%Y%m%dT%H%M%SZ')}",
        "run_ts": now.isoformat(),
        "window_hours": window_hours,
        "summary": {
            "total_runs": total,
            "ready_runs": ready_count,
            "hold_runs": hold_count,
            "ready_rate_pct": round((ready_count / total) * 100, 2) if total else 0.0,
            "latest_status": latest_status,
            "status": "READY" if total > 0 and latest_status == "READY_FOR_DAY17" else "MONITORING",
        },
        "latest_snapshot": latest,
        "notes": [
            "Tracks Day 16 observation readiness progression in the last 24h.",
            "Transition to READY is driven by latest Day 16 report status READY_FOR_DAY17.",
        ],
    }


def main() -> int:
    parser = argparse.ArgumentParser(description="Build Day 16 observation trend report from hourly history")
    parser.add_argument(
        "--history-dir",
        default="documentation/migration/reports/history",
        help="Directory containing DAY16_OBSERVATION_REPORT_*.json snapshots",
    )
    parser.add_argument(
        "--latest-file",
        default="documentation/migration/reports/DAY16_OBSERVATION_REPORT.json",
        help="Path to latest Day 16 observation report",
    )
    parser.add_argument(
        "--window-hours",
        default=24,
        type=int,
        help="Time window to aggregate trend",
    )
    parser.add_argument(
        "--output",
        default="documentation/migration/reports/DAY16_OBSERVATION_TREND_24H.json",
        help="Path for trend output JSON",
    )

    args = parser.parse_args()

    reports = _load_reports(Path(args.history_dir), Path(args.latest_file))
    trend = build_day16_trend_report(reports=reports, window_hours=args.window_hours)

    output_path = Path(args.output)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(json.dumps(trend, indent=2), encoding="utf-8")

    print(f"[DONE] day16 trend report: {output_path}")
    print(f"[STATUS] trend={trend['summary']['status']} runs={trend['summary']['total_runs']}")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
