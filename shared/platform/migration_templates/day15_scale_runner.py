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
    return str(value).strip().lower() in {"1", "true", "yes", "on"}


def evaluate_day15_scale(
    day14_report: Dict[str, Any],
    day10_report: Dict[str, Any],
    env15: Dict[str, str],
) -> Dict[str, Any]:
    now = datetime.now(timezone.utc)

    gate2_status = str(day14_report.get("summary", {}).get("status", "NO_GO")).upper()
    gate2_approved = bool(day14_report.get("summary", {}).get("approve_scale_week3", False))

    current_percent = int(day10_report.get("rollout", {}).get("effective_percent", 20) or 20)
    target_percent = int(env15.get("OSS_CANARY_WRITE_PERCENT", "50"))

    dual_run_compare_hourly = _is_true(env15.get("DUAL_RUN_COMPARE_HOURLY", "true"))
    read_from_oss_serving = _is_true(env15.get("READ_FROM_OSS_SERVING", "false"))

    step_delta = target_percent - current_percent

    checks = {
        "gate2_pass_required": {
            "day14_status": gate2_status,
            "approve_scale_week3": gate2_approved,
            "status": "PASS" if gate2_status == "PASS" and gate2_approved else "FAIL",
        },
        "target_percent_is_50": {
            "target_percent": target_percent,
            "status": "PASS" if target_percent == 50 else "FAIL",
        },
        "stepwise_increase_safe": {
            "previous_percent": current_percent,
            "target_percent": target_percent,
            "delta_percent": step_delta,
            "status": "PASS" if current_percent >= 20 and step_delta > 0 and step_delta <= 30 else "FAIL",
        },
        "dual_run_compare_hourly_enabled": {
            "configured": dual_run_compare_hourly,
            "status": "PASS" if dual_run_compare_hourly else "FAIL",
        },
        "read_path_remains_legacy": {
            "read_from_oss_serving": read_from_oss_serving,
            "status": "PASS" if not read_from_oss_serving else "FAIL",
        },
    }

    rollout_gate_pass = all(check["status"] == "PASS" for check in checks.values())

    final_status = "SCALED_TO_50" if rollout_gate_pass else "BLOCKED"
    applied = final_status == "SCALED_TO_50"

    blockers = [name for name, detail in checks.items() if detail["status"] != "PASS"]

    return {
        "run_id": f"day15_scale_{now.strftime('%Y%m%dT%H%M%SZ')}",
        "run_ts": now.isoformat(),
        "scope": "Day 15 guarded scale-up to 50% after Gate 2 PASS",
        "checks": checks,
        "rollout": {
            "requested_percent": target_percent,
            "previous_percent": current_percent,
            "applied": applied,
            "effective_percent": target_percent if applied else current_percent,
            "status": final_status,
            "blockers": blockers,
        },
        "summary": {
            "status": final_status,
            "ready_for_day16_observation": applied,
            "decision": (
                "Scaled to 50% and continue hourly dual-run compare"
                if applied
                else "Scale-up blocked until Gate 2 and config checks pass"
            ),
        },
        "inputs": {
            "day14_gate2_report": "documentation/migration/reports/DAY14_GATE2_REPORT.json",
            "day10_rollout_report": "documentation/migration/reports/DAY10_ROLLOUT_REPORT.json",
            "day15_env": "infrastructure/docker/migration-day4/.env.day15.scale50.example",
        },
    }


def main() -> int:
    parser = argparse.ArgumentParser(description="Run Day 15 guarded scale-up evaluation")
    parser.add_argument(
        "--day14-report",
        default="documentation/migration/reports/DAY14_GATE2_REPORT.json",
        help="Path to Day 14 Gate 2 report",
    )
    parser.add_argument(
        "--day10-report",
        default="documentation/migration/reports/DAY10_ROLLOUT_REPORT.json",
        help="Path to Day 10 rollout report (current percent baseline)",
    )
    parser.add_argument(
        "--env-file",
        default="infrastructure/docker/migration-day4/.env.day15.scale50.example",
        help="Path to Day 15 env profile",
    )
    parser.add_argument(
        "--output",
        default="documentation/migration/reports/DAY15_SCALE_REPORT.json",
        help="Path to Day 15 output report",
    )

    args = parser.parse_args()

    day14_report = _read_json(Path(args.day14_report))
    day10_report = _read_json(Path(args.day10_report))
    env15 = _read_env_file(Path(args.env_file))

    report = evaluate_day15_scale(
        day14_report=day14_report,
        day10_report=day10_report,
        env15=env15,
    )

    output_path = Path(args.output)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(json.dumps(report, indent=2), encoding="utf-8")

    print(f"[DONE] day15 report: {output_path}")
    print(f"[STATUS] day15={report['summary']['status']}")

    return 0 if report["summary"]["status"] == "SCALED_TO_50" else 2


if __name__ == "__main__":
    raise SystemExit(main())
