"""
Batch Job: User Segmentation
User profiling and segmentation based on behavior
"""

import sys
import os
import argparse
from datetime import datetime, timedelta

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from pyspark.sql import SparkSession, Window
from pyspark.sql import functions as F
from pyspark.sql.functions import col, count, sum as spark_sum, avg, max as spark_max, min as spark_min, current_timestamp, when

from configs.spark_config import OUTPUTS_DIR
from configs.logging_config import setup_logger

logger = setup_logger(__name__)


class UserSegmentationJob:
    """User profiling and behavior-based segmentation"""
    
    def __init__(self, app_name: str = "user-segmentation-job"):
        self.app_name = app_name
        self.spark = None
    
    def start(self, lookback_days: int = 30):
        """
        Start the batch job
        
        Args:
            lookback_days: Number of days to look back for segmentation
        """
        try:
            logger.info(f"🚀 Starting User Segmentation Job (lookback: {lookback_days} days)")
            
            # Create Spark session
            self.spark = SparkSession.builder \
                .appName(self.app_name) \
                .getOrCreate()
            
            events_path = os.path.join(OUTPUTS_DIR, "events_aggregated_realtime")
            clickstream_path = os.path.join(OUTPUTS_DIR, "clickstream_sessions")
            
            try:
                # Load data
                events_df = self.spark.read.parquet(events_path)
                clickstream_df = self.spark.read.parquet(clickstream_path)
                
                logger.info("👥 Building user profiles from event data")
                
                # Aggregate events by user
                user_events = events_df.groupBy("user_id").agg(
                    count("*").alias("total_events"),
                    F.countDistinct("event_type").alias("event_type_count"),
                    F.countDistinct("app_type").alias("app_type_count"),
                    F.max("event_count").alias("max_events_in_window"),
                    F.avg("event_count").alias("avg_events_in_window")
                )
                
                # Aggregate clickstream by user
                user_clicks = clickstream_df.groupBy("user_id").agg(
                    count("*").alias("session_count"),
                    F.sum("total_clicks").alias("total_clicks"),
                    F.avg("total_clicks").alias("avg_clicks_per_session"),
                    F.avg("unique_pages").alias("avg_pages_per_session"),
                    F.avg("session_duration_sec").alias("avg_session_duration_sec"),
                    F.max("session_duration_sec").alias("max_session_duration_sec")
                )
                
                # Join and create segments
                user_profile = user_events.join(
                    user_clicks,
                    on="user_id",
                    how="outer"
                )
                
                # Create segments based on engagement
                logger.info("🎯 Creating user segments based on engagement")
                
                segmented_users = user_profile.withColumn(
                    "engagement_score",
                    (
                        col("total_events") * 0.5 +
                        col("total_clicks") * 0.3 +
                        col("session_count") * 0.2
                    ) / 100
                ).withColumn(
                    "user_segment",
                    when(col("engagement_score") > 100, "VIP")
                    .when(col("engagement_score") > 50, "Active")
                    .when(col("engagement_score") > 20, "Regular")
                    .otherwise("Inactive")
                ).withColumn(
                    "session_frequency",
                    when(col("session_count") > 50, "Very High")
                    .when(col("session_count") > 20, "High")
                    .when(col("session_count") > 5, "Medium")
                    .otherwise("Low")
                ).withColumn(
                    "content_interest",
                    when(col("event_type_count") > 4, "Diverse")
                    .when(col("event_type_count") > 2, "Selected")
                    .otherwise("Limited")
                ).withColumn(
                    "device_preference",
                    when(col("app_type_count") > 1, "Multi-device")
                    .otherwise("Single-device")
                ).withColumn(
                    "processing_time",
                    current_timestamp()
                )
                
                # Select and order columns
                final_segments = segmented_users.select(
                    "user_id",
                    "user_segment",
                    "engagement_score",
                    "session_frequency",
                    "content_interest",
                    "device_preference",
                    "total_events",
                    "session_count",
                    "total_clicks",
                    "avg_clicks_per_session",
                    "avg_pages_per_session",
                    "avg_session_duration_sec",
                    "processing_time"
                )
                
                # Write output
                output_path = os.path.join(OUTPUTS_DIR, "user_segments")
                logger.info(f"💾 Writing user segments to {output_path}")
                
                final_segments.write.mode("overwrite").parquet(output_path)
                
                # Print segment distribution
                logger.info("📊 User Segment Distribution:")
                distributions = final_segments.groupBy("user_segment").count()
                distributions.show()
                
                logger.info(f"✅ User Segmentation completed")
                
            except Exception as e:
                logger.warning(f"⚠️  Could not process user data: {e}")
                logger.info("Data will be available once events are aggregated")
            
        except Exception as e:
            logger.error(f"❌ Error in User Segmentation Job: {e}")
            raise
    
    def stop(self):
        """Stop the Spark session"""
        try:
            if self.spark:
                logger.info("⏹️  Stopping Spark Session")
                self.spark.stop()
                logger.info("✅ Spark Session stopped")
        except Exception as e:
            logger.error(f"❌ Error stopping job: {e}")


def main():
    """Main entry point"""
    parser = argparse.ArgumentParser(description="User Segmentation Batch Job")
    parser.add_argument(
        "--lookback-days",
        type=int,
        default=30,
        help="Number of days to look back for segmentation (default: 30)"
    )
    
    args = parser.parse_args()
    
    job = UserSegmentationJob()
    
    try:
        job.start(lookback_days=args.lookback_days)
    except Exception as e:
        logger.error(f"Fatal error: {e}")
        job.stop()
        sys.exit(1)


if __name__ == "__main__":
    main()
