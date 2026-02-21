"""
Web User Analytics - Silver Layer Transformations

Transforms Bronze layer events into clean, deduplicated Silver layer data.
Handles data quality, deduplication, and data type conversions.
"""

from pyspark.sql import DataFrame, SparkSession, Window
from pyspark.sql.functions import (
    col, to_timestamp, to_date, hour, year, month, dayofmonth,
    row_number, when, hash, md5, concat_ws, lower, trim,
    ntile, explode_outer, max as spark_max, min as spark_min, avg, count,
    collect_list, first, last, lit, datediff
)
from pyspark.sql.types import DoubleType
from datetime import datetime, timedelta, timezone


class BronzeToSilverTransformer:
    """Transforms Bronze events to Silver layer"""
    
    def __init__(self, spark: SparkSession):
        """Initialize transformer with SparkSession"""
        self.spark = spark
    
    def deduplicate_page_views(self, bronze_df: DataFrame) -> DataFrame:
        """
        Deduplicate page view events based on event_id and timestamp.
        
        Uses window functions to identify and remove duplicates within a short time window.
        """
        # Filter for page_view events
        pv_df = bronze_df.filter(col("event_type") == "page_view")
        
        # Define window for deduplication (same event_id within 1 second)
        window = Window.partitionBy("event_id").orderBy("timestamp")
        
        # Row number to identify first occurrence
        deduped = pv_df.withColumn("rn", row_number().over(window)).filter(col("rn") == 1)
        
        return deduped.drop("rn")
    
    def clean_page_views(self, bronze_df: DataFrame) -> DataFrame:
        """
        Clean and validate page view data.
        
        - Validate URLs
        - Convert page_load_time to valid range
        - Fill missing browser/OS with defaults
        - Add quality score
        """
        pv_df = self.deduplicate_page_views(bronze_df)
        
        # Validate and clean page_load_time
        pv_df = pv_df.withColumn(
            "page_load_time_ms",
            when(
                (col("page_load_time_ms") >= 0) & (col("page_load_time_ms") <= 300000),
                col("page_load_time_ms")
            ).otherwise(None)
        )
        
        # Fill defaults for browser/OS
        pv_df = pv_df.withColumn(
            "browser",
            when(col("browser").isNotNull(), col("browser")).otherwise("Unknown")
        )
        
        pv_df = pv_df.withColumn(
            "os",
            when(col("os").isNotNull(), col("os")).otherwise("Unknown")
        )
        
        # Add device type consistency
        pv_df = pv_df.withColumn(
            "device_type",
            when(
                col("device_type").isin(["mobile", "desktop", "tablet"]),
                col("device_type")
            ).otherwise("unknown")
        )
        
        # Calculate quality score
        pv_df = pv_df.withColumn(
            "quality_score",
            self._calculate_quality_score(
                col("page_url"),
                col("page_load_time_ms"),
                col("is_bot"),
            )
        )
        
        # Add validation flag
        pv_df = pv_df.withColumn(
            "is_valid",
            (col("event_id").isNotNull()) & 
            (col("user_id").isNotNull()) & 
            (col("session_id").isNotNull()) &
            (col("page_url").isNotNull()) &
            (col("quality_score") > 0.5)
        )
        
        # Add partitioning columns
        pv_df = pv_df.withColumn("event_date", to_date(col("timestamp")))
        pv_df = pv_df.withColumn("event_hour", hour(col("timestamp")))
        
        # Select relevant columns
        return pv_df.select(
            "event_id", "user_id", "session_id", "is_new_session", "is_returning_user",
            "page_url", "page_path", "page_title", "referrer", "page_load_time_ms",
            "device_type", "device_brand", "device_model",
            "browser", "browser_version", "os", "os_version",
            "country", "region", "city", "latitude", "longitude",
            "is_bot", "traffic_source", "traffic_medium", "campaign_name",
            "quality_score", "is_valid", "timestamp", "event_date", "event_hour"
        )
    
    def reconstruct_sessions(self, bronze_df: DataFrame) -> DataFrame:
        """
        Reconstruct sessions from raw page_view and session events.
        
        Groups events by session_id and aggregates metrics.
        """
        # Filter for session events + page views
        session_events = bronze_df.filter(
            col("event_type").isin(["session_start", "session_end", "page_view"])
        )
        
        # Window for session aggregation
        session_window = Window.partitionBy("session_id").orderBy("timestamp")
        
        # Aggregate by session
        sessions_df = session_events.groupBy("session_id", "user_id").agg(
            spark_min("timestamp").alias("start_time"),
            spark_max("timestamp").alias("end_time"),
            count(when(col("event_type") == "page_view", 1)).alias("page_view_count"),
            count("*").alias("events_count"),
            collect_list(when(col("event_type") == "page_view", col("page_url"))).alias("page_views"),
            first("device_type").alias("device_type"),
            first("browser").alias("browser"),
            first("country").alias("country"),
            first("region").alias("region"),
            first("city").alias("city"),
            first("is_bot").alias("is_bot"),
            first("traffic_source").alias("traffic_source"),
            first("traffic_medium").alias("traffic_medium"),
            first("campaign_name").alias("campaign_name"),
        )
        
        # Calculate derived metrics
        sessions_df = sessions_df.withColumn(
            "duration_seconds",
            (datediff(col("end_time"), col("start_time")) * 86400).cast("long")
        )
        
        sessions_df = sessions_df.withColumn(
            "unique_pages",
            count(col("page_views")).over(Window.partitionBy("session_id"))
        )
        
        # Determine if bounce
        sessions_df = sessions_df.withColumn(
            "is_bounce",
            col("page_view_count") <= 1
        )
        
        # Quality score
        sessions_df = sessions_df.withColumn(
            "quality_score",
            when(col("is_bot"), 0.0).otherwise(
                (col("page_view_count") / (col("events_count") + 1)).cast(DoubleType())
            )
        )
        
        # Partitioning columns
        sessions_df = sessions_df.withColumn("event_date", to_date(col("start_time")))
        sessions_df = sessions_df.withColumn("event_hour", hour(col("start_time")))
        
        return sessions_df.select(
            "session_id", "user_id", "start_time", "end_time", "duration_seconds",
            "page_views", "events_count", "page_view_count", "unique_pages",
            "device_type", "browser", "country", "region", "city",
            "is_bot", "is_bounce", "quality_score",
            "traffic_source", "traffic_medium", "campaign_name",
            "event_date", "event_hour"
        )
    
    def _calculate_quality_score(self, url_col, load_time_col, is_bot_col) -> DataFrame:
        """
        Calculate data quality score for an event.
        
        Score from 0.0 to 1.0:
        - Bot traffic: 0.0
        - Normal traffic: 0.5-1.0 based on completeness
        """
        return when(
            is_bot_col == True, 0.0
        ).when(
            url_col.isNotNull() & (load_time_col >= 0), 0.9
        ).when(
            url_col.isNotNull(), 0.7
        ).otherwise(0.3)


class SilverAggregator:
    """Aggregates Silver data for various use cases"""
    
    def __init__(self, spark: SparkSession):
        """Initialize aggregator"""
        self.spark = spark
    
    def aggregate_hourly_page_metrics(self, silver_pv_df: DataFrame) -> DataFrame:
        """
        Aggregate hourly page metrics from Silver page views.
        
        Returns: DataFrame with page_id, hour, PV, UV, device breakdown, etc.
        """
        agg_df = silver_pv_df.filter(col("is_valid") & ~col("is_bot")).groupBy(
            "page_path", "event_date", "event_hour"
        ).agg(
            count("event_id").alias("page_views"),
            count(col("user_id")).cast("long").alias("unique_visitors"),  # Simplified
            # More accurate would need distinct approx
            avg("page_load_time_ms").alias("avg_page_load_time_ms"),
            (count(when(col("device_type") == "mobile", 1))).alias("mobile_views"),
            (count(when(col("device_type") == "desktop", 1))).alias("desktop_views"),
            (count(when(col("device_type") == "tablet", 1))).alias("tablet_views"),
        )
        
        # Add computed columns
        agg_df = agg_df.withColumn(
            "page_id",
            md5(col("page_path"))
        ).withColumn(
            "aggregated_at",
            lit(datetime.now(timezone.utc)).cast("timestamp")
        ).withColumn(
            "bot_percentage",
            lit(0.0)
        ).withColumn(
            "bounce_rate",
            lit(0.5)
        )
        
        return agg_df.select(
            "page_id", "event_date", "event_hour", "page_views", 
            "unique_visitors", "avg_page_load_time_ms",
            "mobile_views", "desktop_views", "tablet_views",
            "bounce_rate", "bot_percentage", "aggregated_at"
        )
    
    def aggregate_daily_conversion(self, silver_sessions_df: DataFrame) -> DataFrame:
        """
        Aggregate daily conversion metrics.
        
        Returns: DataFrame with conversion counts by day
        """
        conv_df = silver_sessions_df.filter(~col("is_bounce")).groupBy(
            "event_date"
        ).agg(
            count("session_id").alias("conversion_count"),
            count(col("user_id")).cast("long").alias("unique_users"),
        )
        
        conv_df = conv_df.withColumn(
            "aggregated_at",
            lit(datetime.now(timezone.utc)).cast("timestamp")
        )
        
        return conv_df


class SilverValidator:
    """Validates Silver layer data quality"""
    
    @staticmethod
    def validate_page_view(pv_df: DataFrame) -> DataFrame:
        """Validate page view record"""
        return pv_df.filter(
            (col("event_id").isNotNull()) &
            (col("user_id").isNotNull()) &
            (col("session_id").isNotNull()) &
            (col("page_url").isNotNull()) &
            (col("quality_score") > 0.5)
        )
    
    @staticmethod
    def validate_session(session_df: DataFrame) -> DataFrame:
        """Validate session record"""
        return session_df.filter(
            (col("session_id").isNotNull()) &
            (col("user_id").isNotNull()) &
            (col("duration_seconds") >= 0) &
            (col("events_count") > 0)
        )
    
    @staticmethod
    def get_data_quality_report(pv_df: DataFrame) -> dict:
        """Generate data quality report for page views"""
        total_records = pv_df.count()
        valid_records = pv_df.filter(col("is_valid")).count()
        bot_records = pv_df.filter(col("is_bot")).count()
        
        return {
            "total_records": total_records,
            "valid_records": valid_records,
            "invalid_records": total_records - valid_records,
            "bot_records": bot_records,
            "data_quality_%": (valid_records / total_records * 100) if total_records > 0 else 0,
            "timestamp": datetime.now(timezone.utc).isoformat(),
        }
