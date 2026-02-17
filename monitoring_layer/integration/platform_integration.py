"""
Monitoring Integration
Automatic instrumentation for data platform components
"""

from typing import Dict, List, Callable, Optional
import time
import functools
from datetime import datetime


class MonitoringIntegration:
    """Integration layer for automatic instrumentation"""

    def __init__(self, metrics_collector=None, log_aggregator=None,
                 tracing_collector=None):
        """Initialize monitoring integration"""
        self.metrics = metrics_collector
        self.logs = log_aggregator
        self.traces = tracing_collector
        self.registered_components = {}

    def register_component(self, component_name: str,
                          component_type: str = "service") -> bool:
        """Register component for monitoring"""
        if component_name in self.registered_components:
            return False
        
        self.registered_components[component_name] = {
            "type": component_type,
            "registered_at": datetime.now().isoformat(),
            "metrics": [],
            "handlers": []
        }
        
        # Register default metrics for component
        self._register_component_metrics(component_name, component_type)
        
        return True

    def unregister_component(self, component_name: str) -> bool:
        """Unregister component"""
        if component_name not in self.registered_components:
            return False
        
        del self.registered_components[component_name]
        return True

    def get_registered_components(self) -> Dict:
        """Get all registered components"""
        return dict(self.registered_components)

    def integrate_kafka_metrics(self, broker: str = "localhost:9092") -> Dict:
        """Register Kafka metrics"""
        metrics = {
            "kafka_messages_in": "counter",
            "kafka_messages_out": "counter",
            "kafka_bytes_in": "counter",
            "kafka_bytes_out": "counter",
            "kafka_lag": "gauge",
            "kafka_processing_time_ms": "histogram"
        }
        
        if self.metrics:
            for metric_name, metric_type in metrics.items():
                self.metrics.register_metric(
                    name=metric_name,
                    metric_type=metric_type,
                    description=f"Kafka {metric_name}",
                    labels={"broker": broker}
                )
        
        return metrics

    def integrate_spark_metrics(self, app_name: str = "spark") -> Dict:
        """Register Spark job metrics"""
        metrics = {
            "spark_jobs_completed": "counter",
            "spark_jobs_failed": "counter",
            "spark_tasks_completed": "counter",
            "spark_tasks_failed": "counter",
            "spark_rdd_blocks": "gauge",
            "spark_memory_used_mb": "gauge",
            "spark_execution_time_ms": "histogram",
            "spark_shuffle_bytes": "counter"
        }
        
        if self.metrics:
            for metric_name, metric_type in metrics.items():
                self.metrics.register_metric(
                    name=metric_name,
                    metric_type=metric_type,
                    description=f"Spark {metric_name}",
                    labels={"app": app_name}
                )
        
        return metrics

    def integrate_lakehouse_metrics(self) -> Dict:
        """Register data lakehouse metrics"""
        metrics = {
            "lakehouse_records_ingested": "counter",
            "lakehouse_records_processed": "counter",
            "lakehouse_records_gold": "gauge",
            "lakehouse_data_size_gb": "gauge",
            "lakehouse_processing_time_ms": "histogram",
            "lakehouse_quality_score": "gauge"
        }
        
        if self.metrics:
            for metric_name, metric_type in metrics.items():
                self.metrics.register_metric(
                    name=metric_name,
                    metric_type=metric_type,
                    description=f"Lakehouse {metric_name}",
                    labels={"layer": "all"}
                )
        
        return metrics

    def integrate_governance_metrics(self) -> Dict:
        """Register governance system metrics"""
        metrics = {
            "governance_policies_checked": "counter",
            "governance_violations_detected": "counter",
            "governance_lineage_edges": "gauge",
            "governance_catalog_entries": "gauge",
            "governance_check_time_ms": "histogram",
            "governance_compliance_score": "gauge"
        }
        
        if self.metrics:
            for metric_name, metric_type in metrics.items():
                self.metrics.register_metric(
                    name=metric_name,
                    metric_type=metric_type,
                    description=f"Governance {metric_name}",
                    labels={"system": "governance"}
                )
        
        return metrics

    def monitored_function(self, component: str = "unknown",
                          operation: str = "unknown"):
        """Decorator for automatic function monitoring"""
        def decorator(func: Callable):
            @functools.wraps(func)
            def wrapper(*args, **kwargs):
                start_time = time.time()
                duration_ms = None
                
                # Start trace
                trace_id = None
                span_id = None
                if self.traces:
                    try:
                        result = self.traces.start_trace(
                            service=component,
                            request_id=f"{operation}_{int(start_time*1000)}"
                        )
                        trace_id = result[0] if isinstance(result, tuple) else result
                        span_id = self.traces.start_span(
                            operation_name=operation,
                            component=component
                        )
                    except:
                        pass
                
                # Log function call
                if self.logs:
                    try:
                        self.logs.info(
                            component=component,
                            message=f"Started: {operation}",
                            trace_id=trace_id
                        )
                    except:
                        pass
                
                try:
                    result = func(*args, **kwargs)
                    duration_ms = (time.time() - start_time) * 1000
                    
                    # Record metrics
                    if self.metrics:
                        try:
                            # Count executions
                            self.metrics.increment_counter(
                                f"{component}_{operation}_calls",
                                labels={"status": "success"}
                            )
                            # Record duration
                            self.metrics.observe_histogram(
                                f"{component}_{operation}_duration_ms",
                                duration_ms
                            )
                        except:
                            pass
                    
                    # Log success
                    if self.logs:
                        try:
                            self.logs.info(
                                component=component,
                                message=f"Completed: {operation} ({duration_ms:.2f}ms)",
                                trace_id=trace_id
                            )
                        except:
                            pass
                    
                    # End span
                    if self.traces and span_id:
                        try:
                            self.traces.end_span(span_id, "SUCCESS")
                            self.traces.end_trace(trace_id)
                        except:
                            pass
                    
                    return result
                
                except Exception as e:
                    duration_ms = (time.time() - start_time) * 1000
                    
                    # Record metrics
                    if self.metrics:
                        try:
                            self.metrics.increment_counter(
                                f"{component}_{operation}_calls",
                                labels={"status": "error"}
                            )
                            self.metrics.observe_histogram(
                                f"{component}_{operation}_duration_ms",
                                duration_ms
                            )
                        except:
                            pass
                    
                    # Log error
                    if self.logs:
                        try:
                            self.logs.error(
                                component=component,
                                message=f"Failed: {operation}",
                                exception=str(e),
                                trace_id=trace_id
                            )
                        except:
                            pass
                    
                    # End span with error
                    if self.traces and span_id:
                        try:
                            self.traces.end_span(
                                span_id, "ERROR",
                                error_details={"error": str(e)}
                            )
                            self.traces.end_trace(trace_id)
                        except:
                            pass
                    
                    raise
            
            return wrapper
        return decorator

    def create_timer(self, component: str, operation: str):
        """Context manager for timing operations"""
        return OperationTimer(
            component=component,
            operation=operation,
            metrics=self.metrics,
            logs=self.logs,
            traces=self.traces
        )

    def _register_component_metrics(self, component_name: str,
                                   component_type: str):
        """Register default metrics for component"""
        if not self.metrics:
            return
        
        base_metrics = {
            f"{component_name}_operations_total": "counter",
            f"{component_name}_errors_total": "counter",
            f"{component_name}_operation_duration_seconds": "histogram",
            f"{component_name}_status": "gauge"
        }
        
        try:
            for metric_name, metric_type in base_metrics.items():
                self.metrics.register_metric(
                    name=metric_name,
                    metric_type=metric_type,
                    description=f"{component_name} {metric_name}",
                    labels={"component": component_name, "type": component_type}
                )
                self.registered_components[component_name]["metrics"].append(metric_name)
        except:
            pass


class OperationTimer:
    """Context manager for timing operations"""

    def __init__(self, component: str, operation: str,
                 metrics=None, logs=None, traces=None):
        """Initialize operation timer"""
        self.component = component
        self.operation = operation
        self.metrics = metrics
        self.logs = logs
        self.traces = traces
        self.start_time = None
        self.duration_ms = None
        self.trace_id = None
        self.span_id = None

    def __enter__(self):
        """Enter context"""
        self.start_time = time.time()
        
        # Start trace
        if self.traces:
            try:
                self.trace_id = self.traces.start_trace(
                    service=self.component,
                    request_id=f"{self.operation}_{int(self.start_time*1000)}"
                )
                self.span_id = self.traces.start_span(
                    operation_name=self.operation,
                    component=self.component
                )
            except:
                pass
        
        # Log start
        if self.logs:
            try:
                self.logs.info(
                    component=self.component,
                    message=f"Started: {self.operation}",
                    trace_id=self.trace_id
                )
            except:
                pass
        
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Exit context"""
        self.duration_ms = (time.time() - self.start_time) * 1000
        
        if exc_type is None:
            # Success
            if self.metrics:
                try:
                    self.metrics.increment_counter(
                        f"{self.component}_{self.operation}_calls",
                        labels={"status": "success"}
                    )
                    self.metrics.observe_histogram(
                        f"{self.component}_{self.operation}_duration_ms",
                        self.duration_ms
                    )
                except:
                    pass
            
            if self.logs:
                try:
                    self.logs.info(
                        component=self.component,
                        message=f"Completed: {self.operation} ({self.duration_ms:.2f}ms)",
                        trace_id=self.trace_id
                    )
                except:
                    pass
            
            if self.traces and self.span_id:
                try:
                    self.traces.end_span(self.span_id, "SUCCESS", duration_ms=self.duration_ms)
                    self.traces.end_trace(self.trace_id)
                except:
                    pass
        
        else:
            # Error
            if self.metrics:
                try:
                    self.metrics.increment_counter(
                        f"{self.component}_{self.operation}_calls",
                        labels={"status": "error"}
                    )
                    self.metrics.observe_histogram(
                        f"{self.component}_{self.operation}_duration_ms",
                        self.duration_ms
                    )
                except:
                    pass
            
            if self.logs:
                try:
                    self.logs.error(
                        component=self.component,
                        message=f"Failed: {self.operation}",
                        exception=str(exc_val),
                        trace_id=self.trace_id
                    )
                except:
                    pass
            
            if self.traces and self.span_id:
                try:
                    self.traces.end_span(
                        self.span_id, "ERROR",
                        duration_ms=self.duration_ms,
                        error_details={"error": str(exc_val)}
                    )
                    self.traces.end_trace(self.trace_id)
                except:
                    pass
        
        return False


# Global integration instance
_integration = None

def get_monitoring_integration(metrics_collector=None, log_aggregator=None,
                             tracing_collector=None) -> MonitoringIntegration:
    """Get or create global monitoring integration"""
    global _integration
    if _integration is None:
        _integration = MonitoringIntegration(
            metrics_collector, log_aggregator, tracing_collector
        )
    return _integration
