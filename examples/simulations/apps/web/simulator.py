"""
Web App Simulator
Simulates user events from web app and sends to FastAPI Gateway
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
PAGES = ["home", "search_results", "booking_detail", "my_bookings", "profile", "payment"]
USER_IDS = [f"user_{i}" for i in range(101, 201)]

def generate_session_id():
    return f"ses_{uuid.uuid4().hex[:8]}"

def send_user_event(event_type, user_id, session_id, properties):
    """Send user event to API"""
    payload = {
        "event_type": event_type,
        "user_id": user_id,
        "session_id": session_id,
        "app_type": "web",
        "timestamp": datetime.now().isoformat(),
        "properties": properties
    }
    
    try:
        response = requests.post(f"{API_URL}/events/user", json=payload, timeout=5)
        if response.status_code == 200:
            logger.info(f"✅ Web Event sent: {event_type} from {user_id}")
        else:
            logger.error(f"❌ Failed to send event: {response.status_code}")
    except Exception as e:
        logger.error(f"❌ Error sending event: {e}")

def simulate_user_session():
    """Simulate a complete web user session"""
    user_id = random.choice(USER_IDS)
    session_id = generate_session_id()
    
    # Page view - home
    send_user_event("page_view", user_id, session_id, {
        "page": "home",
        "referrer": "google.com" if random.random() > 0.5 else "direct",
        "device": "desktop"
    })
    time.sleep(random.uniform(1, 3))
    
    # Click on search
    send_user_event("click", user_id, session_id, {
        "element": "search_box",
        "page": "home"
    })
    time.sleep(random.uniform(0.5, 1.5))
    
    # Page view - search results
    destination = random.choice(DESTINATIONS)
    send_user_event("page_view", user_id, session_id, {
        "page": "search_results",
        "destination": destination,
        "results_count": random.randint(10, 100),
        "device": "desktop"
    })
    time.sleep(random.uniform(2, 5))
    
    # Sort/Filter applied
    send_user_event("filter_applied", user_id, session_id, {
        "filter_type": ["price", "rating", "distance"][random.randint(0, 2)],
        "value": random.choice(["asc", "desc"])
    })
    time.sleep(random.uniform(1, 2))
    
    # Click on item
    send_user_event("click", user_id, session_id, {
        "element": "booking_card",
        "booking_id": f"book_{uuid.uuid4().hex[:6]}"
    })
    time.sleep(random.uniform(1, 3))
    
    # Page view - booking detail
    send_user_event("page_view", user_id, session_id, {
        "page": "booking_detail",
        "trip_type": random.choice(TRIP_TYPES),
        "price": round(random.uniform(100, 1000), 2),
        "device": "desktop"
    })
    time.sleep(random.uniform(2, 4))
    
    # Add to cart
    if random.random() > 0.4:
        send_user_event("click", user_id, session_id, {
            "element": "add_to_cart",
            "action": "success"
        })
        time.sleep(random.uniform(1, 2))
        
        # Proceed to checkout
        if random.random() > 0.3:
            send_user_event("page_view", user_id, session_id, {
                "page": "payment",
                "payment_method": random.choice(["credit_card", "paypal", "bank_transfer"]),
                "device": "desktop"
            })

def simulate_continuous_traffic(duration_minutes=5):
    """Simulate continuous web user traffic"""
    logger.info(f"🌐 Starting web app simulation for {duration_minutes} minutes...")
    
    start_time = time.time()
    end_time = start_time + (duration_minutes * 60)
    
    while time.time() < end_time:
        try:
            # Simulate 2-5 concurrent user sessions
            for _ in range(random.randint(2, 5)):
                simulate_user_session()
            
            # Wait between batches
            time.sleep(random.uniform(3, 7))
            
        except KeyboardInterrupt:
            logger.info("⏹️  Simulation stopped by user")
            break
        except Exception as e:
            logger.error(f"❌ Error in simulation: {e}")
            time.sleep(5)
    
    logger.info("✅ Web app simulation completed")

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
