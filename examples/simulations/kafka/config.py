"""
Kafka Configuration and Utilities
Handles all Kafka topics, producers, and consumers
"""

from enum import Enum
from dataclasses import dataclass
from typing import Optional

class KafkaTopics(str, Enum):
    """Kafka topics for data platform"""
    APP_EVENTS = "topic_app_events"
    CDC_CHANGES = "topic_cdc_changes"
    CLICKSTREAM = "topic_clickstream"
    APP_LOGS = "topic_app_logs"
    EXTERNAL_DATA = "topic_external_data"
    PROCESSED_EVENTS = "topic_processed_events"
    
    # Compacted topics for state stores
    USER_STATE = "topic_user_state"
    BOOKING_STATE = "topic_booking_state"

TOPIC_CONFIGS = {
    "topic_app_events": {
        "partitions": 6,
        "replication_factor": 3,
        "retention_ms": 86400000,  # 1 day
        "segment_ms": 3600000,     # 1 hour
        "cleanup_policy": "delete",
        "compression_type": "snappy"
    },
    "topic_cdc_changes": {
        "partitions": 4,
        "replication_factor": 3,
        "retention_ms": 604800000,  # 7 days
        "cleanup_policy": "delete",
        "compression_type": "snappy"
    },
    "topic_clickstream": {
        "partitions": 8,
        "replication_factor": 3,
        "retention_ms": 259200000,  # 3 days
        "cleanup_policy": "delete",
        "compression_type": "snappy"
    },
    "topic_app_logs": {
        "partitions": 4,
        "replication_factor": 2,
        "retention_ms": 172800000,  # 2 days
        "cleanup_policy": "delete"
    },
    "topic_external_data": {
        "partitions": 3,
        "replication_factor": 2,
        "retention_ms": 2592000000,  # 30 days
        "cleanup_policy": "delete"
    },
    "topic_processed_events": {
        "partitions": 6,
        "replication_factor": 3,
        "retention_ms": 604800000,  # 7 days
        "cleanup_policy": "delete"
    },
    "topic_user_state": {
        "partitions": 6,
        "replication_factor": 3,
        "cleanup_policy": "compact",
        "min_compaction_lag_ms": 3600000,  # 1 hour
        "segment_ms": 3600000
    },
    "topic_booking_state": {
        "partitions": 6,
        "replication_factor": 3,
        "cleanup_policy": "compact",
        "min_compaction_lag_ms": 3600000,  # 1 hour
        "segment_ms": 3600000
    }
}

KAFKA_BROKERS = ["kafka:9092"]
SCHEMA_REGISTRY_URL = "http://schema-registry:8081"

@dataclass
class ProducerConfig:
    """Kafka Producer Configuration"""
    bootstrap_servers: list = None
    value_serializer: callable = None
    acks: str = "all"
    retries: int = 3
    max_in_flight_requests_per_connection: int = 5
    compression_type: str = "snappy"
    linger_ms: int = 10
    batch_size: int = 16384
    
    def __post_init__(self):
        if self.bootstrap_servers is None:
            self.bootstrap_servers = KAFKA_BROKERS

@dataclass
class ConsumerConfig:
    """Kafka Consumer Configuration"""
    bootstrap_servers: list = None
    group_id: str = ""
    auto_offset_reset: str = "earliest"
    enable_auto_commit: bool = False
    value_deserializer: callable = None
    session_timeout_ms: int = 30000
    
    def __post_init__(self):
        if self.bootstrap_servers is None:
            self.bootstrap_servers = KAFKA_BROKERS

def get_producer_config(value_serializer=None):
    """Get producer configuration"""
    return ProducerConfig(value_serializer=value_serializer)

def get_consumer_config(group_id, value_deserializer=None):
    """Get consumer configuration"""
    return ConsumerConfig(
        group_id=group_id,
        value_deserializer=value_deserializer
    )
