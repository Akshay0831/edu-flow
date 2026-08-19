"""
Monitoring System Module

This module provides comprehensive monitoring and logging capabilities
for the Edu-Flow backend system.
"""

import logging
import asyncio
import json
import time
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional, Callable
from dataclasses import dataclass, field
from contextlib import contextmanager
import psutil
import aiofiles
import pandas as pd
from prometheus_client import Counter, Histogram, Gauge, generate_latest
import threading
import queue
import sys

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('logs/monitoring.log'),
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger(__name__)

@dataclass
class SystemMetrics:
    """System metrics data class"""
    timestamp: float
    cpu_usage: float
    memory_usage: float
    disk_usage: float
    network_io: Dict[str, float]
    process_count: int
    thread_count: int
    gc_count: int = field(default_factory=int)

@dataclass
class APIMetrics:
    """API metrics data class"""
    endpoint: str
    method: str
    status_code: int
    response_time: float
    request_size: int
    response_size: int
    user_id: Optional[str] = None
    error_message: Optional[str] = None

@dataclass
class DatabaseMetrics:
    """Database metrics data class"""
    query_type: str
    query_duration: float
    query_size: int
    result_size: int
    connection_pool_size: int
    active_connections: int
    slow_queries: List[Dict[str, Any]] = field(default_factory=list)

class AlertSystem:
    """Alert management system"""
    
    def __init__(self):
        self.alerts: List[Dict[str, Any]] = []
        self.alert_handlers: Dict[str, List[Callable]] = {}
        self.alert_history_file = "logs/alert_history.json"
    
    def add_alert_handler(self, alert_type: str, handler: Callable):
        """Add alert handler"""
        if alert_type not in self.alert_handlers:
            self.alert_handlers[alert_type] = []
        self.alert_handlers[alert_type].append(handler)
    
    async def send_alert(self, alert_type: str, message: str, severity: str = "INFO"):
        """Send alert"""
        alert = {
            "id": str(len(self.alerts) + 1),
            "type": alert_type,
            "message": message,
            "severity": severity,
            "timestamp": datetime.now().isoformat(),
            "resolved": False
        }
        
        self.alerts.append(alert)
        
        # Log alert
        logger.warning(f"ALERT {alert_type}: {message} (Severity: {severity})")
        
        # Notify handlers
        if alert_type in self.alert_handlers:
            for handler in self.alert_handlers[alert_type]:
                try:
                    await handler(alert)
                except Exception as e:
                    logger.error(f"Error in alert handler: {e}")
        
        # Save to history
        await self.save_alert_to_history(alert)
        
        return alert
    
    async def save_alert_to_history(self, alert: Dict[str, Any]):
        """Save alert to history file"""
        try:
            async with aiofiles.open(self.alert_history_file, 'a') as f:
                await f.write(json.dumps(alert) + '\n')
        except Exception as e:
            logger.error(f"Error saving alert to history: {e}")
    
    def get_alerts(self, alert_type: str = None, resolved: bool = None):
        """Get alerts"""
        alerts = self.alerts
        
        if alert_type:
            alerts = [a for a in alerts if a['type'] == alert_type]
        
        if resolved is not None:
            alerts = [a for a in alerts if a['resolved'] == resolved]
        
        return alerts

class PerformanceMonitor:
    """Performance monitoring"""
    
    def __init__(self):
        self.api_metrics: List[APIMetrics] = []
        self.database_metrics: List[DatabaseMetrics] = []
        self.system_metrics: List[SystemMetrics] = []
        self.alert_system = AlertSystem()
        
        # Prometheus metrics
        self.request_counter = Counter('api_requests_total', 'Total API requests', ['endpoint', 'method', 'status'])
        self.response_histogram = Histogram('api_response_time_seconds', 'API response time', ['endpoint', 'method'])
        self.error_counter = Counter('api_errors_total', 'Total API errors', ['error_type'])
        self.db_query_counter = Counter('db_queries_total', 'Total database queries', ['query_type'])
        self.db_slow_query_counter = Counter('db_slow_queries_total', 'Total slow database queries', ['query_type'])
        
        # Alert thresholds
        self.alert_thresholds = {
            'high_cpu_usage': 80.0,  # 80%
            'high_memory_usage': 90.0,  # 90%
            'high_disk_usage': 95.0,  # 95%
            'slow_api_response': 5.0,  # 5 seconds
            'slow_db_query': 1.0,  # 1 second
        }
    
    @contextmanager
    def measure_api(self, endpoint: str, method: str, user_id: str = None):
        """Measure API performance"""
        start_time = time.time()
        request_size = sys.getsizeof({})  # This would be actual request size
        
        try:
            yield
        except Exception as e:
            response_time = time.time() - start_time
            error_message = str(e)
            
            # Record error
            self.record_api_metrics(
                endpoint=endpoint,
                method=method,
                status_code=500,
                response_time=response_time,
                request_size=request_size,
                response_size=0,
                user_id=user_id,
                error_message=error_message
            )
            
            # Send error alert
            asyncio.create_task(self.alert_system.send_alert(
                "API_ERROR",
                f"API error in {endpoint} ({method}): {error_message}",
                "ERROR"
            ))
            
            self.error_counter.labels(error_type="server_error").inc()
            raise
        finally:
            response_time = time.time() - start_time
            # Record metrics (would need actual response size)
            self.record_api_metrics(
                endpoint=endpoint,
                method=method,
                status_code=200,  # Placeholder, would be actual status
                response_time=response_time,
                request_size=request_size,
                response_size=0,  # Placeholder
                user_id=user_id
            )
            
            # Prometheus metrics
            self.request_counter.labels(endpoint=endpoint, method=method, status="200").inc()
            self.response_histogram.labels(endpoint=endpoint, method=method).observe(response_time)
    
    def record_api_metrics(self, endpoint: str, method: str, status_code: int,
                          response_time: float, request_size: int, response_size: int,
                          user_id: str = None, error_message: str = None):
        """Record API metrics"""
        metrics = APIMetrics(
            endpoint=endpoint,
            method=method,
            status_code=status_code,
            response_time=response_time,
            request_size=request_size,
            response_size=response_size,
            user_id=user_id,
            error_message=error_message
        )
        
        self.api_metrics.append(metrics)
        
        # Check for performance alerts
        if response_time > self.alert_thresholds['slow_api_response']:
            asyncio.create_task(self.alert_system.send_alert(
                "SLOW_API",
                f"Slow API response: {endpoint} ({method}) - {response_time:.2f}s",
                "WARNING"
            ))
            self.error_counter.labels(error_type="slow_response").inc()
    
    @contextmanager
    def measure_database(self, query_type: str):
        """Measure database performance"""
        start_time = time.time()
        query_size = sys.getsizeof({})  # This would be actual query size
        
        try:
            yield
        finally:
            query_duration = time.time() - start_time
            result_size = 0  # Placeholder, would be actual result size
            
            # Record metrics
            metrics = DatabaseMetrics(
                query_type=query_type,
                query_duration=query_duration,
                query_size=query_size,
                result_size=result_size,
                connection_pool_size=10,  # Placeholder
                active_connections=5  # Placeholder
            )
            
            self.database_metrics.append(metrics)
            
            # Prometheus metrics
            self.db_query_counter.labels(query_type=query_type).inc()
            
            # Check for slow queries
            if query_duration > self.alert_thresholds['slow_db_query']:
                asyncio.create_task(self.alert_system.send_alert(
                    "SLOW_DB_QUERY",
                    f"Slow database query ({query_type}): {query_duration:.2f}s",
                    "WARNING"
                ))
                self.db_slow_query_counter.labels(query_type=query_type).inc()
                metrics.slow_queries.append({
                    "timestamp": datetime.now().isoformat(),
                    "duration": query_duration,
                    "query_type": query_type
                })
    
    def collect_system_metrics(self):
        """Collect system metrics"""
        cpu_usage = psutil.cpu_percent()
        memory = psutil.virtual_memory()
        disk = psutil.disk_usage('/')
        network = psutil.net_io_counters()
        process = psutil.Process()
        
        metrics = SystemMetrics(
            timestamp=time.time(),
            cpu_usage=cpu_usage,
            memory_usage=memory.percent,
            disk_usage=disk.percent,
            network_io={
                'bytes_sent': network.bytes_sent,
                'bytes_recv': network.bytes_recv,
                'packets_sent': network.packets_sent,
                'packets_recv': network.packets_recv
            },
            process_count=len(psutil.pids()),
            thread_count=process.num_threads(),
            gc_count=len(gc.get_objects()) if 'gc' in sys.modules else 0
        )
        
        self.system_metrics.append(metrics)
        
        # Check for system alerts
        if cpu_usage > self.alert_thresholds['high_cpu_usage']:
            asyncio.create_task(self.alert_system.send_alert(
                "HIGH_CPU",
                f"High CPU usage: {cpu_usage}%",
                "WARNING"
            ))
        
        if memory.percent > self.alert_thresholds['high_memory_usage']:
            asyncio.create_task(self.alert_system.send_alert(
                "HIGH_MEMORY",
                f"High memory usage: {memory.percent}%",
                "WARNING"
            ))
        
        if disk.percent > self.alert_thresholds['high_disk_usage']:
            asyncio.create_task(self.alert_system.send_alert(
                "HIGH_DISK",
                f"High disk usage: {disk.percent}%",
                "CRITICAL"
            ))
    
    def get_metrics_report(self, time_range: int = 3600) -> Dict[str, Any]:
        """Generate metrics report"""
        now = time.time()
        cutoff_time = now - time_range
        
        # Filter metrics by time range
        api_metrics = [m for m in self.api_metrics if m.timestamp > cutoff_time]
        db_metrics = [m for m in self.database_metrics if m.timestamp > cutoff_time]
        system_metrics = [m for m in self.system_metrics if m.timestamp > cutoff_time]
        
        # Calculate averages
        avg_api_response_time = statistics.mean([m.response_time for m in api_metrics]) if api_metrics else 0
        avg_db_query_time = statistics.mean([m.query_duration for m in db_metrics]) if db_metrics else 0
        avg_cpu_usage = statistics.mean([m.cpu_usage for m in system_metrics]) if system_metrics else 0
        
        # Top endpoints by response time
        endpoint_times = {}
        for metrics in api_metrics:
            key = f"{metrics.endpoint}_{metrics.method}"
            if key not in endpoint_times:
                endpoint_times[key] = []
            endpoint_times[key].append(metrics.response_time)
        
        slowest_endpoints = sorted([
            (endpoint, statistics.mean(times))
            for endpoint, times in endpoint_times.items()
            if len(times) >= 10  # Only consider endpoints with at least 10 requests
        ], key=lambda x: x[1], reverse=True)[:10]
        
        # Slow database queries
        slow_db_queries = []
        for metrics in db_metrics:
            if metrics.slow_queries:
                slow_db_queries.extend(metrics.slow_queries)
        
        return {
            'timestamp': datetime.now().isoformat(),
            'time_range_seconds': time_range,
            'api_metrics': {
                'total_requests': len(api_metrics),
                'avg_response_time': avg_api_response_time,
                'endpoints': slowest_endpoints,
                'error_rate': len([m for m in api_metrics if m.status_code >= 400]) / len(api_metrics) * 100 if api_metrics else 0
            },
            'database_metrics': {
                'total_queries': len(db_metrics),
                'avg_query_time': avg_db_query_time,
                'slow_queries': len(slow_db_queries),
                'slow_query_details': slow_db_queries[-10:]  # Last 10 slow queries
            },
            'system_metrics': {
                'avg_cpu_usage': avg_cpu_usage,
                'total_system_metrics': len(system_metrics),
                'latest_metrics': system_metrics[-1] if system_metrics else None
            },
            'alerts': self.alert_system.get_alerts(resolved=False)
        }
    
    def export_metrics_to_prometheus(self) -> str:
        """Export metrics to Prometheus format"""
        return generate_latest().decode('utf-8')
    
    async def save_metrics_to_file(self, filename: str):
        """Save metrics to file"""
        try:
            async with aiofiles.open(filename, 'w') as f:
                report = self.get_metrics_report()
                await f.write(json.dumps(report, indent=2))
        except Exception as e:
            logger.error(f"Error saving metrics: {e}")

class MonitoringService:
    """Main monitoring service"""
    
    def __init__(self):
        self.performance_monitor = PerformanceMonitor()
        self.monitoring_task = None
        self.metrics_queue = queue.Queue()
        
        # Configure alert handlers
        self._setup_alert_handlers()
    
    def _setup_alert_handlers(self):
        """Setup alert handlers"""
        async def log_alert_handler(alert):
            """Log alerts to file"""
            try:
                async with aiofiles.open('logs/alerts.log', 'a') as f:
                    await f.write(f"{json.dumps(alert)}\n")
            except Exception as e:
                logger.error(f"Error logging alert: {e}")
        
        async def email_alert_handler(alert):
            """Send email alerts"""
            # Placeholder for email sending logic
            logger.info(f"Email alert sent: {alert['message']}")
        
        # Add handlers
        self.performance_monitor.alert_system.add_alert_handler("API_ERROR", log_alert_handler)
        self.performance_monitor.alert_system.add_alert_handler("SLOW_API", log_alert_handler)
        self.performance_monitor.alert_system.add_alert_handler("SLOW_DB_QUERY", log_alert_handler)
        self.performance_monitor.alert_system.add_alert_handler("HIGH_CPU", log_alert_handler)
        self.performance_monitor.alert_system.add_alert_handler("HIGH_MEMORY", log_alert_handler)
        self.performance_monitor.alert_system.add_alert_handler("HIGH_DISK", log_alert_handler)
    
    async def start_monitoring(self):
        """Start monitoring"""
        self.monitoring_task = asyncio.create_task(self._monitoring_loop())
        logger.info("Monitoring service started")
    
    async def stop_monitoring(self):
        """Stop monitoring"""
        if self.monitoring_task:
            self.monitoring_task.cancel()
            try:
                await self.monitoring_task
            except asyncio.CancelledError:
                pass
            logger.info("Monitoring service stopped")
    
    async def _monitoring_loop(self):
        """Main monitoring loop"""
        while True:
            try:
                # Collect system metrics every 30 seconds
                self.performance_monitor.collect_system_metrics()
                
                # Save metrics every 5 minutes
                if int(time.time()) % 300 == 0:
                    await self.performance_monitor.save_metrics_to_file('logs/latest_metrics.json')
                
                # Clean up old metrics every hour
                if int(time.time()) % 3600 == 0:
                    await self._cleanup_old_metrics()
                
                await asyncio.sleep(30)  # Check every 30 seconds
            except Exception as e:
                logger.error(f"Error in monitoring loop: {e}")
                await asyncio.sleep(60)  # Wait longer if there's an error
    
    async def _cleanup_old_metrics(self):
        """Clean up old metrics"""
        # Keep only last 24 hours of metrics
        cutoff_time = time.time() - (24 * 60 * 60)
        
        self.performance_monitor.api_metrics = [
            m for m in self.performance_monitor.api_metrics if m.timestamp > cutoff_time
        ]
        self.performance_monitor.database_metrics = [
            m for m in self.performance_monitor.database_metrics if m.timestamp > cutoff_time
        ]
        self.performance_monitor.system_metrics = [
            m for m in self.performance_monitor.system_metrics if m.timestamp > cutoff_time
        ]
        
        logger.info("Cleaned up old metrics")
    
    def get_prometheus_metrics(self) -> str:
        """Get Prometheus metrics"""
        return self.performance_monitor.export_metrics_to_prometheus()
    
    async def get_metrics_report(self, time_range: int = 3600) -> Dict[str, Any]:
        """Get metrics report"""
        return self.performance_monitor.get_metrics_report(time_range)
    
    async def add_custom_metric(self, name: str, value: float, labels: Dict[str, str] = None):
        """Add custom metric"""
        # This would integrate with your preferred metrics system
        logger.info(f"Custom metric: {name} = {value}, labels = {labels}")

# Global monitoring service instance
monitoring_service = MonitoringService()

# Middleware for FastAPI
async def monitoring_middleware(request, call_next):
    """Monitoring middleware for FastAPI"""
    endpoint = request.url.path
    method = request.method
    
    # Extract user ID from JWT token (placeholder)
    user_id = getattr(request.state, 'user', {}).get('id', None)
    
    with monitoring_service.performance_monitor.measure_api(endpoint, method, user_id):
        response = await call_next(request)
        return response

# Initialize monitoring service
async def init_monitoring():
    """Initialize monitoring service"""
    await monitoring_service.start_monitoring()
    logger.info("Monitoring system initialized")

# Cleanup monitoring service
async def cleanup_monitoring():
    """Cleanup monitoring service"""
    await monitoring_service.stop_monitoring()
    logger.info("Monitoring system cleanup completed")

# Example usage
if __name__ == "__main__":
    async def main():
        # Initialize monitoring
        await init_monitoring()
        
        # Simulate some API calls
        for i in range(10):
            with monitoring_service.performance_monitor.measure_api("/test", "GET"):
                await asyncio.sleep(0.1)
        
        # Get metrics report
        report = await monitoring_service.get_metrics_report()
        print(json.dumps(report, indent=2))
        
        # Cleanup
        await cleanup_monitoring()
    
    asyncio.run(main())