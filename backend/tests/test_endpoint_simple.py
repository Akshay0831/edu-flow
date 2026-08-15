"""
Simple Integration Test for Authentication Endpoints

Basic test to verify authentication endpoints are accessible and functional.

Author: Edu-Flow Team
"""

import pytest
import json
from httpx import AsyncClient
from fastapi.testclient import TestClient
from fastapi import FastAPI

class TestEndpointIntegration:
    """Test authentication endpoint integration"""
    
    @pytest.fixture(scope="class")
    @classmethod
    def app(cls):
        """Create FastAPI app for testing"""
        from src.main import app
        return app
    
    @pytest.mark.asyncio
    async def test_health_endpoint(self, app):
        """Test health endpoint"""
        client = TestClient(app)
        response = client.get("/health")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"
    
    @pytest.mark.asyncio
    async def test_auth_provider_listing(self, app):
        """Test auth provider listing endpoint"""
        client = TestClient(app)
        response = client.get("/api/v1/auth/enhanced/providers")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "success"
        assert "providers" in data
        assert "default_provider" in data
    
    @pytest.mark.asyncio
    async def test_jwt_health_endpoint(self, app):
        """Test JWT provider health endpoint"""
        client = TestClient(app)
        response = client.get("/api/v1/auth/enhanced/providers/jwt/health")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "success"
        assert data["data"]["provider"] == "jwt"
    
    @pytest.mark.asyncio
    async def test_firebase_health_endpoint(self, app):
        """Test Firebase provider health endpoint"""
        client = TestClient(app)
        response = client.get("/api/v1/auth/enhanced/providers/firebase/health")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "success"
        assert data["data"]["provider"] == "firebase"
    
    @pytest.mark.asyncio
    async def test_login_endpoint_validation(self, app):
        """Test login endpoint validation"""
        client = TestClient(app)
        # Test with missing credentials
        response = client.post("/api/v1/auth/enhanced/login", json={})
        assert response.status_code == 422
        
        # Test with invalid provider
        response = client.post("/api/v1/auth/enhanced/login", json={
            "provider": "invalid",
            "credentials": {
                "email": "test@example.com",
                "password": "password"
            }
        })
        assert response.status_code == 422
    
    @pytest.mark.asyncio
    async def test_register_endpoint_validation(self, app):
        """Test register endpoint validation"""
        client = TestClient(app)
        # Test with missing data
        response = client.post("/api/v1/auth/enhanced/register", json={})
        assert response.status_code == 422
        
        # Test with invalid email
        response = client.post("/api/v1/auth/enhanced/register", json={
            "provider": "jwt",
            "user_data": {
                "email": "invalid-email",
                "password": "password"
            }
        })
        assert response.status_code == 422
    
    @pytest.mark.asyncio
    async def test_logout_endpoint(self, app):
        """Test logout endpoint"""
        client = TestClient(app)
        response = client.post("/api/v1/auth/enhanced/logout", json={"provider": "jwt"})
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "success"
    
    @pytest.mark.asyncio
    async def test_forgot_password_validation(self, app):
        """Test forgot password endpoint validation"""
        client = TestClient(app)
        # Test with missing email
        response = client.post("/api/v1/auth/enhanced/forgot-password", json={})
        assert response.status_code == 422
        
        # Test with valid email format
        response = client.post("/api/v1/auth/enhanced/forgot-password", json={
            "email": "test@example.com"
        })
        # Should not return 422 for email format
        assert response.status_code != 422
    
    @pytest.mark.asyncio
    async def test_cors_headers_present(self, app):
        """Test that CORS headers are present in responses"""
        client = TestClient(app)
        response = client.get("/api/v1/auth/enhanced/providers")
        assert "access-control-allow-origin" in response.headers
        assert "access-control-allow-headers" in response.headers
        assert "access-control-allow-methods" in response.headers