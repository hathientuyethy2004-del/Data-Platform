"""
Mobile App Simulator
Simulates user events from mobile app and sends to FastAPI Gateway
"""

import requests
import json
import random
import time
import uuid
from datetime import datetime
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

API_URL = "http://api:8000"

# Sample data pools
DESTINATIONS = ["Ha Noi", "Ho Chi Minh", "Da Nang", "Hai Phong", "Can Tho", "Hue"]
TRIP_TYPES = ["one_way", "round_trip", "multi_city"]
EVENT_TYPES = ["app_open", "page_view", "search", "filter_applied", "booking_view", "click_cta"]
USER_IDS = [f"user_{i}" for i in range(1, 101)]

def generate_session_id():
    return f"sess_{uuid.uuid4().hex[:8]}"

def send_user_event(event_type, user_id, session_id, properties):
    """Send user event to API"""
    payload = {
        "event_type": event_type,
        "user_id": user_id,
        "session_id": session_id,
        "app_type": "mobile",
        "timestamp": datetime.now().isoformat(),
        "properties": properties
    }
    
    try:
        response = requests.post(f"{API_URL}/events/user", json=payload, timeout=5)
        if response.status_code == 200:
            logger.info(f"✅ Mobile Event sent: {event_type} from {user_id}")
        else:
            logger.error(f"❌ Failed to send event: {response.status_code}")
    except Exception as e:
        logger.error(f"❌ Error sending event: {e}")

def simulate_user_journey():
    """Simulate a complete user journey"""
    user_id = random.choice(USER_IDS)
    session_id = generate_session_id()
    
    # App open
    send_user_event("app_open", user_id, session_id, {
        "app_version": "2.1.0",
        "os": "iOS"
    })
    time.sleep(random.uniform(0.5, 2))
    
    # Home page view
    send_user_event("page_view", user_id, session_id, {
        "page": "home",
        "source": "app_launch"
    })
    time.sleep(random.uniform(1, 3))
    
    # Search for destination
    destination = random.choice(DESTINATIONS)
    send_user_event("search", user_id, session_id, {
        "destination": destination,
        "check_in": "2026-03-01",
        "check_out": "2026-03-05"
    })
    time.sleep(random.uniform(0.5, 1.5))
    
    # Apply filters
    send_user_event("filter_applied", user_id, session_id, {
        "filter_type": "price",
        "min_price": 100,
        "max_price": 500
    })
    time.sleep(random.uniform(1, 2))
    
    # View booking detail
    send_user_event("booking_view", user_id, session_id, {
        "booking_id": f"book_{uuid.uuid4().hex[:6]}",
        "trip_type": random.choice(TRIP_TYPES),
        "price": round(random.uniform(100, 1000), 2)
    })
    time.sleep(random.uniform(0.5, 2))
    
    # Click CTA (potential conversion)
    if random.random() > 0.3:  # 70% conversion
        send_user_event("click_cta", user_id, session_id, {
            "cta_text": "Book Now",
            "destination": destination
        })

def simulate_continuous_traffic(duration_minutes=5):
    """Simulate continuous user traffic"""
    logger.info(f"🚀 Starting mobile app simulation for {duration_minutes} minutes...")
    
    start_time = time.time()
    end_time = start_time + (duration_minutes * 60)
    
    while time.time() < end_time:
        try:
            # Simulate 3-7 concurrent user journeys
            for _ in range(random.randint(3, 7)):
                simulate_user_journey()
            
            # Wait between batches
            time.sleep(random.uniform(2, 5))
            
        except KeyboardInterrupt:
            logger.info("⏹️  Simulation stopped by user")
            break
        except Exception as e:
            logger.error(f"❌ Error in simulation: {e}")
            time.sleep(5)
    
    logger.info("✅ Mobile app simulation completed")

if __name__ == "__main__":
    # Wait for API to be ready
    for attempt in range(30):
        try:
            response = requests.get(f"{API_URL}/health", timeout=2)
            if response.status_code == 200:
                logger.info("✅ API is ready")
                break
        except:
            if attempt < 29:
                logger.info(f"⏳ Waiting for API to be ready... ({attempt+1}/30)")
                time.sleep(2)
    
    # Run simulation
    simulate_continuous_traffic(duration_minutes=30)
