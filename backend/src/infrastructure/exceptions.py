"""
Infrastructure exceptions module

This module contains exceptions used by infrastructure layer components.
"""

class AuthenticationError(Exception):
    """Authentication related errors"""
    def __init__(self, message: str = "Authentication failed"):
        super().__init__(message)


class AuthorizationError(Exception):
    """Authorization related errors"""
    def __init__(self, message: str = "Authorization denied"):
        super().__init__(message)


class ValidationError(Exception):
    """Validation related errors"""
    def __init__(self, message: str = "Validation failed"):
        super().__init__(message)


class NotFoundError(Exception):
    """Resource not found errors"""
    def __init__(self, message: str = "Resource not found"):
        super().__init__(message)


class ConflictError(Exception):
    """Resource conflict errors"""
    def __init__(self, message: str = "Resource conflict"):
        super().__init__(message)


class DatabaseError(Exception):
    """Database related errors"""
    def __init__(self, message: str = "Database operation failed"):
        super().__init__(message)