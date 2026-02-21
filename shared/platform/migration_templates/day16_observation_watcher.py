from __future__ import annotations

import argparse
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict


def _read_json(path: Path) -> Dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def _read_json_or_default(path: Path, default: Dict[str, Any]) -> Dict[str, Any]:
    if not path.exists():
        return dict(default)
    return json.loads(path.read_text(encoding="utf-8"))


def _append_jsonl(path: Path, payload: Dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a", encoding="utf-8") as fp:
        fp.write(json.dumps(payload, ensure_ascii=False) + "\n")


def sync_day16_transition(
    day16_report_path: Path,
    day16_report: Dict[str, Any],
    state_path: Path,
    transition_log_path: Path,
) -> Dict[str, Any]:
    now = datetime.now(timezone.utc)
    current_status = str(day16_report.get("summary", {}).get("status", "UNKNOWN")).upper()
    run_id = str(day16_report.get("run_id", ""))
    run_ts = str(day16_report.get("run_ts", now.isoformat()))

    prev_state = _read_json_or_default(
        state_path,
        {
            "last_day16_status": "UNKNOWN",
            "day17_unlocked_timestamp": None,
            "last_transition_at": None,
        },
    )

    previous_status = str(prev_state.get("last_day16_status", "UNKNOWN")).upper()
    unlocked_ts = prev_state.get("day17_unlocked_timestamp")

    transition_logged = False
    transition_type = "none"

    if previous_status == "HOLD" and current_status == "READY_FOR_DAY17":
        transition_logged = True
        transition_type = "hold_to_ready_for_day17"
        unlocked_ts = run_ts
        _append_jsonl(
            transition_log_path,
            {
                "event": "DAY16_STATUS_TRANSITION",
                "transition": "HOLD_TO_READY_FOR_DAY17",
                "at": run_ts,
                "run_id": run_id,
                "previous_status": previous_status,
                "current_status": current_status,
                "scope": day16_report.get("scope"),
            },
        )

    if current_status == "READY_FOR_DAY17" and not unlocked_ts:
        unlocked_ts = run_ts

    day16_report.setdefault("audit", {})
    day16_report["audit"]["day17_unlocked_timestamp"] = unlocked_ts
    day16_report["audit"]["status_transition"] = {
        "previous": previous_status,
        "current": current_status,
        "type": transition_type,
        "logged": transition_logged,
    }
    day16_report_path.write_text(json.dumps(day16_report, indent=2), encoding="utf-8")

    next_state = {
        "last_day16_status": current_status,
        "day17_unlocked_timestamp": unlocked_ts,
        "last_transition_at": run_ts if transition_logged else prev_state.get("last_transition_at"),
        "last_seen_run_id": run_id,
        "updated_at": now.isoformat(),
    }
    state_path.parent.mkdir(parents=True, exist_ok=True)
    state_path.write_text(json.dumps(next_state, indent=2), encoding="utf-8")

    return {
        "previous_status": previous_status,
        "current_status": current_status,
        "transition_logged": transition_logged,
        "transition_type": transition_type,
        "day17_unlocked_timestamp": unlocked_ts,
        "state_file": str(state_path),
        "transition_log_file": str(transition_log_path),
    }


def main() -> int:
    parser = argparse.ArgumentParser(description="Track Day 16 observation status transitions")
    parser.add_argument(
        "--day16-report",
        default="documentation/migration/reports/DAY16_OBSERVATION_REPORT.json",
        help="Path to Day 16 report",
    )
    parser.add_argument(
        "--output",
        default="documentation/migration/reports/DAY16_WATCHER_RESULT.json",
        help="Path to watcher output",
    )
    parser.add_argument(
        "--state-file",
        default="documentation/migration/reports/history/DAY16_OBSERVATION_STATE.json",
        help="Path to watcher state JSON",
    )
    parser.add_argument(
        "--transition-log",
        default="documentation/migration/reports/history/DAY16_OBSERVATION_TRANSITIONS.jsonl",
        help="Path to watcher transition log JSONL",
    )

    args = parser.parse_args()

    day16_report_path = Path(args.day16_report)
    day16_report = _read_json(day16_report_path)
    transition = sync_day16_transition(
        day16_report_path=day16_report_path,
        day16_report=day16_report,
        state_path=Path(args.state_file),
        transition_log_path=Path(args.transition_log),
    )

    now = datetime.now(timezone.utc)
    payload = {
        "run_id": f"day16_watcher_{now.strftime('%Y%m%dT%H%M%SZ')}",
        "run_ts": now.isoformat(),
        "day16_status": transition["current_status"],
        "transition": transition,
    }
    out_path = Path(args.output)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(json.dumps(payload, indent=2), encoding="utf-8")

    print(f"[DONE] day16 watcher report: {args.output}")
    print(
        "[STATUS] "
        f"day16_status={transition['current_status']} "
        f"transition={transition['transition_type']}"
    )

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
