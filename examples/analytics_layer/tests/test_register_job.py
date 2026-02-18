import os
import pytest
from monitoring_layer.metrics.metrics_collector import get_metrics_collector


def test_register_aggregation_job_creates_metrics():
    # Ensure metrics collector uses a temp path so tests don't interfere
    metrics = get_metrics_collector(storage_path="/tmp/monitoring_test/metrics")
    # Run the register example
    import analytics_layer.examples.register_aggregation_job as r
    r.register_and_run()

    # Check that aggregation job metrics are registered
    expected_counter = "aggregation_events_count_job_runs_total"
    expected_duration = "aggregation_events_count_job_duration_ms"
    expected_status = "aggregation_events_count_job_last_status"

    registered = metrics.metrics
    assert expected_counter in registered or any(k.startswith(expected_counter) for k in registered.keys())
    assert expected_duration in registered or any(k.startswith(expected_duration) for k in registered.keys())
    assert expected_status in registered or any(k.startswith(expected_status) for k in registered.keys())
