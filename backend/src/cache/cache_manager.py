"""
Cache Manager for Edu-Flow Backend

This module provides comprehensive caching functionality including:
- Redis caching with multiple strategies
- Cache invalidation policies
- Cache warming strategies
- Cache performance monitoring
- Distributed cache support

Author: Edu-Flow Team
"""

import asyncio
import json
import logging
import time
from typing import Dict, Any, Optional, List, Union, Callable
from datetime import datetime, timedelta
from functools import wraps
from enum import Enum
import hashlib
import pickle
from contextlib import asynccontextmanager
from dataclasses import dataclass, asdict

try:
    import redis.asyncio as redis
    REDIS_AVAILABLE = True
except ImportError:
    redis = None
    REDIS_AVAILABLE = False

from config.settings import settings
from core.exceptions import CacheError


class CacheStrategy(Enum):
    """Cache strategies"""
    TTL = "ttl"  # Time to live
    LRU = "lru"  # Least recently used
    LFU = "lfu"  # Least frequently used
    WRITE_THROUGH = "write_through"
    WRITE_BEHIND = "write_behind"
    READ_THROUGH = "read_through"


class CacheKey(Enum):
    """Cache keys for different data types"""
    USER_SESSION = "user_session"
    USER_PROFILE = "user_profile"
    STUDENT_DATA = "student_data"
    COURSE_DATA = "course_data"
    MARKS_DATA = "marks_data"
    DEPARTMENT_DATA = "department_data"
    CLASS_SCHEDULE = "class_schedule"
    ANALYTICS_DATA = "analytics_data"
    CONFIG_DATA = "config_data"
    TEMP_DATA = "temp_data"


@dataclass
class CacheMetrics:
    """Cache performance metrics"""
    hits: int = 0
    misses: int = 0
    evictions: int = 0
    write_operations: int = 0
    read_operations: int = 0
    error_operations: int = 0
    avg_response_time: float = 0.0
    total_response_time: float = 0.0
    operation_count: int = 0


class CacheManager:
    """Advanced cache manager with multiple strategies and monitoring"""
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.redis_client = None
        self.local_cache = {}  # Local in-memory cache as fallback
        self.cache_metrics = {}
        self.cache_ttl = settings.cache_ttl or 3600
        self.max_cache_size = settings.cache_max_size or 1000
        self.cache_strategy = CacheStrategy.TTL
        
        # Initialize Redis if available
        if REDIS_AVAILABLE and settings.cache_enabled:
            self._initialize_redis()
    
    def _initialize_redis(self):
        """Initialize Redis connection"""
        try:
            self.redis_client = redis.from_url(
                settings.redis_url,
                decode_responses=True,
                health_check_interval=30,
                retry_on_timeout=True,
                socket_keepalive=True,
                socket_keepalive_options={},
                socket_timeout=5,
                socket_connect_timeout=5,
                retry_on_error=[redis.exceptions.ConnectionError],
                connection_pool_kwargs={
                    'max_connections': 50,
                    'health_check_interval': 30
                }
            )
            # Test connection
            asyncio.create_task(self.redis_client.ping())
            self.logger.info("Redis cache initialized successfully")
        except Exception as e:
            self.logger.warning(f"Failed to initialize Redis cache: {e}")
            self.redis_client = None
    
    def _generate_cache_key(self, key_enum: CacheKey, *args) -> str:
        """Generate cache key from enum and arguments"""
        key_base = key_enum.value
        if args:
            key_hash = hashlib.md5(str(args).encode()).hexdigest()[:8]
            return f"{key_base}:{key_hash}"
        return key_base
    
    def _get_metrics(self, cache_key: str) -> CacheMetrics:
        """Get cache metrics for a key"""
        if cache_key not in self.cache_metrics:
            self.cache_metrics[cache_key] = CacheMetrics()
        return self.cache_metrics[cache_key]
    
    def _update_metrics(self, metrics: CacheMetrics, response_time: float):
        """Update cache performance metrics"""
        metrics.operation_count += 1
        metrics.total_response_time += response_time
        metrics.avg_response_time = metrics.total_response_time / metrics.operation_count
    
    async def get(self, key_enum: CacheKey, *args, default=None) -> Any:
        """Get value from cache"""
        cache_key = self._generate_cache_key(key_enum, *args)
        start_time = time.time()
        
        try:
            # Try Redis first
            if self.redis_client:
                value = await self.redis_client.get(cache_key)
                if value is not None:
                    # Deserialize complex objects
                    if value.startswith('{') or value.startswith('['):
                        value = json.loads(value)
                    metrics = self._get_metrics(cache_key)
                    metrics.hits += 1
                    metrics.read_operations += 1
                    response_time = time.time() - start_time
                    self._update_metrics(metrics, response_time)
                    self.logger.debug(f"Cache hit for {cache_key}")
                    return value
            
            # Fallback to local cache
            if cache_key in self.local_cache:
                value, expiry = self.local_cache[cache_key]
                if expiry is None or time.time() < expiry:
                    metrics = self._get_metrics(cache_key)
                    metrics.hits += 1
                    metrics.read_operations += 1
                    response_time = time.time() - start_time
                    self._update_metrics(metrics, response_time)
                    self.logger.debug(f"Local cache hit for {cache_key}")
                    return value
            
            # Cache miss
            metrics = self._get_metrics(cache_key)
            metrics.misses += 1
            metrics.read_operations += 1
            response_time = time.time() - start_time
            self._update_metrics(metrics, response_time)
            self.logger.debug(f"Cache miss for {cache_key}")
            return default
            
        except Exception as e:
            metrics = self._get_metrics(cache_key)
            metrics.error_operations += 1
            response_time = time.time() - start_time
            self._update_metrics(metrics, response_time)
            self.logger.error(f"Cache error for {cache_key}: {e}")
            return default
    
    async def set(self, key_enum: CacheKey, value: Any, *args, ttl: int = None, strategy: CacheStrategy = None):
        """Set value in cache"""
        cache_key = self._generate_cache_key(key_enum, *args)
        start_time = time.time()
        
        try:
            # Serialize complex objects
            if isinstance(value, (dict, list)):
                value = json.dumps(value, default=str)
            
            effective_ttl = ttl or self.cache_ttl
            effective_strategy = strategy or self.cache_strategy
            
            # Use Redis if available
            if self.redis_client:
                if effective_ttl > 0:
                    await self.redis_client.setex(cache_key, effective_ttl, value)
                else:
                    await self.redis_client.set(cache_key, value)
                
                metrics = self._get_metrics(cache_key)
                metrics.write_operations += 1
                metrics.hits += 1  # Update cache statistics
                response_time = time.time() - start_time
                self._update_metrics(metrics, response_time)
                self.logger.debug(f"Cache set for {cache_key}")
                
                # Handle cache size for LRU strategy
                if effective_strategy == CacheStrategy.LRU:
                    await self._handle_lru_eviction(cache_key)
                return
            
            # Fallback to local cache
            expiry_time = None if effective_ttl <= 0 else time.time() + effective_ttl
            self.local_cache[cache_key] = (value, expiry_time)
            
            metrics = self._get_metrics(cache_key)
            metrics.write_operations += 1
            metrics.hits += 1
            response_time = time.time() - start_time
            self._update_metrics(metrics, response_time)
            self.logger.debug(f"Local cache set for {cache_key}")
            
            # Handle local cache size
            if len(self.local_cache) > self.max_cache_size:
                await self._evict_local_cache()
                
        except Exception as e:
            metrics = self._get_metrics(cache_key)
            metrics.error_operations += 1
            response_time = time.time() - start_time
            self._update_metrics(metrics, response_time)
            self.logger.error(f"Cache set error for {cache_key}: {e}")
    
    async def delete(self, key_enum: CacheKey, *args):
        """Delete value from cache"""
        cache_key = self._generate_cache_key(key_enum, *args)
        
        try:
            # Delete from Redis if available
            if self.redis_client:
                await self.redis_client.delete(cache_key)
            
            # Delete from local cache
            if cache_key in self.local_cache:
                del self.local_cache[cache_key]
            
            self.logger.debug(f"Cache deleted for {cache_key}")
            
        except Exception as e:
            self.logger.error(f"Cache delete error for {cache_key}: {e}")
    
    async def exists(self, key_enum: CacheKey, *args) -> bool:
        """Check if key exists in cache"""
        cache_key = self._generate_cache_key(key_enum, *args)
        
        try:
            # Check Redis first
            if self.redis_client:
                exists = await self.redis_client.exists(cache_key)
                return exists > 0
            
            # Check local cache
            if cache_key in self.local_cache:
                _, expiry = self.local_cache[cache_key]
                if expiry is None or time.time() < expiry:
                    return True
            
            return False
            
        except Exception as e:
            self.logger.error(f"Cache exists error for {cache_key}: {e}")
            return False
    
    async def clear_pattern(self, pattern: str):
        """Clear all keys matching pattern"""
        try:
            if self.redis_client:
                # Redis pattern matching
                keys = await self.redis_client.keys(pattern)
                if keys:
                    await self.redis_client.delete(*keys)
            
            # Clear local cache matching pattern
            keys_to_delete = [k for k in self.local_cache.keys() if pattern in k]
            for key in keys_to_delete:
                del self.local_cache[key]
            
            self.logger.debug(f"Cleared {len(keys_to_delete)} keys matching pattern: {pattern}")
            
        except Exception as e:
            self.logger.error(f"Cache clear pattern error for {pattern}: {e}")
    
    async def _evict_local_cache(self):
        """Evict from local cache using LRU strategy"""
        if len(self.local_cache) <= self.max_cache_size:
            return
        
        # Find oldest entries
        current_time = time.time()
        cache_with_expiry = []
        
        for key, (value, expiry) in self.local_cache.items():
            if expiry is None:
                expiry = current_time
            cache_with_expiry.append((key, value, expiry))
        
        # Sort by expiry time (oldest first)
        cache_with_expiry.sort(key=lambda x: x[2])
        
        # Remove oldest entries
        entries_to_remove = len(self.local_cache) - self.max_cache_size
        for i in range(entries_to_remove):
            if i < len(cache_with_expiry):
                key_to_remove = cache_with_expiry[i][0]
                del self.local_cache[key_to_remove]
                metrics = self._get_metrics(key_to_remove)
                metrics.evictions += 1
        
        self.logger.info(f"Evicted {entries_to_remove} entries from local cache")
    
    async def _handle_lru_eviction(self, key: str):
        """Handle LRU eviction in Redis"""
        # This would require Redis LRU management, which is typically handled by Redis itself
        pass
    
    def get_metrics(self) -> Dict[str, Any]:
        """Get cache performance metrics"""
        metrics = {}
        for key, metric in self.cache_metrics.items():
            metrics[key] = asdict(metric)
        
        # Calculate overall statistics
        total_operations = sum(m.operation_count for m in self.cache_metrics.values())
        total_hits = sum(m.hits for m in self.cache_metrics.values())
        total_misses = sum(m.misses for m in self.cache_metrics.values())
        
        metrics['overall'] = {
            'hit_rate': total_hits / total_operations if total_operations > 0 else 0,
            'total_operations': total_operations,
            'total_hits': total_hits,
            'total_misses': total_misses,
            'total_writes': sum(m.write_operations for m in self.cache_metrics.values()),
            'total_errors': sum(m.error_operations for m in self.cache_metrics.values()),
        }
        
        return metrics
    
    def clear_all(self):
        """Clear all cache"""
        try:
            if self.redis_client:
                asyncio.create_task(self.redis_client.flushdb())
            
            self.local_cache.clear()
            self.cache_metrics.clear()
            
            self.logger.info("All cache cleared")
            
        except Exception as e:
            self.logger.error(f"Clear all cache error: {e}")


def cache_result(key_enum: CacheKey, ttl: int = None, strategy: CacheStrategy = None):
    """Decorator to cache function results"""
    def decorator(func: Callable):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            cache_manager = CacheManager()
            cache_key = key_enum
            
            # Generate cache key based on function arguments
            arg_key = tuple(args) + tuple(kwargs.items())
            
            # Try to get from cache
            cached_result = await cache_manager.get(cache_key, *arg_key)
            if cached_result is not None:
                return cached_result
            
            # Execute function and cache result
            result = await func(*args, **kwargs)
            await cache_manager.set(cache_key, result, *arg_key, ttl=ttl, strategy=strategy)
            return result
        
        return wrapper
    return decorator


# Global cache manager instance
cache_manager = CacheManager()


async def warm_up_cache():
    """Warm up cache with frequently accessed data"""
    logger = logging.getLogger(__name__)
    
    try:
        # Warm up user sessions
        await cache_manager.set(CacheKey.USER_SESSION, {}, ttl=3600)
        
        # Warm up config data
        await cache_manager.set(CacheKey.CONFIG_DATA, {}, ttl=86400)
        
        logger.info("Cache warm-up completed")
        
    except Exception as e:
        logger.error(f"Cache warm-up failed: {e}")


@asynccontextmanager
async def get_cache():
    """Context manager for cache operations"""
    cache_manager = CacheManager()
    try:
        yield cache_manager
    finally:
        pass


# Cache statistics endpoint (for monitoring)
async def get_cache_stats():
    """Get cache statistics"""
    return cache_manager.get_metrics()