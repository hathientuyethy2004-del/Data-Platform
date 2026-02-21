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

    for path in sorted(history_dir.glob("DAY15_SCALE_REPORT_*.json")):
        reports.append(json.loads(path.read_text(encoding="utf-8")))

    if latest_file.exists():
        latest = json.loads(latest_file.read_text(encoding="utf-8"))
        latest_run_id = str(latest.get("run_id", ""))
        known_run_ids = {str(item.get("run_id", "")) for item in reports}
        if latest_run_id and latest_run_id not in known_run_ids:
            reports.append(latest)

    return reports


def build_day15_compare_trend_report(
    reports: List[Dict[str, Any]],
    window_hours: int,
) -> Dict[str, Any]:
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

    compare_pass = 0
    compare_fail = 0
    scaled_count = 0
    blocked_count = 0

    for report in in_window:
        checks = report.get("checks", {})
        compare_status = str(checks.get("dual_run_compare_hourly_enabled", {}).get("status", "")).upper()
        if compare_status == "PASS":
            compare_pass += 1
        else:
            compare_fail += 1

        rollout_status = str(report.get("rollout", {}).get("status", "")).upper()
        if rollout_status == "SCALED_TO_50":
            scaled_count += 1
        elif rollout_status == "BLOCKED":
            blocked_count += 1

    latest = in_window[-1] if in_window else None

    return {
        "run_id": f"day15_compare_trend_{now.strftime('%Y%m%dT%H%M%SZ')}",
        "run_ts": now.isoformat(),
        "window_hours": window_hours,
        "summary": {
            "total_runs": total,
            "compare_pass_runs": compare_pass,
            "compare_fail_runs": compare_fail,
            "compare_pass_rate_pct": round((compare_pass / total) * 100, 2) if total else 0.0,
            "scaled_to_50_runs": scaled_count,
            "blocked_runs": blocked_count,
            "status": "PASS" if total > 0 and compare_fail == 0 else "MONITORING",
        },
        "latest_snapshot": latest,
        "notes": [
            "Tracks Day 15 requirement: dual-run compare automation every hour.",
            "BLOCKED rollout can still be healthy if dual_run_compare_hourly_enabled remains PASS.",
        ],
    }


def main() -> int:
    parser = argparse.ArgumentParser(description="Build Day 15 hourly compare trend report")
    parser.add_argument(
        "--history-dir",
        default="documentation/migration/reports/history",
        help="Directory containing DAY15_SCALE_REPORT_*.json snapshots",
    )
    parser.add_argument(
        "--latest-file",
        default="documentation/migration/reports/DAY15_SCALE_REPORT.json",
        help="Path to latest day15 scale report",
    )
    parser.add_argument(
        "--window-hours",
        default=24,
        type=int,
        help="Time window to aggregate trend",
    )
    parser.add_argument(
        "--output",
        default="documentation/migration/reports/DAY15_COMPARE_TREND_24H.json",
        help="Path for trend output JSON",
    )

    args = parser.parse_args()

    history_dir = Path(args.history_dir)
    latest_file = Path(args.latest_file)
    reports = _load_reports(history_dir, latest_file)

    trend = build_day15_compare_trend_report(reports=reports, window_hours=args.window_hours)

    output_path = Path(args.output)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(json.dumps(trend, indent=2), encoding="utf-8")

    print(f"[DONE] day15 trend report: {output_path}")
    print(f"[STATUS] trend={trend['summary']['status']} runs={trend['summary']['total_runs']}")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
