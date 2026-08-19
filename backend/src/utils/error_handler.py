"""
Comprehensive error handling utilities for the Edu-Flow backend.
Provides centralized error management, logging, and recovery mechanisms.
"""

import logging
import traceback
from datetime import datetime, timezone
from typing import Any, Dict, Optional, Union, Callable
from functools import wraps
from contextlib import contextmanager
import asyncio

from fastapi import HTTPException, Request
from fastapi.responses import JSONResponse
from starlette.responses import Response

from ..core.exceptions import BaseError, ValidationError, NotFoundError, ServerError
from ..core.logging import get_logger, performance_monitor

logger = get_logger(__name__)


class ErrorHandler:
    """
    Centralized error handling utility class.
    
    Features:
    - Exception categorization and handling
    - Error logging with context
    - Recovery mechanisms
    - Performance monitoring
    - Error rate limiting
    """
    
    def __init__(self, config: Dict[str, Any] = None):
        self.config = config or {}
        self.error_counts = {}
        self.recovery_attempts = {}
        self.fallback_handlers = []
        
        # Configuration
        self.max_error_details = self.config.get('max_error_details', 1000)
        self.enable_performance_tracking = self.config.get('enable_performance_tracking', True)
        self.enable_error_recovery = self.config.get('enable_error_recovery', True)
        self.max_recovery_attempts = self.config.get('max_recovery_attempts', 3)
        
    def handle_exception(self, error: Exception, context: Dict[str, Any] = None) -> Dict[str, Any]:
        """
        Handle exception and return standardized error response.
        
        Args:
            error: The exception to handle
            context: Additional context for error handling
            
        Returns:
            Dictionary containing error details
        """
        
        # Get error context
        error_context = context or {}
        error_context.update({
            'timestamp': datetime.now(timezone.utc).isoformat(),
            'error_type': type(error).__name__,
            'error_message': str(error),
            'traceback': traceback.format_exc(),
        })
        
        # Track error counts
        self._track_error(error)
        
        # Categorize error
        error_category = self._categorize_error(error)
        
        # Handle different error types
        if isinstance(error, ValidationError):
            return self._handle_validation_error(error, error_context)
        elif isinstance(error, NotFoundError):
            return self._handle_not_found_error(error, error_context)
        elif isinstance(error, ServerError):
            return self._handle_server_error(error, error_context)
        elif isinstance(error, BaseError):
            return self._handle_base_error(error, error_context)
        else:
            return self._handle_unexpected_error(error, error_context)
    
    def _categorize_error(self, error: Exception) -> str:
        """Categorize error into appropriate category."""
        
        error_type = type(error).__name__
        
        # Business logic errors
        business_errors = [
            'ValidationError',
            'BusinessLogicError',
            'DataIntegrityError',
            'ProcessingError',
        ]
        
        # System errors
        system_errors = [
            'ServerError',
            'DatabaseError',
            'NetworkError',
            'StorageError',
        ]
        
        # Security errors
        security_errors = [
            'AuthenticationError',
            'AuthorizationError',
            'SecurityError',
            'PermissionError',
        ]
        
        if error_type in business_errors:
            return 'business'
        elif error_type in system_errors:
            return 'system'
        elif error_type in security_errors:
            return 'security'
        else:
            return 'unknown'
    
    def _track_error(self, error: Exception):
        """Track error statistics."""
        
        error_type = type(error).__name__
        self.error_counts[error_type] = self.error_counts.get(error_type, 0) + 1
        
        # Log error rate warnings
        total_errors = sum(self.error_counts.values())
        if total_errors % 100 == 0:
            logger.warning(f"Total errors handled: {total_errors} | Unique error types: {len(self.error_counts)}")
    
    def _handle_base_error(self, error: BaseError, context: Dict[str, Any]) -> Dict[str, Any]:
        """Handle base application errors."""
        
        error_data = {
            'code': error.error_code,
            'message': error.message,
            'details': error.details,
            'category': 'business',
            'status_code': getattr(error, 'status_code', 400),
        }
        
        # Log error
        logger.error(f"Base error: {error.error_code} | {error.message}", extra=context)
        
        # Try recovery if enabled
        if self.enable_error_recovery:
            recovery_result = self._attempt_recovery(error, context)
            if recovery_result:
                error_data['recovery'] = recovery_result
        
        return error_data
    
    def _handle_validation_error(self, error: ValidationError, context: Dict[str, Any]) -> Dict[str, Any]:
        """Handle validation errors."""
        
        error_data = {
            'code': 'VALIDATION_ERROR',
            'message': error.message,
            'details': error.details,
            'category': 'business',
            'status_code': 400,
        }
        
        # Log validation error
        logger.warning(f"Validation error: {error.message}", extra=context)
        
        # Try recovery
        if self.enable_error_recovery:
            recovery_result = self._attempt_recovery(error, context)
            if recovery_result:
                error_data['recovery'] = recovery_result
        
        return error_data
    
    def _handle_not_found_error(self, error: NotFoundError, context: Dict[str, Any]) -> Dict[str, Any]:
        """Handle not found errors."""
        
        error_data = {
            'code': 'NOT_FOUND',
            'message': error.message,
            'details': error.details,
            'category': 'business',
            'status_code': 404,
        }
        
        # Log not found error
        logger.warning(f"Not found error: {error.message}", extra=context)
        
        return error_data
    
    def _handle_server_error(self, error: ServerError, context: Dict[str, Any]) -> Dict[str, Any]:
        """Handle server errors."""
        
        error_data = {
            'code': 'SERVER_ERROR',
            'message': error.message,
            'details': error.details,
            'category': 'system',
            'status_code': 500,
        }
        
        # Log server error
        logger.error(f"Server error: {error.message}", extra=context)
        
        # Try recovery
        if self.enable_error_recovery:
            recovery_result = self._attempt_recovery(error, context)
            if recovery_result:
                error_data['recovery'] = recovery_result
        
        return error_data
    
    def _handle_unexpected_error(self, error: Exception, context: Dict[str, Any]) -> Dict[str, Any]:
        """Handle unexpected/unhandled errors."""
        
        error_data = {
            'code': 'INTERNAL_ERROR',
            'message': 'Internal server error',
            'details': {
                'original_error': str(error),
                'error_type': type(error).__name__,
            },
            'category': 'system',
            'status_code': 500,
        }
        
        # Log unexpected error
        logger.critical(f"Unexpected error: {type(error).__name__} | {str(error)}", extra=context)
        
        # Try recovery
        if self.enable_error_recovery:
            recovery_result = self._attempt_recovery(error, context)
            if recovery_result:
                error_data['recovery'] = recovery_result
        
        return error_data
    
    def _attempt_recovery(self, error: Exception, context: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Attempt error recovery."""
        
        error_type = type(error).__name__
        
        # Check if we've already tried recovery
        recovery_key = f"{error_type}_{id(error)}"
        attempts = self.recovery_attempts.get(recovery_key, 0)
        
        if attempts >= self.max_recovery_attempts:
            logger.warning(f"Max recovery attempts reached for {error_type}")
            return None
        
        # Increment recovery attempts
        self.recovery_attempts[recovery_key] = attempts + 1
        
        # Try each fallback handler
        for handler in self.fallback_handlers:
            try:
                recovery_result = handler(error, context)
                if recovery_result:
                    logger.info(f"Error recovery successful for {error_type}")
                    return recovery_result
            except Exception as recovery_error:
                logger.warning(f"Recovery failed: {recovery_error}")
        
        return None
    
    def add_recovery_handler(self, handler: Callable[[Exception, Dict[str, Any]], Optional[Dict[str, Any]]]):
        """Add a custom recovery handler."""
        
        self.fallback_handlers.append(handler)
    
    def get_error_statistics(self) -> Dict[str, Any]:
        """Get error handling statistics."""
        
        total_errors = sum(self.error_counts.values())
        unique_errors = len(self.error_counts)
        total_recovery_attempts = sum(self.recovery_attempts.values())
        successful_recoveries = len([r for r in self.recovery_attempts.values() if r > 0])
        
        return {
            'total_errors': total_errors,
            'unique_error_types': unique_errors,
            'error_distribution': self.error_counts,
            'total_recovery_attempts': total_recovery_attempts,
            'successful_recoveries': successful_recoveries,
            'recovery_rate': successful_recoveries / total_recovery_attempts if total_recovery_attempts > 0 else 0,
            'enable_error_recovery': self.enable_error_recovery,
        }


def handle_errors(func: Callable) -> Callable:
    """
    Decorator for automatic error handling.
    
    Args:
        func: Function to wrap with error handling
        
    Returns:
        Wrapped function with error handling
    """
    
    @wraps(func)
    async def async_wrapper(*args, **kwargs):
        try:
            return await func(*args, **kwargs)
        except Exception as e:
            # Get request context if available
            context = {}
            if args and len(args) > 0 and hasattr(args[0], 'state'):
                context = getattr(args[0].state, 'context', {})
            
            # Use error handler
            error_handler = ErrorHandler()
            error_response = error_handler.handle_exception(e, context)
            
            # Log error
            logger.error(f"Error in {func.__name__}: {str(e)}", extra={
                'function': func.__name__,
                'error_type': type(e).__name__,
                'context': context,
            })
            
            # Return error response
            return JSONResponse(
                status_code=error_response['status_code'],
                content={'error': error_response}
            )
    
    @wraps(func)
    def sync_wrapper(*args, **kwargs):
        try:
            return func(*args, **kwargs)
        except Exception as e:
            # Get request context if available
            context = {}
            if args and len(args) > 0 and hasattr(args[0], 'state'):
                context = getattr(args[0].state, 'context', {})
            
            # Use error handler
            error_handler = ErrorHandler()
            error_response = error_handler.handle_exception(e, context)
            
            # Log error
            logger.error(f"Error in {func.__name__}: {str(e)}", extra={
                'function': func.__name__,
                'error_type': type(e).__name__,
                'context': context,
            })
            
            # Return error response
            return JSONResponse(
                status_code=error_response['status_code'],
                content={'error': error_response}
            )
    
    # Return appropriate wrapper based on function type
    if asyncio.iscoroutinefunction(func):
        return async_wrapper
    else:
        return sync_wrapper


class CircuitBreaker:
    """
    Circuit breaker implementation for handling service failures.
    
    Features:
    - Failure threshold detection
    - Automatic recovery
    - Fallback mechanisms
    - State monitoring
    """
    
    def __init__(self, failure_threshold: int = 5, recovery_timeout: int = 60, timeout: int = 30):
        self.failure_threshold = failure_threshold
        self.recovery_timeout = recovery_timeout
        self.timeout = timeout
        
        self.failure_count = 0
        self.last_failure_time = None
        self.state = 'closed'  # closed, open, half_open
        self.success_count = 0
        self.call_count = 0
        
    async def call(self, func: Callable, *args, fallback: Callable = None, **kwargs) -> Any:
        """
        Call function with circuit breaker protection.
        
        Args:
            func: Function to call
            fallback: Fallback function if circuit is open
            
        Returns:
            Function result or fallback result
        """
        
        self.call_count += 1
        
        # Check if circuit should be open
        if self.state == 'open':
            if self._should_attempt_recovery():
                self.state = 'half_open'
            elif fallback:
                return await fallback(*args, **kwargs)
            else:
                raise HTTPException(status_code=503, detail="Service temporarily unavailable")
        
        try:
            # Set timeout for the call
            result = await asyncio.wait_for(func(*args, **kwargs), timeout=self.timeout)
            
            # Reset on success
            self._on_success()
            return result
            
        except Exception as e:
            # Handle failure
            self._on_failure(e)
            
            # Try fallback if available
            if fallback:
                return await fallback(*args, **kwargs)
            
            raise e
    
    def _should_attempt_recovery(self) -> bool:
        """Check if recovery should be attempted."""
        
        if self.last_failure_time is None:
            return True
        
        return (datetime.now(timezone.utc) - self.last_failure_time).seconds > self.recovery_timeout
    
    def _on_success(self):
        """Handle successful call."""
        
        self.failure_count = 0
        self.success_count += 1
        
        if self.state == 'half_open':
            if self.success_count >= 3:  # Success threshold for recovery
                self.state = 'closed'
                self.success_count = 0
                logger.info("Circuit breaker closed after successful recovery")
    
    def _on_failure(self, error: Exception):
        """Handle failed call."""
        
        self.failure_count += 1
        self.last_failure_time = datetime.now(timezone.utc)
        
        if self.failure_count >= self.failure_threshold:
            self.state = 'open'
            logger.warning(f"Circuit breaker opened after {self.failure_count} failures")
    
    def get_state(self) -> Dict[str, Any]:
        """Get current circuit breaker state."""
        
        return {
            'state': self.state,
            'failure_count': self.failure_count,
            'success_count': self.success_count,
            'call_count': self.call_count,
            'last_failure_time': self.last_failure_time.isoformat() if self.last_failure_time else None,
        }


# Global error handler instance
error_handler = ErrorHandler()


# Context manager for error handling
@contextmanager
def error_context(context: Dict[str, Any] = None):
    """
    Context manager for error handling with additional context.
    
    Args:
        context: Additional context for error handling
        
    Yields:
        Context dictionary
    """
    
    context = context or {}
    try:
        yield context
    except Exception as e:
        # Add context to error
        error_context = context.copy()
        error_context['error'] = str(e)
        error_context['error_type'] = type(e).__name__
        
        # Log error
        logger.error(f"Error in context: {str(e)}", extra=error_context)
        
        # Re-raise the error
        raise


# Performance monitoring decorator
def monitor_performance(func: Callable) -> Callable:
    """
    Decorator for performance monitoring.
    
    Args:
        func: Function to monitor
        
    Returns:
        Wrapped function with performance monitoring
    """
    
    @wraps(func)
    async def async_wrapper(*args, **kwargs):
        start_time = datetime.now(timezone.utc)
        
        try:
            result = await func(*args, **kwargs)
            duration = (datetime.now(timezone.utc) - start_time).total_seconds()
            
            # Log performance
            performance_monitor.record(
                func.__name__,
                duration=duration,
                success=True,
                metadata={
                    'function': func.__name__,
                    'duration_ms': duration * 1000,
                }
            )
            
            return result
            
        except Exception as e:
            duration = (datetime.now(timezone.utc) - start_time).total_seconds()
            
            # Log performance with error
            performance_monitor.record(
                func.__name__,
                duration=duration,
                success=False,
                error=str(e),
                metadata={
                    'function': func.__name__,
                    'duration_ms': duration * 1000,
                    'error': str(e),
                }
            )
            
            raise
    
    @wraps(func)
    def sync_wrapper(*args, **kwargs):
        start_time = datetime.now(timezone.utc)
        
        try:
            result = func(*args, **kwargs)
            duration = (datetime.now(timezone.utc) - start_time).total_seconds()
            
            # Log performance
            func_name = getattr(func, '__name__', str(func))
            performance_monitor.record(
                func_name,
                duration=duration,
                success=True,
                metadata={
                    'function': func_name,
                    'duration_ms': duration * 1000,
                }
            )
            
            return result
            
        except Exception as e:
            duration = (datetime.now(timezone.utc) - start_time).total_seconds()
            
            # Log performance with error
            performance_monitor.record(
                func.__name__,
                duration=duration,
                success=False,
                error=str(e),
                metadata={
                    'function': func.__name__,
                    'duration_ms': duration * 1000,
                    'error': str(e),
                }
            )
            
            raise
    
    # Return appropriate wrapper based on function type
    if asyncio.iscoroutinefunction(func):
        return async_wrapper
    else:
        return sync_wrapper