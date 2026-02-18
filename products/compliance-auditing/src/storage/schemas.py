"""
Delta Lake schemas for Compliance Auditing product

Defines Bronze/Silver/Gold layer schemas for:
- Audit trails and access logs
- Compliance violations and incidents
- Data subject requests
- Retention schedules
"""

from pyspark.sql.types import StructType, StructField, StringType, LongType, DoubleType, BooleanType, ArrayType, MapType, TimestampType
from pyspark.sql import SparkSession


class ComplianceAuditSchemas:
    """Delta Lake schemas for compliance auditing"""
    
    # ============ BRONZE LAYER ============
    # Raw audit events with minimal transformation
    
    BRONZE_AUDIT_EVENTS = StructType([
        StructField("event_id", StringType(), False),
        StructField("event_type", StringType(), False),  # data_access, deletion, api_call, etc
        StructField("timestamp", StringType(), False),
        StructField("user_id", StringType(), True),
        StructField("service", StringType(), False),
        StructField("resource", StringType(), False),
        StructField("resource_type", StringType(), False),
        StructField("action", StringType(), False),
        StructField("data_classification", StringType(), False),
        StructField("contains_pii", BooleanType(), False),
        StructField("pii_fields", ArrayType(StringType()), True),
        StructField("status", StringType(), False),
        StructField("status_code", LongType(), True),
        StructField("error_message", StringType(), True),
        StructField("retention_days", LongType(), False),
        StructField("source_ip", StringType(), True),
        StructField("session_id", StringType(), True),
        StructField("metadata", MapType(StringType(), StringType()), True),
        StructField("ingestion_timestamp", StringType(), False),
    ])
    
    BRONZE_DATA_DELETION_REQUESTS = StructType([
        StructField("request_id", StringType(), False),
        StructField("subject_id", StringType(), False),
        StructField("deletion_reason", StringType(), False),
        StructField("datasets_affected", ArrayType(StringType()), False),
        StructField("requested_at", StringType(), False),
        StructField("status", StringType(), False),  # pending, in_progress, completed, failed
        StructField("records_deleted", LongType(), True),
        StructField("completed_at", StringType(), True),
        StructField("error_message", StringType(), True),
        StructField("ingestion_timestamp", StringType(), False),
    ])
    
    BRONZE_COMPLIANCE_VIOLATIONS = StructType([
        StructField("violation_id", StringType(), False),
        StructField("detected_at", StringType(), False),
        StructField("violation_type", StringType(), False),
        StructField("severity", StringType(), False),
        StructField("dataset", StringType(), False),
        StructField("framework", StringType(), False),
        StructField("description", StringType(), False),
        StructField("remediation_status", StringType(), False),
        StructField("remediated_at", StringType(), True),
        StructField("metadata", MapType(StringType(), StringType()), True),
        StructField("ingestion_timestamp", StringType(), False),
    ])
    
    BRONZE_DATA_LINEAGE = StructType([
        StructField("lineage_id", StringType(), False),
        StructField("source_dataset", StringType(), False),
        StructField("target_dataset", StringType(), False),
        StructField("transformation_job", StringType(), False),
        StructField("timestamp", StringType(), False),
        StructField("records_input", LongType(), False),
        StructField("records_output", LongType(), False),
        StructField("pii_fields_processed", ArrayType(StringType()), True),
        StructField("anonymization_applied", BooleanType(), False),
        StructField("data_quality_checks", MapType(StringType(), StringType()), True),
        StructField("ingestion_timestamp", StringType(), False),
    ])
    
    # ============ SILVER LAYER ============
    # Cleaned and validated audit data
    
    SILVER_AUDIT_TRAIL = StructType([
        StructField("event_id", StringType(), False),
        StructField("event_date", StringType(), False),
        StructField("event_hour", StringType(), False),
        StructField("event_type", StringType(), False),
        StructField("user_id", StringType(), True),
        StructField("service", StringType(), False),
        StructField("resource", StringType(), False),
        StructField("action", StringType(), False),
        StructField("classification", StringType(), False),
        StructField("pii_involved", BooleanType(), False),
        StructField("action_result", StringType(), False),  # success, failure, denied
        StructField("has_violations", BooleanType(), False),
        StructField("processed_timestamp", StringType(), False),
    ])
    
    SILVER_GDPR_COMPLIANCE = StructType([
        StructField("check_id", StringType(), False),
        StructField("check_date", StringType(), False),
        StructField("dataset", StringType(), False),
        StructField("check_type", StringType(), False),  # retention, access, minimization
        StructField("compliant", BooleanType(), False),
        StructField("details", MapType(StringType(), StringType()), True),
        StructField("processed_timestamp", StringType(), False),
    ])
    
    # ============ GOLD LAYER ============
    # Aggregated compliance metrics and reports
    
    GOLD_DAILY_AUDIT_SUMMARY = StructType([
        StructField("summary_date", StringType(), False),
        StructField("service", StringType(), False),
        StructField("total_events", LongType(), False),
        StructField("successful_events", LongType(), False),
        StructField("failed_events", LongType(), False),
        StructField("denied_events", LongType(), False),
        StructField("pii_access_events", LongType(), False),
        StructField("unique_users", LongType(), False),
        StructField("datasets_accessed", LongType(), False),
    ])
    
    GOLD_COMPLIANCE_STATUS = StructType([
        StructField("status_date", StringType(), False),
        StructField("framework", StringType(), False),
        StructField("overall_status", StringType(), False),  # COMPLIANT, VIOLATIONS
        StructField("total_checks", LongType(), False),
        StructField("passed_checks", LongType(), False),
        StructField("failed_checks", LongType(), False),
        StructField("compliance_score", DoubleType(), False),
        StructField("critical_violations", LongType(), False),
        StructField("high_violations", LongType(), False),
    ])
    
    GOLD_DATA_RETENTION_SCHEDULE = StructType([
        StructField("schedule_id", StringType(), False),
        StructField("dataset", StringType(), False),
        StructField("age_days", LongType(), False),
        StructField("retention_limit_days", LongType(), False),
        StructField("scheduled_deletion_date", StringType(), False),
        StructField("status", StringType(), False),  # pending, preparing, deleting, completed
        StructField("reason", StringType(), False),
    ])
    
    GOLD_PII_ACCESS_LOG = StructType([
        StructField("log_date", StringType(), False),
        StructField("log_hour", StringType(), False),
        StructField("user_id", StringType(), False),
        StructField("dataset", StringType(), False),
        StructField("pii_fields_accessed", ArrayType(StringType()), False),
        StructField("access_count", LongType(), False),
        StructField("justified", BooleanType(), False),
        StructField("access_purpose", StringType(), True),
    ])
    
    GOLD_GDPR_DATA_SUBJECT_REQUESTS = StructType([
        StructField("request_date", StringType(), False),
        StructField("request_id", StringType(), False),
        StructField("request_type", StringType(), False),  # access, deletion, correction
        StructField("subject_count", LongType(), False),
        StructField("status", StringType(), False),  # pending, processing, completed
        StructField("average_processing_days", DoubleType(), False),
        StructField("compliance_status", StringType(), False),
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
            f"{base_path}/bronze/audit_events": ComplianceAuditSchemas.BRONZE_AUDIT_EVENTS,
            f"{base_path}/bronze/deletion_requests": ComplianceAuditSchemas.BRONZE_DATA_DELETION_REQUESTS,
            f"{base_path}/bronze/violations": ComplianceAuditSchemas.BRONZE_COMPLIANCE_VIOLATIONS,
            f"{base_path}/bronze/data_lineage": ComplianceAuditSchemas.BRONZE_DATA_LINEAGE,
            
            f"{base_path}/silver/audit_trail": ComplianceAuditSchemas.SILVER_AUDIT_TRAIL,
            f"{base_path}/silver/gdpr_compliance": ComplianceAuditSchemas.SILVER_GDPR_COMPLIANCE,
            
            f"{base_path}/gold/daily_audit_summary": ComplianceAuditSchemas.GOLD_DAILY_AUDIT_SUMMARY,
            f"{base_path}/gold/compliance_status": ComplianceAuditSchemas.GOLD_COMPLIANCE_STATUS,
            f"{base_path}/gold/retention_schedule": ComplianceAuditSchemas.GOLD_DATA_RETENTION_SCHEDULE,
            f"{base_path}/gold/pii_access_log": ComplianceAuditSchemas.GOLD_PII_ACCESS_LOG,
            f"{base_path}/gold/data_subject_requests": ComplianceAuditSchemas.GOLD_GDPR_DATA_SUBJECT_REQUESTS,
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
