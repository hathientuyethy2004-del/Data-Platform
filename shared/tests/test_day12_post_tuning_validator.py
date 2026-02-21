from shared.platform.migration_templates.day12_post_tuning_validator import build_day12_report


def _day11_report():
    return {
        "baseline": {
            "guardrails": {
                "p95_limit_ms": 500.0,
                "p99_limit_ms": 1200.0,
                "error_rate_limit_pct": 1.0,
                "queue_depth_limit": 300,
            }
        }
    }


def _tuned_thresholds():
    return {
        "latency_p95_warning_ms": 300,
        "latency_p99_critical_ms": 700,
        "error_rate_warning_pct": 0.625,
        "queue_depth_warning": 171,
        "min_consecutive_breaches": 3,
        "cooldown_minutes": 15,
    }


def _observations():
    obs = []
    for idx in range(20):
        item = {
            "ts": f"2026-02-21T12:{idx:02d}:00+00:00",
            "p95_latency_ms": 220,
            "p99_latency_ms": 500,
            "error_rate_pct": 0.2,
            "queue_depth": 90,
            "incident_confirmed": False,
        }
        obs.append(item)

    for idx in [3, 7, 12]:
        obs[idx]["p95_latency_ms"] = 380
        obs[idx]["p99_latency_ms"] = 780
        obs[idx]["error_rate_pct"] = 0.6
        obs[idx]["queue_depth"] = 190

    for idx in [15, 16, 17, 18]:
        obs[idx]["p95_latency_ms"] = 560
        obs[idx]["p99_latency_ms"] = 1300
        obs[idx]["error_rate_pct"] = 1.5
        obs[idx]["queue_depth"] = 350
        obs[idx]["incident_confirmed"] = True

    return obs


def test_day12_validation_report_has_comparison_and_summary():
    report = build_day12_report(
        day11_report=_day11_report(),
        tuned_thresholds=_tuned_thresholds(),
        observations=_observations(),
    )

    assert "comparison" in report
    assert report["summary"]["status"] == "VALIDATED"
    assert "false_positive_rate_reduction_pct_points" in report["comparison"]
    assert "alert_volume_reduction_pct" in report["comparison"]


def test_day12_after_policy_has_no_false_negative_for_incident_window():
    report = build_day12_report(
        day11_report=_day11_report(),
        tuned_thresholds=_tuned_thresholds(),
        observations=_observations(),
    )

    after_eval = report["comparison"]["after_policy"]["evaluation"]
    assert after_eval["false_negative_incident_windows"] == 0
