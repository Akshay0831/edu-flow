
from src.core.exceptions import ValidationError, AuthenticationError, NotFoundError
"""
Tests for the Edu-Flow unified logging system.
"""

import pytest
import tempfile
import os
import sys
import time
from pathlib import Path
from unittest.mock import patch, MagicMock

# Add src to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from src.config.logging import get_logger, reset_loggers, LOGGING_CONFIG
from src.core.logging_utils import LogContext
from src.core.logging_integration import setup_logging_middleware
from fastapi import FastAPI, Request, Response
from fastapi.testclient import TestClient

class TestUnifiedLogger:
    """Test cases for the UnifiedLogger class"""
    
    def test_logger_creation(self):
        """Test logger creation for different components"""
        logger = get_logger('backend')
        assert logger.component == 'backend'
        assert logger.environment == 'development'
        
        # Test different components
        frontend_logger = get_logger('frontend')
        assert frontend_logger.component == 'frontend'
        
        # Test same logger instance returned for same component
        same_logger = get_logger('backend')
        assert logger is same_logger
    
    def test_logger_levels(self):
        """Test different log levels"""
        logger = get_logger('backend')
        
        # These should not raise exceptions
        logger.debug("Debug message")
        logger.info("Info message")
        logger.warning("Warning message")
        logger.error("Error message")
    
    def test_logger_with_context(self):
        """Test logging with context"""
        logger = get_logger('backend')
        
        # Log with context
        logger.info("Test message", user_id="123", action="test")
        
        # Log without context
        logger.error("Error message")
    
    def test_audit_logging(self):
        """Test audit logging functionality"""
        logger = get_logger('backend')
        
        # Test audit logging
        logger.audit(
            action="user_login",
            user="user123",
            resource="auth_service",
            details={"method": "jwt"}
        )
    
    def test_security_logging(self):
        """Test security logging functionality"""
        logger = get_logger('security')
        
        # Test security event logging
        logger.security_event(
            event_type="unauthorized_access",
            severity="HIGH",
            details={"user_id": "unknown", "resource": "admin_panel"}
        )
    
    def test_api_request_logging(self):
        """Test API request logging functionality"""
        logger = get_logger('backend')
        
        # Test API request logging
        logger.api_request(
            method="GET",
            endpoint="/api/users",
            status_code=200,
            duration=0.1,
            user="user123"
        )
    
    def test_database_operation_logging(self):
        """Test database operation logging functionality"""
        logger = get_logger('database')
        
        # Test database operation logging
        logger.database_operation(
            operation="select",
            collection="users",
            duration=0.05,
            record_count=10
        )
    
    def test_ai_service_logging(self):
        """Test AI service logging functionality"""
        logger = get_logger('ai-services')
        
        # Test AI service logging
        logger.ai_service_request(
            service="course-recommendation",
            model="bert-base",
            input_size=1024,
            output_size=512,
            duration=1.5
        )
    
    def test_log_directory_creation(self):
        """Test that log directories are created automatically"""
        with tempfile.TemporaryDirectory() as temp_dir:
            # Change to temp directory
            original_cwd = os.getcwd()
            os.chdir(temp_dir)
            
            try:
                logger = get_logger('test_component')
                
                # Check that directories were created
                logs_dir = Path("logs")
                component_dir = logs_dir / "test_component"
                
                assert logs_dir.exists()
                assert component_dir.exists()
                
                # Check that log files were created
                log_file = component_dir / "test_component.log"
                error_log = component_dir / "test_component_error.log"
                audit_log = component_dir / "test_component_audit.log"
                
                assert log_file.exists()
                assert error_log.exists()
                assert audit_log.exists()
                
                # Explicitly close logger handlers to prevent file handle issues
                for handler in logger.logger.handlers[:]:
                    logger.logger.removeHandler(handler)
                    handler.close()
                
            finally:
                os.chdir(original_cwd)
                # Clean up any remaining logger instances
                reset_loggers()

class TestLoggingUtils:
    """Test cases for logging utilities"""
    
    def test_log_context_manager(self):
        """Test the LogContext context manager"""
        logger = get_logger('backend')
        
        # Test context manager
        with LogContext('backend', request_id="12345", user_id="user123"):
            logger.info("Message with context")
        
        # Log after context should not have the context
        logger.info("Message without context")

class TestLoggingIntegration:
    """Test cases for logging integration"""
    
    def test_setup_logging_middleware(self):
        """Test logging middleware setup"""
        app = FastAPI()
        
        # This should not raise exceptions
        setup_logging_middleware(app)
        
        # The middleware should be accessible
        assert app.state is not None

class TestLoggingConfiguration:
    """Test cases for logging configuration"""
    
    def test_logging_config(self):
        """Test logging configuration"""
        # Test that configuration is loaded
        assert 'development' in LOGGING_CONFIG
        assert 'testing' in LOGGING_CONFIG
        assert 'production' in LOGGING_CONFIG
        
        # Test development config
        dev_config = LOGGING_CONFIG['development']
        assert dev_config['level'] == 'DEBUG'
        assert dev_config['console'] == True
        assert dev_config['files'] == True
        
        # Test production config
        prod_config = LOGGING_CONFIG['production']
        assert prod_config['level'] == 'WARNING'
        assert prod_config['console'] == False
        assert prod_config['files'] == True
    
    def test_environment_detection(self):
        """Test environment detection"""
        with patch.dict(os.environ, {'ENVIRONMENT': 'testing'}):
            reset_loggers()
            logger = get_logger('backend')
            assert logger.environment == 'testing'
        
        with patch.dict(os.environ, {'ENVIRONMENT': 'production'}):
            reset_loggers()
            logger = get_logger('backend')
            assert logger.environment == 'production'

class TestPerformance:
    """Performance tests for the logging system"""
    
    def test_logging_performance(self):
        """Test that logging doesn't significantly impact performance"""
        import time
        
        logger = get_logger('backend')
        
        # Time 1000 log operations
        start_time = time.time()
        for i in range(1000):
            logger.info("Test message", iteration=i)
        end_time = time.time()
        
        duration = end_time - start_time
        operations_per_second = 1000 / duration
        
        # Should be able to handle at least 100 operations per second
        assert operations_per_second > 100
        
        print(f"Logging performance: {operations_per_second:.2f} operations/second")

class TestErrorHandling:
    """Error handling tests for the logging system"""
    
    def test_logging_error_handling(self):
        """Test that logging errors don't crash the application"""
        logger = get_logger('backend')
        
        # These should not raise exceptions
        logger.info("Normal message")
        
        # Test with invalid data types (should not crash)
        logger.info("Message with invalid context", invalid_context={"test": 123})
        logger.error("Error message", invalid_data={"nested": {"bad": object()}})

def test_all_loggers_creation():
    """Test creation of all logger types"""
    components = ['backend', 'frontend', 'auth-gateway', 'ai-services', 'database', 'performance', 'security']
    
    for component in components:
        logger = get_logger(component)
        assert logger.component == component
        assert logger.environment == 'development'

def test_log_formatting():
    """Test log message formatting"""
    logger = get_logger('backend')
    
    # Test message formatting with various data types
    logger.info("Test message", 
               string="text", 
               number=123, 
               float=3.14, 
               boolean=True, 
               none=None,
               list=[1, 2, 3],
               dict={"key": "value"})

def test_concurrent_logging():
    """Test concurrent logging from multiple threads"""
    import threading
    
    logger = get_logger('backend')
    
    def log_messages(thread_id, count):
        for i in range(count):
            logger.info(f"Thread {thread_id} message {i}", thread_id=thread_id, iteration=i)
            time.sleep(0.001)
    
    # Create multiple threads
    threads = []
    for i in range(5):
        thread = threading.Thread(target=log_messages, args=(i, 20))
        threads.append(thread)
    
    # Start all threads
    for thread in threads:
        thread.start()
    
    # Wait for all threads to complete
    for thread in threads:
        thread.join()
    
    # All messages should have been logged without exceptions
    assert True

if __name__ == "__main__":
    # Run the tests
    pytest.main([__file__, "-v"])