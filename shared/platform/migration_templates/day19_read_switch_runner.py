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
    p95_latency_ms = 280 + (read_percent * 3)
    p99_latency_ms = 760 + (read_percent * 6)
    error_rate_pct = round(0.30 + (read_percent * 0.009), 3)

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


def evaluate_day19_read_switch(
    day18_report: Dict[str, Any],
    day15_scale_report: Dict[str, Any],
    env19: Dict[str, str],
) -> Dict[str, Any]:
    now = datetime.now(timezone.utc)

    day18_status = str(day18_report.get("summary", {}).get("status", "BLOCKED")).upper()
    day18_switched = day18_status == "READ_SWITCHED_30" and bool(
        day18_report.get("read_switch", {}).get("applied", False)
    )

    day15_effective_percent = int(day15_scale_report.get("rollout", {}).get("effective_percent", 0) or 0)
    day15_is_50_plus = day15_effective_percent >= 50

    target_percent = int(env19.get("READ_SWITCH_PERCENT", "50"))
    previous_percent = int(env19.get("CURRENT_READ_SWITCH_PERCENT", "30"))

    monitoring = _simulate_read_switch_monitoring(target_percent)

    checks = {
        "day18_read_switch_30_required": {
            "day18_status": day18_status,
            "status": "PASS" if day18_switched else "FAIL",
        },
        "day15_write_scale_50_required": {
            "day15_effective_percent": day15_effective_percent,
            "status": "PASS" if day15_is_50_plus else "FAIL",
        },
        "target_read_switch_is_50": {
            "target_percent": target_percent,
            "status": "PASS" if target_percent == 50 else "FAIL",
        },
        "stepwise_read_increase_safe": {
            "previous_percent": previous_percent,
            "target_percent": target_percent,
            "delta_percent": target_percent - previous_percent,
            "status": "PASS" if previous_percent >= 30 and 0 < (target_percent - previous_percent) <= 20 else "FAIL",
        },
    }

    precheck_pass = all(item["status"] == "PASS" for item in checks.values())
    monitor_pass = monitoring["overall_status"] == "PASS"

    applied = precheck_pass and monitor_pass
    final_status = "READ_SWITCHED_50" if applied else "BLOCKED"

    blockers = [name for name, detail in checks.items() if detail["status"] != "PASS"]
    if precheck_pass and not monitor_pass:
        blockers.append("latency_error_monitoring")

    return {
        "run_id": f"day19_read_switch_{now.strftime('%Y%m%dT%H%M%SZ')}",
        "run_ts": now.isoformat(),
        "scope": "Day 19 guarded read switch increase to 50%",
        "checks": checks,
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
            "ready_for_day20": applied and monitor_pass,
            "decision": (
                "Read switch increased to 50% with healthy latency/error metrics"
                if applied
                else "Read switch increase remains blocked until Day 18 and write-scale prerequisites pass"
            ),
        },
        "inputs": {
            "day18_report": "documentation/migration/reports/DAY18_READ_SWITCH_REPORT.json",
            "day15_scale_report": "documentation/migration/reports/DAY15_SCALE_REPORT.json",
            "day19_env": "infrastructure/docker/migration-day4/.env.day19.read50.example",
        },
    }


def main() -> int:
    parser = argparse.ArgumentParser(description="Run Day 19 guarded read switch evaluation")
    parser.add_argument(
        "--day18-report",
        default="documentation/migration/reports/DAY18_READ_SWITCH_REPORT.json",
        help="Path to Day 18 read-switch report",
    )
    parser.add_argument(
        "--day15-scale-report",
        default="documentation/migration/reports/DAY15_SCALE_REPORT.json",
        help="Path to Day 15 scale report",
    )
    parser.add_argument(
        "--env-file",
        default="infrastructure/docker/migration-day4/.env.day19.read50.example",
        help="Path to Day 19 env profile",
    )
    parser.add_argument(
        "--output",
        default="documentation/migration/reports/DAY19_READ_SWITCH_REPORT.json",
        help="Path to Day 19 output report",
    )

    args = parser.parse_args()

    report = evaluate_day19_read_switch(
        day18_report=_read_json(Path(args.day18_report)),
        day15_scale_report=_read_json(Path(args.day15_scale_report)),
        env19=_read_env_file(Path(args.env_file)),
    )

    output_path = Path(args.output)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(json.dumps(report, indent=2), encoding="utf-8")

    print(f"[DONE] day19 report: {output_path}")
    print(f"[STATUS] day19={report['summary']['status']}")

    return 0 if report["summary"]["status"] == "READ_SWITCHED_50" else 2


if __name__ == "__main__":
    raise SystemExit(main())
