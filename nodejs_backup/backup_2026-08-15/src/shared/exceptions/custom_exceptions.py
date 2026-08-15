"""
Custom exceptions for Edu-Flow

This module contains custom exceptions used across the application:
- Base exceptions for domain errors
- Authentication and authorization exceptions
- Business logic exceptions
- Validation exceptions
- Database exceptions

Author: Edu-Flow Team
"""


class EduFlowException(Exception):
    """Base exception for Edu-Flow application"""
    
    def __init__(self, message: str, error_code: str = "INTERNAL_ERROR"):
        self.message = message
        self.error_code = error_code
        super().__init__(self.message)


class AuthenticationError(EduFlowException):
    """Exception raised for authentication errors"""
    
    def __init__(self, message: str):
        super().__init__(message, "AUTHENTICATION_ERROR")


class AuthorizationError(EduFlowException):
    """Exception raised for authorization errors"""
    
    def __init__(self, message: str):
        super().__init__(message, "AUTHORIZATION_ERROR")


class ValidationError(EduFlowException):
    """Exception raised for validation errors"""
    
    def __init__(self, message: str):
        super().__init__(message, "VALIDATION_ERROR")


class NotFoundError(EduFlowException):
    """Exception raised when a resource is not found"""
    
    def __init__(self, message: str):
        super().__init__(message, "NOT_FOUND_ERROR")


class ConflictError(EduFlowException):
    """Exception raised for conflicts (e.g., duplicate entries)"""
    
    def __init__(self, message: str):
        super().__init__(message, "CONFLICT_ERROR")


class BusinessRuleError(EduFlowException):
    """Exception raised when business rules are violated"""
    
    def __init__(self, message: str):
        super().__init__(message, "BUSINESS_RULE_ERROR")


class DatabaseError(EduFlowException):
    """Exception raised for database errors"""
    
    def __init__(self, message: str):
        super().__init__(message, "DATABASE_ERROR")


class ExternalServiceError(EduFlowException):
    """Exception raised for external service errors"""
    
    def __init__(self, message: str, service_name: str = "external"):
        super().__init__(message, "EXTERNAL_SERVICE_ERROR")
        self.service_name = service_name


class ConfigurationError(EduFlowException):
    """Exception raised for configuration errors"""
    
    def __init__(self, message: str):
        super().__init__(message, "CONFIGURATION_ERROR")


class RateLimitError(EduFlowException):
    """Exception raised for rate limit violations"""
    
    def __init__(self, message: str):
        super().__init__(message, "RATE_LIMIT_ERROR")


class SecurityError(EduFlowException):
    """Exception raised for security-related errors"""
    
    def __init__(self, message: str):
        super().__init__(message, "SECURITY_ERROR")


class PaymentError(EduFlowException):
    """Exception raised for payment-related errors"""
    
    def __init__(self, message: str):
        super().__init__(message, "PAYMENT_ERROR")


class CommunicationError(EduFlowException):
    """Exception raised for communication errors"""
    
    def __init__(self, message: str):
        super().__init__(message, "COMMUNICATION_ERROR")


class FileOperationError(EduFlowException):
    """Exception raised for file operation errors"""
    
    def __init__(self, message: str):
        super().__init__(message, "FILE_OPERATION_ERROR")


class ExportError(EduFlowException):
    """Exception raised for export operation errors"""
    
    def __init__(self, message: str):
        super().__init__(message, "EXPORT_ERROR")


class ImportError(EduFlowException):
    """Exception raised for import operation errors"""
    
    def __init__(self, message: str):
        super().__init__(message, "IMPORT_ERROR")


class NotificationError(EduFlowException):
    """Exception raised for notification errors"""
    
    def __init__(self, message: str):
        super().__init__(message, "NOTIFICATION_ERROR")


class TimeoutError(EduFlowException):
    """Exception raised for timeout errors"""
    
    def __init__(self, message: str):
        super().__init__(message, "TIMEOUT_ERROR")