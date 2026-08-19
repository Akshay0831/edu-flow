"""
Monitoring and Observability for Rust AI Services

This module provides comprehensive monitoring and observability:
- Prometheus metrics collection
- Service health checks
- Request/response tracking
- Error rate monitoring
- Performance metrics
- Distributed tracing

Author: Edu-Flow Team
"""

import time
import asyncio
import logging
from typing import Dict, List, Optional, Any, Callable
from dataclasses import dataclass, field
from datetime import datetime
from contextlib import contextmanager
import json

try:
    import prometheus_client as prometheus
    from prometheus_client import Counter, Gauge, Histogram, Summary
    PROMETHEUS_AVAILABLE = True
except ImportError:
    PROMETHEUS_AVAILABLE = False
    logger = logging.getLogger(__name__)

logger = logging.getLogger(__name__)


@dataclass
class ServiceMetrics:
    """Metrics for a service"""
    service_name: str
    requests_total: int
    requests_failed: int
    requests_success: int
    errors_total: int
    error_types: Dict[str, int]
    avg_latency_ms: float
    latency_p95_ms: float
    cache_hits: int
    cache_misses: int
    active_sessions: int
    memory_usage_mb: float
    cpu_usage_percent: float


class MonitoringSystem:
    """Monitoring and observability system for AI services"""
    
    def __init__(self, enabled: bool = True):
        """
        Initialize monitoring system
        
        Args:
            enabled: Enable/disable monitoring
        """
        self.enabled = enabled
        self._services: Dict[str, ServiceMetrics] = {}
        self._metrics = {}
        self._start_time = time.time()
        self._request_traces: List[Dict[str, Any]] = []
        self._max_trace_length = 1000
        
        if self.enabled and PROMETHEUS_AVAILABLE:
            self._init_prometheus_metrics()
    
    def _init_prometheus_metrics(self):
        """Initialize Prometheus metrics"""
        try:
            self._metrics["request_total"] = Counter(
                "rust_ai_requests_total",
                "Total number of requests to Rust AI services",
                ["service_name", "endpoint", "status"]
            )
            
            self._metrics["request_duration_seconds"] = Histogram(
                "rust_ai_request_duration_seconds",
                "Request duration in seconds",
                ["service_name", "endpoint"]
            )
            
            self._metrics["request_latency_ms"] = Histogram(
                "rust_ai_request_latency_ms",
                "Request latency in milliseconds",
                ["service_name", "endpoint"]
            )
            
            self._metrics["cache_hits_total"] = Counter(
                "rust_ai_cache_hits_total",
                "Total number of cache hits"
            )
            
            self._metrics["cache_misses_total"] = Counter(
                "rust_ai_cache_misses_total",
                "Total number of cache misses"
            )
            
            self._metrics["active_sessions"] = Gauge(
                "rust_ai_active_sessions",
                "Number of active sessions",
                ["service_name"]
            )
            
            logger.info("Prometheus metrics initialized")
            
        except Exception as e:
            logger.error(f"Failed to initialize Prometheus metrics: {e}")
            self.enabled = False
    
    def track_request(
        self,
        service_name: str,
        endpoint: str,
        status: str = "success",
        latency_ms: float = 0.0
    ):
        """
        Track request metrics
        
        Args:
            service_name: Name of service
            endpoint: Request endpoint
            status: Request status (success/failed)
            latency_ms: Request latency in milliseconds
        """
        if not self.enabled:
            return
        
        try:
            if PROMETHEUS_AVAILABLE:
                self._metrics["request_total"].labels(
                    service_name=service_name,
                    endpoint=endpoint,
                    status=status
                ).inc()
                
                self._metrics["request_latency_ms"].labels(
                    service_name=service_name,
                    endpoint=endpoint
                ).observe(latency_ms)
            
            # Update local metrics
            if service_name not in self._services:
                self._services[service_name] = ServiceMetrics(
                    service_name=service_name,
                    requests_total=0,
                    requests_failed=0,
                    requests_success=0,
                    errors_total=0,
                    error_types={},
                    avg_latency_ms=0.0,
                    latency_p95_ms=0.0,
                    cache_hits=0,
                    cache_misses=0,
                    active_sessions=0,
                    memory_usage_mb=0.0,
                    cpu_usage_percent=0.0,
                )
            
            metrics = self._services[service_name]
            metrics.requests_total += 1
            
            if status == "success":
                metrics.requests_success += 1
            else:
                metrics.requests_failed += 1
            
            if latency_ms > 0:
                metrics.avg_latency_ms = (
                    (metrics.avg_latency_ms * (metrics.requests_total - 1) + latency_ms) 
                    / metrics.requests_total
                )
            
        except Exception as e:
            logger.error(f"Error tracking request: {e}")
    
    def track_cache_hit(self, service_name: str):
        """Track cache hit"""
        if not self.enabled:
            return
        
        if PROMETHEUS_AVAILABLE:
            self._metrics["cache_hits_total"].inc()
        
        if service_name in self._services:
            self._services[service_name].cache_hits += 1
    
    def track_cache_miss(self, service_name: str):
        """Track cache miss"""
        if not self.enabled:
            return
        
        if PROMETHEUS_AVAILABLE:
            self._metrics["cache_misses_total"].inc()
        
        if service_name in self._services:
            self._services[service_name].cache_misses += 1
    
    def track_error(self, service_name: str, error_type: str):
        """Track error event"""
        if not self.enabled:
            return
        
        if service_name not in self._services:
            return
        
        metrics = self._services[service_name]
        metrics.errors_total += 1
        
        if error_type not in metrics.error_types:
            metrics.error_types[error_type] = 0
        metrics.error_types[error_type] += 1
    
    def track_session(self, service_name: str, count: int):
        """Track active sessions"""
        if not self.enabled:
            return
        
        if PROMETHEUS_AVAILABLE:
            self._metrics["active_sessions"].labels(
                service_name=service_name
            ).set(count)
        
        if service_name in self._services:
            self._services[service_name].active_sessions = count
    
    @contextmanager
    def request_timer(self, service_name: str, endpoint: str):
        """
        Context manager for tracking request duration
        
        Args:
            service_name: Name of service
            endpoint: Request endpoint
            
        Yields:
            None
            
        Example:
            with monitoring.request_timer("service", "/endpoint") as timer:
                # Do something
                pass
        """
        start_time = time.time()
        
        try:
            yield
            
            latency_ms = (time.time() - start_time) * 1000
            self.track_request(service_name, endpoint, "success", latency_ms)
            
        except Exception as e:
            latency_ms = (time.time() - start_time) * 1000
            self.track_request(service_name, endpoint, "failed", latency_ms)
            self.track_error(service_name, type(e).__name__)
            
            raise
    
    def log_request_trace(self, trace_data: Dict[str, Any]):
        """
        Log request trace
        
        Args:
            trace_data: Trace data dictionary
        """
        trace_data["timestamp"] = datetime.now().isoformat()
        
        self._request_traces.append(trace_data)
        
        # Limit trace length
        if len(self._request_traces) > self._max_trace_length:
            self._request_traces = self._request_traces[-self._max_trace_length:]
    
    def get_service_metrics(self, service_name: str) -> Optional[ServiceMetrics]:
        """Get metrics for a service"""
        return self._services.get(service_name)
    
    def get_all_metrics(self) -> Dict[str, ServiceMetrics]:
        """Get metrics for all services"""
        return self._services
    
    def get_system_metrics(self) -> Dict[str, Any]:
        """Get system-wide metrics"""
        total_requests = sum(s.requests_total for s in self._services.values())
        total_errors = sum(s.errors_total for s in self._services.values())
        uptime_seconds = time.time() - self._start_time
        
        return {
            "uptime_seconds": uptime_seconds,
            "total_requests": total_requests,
            "total_errors": total_errors,
            "error_rate": (total_errors / total_requests * 100) if total_requests > 0 else 0.0,
            "services_count": len(self._services),
            "services": {
                name: {
                    "requests_total": m.requests_total,
                    "errors_total": m.errors_total,
                    "avg_latency_ms": round(m.avg_latency_ms, 2),
                    "cache_hits": m.cache_hits,
                    "cache_misses": m.cache_misses,
                }
                for name, m in self._services.items()
            },
        }
    
    def get_request_traces(
        self,
        limit: int = 100,
        start_time: Optional[datetime] = None,
        end_time: Optional[datetime] = None
    ) -> List[Dict[str, Any]]:
        """
        Get request traces
        
        Args:
            limit: Maximum number of traces to return
            start_time: Start time filter
            end_time: End time filter
            
        Returns:
            List[Dict[str, Any]]: Request traces
        """
        traces = self._request_traces
        
        if start_time:
            traces = [t for t in traces if t.get('timestamp') >= start_time.isoformat()]
        
        if end_time:
            traces = [t for t in traces if t.get('timestamp') <= end_time.isoformat()]
        
        return traces[-limit:]
    
    def export_metrics_json(self) -> str:
        """Export metrics as JSON"""
        return json.dumps({
            "system": self.get_system_metrics(),
            "services": self.get_all_metrics(),
        }, indent=2)
    
    def reset_service_metrics(self, service_name: str):
        """Reset metrics for a service"""
        if service_name in self._services:
            self._services[service_name] = ServiceMetrics(
                service_name=service_name,
                requests_total=0,
                requests_failed=0,
                requests_success=0,
                errors_total=0,
                error_types={},
                avg_latency_ms=0.0,
                latency_p95_ms=0.0,
                cache_hits=0,
                cache_misses=0,
                active_sessions=0,
                memory_usage_mb=0.0,
                cpu_usage_percent=0.0,
            )
    
    def reset_all_metrics(self):
        """Reset all metrics"""
        self._services = {}
        self._request_traces = []
        self._start_time = time.time()


# Global monitoring instance
monitoring = MonitoringSystem(enabled=True)


def track_service_request(service_name: str, endpoint: str):
    """
    Decorator for tracking service requests
    
    Args:
        service_name: Name of service
        endpoint: Request endpoint
        
    Example:
        @track_service_request("service", "/endpoint")
        async def my_function():
            pass
    """
    def decorator(f):
        @wraps(f)
        async def wrapper(*args, **kwargs):
            with monitoring.request_timer(service_name, endpoint):
                return await f(*args, **kwargs)
        return wrapper
    return decorator
