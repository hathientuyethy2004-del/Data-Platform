from __future__ import annotations

import argparse
import json
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any, Dict, Tuple


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


def _has_critical_issue(report: Dict[str, Any]) -> bool:
    issues = report.get("issues", [])
    for issue in issues:
        severity = str(issue.get("severity", "")).lower().strip()
        if severity == "critical":
            return True
    return False


def evaluate_gate(
    baseline_report: Dict[str, Any],
    smoke_report: Dict[str, Any],
    day6_regression_report: Dict[str, Any],
    min_stability_hours: int,
) -> Tuple[Dict[str, Any], int]:
    now = datetime.now(timezone.utc)

    baseline_ts = _parse_iso(str(baseline_report.get("run_ts")))
    elapsed_hours = round((now - baseline_ts).total_seconds() / 3600, 2)
    remaining_hours = round(max(0.0, float(min_stability_hours) - elapsed_hours), 2)
    estimated_pass_at = baseline_ts + timedelta(hours=min_stability_hours)

    smoke_pass = str(smoke_report.get("overall_status", "")).upper() == "PASS"
    baseline_pass = str(
        baseline_report.get("summary", {}).get("overall_status", "")
    ).upper() == "PASS"
    day6_pass = (
        str(day6_regression_report.get("result", {}).get("status", "")).upper() == "PASS"
    )

    critical_issue_count = int(baseline_report.get("summary", {}).get("critical_issues", 0))
    has_critical_issue_detail = _has_critical_issue(baseline_report)

    checks = {
        "dual_run_staging_stable_24h": {
            "required_hours": min_stability_hours,
            "observed_hours": elapsed_hours,
            "remaining_hours_to_gate": remaining_hours,
            "estimated_pass_at_utc": estimated_pass_at.isoformat(),
            "status": "PASS" if elapsed_hours >= min_stability_hours else "FAIL",
            "evidence": {
                "baseline_run_ts": baseline_report.get("run_ts"),
                "smoke_status": smoke_report.get("overall_status"),
                "baseline_status": baseline_report.get("summary", {}).get("overall_status"),
                "day6_regression_status": day6_regression_report.get("result", {}).get("status"),
            },
        },
        "no_critical_mismatch": {
            "critical_issues": critical_issue_count,
            "critical_issue_in_details": has_critical_issue_detail,
            "status": "PASS"
            if critical_issue_count == 0 and not has_critical_issue_detail
            else "FAIL",
        },
        "prerequisite_smoke_and_regression": {
            "smoke_status": smoke_report.get("overall_status"),
            "day6_regression_status": day6_regression_report.get("result", {}).get("status"),
            "status": "PASS" if smoke_pass and baseline_pass and day6_pass else "FAIL",
        },
    }

    gate_pass = (
        checks["dual_run_staging_stable_24h"]["status"] == "PASS"
        and checks["no_critical_mismatch"]["status"] == "PASS"
        and checks["prerequisite_smoke_and_regression"]["status"] == "PASS"
    )

    report = {
        "run_id": f"day7_gate1_{now.strftime('%Y%m%dT%H%M%SZ')}",
        "run_ts": now.isoformat(),
        "gate": "WEEK1_GATE1",
        "summary": {
            "status": "PASS" if gate_pass else "FAIL",
            "allow_move_to_week2": gate_pass,
            "remaining_hours_to_gate": remaining_hours,
            "estimated_pass_at_utc": estimated_pass_at.isoformat(),
            "reason": (
                "All Gate 1 checks passed"
                if gate_pass
                else "One or more Gate 1 checks failed"
            ),
        },
        "checks": checks,
        "inputs": {
            "baseline_report": "documentation/migration/reports/BASELINE_COMPARE_REPORT_DAY5.json",
            "smoke_report": "documentation/migration/reports/DAY5_SMOKE_RESULT.json",
            "day6_regression_report": "documentation/migration/reports/DAY6_REGRESSION_RESULT.json",
        },
        "next_actions": [
            "Continue dual-run monitoring until stability window reaches >= 24h if not yet met.",
            "Keep compare report checks running on schedule (hourly recommended).",
            "Approve transition to Week 2 only when Gate 1 status is PASS.",
        ],
    }

    return report, (0 if gate_pass else 2)


def main() -> int:
    parser = argparse.ArgumentParser(description="Evaluate Day 7 Week-1 Gate 1 readiness")
    parser.add_argument(
        "--baseline-report",
        default="documentation/migration/reports/BASELINE_COMPARE_REPORT_DAY5.json",
        help="Path to baseline compare report",
    )
    parser.add_argument(
        "--smoke-report",
        default="documentation/migration/reports/DAY5_SMOKE_RESULT.json",
        help="Path to smoke test report",
    )
    parser.add_argument(
        "--day6-regression-report",
        default="documentation/migration/reports/DAY6_REGRESSION_RESULT.json",
        help="Path to day6 regression report",
    )
    parser.add_argument(
        "--output",
        default="documentation/migration/reports/DAY7_GATE1_REPORT.json",
        help="Output path for gate report",
    )
    parser.add_argument(
        "--min-stability-hours",
        default=24,
        type=int,
        help="Required minimum dual-run stability hours",
    )

    args = parser.parse_args()

    baseline_path = Path(args.baseline_report)
    smoke_path = Path(args.smoke_report)
    day6_path = Path(args.day6_regression_report)
    output_path = Path(args.output)

    baseline_report = _read_json(baseline_path)
    smoke_report = _read_json(smoke_path)
    day6_regression_report = _read_json(day6_path)

    report, exit_code = evaluate_gate(
        baseline_report=baseline_report,
        smoke_report=smoke_report,
        day6_regression_report=day6_regression_report,
        min_stability_hours=args.min_stability_hours,
    )

    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(json.dumps(report, indent=2), encoding="utf-8")

    print(f"[DONE] day7 gate report: {output_path}")
    print(f"[STATUS] gate={report['summary']['status']}")

    return exit_code


if __name__ == "__main__":
    raise SystemExit(main())
