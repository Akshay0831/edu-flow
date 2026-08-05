import pytest
import json
from datetime import datetime, timedelta
from typing import Dict, Any
import os
import sys

# Add the project root to the Python path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

@pytest.fixture
def auth_test_data() -> Dict[str, Any]:
    """Test data for authentication system"""
    return {
        "valid_user": {
            "email": "test@example.com",
            "password": "password123",
            "name": "Test User",
            "role": "teacher"
        },
        "admin_user": {
            "email": "admin@example.com",
            "password": "admin123",
            "name": "Admin User",
            "role": "admin"
        },
        "student_user": {
            "email": "student@example.com", 
            "password": "student123",
            "name": "Student User",
            "role": "student"
        },
        "invalid_credentials": {
            "email": "invalid@example.com",
            "password": "wrongpassword"
        },
        "malformed_email": {
            "email": "invalid-email",
            "password": "password123"
        },
        "weak_password": {
            "email": "test@example.com",
            "password": "123"
        },
        "missing_fields": {
            "email": "test@example.com"
        }
    }

@pytest.fixture
def mock_jwt_tokens() -> Dict[str, str]:
    """Mock JWT tokens for testing"""
    return {
        "valid_admin_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiJhZG1pbkBleGFtcGxlLmNvbSIsImV4cCI6MTk4ODgwODIwMCwiaWF0IjoxNjk4ODgwMjAwfQ.test_signature",
        "valid_teacher_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiJ0ZWFzdGVyQGV4YW1wbGUuY29tIiwiZXhwIjoxOTg4ODA4MjAwLCJpYXQiOTo2OTg4ODAyMDAwfQ.test_signature",
        "valid_student_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiJzdHVkZW50QGV4YW1wbGUuY29tIiwiZXhwIjoxOTg4ODA4MjAwLCJpYXQiOTo2OTg4ODAyMDAwfQ.test_signature",
        "expired_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiJ0ZXN0QGV4YW1wbGUuY29tIiwiZXhwIjoxNjQ4ODgwODIwMCwiaWF0IjoxNjk4ODAyMDAwfQ.test_signature",
        "invalid_token": "invalid.token.signature",
        "no_token": ""
    }

@pytest.fixture
def test_headers(mock_jwt_tokens):
    """Test headers for API requests"""
    return {
        "valid_admin": {"Authorization": f"Bearer {mock_jwt_tokens['valid_admin_token']}"},
        "valid_teacher": {"Authorization": f"Bearer {mock_jwt_tokens['valid_teacher_token']}"},
        "valid_student": {"Authorization": f"Bearer {mock_jwt_tokens['valid_student_token']}"},
        "expired": {"Authorization": f"Bearer {mock_jwt_tokens['expired_token']}"},
        "invalid": {"Authorization": f"Bearer {mock_jwt_tokens['invalid_token']}"},
        "no_auth": {},
        "invalid_auth": {"Authorization": "Invalid Bearer Token"}
    }

@pytest.fixture
def mock_database_operations():
    """Mock database operations for testing"""
    return {
        "find_user_by_email": lambda email: {
            "email": email,
            "password_hash": "$2b$12$EixZaYVK1fsbw1ZfbX3OXePaWxn96p36WQoeG6Lruj3vjPkU2Cslq",  # password123
            "name": "Test User",
            "role": "teacher",
            "is_active": True,
            "created_at": datetime.utcnow(),
            "updated_at": datetime.utcnow()
        }.get(email) if email in ["test@example.com", "admin@example.com", "student@example.com"] else None,
        
        "create_user": lambda user_data: {
            "id": "user123",
            **user_data,
            "password_hash": "$2b$12$EixZaYVK1fsbw1ZfbX3OXePaWxn96p36WQoeG6Lruj3vjPkU2Cslq",
            "is_active": True,
            "created_at": datetime.utcnow(),
            "updated_at": datetime.utcnow()
        },
        
        "deactivate_user": lambda user_id: True,
        
        "get_user_by_id": lambda user_id: {
            "id": user_id,
            "email": "test@example.com",
            "name": "Test User",
            "role": "teacher",
            "is_active": True,
            "created_at": datetime.utcnow(),
            "updated_at": datetime.utcnow()
        } if user_id == "user123" else None
    }

@pytest.fixture
def mock_password_operations():
    """Mock password operations for testing"""
    return {
        "hash_password": lambda password: "$2b$12$EixZaYVK1fsbw1ZfbX3OXePaWxn96p36WQoeG6Lruj3vjPkU2Cslq",
        "verify_password": lambda plain_password, hashed_password: plain_password == "password123",
        "validate_password_strength": lambda password: len(password) >= 8,
        "validate_email_format": lambda email: "@" in email and "." in email.split("@")[1]
    }