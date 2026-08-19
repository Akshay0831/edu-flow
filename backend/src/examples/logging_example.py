"""
Example usage of the Edu-Flow unified logging system.
This demonstrates various logging patterns and best practices.
"""

import time
import asyncio
from datetime import datetime
import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), '..', '..'))

from config.logging import get_logger
from core.logging_utils import (
    log_function_call,
    log_api_request,
    log_database_operation,
    log_ai_service_request,
    log_user_action,
    log_security_event,
    log_performance_metric,
    LogContext
)

# Initialize loggers for different components
backend_logger = get_logger('backend')
frontend_logger = get_logger('frontend')
auth_logger = get_logger('auth-gateway')
ai_logger = get_logger('ai-services')
database_logger = get_logger('database')
security_logger = get_logger('security')
performance_logger = get_logger('performance')

def basic_logging_example():
    """Basic logging examples"""
    print("=== Basic Logging Examples ===")
    
    # Basic log messages
    backend_logger.info("Application started successfully")
    backend_logger.warning("Rate limit approaching", current_rate=95, max_rate=100)
    backend_logger.error("Database connection failed", db_host="localhost", db_port=5432)
    backend_logger.debug("Detailed debugging information for development")
    
    # Logging with context
    backend_logger.info("User created account", 
                      user_id="user123", 
                      email="user@example.com",
                      ip_address="192.168.1.1")
    
    # Logging exceptions
    try:
        result = 1 / 0
    except Exception as e:
        backend_logger.error("Division by zero error", error=str(e), exception=str(e.__class__.__name__))

def audit_logging_example():
    """Audit logging examples"""
    print("\n=== Audit Logging Examples ===")
    
    # User authentication events
    auth_logger.audit(
        action="user_login",
        user="user123",
        resource="auth_service",
        details={"method": "jwt", "ip": "192.168.1.1", "user_agent": "Mozilla/5.0..."}
    )
    
    auth_logger.audit(
        action="user_logout",
        user="user123",
        resource="auth_service",
        details={"session_duration": 3600}
    )
    
    # Data access events
    backend_logger.audit(
        action="data_access",
        user="teacher456",
        resource="student_grades",
        details={"student_id": "student789", "operation": "read"}
    )

def security_logging_example():
    """Security logging examples"""
    print("\n=== Security Logging Examples ===")
    
    # Security events with different severity levels
    security_logger.security_event(
        event_type="unauthorized_access",
        severity="HIGH",
        details={"user_id": "unknown", "resource": "admin_panel", "ip": "192.168.1.100"}
    )
    
    security_logger.security_event(
        event_type="suspicious_activity",
        severity="MEDIUM",
        details={"user_id": "user123", "pattern": "multiple_failed_logins", "count": 5}
    )
    
    security_logger.security_event(
        event_type="data_breach_attempt",
        severity="CRITICAL",
        details={"user_id": "hacker789", "target": "user_database", "method": "sql_injection"}
    )

@log_function_call('backend')
def database_example():
    """Database operation logging example"""
    print("\n=== Database Operation Examples ===")
    
    # This decorator automatically logs database operations
    @log_database_operation('select', 'users')
    def get_users():
        # Simulate database operation
        time.sleep(0.1)
        return [{"id": 1, "name": "User 1"}, {"id": 2, "name": "User 2"}]
    
    users = get_users()
    backend_logger.info(f"Retrieved {len(users)} users", count=len(users))
    
    @log_database_operation('insert', 'students')
    def create_student(student_data):
        # Simulate database operation
        time.sleep(0.05)
        return {"id": 123, "name": student_data["name"], "status": "created"}
    
    student = create_student({"name": "John Doe", "email": "john@example.com"})
    backend_logger.info("Student created", student_id=student["id"])

@log_api_request('backend')
def api_example():
    """API request logging example"""
    print("\n=== API Request Examples ===")
    
    # This decorator automatically logs API requests
    # Simulate API processing
    time.sleep(0.2)
    
    # Log API completion
    backend_logger.api_request(
        method="GET",
        endpoint="/api/users",
        status_code=200,
        duration=0.2,
        user="user123"
    )

@log_ai_service_request('course-recommendation', 'bert-base')
def ai_service_example():
    """AI service logging example"""
    print("\n=== AI Service Examples ===")
    
    # This decorator automatically logs AI service requests
    # Simulate AI processing
    time.sleep(1.5)
    
    # Log AI service completion
    ai_logger.ai_service_request(
        service="course-recommendation",
        model="bert-base",
        input_size=1024,
        output_size=512,
        duration=1.5
    )

def performance_metric_example():
    """Performance metric logging example"""
    print("\n=== Performance Metric Examples ===")
    
    # Log various performance metrics
    log_performance_metric(
        metric_name="api_response_time",
        value=0.25,
        unit="seconds",
        tags={"endpoint": "/api/users", "method": "GET", "status": "200"}
    )
    
    log_performance_metric(
        metric_name="database_query_time",
        value=0.05,
        unit="seconds",
        tags={"operation": "select", "table": "users", "rows": 100}
    )
    
    log_performance_metric(
        metric_name="ai_processing_time",
        value=1.2,
        unit="seconds",
        tags={"service": "course-recommendation", "model": "bert-base"}
    )

def logging_context_example():
    """Logging context example"""
    print("\n=== Logging Context Examples ===")
    
    # Use context manager for adding contextual information
    with LogContext('backend', request_id="req_12345", user_id="user123"):
        backend_logger.info("Processing request")
        backend_logger.debug("Debug information with context")
    
    # Context is automatically removed after the block
    backend_logger.info("Without context", request_id=None)

async def async_logging_example():
    """Asynchronous logging example"""
    print("\n=== Async Logging Examples ===")
    
    async def process_async_task(task_id: str):
        backend_logger.info(f"Starting async task {task_id}")
        await asyncio.sleep(0.5)
        backend_logger.info(f"Completed async task {task_id}")
        return f"Task {task_id} completed"
    
    # Run multiple async tasks concurrently
    tasks = [process_async_task(f"task_{i}") for i in range(1, 4)]
    results = await asyncio.gather(*tasks)
    
    backend_logger.info("All async tasks completed", total_tasks=len(results), results=results)

def error_handling_example():
    """Error handling and logging example"""
    print("\n=== Error Handling Examples ===")
    
    def risky_operation():
        # Simulate an error
        if True:  # Always error in this example
            raise ValueError("Invalid input data")
    
    try:
        risky_operation()
    except ValueError as e:
        backend_logger.error(
            "Risky operation failed",
            error=str(e),
            exception=str(e.__class__.__name__),
            operation="data_validation"
        )
        # Re-raise if needed
        raise

def comprehensive_example():
    """Comprehensive example showing all logging patterns"""
    print("\n=== Comprehensive Logging Example ===")
    
    # User authentication flow
    auth_logger.info("User authentication flow started")
    
    # User login
    log_user_action(
        action="user_login",
        user_id="user123",
        resource="auth_service",
        details={"method": "jwt", "ip": "192.168.1.1"}
    )
    
    # Security check
    security_logger.security_event(
        event_type="authentication_success",
        severity="LOW",
        user_id="user123",
        ip_address="192.168.1.1"
    )
    
    # API request
    with LogContext('backend', user_id="user123", session_id="sess_12345"):
        backend_logger.info("API request received", endpoint="/api/courses")
        
        # Database operation
        @log_database_operation('select', 'courses')
        def get_courses():
            time.sleep(0.1)
            return [{"id": 1, "name": "Math 101"}, {"id": 2, "name": "Science 201"}]
        
        courses = get_courses()
        backend_logger.info("Courses retrieved", count=len(courses))
        
        # Performance monitoring
        log_performance_metric("api_response_time", 0.35, "seconds")
    
    # User logout
    log_user_action(
        action="user_logout",
        user_id="user123",
        resource="auth_service",
        details={"session_duration": 3600}
    )
    
    auth_logger.info("User authentication flow completed")

def run_all_examples():
    """Run all logging examples"""
    print("Edu-Flow Logging System Examples")
    print("=" * 50)
    
    try:
        basic_logging_example()
        audit_logging_example()
        security_logging_example()
        database_example()
        api_example()
        ai_service_example()
        performance_metric_example()
        logging_context_example()
        error_handling_example()
        comprehensive_example()
        
        # Run async example
        asyncio.run(async_logging_example())
        
        print("\n" + "=" * 50)
        print("All examples completed successfully!")
        
    except Exception as e:
        backend_logger.error("Example execution failed", error=str(e))
        print(f"Error: {e}")

if __name__ == "__main__":
    run_all_examples()