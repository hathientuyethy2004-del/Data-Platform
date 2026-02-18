"""
Spark Session Factory & Utilities
Tạo và quản lý Spark Sessions
"""

import os
from pyspark.sql import SparkSession
from pyspark.sql.types import StructType, StructField, StringType, IntegerType, LongType, DoubleType, TimestampType
from configs.spark_config import get_spark_config, SPARK_APP_NAME, LOG_LEVEL
from configs.logging_config import setup_logger

logger = setup_logger(__name__)

# ============================================================================
# Spark Session Factory
# ============================================================================

def create_spark_session(app_name: str = None, enable_hive: bool = False) -> SparkSession:
    """
    Create or get a Spark session
    
    Args:
        app_name: Application name for Spark
        enable_hive: Enable Hive support
        
    Returns:
        SparkSession instance
    """
    if app_name is None:
        app_name = SPARK_APP_NAME
    
    logger.info(f"🔧 Creating Spark Session: {app_name}")
    
    # Get Spark config
    spark_config = get_spark_config()
    
    # Build SparkSession
    builder = SparkSession.builder.appName(app_name)
    
    for key, value in spark_config.items():
        builder = builder.config(key, value)
    
    if enable_hive:
        builder = builder.enableHiveSupport()
    
    spark = builder.getOrCreate()
    
    # Set log level
    spark.sparkContext.setLogLevel(LOG_LEVEL)
    
    logger.info(f"✅ Spark Session created: {spark.version}")
    
    return spark


def stop_spark_session(spark: SparkSession):
    """Stop Spark session"""
    if spark:
        logger.info("⏹️  Stopping Spark Session")
        spark.stop()
        logger.info("✅ Spark Session stopped")


# ============================================================================
# Schema Definitions for Kafka Topics
# ============================================================================

def get_app_events_schema() -> StructType:
    """Schema for topic_app_events"""
    return StructType([
        StructField("event_type", StringType(), True),
        StructField("user_id", StringType(), True),
        StructField("session_id", StringType(), True),
        StructField("timestamp", StringType(), True),
        StructField("app_type", StringType(), True),
        StructField("properties", StringType(), True),
        StructField("source", StringType(), True),
        StructField("version", StringType(), True),
    ])


def get_cdc_changes_schema() -> StructType:
    """Schema for topic_cdc_changes"""
    return StructType([
        StructField("op", StringType(), True),
        StructField("table", StringType(), True),
        StructField("before", StringType(), True),
        StructField("after", StringType(), True),
        StructField("ts_ms", LongType(), True),
        StructField("db", StringType(), True),
        StructField("schema", StringType(), True),
        StructField("txId", LongType(), True),
        StructField("lsn", LongType(), True),
    ])


def get_clickstream_schema() -> StructType:
    """Schema for topic_clickstream"""
    return StructType([
        StructField("event_id", StringType(), True),
        StructField("user_id", StringType(), True),
        StructField("page_url", StringType(), True),
        StructField("timestamp", StringType(), True),
        StructField("event_type", StringType(), True),
        StructField("element_id", StringType(), True),
        StructField("x_pos", DoubleType(), True),
        StructField("y_pos", DoubleType(), True),
        StructField("device_type", StringType(), True),
        StructField("session_id", StringType(), True),
    ])


def get_external_data_schema() -> StructType:
    """Schema for topic_external_data"""
    return StructType([
        StructField("data_source", StringType(), True),
        StructField("timestamp", StringType(), True),
        StructField("data", StringType(), True),
        StructField("location", StringType(), True),
        StructField("value", StringType(), True),
        StructField("status", StringType(), True),
    ])


# ============================================================================
# Kafka Source Helper
# ============================================================================

def read_kafka_stream(
    spark: SparkSession,
    bootstrap_servers: str,
    topics: list,
    group_id: str,
    starting_offsets: str = "latest"
):
    """
    Read Kafka stream as DataFrame
    
    Args:
        spark: SparkSession
        bootstrap_servers: Kafka bootstrap servers (comma-separated)
        topics: List of topics to subscribe
        group_id: Consumer group ID
        starting_offsets: Starting offset strategy (latest, earliest)
        
    Returns:
        DataFrame with Kafka data (including key, value, timestamp, partition, offset)
    """
    logger.info(f"📥 Setting up Kafka stream reader for topics: {topics}")
    
    df = spark.readStream \
        .format("kafka") \
        .option("kafka.bootstrap.servers", bootstrap_servers) \
        .option("subscribe", ",".join(topics)) \
        .option("group.id", group_id) \
        .option("startingOffsets", starting_offsets) \
        .option("failOnDataLoss", "false") \
        .option("kafka.session.timeout.ms", "30000") \
        .load()
    
    logger.info(f"✅ Kafka stream reader created")
    
    return df


def write_kafka_stream(
    df,
    bootstrap_servers: str,
    topic: str,
    checkpoint_dir: str,
    output_mode: str = "append"
):
    """
    Write DataFrame to Kafka topic
    
    Args:
        df: DataFrame to write
        bootstrap_servers: Kafka bootstrap servers
        topic: Target Kafka topic
        checkpoint_dir: Checkpoint directory for recovery
        output_mode: append, update, complete
        
    Returns:
        StreamingQuery
    """
    logger.info(f"📤 Writing stream to Kafka topic: {topic}")
    
    query = df.select("value") \
        .writeStream \
        .format("kafka") \
        .option("kafka.bootstrap.servers", bootstrap_servers) \
        .option("topic", topic) \
        .option("checkpointLocation", checkpoint_dir) \
        .outputMode(output_mode) \
        .start()
    
    logger.info(f"✅ Kafka stream writer started: {topic}")
    
    return query


def write_parquet_stream(
    df,
    output_path: str,
    checkpoint_dir: str,
    output_mode: str = "append"
):
    """
    Write DataFrame to Parquet in append mode
    
    Args:
        df: DataFrame to write
        output_path: Path to output
        checkpoint_dir: Checkpoint directory
        output_mode: append, update, complete
        
    Returns:
        StreamingQuery
    """
    logger.info(f"💾 Writing stream to Parquet: {output_path}")
    
    query = df.writeStream \
        .format("parquet") \
        .option("path", output_path) \
        .option("checkpointLocation", checkpoint_dir) \
        .outputMode(output_mode) \
        .start()
    
    logger.info(f"✅ Parquet stream writer started: {output_path}")
    
    return query


def write_csv_stream(
    df,
    output_path: str,
    checkpoint_dir: str,
    output_mode: str = "append"
):
    """
    Write DataFrame to CSV in append mode
    
    Args:
        df: DataFrame to write
        output_path: Path to output
        checkpoint_dir: Checkpoint directory
        output_mode: append, update, complete
        
    Returns:
        StreamingQuery
    """
    logger.info(f"📄 Writing stream to CSV: {output_path}")
    
    query = df.writeStream \
        .format("csv") \
        .option("path", output_path) \
        .option("header", "true") \
        .option("checkpointLocation", checkpoint_dir) \
        .outputMode(output_mode) \
        .start()
    
    logger.info(f"✅ CSV stream writer started: {output_path}")
    
    return query
