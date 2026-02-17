"""
Observability Dashboard
Real-time monitoring visualization and API
"""

from typing import Dict, List, Optional
from datetime import datetime, timedelta
import json
import threading
from threading import Lock


class ObservabilityDashboard:
    """Real-time observability dashboard"""

    def __init__(self, metrics_collector=None, log_aggregator=None,
                 tracing_collector=None, health_manager=None, alert_manager=None):
        """Initialize observability dashboard"""
        self.metrics = metrics_collector
        self.logs = log_aggregator
        self.traces = tracing_collector
        self.health = health_manager
        self.alerts = alert_manager
        
        self.lock = Lock()
        self.last_updated = None

    def get_dashboard_summary(self) -> Dict:
        """Get dashboard summary"""
        return {
            "timestamp": datetime.now().isoformat(),
            "system_health": self._get_health_summary(),
            "metrics_overview": self._get_metrics_summary(),
            "alerts_overview": self._get_alerts_summary(),
            "logs_overview": self._get_logs_summary(),
            "traces_overview": self._get_traces_summary()
        }

    def get_metrics_panel(self, metric_name: str = None,
                         time_range_minutes: int = 60) -> Dict:
        """Get metrics panel data"""
        if not self.metrics:
            return {"error": "Metrics collector not available"}
        
        return {
            "timestamp": datetime.now().isoformat(),
            "metrics": self._collect_metrics_data(metric_name, time_range_minutes)
        }

    def get_traces_panel(self, limit: int = 50,
                        status: str = None) -> Dict:
        """Get traces panel data"""
        if not self.traces:
            return {"error": "Tracing collector not available"}
        
        return {
            "timestamp": datetime.now().isoformat(),
            "traces": self._collect_traces_data(limit, status)
        }

    def get_logs_panel(self, component: str = None,
                      level: str = None,
                      limit: int = 100) -> Dict:
        """Get logs panel data"""
        if not self.logs:
            return {"error": "Log aggregator not available"}
        
        return {
            "timestamp": datetime.now().isoformat(),
            "logs": self._collect_logs_data(component, level, limit)
        }

    def get_health_panel(self) -> Dict:
        """Get health panel data"""
        if not self.health:
            return {"error": "Health manager not available"}
        
        return {
            "timestamp": datetime.now().isoformat(),
            "system_health": self.health.get_system_health()
        }

    def get_alerts_panel(self, severity: str = None,
                        limit: int = 50) -> Dict:
        """Get alerts panel data"""
        if not self.alerts:
            return {"error": "Alert manager not available"}
        
        return {
            "timestamp": datetime.now().isoformat(),
            "statistics": self.alerts.get_alert_statistics(),
            "active_alerts": [
                self._format_alert(a)
                for a in self.alerts.get_active_alerts()[:limit]
            ],
            "open_incidents": [
                self._format_incident(i)
                for i in self.alerts.get_open_incidents()[:10]
            ]
        }

    def get_timeline_data(self, hours: int = 24) -> Dict:
        """Get timeline data for last N hours"""
        timeline = []
        
        for i in range(hours, 0, -1):
            hour_start = datetime.now() - timedelta(hours=i)
            hour_end = datetime.now() - timedelta(hours=i-1)
            
            timeline.append({
                "timestamp": hour_start.isoformat(),
                "metrics_count": self._count_events_in_range(hour_start, hour_end, "metrics"),
                "logs_count": self._count_events_in_range(hour_start, hour_end, "logs"),
                "traces_count": self._count_events_in_range(hour_start, hour_end, "traces"),
                "alerts_count": self._count_events_in_range(hour_start, hour_end, "alerts")
            })
        
        return {
            "timestamp": datetime.now().isoformat(),
            "timeline": timeline
        }

    def get_performance_metrics(self) -> Dict:
        """Get performance metrics"""
        if not self.metrics:
            return {"error": "Metrics collector not available"}
        
        return {
            "timestamp": datetime.now().isoformat(),
            "latency_p50": self.metrics.get_metric_value("request_latency_p50", {}),
            "latency_p95": self.metrics.get_metric_value("request_latency_p95", {}),
            "latency_p99": self.metrics.get_metric_value("request_latency_p99", {}),
            "throughput": self.metrics.get_metric_value("request_throughput", {}),
            "error_rate": self.metrics.get_metric_value("error_rate", {})
        }

    def get_service_status(self) -> Dict:
        """Get service status overview"""
        if not self.health:
            return {"error": "Health manager not available"}
        
        services = {}
        for component, health in self.health.get_all_components_status().items():
            services[component] = {
                "status": health.status,
                "uptime": health.uptime_percent,
                "last_check": health.last_check,
                "last_error": health.last_error
            }
        
        return {
            "timestamp": datetime.now().isoformat(),
            "services": services
        }

    def export_report(self, export_path: str, include_details: bool = True) -> bool:
        """Export complete observability report"""
        try:
            report = {
                "generated_at": datetime.now().isoformat(),
                "dashboard_summary": self.get_dashboard_summary()
            }
            
            if include_details:
                report["metrics"] = self.get_metrics_panel()
                report["traces"] = self.get_traces_panel(limit=20)
                report["logs"] = self.get_logs_panel(limit=50)
                report["health"] = self.get_health_panel()
                report["alerts"] = self.get_alerts_panel(limit=25)
            
            with open(export_path, 'w') as f:
                json.dump(report, f, indent=2, default=str)
            
            return True
        except Exception as e:
            print(f"Error exporting report: {e}")
            return False

    def _get_health_summary(self) -> Dict:
        """Get health summary"""
        if not self.health:
            return {"error": "Health manager not available"}
        
        system_health = self.health.get_system_health()
        return {
            "status": system_health.get("status", "unknown"),
            "healthy_components": system_health.get("healthy_components", 0),
            "degraded_components": system_health.get("degraded_components", 0),
            "unhealthy_components": system_health.get("unhealthy_components", 0),
            "system_availability": system_health.get("system_availability", 0)
        }

    def _get_metrics_summary(self) -> Dict:
        """Get metrics summary"""
        if not self.metrics:
            return {"error": "Metrics collector not available"}
        
        try:
            platform_metrics = self.metrics.get_platform_metrics()
            return {
                "total_metrics": len(platform_metrics.get("metrics", {})),
                "metrics_by_type": self._count_metrics_by_type()
            }
        except:
            return {"error": "Failed to get metrics"}

    def _get_alerts_summary(self) -> Dict:
        """Get alerts summary"""
        if not self.alerts:
            return {"error": "Alert manager not available"}
        
        try:
            stats = self.alerts.get_alert_statistics()
            return {
                "total_alerts": stats.get("total_alerts", 0),
                "triggered": stats.get("triggered", 0),
                "acknowledged": stats.get("acknowledged", 0),
                "critical_count": stats.get("critical_count", 0),
                "open_incidents": stats.get("open_incidents", 0)
            }
        except:
            return {"error": "Failed to get alerts"}

    def _get_logs_summary(self) -> Dict:
        """Get logs summary"""
        if not self.logs:
            return {"error": "Log aggregator not available"}
        
        try:
            stats = self.logs.get_log_statistics()
            return {
                "total_logs": stats.get("total_logs", 0),
                "errors": stats.get("errors", 0),
                "warnings": stats.get("warnings", 0),
                "error_rate": stats.get("error_rate", 0)
            }
        except:
            return {"error": "Failed to get logs"}

    def _get_traces_summary(self) -> Dict:
        """Get traces summary"""
        if not self.traces:
            return {"error": "Tracing collector not available"}
        
        try:
            stats = self.traces.get_tracing_statistics()
            return {
                "total_traces": stats.get("total_traces", 0),
                "completed": stats.get("completed_traces", 0),
                "errors": stats.get("error_traces", 0),
                "error_rate": stats.get("error_rate", 0)
            }
        except:
            return {"error": "Failed to get traces"}

    def _collect_metrics_data(self, metric_name: str = None,
                             time_range_minutes: int = 60) -> List[Dict]:
        """Collect metrics data"""
        try:
            if not self.metrics:
                return []
            
            metrics = []
            platform_metrics = self.metrics.get_platform_metrics()
            
            for metric in platform_metrics.get("metrics", []):
                if metric_name and metric.get("name") != metric_name:
                    continue
                
                stats = self.metrics.get_metric_statistics(
                    metric.get("name"), metric.get("labels", {})
                )
                
                metrics.append({
                    "name": metric.get("name"),
                    "type": metric.get("type"),
                    "value": stats.get("value"),
                    "count": stats.get("count"),
                    "mean": stats.get("mean"),
                    "min": stats.get("min"),
                    "max": stats.get("max"),
                    "p95": stats.get("p95"),
                    "p99": stats.get("p99")
                })
            
            return metrics
        except:
            return []

    def _collect_traces_data(self, limit: int = 50,
                            status: str = None) -> List[Dict]:
        """Collect traces data"""
        try:
            if not self.traces:
                return []
            
            traces = []
            
            # Get traces
            for trace in list(self.traces.traces.values())[:limit]:
                if status and trace.status != status:
                    continue
                
                traces.append({
                    "trace_id": trace.trace_id,
                    "status": trace.status,
                    "duration_ms": trace.duration_ms,
                    "start_time": trace.start_time,
                    "service": trace.service,
                    "span_count": len(trace.spans)
                })
            
            return traces
        except:
            return []

    def _collect_logs_data(self, component: str = None,
                          level: str = None,
                          limit: int = 100) -> List[Dict]:
        """Collect logs data"""
        try:
            if not self.logs:
                return []
            
            logs = []
            all_logs = self.logs.get_logs(
                component=component,
                level=level,
                limit=limit
            )
            
            for log in all_logs:
                logs.append({
                    "timestamp": log.timestamp,
                    "level": log.level,
                    "component": log.component,
                    "message": log.message,
                    "trace_id": log.trace_id
                })
            
            return logs
        except:
            return []

    def _format_alert(self, alert) -> Dict:
        """Format alert for display"""
        return {
            "alert_id": alert.alert_id,
            "rule_name": alert.rule_name,
            "severity": alert.severity,
            "status": alert.status,
            "value": alert.value,
            "timestamp": alert.timestamp,
            "message": alert.message
        }

    def _format_incident(self, incident) -> Dict:
        """Format incident for display"""
        return {
            "incident_id": incident.incident_id,
            "title": incident.title,
            "severity": incident.severity,
            "status": incident.status,
            "alert_count": len(incident.alert_ids),
            "start_time": incident.start_time,
            "assigned_to": incident.assigned_to
        }

    def _count_events_in_range(self, start: datetime, end: datetime,
                              event_type: str) -> int:
        """Count events in time range"""
        count = 0
        
        if event_type == "logs" and self.logs:
            try:
                logs = self.logs.get_logs(limit=1000)
                count = sum(
                    1 for log in logs
                    if start <= datetime.fromisoformat(log.timestamp) <= end
                )
            except:
                pass
        
        elif event_type == "traces" and self.traces:
            try:
                traces = list(self.traces.traces.values())
                count = sum(
                    1 for trace in traces
                    if start <= datetime.fromisoformat(trace.start_time) <= end
                )
            except:
                pass
        
        elif event_type == "alerts" and self.alerts:
            try:
                alerts = self.alerts.get_alert_history(limit=1000)
                count = sum(
                    1 for alert in alerts
                    if start <= datetime.fromisoformat(alert.timestamp) <= end
                )
            except:
                pass
        
        return count

    def _count_metrics_by_type(self) -> Dict:
        """Count metrics by type"""
        counts = {
            "counter": 0,
            "gauge": 0,
            "histogram": 0,
            "summary": 0
        }
        
        if not self.metrics:
            return counts
        
        try:
            platform_metrics = self.metrics.get_platform_metrics()
            for metric in platform_metrics.get("metrics", []):
                metric_type = metric.get("type", "unknown").lower()
                if metric_type in counts:
                    counts[metric_type] += 1
        except:
            pass
        
        return counts


# Global dashboard instance
_dashboard = None

def get_observability_dashboard(metrics_collector=None, log_aggregator=None,
                               tracing_collector=None, health_manager=None,
                               alert_manager=None) -> ObservabilityDashboard:
    """Get or create global observability dashboard"""
    global _dashboard
    if _dashboard is None:
        _dashboard = ObservabilityDashboard(
            metrics_collector, log_aggregator, tracing_collector,
            health_manager, alert_manager
        )
    return _dashboard
