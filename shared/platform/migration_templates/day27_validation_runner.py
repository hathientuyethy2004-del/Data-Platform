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


def evaluate_day27_validation(day25_26_report: Dict[str, Any], env27: Dict[str, str]) -> Dict[str, Any]:
    now = datetime.now(timezone.utc)

    day25_26_status = str(day25_26_report.get("summary", {}).get("status", "BLOCKED")).upper()
    day25_26_ready = day25_26_status == "READ_PATH_100_LEGACY_DRAINING" and bool(
        day25_26_report.get("read_cutover", {}).get("applied", False)
    )

    regression_pass = _is_true(env27.get("REGRESSION_SUITE_PASS", "false"))
    performance_pass = _is_true(env27.get("PERFORMANCE_SUITE_PASS", "false"))
    slo_dashboard_ok = _is_true(env27.get("SLO_DASHBOARD_PASS", "false"))
    alerts_ok = _is_true(env27.get("ALERTS_PASS", "false"))
    audit_logs_ok = _is_true(env27.get("AUDIT_LOGS_PASS", "false"))

    performance_p95_ms = float(env27.get("PERF_P95_MS", "0") or 0)
    performance_p99_ms = float(env27.get("PERF_P99_MS", "0") or 0)
    performance_error_rate_pct = float(env27.get("PERF_ERROR_RATE_PCT", "0") or 0)

    checks = {
        "day25_26_read_cutover_required": {
            "day25_26_status": day25_26_status,
            "status": "PASS" if day25_26_ready else "FAIL",
        },
        "full_regression_suite_passed": {
            "status": "PASS" if regression_pass else "FAIL",
        },
        "performance_suite_passed": {
            "status": "PASS" if performance_pass else "FAIL",
        },
        "performance_guardrails": {
            "p95_ms": performance_p95_ms,
            "p99_ms": performance_p99_ms,
            "error_rate_pct": performance_error_rate_pct,
            "status": "PASS"
            if performance_p95_ms <= 500 and performance_p99_ms <= 1200 and performance_error_rate_pct < 1.0
            else "FAIL",
        },
        "slo_dashboard_passed": {
            "status": "PASS" if slo_dashboard_ok else "FAIL",
        },
        "alerts_verified": {
            "status": "PASS" if alerts_ok else "FAIL",
        },
        "audit_logs_verified": {
            "status": "PASS" if audit_logs_ok else "FAIL",
        },
    }

    validation_pass = all(item["status"] == "PASS" for item in checks.values())
    final_status = "VALIDATED_FOR_FREEZE" if validation_pass else "BLOCKED"

    blockers = [name for name, detail in checks.items() if detail["status"] != "PASS"]

    return {
        "run_id": f"day27_validation_{now.strftime('%Y%m%dT%H%M%SZ')}",
        "run_ts": now.isoformat(),
        "scope": "Day 27 guarded validation: regression + performance + SLO/audit checks",
        "checks": checks,
        "validation": {
            "applied": validation_pass,
            "status": final_status,
            "blockers": blockers,
        },
        "summary": {
            "status": final_status,
            "ready_for_day28": validation_pass,
            "decision": (
                "Day 27 validations passed; ready for Day 28 freeze window"
                if validation_pass
                else "Day 27 validations blocked; resolve regression/performance/SLO-audit gaps first"
            ),
        },
        "inputs": {
            "day25_26_report": "documentation/migration/reports/DAY25_26_READ_CUTOVER_REPORT.json",
            "day27_env": "infrastructure/docker/migration-day4/.env.day27.validation.example",
        },
    }


def main() -> int:
    parser = argparse.ArgumentParser(description="Run Day 27 guarded validation")
    parser.add_argument(
        "--day25-26-report",
        default="documentation/migration/reports/DAY25_26_READ_CUTOVER_REPORT.json",
        help="Path to Day 25-26 read-cutover report",
    )
    parser.add_argument(
        "--env-file",
        default="infrastructure/docker/migration-day4/.env.day27.validation.example",
        help="Path to Day 27 env profile",
    )
    parser.add_argument(
        "--output",
        default="documentation/migration/reports/DAY27_VALIDATION_REPORT.json",
        help="Path to Day 27 output report",
    )

    args = parser.parse_args()

    report = evaluate_day27_validation(
        day25_26_report=_read_json(Path(args.day25_26_report)),
        env27=_read_env_file(Path(args.env_file)),
    )

    output_path = Path(args.output)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(json.dumps(report, indent=2), encoding="utf-8")

    print(f"[DONE] day27 report: {output_path}")
    print(f"[STATUS] day27={report['summary']['status']}")

    return 0 if report["summary"]["status"] == "VALIDATED_FOR_FREEZE" else 2


if __name__ == "__main__":
    raise SystemExit(main())
