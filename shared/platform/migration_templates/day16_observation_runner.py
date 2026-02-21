from __future__ import annotations

import argparse
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict


def _read_json(path: Path) -> Dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def evaluate_day16_observation(
    day15_scale_report: Dict[str, Any],
    day15_trend_report: Dict[str, Any],
    cron_health_report: Dict[str, Any],
    min_trend_runs: int = 6,
    min_compare_pass_rate_pct: float = 99.0,
) -> Dict[str, Any]:
    now = datetime.now(timezone.utc)

    rollout = day15_scale_report.get("rollout", {})
    scale_summary = day15_scale_report.get("summary", {})
    trend_summary = day15_trend_report.get("summary", {})
    cron_checks = cron_health_report.get("checks", {})

    day15_scaled = (
        str(scale_summary.get("status", "")).upper() == "SCALED_TO_50"
        and bool(rollout.get("applied", False))
        and int(rollout.get("effective_percent", 0) or 0) >= 50
    )

    trend_runs = int(trend_summary.get("total_runs", 0) or 0)
    trend_pass_rate = float(trend_summary.get("compare_pass_rate_pct", 0.0) or 0.0)
    trend_status = str(trend_summary.get("status", "MONITORING")).upper()
    trend_healthy = (
        trend_status == "PASS"
        and trend_runs >= min_trend_runs
        and trend_pass_rate >= min_compare_pass_rate_pct
    )

    cron_overall_pass = str(cron_health_report.get("status", "FAIL")).upper() == "PASS"
    day14_cron_pass = str(cron_checks.get("day14_gate2_hourly", {}).get("status", "FAIL")).upper() == "PASS"
    day15_cron_pass = str(cron_checks.get("day15_compare_hourly", {}).get("status", "FAIL")).upper() == "PASS"
    cron_healthy = cron_overall_pass and day14_cron_pass and day15_cron_pass

    checks = {
        "day15_scaled_to_50": {
            "day15_status": scale_summary.get("status"),
            "effective_percent": rollout.get("effective_percent"),
            "status": "PASS" if day15_scaled else "FAIL",
        },
        "day15_compare_trend_stable": {
            "trend_status": trend_status,
            "total_runs": trend_runs,
            "compare_pass_rate_pct": trend_pass_rate,
            "required_min_runs": min_trend_runs,
            "required_min_pass_rate_pct": min_compare_pass_rate_pct,
            "status": "PASS" if trend_healthy else "FAIL",
        },
        "cron_health_recent": {
            "overall_status": cron_health_report.get("status"),
            "day14_status": cron_checks.get("day14_gate2_hourly", {}).get("status"),
            "day15_status": cron_checks.get("day15_compare_hourly", {}).get("status"),
            "status": "PASS" if cron_healthy else "FAIL",
        },
    }

    ready = all(item["status"] == "PASS" for item in checks.values())
    blockers = [name for name, detail in checks.items() if detail["status"] != "PASS"]

    return {
        "run_id": f"day16_observation_{now.strftime('%Y%m%dT%H%M%SZ')}",
        "run_ts": now.isoformat(),
        "scope": "Day 16 observation readiness for Day 17 controlled read-switch",
        "checks": checks,
        "summary": {
            "status": "READY_FOR_DAY17" if ready else "HOLD",
            "ready_for_day17_read_switch": ready,
            "blockers": blockers,
            "decision": (
                "Observation window healthy; can proceed to Day 17 read-switch planning"
                if ready
                else "Continue stabilization and observation before Day 17"
            ),
        },
        "inputs": {
            "day15_scale_report": "documentation/migration/reports/DAY15_SCALE_REPORT.json",
            "day15_compare_trend": "documentation/migration/reports/DAY15_COMPARE_TREND_24H.json",
            "cron_health_report": "documentation/migration/reports/MIGRATION_CRON_HEALTH_STATUS.json",
        },
    }


def main() -> int:
    parser = argparse.ArgumentParser(description="Run Day 16 observation readiness check")
    parser.add_argument(
        "--day15-scale-report",
        default="documentation/migration/reports/DAY15_SCALE_REPORT.json",
        help="Path to Day 15 scale report",
    )
    parser.add_argument(
        "--day15-trend-report",
        default="documentation/migration/reports/DAY15_COMPARE_TREND_24H.json",
        help="Path to Day 15 compare trend report",
    )
    parser.add_argument(
        "--cron-health-report",
        default="documentation/migration/reports/MIGRATION_CRON_HEALTH_STATUS.json",
        help="Path to migration cron health status report",
    )
    parser.add_argument(
        "--min-trend-runs",
        default=6,
        type=int,
        help="Minimum number of trend runs in window",
    )
    parser.add_argument(
        "--min-compare-pass-rate-pct",
        default=99.0,
        type=float,
        help="Minimum compare pass rate in trend window",
    )
    parser.add_argument(
        "--output",
        default="documentation/migration/reports/DAY16_OBSERVATION_REPORT.json",
        help="Path to Day 16 output report",
    )

    args = parser.parse_args()

    report = evaluate_day16_observation(
        day15_scale_report=_read_json(Path(args.day15_scale_report)),
        day15_trend_report=_read_json(Path(args.day15_trend_report)),
        cron_health_report=_read_json(Path(args.cron_health_report)),
        min_trend_runs=args.min_trend_runs,
        min_compare_pass_rate_pct=args.min_compare_pass_rate_pct,
    )

    output_path = Path(args.output)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(json.dumps(report, indent=2), encoding="utf-8")

    print(f"[DONE] day16 report: {output_path}")
    print(f"[STATUS] day16={report['summary']['status']}")

    return 0 if report["summary"]["status"] == "READY_FOR_DAY17" else 2


if __name__ == "__main__":
    raise SystemExit(main())
