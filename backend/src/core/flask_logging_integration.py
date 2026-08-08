"""
Flask integration module for the logging system.
This module provides easy integration of the logging system with Flask applications.
"""

import os
import time
import traceback
from typing import Optional, Dict, Any, Callable
from datetime import datetime
from flask import Flask, request, jsonify
from ..config.logging import get_logger, get_component_logger
from ..config.logging_config import setup_logging
from functools import wraps

class FlaskLoggingMiddleware:
    """
    Flask middleware for logging HTTP requests and responses.
    """
    
    def __init__(self, app: Flask):
        self.app = app
        self.logger = get_logger('backend')
        self.setup_middleware()
    
    def setup_middleware(self):
        """Setup Flask middleware for logging"""
        @self.app.before_request
        def before_request():
            """Log request information before processing"""
            request.start_time = time.time()
            
            # Extract request information
            method = request.method
            url = request.url
            client_host = request.remote_addr
            user_agent = request.headers.get('user-agent', 'unknown')
            
            # Extract user information from JWT token if available
            user_id = None
            token = request.headers.get('authorization', '')
            
            if token:
                try:
                    if len(token.split(' ')) == 2 and token.split(' ')[0].lower() == 'bearer':
                        payload = self._decode_jwt(token.split(' ')[1])
                        if payload and 'user_id' in payload:
                            user_id = payload['user_id']
                except:
                    pass
            
            # Log the request start
            self.logger.info(
                f"Request started: {method} {url}",
                method=method,
                url=url,
                client_host=client_host,
                user_agent=user_agent,
                user_id=user_id
            )
            
            # Store request info for later use
            request._log_info = {
                'method': method,
                'url': url,
                'client_host': client_host,
                'user_agent': user_agent,
                'user_id': user_id,
                'start_time': request.start_time
            }
        
        @self.app.after_request
        def after_request(response):
            """Log response information after processing"""
            if hasattr(request, 'start_time'):
                # Calculate duration
                duration = time.time() - request.start_time
                
                # Get request info
                log_info = getattr(request, '_log_info', {})
                
                # Log the response
                self.logger.api_request(
                    method=log_info.get('method', 'UNKNOWN'),
                    endpoint=log_info.get('url', str(request.url)),
                    status_code=response.status_code,
                    duration=duration,
                    user=log_info.get('user_id')
                )
                
                # Log user actions for certain status codes
                if response.status_code == 200 and log_info.get('user_id'):
                    self.log_user_action(
                        action="api_success",
                        user_id=log_info['user_id'],
                        resource=log_info.get('url', str(request.url)),
                        details={
                            "method": log_info.get('method'),
                            "status_code": response.status_code,
                            "duration_ms": round(duration * 1000, 2)
                        }
                    )
                
                # Log security events for certain status codes
                if response.status_code == 401 and log_info.get('user_id'):
                    self.log_security_event(
                        event_type="unauthorized_access",
                        severity="MEDIUM",
                        user_id=log_info['user_id'],
                        ip_address=log_info.get('client_host'),
                        user_agent=log_info.get('user_agent'),
                        details={
                            "url": log_info.get('url', str(request.url)),
                            "method": log_info.get('method'),
                            "status_code": response.status_code
                        }
                    )
                elif response.status_code == 403 and log_info.get('user_id'):
                    self.log_security_event(
                        event_type="forbidden_access",
                        severity="MEDIUM",
                        user_id=log_info['user_id'],
                        ip_address=log_info.get('client_host'),
                        user_agent=log_info.get('user_agent'),
                        details={
                            "url": log_info.get('url', str(request.url)),
                            "method": log_info.get('method'),
                            "status_code": response.status_code
                        }
                    )
                elif response.status_code >= 500:
                    # Log server errors as security events
                    self.log_security_event(
                        event_type="server_error",
                        severity="HIGH",
                        ip_address=log_info.get('client_host'),
                        user_agent=log_info.get('user_agent'),
                        details={
                            "url": log_info.get('url', str(request.url)),
                            "method": log_info.get('method'),
                            "status_code": response.status_code,
                            "duration_ms": round(duration * 1000, 2)
                        }
                    )
            
            return response
        
        @self.app.errorhandler(Exception)
        def handle_exception(e):
            """Handle exceptions and log them"""
            if hasattr(request, 'start_time'):
                duration = time.time() - request.start_time
                log_info = getattr(request, '_log_info', {})
                
                # Log the error
                self.logger.error(
                    f"Request failed: {log_info.get('method', 'UNKNOWN')} {log_info.get('url', str(request.url))}",
                    method=log_info.get('method'),
                    url=log_info.get('url', str(request.url)),
                    client_host=log_info.get('client_host'),
                    user_agent=log_info.get('user_agent'),
                    duration_ms=round(duration * 1000, 2),
                    error=str(e),
                    exception=traceback.format_exc()
                )
                
                # Log security event for unhandled exceptions
                self.log_security_event(
                    event_type="unhandled_exception",
                    severity="HIGH",
                    ip_address=log_info.get('client_host'),
                    user_agent=log_info.get('user_agent'),
                    details={
                        "url": log_info.get('url', str(request.url)),
                        "method": log_info.get('method'),
                        "error": str(e),
                        "duration_ms": round(duration * 1000, 2)
                    }
                )
            
            return jsonify({"error": str(e)}), 500
    
    def _decode_jwt(self, token: str) -> Optional[Dict[str, Any]]:
        """Decode JWT token to extract user information"""
        try:
            # This is a placeholder implementation
            # In a real implementation, you would use your JWT library
            return None
        except:
            return None
    
    def log_user_action(self, action: str, user_id: str, resource: str = None, details: Dict[str, Any] = None):
        """Log user actions for audit purposes"""
        self.logger.audit(
            action=action,
            user=user_id,
            resource=resource or 'system',
            details=details or {}
        )
    
    def log_security_event(self, event_type: str, severity: str, user_id: str = None, 
                          ip_address: str = None, user_agent: str = None, details: Dict[str, Any] = None):
        """Log security events"""
        self.logger.security_event(
            event_type=event_type,
            severity=severity,
            details=details or {}
        )

def create_flask_app(
    app_name: str = "Edu-Flow",
    environment: str = None,
    debug: bool = None
) -> Flask:
    """
    Create a Flask application with logging middleware already configured.
    
    Args:
        app_name: Name of the application
        environment: Environment (development, testing, production)
        debug: Debug mode
        
    Returns:
        Configured Flask application
    """
    # Determine environment
    env = environment or os.getenv('ENVIRONMENT', 'development')
    
    # Create Flask app
    app = Flask(app_name)
    app.config['ENV'] = env
    app.config['DEBUG'] = debug if debug is not None else (env == 'development')
    
    # Setup logging middleware
    FlaskLoggingMiddleware(app)
    
    # Add startup and shutdown events for logging
    @app.before_first_request
    def startup_event():
        logger = get_logger('backend')
        logger.info(f"{app_name} starting up", environment=env)
        
        # Log system information
        self.log_user_action(
            action="system_startup",
            user_id="system",
            resource="application",
            details={
                "app_name": app_name,
                "environment": env,
                "version": "2.0.0"
            }
        )
    
    @app.teardown_appcontext
    def shutdown_event(exception=None):
        logger = get_logger('backend')
        if exception:
            logger.error(f"{app_name} shutting down with error", error=str(exception))
        else:
            logger.info(f"{app_name} shutting down", environment=env)
        
        # Log system information
        self.log_user_action(
            action="system_shutdown",
            user_id="system",
            resource="application",
            details={
                "app_name": app_name,
                "environment": env,
                "has_error": bool(exception)
            }
        )
    
    return app

def log_function_call(component: str = 'backend'):
    """
    Decorator to log function calls with performance metrics.
    
    Args:
        component: Component name for the logger
    """
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        def wrapper(*args, **kwargs):
            start_time = time.time()
            func_name = f"{func.__module__}.{func.__name__}"
            
            # Get component-specific logger
            comp_logger = get_logger(component)
            
            try:
                # Log function call start
                comp_logger.info(
                    f"Function call started: {func_name}",
                    function=func_name,
                    args_count=len(args),
                    kwargs_count=len(kwargs)
                )
                
                # Execute function
                result = func(*args, **kwargs)
                
                # Calculate duration
                duration = time.time() - start_time
                
                # Log function call completion
                comp_logger.info(
                    f"Function call completed: {func_name}",
                    function=func_name,
                    duration_ms=round(duration * 1000, 2),
                    status="success"
                )
                
                return result
                
            except Exception as e:
                # Calculate duration
                duration = time.time() - start_time
                
                # Log function call error
                comp_logger.error(
                    f"Function call failed: {func_name}",
                    function=func_name,
                    duration_ms=round(duration * 1000, 2),
                    error=str(e),
                    exception=traceback.format_exc(),
                    status="error"
                )
                
                # Re-raise the exception
                raise
        
        return wrapper
    return decorator

def log_api_call(component: str = 'backend'):
    """
    Decorator to log API calls with performance metrics.
    
    Args:
        component: Component name for the logger
    """
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        def wrapper(*args, **kwargs):
            start_time = time.time()
            func_name = f"{func.__module__}.{func.__name__}"
            
            comp_logger = get_logger(component)
            
            try:
                # Log API call start
                comp_logger.info(
                    f"API call started: {func_name}",
                    function=func_name
                )
                
                # Execute function
                result = func(*args, **kwargs)
                
                # Calculate duration
                duration = time.time() - start_time
                
                # Log API call completion
                comp_logger.info(
                    f"API call completed: {func_name}",
                    function=func_name,
                    duration_ms=round(duration * 1000, 2),
                    status="success"
                )
                
                return result
                
            except Exception as e:
                # Calculate duration
                duration = time.time() - start_time
                
                # Log API call error
                comp_logger.error(
                    f"API call failed: {func_name}",
                    function=func_name,
                    duration_ms=round(duration * 1000, 2),
                    error=str(e),
                    exception=traceback.format_exc(),
                    status="error"
                )
                
                # Re-raise the exception
                raise
        
        return wrapper
    return decorator

def get_loggers():
    """Get loggers for all components"""
    return {
        'backend': get_component_logger('backend'),
        'frontend': get_component_logger('frontend'),
        'auth-gateway': get_component_logger('auth-gateway'),
        'ai-services': get_component_logger('ai-services'),
        'database': get_component_logger('database'),
        'performance': get_component_logger('performance'),
        'security': get_component_logger('security')
    }