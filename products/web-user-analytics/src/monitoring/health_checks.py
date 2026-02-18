"""
Web User Analytics - Monitoring & Health Checks

Monitors pipeline health, data quality, and performance metrics.
Provides endpoints for health checks and status reporting.
"""

import logging
from typing import Dict, Any, Optional, List
from datetime import datetime, timedelta
from dataclasses import dataclass, asdict
from enum import Enum

from pyspark.sql import SparkSession, DataFrame
from pyspark.sql.functions import col, count, countDistinct, avg


logger = logging.getLogger(__name__)


class HealthStatus(str, Enum):
    """Health status levels"""
    HEALTHY = "healthy"
    WARNING = "warning"
    CRITICAL = "critical"
    UNKNOWN = "unknown"


@dataclass
class HealthCheckResult:
    """Result of a health check"""
    component: str
    status: HealthStatus
    timestamp: datetime
    message: str
    details: Dict[str, Any]


class PipelineHealthMonitor:
    """Monitors data pipeline health"""
    
    def __init__(self, spark: SparkSession, gold_path: str):
        """
        Initialize health monitor.
        
        Args:
            spark: SparkSession
            gold_path: Path to Gold layer
        """
        self.spark = spark
        self.gold_path = gold_path
        self.latest_checks: List[HealthCheckResult] = []
    
    def check_bronze_layer(self, bronze_path: str,
                          hours_back: int = 24) -> HealthCheckResult:
        """
        Check Bronze layer health.
        
        Verifies:
        - Recent data availability
        - Record counts are reasonable
        
        Args:
            bronze_path: Path to Bronze layer
            hours_back: Hours to check back
            
        Returns:
            HealthCheckResult
        """
        try:
            df = self.spark.read.format("delta").load(bronze_path)
            
            # Count recent records
            cutoff = (datetime.utcnow() - timedelta(hours=hours_back)).isoformat()
            recent_count = df.filter(col("timestamp") >= cutoff).count()
            
            if recent_count == 0:
                status = HealthStatus.CRITICAL
                message = f"No Bronze records in last {hours_back} hours"
            elif recent_count < 100:  # Low count threshold
                status = HealthStatus.WARNING
                message = f"Low Bronze record count: {recent_count} in {hours_back}h"
            else:
                status = HealthStatus.HEALTHY
                message = f"Bronze layer healthy with {recent_count} recent records"
            
            return HealthCheckResult(
                component="bronze_layer",
                status=status,
                timestamp=datetime.utcnow(),
                message=message,
                details={
                    "recent_records": recent_count,
                    "hours_checked": hours_back,
                }
            )
        
        except Exception as e:
            logger.error(f"Bronze health check failed: {e}")
            return HealthCheckResult(
                component="bronze_layer",
                status=HealthStatus.UNKNOWN,
                timestamp=datetime.utcnow(),
                message=f"Health check failed: {str(e)}",
                details={"error": str(e)}
            )
    
    def check_silver_layer(self, silver_path: str) -> HealthCheckResult:
        """
        Check Silver layer health.
        
        Verifies:
        - Data exists
        - Valid records vs invalid records ratio
        
        Args:
            silver_path: Path to Silver layer
            
        Returns:
            HealthCheckResult
        """
        try:
            df = self.spark.read.format("delta").load(f"{silver_path}/page_views")
            
            total_count = df.count()
            valid_count = df.filter(col("is_valid") == True).count()
            
            if total_count == 0:
                status = HealthStatus.WARNING
                message = "Silver layer empty"
            else:
                valid_rate = valid_count / total_count
                if valid_rate < 0.8:  # 80% threshold
                    status = HealthStatus.WARNING
                    message = f"Low data quality: {valid_rate*100:.1f}% valid"
                else:
                    status = HealthStatus.HEALTHY
                    message = f"Silver layer healthy with {valid_rate*100:.1f}% valid records"
            
            return HealthCheckResult(
                component="silver_layer",
                status=status,
                timestamp=datetime.utcnow(),
                message=message,
                details={
                    "total_records": total_count,
                    "valid_records": valid_count,
                    "valid_percentage": (valid_count / total_count * 100) if total_count > 0 else 0,
                }
            )
        
        except Exception as e:
            logger.error(f"Silver health check failed: {e}")
            return HealthCheckResult(
                component="silver_layer",
                status=HealthStatus.UNKNOWN,
                timestamp=datetime.utcnow(),
                message=f"Health check failed: {str(e)}",
                details={"error": str(e)}
            )
    
    def check_gold_layer(self) -> HealthCheckResult:
        """
        Check Gold layer health.
        
        Verifies:
        - Metrics tables have recent data
        
        Returns:
            HealthCheckResult
        """
        try:
            df = self.spark.read.format("delta").load(f"{self.gold_path}/page_metrics")
            
            count = df.count()
            
            if count == 0:
                status = HealthStatus.WARNING
                message = "Gold metrics are empty"
            else:
                status = HealthStatus.HEALTHY
                message = f"Gold layer has {count} metric records"
            
            return HealthCheckResult(
                component="gold_layer",
                status=status,
                timestamp=datetime.utcnow(),
                message=message,
                details={"metric_records": count}
            )
        
        except Exception as e:
            logger.error(f"Gold health check failed: {e}")
            return HealthCheckResult(
                component="gold_layer",
                status=HealthStatus.UNKNOWN,
                timestamp=datetime.utcnow(),
                message=f"Health check failed: {str(e)}",
                details={"error": str(e)}
            )
    
    def check_freshness(self, table_path: str,
                       max_age_hours: int = 6) -> HealthCheckResult:
        """
        Check data freshness.
        
        Args:
            table_path: Path to table
            max_age_hours: Maximum acceptable age in hours
            
        Returns:
            HealthCheckResult
        """
        try:
            df = self.spark.read.format("delta").load(table_path)
            
            # Get max timestamp
            latest_ts = df.agg({"timestamp": "max"}).collect()[0][0]
            
            if latest_ts is None:
                status = HealthStatus.CRITICAL
                message = "No data in table"
                age_hours = None
            else:
                age = datetime.utcnow() - latest_ts
                age_hours = age.total_seconds() / 3600
                
                if age_hours > max_age_hours:
                    status = HealthStatus.WARNING
                    message = f"Data is {age_hours:.1f} hours old (max {max_age_hours}h)"
                else:
                    status = HealthStatus.HEALTHY
                    message = f"Data is fresh ({age_hours:.1f} hours old)"
            
            return HealthCheckResult(
                component="data_freshness",
                status=status,
                timestamp=datetime.utcnow(),
                message=message,
                details={"age_hours": age_hours, "max_age_hours": max_age_hours}
            )
        
        except Exception as e:
            logger.error(f"Freshness check failed: {e}")
            return HealthCheckResult(
                component="data_freshness",
                status=HealthStatus.UNKNOWN,
                timestamp=datetime.utcnow(),
                message=f"Check failed: {str(e)}",
                details={"error": str(e)}
            )


class PerformanceMonitor:
    """Monitors analytics query performance"""
    
    def __init__(self):
        """Initialize performance monitor"""
        self.query_times: Dict[str, List[float]] = {}
        self.query_counts: Dict[str, int] = {}
    
    def record_query_time(self, query_name: str, elapsed_seconds: float) -> None:
        """Record query execution time"""
        if query_name not in self.query_times:
            self.query_times[query_name] = []
            self.query_counts[query_name] = 0
        
        self.query_times[query_name].append(elapsed_seconds)
        self.query_counts[query_name] += 1
    
    def get_metrics(self) -> Dict[str, Any]:
        """Get performance metrics"""
        metrics = {}
        
        for query_name, times in self.query_times.items():
            if times:
                metrics[query_name] = {
                    "count": self.query_counts[query_name],
                    "avg_time_ms": sum(times) / len(times) * 1000,
                    "min_time_ms": min(times) * 1000,
                    "max_time_ms": max(times) * 1000,
                    "p99_time_ms": sorted(times)[int(len(times) * 0.99)] * 1000 if len(times) > 100 else max(times) * 1000,
                }
        
        return metrics


class DataQualityMonitor:
    """Monitors data quality metrics"""
    
    def __init__(self, spark: SparkSession):
        """Initialize DQ monitor"""
        self.spark = spark
    
    def check_duplicate_rate(self, df: DataFrame) -> float:
        """
        Calculate duplicate rate.
        
        Args:
            df: DataFrame to check
            
        Returns:
            Duplicate percentage (0-100)
        """
        try:
            total = df.count()
            deduped = df.dropDuplicates().count()
            
            if total == 0:
                return 0.0
            
            return (total - deduped) / total * 100
        
        except Exception as e:
            logger.error(f"Duplicate check failed: {e}")
            return 0.0
    
    def check_null_rate(self, df: DataFrame, column: str) -> float:
        """
        Calculate null rate for column.
        
        Args:
            df: DataFrame
            column: Column name
            
        Returns:
            Null percentage (0-100)
        """
        try:
            total = df.count()
            nulls = df.filter(col(column).isNull()).count()
            
            if total == 0:
                return 0.0
            
            return nulls / total * 100
        
        except Exception as e:
            logger.error(f"Null check failed: {e}")
            return 0.0
    
    def get_quality_report(self, df: DataFrame) -> Dict[str, Any]:
        """Generate data quality report"""
        return {
            "total_records": df.count(),
            "duplicate_rate_%": self.check_duplicate_rate(df),
            "timestamp": datetime.utcnow().isoformat(),
        }


# Global monitors
_health_monitor: Optional[PipelineHealthMonitor] = None
_performance_monitor: Optional[PerformanceMonitor] = None
_dq_monitor: Optional[DataQualityMonitor] = None


def get_health_monitor(spark: SparkSession, gold_path: str) -> PipelineHealthMonitor:
    """Get or create health monitor"""
    global _health_monitor
    if _health_monitor is None:
        _health_monitor = PipelineHealthMonitor(spark, gold_path)
    return _health_monitor


def get_performance_monitor() -> PerformanceMonitor:
    """Get or create performance monitor"""
    global _performance_monitor
    if _performance_monitor is None:
        _performance_monitor = PerformanceMonitor()
    return _performance_monitor


def get_dq_monitor(spark: SparkSession) -> DataQualityMonitor:
    """Get or create data quality monitor"""
    global _dq_monitor
    if _dq_monitor is None:
        _dq_monitor = DataQualityMonitor(spark)
    return _dq_monitor
