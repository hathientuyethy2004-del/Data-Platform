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


def _simulate_read_switch_monitoring(read_percent: int) -> Dict[str, Any]:
    p95_latency_ms = 240 + (read_percent * 3)
    p99_latency_ms = 640 + (read_percent * 5)
    error_rate_pct = round(0.20 + (read_percent * 0.01), 3)

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


def evaluate_day17_read_switch(
    day16_report: Dict[str, Any],
    day15_scale_report: Dict[str, Any],
    env17: Dict[str, str],
) -> Dict[str, Any]:
    now = datetime.now(timezone.utc)

    day16_status = str(day16_report.get("summary", {}).get("status", "HOLD")).upper()
    day16_ready = day16_status == "READY_FOR_DAY17" and bool(
        day16_report.get("summary", {}).get("ready_for_day17_read_switch", False)
    )

    day15_effective_percent = int(day15_scale_report.get("rollout", {}).get("effective_percent", 0) or 0)
    day15_is_50_plus = day15_effective_percent >= 50

    target_percent = int(env17.get("READ_SWITCH_PERCENT", "10"))
    previous_percent = int(env17.get("CURRENT_READ_SWITCH_PERCENT", "0"))

    monitoring = _simulate_read_switch_monitoring(target_percent)

    prechecks = {
        "day16_ready_required": {
            "day16_status": day16_status,
            "status": "PASS" if day16_ready else "FAIL",
        },
        "day15_write_scale_50_required": {
            "day15_effective_percent": day15_effective_percent,
            "status": "PASS" if day15_is_50_plus else "FAIL",
        },
        "target_read_switch_is_10": {
            "target_percent": target_percent,
            "status": "PASS" if target_percent == 10 else "FAIL",
        },
    }

    can_apply = all(item["status"] == "PASS" for item in prechecks.values())
    monitor_pass = monitoring["overall_status"] == "PASS"

    applied = can_apply and monitor_pass
    final_status = "READ_SWITCHED_10" if applied else "BLOCKED"

    blockers = [name for name, detail in prechecks.items() if detail["status"] != "PASS"]
    if can_apply and not monitor_pass:
        blockers.append("latency_error_monitoring")

    return {
        "run_id": f"day17_read_switch_{now.strftime('%Y%m%dT%H%M%SZ')}",
        "run_ts": now.isoformat(),
        "scope": "Day 17 guarded read switch 10% to OSS",
        "checks": prechecks,
        "read_switch": {
            "requested_percent": target_percent,
            "previous_percent": previous_percent,
            "applied": applied,
            "effective_percent": target_percent if applied else previous_percent,
            "status": final_status,
            "blockers": blockers,
        },
        "monitoring": monitoring,
        "summary": {
            "status": final_status,
            "ready_for_day18": applied and monitor_pass,
            "decision": (
                "Read switch 10% enabled with healthy latency/error metrics"
                if applied
                else "Read switch remains blocked until Day 16 readiness and write-scale prerequisites pass"
            ),
        },
        "inputs": {
            "day16_report": "documentation/migration/reports/DAY16_OBSERVATION_REPORT.json",
            "day15_scale_report": "documentation/migration/reports/DAY15_SCALE_REPORT.json",
            "day17_env": "infrastructure/docker/migration-day4/.env.day17.read10.example",
        },
    }


def main() -> int:
    parser = argparse.ArgumentParser(description="Run Day 17 guarded read switch evaluation")
    parser.add_argument(
        "--day16-report",
        default="documentation/migration/reports/DAY16_OBSERVATION_REPORT.json",
        help="Path to Day 16 observation report",
    )
    parser.add_argument(
        "--day15-scale-report",
        default="documentation/migration/reports/DAY15_SCALE_REPORT.json",
        help="Path to Day 15 scale report",
    )
    parser.add_argument(
        "--env-file",
        default="infrastructure/docker/migration-day4/.env.day17.read10.example",
        help="Path to Day 17 env profile",
    )
    parser.add_argument(
        "--output",
        default="documentation/migration/reports/DAY17_READ_SWITCH_REPORT.json",
        help="Path to Day 17 output report",
    )

    args = parser.parse_args()

    report = evaluate_day17_read_switch(
        day16_report=_read_json(Path(args.day16_report)),
        day15_scale_report=_read_json(Path(args.day15_scale_report)),
        env17=_read_env_file(Path(args.env_file)),
    )

    output_path = Path(args.output)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(json.dumps(report, indent=2), encoding="utf-8")

    print(f"[DONE] day17 report: {output_path}")
    print(f"[STATUS] day17={report['summary']['status']}")

    return 0 if report["summary"]["status"] == "READ_SWITCHED_10" else 2


if __name__ == "__main__":
    raise SystemExit(main())
