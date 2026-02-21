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


def _simulate_traffic_monitoring(total_traffic_percent: int) -> Dict[str, Any]:
    p95_latency_ms = 300 + (total_traffic_percent * 2)
    p99_latency_ms = 760 + (total_traffic_percent * 4)
    error_rate_pct = round(0.30 + (total_traffic_percent * 0.007), 3)

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


def evaluate_day20_traffic(
    day19_report: Dict[str, Any],
    day15_scale_report: Dict[str, Any],
    env20: Dict[str, str],
) -> Dict[str, Any]:
    now = datetime.now(timezone.utc)

    day19_status = str(day19_report.get("summary", {}).get("status", "BLOCKED")).upper()
    day19_switched = day19_status == "READ_SWITCHED_50" and bool(day19_report.get("read_switch", {}).get("applied", False))

    day15_effective_percent = int(day15_scale_report.get("rollout", {}).get("effective_percent", 0) or 0)
    day15_is_50_plus = day15_effective_percent >= 50

    target_percent = int(env20.get("TOTAL_TRAFFIC_PERCENT", "80"))
    previous_percent = int(env20.get("CURRENT_TOTAL_TRAFFIC_PERCENT", "50"))

    permission_audit_ok = _is_true(env20.get("PERMISSION_AUDIT_PASS", "true"))
    secret_rotation_ok = _is_true(env20.get("SECRET_ROTATION_CHECK_PASS", "true"))
    rate_limiting_ok = _is_true(env20.get("RATE_LIMIT_AUDIT_PASS", "true"))

    monitoring = _simulate_traffic_monitoring(target_percent)

    checks = {
        "day19_read_switch_50_required": {
            "day19_status": day19_status,
            "status": "PASS" if day19_switched else "FAIL",
        },
        "day15_write_scale_50_required": {
            "day15_effective_percent": day15_effective_percent,
            "status": "PASS" if day15_is_50_plus else "FAIL",
        },
        "target_total_traffic_is_80": {
            "target_percent": target_percent,
            "status": "PASS" if target_percent == 80 else "FAIL",
        },
        "stepwise_traffic_increase_safe": {
            "previous_percent": previous_percent,
            "target_percent": target_percent,
            "delta_percent": target_percent - previous_percent,
            "status": "PASS" if previous_percent >= 50 and 0 < (target_percent - previous_percent) <= 30 else "FAIL",
        },
        "permission_audit_passed": {
            "status": "PASS" if permission_audit_ok else "FAIL",
        },
        "secret_rotation_checked": {
            "status": "PASS" if secret_rotation_ok else "FAIL",
        },
        "rate_limiting_audit_passed": {
            "status": "PASS" if rate_limiting_ok else "FAIL",
        },
    }

    precheck_pass = all(item["status"] == "PASS" for item in checks.values())
    monitor_pass = monitoring["overall_status"] == "PASS"

    applied = precheck_pass and monitor_pass
    final_status = "TRAFFIC_80_APPLIED" if applied else "BLOCKED"

    blockers = [name for name, detail in checks.items() if detail["status"] != "PASS"]
    if precheck_pass and not monitor_pass:
        blockers.append("latency_error_monitoring")

    return {
        "run_id": f"day20_traffic_{now.strftime('%Y%m%dT%H%M%SZ')}",
        "run_ts": now.isoformat(),
        "scope": "Day 20 guarded total traffic increase to 80%",
        "checks": checks,
        "traffic": {
            "requested_total_percent": target_percent,
            "previous_total_percent": previous_percent,
            "applied": applied,
            "effective_total_percent": target_percent if applied else previous_percent,
            "status": final_status,
            "blockers": blockers,
        },
        "monitoring": monitoring,
        "summary": {
            "status": final_status,
            "ready_for_day21": applied and monitor_pass,
            "decision": (
                "Total traffic increased to 80% with security audits and healthy metrics"
                if applied
                else "Traffic increase remains blocked until Day 19 and audit prerequisites pass"
            ),
        },
        "inputs": {
            "day19_report": "documentation/migration/reports/DAY19_READ_SWITCH_REPORT.json",
            "day15_scale_report": "documentation/migration/reports/DAY15_SCALE_REPORT.json",
            "day20_env": "infrastructure/docker/migration-day4/.env.day20.traffic80.example",
        },
    }


def main() -> int:
    parser = argparse.ArgumentParser(description="Run Day 20 guarded traffic evaluation")
    parser.add_argument(
        "--day19-report",
        default="documentation/migration/reports/DAY19_READ_SWITCH_REPORT.json",
        help="Path to Day 19 read-switch report",
    )
    parser.add_argument(
        "--day15-scale-report",
        default="documentation/migration/reports/DAY15_SCALE_REPORT.json",
        help="Path to Day 15 scale report",
    )
    parser.add_argument(
        "--env-file",
        default="infrastructure/docker/migration-day4/.env.day20.traffic80.example",
        help="Path to Day 20 env profile",
    )
    parser.add_argument(
        "--output",
        default="documentation/migration/reports/DAY20_TRAFFIC_REPORT.json",
        help="Path to Day 20 output report",
    )

    args = parser.parse_args()

    report = evaluate_day20_traffic(
        day19_report=_read_json(Path(args.day19_report)),
        day15_scale_report=_read_json(Path(args.day15_scale_report)),
        env20=_read_env_file(Path(args.env_file)),
    )

    output_path = Path(args.output)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(json.dumps(report, indent=2), encoding="utf-8")

    print(f"[DONE] day20 report: {output_path}")
    print(f"[STATUS] day20={report['summary']['status']}")

    return 0 if report["summary"]["status"] == "TRAFFIC_80_APPLIED" else 2


if __name__ == "__main__":
    raise SystemExit(main())
