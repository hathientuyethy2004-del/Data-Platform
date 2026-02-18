"""
Web User Analytics - Gold Layer Metrics

Calculates aggregated analytics metrics for reporting and dashboarding.
Produces KPI tables for pages, funnels, sessions, and conversions.
"""

from pyspark.sql import DataFrame, SparkSession, Window
from pyspark.sql.functions import (
    col, to_date, hour, day, month, year, round as spark_round,
    count, countDistinct, sum as spark_sum, avg, min as spark_min, max as spark_max,
    when, percentile_approx, row_number, lag, lead, lit, concat_ws,
    datediff, unix_timestamp, cast
)
from pyspark.sql.types import DoubleType, LongType, IntegerType
from datetime import datetime
from typing import Dict, List, Any


class GoldPageMetricsCalculator:
    """Calculates page-level analytics metrics"""
    
    def __init__(self, spark: SparkSession):
        self.spark = spark
    
    def calculate_hourly_page_metrics(self, silver_pv_df: DataFrame) -> DataFrame:
        """
        Calculate hourly page-level metrics.
        
        Includes: PV, UV, Load Time Percentiles, Device Mix, etc.
        """
        # Filter valid, non-bot traffic
        valid_pv = silver_pv_df.filter(
            (col("is_valid") == True) & (col("is_bot") == False)
        )
        
        # Group by page and hour
        metrics_df = valid_pv.groupBy(
            "page_path", "event_date", "event_hour"
        ).agg(
            # Counts
            count("event_id").alias("page_views"),
            countDistinct("user_id").alias("unique_visitors"),
            countDistinct("session_id").alias("unique_sessions"),
            countDistinct(
                when(col("is_new_session") == True, col("user_id"))
            ).alias("new_visitors"),
            countDistinct(
                when(col("is_returning_user") == True, col("user_id"))
            ).alias("returning_visitors"),
            
            # Performance
            avg("page_load_time_ms").alias("avg_page_load_time_ms"),
            percentile_approx("page_load_time_ms", 0.5).alias("p50_page_load_time_ms"),
            percentile_approx("page_load_time_ms", 0.9).alias("p90_page_load_time_ms"),
            percentile_approx("page_load_time_ms", 0.99).alias("p99_page_load_time_ms"),
            spark_max("page_load_time_ms").alias("max_page_load_time_ms"),
            
            # Device/Browser
            spark_sum(when(col("device_type") == "mobile", 1)).alias("mobile_views"),
            spark_sum(when(col("device_type") == "desktop", 1)).alias("desktop_views"),
            spark_sum(when(col("device_type") == "tablet", 1)).alias("tablet_views"),
        )
        
        # Calculate derived metrics
        metrics_df = metrics_df.withColumn(
            "page_id",
            col("page_path")
        ).withColumn(
            "bounce_rate",
            spark_round(
                spark_sum(when(col("is_new_session") == True, 1)).over(
                    Window.partitionBy("page_path", "event_date")
                ) / (col("unique_visitors") + 1),
                3
            )
        ).withColumn(
            "bot_views",
            lit(0)  # Filtered out above
        ).withColumn(
            "bot_percentage",
            lit(0.0)
        ).withColumn(
            "aggregated_at",
            lit(datetime.utcnow()).cast("timestamp")
        )
        
        return metrics_df.select(
            "page_id", "event_date", "event_hour",
            "page_views", "unique_visitors", "unique_sessions",
            "new_visitors", "returning_visitors",
            "avg_page_load_time_ms", "p50_page_load_time_ms", "p90_page_load_time_ms",
            "p99_page_load_time_ms", "max_page_load_time_ms",
            "bounce_rate", "mobile_views", "desktop_views", "tablet_views",
            "bot_views", "bot_percentage", "aggregated_at"
        ).coalesce(1)
    
    def calculate_daily_page_metrics(self, silver_pv_df: DataFrame) -> DataFrame:
        """Calculate daily aggregated page metrics"""
        valid_pv = silver_pv_df.filter((col("is_valid")) & (~col("is_bot")))
        
        metrics_df = valid_pv.groupBy(
            "page_path", "event_date"
        ).agg(
            count("event_id").alias("page_views"),
            countDistinct("user_id").alias("unique_visitors"),
            countDistinct("session_id").alias("unique_sessions"),
            avg("page_load_time_ms").alias("avg_page_load_time_ms"),
            percentile_approx("page_load_time_ms", 0.5).alias("p50_page_load_time_ms"),
            percentile_approx("page_load_time_ms", 0.9).alias("p90_page_load_time_ms"),
        )
        
        return metrics_df.withColumn(
            "page_id", col("page_path")
        ).withColumn(
            "event_hour", lit(-1)  # Daily aggregate
        ).withColumn(
            "aggregated_at", lit(datetime.utcnow()).cast("timestamp")
        )


class GoldFunnelMetricsCalculator:
    """Calculates funnel conversion metrics"""
    
    def __init__(self, spark: SparkSession):
        self.spark = spark
    
    def calculate_funnel_conversion(self, 
                                   funnels_config: Dict[str, List[str]],
                                   silver_sessions_df: DataFrame) -> DataFrame:
        """
        Calculate funnel conversion metrics.
        
        Args:
            funnels_config: Dict mapping funnel_id to list of page paths
            silver_sessions_df: Silver layer sessions
            
        Returns:
            DataFrame with funnel metrics
        """
        results = []
        
        event_date_window = Window.partitionBy("funnel_id", "event_date").orderBy("step_number")
        
        for funnel_id, pages in funnels_config.items():
            step_dfs = []
            
            for step_num, page_path in enumerate(pages, 1):
                step_df = silver_sessions_df.filter(
                    col("page_views").contains(page_path)
                ).withColumn(
                    "step_number", lit(step_num)
                ).withColumn(
                    "step_name", lit(page_path)
                ).withColumn(
                    "funnel_id", lit(funnel_id)
                ).select(
                    "funnel_id", "step_number", "step_name", "session_id", "user_id",
                    "event_date"
                )
                step_dfs.append(step_df)
            
            # Join steps
            funnel_df = step_dfs[0]
            for i in range(1, len(step_dfs)):
                funnel_df = funnel_df.join(
                    step_dfs[i],
                    on=["session_id", "funnel_id"],
                    how="left"
                )
            
            # Aggregate
            agg_df = funnel_df.groupBy(
                "funnel_id", "step_number", "step_name", "event_date"
            ).agg(
                count("session_id").alias("entered_count"),
                countDistinct("user_id").alias("unique_users"),
            )
            
            # Calculate conversion and drop-off
            agg_df = agg_df.withColumn(
                "lead_entered",
                lead("entered_count").over(event_date_window)
            ).withColumn(
                "drop_off_count",
                when(col("lead_entered").isNotNull(),
                     col("entered_count") - col("lead_entered")).otherwise(0)
            ).withColumn(
                "conversion_rate",
                spark_round(
                    when(col("lead_entered").isNotNull(),
                         col("lead_entered") / col("entered_count")).otherwise(1.0),
                    3
                )
            ).withColumn(
                "aggregated_at",
                lit(datetime.utcnow()).cast("timestamp")
            )
            
            results.append(agg_df)
        
        if results:
            return self.spark.unionByName(*results)
        else:
            return self.spark.createDataFrame([], "funnel_id STRING")


class GoldSessionMetricsCalculator:
    """Calculates session-level metrics"""
    
    def __init__(self, spark: SparkSession):
        self.spark = spark
    
    def calculate_session_metrics(self, silver_sessions_df: DataFrame) -> DataFrame:
        """
        Calculate session-level metrics for analysis.
        
        Returns session-level KPIs
        """
        metrics_df = silver_sessions_df.select(
            "session_id", "user_id", "event_date",
            "duration_seconds", "page_view_count", "events_count",
            "unique_pages", "device_type", "country", "region",
            "is_bot", "is_bounce", "traffic_source", "traffic_medium",
            "campaign_name"
        ).withColumn(
            "aggregated_at", lit(datetime.utcnow()).cast("timestamp")
        ).withColumn(
            "pages_visited", col("unique_pages")
        )
        
        return metrics_df


class GoldUserJourneyCalculator:
    """Calculates user journey metrics"""
    
    def __init__(self, spark: SparkSession):
        self.spark = spark
    
    def calculate_user_metrics(self, 
                              silver_sessions_df: DataFrame,
                              silver_pv_df: DataFrame,
                              date_range_days: int = 90) -> DataFrame:
        """
        Calculate user-level journey metrics.
        
        Args:
            silver_sessions_df: Silver sessions
            silver_pv_df: Silver page views
            date_range_days: Days to look back
            
        Returns:
            DataFrame with user journey metrics
        """
        # Aggregate sessions by user
        user_metrics = silver_sessions_df.groupBy("user_id").agg(
            count("session_id").alias("total_sessions"),
            spark_sum("page_view_count").alias("total_page_views"),
            spark_sum("events_count").alias("total_events"),
            spark_sum("duration_seconds").alias("total_time_seconds"),
            spark_max("start_time").alias("last_session_time"),
        )
        
        # Calculate RFM and other metrics
        user_metrics = user_metrics.withColumn(
            "avg_session_duration_sec",
            spark_round(col("total_time_seconds") / col("total_sessions"), 1)
        ).withColumn(
            "avg_pages_per_session",
            spark_round(col("total_page_views") / col("total_sessions"), 2)
        ).withColumn(
            "aggregated_at",
            lit(datetime.utcnow()).cast("timestamp")
        )
        
        return user_metrics


class GoldConversionCalculator:
    """Calculates conversion metrics"""
    
    def __init__(self, spark: SparkSession):
        self.spark = spark
    
    def calculate_page_conversion(self, 
                                 silver_sessions_df: DataFrame,
                                 conversion_pages: List[str]) -> DataFrame:
        """
        Calculate conversion metrics by page.
        
        Args:
            silver_sessions_df: Silver sessions
            conversion_pages: Page paths that count as conversions
            
        Returns:
            Conversion metrics by page
        """
        # Filter for conversion events
        conversion_df = silver_sessions_df.filter(
            col("page_views").isNotNull()
        ).select(
            "event_date", "page_views", "session_id", "user_id"
        )
        
        # For each conversion page
        results = []
        for conv_page in conversion_pages:
            page_conv = conversion_df.filter(
                col("page_views").contains(conv_page)
            ).groupBy("event_date").agg(
                count("session_id").alias("conversion_count"),
                countDistinct("user_id").alias("unique_users"),
            ).withColumn(
                "page_url", lit(conv_page)
            ).withColumn(
                "conversion_type", lit("page_view")
            ).withColumn(
                "aggregated_at", lit(datetime.utcnow()).cast("timestamp")
            )
            results.append(page_conv)
        
        if results:
            return self.spark.unionByName(*results)
        else:
            return self.spark.createDataFrame([], "conversion_count LONG")


class GoldMetricsWriter:
    """Writes calculated metrics to Gold layer Delta tables"""
    
    def __init__(self, spark: SparkSession, output_path: str):
        """
        Initialize metrics writer.
        
        Args:
            spark: SparkSession
            output_path: Base path for Gold layer output
        """
        self.spark = spark
        self.output_path = output_path
    
    def write_table(self, df: DataFrame, table_name: str, 
                   partition_by: List[str] = None, mode: str = "overwrite") -> None:
        """
        Write DataFrame to Delta table.
        
        Args:
            df: DataFrame to write
            table_name: Name of table
            partition_by: Columns to partition by
            mode: Write mode (overwrite, append, etc.)
        """
        output_location = f"{self.output_path}/{table_name}"
        
        writer = df.write.format("delta").mode(mode)
        
        if partition_by:
            writer = writer.partitionBy(*partition_by)
        
        writer.save(output_location)
        
        print(f"Wrote {df.count()} records to {table_name}")
    
    def write_page_metrics(self, df: DataFrame) -> None:
        """Write page metrics"""
        self.write_table(df, "page_metrics", partition_by=["event_date", "event_hour"])
    
    def write_funnel_metrics(self, df: DataFrame) -> None:
        """Write funnel metrics"""
        self.write_table(df, "funnel_metrics", partition_by=["event_date"])
    
    def write_session_metrics(self, df: DataFrame) -> None:
        """Write session metrics"""
        self.write_table(df, "session_metrics", partition_by=["event_date"])
    
    def write_user_journey(self, df: DataFrame) -> None:
        """Write user journey metrics"""
        self.write_table(df, "user_journey", partition_by=["event_date"])
    
    def write_conversion(self, df: DataFrame) -> None:
        """Write conversion metrics"""
        self.write_table(df, "conversion_metrics", partition_by=["event_date"])
