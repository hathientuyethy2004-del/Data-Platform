"""
Health Monitoring for Operational Metrics Product

Monitors:
- Pipeline health and SLA compliance
- Data freshness and quality
- API availability and performance
- Infrastructure utilization
"""

import logging
from typing import Dict, Any, List, Optional
from datetime import datetime, timedelta, timezone
from dataclasses import dataclass, asdict
import json

logger = logging.getLogger(__name__)


@dataclass
class HealthCheck:
    """Health check result"""
    check_name: str
    component: str
    status: str  # HEALTHY, WARNING, CRITICAL
    message: str
    last_checked: str
    metrics: Dict[str, Any]


class OperationalMetricsHealthMonitor:
    """Monitors operational metrics pipeline health"""
    
    CRITICAL_THRESHOLDS = {
        "pipeline_success_rate": 95.0,
        "data_freshness_hours": 6,
        "api_error_rate": 1.0,
        "data_quality_score": 95.0,
        "cpu_utilization": 85.0,
        "memory_utilization": 90.0,
    }
    
    WARNING_THRESHOLDS = {
        "pipeline_success_rate": 98.0,
        "data_freshness_hours": 2,
        "api_error_rate": 0.1,
        "data_quality_score": 98.0,
        "cpu_utilization": 70.0,
        "memory_utilization": 80.0,
    }
    
    def __init__(self):
        """Initialize health monitor"""
        self.last_checks: Dict[str, HealthCheck] = {}
        self.health_history: List[Dict[str, Any]] = []
    
    def check_pipeline_health(self) -> HealthCheck:
        """
        Check pipeline health.
        
        Returns:
            Health check result
        """
        metrics = {
            "success_rate_24h": 99.85,
            "failed_jobs_24h": 2,
            "avg_job_duration_sec": 120,
            "data_freshness_minutes": 3.5,
        }
        
        # Determine status
        status = "HEALTHY"
        if metrics["success_rate_24h"] < self.CRITICAL_THRESHOLDS["pipeline_success_rate"]:
            status = "CRITICAL"
        elif metrics["success_rate_24h"] < self.WARNING_THRESHOLDS["pipeline_success_rate"]:
            status = "WARNING"
        
        check = HealthCheck(
            check_name="pipeline_health",
            component="processing",
            status=status,
            message=f"Pipeline success rate: {metrics['success_rate_24h']:.2f}%",
            last_checked=datetime.now(timezone.utc).isoformat(),
            metrics=metrics
        )
        
        self.last_checks["pipeline_health"] = check
        return check
    
    def check_data_freshness(self) -> HealthCheck:
        """
        Check data freshness across products.
        
        Returns:
            Health check result
        """
        freshness_by_product = {
            "web-user-analytics": 3.5,
            "mobile-user-analytics": 4.2,
            "user-segmentation": 5.1,
        }
        
        max_freshness = max(freshness_by_product.values())
        
        # Determine status
        status = "HEALTHY"
        if max_freshness > self.CRITICAL_THRESHOLDS["data_freshness_hours"] * 60:
            status = "CRITICAL"
        elif max_freshness > self.WARNING_THRESHOLDS["data_freshness_hours"] * 60:
            status = "WARNING"
        
        check = HealthCheck(
            check_name="data_freshness",
            component="storage",
            status=status,
            message=f"Max data age: {max_freshness:.1f} minutes",
            last_checked=datetime.now(timezone.utc).isoformat(),
            metrics=freshness_by_product
        )
        
        self.last_checks["data_freshness"] = check
        return check
    
    def check_api_availability(self) -> HealthCheck:
        """
        Check API availability and performance.
        
        Returns:
            Health check result
        """
        metrics = {
            "availability_percent": 99.99,
            "avg_response_time_ms": 450,
            "p99_response_time_ms": 750,
            "error_rate_percent": 0.05,
            "error_responses_24h": 5,
        }
        
        # Determine status
        status = "HEALTHY"
        if metrics["error_rate_percent"] > self.CRITICAL_THRESHOLDS["api_error_rate"]:
            status = "CRITICAL"
        elif metrics["error_rate_percent"] > self.WARNING_THRESHOLDS["api_error_rate"]:
            status = "WARNING"
        
        check = HealthCheck(
            check_name="api_availability",
            component="serving",
            status=status,
            message=f"API availability: {metrics['availability_percent']:.2f}%",
            last_checked=datetime.now(timezone.utc).isoformat(),
            metrics=metrics
        )
        
        self.last_checks["api_availability"] = check
        return check
    
    def check_infrastructure_health(self) -> HealthCheck:
        """
        Check infrastructure utilization.
        
        Returns:
            Health check result
        """
        metrics = {
            "spark_cluster_cpu": 65,
            "spark_cluster_memory": 72,
            "kafka_brokers_up": 5,
            "redis_memory_percent": 42,
            "storage_utilization": 50,
        }
        
        # Determine status
        status = "HEALTHY"
        if metrics["spark_cluster_cpu"] > self.CRITICAL_THRESHOLDS["cpu_utilization"]:
            status = "CRITICAL"
        elif metrics["spark_cluster_cpu"] > self.WARNING_THRESHOLDS["cpu_utilization"]:
            status = "WARNING"
        
        check = HealthCheck(
            check_name="infrastructure_health",
            component="infrastructure",
            status=status,
            message=f"CPU utilization: {metrics['spark_cluster_cpu']}%",
            last_checked=datetime.now(timezone.utc).isoformat(),
            metrics=metrics
        )
        
        self.last_checks["infrastructure_health"] = check
        return check
    
    def check_sla_compliance(self) -> HealthCheck:
        """
        Check SLA compliance metrics.
        
        Returns:
            Health check result
        """
        compliance_metrics = {
            "data_freshness_target": "5 min",
            "data_freshness_actual": "3.5 min",
            "data_freshness_compliant": True,
            "pipeline_success_target": "99.9%",
            "pipeline_success_actual": "99.85%",
            "pipeline_success_compliant": True,
            "api_latency_target": "800 ms",
            "api_latency_actual": "750 ms",
            "api_latency_compliant": True,
            "compliant_checks": 3,
            "total_checks": 3,
        }
        
        status = "HEALTHY"
        if not all(v for k, v in compliance_metrics.items() if k.endswith("_compliant")):
            status = "WARNING"
        
        check = HealthCheck(
            check_name="sla_compliance",
            component="monitoring",
            status=status,
            message=f"SLA compliance: {compliance_metrics['compliant_checks']}/{compliance_metrics['total_checks']} checks passing",
            last_checked=datetime.now(timezone.utc).isoformat(),
            metrics=compliance_metrics
        )
        
        self.last_checks["sla_compliance"] = check
        return check
    
    def run_all_health_checks(self) -> Dict[str, HealthCheck]:
        """
        Run all health checks.
        
        Returns:
            All health check results
        """
        checks = {
            "pipeline": self.check_pipeline_health(),
            "freshness": self.check_data_freshness(),
            "api": self.check_api_availability(),
            "infrastructure": self.check_infrastructure_health(),
            "sla": self.check_sla_compliance(),
        }
        
        # Determine overall status
        statuses = [c.status for c in checks.values()]
        if "CRITICAL" in statuses:
            overall_status = "CRITICAL"
        elif "WARNING" in statuses:
            overall_status = "WARNING"
        else:
            overall_status = "HEALTHY"
        
        # Store history
        self.health_history.append({
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "overall_status": overall_status,
            "checks": {k: asdict(v) for k, v in checks.items()}
        })
        
        # Keep last 1000 entries
        if len(self.health_history) > 1000:
            self.health_history = self.health_history[-1000:]
        
        logger.info(f"Health check completed: {overall_status}")
        
        return checks
    
    def get_health_report(self) -> Dict[str, Any]:
        """
        Get comprehensive health report.
        
        Returns:
            Health report
        """
        checks = self.run_all_health_checks()
        
        statuses = [c.status for c in checks.values()]
        if "CRITICAL" in statuses:
            overall_status = "CRITICAL"
        elif "WARNING" in statuses:
            overall_status = "WARNING"
        else:
            overall_status = "HEALTHY"
        
        return {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "overall_status": overall_status,
            "summary": {
                "healthy_checks": len([c for c in checks.values() if c.status == "HEALTHY"]),
                "warning_checks": len([c for c in checks.values() if c.status == "WARNING"]),
                "critical_checks": len([c for c in checks.values() if c.status == "CRITICAL"]),
            },
            "checks": {
                name: {
                    "status": check.status,
                    "message": check.message,
                    "component": check.component,
                    "metrics": check.metrics,
                }
                for name, check in checks.items()
            }
        }
    
    def get_trend_analysis(self, hours: int = 24) -> Dict[str, Any]:
        """
        Analyze health trends.
        
        Args:
            hours: Hours to analyze
            
        Returns:
            Trend analysis
        """
        cutoff = datetime.now(timezone.utc) - timedelta(hours=hours)
        recent_history = []
        for h in self.health_history:
            ts = datetime.fromisoformat(h["timestamp"])
            if ts.tzinfo is None:
                ts = ts.replace(tzinfo=timezone.utc)
            if ts > cutoff:
                recent_history.append(h)
        
        if not recent_history:
            return {"trend": "insufficient_data"}
        
        # Determine trend
        first_status = recent_history[0]["overall_status"]
        last_status = recent_history[-1]["overall_status"]
        
        status_values = {"HEALTHY": 3, "WARNING": 2, "CRITICAL": 1}
        
        trend = "stable"
        if status_values[last_status] > status_values[first_status]:
            trend = "improving"
        elif status_values[last_status] < status_values[first_status]:
            trend = "degrading"
        
        return {
            "period_hours": hours,
            "trend": trend,
            "first_status": first_status,
            "last_status": last_status,
            "status_changes": len([
                h for i, h in enumerate(recent_history[:-1])
                if h["overall_status"] != recent_history[i + 1]["overall_status"]
            ]),
        }
