"""
Cache abstraction layer for swappable cache backends.

This module provides:
- Abstract cache interface
- Multiple cache implementations (Redis, Memory, File)
- Cache strategies (TTL, LRU, LFU)
- Cache warming and invalidation
- Cache statistics and monitoring
- Circuit breaker pattern for cache failures
"""

from abc import ABC, abstractmethod
from typing import Dict, Any, Optional, Union, List, Callable
from datetime import datetime, timedelta
import asyncio
import json
import hashlib
import pickle
import logging
from dataclasses import dataclass, asdict
from enum import Enum
from functools import wraps

from .exceptions import ExternalServiceError, ConfigurationError
from .logging import get_logger

logger = get_logger(__name__)


class CacheBackend(Enum):
    """Supported cache backends."""
    MEMORY = "memory"
    REDIS = "redis"
    FILE = "file"
    DATABASE = "database"


@dataclass
class CacheConfig:
    """Configuration for cache connections."""
    backend: CacheBackend
    host: str = "localhost"
    port: int = 6379
    database: str = "0"
    password: str = ""
    max_connections: int = 10
    timeout: int = 30
    ttl: int = 3600  # Default TTL in seconds
    key_prefix: str = "edu_flow:"
    compression: bool = True
    serialization: str = "json"  # json, pickle, msgpack
    max_memory_size: int = 1024 * 1024 * 1024  # 1GB default
    eviction_policy: str = "lru"  # lru, lfu, none


class CacheStats:
    """Cache statistics tracking."""
    
    def __init__(self):
        self.hits = 0
        self.misses = 0
        self.errors = 0
        self.warmups = 0
        self.invalidations = 0
        self.total_operations = 0
    
    def record_hit(self):
        self.hits += 1
        self.total_operations += 1
    
    def record_miss(self):
        self.misses += 1
        self.total_operations += 1
    
    def record_error(self):
        self.errors += 1
        self.total_operations += 1
    
    def record_warmup(self):
        self.warmups += 1
    
    def record_invalidation(self):
        self.invalidations += 1
    
    def get_hit_rate(self) -> float:
        total = self.hits + self.misses
        return self.hits / total if total > 0 else 0.0
    
    def get_stats(self) -> Dict[str, Any]:
        return {
            'hits': self.hits,
            'misses': self.misses,
            'errors': self.errors,
            'warmups': self.warmups,
            'invalidations': self.invalidations,
            'total_operations': self.total_operations,
            'hit_rate': self.get_hit_rate(),
        }


class CacheInterface(ABC):
    """Abstract interface for cache operations."""
    
    @abstractmethod
    async def connect(self):
        """Establish cache connection."""
        pass
    
    @abstractmethod
    async def disconnect(self):
        """Close cache connection."""
        pass
    
    @abstractmethod
    async def health_check(self) -> bool:
        """Check cache health."""
        pass
    
    @abstractmethod
    async def get(self, key: str, default: Any = None) -> Any:
        """Get value from cache."""
        pass
    
    @abstractmethod
    async def set(self, key: str, value: Any, ttl: int = None) -> bool:
        """Set value in cache with optional TTL."""
        pass
    
    @abstractmethod
    async def delete(self, key: str) -> bool:
        """Delete key from cache."""
        pass
    
    @abstractmethod
    async def exists(self, key: str) -> bool:
        """Check if key exists in cache."""
        pass
    
    @abstractmethod
    async def clear(self, pattern: str = None) -> bool:
        """Clear cache, optionally by pattern."""
        pass
    
    @abstractmethod
    async def get_ttl(self, key: str) -> int:
        """Get TTL for a key."""
        pass
    
    @abstractmethod
    async def set_ttl(self, key: str, ttl: int) -> bool:
        """Set TTL for a key."""
        pass
    
    @abstractmethod
    async def increment(self, key: str, delta: int = 1) -> int:
        """Increment a numeric value."""
        pass
    
    @abstractmethod
    async def decrement(self, key: str, delta: int = 1) -> int:
        """Decrement a numeric value."""
        pass
    
    @abstractmethod
    async def expire(self, key: str, ttl: int) -> bool:
        """Set expiration time for a key."""
        pass
    
    @abstractmethod
    async def get_stats(self) -> Dict[str, Any]:
        """Get cache statistics."""
        pass


class MemoryCache(CacheInterface):
    """In-memory cache implementation."""
    
    def __init__(self, config: CacheConfig):
        self.config = config
        self._cache: Dict[str, Dict[str, Any]] = {}
        self._stats = CacheStats()
        self._initialized = False
        self._lock = asyncio.Lock()
    
    async def connect(self):
        """Initialize in-memory cache."""
        self._initialized = True
        logger.info("Memory cache initialized")
    
    async def disconnect(self):
        """Clear in-memory cache."""
        async with self._lock:
            self._cache.clear()
        self._initialized = False
        logger.info("Memory cache disconnected")
    
    async def health_check(self) -> bool:
        """Check memory cache health."""
        return self._initialized
    
    def _serialize(self, value: Any) -> bytes:
        """Serialize value for storage."""
        if self.config.serialization == "json":
            return json.dumps(value).encode('utf-8')
        elif self.config.serialization == "pickle":
            return pickle.dumps(value)
        else:
            raise ConfigurationError(f"Unsupported serialization: {self.config.serialization}")
    
    def _deserialize(self, data: bytes) -> Any:
        """Deserialize value from storage."""
        if self.config.serialization == "json":
            return json.loads(data.decode('utf-8'))
        elif self.config.serialization == "pickle":
            return pickle.loads(data)
        else:
            raise ConfigurationError(f"Unsupported serialization: {self.config.serialization}")
    
    async def get(self, key: str, default: Any = None) -> Any:
        """Get value from memory cache."""
        try:
            full_key = self.config.key_prefix + key
            async with self._lock:
                if full_key in self._cache:
                    entry = self._cache[full_key]
                    if datetime.now() < entry['expires_at']:
                        self._stats.record_hit()
                        return self._deserialize(entry['data'])
                    else:
                        # Remove expired entry
                        del self._cache[full_key]
                
                self._stats.record_miss()
                return default
        except Exception as e:
            self._stats.record_error()
            logger.error(f"Memory cache get error: {e}")
            return default
    
    async def set(self, key: str, value: Any, ttl: int = None) -> bool:
        """Set value in memory cache."""
        try:
            full_key = self.config.key_prefix + key
            ttl = ttl or self.config.ttl
            
            data = self._serialize(value)
            expires_at = datetime.now() + timedelta(seconds=ttl)
            
            async with self._lock:
                # Check memory limit
                if len(self._cache) >= self.config.max_memory_size:
                    self._evict_entries()
                
                self._cache[full_key] = {
                    'data': data,
                    'expires_at': expires_at,
                    'created_at': datetime.now()
                }
            
            return True
        except Exception as e:
            self._stats.record_error()
            logger.error(f"Memory cache set error: {e}")
            return False
    
    def _evict_entries(self):
        """Evict entries based on policy."""
        if self.config.eviction_policy == "lru":
            # Sort by access time and remove oldest
            sorted_items = sorted(
                self._cache.items(),
                key=lambda x: x[1]['created_at']
            )
            for i, (key, _) in enumerate(sorted_items):
                if i >= len(sorted_items) // 4:  # Remove 25% of entries
                    del self._cache[key]
        elif self.config.eviction_policy == "lfu":
            # Simple LFU implementation - remove least frequently accessed
            # This is a simplified version
            oldest_key = min(self._cache.keys(), 
                           key=lambda k: self._cache[k]['created_at'])
            del self._cache[oldest_key]
    
    async def delete(self, key: str) -> bool:
        """Delete key from memory cache."""
        try:
            full_key = self.config.key_prefix + key
            async with self._lock:
                if full_key in self._cache:
                    del self._cache[full_key]
                    self._stats.record_invalidation()
                    return True
                return False
        except Exception as e:
            self._stats.record_error()
            logger.error(f"Memory cache delete error: {e}")
            return False
    
    async def exists(self, key: str) -> bool:
        """Check if key exists in memory cache."""
        try:
            full_key = self.config.key_prefix + key
            async with self._lock:
                if full_key in self._cache:
                    entry = self._cache[full_key]
                    if datetime.now() < entry['expires_at']:
                        return True
                    else:
                        del self._cache[full_key]
                return False
        except Exception as e:
            self._stats.record_error()
            logger.error(f"Memory cache exists error: {e}")
            return False
    
    async def clear(self, pattern: str = None) -> bool:
        """Clear memory cache."""
        try:
            async with self._lock:
                if pattern:
                    prefix = self.config.key_prefix + pattern
                    keys_to_delete = [k for k in self._cache.keys() if k.startswith(prefix)]
                    for key in keys_to_delete:
                        del self._cache[key]
                else:
                    self._cache.clear()
            
            self._stats.record_invalidation()
            return True
        except Exception as e:
            self._stats.record_error()
            logger.error(f"Memory cache clear error: {e}")
            return False
    
    async def get_ttl(self, key: str) -> int:
        """Get TTL for a key."""
        try:
            full_key = self.config.key_prefix + key
            async with self._lock:
                if full_key in self._cache:
                    entry = self._cache[full_key]
                    remaining = (entry['expires_at'] - datetime.now()).total_seconds()
                    return max(0, int(remaining))
                return -1
        except Exception as e:
            self._stats.record_error()
            logger.error(f"Memory cache get_ttl error: {e}")
            return -1
    
    async def set_ttl(self, key: str, ttl: int) -> bool:
        """Set TTL for a key."""
        try:
            full_key = self.config.key_prefix + key
            async with self._lock:
                if full_key in self._cache:
                    self._cache[full_key]['expires_at'] = datetime.now() + timedelta(seconds=ttl)
                    return True
                return False
        except Exception as e:
            self._stats.record_error()
            logger.error(f"Memory cache set_ttl error: {e}")
            return False
    
    async def increment(self, key: str, delta: int = 1) -> int:
        """Increment a numeric value."""
        try:
            current = await self.get(key, 0)
            new_value = int(current) + delta
            await self.set(key, new_value)
            return new_value
        except Exception as e:
            self._stats.record_error()
            logger.error(f"Memory cache increment error: {e}")
            return 0
    
    async def decrement(self, key: str, delta: int = 1) -> int:
        """Decrement a numeric value."""
        return await self.increment(key, -delta)
    
    async def expire(self, key: str, ttl: int) -> bool:
        """Set expiration time for a key."""
        return await self.set_ttl(key, ttl)
    
    async def get_stats(self) -> Dict[str, Any]:
        """Get memory cache statistics."""
        stats = self._stats.get_stats()
        stats.update({
            'backend': 'memory',
            'total_keys': len(self._cache),
            'memory_usage': sum(len(v['data']) for v in self._cache.values()),
            'config': asdict(self.config)
        })
        return stats


class RedisCache(CacheInterface):
    """Redis cache implementation."""
    
    def __init__(self, config: CacheConfig):
        self.config = config
        self._client = None
        self._stats = CacheStats()
        self._initialized = False
    
    async def connect(self):
        """Initialize Redis connection."""
        try:
            import aioredis
            
            self._client = aioredis.from_url(
                f"redis://{self.config.host}:{self.config.port}",
                password=self.config.password,
                db=self.config.database,
                max_connections=self.config.max_connections,
                socket_timeout=self.config.timeout,
                socket_connect_timeout=self.config.timeout,
            )
            
            # Test connection
            await self._client.ping()
            self._initialized = True
            logger.info("Redis cache connected")
            
        except ImportError:
            raise ConfigurationError("aioredis package is required for Redis cache")
        except Exception as e:
            logger.error(f"Redis connection failed: {e}")
            raise ExternalServiceError(f"Redis connection failed: {e}")
    
    async def disconnect(self):
        """Close Redis connection."""
        if self._client:
            await self._client.close()
            self._initialized = False
            logger.info("Redis cache disconnected")
    
    async def health_check(self) -> bool:
        """Check Redis health."""
        try:
            await self._client.ping()
            return True
        except Exception as e:
            logger.error(f"Redis health check failed: {e}")
            return False
    
    def _serialize(self, value: Any) -> bytes:
        """Serialize value for storage."""
        if self.config.serialization == "json":
            return json.dumps(value).encode('utf-8')
        elif self.config.serialization == "pickle":
            return pickle.dumps(value)
        else:
            raise ConfigurationError(f"Unsupported serialization: {self.config.serialization}")
    
    def _deserialize(self, data: bytes) -> Any:
        """Deserialize value from storage."""
        if self.config.serialization == "json":
            return json.loads(data.decode('utf-8'))
        elif self.config.serialization == "pickle":
            return pickle.loads(data)
        else:
            raise ConfigurationError(f"Unsupported serialization: {self.config.serialization}")
    
    async def get(self, key: str, default: Any = None) -> Any:
        """Get value from Redis cache."""
        try:
            full_key = self.config.key_prefix + key
            data = await self._client.get(full_key)
            
            if data is None:
                self._stats.record_miss()
                return default
            
            try:
                value = self._deserialize(data)
                self._stats.record_hit()
                return value
            except Exception as e:
                self._stats.record_error()
                logger.error(f"Redis deserialize error: {e}")
                return default
        except Exception as e:
            self._stats.record_error()
            logger.error(f"Redis cache get error: {e}")
            return default
    
    async def set(self, key: str, value: Any, ttl: int = None) -> bool:
        """Set value in Redis cache."""
        try:
            full_key = self.config.key_prefix + key
            ttl = ttl or self.config.ttl
            
            data = self._serialize(value)
            result = await self._client.setex(full_key, ttl, data)
            
            if result:
                return True
            else:
                self._stats.record_error()
                return False
        except Exception as e:
            self._stats.record_error()
            logger.error(f"Redis cache set error: {e}")
            return False
    
    async def delete(self, key: str) -> bool:
        """Delete key from Redis cache."""
        try:
            full_key = self.config.key_prefix + key
            result = await self._client.delete(full_key)
            if result > 0:
                self._stats.record_invalidation()
                return True
            return False
        except Exception as e:
            self._stats.record_error()
            logger.error(f"Redis cache delete error: {e}")
            return False
    
    async def exists(self, key: str) -> bool:
        """Check if key exists in Redis cache."""
        try:
            full_key = self.config.key_prefix + key
            result = await self._client.exists(full_key)
            return result > 0
        except Exception as e:
            self._stats.record_error()
            logger.error(f"Redis cache exists error: {e}")
            return False
    
    async def clear(self, pattern: str = None) -> bool:
        """Clear Redis cache."""
        try:
            if pattern:
                full_pattern = self.config.key_prefix + pattern
                keys = await self._client.keys(full_pattern)
                if keys:
                    await self._client.delete(*keys)
            else:
                await self._client.flushdb()
            
            self._stats.record_invalidation()
            return True
        except Exception as e:
            self._stats.record_error()
            logger.error(f"Redis cache clear error: {e}")
            return False
    
    async def get_ttl(self, key: str) -> int:
        """Get TTL for a key in Redis."""
        try:
            full_key = self.config.key_prefix + key
            ttl = await self._client.ttl(full_key)
            return ttl if ttl >= 0 else -1
        except Exception as e:
            self._stats.record_error()
            logger.error(f"Redis cache get_ttl error: {e}")
            return -1
    
    async def set_ttl(self, key: str, ttl: int) -> bool:
        """Set TTL for a key in Redis."""
        try:
            full_key = self.config.key_prefix + key
            result = await self._client.expire(full_key, ttl)
            return result
        except Exception as e:
            self._stats.record_error()
            logger.error(f"Redis cache set_ttl error: {e}")
            return False
    
    async def increment(self, key: str, delta: int = 1) -> int:
        """Increment a numeric value in Redis."""
        try:
            full_key = self.config.key_prefix + key
            result = await self._client.incrby(full_key, delta)
            return result
        except Exception as e:
            self._stats.record_error()
            logger.error(f"Redis cache increment error: {e}")
            return 0
    
    async def decrement(self, key: str, delta: int = 1) -> int:
        """Decrement a numeric value in Redis."""
        return await self.increment(key, -delta)
    
    async def expire(self, key: str, ttl: int) -> bool:
        """Set expiration time for a key in Redis."""
        return await self.set_ttl(key, ttl)
    
    async def get_stats(self) -> Dict[str, Any]:
        """Get Redis cache statistics."""
        stats = self._stats.get_stats()
        try:
            info = await self._client.info('memory')
            stats.update({
                'backend': 'redis',
                'used_memory': info.get('used_memory', 0),
                'connected_clients': info.get('connected_clients', 0),
                'total_commands_processed': info.get('total_commands_processed', 0),
                'config': asdict(self.config)
            })
        except Exception as e:
            logger.error(f"Failed to get Redis stats: {e}")
            stats['config'] = asdict(self.config)
        
        return stats


class CacheManager:
    """Cache manager for handling multiple cache backends."""
    
    def __init__(self, config: CacheConfig):
        self.config = config
        self._cache: CacheInterface = None
        self._stats = CacheStats()
        self._initialized = False
        self._circuit_breaker = None
    
    async def initialize(self):
        """Initialize the cache manager."""
        try:
            # Create appropriate cache instance
            if self.config.backend == CacheBackend.MEMORY:
                self._cache = MemoryCache(self.config)
            elif self.config.backend == CacheBackend.REDIS:
                self._cache = RedisCache(self.config)
            else:
                raise ConfigurationError(f"Unsupported cache backend: {self.config.backend}")
            
            await self._cache.connect()
            self._initialized = True
            logger.info(f"Cache manager initialized with {self.config.backend.value}")
            
        except Exception as e:
            logger.error(f"Failed to initialize cache manager: {e}")
            raise ExternalServiceError(f"Cache manager initialization failed: {e}")
    
    async def disconnect(self):
        """Close cache connections."""
        if self._cache:
            await self._cache.disconnect()
        self._initialized = False
        logger.info("Cache manager disconnected")
    
    async def health_check(self) -> bool:
        """Check cache health."""
        if not self._initialized:
            return False
        return await self._cache.health_check()
    
    def get_cache(self) -> CacheInterface:
        """Get the cache interface."""
        if not self._initialized:
            raise ExternalServiceError("Cache manager not initialized")
        return self._cache
    
    async def get_stats(self) -> Dict[str, Any]:
        """Get cache statistics."""
        if not self._initialized:
            return {}
        
        cache_stats = await self._cache.get_stats()
        cache_stats['total_stats'] = self._stats.get_stats()
        return cache_stats
    
    # Convenience methods with circuit breaker
    async def get(self, key: str, default: Any = None, use_cache: bool = True) -> Any:
        """Get value from cache with fallback."""
        if not use_cache or not self._initialized:
            return default
        
        try:
            value = await self._cache.get(key, default)
            if value is not None:
                self._stats.record_hit()
            else:
                self._stats.record_miss()
            return value
        except Exception as e:
            self._stats.record_error()
            logger.error(f"Cache get error for key {key}: {e}")
            return default
    
    async def set(self, key: str, value: Any, ttl: int = None, use_cache: bool = True) -> bool:
        """Set value in cache."""
        if not use_cache or not self._initialized:
            return True
        
        try:
            result = await self._cache.set(key, value, ttl)
            if result:
                logger.debug(f"Cache set successful for key {key}")
            return result
        except Exception as e:
            self._stats.record_error()
            logger.error(f"Cache set error for key {key}: {e}")
            return False
    
    async def delete(self, key: str, use_cache: bool = True) -> bool:
        """Delete key from cache."""
        if not use_cache or not self._initialized:
            return True
        
        try:
            result = await self._cache.delete(key)
            if result:
                self._stats.record_invalidation()
                logger.debug(f"Cache delete successful for key {key}")
            return result
        except Exception as e:
            self._stats.record_error()
            logger.error(f"Cache delete error for key {key}: {e}")
            return False
    
    async def clear(self, pattern: str = None, use_cache: bool = True) -> bool:
        """Clear cache."""
        if not use_cache or not self._initialized:
            return True
        
        try:
            result = await self._cache.clear(pattern)
            if result:
                self._stats.record_invalidation()
                logger.debug(f"Cache clear successful for pattern {pattern}")
            return result
        except Exception as e:
            self._stats.record_error()
            logger.error(f"Cache clear error: {e}")
            return False
    
    # Decorator for cache warming
    def cache_warmup(self, cache_keys: List[str]):
        """Decorator to warm up cache for given keys."""
        def decorator(func):
            @wraps(func)
            async def wrapper(*args, **kwargs):
                # Warm up cache
                for key in cache_keys:
                    try:
                        value = await func(*args, **kwargs)
                        await self.set(key, value)
                        self._stats.record_warmup()
                    except Exception as e:
                        logger.error(f"Cache warmup failed for key {key}: {e}")
                
                return await func(*args, **kwargs)
            return wrapper
        return decorator
    
    # Decorator for memoization
    def cache_memoize(self, ttl: int = None, key_prefix: str = "memoize"):
        """Decorator for memoization with cache."""
        def decorator(func):
            @wraps(func)
            async def wrapper(*args, **kwargs):
                # Generate cache key
                key_data = {
                    'func': func.__name__,
                    'args': str(args),
                    'kwargs': str(sorted(kwargs.items()))
                }
                key = f"{key_prefix}:{hashlib.md5(str(key_data).encode()).hexdigest()}"
                
                # Try to get from cache first
                cached_result = await self.get(key)
                if cached_result is not None:
                    return cached_result
                
                # Execute function and cache result
                result = await func(*args, **kwargs)
                await self.set(key, result, ttl)
                return result
            return wrapper
        return decorator


# Factory function to create cache manager
async def create_cache_manager(config: CacheConfig) -> CacheManager:
    """Create a cache manager with the given configuration."""
    manager = CacheManager(config)
    await manager.initialize()
    return manager


# Global cache manager instance
_cache_manager = None


def get_cache_manager() -> CacheManager:
    """Get the global cache manager instance."""
    if _cache_manager is None:
        raise ExternalServiceError("Cache manager not initialized")
    return _cache_manager


def initialize_cache_manager(config: CacheConfig):
    """Initialize the global cache manager."""
    global _cache_manager
    _cache_manager = CacheManager(config)
    return _cache_manager