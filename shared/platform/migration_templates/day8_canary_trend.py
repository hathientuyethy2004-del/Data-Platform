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

    for path in sorted(history_dir.glob("DAY8_CANARY_STATUS_*.json")):
        reports.append(json.loads(path.read_text(encoding="utf-8")))

    if latest_file.exists():
        latest = json.loads(latest_file.read_text(encoding="utf-8"))
        latest_run_id = str(latest.get("run_id", ""))
        known_run_ids = {str(item.get("run_id", "")) for item in reports}
        if latest_run_id and latest_run_id not in known_run_ids:
            reports.append(latest)

    return reports


def build_day8_trend_report(
    reports: List[Dict[str, Any]],
    window_hours: int,
) -> Dict[str, Any]:
    now = datetime.now(timezone.utc)
    cutoff = now - timedelta(hours=window_hours)

    in_window = []
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
    pass_count = sum(1 for r in in_window if str(r.get("summary", {}).get("status", "")).upper() == "PASS")
    fail_count = total - pass_count

    check_names = [
        "canary_write_percent_is_10",
        "read_path_stays_legacy",
        "dual_run_compare_enabled",
        "canary_distribution_sanity",
    ]

    check_stats: Dict[str, Dict[str, Any]] = {}
    for name in check_names:
        check_pass = 0
        check_total = 0
        for report in in_window:
            checks = report.get("checks", {})
            if name in checks:
                check_total += 1
                if str(checks[name].get("status", "")).upper() == "PASS":
                    check_pass += 1
        ratio = round((check_pass / check_total) * 100, 2) if check_total > 0 else 0.0
        check_stats[name] = {
            "pass": check_pass,
            "total": check_total,
            "pass_rate_pct": ratio,
        }

    latest = in_window[-1] if in_window else None

    return {
        "run_id": f"day8_trend_{now.strftime('%Y%m%dT%H%M%SZ')}",
        "run_ts": now.isoformat(),
        "window_hours": window_hours,
        "summary": {
            "total_runs": total,
            "pass_runs": pass_count,
            "fail_runs": fail_count,
            "overall_pass_rate_pct": round((pass_count / total) * 100, 2) if total else 0.0,
            "status": "PASS" if total > 0 and fail_count == 0 else "MONITORING",
        },
        "checks": check_stats,
        "latest_snapshot": latest,
        "notes": [
            "Use this report to evaluate Day 8-9 stability trend before Day 10 canary increase.",
            "A non-zero fail_runs indicates Day 8 setup drift that should be investigated.",
        ],
    }


def main() -> int:
    parser = argparse.ArgumentParser(description="Build Day 8 canary trend report from hourly history")
    parser.add_argument(
        "--history-dir",
        default="documentation/migration/reports/history",
        help="Directory containing hourly DAY8_CANARY_STATUS_*.json snapshots",
    )
    parser.add_argument(
        "--latest-file",
        default="documentation/migration/reports/DAY8_CANARY_STATUS.json",
        help="Path to latest day8 status file",
    )
    parser.add_argument(
        "--window-hours",
        default=24,
        type=int,
        help="Time window to aggregate trend",
    )
    parser.add_argument(
        "--output",
        default="documentation/migration/reports/DAY8_CANARY_TREND_24H.json",
        help="Path for trend output JSON",
    )
    args = parser.parse_args()

    history_dir = Path(args.history_dir)
    latest_file = Path(args.latest_file)
    reports = _load_reports(history_dir, latest_file)

    trend = build_day8_trend_report(reports=reports, window_hours=args.window_hours)

    output_path = Path(args.output)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(json.dumps(trend, indent=2), encoding="utf-8")

    print(f"[DONE] day8 trend report: {output_path}")
    print(f"[STATUS] trend={trend['summary']['status']} runs={trend['summary']['total_runs']}")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
