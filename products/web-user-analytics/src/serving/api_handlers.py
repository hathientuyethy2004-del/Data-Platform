"""
Web User Analytics - REST API Handlers

FastAPI endpoints for accessing analytics data from Gold layer tables.
Includes endpoints for pages, funnels, sessions, and custom queries.
"""

from fastapi import FastAPI, HTTPException, Query, Depends, Header
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any, Annotated
from datetime import datetime, timedelta
import logging
from enum import Enum
import hashlib

from pyspark.sql import SparkSession, DataFrame
from pyspark.sql.functions import col, to_date, sum as spark_sum, avg, count, percentile_approx

logger = logging.getLogger(__name__)


class TimeGranularity(str, Enum):
    """Time granularity for aggregations"""
    HOURLY = "hourly"
    DAILY = "daily"
    WEEKLY = "weekly"
    MONTHLY = "monthly"


class PageMetricsResponse(BaseModel):
    """Page metrics response"""
    page_id: str
    page_url: str
    page_views: int
    unique_visitors: int
    bounce_rate: float = Field(..., ge=0, le=1)
    avg_session_duration_sec: float
    avg_page_load_time_ms: Optional[float] = None
    p99_page_load_time_ms: Optional[float] = None
    conversion_rate: Optional[float] = None


class FunnelConversionResponse(BaseModel):
    """Funnel conversion response"""
    funnel_id: str
    step_number: int
    step_name: str
    entered_count: int
    completed_count: int
    conversion_rate: float = Field(..., ge=0, le=1)
    drop_off_count: int
    drop_off_rate: float = Field(..., ge=0, le=1)


class SessionDetailResponse(BaseModel):
    """Session detail response"""
    session_id: str
    user_id: str
    duration_seconds: int
    pages_visited: int
    events_count: int
    device_type: str
    traffic_source: str
    country: str
    is_bounced: bool


class AnalyticsAPIService:
    """Provides analytics data API service"""
    
    def __init__(self, spark: SparkSession, gold_path: str):
        """
        Initialize API service.
        
        Args:
            spark: SparkSession
            gold_path: Path to Gold layer tables
        """
        self.spark = spark
        self.gold_path = gold_path
        self.rate_limit_cache = {}
    
    def validate_date_range(self, start_date: str, end_date: str, 
                           max_days: int = 90) -> None:
        """
        Validate date range parameters.
        
        Args:
            start_date: Start date (YYYY-MM-DD)
            end_date: End date (YYYY-MM-DD)
            max_days: Maximum days allowed
            
        Raises:
            ValueError: If dates invalid
        """
        try:
            start = datetime.strptime(start_date, "%Y-%m-%d").date()
            end = datetime.strptime(end_date, "%Y-%m-%d").date()
        except ValueError:
            raise ValueError("Invalid date format. Use YYYY-MM-DD")
        
        if start > end:
            raise ValueError("start_date must be <= end_date")
        
        days_diff = (end - start).days
        if days_diff > max_days:
            raise ValueError(f"Date range cannot exceed {max_days} days")
    
    def get_page_metrics(self,
                        page_id: str,
                        start_date: str,
                        end_date: str,
                        granularity: TimeGranularity = TimeGranularity.DAILY) -> List[Dict[str, Any]]:
        """
        Get metrics for a specific page.
        
        Args:
            page_id: Page identifier
            start_date: Start date (YYYY-MM-DD)
            end_date: End date (YYYY-MM-DD)
            granularity: Time granularity
            
        Returns:
            List of metrics records
        """
        self.validate_date_range(start_date, end_date)
        
        try:
            # Read page metrics
            df = self.spark.read.format("delta").load(
                f"{self.gold_path}/page_metrics"
            )
            
            # Filter
            df = df.filter(
                (col("page_id") == page_id) &
                (col("event_date") >= start_date) &
                (col("event_date") <= end_date)
            )
            
            # Aggregate by granularity if needed
            if granularity == TimeGranularity.DAILY:
                df = df.groupBy("page_id", "event_date").agg(
                    spark_sum("page_views").alias("page_views"),
                    spark_sum("unique_visitors").alias("unique_visitors"),
                    avg("bounce_rate").alias("bounce_rate"),
                    avg("avg_page_load_time_ms").alias("avg_page_load_time_ms"),
                )
            
            # Convert to list of dicts
            return df.toPandas().to_dict("records")
        
        except Exception as e:
            logger.error(f"Failed to get page metrics: {e}")
            raise HTTPException(status_code=500, detail=str(e))
    
    def get_funnel_conversion(self,
                             funnel_id: str,
                             start_date: str,
                             end_date: str) -> List[FunnelConversionResponse]:
        """
        Get funnel conversion metrics.
        
        Args:
            funnel_id: Funnel identifier
            start_date: Start date
            end_date: End date
            
        Returns:
            List of funnel step metrics
        """
        self.validate_date_range(start_date, end_date)
        
        try:
            df = self.spark.read.format("delta").load(
                f"{self.gold_path}/funnel_metrics"
            )
            
            df = df.filter(
                (col("funnel_id") == funnel_id) &
                (col("event_date") >= start_date) &
                (col("event_date") <= end_date)
            )
            
            # Group by step
            df = df.groupBy("funnel_id", "step_number", "step_name").agg(
                spark_sum("entered_count").alias("total_entered"),
                spark_sum("completed_count").alias("total_completed"),
                spark_sum("drop_off_count").alias("total_drop_off"),
            )
            
            # Calculate rates
            df = df.withColumn(
                "conversion_rate",
                df["total_completed"] / (df["total_entered"] + 1)
            ).withColumn(
                "drop_off_rate",
                df["total_drop_off"] / (df["total_entered"] + 1)
            )
            
            return df.toPandas().to_dict("records")
        
        except Exception as e:
            logger.error(f"Failed to get funnel metrics: {e}")
            raise HTTPException(status_code=500, detail=str(e))
    
    def get_session_details(self, session_id: str) -> Dict[str, Any]:
        """
        Get details for specific session.
        
        Args:
            session_id: Session ID
            
        Returns:
            Session detail record
        """
        try:
            df = self.spark.read.format("delta").load(
                f"{self.gold_path}/session_metrics"
            )
            
            df = df.filter(col("session_id") == session_id)
            
            records = df.toPandas().to_dict("records")
            if not records:
                raise HTTPException(status_code=404, detail="Session not found")
            
            return records[0]
        
        except Exception as e:
            logger.error(f"Failed to get session details: {e}")
            raise HTTPException(status_code=500, detail=str(e))
    
    def get_user_journey(self, user_id: str,
                        start_date: Optional[str] = None,
                        end_date: Optional[str] = None) -> Dict[str, Any]:
        """
        Get user journey metrics.
        
        Args:
            user_id: User ID
            start_date: Optional start date
            end_date: Optional end date
            
        Returns:
            User journey metrics
        """
        try:
            df = self.spark.read.format("delta").load(
                f"{self.gold_path}/user_journey"
            )
            
            df = df.filter(col("user_id") == user_id)
            
            if start_date:
                df = df.filter(col("event_date") >= start_date)
            if end_date:
                df = df.filter(col("event_date") <= end_date)
            
            records = df.toPandas().to_dict("records")
            if not records:
                raise HTTPException(status_code=404, detail="User not found")
            
            return records[0]
        
        except Exception as e:
            logger.error(f"Failed to get user journey: {e}")
            raise HTTPException(status_code=500, detail=str(e))
    
    def execute_custom_query(self, sql_query: str, 
                            api_key: str,
                            max_results: int = 10000) -> List[Dict[str, Any]]:
        """
        Execute custom SQL query on Gold tables.
        
        Args:
            sql_query: SQL query (must select from gold tables only)
            api_key: API key for authorization
            max_results: Maximum results to return
            
        Returns:
            Query results
            
        Raises:
            HTTPException: If query invalid or unauthorized
        """
        # Validate API key
        if not self._validate_api_key(api_key):
            raise HTTPException(status_code=401, detail="Invalid API key")
        
        # Validate query (prevent access to non-Gold tables)
        if not self._is_safe_query(sql_query):
            raise HTTPException(status_code=400, 
                              detail="Query must only access Gold tables")
        
        try:
            df = self.spark.sql(sql_query)
            df = df.limit(max_results)
            
            return df.toPandas().to_dict("records")
        
        except Exception as e:
            logger.error(f"Custom query failed: {e}")
            raise HTTPException(status_code=400, detail=str(e))
    
    def get_traffic_sources(self,
                           start_date: str,
                           end_date: str) -> List[Dict[str, Any]]:
        """
        Get traffic breakdown by source.
        
        Args:
            start_date: Start date
            end_date: End date
            
        Returns:
            Traffic source breakdown
        """
        self.validate_date_range(start_date, end_date)
        
        try:
            df = self.spark.read.format("delta").load(
                f"{self.gold_path}/session_metrics"
            )
            
            df = df.filter(
                (col("event_date") >= start_date) &
                (col("event_date") <= end_date)
            )
            
            # Group by traffic source
            traffic = df.groupBy("traffic_source").agg(
                count("session_id").alias("sessions"),
                spark_sum("pages_visited").alias("pages"),
                avg("duration_seconds").alias("avg_duration_sec"),
            )
            
            return traffic.toPandas().to_dict("records")
        
        except Exception as e:
            logger.error(f"Failed to get traffic sources: {e}")
            raise HTTPException(status_code=500, detail=str(e))
    
    def get_device_breakdown(self,
                            start_date: str,
                            end_date: str) -> List[Dict[str, Any]]:
        """
        Get device type breakdown.
        
        Args:
            start_date: Start date
            end_date: End date
            
        Returns:
            Device breakdown metrics
        """
        self.validate_date_range(start_date, end_date)
        
        try:
            df = self.spark.read.format("delta").load(
                f"{self.gold_path}/session_metrics"
            )
            
            df = df.filter(
                (col("event_date") >= start_date) &
                (col("event_date") <= end_date)
            )
            
            # Group by device
            devices = df.groupBy("device_type").agg(
                count("session_id").alias("sessions"),
                spark_sum("pages_visited").alias("pages"),
                avg("duration_seconds").alias("avg_duration_sec"),
            )
            
            return devices.toPandas().to_dict("records")
        
        except Exception as e:
            logger.error(f"Failed to get device breakdown: {e}")
            raise HTTPException(status_code=500, detail=str(e))
    
    def _validate_api_key(self, api_key: str) -> bool:
        """Validate API key for custom queries"""
        # In production, validate against secure store
        # For now, simple validation
        return len(api_key) > 0
    
    def _is_safe_query(self, query: str) -> bool:
        """Check if query only accesses Gold tables"""
        query_upper = query.upper()
        
        # Block access to non-Gold data
        blocked = ["BRONZE", "SILVER", "RAW", "STAGING"]
        for term in blocked:
            if term in query_upper:
                return False
        
        # Only select queries
        if not query_upper.startswith("SELECT"):
            return False
        
        return True


# Initialize FastAPI app
app = FastAPI(
    title="Web User Analytics API",
    description="Analytics API for web user data",
    version="1.0.0"
)

# Service instance (would be initialized with real SparkSession in production)
api_service: Optional[AnalyticsAPIService] = None


@app.on_event("startup")
async def startup_event():
    """Initialize service on startup"""
    global api_service
    spark = SparkSession.builder.appName("analytics-api").getOrCreate()
    api_service = AnalyticsAPIService(spark, "/data/gold")
    logger.info("Analytics API service initialized")


@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {"status": "healthy", "timestamp": datetime.utcnow().isoformat()}


@app.get("/pages/{page_id}/metrics", response_model=List[Dict[str, Any]])
async def get_page_metrics(
    page_id: str = Query(..., description="Page identifier"),
    start_date: str = Query(..., description="Start date (YYYY-MM-DD)"),
    end_date: str = Query(..., description="End date (YYYY-MM-DD)"),
    granularity: TimeGranularity = Query(TimeGranularity.DAILY),
):
    """Get metrics for specific page"""
    if not api_service:
        raise HTTPException(status_code=503, detail="Service not initialized")
    
    return api_service.get_page_metrics(page_id, start_date, end_date, granularity)


@app.get("/funnels/{funnel_id}/conversion", response_model=List[Dict[str, Any]])
async def get_funnel_conversion(
    funnel_id: str = Query(..., description="Funnel identifier"),
    start_date: str = Query(..., description="Start date (YYYY-MM-DD)"),
    end_date: str = Query(..., description="End date (YYYY-MM-DD)"),
):
    """Get funnel conversion metrics"""
    if not api_service:
        raise HTTPException(status_code=503, detail="Service not initialized")
    
    return api_service.get_funnel_conversion(funnel_id, start_date, end_date)


@app.get("/sessions/{session_id}")
async def get_session(session_id: str):
    """Get session details"""
    if not api_service:
        raise HTTPException(status_code=503, detail="Service not initialized")
    
    return api_service.get_session_details(session_id)


@app.get("/users/{user_id}/journey")
async def get_user_journey(
    user_id: str,
    start_date: Optional[str] = Query(None),
    end_date: Optional[str] = Query(None),
):
    """Get user journey metrics"""
    if not api_service:
        raise HTTPException(status_code=503, detail="Service not initialized")
    
    return api_service.get_user_journey(user_id, start_date, end_date)


@app.get("/traffic-sources")
async def get_traffic_sources(
    start_date: str = Query(..., description="Start date (YYYY-MM-DD)"),
    end_date: str = Query(..., description="End date (YYYY-MM-DD)"),
):
    """Get traffic source breakdown"""
    if not api_service:
        raise HTTPException(status_code=503, detail="Service not initialized")
    
    return api_service.get_traffic_sources(start_date, end_date)


@app.get("/devices")
async def get_device_breakdown(
    start_date: str = Query(..., description="Start date (YYYY-MM-DD)"),
    end_date: str = Query(..., description="End date (YYYY-MM-DD)"),
):
    """Get device type breakdown"""
    if not api_service:
        raise HTTPException(status_code=503, detail="Service not initialized")
    
    return api_service.get_device_breakdown(start_date, end_date)


@app.post("/query")
async def custom_query(
    sql_query: str = Query(..., description="SQL query"),
    api_key: Annotated[str, Header()] = None,
):
    """Execute custom SQL query on Gold tables"""
    if not api_service:
        raise HTTPException(status_code=503, detail="Service not initialized")
    
    if not api_key:
        raise HTTPException(status_code=401, detail="API key required")
    
    return api_service.execute_custom_query(sql_query, api_key)


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8002)
