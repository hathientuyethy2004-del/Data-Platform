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


def evaluate_day30_closure(day29_report: Dict[str, Any], env30: Dict[str, str]) -> Dict[str, Any]:
    now = datetime.now(timezone.utc)

    day29_status = str(day29_report.get("summary", {}).get("status", "BLOCKED")).upper()
    day29_ready = day29_status == "DECOMMISSIONED_WITH_BACKUP" and bool(
        day29_report.get("decommission", {}).get("applied", False)
    )

    technical_acceptance_signed = _is_true(env30.get("TECHNICAL_ACCEPTANCE_SIGNED", "false"))
    lessons_learned_published = _is_true(env30.get("LESSONS_LEARNED_PUBLISHED", "false"))
    optimization_phase_kickoff = _is_true(env30.get("OPTIMIZATION_PHASE_KICKOFF", "false"))

    checks = {
        "day29_decommission_required": {
            "day29_status": day29_status,
            "status": "PASS" if day29_ready else "FAIL",
        },
        "technical_acceptance_signed": {
            "status": "PASS" if technical_acceptance_signed else "FAIL",
        },
        "lessons_learned_published": {
            "status": "PASS" if lessons_learned_published else "FAIL",
        },
        "optimization_phase_kickoff": {
            "status": "PASS" if optimization_phase_kickoff else "FAIL",
        },
    }

    closure_pass = all(item["status"] == "PASS" for item in checks.values())
    final_status = "GO_LIVE_CLOSED" if closure_pass else "BLOCKED"
    blockers = [name for name, detail in checks.items() if detail["status"] != "PASS"]

    return {
        "run_id": f"day30_closure_{now.strftime('%Y%m%dT%H%M%SZ')}",
        "run_ts": now.isoformat(),
        "scope": "Day 30 guarded closure: technical sign-off + lessons learned + optimization phase kickoff",
        "checks": checks,
        "closure": {
            "applied": closure_pass,
            "status": final_status,
            "blockers": blockers,
        },
        "summary": {
            "status": final_status,
            "migration_closed": closure_pass,
            "decision": (
                "Day 30 closure completed; migration accepted and moved to optimization phase"
                if closure_pass
                else "Day 30 closure blocked; complete pending closure items before formal sign-off"
            ),
        },
        "inputs": {
            "day29_report": "documentation/migration/reports/DAY29_DECOMMISSION_REPORT.json",
            "day30_env": "infrastructure/docker/migration-day4/.env.day30.closure.example",
        },
    }


def main() -> int:
    parser = argparse.ArgumentParser(description="Run Day 30 guarded closure evaluation")
    parser.add_argument(
        "--day29-report",
        default="documentation/migration/reports/DAY29_DECOMMISSION_REPORT.json",
        help="Path to Day 29 decommission report",
    )
    parser.add_argument(
        "--env-file",
        default="infrastructure/docker/migration-day4/.env.day30.closure.example",
        help="Path to Day 30 env profile",
    )
    parser.add_argument(
        "--output",
        default="documentation/migration/reports/DAY30_CLOSURE_REPORT.json",
        help="Path to Day 30 output report",
    )

    args = parser.parse_args()

    report = evaluate_day30_closure(
        day29_report=_read_json(Path(args.day29_report)),
        env30=_read_env_file(Path(args.env_file)),
    )

    output_path = Path(args.output)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(json.dumps(report, indent=2), encoding="utf-8")

    print(f"[DONE] day30 report: {output_path}")
    print(f"[STATUS] day30={report['summary']['status']}")

    return 0 if report["summary"]["status"] == "GO_LIVE_CLOSED" else 2


if __name__ == "__main__":
    raise SystemExit(main())
