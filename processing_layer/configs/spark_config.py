"""
Spark Configuration Module
Cấu hình cho Spark Session (Streaming và Batch)
"""

import os
from typing import Dict, Any

# ============================================================================
# Kafka Configuration (Source)
# ============================================================================
KAFKA_BOOTSTRAP_SERVER = os.getenv("KAFKA_BOOTSTRAP_SERVER", "localhost:29092")
KAFKA_BROKERS = os.getenv("KAFKA_BROKERS", "localhost:29092").split(",")

# ============================================================================
# Spark Configuration
# ============================================================================

# Application name
SPARK_APP_NAME = os.getenv("SPARK_APP_NAME", "data-platform-processing")

# Master URL - local for dev, spark://master:7077 for cluster
SPARK_MASTER = os.getenv("SPARK_MASTER", "local[*]")

# Executor configuration
EXECUTOR_MEMORY = os.getenv("EXECUTOR_MEMORY", "2g")
EXECUTOR_CORES = os.getenv("EXECUTOR_CORES", "2")
DRIVER_MEMORY = os.getenv("DRIVER_MEMORY", "2g")
DRIVER_CORES = os.getenv("DRIVER_CORES", "2")

# Streaming configuration
STREAMING_BATCH_INTERVAL_MS = int(os.getenv("STREAMING_BATCH_INTERVAL_MS", "10000"))  # 10 seconds
STREAMING_TIMEOUT_MS = int(os.getenv("STREAMING_TIMEOUT_MS", "30000"))  # 30 seconds
STREAMING_MAX_OFFSETS_PER_TRIGGER = int(os.getenv("STREAMING_MAX_OFFSETS_PER_TRIGGER", "10000"))

# Checkpoint configuration
CHECKPOINT_DIR = os.getenv("CHECKPOINT_DIR", "/tmp/spark-checkpoints")
OUTPUTS_DIR = os.getenv("OUTPUTS_DIR", "/workspaces/Data-Platform/processing_layer/outputs")

# Log level
LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO")

# ============================================================================
# Spark Session Configuration Dict
# ============================================================================

def get_spark_config() -> Dict[str, Any]:
    """
    Get Spark configuration as dictionary
    
    Returns:
        Dict with Spark configuration key-value pairs
    """
    return {
        "spark.app.name": SPARK_APP_NAME,
        "spark.master": SPARK_MASTER,
        
        # Memory and core settings
        "spark.executor.memory": EXECUTOR_MEMORY,
        "spark.executor.cores": EXECUTOR_CORES,
        "spark.driver.memory": DRIVER_MEMORY,
        "spark.driver.cores": DRIVER_CORES,
        
        # Streaming settings
        "spark.streaming.backpressure.enabled": "true",
        "spark.streaming.backpressure.initialRate": "100000",
        "spark.streaming.kafka.maxRatePerPartition": "100000",
        
        # Performance tuning
        "spark.sql.shuffle.partitions": "200",
        "spark.default.parallelism": "200",
        "spark.sql.adaptive.enabled": "true",
        "spark.sql.adaptive.coalescePartitions.enabled": "true",
        
        # Logging
        "spark.driver.log.level": LOG_LEVEL,
        "spark.driver.log.dfsDir": "/tmp/spark-logs",
        
        # Serialization
        "spark.serializer": "org.apache.spark.serializer.KryoSerializer",
        "spark.kryoserializer.buffer.max": "512m",
        
        # Network
        "spark.network.timeout": "120s",
        "spark.executor.heartbeatInterval": "60s",
        
        # Delta Lake (if using)
        "spark.sql.extensions": "io.delta.sql.DeltaSparkSessionExtension",
        "spark.sql.catalog.spark_catalog": "org.apache.spark.sql.delta.catalog.DeltaCatalog",
    }


# ============================================================================
# Output Configuration (Streaming & Batch)
# ============================================================================

OUTPUT_FORMATS = {
    "parquet": {
        "compression": "snappy",
        "mode": "overwrite"
    },
    "delta": {
        "mode": "overwrite"
    },
    "csv": {
        "mode": "overwrite",
        "header": "true"
    },
    "kafka": {
        "mode": "append"
    }
}

# ============================================================================
# Processing Job Configuration
# ============================================================================

PROCESSING_JOBS = {
    "event_aggregation": {
        "type": "streaming",
        "enabled": True,
        "description": "Real-time aggregation of app events by user and time"
    },
    "clickstream_analysis": {
        "type": "streaming",
        "enabled": True,
        "description": "Real-time clickstream path analysis"
    },
    "data_enrichment": {
        "type": "streaming",
        "enabled": True,
        "description": "Enrich events with user attributes and device info"
    },
    "cdc_transformation": {
        "type": "streaming",
        "enabled": True,
        "description": "Transform CDC events into upserts and deletes"
    },
    "hourly_aggregate": {
        "type": "batch",
        "enabled": True,
        "description": "Hourly aggregation of all sources",
        "schedule": "0 0 * * * ?"  # Every hour
    },
    "daily_summary": {
        "type": "batch",
        "enabled": True,
        "description": "Daily summary statistics",
        "schedule": "0 0 0 * * ?"  # Daily at midnight
    },
    "user_segment": {
        "type": "batch",
        "enabled": True,
        "description": "User segmentation and profiling",
        "schedule": "0 0 2 * * ?"  # Daily at 2 AM
    }
}

# ============================================================================
# Kafka Topics & Consumer Configuration
# ============================================================================

KAFKA_TOPICS = {
    "topic_app_events": {
        "description": "Application user events",
        "partitions": 6
    },
    "topic_cdc_changes": {
        "description": "PostgreSQL CDC events",
        "partitions": 4
    },
    "topic_clickstream": {
        "description": "Clickstream events",
        "partitions": 8
    },
    "topic_external_data": {
        "description": "External data sources",
        "partitions": 3
    }
}

OUTPUT_TOPICS = {
    "topic_events_aggregated": "Aggregated events (streaming)",
    "topic_clicks_path": "Click path analysis (streaming)",
    "topic_enriched_events": "Enriched events (streaming)",
    "topic_cdc_upserts": "CDC upsert operations (streaming)"
}

# ============================================================================
# Default Consumer Group Configuration
# ============================================================================

CONSUMER_GROUP_PREFIX = "processing-layer"

KAFKA_CONSUMER_CONFIG = {
    "bootstrap.servers": KAFKA_BOOTSTRAP_SERVER,
    "auto.offset.reset": "latest",  # Start from latest for streaming
    "enable.auto.commit": True,
    "auto.commit.interval.ms": 5000,
    "session.timeout.ms": 30000,
    "max.poll.records": 500,
    "fetch.min.bytes": 1024,
    "fetch.max.wait.ms": 500,
    "connections.max.idle.ms": 300000,
    # Kafka-Spark specific
    "startingOffsets": "latest",
    "endingOffsets": "latest",
    "maxOffsetsPerTrigger": STREAMING_MAX_OFFSETS_PER_TRIGGER,
    "failOnDataLoss": False
}
