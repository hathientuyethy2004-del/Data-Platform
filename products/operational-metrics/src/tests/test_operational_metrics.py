"""
Tests for Operational Metrics product

Test coverage:
- KPI calculations (SLA, cost, pipeline metrics)
- Metrics collection and aggregation
- Health monitoring
- Alert detection
"""

import pytest
from datetime import datetime, timedelta
from unittest.mock import Mock, patch, MagicMock

from src.ingestion.metrics_collector import (
    MetricsCollector, PipelineHealthMetric, DataQualityMetric,
    APIPerformanceMetric, InfrastructureMetric, MetricsAggregator
)
from src.processing.kpi_engine import (
    OperationalMetricsCalculator, SLAMonitor, OperationalDashboard,
    CostAnalyzer
)
from src.monitoring.health_checks import OperationalMetricsHealthMonitor


class TestMetricsCollector:
    """Tests for metrics collection"""
    
    @pytest.fixture
    def collector(self):
        return MetricsCollector()
    
    def test_add_pipeline_health_metric(self, collector):
        """Test adding pipeline health metric"""
        metric = PipelineHealthMetric(
            product="test-product",
            job_name="test_job",
            run_timestamp="2024-02-18T12:00:00Z",
            status="SUCCESS",
            duration_seconds=120,
            records_input=1000000,
            records_output=900000,
            records_failed=1000,
        )
        
        collector.add_pipeline_health_metric(metric)
        
        assert len(collector.metrics_buffer["pipeline_health"]) == 1
    
    def test_add_data_quality_metric(self, collector):
        """Test adding data quality metric"""
        metric = DataQualityMetric(
            product="test",
            layer="silver",
            table_name="users",
            timestamp="2024-02-18T12:00:00Z",
            total_records=1000000,
            null_count=500,
            duplicate_count=100,
            schema_violations=50,
            quality_score=99.5,
        )
        
        collector.add_data_quality_metric(metric)
        
        assert len(collector.metrics_buffer["data_quality"]) == 1
    
    def test_pipeline_summary(self, collector):
        """Test pipeline summary calculation"""
        for i in range(5):
            metric = PipelineHealthMetric(
                product="test",
                job_name=f"job_{i}",
                run_timestamp=f"2024-02-18T12:{i:02d}:00Z",
                status="SUCCESS" if i < 4 else "FAILED",
                duration_seconds=100 + i * 10,
                records_input=1000000,
                records_output=900000,
                records_failed=1000 if i < 4 else 100000,
            )
            collector.add_pipeline_health_metric(metric)
        
        summary = collector.get_pipeline_summary("test")
        
        assert summary["total_runs"] == 5
        assert summary["successful"] == 4
        assert summary["failed"] == 1
        assert summary["success_rate"] == 80.0
    
    def test_data_quality_summary(self, collector):
        """Test data quality summary"""
        for i in range(3):
            metric = DataQualityMetric(
                product="test",
                layer="gold",
                table_name=f"table_{i}",
                timestamp="2024-02-18T12:00:00Z",
                total_records=1000000,
                null_count=1000,
                duplicate_count=100,
                schema_violations=10,
                quality_score=99.0,
            )
            collector.add_data_quality_metric(metric)
        
        summary = collector.get_data_quality_summary("test")
        
        assert summary["tables_checked"] == 3
        assert summary["avg_quality_score"] == 99.0


class TestSLAMonitor:
    """Tests for SLA monitoring"""
    
    @pytest.fixture
    def monitor(self):
        return SLAMonitor()
    
    def test_sla_compliance_healthy(self, monitor):
        """Test SLA compliance check - healthy"""
        result = monitor.check_sla_compliance("data_freshness_minutes", 3.0)
        
        assert result["status"] == "HEALTHY"
        assert result["metric"] == "data_freshness_minutes"
    
    def test_sla_compliance_warning(self, monitor):
        """Test SLA compliance check - warning"""
        result = monitor.check_sla_compliance("api_p99_latency_ms", 1200.0)
        
        assert result["status"] == "WARNING"
    
    def test_sla_compliance_critical(self, monitor):
        """Test SLA compliance check - critical"""
        result = monitor.check_sla_compliance("pipeline_success_rate", 94.0)
        
        assert result["status"] == "CRITICAL"
    
    def test_sla_report_mixed(self, monitor):
        """Test SLA report with mixed statuses"""
        metrics = {
            "data_freshness_minutes": 3.5,
            "api_p99_latency_ms": 750,
            "pipeline_success_rate": 99.85,
            "data_quality_score": 99.6,
        }
        
        report = monitor.get_sla_report(metrics)
        
        assert "sla_checks" in report
        assert len(report["sla_checks"]) == 4
        assert report["overall_status"] == "HEALTHY"


class TestCostAnalyzer:
    """Tests for cost analysis"""
    
    def test_monthly_cost_estimation(self):
        """Test cost estimation"""
        costs = CostAnalyzer.estimate_monthly_cost(
            spark_executors=80,
            kafka_brokers=5,
            storage_gb=2500
        )
        
        assert costs["spark_compute"] > 0
        assert costs["kafka_streaming"] > 0
        assert costs["storage"] > 0
        assert costs["total_monthly"] > 0
    
    def test_cost_allocation(self):
        """Test cost allocation by product"""
        metrics = {
            "product_a": {"records_processed_daily": 2000000},
            "product_b": {"records_processed_daily": 3000000},
            "product_c": {"records_processed_daily": 5000000},
        }
        
        costs = CostAnalyzer.analyze_cost_per_product(metrics)
        
        assert len(costs) == 3
        assert costs["product_a"] < costs["product_b"] < costs["product_c"]


class TestOperationalMetricsHealthMonitor:
    """Tests for health monitoring"""
    
    @pytest.fixture
    def monitor(self):
        return OperationalMetricsHealthMonitor()
    
    def test_pipeline_health_check(self, monitor):
        """Test pipeline health check"""
        check = monitor.check_pipeline_health()
        
        assert check.check_name == "pipeline_health"
        assert check.status in ["HEALTHY", "WARNING", "CRITICAL"]
        assert check.component == "processing"
    
    def test_data_freshness_check(self, monitor):
        """Test data freshness check"""
        check = monitor.check_data_freshness()
        
        assert check.check_name == "data_freshness"
        assert check.status in ["HEALTHY", "WARNING", "CRITICAL"]
    
    def test_api_availability_check(self, monitor):
        """Test API availability check"""
        check = monitor.check_api_availability()
        
        assert check.check_name == "api_availability"
        assert check.status in ["HEALTHY", "WARNING", "CRITICAL"]
    
    def test_infrastructure_health_check(self, monitor):
        """Test infrastructure health check"""
        check = monitor.check_infrastructure_health()
        
        assert check.check_name == "infrastructure_health"
        assert check.status in ["HEALTHY", "WARNING", "CRITICAL"]
    
    def test_sla_compliance_check(self, monitor):
        """Test SLA compliance check"""
        check = monitor.check_sla_compliance()
        
        assert check.check_name == "sla_compliance"
        assert check.status in ["HEALTHY", "WARNING", "CRITICAL"]
    
    def test_all_health_checks(self, monitor):
        """Test running all health checks"""
        checks = monitor.run_all_health_checks()
        
        assert len(checks) == 5
        assert "pipeline" in checks
        assert "freshness" in checks
        assert "api" in checks
        assert "infrastructure" in checks
        assert "sla" in checks
    
    def test_health_report(self, monitor):
        """Test health report generation"""
        report = monitor.get_health_report()
        
        assert "overall_status" in report
        assert "summary" in report
        assert "checks" in report
        assert report["overall_status"] in ["HEALTHY", "WARNING", "CRITICAL"]
    
    def test_trend_analysis(self, monitor):
        """Test trend analysis"""
        # Run checks multiple times to build history
        for _ in range(3):
            monitor.run_all_health_checks()
        
        trend = monitor.get_trend_analysis(hours=24)
        
        assert "trend" in trend
        assert trend["period_hours"] == 24


class TestIntegration:
    """Integration tests"""
    
    def test_metrics_collection_aggregation(self):
        """Test end-to-end metrics collection and aggregation"""
        collector = MetricsCollector()
        
        # Add multiple metrics
        for i in range(5):
            metric = PipelineHealthMetric(
                product="test",
                job_name=f"job_{i}",
                run_timestamp=f"2024-02-18T{i:02d}:00:00Z",
                status="SUCCESS",
                duration_seconds=100,
                records_input=1000000,
                records_output=900000,
                records_failed=1000,
            )
            collector.add_pipeline_health_metric(metric)
        
        aggregator = MetricsAggregator(collector)
        aggregation = aggregator.aggregate_by_product()
        
        assert "test" in aggregation
        assert "pipeline" in aggregation["test"]
    
    def test_health_monitoring_workflow(self):
        """Test complete health monitoring workflow"""
        monitor = OperationalMetricsHealthMonitor()
        
        # Run health checks
        checks = monitor.run_all_health_checks()
        
        # Get report
        report = monitor.get_health_report()
        
        # Get trends
        trend = monitor.get_trend_analysis()
        
        assert all(check.status in ["HEALTHY", "WARNING", "CRITICAL"] 
                  for check in checks.values())
        assert report["overall_status"] in ["HEALTHY", "WARNING", "CRITICAL"]


# Fixtures for complex test scenarios
@pytest.fixture
def spark_session():
    """Fixture for Spark session"""
    from pyspark.sql import SparkSession
    return SparkSession.builder \
        .appName("test") \
        .master("local[*]") \
        .getOrCreate()


@pytest.fixture
def sample_metrics():
    """Sample metrics data"""
    return {
        "pipeline_success_rate": 99.85,
        "data_freshness_minutes": 3.5,
        "api_p99_latency_ms": 750,
        "data_quality_score": 99.6,
    }
