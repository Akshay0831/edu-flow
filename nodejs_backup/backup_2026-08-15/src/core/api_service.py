"""
Enhanced API service layer with comprehensive error handling, caching, and optimization.

This module provides:
- HTTP client with retry mechanisms
- Response caching and optimization
- Rate limiting and throttling
- Request/response transformation
- Circuit breaker pattern for external services
- Metrics and monitoring
"""

import asyncio
import time
import json
import hashlib
from typing import Dict, Any, Optional, List, Union, Callable, TypeVar
from datetime import datetime, timedelta
from dataclasses import dataclass, field
from enum import Enum
import logging
from functools import wraps
import aiohttp
from aiohttp import ClientSession, ClientTimeout, ClientError
import async_timeout

from src.core.exceptions import ExternalServiceError, RateLimitError, ConfigurationError
from src.core.cache_abstraction import CacheManager, CacheConfig, CacheBackend
from src.core.error_handling import retry_handler, handle_external_service_errors
from src.core.service_container import get_service_container
from src.core.logging import get_logger

logger = get_logger(__name__)

T = TypeVar('T')


class APIMethod(Enum):
    """HTTP methods."""
    GET = "GET"
    POST = "POST"
    PUT = "PUT"
    DELETE = "DELETE"
    PATCH = "PATCH"
    HEAD = "HEAD"
    OPTIONS = "OPTIONS"


@dataclass
class APIRequest:
    """API request configuration."""
    method: APIMethod
    url: str
    headers: Dict[str, str] = field(default_factory=dict)
    params: Dict[str, Any] = field(default_factory=dict)
    data: Any = None
    json: Dict[str, Any] = None
    timeout: int = 30
    retries: int = 3
    retry_delay: float = 1.0
    cache_key: Optional[str] = None
    cache_ttl: int = 3600
    rate_limit: Optional[int] = None
    circuit_breaker: bool = True
    
    def __post_init__(self):
        if self.json is not None and self.data is not None:
            logger.warning("Both 'data' and 'json' provided, 'json' will be used")


@dataclass
class APIResponse:
    """API response wrapper."""
    status_code: int
    headers: Dict[str, str]
    data: Any
    raw_response: Optional[str] = None
    request_time: float = 0
    cache_hit: bool = False
    error: Optional[str] = None
    
    @property
    def success(self) -> bool:
        """Check if response was successful."""
        return 200 <= self.status_code < 300
    
    @property
    def json_data(self) -> Dict[str, Any]:
        """Get response data as JSON."""
        if isinstance(self.data, dict):
            return self.data
        return {}


class APIClient:
    """Enhanced HTTP client with caching, retry, and optimization."""
    
    def __init__(self, base_url: str = "", timeout: int = 30, 
                 cache_manager: CacheManager = None, 
                 max_concurrent_requests: int = 10):
        self.base_url = base_url.rstrip("/")
        self.timeout = timeout
        self.max_concurrent_requests = max_concurrent_requests
        self._session: Optional[ClientSession] = None
        self._semaphore = asyncio.Semaphore(max_concurrent_requests)
        self._cache_manager = cache_manager
        self._rate_limiter = {}
        self._request_history = []
        self._metrics = {
            'total_requests': 0,
            'successful_requests': 0,
            'failed_requests': 0,
            'cache_hits': 0,
            'cache_misses': 0,
            'retries': 0,
            'average_response_time': 0.0
        }
    
    async def initialize(self):
        """Initialize the HTTP client."""
        if not self._session:
            timeout = ClientTimeout(total=self.timeout)
            self._session = ClientSession(timeout=timeout)
            logger.info("HTTP client initialized")
    
    async def close(self):
        """Close the HTTP client."""
        if self._session:
            await self._session.close()
            self._session = None
            logger.info("HTTP client closed")
    
    async def __aenter__(self):
        await self.initialize()
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        await self.close()
    
    @handle_external_service_errors
    async def request(self, api_request: APIRequest) -> APIResponse:
        """Execute an API request with full error handling and optimization."""
        start_time = time.time()
        self._metrics['total_requests'] += 1
        
        try:
            # Check cache first
            if self._cache_manager and api_request.cache_key:
                cached_response = await self._cache_manager.get(api_request.cache_key)
                if cached_response:
                    self._metrics['cache_hits'] += 1
                    response = APIResponse(
                        status_code=200,
                        headers={'X-Cache': 'HIT'},
                        data=cached_response,
                        request_time=time.time() - start_time,
                        cache_hit=True
                    )
                    self._update_metrics(response)
                    return response
            
            # Check rate limit
            if api_request.rate_limit:
                await self._check_rate_limit(api_request.rate_limit)
            
            # Execute request with retry
            response = await self._execute_with_retry(api_request)
            
            # Cache successful responses
            if self._cache_manager and api_request.cache_key and response.success:
                await self._cache_manager.set(api_request.cache_key, response.json_data, api_request.cache_ttl)
                self._metrics['cache_misses'] += 1
            
            self._update_metrics(response)
            return response
            
        except Exception as e:
            self._metrics['failed_requests'] += 1
            logger.error(f"API request failed: {str(e)}")
            raise ExternalServiceError(f"API request failed: {str(e)}")
    
    async def _execute_with_retry(self, api_request: APIRequest) -> APIResponse:
        """Execute request with retry logic."""
        last_exception = None
        
        for attempt in range(api_request.retries + 1):
            try:
                async with self._semaphore:
                    response = await self._make_request(api_request)
                    return response
                    
            except (aiohttp.ClientError, asyncio.TimeoutError) as e:
                last_exception = e
                if attempt == api_request.retries:
                    break
                
                delay = api_request.retry_delay * (2 ** attempt)  # Exponential backoff
                logger.warning(f"Attempt {attempt + 1} failed, retrying in {delay}s: {str(e)}")
                await asyncio.sleep(delay)
                
                # Update request with new retry parameters
                api_request.retries = api_request.retries - attempt - 1
        
        raise ExternalServiceError(f"All retry attempts failed: {str(last_exception)}")
    
    async def _make_request(self, api_request: APIRequest) -> APIResponse:
        """Make a single HTTP request."""
        full_url = f"{self.base_url}/{api_request.url.lstrip('/')}"
        
        headers = {
            'Content-Type': 'application/json',
            'User-Agent': 'EduFlow-API-Client/1.0',
            **api_request.headers
        }
        
        # Prepare request data
        request_kwargs = {
            'headers': headers,
            'params': api_request.params,
            'timeout': ClientTimeout(total=api_request.timeout)
        }
        
        if api_request.json is not None:
            request_kwargs['json'] = api_request.json
        elif api_request.data is not None:
            request_kwargs['data'] = api_request.data
        
        # Execute request
        async with self._session.request(
            method=api_request.method.value,
            url=full_url,
            **request_kwargs
        ) as response:
            request_time = time.time() - api_request.timeout
            
            # Read response data
            try:
                if response.content_type == 'application/json':
                    data = await response.json()
                else:
                    data = await response.text()
            except Exception as e:
                data = await response.text()
                logger.warning(f"Failed to parse response as JSON: {e}")
            
            api_response = APIResponse(
                status_code=response.status,
                headers=dict(response.headers),
                data=data,
                raw_response=str(response),
                request_time=request_time
            )
            
            # Log request
            self._log_request(api_request, api_response)
            
            return api_response
    
    async def _check_rate_limit(self, limit: int):
        """Check and enforce rate limiting."""
        now = time.time()
        window_start = now - 60  # 1-minute window
        
        # Clean old entries
        self._rate_limiter = {
            key: timestamps for key, timestamps in self._rate_limiter.items()
            if timestamps[-1] > window_start
        }
        
        # Count requests in current window
        total_requests = sum(len(timestamps) for timestamps in self._rate_limiter.values())
        
        if total_requests >= limit:
            sleep_time = 60 - (now - window_start)
            raise RateLimitError(f"Rate limit exceeded. Try again in {sleep_time:.1f} seconds")
    
    def _log_request(self, api_request: APIRequest, response: APIResponse):
        """Log the request and response."""
        log_data = {
            'method': api_request.method.value,
            'url': api_request.url,
            'status_code': response.status_code,
            'response_time': response.request_time,
            'cache_hit': response.cache_hit,
            'timestamp': datetime.now().isoformat()
        }
        
        if response.success:
            logger.info(f"API request successful: {log_data}")
        else:
            logger.warning(f"API request failed: {log_data}")
        
        # Store in history
        self._request_history.append(log_data)
        
        # Keep only last 1000 requests
        if len(self._request_history) > 1000:
            self._request_history = self._request_history[-1000:]
    
    def _update_metrics(self, response: APIResponse):
        """Update metrics for the response."""
        if response.success:
            self._metrics['successful_requests'] += 1
        else:
            self._metrics['failed_requests'] += 1
        
        # Update average response time
        current_avg = self._metrics['average_response_time']
        total_requests = self._metrics['total_requests']
        self._metrics['average_response_time'] = (
            (current_avg * (total_requests - 1) + response.request_time) / total_requests
        )
    
    def get_metrics(self) -> Dict[str, Any]:
        """Get client metrics."""
        return self._metrics.copy()
    
    def get_request_history(self, limit: int = 100) -> List[Dict[str, Any]]:
        """Get request history."""
        return self._request_history[-limit:]
    
    # Convenience methods
    async def get(self, url: str, params: Dict[str, Any] = None, 
                  headers: Dict[str, str] = None, **kwargs) -> APIResponse:
        """GET request."""
        request = APIRequest(
            method=APIMethod.GET,
            url=url,
            params=params,
            headers=headers,
            **kwargs
        )
        return await self.request(request)
    
    async def post(self, url: str, data: Any = None, json: Dict[str, Any] = None,
                   headers: Dict[str, str] = None, **kwargs) -> APIResponse:
        """POST request."""
        request = APIRequest(
            method=APIMethod.POST,
            url=url,
            data=data,
            json=json,
            headers=headers,
            **kwargs
        )
        return await self.request(request)
    
    async def put(self, url: str, data: Any = None, json: Dict[str, Any] = None,
                  headers: Dict[str, str] = None, **kwargs) -> APIResponse:
        """PUT request."""
        request = APIRequest(
            method=APIMethod.PUT,
            url=url,
            data=data,
            json=json,
            headers=headers,
            **kwargs
        )
        return await self.request(request)
    
    async def delete(self, url: str, **kwargs) -> APIResponse:
        """DELETE request."""
        request = APIRequest(
            method=APIMethod.DELETE,
            url=url,
            **kwargs
        )
        return await self.request(request)
    
    async def patch(self, url: str, data: Any = None, json: Dict[str, Any] = None,
                   headers: Dict[str, str] = None, **kwargs) -> APIResponse:
        """PATCH request."""
        request = APIRequest(
            method=APIMethod.PATCH,
            url=url,
            data=data,
            json=json,
            headers=headers,
            **kwargs
        )
        return await self.request(request)


class APIService:
    """High-level API service with business logic and optimization."""
    
    def __init__(self, api_client: APIClient):
        self.client = api_client
        self._services = {}
        self._initialized = False
    
    async def initialize(self):
        """Initialize the API service."""
        await self.client.initialize()
        self._initialized = True
        logger.info("API service initialized")
    
    async def close(self):
        """Close the API service."""
        await self.client.close()
        self._initialized = False
        logger.info("API service closed")
    
    def register_service(self, name: str, base_url: str, default_headers: Dict[str, str] = None):
        """Register a service with the API client."""
        service_client = APIClient(
            base_url=base_url,
            timeout=30,
            cache_manager=self.client._cache_manager
        )
        self._services[name] = service_client
        logger.info(f"Registered service: {name} -> {base_url}")
    
    def get_service_client(self, name: str) -> APIClient:
        """Get a service client by name."""
        if name not in self._services:
            raise ConfigurationError(f"Service '{name}' not registered")
        return self._services[name]
    
    async def health_check(self) -> Dict[str, Any]:
        """Perform health check on all services."""
        health_status = {
            'initialized': self._initialized,
            'services': {}
        }
        
        for name, service_client in self._services.items():
            try:
                response = await service_client.get('/health', timeout=10)
                health_status['services'][name] = {
                    'status': 'healthy' if response.success else 'unhealthy',
                    'response_time': response.request_time,
                    'status_code': response.status_code
                }
            except Exception as e:
                health_status['services'][name] = {
                    'status': 'error',
                    'error': str(e)
                }
        
        return health_status
    
    # Service registration convenience methods
    def register_database_service(self, base_url: str, **kwargs):
        """Register database service."""
        self.register_service('database', base_url, **kwargs)
    
    def register_auth_service(self, base_url: str, **kwargs):
        """Register authentication service."""
        self.register_service('auth', base_url, **kwargs)
    
    def register_ai_service(self, base_url: str, **kwargs):
        """Register AI service."""
        self.register_service('ai', base_url, **kwargs)
    
    def register_notification_service(self, base_url: str, **kwargs):
        """Register notification service."""
        self.register_service('notification', base_url, **kwargs)


# Global API client instance
_api_client = None
_api_service = None


def get_api_client() -> APIClient:
    """Get the global API client instance."""
    global _api_client
    if _api_client is None:
        _api_client = APIClient()
    return _api_client


def get_api_service() -> APIService:
    """Get the global API service instance."""
    global _api_service
    if _api_service is None:
        _api_service = APIService(get_api_client())
    return _api_service


async def initialize_api_client(config: Dict[str, Any] = None):
    """Initialize the global API client with configuration."""
    global _api_client, _api_service
    
    _api_client = APIClient(
        base_url=config.get('base_url', ''),
        timeout=config.get('timeout', 30),
        max_concurrent_requests=config.get('max_concurrent_requests', 10)
    )
    
    # Initialize cache if available
    container = get_service_container()
    if container.get_service('cache_manager'):
        _api_client._cache_manager = container.get_service('cache_manager')
    
    _api_service = APIService(_api_client)
    await _api_client.initialize()
    await _api_service.initialize()
    
    # Register services
    for service_name, service_config in config.get('services', {}).items():
        _api_service.register_service(
            service_name,
            service_config['base_url'],
            service_config.get('headers', {})
        )
    
    return _api_client, _api_service


# Decorators for API caching and optimization
def api_cache(cache_key: str = None, cache_ttl: int = 3600):
    """Decorator for API response caching."""
    def decorator(func):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            client = get_api_client()
            
            # Generate cache key
            if cache_key:
                key = cache_key.format(**kwargs)
            else:
                key = f"{func.__name__}:{hash(str(args) + str(kwargs))}"
            
            # Check cache first
            if client._cache_manager:
                cached_data = await client._cache_manager.get(key)
                if cached_data is not None:
                    logger.debug(f"Cache hit for {key}")
                    return cached_data
            
            # Execute function
            result = await func(*args, **kwargs)
            
            # Cache result
            if client._cache_manager and result is not None:
                await client._cache_manager.set(key, result, cache_ttl)
                logger.debug(f"Cached result for {key}")
            
            return result
        return wrapper
    return decorator


def api_retry(max_retries: int = 3, base_delay: float = 1.0):
    """Decorator for API request retry."""
    def decorator(func):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            for attempt in range(max_retries):
                try:
                    return await func(*args, **kwargs)
                except (ExternalServiceError, aiohttp.ClientError) as e:
                    if attempt == max_retries - 1:
                        raise
                    delay = base_delay * (2 ** attempt)
                    logger.warning(f"Attempt {attempt + 1} failed, retrying in {delay}s: {str(e)}")
                    await asyncio.sleep(delay)
        return wrapper
    return decorator


def api_rate_limit(limit: int = 100):
    """Decorator for API rate limiting."""
    def decorator(func):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            client = get_api_client()
            
            # Check rate limit
            if limit:
                await client._check_rate_limit(limit)
            
            return await func(*args, **kwargs)
        return wrapper
    return decorator