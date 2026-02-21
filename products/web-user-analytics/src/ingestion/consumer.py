"""
Web User Analytics - Kafka Consumer

Consumes events from Kafka topics, validates, filters, and enriches them.
Integrates schema validation, bot detection, and session tracking.
"""

import json
import logging
from typing import Dict, Any, Optional, Callable, List
from datetime import datetime, timezone
from kafka import KafkaConsumer, KafkaProducer, TopicPartition
from kafka.errors import KafkaError
import geoip2.database

from .schema import create_event, BronzeEvent, EventType
from .validators import EventValidator, EventFilter, BotDetector, DuplicateDetector, DataQualityChecker
from .session_tracker import SessionManager, SessionAttributor


# Configure logging
logger = logging.getLogger(__name__)


class GeoIPEnricher:
    """Enriches events with geographic information"""
    
    def __init__(self, maxmind_db_path: Optional[str] = None):
        """
        Initialize GeoIP enricher.
        
        Args:
            maxmind_db_path: Path to MaxMind GeoIP2 database
        """
        self.db_path = maxmind_db_path
        self.reader = None
        
        if self.db_path:
            try:
                import geoip2.database
                self.reader = geoip2.database.Reader(maxmind_db_path)
            except Exception as e:
                logger.warning(f"Failed to load GeoIP database: {e}")
    
    def enrich(self, event_data: Dict[str, Any]) -> None:
        """
        Enrich event with geographic data from IP.
        
        Args:
            event_data: Event data to enrich (modified in place)
        """
        if not self.reader:
            return
        
        try:
            ip = event_data.get("ip_address", "")
            if not ip or ip.startswith("127."):
                return
            
            response = self.reader.city(ip)
            
            event_data["country"] = response.country.iso_code
            event_data["region"] = response.subdivisions[0].iso_code if response.subdivisions else None
            event_data["city"] = response.city.name
            event_data["latitude"] = response.location.latitude
            event_data["longitude"] = response.location.longitude
            
        except Exception as e:
            logger.debug(f"GeoIP enrichment failed for IP {ip}: {e}")


class EventEnricher:
    """Enriches events with additional data"""
    
    def __init__(self, geoip_db_path: Optional[str] = None):
        """
        Initialize event enricher.
        
        Args:
            geoip_db_path: Path to GeoIP database
        """
        self.geoip = GeoIPEnricher(geoip_db_path)
        self.bot_detector = BotDetector()
        self.session_attributor = SessionAttributor()
    
    def enrich_event(self, event_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Enrich event with additional data.
        
        Args:
            event_data: Raw event data
            
        Returns:
            Enriched event data
        """
        enriched = event_data.copy()
        
        # Enrich with GeoIP
        self.geoip.enrich(enriched)
        
        # Detect bots
        user_agent = enriched.get("user_agent", "")
        properties = enriched.get("properties", {})
        enriched["is_bot"] = self.bot_detector.is_bot(user_agent, properties)
        
        # Extract traffic source
        if enriched.get("event_type") == "session_start":
            referrer = enriched.get("referrer")
            utm_source = enriched.get("properties", {}).get("utm_source")
            enriched["traffic_source"] = self.session_attributor.get_traffic_source(referrer, utm_source)
            enriched["traffic_medium"] = self.session_attributor.get_traffic_medium(referrer, enriched.get("properties", {}).get("utm_medium"))
        
        return enriched


class WebAnalyticsConsumer:
    """
    Kafka consumer for web analytics events.
    
    Consumes from Kafka, validates, enriches, and filters events.
    Publishes to Bronze layer or dead letter topic.
    """
    
    def __init__(self,
                 bootstrap_servers: List[str],
                 group_id: str,
                 topics: List[str],
                 geoip_db_path: Optional[str] = None,
                 enable_bot_detection: bool = True,
                 session_timeout: int = 30 * 60,
                 kafka_config: Optional[Dict[str, Any]] = None):
        """
        Initialize Web Analytics Consumer.
        
        Args:
            bootstrap_servers: Kafka bootstrap servers
            group_id: Consumer group ID
            topics: Topics to consume from
            geoip_db_path: Path to GeoIP database
            enable_bot_detection: Enable bot detection
            session_timeout: Session timeout in seconds
            kafka_config: Additional Kafka configuration
        """
        self.bootstrap_servers = bootstrap_servers
        self.group_id = group_id
        self.topics = topics
        self.enable_bot_detection = enable_bot_detection
        self.session_timeout = session_timeout
        
        # Initialize components
        self.enricher = EventEnricher(geoip_db_path)
        self.validator = EventValidator()
        self.filter = EventFilter()
        self.session_manager = SessionManager(session_timeout)
        self.qc = DataQualityChecker()
        self.duplicate_detector = DuplicateDetector()
        
        # Kafka clients
        consumer_config = {
            "bootstrap_servers": bootstrap_servers,
            "group_id": group_id,
            "auto_offset_reset": "earliest",
            "enable_auto_commit": False,
            "value_deserializer": lambda m: json.loads(m.decode("utf-8")),
            **(kafka_config or {})
        }
        
        self.consumer = KafkaConsumer(*topics, **consumer_config)
        
        # Producer for Bronze layer / Dead letter
        producer_config = {
            "bootstrap_servers": bootstrap_servers,
            "value_serializer": lambda v: json.dumps(v).encode("utf-8"),
        }
        self.bronze_producer = KafkaProducer(**producer_config)
        self.dlq_producer = KafkaProducer(**producer_config)
        
        # Statistics
        self.stats = {
            "events_received": 0,
            "events_validated": 0,
            "events_filtered": 0,
            "events_enriched": 0,
            "events_to_bronze": 0,
            "events_to_dlq": 0,
        }
        
        # Recent event hashes for duplicate detection (in-memory, use Redis in production)
        self.recent_hashes: List[str] = []
        self.max_recent_hashes = 10000
    
    def process_event(self, raw_event: Dict[str, Any]) -> Optional[BronzeEvent]:
        """
        Process a single event through the pipeline.
        
        Args:
            raw_event: Raw event from Kafka
            
        Returns:
            BronzeEvent if successful, None if filtered/invalid
        """
        self.stats["events_received"] += 1
        
        # Validate
        is_valid, error = self.validator.validate_event(raw_event)
        if not is_valid:
            logger.warning(f"Event validation failed: {error}")
            return None
        
        self.stats["events_validated"] += 1
        
        # Filter
        should_filter, reason = self.filter.should_filter_event(raw_event, self.enable_bot_detection)
        if should_filter:
            logger.debug(f"Event filtered: {reason}")
            self.stats["events_filtered"] += 1
            return None
        
        # Duplicate detection
        event_hash = self.duplicate_detector.get_event_hash(raw_event)
        if self.duplicate_detector.is_likely_duplicate(event_hash, self.recent_hashes):
            logger.debug("Duplicate event detected")
            self.stats["events_filtered"] += 1
            return None
        
        self.recent_hashes.append(event_hash)
        if len(self.recent_hashes) > self.max_recent_hashes:
            self.recent_hashes = self.recent_hashes[-self.max_recent_hashes:]
        
        # Enrich
        enriched_event = self.enricher.enrich_event(raw_event)
        self.stats["events_enriched"] += 1
        
        # Quality check
        quality = self.qc.check_event_quality(enriched_event)
        enriched_event["_quality"] = quality
        
        # Create Bronze event
        bronze_event = BronzeEvent(
            event_id=enriched_event.get("event_id"),
            user_id=enriched_event.get("user_id"),
            session_id=enriched_event.get("session_id"),
            event_type=enriched_event.get("event_type"),
            timestamp=datetime.fromisoformat(str(enriched_event.get("timestamp", datetime.now(timezone.utc).isoformat()))),
            raw_data=enriched_event,
            ingested_at=datetime.now(timezone.utc),
        )
        
        # Update session
        session_id = enriched_event.get("session_id")
        user_id = enriched_event.get("user_id")
        
        if not self.session_manager.get_session(session_id):
            traffic_source = enriched_event.get("traffic_source")
            self.session_manager.create_session(
                session_id=session_id,
                user_id=user_id,
                traffic_source=traffic_source,
            )
        
        session = self.session_manager.update_session_activity(session_id, enriched_event)
        if session:
            bronze_event.raw_data["_session_info"] = session.to_dict()
        
        self.stats["events_to_bronze"] += 1
        return bronze_event
    
    def run(self,
            batch_size: int = 100,
            output_handler: Optional[Callable[[BronzeEvent], None]] = None,
            dlq_handler: Optional[Callable[[Dict[str, Any], str], None]] = None) -> None:
        """
        Run consumer in continuous mode.
        
        Args:
            batch_size: Batch size for processing
            output_handler: Handler for processed Bronze events
            dlq_handler: Handler for dead letter queue events
        """
        logger.info(f"Starting consumer for topics: {self.topics}")
        
        try:
            batch = []
            
            for message in self.consumer:
                try:
                    raw_event = message.value
                    
                    # Process event
                    bronze_event = self.process_event(raw_event)
                    
                    if bronze_event:
                        if output_handler:
                            output_handler(bronze_event)
                        batch.append(bronze_event)
                    else:
                        if dlq_handler:
                            dlq_handler(raw_event, "validation_failed")
                    
                    # Batch processing
                    if len(batch) >= batch_size:
                        self.flush_batch(batch)
                        batch = []
                        self.consumer.commit()
                    
                except Exception as e:
                    logger.error(f"Error processing event: {e}", exc_info=True)
                    if dlq_handler:
                        dlq_handler(raw_event, f"processing_error: {str(e)}")
        
        except KeyboardInterrupt:
            logger.info("Consumer interrupted")
        finally:
            self.flush_batch(batch)
            self.consumer.close()
            self.bronze_producer.close()
            logger.info(f"Consumer stopped. Stats: {self.stats}")
    
    def flush_batch(self, batch: List[BronzeEvent]) -> None:
        """Flush batch of Bronze events"""
        if not batch:
            return
        
        for bronze_event in batch:
            try:
                # Send to Bronze topic
                self.bronze_producer.send(
                    "topic_bronze_events",
                    value=bronze_event.dict()
                )
            except KafkaError as e:
                logger.error(f"Failed to send to Bronze: {e}")
        
        self.bronze_producer.flush()
    
    def get_stats(self) -> Dict[str, Any]:
        """Get consumer statistics"""
        return {
            **self.stats,
            "sessions": self.session_manager.get_stats(),
        }
    
    def close(self) -> None:
        """Close consumer and cleanup resources"""
        self.consumer.close()
        self.bronze_producer.close()
        self.dlq_producer.close()


# Standalone entry point for running consumer
if __name__ == "__main__":
    import os
    from dotenv import load_dotenv
    
    load_dotenv()
    
    # Configuration
    BOOTSTRAP_SERVERS = os.getenv("KAFKA_BOOTSTRAP_SERVERS", "localhost:9092").split(",")
    GROUP_ID = os.getenv("KAFKA_CONSUMER_GROUP", "web-analytics-consumer")
    TOPICS = ["topic_web_events"]
    GEOIP_DB = os.getenv("GEOIP_DB_PATH")
    
    # Create and run consumer
    consumer = WebAnalyticsConsumer(
        bootstrap_servers=BOOTSTRAP_SERVERS,
        group_id=GROUP_ID,
        topics=TOPICS,
        geoip_db_path=GEOIP_DB,
        enable_bot_detection=True,
    )
    
    try:
        consumer.run(batch_size=100)
    except Exception as e:
        logger.error(f"Consumer error: {e}", exc_info=True)
    finally:
        consumer.close()
