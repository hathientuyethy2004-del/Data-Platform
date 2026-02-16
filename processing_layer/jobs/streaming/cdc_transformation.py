"""
Streaming Job: CDC Transformation
Transform PostgreSQL CDC events into upsert/delete operations
"""

import sys
import os
import json

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from pyspark.sql import SparkSession
from pyspark.sql import functions as F
from pyspark.sql.functions import from_json, col, current_timestamp, to_timestamp

from configs.spark_config import (
    KAFKA_BOOTSTRAP_SERVER, CHECKPOINT_DIR, OUTPUTS_DIR
)
from configs.logging_config import setup_logger
from utils.spark_utils import create_spark_session, read_kafka_stream, write_parquet_stream

logger = setup_logger(__name__)


class CDCTransformationJob:
    """Transform CDC events into standardized upsert/delete operations"""
    
    def __init__(self, app_name: str = "cdc-transformation-job"):
        self.app_name = app_name
        self.spark = None
        self.query = None
    
    def start(self):
        """Start the streaming job"""
        try:
            logger.info("🚀 Starting CDC Transformation Job")
            
            # Create Spark session
            self.spark = create_spark_session(self.app_name)
            
            # Read from Kafka
            df = read_kafka_stream(
                spark=self.spark,
                bootstrap_servers=KAFKA_BOOTSTRAP_SERVER,
                topics=["topic_cdc_changes"],
                group_id="processing-cdc-transformation",
                starting_offsets="latest"
            )
            
            # Parse Kafka value as JSON
            logger.info("📝 Parsing Kafka CDC messages")
            schema = """
                op STRING,
                table STRING,
                before STRING,
                after STRING,
                ts_ms LONG,
                db STRING,
                schema STRING,
                txId LONG,
                lsn LONG
            """
            
            cdc_df = df.select(
                from_json(col("value").cast("string"), schema).alias("data")
            ).select("data.*") \
             .withColumn("event_timestamp", F.from_unixtime(col("ts_ms") / 1000.0))
            
            # Transform CDC operations
            logger.info("🔄 Transforming CDC operations to standard format")
            
            transformed_df = cdc_df.select(
                col("op").alias("operation"),  # i=insert, u=update, d=delete
                col("table").alias("table_name"),
                col("db").alias("database"),
                col("schema").alias("schema_name"),
                F.when(col("op") == "i", col("after"))
                 .when(col("op") == "u", col("after"))
                 .when(col("op") == "d", col("before"))
                 .alias("record_data"),
                col("before").alias("old_record"),
                col("after").alias("new_record"),
                F.from_unixtime(col("ts_ms") / 1000.0).alias("event_time"),
                col("txId").alias("transaction_id"),
                col("lsn").alias("log_sequence_number"),
                current_timestamp().alias("processing_time"),
                # Create operation description
                F.when(col("op") == "i", "INSERT")
                 .when(col("op") == "u", "UPDATE")
                 .when(col("op") == "d", "DELETE")
                 .otherwise("UNKNOWN")
                 .alias("operation_type")
            )
            
            # Aggregate CDC operations per table
            cdc_summary = cdc_df.groupBy(
                col("table"),
                F.window(F.from_unixtime(col("ts_ms") / 1000.0), "1 minute", "1 minute")
            ).agg(
                F.countDistinct(F.when(col("op") == "i", 1)).alias("insert_count"),
                F.countDistinct(F.when(col("op") == "u", 1)).alias("update_count"),
                F.countDistinct(F.when(col("op") == "d", 1)).alias("delete_count"),
                F.count("*").alias("total_operations")
            ).select(
                F.col("window.start").alias("window_start"),
                F.col("window.end").alias("window_end"),
                col("table"),
                col("insert_count"),
                col("update_count"),
                col("delete_count"),
                col("total_operations"),
                current_timestamp().alias("processing_time")
            )
            
            # Write to Parquet
            checkpoint_path = os.path.join(CHECKPOINT_DIR, "cdc_transformation")
            output_path = os.path.join(OUTPUTS_DIR, "cdc_transformed")
            
            self.query = write_parquet_stream(
                df=transformed_df,
                output_path=output_path,
                checkpoint_dir=checkpoint_path,
                output_mode="append"
            )
            
            logger.info(f"✅ CDC Transformation Job started")
            logger.info(f"   Output: {output_path}")
            logger.info(f"   Checkpoint: {checkpoint_path}")
            
            # Await termination
            self.query.awaitTermination()
            
        except Exception as e:
            logger.error(f"❌ Error in CDC Transformation Job: {e}")
            raise
    
    def stop(self):
        """Stop the streaming job"""
        try:
            if self.query:
                logger.info("⏹️  Stopping CDC Transformation Job")
                self.query.stop()
                logger.info("✅ CDC Transformation Job stopped")
            
            if self.spark:
                self.spark.stop()
        except Exception as e:
            logger.error(f"❌ Error stopping job: {e}")


def main():
    """Main entry point"""
    job = CDCTransformationJob()
    
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
