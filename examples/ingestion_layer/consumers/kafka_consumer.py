"""
Kafka Consumer - Ingestion Layer
Consume dữ liệu từ Kafka topics và xử lý theo batch
"""

import json
import logging
from typing import Dict, List, Optional, Any
from datetime import datetime
from collections import defaultdict
from kafka import KafkaConsumer
from kafka.errors import KafkaError
import sys
sys.path.insert(0, '/workspaces/Data-Platform/ingestion_layer')

from configs.kafka_config import (
    KAFKA_BOOTSTRAP_SERVER,
    CONSUMER_CONFIG,
    INGESTION_CONFIG,
    VALIDATION_RULES,
    CONSUMER_GROUPS
)

# Centralized logging + connection pool
from logs.logging_config import setup_logger, ContextLogger
from kafka_cluster.connection_pool import create_connection_pool, KafkaConnectionPool

_base_logger = setup_logger(name=__name__, json_format=True, log_file='consumer.log')
logger = ContextLogger(_base_logger)


class KafkaIngestionConsumer:
    """
    Kafka Consumer cho INGESTION LAYER
    - Consume dữ liệu từ Kafka topics
    - Validate dữ liệu theo schema
    - Batch processing
    - Error handling & Dead Letter Queue
    """

    def __init__(self, group_id: str, topics: List[str]):
        self.group_id = group_id
        self.topics = topics
        self.batch_size = INGESTION_CONFIG["batch_size"]
        self.batch_timeout_ms = INGESTION_CONFIG["batch_timeout_ms"]
        self.enable_validation = INGESTION_CONFIG["enable_validation"]
        
        # Message buffer
        self.message_buffer = []
        self.topic_buffer = defaultdict(list)
        
        # Metrics
        self.metrics = {
            "messages_consumed": 0,
            "messages_processed": 0,
            "messages_failed": 0,
            "batches_processed": 0,
            "errors": defaultdict(int)
        }
        
        # Initialize consumer
        self.consumer = None
        self.pool: KafkaConnectionPool | None = None
        self._initialize_consumer()

    def _initialize_consumer(self):
        """Khởi tạo Kafka Consumer"""
        try:
            # Use connection pool to create a resilient consumer
            self.pool = create_connection_pool(KAFKA_BOOTSTRAP_SERVER)
            if self.pool is None:
                raise RuntimeError("Cannot initialize Kafka connection pool")

            # Create consumer with retry logic from pool
            consumer = self.pool.create_consumer_with_retry(self.group_id, self.topics)
            if consumer is None:
                raise RuntimeError("Failed to create Kafka consumer after retries")

            # Apply value deserializer if not present
            try:
                # kafka-python consumer created via pool may need deserializer override
                consumer.config['value_deserializer'] = lambda m: json.loads(m.decode('utf-8')) if m else None
            except Exception:
                pass

            self.consumer = consumer
            logger.info(f"✅ Consumer initialized: group={self.group_id}, topics={self.topics}")
        except Exception as e:
            logger.error(f"❌ Failed to initialize consumer: {e}")
            raise

    def validate_message(self, message: Dict, topic: str) -> tuple[bool, Optional[str]]:
        """
        Validate tin nhắn theo schema rules
        
        Args:
            message: Tin nhắn từ Kafka
            topic: Topic mà tin nhắn đến từ
            
        Returns:
            (is_valid, error_message)
        """
        if not self.enable_validation:
            return True, None
        
        rules = VALIDATION_RULES.get(topic, {})
        required_fields = rules.get("required_fields", [])
        
        # Kiểm tra required fields
        for field in required_fields:
            if field not in message:
                return False, f"Missing required field: {field}"
        
        # Kiểm tra timestamp
        if "timestamp" in message:
            try:
                ts = message["timestamp"]
                if isinstance(ts, str):
                    datetime.fromisoformat(ts.replace('Z', '+00:00'))
            except ValueError:
                return False, f"Invalid timestamp format: {message['timestamp']}"
        
        return True, None

    def process_batch(self, batch: List[Dict]) -> Dict[str, Any]:
        """
        Xử lý một batch tin nhắn
        
        Args:
            batch: Danh sách tin nhắn
            
        Returns:
            Kết quả xử lý (processed_count, failed_count, errors)
        """
        processed = 0
        failed = 0
        errors = []
        
        for msg_data in batch:
            try:
                # Tách topic từ message metadata
                topic = msg_data.get("__topic__")
                if not topic:
                    continue
                
                # Validate message
                is_valid, error_msg = self.validate_message(msg_data, topic)
                if not is_valid:
                    logger.warning(f"⚠️  Invalid message from {topic}: {error_msg}")
                    failed += 1
                    self.metrics["errors"]["validation"] += 1
                    errors.append({
                        "topic": topic,
                        "error": error_msg,
                        "timestamp": datetime.utcnow().isoformat()
                    })
                    continue
                
                # Xử lý message
                self._handle_message(msg_data, topic)
                processed += 1
                self.metrics["messages_processed"] += 1
                
            except Exception as e:
                logger.error(f"❌ Error processing message: {e}")
                failed += 1
                self.metrics["errors"]["processing"] += 1
                errors.append({
                    "error": str(e),
                    "timestamp": datetime.utcnow().isoformat()
                })
        
        return {
            "processed": processed,
            "failed": failed,
            "errors": errors
        }

    def _handle_message(self, message: Dict, topic: str):
        """
        Xử lý một tin nhắn đơn lẻ
        Có thể override để custom processing
        """
        self.topic_buffer[topic].append(message)
        
        # Log theo interval
        if self.metrics["messages_processed"] % 100 == 0:
            logger.info(
                f"📊 Processed {self.metrics['messages_processed']} messages | "
                f"Topic {topic} buffer: {len(self.topic_buffer[topic])}"
            )

    def consume_messages(self, timeout_sec: int = 30):
        """
        Consume và process tin nhắn từ Kafka
        
        Args:
            timeout_sec: Timeout trong giây
        """
        logger.info(f"🚀 Starting consumption from topics: {self.topics}")
        
        try:
            batch = []
            
            for message in self.consumer:
                try:
                    # Parse message
                    if message.value is None:
                        continue
                    
                    msg_data = message.value.copy()
                    msg_data["__topic__"] = message.topic
                    msg_data["__partition__"] = message.partition
                    msg_data["__offset__"] = message.offset
                    
                    batch.append(msg_data)
                    self.metrics["messages_consumed"] += 1
                    
                    # Process batch khi đủ size
                    if len(batch) >= self.batch_size:
                        result = self.process_batch(batch)
                        self.metrics["batches_processed"] += 1
                        logger.info(
                            f"✅ Batch processed: "
                            f"processed={result['processed']}, "
                            f"failed={result['failed']}"
                        )
                        batch = []
                        
                except Exception as e:
                    logger.error(f"❌ Error in message loop: {e}")
                    self.metrics["errors"]["consumption"] += 1
                    
        except KeyboardInterrupt:
            logger.info("⏹️  Stopping consumer...")
            # Process remaining batch
            if batch:
                result = self.process_batch(batch)
                self.metrics["batches_processed"] += 1
                logger.info(f"✅ Final batch: processed={result['processed']}, failed={result['failed']}")
        finally:
            self.close()

    def get_metrics(self) -> Dict:
        """Lấy metrics"""
        return {
            "timestamp": datetime.utcnow().isoformat(),
            "group_id": self.group_id,
            "topics": self.topics,
            **self.metrics
        }

    def print_metrics(self):
        """In ra metrics"""
        metrics = self.get_metrics()
        logger.info(
            f"\n📈 Metrics:\n"
            f"  Messages consumed: {metrics['messages_consumed']}\n"
            f"  Messages processed: {metrics['messages_processed']}\n"
            f"  Messages failed: {metrics['messages_failed']}\n"
            f"  Batches processed: {metrics['batches_processed']}\n"
            f"  Validation errors: {metrics['errors'].get('validation', 0)}\n"
            f"  Processing errors: {metrics['errors'].get('processing', 0)}"
        )

    def close(self):
        """Đóng consumer"""
        if self.consumer:
            self.consumer.close()
            logger.info("✅ Consumer closed")
        # Close pool resources if present
        if self.pool:
            try:
                self.pool.close()
            except Exception:
                pass
        self.print_metrics()


def create_consumer(group_id: str, topics: List[str]) -> KafkaIngestionConsumer:
    """Factory function để tạo consumer"""
    return KafkaIngestionConsumer(group_id, topics)


if __name__ == "__main__":
    # Test: Consume từ một topic
    group_id = "test-ingestion-consumer"
    topics = ["topic_app_events"]
    
    consumer = create_consumer(group_id, topics)
    consumer.consume_messages(timeout_sec=30)
