"""
Platform bootstrap helpers - start long-running platform services.
"""
from typing import Optional


def start_platform_services(metrics_storage_path: Optional[str] = None):
    """Start platform background services such as aggregation scheduler.

    This centralizes startup so that creating MonitoringIntegration does not
    have side-effects.
    """
    try:
        from analytics_layer.aggregation_engine import get_aggregation_engine
        from monitoring_layer.metrics.metrics_collector import get_metrics_collector

        engine = get_aggregation_engine()
        engine.start_scheduler()

        # Register a scheduler status metric for visibility
        try:
            metrics = get_metrics_collector(metrics_storage_path or "/tmp/monitoring/metrics")
            metrics.register_metric(
                name="aggregation_scheduler_status",
                type_="gauge",
                description="Aggregation scheduler running status (1=running)",
                labels=["component"]
            )
            metrics.set_gauge("aggregation_scheduler_status", 1, labels={"component": "aggregation_scheduler"})
        except Exception:
            pass

    except Exception:
        # Best-effort start; avoid failing platform startup if analytics not available
        pass


if __name__ == '__main__':
    start_platform_services()
