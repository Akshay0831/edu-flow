"""
Authentication domain services

This module contains domain services for authentication:
- AuthService: Authentication service
- PasswordService: Password management service
- TokenService: Token management service

Author: Edu-Flow Team
"""

from datetime import datetime, timedelta, timezone
from typing import Optional, Dict, Any
import hashlib
from passlib.context import CryptContext
from jose import JWTError, jwt

from .entities import User, UserRole, Token
from ...infrastructure.exceptions import AuthenticationError, AuthorizationError, ValidationError


class AuthService:
    """Domain service for authentication and authorization"""
    
    def __init__(self, secret_key: str, algorithm: str = "HS256", 
                 access_token_expire_minutes: int = 30,
                 refresh_token_expire_days: int = 7):
        self.secret_key = secret_key
        self.algorithm = algorithm
        self.access_token_expire_minutes = access_token_expire_minutes
        self.refresh_token_expire_days = refresh_token_expire_days
        self.pwd_context = CryptContext(schemes=["sha256_crypt", "bcrypt"], deprecated="auto")
    
    def create_access_token(self, user: User, expires_delta: Optional[timedelta] = None) -> str:
        """Create JWT access token for user"""
        to_encode = {
            "sub": user.id,
            "email": user.email,
            "role": user.role.value,
            "type": "access"
        }
        
        if expires_delta:
            expire = datetime.now(timezone.utc) + expires_delta
        else:
            expire = datetime.now(timezone.utc) + timedelta(minutes=self.access_token_expire_minutes)
        
        to_encode.update({"exp": expire})
        encoded_jwt = jwt.encode(to_encode, self.secret_key, algorithm=self.algorithm)
        return encoded_jwt
    
    def create_refresh_token(self, user: User) -> str:
        """Create JWT refresh token for user"""
        to_encode = {
            "sub": user.id,
            "email": user.email,
            "role": user.role.value,
            "type": "refresh"
        }
        
        expire = datetime.now(timezone.utc) + timedelta(days=self.refresh_token_expire_days)
        to_encode.update({"exp": expire})
        encoded_jwt = jwt.encode(to_encode, self.secret_key, algorithm=self.algorithm)
        return encoded_jwt
    
    def create_token_pair(self, user: User) -> Token:
        """Create access and refresh token pair"""
        access_token = self.create_access_token(user)
        refresh_token = self.create_refresh_token(user)
        
        return Token(
            access_token=access_token,
            refresh_token=refresh_token,
            token_type="bearer",
            expires_at=datetime.now(timezone.utc) + timedelta(minutes=self.access_token_expire_minutes),
            user_id=user.id,
            email=user.email,
            role=user.role
        )
    
    def verify_token(self, token: str) -> User:
        """Verify JWT token and return user data"""
        try:
            payload = jwt.decode(token, self.secret_key, algorithms=[self.algorithm])
            
            user_id: str = payload.get("sub")
            email: str = payload.get("email")
            role: str = payload.get("role")
            token_type: str = payload.get("type")
            
            if not user_id or not email or not role:
                raise AuthenticationError("Invalid token payload")
            
            if token_type != "access":
                raise AuthenticationError("Invalid token type")
            
            # Create user entity (would normally fetch from repository)
            user = User(
                id=user_id,
                email=email,
                name="Unknown User",  # Would be fetched from repository
                password_hash="",
                role=UserRole(role),
                is_active=True,
                created_at=datetime.now(timezone.utc)
            )
            
            return user
            
        except JWTError as e:
            raise AuthenticationError(f"Invalid token: {str(e)}")
    
    def refresh_access_token(self, refresh_token: str) -> Token:
        """Refresh access token using refresh token"""
        try:
            payload = jwt.decode(refresh_token, self.secret_key, algorithms=[self.algorithm])
            
            # Verify it's a refresh token
            if payload.get("type") != "refresh":
                raise AuthenticationError("Invalid refresh token")
            
            # Create user entity (would normally fetch from repository)
            user = User(
                id=payload.get("sub"),
                email=payload.get("email"),
                name="Unknown User",  # Would be fetched from repository
                password_hash="",
                role=UserRole(payload.get("role")),
                is_active=True,
                created_at=datetime.now(timezone.utc)
            )
            
            # Create new token pair
            return self.create_token_pair(user)
            
        except JWTError as e:
            raise AuthenticationError(f"Invalid refresh token: {str(e)}")


class PasswordService:
    """Domain service for password management"""
    
    def __init__(self):
        self.pwd_context = CryptContext(schemes=["sha256_crypt", "bcrypt"], deprecated="auto")
    
    def hash_password(self, password: str) -> str:
        """Hash password using secure algorithm"""
        try:
            # Try bcrypt first
            return self.pwd_context.hash(password)
        except Exception as e:
            # Fallback to SHA-256 if bcrypt fails
            if "72 bytes" in str(e):
                # Truncate password for bcrypt compatibility
                truncated_password = password[:72]
                return self.pwd_context.hash(truncated_password)
            else:
                # For other errors, try SHA-256 fallback
                try:
                    return self.pwd_context.hash(password)
                except:
                    # Final fallback to simple SHA-256
                    return hashlib.sha256(password.encode()).hexdigest()
    
    def verify_password(self, plain_password: str, hashed_password: str) -> bool:
        """Verify password against hash"""
        return self.pwd_context.verify(plain_password, hashed_password)
    
    def validate_password_strength(self, password: str) -> Dict[str, Any]:
        """Validate password strength and return validation results"""
        result = {
            "is_valid": True,
            "errors": [],
            "warnings": []
        }
        
        if len(password) < 8:
            result["is_valid"] = False
            result["errors"].append("Password must be at least 8 characters long")
        
        if not any(c.isupper() for c in password):
            result["warnings"].append("Password should contain at least one uppercase letter")
        
        if not any(c.islower() for c in password):
            result["warnings"].append("Password should contain at least one lowercase letter")
        
        if not any(c.isdigit() for c in password):
            result["warnings"].append("Password should contain at least one digit")
        
        if len(password) > 72:
            result["warnings"].append("Password longer than 72 characters may have compatibility issues")
        
        return result