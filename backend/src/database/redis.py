"""Redis integration for caching and session management."""

import json
import pickle
import hashlib
from typing import Any, Optional, Dict, List
from datetime import datetime, timedelta
from src.database.connection import database_manager
from src.config.settings import settings
from src.core.exceptions import ConfigurationError


class RedisCache:
    """Redis cache with automatic serialization and TTL management."""
    
    def __init__(self, prefix: str = "edu_flow"):
        self.prefix = prefix
        self.client = None
        self._initialized = False
    
    async def initialize(self) -> None:
        """Initialize Redis connection."""
        if self._initialized:
            return
        
        try:
            self.client = await database_manager.get_redis_client()
            if not self.client:
                raise ConfigurationError("Redis client not available")
            self._initialized = True
        except Exception as e:
            raise ConfigurationError(f"Failed to initialize Redis: {e}")
    
    async def _get_key(self, key: str) -> str:
        """Get full Redis key with prefix."""
        return f"{self.prefix}:{key}"
    
    async def _serialize(self, value: Any) -> bytes:
        """Serialize value for storage."""
        if isinstance(value, (str, int, float, bool, dict, list)):
            return json.dumps(value, default=str).encode('utf-8')
        else:
            return pickle.dumps(value)
    
    async def _deserialize(self, data: bytes) -> Any:
        """Deserialize value from storage."""
        try:
            # Try JSON first
            return json.loads(data.decode('utf-8'))
        except (json.JSONDecodeError, UnicodeDecodeError):
            # Fall back to pickle
            return pickle.loads(data)
    
    async def get(self, key: str, default: Any = None) -> Any:
        """Get value from cache."""
        try:
            if not self._initialized:
                await self.initialize()
            
            full_key = await self._get_key(key)
            data = await self.client.get(full_key)
            
            if data is None:
                return default
            
            return await self._deserialize(data)
            
        except Exception as e:
            # If Redis is down, return default without failing
            return default
    
    async def set(self, key: str, value: Any, ttl: int = None) -> bool:
        """Set value in cache with optional TTL."""
        try:
            if not self._initialized:
                await self.initialize()
            
            full_key = await self._get_key(key)
            serialized_data = await self._serialize(value)
            
            if ttl is None:
                ttl = settings.cache_ttl
            
            if ttl > 0:
                await self.client.setex(full_key, ttl, serialized_data)
            else:
                await self.client.set(full_key, serialized_data)
            
            return True
            
        except Exception as e:
            # If Redis is down, don't fail the operation
            return False
    
    async def delete(self, key: str) -> bool:
        """Delete value from cache."""
        try:
            if not self._initialized:
                await self.initialize()
            
            full_key = await self._get_key(key)
            result = await self.client.delete(full_key)
            
            return result > 0
            
        except Exception as e:
            # If Redis is down, return False
            return False
    
    async def exists(self, key: str) -> bool:
        """Check if key exists in cache."""
        try:
            if not self._initialized:
                await self.initialize()
            
            full_key = await self._get_key(key)
            return await self.client.exists(full_key) > 0
            
        except Exception as e:
            # If Redis is down, assume key doesn't exist
            return False
    
    async def expire(self, key: str, ttl: int) -> bool:
        """Set expiration time for a key."""
        try:
            if not self._initialized:
                await self.initialize()
            
            full_key = await self._get_key(key)
            return await self.client.expire(full_key, ttl)
            
        except Exception as e:
            # If Redis is down, return False
            return False
    
    async def ttl(self, key: str) -> int:
        """Get TTL for a key."""
        try:
            if not self._initialized:
                await self.initialize()
            
            full_key = await self._get_key(key)
            return await self.client.ttl(full_key)
            
        except Exception as e:
            # If Redis is down, return -1
            return -1
    
    async def increment(self, key: str, amount: int = 1) -> int:
        """Increment a counter value."""
        try:
            if not self._initialized:
                await self.initialize()
            
            full_key = await self._get_key(key)
            return await self.client.incrby(full_key, amount)
            
        except Exception as e:
            # If Redis is down, return 0
            return 0
    
    async def decrement(self, key: str, amount: int = 1) -> int:
        """Decrement a counter value."""
        try:
            if not self._initialized:
                await self.initialize()
            
            full_key = await self._get_key(key)
            return await self.client.decrby(full_key, amount)
            
        except Exception as e:
            # If Redis is down, return 0
            return 0
    
    async def set_hash(self, key: str, field: str, value: Any, ttl: int = None) -> bool:
        """Set a field in a hash."""
        try:
            if not self._initialized:
                await self.initialize()
            
            full_key = await self._get_key(key)
            serialized_value = await self._serialize(value)
            
            result = await self.client.hset(full_key, field, serialized_value)
            
            if ttl and ttl > 0:
                await self.client.expire(full_key, ttl)
            
            return result > 0
            
        except Exception as e:
            return False
    
    async def get_hash(self, key: str, field: str) -> Any:
        """Get a field from a hash."""
        try:
            if not self._initialized:
                await self.initialize()
            
            full_key = await self._get_key(key)
            data = await self.client.hget(full_key, field)
            
            if data is None:
                return None
            
            return await self._deserialize(data)
            
        except Exception as e:
            return None
    
    async def delete_hash_field(self, key: str, field: str) -> bool:
        """Delete a field from a hash."""
        try:
            if not self._initialized:
                await self.initialize()
            
            full_key = await self._get_key(key)
            result = await self.client.hdel(full_key, field)
            
            return result > 0
            
        except Exception as e:
            return False
    
    async def get_hash_all(self, key: str) -> Dict[str, Any]:
        """Get all fields from a hash."""
        try:
            if not self._initialized:
                await self.initialize()
            
            full_key = await self._get_key(key)
            data = await self.client.hgetall(full_key)
            
            if not data:
                return {}
            
            result = {}
            for field, value in data.items():
                result[field] = await self._deserialize(value)
            
            return result
            
        except Exception as e:
            return {}
    
    async def list_push(self, key: str, value: Any, ttl: int = None) -> bool:
        """Push value to a list."""
        try:
            if not self._initialized:
                await self.initialize()
            
            full_key = await self._get_key(key)
            serialized_value = await self._serialize(value)
            
            result = await self.client.lpush(full_key, serialized_value)
            
            if ttl and ttl > 0:
                await self.client.expire(full_key, ttl)
            
            return result > 0
            
        except Exception as e:
            return False
    
    async def list_pop(self, key: str) -> Any:
        """Pop value from a list."""
        try:
            if not self._initialized:
                await self.initialize()
            
            full_key = await self._get_key(key)
            data = await self.client.lpop(full_key)
            
            if data is None:
                return None
            
            return await self._deserialize(data)
            
        except Exception as e:
            return None
    
    async def list_get_all(self, key: str) -> List[Any]:
        """Get all values from a list."""
        try:
            if not self._initialized:
                await self.initialize()
            
            full_key = await self._get_key(key)
            data = await self.client.lrange(full_key, 0, -1)
            
            if not data:
                return []
            
            result = []
            for item in data:
                result.append(await self._deserialize(item))
            
            return result
            
        except Exception as e:
            return []
    
    async def get_memory_usage(self) -> Dict[str, int]:
        """Get memory usage statistics."""
        try:
            if not self._initialized:
                await self.initialize()
            
            info = await self.client.info('memory')
            return {
                'used_memory': info.get('used_memory', 0),
                'used_memory_human': info.get('used_memory_human', '0B'),
                'total_system_memory': info.get('total_system_memory', 0),
                'maxmemory': info.get('maxmemory', 0),
                'maxmemory_human': info.get('maxmemory_human', '0B')
            }
            
        except Exception as e:
            return {
                'used_memory': 0,
                'used_memory_human': '0B',
                'total_system_memory': 0,
                'maxmemory': 0,
                'maxmemory_human': '0B'
            }
    
    async def flush_pattern(self, pattern: str) -> int:
        """Delete all keys matching a pattern."""
        try:
            if not self._initialized:
                await self.initialize()
            
            full_pattern = f"{self.prefix}:{pattern}"
            keys = await self.client.keys(full_pattern)
            
            if not keys:
                return 0
            
            deleted = await self.client.delete(*keys)
            return deleted
            
        except Exception as e:
            return 0
    
    async def health_check(self) -> Dict[str, Any]:
        """Check Redis health."""
        try:
            if not self._initialized:
                await self.initialize()
            
            # Test connection
            await self.client.ping()
            
            # Get info
            info = await self.client.info()
            
            return {
                'status': 'healthy',
                'connected_clients': info.get('connected_clients', 0),
                'used_memory': info.get('used_memory', 0),
                'used_memory_human': info.get('used_memory_human', '0B'),
                'keyspace_hits': info.get('keyspace_hits', 0),
                'keyspace_misses': info.get('keyspace_misses', 0),
                'total_commands_processed': info.get('total_commands_processed', 0)
            }
            
        except Exception as e:
            return {
                'status': 'unhealthy',
                'error': str(e)
            }


# Global Redis cache instance
redis_cache = RedisCache()