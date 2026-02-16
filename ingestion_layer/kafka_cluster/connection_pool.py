"""
Kafka Connection Pool Module
Quản lý connection pooling, retry logic, và resilience
"""

import logging
from typing import Optional, Dict, Any
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from kafka import KafkaProducer, KafkaConsumer
from kafka.errors import KafkaError, KafkaConnectionError
import threading
import time

logger = logging.getLogger(__name__)


@dataclass
class ConnectionConfig:
    """Configuration cho Kafka connection"""
    bootstrap_servers: str
    
    # Retry settings
    max_retries: int = 5
    initial_retry_backoff_ms: int = 200
    max_retry_backoff_ms: int = 32000
    
    # Timeout settings
    request_timeout_ms: int = 10000
    connections_max_idle_ms: int = 540000  # 9 minutes
    
    # Batch settings
    batch_size: int = 16384
    linger_ms: int = 10
    
    # Security
    use_ssl: bool = False
    ssl_cafile: Optional[str] = None
    
    # Extra settings
    extra: Dict[str, Any] = field(default_factory=dict)


class ConnectionHealthChecker:
    """Kiểm tra health của connection"""
    
    def __init__(self, check_interval_sec: int = 30, failure_threshold: int = 3):
        self.check_interval_sec = check_interval_sec
        self.failure_threshold = failure_threshold
        self.last_check = None
        self.failure_count = 0
        self.is_healthy = True
        self.lock = threading.Lock()

    def record_success(self):
        """Ghi nhận successful connection"""
        with self.lock:
            self.failure_count = 0
            self.is_healthy = True
            self.last_check = datetime.now()

    def record_failure(self):
        """Ghi nhận failed connection"""
        with self.lock:
            self.failure_count += 1
            self.is_healthy = self.failure_count < self.failure_threshold
            self.last_check = datetime.now()
            
            if not self.is_healthy:
                logger.warning(
                    f"⚠️  Connection health degraded "
                    f"({self.failure_count}/{self.failure_threshold} failures)"
                )

    def should_check(self) -> bool:
        """Check xem có cần health check không"""
        if self.last_check is None:
            return True
        
        elapsed = datetime.now() - self.last_check
        return elapsed.total_seconds() >= self.check_interval_sec


class KafkaConnectionPool:
    """
    Connection pool for Kafka
    - Quản lý múltiple connections
    - Automatic reconnection
    - Health checking
    - Exponential backoff retry
    """

    def __init__(self, config: ConnectionConfig):
        self.config = config
        self.producer = None
        self.consumer_configs = {}
        self.health_checker = ConnectionHealthChecker()
        self.lock = threading.Lock()
        
        logger.info("🔌 Initializing Kafka Connection Pool")
        logger.info(f"   Bootstrap servers: {config.bootstrap_servers}")
        logger.info(f"   Max retries: {config.max_retries}")
        logger.info(f"   Request timeout: {config.request_timeout_ms}ms")

    def get_producer(self) -> Optional[KafkaProducer]:
        """
        Lấy hoặc tạo Kafka producer
        Nếu connection fail, retry với exponential backoff
        """
        if self.producer is not None:
            return self.producer

        return self._create_producer_with_retry()

    def _create_producer_with_retry(self) -> Optional[KafkaProducer]:
        """Tạo producer với retry logic"""
        retry_count = 0
        backoff_ms = self.config.initial_retry_backoff_ms
        # Try preferred compressions then fallback if codec not available
        compression_candidates = ['snappy', 'gzip', None]

        while retry_count < self.config.max_retries:
            try:
                logger.info(f"📤 Creating Kafka producer (attempt {retry_count + 1})...")

                for compression in compression_candidates:
                    try:
                        kwargs = dict(
                            bootstrap_servers=self.config.bootstrap_servers,
                            acks='all',
                            retries=self.config.max_retries,
                            max_in_flight_requests_per_connection=1,
                            request_timeout_ms=self.config.request_timeout_ms,
                            linger_ms=self.config.linger_ms,
                            batch_size=self.config.batch_size,
                            **self.config.extra
                        )
                        if compression is not None:
                            kwargs['compression_type'] = compression

                        logger.info(f"   Trying producer compression='{compression}'")
                        producer = KafkaProducer(**kwargs)
                        # ensure producer connected to bootstrap
                        if hasattr(producer, 'bootstrap_connected') and producer.bootstrap_connected():
                            self.producer = producer
                            logger.info(f"✅ Kafka producer created successfully (compression={compression})")
                            self.health_checker.record_success()
                            return self.producer
                        else:
                            # close and continue trying
                            try:
                                producer.close()
                            except Exception:
                                pass

                    except Exception as ce:
                        logger.warning(f"   Compression {compression} failed: {ce}")
                        # try next compression candidate

                # If none of the compression candidates produced a working producer, raise
                raise KafkaError("All compression attempts failed or producer not connected")

            except Exception as e:
                retry_count += 1
                self.health_checker.record_failure()

                if retry_count < self.config.max_retries:
                    logger.warning(
                        f"❌ Failed to create producer (attempt {retry_count}): {e}\n"
                        f"   Retrying in {backoff_ms}ms..."
                    )
                    time.sleep(backoff_ms / 1000)
                    backoff_ms = min(backoff_ms * 2, self.config.max_retry_backoff_ms)
                else:
                    logger.error(f"❌ Failed to create producer after {self.config.max_retries} attempts: {e}")
                    self.producer = None
                    return None

    def get_consumer_config(self, 
                          group_id: str, 
                          topics: list,
                          auto_offset_reset: str = 'earliest') -> Dict[str, Any]:
        """
        Lấy consumer config
        
        Args:
            group_id: Consumer group ID
            topics: List of topics to consume
            auto_offset_reset: What to do when no initial offset
        """
        return {
            'bootstrap_servers': self.config.bootstrap_servers,
            'group_id': group_id,
            'topics': topics,
            'auto_offset_reset': auto_offset_reset,
            'enable_auto_commit': True,
            'auto_commit_interval_ms': 5000,
            'session_timeout_ms': 6000,
            'request_timeout_ms': self.config.request_timeout_ms,
            'max_poll_records': 100,
            'value_deserializer': lambda m: m.decode('utf-8') if m else None,
            **self.config.extra
        }

    def create_consumer_with_retry(self, 
                                   group_id: str, 
                                   topics: list) -> Optional[KafkaConsumer]:
        """
        Tạo consumer với retry logic
        
        Args:
            group_id: Consumer group ID
            topics: Topics to subscribe to
            
        Returns:
            KafkaConsumer or None if failed
        """
        retry_count = 0
        backoff_ms = self.config.initial_retry_backoff_ms
        
        while retry_count < self.config.max_retries:
            try:
                logger.info(
                    f"📥 Creating Kafka consumer for group '{group_id}' "
                    f"(attempt {retry_count + 1})..."
                )
                
                consumer_config = self.get_consumer_config(group_id, topics)
                consumer = KafkaConsumer(**consumer_config)
                
                logger.info(
                    f"✅ Consumer created: group='{group_id}', "
                    f"topics={topics}"
                )
                self.health_checker.record_success()
                return consumer

            except Exception as e:
                retry_count += 1
                self.health_checker.record_failure()
                
                if retry_count < self.config.max_retries:
                    logger.warning(
                        f"❌ Failed to create consumer (attempt {retry_count}): {e}\n"
                        f"   Retrying in {backoff_ms}ms..."
                    )
                    time.sleep(backoff_ms / 1000)
                    backoff_ms = min(backoff_ms * 2, self.config.max_retry_backoff_ms)
                else:
                    logger.error(
                        f"❌ Failed to create consumer after {self.config.max_retries} attempts"
                    )
                    return None

    def health_check(self) -> bool:
        """
        Kiểm tra health của connection pool
        
        Returns:
            True if healthy, False otherwise
        """
        if self.health_checker.should_check():
            try:
                # Test producer
                if self.producer:
                    self.producer.send_and_wait(
                        "__health_check__",
                        b"ping",
                        timeout_ms=self.config.request_timeout_ms
                    )
                    self.health_checker.record_success()
                    return True
                else:
                    # Try to create producer
                    producer = self.get_producer()
                    return producer is not None

            except Exception as e:
                logger.warning(f"⚠️  Connection health check failed: {e}")
                self.health_checker.record_failure()
                return False

        return self.health_checker.is_healthy

    def reset_producer(self):
        """Reset producer connection (useful for failover)"""
        with self.lock:
            if self.producer:
                try:
                    self.producer.close()
                except:
                    pass
                self.producer = None
                logger.info("🔄 Producer connection reset")

    def close(self):
        """Đóng tất cả connections"""
        if self.producer:
            try:
                self.producer.close()
                logger.info("✅ Producer closed")
            except Exception as e:
                logger.error(f"Error closing producer: {e}")

        self.producer = None
        logger.info("✅ Connection pool closed")


def create_connection_pool(bootstrap_servers: str) -> Optional[KafkaConnectionPool]:
    """Factory function để tạo connection pool"""
    config = ConnectionConfig(bootstrap_servers=bootstrap_servers)
    pool = KafkaConnectionPool(config)
    
    # Test connection
    if pool.get_producer() is not None:
        return pool
    
    return None


if __name__ == "__main__":
    # Test
    pool = create_connection_pool("localhost:9092")
    if pool:
        # Check health
        is_healthy = pool.health_check()
        print(f"Pool health: {is_healthy}")
        
        pool.close()
