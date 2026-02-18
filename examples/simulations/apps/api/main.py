"""
FastAPI Application Data Gateway
Receives events from Mobile/Web Applications and publishes to Kafka
"""

from fastapi import FastAPI, HTTPException, BackgroundTasks
from pydantic import BaseModel
from typing import Optional, Dict, Any
from datetime import datetime
import json
import logging
from kafka import KafkaProducer
from kafka.errors import KafkaError
import uuid
from contextlib import asynccontextmanager

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Initialize Kafka Producer
kafka_producer = None

class UserEvent(BaseModel):
    """Mobile/Web App User Event"""
    event_type: str
    user_id: str
    session_id: str
    app_type: str  # 'mobile' or 'web'
    timestamp: Optional[datetime] = None
    properties: Dict[str, Any]
    
    class Config:
        json_schema_extra = {
            "example": {
                "event_type": "page_view",
                "user_id": "user_123",
                "session_id": "sess_abc",
                "app_type": "mobile",
                "timestamp": "2026-02-16T10:30:00Z",
                "properties": {
                    "page": "booking_detail",
                    "destination": "Ha Noi",
                    "trip_type": "round_trip"
                }
            }
        }

class BookingEvent(BaseModel):
    """Booking System Event"""
    event_type: str  # 'booking_created', 'booking_updated', 'payment_completed'
    booking_id: str
    user_id: str
    timestamp: Optional[datetime] = None
    properties: Dict[str, Any]

class ApplicationEvent(BaseModel):
    """Generic Application Event Wrapper"""
    event_id: str = None
    event_type: str
    source_app: str  # 'mobile_app', 'web_app', 'booking_system'
    timestamp: Optional[datetime] = None
    data: Dict[str, Any]

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Startup and shutdown events"""
    global kafka_producer
    try:
        # Initialize Kafka producer on startup
        kafka_producer = KafkaProducer(
            bootstrap_servers='kafka:9092',
            value_serializer=lambda v: json.dumps(v).encode('utf-8'),
            acks='all',
            retries=3
        )
        logger.info("✅ Kafka Producer initialized")
    except Exception as e:
        logger.error(f"❌ Failed to initialize Kafka Producer: {e}")
    
    yield
    
    # Cleanup on shutdown
    if kafka_producer:
        kafka_producer.flush()
        kafka_producer.close()
        logger.info("✅ Kafka Producer closed")

# Create FastAPI app
app = FastAPI(
    title="Data Platform - Application Data Layer",
    description="API Gateway for collecting events from Mobile/Web Applications",
    version="1.0.0",
    lifespan=lifespan
)

# Health check endpoint
@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "timestamp": datetime.now().isoformat(),
        "service": "Application Data Gateway"
    }

# User Events Endpoints
@app.post("/events/user")
async def track_user_event(event: UserEvent, background_tasks: BackgroundTasks):
    """
    Track user events from mobile/web applications
    
    Events include: page_view, click, search, booking_view, etc.
    """
    try:
        if not event.timestamp:
            event.timestamp = datetime.now()
        
        # Create event payload with unique ID
        event_payload = {
            "event_id": str(uuid.uuid4()),
            "event_type": event.event_type,
            "user_id": event.user_id,
            "session_id": event.session_id,
            "app_type": event.app_type,
            "timestamp": event.timestamp.isoformat(),
            "properties": event.properties
        }
        
        # Publish to Kafka (non-blocking)
        background_tasks.add_task(publish_to_kafka, "topic_app_events", event_payload)
        
        logger.info(f"✅ User event tracked: {event.event_type} from {event.app_type}")
        
        return {
            "status": "accepted",
            "event_id": event_payload["event_id"],
            "timestamp": datetime.now().isoformat()
        }
    except Exception as e:
        logger.error(f"❌ Error tracking user event: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/events/booking")
async def track_booking_event(event: BookingEvent, background_tasks: BackgroundTasks):
    """
    Track booking system events
    
    Events include: booking_created, booking_updated, payment_completed, booking_cancelled
    """
    try:
        if not event.timestamp:
            event.timestamp = datetime.now()
        
        event_payload = {
            "event_id": str(uuid.uuid4()),
            "event_type": event.event_type,
            "booking_id": event.booking_id,
            "user_id": event.user_id,
            "timestamp": event.timestamp.isoformat(),
            "properties": event.properties
        }
        
        background_tasks.add_task(publish_to_kafka, "topic_app_events", event_payload)
        
        logger.info(f"✅ Booking event tracked: {event.event_type}")
        
        return {
            "status": "accepted",
            "event_id": event_payload["event_id"],
            "timestamp": datetime.now().isoformat()
        }
    except Exception as e:
        logger.error(f"❌ Error tracking booking event: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/events/batch")
async def batch_events(events: list[ApplicationEvent], background_tasks: BackgroundTasks):
    """
    Batch publish multiple application events
    
    Useful for offline event batching from mobile apps
    """
    try:
        processed_events = 0
        
        for event in events:
            if not event.event_id:
                event.event_id = str(uuid.uuid4())
            if not event.timestamp:
                event.timestamp = datetime.now()
            
            event_payload = {
                "event_id": event.event_id,
                "event_type": event.event_type,
                "source_app": event.source_app,
                "timestamp": event.timestamp.isoformat(),
                "data": event.data
            }
            
            background_tasks.add_task(publish_to_kafka, "topic_app_events", event_payload)
            processed_events += 1
        
        logger.info(f"✅ Batch published: {processed_events} events")
        
        return {
            "status": "accepted",
            "events_processed": processed_events,
            "timestamp": datetime.now().isoformat()
        }
    except Exception as e:
        logger.error(f"❌ Error publishing batch events: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# Utility function to publish to Kafka
def publish_to_kafka(topic: str, message: Dict[str, Any]):
    """Publish message to Kafka topic"""
    global kafka_producer
    
    if not kafka_producer:
        logger.error("❌ Kafka producer not initialized")
        return
    
    try:
        future = kafka_producer.send(topic, value=message)
        record_metadata = future.get(timeout=10)
        logger.debug(f"Message sent to {record_metadata.topic} "
                    f"partition {record_metadata.partition} "
                    f"at offset {record_metadata.offset}")
    except KafkaError as e:
        logger.error(f"❌ Kafka error: {e}")
    except Exception as e:
        logger.error(f"❌ Error publishing to Kafka: {e}")

# Statistics endpoints
@app.get("/stats")
async def get_stats():
    """Get event statistics"""
    return {
        "status": "operational",
        "kafka_broker": "kafka:9092",
        "topics": ["topic_app_events"],
        "timestamp": datetime.now().isoformat()
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
