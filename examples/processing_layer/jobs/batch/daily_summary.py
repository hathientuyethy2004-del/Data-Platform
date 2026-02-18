"""
Batch Job: Daily Summary
Daily summary statistics and KPIs across all sources
"""

import sys
import os
import argparse
from datetime import datetime, timedelta

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from pyspark.sql import SparkSession, Window
from pyspark.sql import functions as F
from pyspark.sql.functions import col, date, count, sum as spark_sum, avg, percentile_approx, current_timestamp, lit

from configs.spark_config import OUTPUTS_DIR
from configs.logging_config import setup_logger

logger = setup_logger(__name__)


class DailySummaryJob:
    """Generate daily summary statistics"""
    
    def __init__(self, app_name: str = "daily-summary-job"):
        self.app_name = app_name
        self.spark = None
    
    def start(self, target_date: str = None):
        """
        Start the batch job
        
        Args:
            target_date: Target date in format 'YYYY-MM-DD' (defaults to yesterday)
        """
        try:
            logger.info("🚀 Starting Daily Summary Job")
            
            # Create Spark session
            self.spark = SparkSession.builder \
                .appName(self.app_name) \
                .getOrCreate()
            
            # If target date not specified, use yesterday
            if target_date is None:
                yesterday = datetime.utcnow().date() - timedelta(days=1)
                target_date = yesterday.strftime("%Y-%m-%d")
            
            logger.info(f"📅 Processing date: {target_date}")
            
            # Try to read data from streaming outputs
            events_path = os.path.join(OUTPUTS_DIR, "events_aggregated_realtime")
            clickstream_path = os.path.join(OUTPUTS_DIR, "clickstream_sessions")
            
            try:
                # Load data
                events_df = self.spark.read.parquet(events_path)
                clickstream_df = self.spark.read.parquet(clickstream_path)
                
                # Calculate daily events summary
                logger.info("📊 Calculating daily events summary")
                daily_events = events_df.select(
                    date(col("window_start")).alias("event_date"),
                    col("event_type"),
                    col("app_type"),
                    col("event_count")
                ).groupBy(
                    "event_date", "event_type", "app_type"
                ).agg(
                    spark_sum("event_count").alias("total_events"),
                    count("*").alias("aggregation_points")
                )
                
                # Calculate daily clickstream summary
                logger.info("📊 Calculating daily clickstream summary")
                daily_clickstream = clickstream_df.select(
                    date(col("session_start")).alias("event_date"),
                    col("total_clicks"),
                    col("unique_pages"),
                    col("session_duration_sec")
                ).groupBy(
                    "event_date"
                ).agg(
                    count("*").alias("sessions"),
                    spark_sum("total_clicks").alias("total_clicks"),
                    avg("total_clicks").alias("avg_clicks_per_session"),
                    percentile_approx("session_duration_sec", 0.5).alias("median_session_duration"),
                    percentile_approx("session_duration_sec", 0.95).alias("p95_session_duration"),
                    avg("unique_pages").alias("avg_pages_per_session")
                )
                
                # Combine summaries
                daily_summary = daily_events.select("event_date").distinct() \
                    .join(daily_events, "event_date", "left") \
                    .join(daily_clickstream, "event_date", "left") \
                    .withColumn("processing_time", current_timestamp())
                
                # Write output
                output_path = os.path.join(OUTPUTS_DIR, "daily_summaries")
                logger.info(f"💾 Writing daily summary to {output_path}")
                
                daily_summary.write.mode("append").parquet(output_path)
                logger.info(f"✅ Daily summary completed for {target_date}")
                
            except Exception as e:
                logger.warning(f"⚠️  Could not read/aggregate data: {e}")
                logger.info("Data will be available once streaming jobs have processed events")
            
        except Exception as e:
            logger.error(f"❌ Error in Daily Summary Job: {e}")
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
    parser = argparse.ArgumentParser(description="Daily Summary Batch Job")
    parser.add_argument(
        "--target-date",
        type=str,
        help="Target date in format 'YYYY-MM-DD'"
    )
    
    args = parser.parse_args()
    
    job = DailySummaryJob()
    
    try:
        job.start(target_date=args.target_date)
    except Exception as e:
        logger.error(f"Fatal error: {e}")
        job.stop()
        sys.exit(1)


if __name__ == "__main__":
    main()
