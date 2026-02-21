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


def evaluate_day29_decommission(day28_report: Dict[str, Any], env29: Dict[str, str]) -> Dict[str, Any]:
    now = datetime.now(timezone.utc)

    day28_status = str(day28_report.get("summary", {}).get("status", "BLOCKED")).upper()
    day28_ready = day28_status == "FREEZE_LOCKED_REPORT_FINALIZED" and bool(
        day28_report.get("freeze", {}).get("applied", False)
    )

    legacy_cron_removed = _is_true(env29.get("LEGACY_CRON_REMOVED", "false"))
    legacy_jobs_disabled = _is_true(env29.get("LEGACY_JOBS_DISABLED", "false"))
    legacy_routes_disabled = _is_true(env29.get("LEGACY_ROUTES_DISABLED", "false"))
    legacy_configs_archived = _is_true(env29.get("LEGACY_CONFIGS_ARCHIVED", "false"))
    backup_config_done = _is_true(env29.get("BACKUP_CONFIG_DONE", "false"))
    runbook_finalized = _is_true(env29.get("RUNBOOK_FINALIZED", "false"))
    rollback_snapshot_created = _is_true(env29.get("ROLLBACK_SNAPSHOT_CREATED", "false"))
    decommission_dry_run_pass = _is_true(env29.get("DECOMMISSION_DRY_RUN_PASS", "false"))

    checks = {
        "day28_freeze_required": {
            "day28_status": day28_status,
            "status": "PASS" if day28_ready else "FAIL",
        },
        "legacy_cron_removed": {
            "status": "PASS" if legacy_cron_removed else "FAIL",
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
        "backup_config_done": {
            "status": "PASS" if backup_config_done else "FAIL",
        },
        "runbook_finalized": {
            "status": "PASS" if runbook_finalized else "FAIL",
        },
        "rollback_snapshot_created": {
            "status": "PASS" if rollback_snapshot_created else "FAIL",
        },
        "decommission_dry_run_pass": {
            "status": "PASS" if decommission_dry_run_pass else "FAIL",
        },
    }

    decommission_pass = all(item["status"] == "PASS" for item in checks.values())
    final_status = "DECOMMISSIONED_WITH_BACKUP" if decommission_pass else "BLOCKED"

    blockers = [name for name, detail in checks.items() if detail["status"] != "PASS"]

    return {
        "run_id": f"day29_decommission_{now.strftime('%Y%m%dT%H%M%SZ')}",
        "run_ts": now.isoformat(),
        "scope": "Day 29 guarded decommission: remove legacy runtime + finalize backup/runbook/rollback snapshot",
        "checks": checks,
        "decommission": {
            "applied": decommission_pass,
            "status": final_status,
            "blockers": blockers,
        },
        "summary": {
            "status": final_status,
            "ready_for_day30": decommission_pass,
            "decision": (
                "Day 29 decommission completed with backup and rollback snapshot; ready for Day 30 closure"
                if decommission_pass
                else "Day 29 decommission blocked; keep legacy fallback controls until all checks pass"
            ),
        },
        "inputs": {
            "day28_report": "documentation/migration/reports/DAY28_FREEZE_REPORT.json",
            "day29_env": "infrastructure/docker/migration-day4/.env.day29.decommission.example",
        },
    }


def main() -> int:
    parser = argparse.ArgumentParser(description="Run Day 29 guarded decommission evaluation")
    parser.add_argument(
        "--day28-report",
        default="documentation/migration/reports/DAY28_FREEZE_REPORT.json",
        help="Path to Day 28 freeze report",
    )
    parser.add_argument(
        "--env-file",
        default="infrastructure/docker/migration-day4/.env.day29.decommission.example",
        help="Path to Day 29 env profile",
    )
    parser.add_argument(
        "--output",
        default="documentation/migration/reports/DAY29_DECOMMISSION_REPORT.json",
        help="Path to Day 29 output report",
    )

    args = parser.parse_args()

    report = evaluate_day29_decommission(
        day28_report=_read_json(Path(args.day28_report)),
        env29=_read_env_file(Path(args.env_file)),
    )

    output_path = Path(args.output)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(json.dumps(report, indent=2), encoding="utf-8")

    print(f"[DONE] day29 report: {output_path}")
    print(f"[STATUS] day29={report['summary']['status']}")

    return 0 if report["summary"]["status"] == "DECOMMISSIONED_WITH_BACKUP" else 2


if __name__ == "__main__":
    raise SystemExit(main())
