"""
Kafka Cluster Management Module
Quản lý kết nối, health check, và topic initialization cho Kafka
"""

import logging
from typing import Dict, List, Optional, Tuple
from kafka import KafkaProducer, KafkaConsumer, KafkaAdminClient
from kafka.admin import NewTopic, ConfigResource, ConfigResourceType
from kafka.errors import KafkaError, KafkaConnectionError, TopicAlreadyExistsError
from kafka.cluster import ClusterMetadata
import sys
import time

logger = logging.getLogger(__name__)


class KafkaClusterManager:
    """
    Quản lý Kafka cluster
    - Kết nối đến brokers
    - Kiểm tra health
    - Tạo topics
    - Quản lý metadata
    """

    def __init__(self, bootstrap_servers: str, request_timeout_ms: int = 10000):
        self.bootstrap_servers = bootstrap_servers.split(',') if isinstance(bootstrap_servers, str) else bootstrap_servers
        self.request_timeout_ms = request_timeout_ms
        self.admin_client = None
        self._meta_consumer = None
        self.is_connected = False
        
        logger.info(f"🔧 Initializing KafkaClusterManager")
        logger.info(f"   Bootstrap servers: {self.bootstrap_servers}")
        logger.info(f"   Request timeout: {request_timeout_ms}ms")

    def connect(self) -> bool:
        """Kết nối đến Kafka cluster"""
        try:
            logger.info("📡 Connecting to Kafka cluster...")
            
            self.admin_client = KafkaAdminClient(
                bootstrap_servers=self.bootstrap_servers,
                request_timeout_ms=self.request_timeout_ms
            )

            # Use a lightweight consumer to fetch metadata for topics/brokers
            try:
                self._meta_consumer = KafkaConsumer(bootstrap_servers=self.bootstrap_servers,
                                                    request_timeout_ms=self.request_timeout_ms)
                topics = self._meta_consumer.topics()
                # Try to get brokers from internal client (best-effort)
                brokers_count = 0
                try:
                    cluster = getattr(self._meta_consumer._client, 'cluster', None)
                    if cluster is not None:
                        brokers_count = len(list(cluster.brokers()))
                except Exception:
                    brokers_count = 0

                self.is_connected = True

                logger.info(f"✅ Connected to Kafka cluster")
                logger.info(f"   Brokers: {brokers_count}")
                logger.info(f"   Topics: {len(topics)}")

            except Exception as e:
                logger.warning(f"⚠️  Connected admin client but failed to fetch metadata via consumer: {e}")
                self.is_connected = True
            
            return True
            
        except Exception as e:
            logger.error(f"❌ Failed to connect to Kafka: {e}")
            self.is_connected = False
            return False

    def health_check(self) -> Dict[str, any]:
        """
        Kiểm tra health của Kafka cluster
        
        Returns:
            Dict với health status
        """
        health = {
            "status": "unknown",
            "brokers": 0,
            "topics": 0,
            "is_healthy": False,
            "errors": []
        }

        try:
            if not self.is_connected:
                if not self.connect():
                    health["errors"].append("Cannot connect to cluster")
                    return health

            # Get topics from meta consumer if available
            topics = set()
            brokers_count = 0
            try:
                if self._meta_consumer:
                    topics = self._meta_consumer.topics()
                    cluster = getattr(self._meta_consumer._client, 'cluster', None)
                    if cluster is not None:
                        brokers_count = len(list(cluster.brokers()))
            except Exception as e:
                logger.debug(f"Could not get metadata from meta_consumer: {e}")

            health["brokers"] = brokers_count
            health["topics"] = len(topics)

            # Basic broker checks
            if health["brokers"] <= 0:
                health["errors"].append("no brokers available")
                health["status"] = "degraded"
            else:
                health["status"] = "healthy"
                health["is_healthy"] = True

            logger.info(
                f"❤️  Kafka Health: {health['status']} "
                f"({health['brokers']} brokers, {health['topics']} topics)"
            )

            return health

        except Exception as e:
            health["errors"].append(str(e))
            logger.error(f"❌ Health check failed: {e}")
            return health

    def create_topics(self, topics_config: Dict[str, Dict]) -> Tuple[bool, List[str]]:
        """
        Tạo topics nếu chưa tồn tại
        
        Args:
            topics_config: Dict config của topics
            
        Returns:
            (success, created_topics_list)
        """
        try:
            if not self.is_connected:
                if not self.connect():
                    logger.error("Cannot create topics: not connected to Kafka")
                    return False, []

            new_topics = []
            for topic_name, config in topics_config.items():
                new_topic = NewTopic(
                    name=topic_name,
                    num_partitions=config.get("partitions", 3),
                    replication_factor=config.get("replication_factor", 1),
                    topic_configs={
                        'compression.type': config.get('compression_type', 'snappy'),
                        'retention.ms': str(config.get('retention_ms', 604800000)),
                        'segment.ms': str(config.get('segment_ms', 86400000)),
                        'cleanup.policy': config.get('cleanup_policy', 'delete'),
                        'min.insync.replicas': str(config.get('min_insync_replicas', 1))
                    }
                )
                new_topics.append(new_topic)

            # Create topics
            try:
                fs = self.admin_client.create_topics(new_topics, validate_only=False)
                
                created = []
                failed = []
                
                for topic_name, f in fs.items():
                    try:
                        f.result(timeout_sec=10)
                        created.append(topic_name)
                        logger.info(f"✅ Topic created: {topic_name}")
                    except TopicAlreadyExistsError:
                        logger.info(f"ℹ️  Topic already exists: {topic_name}")
                        created.append(topic_name)
                    except Exception as e:
                        failed.append(topic_name)
                        logger.error(f"❌ Failed to create topic {topic_name}: {e}")

                return len(failed) == 0, created

            except TopicAlreadyExistsError:
                logger.info("ℹ️  Topics already exist")
                return True, list(topics_config.keys())

        except Exception as e:
            logger.error(f"❌ Error creating topics: {e}")
            return False, []

    def list_topics(self) -> Dict[str, Dict]:
        """List tất cả topics và metadata"""
        try:
            if not self.is_connected:
                if not self.connect():
                    return {}

            topics_info = {}
            try:
                if self._meta_consumer:
                    for topic in self._meta_consumer.topics():
                        # Attempt to get partitions via partitions_for_topic
                        try:
                            parts = self._meta_consumer.partitions_for_topic(topic)
                            topics_info[topic] = {
                                "partitions": len(parts) if parts else 0,
                                "partition_ids": list(parts) if parts else []
                            }
                        except Exception:
                            topics_info[topic] = {"partitions": 0, "partition_ids": []}

            except Exception as e:
                logger.error(f"❌ Error listing topics: {e}")
                return {}

            logger.info(f"📋 Total topics: {len(topics_info)}")
            return topics_info

        except Exception as e:
            logger.error(f"❌ Error listing topics: {e}")
            return {}

    def get_topic_partition_count(self, topic: str) -> int:
        """Lấy số partitions của một topic"""
        try:
            if not self.is_connected:
                if not self.connect():
                    return 0

            try:
                if self._meta_consumer:
                    parts = self._meta_consumer.partitions_for_topic(topic)
                    return len(parts) if parts else 0
            except Exception as e:
                logger.warning(f"⚠️  Cannot get partition count for {topic}: {e}")
            return 0

        except Exception as e:
            logger.warning(f"⚠️  Cannot get partition count for {topic}: {e}")
            return 0

    def get_broker_info(self) -> Dict:
        """Lấy thông tin về các brokers"""
        try:
            if not self.is_connected:
                if not self.connect():
                    return {}

            brokers_info = {}
            try:
                if self._meta_consumer:
                    cluster = getattr(self._meta_consumer._client, 'cluster', None)
                    if cluster is not None:
                        for broker in cluster.brokers():
                            brokers_info[broker.nodeId] = {
                                "host": broker.host,
                                "port": broker.port
                            }
            except Exception as e:
                logger.error(f"❌ Error getting broker info: {e}")
                return {}

            logger.info(f"🖥️  {len(brokers_info)} brokers found")
            for broker_id, info in brokers_info.items():
                logger.info(f"   Broker {broker_id}: {info['host']}:{info['port']}")

            return brokers_info

        except Exception as e:
            logger.error(f"❌ Error getting broker info: {e}")
            return {}

    def delete_topic(self, topic: str) -> bool:
        """Xóa một topic (careful!)"""
        try:
            if not self.is_connected:
                if not self.connect():
                    return False

            logger.warning(f"⚠️  Deleting topic: {topic}")
            fs = self.admin_client.delete_topics([topic], validate_only=False)
            
            for topic_name, f in fs.items():
                try:
                    f.result(timeout_sec=10)
                    logger.info(f"✅ Topic deleted: {topic_name}")
                    return True
                except Exception as e:
                    logger.error(f"❌ Failed to delete topic: {e}")
                    return False

        except Exception as e:
            logger.error(f"❌ Error deleting topic: {e}")
            return False

    def close(self):
        """Đóng kết nối"""
        if self.admin_client:
            self.admin_client.close()
            logger.info("✅ Kafka cluster manager closed")


def create_cluster_manager(bootstrap_servers: str) -> Optional[KafkaClusterManager]:
    """Factory function để tạo KafkaClusterManager"""
    manager = KafkaClusterManager(bootstrap_servers)
    if manager.connect():
        return manager
    return None


if __name__ == "__main__":
    # Test
    manager = create_cluster_manager("localhost:9092")
    if manager:
        # Health check
        health = manager.health_check()
        print(f"Health: {health}")
        
        # List topics
        topics = manager.list_topics()
        print(f"Topics: {topics}")
        
        # Broker info
        brokers = manager.get_broker_info()
        print(f"Brokers: {brokers}")
        
        manager.close()
