"""
Integration Tests - Monitoring Layer
Complete system testing with all components
"""

import sys
import json
import time
from datetime import datetime
from pathlib import Path

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent))

from metrics.metrics_collector import get_metrics_collector, MetricType
from logging.log_aggregator import get_log_aggregator, LogLevel
from tracing.tracing_collector import get_tracing_collector
from health.health_checks import get_health_check_manager, create_storage_check
from alerts.alert_manager import get_alert_manager, AlertRule, NotificationChannel, Severity
from dashboard.observability_dashboard import get_observability_dashboard
from integration.platform_integration import get_monitoring_integration
from utils.monitoring_decorators import TrackExecution, MeasureTime


def test_metrics_collection():
    """Test metrics collection system"""
    print("\n" + "="*60)
    print("TEST 1: Metrics Collection")
    print("="*60)
    
    metrics = get_metrics_collector()
    
    # Register metrics
    metrics.register_metric("request_count", "counter", "HTTP requests", "count")
    metrics.register_metric("response_time", "histogram", "Response time", "ms")
    metrics.register_metric("active_connections", "gauge", "Active connections", "count")
    metrics.register_metric("memory_usage", "summary", "Memory usage", "MB")
    
    # Record data
    for i in range(100):
        metrics.increment_counter("request_count", labels={"method": "GET"})
        metrics.observe_histogram("response_time", 50 + (i % 30), labels={"endpoint": "/api"})
    
    metrics.set_gauge("active_connections", 42, labels={"service": "api"})
    for i in range(50):
        metrics.observe_summary("memory_usage", 100 + (i * 2), labels={"service": "api"})
    
    # Get statistics
    stats = metrics.get_metric_statistics("response_time", labels={"endpoint": "/api"})
    print(f"\nResponse Time Statistics:")
    print(f"  Count: {stats.get('count', 0)}")
    print(f"  Mean: {stats.get('mean', 0):.2f}ms")
    print(f"  Min: {stats.get('min', 0):.2f}ms")
    print(f"  Max: {stats.get('max', 0):.2f}ms")
    print(f"  P95: {stats.get('p95', 0):.2f}ms")
    print(f"  P99: {stats.get('p99', 0):.2f}ms")
    
    # Export
    metrics.export_metrics("/tmp/monitoring_test_metrics.json")
    print("\n✓ Metrics exported to /tmp/monitoring_test_metrics.json")
    
    return True


def test_logging_system():
    """Test centralized logging system"""
    print("\n" + "="*60)
    print("TEST 2: Centralized Logging")
    print("="*60)
    
    logs = get_log_aggregator()
    
    # Log various events
    logs.info("system", "Application started")
    logs.debug("database", "Connecting to database")
    logs.warning("cache", "Cache miss rate high", context={"rate": 0.05})
    
    for i in range(20):
        logs.info("api", f"Request {i} processed", trace_id=f"trace_{i}")
    
    # Simulate errors
    for i in range(5):
        logs.error("database", "Connection timeout", exception="TimeoutError")
        logs.error("api", "Request failed", exception="HTTPError")
    
    # Get statistics
    stats = logs.get_log_statistics()
    print(f"\nLog Statistics:")
    print(f"  Total Logs: {stats.get('total_logs', 0)}")
    print(f"  Errors: {stats.get('errors', 0)}")
    print(f"  Warnings: {stats.get('warnings', 0)}")
    print(f"  Error Rate: {stats.get('error_rate', 0)*100:.2f}%")
    
    # Get error summary
    error_summary = logs.get_error_summary()
    print(f"\nTop Errors:")
    for error_type, count in list(error_summary.items())[:5]:
        print(f"  {error_type}: {count}")
    
    # Export logs
    logs.export_logs("/tmp/monitoring_test_logs.json")
    print("\n✓ Logs exported to /tmp/monitoring_test_logs.json")
    
    return True


def test_tracing_system():
    """Test distributed tracing system"""
    print("\n" + "="*60)
    print("TEST 3: Distributed Tracing")
    print("="*60)
    
    traces = get_tracing_collector()
    
    # Simulate a request trace
    trace_id = traces.start_trace(service="user-service", request_id="req_123")
    
    # Simulate span hierarchy
    auth_span = traces.start_span(
        operation_name="authenticate",
        component="auth-service"
    )
    time.sleep(0.05)
    traces.add_event(auth_span, "user_authenticated", {"user_id": "user_123"})
    traces.end_span(auth_span, "SUCCESS")
    
    db_span = traces.start_span(
        operation_name="fetch_user",
        component="database"
    )
    time.sleep(0.02)
    traces.add_tag(db_span, "query", "SELECT * FROM users WHERE id=?")
    traces.end_span(db_span, "SUCCESS")
    
    traces.end_trace(trace_id)
    
    # Create more traces
    for i in range(10):
        t_id = traces.start_trace(service="api-service", request_id=f"req_{i}")
        span = traces.start_span(operation_name=f"operation_{i}", component="handler")
        time.sleep(0.001 * (i + 1))
        traces.end_span(span, "SUCCESS")
        traces.end_trace(t_id)
    
    # Get statistics
    stats = traces.get_tracing_statistics()
    print(f"\nTracing Statistics:")
    print(f"  Total Traces: {stats.get('total_traces', 0)}")
    print(f"  Completed: {stats.get('completed_traces', 0)}")
    print(f"  Average Duration: {stats.get('average_duration_ms', 0):.2f}ms")
    print(f"  By Service: {stats.get('by_service', {})}")
    
    # Export a trace
    traces.export_trace(trace_id, "/tmp/monitoring_test_trace.json")
    print(f"\n✓ Trace exported to /tmp/monitoring_test_trace.json")
    
    return True


def test_health_checks():
    """Test health checking system"""
    print("\n" + "="*60)
    print("TEST 4: Health Checks")
    print("="*60)
    
    health = get_health_check_manager()
    
    # Register health checks
    storage_check = create_storage_check("/tmp")
    health.register_check("storage", "disk_check", storage_check)
    
    # Simple service check
    def service_check():
        return ("healthy", "Service responding", {})
    
    health.register_check("api_service", "liveness", service_check)
    health.register_check("api_service", "readiness", service_check)
    
    # Run checks
    health.run_all_checks()
    
    # Get system health
    system_health = health.get_system_health()
    print(f"\nSystem Health Status: {system_health.get('status').upper()}")
    print(f"  Healthy Components: {system_health.get('healthy_components', 0)}")
    print(f"  Degraded Components: {system_health.get('degraded_components', 0)}")
    print(f"  System Availability: {system_health.get('system_availability', 0):.2f}%")
    
    # Export health report
    health.export_health_report("/tmp/monitoring_test_health.json")
    print("\n✓ Health report exported to /tmp/monitoring_test_health.json")
    
    return True


def test_alert_system():
    """Test alert management system"""
    print("\n" + "="*60)
    print("TEST 5: Alert Management")
    print("="*60)
    
    alerts = get_alert_manager()
    
    # Register notification channel
    channel = NotificationChannel(
        channel_type="console",
        channel_name="default",
        config={"output": "stdout"}
    )
    alerts.register_channel(channel)
    
    # Create alert rules
    rule1 = AlertRule(
        rule_id="rule_1",
        name="High CPU Usage",
        metric="cpu_usage",
        condition="> 85",
        threshold=85,
        severity=Severity.CRITICAL.value,
        notification_channels=["default"]
    )
    
    rule2 = AlertRule(
        rule_id="rule_2",
        name="Low Disk Space",
        metric="disk_free_gb",
        condition="< 10",
        threshold=10,
        severity=Severity.HIGH.value,
        notification_channels=["default"]
    )
    
    alerts.register_rule(rule1)
    alerts.register_rule(rule2)
    
    # Evaluate and trigger alerts
    print("\nTriggering alerts...")
    alerts.evaluate_and_trigger("cpu_usage", 92, triggered_by="monitoring_system")
    alerts.evaluate_and_trigger("disk_free_gb", 5, triggered_by="monitoring_system")
    alerts.evaluate_and_trigger("cpu_usage", 88, triggered_by="monitoring_system")
    
    # Get alert statistics
    stats = alerts.get_alert_statistics()
    print(f"\nAlert Statistics:")
    print(f"  Total Alerts: {stats.get('total_alerts', 0)}")
    print(f"  Triggered: {stats.get('triggered', 0)}")
    print(f"  Critical: {stats.get('critical_count', 0)}")
    print(f"  Open Incidents: {stats.get('open_incidents', 0)}")
    
    # Export incidents
    alerts.export_incidents("/tmp/monitoring_test_incidents.json")
    print("\n✓ Incidents exported to /tmp/monitoring_test_incidents.json")
    
    return True


def test_observability_dashboard():
    """Test observability dashboard"""
    print("\n" + "="*60)
    print("TEST 6: Observability Dashboard")
    print("="*60)
    
    # Get all components
    metrics = get_metrics_collector()
    logs = get_log_aggregator()
    traces = get_tracing_collector()
    health = get_health_check_manager()
    alerts = get_alert_manager()
    
    # Create dashboard
    dashboard = get_observability_dashboard(
        metrics_collector=metrics,
        log_aggregator=logs,
        tracing_collector=traces,
        health_manager=health,
        alert_manager=alerts
    )
    
    # Get dashboard summary
    summary = dashboard.get_dashboard_summary()
    print(f"\nDashboard Summary:")
    print(f"  System Status: {summary.get('system_health', {}).get('status', 'unknown').upper()}")
    print(f"  Total Metrics: {summary.get('metrics_overview', {}).get('total_metrics', 0)}")
    print(f"  Active Alerts: {summary.get('alerts_overview', {}).get('triggered', 0)}")
    print(f"  Total Logs: {summary.get('logs_overview', {}).get('total_logs', 0)}")
    
    # Export report
    dashboard.export_report("/tmp/monitoring_test_report.json")
    print("\n✓ Dashboard report exported to /tmp/monitoring_test_report.json")
    
    return True


def test_platform_integration():
    """Test platform integration system"""
    print("\n" + "="*60)
    print("TEST 7: Platform Integration")
    print("="*60)
    
    metrics = get_metrics_collector()
    logs = get_log_aggregator()
    traces = get_tracing_collector()
    
    integration = get_monitoring_integration(metrics, logs, traces)
    
    # Register components
    integration.register_component("kafka_ingestion", "streaming")
    integration.register_component("spark_processing", "computing")
    integration.register_component("lakehouse_storage", "storage")
    
    # Register component metrics
    print("\nRegistering component metrics...")
    kafka_metrics = integration.integrate_kafka_metrics()
    spark_metrics = integration.integrate_spark_metrics()
    lakehouse_metrics = integration.integrate_lakehouse_metrics()
    
    print(f"  Kafka metrics: {len(kafka_metrics)} registered")
    print(f"  Spark metrics: {len(spark_metrics)} registered")
    print(f"  Lakehouse metrics: {len(lakehouse_metrics)} registered")
    
    # Test monitored function
    @integration.monitored_function(component="spark_processing", operation="process_batch")
    def process_data_batch(records):
        time.sleep(0.1)
        return {"processed": len(records), "status": "success"}
    
    print("\nExecuting monitored function...")
    result = process_data_batch([1, 2, 3, 4, 5])
    print(f"  Processing result: {result}")
    
    # Test context manager
    print("\nUsing monitoring context manager...")
    with integration.create_timer("data_pipeline", "etl_run"):
        time.sleep(0.05)
        logs.info("data_pipeline", "ETL pipeline executed successfully")
    
    registered = integration.get_registered_components()
    print(f"\nRegistered Components: {len(registered)}")
    for comp_name, comp_info in registered.items():
        print(f"  - {comp_name} ({comp_info['type']})")
    
    return True


def test_monitoring_decorators():
    """Test monitoring decorators"""
    print("\n" + "="*60)
    print("TEST 8: Monitoring Decorators")
    print("="*60)
    
    metrics = get_metrics_collector()
    
    # Test tracking decorator
    @TrackExecution(component="demo", metrics_collector=metrics)
    def demo_function(x):
        time.sleep(0.01)
        return x * 2
    
    print("\nTesting @TrackExecution decorator...")
    for i in range(5):
        result = demo_function(i)
    
    # Get metrics
    stats = metrics.get_metric_statistics("demo_demo_function_duration_ms", labels={})
    print(f"  Function execution metrics:")
    print(f"    Call count: {metrics.get_metric_value('demo_demo_function_calls', {'status': 'success'})}")
    print(f"    Mean duration: {stats.get('mean', 0):.2f}ms")
    
    print("\n✓ Decorators tested successfully")
    
    return True


def run_all_tests():
    """Run all integration tests"""
    print("\n" + "="*70)
    print(" "*15 + "MONITORING LAYER INTEGRATION TESTS")
    print("="*70)
    
    tests = [
        ("Metrics Collection", test_metrics_collection),
        ("Logging System", test_logging_system),
        ("Tracing System", test_tracing_system),
        ("Health Checks", test_health_checks),
        ("Alert System", test_alert_system),
        ("Dashboard", test_observability_dashboard),
        ("Platform Integration", test_platform_integration),
        ("Decorators", test_monitoring_decorators),
    ]
    
    results = {}
    for test_name, test_func in tests:
        try:
            results[test_name] = test_func()
        except Exception as e:
            results[test_name] = False
            print(f"\n✗ {test_name} failed: {str(e)}")
    
    # Summary
    print("\n" + "="*70)
    print(" "*20 + "TEST SUMMARY")
    print("="*70)
    
    passed = sum(1 for r in results.values() if r)
    total = len(results)
    
    for test_name, result in results.items():
        status = "✓ PASS" if result else "✗ FAIL"
        print(f"{status}: {test_name}")
    
    print(f"\nTotal: {passed}/{total} tests passed")
    print("\n✓ All exports available in /tmp/monitoring_test_*.json")
    
    return passed == total


if __name__ == "__main__":
    success = run_all_tests()
    sys.exit(0 if success else 1)
