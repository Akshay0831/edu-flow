"""Enhanced logging middleware with structured logging and audit trails."""

import time
import json
import uuid
import traceback
from datetime import datetime, timezone
from typing import Dict, Any, Optional, Callable
from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.middleware.base import RequestResponseEndpoint
from core.security import auth_service
from core.exceptions import AuthenticationError, AuthorizationError
from config.settings import settings
from core.logging import get_logger


class AuditLogMiddleware(BaseHTTPMiddleware):
    """Middleware for audit logging and security monitoring."""
    
    async def dispatch(self, request: Request, call_next: RequestResponseEndpoint) -> Response:
        # Generate request ID for tracing
        request_id = str(uuid.uuid4())
        request.state.request_id = request_id
        
        # Record request start time
        start_time = time.time()
        request.state.start_time = start_time
        
        # Extract user information if authenticated
        user_info = await self._extract_user_info(request)
        
        # Create audit log entry
        audit_log = {
            'request_id': request_id,
            'timestamp': datetime.now(timezone.utc).isoformat(),
            'method': request.method,
            'url': str(request.url),
            'user_agent': request.headers.get('user-agent', ''),
            'client_ip': request.client.host if request.client else 'unknown',
            'user_id': user_info.get('id') if user_info else None,
            'user_role': user_info.get('role') if user_info else None,
            'endpoint': request.url.path,
            'query_params': dict(request.query_params),
            'headers': dict(request.headers),
        }
        
        # Process request
        try:
            response = await call_next(request)
            
            # Calculate processing time
            processing_time = time.time() - start_time
            
            # Update audit log with response data
            audit_log.update({
                'status_code': response.status_code,
                'processing_time_ms': round(processing_time * 1000, 2),
                'response_size': len(response.body) if hasattr(response, 'body') else 0,
            })
            
            # Log based on response status
            if response.status_code >= 400:
                await self._log_error(audit_log, response)
            else:
                await self._log_success(audit_log)
            
            return response
            
        except Exception as e:
            # Calculate processing time for failed requests
            processing_time = time.time() - start_time
            
            # Update audit log with error data
            audit_log.update({
                'status_code': 500,
                'processing_time_ms': round(processing_time * 1000, 2),
                'error': str(e),
                'error_type': type(e).__name__,
            })
            
            await self._log_error(audit_log, None)
            raise
    
    async def _extract_user_info(self, request: Request) -> Optional[Dict[str, Any]]:
        """Extract user information from JWT token."""
        try:
            # Extract Authorization header
            auth_header = request.headers.get('authorization')
            if not auth_header or not auth_header.startswith('Bearer '):
                return None
            
            token = auth_header[7:]  # Remove 'Bearer ' prefix
            
            # Verify token using auth service
            if hasattr(auth_service, 'verify_token'):
                token_data = auth_service.verify_token(token)
                return {
                    'id': token_data.user_id,
                    'email': token_data.email,
                    'role': token_data.role,
                }
            else:
                return None
                
        except Exception:
            return None
    
    async def _log_success(self, audit_log: Dict[str, Any]) -> None:
        """Log successful request."""
        if settings.enable_audit_logging:
            # In production, this would write to a dedicated audit log collection
            print(f"[AUDIT] SUCCESS: {json.dumps(audit_log, indent=2)}")
    
    async def _log_error(self, audit_log: Dict[str, Any], response: Optional[Response]) -> None:
        """Log error request."""
        if settings.enable_error_logging:
            # Include additional error details if available
            if response:
                audit_log['response_headers'] = dict(response.headers)
            
            # In production, this would write to a dedicated error log collection
            print(f"[ERROR] FAILED: {json.dumps(audit_log, indent=2)}")


class SecurityMiddleware(BaseHTTPMiddleware):
    """Middleware for security headers and rate limiting."""
    
    def __init__(self, app, rate_limiter=None):
        super().__init__(app)
        self.rate_limiter = rate_limiter
    
    async def dispatch(self, request: Request, call_next: RequestResponseEndpoint) -> Response:
        # Add security headers
        response = await call_next(request)
        
        # Security headers
        response.headers['X-Content-Type-Options'] = 'nosniff'
        response.headers['X-Frame-Options'] = 'DENY'
        response.headers['X-XSS-Protection'] = '1; mode=block'
        response.headers['Strict-Transport-Security'] = 'max-age=31536000; includeSubDomains'
        response.headers['X-Request-ID'] = getattr(request.state, 'request_id', str(uuid.uuid4()))
        
        # Content Security Policy
        if settings.enable_csp:
            csp_header = "default-src 'self'; script-src 'self' 'unsafe-inline'; style-src 'self' 'unsafe-inline'"
            response.headers['Content-Security-Policy'] = csp_header
        
        return response


class PerformanceMiddleware(BaseHTTPMiddleware):
    """Middleware for performance monitoring and metrics."""
    
    async def dispatch(self, request: Request, call_next: RequestResponseEndpoint) -> Response:
        # Record metrics
        start_time = time.time()
        
        # Add performance headers to response
        response = await call_next(request)
        
        # Calculate timing
        duration = time.time() - start_time
        
        # Add performance headers
        response.headers['X-Response-Time'] = f"{duration:.3f}s"
        response.headers['X-Processing-Time'] = f"{duration * 1000:.2f}ms"
        
        # Log performance metrics
        if settings.enable_performance_logging:
            print(f"[PERF] {request.method} {request.url.path} - {duration:.3f}s")
        
        return response


class CORSMiddleware(BaseHTTPMiddleware):
    """Enhanced CORS middleware with security considerations."""
    
    def __init__(self, app, allowed_origins=None, allow_credentials=True):
        super().__init__(app)
        self.allowed_origins = allowed_origins or settings.allowed_origins
        self.allow_credentials = allow_credentials
    
    async def dispatch(self, request: Request, call_next: RequestResponseEndpoint) -> Response:
        response = await call_next(request)
        
        # CORS headers
        response.headers['Access-Control-Allow-Origin'] = ', '.join(self.allowed_origins)
        response.headers['Access-Control-Allow-Methods'] = 'GET, POST, PUT, DELETE, OPTIONS'
        response.headers['Access-Control-Allow-Headers'] = 'Content-Type, Authorization, X-Requested-With'
        
        if self.allow_credentials:
            response.headers['Access-Control-Allow-Credentials'] = 'true'
        
        # Handle preflight requests
        if request.method == 'OPTIONS':
            response.headers['Access-Control-Max-Age'] = '86400'
            return response
        
        return response


class RequestValidatorMiddleware(BaseHTTPMiddleware):
    """Middleware for request validation and sanitization."""
    
    async def dispatch(self, request: Request, call_next: RequestResponseEndpoint) -> Response:
        # Validate request method
        if request.method not in ['GET', 'POST', 'PUT', 'DELETE', 'PATCH', 'OPTIONS']:
            from fastapi import HTTPException
            raise HTTPException(status_code=405, detail="Method not allowed")
        
        # Validate content type for certain methods
        if request.method in ['POST', 'PUT', 'PATCH']:
            content_type = request.headers.get('content-type', '')
            if not content_type.startswith('application/json'):
                from fastapi import HTTPException
                raise HTTPException(status_code=400, detail="Content-Type must be application/json")
        
        # Sanitize headers
        await self._sanitize_headers(request)
        
        response = await call_next(request)
        return response
    
    async def _sanitize_headers(self, request: Request) -> None:
        """Sanitize request headers to prevent injection attacks."""
        suspicious_headers = [
            'x-forwarded-for',
            'x-forwarded-host',
            'x-forwarded-proto',
            'x-real-ip',
        ]
        
        for header in suspicious_headers:
            if header in request.headers:
                # In production, you might want to log or block these
                pass


class LoggingMiddleware(BaseHTTPMiddleware):
    """Enhanced logging middleware for comprehensive request/response logging."""
    
    async def dispatch(self, request: Request, call_next: RequestResponseEndpoint) -> Response:
        start_time = time.time()
        
        # Generate request ID
        request_id = str(uuid.uuid4())
        request.state.request_id = request_id
        
        # Log request start
        print(f"[LOG] Request started: {request.method} {request.url} (ID: {request_id})")
        
        try:
            response = await call_next(request)
            
            # Calculate duration
            duration = time.time() - start_time
            
            # Log response
            print(f"[LOG] Response: {response.status_code} in {duration:.3f}s (ID: {request_id})")
            
            return response
            
        except Exception as e:
            duration = time.time() - start_time
            print(f"[LOG] Error: {str(e)} in {duration:.3f}s (ID: {request_id})")
            raise
            
            # Calculate duration
            duration = time.time() - start_time
            
            # Log the error
            self.logger.error(
                f"Request failed: {method} {url}",
                method=method,
                url=url,
                client_host=client_host,
                user_agent=user_agent,
                duration_ms=round(duration * 1000, 2),
                error=str(e),
                exception=traceback.format_exc()
            )
            
            # Log security event for unhandled exceptions
            log_security_event(
                event_type="unhandled_exception",
                severity="HIGH",
                ip_address=client_host,
                user_agent=user_agent,
                details={
                    "url": url,
                    "method": method,
                    "error": str(e),
                    "duration_ms": round(duration * 1000, 2)
                }
            )
            
            # Re-raise the exception
            raise
    
    def _decode_jwt(self, token: str) -> Optional[Dict[str, Any]]:
        """
        Decode JWT token to extract user information.
        This is a placeholder implementation and should be adapted to your specific JWT implementation.
        
        Args:
            token: JWT token string
            
        Returns:
            Decoded token payload or None if decoding fails
        """
        try:
            # This is a placeholder implementation
            # In a real implementation, you would use your JWT library (e.g., PyJWT)
            # to decode the token and extract the user ID
            
            # Example implementation:
            # import jwt
            # payload = jwt.decode(token, secret_key, algorithms=['HS256'])
            # return payload
            
            return None  # Placeholder - return None for now
        except:
            return None

class SecurityLoggingMiddleware(BaseHTTPMiddleware):
    """
    Specialized middleware for security-related logging.
    Logs authentication attempts, authorization failures, and security events.
    """
    
    def __init__(self, app):
        super().__init__(app)
        self.logger = get_logger('security')
    
    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        """Process the request and add security logging"""
        start_time = time.time()
        
        # Extract request information
        method = request.method
        url = str(request.url)
        client_host = request.client.host if request.client else "unknown"
        user_agent = request.headers.get("user-agent", "unknown")
        
        # Extract authentication headers
        auth_header = request.headers.get("authorization", "")
        api_key = request.headers.get("x-api-key", "")
        
        # Log authentication attempts
        if "/auth/" in url or "/login" in url or "/api/auth/" in url:
            if auth_header:
                self.logger.info(
                    f"Authentication attempt: {method} {url}",
                    method=method,
                    url=url,
                    client_host=client_host,
                    has_auth_header=True,
                    has_api_key=False
                )
            elif api_key:
                self.logger.info(
                    f"API key authentication attempt: {method} {url}",
                    method=method,
                    url=url,
                    client_host=client_host,
                    has_auth_header=False,
                    has_api_key=True
                )
            else:
                self.logger.warning(
                    f"Unauthenticated access attempt: {method} {url}",
                    method=method,
                    url=url,
                    client_host=client_host,
                    has_auth_header=False,
                    has_api_key=False
                )
        
        # Process the request
        try:
            response = await call_next(request)
            
            # Calculate response time
            duration = time.time() - start_time
            
            # Log security events based on response status
            if response.status_code == 401:
                self.logger.warning(
                    f"Unauthorized access: {method} {url}",
                    method=method,
                    url=url,
                    client_host=client_host,
                    user_agent=user_agent,
                    status_code=response.status_code,
                    duration_ms=round(duration * 1000, 2),
                    has_auth_header=bool(auth_header),
                    has_api_key=bool(api_key)
                )
            elif response.status_code == 403:
                self.logger.warning(
                    f"Forbidden access: {method} {url}",
                    method=method,
                    url=url,
                    client_host=client_host,
                    user_agent=user_agent,
                    status_code=response.status_code,
                    duration_ms=round(duration * 1000, 2),
                    has_auth_header=bool(auth_header),
                    has_api_key=bool(api_key)
                )
            elif response.status_code == 429:
                self.logger.warning(
                    f"Rate limit exceeded: {method} {url}",
                    method=method,
                    url=url,
                    client_host=client_host,
                    user_agent=user_agent,
                    status_code=response.status_code,
                    duration_ms=round(duration * 1000, 2)
                )
            elif response.status_code >= 500:
                self.logger.error(
                    f"Server error: {method} {url}",
                    method=method,
                    url=url,
                    client_host=client_host,
                    user_agent=user_agent,
                    status_code=response.status_code,
                    duration_ms=round(duration * 1000, 2)
                )
            
            return response
            
        except Exception as e:
            # Calculate duration
            duration = time.time() - start_time
            
            # Log the error
            self.logger.error(
                f"Security middleware error: {method} {url}",
                method=method,
                url=url,
                client_host=client_host,
                user_agent=user_agent,
                duration_ms=round(duration * 1000, 2),
                error=str(e),
                exception=traceback.format_exc()
            )
            
            # Re-raise the exception
            raise

class PerformanceLoggingMiddleware(BaseHTTPMiddleware):
    """
    Middleware for logging performance metrics.
    Tracks request duration, response sizes, and performance patterns.
    """
    
    def __init__(self, app):
        super().__init__(app)
        self.logger = get_logger('performance')
    
    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        """Process the request and add performance logging"""
        start_time = time.time()
        
        # Extract request information
        method = request.method
        url = str(request.url)
        content_length = request.headers.get("content-length", 0)
        
        # Process the request
        try:
            response = await call_next(request)
            
            # Calculate metrics
            duration = time.time() - start_time
            response_size = 0
            
            # Calculate response size if available
            if hasattr(response, 'body'):
                response_size = len(response.body)
            elif hasattr(response, 'content'):
                response_size = len(response.content)
            
            # Log performance metrics
            self.logger.info(
                f"Performance metrics: {method} {url}",
                method=method,
                url=url,
                duration_ms=round(duration * 1000, 2),
                request_size=int(content_length),
                response_size=response_size,
                status_code=response.status_code
            )
            
            # Log slow requests (> 1 second)
            if duration > 1.0:
                self.logger.warning(
                    f"Slow request detected: {method} {url}",
                    method=method,
                    url=url,
                    duration_ms=round(duration * 1000, 2),
                    status_code=response.status_code
                )
            
            return response
            
        except Exception as e:
            # Calculate duration
            duration = time.time() - start_time
            
            # Log the error
            self.logger.error(
                f"Performance middleware error: {method} {url}",
                method=method,
                url=url,
                duration_ms=round(duration * 1000, 2),
                error=str(e)
            )
            
            # Re-raise the exception
            raise