from __future__ import annotations

import argparse
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict


def _read_json(path: Path) -> Dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def evaluate_day9_readiness(
    day8_status: Dict[str, Any],
    day8_trend: Dict[str, Any],
    day7_gate: Dict[str, Any],
    min_trend_runs: int,
    required_pass_rate_pct: float,
) -> Dict[str, Any]:
    now = datetime.now(timezone.utc)

    day8_ready = bool(day8_status.get("summary", {}).get("day8_canary_ready", False))
    trend_summary = day8_trend.get("summary", {})
    trend_runs = int(trend_summary.get("total_runs", 0))
    trend_fail_runs = int(trend_summary.get("fail_runs", 0))
    trend_pass_rate = float(trend_summary.get("overall_pass_rate_pct", 0.0))

    gate_summary = day7_gate.get("summary", {})
    gate_status = str(gate_summary.get("status", "UNKNOWN")).upper()

    checks = {
        "day8_canary_setup_ready": {
            "value": day8_ready,
            "status": "PASS" if day8_ready else "FAIL",
        },
        "trend_has_minimum_runs": {
            "required": min_trend_runs,
            "actual": trend_runs,
            "status": "PASS" if trend_runs >= min_trend_runs else "FAIL",
        },
        "trend_has_no_fail_runs": {
            "fail_runs": trend_fail_runs,
            "status": "PASS" if trend_fail_runs == 0 else "FAIL",
        },
        "trend_pass_rate_threshold": {
            "required_pct": required_pass_rate_pct,
            "actual_pct": trend_pass_rate,
            "status": "PASS" if trend_pass_rate >= required_pass_rate_pct else "FAIL",
        },
        "gate1_week1_passed": {
            "gate_status": gate_status,
            "status": "PASS" if gate_status == "PASS" else "FAIL",
            "remaining_hours_to_gate": gate_summary.get("remaining_hours_to_gate"),
            "estimated_pass_at_utc": gate_summary.get("estimated_pass_at_utc"),
        },
    }

    all_pass = all(item["status"] == "PASS" for item in checks.values())

    blockers = [name for name, item in checks.items() if item["status"] == "FAIL"]

    return {
        "run_id": f"day9_readiness_{now.strftime('%Y%m%dT%H%M%SZ')}",
        "run_ts": now.isoformat(),
        "scope": "Day 9 stability and Day 10 canary increase readiness",
        "checks": checks,
        "summary": {
            "status": "GO" if all_pass else "NO_GO",
            "ready_for_day10_canary_20": all_pass,
            "blockers": blockers,
        },
        "inputs": {
            "day8_status": "documentation/migration/reports/DAY8_CANARY_STATUS.json",
            "day8_trend": "documentation/migration/reports/DAY8_CANARY_TREND_24H.json",
            "day7_gate": "documentation/migration/reports/DAY7_GATE1_REPORT.json",
        },
        "next_actions": [
            "If NO_GO: keep canary at 10%, continue hourly trend monitoring, and resolve blockers.",
            "If GO: prepare Day 10 rollout plan to increase canary to 20% with guardrails.",
        ],
    }


def main() -> int:
    parser = argparse.ArgumentParser(description="Evaluate Day 9 readiness for Day 10 canary increase")
    parser.add_argument(
        "--day8-status",
        default="documentation/migration/reports/DAY8_CANARY_STATUS.json",
        help="Path to day8 status report",
    )
    parser.add_argument(
        "--day8-trend",
        default="documentation/migration/reports/DAY8_CANARY_TREND_24H.json",
        help="Path to day8 24h trend report",
    )
    parser.add_argument(
        "--day7-gate",
        default="documentation/migration/reports/DAY7_GATE1_REPORT.json",
        help="Path to day7 gate report",
    )
    parser.add_argument(
        "--min-trend-runs",
        default=6,
        type=int,
        help="Minimum number of Day 8 trend runs required to consider stability evidence",
    )
    parser.add_argument(
        "--required-pass-rate-pct",
        default=99.0,
        type=float,
        help="Minimum pass rate percentage required for trend readiness",
    )
    parser.add_argument(
        "--output",
        default="documentation/migration/reports/DAY9_STABILITY_REPORT.json",
        help="Path to day9 readiness report",
    )

    args = parser.parse_args()

    day8_status = _read_json(Path(args.day8_status))
    day8_trend = _read_json(Path(args.day8_trend))
    day7_gate = _read_json(Path(args.day7_gate))

    report = evaluate_day9_readiness(
        day8_status=day8_status,
        day8_trend=day8_trend,
        day7_gate=day7_gate,
        min_trend_runs=args.min_trend_runs,
        required_pass_rate_pct=args.required_pass_rate_pct,
    )

    output_path = Path(args.output)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(json.dumps(report, indent=2), encoding="utf-8")

    print(f"[DONE] day9 report: {output_path}")
    print(f"[STATUS] day9={report['summary']['status']}")

    return 0 if report["summary"]["status"] == "GO" else 2


if __name__ == "__main__":
    raise SystemExit(main())
