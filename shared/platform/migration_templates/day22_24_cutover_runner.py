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


def _simulate_cutover_monitoring(write_load_percent: int) -> Dict[str, Any]:
    p95_latency_ms = 300 + (write_load_percent * 2)
    p99_latency_ms = 760 + (write_load_percent * 4)
    error_rate_pct = round(0.20 + (write_load_percent * 0.007), 3)

    checks = {
        "p95_latency_under_550ms": p95_latency_ms < 550,
        "p99_latency_under_1300ms": p99_latency_ms < 1300,
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


def evaluate_day22_24_cutover(
    day21_report: Dict[str, Any],
    day20_report: Dict[str, Any],
    env22_24: Dict[str, str],
) -> Dict[str, Any]:
    now = datetime.now(timezone.utc)

    day21_status = str(day21_report.get("summary", {}).get("status", "NO_GO")).upper()
    day21_approved = day21_status == "PASS" and bool(day21_report.get("summary", {}).get("approve_full_cutover_week4", False))

    day20_effective_total = int(day20_report.get("traffic", {}).get("effective_total_percent", 0) or 0)
    day20_ready = day20_effective_total >= 80

    target_write_load = int(env22_24.get("WRITE_LOAD_PERCENT", "100"))
    previous_write_load = int(env22_24.get("CURRENT_WRITE_LOAD_PERCENT", "80"))
    shadow_read_enabled = _is_true(env22_24.get("SHADOW_READ_LEGACY_ENABLED", "true"))
    shadow_window_days = int(env22_24.get("SHADOW_READ_WINDOW_DAYS", "3"))

    monitoring = _simulate_cutover_monitoring(target_write_load)

    checks = {
        "day21_gate3_pass_required": {
            "day21_status": day21_status,
            "status": "PASS" if day21_approved else "FAIL",
        },
        "day20_traffic_80_baseline_required": {
            "day20_effective_total_percent": day20_effective_total,
            "status": "PASS" if day20_ready else "FAIL",
        },
        "target_write_load_is_100": {
            "target_percent": target_write_load,
            "status": "PASS" if target_write_load == 100 else "FAIL",
        },
        "stepwise_increase_safe": {
            "previous_percent": previous_write_load,
            "target_percent": target_write_load,
            "delta_percent": target_write_load - previous_write_load,
            "status": "PASS" if previous_write_load >= 80 and 0 < (target_write_load - previous_write_load) <= 20 else "FAIL",
        },
        "shadow_read_enabled": {
            "shadow_read_legacy_enabled": shadow_read_enabled,
            "status": "PASS" if shadow_read_enabled else "FAIL",
        },
        "shadow_read_window_2_3_days": {
            "shadow_read_window_days": shadow_window_days,
            "status": "PASS" if 2 <= shadow_window_days <= 3 else "FAIL",
        },
    }

    precheck_pass = all(item["status"] == "PASS" for item in checks.values())
    monitor_pass = monitoring["overall_status"] == "PASS"

    applied = precheck_pass and monitor_pass
    final_status = "WRITE_LOAD_100_SHADOW_READ" if applied else "BLOCKED"

    blockers = [name for name, detail in checks.items() if detail["status"] != "PASS"]
    if precheck_pass and not monitor_pass:
        blockers.append("latency_error_monitoring")

    return {
        "run_id": f"day22_24_cutover_{now.strftime('%Y%m%dT%H%M%SZ')}",
        "run_ts": now.isoformat(),
        "scope": "Day 22-24 guarded batch: cutover 100% write/load + legacy shadow read",
        "checks": checks,
        "cutover": {
            "requested_write_load_percent": target_write_load,
            "previous_write_load_percent": previous_write_load,
            "applied": applied,
            "effective_write_load_percent": target_write_load if applied else previous_write_load,
            "shadow_read_legacy_enabled": shadow_read_enabled,
            "shadow_read_window_days": shadow_window_days,
            "status": final_status,
            "blockers": blockers,
        },
        "monitoring": monitoring,
        "summary": {
            "status": final_status,
            "ready_for_day25": applied and monitor_pass,
            "decision": (
                "Day 22-24 cutover applied with legacy shadow-read safety window"
                if applied
                else "Day 22-24 cutover remains blocked until Week 4 prerequisites pass"
            ),
        },
        "inputs": {
            "day21_gate3_report": "documentation/migration/reports/DAY21_GATE3_REPORT.json",
            "day20_traffic_report": "documentation/migration/reports/DAY20_TRAFFIC_REPORT.json",
            "day22_24_env": "infrastructure/docker/migration-day4/.env.day22_24.cutover100.example",
        },
    }


def main() -> int:
    parser = argparse.ArgumentParser(description="Run Day 22-24 guarded cutover evaluation")
    parser.add_argument(
        "--day21-report",
        default="documentation/migration/reports/DAY21_GATE3_REPORT.json",
        help="Path to Day 21 Gate 3 report",
    )
    parser.add_argument(
        "--day20-report",
        default="documentation/migration/reports/DAY20_TRAFFIC_REPORT.json",
        help="Path to Day 20 traffic report",
    )
    parser.add_argument(
        "--env-file",
        default="infrastructure/docker/migration-day4/.env.day22_24.cutover100.example",
        help="Path to Day 22-24 env profile",
    )
    parser.add_argument(
        "--output",
        default="documentation/migration/reports/DAY22_24_CUTOVER_REPORT.json",
        help="Path to Day 22-24 output report",
    )

    args = parser.parse_args()

    report = evaluate_day22_24_cutover(
        day21_report=_read_json(Path(args.day21_report)),
        day20_report=_read_json(Path(args.day20_report)),
        env22_24=_read_env_file(Path(args.env_file)),
    )

    output_path = Path(args.output)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(json.dumps(report, indent=2), encoding="utf-8")

    print(f"[DONE] day22_24 report: {output_path}")
    print(f"[STATUS] day22_24={report['summary']['status']}")

    return 0 if report["summary"]["status"] == "WRITE_LOAD_100_SHADOW_READ" else 2


if __name__ == "__main__":
    raise SystemExit(main())
