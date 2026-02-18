"""
Web User Analytics - Storage Layer Schemas

Defines Delta Lake schemas for Bronze, Silver, and Gold layers.
Bronze: Raw ingested data
Silver: Cleaned, deduplicated data
Gold: Aggregated metrics
"""

from pyspark.sql.types import (
    StructType, StructField, StringType, IntegerType, LongType, 
    DoubleType, BooleanType, TimestampType, ArrayType, MapType, DateType
)


# ============================================================================
# BRONZE LAYER - Raw ingested events
# ============================================================================

BRONZE_EVENT_SCHEMA = StructType([
    StructField("event_id", StringType(), False),
    StructField("user_id", StringType(), False),
    StructField("session_id", StringType(), False),
    StructField("event_type", StringType(), False),
    StructField("timestamp", TimestampType(), False),
    
    # Device info
    StructField("device_type", StringType(), True),
    StructField("device_brand", StringType(), True),
    StructField("device_model", StringType(), True),
    
    # Browser info
    StructField("browser", StringType(), False),
    StructField("browser_version", StringType(), True),
    StructField("os", StringType(), False),
    StructField("os_version", StringType(), True),
    
    # Geographic
    StructField("country", StringType(), False),
    StructField("region", StringType(), True),
    StructField("city", StringType(), True),
    StructField("latitude", DoubleType(), True),
    StructField("longitude", DoubleType(), True),
    
    # Session info
    StructField("is_new_session", BooleanType(), True),
    StructField("is_returning_user", BooleanType(), True),
    StructField("user_agent", StringType(), False),
    StructField("ip_address", StringType(), False),
    
    # Bot detection
    StructField("is_bot", BooleanType(), False),
    
    # Event-specific fields
    StructField("page_url", StringType(), True),
    StructField("page_path", StringType(), True),
    StructField("page_title", StringType(), True),
    StructField("referrer", StringType(), True),
    StructField("page_load_time_ms", LongType(), True),
    
    # Engagement
    StructField("click_element", StringType(), True),
    StructField("scroll_depth", IntegerType(), True),
    StructField("form_success", BooleanType(), True),
    StructField("video_id", StringType(), True),
    
    # Traffic source
    StructField("traffic_source", StringType(), True),
    StructField("traffic_medium", StringType(), True),
    StructField("campaign_name", StringType(), True),
    
    # Quality
    StructField("_quality", MapType(StringType(), StringType()), True),
    StructField("_session_info", MapType(StringType(), StringType()), True),
    
    # Metadata
    StructField("properties", MapType(StringType(), StringType()), True),
    StructField("ingested_at", TimestampType(), False),
    StructField("ingested_year", IntegerType(), False),
    StructField("ingested_month", IntegerType(), False),
    StructField("ingested_day", IntegerType(), False),
])


# ============================================================================
# SILVER LAYER - Cleaned, deduplicated events
# ============================================================================

SILVER_PAGE_VIEW_SCHEMA = StructType([
    StructField("event_id", StringType(), False),
    StructField("user_id", StringType(), False),
    StructField("session_id", StringType(), False),
    StructField("is_new_session", BooleanType(), False),
    StructField("is_returning_user", BooleanType(), False),
    
    # Page info
    StructField("page_url", StringType(), False),
    StructField("page_path", StringType(), False),
    StructField("page_title", StringType(), False),
    StructField("referrer", StringType(), True),
    
    # Performance
    StructField("page_load_time_ms", LongType(), True),
    StructField("dom_interactive_ms", LongType(), True),
    StructField("dom_complete_ms", LongType(), True),
    StructField("viewport_width", IntegerType(), True),
    StructField("viewport_height", IntegerType(), True),
    
    # Device/Browser/OS
    StructField("device_type", StringType(), False),
    StructField("device_brand", StringType(), True),
    StructField("device_model", StringType(), True),
    StructField("browser", StringType(), False),
    StructField("browser_version", StringType(), True),
    StructField("os", StringType(), False),
    StructField("os_version", StringType(), True),
    
    # Geographic
    StructField("country", StringType(), False),
    StructField("region", StringType(), True),
    StructField("city", StringType(), True),
    StructField("latitude", DoubleType(), True),
    StructField("longitude", DoubleType(), True),
    
    # Bot check
    StructField("is_bot", BooleanType(), False),
    
    # Traffic source
    StructField("traffic_source", StringType(), True),
    StructField("traffic_medium", StringType(), True),
    StructField("campaign_name", StringType(), True),
    
    # Data quality
    StructField("quality_score", DoubleType(), False),
    StructField("is_valid", BooleanType(), False),
    
    # Timestamps for partitioning
    StructField("timestamp", TimestampType(), False),
    StructField("event_date", StringType(), False),  # YYYY-MM-DD
    StructField("event_hour", IntegerType(), False),  # 0-23
])


SILVER_SESSION_SCHEMA = StructType([
    StructField("session_id", StringType(), False),
    StructField("user_id", StringType(), False),
    StructField("start_time", TimestampType(), False),
    StructField("end_time", TimestampType(), True),
    StructField("duration_seconds", LongType(), False),
    
    # Content
    StructField("page_views", ArrayType(StringType()), False),
    StructField("events_count", IntegerType(), False),
    StructField("page_view_count", IntegerType(), False),
    StructField("unique_pages", IntegerType(), False),
    
    # Engagement
    StructField("click_count", IntegerType(), True),
    StructField("scroll_count", IntegerType(), True),
    StructField("form_submit_count", IntegerType(), True),
    
    # Device/Traffic
    StructField("device_type", StringType(), True),
    StructField("browser", StringType(), True),
    StructField("traffic_source", StringType(), True),
    StructField("traffic_medium", StringType(), True),
    StructField("campaign_name", StringType(), True),
    
    # Geographic
    StructField("country", StringType(), False),
    StructField("region", StringType(), True),
    StructField("city", StringType(), True),
    
    # Bot/Quality
    StructField("is_bot", BooleanType(), False),
    StructField("is_bounce", BooleanType(), False),
    StructField("quality_score", DoubleType(), False),
    
    # Timestamps for partitioning
    StructField("event_date", StringType(), False),  # YYYY-MM-DD
    StructField("event_hour", IntegerType(), False),  # 0-23
])


# ============================================================================
# GOLD LAYER - Aggregated metrics
# ============================================================================

GOLD_PAGE_METRICS_SCHEMA = StructType([
    StructField("page_id", StringType(), False),
    StructField("event_date", StringType(), False),
    StructField("event_hour", IntegerType(), False),
    
    # Counts
    StructField("page_views", LongType(), False),
    StructField("unique_visitors", LongType(), False),
    StructField("unique_sessions", LongType(), False),
    StructField("new_visitors", LongType(), False),
    StructField("returning_visitors", LongType(), False),
    
    # Performance metrics
    StructField("avg_page_load_time_ms", DoubleType(), True),
    StructField("p50_page_load_time_ms", DoubleType(), True),
    StructField("p90_page_load_time_ms", DoubleType(), True),
    StructField("p99_page_load_time_ms", DoubleType(), True),
    StructField("max_page_load_time_ms", LongType(), True),
    
    # Engagement
    StructField("bounce_rate", DoubleType(), True),
    StructField("avg_session_duration_sec", DoubleType(), True),
    StructField("avg_pages_per_session", DoubleType(), True),
    
    # Device breakdown
    StructField("mobile_views", LongType(), False),
    StructField("desktop_views", LongType(), False),
    StructField("tablet_views", LongType(), False),
    
    # Top dimensions
    StructField("top_referrer", StringType(), True),
    StructField("top_country", StringType(), True),
    StructField("top_browser", StringType(), True),
    
    # Bot metrics
    StructField("bot_views", LongType(), False),
    StructField("bot_percentage", DoubleType(), True),
    
    # Timestamps
    StructField("aggregated_at", TimestampType(), False),
])


GOLD_FUNNEL_METRICS_SCHEMA = StructType([
    StructField("funnel_id", StringType(), False),
    StructField("step_number", IntegerType(), False),
    StructField("step_name", StringType(), False),
    StructField("event_date", StringType(), False),
    StructField("event_hour", IntegerType(), False),
    
    # Counts
    StructField("entered_count", LongType(), False),
    StructField("completed_count", LongType(), False),
    StructField("drop_off_count", LongType(), False),
    
    # Rates
    StructField("conversion_rate", DoubleType(), False),
    StructField("drop_off_rate", DoubleType(), False),
    
    # Time metrics
    StructField("avg_time_to_next_ms", LongType(), True),
    StructField("median_time_to_next_ms", LongType(), True),
    
    # Device breakdown
    StructField("mobile_enters", LongType(), False),
    StructField("desktop_enters", LongType(), False),
    
    # Timestamps
    StructField("aggregated_at", TimestampType(), False),
])


GOLD_SESSION_METRICS_SCHEMA = StructType([
    StructField("session_id", StringType(), False),
    StructField("user_id", StringType(), False),
    StructField("event_date", StringType(), False),
    
    # Session info
    StructField("session_duration_seconds", LongType(), False),
    StructField("pages_visited", IntegerType(), False),
    StructField("events_count", IntegerType(), False),
    StructField("unique_pages", IntegerType(), False),
    
    # Engagement
    StructField("page_view_count", IntegerType(), False),
    StructField("click_count", IntegerType(), False),
    StructField("scroll_count", IntegerType(), False),
    StructField("form_submit_count", IntegerType(), False),
    
    # Device/Traffic
    StructField("device_type", StringType(), True),
    StructField("traffic_source", StringType(), True),
    StructField("traffic_medium", StringType(), True),
    StructField("campaign_name", StringType(), True),
    
    # Geographic
    StructField("country", StringType(), False),
    StructField("region", StringType(), True),
    
    # Quality
    StructField("is_bot", BooleanType(), False),
    StructField("is_bounced", BooleanType(), False),
    
    # Timestamps
    StructField("aggregated_at", TimestampType(), False),
])


GOLD_USER_JOURNEY_SCHEMA = StructType([
    StructField("user_id", StringType(), False),
    StructField("event_date", StringType(), False),
    
    # User metrics
    StructField("total_sessions", IntegerType(), False),
    StructField("total_page_views", LongType(), False),
    StructField("total_events", LongType(), False),
    StructField("total_time_seconds", LongType(), False),
    
    # Engagement
    StructField("avg_session_duration_sec", DoubleType(), True),
    StructField("avg_pages_per_session", DoubleType(), True),
    StructField("bounce_rate", DoubleType(), True),
    
    # Device info
    StructField("primary_device", StringType(), True),
    StructField("primary_browser", StringType(), True),
    StructField("devices_used", ArrayType(StringType()), True),
    
    # Traffic
    StructField("first_traffic_source", StringType(), True),
    StructField("traffic_sources", ArrayType(StringType()), True),
    
    # Geographic
    StructField("primary_country", StringType(), True),
    StructField("countries", ArrayType(StringType()), True),
    
    # Recency / Frequency / Monetary
    StructField("last_session_time", TimestampType(), True),
    StructField("days_since_first", IntegerType(), True),
    
    # Timestamps
    StructField("aggregated_at", TimestampType(), False),
])


# ============================================================================
# Conversion metrics
# ============================================================================

GOLD_CONVERSION_SCHEMA = StructType([
    StructField("page_url", StringType(), False),
    StructField("conversion_type", StringType(), False),  # signup, purchase, etc.
    StructField("event_date", StringType(), False),
    StructField("event_hour", IntegerType(), False),
    
    # Counts
    StructField("conversion_count", LongType(), False),
    StructField("unique_sessions", LongType(), False),
    StructField("unique_users", LongType(), False),
    
    # Rates
    StructField("conversion_rate", DoubleType(), False),
    StructField("conversion_cost", DoubleType(), True),
    
    # Attribution
    StructField("attributed_to_traffic_source", StringType(), True),
    StructField("attributed_to_campaign", StringType(), True),
    
    # Device breakdown
    StructField("mobile_conversions", LongType(), False),
    StructField("desktop_conversions", LongType(), False),
    
    # Time to conversion
    StructField("avg_time_to_conversion_sec", LongType(), True),
    StructField("median_time_to_conversion_sec", LongType(), True),
    
    # Timestamps
    StructField("aggregated_at", TimestampType(), False),
])


# ============================================================================
# Schema mappings
# ============================================================================

BRONZE_SCHEMAS = {
    "events": BRONZE_EVENT_SCHEMA,
}

SILVER_SCHEMAS = {
    "page_views": SILVER_PAGE_VIEW_SCHEMA,
    "sessions": SILVER_SESSION_SCHEMA,
}

GOLD_SCHEMAS = {
    "page_metrics": GOLD_PAGE_METRICS_SCHEMA,
    "funnel_metrics": GOLD_FUNNEL_METRICS_SCHEMA,
    "session_metrics": GOLD_SESSION_METRICS_SCHEMA,
    "user_journey": GOLD_USER_JOURNEY_SCHEMA,
    "conversion": GOLD_CONVERSION_SCHEMA,
}


def get_schema(layer: str, table_name: str) -> StructType:
    """
    Get schema for a specific layer and table.
    
    Args:
        layer: "bronze", "silver", or "gold"
        table_name: Name of the table
        
    Returns:
        StructType schema
        
    Raises:
        ValueError: If layer or table not found
    """
    schemas = {
        "bronze": BRONZE_SCHEMAS,
        "silver": SILVER_SCHEMAS,
        "gold": GOLD_SCHEMAS,
    }
    
    if layer not in schemas:
        raise ValueError(f"Unknown layer: {layer}")
    
    if table_name not in schemas[layer]:
        raise ValueError(f"Unknown table {table_name} in layer {layer}")
    
    return schemas[layer][table_name]
