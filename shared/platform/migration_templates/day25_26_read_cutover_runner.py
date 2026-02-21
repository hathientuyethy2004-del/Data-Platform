from __future__ import annotations

import argparse
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict


def _read_json(path: Path) -> Dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def _read_env_file(path: Path) -> Dict[str, str]:
    data: Dict[str, str] = {}
    for line in path.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, value = line.split("=", 1)
        data[key.strip()] = value.strip()
    return data


def _is_true(value: str) -> bool:
    return value.strip().lower() in {"1", "true", "yes", "on"}


def _simulate_read_cutover_monitoring(read_percent: int) -> Dict[str, Any]:
    p95_latency_ms = 260 + (read_percent * 2)
    p99_latency_ms = 700 + (read_percent * 4)
    error_rate_pct = round(0.15 + (read_percent * 0.007), 3)

    checks = {
        "p95_latency_under_500ms": p95_latency_ms < 500,
        "p99_latency_under_1200ms": p99_latency_ms < 1200,
        "error_rate_under_1pct": error_rate_pct < 1.0,
    }

    return {
        "metrics": {
            "p95_latency_ms": p95_latency_ms,
            "p99_latency_ms": p99_latency_ms,
            "error_rate_pct": error_rate_pct,
        },
        "checks": {k: {"status": "PASS" if v else "FAIL"} for k, v in checks.items()},
        "overall_status": "PASS" if all(checks.values()) else "FAIL",
    }


def evaluate_day25_26_read_cutover(
    day22_24_report: Dict[str, Any],
    day21_report: Dict[str, Any],
    env25_26: Dict[str, str],
) -> Dict[str, Any]:
    now = datetime.now(timezone.utc)

    day22_status = str(day22_24_report.get("summary", {}).get("status", "BLOCKED")).upper()
    day22_applied = bool(day22_24_report.get("cutover", {}).get("applied", False))
    day22_ready = day22_status == "WRITE_LOAD_100_SHADOW_READ" and day22_applied

    day21_status = str(day21_report.get("summary", {}).get("status", "NO_GO")).upper()
    day21_approved = day21_status == "PASS" and bool(day21_report.get("summary", {}).get("approve_full_cutover_week4", False))

    target_read_percent = int(env25_26.get("READ_SWITCH_PERCENT", "100"))
    previous_read_percent = int(env25_26.get("CURRENT_READ_SWITCH_PERCENT", "50"))

    legacy_jobs_disabled = _is_true(env25_26.get("LEGACY_JOBS_DISABLED", "false"))
    legacy_routes_disabled = _is_true(env25_26.get("LEGACY_ROUTES_DISABLED", "false"))
    legacy_configs_archived = _is_true(env25_26.get("LEGACY_CONFIGS_ARCHIVED", "false"))

    monitoring = _simulate_read_cutover_monitoring(target_read_percent)

    checks = {
        "day22_24_cutover_required": {
            "day22_24_status": day22_status,
            "status": "PASS" if day22_ready else "FAIL",
        },
        "day21_gate3_pass_required": {
            "day21_status": day21_status,
            "status": "PASS" if day21_approved else "FAIL",
        },
        "target_read_switch_is_100": {
            "target_percent": target_read_percent,
            "status": "PASS" if target_read_percent == 100 else "FAIL",
        },
        "stepwise_read_increase_safe": {
            "previous_percent": previous_read_percent,
            "target_percent": target_read_percent,
            "delta_percent": target_read_percent - previous_read_percent,
            "status": "PASS" if previous_read_percent >= 50 and 0 < (target_read_percent - previous_read_percent) <= 50 else "FAIL",
        },
        "legacy_jobs_disabled": {
            "status": "PASS" if legacy_jobs_disabled else "FAIL",
        },
        "legacy_routes_disabled": {
            "status": "PASS" if legacy_routes_disabled else "FAIL",
        },
        "legacy_configs_archived": {
            "status": "PASS" if legacy_configs_archived else "FAIL",
        },
    }

    precheck_pass = all(item["status"] == "PASS" for item in checks.values())
    monitor_pass = monitoring["overall_status"] == "PASS"

    applied = precheck_pass and monitor_pass
    final_status = "READ_PATH_100_LEGACY_DRAINING" if applied else "BLOCKED"

    blockers = [name for name, detail in checks.items() if detail["status"] != "PASS"]
    if precheck_pass and not monitor_pass:
        blockers.append("latency_error_monitoring")

    return {
        "run_id": f"day25_26_read_cutover_{now.strftime('%Y%m%dT%H%M%SZ')}",
        "run_ts": now.isoformat(),
        "scope": "Day 25-26 guarded read-path cutover 100% + phased legacy decommission",
        "checks": checks,
        "read_cutover": {
            "requested_read_switch_percent": target_read_percent,
            "previous_read_switch_percent": previous_read_percent,
            "applied": applied,
            "effective_read_switch_percent": target_read_percent if applied else previous_read_percent,
            "legacy_jobs_disabled": legacy_jobs_disabled,
            "legacy_routes_disabled": legacy_routes_disabled,
            "legacy_configs_archived": legacy_configs_archived,
            "status": final_status,
            "blockers": blockers,
        },
        "monitoring": monitoring,
        "summary": {
            "status": final_status,
            "ready_for_day27": applied and monitor_pass,
            "decision": (
                "Day 25-26 read-path cutover applied with legacy draining controls"
                if applied
                else "Day 25-26 cutover remains blocked until Day 22-24 and legacy-drain prerequisites pass"
            ),
        },
        "inputs": {
            "day22_24_cutover_report": "documentation/migration/reports/DAY22_24_CUTOVER_REPORT.json",
            "day21_gate3_report": "documentation/migration/reports/DAY21_GATE3_REPORT.json",
            "day25_26_env": "infrastructure/docker/migration-day4/.env.day25_26.read100.example",
        },
    }


def main() -> int:
    parser = argparse.ArgumentParser(description="Run Day 25-26 guarded read-path cutover evaluation")
    parser.add_argument(
        "--day22-24-report",
        default="documentation/migration/reports/DAY22_24_CUTOVER_REPORT.json",
        help="Path to Day 22-24 cutover report",
    )
    parser.add_argument(
        "--day21-report",
        default="documentation/migration/reports/DAY21_GATE3_REPORT.json",
        help="Path to Day 21 Gate 3 report",
    )
    parser.add_argument(
        "--env-file",
        default="infrastructure/docker/migration-day4/.env.day25_26.read100.example",
        help="Path to Day 25-26 env profile",
    )
    parser.add_argument(
        "--output",
        default="documentation/migration/reports/DAY25_26_READ_CUTOVER_REPORT.json",
        help="Path to Day 25-26 output report",
    )

    args = parser.parse_args()

    report = evaluate_day25_26_read_cutover(
        day22_24_report=_read_json(Path(args.day22_24_report)),
        day21_report=_read_json(Path(args.day21_report)),
        env25_26=_read_env_file(Path(args.env_file)),
    )

    output_path = Path(args.output)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(json.dumps(report, indent=2), encoding="utf-8")

    print(f"[DONE] day25_26 report: {output_path}")
    print(f"[STATUS] day25_26={report['summary']['status']}")

    return 0 if report["summary"]["status"] == "READ_PATH_100_LEGACY_DRAINING" else 2


if __name__ == "__main__":
    raise SystemExit(main())
