"""
Web User Analytics - Event Validators

Validates events for data quality, schema compliance, and business rules.
Performs filtering for bot traffic, invalid data, and duplicate detection.
"""

import re
import hashlib
from typing import Dict, Any, Optional, Tuple, List
from datetime import datetime
from .schema import BaseEvent, PageViewEvent, EventType


class BotDetector:
    """Detects bot traffic based on user agent and behavior patterns"""
    
    # Common bot user agents (partial matches)
    BOT_USER_AGENTS = [
        "googlebot", "bingbot", "slurp", "duckduckbot", "baiduspider",
        "yandexbot", "facebookexternalhit", "twitterbot", "linkedinbot",
        "whatsapp", "telegrambot", "slackbot", "discordbot", "curl",
        "wget", "python", "scrapy", "applebot", "ahrefsbot", "semrushbot",
        "mj12bot", "dotbot", "majestic", "ahrefs", "rogerbot"
    ]
    
    @staticmethod
    def is_bot(user_agent: str, properties: Dict[str, Any]) -> bool:
        """
        Detect if traffic is from a bot.
        
        Args:
            user_agent: User agent string
            properties: Event properties for behavioral analysis
            
        Returns:
            True if likely bot, False otherwise
        """
        user_agent_lower = user_agent.lower()
        
        # User agent based detection
        for bot_ua in BotDetector.BOT_USER_AGENTS:
            if bot_ua in user_agent_lower:
                return True
        
        # Behavioral detection
        # Bots typically have very short page load times or specific patterns
        if "page_load_time_ms" in properties:
            page_load = properties.get("page_load_time_ms", 0)
            if page_load < 10:  # Suspiciously fast
                return True
        
        # Bots often provide explicit impossible viewport values
        if "viewport_width" in properties and properties.get("viewport_width") == 0:
            return True
        
        return False


class EventValidator:
    """Validates events for data quality and business rules"""
    
    # Valid countries (simplified - use real country list in production)
    VALID_COUNTRIES = set([
        "US", "GB", "CA", "AU", "DE", "FR", "JP", "CN", "IN", "BR",
        "MX", "SG", "HK", "NZ", "ZA", "KR", "VN", "ID", "TH", "MY"
    ])
    
    @staticmethod
    def validate_core_event(event_data: Dict[str, Any]) -> Tuple[bool, Optional[str]]:
        """
        Validate core event envelope fields only.

        Args:
            event_data: Raw event dictionary

        Returns:
            Tuple of (is_valid: bool, error_message: str or None)
        """
        required_fields = ["event_id", "user_id", "session_id", "event_type", "timestamp"]
        for field in required_fields:
            if field not in event_data:
                return False, f"Missing required field: {field}"

        valid_types = [e.value for e in EventType]
        if event_data["event_type"] not in valid_types:
            return False, f"Invalid event_type: {event_data['event_type']}"

        try:
            if isinstance(event_data["timestamp"], str):
                datetime.fromisoformat(event_data["timestamp"])
            elif not isinstance(event_data["timestamp"], datetime):
                return False, "timestamp must be ISO string or datetime"
        except ValueError:
            return False, f"Invalid timestamp format: {event_data['timestamp']}"

        return True, None

    @staticmethod
    def validate_event(event_data: Dict[str, Any]) -> Tuple[bool, Optional[str]]:
        """
        Validate event data for completeness and validity.
        
        Args:
            event_data: Raw event dictionary
            
        Returns:
            Tuple of (is_valid: bool, error_message: str or None)
        """
        is_valid, error = EventValidator.validate_core_event(event_data)
        if not is_valid:
            return False, error
        
        # Validate event-specific fields
        event_type = event_data["event_type"]
        if event_type == EventType.PAGE_VIEW.value:
            if "page_url" not in event_data or not event_data["page_url"]:
                return False, "page_view requires page_url"
            if "page_load_time_ms" in event_data:
                if not isinstance(event_data["page_load_time_ms"], (int, float)):
                    return False, "page_load_time_ms must be numeric"
        
        elif event_type == EventType.SCROLL.value:
            if "scroll_depth" not in event_data:
                return False, "scroll requires scroll_depth"
            scroll_depth = event_data["scroll_depth"]
            if not isinstance(scroll_depth, int) or scroll_depth < 0 or scroll_depth > 100:
                return False, f"scroll_depth must be 0-100, got: {scroll_depth}"
        
        elif event_type == EventType.FORM_SUBMIT.value:
            if "form_success" not in event_data:
                return False, "form_submit requires form_success"
        
        elif event_type == EventType.SESSION_START.value:
            if "traffic_source" not in event_data:
                return False, "session_start requires traffic_source"
        
        elif event_type == EventType.SESSION_END.value:
            if "session_duration_seconds" not in event_data:
                return False, "session_end requires session_duration_seconds"
        
        return True, None
    
    @staticmethod
    def validate_page_view(event_data: Dict[str, Any]) -> Tuple[bool, Optional[str]]:
        """Validate page_view specific fields"""
        if "page_url" not in event_data:
            return False, "page_url required"
        
        # Validate URL format
        url = event_data["page_url"]
        if not url.startswith(("http://", "https://")):
            return False, f"Invalid URL format: {url}"
        
        # Validate page_load_time if present
        if "page_load_time_ms" in event_data:
            load_time = event_data["page_load_time_ms"]
            if not isinstance(load_time, (int, float)):
                return False, "page_load_time_ms must be numeric"
            if load_time < 0 or load_time > 300000:  # Max 5 minutes
                return False, f"page_load_time_ms out of range: {load_time}"
        
        return True, None
    
    @staticmethod
    def validate_geographic(event_data: Dict[str, Any]) -> Tuple[bool, Optional[str]]:
        """Validate geographic data"""
        country = event_data.get("country", "").upper()
        
        # Country code should be 2 characters
        if len(country) != 2:
            return False, f"Invalid country code: {country}"
        
        # Should be alphabetic
        if not country.isalpha():
            return False, f"Country code must be alphabetic: {country}"
        
        return True, None


class EventFilter:
    """Filters events based on quality and business rules"""
    
    # Session timeout in seconds (30 minutes)
    SESSION_TIMEOUT = 30 * 60
    
    # Maximum events per session
    MAX_EVENTS_PER_SESSION = 10000
    
    @staticmethod
    def should_filter_event(event_data: Dict[str, Any], 
                           bot_detection_enabled: bool = True) -> Tuple[bool, Optional[str]]:
        """
        Determine if event should be filtered out.
        
        Args:
            event_data: Event data
            bot_detection_enabled: Whether to check for bots
            
        Returns:
            Tuple of (should_filter: bool, reason: str or None)
        """
        # Check for bot traffic
        if bot_detection_enabled:
            user_agent = event_data.get("user_agent", "")
            properties = event_data.get("properties", {})
            if BotDetector.is_bot(user_agent, properties):
                return True, "bot_traffic_detected"
        
        # Check for duplicate events (same event_id within short time)
        # This would be done with Redis/cache in production
        
        # Check for invalid IP
        ip = event_data.get("ip_address", "")
        if not EventFilter._is_valid_ip(ip):
            return True, f"invalid_ip:{ip}"
        
        # Check for missing critical fields
        if not event_data.get("user_id"):
            return True, "missing_user_id"
        
        if not event_data.get("session_id"):
            return True, "missing_session_id"
        
        return False, None
    
    @staticmethod
    def _is_valid_ip(ip: str) -> bool:
        """Validate IP address format"""
        if not ip:
            return False
        
        # Simple IPv4 validation
        parts = ip.split(".")
        if len(parts) == 4:
            try:
                return all(0 <= int(part) <= 255 for part in parts)
            except ValueError:
                return False
        
        # IPv6 would be more complex, accept for now
        if ":" in ip:
            return True
        
        return False


class DuplicateDetector:
    """Detects duplicate events using event fuzzy matching"""
    
    @staticmethod
    def get_event_hash(event_data: Dict[str, Any]) -> str:
        """
        Create hash of event for duplicate detection.
        
        Args:
            event_data: Event data
            
        Returns:
            MD5 hash of key event fields
        """
        key_fields = [
            event_data.get("event_id", ""),
            event_data.get("user_id", ""),
            event_data.get("session_id", ""),
            event_data.get("event_type", ""),
            str(event_data.get("timestamp", "")),
        ]
        
        key_string = "|".join(str(f) for f in key_fields)
        return hashlib.md5(key_string.encode()).hexdigest()
    
    @staticmethod
    def is_likely_duplicate(current_hash: str, 
                           recent_hashes: List[str],
                           time_window_seconds: int = 60) -> bool:
        """
        Check if event is likely a duplicate.
        
        Args:
            current_hash: Hash of current event
            recent_hashes: List of recent event hashes
            time_window_seconds: Time window to consider
            
        Returns:
            True if likely duplicate, False otherwise
        """
        # In production, would also check timestamps
        return current_hash in recent_hashes


class DataQualityChecker:
    """Checks data quality metrics and statistics"""
    
    @staticmethod
    def check_event_quality(event_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Check data quality of event.
        
        Returns dict with quality metrics:
        """
        quality = {
            "is_valid": True,
            "completeness": 0.0,
            "missing_fields": [],
            "warnings": [],
            "errors": [],
        }
        
        # Check required fields
        required = ["event_id", "user_id", "session_id", "event_type", "timestamp"]
        present_fields = [f for f in required if f in event_data and event_data[f]]
        quality["completeness"] = len(present_fields) / len(required)
        quality["missing_fields"] = [f for f in required if f not in event_data or not event_data[f]]
        
        if quality["missing_fields"]:
            quality["is_valid"] = False
        
        # Check for PII
        for key in ["user_email", "credit_card", "phone"]:
            if key in event_data:
                quality["warnings"].append(f"Potential PII field detected: {key}")
        
        # Validate core schema envelope; strict event-specific checks run in pipeline validation
        is_valid, error = EventValidator.validate_core_event(event_data)
        if not is_valid:
            quality["is_valid"] = False
            quality["errors"].append(error)
        
        return quality


# Global validator instance
validator = EventValidator()
bot_detector = BotDetector()
event_filter = EventFilter()
qc = DataQualityChecker()
