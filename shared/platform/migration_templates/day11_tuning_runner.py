from __future__ import annotations

import argparse
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List


def _read_json(path: Path) -> Dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def _safe_float(value: Any, default: float) -> float:
    try:
        return float(value)
    except (TypeError, ValueError):
        return default


def _safe_int(value: Any, default: int) -> int:
    try:
        return int(value)
    except (TypeError, ValueError):
        return default


def evaluate_day11_tuning(day10_report: Dict[str, Any]) -> Dict[str, Any]:
    now = datetime.now(timezone.utc)

    load = day10_report.get("load_backpressure", {})
    metrics = load.get("metrics", {})

    p95 = _safe_float(metrics.get("p95_latency_ms"), 999.0)
    p99 = _safe_float(metrics.get("p99_latency_ms"), 999.0)
    error_rate = _safe_float(metrics.get("error_rate_pct"), 5.0)
    queue_depth = _safe_int(metrics.get("max_queue_depth"), 999)

    guardrails = {
        "p95_limit_ms": 500.0,
        "p99_limit_ms": 1200.0,
        "error_rate_limit_pct": 1.0,
        "queue_depth_limit": 300,
    }

    utilization = {
        "p95": round(p95 / guardrails["p95_limit_ms"], 3),
        "p99": round(p99 / guardrails["p99_limit_ms"], 3),
        "error_rate": round(error_rate / guardrails["error_rate_limit_pct"], 3),
        "queue_depth": round(queue_depth / guardrails["queue_depth_limit"], 3),
    }

    bottlenecks: List[str] = []
    if utilization["p95"] >= 0.8:
        bottlenecks.append("p95_latency_near_limit")
    if utilization["p99"] >= 0.8:
        bottlenecks.append("p99_latency_near_limit")
    if utilization["error_rate"] >= 0.8:
        bottlenecks.append("error_rate_near_limit")
    if utilization["queue_depth"] >= 0.8:
        bottlenecks.append("queue_depth_near_limit")

    bottleneck_actions = {
        "partitioning": "Increase partitions only if queue depth trend > 70% for sustained window.",
        "batch_size": "Tune batch size incrementally by +10% with p95/p99 verification.",
        "retry_policy": "Use exponential backoff and cap retries to prevent retry storms.",
        "timeouts": "Set client timeout above p99 + safety margin; avoid too-aggressive timeout.",
        "connection_pool": "Increase pool size when concurrency rises and queue depth persists.",
    }

    tuned_alert_thresholds = {
        "latency_p95_warning_ms": max(300, int(round(p95 * 1.35))),
        "latency_p99_critical_ms": max(700, int(round(p99 * 1.4))),
        "error_rate_warning_pct": round(max(0.4, error_rate * 2.5), 3),
        "queue_depth_warning": max(120, int(round(queue_depth * 1.8))),
        "min_consecutive_breaches": 3,
        "evaluation_window_minutes": 10,
        "cooldown_minutes": 15,
    }

    load_status = str(load.get("overall_status", "UNKNOWN")).upper()
    tuning_status = "TUNED" if load_status == "PASS" else "ACTION_REQUIRED"

    return {
        "run_id": f"day11_tuning_{now.strftime('%Y%m%dT%H%M%SZ')}",
        "run_ts": now.isoformat(),
        "scope": "Day 11 bottleneck analysis + alert threshold tuning",
        "inputs": {
            "day10_rollout_report": "documentation/migration/reports/DAY10_ROLLOUT_REPORT.json",
        },
        "baseline": {
            "metrics": {
                "p95_latency_ms": p95,
                "p99_latency_ms": p99,
                "error_rate_pct": error_rate,
                "max_queue_depth": queue_depth,
            },
            "guardrails": guardrails,
            "utilization_ratio": utilization,
        },
        "bottleneck_analysis": {
            "detected_items": bottlenecks,
            "actions": bottleneck_actions,
        },
        "alert_tuning": {
            "policy_version": "day11-v1",
            "tuned_thresholds": tuned_alert_thresholds,
            "goal": "Reduce false positives while preserving safety guardrails",
        },
        "summary": {
            "status": tuning_status,
            "bottleneck_items_count": len(bottlenecks),
            "decision": (
                "Day 11 tuning ready for rollout"
                if tuning_status == "TUNED"
                else "Investigate load regressions before applying tuned thresholds"
            ),
        },
    }


def main() -> int:
    parser = argparse.ArgumentParser(description="Run Day 11 bottleneck and alert tuning")
    parser.add_argument(
        "--day10-report",
        default="documentation/migration/reports/DAY10_ROLLOUT_REPORT.json",
        help="Path to day10 rollout report",
    )
    parser.add_argument(
        "--output",
        default="documentation/migration/reports/DAY11_TUNING_REPORT.json",
        help="Path to day11 report output",
    )
    parser.add_argument(
        "--threshold-output",
        default="infrastructure/docker/migration-day4/alert_thresholds.day11.tuned.json",
        help="Path to tuned alert thresholds output",
    )

    args = parser.parse_args()

    day10_report = _read_json(Path(args.day10_report))
    report = evaluate_day11_tuning(day10_report)

    output_path = Path(args.output)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(json.dumps(report, indent=2), encoding="utf-8")

    threshold_path = Path(args.threshold_output)
    threshold_path.parent.mkdir(parents=True, exist_ok=True)
    threshold_path.write_text(
        json.dumps(report["alert_tuning"]["tuned_thresholds"], indent=2),
        encoding="utf-8",
    )

    print(f"[DONE] day11 report: {output_path}")
    print(f"[DONE] tuned thresholds: {threshold_path}")
    print(f"[STATUS] day11={report['summary']['status']}")

    return 0 if report["summary"]["status"] == "TUNED" else 2


if __name__ == "__main__":
    raise SystemExit(main())
