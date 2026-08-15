"""
Enhanced error handling system with comprehensive error management and recovery strategies.

This module provides:
- Global error handlers
- Error recovery mechanisms
- Detailed error logging
- Consistent error responses
- Circuit breaker pattern for external services
- Retry mechanisms
"""

import asyncio
import logging
import time
from typing import Dict, Any, Optional, Callable, Type, Union, List
from functools import wraps
from contextlib import asynccontextmanager
from datetime import datetime, timezone
import traceback

from fastapi import FastAPI, Request, HTTPException, status
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware
from sqlalchemy.exc import SQLAlchemyError

from src.core.exceptions import (
    BaseError, ValidationError, NotFoundError, AuthenticationError,
    AuthorizationError, ForbiddenError, ConflictError, DatabaseError,
    ExternalServiceError, RateLimitError, ConfigurationError
)
from src.core.logging import get_logger

logger = get_logger(__name__)


class ErrorHandlerMiddleware(BaseHTTPMiddleware):
    """
    Global error handler middleware that catches and formats all exceptions consistently.
    """
    
    async def dispatch(self, request: Request, call_next):
        try:
            response = await call_next(request)
            return response
        except Exception as e:
            return await self.handle_exception(request, e)
    
    async def handle_exception(self, request: Request, error: Exception) -> JSONResponse:
        """
        Handle different types of exceptions and return appropriate responses.
        """
        start_time = getattr(request.state, 'request_start_time', time.time())
        execution_time = time.time() - start_time
        
        if isinstance(error, BaseError):
            logger.error(
                f"Business error occurred: {error.error_code} - {error.message}",
                extra={
                    'error_code': error.error_code,
                    'error_details': error.details,
                    'execution_time': execution_time,
                    'path': request.url.path,
                    'method': request.method,
                    'user_agent': request.headers.get('user-agent'),
                }
            )
            return JSONResponse(
                status_code=self._get_http_status(error),
                content=error.to_dict()
            )
        
        elif isinstance(error, HTTPException):
            logger.warning(
                f"HTTP exception occurred: {error.status_code} - {error.detail}",
                extra={
                    'http_status': error.status_code,
                    'error_detail': error.detail,
                    'execution_time': execution_time,
                    'path': request.url.path,
                    'method': request.method,
                }
            )
            return JSONResponse(
                status_code=error.status_code,
                content={
                    'error_code': 'HTTP_ERROR',
                    'message': error.detail,
                    'timestamp': datetime.now(timezone.utc).isoformat(),
                }
            )
        
        elif isinstance(error, SQLAlchemyError):
            error_id = f"db_error_{int(time.time())}"
            logger.error(
                f"Database error {error_id}: {str(error)}",
                extra={
                    'error_id': error_id,
                    'error_type': type(error).__name__,
                    'execution_time': execution_time,
                    'path': request.url.path,
                    'method': request.method,
                    'traceback': traceback.format_exc(),
                }
            )
            return JSONResponse(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                content={
                    'error_code': 'DATABASE_ERROR',
                    'message': 'A database error occurred. Please try again later.',
                    'error_id': error_id,
                    'timestamp': datetime.now(timezone.utc).isoformat(),
                }
            )
        
        else:
            error_id = f"system_error_{int(time.time())}"
            logger.critical(
                f"Unhandled system error {error_id}: {str(error)}",
                extra={
                    'error_id': error_id,
                    'error_type': type(error).__name__,
                    'execution_time': execution_time,
                    'path': request.url.path,
                    'method': request.method,
                    'traceback': traceback.format_exc(),
                }
            )
            return JSONResponse(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                content={
                    'error_code': 'SYSTEM_ERROR',
                    'message': 'An unexpected error occurred. Please try again later.',
                    'error_id': error_id,
                    'timestamp': datetime.now(timezone.utc).isoformat(),
                }
            )
    
    def _get_http_status(self, error: BaseError) -> int:
        """Convert error type to HTTP status code."""
        status_mapping = {
            ValidationError: status.HTTP_422_UNPROCESSABLE_ENTITY,
            NotFoundError: status.HTTP_404_NOT_FOUND,
            AuthenticationError: status.HTTP_401_UNAUTHORIZED,
            AuthorizationError: status.HTTP_403_FORBIDDEN,
            ForbiddenError: status.HTTP_403_FORBIDDEN,
            ConflictError: status.HTTP_409_CONFLICT,
            RateLimitError: status.HTTP_429_TOO_MANY_REQUESTS,
            DatabaseError: status.HTTP_500_INTERNAL_SERVER_ERROR,
            ExternalServiceError: status.HTTP_503_SERVICE_UNAVAILABLE,
            ConfigurationError: status.HTTP_500_INTERNAL_SERVER_ERROR,
        }
        return status_mapping.get(type(error), status.HTTP_500_INTERNAL_SERVER_ERROR)


class CircuitBreaker:
    """
    Circuit breaker pattern for handling external service failures.
    """
    
    def __init__(self, 
                 failure_threshold: int = 5, 
                 recovery_timeout: int = 60,
                 expected_exception: Type[Exception] = Exception):
        self.failure_threshold = failure_threshold
        self.recovery_timeout = recovery_timeout
        self.expected_exception = expected_exception
        self.failure_count = 0
        self.last_failure_time = 0
        self.state = 'CLOSED'  # CLOSED, OPEN, HALF_OPEN
    
    def call(self, func: Callable):
        """Decorator for circuit breaker pattern."""
        @wraps(func)
        async def wrapper(*args, **kwargs):
            if self.state == 'OPEN':
                if self._should_attempt_reset():
                    self.state = 'HALF_OPEN'
                else:
                    raise ExternalServiceError(
                        message="Service temporarily unavailable (circuit breaker open)",
                        details={'service': func.__name__, 'state': self.state}
                    )
            
            try:
                result = await func(*args, **kwargs)
                self._on_success()
                return result
            except self.expected_exception as e:
                self._on_failure()
                raise e
        
        return wrapper
    
    def _should_attempt_reset(self) -> bool:
        """Check if circuit breaker should attempt reset."""
        return time.time() - self.last_failure_time > self.recovery_timeout
    
    def _on_success(self):
        """Handle successful call."""
        self.failure_count = 0
        self.state = 'CLOSED'
        logger.info(f"Circuit breaker for service closed after success")
    
    def _on_failure(self):
        """Handle failed call."""
        self.failure_count += 1
        self.last_failure_time = time.time()
        
        if self.failure_count >= self.failure_threshold:
            self.state = 'OPEN'
            logger.warning(
                f"Circuit breaker opened for service after {self.failure_count} failures"
            )


class RetryHandler:
    """
    Retry mechanism for handling transient failures.
    """
    
    def __init__(self, 
                 max_attempts: int = 3,
                 base_delay: float = 1.0,
                 max_delay: float = 60.0,
                 exponential_base: float = 2.0,
                 exceptions: List[Type[Exception]] = None):
        self.max_attempts = max_attempts
        self.base_delay = base_delay
        self.max_delay = max_delay
        self.exponential_base = exponential_base
        self.exceptions = exceptions or [Exception]
    
    async def execute(self, func: Callable, *args, **kwargs) -> Any:
        """Execute function with retry logic."""
        last_exception = None
        
        for attempt in range(self.max_attempts):
            try:
                return await func(*args, **kwargs)
            except tuple(self.exceptions) as e:
                last_exception = e
                if attempt == self.max_attempts - 1:
                    break
                
                delay = min(
                    self.base_delay * (self.exponential_base ** attempt),
                    self.max_delay
                )
                
                logger.warning(
                    f"Attempt {attempt + 1} failed, retrying in {delay}s: {str(e)}"
                )
                await asyncio.sleep(delay)
        
        raise last_exception


# Global circuit breakers for different services
database_circuit_breaker = CircuitBreaker(
    failure_threshold=3,
    recovery_timeout=30,
    expected_exception=DatabaseError
)

external_service_circuit_breaker = CircuitBreaker(
    failure_threshold=5,
    recovery_timeout=60,
    expected_exception=ExternalServiceError
)


# Global retry handler
retry_handler = RetryHandler(
    max_attempts=3,
    base_delay=1.0,
    max_delay=30.0,
    exceptions=[ConnectionError, TimeoutError, ExternalServiceError]
)


class HealthChecker:
    """
    Health check service for monitoring system components.
    """
    
    def __init__(self):
        self._checks = {}
        self._last_results = {}
    
    def register_check(self, name: str, check_func: Callable):
        """Register a health check function."""
        self._checks[name] = check_func
    
    async def run_checks(self) -> Dict[str, Any]:
        """Run all registered health checks."""
        results = {}
        
        for name, check_func in self._checks.items():
            try:
                start_time = time.time()
                result = await check_func()
                duration = time.time() - start_time
                
                results[name] = {
                    'status': 'healthy' if result else 'unhealthy',
                    'duration': duration,
                    'timestamp': datetime.now(timezone.utc).isoformat(),
                }
                self._last_results[name] = results[name]
            except Exception as e:
                logger.error(f"Health check failed for {name}: {str(e)}")
                results[name] = {
                    'status': 'error',
                    'error': str(e),
                    'timestamp': datetime.now(timezone.utc).isoformat(),
                }
                self._last_results[name] = results[name]
        
        return results


# Global health checker
health_checker = HealthChecker()


def register_health_checks(app: FastAPI):
    """Register health checks with the FastAPI application."""
    
    @app.get("/health")
    async def health_check():
        """Health check endpoint."""
        results = await health_checker.run_checks()
        
        overall_status = 'healthy'
        for result in results.values():
            if result['status'] != 'healthy':
                overall_status = 'unhealthy'
                break
        
        return {
            'status': overall_status,
            'checks': results,
            'timestamp': datetime.now(timezone.utc).isoformat(),
        }
    
    @app.get("/health/detailed")
    async def detailed_health_check():
        """Detailed health check endpoint with cached results."""
        return {
            'current_checks': await health_checker.run_checks(),
            'last_results': health_checker._last_results,
            'timestamp': datetime.now(timezone.utc).isoformat(),
        }


def setup_error_handling(app: FastAPI):
    """Setup comprehensive error handling for the application."""
    
    # Add error handler middleware
    app.add_middleware(ErrorHandlerMiddleware)
    
    # Register health checks
    register_health_checks(app)
    
    # Add request timing middleware
    @app.middleware("http")
    async def add_timing_middleware(request: Request, call_next):
        request.state.request_start_time = time.time()
        response = await call_next(request)
        execution_time = time.time() - request.state.request_start_time
        
        response.headers["X-Execution-Time"] = f"{execution_time:.3f}s"
        return response
    
    logger.info("Error handling middleware setup completed")


# Decorators for common error handling patterns
def handle_database_errors(func):
    """Decorator to handle database errors with circuit breaker."""
    @wraps(func)
    async def wrapper(*args, **kwargs):
        return await database_circuit_breaker.call(func)(*args, **kwargs)
    return wrapper


def handle_external_service_errors(func):
    """Decorator to handle external service errors with circuit breaker and retry."""
    @wraps(func)
    async def wrapper(*args, **kwargs):
        return await retry_handler.execute(
            external_service_circuit_breaker.call(func),
            *args, **kwargs
        )
    return wrapper


def log_errors(func):
    """Decorator to log errors with additional context."""
    @wraps(func)
    async def wrapper(*args, **kwargs):
        try:
            return await func(*args, **kwargs)
        except Exception as e:
            logger.error(
                f"Error in {func.__name__}: {str(e)}",
                extra={
                    'function': func.__name__,
                    'args': args,
                    'kwargs': kwargs,
                    'error_type': type(e).__name__,
                }
            )
            raise
    return wrapper