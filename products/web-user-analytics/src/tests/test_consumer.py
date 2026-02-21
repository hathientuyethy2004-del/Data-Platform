"""
Web User Analytics - Unit Tests

Tests for core analytics components including consumers, transformations, and APIs.
Run with: pytest tests/ -v
"""

import pytest
from datetime import datetime, timedelta, timezone
from unittest.mock import Mock, patch, MagicMock
import json

# Import modules to test
from src.ingestion.schema import (
    EventType, PageViewEvent, ClickEvent, create_event, BaseEvent
)
from src.ingestion.validators import (
    BotDetector, EventValidator, EventFilter, DataQualityChecker
)
from src.ingestion.session_tracker import (
    Session, SessionManager, SessionAttributor, SessionReconstructor
)


class TestEventSchemas:
    """Test event schema validation"""
    
    def test_create_page_view_event(self):
        """Test creating page view event"""
        event_data = {
            "event_id": "evt_123",
            "user_id": "user_456",
            "session_id": "sess_789",
            "event_type": "page_view",
            "timestamp": datetime.now(timezone.utc),
            "page_url": "https://example.com/page1",
            "page_path": "/page1",
            "page_title": "Page 1",
            "browser": "Chrome",
            "os": "Windows",
            "country": "US",
            "user_agent": "Mozilla/5.0",
            "ip_address": "192.168.1.1",
            "device_type": "desktop",
        }
        
        event = PageViewEvent(**event_data)
        assert event.event_id == "evt_123"
        assert event.page_url == "https://example.com/page1"
        assert event.event_type == EventType.PAGE_VIEW
    
    def test_create_event_from_type(self):
        """Test event creation from type"""
        event_data = {
            "event_id": "evt_123",
            "user_id": "user_456",
            "session_id": "sess_789",
            "event_type": "page_view",
            "timestamp": datetime.now(timezone.utc),
            "page_url": "https://example.com",
            "page_path": "/",
            "page_title": "Home",
            "browser": "Chrome",
            "os": "Windows",
            "country": "US",
            "user_agent": "Mozilla",
            "ip_address": "192.168.1.1",
        }
        
        event = create_event("page_view", event_data)
        assert isinstance(event, PageViewEvent)
        assert event.event_id == "evt_123"


class TestBotDetection:
    """Test bot detection logic"""
    
    def test_detect_googlebot(self):
        """Test detection of Googlebot"""
        user_agent = "Mozilla/5.0 (compatible; Googlebot/2.1)"
        is_bot = BotDetector.is_bot(user_agent, {})
        assert is_bot is True
    
    def test_detect_normal_user(self):
        """Test normal user detection"""
        user_agent = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) Chrome/91.0"
        is_bot = BotDetector.is_bot(user_agent, {})
        assert is_bot is False
    
    def test_detect_suspicious_timing(self):
        """Test detection of suspicious behavior"""
        user_agent = "Mozilla/5.0 Chrome/91.0"
        properties = {"page_load_time_ms": 5}  # Suspiciously fast
        is_bot = BotDetector.is_bot(user_agent, properties)
        assert is_bot is True


class TestEventValidation:
    """Test event validation"""
    
    def test_validate_valid_event(self):
        """Test validation of valid event"""
        event_data = {
            "event_id": "evt_123",
            "user_id": "user_456",
            "session_id": "sess_789",
            "event_type": "page_view",
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "page_url": "https://example.com",
            "browser": "Chrome",
            "os": "Windows",
            "country": "US",
            "user_agent": "Mozilla",
            "ip_address": "192.168.1.1",
        }
        
        is_valid, error = EventValidator.validate_event(event_data)
        assert is_valid is True
        assert error is None
    
    def test_validate_missing_field(self):
        """Test validation with missing required field"""
        event_data = {
            "event_id": "evt_123",
            # Missing user_id
            "session_id": "sess_789",
            "event_type": "page_view",
            "timestamp": datetime.now(timezone.utc).isoformat(),
        }
        
        is_valid, error = EventValidator.validate_event(event_data)
        assert is_valid is False
        assert "Missing required field" in error
    
    def test_validate_invalid_url(self):
        """Test validation of invalid URL"""
        event_data = {
            "event_id": "evt_123",
            "user_id": "user_456",
            "session_id": "sess_789",
            "event_type": "page_view",
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "page_url": "not-a-valid-url",
            "browser": "Chrome",
            "os": "Windows",
            "country": "US",
            "user_agent": "Mozilla",
            "ip_address": "192.168.1.1",
        }
        
        is_valid, error = EventValidator.validate_page_view(event_data)
        assert is_valid is False


class TestEventFiltering:
    """Test event filtering logic"""
    
    def test_filter_bot_traffic(self):
        """Test filtering of bot traffic"""
        event_data = {
            "event_id": "evt_123",
            "user_id": "bot_user",
            "session_id": "sess_789",
            "event_type": "page_view",
            "user_agent": "Googlebot/2.1",
            "ip_address": "192.168.1.1",
            "properties": {},
        }
        
        should_filter, reason = EventFilter.should_filter_event(event_data, bot_detection_enabled=True)
        assert should_filter is True
        assert reason == "bot_traffic_detected"
    
    def test_filter_valid_traffic(self):
        """Test that valid traffic is not filtered"""
        event_data = {
            "event_id": "evt_123",
            "user_id": "user_456",
            "session_id": "sess_789",
            "event_type": "page_view",
            "user_agent": "Mozilla/5.0 Chrome/91.0",
            "ip_address": "192.168.1.100",
            "properties": {},
        }
        
        should_filter, reason = EventFilter.should_filter_event(event_data)
        assert should_filter is False


class TestSessionTracking:
    """Test session tracking"""
    
    def test_create_session(self):
        """Test session creation"""
        manager = SessionManager()
        session = manager.create_session(
            session_id="sess_123",
            user_id="user_456",
            traffic_source="organic"
        )
        
        assert session.session_id == "sess_123"
        assert session.user_id == "user_456"
        assert session.traffic_source == "organic"
    
    def test_add_event_to_session(self):
        """Test adding events to session"""
        manager = SessionManager()
        session = manager.create_session("sess_123", "user_456")
        
        event_data = {
            "event_id": "evt_1",
            "event_type": "page_view",
            "page_url": "https://example.com/page1",
        }
        
        session.add_event(event_data)
        
        assert len(session.events) == 1
        assert session.get_page_view_count() == 1
    
    def test_session_bounce_detection(self):
        """Test bounce session detection"""
        manager = SessionManager()
        session = manager.create_session("sess_123", "user_456")
        
        # Add only one page view
        event_data = {"event_id": "evt_1", "event_type": "page_view", "page_url": "https://example.com"}
        session.add_event(event_data)
        
        assert session.is_bounce_session() is True
    
    def test_session_timeout(self):
        """Test session timeout detection"""
        manager = SessionManager(session_timeout=60)  # 1 minute
        session = manager.create_session("sess_123", "user_456")
        
        # Simulate old last activity
        session.last_activity_time = datetime.now(timezone.utc) - timedelta(minutes=2)
        
        timed_out = manager.get_timed_out_sessions()
        
        assert len(timed_out) > 0
        assert timed_out[0].session_id == "sess_123"
    
    def test_returning_user_detection(self):
        """Test returning user detection"""
        manager = SessionManager()
        
        # Create multiple sessions for same user
        manager.create_session("sess_1", "user_456")
        manager.create_session("sess_2", "user_456")
        
        is_returning = manager.get_user_is_returning("user_456")
        
        assert is_returning is True


class TestSessionAttribution:
    """Test session traffic attribution"""
    
    def test_detect_direct_traffic(self):
        """Test detection of direct traffic"""
        traffic_source = SessionAttributor.get_traffic_source(None, None)
        assert traffic_source == "direct"
    
    def test_detect_organic_traffic(self):
        """Test detection of organic search traffic"""
        referrer = "https://www.google.com/search?q=example"
        traffic_source = SessionAttributor.get_traffic_source(referrer, None)
        assert traffic_source == "organic"
    
    def test_detect_utm_traffic(self):
        """Test detection of UTM-tagged traffic"""
        traffic_source = SessionAttributor.get_traffic_source(None, "facebook")
        assert traffic_source == "facebook"


class TestDataQualityChecker:
    """Test data quality checks"""
    
    def test_quality_check_valid_event(self):
        """Test quality check of valid event"""
        event_data = {
            "event_id": "evt_123",
            "user_id": "user_456",
            "session_id": "sess_789",
            "event_type": "page_view",
            "timestamp": datetime.now(timezone.utc),
            "browser": "Chrome",
            "os": "Windows",
            "country": "US",
            "user_agent": "Mozilla",
            "ip_address": "192.168.1.1",
        }
        
        quality = DataQualityChecker.check_event_quality(event_data)
        
        assert quality["is_valid"] is True
        assert quality["completeness"] > 0.8
    
    def test_quality_check_missing_fields(self):
        """Test quality check with missing fields"""
        event_data = {
            "event_id": "evt_123",
            # Missing several fields
            "event_type": "page_view",
        }
        
        quality = DataQualityChecker.check_event_quality(event_data)
        
        assert quality["is_valid"] is False
        assert len(quality["missing_fields"]) > 0


class TestIntegration:
    """Integration tests"""
    
    def test_end_to_end_event_processing(self):
        """Test complete event processing pipeline"""
        # Create event
        event_data = {
            "event_id": "evt_123",
            "user_id": "user_456",
            "session_id": "sess_789",
            "event_type": "page_view",
            "timestamp": datetime.now(timezone.utc),
            "page_url": "https://example.com/page1",
            "page_path": "/page1",
            "page_title": "Page 1",
            "browser": "Chrome",
            "browser_version": "91.0",
            "os": "Windows",
            "os_version": "10",
            "country": "US",
            "region": "CA",
            "user_agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) Chrome/91.0",
            "ip_address": "192.168.1.100",
            "device_type": "desktop",
        }
        
        # Validate
        is_valid, error = EventValidator.validate_event(event_data)
        assert is_valid is True
        
        # Filter
        should_filter, reason = EventFilter.should_filter_event(event_data)
        assert should_filter is False
        
        # Check quality
        quality = DataQualityChecker.check_event_quality(event_data)
        assert quality["is_valid"] is True
        
        # Create event object
        event = create_event("page_view", event_data)
        assert isinstance(event, PageViewEvent)
        
        # Track in session
        manager = SessionManager()
        session = manager.create_session("sess_789", "user_456")
        session.add_event(event_data)
        
        assert session.get_page_view_count() == 1


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
