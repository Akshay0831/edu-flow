"""
Test helpers for Edu-Flow backend testing

This module provides helper functions and fixtures for testing the backend services.
"""

import asyncio
import pytest
from typing import Dict, Any
from fastapi.testclient import TestClient
from src.core.security import auth_service
from src.services.user_service import UserService

@pytest.fixture
def test_client():
    """Create test client for FastAPI application"""
    from src.main import app
    return TestClient(app)

@pytest.fixture
async def auth_service_with_user():
    """Create auth service with user service attached"""
    user_service = UserService()
    auth_service.user_service = user_service
    return auth_service

@pytest.fixture
def test_user_data():
    """Standard test user data"""
    return {
        'email': 'testuser@example.com',
        'password': 'TestUser123!',
        'name': 'Test User',
        'role': 'student'
    }

@pytest.fixture
async def created_user(auth_service_with_user, test_user_data):
    """Create a test user and return the result"""
    result = await auth_service_with_user.create_user(test_user_data)
    return result

@pytest.fixture
async def auth_tokens(auth_service_with_user, test_user_data):
    """Create auth tokens for a test user"""
    # First create the user if it doesn't exist
    try:
        await auth_service_with_user.create_user(test_user_data)
    except:
        pass  # User might already exist
    
    # Then authenticate
    login_result = await auth_service_with_user.login_user(test_user_data)
    return login_result

def create_test_headers(auth_tokens: Dict[str, Any]) -> Dict[str, str]:
    """Create authentication headers for API requests"""
    return {
        "Authorization": f"Bearer {auth_tokens['access_token']}",
        "Content-Type": "application/json"
    }

async def setup_test_database():
    """Setup test database environment"""
    # Initialize services for testing
    from src.services.user_service import UserService
    user_service = UserService()
    await user_service.initialize()
    return user_service