"""
Kafka Cluster Configuration
Cấu hình Kafka Cluster cho INGESTION LAYER
"""

import os
from typing import Dict, List

# ============================================================================
# Kafka Broker Configuration
# ============================================================================

KAFKA_BROKERS = os.getenv("KAFKA_BROKERS", "localhost:9092").split(",")
KAFKA_BOOTSTRAP_SERVER = os.getenv("KAFKA_BOOTSTRAP_SERVER", "localhost:9092")

# Consumer Group Configuration
CONSUMER_GROUPS = {
    "app_events_consumer": {
        "topics": ["topic_app_events"],
        "description": "Consume application user events from mobile/web"
    },
    "cdc_consumer": {
        "topics": ["topic_cdc_changes"],
        "description": "Consume PostgreSQL CDC change events"
    },
    "clickstream_consumer": {
        "topics": ["topic_clickstream"],
        "description": "Consume clickstream/navigation events"
    },
    "external_data_consumer": {
        "topics": ["topic_external_data"],
        "description": "Consume external data sources (weather, maps, etc)"
    },
    "unified_consumer": {
        "topics": ["topic_app_events", "topic_cdc_changes", "topic_clickstream", "topic_external_data"],
        "description": "Consume all data sources for unified processing"
    }
}

# ============================================================================
# Kafka Consumer Configuration
# ============================================================================

CONSUMER_CONFIG = {
    "bootstrap.servers": KAFKA_BOOTSTRAP_SERVER,
    "group.id": "ingestion-layer-consumer-group",
    "auto.offset.reset": "earliest",  # Start từ beginning nếu không có offset
    "enable.auto.commit": True,
    "auto.commit.interval.ms": 5000,
    "session.timeout.ms": 30000,
    "max.poll.records": 500,
    "fetch.min.bytes": 1024,
    "fetch.max.wait.ms": 500,
    "connections.max.idle.ms": 300000
}

# ============================================================================
# Kafka Topics Configuration
# ============================================================================

TOPICS_CONFIG = {
    "topic_app_events": {
        "partitions": 6,
        "replication_factor": 1,
        "compression_type": "snappy",
        "retention_ms": 604800000,  # 7 days
        "segment_ms": 86400000,
        "cleanup_policy": "delete",
        "min_insync_replicas": 1,
        "description": "User events from mobile and web applications"
    },
    "topic_cdc_changes": {
        "partitions": 4,
        "replication_factor": 1,
        "compression_type": "snappy",
        "retention_ms": 604800000,
        "segment_ms": 86400000,
        "cleanup_policy": "delete",
        "min_insync_replicas": 1,
        "description": "PostgreSQL CDC (Change Data Capture) events"
    },
    "topic_clickstream": {
        "partitions": 8,
        "replication_factor": 1,
        "compression_type": "snappy",
        "retention_ms": 604800000,
        "segment_ms": 86400000,
        "cleanup_policy": "delete",
        "min_insync_replicas": 1,
        "description": "Clickstream and user navigation events"
    },
    "topic_external_data": {
        "partitions": 3,
        "replication_factor": 1,
        "compression_type": "snappy",
        "retention_ms": 604800000,
        "segment_ms": 86400000,
        "cleanup_policy": "delete",
        "min_insync_replicas": 1,
        "description": "External data sources (weather, maps, social media)"
    }
}

# ============================================================================
# Ingestion Configuration
# ============================================================================

INGESTION_CONFIG = {
    "batch_size": 100,
    "batch_timeout_ms": 5000,
    "retry_attempts": 3,
    "retry_backoff_ms": 1000,
    "enable_validation": True,
    "enable_monitoring": True,
    "enable_dead_letter_queue": True,
    "dead_letter_topic": "topic_ingestion_errors"
}

# ============================================================================
# Data Validation Rules
# ============================================================================

VALIDATION_RULES = {
    "topic_app_events": {
        "required_fields": ["event_type", "user_id", "session_id", "timestamp"],
        "schema_subject": "AppEvent-value",
        "timeout_seconds": 30
    },
    "topic_cdc_changes": {
        "required_fields": ["op", "table", "before", "after", "ts_ms"],
        "schema_subject": "CDCChange-value",
        "timeout_seconds": 30
    },
    "topic_clickstream": {
        "required_fields": ["event_id", "user_id", "page_url", "timestamp"],
        "schema_subject": "Clickstream-value",
        "timeout_seconds": 30
    },
    "topic_external_data": {
        "required_fields": ["data_source", "timestamp"],
        "schema_subject": "ExternalData-value",
        "timeout_seconds": 30
    }
}

# ============================================================================
# Monitoring Configuration
# ============================================================================

MONITORING_CONFIG = {
    "metrics_interval_sec": 10,
    "log_interval_sec": 30,
    "enable_prometheus": True,
    "prometheus_port": 8001,
    "enable_health_check": True,
    "health_check_port": 8002,
    "track_lag": True,
    "track_throughput": True,
    "track_errors": True,
    "alert_threshold": {
        "consumer_lag": 10000,
        "error_rate": 0.05,
        "throughput_min": 100  # messages/sec
    }
}

# ============================================================================
# Schema Registry Configuration
# ============================================================================

SCHEMA_REGISTRY_CONFIG = {
    "url": os.getenv("SCHEMA_REGISTRY_URL", "http://schema-registry:8081"),
    "timeout_seconds": 10,
    "cache_schemas": True,
    "validate_on_ingestion": True
}

# ============================================================================
# Storage Configuration
# ============================================================================

STORAGE_CONFIG = {
    "checkpoint_dir": "/tmp/ingestion_checkpoints",
    "metrics_dir": "/tmp/ingestion_metrics",
    "log_dir": "/var/log/ingestion_layer",
    "enable_local_cache": True,
    "cache_size_mb": 1024
}

# ============================================================================
# Logging Configuration
# ============================================================================

LOGGING_CONFIG = {
    "version": 1,
    "disable_existing_loggers": False,
    "formatters": {
        "standard": {
            "format": "%(asctime)s [%(levelname)s] %(name)s: %(message)s"
        },
        "detailed": {
            "format": "%(asctime)s [%(levelname)s] %(name)s:%(funcName)s:%(lineno)d: %(message)s"
        }
    },
    "handlers": {
        "console": {
            "class": "logging.StreamHandler",
            "level": "INFO",
            "formatter": "standard",
            "stream": "ext://sys.stdout"
        },
        "file": {
            "class": "logging.handlers.RotatingFileHandler",
            "level": "DEBUG",
            "formatter": "detailed",
            "filename": "/var/log/ingestion_layer/ingestion.log",
            "maxBytes": 10485760,  # 10MB
            "backupCount": 5
        }
    },
    "root": {
        "level": "INFO",
        "handlers": ["console", "file"]
    }
}


def get_consumer_config(group_id: str = None, topics: List[str] = None) -> Dict:
    """Get consumer configuration for a specific group"""
    config = CONSUMER_CONFIG.copy()
    if group_id:
        config["group.id"] = group_id
    return config


def get_topic_config(topic_name: str) -> Dict:
    """Get configuration for a specific topic"""
    return TOPICS_CONFIG.get(topic_name, {})


def validate_config() -> bool:
    """Validate all configuration settings"""
    try:
        assert KAFKA_BROKERS, "KAFKA_BROKERS not configured"
        assert CONSUMER_GROUPS, "CONSUMER_GROUPS not configured"
        assert TOPICS_CONFIG, "TOPICS_CONFIG not configured"
        return True
    except AssertionError as e:
        print(f"❌ Configuration validation failed: {e}")
        return False
