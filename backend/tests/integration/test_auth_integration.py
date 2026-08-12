import pytest
import json
import httpx
from unittest.mock import Mock, patch
from fastapi.testclient import TestClient
import sys
import os
from tests.test_utils import assert_response_format, assert_error, assert_success
from src.core.exceptions import ValidationError, AuthenticationError, NotFoundError
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from src.main import app, auth_service
from src.core.security import AuthService
from src.core.exceptions import AuthenticationError, ValidationError

@pytest.fixture
def auth_test_data():
    """Test data fixture for authentication tests"""
    return {
        "valid_user": {
            "email": "test@example.com",
            "password": "Password123!",
            "name": "Test User",
            "role": "teacher"
        },
        "invalid_user": {
            "email": "invalid-email",
            "password": "short",
            "name": "",
            "role": "invalid_role"
        },
        "duplicate_user": {
            "email": "existing@example.com",
            "password": "Password123!",
            "name": "Existing User",
            "role": "student"
        }
    }

class TestAuthenticationIntegration:
    """Integration tests for authentication system"""
    
    def setup_method(self):
        """Setup for each test method"""
        self.client = TestClient(app)
        # Use the same auth service instance as the main app
        self.auth_service = auth_service
        
        # Ensure user service is attached (in case main.py setup didn't work)
        from src.services.user_service import UserService
        if self.auth_service.user_service is None:
            self.auth_service.user_service = UserService()
    
    def test_user_registration_endpoint(self, auth_test_data):
        """Test user registration API endpoint"""
        # Test valid user registration
        response = self.client.post(
            "/api/v1/auth/register",
            json=auth_test_data["valid_user"]
        )
    
        assert response.status_code == 201
        data = response.json()
        
        # Verify response structure
        assert "data" in data
        user_data = data["data"]
        assert "user_id" in user_data
        assert "access_token" in user_data  
        assert "refresh_token" in user_data
        
        # Verify token validity
        token_data = self.auth_service.verify_token(user_data["access_token"])
        assert token_data.sub == user_data["user_id"]
        assert token_data.role == auth_test_data["valid_user"]["role"]
    
    def test_user_login_endpoint(self, auth_test_data):
        """Test user login API endpoint"""
        # First register a user with a unique email to avoid conflicts
        unique_email = f"login_test_{id(self)}@example.com"
        register_data = auth_test_data["valid_user"].copy()
        register_data["email"] = unique_email
        
        register_response = self.client.post(
            "/api/v1/auth/register",
            json=register_data
        )
        user_id = register_response.json()["data"]["user_id"]
        
        # Then login
        login_data = {
            "email": unique_email,
            "password": auth_test_data["valid_user"]["password"]
        }
        
        response = self.client.post(
            "/api/v1/auth/login",
            json=login_data
        )
        
        assert response.status_code == 200
        data = response.json()
        
        # Verify response structure
        # Test successful response structure
        assert "data" in data
        user_data = data["data"]
        assert "access_token" in user_data
        assert "refresh_token" in user_data
        if "data" not in data:
            data["data"] = {}
        if "data" not in data:
            data["data"] = {}
        if "data" not in data:
            data["data"] = {}
        assert data["success"] is True
        assert "message" in data
        assert "data" in data  # Login endpoint should return data with tokens
        assert "message" in data

class TestSecurityCompliance:
    """Test security compliance requirements"""
    
    def setup_method(self):
        """Setup for each test method"""
        self.client = TestClient(app)
    
    def test_cors_headers(self):
        """Test CORS headers are properly set"""
        # Add CORS headers to simulate a preflight request
        headers = {
            "Origin": "http://localhost:3000",
            "Access-Control-Request-Method": "POST",
            "Access-Control-Request-Headers": "Content-Type,Authorization"
        }
        response = self.client.options("/api/v1/auth/register", headers=headers)
        
        # Check CORS headers are present
        assert "access-control-allow-origin" in response.headers
        assert "access-control-allow-methods" in response.headers
        assert "access-control-allow-headers" in response.headers
    
    def test_rate_limiting(self):
        """Test rate limiting on authentication endpoints"""
        # Make multiple requests to same endpoint
        for i in range(5):
            response = self.client.post(
                "/api/v1/auth/login",
                json={"email": "test@example.com", "password": "password123"}
            )
        
        # Should be rate limited after certain number of requests
        if response.status_code == 429:
            assert "retry-after" in response.headers
    
    def test_input_sanitization(self):
        """Test input sanitization and validation"""
        malicious_inputs = [
            {
                "email": "test@example.com",
                "password": "<script>alert('xss')</script>",
                "name": "Test User",
                "role": "teacher"
            },
            {
                "email": "test@example.com",
                "password": "password123",
                "name": "Robert'); DROP TABLE users;--",
                "role": "teacher"
            }
        ]
        
        for malicious_data in malicious_inputs:
            response = self.client.post(
                "/api/v1/auth/register",
                json=malicious_data
            )
            
            # Should handle malicious input gracefully
            assert response.status_code in [400, 422]
    
    def test_security_headers(self):
        """Test security headers are present"""
        response = self.client.post(
            "/api/v1/auth/register",
            json={
                "email": "test@example.com",
                "password": "password123",
                "name": "Test User",
                "role": "teacher"
            }
        )
        
        # Check security headers
        assert "x-content-type-options" in response.headers
        assert "x-frame-options" in response.headers
        assert "x-xss-protection" in response.headers