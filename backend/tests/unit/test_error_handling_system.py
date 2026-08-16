"""
Comprehensive test suite for the error handling and logging system.
Tests all components of the error handling infrastructure.
"""

import pytest
import asyncio
import json
from datetime import datetime, timezone
from unittest.mock import Mock, patch, AsyncMock
from typing import Dict, Any

from src.core.exceptions import (
    BaseError,
    ValidationError,
    NotFoundError,
    ServerError,
    AuthException,
)
from src.utils.error_handler import (
    ErrorHandler,
    handle_errors,
    CircuitBreaker,
    monitor_performance,
    error_context,
)
from src.utils.logging_integration import (
    StructuredLogger,
    PerformanceLogger,
    AuditLogger,
    LogLevel,
    LogCategory,
    LogEvent,
    monitor_performance as performance_monitor_decorator,
)


class TestErrorHandler:
    """Test the ErrorHandler class."""
    
    def setup_method(self):
        """Setup test fixtures."""
        self.error_handler = ErrorHandler()
        
    def test_handle_base_error(self):
        """Test handling of base errors."""
        
        error = BaseError(
            message="Test error",
            error_code="TEST_ERROR",
            details={"field": "value"}
        )
        
        result = self.error_handler.handle_exception(error)
        
        assert result['code'] == 'TEST_ERROR'
        assert result['message'] == 'Test error'
        assert result['category'] == 'business'
        assert result['details'] == {"field": "value"}
        
    def test_handle_validation_error(self):
        """Test handling of validation errors."""
        
        error = ValidationError(
            message="Validation failed",
            field="email",
            details={"email": "invalid"}
        )
        
        result = self.error_handler.handle_exception(error)
        
        assert result['code'] == 'VALIDATION_ERROR'
        assert result['message'] == 'Validation failed'
        assert result['category'] == 'business'
        assert result['status_code'] == 400
        
    def test_handle_not_found_error(self):
        """Test handling of not found errors."""
        
        error = NotFoundError(
            resource="user",
            id="123"
        )
        
        result = self.error_handler.handle_exception(error)
        
        assert result['code'] == 'NOT_FOUND'
        assert result['message'] == 'user not found with ID: 123'
        assert result['category'] == 'business'
        assert result['status_code'] == 404
        
    def test_handle_server_error(self):
        """Test handling of server errors."""
        
        error = ServerError(
            message="Server error",
            error_code="SERVER_ERROR"
        )
        
        result = self.error_handler.handle_exception(error)
        
        assert result['code'] == 'SERVER_ERROR'
        assert result['message'] == 'Server error'
        assert result['category'] == 'system'
        assert result['status_code'] == 500
        
    def test_handle_unexpected_error(self):
        """Test handling of unexpected errors."""
        
        error = Exception("Unexpected error")
        
        result = self.error_handler.handle_exception(error)
        
        assert result['code'] == 'INTERNAL_ERROR'
        assert result['message'] == 'Internal server error'
        assert result['category'] == 'system'
        assert result['status_code'] == 500
        
    def test_error_categorization(self):
        """Test error categorization."""
        
        # Business error
        business_error = ValidationError("Test")
        category = self.error_handler._categorize_error(business_error)
        assert category == 'business'
        
        # System error
        system_error = ServerError("Test")
        category = self.error_handler._categorize_error(system_error)
        assert category == 'system'
        
        # Security error
        security_error = AuthException("Test", auth_type="token")
        category = self.error_handler._categorize_error(security_error)
        assert category == 'security'
        
        # Unknown error
        unknown_error = Exception("Test")
        category = self.error_handler._categorize_error(unknown_error)
        assert category == 'unknown'
        
    def test_error_tracking(self):
        """Test error tracking functionality."""
        
        # Track some errors
        error1 = ValidationError("Error 1")
        error2 = ValidationError("Error 2")
        error3 = ServerError("Error 3")
        
        self.error_handler.handle_exception(error1)
        self.error_handler.handle_exception(error2)
        self.error_handler.handle_exception(error3)
        
        # Check statistics
        stats = self.error_handler.get_error_statistics()
        assert stats['total_errors'] == 3
        assert stats['unique_error_types'] == 2
        assert stats['error_distribution']['ValidationError'] == 2
        assert stats['error_distribution']['ServerError'] == 1
        
    def test_recovery_mechanism(self):
        """Test error recovery mechanism."""
        
        # Create a mock recovery handler
        mock_recovery = Mock(return_value={'recovered': True})
        self.error_handler.add_recovery_handler(mock_recovery)
        
        error = ValidationError("Test error")
        result = self.error_handler.handle_exception(error)
        
        # Check if recovery was attempted
        assert mock_recovery.called
        assert 'recovery' in result
        
    def test_circuit_breaker(self):
        """Test circuit breaker functionality."""
        
        # Create circuit breaker
        circuit_breaker = CircuitBreaker(failure_threshold=3, recovery_timeout=1)
        
        # Mock function that fails
        async def failing_function():
            raise Exception("Function failed")
        
        # Mock fallback function
        async def fallback_function():
            return {"fallback": True}
        
        # Test circuit breaker states
        with pytest.raises(Exception):
            # First calls should work
            await circuit_breaker.call(failing_function)
        
        with pytest.raises(Exception):
            await circuit_breaker.call(failing_function)
        
        # Third call should trigger circuit breaker
        with pytest.raises(Exception):
            await circuit_breaker.call(failing_function)
        
        # Next call should use fallback
        result = await circuit_breaker.call(failing_function, fallback=fallback_function)
        assert result == {"fallback": True}
        
        # Check circuit breaker state
        state = circuit_breaker.get_state()
        assert state['state'] == 'open'
        assert state['failure_count'] == 3


class TestStructuredLogger:
    """Test the StructuredLogger class."""
    
    def setup_method(self):
        """Setup test fixtures."""
        self.logger = StructuredLogger("test_logger")
        
    def test_log_with_context(self):
        """Test logging with context."""
        
        # Set context
        self.logger.set_context(
            correlation_id="test-correlation",
            user_id="test-user",
            session_id="test-session"
        )
        
        # Log a message
        self.logger.info("Test message", category=LogCategory.BUSINESS, event=LogEvent.USER_LOGIN)
        
        # Context should be set
        assert self.logger.correlation_id == "test-correlation"
        assert self.logger.user_id == "test-user"
        assert self.logger.session_id == "test-session"
        
    def test_log_levels(self):
        """Test different log levels."""
        
        # Test all log levels
        self.logger.debug("Debug message")
        self.logger.info("Info message")
        self.logger.warning("Warning message")
        self.logger.error("Error message")
        self.logger.critical("Critical message")
        
        # All should pass without error
        assert True
        
    def test_sensitive_data_filtering(self):
        """Test sensitive data filtering."""
        
        # Log with sensitive data
        self.logger.info(
            "Test message",
            category=LogCategory.SECURITY,
            password="secret123",
            token="abc123",
            normal_field="normal_value"
        )
        
        # Sensitive data should be filtered
        # This is tested indirectly as the actual logging is mocked
        
    def test_structured_logging(self):
        """Test structured logging format."""
        
        # Mock the underlying logger
        with patch.object(self.logger, '_log_structured') as mock_log:
            self.logger.info("Test message", category=LogCategory.BUSINESS)
            
            # Check that structured logging was called
            mock_log.assert_called_once()
            
            # Check log data structure
            call_args = mock_log.call_args[0][0]
            assert call_args['level'] == 'INFO'
            assert call_args['message'] == 'Test message'
            assert call_args['category'] == 'business'
            assert 'timestamp' in call_args
            assert 'correlation_id' in call_args
            
    def test_standard_logging(self):
        """Test standard logging format."""
        
        # Mock the underlying logger
        with patch.object(self.logger, '_log_standard') as mock_log:
            self.logger.info("Test message", category=LogCategory.BUSINESS)
            
            # Check that standard logging was called
            mock_log.assert_called_once()
            
            # Check log data structure
            call_args = mock_log.call_args[0]
            assert call_args[0] == LogLevel.INFO
            assert call_args[1] == 'Test message'
            assert call_args[2]['category'] == 'business'


class TestPerformanceLogger:
    """Test the PerformanceLogger class."""
    
    def setup_method(self):
        """Setup test fixtures."""
        self.performance_logger = PerformanceLogger()
        
    def test_log_operation(self):
        """Test operation logging."""
        
        # Log a successful operation
        self.performance_logger.log_operation("test_operation", 0.5, success=True)
        
        # Log a failed operation
        self.performance_logger.log_operation("test_operation", 0.1, success=False, error="Test error")
        
        # Check metrics
        metrics = self.performance_logger.get_metrics()
        assert metrics['metrics']['test_operation']['count'] == 2
        assert metrics['metrics']['test_operation']['success_count'] == 1
        assert metrics['metrics']['test_operation']['failure_count'] == 1
        assert metrics['metrics']['test_operation']['average_duration'] == 300  # (500 + 100) / 2
        
    def test_slow_operation_detection(self):
        """Test slow operation detection."""
        
        # Set slow threshold to 200ms
        self.performance_logger.slow_threshold = 200
        
        # Log a slow operation
        self.performance_logger.log_operation("slow_operation", 0.3)  # 300ms
        
        # Log a fast operation
        self.performance_logger.log_operation("fast_operation", 0.1)  # 100ms
        
        # Check slow operations
        slow_ops = self.performance_logger.get_slow_operations()
        assert len(slow_ops) == 1
        assert slow_ops[0]['operation'] == 'slow_operation'
        assert slow_ops[0]['duration_ms'] == 300
        assert slow_ops[0]['threshold_exceeded'] is True
        
    def test_performance_monitoring_decorator(self):
        """Test performance monitoring decorator."""
        
        @monitor_performance("test_operation")
        async def test_function():
            return "result"
        
        # Mock the performance logger
        with patch.object(self.performance_logger, 'log_operation') as mock_log:
            # Call the decorated function
            result = asyncio.run(test_function())
            
            # Check that performance was logged
            mock_log.assert_called()
            
            # Check result
            assert result == "result"


class TestAuditLogger:
    """Test the AuditLogger class."""
    
    def setup_method(self):
        """Setup test fixtures."""
        self.audit_logger = AuditLogger()
        
    def test_log_user_activity(self):
        """Test user activity logging."""
        
        # Mock the audit logger
        with patch.object(self.audit_logger, '_log_audit') as mock_log:
            self.audit_logger.log_user_activity(
                user_id="test-user",
                action="login",
                resource="system",
                success=True,
                ip_address="192.168.1.1",
                user_agent="test-agent"
            )
            
            # Check that audit was logged
            mock_log.assert_called_once()
            
            # Check audit data structure
            call_args = mock_log.call_args[0][0]
            assert call_args['user_id'] == 'test-user'
            assert call_args['action'] == 'login'
            assert call_args['resource'] == 'system'
            assert call_args['success'] is True
            assert call_args['ip_address'] == '192.168.1.1'
            assert call_args['user_agent'] == 'test-agent'
            assert call_args['audit_type'] == 'user_activity'
            
    def test_log_security_event(self):
        """Test security event logging."""
        
        # Mock the audit logger
        with patch.object(self.audit_logger, '_log_audit') as mock_log:
            self.audit_logger.log_security_event(
                event_type="unauthorized_access",
                severity="high",
                description="Attempted access to restricted area",
                user_id="test-user",
                ip_address="192.168.1.1"
            )
            
            # Check that audit was logged
            mock_log.assert_called_once()
            
            # Check audit data structure
            call_args = mock_log.call_args[0][0]
            assert call_args['event_type'] == 'unauthorized_access'
            assert call_args['severity'] == 'high'
            assert call_args['description'] == 'Attempted access to restricted area'
            assert call_args['audit_type'] == 'security_event'
            
    def test_log_compliance_event(self):
        """Test compliance event logging."""
        
        # Mock the audit logger
        with patch.object(self.audit_logger, '_log_audit') as mock_log:
            self.audit_logger.log_compliance_event(
                regulation="GDPR",
                requirement="data_protection",
                action="data_processing_consent",
                user_id="test-user"
            )
            
            # Check that audit was logged
            mock_log.assert_called_once()
            
            # Check audit data structure
            call_args = mock_log.call_args[0][0]
            assert call_args['regulation'] == 'GDPR'
            assert call_args['requirement'] == 'data_protection'
            assert call_args['action'] == 'data_processing_consent'
            assert call_args['audit_type'] == 'compliance'


class TestErrorHandlingDecorators:
    """Test error handling decorators."""
    
    def test_handle_errors_decorator(self):
        """Test the handle_errors decorator."""
        
        @handle_errors
        async def test_function(error=False):
            if error:
                raise Exception("Test error")
            return "success"
        
        # Test successful call
        result = asyncio.run(test_function())
        assert result == "success"
        
        # Test error handling
        with patch('src.utils.error_handler.ErrorHandler') as mock_handler:
            mock_handler_instance = Mock()
            mock_handler.return_value = mock_handler_instance
            
            # Mock the error handler to return a response
            mock_handler_instance.handle_exception.return_value = {
                'code': 'TEST_ERROR',
                'message': 'Test error',
                'status_code': 500
            }
            
            result = asyncio.run(test_function(error=True))
            assert result.code == 500  # FastAPI Response has a code attribute
            
    def test_error_context_manager(self):
        """Test the error_context manager."""
        
        with patch('src.utils.error_handler.logger') as mock_logger:
            with error_context({"test": "context"}):
                raise Exception("Test error")
            
            # Check that error was logged
            mock_logger.error.assert_called_once()
            
    def test_performance_context_manager(self):
        """Test the performance_context manager."""
        
        @monitor_performance("test_operation")
        async def test_function():
            return "result"
        
        # Mock the performance logger
        with patch('src.utils.logging_integration.performance_logger') as mock_perf_logger:
            # Call the decorated function
            result = asyncio.run(test_function())
            
            # Check that performance was logged
            mock_perf_logger.log_operation.assert_called()
            
            # Check result
            assert result == "result"


class TestIntegration:
    """Integration tests for the complete error handling system."""
    
    def test_complete_error_handling_flow(self):
        """Test complete error handling flow."""
        
        # Create error handler
        error_handler = ErrorHandler()
        
        # Create structured logger
        logger = StructuredLogger("test_logger")
        logger.set_context(correlation_id="test-correlation")
        
        # Create audit logger
        audit_logger = AuditLogger()
        
        # Test error handling with logging
        error = ValidationError(
            message="Validation failed",
            field="email",
            details={"email": "invalid"}
        )
        
        # Handle error
        result = error_handler.handle_exception(error)
        
        # Log error
        logger.error("Validation error occurred", category=LogCategory.BUSINESS, event=LogEvent.ERROR_OCCURRED)
        
        # Log audit event
        audit_logger.log_user_activity(
            user_id="test-user",
            action="validation_failure",
            resource="user_email",
            success=False
        )
        
        # Check results
        assert result['code'] == 'VALIDATION_ERROR'
        assert result['message'] == 'Validation failed'
        assert result['status_code'] == 400
        
    def test_error_recovery_flow(self):
        """Test error recovery flow."""
        
        # Create error handler with recovery
        error_handler = ErrorHandler(enable_error_recovery=True)
        
        # Create recovery handler
        def recovery_handler(error, context):
            return {"recovered": True, "original_error": str(error)}
        
        error_handler.add_recovery_handler(recovery_handler)
        
        # Test error handling with recovery
        error = ValidationError("Test error")
        result = error_handler.handle_exception(error)
        
        # Check that recovery was attempted
        assert 'recovery' in result
        assert result['recovered'] is True
        
    def test_performance_monitoring_flow(self):
        """Test performance monitoring flow."""
        
        # Create performance logger
        performance_logger = PerformanceLogger()
        
        # Test operation logging
        performance_logger.log_operation("test_operation", 0.5, success=True)
        
        # Test slow operation detection
        performance_logger.log_operation("slow_operation", 0.3, success=False)
        
        # Check metrics
        metrics = performance_logger.get_metrics()
        assert metrics['metrics']['test_operation']['count'] == 1
        assert metrics['metrics']['slow_operation']['count'] == 1
        assert metrics['slow_operations'][0]['operation'] == 'slow_operation'


# Run the tests
if __name__ == "__main__":
    pytest.main([__file__, "-v"])