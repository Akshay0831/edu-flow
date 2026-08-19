"""
Enhanced Security Configuration for Edu-Flow Backend

This module provides comprehensive security features including:
- Rate limiting with multiple strategies
- Input validation and sanitization
- Security middleware and headers
- Authentication enhancement
- Authorization controls
- Security logging and monitoring

Author: Edu-Flow Team
"""

import asyncio
import time
import logging
import re
import ipaddress
from typing import Dict, List, Optional, Any, Union
from datetime import datetime, timedelta, timezone
from fastapi import FastAPI, Request, Response, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.trustedhost import TrustedHostMiddleware
from fastapi.middleware.httpsredirect import HTTPSRedirectMiddleware
from fastapi.middleware.gzip import GZipMiddleware
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.middleware.sessions import SessionMiddleware
from starlette.middleware import Middleware
from pydantic import BaseModel, validator, Field
from prometheus_client import Counter, Histogram, Gauge
from core.security import SecurityConfig, AuthService
from core.exceptions import AuthenticationError, AuthorizationError
from config.settings import settings


class RateLimitConfig:
    """Rate limiting configuration"""
    
    def __init__(self):
        # Memory-based rate limiter
        self.requests = {}  # type: Dict[str, List[float]]
        self.cleanup_interval = 3600  # 1 hour
        self.last_cleanup = time.time()
        
        # Prometheus metrics
        self.request_counter = Counter(
            'http_requests_total',
            'Total HTTP requests',
            ['method', 'endpoint', 'status']
        )
        self.request_duration = Histogram(
            'http_request_duration_seconds',
            'HTTP request duration',
            ['method', 'endpoint']
        )
        self.active_requests = Gauge(
            'active_requests',
            'Number of active requests'
        )
    
    async def is_allowed(self, key: str, limit: int, window: int) -> bool:
        """Check if a request is allowed based on rate limiting"""
        current_time = time.time()
        
        # Cleanup old entries
        if current_time - self.last_cleanup > self.cleanup_interval:
            await self.cleanup()
        
        if key not in self.requests:
            self.requests[key] = []
        
        # Remove old requests outside the window
        self.requests[key] = [
            req_time for req_time in self.requests[key]
            if current_time - req_time < window
        ]
        
        # Check if request is allowed
        if len(self.requests[key]) >= limit:
            return False
        
        # Record this request
        self.requests[key].append(current_time)
        return True
    
    async def cleanup(self):
        """Clean up old rate limit entries"""
        current_time = time.time()
        keys_to_remove = []
        
        for key, req_times in self.requests.items():
            # Remove requests older than 24 hours
            req_times = [t for t in req_times if current_time - t < 86400]
            if not req_times:
                keys_to_remove.append(key)
            else:
                self.requests[key] = req_times
        
        for key in keys_to_remove:
            del self.requests[key]
        
        self.last_cleanup = current_time


class InputSanitizer:
    """Input validation and sanitization"""
    
    # Patterns for common vulnerabilities
    XSS_PATTERNS = [
        r'<script[^>]*>.*?</script>',
        r'javascript:',
        r'on\w+\s*=',
        r'<iframe[^>]*>',
        r'<link[^>]*>',
        r'<meta[^>]*>',
        r'<object[^>]*>',
        r'<embed[^>]*>',
        r'<form[^>]*>',
        r'<input[^>]*>',
        r'<button[^>]*>',
        r'<select[^>]*>',
        r'<textarea[^>]*>',
        r'<img[^>]*>',
        r'<style[^>]*>.*?</style>',
        r'<svg[^>]*>',
        r'<math[^>]*>',
        r'<![CDATA\[.*?\]\]>',
        r'&lt;script&gt;',
        r'&lt;/script&gt;',
        r'eval\(',
        r'document\.',
        r'window\.',
        r'alert\(',
        r'confirm\(',
        r'prompt\(',
    ]
    
    SQL_INJECTION_PATTERNS = [
        r'union\s+select',
        r'select\s+.*?\s+from',
        r'insert\s+into',
        r'delete\s+from',
        r'update\s+.*?\s+set',
        r'drop\s+table',
        r'exec\s*\(',
        r'xp_\w+',
        r'sysobjects',
        r'information_schema',
        r'master\.',
        r'tempdb\.',
        r'\bor\s+1\s*=\s*1',
        r'\bor\s+1\s*=\s*1--',
        r'--',
        r'\#',
        r'\/\*.*?\*\/',
    ]
    
    @classmethod
    def sanitize_input(cls, value: str, input_type: str = "text") -> str:
        """Sanitize input based on type"""
        if not value:
            return value
        
        if input_type == "text":
            # Remove control characters except basic ones
            value = re.sub(r'[\x00-\x08\x0b\x0c\x0e-\x1f\x7f-\x9f]', '', value)
            
            # Escape HTML entities
            value = value.replace('&', '&amp;').replace('<', '&lt;').replace('>', '&gt;')
            
            # Remove potential XSS patterns
            for pattern in cls.XSS_PATTERNS:
                value = re.sub(pattern, '', value, flags=re.IGNORECASE)
        
        elif input_type == "email":
            # Basic email validation
            if not re.match(r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$', value):
                raise ValueError("Invalid email format")
        
        elif input_type == "password":
            # Password complexity checks should be done separately
            pass
        
        elif input_type == "html":
            # Allow basic HTML but strip dangerous tags
            allowed_tags = ['p', 'br', 'strong', 'em', 'u', 'ol', 'ul', 'li', 'h1', 'h2', 'h3', 'h4', 'h5', 'h6']
            for tag in allowed_tags:
                # Keep safe tags
                pass
        
        return value.strip()
    
    @classmethod
    def detect_sql_injection(cls, value: str) -> bool:
        """Detect potential SQL injection patterns"""
        if not value:
            return False
        
        value_lower = value.lower()
        for pattern in cls.SQL_INJECTION_PATTERNS:
            if re.search(pattern, value_lower):
                return True
        return False


class SecurityHeaders:
    """Security headers configuration"""
    
    DEFAULT_HEADERS = {
        'X-Content-Type-Options': 'nosniff',
        'X-Frame-Options': 'DENY',
        'X-XSS-Protection': '1; mode=block',
        'Strict-Transport-Security': 'max-age=31536000; includeSubDomains',
        'Content-Security-Policy': "default-src 'self'; script-src 'self' 'unsafe-inline' 'unsafe-eval'; style-src 'self' 'unsafe-inline'; img-src 'self' data:; font-src 'self' data:; connect-src 'self'; frame-src 'none'; object-src 'none';",
        'Referrer-Policy': 'strict-origin-when-cross-origin',
        'Permissions-Policy': 'geolocation=(), microphone=(), camera=()',
        'Cache-Control': 'no-cache, no-store, must-revalidate',
        'Pragma': 'no-cache',
        'Expires': '0',
    }
    
    @classmethod
    def get_headers(cls, custom_headers: Optional[Dict[str, str]] = None) -> Dict[str, str]:
        """Get security headers with optional custom additions"""
        headers = cls.DEFAULT_HEADERS.copy()
        if custom_headers:
            headers.update(custom_headers)
        return headers


class SecurityMiddleware(BaseHTTPMiddleware):
    """Security middleware for FastAPI"""
    
    def __init__(self, app, rate_limit_config: RateLimitConfig, security_config: SecurityConfig):
        super().__init__(app)
        self.rate_limit_config = rate_limit_config
        self.security_config = security_config
        self.logger = logging.getLogger(__name__)
    
    async def dispatch(self, request: Request, call_next):
        """Process security middleware"""
        start_time = time.time()
        
        # Get client IP for rate limiting
        client_ip = self._get_client_ip(request)
        
        # Rate limiting
        if settings.rate_limit_enabled:
            rate_key = f"{client_ip}:{request.url.path}"
            if not await self.rate_limit_config.is_allowed(
                rate_key,
                settings.rate_limit_requests,
                settings.rate_limit_window
            ):
                self.logger.warning(f"Rate limit exceeded for {client_ip} on {request.url.path}")
                return Response(
                    status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                    content="Too many requests. Please try again later."
                )
        
        # Security headers
        response = await call_next(request)
        
        # Add security headers
        security_headers = SecurityHeaders.get_headers()
        for header, value in security_headers.items():
            response.headers[header] = value
        
        # Track metrics
        request_time = time.time() - start_time
        self.rate_limit_config.request_duration.observe(
            request_time,
            [request.method, str(request.url.path)]
        )
        self.rate_limit_config.request_counter.labels(
            request.method,
            str(request.url.path),
            str(response.status_code)
        ).inc()
        self.rate_limit_config.active_requests.inc()
        
        # Log security events
        if response.status_code >= 400:
            self.logger.warning(
                f"Security event: {client_ip} - {request.method} {request.url.path} - "
                f"Status: {response.status_code}"
            )
        
        return response
    
    def _get_client_ip(self, request: Request) -> str:
        """Get client IP address, handling proxies"""
        # Check for forwarded headers
        forwarded_for = request.headers.get('X-Forwarded-For')
        if forwarded_for:
            # Take the first IP from the forwarded header
            client_ip = forwarded_for.split(',')[0].strip()
        else:
            client_ip = request.client.host
        
        # Validate IP address
        try:
            ipaddress.ip_address(client_ip)
            return client_ip
        except ValueError:
            return "unknown"


class SecurityValidator:
    """Advanced security validation"""
    
    @staticmethod
    def validate_password_strength(password: str) -> Dict[str, Any]:
        """Validate password strength"""
        checks = {
            'length': len(password) >= 8,
            'uppercase': any(c.isupper() for c in password) if settings.password_require_uppercase else True,
            'lowercase': any(c.islower() for c in password) if settings.password_require_lowercase else True,
            'number': any(c.isdigit() for c in password) if settings.password_require_number else True,
            'special': any(c in '!@#$%^&*()_+-=[]{}|;:,.<>?' for c in password) if settings.password_require_special else True,
        }
        
        score = sum(checks.values()) / len(checks)
        strength = 'weak' if score < 0.6 else 'medium' if score < 0.8 else 'strong'
        
        return {
            'valid': all(checks.values()),
            'score': score,
            'strength': strength,
            'checks': checks,
            'feedback': SecurityValidator._get_password_feedback(checks, strength)
        }
    
    @staticmethod
    def _get_password_feedback(checks: Dict[str, bool], strength: str) -> List[str]:
        """Get feedback for password improvement"""
        feedback = []
        
        if not checks['length']:
            feedback.append("Password should be at least 8 characters long")
        if not checks['uppercase']:
            feedback.append("Add uppercase letters")
        if not checks['lowercase']:
            feedback.append("Add lowercase letters")
        if not checks['number']:
            feedback.append("Add numbers")
        if not checks['special']:
            feedback.append("Add special characters (!@#$%^&*()_+-=[]{}|;:,.<>?)")
        
        if strength == 'weak':
            feedback.append("Password is too weak. Please add more complexity")
        elif strength == 'medium':
            feedback.append("Password is medium strength. Consider adding more complexity")
        else:
            feedback.append("Password is strong")
        
        return feedback


# Global security instances
rate_limit_config = RateLimitConfig()
security_config = SecurityConfig()

# Security middleware setup
def setup_security_middleware(app: FastAPI):
    """Setup security middleware for FastAPI app"""
    
    # Add CORS middleware with security settings
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origins,
        allow_credentials=settings.cors_allow_credentials,
        allow_methods=settings.cors_allow_methods,
        allow_headers=settings.cors_allow_headers,
        max_age=600,
    )
    
    # Add security middleware
    app.add_middleware(
        SecurityMiddleware,
        rate_limit_config=rate_limit_config,
        security_config=security_config
    )
    
    # Add trusted host middleware
    app.add_middleware(
        TrustedHostMiddleware,
        allowed_hosts=["*"] if settings.debug else ["localhost", "127.0.0.1"]
    )
    
    # Add HTTPS redirect middleware (production only)
    if not settings.debug:
        app.add_middleware(HTTPSRedirectMiddleware)
    
    # Add GZip compression
    app.add_middleware(GZipMiddleware, minimum_size=1000)
    
    # Add session middleware
    app.add_middleware(SessionMiddleware, secret_key=settings.secret_key)
    
    logger = logging.getLogger(__name__)
    logger.info("Security middleware configured successfully")