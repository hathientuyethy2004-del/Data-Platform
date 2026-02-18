"""
Web User Analytics - Cache Layer

Caching strategy for frequently accessed analytics data.
Uses Redis for distributed caching with TTL management.
"""

import json
import logging
from typing import Optional, Any, Dict, List
from datetime import datetime, timedelta
from enum import Enum
import hashlib

try:
    import redis
    from redis import Redis
    REDIS_AVAILABLE = True
except ImportError:
    REDIS_AVAILABLE = False
    logger = logging.getLogger(__name__)
    logger.warning("Redis not available - caching disabled")


logger = logging.getLogger(__name__)


class CacheTTL(int, Enum):
    """Cache TTL in seconds"""
    SHORT = 5 * 60  # 5 minutes
    MEDIUM = 30 * 60  # 30 minutes
    LONG = 24 * 60 * 60  # 24 hours
    VERY_LONG = 7 * 24 * 60 * 60  # 7 days


class CacheKeyStrategy:
    """Generates cache keys for analytics queries"""
    
    PREFIX = "analytics:"
    
    @staticmethod
    def page_metrics_key(page_id: str, start_date: str, end_date: str, 
                        granularity: str) -> str:
        """Generate key for page metrics"""
        key_parts = [
            CacheKeyStrategy.PREFIX,
            "page_metrics",
            page_id,
            start_date,
            end_date,
            granularity
        ]
        return "|".join(key_parts)
    
    @staticmethod
    def funnel_key(funnel_id: str, start_date: str, end_date: str) -> str:
        """Generate key for funnel metrics"""
        return f"{CacheKeyStrategy.PREFIX}funnel|{funnel_id}|{start_date}|{end_date}"
    
    @staticmethod
    def session_key(session_id: str) -> str:
        """Generate key for session"""
        return f"{CacheKeyStrategy.PREFIX}session|{session_id}"
    
    @staticmethod
    def user_journey_key(user_id: str, start_date: Optional[str] = None,
                        end_date: Optional[str] = None) -> str:
        """Generate key for user journey"""
        key_parts = [CacheKeyStrategy.PREFIX, "journey", user_id]
        if start_date:
            key_parts.append(start_date)
        if end_date:
            key_parts.append(end_date)
        return "|".join(key_parts)
    
    @staticmethod
    def traffic_sources_key(start_date: str, end_date: str) -> str:
        """Generate key for traffic sources"""
        return f"{CacheKeyStrategy.PREFIX}traffic|{start_date}|{end_date}"
    
    @staticmethod
    def device_breakdown_key(start_date: str, end_date: str) -> str:
        """Generate key for device breakdown"""
        return f"{CacheKeyStrategy.PREFIX}devices|{start_date}|{end_date}"
    
    @staticmethod
    def query_hash_key(sql_query: str) -> str:
        """Generate cache key for custom query"""
        query_hash = hashlib.md5(sql_query.encode()).hexdigest()
        return f"{CacheKeyStrategy.PREFIX}query|{query_hash}"


class AnalyticsCache:
    """Redis-based cache for analytics queries"""
    
    def __init__(self, redis_host: str = "localhost",
                redis_port: int = 6379,
                redis_db: int = 0,
                default_ttl: int = CacheTTL.MEDIUM):
        """
        Initialize cache.
        
        Args:
            redis_host: Redis host
            redis_port: Redis port
            redis_db: Redis database number
            default_ttl: Default TTL in seconds
        """
        self.enabled = REDIS_AVAILABLE
        self.default_ttl = default_ttl
        self.redis_client: Optional[Redis] = None
        
        if self.enabled:
            try:
                self.redis_client = redis.Redis(
                    host=redis_host,
                    port=redis_port,
                    db=redis_db,
                    decode_responses=True,
                    socket_connect_timeout=5,
                    retry_on_timeout=True
                )
                # Test connection
                self.redis_client.ping()
                logger.info(f"Connected to Redis at {redis_host}:{redis_port}")
            except Exception as e:
                logger.error(f"Failed to connect to Redis: {e}")
                self.enabled = False
    
    def get(self, key: str) -> Optional[Any]:
        """
        Get value from cache.
        
        Args:
            key: Cache key
            
        Returns:
            Cached value or None
        """
        if not self.enabled or not self.redis_client:
            return None
        
        try:
            value = self.redis_client.get(key)
            if value:
                # Deserialize JSON
                return json.loads(value)
            return None
        
        except Exception as e:
            logger.error(f"Cache GET failed for {key}: {e}")
            return None
    
    def set(self, key: str, value: Any, ttl: int = None) -> bool:
        """
        Set value in cache.
        
        Args:
            key: Cache key
            value: Value to cache
            ttl: Time to live in seconds (uses default if None)
            
        Returns:
            True if successful
        """
        if not self.enabled or not self.redis_client:
            return False
        
        try:
            ttl = ttl or self.default_ttl
            # Serialize to JSON
            serialized = json.dumps(value, default=str)
            self.redis_client.setex(key, ttl, serialized)
            return True
        
        except Exception as e:
            logger.error(f"Cache SET failed for {key}: {e}")
            return False
    
    def delete(self, key: str) -> bool:
        """Delete cache key"""
        if not self.enabled or not self.redis_client:
            return False
        
        try:
            self.redis_client.delete(key)
            return True
        except Exception as e:
            logger.error(f"Cache DELETE failed for {key}: {e}")
            return False
    
    def clear_pattern(self, pattern: str) -> int:
        """
        Clear all keys matching pattern.
        
        Args:
            pattern: Key pattern (e.g., "analytics:page_metrics*")
            
        Returns:
            Number of keys deleted
        """
        if not self.enabled or not self.redis_client:
            return 0
        
        try:
            keys = self.redis_client.keys(pattern)
            if keys:
                return self.redis_client.delete(*keys)
            return 0
        
        except Exception as e:
            logger.error(f"Cache CLEAR failed for pattern {pattern}: {e}")
            return 0
    
    def get_stats(self) -> Dict[str, Any]:
        """Get cache statistics"""
        if not self.enabled or not self.redis_client:
            return {"enabled": False}
        
        try:
            info = self.redis_client.info()
            return {
                "enabled": True,
                "memory_used_mb": info.get("used_memory_mb", 0),
                "connected_clients": info.get("connected_clients", 0),
                "hits": info.get("keyspace_hits", 0),
                "misses": info.get("keyspace_misses", 0),
            }
        
        except Exception as e:
            logger.error(f"Failed to get cache stats: {e}")
            return {"enabled": True, "error": str(e)}
    
    def close(self):
        """Close Redis connection"""
        if self.redis_client:
            self.redis_client.close()


class CachedQueryExecutor:
    """Wraps query execution with caching"""
    
    def __init__(self, cache: AnalyticsCache):
        """Initialize with cache instance"""
        self.cache = cache
    
    def execute_cached(self,
                      query_fn,
                      cache_key: str,
                      ttl: int = CacheTTL.MEDIUM,
                      **kwargs) -> Any:
        """
        Execute query with caching.
        
        If result is cached, returns cached value.
        Otherwise executes query_fn and caches result.
        
        Args:
            query_fn: Function to execute
            cache_key: Cache key
            ttl: Time to live
            **kwargs: Arguments to pass to query_fn
            
        Returns:
            Query result
        """
        # Try cache first
        cached_value = self.cache.get(cache_key)
        if cached_value is not None:
            logger.debug(f"Cache HIT for {cache_key}")
            return cached_value
        
        # Execute query
        logger.debug(f"Cache MISS for {cache_key}")
        result = query_fn(**kwargs)
        
        # Cache result
        self.cache.set(cache_key, result, ttl)
        
        return result
    
    def invalidate_cache_pattern(self, pattern: str) -> int:
        """Invalidate cache for pattern (after data update)"""
        logger.info(f"Invalidating cache pattern: {pattern}")
        return self.cache.clear_pattern(pattern)


# Global cache instance
_cache_instance: Optional[AnalyticsCache] = None


def get_cache(redis_host: str = "localhost",
             redis_port: int = 6379,
             redis_db: int = 0) -> AnalyticsCache:
    """Get or create cache instance (singleton-ish)"""
    global _cache_instance
    
    if _cache_instance is None:
        _cache_instance = AnalyticsCache(redis_host, redis_port, redis_db)
    
    return _cache_instance


def get_cached_executor(cache: Optional[AnalyticsCache] = None) -> CachedQueryExecutor:
    """Get cached query executor"""
    if cache is None:
        cache = get_cache()
    
    return CachedQueryExecutor(cache)
