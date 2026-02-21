from __future__ import annotations

import argparse
import json
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any, Dict, List


def _read_json(path: Path) -> Dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def _read_incidents(path: Path) -> List[Dict[str, Any]]:
    if not path.exists():
        return []
    payload = json.loads(path.read_text(encoding="utf-8"))
    items = payload.get("incidents")
    if isinstance(items, list):
        return items
    return []


def _parse_iso(ts: str) -> datetime:
    raw = ts.strip()
    if raw.endswith("Z"):
        raw = raw[:-1] + "+00:00"
    parsed = datetime.fromisoformat(raw)
    if parsed.tzinfo is None:
        parsed = parsed.replace(tzinfo=timezone.utc)
    return parsed.astimezone(timezone.utc)


def evaluate_gate2(
    day10_report: Dict[str, Any],
    day13_report: Dict[str, Any],
    incidents: List[Dict[str, Any]],
    min_stability_hours: int = 48,
) -> Dict[str, Any]:
    now = datetime.now(timezone.utc)

    rollout = day10_report.get("rollout", {})
    rollout_applied = bool(rollout.get("applied", False))
    effective_percent = int(rollout.get("effective_percent", 0) or 0)
    rollout_ts = _parse_iso(str(day10_report.get("run_ts", now.isoformat())))

    stable_hours = round((now - rollout_ts).total_seconds() / 3600, 2)
    remaining_hours = round(max(0.0, float(min_stability_hours) - stable_hours), 2)
    estimated_gate2_at = (rollout_ts + timedelta(hours=min_stability_hours)).isoformat()

    lookback_start = now - timedelta(hours=min_stability_hours)
    sev12_events = []
    for item in incidents:
        severity = str(item.get("severity", "")).upper()
        if severity not in {"SEV-1", "SEV-2", "SEV1", "SEV2"}:
            continue
        ts_raw = item.get("ts")
        if not ts_raw:
            sev12_events.append(item)
            continue
        try:
            event_ts = _parse_iso(str(ts_raw))
        except ValueError:
            sev12_events.append(item)
            continue
        if event_ts >= lookback_start:
            sev12_events.append(item)

    chaos_summary = day13_report.get("summary", {})
    chaos_pass = (
        str(chaos_summary.get("status", "")).upper() == "PASS"
        and bool(chaos_summary.get("integrity_passed", False))
    )

    checks = {
        "canary_20_stable_48h": {
            "rollout_applied": rollout_applied,
            "effective_percent": effective_percent,
            "required_hours": min_stability_hours,
            "observed_hours": stable_hours,
            "remaining_hours": remaining_hours,
            "estimated_gate2_at_utc": estimated_gate2_at,
            "status": "PASS"
            if rollout_applied and effective_percent >= 20 and stable_hours >= min_stability_hours
            else "FAIL",
        },
        "no_sev1_sev2": {
            "lookback_hours": min_stability_hours,
            "sev1_sev2_count": len(sev12_events),
            "status": "PASS" if len(sev12_events) == 0 else "FAIL",
        },
        "chaos_integrity_passed": {
            "day13_status": chaos_summary.get("status"),
            "integrity_passed": chaos_summary.get("integrity_passed"),
            "status": "PASS" if chaos_pass else "FAIL",
        },
    }

    gate_pass = all(item["status"] == "PASS" for item in checks.values())
    blockers = [name for name, item in checks.items() if item["status"] == "FAIL"]

    return {
        "run_id": f"day14_gate2_{now.strftime('%Y%m%dT%H%M%SZ')}",
        "run_ts": now.isoformat(),
        "gate": "WEEK2_GATE2",
        "scope": "Day 14 Gate 2 evaluation for Week 3 scale readiness",
        "checks": checks,
        "summary": {
            "status": "PASS" if gate_pass else "NO_GO",
            "approve_scale_week3": gate_pass,
            "blockers": blockers,
            "decision": (
                "Gate 2 passed, approved to scale into Week 3"
                if gate_pass
                else "Gate 2 not met; continue stabilization at 20%"
            ),
        },
        "inputs": {
            "day10_rollout_report": "documentation/migration/reports/DAY10_ROLLOUT_REPORT.json",
            "day13_chaos_report": "documentation/migration/reports/DAY13_CHAOS_REPORT.json",
            "incident_log": "documentation/migration/reports/DAY14_INCIDENT_LOG.json",
        },
        "next_actions": [
            "If NO_GO: keep 20% canary and continue stability observation until 48h requirement is met.",
            "If PASS: proceed to Week 3 Day 15-16 scale plan.",
        ],
    }


def main() -> int:
    parser = argparse.ArgumentParser(description="Run Day 14 Gate 2 evaluation")
    parser.add_argument(
        "--day10-report",
        default="documentation/migration/reports/DAY10_ROLLOUT_REPORT.json",
        help="Path to Day 10 rollout report",
    )
    parser.add_argument(
        "--day13-report",
        default="documentation/migration/reports/DAY13_CHAOS_REPORT.json",
        help="Path to Day 13 chaos report",
    )
    parser.add_argument(
        "--incident-log",
        default="documentation/migration/reports/DAY14_INCIDENT_LOG.json",
        help="Path to Day 14 incident log",
    )
    parser.add_argument(
        "--output",
        default="documentation/migration/reports/DAY14_GATE2_REPORT.json",
        help="Path to Day 14 Gate 2 output report",
    )
    parser.add_argument(
        "--min-stability-hours",
        default=48,
        type=int,
        help="Required stability window in hours",
    )

    args = parser.parse_args()

    day10_report = _read_json(Path(args.day10_report))
    day13_report = _read_json(Path(args.day13_report))
    incidents = _read_incidents(Path(args.incident_log))

    report = evaluate_gate2(
        day10_report=day10_report,
        day13_report=day13_report,
        incidents=incidents,
        min_stability_hours=args.min_stability_hours,
    )

    output_path = Path(args.output)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(json.dumps(report, indent=2), encoding="utf-8")

    print(f"[DONE] day14 report: {output_path}")
    print(f"[STATUS] gate2={report['summary']['status']}")

    return 0 if report["summary"]["status"] == "PASS" else 2


if __name__ == "__main__":
    raise SystemExit(main())
