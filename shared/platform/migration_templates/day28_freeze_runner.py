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


def evaluate_day28_freeze(day27_report: Dict[str, Any], env28: Dict[str, str]) -> Dict[str, Any]:
    now = datetime.now(timezone.utc)

    day27_status = str(day27_report.get("summary", {}).get("status", "BLOCKED")).upper()
    day27_ready = day27_status == "VALIDATED_FOR_FREEZE" and bool(day27_report.get("validation", {}).get("applied", False))

    freeze_enabled = _is_true(env28.get("FREEZE_WINDOW_ENABLED", "false"))
    observed_hours = float(env28.get("FREEZE_OBSERVED_HOURS", "0") or 0)
    critical_changes_detected = _is_true(env28.get("CRITICAL_CHANGES_DETECTED", "false"))
    slo_stable = _is_true(env28.get("SLO_STABLE_24H", "false"))
    no_sev_incidents = _is_true(env28.get("NO_SEV1_SEV2_24H", "false"))
    post_cutover_report_ready = _is_true(env28.get("POST_CUTOVER_REPORT_READY", "false"))

    checks = {
        "day27_validated_required": {
            "day27_status": day27_status,
            "status": "PASS" if day27_ready else "FAIL",
        },
        "freeze_window_enabled": {
            "enabled": freeze_enabled,
            "status": "PASS" if freeze_enabled else "FAIL",
        },
        "freeze_observed_24h": {
            "observed_hours": observed_hours,
            "required_hours": 24,
            "status": "PASS" if observed_hours >= 24 else "FAIL",
        },
        "no_critical_changes": {
            "critical_changes_detected": critical_changes_detected,
            "status": "PASS" if not critical_changes_detected else "FAIL",
        },
        "slo_stable_24h": {
            "status": "PASS" if slo_stable else "FAIL",
        },
        "no_sev1_sev2_24h": {
            "status": "PASS" if no_sev_incidents else "FAIL",
        },
        "post_cutover_report_ready": {
            "status": "PASS" if post_cutover_report_ready else "FAIL",
        },
    }

    freeze_pass = all(item["status"] == "PASS" for item in checks.values())
    final_status = "FREEZE_LOCKED_REPORT_FINALIZED" if freeze_pass else "BLOCKED"

    blockers = [name for name, detail in checks.items() if detail["status"] != "PASS"]

    return {
        "run_id": f"day28_freeze_{now.strftime('%Y%m%dT%H%M%SZ')}",
        "run_ts": now.isoformat(),
        "scope": "Day 28 guarded freeze: 24h freeze observation + post-cutover report closure",
        "checks": checks,
        "freeze": {
            "applied": freeze_pass,
            "status": final_status,
            "blockers": blockers,
        },
        "summary": {
            "status": final_status,
            "ready_for_day29": freeze_pass,
            "decision": (
                "Day 28 freeze locked and post-cutover report finalized; ready for Day 29 decommission"
                if freeze_pass
                else "Day 28 freeze blocked; keep freeze and resolve stability/report gaps"
            ),
        },
        "inputs": {
            "day27_report": "documentation/migration/reports/DAY27_VALIDATION_REPORT.json",
            "day28_env": "infrastructure/docker/migration-day4/.env.day28.freeze.example",
        },
    }


def main() -> int:
    parser = argparse.ArgumentParser(description="Run Day 28 guarded freeze evaluation")
    parser.add_argument(
        "--day27-report",
        default="documentation/migration/reports/DAY27_VALIDATION_REPORT.json",
        help="Path to Day 27 validation report",
    )
    parser.add_argument(
        "--env-file",
        default="infrastructure/docker/migration-day4/.env.day28.freeze.example",
        help="Path to Day 28 env profile",
    )
    parser.add_argument(
        "--output",
        default="documentation/migration/reports/DAY28_FREEZE_REPORT.json",
        help="Path to Day 28 output report",
    )

    args = parser.parse_args()

    report = evaluate_day28_freeze(
        day27_report=_read_json(Path(args.day27_report)),
        env28=_read_env_file(Path(args.env_file)),
    )

    output_path = Path(args.output)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(json.dumps(report, indent=2), encoding="utf-8")

    print(f"[DONE] day28 report: {output_path}")
    print(f"[STATUS] day28={report['summary']['status']}")

    return 0 if report["summary"]["status"] == "FREEZE_LOCKED_REPORT_FINALIZED" else 2


if __name__ == "__main__":
    raise SystemExit(main())
