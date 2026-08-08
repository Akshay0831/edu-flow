"""
Common logging utilities for Edu-Flow application.
This module provides helper functions and decorators for consistent logging.
"""

import time
import functools
import traceback
from typing import Dict, Any, Optional, Callable
from datetime import datetime
from ..config.logging import get_logger

# Global logger instance
logger = get_logger('backend')

def log_function_call(component: str = 'backend'):
    """
    Decorator to log function calls with performance metrics.
    
    Args:
        component: Component name for the logger
    """
    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
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

def log_api_request(component: str = 'backend'):
    """
    Decorator to log API requests with performance metrics.
    
    Args:
        component: Component name for the logger
    """
    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            start_time = time.time()
            func_name = f"{func.__module__}.{func.__name__}"
            
            # Extract request info from FastAPI request
            request = None
            status_code = 200
            user = None
            
            # Try to extract request object from FastAPI context
            try:
                # This assumes FastAPI request injection
                request = next((arg for arg in args if hasattr(arg, 'method')), None)
                if request:
                    user = getattr(request, 'user', None)
                    if user and hasattr(user, 'username'):
                        user = user.username
                    elif user and hasattr(user, 'email'):
                        user = user.email
            except:
                pass
            
            comp_logger = get_logger(component)
            
            try:
                # Log API request start
                if request:
                    comp_logger.api_request(
                        method=request.method,
                        endpoint=str(request.url),
                        status_code=status_code,
                        duration=0,  # Will be updated later
                        user=user
                    )
                
                # Execute function
                result = func(*args, **kwargs)
                
                # Calculate duration
                duration = time.time() - start_time
                
                # Extract status code from response if available
                if hasattr(result, 'status_code'):
                    status_code = result.status_code
                
                # Log API request completion
                comp_logger.api_request(
                    method=request.method if request else 'UNKNOWN',
                    endpoint=str(request.url) if request else func_name,
                    status_code=status_code,
                    duration=duration,
                    user=user
                )
                
                return result
                
            except Exception as e:
                # Calculate duration
                duration = time.time() - start_time
                
                # Log API request error
                comp_logger.api_request(
                    method=request.method if request else 'UNKNOWN',
                    endpoint=str(request.url) if request else func_name,
                    status_code=500,
                    duration=duration,
                    user=user
                )
                
                comp_logger.error(
                    f"API request failed: {func_name}",
                    function=func_name,
                    error=str(e),
                    exception=traceback.format_exc()
                )
                
                # Re-raise the exception
                raise
        
        return wrapper
    return decorator

def log_database_operation(operation: str, collection: str, component: str = 'database'):
    """
    Decorator to log database operations with performance metrics.
    
    Args:
        operation: Database operation type (insert, update, delete, query)
        collection: Collection/table name
        component: Component name for the logger
    """
    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            start_time = time.time()
            func_name = f"{func.__module__}.{func.__name__}"
            
            comp_logger = get_logger(component)
            record_count = 0
            
            try:
                # Log database operation start
                comp_logger.info(
                    f"Database operation started: {operation}",
                    operation=operation,
                    collection=collection,
                    function=func_name
                )
                
                # Execute function
                result = func(*args, **kwargs)
                
                # Calculate duration and record count
                duration = time.time() - start_time
                
                # Try to extract record count from result
                if isinstance(result, list):
                    record_count = len(result)
                elif hasattr(result, 'rowcount'):
                    record_count = result.rowcount
                elif hasattr(result, 'count'):
                    record_count = result.count
                
                # Log database operation completion
                comp_logger.database_operation(
                    operation=operation,
                    collection=collection,
                    duration=duration,
                    record_count=record_count
                )
                
                return result
                
            except Exception as e:
                # Calculate duration
                duration = time.time() - start_time
                
                # Log database operation error
                comp_logger.error(
                    f"Database operation failed: {operation}",
                    operation=operation,
                    collection=collection,
                    duration=duration,
                    error=str(e),
                    exception=traceback.format_exc()
                )
                
                # Re-raise the exception
                raise
        
        return wrapper
    return decorator

def log_ai_service_request(service: str, model: str, component: str = 'ai-services'):
    """
    Decorator to log AI service requests with performance metrics.
    
    Args:
        service: AI service name
        model: Model name
        component: Component name for the logger
    """
    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            start_time = time.time()
            func_name = f"{func.__module__}.{func.__name__}"
            
            comp_logger = get_logger(component)
            input_size = 0
            output_size = 0
            
            try:
                # Log AI service request start
                comp_logger.info(
                    f"AI service request started: {service}",
                    service=service,
                    model=model,
                    function=func_name
                )
                
                # Execute function
                result = func(*args, **kwargs)
                
                # Calculate duration
                duration = time.time() - start_time
                
                # Try to extract input/output sizes
                if args:
                    input_size = len(str(args))
                if kwargs:
                    input_size += len(str(kwargs))
                
                if result:
                    output_size = len(str(result))
                
                # Log AI service request completion
                comp_logger.ai_service_request(
                    service=service,
                    model=model,
                    input_size=input_size,
                    output_size=output_size,
                    duration=duration
                )
                
                return result
                
            except Exception as e:
                # Calculate duration
                duration = time.time() - start_time
                
                # Log AI service request error
                comp_logger.error(
                    f"AI service request failed: {service}",
                    service=service,
                    model=model,
                    duration=duration,
                    error=str(e),
                    exception=traceback.format_exc()
                )
                
                # Re-raise the exception
                raise
        
        return wrapper
    return decorator

class LogContext:
    """Context manager for adding contextual information to logs"""
    
    def __init__(self, component: str = 'backend', **context):
        self.component = component
        self.context = context
        self.logger = get_logger(component)
    
    def __enter__(self):
        # Store existing context (if any)
        self.old_context = getattr(self.logger, 'context', {})
        # Add new context
        self.logger.context = {**self.old_context, **self.context}
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        # Restore old context
        if hasattr(self.logger, 'old_context'):
            self.logger.context = self.old_context
        else:
            delattr(self.logger, 'context')

def log_user_action(action: str, user_id: str, resource: str = None, details: Dict[str, Any] = None, component: str = 'backend'):
    """
    Log user actions for audit purposes.
    
    Args:
        action: Action performed (login, logout, create, update, delete, etc.)
        user_id: User identifier
        resource: Resource being accessed (optional)
        details: Additional details about the action
        component: Component name for the logger
    """
    comp_logger = get_logger(component)
    
    audit_details = {
        'action': action,
        'user_id': user_id,
        'timestamp': datetime.now().isoformat()
    }
    
    if resource:
        audit_details['resource'] = resource
    
    if details:
        audit_details.update(details)
    
    comp_logger.audit(
        action=action,
        user=user_id,
        resource=resource or 'system',
        details=audit_details
    )

def log_security_event(event_type: str, severity: str, user_id: str = None, ip_address: str = None, 
                      user_agent: str = None, details: Dict[str, Any] = None, component: str = 'security'):
    """
    Log security events with severity levels.
    
    Args:
        event_type: Type of security event (login_attempt, unauthorized_access, etc.)
        severity: Severity level (LOW, MEDIUM, HIGH, CRITICAL)
        user_id: User identifier (optional)
        ip_address: IP address (optional)
        user_agent: User agent (optional)
        details: Additional details about the event
        component: Component name for the logger
    """
    comp_logger = get_logger(component)
    
    security_details = {
        'event_type': event_type,
        'timestamp': datetime.now().isoformat()
    }
    
    if user_id:
        security_details['user_id'] = user_id
    if ip_address:
        security_details['ip_address'] = ip_address
    if user_agent:
        security_details['user_agent'] = user_agent
    if details:
        security_details.update(details)
    
    comp_logger.security_event(
        event_type=event_type,
        severity=severity,
        details=security_details
    )

def log_performance_metric(metric_name: str, value: float, unit: str = 'ms', 
                         tags: Dict[str, str] = None, component: str = 'performance'):
    """
    Log performance metrics.
    
    Args:
        metric_name: Name of the metric
        value: Metric value
        unit: Unit of measurement
        tags: Additional tags for the metric
        component: Component name for the logger
    """
    comp_logger = get_logger(component)
    
    metric_data = {
        'metric': metric_name,
        'value': value,
        'unit': unit,
        'timestamp': datetime.now().isoformat()
    }
    
    if tags:
        metric_data.update(tags)
    
    comp_logger.info(f"PERFORMANCE: {metric_data}", **metric_data)