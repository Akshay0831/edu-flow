"""Custom exception hierarchy for consistent error handling."""

from typing import Optional, Dict, Any
from fastapi import HTTPException, status
from datetime import datetime, timezone


class BaseError(Exception):
    """Base exception class for all custom errors."""
    
    def __init__(self, message: str, error_code: str = None, details: Dict = None):
        self.message = message
        self.error_code = error_code or self.__class__.__name__
        self.details = details or {}
        self.timestamp = datetime.now(timezone.utc).isoformat()
        super().__init__(self.message)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert exception to dictionary format."""
        return {
            'error_code': self.error_code,
            'message': self.message,
            'details': self.details,
            'timestamp': self.timestamp
        }


class ValidationError(BaseError):
    """Exception raised for validation errors."""
    
    def __init__(self, message: str, field: str = None, details: Dict = None):
        self.field = field
        super().__init__(
            message=message,
            error_code='VALIDATION_ERROR',
            details={'field': field, **(details or {})}
        )


class NotFoundError(BaseError):
    """Exception raised when a resource is not found."""
    
    def __init__(self, resource: str, id: str = None, details: Dict = None):
        self.resource = resource
        self.id = id
        message = f"{resource} not found"
        if id:
            message += f" with ID: {id}"
        super().__init__(
            message=message,
            error_code='NOT_FOUND',
            details={'resource': resource, 'id': id, **(details or {})}
        )


class AuthenticationError(BaseError):
    """Exception raised for authentication errors."""
    
    def __init__(self, message: str = "Authentication failed", details: Dict = None):
        super().__init__(
            message=message,
            error_code='AUTHENTICATION_ERROR',
            details=details or {}
        )


class AuthorizationError(BaseError):
    """Exception raised for authorization errors."""
    
    def __init__(self, message: str = "Access denied", required_permission: str = None, details: Dict = None):
        self.required_permission = required_permission
        super().__init__(
            message=message,
            error_code='AUTHORIZATION_ERROR',
            details={'required_permission': required_permission, **(details or {})}
        )


class ForbiddenError(BaseError):
    """Exception raised for forbidden access."""
    
    def __init__(self, message: str = "Access forbidden", details: Dict = None):
        super().__init__(
            message=message,
            error_code='FORBIDDEN',
            details=details or {}
        )


class ConflictError(BaseError):
    """Exception raised for conflicts (e.g., duplicate entries)."""
    
    def __init__(self, message: str, conflict_field: str = None, conflict_value: str = None, details: Dict = None):
        self.conflict_field = conflict_field
        self.conflict_value = conflict_value
        super().__init__(
            message=message,
            error_code='CONFLICT',
            details={
                'conflict_field': conflict_field,
                'conflict_value': conflict_value,
                **(details or {})
            }
        )


class DatabaseError(BaseError):
    """Exception raised for database-related errors."""
    
    def __init__(self, message: str, operation: str = None, details: Dict = None):
        self.operation = operation
        super().__init__(
            message=message,
            error_code='DATABASE_ERROR',
            details={'operation': operation, **(details or {})}
        )


class ExternalServiceError(BaseError):
    """Exception raised for external service errors."""
    
    def __init__(self, message: str, service_name: str = None, details: Dict = None):
        self.service_name = service_name
        super().__init__(
            message=message,
            error_code='EXTERNAL_SERVICE_ERROR',
            details={'service_name': service_name, **(details or {})}
        )


class RateLimitError(BaseError):
    """Exception raised for rate limit exceeded."""
    
    def __init__(self, message: str = "Rate limit exceeded", retry_after: int = None, details: Dict = None):
        self.retry_after = retry_after
        super().__init__(
            message=message,
            error_code='RATE_LIMIT',
            details={'retry_after': retry_after, **(details or {})}
        )


class ConfigurationError(BaseError):
    """Exception raised for configuration errors."""
    
    def __init__(self, message: str, config_key: str = None, details: Dict = None):
        self.config_key = config_key
        super().__init__(
            message=message,
            error_code='CONFIGURATION_ERROR',
            details={'config_key': config_key, **(details or {})}
        )


class MigrationError(BaseError):
    """Exception raised for migration errors."""
    
    def __init__(self, message: str, migration_version: str = None, details: Dict = None):
        self.migration_version = migration_version
        super().__init__(
            message=message,
            error_code='MIGRATION_ERROR',
            details={'migration_version': migration_version, **(details or {})}
        )


class UserNotFoundError(BaseError):
    """Exception raised when a user is not found."""
    
    def __init__(self, user_id: str = None, email: str = None, details: Dict = None):
        message = "User not found"
        if user_id:
            message += f" with ID: {user_id}"
        if email:
            message += f" with email: {email}"
        super().__init__(
            message=message,
            error_code='USER_NOT_FOUND',
            details={'user_id': user_id, 'email': email, **(details or {})}
        )


class UserExistsError(BaseError):
    """Exception raised when trying to create a user that already exists."""
    
    def __init__(self, email: str = None, user_id: str = None, details: Dict = None):
        message = "User already exists"
        if email:
            message += f" with email: {email}"
        if user_id:
            message += f" with ID: {user_id}"
        super().__init__(
            message=message,
            error_code='USER_EXISTS',
            details={'email': email, 'user_id': user_id, **(details or {})}
        )


class StudentNotFoundError(BaseError):
    """Exception raised when a student is not found."""
    
    def __init__(self, student_id: str = None, email: str = None, details: Dict = None):
        message = "Student not found"
        if student_id:
            message += f" with ID: {student_id}"
        if email:
            message += f" with email: {email}"
        super().__init__(
            message=message,
            error_code='STUDENT_NOT_FOUND',
            details={'student_id': student_id, 'email': email, **(details or {})}
        )


class CourseNotFoundError(BaseError):
    """Exception raised when a course is not found."""
    
    def __init__(self, course_id: str = None, course_name: str = None, details: Dict = None):
        message = "Course not found"
        if course_id:
            message += f" with ID: {course_id}"
        if course_name:
            message += f" with name: {course_name}"
        super().__init__(
            message=message,
            error_code='COURSE_NOT_FOUND',
            details={'course_id': course_id, 'course_name': course_name, **(details or {})}
        )


class DepartmentNotFoundError(BaseError):
    """Exception raised when a department is not found."""
    
    def __init__(self, department_id: str = None, department_name: str = None, details: Dict = None):
        message = "Department not found"
        if department_id:
            message += f" with ID: {department_id}"
        if department_name:
            message += f" with name: {department_name}"
        super().__init__(
            message=message,
            error_code='DEPARTMENT_NOT_FOUND',
            details={'department_id': department_id, 'department_name': department_name, **(details or {})}
        )


class EnrollmentError(BaseError):
    """Exception raised for enrollment-related errors."""
    
    def __init__(self, message: str, details: Dict = None):
        super().__init__(
            message=message,
            error_code='ENROLLMENT_ERROR',
            details=details or {}
        )


class UnauthorizedError(BaseError):
    """Exception raised for unauthorized access."""
    
    def __init__(self, message: str = "Unauthorized access", required_permission: str = None, details: Dict = None):
        self.required_permission = required_permission
        super().__init__(
            message=message,
            error_code='UNAUTHORIZED_ERROR',
            details={'required_permission': required_permission, **(details or {})}
        )


class HTTPError(HTTPException):
    """HTTP exception with error details."""
    
    def __init__(self, error: BaseError):
        super().__init__(
            status_code=error.__class__.__name__ if error.__class__.__name__ in [
                'ValidationError', 'AuthenticationError', 'AuthorizationError', 
                'ForbiddenError', 'NotFoundError', 'ConflictError', 'UnauthorizedError'
            ] else status.HTTP_500_INTERNAL_SERVER_ERROR,
            content={'error': error.to_dict()}
        )


def get_http_exception(error: BaseError) -> HTTPException:
    """Convert a BaseError to HTTPException."""
    status_code_map = {
        'ValidationError': status.HTTP_422_UNPROCESSABLE_ENTITY,
        'NotFoundError': status.HTTP_404_NOT_FOUND,
        'AuthenticationError': status.HTTP_401_UNAUTHORIZED,
        'AuthorizationError': status.HTTP_403_FORBIDDEN,
        'ForbiddenError': status.HTTP_403_FORBIDDEN,
        'ConflictError': status.HTTP_409_CONFLICT,
        'DatabaseError': status.HTTP_500_INTERNAL_SERVER_ERROR,
        'ExternalServiceError': status.HTTP_502_BAD_GATEWAY,
        'RateLimitError': status.HTTP_429_TOO_MANY_REQUESTS,
        'ConfigurationError': status.HTTP_500_INTERNAL_SERVER_ERROR,
        'UnauthorizedError': status.HTTP_401_UNAUTHORIZED,
    }
    
    status_code = status_code_map.get(error.error_code, status.HTTP_500_INTERNAL_SERVER_ERROR)
    
    return HTTPException(
        status_code=status_code,
        content={'error': error.to_dict()}
    )


class ConflictError(HTTPException):
    """Custom conflict error"""
    
    def __init__(self, detail: str, status_code: int = status.HTTP_409_CONFLICT):
        super().__init__(status_code=status_code, detail=detail)


class InternalServerError(HTTPException):
    """Custom internal server error"""
    
    def __init__(self, detail: str, status_code: int = status.HTTP_500_INTERNAL_SERVER_ERROR):
        super().__init__(status_code=status_code, detail=detail)


class DatabaseError(Exception):
    """Database operation error"""
    pass


class ExternalServiceError(Exception):
    """External service integration error"""
    pass


class ServiceNotFoundError(Exception):
    """Service not found error"""
    pass





class RateLimitError(HTTPException):
    """Rate limiting error"""
    
    def __init__(self, detail: str = "Rate limit exceeded", status_code: int = status.HTTP_429_TOO_MANY_REQUESTS):
        super().__init__(status_code=status_code, detail=detail)


class ProcessingError(Exception):
    """Data processing error"""
    pass


class FileProcessingError(ProcessingError):
    """File processing error"""
    pass


class CalculationError(Exception):
    """Calculation error"""
    pass


class DataValidationError(Exception):
    """Data validation error"""
    pass