"""
Delta Lake schemas for Operational Metrics product

Defines Bronze/Silver/Gold layer schemas for:
- Pipeline execution logs
- Alert incidents
- Cost tracking
- Infrastructure metrics
"""

from delta.tables import DeltaTable
from pyspark.sql.types import StructType, StructField, StringType, LongType, DoubleType, BooleanType, ArrayType, MapType, TimestampType
from pyspark.sql import SparkSession


class OperationalMetricsSchemas:
    """Delta Lake schemas for operational metrics"""
    
    # ============ BRONZE LAYER ============
    # Raw ingestion from Kafka/APIs with minimal transformation
    
    BRONZE_PIPELINE_LOGS = StructType([
        StructField("product", StringType(), False),
        StructField("job_name", StringType(), False),
        StructField("job_id", StringType(), False),
        StructField("run_timestamp", StringType(), False),
        StructField("status", StringType(), False),  # SUCCESS, FAILED, RUNNING
        StructField("duration_seconds", LongType(), True),
        StructField("records_input", LongType(), True),
        StructField("records_output", LongType(), True),
        StructField("records_failed", LongType(), True),
        StructField("error_message", StringType(), True),
        StructField("retry_count", LongType(), True),
        StructField("executor_memory_mb", LongType(), True),
        StructField("executor_cores", LongType(), True),
        StructField("spark_version", StringType(), True),
        StructField("raw_metadata", MapType(StringType(), StringType()), True),
        StructField("ingestion_timestamp", StringType(), False),
    ])
    
    BRONZE_ALERT_INCIDENTS = StructType([
        StructField("incident_id", StringType(), False),
        StructField("alert_id", StringType(), False),
        StructField("metric", StringType(), False),
        StructField("value", DoubleType(), False),
        StructField("threshold", DoubleType(), False),
        StructField("severity", StringType(), False),  # low, medium, high, critical
        StructField("triggered_at", StringType(), False),
        StructField("product", StringType(), True),
        StructField("component", StringType(), True),
        StructField("alert_config", MapType(StringType(), StringType()), True),
        StructField("acknowledged", BooleanType(), True),
        StructField("acknowledged_at", StringType(), True),
        StructField("acknowledged_by", StringType(), True),
        StructField("ingestion_timestamp", StringType(), False),
    ])
    
    BRONZE_COST_EVENTS = StructType([
        StructField("cost_event_id", StringType(), False),
        StructField("product", StringType(), False),
        StructField("component", StringType(), False),
        StructField("cost_type", StringType(), False),  # compute, storage, network, licensing
        StructField("cost_amount", DoubleType(), False),
        StructField("currency", StringType(), False),
        StructField("period_start", StringType(), False),
        StructField("period_end", StringType(), False),
        StructField("usage_value", DoubleType(), False),
        StructField("usage_unit", StringType(), False),
        StructField("rate_per_unit", DoubleType(), False),
        StructField("metadata", MapType(StringType(), StringType()), True),
        StructField("ingestion_timestamp", StringType(), False),
    ])
    
    BRONZE_INFRASTRUCTURE_METRICS = StructType([
        StructField("metric_id", StringType(), False),
        StructField("component", StringType(), False),  # spark, kafka, redis, storage
        StructField("timestamp", StringType(), False),
        StructField("cpu_percent", DoubleType(), False),
        StructField("memory_percent", DoubleType(), False),
        StructField("memory_mb", LongType(), True),
        StructField("network_io_mbps", DoubleType(), False),
        StructField("disk_io_mbps", DoubleType(), False),
        StructField("latency_ms", DoubleType(), True),
        StructField("connection_count", LongType(), True),
        StructField("error_count", LongType(), True),
        StructField("host", StringType(), True),
        StructField("ingestion_timestamp", StringType(), False),
    ])
    
    # ============ SILVER LAYER ============
    # Cleaned, validated data with deduplication and validation
    
    SILVER_PIPELINE_METRICS = StructType([
        StructField("product", StringType(), False),
        StructField("job_name", StringType(), False),
        StructField("run_date", StringType(), False),
        StructField("run_hour", StringType(), False),
        StructField("status", StringType(), False),
        StructField("duration_seconds", LongType(), False),
        StructField("records_input", LongType(), False),
        StructField("records_output", LongType(), False),
        StructField("records_failed", LongType(), False),
        StructField("error_category", StringType(), True),
        StructField("success_flag", BooleanType(), False),
        StructField("executor_memory_mb", LongType(), True),
        StructField("spark_version", StringType(), True),
        StructField("is_duplicate", BooleanType(), False),
        StructField("data_quality_score", DoubleType(), False),
        StructField("processed_timestamp", StringType(), False),
    ])
    
    SILVER_SLA_METRICS = StructType([
        StructField("sla_id", StringType(), False),
        StructField("product", StringType(), False),
        StructField("metric_name", StringType(), False),
        StructField("measurement_date", StringType(), False),
        StructField("measurement_hour", StringType(), False),
        StructField("target_value", DoubleType(), False),
        StructField("actual_value", DoubleType(), False),
        StructField("unit", StringType(), False),
        StructField("compliant", BooleanType(), False),
        StructField("variance_percent", DoubleType(), False),
        StructField("status", StringType(), False),  # HEALTHY, WARNING, CRITICAL
        StructField("processed_timestamp", StringType(), False),
    ])
    
    # ============ GOLD LAYER ============
    # Aggregated metrics ready for consumption
    
    GOLD_DAILY_PIPELINE_SUMMARY = StructType([
        StructField("product", StringType(), False),
        StructField("summary_date", StringType(), False),
        StructField("total_runs", LongType(), False),
        StructField("successful_runs", LongType(), False),
        StructField("failed_runs", LongType(), False),
        StructField("success_rate", DoubleType(), False),
        StructField("avg_duration_seconds", DoubleType(), False),
        StructField("total_records_processed", LongType(), False),
        StructField("total_records_failed", LongType(), False),
        StructField("failure_rate", DoubleType(), False),
        StructField("avg_executor_memory_mb", LongType(), True),
    ])
    
    GOLD_HOURLY_SLA_COMPLIANCE = StructType([
        StructField("compliance_date", StringType(), False),
        StructField("compliance_hour", StringType(), False),
        StructField("product", StringType(), False),
        StructField("metric_name", StringType(), False),
        StructField("target_value", DoubleType(), False),
        StructField("actual_value", DoubleType(), False),
        StructField("compliant", BooleanType(), False),
        StructField("variance_percent", DoubleType(), False),
        StructField("sla_status", StringType(), False),  # HEALTHY, WARNING, CRITICAL
    ])
    
    GOLD_DAILY_COST_SUMMARY = StructType([
        StructField("cost_date", StringType(), False),
        StructField("product", StringType(), False),
        StructField("compute_cost", DoubleType(), False),
        StructField("storage_cost", DoubleType(), False),
        StructField("network_cost", DoubleType(), False),
        StructField("licensing_cost", DoubleType(), False),
        StructField("total_cost", DoubleType(), False),
        StructField("currency", StringType(), False),
        StructField("records_processed", LongType(), False),
        StructField("cost_per_record", DoubleType(), False),
    ])
    
    GOLD_ALERT_SUMMARY = StructType([
        StructField("alert_date", StringType(), False),
        StructField("alert_hour", StringType(), False),
        StructField("product", StringType(), False),
        StructField("total_incidents", LongType(), False),
        StructField("critical_incidents", LongType(), False),
        StructField("high_incidents", LongType(), False),
        StructField("medium_incidents", LongType(), False),
        StructField("low_incidents", LongType(), False),
        StructField("acknowledged_count", LongType(), False),
        StructField("avg_acknowledgement_time_minutes", DoubleType(), False),
    ])
    
    @staticmethod
    def create_or_update_tables(spark: SparkSession, base_path: str) -> None:
        """
        Create or update all Delta tables.
        
        Args:
            spark: SparkSession
            base_path: Base path for data
        """
        tables = {
            f"{base_path}/bronze/pipeline_logs": OperationalMetricsSchemas.BRONZE_PIPELINE_LOGS,
            f"{base_path}/bronze/alert_incidents": OperationalMetricsSchemas.BRONZE_ALERT_INCIDENTS,
            f"{base_path}/bronze/cost_events": OperationalMetricsSchemas.BRONZE_COST_EVENTS,
            f"{base_path}/bronze/infrastructure_metrics": OperationalMetricsSchemas.BRONZE_INFRASTRUCTURE_METRICS,
            
            f"{base_path}/silver/pipeline_metrics": OperationalMetricsSchemas.SILVER_PIPELINE_METRICS,
            f"{base_path}/silver/sla_metrics": OperationalMetricsSchemas.SILVER_SLA_METRICS,
            
            f"{base_path}/gold/daily_pipeline_summary": OperationalMetricsSchemas.GOLD_DAILY_PIPELINE_SUMMARY,
            f"{base_path}/gold/hourly_sla_compliance": OperationalMetricsSchemas.GOLD_HOURLY_SLA_COMPLIANCE,
            f"{base_path}/gold/daily_cost_summary": OperationalMetricsSchemas.GOLD_DAILY_COST_SUMMARY,
            f"{base_path}/gold/alert_summary": OperationalMetricsSchemas.GOLD_ALERT_SUMMARY,
        }
        
        for table_path, schema in tables.items():
            try:
                # Check if table exists
                spark.read.format("delta").load(table_path)
            except:
                # Create empty table
                spark.createDataFrame([], schema=schema) \
                    .write \
                    .format("delta") \
                    .mode("overwrite") \
                    .save(table_path)
