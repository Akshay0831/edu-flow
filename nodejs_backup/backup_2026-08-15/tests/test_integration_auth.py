"""
Integration Tests for Enhanced Authentication

Integration tests that verify the complete authentication flow,
including API endpoints and database interactions.

Author: Edu-Flow Team
"""

import pytest
import json
from httpx import AsyncClient
from unittest.mock import Mock, patch, AsyncMock
from src.core.auth_gateway import AuthProvider
from src.core.exceptions import AuthenticationError

class TestAuthEndpointIntegration:
    """Test authentication API endpoints integration"""
    
    @pytest.mark.asyncio
    async def test_jwt_login_endpoint_success(self):
        """Test JWT login endpoint success"""
        from src.api.v1.endpoints.auth_enhanced import auth_enhanced_router
        
        # Mock the database user service
        with patch('src.core.auth_gateway.user_service') as mock_user_service:
            # Mock user existence check
            mock_user_service.find_by_email.return_value = {
                "user_id": "123",
                "email": "test@example.com",
                "password_hash": "hashed_password",
                "name": "Test User",
                "role": "student"
            }
            
            # Mock password verification
            with patch('src.core.security.pwd_context.verify_password') as mock_verify:
                mock_verify.return_value = True
                
                # Mock authentication
                with patch('src.core.auth_gateway.auth_gateway.authenticate') as mock_auth:
                    mock_auth.return_value = {
                        "user_id": "123",
                        "email": "test@example.com",
                        "provider": AuthProvider.JWT,
                        "access_token": "test_token"
                    }
                    
                    # Mock user service get
                    with patch('src.core.auth_gateway.user_service.get') as mock_get:
                        mock_get.return_value = {
                            "user_id": "123",
                            "email": "test@example.com",
                            "name": "Test User",
                            "role": "student"
                        }
                        
                        # Create a test client
                        from src.main import app
                        async with AsyncClient(app=app, base_url="http://test") as ac:
                            response = await ac.post(
                                "/api/v1/auth/enhanced/login",
                                json={
                                    "provider": "jwt",
                                    "credentials": {
                                        "email": "test@example.com",
                                        "password": "password"
                                    }
                                }
                            )
                            
                            assert response.status_code == 200
                            data = response.json()
                            assert data["status"] == "success"
                            assert data["user"]["email"] == "test@example.com"
                            assert "access_token" in data
                            assert "token_type" in data
    
    @pytest.mark.asyncio
    async def test_jwt_login_endpoint_missing_credentials(self):
        """Test JWT login endpoint with missing credentials"""
        from src.main import app
        async with AsyncClient(app=app, base_url="http://test") as ac:
            response = await ac.post(
                "/api/v1/auth/enhanced/login",
                json={
                    "provider": "jwt",
                    "credentials": {
                        "email": "test@example.com"  # Missing password
                    }
                }
            )
            
            assert response.status_code == 422
            data = response.json()
            assert "detail" in data
    
    @pytest.mark.asyncio
    async def test_jwt_login_endpoint_invalid_provider(self):
        """Test JWT login endpoint with invalid provider"""
        from src.main import app
        async with AsyncClient(app=app, base_url="http://test") as ac:
            response = await ac.post(
                "/api/v1/auth/enhanced/login",
                json={
                    "provider": "invalid",
                    "credentials": {
                        "email": "test@example.com",
                        "password": "password"
                    }
                }
            )
            
            assert response.status_code == 200  # Should fallback to JWT
            data = response.json()
            assert data["status"] == "success"
    
    @pytest.mark.asyncio
    async def test_jwt_register_endpoint_success(self):
        """Test JWT registration endpoint success"""
        from src.main import app
        async with AsyncClient(app=app, base_url="http://test") as ac:
            # Mock authentication gateway
            with patch('src.core.auth_gateway.auth_gateway.create_user') as mock_create:
                mock_create.return_value = {
                    "user_id": "new_user_123",
                    "email": "new@example.com",
                    "name": "New User",
                    "role": "student",
                    "provider": AuthProvider.JWT,
                    "access_token": "new_token"
                }
                
                response = await ac.post(
                    "/api/v1/auth/enhanced/register",
                    json={
                        "provider": "jwt",
                        "user_data": {
                            "email": "new@example.com",
                            "password": "password123",
                            "name": "New User",
                            "role": "student"
                        }
                    }
                )
                
                assert response.status_code == 201
                data = response.json()
                assert data["status"] == "success"
                assert data["user"]["email"] == "new@example.com"
                assert "access_token" in data
    
    @pytest.mark.asyncio
    async def test_register_endpoint_missing_user_data(self):
        """Test registration endpoint with missing user data"""
        from src.main import app
        async with AsyncClient(app=app, base_url="http://test") as ac:
            response = await ac.post(
                "/api/v1/auth/enhanced/register",
                json={
                    "provider": "jwt",
                    "user_data": {
                        "email": "new@example.com"  # Missing required fields
                    }
                }
            )
            
            assert response.status_code == 422
            data = response.json()
            assert "detail" in data
    
    @pytest.mark.asyncio
    async def test_firebase_login_endpoint_not_configured(self):
        """Test Firebase login endpoint when Firebase is not configured"""
        from src.main import app
        async with AsyncClient(app=app, base_url="http://test") as ac:
            response = await ac.post(
                "/api/v1/auth/enhanced/login",
                json={
                    "provider": "firebase",
                    "credentials": {
                        "id_token": "test_token"
                    }
                }
            )
            
            assert response.status_code == 200  # Should handle gracefully
            data = response.json()
            # Should contain error information or appropriate response
            assert "status" in data
    
    @pytest.mark.asyncio
    async def test_provider_health_endpoint_jwt(self):
        """Test provider health check endpoint for JWT"""
        from src.main import app
        async with AsyncClient(app=app, base_url="http://test") as ac:
            response = await ac.get("/api/v1/auth/enhanced/providers/jwt/health")
            
            assert response.status_code == 200
            data = response.json()
            assert data["status"] == "healthy"
            assert data["provider"] == "jwt"
            assert "last_checked" in data
    
    @pytest.mark.asyncio
    async def test_provider_health_endpoint_firebase(self):
        """Test provider health check endpoint for Firebase"""
        from src.main import app
        async with AsyncClient(app=app, base_url="http://test") as ac:
            response = await ac.get("/api/v1/auth/enhanced/providers/firebase/health")
            
            assert response.status_code == 200
            data = response.json()
            assert data["provider"] == "firebase"
            assert "configured" in data
            assert "status" in data
    
    @pytest.mark.asyncio
    async def test_list_providers_endpoint(self):
        """Test list providers endpoint"""
        from src.main import app
        async with AsyncClient(app=app, base_url="http://test") as ac:
            response = await ac.get("/api/v1/auth/enhanced/providers")
            
            assert response.status_code == 200
            data = response.json()
            assert data["status"] == "success"
            assert "providers" in data
            
            # Check for JWT provider
            jwt_provider = next((p for p in data["providers"] if p["id"] == "jwt"), None)
            assert jwt_provider is not None
            assert jwt_provider["status"] == "healthy"
            assert jwt_provider["default"] == True
    
    @pytest.mark.asyncio
    async def test_logout_endpoint(self):
        """Test logout endpoint"""
        from src.main import app
        async with AsyncClient(app=app, base_url="http://test") as ac:
            response = await ac.post(
                "/api/v1/auth/enhanced/logout",
                json={"provider": "jwt"}
            )
            
            assert response.status_code == 200
            data = response.json()
            assert data["status"] == "success"
            assert data["message"] == "Successfully logged out"
    
    @pytest.mark.asyncio
    async def test_forgot_password_endpoint(self):
        """Test forgot password endpoint"""
        from src.main import app
        async with AsyncClient(app=app, base_url="http://test") as ac:
            # Mock user service find_by_email
            with patch('src.core.auth_gateway.user_service.find_by_email') as mock_find:
                mock_find.return_value = {
                    "user_id": "123",
                    "email": "test@example.com",
                    "name": "Test User"
                }
                
                response = await ac.post(
                    "/api/v1/auth/enhanced/forgot-password",
                    json={"email": "test@example.com"}
                )
                
                assert response.status_code == 200
                data = response.json()
                assert data["status"] == "success"
                assert "message" in data
    
    @pytest.mark.asyncio
    async def test_forgot_password_email_not_found(self):
        """Test forgot password endpoint with email not found"""
        from src.main import app
        async with AsyncClient(app=app, base_url="http://test") as ac:
            # Mock user service find_by_email
            with patch('src.core.auth_gateway.user_service.find_by_email') as mock_find:
                mock_find.return_value = None
                
                response = await ac.post(
                    "/api/v1/auth/enhanced/forgot-password",
                    json={"email": "notfound@example.com"}
                )
                
                assert response.status_code == 200  # Still return success for security
                data = response.json()
                assert data["status"] == "success"
    
    @pytest.mark.asyncio
    async def test_change_password_endpoint(self):
        """Test change password endpoint"""
        from src.main import app
        async with AsyncClient(app=app, base_url="http://test") as ac:
            # Mock user authentication and verification
            with patch('src.core.auth_gateway.user_service.get') as mock_get:
                mock_get.return_value = {
                    "user_id": "123",
                    "email": "test@example.com"
                }
            
            with patch('src.core.auth_gateway.user_service.update') as mock_update:
                mock_update.return_value = True
                
                response = await ac.put(
                    "/api/v1/auth/enhanced/change-password",
                    json={
                        "current_password": "old_password",
                        "new_password": "new_password123"
                    }
                )
                
                assert response.status_code == 200
                data = response.json()
                assert data["status"] == "success"
                assert data["message"] == "Password changed successfully"
    
    @pytest.mark.asyncio
    async def test_change_password_missing_fields(self):
        """Test change password endpoint with missing fields"""
        from src.main import app
        async with AsyncClient(app=app, base_url="http://test") as ac:
            response = await ac.put(
                "/api/v1/auth/enhanced/change-password",
                json={
                    "current_password": "old_password"
                    # Missing new_password
                }
            )
            
            assert response.status_code == 422
            data = response.json()
            assert "detail" in data

class TestErrorHandling:
    """Test error handling in authentication endpoints"""
    
    @pytest.mark.asyncio
    async def test_authentication_error_handling(self):
        """Test handling of authentication errors"""
        from src.main import app
        async with AsyncClient(app=app, base_url="http://test") as ac:
            # Mock authentication to raise an error
            with patch('src.core.auth_gateway.auth_gateway.authenticate') as mock_auth:
                mock_auth.side_effect = AuthenticationError("Authentication failed")
                
                response = await ac.post(
                    "/api/v1/auth/enhanced/login",
                    json={
                        "provider": "jwt",
                        "credentials": {
                            "email": "test@example.com",
                            "password": "wrong_password"
                        }
                    }
                )
                
                assert response.status_code == 401
                data = response.json()
                assert data["status"] == "error"
                assert "Authentication failed" in data["message"]
    
    @pytest.mark.asyncio
    async def test_validation_error_handling(self):
        """Test handling of validation errors"""
        from src.main import app
        async with AsyncClient(app=app, base_url="http://test") as ac:
            response = await ac.post(
                "/api/v1/auth/enhanced/login",
                json={
                    "provider": "jwt"
                    # Missing credentials
                }
            )
            
            assert response.status_code == 422
            data = response.json()
            assert "detail" in data
    
    @pytest.mark.asyncio
    async def test_system_error_handling(self):
        """Test handling of system errors"""
        from src.main import app
        async with AsyncClient(app=app, base_url="http://test") as ac:
            # Mock authentication to raise a system error
            with patch('src.core.auth_gateway.auth_gateway.authenticate') as mock_auth:
                mock_auth.side_effect = Exception("System error")
                
                response = await ac.post(
                    "/api/v1/auth/enhanced/login",
                    json={
                        "provider": "jwt",
                        "credentials": {
                            "email": "test@example.com",
                            "password": "password"
                        }
                    }
                )
                
                assert response.status_code == 500
                data = response.json()
                assert data["status"] == "error"
                assert "Internal server error" in data["message"]

class TestCORSHeaders:
    """Test CORS headers in authentication endpoints"""
    
    @pytest.mark.asyncio
    async def test_cors_headers_present(self):
        """Test that CORS headers are present in responses"""
        from src.main import app
        async with AsyncClient(app=app, base_url="http://test") as ac:
            response = await ac.post(
                "/api/v1/auth/enhanced/login",
                json={
                    "provider": "jwt",
                    "credentials": {
                        "email": "test@example.com",
                        "password": "password"
                    }
                }
            )
            
            # Check CORS headers
            assert "access-control-allow-origin" in response.headers
            assert "access-control-allow-headers" in response.headers
            assert "access-control-allow-methods" in response.headers
    
    @pytest.mark.asyncio
    async def test_preflight_request_handling(self):
        """Test handling of preflight OPTIONS requests"""
        from src.main import app
        async with AsyncClient(app=app, base_url="http://test") as ac:
            response = await ac.options("/api/v1/auth/enhanced/login")
            
            assert response.status_code == 200
            assert "access-control-allow-origin" in response.headers
            assert "access-control-allow-methods" in response.headers
            assert "access-control-allow-headers" in response.headers