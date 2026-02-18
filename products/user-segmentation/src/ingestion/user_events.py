"""
User Segmentation - User Event Processing

Processes customer behavioral events for ML-based segmentation.
Extracts features: RFM, engagement, product usage, retention signals.
"""

from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional, Tuple
from pydantic import BaseModel, Field
from enum import Enum


class UserEventType(str, Enum):
    """User event types for segmentation"""
    PURCHASE = "purchase"
    VIEW_PRODUCT = "view_product"
    ADD_TO_CART = "add_to_cart"
    REMOVE_FROM_CART = "remove_from_cart"
    LOGIN = "login"
    LOGOUT = "logout"
    SUPPORT_TICKET = "support_ticket"
    EMAIL_OPEN = "email_open"
    FEATURE_USAGE = "feature_usage"
    CHURN_SIGNAL = "churn_signal"


class UserBehaviorEvent(BaseModel):
    """User behavioral event for segmentation"""
    event_id: str
    user_id: str
    event_type: UserEventType
    timestamp: datetime
    
    # Purchase events
    order_value: Optional[float] = None
    product_category: Optional[str] = None
    products_count: Optional[int] = None
    
    # Engagement
    session_duration_sec: Optional[int] = None
    pages_viewed: Optional[int] = None
    
    # Support
    ticket_priority: Optional[str] = None
    resolution_time_hours: Optional[int] = None
    
    # Email
    email_type: Optional[str] = None
    
    # Retention signals
    days_since_last_purchase: Optional[int] = None
    churn_risk_score: Optional[float] = None
    
    metadata: Dict[str, Any] = Field(default_factory=dict)


class RFMMetrics(BaseModel):
    """Recency, Frequency, Monetary metrics"""
    user_id: str
    recency_days: int  # Days since last purchase
    frequency: int  # Times purchased
    monetary: float  # Total spent
    recency_score: int = Field(..., ge=1, le=5)  # 1-5, 5 best
    frequency_score: int = Field(..., ge=1, le=5)
    monetary_score: int = Field(..., ge=1, le=5)
    rfm_score: int = Field(..., ge=111, le=555)  # Combined


class UserSegmentFeatures(BaseModel):
    """Features extracted for segmentation model"""
    user_id: str
    computed_date: str
    
    # RFM
    recency_days: int
    frequency: int
    monetary: float
    
    # Engagement
    avg_session_duration_sec: Optional[float] = None
    avg_pages_per_session: Optional[float] = None
    email_open_rate: Optional[float] = None
    
    # Product behavior
    product_categories_purchased: int
    avg_order_value: float
    repeat_purchase_rate: float
    
    # Support/satisfaction
    support_tickets: int
    avg_resolution_time_hours: Optional[float] = None
    
    # Retention indicators
    days_since_last_activity: int
    purchase_frequency_trend: float  # -1 to 1, positive = increasing
    churn_risk_score: float  # 0-1, 1 = high risk
    
    # Lifecycle stage
    customer_age_days: int  # Days since first purchase
    is_active: bool
    
    class Config:
        use_enum_values = True


class RFMCalculator:
    """Calculates RFM metrics from user events"""
    
    @staticmethod
    def calculate_rfm(user_events: List[Dict[str, Any]], 
                     reference_date: datetime) -> RFMMetrics:
        """
        Calculate RFM metrics for user.
        
        Args:
            user_events: List of user purchase events
            reference_date: Date to calculate metrics from
            
        Returns:
            RFMMetrics with scores
        """
        if not user_events:
            return RFMMetrics(
                user_id=user_events[0]['user_id'] if user_events else "unknown",
                recency_days=999,
                frequency=0,
                monetary=0.0,
                recency_score=1,
                frequency_score=1,
                monetary_score=1,
                rfm_score=111,
            )
        
        # Extract purchase events
        purchases = [e for e in user_events if e.get("event_type") == "purchase"]
        
        if not purchases:
            user_id = user_events[0]['user_id']
            return RFMMetrics(
                user_id=user_id,
                recency_days=999,
                frequency=0,
                monetary=0.0,
                recency_score=1,
                frequency_score=1,
                monetary_score=1,
                rfm_score=111,
            )
        
        # Calculate metrics
        last_purchase = max(p['timestamp'] for p in purchases)
        recency_days = (reference_date - last_purchase).days
        
        frequency = len(purchases)
        monetary = sum(p.get('order_value', 0) for p in purchases)
        
        # Score 1-5 (higher is better)
        recency_score = RFMCalculator._score_recency(recency_days)
        frequency_score = RFMCalculator._score_frequency(frequency)
        monetary_score = RFMCalculator._score_monetary(monetary)
        
        rfm_score = int(str(recency_score) + str(frequency_score) + str(monetary_score))
        
        return RFMMetrics(
            user_id=purchases[0]['user_id'],
            recency_days=recency_days,
            frequency=frequency,
            monetary=monetary,
            recency_score=recency_score,
            frequency_score=frequency_score,
            monetary_score=monetary_score,
            rfm_score=rfm_score,
        )
    
    @staticmethod
    def _score_recency(days: int) -> int:
        """Score recency (lower days = higher score)"""
        if days <= 30:
            return 5
        elif days <= 90:
            return 4
        elif days <= 180:
            return 3
        elif days <= 365:
            return 2
        else:
            return 1
    
    @staticmethod
    def _score_frequency(frequency: int) -> int:
        """Score purchase frequency"""
        if frequency >= 10:
            return 5
        elif frequency >= 5:
            return 4
        elif frequency >= 3:
            return 3
        elif frequency >= 1:
            return 2
        else:
            return 1
    
    @staticmethod
    def _score_monetary(monetary: float) -> int:
        """Score monetary value"""
        if monetary >= 5000:
            return 5
        elif monetary >= 2000:
            return 4
        elif monetary >= 500:
            return 3
        elif monetary >= 100:
            return 2
        else:
            return 1


class FeatureExtractor:
    """Extracts ML features from user events"""
    
    @staticmethod
    def extract_features(user_id: str,
                        user_events: List[Dict[str, Any]],
                        computed_date: str) -> UserSegmentFeatures:
        """
        Extract ML features for segmentation model.
        
        Args:
            user_id: User identifier
            user_events: All events for user
            computed_date: Date features computed
            
        Returns:
            UserSegmentFeatures
        """
        reference = datetime.strptime(computed_date, "%Y-%m-%d")
        
        # RFM metrics
        rfm = RFMCalculator.calculate_rfm(user_events, reference)
        
        # Engagement metrics
        sessions = [e for e in user_events if e.get("event_type") == "feature_usage"]
        avg_session_duration = sum(e.get("session_duration_sec", 0) for e in sessions) / len(sessions) if sessions else 0
        
        # Purchase behavior
        purchases = [e for e in user_events if e.get("event_type") == "purchase"]
        categories = set(p.get("product_category") for p in purchases if p.get("product_category"))
        avg_order_value = rfm.monetary / rfm.frequency if rfm.frequency > 0 else 0
        
        # Support metrics
        support = [e for e in user_events if e.get("event_type") == "support_ticket"]
        avg_resolution = sum(e.get("resolution_time_hours", 0) for e in support) / len(support) if support else 0
        
        # Days since last activity
        if user_events:
            last_activity = max(e.get("timestamp", reference) for e in user_events)
            days_since_last = (reference - last_activity).days
        else:
            days_since_last = 999
        
        # Get first purchase date
        if purchases:
            first_purchase = min(p['timestamp'] for p in purchases)
            customer_age = (reference - first_purchase).days
        else:
            customer_age = 0
        
        # Churn risk (high recency, low frequency/monetary = high risk)
        churn_risk = FeatureExtractor._calculate_churn_risk(rfm, customer_age)
        
        return UserSegmentFeatures(
            user_id=user_id,
            computed_date=computed_date,
            recency_days=rfm.recency_days,
            frequency=rfm.frequency,
            monetary=rfm.monetary,
            avg_session_duration_sec=avg_session_duration,
            product_categories_purchased=len(categories),
            avg_order_value=avg_order_value,
            support_tickets=len(support),
            avg_resolution_time_hours=avg_resolution,
            days_since_last_activity=days_since_last,
            churn_risk_score=churn_risk,
            customer_age_days=customer_age,
            is_active=(days_since_last <= 90),
            repeat_purchase_rate=(rfm.frequency - 1) / max(1, rfm.frequency),
            purchase_frequency_trend=0.0,  # Would calculate from trends
        )
    
    @staticmethod
    def _calculate_churn_risk(rfm: RFMMetrics, customer_age: int) -> float:
        """Calculate churn risk score (0-1, 1=high risk)"""
        # High recency = churn risk
        recency_risk = rfm.recency_days / 365.0  # Normalize
        
        # Low frequency = churn risk
        frequency_risk = 1.0 - min(1.0, rfm.frequency / 10.0)
        
        # Low monetary = churn risk
        monetary_risk = 1.0 - min(1.0, rfm.monetary / 1000.0)
        
        # Young customers have higher natural churn
        age_factor = min(1.0, customer_age / 365.0)
        
        # Weighted average
        churn_score = (
            recency_risk * 0.4 +
            frequency_risk * 0.3 +
            monetary_risk * 0.2 +
            (1.0 - age_factor) * 0.1
        )
        
        return min(1.0, max(0.0, churn_score))
