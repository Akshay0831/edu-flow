"""
Authentication Gateway for Edu-Flow Backend

This module provides a flexible authentication system supporting multiple providers:
- JWT (default)
- Firebase (optional)
- Custom authentication
- Future: LDAP, OAuth2

The gateway ensures no dependency on third-party services while providing
flexibility to use them when configured.

Author: Edu-Flow Team
"""

from datetime import datetime, timedelta, timezone
from typing import Optional, Dict, Any, List, Union
import hashlib
import re
from abc import ABC, abstractmethod
from passlib.context import CryptContext
from jose import JWTError, jwt
from pydantic import BaseModel

try:
    import bcrypt
except ImportError:
    bcrypt = None

from core.exceptions import AuthenticationError, AuthorizationError, ValidationError, NotFoundError
from core.config.settings import settings

# Authentication providers enum
class AuthProvider:
    JWT = "jwt"
    FIREBASE = "firebase"
    CUSTOM = "custom"
    LDAP = "ldap"  # Future enhancement
    OAUTH2 = "oauth2"  # Future enhancement

# Token data model
class TokenData(BaseModel):
    sub: str
    email: Optional[str] = None
    role: Optional[str] = None
    exp: Optional[datetime] = None
    type: Optional[str] = None
    provider: Optional[str] = None

class AuthProviderInterface(ABC):
    """Abstract interface for authentication providers"""
    
    @abstractmethod
    async def authenticate(self, credentials: Dict[str, Any]) -> Dict[str, Any]:
        """Authenticate user with provider-specific credentials"""
        pass
    
    @abstractmethod
    async def verify_token(self, token: str) -> Dict[str, Any]:
        """Verify and decode provider token"""
        pass
    
    @abstractmethod
    async def create_user(self, user_data: Dict[str, Any]) -> Dict[str, Any]:
        """Create user with provider"""
        pass

class JWTAuthProvider(AuthProviderInterface):
    """JWT-based authentication provider"""
    
    def __init__(self):
        self.secret_key = settings.security.secret_key
        self.algorithm = settings.security.algorithm
        self.access_token_expire_minutes = settings.security.access_token_expire_minutes
    
    def create_access_token(self, data: Dict[str, Any], expires_delta: Optional[timedelta] = None) -> str:
        """Create JWT access token"""
        to_encode = data.copy()
        if expires_delta:
            expire = datetime.now(timezone.utc) + expires_delta
        else:
            expire = datetime.now(timezone.utc) + timedelta(minutes=self.access_token_expire_minutes)
        
        to_encode.update({"exp": expire, "type": "access", "provider": AuthProvider.JWT})
        encoded_jwt = jwt.encode(to_encode, self.secret_key, algorithm=self.algorithm)
        return encoded_jwt
    
    async def authenticate(self, credentials: Dict[str, Any]) -> Dict[str, Any]:
        """Authenticate with JWT credentials"""
        email = credentials.get("email")
        password = credentials.get("password")
        
        if not email or not password:
            raise AuthenticationError("Email and password are required")
        
        # This would be implemented to check against your user database
        # For now, return a placeholder user
        return {
            "user_id": "jwt_user_123",
            "email": email,
            "name": "JWT User",
            "role": "user",
            "provider": AuthProvider.JWT
        }
    
    async def verify_token(self, token: str) -> Dict[str, Any]:
        """Verify JWT token"""
        try:
            payload = jwt.decode(token, self.secret_key, algorithms=[self.algorithm])
            return {
                "user_id": payload.get("sub"),
                "email": payload.get("email"),
                "name": payload.get("name"),
                "role": payload.get("role"),
                "provider": payload.get("provider", AuthProvider.JWT)
            }
        except JWTError:
            raise AuthenticationError("Invalid token")
    
    async def create_user(self, user_data: Dict[str, Any]) -> Dict[str, Any]:
        """Create JWT user"""
        # Implement user creation in your database
        return {
            "user_id": "jwt_user_new",
            "email": user_data.get("email"),
            "name": user_data.get("name"),
            "role": user_data.get("role", "user"),
            "provider": AuthProvider.JWT
        }

class FirebaseAuthProvider(AuthProviderInterface):
    """Firebase authentication provider"""
    
    def __init__(self):
        self.configured = False
        self.firebase_auth = None
        try:
            import firebase_admin
            from firebase_admin import auth as firebase_auth
            if firebase_admin._apps:
                self.firebase_auth = firebase_auth
                self.configured = True
        except ImportError:
            self.configured = False
    
    async def authenticate(self, credentials: Dict[str, Any]) -> Dict[str, Any]:
        """Authenticate with Firebase"""
        if not self.configured:
            raise AuthenticationError("Firebase is not configured")
        
        try:
            id_token = credentials.get("id_token")
            if not id_token:
                raise AuthenticationError("ID token is required")
            
            # Decode Firebase token
            decoded_token = self.firebase_auth.verify_id_token(id_token)
            return {
                "user_id": decoded_token.get("uid"),
                "email": decoded_token.get("email"),
                "name": decoded_token.get("name") or decoded_token.get("displayName"),
                "role": decoded_token.get("role", "user"),
                "provider": AuthProvider.FIREBASE
            }
        except Exception as e:
            raise AuthenticationError(f"Firebase authentication failed: {str(e)}")
    
    async def verify_token(self, token: str) -> Dict[str, Any]:
        """Verify Firebase token"""
        if not self.configured:
            raise AuthenticationError("Firebase is not configured")
        
        try:
            decoded_token = self.firebase_auth.verify_id_token(token)
            return {
                "user_id": decoded_token.get("uid"),
                "email": decoded_token.get("email"),
                "name": decoded_token.get("name") or decoded_token.get("displayName"),
                "role": decoded_token.get("role", "user"),
                "provider": AuthProvider.FIREBASE
            }
        except Exception as e:
            raise AuthenticationError(f"Firebase token verification failed: {str(e)}")
    
    async def create_user(self, user_data: Dict[str, Any]) -> Dict[str, Any]:
        """Create Firebase user"""
        if not self.configured:
            raise AuthenticationError("Firebase is not configured")
        
        try:
            user_record = self.firebase_auth.create_user(
                email=user_data.get("email"),
                password=user_data.get("password"),
                display_name=user_data.get("name")
            )
            return {
                "user_id": user_record.uid,
                "email": user_record.email,
                "name": user_record.display_name,
                "role": user_data.get("role", "user"),
                "provider": AuthProvider.FIREBASE
            }
        except Exception as e:
            raise AuthenticationError(f"Firebase user creation failed: {str(e)}")

class AuthGateway:
    """Authentication gateway supporting multiple providers"""
    
    def __init__(self):
        self.providers = {
            AuthProvider.JWT: JWTAuthProvider(),
            AuthProvider.FIREBASE: FirebaseAuthProvider(),
            AuthProvider.CUSTOM: JWTAuthProvider()  # Custom uses JWT internally
        }
        self.default_provider = AuthProvider.JWT
    
    def configure_provider(self, provider_name: str, provider_config: Dict[str, Any]):
        """Configure a specific authentication provider"""
        if provider_name == AuthProvider.FIREBASE:
            self.providers[provider_name] = FirebaseAuthProvider()
        else:
            # For JWT and custom, update configuration
            if provider_name in self.providers:
                self.providers[provider_name].__dict__.update(provider_config)
    
    def get_provider(self, provider_name: str = None) -> AuthProviderInterface:
        """Get authentication provider"""
        provider = provider_name or self.default_provider
        if provider not in self.providers:
            raise AuthenticationError(f"Provider {provider} not configured")
        return self.providers[provider]
    
    async def authenticate(self, credentials: Dict[str, Any], provider: str = None) -> Dict[str, Any]:
        """Authenticate using specified provider"""
        auth_provider = self.get_provider(provider)
        return await auth_provider.authenticate(credentials)
    
    async def verify_token(self, token: str, provider: str = None) -> Dict[str, Any]:
        """Verify token using specified provider"""
        auth_provider = self.get_provider(provider)
        return await auth_provider.verify_token(token)
    
    async def create_user(self, user_data: Dict[str, Any], provider: str = None) -> Dict[str, Any]:
        """Create user using specified provider"""
        auth_provider = self.get_provider(provider)
        return await auth_provider.create_user(user_data)

# Global authentication gateway instance
auth_gateway = AuthGateway()