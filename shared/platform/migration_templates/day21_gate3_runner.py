from __future__ import annotations

import argparse
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict


def _read_json(path: Path) -> Dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def _parse_iso(ts: str) -> datetime:
    raw = ts.strip()
    if raw.endswith("Z"):
        raw = raw[:-1] + "+00:00"
    parsed = datetime.fromisoformat(raw)
    if parsed.tzinfo is None:
        parsed = parsed.replace(tzinfo=timezone.utc)
    return parsed.astimezone(timezone.utc)


def evaluate_gate3(
    day20_report: Dict[str, Any],
    day15_compare_trend: Dict[str, Any],
    min_stability_hours: int = 72,
    min_compare_pass_rate_pct: float = 99.5,
) -> Dict[str, Any]:
    now = datetime.now(timezone.utc)

    day20_summary = day20_report.get("summary", {})
    day20_traffic = day20_report.get("traffic", {})
    day20_status = str(day20_summary.get("status", "BLOCKED")).upper()
    day20_applied = bool(day20_traffic.get("applied", False))
    day20_effective_percent = int(day20_traffic.get("effective_total_percent", 0) or 0)
    day20_run_ts = _parse_iso(str(day20_report.get("run_ts", now.isoformat())))

    observed_hours = round((now - day20_run_ts).total_seconds() / 3600, 2)
    remaining_hours = round(max(0.0, float(min_stability_hours) - observed_hours), 2)

    trend_summary = day15_compare_trend.get("summary", {})
    compare_pass_rate_pct = float(trend_summary.get("compare_pass_rate_pct", 0.0) or 0.0)
    compare_total_runs = int(trend_summary.get("total_runs", 0) or 0)

    checks = {
        "traffic_80_stable_72h": {
            "day20_status": day20_status,
            "day20_applied": day20_applied,
            "effective_total_percent": day20_effective_percent,
            "required_hours": min_stability_hours,
            "observed_hours": observed_hours,
            "remaining_hours": remaining_hours,
            "status": "PASS"
            if day20_status == "TRAFFIC_80_APPLIED"
            and day20_applied
            and day20_effective_percent >= 80
            and observed_hours >= min_stability_hours
            else "FAIL",
        },
        "compare_pass_rate_99_5": {
            "compare_pass_rate_pct": compare_pass_rate_pct,
            "required_min_pass_rate_pct": min_compare_pass_rate_pct,
            "total_runs": compare_total_runs,
            "status": "PASS" if compare_total_runs > 0 and compare_pass_rate_pct >= min_compare_pass_rate_pct else "FAIL",
        },
    }

    gate_pass = all(item["status"] == "PASS" for item in checks.values())

    return {
        "run_id": f"day21_gate3_{now.strftime('%Y%m%dT%H%M%SZ')}",
        "run_ts": now.isoformat(),
        "gate": "WEEK3_GATE3",
        "scope": "Day 21 Gate 3 evaluation for Week 4 full cutover approval",
        "checks": checks,
        "summary": {
            "status": "PASS" if gate_pass else "NO_GO",
            "approve_full_cutover_week4": gate_pass,
            "blockers": [name for name, item in checks.items() if item["status"] == "FAIL"],
            "decision": (
                "Gate 3 passed, approved for Week 4 full cutover"
                if gate_pass
                else "Gate 3 not met; continue stabilization at 80%"
            ),
        },
        "inputs": {
            "day20_traffic_report": "documentation/migration/reports/DAY20_TRAFFIC_REPORT.json",
            "day15_compare_trend": "documentation/migration/reports/DAY15_COMPARE_TREND_24H.json",
        },
    }


def main() -> int:
    parser = argparse.ArgumentParser(description="Run Day 21 Gate 3 evaluation")
    parser.add_argument(
        "--day20-report",
        default="documentation/migration/reports/DAY20_TRAFFIC_REPORT.json",
        help="Path to Day 20 traffic report",
    )
    parser.add_argument(
        "--day15-compare-trend",
        default="documentation/migration/reports/DAY15_COMPARE_TREND_24H.json",
        help="Path to Day 15 compare trend report",
    )
    parser.add_argument(
        "--min-stability-hours",
        default=72,
        type=int,
        help="Required stability window in hours at 80% traffic",
    )
    parser.add_argument(
        "--min-compare-pass-rate-pct",
        default=99.5,
        type=float,
        help="Required minimum compare pass rate percentage",
    )
    parser.add_argument(
        "--output",
        default="documentation/migration/reports/DAY21_GATE3_REPORT.json",
        help="Path to Day 21 Gate 3 output report",
    )

    args = parser.parse_args()

    report = evaluate_gate3(
        day20_report=_read_json(Path(args.day20_report)),
        day15_compare_trend=_read_json(Path(args.day15_compare_trend)),
        min_stability_hours=args.min_stability_hours,
        min_compare_pass_rate_pct=args.min_compare_pass_rate_pct,
    )

    output_path = Path(args.output)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(json.dumps(report, indent=2), encoding="utf-8")

    print(f"[DONE] day21 report: {output_path}")
    print(f"[STATUS] gate3={report['summary']['status']}")

    return 0 if report["summary"]["status"] == "PASS" else 2


if __name__ == "__main__":
    raise SystemExit(main())
