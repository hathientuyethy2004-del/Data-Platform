from shared.platform.migration_templates.day11_tuning_runner import evaluate_day11_tuning


def _day10_report(load_status: str = "PASS", p95: float = 220, p99: float = 500, error: float = 0.25, queue: int = 95):
    return {
        "load_backpressure": {
            "overall_status": load_status,
            "metrics": {
                "p95_latency_ms": p95,
                "p99_latency_ms": p99,
                "error_rate_pct": error,
                "max_queue_depth": queue,
            },
        }
    }


def test_day11_tuning_status_tuned_when_load_pass():
    report = evaluate_day11_tuning(_day10_report("PASS"))
    assert report["summary"]["status"] == "TUNED"
    assert report["alert_tuning"]["tuned_thresholds"]["min_consecutive_breaches"] == 3


def test_day11_tuning_detects_bottlenecks_near_limits():
    report = evaluate_day11_tuning(_day10_report("PASS", p95=450, p99=1000, error=0.9, queue=260))
    detected = set(report["bottleneck_analysis"]["detected_items"])
    assert "p95_latency_near_limit" in detected
    assert "p99_latency_near_limit" in detected
    assert "error_rate_near_limit" in detected
    assert "queue_depth_near_limit" in detected


def test_day11_tuning_action_required_when_load_fail():
    report = evaluate_day11_tuning(_day10_report("FAIL"))
    assert report["summary"]["status"] == "ACTION_REQUIRED"
