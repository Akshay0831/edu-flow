"""
Database Performance Optimization Configuration

This module provides database performance optimization utilities including:
- Query optimization helpers
- Index management
- Connection pool optimization
- Caching strategies
- Performance monitoring

Author: Edu-Flow Team
"""

import asyncio
import logging
from typing import Dict, List, Any, Optional
from datetime import datetime, timedelta
import time
from contextlib import asynccontextmanager
from motor.motor_asyncio import AsyncIOMotorCollection
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import text, create_engine
from sqlalchemy.pool import QueuePool
import redis.asyncio as redis
from src.config.settings import settings
from src.core.dependencies import get_db


class DatabasePerformanceOptimizer:
    """Database performance optimization utilities."""
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.query_stats = {}
        self.slow_query_threshold = 1.0  # seconds
        self.redis_client = None
        
    async def initialize(self):
        """Initialize performance optimization components."""
        if settings.cache_enabled:
            await self._initialize_redis()
            
    async def _initialize_redis(self):
        """Initialize Redis for caching."""
        try:
            self.redis_client = redis.from_url(
                settings.redis_url,
                decode_responses=True,
                health_check_interval=30,
                retry_on_timeout=True,
                socket_keepalive=True,
                socket_keepalive_options={}
            )
            await self.redis_client.ping()
            self.logger.info("Redis cache initialized for performance optimization")
        except Exception as e:
            self.logger.warning(f"Failed to initialize Redis cache: {e}")
            self.redis_client = None
    
    @asynccontextmanager
    async def monitor_query_performance(self, query_type: str, description: str):
        """Monitor query performance metrics."""
        start_time = time.time()
        try:
            yield
        finally:
            execution_time = time.time() - start_time
            
            # Record query stats
            if query_type not in self.query_stats:
                self.query_stats[query_type] = {
                    'count': 0,
                    'total_time': 0,
                    'max_time': 0,
                    'min_time': float('inf')
                }
            
            stats = self.query_stats[query_type]
            stats['count'] += 1
            stats['total_time'] += execution_time
            stats['max_time'] = max(stats['max_time'], execution_time)
            stats['min_time'] = min(stats['min_time'], execution_time)
            
            # Log slow queries
            if execution_time > self.slow_query_threshold:
                self.logger.warning(
                    f"Slow query detected: {query_type} - {description} - "
                    f"Execution time: {execution_time:.2f}s"
                )
    
    async def cache_result(self, key: str, result: Any, ttl: int = None):
        """Cache a result in Redis."""
        if not self.redis_client or not settings.cache_enabled:
            return
            
        try:
            cache_ttl = ttl or settings.cache_ttl
            await self.redis_client.setex(key, cache_ttl, str(result))
        except Exception as e:
            self.logger.warning(f"Failed to cache result for {key}: {e}")
    
    async def get_cached_result(self, key: str) -> Optional[Any]:
        """Get a cached result from Redis."""
        if not self.redis_client or not settings.cache_enabled:
            return None
            
        try:
            result = await self.redis_client.get(key)
            return eval(result) if result else None
        except Exception as e:
            self.logger.warning(f"Failed to get cached result for {key}: {e}")
            return None
    
    async def optimize_query(
        self, 
        query: str, 
        params: Dict[str, Any] = None,
        db: AsyncSession = None
    ) -> List[Dict[str, Any]]:
        """Optimize and execute a database query with monitoring."""
        if not db:
            db = next(get_db())
            
        async with self.monitor_query_performance("sql_query", query):
            try:
                # Add query optimization hints if needed
                optimized_query = self._add_query_hints(query)
                
                # Execute query
                result = await db.execute(text(optimized_query), params or {})
                
                # Convert to list of dictionaries
                return [dict(row._mapping) for row in result.fetchall()]
                
            except Exception as e:
                self.logger.error(f"Query optimization failed: {e}")
                raise
    
    def _add_query_hints(self, query: str) -> str:
        """Add query optimization hints if needed."""
        # Add specific optimizations for common query patterns
        if "SELECT" in query and "ORDER BY" in query:
            # Consider adding index hints for ORDER BY queries
            pass
        
        if "SELECT" in query and "WHERE" in query:
            # Consider adding index hints for WHERE queries
            pass
            
        return query
    
    def get_query_stats(self) -> Dict[str, Any]:
        """Get performance statistics for all queries."""
        stats = {}
        for query_type, data in self.query_stats.items():
            avg_time = data['total_time'] / data['count'] if data['count'] > 0 else 0
            stats[query_type] = {
                'count': data['count'],
                'avg_time': avg_time,
                'total_time': data['total_time'],
                'max_time': data['max_time'],
                'min_time': data['min_time']
            }
        return stats
    
    async def optimize_indexes(self, db: AsyncSession):
        """Analyze and optimize database indexes."""
        try:
            # Get index usage statistics
            result = await db.execute(text("""
                SELECT 
                    schemaname,
                    tablename,
                    indexname,
                    idx_scan,
                    idx_tup_read,
                    idx_tup_fetch
                FROM pg_stat_user_indexes
                ORDER BY idx_scan DESC
            """))
            
            indexes = result.fetchall()
            
            # Recommend index creation for frequently accessed columns
            recommendations = []
            for index in indexes:
                if index.idx_scan > 1000:  # High usage index
                    recommendations.append({
                        'table': index.tablename,
                        'index': index.indexname,
                        'usage': index.idx_scan,
                        'recommendation': 'KEEP - High usage'
                    })
                elif index.idx_scan < 10:  # Low usage index
                    recommendations.append({
                        'table': index.tablename,
                        'index': index.indexname,
                        'usage': index.idx_scan,
                        'recommendation': 'CONSIDER REMOVING - Low usage'
                    })
            
            self.logger.info(f"Index optimization completed. {len(recommendations)} recommendations found.")
            return recommendations
            
        except Exception as e:
            self.logger.error(f"Index optimization failed: {e}")
            return []


# Global performance optimizer instance
performance_optimizer = DatabasePerformanceOptimizer()


async def optimize_database_connections():
    """Optimize database connection pool settings."""
    # PostgreSQL connection optimization
    postgres_engine = create_engine(
        settings.database_url,
        poolclass=QueuePool,
        pool_size=20,  # Adjust based on expected load
        max_overflow=30,
        pool_pre_ping=True,
        pool_recycle=3600,
        echo=settings.debug,
        future=True,
        pool_timeout=30,  # How long to wait for a connection from the pool
        pool_reset_on_return='commit',  # Reset connections when returning to pool
    )
    
    # Redis connection optimization
    redis_client = redis.from_url(
        settings.redis_url,
        decode_responses=True,
        health_check_interval=30,
        retry_on_timeout=True,
        socket_keepalive=True,
        socket_keepalive_options={},
        retry_on_error=[redis.exceptions.ConnectionError],
        connection_pool_kwargs={
            'max_connections': 50,
            'health_check_interval': 30
        }
    )
    
    return postgres_engine, redis_client