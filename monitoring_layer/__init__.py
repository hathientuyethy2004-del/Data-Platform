"""
Monitoring Layer - Complete Observability System
Metrics, Logging, Tracing, Health Checks, Alerts, and Dashboard
"""

# Core monitoring components
from monitoring_layer.metrics.metrics_collector import (
    MetricType,
    MetricPoint,
    Metric,
    MetricsCollector,
    get_metrics_collector
)

from monitoring_layer.logging.log_aggregator import (
    LogLevel,
    LogEvent,
    LogAggregator,
    get_log_aggregator
)

from monitoring_layer.tracing.tracing_collector import (
    Span,
    Trace,
    TracingCollector,
    get_tracing_collector
)

# Health checking
from monitoring_layer.health.health_checks import (
    HealthStatus,
    HealthCheckResult,
    ComponentHealth,
    HealthCheckManager,
    create_kafka_check,
    create_storage_check,
    create_database_check,
    get_health_check_manager
)

# Alerting
from monitoring_layer.alerts.alert_manager import (
    Severity,
    AlertStatus,
    AlertRule,
    Alert,
    Incident,
    NotificationChannel,
    AlertManager,
    get_alert_manager
)

# Dashboard
from monitoring_layer.dashboard.observability_dashboard import (
    ObservabilityDashboard,
    get_observability_dashboard
)

# Integration
from monitoring_layer.integration.platform_integration import (
    MonitoringIntegration,
    OperationTimer,
    get_monitoring_integration
)

# Utilities and decorators
from monitoring_layer.utils.monitoring_decorators import (
    make_metric_name,
    make_log_message,
    TrackExecution,
    TrackTiming,
    CountCalls,
    TrackErrors,
    LogFunction,
    TraceFunction,
    measure_time,
    count_operation,
    retry_with_tracking,
    batch_operation
)

__all__ = [
    # Metrics
    "MetricType",
    "MetricPoint",
    "Metric",
    "MetricsCollector",
    "get_metrics_collector",
    
    # Logging
    "LogLevel",
    "LogEvent",
    "LogAggregator",
    "get_log_aggregator",
    
    # Tracing
    "Span",
    "Trace",
    "TracingCollector",
    "get_tracing_collector",
    
    # Health
    "HealthStatus",
    "HealthCheckResult",
    "ComponentHealth",
    "HealthCheckManager",
    "create_kafka_check",
    "create_storage_check",
    "create_database_check",
    "get_health_check_manager",
    
    # Alerts
    "Severity",
    "AlertStatus",
    "AlertRule",
    "Alert",
    "Incident",
    "NotificationChannel",
    "AlertManager",
    "get_alert_manager",
    
    # Dashboard
    "ObservabilityDashboard",
    "get_observability_dashboard",
    
    # Integration
    "MonitoringIntegration",
    "OperationTimer",
    "get_monitoring_integration",
    
    # Decorators and utilities
    "make_metric_name",
    "make_log_message",
    "TrackExecution",
    "TrackTiming",
    "CountCalls",
    "TrackErrors",
    "LogFunction",
    "TraceFunction",
    "measure_time",
    "count_operation",
    "retry_with_tracking",
    "batch_operation"
]

__version__ = "1.0.0"
__description__ = "Enterprise-grade monitoring and observability platform"
