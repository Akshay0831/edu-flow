"""
FastAPI v1 API endpoints

This module contains all API endpoints for the Edu-Flow application.
- User authentication and management
- Student management
- Teacher management  
- Course management
- Assessment management
- Analytics endpoints

Author: Edu-Flow Team
"""

from fastapi import APIRouter

# Import all endpoint routers
from .endpoints import auth, students, courses

# Create main router
api_router = APIRouter()

# Include all endpoint routers
api_router.include_router(auth.router, prefix="/auth", tags=["authentication"])
api_router.include_router(students.router, prefix="/students", tags=["students"])
api_router.include_router(courses.router, prefix="/courses", tags=["courses"])