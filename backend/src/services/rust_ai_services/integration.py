"""
Integration Layer for Rust AI Services

This module provides communication layer between Python FastAPI backend
and Rust microservices:
- REST API communication
- Message-based communication (asyncio queues)
- Error handling and retry logic
- Request/response caching
- Service discovery integration
- Health checking

Author: Edu-Flow Team
"""

import asyncio
import aiohttp
import json
import logging
from typing import Dict, List, Optional, Any, Callable
from datetime import datetime, timedelta
from dataclasses import dataclass, field
from functools import wraps
import hashlib

from .registry import ServiceInstance
from .config import AIServiceConfig

logger = logging.getLogger(__name__)


@dataclass
class ServiceRequest:
    """Request to a service"""
    service_name: str
    endpoint: str
    method: str = "POST"
    data: Optional[Dict[str, Any]] = None
    params: Optional[Dict[str, Any]] = None
    headers: Optional[Dict[str, str]] = None
    timeout: int = 30
    retry_attempts: int = 3
    cache_key: Optional[str] = None
    cache_ttl: int = 3600


@dataclass
class ServiceResponse:
    """Response from a service"""
    success: bool
    data: Optional[Any] = None
    status_code: int = 200
    error: Optional[str] = None
    latency_ms: float = 0.0
    timestamp: datetime = field(default_factory=datetime.now)


class IntegrationLayer:
    """Integration layer for Python-Rust service communication"""
    
    def __init__(self):
        """Initialize integration layer"""
        self._session: Optional[aiohttp.ClientSession] = None
        self._request_cache: Dict[str, Tuple[Any, datetime]] = {}
        self._cache_ttl: int = 3600
        self._listeners: List[Callable] = []
        self._request_counter = 0
        self._response_times: List[float] = []
    
    async def initialize(self):
        """Initialize HTTP session"""
        timeout = aiohttp.ClientTimeout(total=30)
        self._session = aiohttp.ClientSession(timeout=timeout)
        logger.info("Integration layer initialized")
    
    async def close(self):
        """Close HTTP session"""
        if self._session:
            await self._session.close()
            logger.info("Integration layer closed")
    
    async def request(self, request: ServiceRequest) -> ServiceResponse:
        """
        Send request to service
        
        Args:
            request: Service request
            
        Returns:
            ServiceResponse: Service response
        """
        # Check cache first
        if request.cache_key:
            cached_result = self._get_from_cache(request.cache_key)
            if cached_result:
                logger.debug(f"Returning cached response for {request.cache_key}")
                return cached_result
        
        # Send request
        start_time = datetime.now()
        
        try:
            response = await self._send_request(request)
            latency_ms = (datetime.now() - start_time).total_seconds() * 1000
            
            result = ServiceResponse(
                success=True,
                data=response,
                status_code=200,
                latency_ms=latency_ms,
            )
            
            # Update response times
            self._response_times.append(latency_ms)
            if len(self._response_times) > 100:
                self._response_times = self._response_times[-100:]
            
            # Cache response if needed
            if request.cache_key:
                self._save_to_cache(request.cache_key, result, request.cache_ttl)
            
            # Notify listeners
            self._notify_listeners(request, result)
            
            return result
            
        except Exception as e:
            latency_ms = (datetime.now() - start_time).total_seconds() * 1000
            
            result = ServiceResponse(
                success=False,
                error=str(e),
                latency_ms=latency_ms,
            )
            
            # Log error
            logger.error(f"Request to {request.service_name}{request.endpoint} failed: {e}")
            
            # Notify listeners
            self._notify_listeners(request, result, error=True)
            
            return result
    
    async def _send_request(self, request: ServiceRequest) -> Any:
        """
        Send HTTP request to service
        
        Args:
            request: Service request
            
        Returns:
            Any: Response data
        """
        # Get service instance from registry
        service = await self._get_service_instance(request.service_name)
        if not service:
            raise Exception(f"Service {request.service_name} not available")
        
        # Build URL
        base_url = service.instance_url
        if base_url.endswith('/'):
            base_url = base_url[:-1]
        
        url = f"{base_url}{request.endpoint}"
        
        # Prepare headers
        headers = {
            "Content-Type": "application/json",
            "Accept": "application/json",
            "X-Request-ID": str(self._request_counter),
        }
        
        if request.headers:
            headers.update(request.headers)
        
        # Prepare request data
        json_data = None
        if request.data:
            json_data = json.dumps(request.data)
        
        # Send request with retry
        response = await self._send_with_retry(
            request=request,
            url=url,
            headers=headers,
            json_data=json_data,
        )
        
        # Parse response
        response_data = await response.json()
        
        # Update counter
        self._request_counter += 1
        
        return response_data
    
    async def _send_with_retry(
        self,
        request: ServiceRequest,
        url: str,
        headers: Dict[str, str],
        json_data: Optional[str],
    ) -> aiohttp.ClientResponse:
        """
        Send request with retry logic
        
        Args:
            request: Service request
            url: Request URL
            headers: Request headers
            json_data: Request JSON data
            
        Returns:
            aiohttp.ClientResponse: HTTP response
        """
        last_error = None
        
        for attempt in range(request.retry_attempts + 1):
            try:
                async with self._session.request(
                    method=request.method,
                    url=url,
                    headers=headers,
                    json=json.loads(json_data) if json_data else None,
                    params=request.params
                ) as response:
                    if response.status >= 400:
                        error_text = await response.text()
                        raise Exception(f"Service returned error {response.status}: {error_text}")
                    return response
                    
            except (aiohttp.ClientError, asyncio.TimeoutError) as e:
                last_error = e
                if attempt < request.retry_attempts:
                    delay = request.retry_delay * (attempt + 1)
                    logger.warning(f"Retry {attempt + 1}/{request.retry_attempts} after {delay}s delay: {e}")
                    await asyncio.sleep(delay)
                else:
                    raise Exception(f"Failed after {request.retry_attempts} attempts: {e}")
    
    async def _get_service_instance(self, service_name: str) -> Optional[ServiceInstance]:
        """
        Get service instance from registry
        
        Args:
            service_name: Name of service
            
        Returns:
            Optional[ServiceInstance]: Service instance
        """
        # TODO: Integrate with ServiceRegistry
        # This would query the registry to get available service instances
        logger.debug(f"Getting instance for service {service_name}")
        
        return None
    
    def _generate_cache_key(self, request: ServiceRequest) -> str:
        """Generate cache key for request"""
        key_str = f"{request.service_name}_{request.endpoint}_{json.dumps(request.data, sort_keys=True)}"
        return hashlib.md5(key_str.encode()).hexdigest()
    
    def _get_from_cache(self, cache_key: str) -> Optional[ServiceResponse]:
        """Get response from cache"""
        if cache_key in self._request_cache:
            cached_data, timestamp = self._request_cache[cache_key]
            if datetime.now() - timestamp < timedelta(seconds=self._cache_ttl):
                return cached_data
            else:
                del self._request_cache[cache_key]
        
        return None
    
    def _save_to_cache(
        self,
        cache_key: str,
        result: ServiceResponse,
        ttl: int
    ):
        """Save response to cache"""
        self._request_cache[cache_key] = (result, datetime.now())
        
        # Limit cache size
        if len(self._request_cache) > 1000:
            # Remove oldest entries
            sorted_items = sorted(
                self._request_cache.items(),
                key=lambda x: x[1][1]
            )
            self._request_cache = dict(sorted_items[:500])
    
    def subscribe(self, callback: Callable):
        """Subscribe to request events"""
        if callback not in self._listeners:
            self._listeners.append(callback)
    
    def unsubscribe(self, callback: Callable):
        """Unsubscribe from events"""
        if callback in self._listeners:
            self._listeners.remove(callback)
    
    def _notify_listeners(
        self,
        request: ServiceRequest,
        result: ServiceResponse,
        error: bool = False
    ):
        """Notify listeners of event"""
        for callback in self._listeners:
            try:
                callback(request, result, error)
            except Exception as e:
                logger.error(f"Error in listener callback: {e}")
    
    def get_stats(self) -> Dict[str, Any]:
        """Get integration layer statistics"""
        avg_latency = (
            sum(self._response_times) / len(self._response_times) 
            if self._response_times else 0.0
        )
        
        return {
            "total_requests": self._request_counter,
            "successful_requests": self._request_counter - sum(1 for _ in self._response_times),
            "avg_latency_ms": avg_latency,
            "cache_size": len(self._request_cache),
            "listeners_count": len(self._listeners),
        }
    
    def get_average_latency(self) -> float:
        """Get average response latency"""
        return sum(self._response_times) / len(self._response_times) if self._response_times else 0.0


# Global integration layer instance
integration_layer = IntegrationLayer()


def handle_service_error(f):
    """Decorator for handling service errors"""
    @wraps(f)
    async def wrapper(*args, **kwargs):
        try:
            return await f(*args, **kwargs)
        except Exception as e:
            logger.error(f"Service error in {f.__name__}: {e}")
            return None
    return wrapper
