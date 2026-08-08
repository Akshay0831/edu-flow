"""
Logging middleware for FastAPI/Flask applications.
This middleware provides automatic logging for HTTP requests and responses.
"""

import time
import traceback
from typing import Optional, Dict, Any, Callable
from datetime import datetime
from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware
from .logging_utils import log_api_request, log_user_action, log_security_event
from ..config.logging import get_logger

class LoggingMiddleware(BaseHTTPMiddleware):
    """
    Middleware for logging HTTP requests and responses.
    Automatically logs API requests, user actions, and security events.
    """
    
    def __init__(self, app):
        super().__init__(app)
        self.logger = get_logger('backend')
    
    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        """Process the request and add logging"""
        start_time = time.time()
        
        # Extract request information
        method = request.method
        url = str(request.url)
        client_host = request.client.host if request.client else "unknown"
        user_agent = request.headers.get("user-agent", "unknown")
        
        # Extract user information from JWT token if available
        user_id = None
        token = request.headers.get("authorization", "")
        
        if token:
            try:
                # Extract user ID from JWT token
                # This would need to be adapted to your specific JWT implementation
                if len(token.split(" ")) == 2 and token.split(" ")[0].lower() == "bearer":
                    payload = self._decode_jwt(token.split(" ")[1])
                    if payload and "user_id" in payload:
                        user_id = payload["user_id"]
            except:
                # If we can't decode the token, we'll log it as a security event
                log_security_event(
                    event_type="jwt_decode_error",
                    severity="MEDIUM",
                    ip_address=client_host,
                    user_agent=user_agent,
                    details={"url": url, "method": method}
                )
        
        # Log the request start
        self.logger.info(
            f"Request started: {method} {url}",
            method=method,
            url=url,
            client_host=client_host,
            user_agent=user_agent,
            user_id=user_id
        )
        
        # Process the request
        try:
            response = await call_next(request)
            
            # Calculate response time
            duration = time.time() - start_time
            
            # Log the response
            self.logger.api_request(
                method=method,
                endpoint=url,
                status_code=response.status_code,
                duration=duration,
                user=user_id
            )
            
            # Log user actions for certain status codes
            if response.status_code == 200 and user_id:
                log_user_action(
                    action="api_success",
                    user_id=user_id,
                    resource=url,
                    details={
                        "method": method,
                        "status_code": response.status_code,
                        "duration_ms": round(duration * 1000, 2)
                    }
                )
            
            # Log security events for certain status codes
            if response.status_code == 401 and user_id:
                log_security_event(
                    event_type="unauthorized_access",
                    severity="MEDIUM",
                    user_id=user_id,
                    ip_address=client_host,
                    user_agent=user_agent,
                    details={
                        "url": url,
                        "method": method,
                        "status_code": response.status_code
                    }
                )
            elif response.status_code == 403 and user_id:
                log_security_event(
                    event_type="forbidden_access",
                    severity="MEDIUM",
                    user_id=user_id,
                    ip_address=client_host,
                    user_agent=user_agent,
                    details={
                        "url": url,
                        "method": method,
                        "status_code": response.status_code
                    }
                )
            elif response.status_code >= 500:
                # Log server errors as security events
                log_security_event(
                    event_type="server_error",
                    severity="HIGH",
                    ip_address=client_host,
                    user_agent=user_agent,
                    details={
                        "url": url,
                        "method": method,
                        "status_code": response.status_code,
                        "duration_ms": round(duration * 1000, 2)
                    }
                )
            
            return response
            
        except Exception as e:
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