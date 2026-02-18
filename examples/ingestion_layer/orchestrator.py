"""
Ingestion Layer Orchestrator
Điều phối tất cả các consumer, validator, và monitoring
"""

import logging
import sys
import signal
from typing import List, Dict, Optional
from threading import Thread, Event
from datetime import datetime
import time

sys.path.insert(0, '/workspaces/Data-Platform/ingestion_layer')

from configs.kafka_config import CONSUMER_GROUPS, MONITORING_CONFIG, TOPICS_CONFIG, KAFKA_BOOTSTRAP_SERVER
from kafka_cluster.kafka_manager import create_cluster_manager
from consumers.kafka_consumer import create_consumer
from validation.data_validator import DataValidator
from monitoring.metrics import MetricsCollector, HealthCheck

import os

# Centralized logging setup
from logs.logging_config import setup_logger, ContextLogger

# Create a contextual logger for this module (file + JSON file logging enabled)
_base_logger = setup_logger(
    name=__name__,
    log_level=os.getenv('LOG_LEVEL', 'INFO'),
    console_output=True,
    file_output=True,
    json_format=True,
    log_file='orchestrator.log'
)

# Wrap into ContextLogger so modules can attach context like request_id/trace_id
logger = ContextLogger(_base_logger)


class IngestionLayerOrchestrator:
    """
    Orchestrator cho INGESTION LAYER
    - Quản lý multiple consumers
    - Validate dữ liệu
    - Monitor hiệu suất
    - Graceful shutdown
    """

    def __init__(self, consumer_groups: Optional[List[str]] = None):
        self.consumer_groups = consumer_groups or list(CONSUMER_GROUPS.keys())
        self.consumers = {}
        self.threads = {}
        self.shutdown_event = Event()
        
        # Validators
        self.validators = {}
        
        # Metrics
        self.metrics_collector = MetricsCollector()
        self.health_check = HealthCheck(self.metrics_collector)
        
        # Stats
        self.stats = {
            "start_time": datetime.utcnow(),
            "total_messages_processed": 0,
            "total_errors": 0,
            "by_group": {}
        }
        
        logger.info(f"🚀 Initializing INGESTION LAYER ORCHESTRATOR")
        logger.info(f"📋 Consumer groups to start: {self.consumer_groups}")

    def initialize_consumer_group(self, group_name: str) -> bool:
        """Khởi tạo một consumer group"""
        try:
            if group_name not in CONSUMER_GROUPS:
                logger.error(f"❌ Unknown consumer group: {group_name}")
                return False
            
            topics = CONSUMER_GROUPS[group_name]["topics"]
            description = CONSUMER_GROUPS[group_name]["description"]
            
            logger.info(f"\n📌 Initializing consumer group: {group_name}")
            logger.info(f"   Description: {description}")
            logger.info(f"   Topics: {topics}")
            
            # Create consumer
            consumer = create_consumer(group_name, topics)
            self.consumers[group_name] = consumer
            
            # Create validators
            for topic in topics:
                if topic not in self.validators:
                    self.validators[topic] = DataValidator()
            
            self.stats["by_group"][group_name] = {
                "messages_processed": 0,
                "errors": 0,
                "start_time": datetime.utcnow()
            }
            
            logger.info(f"✅ Consumer group '{group_name}' initialized")
            return True
            
        except Exception as e:
            logger.error(f"❌ Failed to initialize consumer group '{group_name}': {e}")
            return False

    def start_consumer_group(self, group_name: str):
        """Khởi động một consumer group trong thread"""
        if group_name not in self.consumers:
            logger.error(f"❌ Consumer group not initialized: {group_name}")
            return
        
        try:
            consumer = self.consumers[group_name]
            logger.info(f"🎯 Starting consumer group: {group_name}")
            
            # Consumer loop với graceful shutdown
            message_count = 0
            batch = []
            
            for message in consumer.consumer:
                if self.shutdown_event.is_set():
                    break
                
                if message.value is None:
                    continue
                
                try:
                    msg_data = message.value.copy()
                    msg_data["__topic__"] = message.topic
                    msg_data["__offset__"] = message.offset
                    
                    # Validate message
                    validator = self.validators.get(message.topic)
                    if validator:
                        start_time = time.time()
                        result = validator.validate_message(msg_data, message.topic)
                        processing_time_ms = (time.time() - start_time) * 1000
                        
                        # Record metrics
                        self.metrics_collector.record_message_processed(
                            topic=message.topic,
                            processing_time_ms=processing_time_ms,
                            success=result.is_valid,
                            message_size_bytes=len(str(msg_data))
                        )
                        
                        if not result.is_valid:
                            logger.warning(f"⚠️  Validation failed: {result.errors}")
                            self.stats["by_group"][group_name]["errors"] += 1
                        
                        message_count += 1
                        self.stats["by_group"][group_name]["messages_processed"] += 1
                        self.stats["total_messages_processed"] += 1
                        
                        # Log periodically
                        if message_count % 100 == 0:
                            logger.info(
                                f"📊 {group_name}: {message_count} messages processed "
                                f"({self.stats['by_group'][group_name]['errors']} errors)"
                            )
                    
                except Exception as e:
                    logger.error(f"❌ Error processing message in {group_name}: {e}")
                    self.stats["by_group"][group_name]["errors"] += 1
                    self.stats["total_errors"] += 1
            
            logger.info(f"⏹️  Consumer group '{group_name}' stopped")
            
        except Exception as e:
            logger.error(f"❌ Error in consumer group '{group_name}': {e}")
        finally:
            if group_name in self.consumers:
                self.consumers[group_name].close()

    def start_all(self):
        """Khởi động tất cả consumer groups"""
        logger.info(f"\n{'='*70}")
        logger.info(f"🚀 STARTING INGESTION LAYER")
        logger.info(f"{'='*70}\n")
        # Initialize Kafka cluster manager and wait for cluster readiness (best-effort)
        try:
            self.cluster_manager = create_cluster_manager(KAFKA_BOOTSTRAP_SERVER)
            if self.cluster_manager:
                # Wait for cluster to become healthy before attempting topic creation
                def wait_for_cluster(timeout_sec: int = 60, interval_sec: int = 3) -> bool:
                    start = time.time()
                    while time.time() - start < timeout_sec:
                        try:
                            healthy = self.cluster_manager.health_check()
                            if healthy:
                                return True
                        except Exception:
                            pass
                        time.sleep(interval_sec)
                    return False

                if wait_for_cluster(timeout_sec=60, interval_sec=3):
                    try:
                        success, created = self.cluster_manager.create_topics(TOPICS_CONFIG)
                        logger.info(f"📦 Topic creation attempted: success={success}, created={created}")
                    except Exception as e:
                        logger.warning(f"⚠️  Exception creating topics: {e}")
                else:
                    logger.warning("⚠️  Kafka cluster not healthy within timeout; skipping topic creation")
            else:
                logger.warning("⚠️  Kafka cluster manager not available; skipping topic creation")
        except Exception as e:
            logger.warning(f"⚠️  Exception during cluster manager init: {e}")

        # Initialize all consumer groups
        initialized = 0
        for group_name in self.consumer_groups:
            if self.initialize_consumer_group(group_name):
                initialized += 1
        
        logger.info(f"✅ Initialized {initialized}/{len(self.consumer_groups)} consumer groups\n")
        
        # Start all consumers in threads
        for group_name in self.consumer_groups:
            if group_name in self.consumers:
                thread = Thread(
                    target=self.start_consumer_group,
                    args=(group_name,),
                    daemon=False,
                    name=f"consumer-{group_name}"
                )
                thread.start()
                self.threads[group_name] = thread
                logger.info(f"🧵 Started thread for {group_name}")
        
        # Start monitoring thread
        monitor_thread = Thread(
            target=self._monitoring_loop,
            daemon=False,
            name="monitor"
        )
        monitor_thread.start()
        self.threads["monitor"] = monitor_thread
        
        logger.info(f"✅ All consumer groups started!\n")

    def _monitoring_loop(self):
        """Monitor loop - in ra metrics periodically"""
        check_interval = MONITORING_CONFIG.get("metrics_interval_sec", 10)
        health_check_interval = MONITORING_CONFIG.get("log_interval_sec", 30)
        
        health_check_counter = 0
        
        while not self.shutdown_event.is_set():
            try:
                time.sleep(check_interval)
                
                health_check_counter += 1
                
                # Print metrics
                if health_check_counter % 3 == 0:
                    self.metrics_collector.print_metrics()
                
                # Print health check
                if health_check_counter * check_interval >= health_check_interval:
                    self.health_check.print_health_check()
                    # Cluster health check (if available)
                    try:
                        if hasattr(self, 'cluster_manager') and self.cluster_manager:
                            cluster_health = self.cluster_manager.health_check()
                            logger.info(f"🧭 Kafka cluster health: {cluster_health}")
                    except Exception as e:
                        logger.warning(f"⚠️  Kafka cluster health check failed: {e}")

                    health_check_counter = 0
                    
            except Exception as e:
                logger.error(f"❌ Error in monitoring loop: {e}")

    def stop_all(self):
        """Dừng tất cả consumers"""
        logger.info(f"\n{'='*70}")
        logger.info(f"⏹️  STOPPING INGESTION LAYER")
        logger.info(f"{'='*70}\n")
        
        # Signal shutdown
        self.shutdown_event.set()
        
        # Close all consumers
        for group_name, consumer in self.consumers.items():
            logger.info(f"Closing consumer group: {group_name}")
            try:
                consumer.close()
            except Exception as e:
                logger.error(f"❌ Error closing {group_name}: {e}")
        
        # Wait for all threads
        logger.info("Waiting for all threads to finish...")
        for thread_name, thread in self.threads.items():
            thread.join(timeout=5)
            logger.info(f"✅ Thread {thread_name} finished")
        
        # Print final stats
        self._print_final_stats()

    def _print_final_stats(self):
        """In ra final statistics"""
        uptime = datetime.utcnow() - self.stats["start_time"]
        uptime_seconds = uptime.total_seconds()
        
        logger.info(f"\n{'='*70}")
        logger.info(f"📊 FINAL STATISTICS")
        logger.info(f"{'='*70}")
        logger.info(f"Uptime: {uptime_seconds:.0f} seconds")
        logger.info(f"Total messages processed: {self.stats['total_messages_processed']}")
        logger.info(f"Total errors: {self.stats['total_errors']}")
        
        if uptime_seconds > 0:
            throughput = self.stats["total_messages_processed"] / uptime_seconds
            logger.info(f"Overall throughput: {throughput:.2f} messages/sec")
        
        logger.info(f"\nBy consumer group:")
        for group_name, group_stats in self.stats["by_group"].items():
            group_uptime = (datetime.utcnow() - group_stats["start_time"]).total_seconds()
            logger.info(
                f"  {group_name}:"
                f"\n    Messages: {group_stats['messages_processed']}"
                f"\n    Errors: {group_stats['errors']}"
            )
        
        self.metrics_collector.print_metrics()
        self.health_check.print_health_check()
        logger.info(f"\n{'='*70}\n")

    def handle_signal(self, signum, frame):
        """Handle SIGTERM/SIGINT"""
        logger.info(f"\n📬 Received signal {signum}, shutting down gracefully...")
        self.stop_all()
        sys.exit(0)


def main():
    """Main entry point"""
    orchestrator = IngestionLayerOrchestrator()
    
    # Register signal handlers
    signal.signal(signal.SIGTERM, orchestrator.handle_signal)
    signal.signal(signal.SIGINT, orchestrator.handle_signal)
    
    try:
        # Start all consumer groups
        orchestrator.start_all()
        
        # Keep main thread alive
        while True:
            time.sleep(1)
            
    except KeyboardInterrupt:
        logger.info("\n⏹️  Keyboard interrupt, shutting down...")
        orchestrator.stop_all()
    except Exception as e:
        logger.error(f"❌ Unexpected error: {e}")
        orchestrator.stop_all()
        sys.exit(1)


if __name__ == "__main__":
    main()
