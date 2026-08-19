"""
Comprehensive logging integration for the Edu-Flow backend.
Provides centralized logging, monitoring, and analytics capabilities.
"""

import logging
import logging.config
import json
import time
from datetime import datetime, timezone
from typing import Any, Dict, Optional, List, Union
from enum import Enum
from functools import wraps
import asyncio
import contextlib
import uuid

from ..core.logging import get_logger


class LogLevel(Enum):
    """Log levels for the logging system."""
    DEBUG = "DEBUG"
    INFO = "INFO"
    WARNING = "WARNING"
    ERROR = "ERROR"
    CRITICAL = "CRITICAL"


class LogCategory(Enum):
    """Log categories for the logging system."""
    BUSINESS = "business"
    SECURITY = "security"
    PERFORMANCE = "performance"
    SYSTEM = "system"
    DATABASE = "database"
    API = "api"
    AUTH = "auth"
    NOTIFICATION = "notification"


class LogEvent(Enum):
    """Log events for the logging system."""
    USER_LOGIN = "user_login"
    USER_LOGOUT = "user_logout"
    USER_REGISTER = "user_register"
    PASSWORD_CHANGE = "password_change"
    PERMISSION_DENIED = "permission_denied"
    DATA_CREATED = "data_created"
    DATA_UPDATED = "data_updated"
    DATA_DELETED = "data_deleted"
    DATA_ACCESS = "data_access"
    API_REQUEST = "api_request"
    API_RESPONSE = "api_response"
    ERROR_OCCURRED = "error_occurred"
    PERFORMANCE_SLOW = "performance_slow"
    SECURITY_ALERT = "security_alert"
    BACKUP_CREATED = "backup_created"
    BACKUP_RESTORED = "backup_restored"


class StructuredLogger:
    """
    Enhanced structured logger for the Edu-Flow backend.
    
    Features:
    - Structured logging with JSON format
    - Automatic correlation IDs
    - Performance monitoring
    - Error tracking
    - Analytics integration
    """
    
    def __init__(self, name: str, config: Dict[str, Any] = None):
        self.name = name
        self.config = config or {}
        self.logger = get_logger(name)
        self.correlation_id = None
        self.user_id = None
        self.session_id = None
        
        # Configuration
        self.enable_structured_logging = self.config.get('enable_structured_logging', True)
        self.enable_performance_tracking = self.config.get('enable_performance_tracking', True)
        self.max_log_size = self.config.get('max_log_size', 1000)
        self.enable_analytics = self.config.get('enable_analytics', False)
        
    def set_context(self, correlation_id: str = None, user_id: str = None, session_id: str = None):
        """Set logging context."""
        
        self.correlation_id = correlation_id or str(uuid.uuid4())
        self.user_id = user_id
        self.session_id = session_id
        
    def log(
        self,
        level: LogLevel,
        message: str,
        category: LogCategory = LogCategory.SYSTEM,
        event: LogEvent = None,
        **kwargs
    ):
        """
        Log a message with structured data.
        
        Args:
            level: Log level
            message: Log message
            category: Log category
            event: Log event type
            **kwargs: Additional log data
        """
        
        # Create structured log data
        log_data = {
            'timestamp': datetime.now(timezone.utc).isoformat(),
            'level': level.value,
            'logger': self.name,
            'message': message,
            'category': category.value,
            'correlation_id': self.correlation_id,
            'user_id': self.user_id,
            'session_id': self.session_id,
        }
        
        # Add event if provided
        if event:
            log_data['event'] = event.value
        
        # Add additional data
        if kwargs:
            # Filter out sensitive data
            filtered_data = self._filter_sensitive_data(kwargs)
            log_data.update(filtered_data)
        
        # Log the message
        if self.enable_structured_logging:
            self._log_structured(log_data)
        else:
            self._log_standard(level, message, log_data)
    
    def debug(self, message: str, category: LogCategory = LogCategory.SYSTEM, event: LogEvent = None, **kwargs):
        """Log debug message."""
        
        self.log(LogLevel.DEBUG, message, category, event, **kwargs)
    
    def info(self, message: str, category: LogCategory = LogCategory.SYSTEM, event: LogEvent = None, **kwargs):
        """Log info message."""
        
        self.log(LogLevel.INFO, message, category, event, **kwargs)
    
    def warning(self, message: str, category: LogCategory = LogCategory.SYSTEM, event: LogEvent = None, **kwargs):
        """Log warning message."""
        
        self.log(LogLevel.WARNING, message, category, event, **kwargs)
    
    def error(self, message: str, category: LogCategory = LogCategory.SYSTEM, event: LogEvent = None, **kwargs):
        """Log error message."""
        
        self.log(LogLevel.ERROR, message, category, event, **kwargs)
    
    def critical(self, message: str, category: LogCategory = LogCategory.SYSTEM, event: LogEvent = None, **kwargs):
        """Log critical message."""
        
        self.log(LogLevel.CRITICAL, message, category, event, **kwargs)
    
    def _log_structured(self, log_data: Dict[str, Any]):
        """Log structured data in JSON format."""
        
        # Convert to JSON string
        json_data = json.dumps(log_data, default=str)
        
        # Log with appropriate level
        if log_data['level'] == 'DEBUG':
            self.logger.debug(json_data)
        elif log_data['level'] == 'INFO':
            self.logger.info(json_data)
        elif log_data['level'] == 'WARNING':
            self.logger.warning(json_data)
        elif log_data['level'] == 'ERROR':
            self.logger.error(json_data)
        elif log_data['level'] == 'CRITICAL':
            self.logger.critical(json_data)
    
    def _log_standard(self, level: LogLevel, message: str, log_data: Dict[str, Any]):
        """Log in standard format."""
        
        # Create formatted message
        formatted_message = f"[{log_data['category']}] {message}"
        
        if log_data['user_id']:
            formatted_message += f" | User: {log_data['user_id']}"
        
        if log_data['correlation_id']:
            formatted_message += f" | Correlation: {log_data['correlation_id']}"
        
        # Log with appropriate level
        if level == LogLevel.DEBUG:
            self.logger.debug(formatted_message)
        elif level == LogLevel.INFO:
            self.logger.info(formatted_message)
        elif level == LogLevel.WARNING:
            self.logger.warning(formatted_message)
        elif level == LogLevel.ERROR:
            self.logger.error(formatted_message)
        elif level == LogLevel.CRITICAL:
            self.logger.critical(formatted_message)
    
    def _filter_sensitive_data(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Filter out sensitive data from log data."""
        
        sensitive_fields = [
            'password',
            'token',
            'secret',
            'key',
            'authorization',
            'credit_card',
            'ssn',
            'passport',
            'id_number',
        ]
        
        filtered_data = {}
        
        for key, value in data.items():
            # Check if field is sensitive
            if any(sensitive in key.lower() for sensitive in sensitive_fields):
                filtered_data[key] = '***REDACTED***'
            else:
                filtered_data[key] = value
        
        return filtered_data


class PerformanceLogger:
    """
    Performance logging utility for monitoring application performance.
    
    Features:
    - Performance metrics collection
    - Slow query detection
    - Response time tracking
    - Resource usage monitoring
    """
    
    def __init__(self, config: Dict[str, Any] = None):
        self.config = config or {}
        self.logger = get_logger('performance')
        
        # Configuration
        self.enable_performance_logging = self.config.get('enable_performance_logging', True)
        self.slow_threshold = self.config.get('slow_threshold', 1000)  # milliseconds
        self.enable_memory_monitoring = self.config.get('enable_memory_monitoring', True)
        self.enable_cpu_monitoring = self.config.get('enable_cpu_monitoring', True)
        
        # Performance metrics storage
        self.metrics = {}
        self.slow_operations = []
        
    def log_operation(
        self,
        operation: str,
        duration: float,
        success: bool = True,
        **kwargs
    ):
        """
        Log operation performance.
        
        Args:
            operation: Operation name
            duration: Duration in seconds
            success: Whether operation was successful
            **kwargs: Additional metrics
        """
        
        if not self.enable_performance_logging:
            return
        
        # Convert duration to milliseconds
        duration_ms = duration * 1000
        
        # Create performance log data
        perf_data = {
            'timestamp': datetime.now(timezone.utc).isoformat(),
            'operation': operation,
            'duration_ms': round(duration_ms, 2),
            'success': success,
            'threshold_exceeded': duration_ms > self.slow_threshold,
        }
        
        # Add additional metrics
        if kwargs:
            perf_data.update(kwargs)
        
        # Log the performance data
        self._log_performance(perf_data)
        
        # Track slow operations
        if duration_ms > self.slow_threshold:
            self._log_slow_operation(operation, duration_ms, **kwargs)
        
        # Update metrics
        self._update_metrics(operation, duration_ms, success)
    
    def _log_performance(self, perf_data: Dict[str, Any]):
        """Log performance data."""
        
        json_data = json.dumps(perf_data, default=str)
        self.logger.info(f"Performance: {json_data}")
    
    def _log_slow_operation(self, operation: str, duration_ms: float, **kwargs):
        """Log slow operation alert."""
        
        slow_data = {
            'operation': operation,
            'duration_ms': duration_ms,
            'threshold_ms': self.slow_threshold,
            'timestamp': datetime.now(timezone.utc).isoformat(),
        }
        
        slow_data.update(kwargs)
        
        json_data = json.dumps(slow_data, default=str)
        self.logger.warning(f"Slow operation: {json_data}")
        
        # Add to slow operations list
        self.slow_operations.append(slow_data)
        
        # Keep only last 100 slow operations
        if len(self.slow_operations) > 100:
            self.slow_operations = self.slow_operations[-100:]
    
    def _update_metrics(self, operation: str, duration_ms: float, success: bool):
        """Update performance metrics."""
        
        if operation not in self.metrics:
            self.metrics[operation] = {
                'count': 0,
                'total_duration': 0,
                'average_duration': 0,
                'max_duration': 0,
                'min_duration': float('inf'),
                'success_count': 0,
                'failure_count': 0,
            }
        
        metrics = self.metrics[operation]
        metrics['count'] += 1
        metrics['total_duration'] += duration_ms
        metrics['average_duration'] = metrics['total_duration'] / metrics['count']
        metrics['max_duration'] = max(metrics['max_duration'], duration_ms)
        metrics['min_duration'] = min(metrics['min_duration'], duration_ms)
        
        if success:
            metrics['success_count'] += 1
        else:
            metrics['failure_count'] += 1
    
    def get_metrics(self) -> Dict[str, Any]:
        """Get performance metrics."""
        
        return {
            'metrics': self.metrics,
            'slow_operations': self.slow_operations,
            'slow_threshold_ms': self.slow_threshold,
        }
    
    def get_slow_operations(self) -> List[Dict[str, Any]]:
        """Get slow operations list."""
        
        return self.slow_operations
    
    def clear_metrics(self):
        """Clear all metrics."""
        
        self.metrics.clear()
        self.slow_operations.clear()


class AuditLogger:
    """
    Audit logging utility for security and compliance.
    
    Features:
    - Security event logging
    - User activity tracking
    - Compliance logging
    - Change tracking
    """
    
    def __init__(self, config: Dict[str, Any] = None):
        self.config = config or {}
        self.logger = get_logger('audit')
        
        # Configuration
        self.enable_audit_logging = self.config.get('enable_audit_logging', True)
        self.enable_user_activity = self.config.get('enable_user_activity', True)
        self.enable_security_events = self.config.get('enable_security_events', True)
        self.enable_compliance = self.config.get('enable_compliance', True)
        
    def log_user_activity(
        self,
        user_id: str,
        action: str,
        resource: str = None,
        details: Dict[str, Any] = None,
        success: bool = True,
        ip_address: str = None,
        user_agent: str = None,
    ):
        """
        Log user activity for audit purposes.
        
        Args:
            user_id: User ID
            action: Action performed
            resource: Resource accessed/modified
            details: Additional details
            success: Whether action was successful
            ip_address: Client IP address
            user_agent: User agent string
        """
        
        if not self.enable_audit_logging:
            return
        
        audit_data = {
            'timestamp': datetime.now(timezone.utc).isoformat(),
            'user_id': user_id,
            'action': action,
            'resource': resource,
            'success': success,
            'ip_address': ip_address,
            'user_agent': user_agent,
            'audit_type': 'user_activity',
        }
        
        if details:
            audit_data['details'] = details
        
        # Log audit data
        self._log_audit(audit_data)
    
    def log_security_event(
        self,
        event_type: str,
        severity: str,
        description: str,
        user_id: str = None,
        ip_address: str = None,
        details: Dict[str, Any] = None,
    ):
        """
        Log security events.
        
        Args:
            event_type: Type of security event
            severity: Severity level
            description: Event description
            user_id: Associated user ID
            ip_address: Client IP address
            details: Additional details
        """
        
        if not self.enable_audit_logging or not self.enable_security_events:
            return
        
        audit_data = {
            'timestamp': datetime.now(timezone.utc).isoformat(),
            'audit_type': 'security_event',
            'event_type': event_type,
            'severity': severity,
            'description': description,
            'user_id': user_id,
            'ip_address': ip_address,
        }
        
        if details:
            audit_data['details'] = details
        
        # Log security event
        self._log_audit(audit_data)
    
    def log_compliance_event(
        self,
        regulation: str,
        requirement: str,
        action: str,
        user_id: str = None,
        details: Dict[str, Any] = None,
    ):
        """
        Log compliance events.
        
        Args:
            regulation: Regulation name
            requirement: Specific requirement
            action: Action taken
            user_id: Associated user ID
            details: Additional details
        """
        
        if not self.enable_audit_logging or not self.enable_compliance:
            return
        
        audit_data = {
            'timestamp': datetime.now(timezone.utc).isoformat(),
            'audit_type': 'compliance',
            'regulation': regulation,
            'requirement': requirement,
            'action': action,
            'user_id': user_id,
        }
        
        if details:
            audit_data['details'] = details
        
        # Log compliance event
        self._log_audit(audit_data)
    
    def _log_audit(self, audit_data: Dict[str, Any]):
        """Log audit data."""
        
        json_data = json.dumps(audit_data, default=str)
        self.logger.info(f"Audit: {json_data}")


# Global instances
performance_logger = PerformanceLogger()
audit_logger = AuditLogger()


# Performance monitoring decorator
def monitor_performance(operation_name: str = None):
    """
    Decorator for performance monitoring.
    
    Args:
        operation_name: Custom operation name
        
    Returns:
        Decorated function
    """
    
    def decorator(func):
        @wraps(func)
        async def async_wrapper(*args, **kwargs):
            start_time = time.time()
            success = False
            
            try:
                result = await func(*args, **kwargs)
                success = True
                return result
            except Exception as e:
                # Log error if monitoring enabled
                performance_logger.log_operation(
                    operation_name or func.__name__,
                    time.time() - start_time,
                    success=False,
                    error=str(e),
                    error_type=type(e).__name__
                )
                raise
            finally:
                # Log performance
                performance_logger.log_operation(
                    operation_name or func.__name__,
                    time.time() - start_time,
                    success=success
                )
        
        @wraps(func)
        def sync_wrapper(*args, **kwargs):
            start_time = time.time()
            success = False
            
            try:
                result = func(*args, **kwargs)
                success = True
                return result
            except Exception as e:
                # Log error if monitoring enabled
                performance_logger.log_operation(
                    operation_name or func.__name__,
                    time.time() - start_time,
                    success=False,
                    error=str(e),
                    error_type=type(e).__name__
                )
                raise
            finally:
                # Log performance
                performance_logger.log_operation(
                    operation_name or func.__name__,
                    time.time() - start_time,
                    success=success
                )
        
        # Return appropriate wrapper based on function type
        if asyncio.iscoroutinefunction(func):
            return async_wrapper
        else:
            return sync_wrapper
    
    return decorator


# Context manager for performance monitoring
@contextlib.asynccontextmanager
async def performance_context(operation_name: str):
    """
    Context manager for performance monitoring.
    
    Args:
        operation_name: Name of the operation
        
    Yields:
        Performance context
    """
    
    start_time = time.time()
    success = False
    
    try:
        yield
        success = True
    except Exception as e:
        # Log error
        performance_logger.log_operation(
            operation_name,
            time.time() - start_time,
            success=False,
            error=str(e),
            error_type=type(e).__name__
        )
        raise
    finally:
        # Log performance
        performance_logger.log_operation(
            operation_name,
            time.time() - start_time,
            success=success
        )


# Factory functions for logger creation
def create_structured_logger(name: str, config: Dict[str, Any] = None) -> StructuredLogger:
    """Create a structured logger instance."""
    
    return StructuredLogger(name, config)


def create_performance_logger(config: Dict[str, Any] = None) -> PerformanceLogger:
    """Create a performance logger instance."""
    
    return PerformanceLogger(config)


def create_audit_logger(config: Dict[str, Any] = None) -> AuditLogger:
    """Create an audit logger instance."""
    
    return AuditLogger(config)