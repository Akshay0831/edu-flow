"""
Shared Services Module

This module provides shared service instances that can be used across the application:
- AuthService: Handles authentication and authorization
- StudentService: Handles student management operations
- UserService: Handles user management operations

This avoids circular imports between main.py and API endpoints.

Author: Edu-Flow Team
"""

from .security import AuthService
from ..services.student_service import StudentService
from ..services.user_service import UserService

# Create shared service instances
SECRET_KEY = "your-secret-key-here-in-production-use-environment-variable"
ALGORITHM = "HS256"

# Initialize shared services
auth_service = AuthService()
user_service = UserService()

def get_student_service():
    """Dependency to get student service with auth service injected"""
    return StudentService(auth_service)