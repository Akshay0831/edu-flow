"""
Redis integration for caching and session management.

This module provides Redis caching functionality:
- Basic Redis operations with automatic serialization
- TTL management
- Session management
- Cache invalidation

Author: Edu-Flow Team
"""

import json
import pickle
import hashlib
from typing import Any, Optional, Dict, List
from datetime import datetime, timedelta
from config.settings import settings
from core.exceptions import ConfigurationError
import asyncio
import logging
from redis.asyncio import Redis

logger = logging.getLogger(__name__)

class RedisCache:
    """Redis cache with automatic serialization and TTL management."""
    
    def __init__(self, prefix: str = "edu_flow"):
        self.prefix = prefix
        self.client: Optional[Redis] = None
        self._initialized = False
        
    async def initialize(self) -> None:
        """Initialize Redis connection."""
        if self._initialized:
            return
        
        try:
            # Parse Redis URL - simplified version
            redis_url = settings.redis_url
            host = "localhost"
            port = 6379
            
            # Basic URL parsing if provided
            if redis_url and "://" in redis_url:
                # Extract host and port from URL
                url_without_protocol = redis_url.split("://")[1]
                if ":" in url_without_protocol:
                    host = url_without_protocol.split(":")[0]
                    port_str = url_without_protocol.split(":")[1]
                    if "/" in port_str:
                        port = int(port_str.split("/")[0])
                    else:
                        port = int(port_str)
                elif "/" in url_without_protocol:
                    host = url_without_protocol.split("/")[0]
            
            # Create Redis client with connection pooling
            self.client = Redis(
                host=host,
                port=port,
                db=0,
                password=None,
                decode_responses=False,  # We'll handle encoding ourselves
                retry_on_timeout=True,
                socket_connect_timeout=5,
                socket_timeout=5,
                max_connections=20
            )
            
            # Test connection
            await self.client.ping()
            self._initialized = True
            logger.info("Redis connected successfully")
            
        except Exception as e:
            logger.error(f"Failed to initialize Redis: {e}")
            raise ConfigurationError(f"Failed to initialize Redis: {e}")
    
    async def _get_key(self, key: str) -> str:
        """Get full Redis key with prefix."""
        return f"{self.prefix}:{key}"
    
    async def _serialize(self, value: Any) -> bytes:
        """Serialize value for storage."""
        try:
            if isinstance(value, (str, int, float, bool, dict, list)):
                return json.dumps(value, default=str).encode('utf-8')
            else:
                return pickle.dumps(value)
        except Exception as e:
            logger.error(f"Serialization failed for value type {type(value)}: {e}")
            raise ConfigurationError(f"Serialization failed: {e}")
    
    async def _deserialize(self, data: bytes) -> Any:
        """Deserialize value from storage."""
        try:
            # Try JSON first
            return json.loads(data.decode('utf-8'))
        except (json.JSONDecodeError, UnicodeDecodeError):
            try:
                # Fall back to pickle
                return pickle.loads(data)
            except Exception as e:
                logger.error(f"Deserialization failed: {e}")
                raise ConfigurationError(f"Deserialization failed: {e}")
    
    async def get(self, key: str) -> Optional[Any]:
        """Get value from Redis."""
        try:
            if not self._initialized:
                await self.initialize()
            
            full_key = await self._get_key(key)
            data = await self.client.get(full_key)
            
            if data is None:
                return None
            
            return await self._deserialize(data)
            
        except Exception as e:
            logger.error(f"Redis get failed for key {key}: {e}")
            raise ConfigurationError(f"Redis get failed: {e}")
    
    async def set(self, key: str, value: Any, ttl: int = None) -> bool:
        """Set value in Redis with optional TTL."""
        try:
            if not self._initialized:
                await self.initialize()
            
            full_key = await self._get_key(key)
            serialized_value = await self._serialize(value)
            
            if ttl:
                await self.client.setex(full_key, ttl, serialized_value)
            else:
                await self.client.set(full_key, serialized_value)
            
            return True
            
        except Exception as e:
            logger.error(f"Redis set failed for key {key}: {e}")
            raise ConfigurationError(f"Redis set failed: {e}")
    
    async def delete(self, key: str) -> bool:
        """Delete key from Redis."""
        try:
            if not self._initialized:
                await self.initialize()
            
            full_key = await self._get_key(key)
            result = await self.client.delete(full_key)
            return result > 0
            
        except Exception as e:
            logger.error(f"Redis delete failed for key {key}: {e}")
            raise ConfigurationError(f"Redis delete failed: {e}")
    
    async def exists(self, key: str) -> bool:
        """Check if key exists in Redis."""
        try:
            if not self._initialized:
                await self.initialize()
            
            full_key = await self._get_key(key)
            return await self.client.exists(full_key) > 0
            
        except Exception as e:
            logger.error(f"Redis exists check failed for key {key}: {e}")
            raise ConfigurationError(f"Redis exists check failed: {e}")
    
    async def expire(self, key: str, ttl: int) -> bool:
        """Set TTL for key."""
        try:
            if not self._initialized:
                await self.initialize()
            
            full_key = await self._get_key(key)
            return await self.client.expire(full_key, ttl)
            
        except Exception as e:
            logger.error(f"Redis expire failed for key {key}: {e}")
            raise ConfigurationError(f"Redis expire failed: {e}")
    
    async def keys(self, pattern: str = "*") -> List[str]:
        """Get keys matching pattern."""
        try:
            if not self._initialized:
                await self.initialize()
            
            full_pattern = f"{self.prefix}:{pattern}"
            keys = await self.client.keys(full_pattern)
            return [key.replace(f"{self.prefix}:", "") for key in keys]
            
        except Exception as e:
            logger.error(f"Redis keys failed for pattern {pattern}: {e}")
            raise ConfigurationError(f"Redis keys failed: {e}")
    
    async def clear(self) -> bool:
        """Clear all keys with this prefix."""
        try:
            if not self._initialized:
                await self.initialize()
            
            pattern = f"{self.prefix}:*"
            keys = await self.client.keys(pattern)
            if keys:
                await self.client.delete(*keys)
            
            return True
            
        except Exception as e:
            logger.error(f"Redis clear failed: {e}")
            raise ConfigurationError(f"Redis clear failed: {e}")
    
    async def close(self) -> None:
        """Close Redis connection."""
        try:
            if self.client:
                await self.client.close()
                self._initialized = False
                logger.info("Redis connection closed")
        except Exception as e:
            logger.error(f"Failed to close Redis: {e}")

# Global Redis cache instance
redis_cache = RedisCache()

# Initialize Redis on import
async def initialize_redis() -> bool:
    """Initialize Redis cache."""
    try:
        await redis_cache.initialize()
        return True
    except Exception as e:
        logger.error(f"Failed to initialize Redis: {e}")
        return False

async def close_redis() -> None:
    """Close Redis connection."""
    await redis_cache.close()