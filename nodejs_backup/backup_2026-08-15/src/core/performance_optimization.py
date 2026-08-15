"""
Performance Optimization Module

This module implements various performance optimization techniques
for the Edu-Flow API to ensure fast response times and efficient resource usage.
"""

import time
import asyncio
import functools
from typing import Dict, List, Any, Optional
from contextlib import asynccontextmanager
from datetime import datetime, timedelta
import json
import logging
from concurrent.futures import ThreadPoolExecutor
from dataclasses import dataclass, field
import redis
from cachetools import TTLCache, cached
import psutil
import statistics

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

@dataclass
class PerformanceMetrics:
    """Performance metrics data class"""
    response_time: float = 0.0
    memory_usage: float = 0.0
    cpu_usage: float = 0.0
    db_query_time: float = 0.0
    cache_hits: int = 0
    cache_misses: int = 0
    request_count: int = 0
    error_count: int = 0

class PerformanceOptimizer:
    """Performance optimization manager"""
    
    def __init__(self):
        # Redis connection for distributed caching
        self.redis_client = redis.Redis(
            host='localhost',
            port=6379,
            db=0,
            decode_responses=True,
            socket_connect_timeout=5,
            socket_timeout=5
        )
        
        # In-memory cache with TTL (1 hour)
        self.cache = TTLCache(maxsize=1000, ttl=3600)
        
        # Performance metrics
        self.metrics: Dict[str, PerformanceMetrics] = {}
        
        # Database connection pooling
        self.db_pool = None
        
        # Background tasks
        self.executor = ThreadPoolExecutor(max_workers=10)
        
        # Request processing optimization
        self.request_queue = asyncio.Queue(maxsize=1000)
        
        # API rate limiting
        self.rate_limits = {}
        
        logger.info("PerformanceOptimizer initialized")
    
    @asynccontextmanager
    async def measure_performance(self, endpoint: str):
        """Measure performance for a specific endpoint"""
        start_time = time.time()
        start_memory = psutil.Process().memory_info().rss / 1024 / 1024  # MB
        start_cpu = psutil.cpu_percent()
        
        try:
            yield
        except Exception as e:
            self.metrics[endpoint].error_count += 1
            raise e
        finally:
            end_time = time.time()
            end_memory = psutil.Process().memory_info().rss / 1024 / 1024  # MB
            end_cpu = psutil.cpu_percent()
            
            # Update metrics
            if endpoint not in self.metrics:
                self.metrics[endpoint] = PerformanceMetrics()
            
            metrics = self.metrics[endpoint]
            metrics.response_time = end_time - start_time
            metrics.memory_usage = end_memory - start_memory
            metrics.cpu_usage = end_cpu - start_cpu
            metrics.request_count += 1
            
            # Log performance
            logger.info(f"Endpoint {endpoint} performance: "
                       f"Time={metrics.response_time:.2f}s, "
                       f"Memory={metrics.memory_usage:.2f}MB, "
                       f"CPU={metrics.cpu_usage:.2f}%")
    
    @cached(cache=TTLCache(maxsize=1000, ttl=3600))
    def get_cached_data(self, key: str, query_func):
        """Get cached data with fallback to query function"""
        try:
            # Try to get from cache
            data = self.cache.get(key)
            if data is not None:
                return data
            
            # Cache miss - get from database
            data = query_func()
            self.cache[key] = data
            return data
        except Exception as e:
            logger.error(f"Cache error for key {key}: {e}")
            return query_func()
    
    def optimize_database_query(self, query_func):
        """Optimize database queries with connection pooling"""
        @functools.wraps(query_func)
        async def wrapper(*args, **kwargs):
            if self.db_pool is None:
                await self._init_db_pool()
            
            start_time = time.time()
            
            try:
                async with self.db_pool.acquire() as conn:
                    result = await query_func(conn, *args, **kwargs)
                
                end_time = time.time()
                return result
            except Exception as e:
                logger.error(f"Database query error: {e}")
                raise e
        return wrapper
    
    async def _init_db_pool(self):
        """Initialize database connection pool"""
        try:
            # This would be initialized with your actual database connection
            # For now, we'll create a mock pool
            self.db_pool = MockConnectionPool()
            logger.info("Database connection pool initialized")
        except Exception as e:
            logger.error(f"Failed to initialize database pool: {e}")
            raise e
    
    def rate_limit(self, max_requests: int = 100, time_window: int = 60):
        """Rate limiting decorator"""
        def decorator(func):
            @functools.wraps(func)
            async def wrapper(*args, **kwargs):
                # Get client identifier (could be IP, user ID, etc.)
                client_id = kwargs.get('user_id') or 'unknown'
                
                # Clean old rate limit entries
                now = time.time()
                if client_id not in self.rate_limits:
                    self.rate_limits[client_id] = []
                
                # Remove old entries
                self.rate_limits[client_id] = [
                    timestamp for timestamp in self.rate_limits[client_id]
                    if now - timestamp < time_window
                ]
                
                # Check if limit exceeded
                if len(self.rate_limits[client_id]) >= max_requests:
                    raise Exception(f"Rate limit exceeded for client {client_id}")
                
                # Add new request
                self.rate_limits[client_id].append(now)
                
                return await func(*args, **kwargs)
            return wrapper
        return decorator
    
    def background_task(self, task_func):
        """Run task in background"""
        def decorator(func):
            @functools.wraps(func)
            def wrapper(*args, **kwargs):
                # Submit to thread pool
                self.executor.submit(task_func, *args, **kwargs)
                return func(*args, **kwargs)
            return wrapper
        return decorator
    
    async def process_queue(self):
        """Process requests from queue"""
        while True:
            try:
                request = await self.request_queue.get()
                await request['func'](*request['args'], **request['kwargs'])
                self.request_queue.task_done()
            except Exception as e:
                logger.error(f"Error processing request: {e}")
    
    def add_to_queue(self, func, *args, **kwargs):
        """Add function to processing queue"""
        try:
            self.request_queue.put_nowait({
                'func': func,
                'args': args,
                'kwargs': kwargs
            })
        except asyncio.QueueFull:
            logger.error("Request queue is full")
    
    def get_performance_report(self) -> Dict[str, Any]:
        """Generate performance report"""
        report = {
            'timestamp': datetime.now().isoformat(),
            'endpoints': {},
            'system_metrics': {
                'memory_usage': psutil.Process().memory_info().rss / 1024 / 1024,  # MB
                'cpu_usage': psutil.cpu_percent(),
                'disk_usage': psutil.disk_usage('/').percent
            }
        }
        
        for endpoint, metrics in self.metrics.items():
            report['endpoints'][endpoint] = {
                'avg_response_time': metrics.response_time,
                'total_requests': metrics.request_count,
                'error_count': metrics.error_count,
                'success_rate': (metrics.request_count - metrics.error_count) / metrics.request_count * 100,
                'cache_hit_rate': metrics.cache_hits / (metrics.cache_hits + metrics.cache_misses) * 100
            }
        
        return report
    
    def export_metrics_to_file(self, filename: str):
        """Export metrics to file"""
        try:
            with open(filename, 'w') as f:
                json.dump(self.get_performance_report(), f, indent=2)
            logger.info(f"Metrics exported to {filename}")
        except Exception as e:
            logger.error(f"Failed to export metrics: {e}")
    
    def cleanup_old_metrics(self, days: int = 7):
        """Clean up old metrics"""
        cutoff_time = time.time() - (days * 24 * 60 * 60)
        endpoints_to_remove = []
        
        for endpoint, metrics in self.metrics.items():
            if metrics.last_updated < cutoff_time:
                endpoints_to_remove.append(endpoint)
        
        for endpoint in endpoints_to_remove:
            del self.metrics[endpoint]
        
        logger.info(f"Cleaned up {len(endpoints_to_remove)} old metrics")

class MockConnectionPool:
    """Mock database connection pool for testing"""
    
    def __init__(self):
        self.connections = []
    
    async def acquire(self):
        return MockConnection()
    
    async def release(self, conn):
        pass

class MockConnection:
    """Mock database connection"""
    
    async def execute(self, query, *args):
        await asyncio.sleep(0.001)  # Simulate database query time
        return []
    
    async def fetchall(self, query, *args):
        await asyncio.sleep(0.001)
        return []
    
    async def fetchone(self, query, *args):
        await asyncio.sleep(0.001)
        return None

# Global performance optimizer instance
performance_optimizer = PerformanceOptimizer()

# Performance monitoring middleware
async def performance_middleware(request, call_next):
    """FastAPI middleware for performance monitoring"""
    endpoint = request.url.path
    user_id = getattr(request.state, 'user', {}).get('id', 'anonymous')
    
    async with performance_optimizer.measure_performance(f"{endpoint}_{user_id}"):
        response = await call_next(request)
        return response

# Database query optimization decorator
def optimize_database_query(func):
    """Decorator to optimize database queries"""
    return performance_optimizer.optimize_database_query(func)

# Rate limiting decorator
def rate_limit(max_requests: int = 100, time_window: int = 60):
    """Decorator to apply rate limiting"""
    return performance_optimizer.rate_limit(max_requests, time_window)

# Background task decorator
def background_task(func):
    """Decorator to run task in background"""
    return performance_optimizer.background_task(func)

# Cached data decorator
def cached_data(key: str):
    """Decorator to cache data"""
    def decorator(func):
        def wrapper(*args, **kwargs):
            return performance_optimizer.get_cached_data(key, lambda: func(*args, **kwargs))
        return wrapper
    return decorator

# Performance monitoring utilities
async def monitor_performance():
    """Continuous performance monitoring"""
    while True:
        try:
            # Generate report every minute
            report = performance_optimizer.get_performance_report()
            
            # Check for performance issues
            for endpoint, metrics in report['endpoints'].items():
                if metrics['avg_response_time'] > 5.0:  # 5 seconds threshold
                    logger.warning(f"High response time for {endpoint}: {metrics['avg_response_time']:.2f}s")
                
                if metrics['error_rate'] > 5.0:  # 5% error rate threshold
                    logger.warning(f"High error rate for {endpoint}: {metrics['error_rate']:.2f}%")
            
            await asyncio.sleep(60)  # Wait 1 minute
        except Exception as e:
            logger.error(f"Performance monitoring error: {e}")
            await asyncio.sleep(60)

# Example usage
if __name__ == "__main__":
    # Example of using the performance optimizer
    
    # 1. Get cached data
    def get_user_from_db(user_id):
        # Simulate database query
        return {"id": user_id, "name": f"User {user_id}"}
    
    @cached_data("user_123")
    def get_user(user_id):
        return get_user_from_db(user_id)
    
    # 2. Rate limited function
    @rate_limit(max_requests=10, time_window=60)
    async def api_call(user_id):
        return {"message": "success"}
    
    # 3. Background task
    @background_task
    def send_notification(user_id, message):
        # Send notification in background
        pass
    
    # 4. Database query optimization
    @optimize_database_query
    async def get_student_grades(conn, student_id):
        # Optimized database query
        await conn.execute("SELECT * FROM grades WHERE student_id = %s", student_id)
        return []
    
    # Start monitoring
    asyncio.create_task(monitor_performance())
    
    # Example usage
    user = get_user("123")
    print(f"User: {user}")
    
    asyncio.run(api_call("123"))