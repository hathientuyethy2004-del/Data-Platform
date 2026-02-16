"""
Streaming Job: Clickstream Analysis
Real-time clickstream path analysis and user journey tracking
"""

import sys
import os
import json

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from pyspark.sql import SparkSession, Window
from pyspark.sql import functions as F
from pyspark.sql.functions import from_json, col, window, count, row_number, current_timestamp

from configs.spark_config import (
    KAFKA_BOOTSTRAP_SERVER, CHECKPOINT_DIR, OUTPUTS_DIR
)
from configs.logging_config import setup_logger
from utils.spark_utils import create_spark_session, read_kafka_stream, write_parquet_stream

logger = setup_logger(__name__)


class ClickstreamAnalysisJob:
    """Real-time clickstream path analysis"""
    
    def __init__(self, app_name: str = "clickstream-analysis-job"):
        self.app_name = app_name
        self.spark = None
        self.query = None
    
    def start(self):
        """Start the streaming job"""
        try:
            logger.info("🚀 Starting Clickstream Analysis Job")
            
            # Create Spark session
            self.spark = create_spark_session(self.app_name)
            
            # Read from Kafka
            df = read_kafka_stream(
                spark=self.spark,
                bootstrap_servers=KAFKA_BOOTSTRAP_SERVER,
                topics=["topic_clickstream"],
                group_id="processing-clickstream-analysis",
                starting_offsets="latest"
            )
            
            # Parse Kafka value as JSON
            logger.info("📝 Parsing Kafka clickstream messages")
            schema = """
                event_id STRING,
                user_id STRING,
                page_url STRING,
                timestamp STRING,
                event_type STRING,
                element_id STRING,
                x_pos DOUBLE,
                y_pos DOUBLE,
                device_type STRING,
                session_id STRING
            """
            
            clicks_df = df.select(
                from_json(col("value").cast("string"), schema).alias("data")
            ).select("data.*") \
             .withColumn("timestamp", F.to_timestamp(col("timestamp"), "yyyy-MM-dd HH:mm:ss.SSS"))
            
            # Analyze click patterns per session
            logger.info("🔗 Analyzing click patterns in sessions")
            
            # Window function to get sequence of clicks per session
            window_spec = Window.partitionBy("session_id").orderBy("timestamp")
            
            click_sequence_df = clicks_df.withColumn(
                "click_sequence",
                row_number().over(window_spec)
            ).select(
                col("session_id"),
                col("user_id"),
                col("timestamp"),
                col("page_url"),
                col("element_id"),
                col("event_type"),
                col("device_type"),
                col("click_sequence")
            )
            
            # Aggregate per session
            session_summary = clicks_df.groupBy(
                "session_id",
                "user_id"
            ).agg(
                F.count("*").alias("total_clicks"),
                F.countDistinct("page_url").alias("unique_pages"),
                F.countDistinct("element_id").alias("unique_elements"),
                F.min("timestamp").alias("session_start"),
                F.max("timestamp").alias("session_end"),
                F.collect_list("page_url").alias("page_path"),
                current_timestamp().alias("processing_time")
            ).select(
                col("session_id"),
                col("user_id"),
                col("total_clicks"),
                col("unique_pages"),
                col("unique_elements"),
                col("session_start"),
                col("session_end"),
                (F.unix_timestamp("session_end") - F.unix_timestamp("session_start")).alias("session_duration_sec"),
                col("page_path"),
                col("processing_time")
            )
            
            # Write to Parquet
            checkpoint_path = os.path.join(CHECKPOINT_DIR, "clickstream_analysis")
            output_path = os.path.join(OUTPUTS_DIR, "clickstream_sessions")
            
            self.query = write_parquet_stream(
                df=session_summary,
                output_path=output_path,
                checkpoint_dir=checkpoint_path,
                output_mode="append"
            )
            
            logger.info(f"✅ Clickstream Analysis Job started")
            logger.info(f"   Output: {output_path}")
            logger.info(f"   Checkpoint: {checkpoint_path}")
            
            # Await termination
            self.query.awaitTermination()
            
        except Exception as e:
            logger.error(f"❌ Error in Clickstream Analysis Job: {e}")
            raise
    
    def stop(self):
        """Stop the streaming job"""
        try:
            if self.query:
                logger.info("⏹️  Stopping Clickstream Analysis Job")
                self.query.stop()
                logger.info("✅ Clickstream Analysis Job stopped")
            
            if self.spark:
                self.spark.stop()
        except Exception as e:
            logger.error(f"❌ Error stopping job: {e}")


def main():
    """Main entry point"""
    job = ClickstreamAnalysisJob()
    
    try:
        job.start()
    except KeyboardInterrupt:
        logger.info("👋 Received interrupt signal")
        job.stop()
    except Exception as e:
        logger.error(f"Fatal error: {e}")
        job.stop()
        sys.exit(1)


if __name__ == "__main__":
    main()
