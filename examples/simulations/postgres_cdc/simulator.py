"""
PostgreSQL CDC Simulator
Simulates Change Data Capture events from PostgreSQL database
"""

import json
import random
import time
import uuid
from datetime import datetime, timedelta
from kafka import KafkaProducer
from kafka.errors import KafkaError
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

KAFKA_BROKER = "kafka:9092"
CDC_TOPIC = "topic_cdc_changes"

# Sample data for simulating CDC changes
USERS_TABLE = "public.users"
BOOKINGS_TABLE = "public.bookings"
PAYMENTS_TABLE = "public.payments"

CITIES = ["Ha Noi", "Ho Chi Minh", "Da Nang", "Can Tho", "Hai Phong"]
PAYMENT_METHODS = ["credit_card", "paypal", "bank_transfer", "cash"]
PAYMENT_STATUSES = ["pending", "completed", "failed", "refunded"]

def create_cdc_producer():
    """Create Kafka producer for CDC changes"""
    try:
        producer = KafkaProducer(
            bootstrap_servers=KAFKA_BROKER,
            value_serializer=lambda v: json.dumps(v).encode('utf-8'),
            acks='all',
            retries=3,
            compression_type='snappy'
        )
        logger.info("✅ CDC Producer initialized")
        return producer
    except Exception as e:
        logger.error(f"❌ Failed to create producer: {e}")
        return None

def generate_cdc_change(operation, table_name, primary_key, before_values=None, after_values=None):
    """Generate a CDC change event"""
    return {
        "change_id": str(uuid.uuid4()),
        "table_name": table_name,
        "operation": operation,
        "primary_key": primary_key,
        "before_values": before_values,
        "after_values": after_values,
        "timestamp": datetime.now().isoformat(),
        "source_database": "PostgreSQL",
        "debezium_metadata": {
            "source": {
                "connector": "postgresql",
                "db": "travel_booking",
                "schema": "public"
            },
            "transaction_ts": int(time.time() * 1000)
        }
    }

def simulate_user_insert(producer):
    """Simulate INSERT operation on users table"""
    user_id = str(uuid.uuid4())
    after_values = {
        "id": user_id,
        "email": f"user_{user_id[:8]}@example.com",
        "full_name": f"User {user_id[:4]}",
        "phone": f"0{random.randint(900000000, 999999999)}",
        "country": "Vietnam",
        "created_at": datetime.now().isoformat(),
        "updated_at": datetime.now().isoformat()
    }
    
    cdc_change = generate_cdc_change(
        operation="INSERT",
        table_name=USERS_TABLE,
        primary_key={"id": user_id},
        after_values=after_values
    )
    
    try:
        future = producer.send(CDC_TOPIC, value=cdc_change)
        future.get(timeout=10)
        logger.info(f"✅ User INSERT: {user_id}")
    except KafkaError as e:
        logger.error(f"❌ Kafka error: {e}")

def simulate_booking_insert(producer):
    """Simulate INSERT operation on bookings table"""
    booking_id = str(uuid.uuid4())
    user_id = str(uuid.uuid4())
    
    after_values = {
        "id": booking_id,
        "user_id": user_id,
        "destination": random.choice(CITIES),
        "check_in_date": (datetime.now() + timedelta(days=random.randint(1, 30))).isoformat(),
        "check_out_date": (datetime.now() + timedelta(days=random.randint(31, 60))).isoformat(),
        "num_guests": random.randint(1, 6),
        "total_price": round(random.uniform(100, 5000), 2),
        "status": "confirmed",
        "created_at": datetime.now().isoformat(),
        "updated_at": datetime.now().isoformat()
    }
    
    cdc_change = generate_cdc_change(
        operation="INSERT",
        table_name=BOOKINGS_TABLE,
        primary_key={"id": booking_id},
        after_values=after_values
    )
    
    try:
        future = producer.send(CDC_TOPIC, value=cdc_change)
        future.get(timeout=10)
        logger.info(f"✅ Booking INSERT: {booking_id}")
    except KafkaError as e:
        logger.error(f"❌ Kafka error: {e}")

def simulate_booking_update(producer):
    """Simulate UPDATE operation on bookings table"""
    booking_id = f"booking_{uuid.uuid4().hex[:8]}"
    
    before_values = {
        "status": "pending",
        "updated_at": (datetime.now() - timedelta(minutes=10)).isoformat()
    }
    
    after_values = {
        "status": "confirmed",
        "updated_at": datetime.now().isoformat()
    }
    
    cdc_change = generate_cdc_change(
        operation="UPDATE",
        table_name=BOOKINGS_TABLE,
        primary_key={"id": booking_id},
        before_values=before_values,
        after_values=after_values
    )
    
    try:
        future = producer.send(CDC_TOPIC, value=cdc_change)
        future.get(timeout=10)
        logger.info(f"✅ Booking UPDATE: {booking_id}")
    except KafkaError as e:
        logger.error(f"❌ Kafka error: {e}")

def simulate_payment_insert(producer):
    """Simulate INSERT operation on payments table"""
    payment_id = str(uuid.uuid4())
    booking_id = f"booking_{uuid.uuid4().hex[:8]}"
    
    after_values = {
        "id": payment_id,
        "booking_id": booking_id,
        "amount": round(random.uniform(100, 5000), 2),
        "currency": "USD",
        "payment_method": random.choice(PAYMENT_METHODS),
        "status": random.choice(PAYMENT_STATUSES),
        "created_at": datetime.now().isoformat(),
        "updated_at": datetime.now().isoformat()
    }
    
    cdc_change = generate_cdc_change(
        operation="INSERT",
        table_name=PAYMENTS_TABLE,
        primary_key={"id": payment_id},
        after_values=after_values
    )
    
    try:
        future = producer.send(CDC_TOPIC, value=cdc_change)
        future.get(timeout=10)
        logger.info(f"✅ Payment INSERT: {payment_id}")
    except KafkaError as e:
        logger.error(f"❌ Kafka error: {e}")

def simulate_cdc_stream(duration_minutes=5):
    """Simulate continuous CDC stream"""
    logger.info(f"📀 Starting PostgreSQL CDC simulation for {duration_minutes} minutes...")
    
    producer = create_cdc_producer()
    if not producer:
        return
    
    start_time = time.time()
    end_time = start_time + (duration_minutes * 60)
    
    operations = [
        simulate_user_insert,
        simulate_booking_insert,
        simulate_booking_update,
        simulate_payment_insert
    ]
    
    while time.time() < end_time:
        try:
            # Randomly perform CDC operations
            operation = random.choice(operations)
            operation(producer)
            
            # Wait between operations
            time.sleep(random.uniform(2, 5))
            
        except KeyboardInterrupt:
            logger.info("⏹️  CDC simulation stopped by user")
            break
        except Exception as e:
            logger.error(f"❌ Error in CDC simulation: {e}")
            time.sleep(5)
    
    producer.flush()
    producer.close()
    logger.info("✅ PostgreSQL CDC simulation completed")

if __name__ == "__main__":
    # Wait for Kafka to be ready
    for attempt in range(30):
        try:
            producer = create_cdc_producer()
            if producer:
                producer.close()
                break
        except:
            if attempt < 29:
                logger.info(f"⏳ Waiting for Kafka to be ready... ({attempt+1}/30)")
                time.sleep(2)
    
    # Run simulation
    simulate_cdc_stream(duration_minutes=30)
