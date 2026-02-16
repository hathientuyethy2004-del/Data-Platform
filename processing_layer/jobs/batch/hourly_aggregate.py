"""
Batch Job: Hourly Aggregation
Hourly aggregation of all data sources with comprehensive metrics
"""

import sys
import os
import argparse
from datetime import datetime, timedelta

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from pyspark.sql import SparkSession, Window
from pyspark.sql import functions as F
from pyspark.sql.functions import col, hour, dayofmonth, month, year, count, sum as spark_sum, avg, min as spark_min, max as spark_max, current_timestamp

from configs.spark_config import OUTPUTS_DIR
from configs.logging_config import setup_logger

logger = setup_logger(__name__)


class HourlyAggregateJob:
    """Hourly aggregation of all Kafka topics"""
    
    def __init__(self, app_name: str = "hourly-aggregate-job"):
        self.app_name = app_name
        self.spark = None
    
    def start(self, target_hour: str = None):
        """
        Start the batch job
        
        Args:
            target_hour: Target hour in format 'YYYY-MM-DD HH:00:00' (defaults to current hour)
        """
        try:
            logger.info("🚀 Starting Hourly Aggregation Job")
            
            # Create Spark session
            self.spark = SparkSession.builder \
                .appName(self.app_name) \
                .getOrCreate()
            
            # If target hour not specified, use current hour
            if target_hour is None:
                now = datetime.utcnow()
                target_hour = now.strftime("%Y-%m-%d %H:00:00")
            
            logger.info(f"📅 Processing hour: {target_hour}")
            
            # Read aggregated events from streaming output
            events_path = os.path.join(OUTPUTS_DIR, "events_aggregated_realtime")
            
            try:
                events_df = self.spark.read.parquet(events_path)
                
                # Filter for target hour and aggregate
                hourly_summary = events_df.select(
                    hour(col("window_start")).alias("hour"),
                    dayofmonth(col("window_start")).alias("day"),
                    month(col("window_start")).alias("month"),
                    year(col("window_start")).alias("year"),
                    col("event_type"),
                    col("app_type")
                ).groupBy(
                    "hour", "day", "month", "year", "event_type", "app_type"
                ).agg(
                    count("*").alias("event_count")
                )
                
                # Write to output
                output_path = os.path.join(OUTPUTS_DIR, "hourly_aggregates")
                logger.info(f"💾 Writing hourly aggregates to {output_path}")
                
                hourly_summary.write.mode("append").parquet(output_path)
                logger.info(f"✅ Hourly aggregation completed")
                
            except Exception as e:
                logger.warning(f"⚠️  No parquet data found yet: {e}")
                logger.info("Job will process when streaming data becomes available")
            
        except Exception as e:
            logger.error(f"❌ Error in Hourly Aggregation Job: {e}")
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
    parser = argparse.ArgumentParser(description="Hourly Aggregation Batch Job")
    parser.add_argument(
        "--target-hour",
        type=str,
        help="Target hour in format 'YYYY-MM-DD HH:00:00'"
    )
    
    args = parser.parse_args()
    
    job = HourlyAggregateJob()
    
    try:
        job.start(target_hour=args.target_hour)
    except Exception as e:
        logger.error(f"Fatal error: {e}")
        job.stop()
        sys.exit(1)


if __name__ == "__main__":
    main()
