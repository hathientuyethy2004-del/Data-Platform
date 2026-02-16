"""
External Data Simulator
Simulates various external data sources (weather, maps, social media, etc.)
"""

import random
import time
import uuid
import json
from datetime import datetime, timedelta
from kafka import KafkaProducer
from kafka.errors import KafkaError
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

KAFKA_BROKER = "kafka:9092"
TOPIC = "topic_external_data"

# External data sources configuration
DATA_SOURCES = {
    "weather": {
        "cities": ["Ha Noi", "Ho Chi Minh", "Da Nang", "Can Tho", "Hai Phong"],
        "metrics": ["temperature", "humidity", "wind_speed"]
    },
    "market_data": {
        "symbols": ["AAPL", "GOOGL", "AMZN", "MSFT", "TSLA"],
        "metrics": ["price", "volume", "change_percent"]
    },
    "social_media": {
        "platforms": ["twitter", "instagram", "tiktok", "facebook"],
        "metrics": ["engagement", "reach", "sentiment"]
    },
    "travel_trends": {
        "categories": ["flights", "hotels", "tours", "restaurants"],
        "regions": ["Southeast Asia", "Europe", "Americas", "Asia Pacific"]
    }
}

def create_producer():
    """Create Kafka producer"""
    try:
        producer = KafkaProducer(
            bootstrap_servers=KAFKA_BROKER,
            value_serializer=lambda v: json.dumps(v).encode('utf-8'),
            compression_type='snappy'
        )
        logger.info("✅ External Data Producer initialized")
        return producer
    except Exception as e:
        logger.error(f"❌ Failed to initialize producer: {e}")
        return None

def generate_weather_data():
    """Generate weather data event"""
    city = random.choice(DATA_SOURCES["weather"]["cities"])
    return {
        "external_data_id": str(uuid.uuid4()),
        "source": "weather_api",
        "source_type": "api",
        "timestamp": datetime.now().isoformat(),
        "data": {
            "city": city,
            "temperature": round(15 + random.random() * 20, 2),
            "humidity": random.randint(40, 90),
            "wind_speed": round(random.random() * 15, 2),
            "condition": random.choice(["Clear", "Cloudy", "Rainy", "Sunny"]),
            "pressure_mb": round(1013 + random.random() * 10, 2)
        }
    }

def generate_market_data():
    """Generate market data event"""
    symbol = random.choice(DATA_SOURCES["market_data"]["symbols"])
    return {
        "external_data_id": str(uuid.uuid4()),
        "source": "market_data_api",
        "source_type": "api",
        "timestamp": datetime.now().isoformat(),
        "data": {
            "symbol": symbol,
            "price": round(100 + random.random() * 1000, 2),
            "volume": random.randint(1000000, 50000000),
            "change_percent": round(-5 + random.random() * 10, 2),
            "high": round(100 + random.random() * 1000, 2),
            "low": round(100 + random.random() * 1000, 2)
        }
    }

def generate_social_media_data():
    """Generate social media trend data"""
    platform = random.choice(DATA_SOURCES["social_media"]["platforms"])
    return {
        "external_data_id": str(uuid.uuid4()),
        "source": "social_media_api",
        "source_type": "api",
        "timestamp": datetime.now().isoformat(),
        "data": {
            "platform": platform,
            "trending_topic": f"Travel_{random.randint(1, 1000)}",
            "engagement_rate": round(random.random() * 100, 2),
            "reach": random.randint(10000, 10000000),
            "sentiment_score": round(-1 + random.random() * 2, 2),
            "post_count": random.randint(100, 10000)
        }
    }

def generate_travel_trends_data():
    """Generate travel trends data"""
    category = random.choice(DATA_SOURCES["travel_trends"]["categories"])
    region = random.choice(DATA_SOURCES["travel_trends"]["regions"])
    return {
        "external_data_id": str(uuid.uuid4()),
        "source": "travel_trends_api",
        "source_type": "api",
        "timestamp": datetime.now().isoformat(),
        "data": {
            "category": category,
            "region": region,
            "trend_score": round(random.random() * 100, 2),
            "booking_count": random.randint(100, 10000),
            "avg_price": round(100 + random.random() * 5000, 2),
            "year_over_year_growth_percent": round(-20 + random.random() * 50, 2)
        }
    }

def get_random_external_data():
    """Get random external data from any source"""
    generators = [
        generate_weather_data,
        generate_market_data,
        generate_social_media_data,
        generate_travel_trends_data
    ]
    return random.choice(generators)()

def send_external_data_batch(producer, count=100):
    """Send batch of external data events"""
    sent_count = 0
    
    for _ in range(count):
        try:
            event = get_random_external_data()
            future = producer.send(TOPIC, value=event)
            future.get(timeout=10)
            sent_count += 1
            
            if sent_count % 25 == 0:
                logger.info(f"✅ External Data: {sent_count} events sent")
                
        except KafkaError as e:
            logger.error(f"❌ Kafka error: {e}")
            break
        except Exception as e:
            logger.error(f"❌ Error: {e}")
    
    logger.info(f"✅ Successfully sent {sent_count} external data events")

def simulate_continuous_external_data(duration_minutes=30, events_per_batch=50):
    """Simulate continuous external data ingestion"""
    logger.info(f"🌐 Starting external data simulation for {duration_minutes} minutes...")
    
    producer = create_producer()
    if not producer:
        return
    
    start_time = time.time()
    end_time = start_time + (duration_minutes * 60)
    
    while time.time() < end_time:
        try:
            # Send batch of external data
            send_external_data_batch(producer, count=events_per_batch)
            
            # Wait before next batch
            time.sleep(random.uniform(5, 15))
            
        except KeyboardInterrupt:
            logger.info("⏹️  External data simulation stopped")
            break
        except Exception as e:
            logger.error(f"❌ Error: {e}")
            time.sleep(5)
    
    producer.flush()
    producer.close()
    logger.info("✅ External data simulation completed")

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
    
    simulate_continuous_external_data(duration_minutes=30)
