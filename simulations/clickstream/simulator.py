"""
Clickstream Simulator
Generates real-time clickstream events
"""

import random
import time
import uuid
import json
from datetime import datetime
from kafka import KafkaProducer
from kafka.errors import KafkaError
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

KAFKA_BROKER = "kafka:9092"
TOPIC = "topic_clickstream"

PAGES = [
    "home", "search_results", "booking_detail", "payment", "confirmation",
    "my_bookings", "profile", "settings", "hotel_list", "flight_search"
]

ELEMENTS = {
    "home": ["search_button", "featured_deals", "destination_card", "banner_cta"],
    "search_results": ["price_filter", "rating_filter", "sort_button", "booking_card", "pagination"],
    "booking_detail": ["add_to_cart", "view_reviews", "map_button", "contact", "share"],
    "payment": ["credit_card_input", "paypal_button", "promo_code", "submit_payment"],
    "confirmation": ["download_receipt", "contact_support", "book_again"]
}

DEVICES = ["mobile", "tablet", "desktop"]

def create_producer():
    """Create Kafka producer"""
    try:
        producer = KafkaProducer(
            bootstrap_servers=KAFKA_BROKER,
            value_serializer=lambda v: json.dumps(v).encode('utf-8'),
            compression_type='snappy'
        )
        logger.info("✅ Clickstream Producer initialized")
        return producer
    except Exception as e:
        logger.error(f"❌ Failed to initialize producer: {e}")
        return None

def generate_clickstream_event():
    """Generate a clickstream event"""
    page = random.choice(PAGES)
    element = random.choice(ELEMENTS.get(page, ELEMENTS["home"]))
    device = random.choice(DEVICES)
    
    event = {
        "click_id": str(uuid.uuid4()),
        "user_id": f"user_{random.randint(1, 10000)}",
        "session_id": f"sess_{random.randint(1, 50000)}",
        "page_url": f"https://travel-booking.com/{page}",
        "element_id": element,
        "x_coordinate": random.randint(0, 1920),
        "y_coordinate": random.randint(0, 1080),
        "timestamp": datetime.now().isoformat(),
        "device_type": device,
        "page_load_time_ms": random.randint(100, 5000),
        "scroll_depth_percent": random.randint(0, 100)
    }
    return event

def send_clickstream_events(producer, count=100):
    """Send clickstream events to Kafka"""
    sent_count = 0
    
    for _ in range(count):
        try:
            event = generate_clickstream_event()
            future = producer.send(TOPIC, value=event)
            future.get(timeout=10)
            sent_count += 1
            
            if sent_count % 50 == 0:
                logger.info(f"✅ Clickstream: {sent_count} events sent")
                
        except KafkaError as e:
            logger.error(f"❌ Kafka error: {e}")
            break
        except Exception as e:
            logger.error(f"❌ Error: {e}")
    
    logger.info(f"✅ Successfully sent {sent_count} clickstream events")

def simulate_continuous_clickstream(duration_minutes=30, events_per_minute=60):
    """Simulate continuous clickstream traffic"""
    logger.info(f"🖱️  Starting clickstream simulation for {duration_minutes} minutes...")
    
    producer = create_producer()
    if not producer:
        return
    
    start_time = time.time()
    end_time = start_time + (duration_minutes * 60)
    
    while time.time() < end_time:
        try:
            # Send events for this minute
            send_clickstream_events(producer, count=events_per_minute)
            
            # Wait until next minute
            time.sleep(60)
            
        except KeyboardInterrupt:
            logger.info("⏹️  Clickstream simulation stopped")
            break
        except Exception as e:
            logger.error(f"❌ Error: {e}")
            time.sleep(5)
    
    producer.flush()
    producer.close()
    logger.info("✅ Clickstream simulation completed")

if __name__ == "__main__":
    # Wait for Kafka
    for attempt in range(30):
        try:
            producer = create_producer()
            if producer:
                producer.close()
                break
        except:
            if attempt < 29:
                logger.info(f"⏳ Waiting for Kafka... ({attempt+1}/30)")
                time.sleep(2)
    
    simulate_continuous_clickstream(duration_minutes=30)
