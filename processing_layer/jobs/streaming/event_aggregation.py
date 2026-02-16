"""
Streaming Job: Event Aggregation
Real-time aggregation of app events by user and event type
"""

import sys
import os
import json
from datetime import datetime

# Add paths
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from pyspark.sql import SparkSession
from pyspark.sql import functions as F
from pyspark.sql.functions import from_json, col, window, count, current_timestamp

from configs.spark_config import (
    KAFKA_BOOTSTRAP_SERVER, CHECKPOINT_DIR, OUTPUTS_DIR, STREAMING_MAX_OFFSETS_PER_TRIGGER
)
from configs.logging_config import setup_logger
from utils.spark_utils import create_spark_session, read_kafka_stream, write_parquet_stream
from utils.transformations import DataTransformations

logger = setup_logger(__name__)

# ============================================================================
# Event Aggregation Job
# ============================================================================

class EventAggregationJob:
    """Real-time aggregation of app events"""
    
    def __init__(self, app_name: str = "event-aggregation-job"):
        self.app_name = app_name
        self.spark = None
        self.query = None
    
    def start(self):
        """Start the streaming job"""
        try:
            logger.info("🚀 Starting Event Aggregation Job")
            
            # Create Spark session
            self.spark = create_spark_session(self.app_name)
            
            # Read from Kafka
            df = read_kafka_stream(
                spark=self.spark,
                bootstrap_servers=KAFKA_BOOTSTRAP_SERVER,
                topics=["topic_app_events"],
                group_id="processing-event-aggregation",
                starting_offsets="latest"
            )
            
            # Parse Kafka value as JSON
            logger.info("📝 Parsing Kafka messages")
            schema = "event_type STRING, user_id STRING, session_id STRING, timestamp STRING, app_type STRING, properties STRING"
            
            events_df = df.select(
                from_json(col("value").cast("string"), schema).alias("data")
            ).select("data.*") \
             .withColumn("timestamp", F.to_timestamp(col("timestamp"), "yyyy-MM-dd HH:mm:ss.SSS"))
            
            # Aggregate by user and event type in 1-minute windows
            logger.info("📊 Aggregating by user and event type (1-minute windows)")
            aggregated_df = events_df.groupBy(
                window(col("timestamp"), "1 minute", "1 minute"),
                col("user_id"),
                col("event_type"),
                col("app_type")
            ).agg(
                count("*").alias("event_count"),
                F.collect_list("session_id").alias("session_ids")
            ).select(
                F.col("window.start").alias("window_start"),
                F.col("window.end").alias("window_end"),
                col("user_id"),
                col("event_type"),
                col("app_type"),
                col("event_count"),
                col("session_ids"),
                current_timestamp().alias("processing_time")
            )
            
            # Write to Parquet with checkpoint
            checkpoint_path = os.path.join(CHECKPOINT_DIR, "event_aggregation")
            output_path = os.path.join(OUTPUTS_DIR, "events_aggregated_realtime")
            
            self.query = write_parquet_stream(
                df=aggregated_df,
                output_path=output_path,
                checkpoint_dir=checkpoint_path,
                output_mode="append"
            )
            
            logger.info(f"✅ Event Aggregation Job started")
            logger.info(f"   Output: {output_path}")
            logger.info(f"   Checkpoint: {checkpoint_path}")
            
            # Await termination
            self.query.awaitTermination()
            
        except Exception as e:
            logger.error(f"❌ Error in Event Aggregation Job: {e}")
            raise
    
    def stop(self):
        """Stop the streaming job"""
        try:
            if self.query:
                logger.info("⏹️  Stopping Event Aggregation Job")
                self.query.stop()
                logger.info("✅ Event Aggregation Job stopped")
            
            if self.spark:
                self.spark.stop()
        except Exception as e:
            logger.error(f"❌ Error stopping job: {e}")


def main():
    """Main entry point"""
    job = EventAggregationJob()
    
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
