"""
Lakehouse Table Schemas
Defines schemas for all lakehouse tables across Bronze/Silver/Gold layers
"""

from pyspark.sql.types import (
    StructType, StructField, StringType, IntegerType, DoubleType,
    LongType, BooleanType, TimestampType, DateType, ArrayType
)


# ============================================================================
# BRONZE LAYER SCHEMAS - Raw data as received
# ============================================================================

BRONZE_APP_EVENTS_SCHEMA = StructType([
    StructField('event_id', StringType(), False),
    StructField('user_id', StringType(), False),
    StructField('event_type', StringType(), False),
    StructField('app_type', StringType(), False),
    StructField('event_timestamp', TimestampType(), False),
    StructField('event_properties', StringType(), True),  # JSON string
    StructField('device_info', StringType(), True),  # JSON string
    StructField('load_timestamp', TimestampType(), False),
    StructField('source_system', StringType(), False),
])

BRONZE_CLICKSTREAM_SCHEMA = StructType([
    StructField('click_id', StringType(), False),
    StructField('session_id', StringType(), False),
    StructField('user_id', StringType(), False),
    StructField('page_name', StringType(), False),
    StructField('click_timestamp', TimestampType(), False),
    StructField('click_path', StringType(), True),
    StructField('user_agent', StringType(), True),
    StructField('load_timestamp', TimestampType(), False),
])

BRONZE_CDC_SCHEMA = StructType([
    StructField('cdc_id', StringType(), False),
    StructField('table_name', StringType(), False),
    StructField('operation_type', StringType(), False),  # INSERT, UPDATE, DELETE
    StructField('primary_key', StringType(), False),
    StructField('before_values', StringType(), True),  # JSON
    StructField('after_values', StringType(), True),  # JSON
    StructField('timestamp', TimestampType(), False),
    StructField('load_timestamp', TimestampType(), False),
])


# ============================================================================
# SILVER LAYER SCHEMAS - Cleaned and validated data
# ============================================================================

SILVER_APP_EVENTS_SCHEMA = StructType([
    StructField('event_id', StringType(), False),
    StructField('user_id', StringType(), False),
    StructField('event_type', StringType(), False),
    StructField('app_type', StringType(), False),
    StructField('event_date', DateType(), False),
    StructField('event_hour', IntegerType(), False),
    StructField('event_timestamp', TimestampType(), False),
    StructField('device_os', StringType(), True),
    StructField('device_model', StringType(), True),
    StructField('event_value', DoubleType(), True),
    StructField('is_valid', BooleanType(), False),
    StructField('quality_checks', StringType(), True),  # JSON array
    StructField('processed_timestamp', TimestampType(), False),
])

SILVER_CLICKSTREAM_SCHEMA = StructType([
    StructField('session_id', StringType(), False),
    StructField('user_id', StringType(), False),
    StructField('session_start_time', TimestampType(), False),
    StructField('session_end_time', TimestampType(), True),
    StructField('session_duration_seconds', IntegerType(), True),
    StructField('page_sequence', ArrayType(StringType()), True),
    StructField('total_clicks', IntegerType(), False),
    StructField('is_completed', BooleanType(), False),
    StructField('processed_timestamp', TimestampType(), False),
])

SILVER_USERS_SCHEMA = StructType([
    StructField('user_id', StringType(), False),
    StructField('first_seen_date', DateType(), False),
    StructField('last_seen_date', DateType(), False),
    StructField('total_events', LongType(), False),
    StructField('total_sessions', IntegerType(), False),
    StructField('is_active', BooleanType(), False),
    StructField('country', StringType(), True),
    StructField('processed_timestamp', TimestampType(), False),
])


# ============================================================================
# GOLD LAYER SCHEMAS - Business-ready aggregated data
# ============================================================================

GOLD_EVENT_METRICS_SCHEMA = StructType([
    StructField('metric_date', DateType(), False),
    StructField('metric_hour', IntegerType(), False),
    StructField('event_type', StringType(), False),
    StructField('app_type', StringType(), False),
    StructField('total_events', LongType(), False),
    StructField('unique_users', LongType(), False),
    StructField('avg_event_value', DoubleType(), True),
    StructField('max_event_value', DoubleType(), True),
    StructField('min_event_value', DoubleType(), True),
])

GOLD_USER_SEGMENTS_SCHEMA = StructType([
    StructField('user_id', StringType(), False),
    StructField('segment_date', DateType(), False),
    StructField('segment_name', StringType(), False),  # VIP, Active, Regular, Inactive
    StructField('lifetime_value', DoubleType(), True),
    StructField('engagement_score', DoubleType(), False),
    StructField('risk_of_churn', DoubleType(), False),
    StructField('recommended_action', StringType(), True),
    StructField('updated_timestamp', TimestampType(), False),
])

GOLD_DAILY_SUMMARY_SCHEMA = StructType([
    StructField('summary_date', DateType(), False),
    StructField('total_users', LongType(), False),
    StructField('new_users', LongType(), False),
    StructField('total_events', LongType(), False),
    StructField('total_sessions', LongType(), False),
    StructField('avg_session_duration', DoubleType(), False),
    StructField('bounce_rate', DoubleType(), False),
    StructField('return_user_percentage', DoubleType(), False),
    StructField('processed_timestamp', TimestampType(), False),
])

GOLD_HOURLY_METRICS_SCHEMA = StructType([
    StructField('metric_date', DateType(), False),
    StructField('metric_hour', IntegerType(), False),
    StructField('total_events', LongType(), False),
    StructField('unique_users', LongType(), False),
    StructField('total_sessions', LongType(), False),
    StructField('avg_response_time_ms', DoubleType(), True),
    StructField('error_count', LongType(), False),
    StructField('processed_timestamp', TimestampType(), False),
])


# Schema mapping by table
LAKEHOUSE_SCHEMAS = {
    # Bronze
    'app_events_bronze': BRONZE_APP_EVENTS_SCHEMA,
    'clickstream_bronze': BRONZE_CLICKSTREAM_SCHEMA,
    'cdc_changes_bronze': BRONZE_CDC_SCHEMA,
    # Silver
    'app_events_silver': SILVER_APP_EVENTS_SCHEMA,
    'clickstream_silver': SILVER_CLICKSTREAM_SCHEMA,
    'users_silver': SILVER_USERS_SCHEMA,
    # Gold
    'event_metrics_gold': GOLD_EVENT_METRICS_SCHEMA,
    'user_segments_gold': GOLD_USER_SEGMENTS_SCHEMA,
    'daily_summary_gold': GOLD_DAILY_SUMMARY_SCHEMA,
    'hourly_metrics_gold': GOLD_HOURLY_METRICS_SCHEMA,
}


def get_schema(table_name: str) -> StructType:
    """Get schema for a table"""
    if table_name not in LAKEHOUSE_SCHEMAS:
        raise ValueError(f"Unknown table: {table_name}")
    return LAKEHOUSE_SCHEMAS[table_name]
