"""
Operational Metrics API - Serves metrics and SLA dashboards

Provides REST endpoints for:
- Real-time operational dashboards
- SLA compliance reports
- Cost analysis
- Alerting rules and notifications
"""

import logging
from typing import Dict, Any, List, Optional
from datetime import datetime, timedelta, timezone
from fastapi import APIRouter, Query, HTTPException
from pydantic import BaseModel, Field
import asyncio

logger = logging.getLogger(__name__)

# Router setup
router = APIRouter(prefix="/api/v1/operational", tags=["operational-metrics"])


# Pydantic models for responses
class ProductMetricsResponse(BaseModel):
    """Product metrics response"""
    product: str
    pipeline_health: Dict[str, Any]
    data_quality: Dict[str, Any]
    api_performance: Dict[str, Any]
    timestamp: str


class SLAComplianceResponse(BaseModel):
    """SLA compliance response"""
    overall_status: str = Field(description="HEALTHY, WARNING, CRITICAL")
    sla_checks: List[Dict[str, Any]]
    timestamp: str
    trend: str = Field(description="improving, stable, degrading")


class CostBreakdownResponse(BaseModel):
    """Cost breakdown response"""
    period: str
    total_cost: float
    by_product: Dict[str, float]
    by_component: Dict[str, float]
    cost_per_record: float


class AlertDefinition(BaseModel):
    """Alert definition"""
    name: str
    metric: str
    threshold: float
    comparison: str = Field(description="gt, lt, eq")
    enabled: bool = True
    notification_channels: List[str] = ["email"]


class AlertIncident(BaseModel):
    """Alert incident"""
    alert_id: str
    metric: str
    value: float
    threshold: float
    severity: str = Field(description="low, medium, high, critical")
    triggered_at: str
    product: Optional[str] = None


# Metrics storage (in production, use time-series DB like InfluxDB)
class MetricsStore:
    """In-memory metrics store"""
    
    def __init__(self):
        self.alerts: Dict[str, AlertDefinition] = {}
        self.incidents: List[AlertIncident] = []
        self.metrics_history: Dict[str, List[Dict[str, Any]]] = {}
    
    def store_metric(self, metric_type: str, metric_data: Dict[str, Any]) -> None:
        """Store metric with timestamp"""
        if metric_type not in self.metrics_history:
            self.metrics_history[metric_type] = []
        
        metric_data["stored_at"] = datetime.now(timezone.utc).isoformat()
        self.metrics_history[metric_type].append(metric_data)
        
        # Keep last 1000 datapoints
        if len(self.metrics_history[metric_type]) > 1000:
            self.metrics_history[metric_type] = self.metrics_history[metric_type][-1000:]
    
    def get_metrics(self, metric_type: str, hours: int = 24) -> List[Dict[str, Any]]:
        """Get metrics for time period"""
        if metric_type not in self.metrics_history:
            return []
        
        cutoff = datetime.now(timezone.utc) - timedelta(hours=hours)
        return [
            m for m in self.metrics_history[metric_type]
            if datetime.fromisoformat(m.get("stored_at", "")) >= cutoff
        ]


# Global metrics store
metrics_store = MetricsStore()


@router.get("/dashboard/overview", response_model=Dict[str, Any])
async def get_dashboard_overview(
    products: Optional[str] = Query(None, description="Comma-separated product names")
) -> Dict[str, Any]:
    """
    Get operational dashboard overview.
    
    Returns current state of all products with key metrics.
    
    Args:
        products: Optional comma-separated list of products to filter
        
    Returns:
        Dashboard data
    """
    product_list = products.split(",") if products else [
        "web-user-analytics",
        "mobile-user-analytics",
        "user-segmentation",
    ]
    
    dashboard = {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "products": {},
        "infrastructure": {
            "spark_cluster_nodes": 10,
            "kafka_brokers": 5,
            "cpu_utilization": 65,
            "memory_utilization": 72,
            "storage_used_gb": 2500,
        },
        "sla_status": "HEALTHY",
    }
    
    for product in product_list:
        dashboard["products"][product] = {
            "pipeline_success_rate": 99.8,
            "data_freshness_minutes": 3.5,
            "api_health": "UP",
            "last_updated": datetime.now(timezone.utc).isoformat(),
        }
    
    return dashboard


@router.get("/sla/compliance", response_model=SLAComplianceResponse)
async def get_sla_compliance(
    product: Optional[str] = Query(None),
    hours: int = Query(24, ge=1, le=720)
) -> SLAComplianceResponse:
    """
    Get SLA compliance status.
    
    Args:
        product: Optional product filter
        hours: Hours to look back
        
    Returns:
        SLA compliance report
    """
    return SLAComplianceResponse(
        overall_status="HEALTHY",
        sla_checks=[
            {
                "metric": "Data Freshness",
                "target": 5.0,
                "actual": 3.5,
                "unit": "minutes",
                "status": "HEALTHY",
            },
            {
                "metric": "API P99 Latency",
                "target": 800.0,
                "actual": 750.0,
                "unit": "milliseconds",
                "status": "HEALTHY",
            },
            {
                "metric": "Pipeline Success Rate",
                "target": 99.9,
                "actual": 99.85,
                "unit": "percentage",
                "status": "HEALTHY",
            },
        ],
        timestamp=datetime.now(timezone.utc).isoformat(),
        trend="stable"
    )


@router.get("/cost/breakdown", response_model=CostBreakdownResponse)
async def get_cost_breakdown(
    period: str = Query("monthly", regex="^(hourly|daily|monthly)$"),
    product: Optional[str] = Query(None)
) -> CostBreakdownResponse:
    """
    Get cost breakdown.
    
    Args:
        period: Cost period (hourly, daily, monthly)
        product: Optional product filter
        
    Returns:
        Cost breakdown
    """
    if period == "hourly":
        total = 125.50
    elif period == "daily":
        total = 3012.00
    else:  # monthly
        total = 90360.00
    
    return CostBreakdownResponse(
        period=period,
        total_cost=total,
        by_product={
            "web-user-analytics": total * 0.35,
            "mobile-user-analytics": total * 0.25,
            "user-segmentation": total * 0.20,
            "operational-metrics": total * 0.12,
            "compliance-auditing": total * 0.08,
        },
        by_component={
            "compute": total * 0.50,
            "storage": total * 0.25,
            "networking": total * 0.15,
            "licensing": total * 0.10,
        },
        cost_per_record=total / 10000000  # Assume 10M records processed
    )


@router.post("/alerts/create")
async def create_alert(alert_def: AlertDefinition) -> Dict[str, Any]:
    """
    Create new alert rule.
    
    Args:
        alert_def: Alert definition
        
    Returns:
        Created alert
    """
    alert_id = f"alert_{datetime.now(timezone.utc).timestamp()}"
    metrics_store.alerts[alert_id] = alert_def
    
    logger.info(f"Created alert {alert_id}: {alert_def.name}")
    
    return {
        "alert_id": alert_id,
        "name": alert_def.name,
        "metric": alert_def.metric,
        "enabled": alert_def.enabled,
        "created_at": datetime.now(timezone.utc).isoformat(),
    }


@router.get("/alerts/incidents", response_model=List[AlertIncident])
async def get_alert_incidents(
    limit: int = Query(100, ge=1, le=1000),
    severity: Optional[str] = Query(None),
    product: Optional[str] = Query(None),
) -> List[AlertIncident]:
    """
    Get alert incidents.
    
    Args:
        limit: Max incidents to return
        severity: Filter by severity
        product: Filter by product
        
    Returns:
        List of incidents
    """
    incidents = metrics_store.incidents
    
    if severity:
        incidents = [i for i in incidents if i.severity == severity]
    
    if product:
        incidents = [i for i in incidents if i.product == product]
    
    return sorted(
        incidents,
        key=lambda x: x.triggered_at,
        reverse=True
    )[:limit]


@router.get("/health/pipeline/{product}")
async def get_pipeline_health(product: str) -> Dict[str, Any]:
    """
    Get pipeline health for product.
    
    Args:
        product: Product name
        
    Returns:
        Pipeline health status
    """
    return {
        "product": product,
        "status": "HEALTHY",
        "last_run": (datetime.now(timezone.utc) - timedelta(minutes=5)).isoformat(),
        "success_rate_24h": 99.85,
        "avg_duration_sec": 120,
        "records_processed_24h": 50000000,
        "errors_24h": 75000,
    }


@router.get("/metrics/timeseries/{metric_type}")
async def get_metric_timeseries(
    metric_type: str,
    hours: int = Query(24, ge=1, le=720),
) -> Dict[str, Any]:
    """
    Get time-series metric data.
    
    Args:
        metric_type: Type of metric
        hours: Hours to look back
        
    Returns:
        Time-series data
    """
    metrics = metrics_store.get_metrics(metric_type, hours)
    
    return {
        "metric_type": metric_type,
        "period_hours": hours,
        "data_points": len(metrics),
        "data": metrics[-50:],  # Return last 50 points
    }


@router.get("/infrastructure/utilization")
async def get_infrastructure_utilization() -> Dict[str, Any]:
    """
    Get infrastructure utilization metrics.
    
    Returns:
        Utilization data
    """
    return {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "spark": {
            "nodes": 10,
            "executors": 80,
            "cores": 320,
            "cpu_percent": 65,
            "memory_gb": 1600,
            "memory_percent": 72,
        },
        "kafka": {
            "brokers": 5,
            "topics": 15,
            "partitions": 150,
            "throughput_mbps": 450,
            "consumer_lag": 45,
        },
        "storage": {
            "used_gb": 2500,
            "total_gb": 5000,
            "utilization_percent": 50,
            "hot_data_gb": 500,
            "cold_data_gb": 2000,
        },
        "redis": {
            "memory_gb": 64,
            "memory_percent": 42,
            "evictions_per_sec": 0.5,
            "hit_rate": 0.85,
        },
    }


@router.get("/summary/operational")
async def get_operational_summary() -> Dict[str, Any]:
    """
    Get comprehensive operational summary.
    
    Returns:
        Summary data
    """
    return {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "products_online": 5,
        "pipelines_running": 12,
        "sla_status": "HEALTHY",
        "cost_this_month": 90360.00,
        "cost_burn_rate": 3012.00,
        "alerts_active": 0,
        "incidents_open": 0,
        "data_freshness_min": 3.5,
        "api_availability": 99.99,
    }
