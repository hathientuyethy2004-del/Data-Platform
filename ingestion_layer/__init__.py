"""
Ingestion Layer - Data consumption and validation
"""

__version__ = "1.0.0"
__author__ = "Data Platform Team"

from .consumers.kafka_consumer import KafkaIngestionConsumer, create_consumer
from .validation.data_validator import DataValidator, ValidationResult
from .monitoring.metrics import MetricsCollector, HealthCheck
from .orchestrator import IngestionLayerOrchestrator

__all__ = [
    "KafkaIngestionConsumer",
    "create_consumer",
    "DataValidator",
    "ValidationResult",
    "MetricsCollector",
    "HealthCheck",
    "IngestionLayerOrchestrator"
]
