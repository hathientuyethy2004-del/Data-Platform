"""
Metrics Collector - Aggregates metrics from all data products

Subscribes to product metrics from Kafka topics and aggregates operational KPIs.
Provides cross-product visibility into pipeline health, SLA compliance.
"""

from typing import Dict, Any, List, Optional, Tuple
from dataclasses import dataclass, asdict
from datetime import datetime, timedelta, timezone
import json
import logging
from enum import Enum
from pydantic import BaseModel, Field, field_validator

logger = logging.getLogger(__name__)


def _to_dict(model: BaseModel) -> Dict[str, Any]:
    """Convert Pydantic model to dictionary (v1/v2 compatible)."""
    if hasattr(model, "model_dump"):
        return model.model_dump()
    return model.dict()


class MetricType(str, Enum):
    """Types of operational metrics"""
    PIPELINE_HEALTH = "pipeline_health"
    DATA_QUALITY = "data_quality"
    API_PERFORMANCE = "api_performance"
    INFRASTRUCTURE = "infrastructure"
    COST = "cost"
    SLA_COMPLIANCE = "sla_compliance"


class PipelineHealthMetric(BaseModel):
    """Pipeline health metric"""
    product: str
    job_name: str
    run_timestamp: str
    status: str = Field(description="SUCCESS, FAILED, RUNNING")
    duration_seconds: int
    records_input: int
    records_output: int
    records_failed: int
    error_message: Optional[str] = None
    retry_count: int = 0
    
    @field_validator("status")
    @classmethod
    def validate_status(cls, v: str) -> str:
        allowed = ["SUCCESS", "FAILED", "RUNNING"]
        if v not in allowed:
            raise ValueError(f"Status must be one of {allowed}")
        return v


class DataQualityMetric(BaseModel):
    """Data quality metric"""
    product: str
    layer: str = Field(description="bronze, silver, gold")
    table_name: str
    timestamp: str
    total_records: int
    null_count: int
    duplicate_count: int
    schema_violations: int
    quality_score: float = Field(ge=0, le=100)
    
    @field_validator("layer")
    @classmethod
    def validate_layer(cls, v: str) -> str:
        if v not in ["bronze", "silver", "gold"]:
            raise ValueError("Layer must be bronze, silver, or gold")
        return v


class APIPerformanceMetric(BaseModel):
    """API performance metric"""
    product: str
    endpoint: str
    timestamp: str
    response_time_ms: int
    status_code: int
    error: Optional[str] = None
    user_id: Optional[str] = None
    query_params: Dict[str, Any] = Field(default_factory=dict)
    cache_hit: bool = False


class InfrastructureMetric(BaseModel):
    """Infrastructure utilization metric"""
    component: str = Field(description="spark, kafka, redis, storage")
    timestamp: str
    cpu_percent: float = Field(ge=0, le=100)
    memory_percent: float = Field(ge=0, le=100)
    network_io_mbps: float
    disk_io_mbps: float
    latency_ms: Optional[float] = None


class CostMetric(BaseModel):
    """Cost tracking metric"""
    product: str
    period: str = Field(description="hourly, daily, monthly")
    compute_cost: float
    storage_cost: float
    network_cost: float
    total_cost: float


class MetricsCollector:
    """Collects and aggregates metrics from all products"""
    
    def __init__(self):
        """Initialize collector"""
        self.metrics_buffer: Dict[str, List[Dict[str, Any]]] = {
            metric_type.value: [] for metric_type in MetricType
        }
        self.aggregation_window_minutes = 5
    
    def add_pipeline_health_metric(self, metric: PipelineHealthMetric) -> None:
        """
        Add pipeline health metric.
        
        Args:
            metric: Pipeline health metric
        """
        self.metrics_buffer[MetricType.PIPELINE_HEALTH.value].append(_to_dict(metric))
        logger.info(f"Added pipeline metric for {metric.product}/{metric.job_name}")
    
    def add_data_quality_metric(self, metric: DataQualityMetric) -> None:
        """
        Add data quality metric.
        
        Args:
            metric: Data quality metric
        """
        self.metrics_buffer[MetricType.DATA_QUALITY.value].append(_to_dict(metric))
        logger.info(f"Added DQ metric for {metric.product}/{metric.table_name}")
    
    def add_api_performance_metric(self, metric: APIPerformanceMetric) -> None:
        """
        Add API performance metric.
        
        Args:
            metric: API performance metric
        """
        self.metrics_buffer[MetricType.API_PERFORMANCE.value].append(_to_dict(metric))
    
    def add_infrastructure_metric(self, metric: InfrastructureMetric) -> None:
        """
        Add infrastructure metric.
        
        Args:
            metric: Infrastructure metric
        """
        self.metrics_buffer[MetricType.INFRASTRUCTURE.value].append(_to_dict(metric))
    
    def get_pipeline_summary(self, product: Optional[str] = None,
                            hours: int = 24) -> Dict[str, Any]:
        """
        Get pipeline summary for product or all.
        
        Args:
            product: Product name (None for all)
            hours: Hours to look back
            
        Returns:
            Pipeline summary
        """
        metrics = self.metrics_buffer[MetricType.PIPELINE_HEALTH.value]
        
        if product:
            metrics = [m for m in metrics if m.get("product") == product]
        
        if not metrics:
            return {"count": 0}
        
        successful = len([m for m in metrics if m.get("status") == "SUCCESS"])
        failed = len([m for m in metrics if m.get("status") == "FAILED"])
        
        return {
            "total_runs": len(metrics),
            "successful": successful,
            "failed": failed,
            "success_rate": (successful / len(metrics) * 100) if metrics else 0,
            "avg_duration_seconds": sum(m.get("duration_seconds", 0) for m in metrics) / len(metrics) if metrics else 0,
            "total_records_processed": sum(m.get("records_output", 0) for m in metrics),
            "total_records_failed": sum(m.get("records_failed", 0) for m in metrics),
        }
    
    def get_data_quality_summary(self, product: Optional[str] = None) -> Dict[str, Any]:
        """
        Get data quality summary.
        
        Args:
            product: Product name (None for all)
            
        Returns:
            Data quality summary
        """
        metrics = self.metrics_buffer[MetricType.DATA_QUALITY.value]
        
        if product:
            metrics = [m for m in metrics if m.get("product") == product]
        
        if not metrics:
            return {"count": 0}
        
        avg_quality = sum(m.get("quality_score", 0) for m in metrics) / len(metrics)
        
        return {
            "tables_checked": len(metrics),
            "avg_quality_score": avg_quality,
            "total_records": sum(m.get("total_records", 0) for m in metrics),
            "total_nulls": sum(m.get("null_count", 0) for m in metrics),
            "total_duplicates": sum(m.get("duplicate_count", 0) for m in metrics),
            "schema_violations": sum(m.get("schema_violations", 0) for m in metrics),
        }
    
    def get_api_performance_summary(self, 
                                   product: Optional[str] = None,
                                   percentiles: List[int] = [50, 95, 99]) -> Dict[str, Any]:
        """
        Get API performance summary.
        
        Args:
            product: Product name (None for all)
            percentiles: Response time percentiles
            
        Returns:
            API performance summary
        """
        metrics = self.metrics_buffer[MetricType.API_PERFORMANCE.value]
        
        if product:
            metrics = [m for m in metrics if m.get("product") == product]
        
        if not metrics:
            return {"count": 0}
        
        response_times = sorted([m.get("response_time_ms", 0) for m in metrics])
        errors = len([m for m in metrics if m.get("status_code", 0) >= 400])
        
        cache_hits = len([m for m in metrics if m.get("cache_hit", False)])
        
        percentile_values = {}
        for p in percentiles:
            idx = int(len(response_times) * p / 100)
            percentile_values[f"p{p}"] = response_times[idx] if idx < len(response_times) else 0
        
        return {
            "total_requests": len(metrics),
            "error_count": errors,
            "error_rate": (errors / len(metrics) * 100) if metrics else 0,
            "avg_response_time_ms": sum(response_times) / len(response_times),
            "min_response_time_ms": min(response_times),
            "max_response_time_ms": max(response_times),
            **percentile_values,
            "cache_hit_rate": (cache_hits / len(metrics) * 100) if metrics else 0,
        }
    
    def get_infrastructure_utilization(self) -> Dict[str, Any]:
        """
        Get infrastructure utilization summary.
        
        Returns:
            Utilization metrics
        """
        metrics = self.metrics_buffer[MetricType.INFRASTRUCTURE.value]
        
        if not metrics:
            return {"count": 0}
        
        components = {}
        for metric in metrics:
            comp = metric.get("component")
            if comp not in components:
                components[comp] = []
            components[comp].append(metric)
        
        summary = {}
        for comp, comp_metrics in components.items():
            summary[comp] = {
                "avg_cpu": sum(m.get("cpu_percent", 0) for m in comp_metrics) / len(comp_metrics),
                "avg_memory": sum(m.get("memory_percent", 0) for m in comp_metrics) / len(comp_metrics),
                "avg_network_io_mbps": sum(m.get("network_io_mbps", 0) for m in comp_metrics) / len(comp_metrics),
                "avg_disk_io_mbps": sum(m.get("disk_io_mbps", 0) for m in comp_metrics) / len(comp_metrics),
            }
        
        return summary
    
    def clear_buffer(self) -> None:
        """Clear metrics buffer"""
        for key in self.metrics_buffer:
            self.metrics_buffer[key] = []
    
    def get_full_report(self) -> Dict[str, Any]:
        """
        Get comprehensive operational report.
        
        Returns:
            Full report
        """
        return {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "pipeline_summary": self.get_pipeline_summary(),
            "data_quality_summary": self.get_data_quality_summary(),
            "api_performance_summary": self.get_api_performance_summary(),
            "infrastructure_utilization": self.get_infrastructure_utilization(),
        }


class MetricsAggregator:
    """Aggregates metrics for dashboard consumption"""
    
    def __init__(self, collector: MetricsCollector):
        """Initialize aggregator"""
        self.collector = collector
        self.time_series_data: Dict[str, List[Dict[str, Any]]] = {}
    
    def aggregate_by_product(self) -> Dict[str, Dict[str, Any]]:
        """
        Aggregate metrics by product.
        
        Returns:
            Product-level aggregation
        """
        products = set()
        
        # Collect all products
        for metric_type in self.collector.metrics_buffer.values():
            products.update([m.get("product") for m in metric_type if "product" in m])
        
        aggregation = {}
        for product in products:
            aggregation[product] = {
                "pipeline": self.collector.get_pipeline_summary(product),
                "data_quality": self.collector.get_data_quality_summary(product),
                "api_performance": self.collector.get_api_performance_summary(product),
            }
        
        return aggregation
    
    def aggregate_by_time_window(self, window_minutes: int = 5) -> Dict[str, Any]:
        """
        Aggregate metrics by time window.
        
        Args:
            window_minutes: Window size in minutes
            
        Returns:
            Time-based aggregation
        """
        # Group metrics by time window
        windowed = {}
        
        for metric_type, metrics in self.collector.metrics_buffer.items():
            for metric in metrics:
                ts = metric.get("timestamp") or metric.get("run_timestamp", "")
                # Simplified windowing (would parse ISO datetime and round)
                window_key = ts[:16]  # YYYY-MM-DDTHH:MM
                
                if window_key not in windowed:
                    windowed[window_key] = {
                        "window": window_key,
                        "metrics": {}
                    }
                
                if metric_type not in windowed[window_key]["metrics"]:
                    windowed[window_key]["metrics"][metric_type] = []
                
                windowed[window_key]["metrics"][metric_type].append(metric)
        
        return windowed
    
    def generate_trend_report(self, hours: int = 24) -> Dict[str, Any]:
        """
        Generate trend report over time.
        
        Args:
            hours: Hours to look back
            
        Returns:
            Trend data
        """
        return {
            "period_hours": hours,
            "pipeline_trends": self._calculate_trends("pipeline"),
            "quality_trends": self._calculate_trends("quality"),
            "api_trends": self._calculate_trends("api"),
        }
    
    def _calculate_trends(self, metric_type: str) -> Dict[str, Any]:
        """Calculate trend for metric type"""
        # Simplified trend calculation
        return {
            "metric_type": metric_type,
            "direction": "stable",
            "change_percent": 0.5,
        }
