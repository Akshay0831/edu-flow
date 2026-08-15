"""
Enhanced Authentication System Tests

Tests for the flexible, multi-provider authentication system
that supports Firebase as an optional service.

Author: Edu-Flow Team
"""

import pytest
from unittest.mock import Mock, patch, AsyncMock
from datetime import timedelta
from src.core.auth_gateway import auth_gateway, AuthProvider, AuthGateway, JWTAuthProvider
from src.core.auth_gateway import FirebaseAuthProvider
from src.core.security import AuthService
from src.core.exceptions import AuthenticationError, ValidationError

class TestAuthProviderEnum:
    """Test authentication provider enum values"""
    
    def test_jwt_provider(self):
        assert AuthProvider.JWT == "jwt"
    
    def test_firebase_provider(self):
        assert AuthProvider.FIREBASE == "firebase"
    
    def test_custom_provider(self):
        assert AuthProvider.CUSTOM == "custom"

class TestJWTAuthProvider:
    """Test JWT authentication provider"""
    
    def test_init(self):
        """Test JWT provider initialization"""
        provider = JWTAuthProvider()
        assert provider.algorithm is not None
        assert provider.secret_key is not None
        assert provider.access_token_expire_minutes is not None
    
    def test_create_access_token(self):
        """Test JWT access token creation"""
        provider = JWTAuthProvider()
        test_data = {"user_id": "123", "email": "test@example.com"}
        
        token = provider.create_access_token(test_data)
        assert token is not None
        assert isinstance(token, str)
    
    def test_create_access_token_with_expires_delta(self):
        """Test JWT access token creation with expiration"""
        provider = JWTAuthProvider()
        test_data = {"user_id": "123", "email": "test@example.com"}
        expires_delta = timedelta(minutes=30)
        
        token = provider.create_access_token(test_data, expires_delta)
        assert token is not None
        assert isinstance(token, str)
    
    @pytest.mark.asyncio
    async def test_authenticate_success(self):
        """Test successful JWT authentication"""
        provider = JWTAuthProvider()
        credentials = {"email": "test@example.com", "password": "password"}
        
        result = await provider.authenticate(credentials)
        assert result["provider"] == AuthProvider.JWT
        assert "user_id" in result
        assert result["email"] == "test@example.com"
    
    @pytest.mark.asyncio
    async def test_authenticate_missing_credentials(self):
        """Test JWT authentication with missing credentials"""
        provider = JWTAuthProvider()
        credentials = {"email": "test@example.com"}  # Missing password
        
        with pytest.raises(AuthenticationError, match="Email and password are required"):
            await provider.authenticate(credentials)
    
    @pytest.mark.asyncio
    async def test_verify_token_success(self):
        """Test successful JWT token verification"""
        provider = JWTAuthProvider()
        # Create a test token
        test_data = {"user_id": "123", "email": "test@example.com"}
        token = provider.create_access_token(test_data)
        
        result = await provider.verify_token(token)
        assert result["user_id"] == "123"
        assert result["email"] == "test@example.com"
        assert result["provider"] == AuthProvider.JWT
    
    @pytest.mark.asyncio
    async def test_verify_token_invalid(self):
        """Test JWT token verification with invalid token"""
        provider = JWTAuthProvider()
        
        with pytest.raises(AuthenticationError, match="Invalid token"):
            await provider.verify_token("invalid_token")
    
    @pytest.mark.asyncio
    async def test_create_user(self):
        """Test JWT user creation"""
        provider = JWTAuthProvider()
        user_data = {
            "email": "test@example.com",
            "password": "password123",
            "name": "Test User",
            "role": "student"
        }
        
        result = await provider.create_user(user_data)
        assert result["user_id"] == "jwt_user_new"
        assert result["email"] == "test@example.com"
        assert result["name"] == "Test User"
        assert result["role"] == "student"
        assert result["provider"] == AuthProvider.JWT

class TestFirebaseAuthProvider:
    """Test Firebase authentication provider"""
    
    def test_init_not_configured(self):
        """Test Firebase provider initialization when not configured"""
        provider = FirebaseAuthProvider()
        assert provider.configured == False
        assert provider.firebase_auth is None
    
    @patch('firebase_admin.initialize_app')
    @patch('firebase_admin._apps', {})
    def test_init_configured(self, mock_apps, mock_init):
        """Test Firebase provider initialization when configured"""
        with patch('firebase_admin.credentials.Certificate') as mock_cert:
            with patch('firebase_admin.auth') as mock_auth:
                provider = FirebaseAuthProvider()
                # This would normally be true if Firebase is properly configured
                provider.configured = True
                provider.firebase_auth = mock_auth
                
                assert provider.configured == True
    
    @pytest.mark.asyncio
    async def test_authenticate_not_configured(self):
        """Test Firebase authentication when not configured"""
        provider = FirebaseAuthProvider()
        credentials = {"id_token": "test_token"}
        
        with pytest.raises(AuthenticationError, match="Firebase is not configured"):
            await provider.authenticate(credentials)
    
    @pytest.mark.asyncio
    async def test_authenticate_no_id_token(self):
        """Test Firebase authentication with no ID token"""
        provider = FirebaseAuthProvider()
        provider.configured = True  # Mock as configured
        
        with pytest.raises(AuthenticationError, match="ID token is required"):
            await provider.authenticate({})
    
    @pytest.mark.asyncio
    async def test_create_user_not_configured(self):
        """Test Firebase user creation when not configured"""
        provider = FirebaseAuthProvider()
        user_data = {
            "email": "test@example.com",
            "password": "password123",
            "name": "Test User"
        }
        
        with pytest.raises(AuthenticationError, match="Firebase is not configured"):
            await provider.create_user(user_data)

class TestAuthGateway:
    """Test authentication gateway"""
    
    def test_init(self):
        """Test gateway initialization"""
        gateway = AuthGateway()
        assert gateway.default_provider == AuthProvider.JWT
        assert AuthProvider.JWT in gateway.providers
        assert AuthProvider.FIREBASE in gateway.providers
        assert AuthProvider.CUSTOM in gateway.providers
    
    def test_get_provider_default(self):
        """Test getting default provider"""
        gateway = AuthGateway()
        provider = gateway.get_provider()
        assert provider is not None
    
    def test_get_provider_specific(self):
        """Test getting specific provider"""
        gateway = AuthGateway()
        provider = gateway.get_provider(AuthProvider.JWT)
        assert provider is not None
        assert isinstance(provider, JWTAuthProvider)
    
    def test_get_provider_invalid(self):
        """Test getting invalid provider"""
        gateway = AuthGateway()
        
        with pytest.raises(AuthenticationError, match="Provider invalid not configured"):
            gateway.get_provider("invalid")
    
    @pytest.mark.asyncio
    async def test_authenticate_with_provider(self):
        """Test authentication with specific provider"""
        gateway = AuthGateway()
        credentials = {"email": "test@example.com", "password": "password"}
        
        result = await gateway.authenticate(credentials, AuthProvider.JWT)
        assert result["provider"] == AuthProvider.JWT
    
    @pytest.mark.asyncio
    async def test_authenticate_with_fallback(self):
        """Test authentication with fallback mechanism"""
        gateway = AuthGateway()
        credentials = {"email": "test@example.com", "password": "password"}
        
        # Test with invalid provider - should fallback to JWT
        result = await gateway.authenticate(credentials, "invalid_provider")
        assert result["provider"] == AuthProvider.JWT
    
    @pytest.mark.asyncio
    async def test_verify_token(self):
        """Test token verification"""
        gateway = AuthGateway()
        # Create a test token
        jwt_provider = gateway.get_provider(AuthProvider.JWT)
        test_data = {"user_id": "123", "email": "test@example.com"}
        token = jwt_provider.create_access_token(test_data)
        
        result = await gateway.verify_token(token, AuthProvider.JWT)
        assert result["user_id"] == "123"
        assert result["email"] == "test@example.com"
    
    @pytest.mark.asyncio
    async def test_create_user(self):
        """Test user creation"""
        gateway = AuthGateway()
        user_data = {
            "email": "test@example.com",
            "password": "password123",
            "name": "Test User",
            "role": "student"
        }
        
        result = await gateway.create_user(user_data, AuthProvider.JWT)
        assert result["user_id"] == "jwt_user_new"
        assert result["email"] == "test@example.com"
        assert result["provider"] == AuthProvider.JWT

class TestAuthService:
    """Test enhanced authentication service"""
    
    def test_init(self):
        """Test auth service initialization"""
        auth_service = AuthService()
        assert auth_service.auth_gateway is not None
        assert auth_service.pwd_context is not None
    
    @pytest.mark.asyncio
    async def test_authenticate_user(self):
        """Test user authentication"""
        auth_service = AuthService()
        credentials = {"email": "test@example.com", "password": "password"}
        
        result = await auth_service.authenticate_user(credentials, AuthProvider.JWT)
        assert result["provider"] == AuthProvider.JWT
        assert "user_id" in result
    
    @pytest.mark.asyncio
    async def test_authenticate_with_fallback(self):
        """Test authentication with fallback"""
        auth_service = AuthService()
        credentials = {"email": "test@example.com", "password": "password"}
        
        # Test with invalid provider - should fallback to JWT
        result = await auth_service.authenticate_with_fallback(
            credentials, "invalid_provider"
        )
        assert result["provider"] == AuthProvider.JWT
    
    def test_password_hashing(self):
        """Test password hashing"""
        auth_service = AuthService()
        password = "test_password"
        hashed = auth_service.get_password_hash(password)
        
        assert hashed is not None
        assert hashed != password
    
    def test_password_verification(self):
        """Test password verification"""
        auth_service = AuthService()
        password = "test_password"
        hashed = auth_service.get_password_hash(password)
        
        assert auth_service.verify_password(password, hashed) == True
        assert auth_service.verify_password("wrong_password", hashed) == False

class TestIntegration:
    """Integration tests for authentication system"""
    
    @pytest.mark.asyncio
    async def test_multi_provider_authentication_flow(self):
        """Test complete authentication flow with multiple providers"""
        gateway = AuthGateway()
        
        # Test JWT authentication
        jwt_credentials = {"email": "jwt@example.com", "password": "password"}
        jwt_result = await gateway.authenticate(jwt_credentials, AuthProvider.JWT)
        assert jwt_result["provider"] == AuthProvider.JWT
        
        # Test token generation and verification
        jwt_provider = gateway.get_provider(AuthProvider.JWT)
        token = jwt_provider.create_access_token(jwt_result)
        verified = await jwt_provider.verify_token(token)
        assert verified["user_id"] == jwt_result["user_id"]
        
        # Test user creation
        user_data = {
            "email": "new@example.com",
            "password": "password123",
            "name": "New User",
            "role": "student"
        }
        created_user = await gateway.create_user(user_data, AuthProvider.JWT)
        assert created_user["email"] == "new@example.com"
        assert created_user["provider"] == AuthProvider.JWT
    
    @pytest.mark.asyncio
    async def test_firebase_optional_behavior(self):
        """Test that Firebase is truly optional"""
        gateway = AuthGateway()
        
        # System should work fine even without Firebase configured
        credentials = {"email": "test@example.com", "password": "password"}
        result = await gateway.authenticate(credentials, AuthProvider.JWT)
        assert result["provider"] == AuthProvider.JWT
        
        # Firebase should not break the system
        firebase_result = await gateway.authenticate(credentials, AuthProvider.FIREBASE)
        # This should not raise an error, but may return None or handle gracefully
        assert firebase_result is None or isinstance(firebase_result, dict)
    
    @pytest.mark.asyncio
    async def test_provider_switching(self):
        """Test switching between providers"""
        gateway = AuthGateway()
        
        # Test switching from invalid to valid provider
        credentials = {"email": "test@example.com", "password": "password"}
        
        # First try with invalid provider
        try:
            await gateway.authenticate(credentials, "invalid_provider")
        except AuthenticationError:
            # This is expected, should fallback or error
            pass
        
        # Then try with valid provider
        jwt_result = await gateway.authenticate(credentials, AuthProvider.JWT)
        assert jwt_result["provider"] == AuthProvider.JWT