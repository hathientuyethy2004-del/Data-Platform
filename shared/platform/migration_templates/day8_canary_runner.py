from __future__ import annotations

import argparse
import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict


def _read_json(path: Path) -> Dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def _read_env_file(path: Path) -> Dict[str, str]:
    result: Dict[str, str] = {}
    for line in path.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, value = line.split("=", 1)
        result[key.strip()] = value.strip()
    return result


def _is_true(value: str | None, default: bool = False) -> bool:
    if value is None:
        return default
    return value.strip().lower() in {"1", "true", "yes", "on"}


def _pick_canary(record_key: str, percent: int) -> bool:
    digest = hashlib.sha1(record_key.encode("utf-8")).hexdigest()
    bucket = int(digest[:8], 16) % 100
    return bucket < percent


def _simulate_canary_distribution(percent: int, total: int = 1000) -> Dict[str, Any]:
    canary_count = 0
    for idx in range(total):
        key = f"evt-canary-{idx:05d}"
        if _pick_canary(key, percent):
            canary_count += 1
    actual_pct = round((canary_count / total) * 100, 2)
    return {
        "sample_size": total,
        "canary_records": canary_count,
        "legacy_records": total - canary_count,
        "actual_percent": actual_pct,
        "within_tolerance": abs(actual_pct - percent) <= 2.0,
    }


def build_day8_report(
    env: Dict[str, str],
    baseline_report: Dict[str, Any],
    smoke_report: Dict[str, Any],
    gate_report: Dict[str, Any],
) -> Dict[str, Any]:
    now = datetime.now(timezone.utc)

    target_percent = int(env.get("OSS_CANARY_WRITE_PERCENT", "10"))
    canary_mode = env.get("OSS_CANARY_MODE", "shadow_write")
    hash_key = env.get("OSS_CANARY_HASH_KEY", "event_id")

    read_from_oss = _is_true(env.get("READ_FROM_OSS_SERVING"), False)
    dual_run_enabled = _is_true(env.get("DUAL_RUN_ENABLED"), False)
    dual_compare = _is_true(env.get("DUAL_RUN_COMPARE_ENABLED"), True)

    simulation = _simulate_canary_distribution(target_percent)

    checks = {
        "canary_write_percent_is_10": {
            "expected": 10,
            "actual": target_percent,
            "status": "PASS" if target_percent == 10 else "FAIL",
        },
        "read_path_stays_legacy": {
            "read_from_oss_serving": read_from_oss,
            "status": "PASS" if not read_from_oss else "FAIL",
        },
        "dual_run_compare_enabled": {
            "dual_run_enabled": dual_run_enabled,
            "dual_run_compare_enabled": dual_compare,
            "status": "PASS" if dual_run_enabled and dual_compare else "FAIL",
        },
        "canary_distribution_sanity": {
            "target_percent": target_percent,
            "actual_percent": simulation["actual_percent"],
            "status": "PASS" if simulation["within_tolerance"] else "FAIL",
        },
    }

    all_pass = all(item["status"] == "PASS" for item in checks.values())

    return {
        "run_id": f"day8_canary_{now.strftime('%Y%m%dT%H%M%SZ')}",
        "run_ts": now.isoformat(),
        "scope": "Day 8 canary setup and initial monitoring snapshot",
        "config": {
            "oss_canary_write_percent": target_percent,
            "oss_canary_mode": canary_mode,
            "oss_canary_hash_key": hash_key,
            "read_from_oss_serving": read_from_oss,
            "dual_run_enabled": dual_run_enabled,
            "dual_run_compare_enabled": dual_compare,
        },
        "checks": checks,
        "canary_simulation": simulation,
        "monitoring_snapshot": {
            "smoke_overall_status": smoke_report.get("overall_status"),
            "baseline_overall_status": baseline_report.get("summary", {}).get("overall_status"),
            "baseline_critical_issues": baseline_report.get("summary", {}).get("critical_issues"),
            "gate1_status": gate_report.get("summary", {}).get("status"),
            "gate1_remaining_hours": gate_report.get("summary", {}).get("remaining_hours_to_gate"),
            "quality_status": "PASS"
            if baseline_report.get("summary", {}).get("critical_issues", 1) == 0
            else "FAIL",
            "slo_status": "MONITORING",
        },
        "summary": {
            "status": "PASS" if all_pass else "FAIL",
            "day8_canary_ready": all_pass,
            "next_step": "Continue Day 9 live SLO/quality tracking over sustained window.",
        },
    }


def main() -> int:
    parser = argparse.ArgumentParser(description="Run Day 8 canary setup checks and monitoring snapshot")
    parser.add_argument(
        "--env-file",
        default="infrastructure/docker/migration-day4/.env.day8.canary10.example",
        help="Path to day8 env profile",
    )
    parser.add_argument(
        "--smoke-report",
        default="documentation/migration/reports/DAY5_SMOKE_RESULT.json",
        help="Path to smoke report",
    )
    parser.add_argument(
        "--baseline-report",
        default="documentation/migration/reports/BASELINE_COMPARE_REPORT_DAY5.json",
        help="Path to baseline compare report",
    )
    parser.add_argument(
        "--gate-report",
        default="documentation/migration/reports/DAY7_GATE1_REPORT.json",
        help="Path to latest day7 gate report",
    )
    parser.add_argument(
        "--output",
        default="documentation/migration/reports/DAY8_CANARY_STATUS.json",
        help="Path to day8 output report",
    )

    args = parser.parse_args()

    env = _read_env_file(Path(args.env_file))
    smoke_report = _read_json(Path(args.smoke_report))
    baseline_report = _read_json(Path(args.baseline_report))
    gate_report = _read_json(Path(args.gate_report))

    report = build_day8_report(
        env=env,
        baseline_report=baseline_report,
        smoke_report=smoke_report,
        gate_report=gate_report,
    )

    output_path = Path(args.output)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(json.dumps(report, indent=2), encoding="utf-8")

    print(f"[DONE] day8 report: {output_path}")
    print(f"[STATUS] day8={report['summary']['status']}")

    return 0 if report["summary"]["status"] == "PASS" else 2


if __name__ == "__main__":
    raise SystemExit(main())
