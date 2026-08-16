"""
Comprehensive error logging middleware for FastAPI application.
Provides centralized error handling, logging, and monitoring.
"""

import logging
import time
import traceback
from datetime import datetime, timezone
from typing import Callable, Dict, Any, Optional
from fastapi import FastAPI, Request, Response, status
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware

from ..core.exceptions import BaseError, ValidationError, NotFoundError, ServerError
from ..core.logging import get_logger, performance_monitor
from ..utils.trace_id import get_trace_id, generate_trace_id

logger = get_logger(__name__)


class ErrorLoggingMiddleware(BaseHTTPMiddleware):
    """
    Middleware for comprehensive error logging and handling.
    
    Features:
    - Request/response logging with performance metrics
    - Exception handling and categorization
    - Error rate monitoring
    - Request tracing
    - Security logging
    """
    
    def __init__(self, app: FastAPI, config: Dict[str, Any] = None):
        super().__init__(app)
        self.config = config or {}
        self.error_counts = {}
        self.request_counts = {}
        self.start_time = time.time()
        
        # Configure logging based on config
        self.log_requests = self.config.get('log_requests', True)
        self.log_responses = self.config.get('log_responses', True)
        self.log_errors = self.config.get('log_errors', True)
        self.log_security = self.config.get('log_security', True)
        self.max_error_details_length = self.config.get('max_error_details_length', 1000)
        
    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        """Process request and handle errors comprehensively."""
        
        # Generate trace ID for this request
        trace_id = get_trace_id()
        request.state.trace_id = trace_id
        
        # Get client information
        client_ip = request.client.host if request.client else "unknown"
        user_agent = request.headers.get('user-agent', 'unknown')
        request_id = f"{trace_id}_{int(time.time())}"
        
        # Log request start
        if self.log_requests:
            await self._log_request_start(
                request_id=request_id,
                method=request.method,
                url=str(request.url),
                client_ip=client_ip,
                user_agent=user_agent,
                trace_id=trace_id,
            )
        
        start_time = time.time()
        
        try:
            # Process the request
            response = await call_next(request)
            
            # Calculate duration
            duration = time.time() - start_time
            
            # Log successful response
            if self.log_responses:
                await self._log_response(
                    request_id=request_id,
                    method=request.method,
                    url=str(request.url),
                    status_code=response.status_code,
                    duration=duration,
                    client_ip=client_ip,
                    trace_id=trace_id,
                )
            
            # Track request counts
            self._track_request(method=request.method, status_code=response.status_code)
            
            # Add trace ID to response headers
            response.headers['X-Trace-ID'] = trace_id
            
            return response
            
        except Exception as e:
            # Calculate duration until error
            duration = time.time() - start_time
            
            # Handle error
            await self._handle_error(
                error=e,
                request=request,
                request_id=request_id,
                duration=duration,
                client_ip=client_ip,
                trace_id=trace_id,
            )
            
            # Return error response
            return await self._create_error_response(e, trace_id)
    
    async def _log_request_start(
        self,
        request_id: str,
        method: str,
        url: str,
        client_ip: str,
        user_agent: str,
        trace_id: str,
    ):
        """Log request start information."""
        
        # Sanitize sensitive headers
        headers = dict(request.headers)
        sensitive_headers = ['authorization', 'cookie', 'set-cookie']
        for header in sensitive_headers:
            if header in headers:
                headers[header] = '***REDACTED***'
        
        log_data = {
            'event': 'request_start',
            'request_id': request_id,
            'method': method,
            'url': url,
            'client_ip': client_ip,
            'user_agent': user_agent,
            'headers': headers,
            'trace_id': trace_id,
            'timestamp': datetime.now(timezone.utc).isoformat(),
        }
        
        # Log with performance monitoring
        performance_monitor.record('request_start', metadata=log_data)
        logger.info(f"Request started: {method} {url} | ID: {request_id} | IP: {client_ip}")
    
    async def _log_response(
        self,
        request_id: str,
        method: str,
        url: str,
        status_code: int,
        duration: float,
        client_ip: str,
        trace_id: str,
    ):
        """Log response information."""
        
        log_data = {
            'event': 'response',
            'request_id': request_id,
            'method': method,
            'url': url,
            'status_code': status_code,
            'duration_ms': round(duration * 1000, 2),
            'client_ip': client_ip,
            'trace_id': trace_id,
            'timestamp': datetime.now(timezone.utc).isoformat(),
        }
        
        # Log with performance monitoring
        performance_monitor.record('response', metadata=log_data)
        
        # Log with appropriate level based on status code
        if status_code >= 500:
            logger.error(f"Server error: {status_code} | {method} {url} | Duration: {duration:.3f}s | IP: {client_ip}")
        elif status_code >= 400:
            logger.warning(f"Client error: {status_code} | {method} {url} | Duration: {duration:.3f}s | IP: {client_ip}")
        else:
            logger.info(f"Success: {status_code} | {method} {url} | Duration: {duration:.3f}s | IP: {client_ip}")
    
    async def _handle_error(
        self,
        error: Exception,
        request: Request,
        request_id: str,
        duration: float,
        client_ip: str,
        trace_id: str,
    ):
        """Handle errors comprehensively."""
        
        # Log the error details
        error_data = {
            'event': 'error',
            'request_id': request_id,
            'error_type': type(error).__name__,
            'error_message': str(error),
            'traceback': traceback.format_exc(),
            'method': request.method,
            'url': str(request.url),
            'duration_ms': round(duration * 1000, 2),
            'client_ip': client_ip,
            'trace_id': trace_id,
            'timestamp': datetime.now(timezone.utc).isoformat(),
        }
        
        # Truncate long error details if needed
        if len(error_data['traceback']) > self.max_error_details_length:
            error_data['traceback'] = error_data['traceback'][:self.max_error_details_length] + '...[TRUNCATED]'
        
        # Track error counts
        self._track_error(error_type=type(error).__name__)
        
        # Log with appropriate level
        if isinstance(error, ServerError):
            logger.error(f"Server error: {error_data['error_type']} | {request.method} {request.url} | IP: {client_ip}", extra=error_data)
        elif isinstance(error, ValidationError):
            logger.warning(f"Validation error: {error_data['error_type']} | {request.method} {request.url} | IP: {client_ip}", extra=error_data)
        elif isinstance(error, (NotFoundError, BaseError)):
            logger.warning(f"Application error: {error_data['error_type']} | {request.method} {request.url} | IP: {client_ip}", extra=error_data)
        else:
            logger.critical(f"Unhandled error: {error_data['error_type']} | {request.method} {request.url} | IP: {client_ip}", extra=error_data)
        
        # Log security-related errors
        if self._is_security_error(error):
            await self._log_security_error(error, request, request_id, trace_id)
        
        # Log to monitoring system if available
        await self._log_to_monitoring(error_data)
    
    def _is_security_error(self, error: Exception) -> bool:
        """Check if error is security-related."""
        security_errors = [
            'AuthenticationException',
            'AuthorizationException',
            'PermissionDeniedError',
            'SecurityError',
            'TokenExpiredError',
            'InvalidTokenError',
            'ForbiddenError',
        ]
        return type(error).__name__ in security_errors
    
    async def _log_security_error(
        self,
        error: Exception,
        request: Request,
        request_id: str,
        trace_id: str,
    ):
        """Log security-related errors separately."""
        
        security_data = {
            'event': 'security_error',
            'request_id': request_id,
            'error_type': type(error).__name__,
            'error_message': str(error),
            'method': request.method,
            'url': str(request.url),
            'client_ip': request.client.host if request.client else 'unknown',
            'user_agent': request.headers.get('user-agent', 'unknown'),
            'trace_id': trace_id,
            'timestamp': datetime.now(timezone.utc).isoformat(),
        }
        
        logger.warning(f"Security error: {type(error).__name__} | {request.method} {request.url} | IP: {request.client.host if request.client else 'unknown'}", extra=security_data)
        
        # Send to security monitoring system if available
        await self._log_to_monitoring(security_data, security=True)
    
    async def _log_to_monitoring(self, error_data: Dict[str, Any], security: bool = False):
        """Log error to monitoring system if available."""
        
        # This would integrate with monitoring systems like:
        # - Sentry
        # - Datadog
        # - Prometheus
        # - ELK Stack
        # - Custom monitoring service
        
        try:
            # TODO: Implement actual monitoring integration
            # For now, just log to console
            if security:
                logger.info(f"Security monitoring: {error_data['event']} | {error_data['error_type']}")
            else:
                logger.info(f"Error monitoring: {error_data['event']} | {error_data['error_type']}")
        except Exception as e:
            logger.warning(f"Failed to log to monitoring system: {str(e)}")
    
    def _track_request(self, method: str, status_code: int):
        """Track request statistics."""
        
        key = f"{method}_{status_code}"
        self.request_counts[key] = self.request_counts.get(key, 0) + 1
        
        # Log rate limiting warnings
        total_requests = sum(self.request_counts.values())
        if total_requests % 1000 == 0:
            logger.info(f"Request count: {total_requests} | Recent errors: {sum(self.error_counts.values())}")
    
    def _track_error(self, error_type: str):
        """Track error statistics."""
        
        self.error_counts[error_type] = self.error_counts.get(error_type, 0) + 1
        
        # Log error rate warnings
        total_errors = sum(self.error_counts.values())
        total_requests = sum(self.request_counts.values())
        
        if total_requests > 0 and total_errors / total_requests > 0.1:  # 10% error rate
            logger.warning(f"High error rate detected: {total_errors}/{total_requests} ({total_errors/total_requests:.1%})")
    
    async def _create_error_response(self, error: Exception, trace_id: str) -> JSONResponse:
        """Create standardized error response."""
        
        # Handle different types of errors
        if isinstance(error, BaseError):
            response_data = {
                'error': error.to_dict(),
                'trace_id': trace_id,
            }
            return JSONResponse(
                status_code=error.status_code if hasattr(error, 'status_code') else status.HTTP_500_INTERNAL_SERVER_ERROR,
                content=response_data,
            )
        elif isinstance(error, ValidationError):
            response_data = {
                'error': {
                    'code': 'VALIDATION_ERROR',
                    'message': str(error),
                    'details': error.details,
                },
                'trace_id': trace_id,
            }
            return JSONResponse(
                status_code=status.HTTP_400_BAD_REQUEST,
                content=response_data,
            )
        elif isinstance(error, NotFoundError):
            response_data = {
                'error': {
                    'code': 'NOT_FOUND',
                    'message': str(error),
                },
                'trace_id': trace_id,
            }
            return JSONResponse(
                status_code=status.HTTP_404_NOT_FOUND,
                content=response_data,
            )
        else:
            # Generic server error
            response_data = {
                'error': {
                    'code': 'INTERNAL_SERVER_ERROR',
                    'message': 'Internal server error',
                },
                'trace_id': trace_id,
            }
            return JSONResponse(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                content=response_data,
            )
    
    def get_error_statistics(self) -> Dict[str, Any]:
        """Get error statistics for monitoring."""
        
        total_errors = sum(self.error_counts.values())
        total_requests = sum(self.request_counts.values())
        
        return {
            'total_requests': total_requests,
            'total_errors': total_errors,
            'error_rate': total_errors / total_requests if total_requests > 0 else 0,
            'error_counts': self.error_counts,
            'uptime_seconds': time.time() - self.start_time,
            'top_errors': sorted(self.error_counts.items(), key=lambda x: x[1], reverse=True)[:10],
        }


class SecurityAuditMiddleware(BaseHTTPMiddleware):
    """
    Middleware for security audit logging.
    
    Features:
    - Security event logging
    - Suspicious activity detection
    - Access pattern analysis
    - Authentication/authorization logging
    """
    
    def __init__(self, app: FastAPI, config: Dict[str, Any] = None):
        super().__init__(app)
        self.config = config or {}
        self.failed_attempts = {}
        self.blocked_ips = set()
        
        # Configuration
        self.max_attempts = self.config.get('max_failed_attempts', 5)
        self.block_duration = self.config.get('block_duration', 300)  # 5 minutes
        self.log_all_requests = self.config.get('log_all_requests', False)
        
    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        """Process request with security checks."""
        
        client_ip = request.client.host if request.client else "unknown"
        request_id = f"security_{int(time.time())}_{hash(client_ip) % 10000}"
        
        # Check if IP is blocked
        if client_ip in self.blocked_ips:
            await self._log_security_event(
                event='blocked_ip',
                request_id=request_id,
                client_ip=client_ip,
                request=request,
                reason='IP blocked due to suspicious activity',
            )
            
            return JSONResponse(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                content={'error': 'IP temporarily blocked due to suspicious activity'},
            )
        
        # Check for authentication failures
        auth_header = request.headers.get('authorization', '')
        if auth_header and self._is_suspicious_auth(auth_header):
            await self._track_failed_attempt(client_ip, auth_failure=True)
        
        try:
            response = await call_next(request)
            
            # Log all requests if enabled
            if self.log_all_requests:
                await self._log_security_event(
                    event='request',
                    request_id=request_id,
                    client_ip=client_ip,
                    request=request,
                    response=response,
                )
            
            return response
            
        except Exception as e:
            # Track failed attempts
            await self._track_failed_attempt(client_ip, error=e)
            raise
    
    def _is_suspicious_auth(self, auth_header: str) -> bool:
        """Check for suspicious authentication patterns."""
        
        # TODO: Implement more sophisticated detection
        # For now, check for common attack patterns
        suspicious_patterns = [
            'admin',
            'password',
            'root',
            'test',
            'debug',
        ]
        
        return any(pattern in auth_header.lower() for pattern in suspicious_patterns)
    
    async def _track_failed_attempt(self, client_ip: str, error: Exception = None, auth_failure: bool = False):
        """Track failed authentication or request attempts."""
        
        key = f"{client_ip}_{auth_failure}"
        self.failed_attempts[key] = self.failed_attempts.get(key, 0) + 1
        
        # Check if threshold is exceeded
        if self.failed_attempts[key] >= self.max_attempts:
            self.blocked_ips.add(client_ip)
            logger.warning(f"IP blocked: {client_ip} (failed attempts: {self.failed_attempts[key]})")
            
            # Schedule unblocking
            # TODO: Implement scheduled unblocking
            await self._schedule_ip_unblocking(client_ip)
    
    async def _schedule_ip_unblocking(self, client_ip: str):
        """Schedule IP unblocking after block duration."""
        
        # TODO: Implement actual scheduling mechanism
        logger.info(f"Scheduled unblocking for IP: {client_ip} in {self.block_duration} seconds")
    
    async def _log_security_event(
        self,
        event: str,
        request_id: str,
        client_ip: str,
        request: Request,
        response: Response = None,
        reason: str = None,
        error: Exception = None,
    ):
        """Log security-related events."""
        
        security_data = {
            'event': event,
            'request_id': request_id,
            'client_ip': client_ip,
            'method': request.method,
            'url': str(request.url),
            'user_agent': request.headers.get('user-agent', 'unknown'),
            'timestamp': datetime.now(timezone.utc).isoformat(),
            'reason': reason,
        }
        
        if response:
            security_data['status_code'] = response.status_code
        
        if error:
            security_data['error'] = str(error)
            security_data['error_type'] = type(error).__name__
        
        logger.info(f"Security event: {event} | IP: {client_ip} | {request.method} {request.url}", extra=security_data)
    
    def get_security_statistics(self) -> Dict[str, Any]:
        """Get security statistics."""
        
        return {
            'failed_attempts': self.failed_attempts,
            'blocked_ips': list(self.blocked_ips),
            'total_blocked': len(self.blocked_ips),
            'config': {
                'max_attempts': self.max_attempts,
                'block_duration': self.block_duration,
            },
        }


# Factory functions for middleware configuration
def create_error_logging_middleware(app: FastAPI, config: Dict[str, Any] = None) -> ErrorLoggingMiddleware:
    """Create and configure error logging middleware."""
    
    default_config = {
        'log_requests': True,
        'log_responses': True,
        'log_errors': True,
        'log_security': True,
        'max_error_details_length': 1000,
    }
    
    if config:
        default_config.update(config)
    
    return ErrorLoggingMiddleware(app, default_config)


def create_security_audit_middleware(app: FastAPI, config: Dict[str, Any] = None) -> SecurityAuditMiddleware:
    """Create and configure security audit middleware."""
    
    default_config = {
        'max_failed_attempts': 5,
        'block_duration': 300,
        'log_all_requests': False,
    }
    
    if config:
        default_config.update(config)
    
    return SecurityAuditMiddleware(app, default_config)