"""
Web User Analytics - Event Schemas

Defines Pydantic schemas for event validation and serialization.
Supports 6 event types: page_view, click, scroll, form_submit, video_play, custom_event
"""

from datetime import datetime, timezone
from typing import Optional, Dict, Any, List
from enum import Enum
from pydantic import BaseModel, Field, validator, ConfigDict


class EventType(str, Enum):
    """Supported event types"""
    PAGE_VIEW = "page_view"
    CLICK = "click"
    SCROLL = "scroll"
    FORM_SUBMIT = "form_submit"
    VIDEO_PLAY = "video_play"
    CUSTOM_EVENT = "custom_event"
    SESSION_START = "session_start"
    SESSION_END = "session_end"


class DeviceType(str, Enum):
    """Supported device types"""
    MOBILE = "mobile"
    DESKTOP = "desktop"
    TABLET = "tablet"
    UNKNOWN = "unknown"


class BaseEvent(BaseModel):
    """Base schema for all events"""
    event_id: str = Field(..., description="Unique event identifier")
    user_id: str = Field(..., description="User identifier")
    session_id: str = Field(..., description="Session identifier")
    event_type: EventType = Field(..., description="Type of event")
    timestamp: datetime = Field(default_factory=lambda: datetime.now(timezone.utc), description="Event timestamp")
    
    # Device info
    device_type: DeviceType = Field(default=DeviceType.UNKNOWN, description="Device type")
    device_brand: Optional[str] = Field(None, description="Device brand")
    device_model: Optional[str] = Field(None, description="Device model")
    
    # Browser info
    browser: str = Field(..., description="Browser name")
    browser_version: Optional[str] = Field(None, description="Browser version")
    os: str = Field(..., description="Operating system")
    os_version: Optional[str] = Field(None, description="OS version")
    
    # Geographic info
    country: str = Field(..., description="Country code (ISO 3166-1 alpha-2)")
    region: Optional[str] = Field(None, description="Region/state")
    city: Optional[str] = Field(None, description="City")
    
    # Session info
    is_new_session: bool = Field(default=False, description="Is this a new session?")
    is_returning_user: bool = Field(default=False, description="Is this a returning user?")
    user_agent: str = Field(..., description="Full user agent string")
    ip_address: str = Field(..., description="IP address")
    
    # Bot detection
    is_bot: bool = Field(default=False, description="Is traffic from bot?")
    
    # Additional metadata
    properties: Dict[str, Any] = Field(default_factory=dict, description="Custom properties")
    
    model_config = ConfigDict(use_enum_values=True)


class PageViewEvent(BaseEvent):
    """Schema for page_view events"""
    event_type: EventType = EventType.PAGE_VIEW
    
    # Page info
    page_url: str = Field(..., description="Full page URL")
    page_path: str = Field(..., description="URL path (without domain)")
    page_title: str = Field(..., description="Page title")
    referrer: Optional[str] = Field(None, description="Referrer URL")
    
    # Performance metrics
    page_load_time_ms: Optional[int] = Field(None, description="Page load time in milliseconds")
    dom_interactive_ms: Optional[int] = Field(None, description="DOM interactive time in ms")
    dom_complete_ms: Optional[int] = Field(None, description="DOM complete time in ms")
    
    # Viewport info
    viewport_width: Optional[int] = Field(None, description="Viewport width in pixels")
    viewport_height: Optional[int] = Field(None, description="Viewport height in pixels")


class ClickEvent(BaseEvent):
    """Schema for click events"""
    event_type: EventType = EventType.CLICK
    
    page_url: str = Field(..., description="Page URL where click occurred")
    element_id: Optional[str] = Field(None, description="ID of clicked element")
    element_class: Optional[str] = Field(None, description="Class of clicked element")
    element_text: Optional[str] = Field(None, description="Text content of clicked element")
    x_position: Optional[int] = Field(None, description="X coordinate of click")
    y_position: Optional[int] = Field(None, description="Y coordinate of click")
    target_url: Optional[str] = Field(None, description="Target URL if element is a link")


class ScrollEvent(BaseEvent):
    """Schema for scroll events"""
    event_type: EventType = EventType.SCROLL
    
    page_url: str = Field(..., description="Page URL where scroll occurred")
    scroll_depth: int = Field(..., description="Scroll depth percentage (0-100)")
    scroll_direction: str = Field(..., description="scroll_up or scroll_down")
    scroll_position_y: int = Field(..., description="Current scroll position in pixels")
    page_height: int = Field(..., description="Total page height in pixels")


class FormSubmitEvent(BaseEvent):
    """Schema for form_submit events"""
    event_type: EventType = EventType.FORM_SUBMIT
    
    page_url: str = Field(..., description="Page URL where form submitted")
    form_id: Optional[str] = Field(None, description="ID of form")
    form_name: Optional[str] = Field(None, description="Name of form")
    form_fields: Dict[str, Any] = Field(default_factory=dict, description="Form fields (PII hashed)")
    form_success: bool = Field(..., description="Did form submission succeed?")
    form_error: Optional[str] = Field(None, description="Error message if failed")


class VideoPlayEvent(BaseEvent):
    """Schema for video_play events"""
    event_type: EventType = EventType.VIDEO_PLAY
    
    page_url: str = Field(..., description="Page URL where video played")
    video_id: str = Field(..., description="Video identifier")
    video_title: Optional[str] = Field(None, description="Video title")
    video_duration_seconds: Optional[int] = Field(None, description="Total video duration")
    play_time_seconds: Optional[int] = Field(None, description="Seconds at which play started")
    autoplay: bool = Field(default=False, description="Was video autoplay?")


class CustomEvent(BaseEvent):
    """Schema for custom_event events"""
    event_type: EventType = EventType.CUSTOM_EVENT
    
    page_url: str = Field(..., description="Page URL for custom event")
    event_name: str = Field(..., description="Custom event name")
    event_category: Optional[str] = Field(None, description="Category of custom event")
    event_value: Optional[float] = Field(None, description="Numeric value of event")
    event_label: Optional[str] = Field(None, description="Label for event")


class SessionStartEvent(BaseEvent):
    """Schema for session_start events"""
    event_type: EventType = EventType.SESSION_START
    
    traffic_source: str = Field(..., description="Traffic source (direct, organic, paid, social, referral, email, dark)")
    traffic_medium: Optional[str] = Field(None, description="Traffic medium (e.g., cpc, organic, referral)")
    campaign_name: Optional[str] = Field(None, description="Campaign name if applicable")


class SessionEndEvent(BaseEvent):
    """Schema for session_end events"""
    event_type: EventType = EventType.SESSION_END
    
    session_duration_seconds: int = Field(..., description="Total session duration in seconds")
    pages_visited: int = Field(..., description="Number of pages visited in session")
    events_count: int = Field(..., description="Total events in session")


class BronzeEvent(BaseModel):
    """Raw event record in Bronze layer - minimal transformation"""
    event_id: str
    user_id: str
    session_id: str
    event_type: str
    timestamp: datetime
    raw_data: Dict[str, Any]  # Raw JSON
    ingested_at: datetime
    
    model_config = ConfigDict(use_enum_values=True)


class SilverPageView(BaseModel):
    """Cleaned and enriched page view for Silver layer"""
    event_id: str
    user_id: str
    session_id: str
    is_new_session: bool
    is_returning_user: bool
    
    # Page info
    page_url: str
    page_path: str
    page_title: str
    referrer: Optional[str]
    
    # Performance
    page_load_time_ms: Optional[int]
    
    # Device/Browser/OS
    device_type: str
    browser: str
    os: str
    
    # Geographic
    country: str
    region: Optional[str]
    
    # Bot check
    is_bot: bool
    
    # Timestamps
    timestamp: datetime
    event_date: str  # YYYY-MM-DD for partitioning
    event_hour: int  # 0-23 for partitioning


class GoldPageMetrics(BaseModel):
    """Aggregated page metrics in Gold layer"""
    page_id: str
    event_date: str
    event_hour: int
    
    # Counts
    page_views: int
    unique_visitors: int
    unique_sessions: int
    
    # Performance
    avg_page_load_time_ms: float
    p50_page_load_time_ms: float
    p90_page_load_time_ms: float
    p99_page_load_time_ms: float
    
    # Traffic
    bounce_rate: float  # 0-1
    avg_session_duration_sec: float
    
    # Device breakdown
    mobile_views: int
    desktop_views: int
    tablet_views: int
    
    # Top referrers
    top_referrer: Optional[str]
    
    # Geographic
    top_country: str
    top_region: Optional[str]
    
    # Bots
    bot_views: int
    
    # Timestamps
    aggregated_at: datetime


class GoldFunnelStep(BaseModel):
    """Funnel conversion metrics in Gold layer"""
    funnel_id: str
    step_number: int
    step_name: str
    event_date: str
    
    # Counts
    entered_count: int
    completed_count: int
    conversion_rate: float  # 0-1
    drop_off_count: int
    
    # Time metrics
    avg_time_to_next_ms: Optional[int]
    
    # Aggregated at
    aggregated_at: datetime


class GolSessionMetrics(BaseModel):
    """Session-level metrics in Gold layer"""
    session_id: str
    user_id: str
    event_date: str
    
    # Session info
    session_duration_seconds: int
    pages_visited: int
    events_count: int
    
    # Page views
    page_view_count: int
    unique_pages: int
    
    # Engagement
    click_count: int
    scroll_count: int
    form_submit_count: int
    
    # Device/Traffic
    device_type: str
    traffic_source: str
    
    # Geographic
    country: str
    
    # Bot flag
    is_bot: bool
    
    # Bounced?
    is_bounced: bool
    
    # Aggregated at
    aggregated_at: datetime


# Event factory for creating events from raw data
def create_event(event_type: str, data: Dict[str, Any]) -> BaseEvent:
    """
    Create event from event type and data dictionary.
    
    Args:
        event_type: Type of event
        data: Event data
        
    Returns:
        Instantiated event object
        
    Raises:
        ValueError: If event type not recognized
        ValidationError: If data validation fails
    """
    schema_map = {
        EventType.PAGE_VIEW.value: PageViewEvent,
        EventType.CLICK.value: ClickEvent,
        EventType.SCROLL.value: ScrollEvent,
        EventType.FORM_SUBMIT.value: FormSubmitEvent,
        EventType.VIDEO_PLAY.value: VideoPlayEvent,
        EventType.CUSTOM_EVENT.value: CustomEvent,
        EventType.SESSION_START.value: SessionStartEvent,
        EventType.SESSION_END.value: SessionEndEvent,
    }
    
    schema_class = schema_map.get(event_type)
    if not schema_class:
        raise ValueError(f"Unknown event type: {event_type}")
    
    return schema_class(**data)
