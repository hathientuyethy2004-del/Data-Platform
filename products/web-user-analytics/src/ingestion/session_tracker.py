"""
Web User Analytics - Session Tracking

Manages session lifecycle, session timeout, and session state tracking.
Handles session reconstruction and session boundary detection.
"""

from datetime import datetime, timedelta
from typing import Dict, Optional, Tuple, Any, List
from dataclasses import dataclass, field
from enum import Enum


class SessionStatus(str, Enum):
    """Session lifecycle states"""
    ACTIVE = "active"
    TIMED_OUT = "timed_out"
    ENDED = "ended"
    INVALID = "invalid"


@dataclass
class Session:
    """Session state tracker"""
    session_id: str
    user_id: str
    start_time: datetime
    last_activity_time: datetime
    traffic_source: Optional[str] = None
    traffic_medium: Optional[str] = None
    campaign_name: Optional[str] = None
    
    # Session metrics
    page_views: List[str] = field(default_factory=list)  # URLs
    events: List[str] = field(default_factory=list)  # Event IDs
    event_types: Dict[str, int] = field(default_factory=dict)  # Event type counts
    
    # Device/Geographic
    device_type: Optional[str] = None
    browser: Optional[str] = None
    country: Optional[str] = None
    
    # Session quality
    is_bot: bool = False
    bot_score: float = 0.0
    
    # Status
    status: SessionStatus = SessionStatus.ACTIVE
    end_time: Optional[datetime] = None
    
    def add_event(self, event_data: Dict[str, Any]) -> None:
        """Add event to session"""
        event_id = event_data.get("event_id")
        event_type = event_data.get("event_type")
        
        if event_id:
            self.events.append(event_id)
        
        if event_type:
            self.event_types[event_type] = self.event_types.get(event_type, 0) + 1
        
        if event_type == "page_view":
            page_url = event_data.get("page_url")
            if page_url:
                self.page_views.append(page_url)
        
        self.last_activity_time = datetime.utcnow()
    
    def get_duration_seconds(self) -> int:
        """Get session duration in seconds"""
        end = self.end_time if self.end_time else datetime.utcnow()
        return int((end - self.start_time).total_seconds())
    
    def get_page_view_count(self) -> int:
        """Get number of page views"""
        return self.event_types.get("page_view", 0)
    
    def get_event_count(self) -> int:
        """Get total events"""
        return len(self.events)
    
    def is_bounce_session(self) -> bool:
        """Check if session is a bounce (single page view)"""
        return self.get_page_view_count() <= 1
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert session to dictionary"""
        return {
            "session_id": self.session_id,
            "user_id": self.user_id,
            "start_time": self.start_time.isoformat(),
            "end_time": self.end_time.isoformat() if self.end_time else None,
            "duration_seconds": self.get_duration_seconds(),
            "page_views": self.page_views,
            "events_count": self.get_event_count(),
            "page_view_count": self.get_page_view_count(),
            "unique_pages": len(set(self.page_views)),
            "device_type": self.device_type,
            "browser": self.browser,
            "country": self.country,
            "traffic_source": self.traffic_source,
            "is_bot": self.is_bot,
            "is_bounce": self.is_bounce_session(),
            "status": self.status.value,
        }


class SessionManager:
    """Manages session lifecycle and timeout"""
    
    # Session timeout in seconds (30 minutes by default)
    DEFAULT_SESSION_TIMEOUT = 30 * 60
    
    # Maximum session duration (24 hours)
    MAX_SESSION_DURATION = 24 * 60 * 60
    
    def __init__(self, session_timeout: int = DEFAULT_SESSION_TIMEOUT):
        """
        Initialize session manager.
        
        Args:
            session_timeout: Session timeout in seconds
        """
        self.session_timeout = session_timeout
        self.sessions: Dict[str, Session] = {}
        self.user_sessions: Dict[str, List[str]] = {}  # user_id -> [session_ids]
    
    def create_session(self, 
                      session_id: str,
                      user_id: str,
                      traffic_source: Optional[str] = None,
                      traffic_medium: Optional[str] = None,
                      campaign_name: Optional[str] = None) -> Session:
        """
        Create new session.
        
        Args:
            session_id: Unique session ID
            user_id: User ID
            traffic_source: Traffic source (direct, organic, paid, etc.)
            traffic_medium: Traffic medium (cpc, organic, referral, etc.)
            campaign_name: Campaign name if applicable
            
        Returns:
            Created Session object
        """
        now = datetime.utcnow()
        session = Session(
            session_id=session_id,
            user_id=user_id,
            start_time=now,
            last_activity_time=now,
            traffic_source=traffic_source,
            traffic_medium=traffic_medium,
            campaign_name=campaign_name,
        )
        
        self.sessions[session_id] = session
        
        if user_id not in self.user_sessions:
            self.user_sessions[user_id] = []
        self.user_sessions[user_id].append(session_id)
        
        return session
    
    def get_session(self, session_id: str) -> Optional[Session]:
        """Get session by ID"""
        return self.sessions.get(session_id)
    
    def update_session_activity(self, session_id: str, event_data: Dict[str, Any]) -> Optional[Session]:
        """
        Update session with new event.
        
        Args:
            session_id: Session ID
            event_data: Event data
            
        Returns:
            Updated Session or None if session not found
            
        Raises:
            ValueError: If session is timed out or ended
        """
        session = self.sessions.get(session_id)
        if not session:
            return None
        
        # Check for timeout
        time_since_last = (datetime.utcnow() - session.last_activity_time).total_seconds()
        if time_since_last > self.session_timeout:
            session.status = SessionStatus.TIMED_OUT
            return session
        
        # Check for max duration
        duration = (datetime.utcnow() - session.start_time).total_seconds()
        if duration > self.MAX_SESSION_DURATION:
            session.status = SessionStatus.ENDED
            session.end_time = datetime.utcnow()
            return session
        
        # Add event to session
        session.add_event(event_data)
        
        return session
    
    def end_session(self, session_id: str) -> Optional[Session]:
        """
        Explicitly end a session.
        
        Args:
            session_id: Session ID to end
            
        Returns:
            Ended Session or None if not found
        """
        session = self.sessions.get(session_id)
        if session:
            session.status = SessionStatus.ENDED
            session.end_time = datetime.utcnow()
        
        return session
    
    def get_timed_out_sessions(self) -> List[Session]:
        """Get all sessions that have timed out"""
        now = datetime.utcnow()
        timed_out = []
        
        for session in self.sessions.values():
            if session.status == SessionStatus.ACTIVE:
                time_since_last = (now - session.last_activity_time).total_seconds()
                if time_since_last > self.session_timeout:
                    session.status = SessionStatus.TIMED_OUT
                    timed_out.append(session)
        
        return timed_out
    
    def get_user_sessions(self, user_id: str) -> List[Session]:
        """Get all sessions for a user"""
        session_ids = self.user_sessions.get(user_id, [])
        return [self.sessions[sid] for sid in session_ids if sid in self.sessions]
    
    def get_active_sessions(self) -> List[Session]:
        """Get all active sessions"""
        return [s for s in self.sessions.values() if s.status == SessionStatus.ACTIVE]
    
    def get_user_is_returning(self, user_id: str) -> bool:
        """Check if user has previous sessions beyond current"""
        sessions = self.get_user_sessions(user_id)
        return len(sessions) > 1
    
    def clear_old_sessions(self, older_than_hours: int = 24) -> int:
        """
        Clear sessions older than specified hours.
        
        Args:
            older_than_hours: Remove sessions older than this many hours
            
        Returns:
            Number of sessions cleared
        """
        now = datetime.utcnow()
        cutoff = now - timedelta(hours=older_than_hours)
        
        sessions_to_remove = [
            sid for sid, session in self.sessions.items()
            if session.last_activity_time < cutoff
        ]
        
        for sid in sessions_to_remove:
            del self.sessions[sid]
        
        return len(sessions_to_remove)
    
    def get_stats(self) -> Dict[str, Any]:
        """Get session manager statistics"""
        active_sessions = [s for s in self.sessions.values() if s.status == SessionStatus.ACTIVE]
        
        return {
            "total_sessions": len(self.sessions),
            "active_sessions": len(active_sessions),
            "unique_users": len(self.user_sessions),
            "avg_session_duration_sec": (
                sum(s.get_duration_seconds() for s in self.sessions.values()) / len(self.sessions)
                if self.sessions else 0
            ),
            "avg_events_per_session": (
                sum(s.get_event_count() for s in self.sessions.values()) / len(self.sessions)
                if self.sessions else 0
            ),
        }


class SessionAttributor:
    """Attributes traffic source and campaign information to sessions"""
    
    TRAFFIC_SOURCES = {
        "direct": "Direct",
        "organic": "Organic Search",
        "paid": "Paid Search",
        "social": "Social Media",
        "referral": "Referral",
        "email": "Email",
        "dark": "Dark Traffic",
        "affiliate": "Affiliate",
    }
    
    @staticmethod
    def get_traffic_source(referrer: Optional[str], 
                           utm_source: Optional[str]) -> str:
        """
        Determine traffic source for session.
        
        Args:
            referrer: HTTP referrer header
            utm_source: UTM source parameter
            
        Returns:
            Traffic source value
        """
        # UTM source takes priority
        if utm_source:
            return utm_source.lower()
        
        # Check referrer
        if not referrer or referrer == "":
            return "direct"
        
        # Analyze referrer domain
        if "google" in referrer.lower():
            return "organic"
        elif "facebook" in referrer.lower() or "twitter" in referrer.lower() or "linkedin" in referrer.lower():
            return "social"
        else:
            return "referral"
    
    @staticmethod
    def get_traffic_medium(referrer: Optional[str],
                          utm_medium: Optional[str]) -> Optional[str]:
        """
        Determine traffic medium.
        
        Args:
            referrer: HTTP referrer
            utm_medium: UTM medium parameter
            
        Returns:
            Traffic medium value
        """
        if utm_medium:
            return utm_medium.lower()
        
        if "cpc" in (referrer or "").lower():
            return "cpc"
        elif "display" in (referrer or "").lower():
            return "display"
        
        return None


class SessionReconstructor:
    """Reconstructs sessions from events"""
    
    @staticmethod
    def reconstruct_session(events: List[Dict[str, Any]],
                           session_timeout: int = SessionManager.DEFAULT_SESSION_TIMEOUT) -> Session:
        """
        Reconstruct session from list of events.
        
        Args:
            events: List of events in session
            session_timeout: Session timeout in seconds
            
        Returns:
            Reconstructed Session object
            
        Raises:
            ValueError: If events list is empty
        """
        if not events:
            raise ValueError("Cannot reconstruct session from empty events list")
        
        # Sort events by timestamp
        sorted_events = sorted(events, key=lambda e: e.get("timestamp", ""))
        
        first_event = sorted_events[0]
        last_event = sorted_events[-1]
        
        session_id = first_event.get("session_id")
        user_id = first_event.get("user_id")
        
        session = Session(
            session_id=session_id,
            user_id=user_id,
            start_time=datetime.fromisoformat(str(first_event.get("timestamp"))),
            last_activity_time=datetime.fromisoformat(str(last_event.get("timestamp"))),
        )
        
        # Extract session attributes
        session_start_event = next(
            (e for e in sorted_events if e.get("event_type") == "session_start"),
            first_event
        )
        
        session.traffic_source = session_start_event.get("traffic_source")
        session.traffic_medium = session_start_event.get("traffic_medium")
        session.campaign_name = session_start_event.get("campaign_name")
        
        # Add all events
        for event in sorted_events:
            session.add_event(event)
        
        # Set other attributes from first event
        session.device_type = first_event.get("device_type")
        session.browser = first_event.get("browser")
        session.country = first_event.get("country")
        session.is_bot = first_event.get("is_bot", False)
        
        return session


# Global session manager instance
session_manager = SessionManager()
session_attributor = SessionAttributor()
session_reconstructor = SessionReconstructor()
