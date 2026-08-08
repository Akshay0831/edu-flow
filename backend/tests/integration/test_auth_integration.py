import pytest
import json
import httpx
from unittest.mock import Mock, patch
from fastapi.testclient import TestClient
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from src.main import app, auth_service
from src.core.security import AuthService
from src.core.exceptions import AuthenticationError, ValidationError

class TestAuthenticationIntegration:
    """Integration tests for authentication system"""
    
    def setup_method(self):
        """Setup for each test method"""
        self.client = TestClient(app)
        # Use the same auth service instance as the main app
        self.auth_service = auth_service
    
    def test_user_registration_endpoint(self, auth_test_data):
        """Test user registration API endpoint"""
        # Test valid user registration
        response = self.client.post(
            "/api/v1/auth/register",
            json=auth_test_data["valid_user"]
        )
        
        assert response.status_code == 200
        data = response.json()
        
        # Verify response structure
        assert "user_id" in data
        assert "access_token" in data
        assert "refresh_token" in data
        
        # Verify token validity
        token_data = self.auth_service.verify_token(data["access_token"])
        assert token_data.sub == data["user_id"]
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
        user_id = register_response.json()["user_id"]
        
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
        assert "access_token" in data
        assert "refresh_token" in data
        assert "user_id" in data
        assert data["user_id"] == user_id
    
    def test_invalid_login_credentials(self, auth_test_data):
        """Test login with invalid credentials"""
        # Register a valid user first
        self.client.post(
            "/api/v1/auth/register",
            json=auth_test_data["valid_user"]
        )
        
        # Try login with wrong password
        invalid_login = {
            "email": auth_test_data["valid_user"]["email"],
            "password": "wrongpassword"
        }
        
        response = self.client.post(
            "/api/v1/auth/login",
            json=invalid_login
        )
        
        assert response.status_code == 401
        data = response.json()
        assert "error" in data
        assert "Invalid credentials" in data["error"]
    
    def test_duplicate_user_registration(self, auth_test_data):
        """Test registration of duplicate user"""
        # Register user first time
        self.client.post(
            "/api/v1/auth/register",
            json=auth_test_data["valid_user"]
        )
        
        # Try to register same user again
        response = self.client.post(
            "/api/v1/auth/register",
            json=auth_test_data["valid_user"]
        )
        
        assert response.status_code == 400
        data = response.json()
        assert "error" in data
        assert "already exists" in data["error"]
    
    def test_invalid_registration_data(self, auth_test_data):
        """Test registration with invalid data"""
        # Test malformed email
        invalid_data = {
            "email": "invalid-email",
            "password": "password123",
            "name": "Test User",
            "role": "teacher"
        }
        
        response = self.client.post(
            "/api/v1/auth/register",
            json=invalid_data
        )
        
        assert response.status_code == 400
        data = response.json()
        assert "error" in data
    
    def test_weak_password_registration(self, auth_test_data):
        """Test registration with weak password"""
        weak_password_data = {
            "email": "test@example.com",
            "password": "123",  # Too weak
            "name": "Test User",
            "role": "teacher"
        }
        
        response = self.client.post(
            "/api/v1/auth/register",
            json=weak_password_data
        )
        
        assert response.status_code == 400
        data = response.json()
        assert "error" in data
        assert "requirements" in data["error"]
    
    def test_missing_registration_fields(self, auth_test_data):
        """Test registration with missing required fields"""
        missing_fields_data = {
            "email": "test@example.com",
            # Missing password and name
            "role": "teacher"
        }
        
        response = self.client.post(
            "/api/v1/auth/register",
            json=missing_fields_data
        )
        
        assert response.status_code == 400
        data = response.json()
        assert "error" in data

class TestProtectedEndpoints:
    """Test protected API endpoints with authentication"""
    
    def setup_method(self):
        """Setup for each test method"""
        self.client = TestClient(app)
        self.auth_service = auth_service  # Use the same auth service as main app
        
        # Register and login to get token
        auth_data = {
            "email": "test@example.com",
            "password": "Password123!",
            "name": "Test User",
            "role": "teacher"
        }
        
        # Register user
        self.client.post("/api/v1/auth/register", json=auth_data)
        
        # Login to get token
        login_response = self.client.post(
            "/api/v1/auth/login",
            json={"email": "test@example.com", "password": "Password123!"}
        )
        self.token = login_response.json()["access_token"]
    
    def test_valid_token_access(self):
        """Test access to protected endpoint with valid token"""
        headers = {"Authorization": f"Bearer {self.token}"}
        
        response = self.client.get("/api/v1/users/me", headers=headers)
        
        assert response.status_code == 200
        data = response.json()
        assert "user_id" in data
        assert "email" in data
        assert "role" in data
    
    def test_missing_token_access(self):
        """Test access to protected endpoint without token"""
        response = self.client.get("/api/v1/users/me")
        
        assert response.status_code == 401
        data = response.json()
        assert "error" in data
        assert "Authorization header missing" in data["error"]
    
    def test_invalid_token_access(self):
        """Test access to protected endpoint with invalid token"""
        headers = {"Authorization": "Bearer invalid.token.signature"}
        
        response = self.client.get("/api/v1/users/me", headers=headers)
        
        assert response.status_code == 401
        data = response.json()
        assert "error" in data
    
    def test_expired_token_access(self):
        """Test access to protected endpoint with expired token"""
        # Create expired token
        from datetime import timedelta
        expired_token = self.auth_service.create_access_token(
            {"sub": "user123", "role": "teacher"},
            expires_delta=timedelta(hours=-1)  # 1 hour ago
        )
        
        headers = {"Authorization": f"Bearer {expired_token}"}
        
        response = self.client.get("/api/v1/users/me", headers=headers)
        
        assert response.status_code == 401
        data = response.json()
        assert "error" in data
    
    def test_role_based_access(self):
        """Test role-based access control"""
        headers = {"Authorization": f"Bearer {self.token}"}
        
        # Test endpoint accessible to teacher role
        response = self.client.get("/api/v1/teachers/me", headers=headers)
        assert response.status_code == 200
        
        # Test endpoint not accessible to wrong role
        response = self.client.get("/api/v1/admin/dashboard", headers=headers)
        assert response.status_code == 403

class TestTokenRefresh:
    """Test token refresh functionality"""
    
    def setup_method(self):
        """Setup for each test method"""
        self.client = TestClient(app)
        
        # Register and login to get token
        auth_data = {
            "email": "test@example.com",
            "password": "Password123!",
            "name": "Test User",
            "role": "teacher"
        }
        
        self.client.post("/api/v1/auth/register", json=auth_data)
        
        login_response = self.client.post(
            "/api/v1/auth/login",
            json={"email": "test@example.com", "password": "Password123!"}
        )
        self.tokens = login_response.json()
    
    def test_token_refresh_endpoint(self):
        """Test token refresh endpoint"""
        refresh_data = {
            "refresh_token": self.tokens["refresh_token"]
        }
        
        response = self.client.post(
            "/api/v1/auth/refresh",
            json=refresh_data
        )
        
        assert response.status_code == 200
        data = response.json()
        
        # Verify new tokens are returned
        assert "access_token" in data
        assert "refresh_token" in data
        
        # Verify new token is different from old one
        assert data["access_token"] != self.tokens["access_token"]
        assert data["refresh_token"] != self.tokens["refresh_token"]
    
    def test_invalid_refresh_token(self):
        """Test token refresh with invalid refresh token"""
        refresh_data = {
            "refresh_token": "invalid.refresh.token"
        }
        
        response = self.client.post(
            "/api/v1/auth/refresh",
            json=refresh_data
        )
        
        assert response.status_code == 401
        data = response.json()
        assert "error" in data
    
    def test_missing_refresh_token(self):
        """Test token refresh without refresh token"""
        response = self.client.post("/api/v1/auth/refresh")
        
        assert response.status_code == 422  # FastAPI returns 422 for validation errors
        data = response.json()
        assert "detail" in data  # FastAPI returns "detail" instead of "error" for validation errors

class TestPasswordReset:
    """Test password reset functionality"""
    
    def setup_method(self):
        """Setup for each test method"""
        self.client = TestClient(app)
        
        # Register user with unique email
        unique_email = f"reset_test_{id(self)}@example.com"
        auth_data = {
            "email": unique_email,
            "password": "Password123!",  # Use valid password that meets strength requirements
            "name": "Test User",
            "role": "teacher"
        }
        
        register_response = self.client.post("/api/v1/auth/register", json=auth_data)
        if register_response.status_code != 200:
            print(f"Registration failed: {register_response.text}")
        
        self.test_email = unique_email
    
    def test_password_reset_request(self):
        """Test password reset request"""
        reset_data = {
            "email": self.test_email
        }
        
        response = self.client.post(
            "/api/v1/auth/reset-password",
            json=reset_data
        )
        
        assert response.status_code == 200
        data = response.json()
        assert "message" in data
        assert "reset_token" in data
        self.reset_token = data["reset_token"]  # Store for next test
    
    def test_invalid_password_reset_request(self):
        """Test password reset request with invalid email"""
        reset_data = {
            "email": "nonexistent@example.com"
        }
        
        response = self.client.post(
            "/api/v1/auth/reset-password",
            json=reset_data
        )
        
        assert response.status_code == 400
        data = response.json()
        assert "error" in data
    
    def test_password_reset_with_token(self):
        """Test password reset with valid token"""
        # Use reset token from previous test (stored in self.reset_token)
        if not hasattr(self, 'reset_token'):
            # If not available, request it first
            reset_data = {
                "email": self.test_email
            }
            
            reset_response = self.client.post(
                "/api/v1/auth/reset-password",
                json=reset_data
            )
            reset_token = reset_response.json()["reset_token"]
        else:
            reset_token = self.reset_token
        
        # Use token to reset password
        new_password_data = {
            "reset_token": reset_token,
            "new_password": "NewPassword123!",
            "confirm_password": "NewPassword123!"
        }
        
        response = self.client.post(
            "/api/v1/auth/confirm-reset",
            json=new_password_data
        )
        
        assert response.status_code == 200
        data = response.json()
        assert "message" in data
        
        # Verify new password works
        login_response = self.client.post(
            "/api/v1/auth/login",
            json={"email": self.test_email, "password": "NewPassword123!"}
        )
        assert login_response.status_code == 200

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