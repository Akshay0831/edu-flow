"""
Security module for Edu-Flow Backend

This module provides authentication, authorization, and security utilities:
- JWT token generation and verification
- Password hashing and validation
- Session management
- Security middleware

Author: Edu-Flow Team
"""

from datetime import datetime, timedelta, timezone
from typing import Optional, Dict, Any
import hashlib
import re
from passlib.context import CryptContext
from jose import JWTError, jwt
from fastapi import Depends, HTTPException, status
from pydantic import BaseModel

try:
    import bcrypt
except ImportError:
    bcrypt = None

from src.core.exceptions import AuthenticationError, AuthorizationError, ValidationError, NotFoundError
from src.config.settings import settings

# Password context for hashing with fallback
pwd_context = CryptContext(schemes=["sha256_crypt", "bcrypt"], deprecated="auto")

# Token data model
class TokenData(BaseModel):
    sub: str
    email: Optional[str] = None
    role: Optional[str] = None
    exp: Optional[datetime] = None
    type: Optional[str] = None

class AuthService:
    """Authentication service for handling JWT tokens and password management"""
    
    def __init__(self, user_service=None):
        self.pwd_context = pwd_context
        self.secret_key = settings.secret_key
        self.algorithm = settings.algorithm
        self.access_token_expire_minutes = settings.access_token_expire_minutes
        self.user_service = user_service
        
    def create_access_token(self, data: dict, expires_delta: Optional[timedelta] = None) -> str:
        """Create JWT access token"""
        to_encode = data.copy()
        
        # Map user_id to sub if present
        if "user_id" in to_encode:
            to_encode["sub"] = to_encode.pop("user_id")
        
        if expires_delta:
            expire = datetime.now(timezone.utc) + expires_delta
        else:
            expire = datetime.now(timezone.utc) + timedelta(minutes=self.access_token_expire_minutes)
            
        to_encode.update({"exp": expire})
        encoded_jwt = jwt.encode(to_encode, self.secret_key, algorithm=self.algorithm)
        return encoded_jwt
    
    def decode_token(self, token: str) -> dict:
        """Decode and validate JWT token"""
        try:
            payload = jwt.decode(token, self.secret_key, algorithms=[self.algorithm])
            return payload
        except JWTError:
            raise AuthenticationError("Invalid token")
    
    def create_refresh_token(self, data: dict) -> str:
        """Create JWT refresh token"""
        to_encode = data.copy()
        
        # Map user_id to sub if present
        if "user_id" in to_encode:
            to_encode["sub"] = to_encode.pop("user_id")
        
        expire = datetime.now(timezone.utc) + timedelta(days=settings.refresh_token_expire_days)
        to_encode.update({"exp": expire, "type": "refresh"})
        encoded_jwt = jwt.encode(to_encode, self.secret_key, algorithm=self.algorithm)
        return encoded_jwt
    
    def create_token_pair(self, data: dict) -> dict:
        """Create access and refresh token pair"""
        access_token = self.create_access_token(data)
        refresh_token = self.create_refresh_token(data)
        
        return {
            "access_token": access_token,
            "refresh_token": refresh_token,
            "token_type": "bearer"
        }
    
    def refresh_access_token(self, refresh_token: str) -> dict:
        """Refresh access token using refresh token"""
        try:
            # Decode the refresh token
            payload = jwt.decode(refresh_token, self.secret_key, algorithms=[self.algorithm])
            
            # Verify it's a refresh token
            if payload.get("type") != "refresh":
                raise AuthenticationError("Invalid refresh token")
            
            # Create new token data from refresh token payload
            user_data = {
                "sub": payload.get("sub"),
                "email": payload.get("email"),
                "role": payload.get("role"),
                "user_id": payload.get("sub")
            }
            
            # Create new access token
            new_access_token = self.create_access_token(user_data)
            
            return {
                "access_token": new_access_token,
                "refresh_token": refresh_token,  # Return original refresh token
                "token_type": "bearer"
            }
        except JWTError:
            raise AuthenticationError("Invalid refresh token")
    
    def verify_token(self, token: str, expected_type: str = None) -> TokenData:
        """Verify JWT token and return decoded data"""
        if not token:
            raise AuthenticationError("Could not validate credentials")
            
        credentials_exception = AuthenticationError("Could not validate credentials")
        
        try:
            payload = jwt.decode(token, self.secret_key, algorithms=[self.algorithm])
            email: str = payload.get("email")
            user_id: str = payload.get("sub")
            role: str = payload.get("role")
            exp: int = payload.get("exp")
            token_type: str = payload.get("type")
            
            if user_id is None:
                raise credentials_exception
            
            # Validate token type if expected
            if expected_type and token_type != expected_type:
                if expected_type == "access" and token_type == "refresh":
                    raise AuthenticationError("Invalid token type - expected access token")
                elif expected_type == "refresh" and token_type == "access":
                    raise AuthenticationError("Invalid token type - expected refresh token")
                else:
                    raise AuthenticationError(f"Invalid token type - expected {expected_type}")
                
            token_data = TokenData(
                sub=user_id,
                email=email,
                role=role,
                exp=datetime.fromtimestamp(exp) if exp else None,
                type=token_type
            )
        except JWTError:
            raise credentials_exception
            
        return token_data
    
    def verify_password(self, plain_password: str, hashed_password: str) -> bool:
        """Verify password against hash"""
        if not hashed_password or not hashed_password.strip():
            return False
        return self.pwd_context.verify(plain_password, hashed_password)
    
    def get_password_hash(self, password: str) -> str:
        """Generate password hash"""
        if not password:
            # Generate hash for empty string instead of None
            password = ""
        
        try:
            # Try bcrypt first
            return self.pwd_context.hash(password)
        except Exception as e:
            # Fallback to SHA-256 if bcrypt fails and is available
            if bcrypt:
                if "72 bytes" in str(e):
                    # Truncate password for bcrypt compatibility
                    truncated_password = password[:72]
                    return self.pwd_context.hash(truncated_password)
                else:
                    # Try bcrypt with different settings
                    return self.pwd_context.hash(password)
            else:
                # If bcrypt is not available, use SHA-256
                return hashlib.sha256(password.encode()).hexdigest()
    
    def authenticate_user(self, email: str, password: str, user_service=None) -> Dict[str, Any]:
        """Authenticate user with email and password"""
        # Use provided user_service or fall back to attached user_service
        if user_service is None:
            user_service = self.user_service
            if user_service is None:
                raise AuthenticationError("User service not available")
        
        user = user_service.get_user_by_email(email)
        if not user or not self.verify_password(password, user["password_hash"]):
            raise AuthenticationError("Invalid credentials")
        
        # Create access token
        access_token_expires = timedelta(minutes=self.access_token_expire_minutes)
        access_token = self.create_access_token(
            data={"sub": user["user_id"], "email": user["email"], "role": user.get("role", "student")},
            expires_delta=access_token_expires
        )
        
        # Create refresh token
        refresh_token = self.create_refresh_token(
            data={"sub": user["user_id"], "email": user["email"], "role": user.get("role", "student")}
        )
        
        return {
            "access_token": access_token,
            "refresh_token": refresh_token,
            "token_type": "bearer",
            "user": {
                "id": user["user_id"],
                "email": user["email"],
                "role": user.get("role", "student"),
                "name": user.get("name", "")
            }
        }
    
    def login_user(self, login_data: Dict[str, str]) -> Dict[str, Any]:
        """Login user and return tokens"""
        return self.authenticate_user(
            email=login_data["email"],
            password=login_data["password"],
            user_service=self.user_service
        )
    
    def create_user(self, email: str, password: str, name: str, role: str, user_service=None) -> Dict[str, str]:
        """Create a new user"""
        try:
            # Hash the password
            hashed_password = self.get_password_hash(password)
            
            # Use provided user_service or the one in auth_service
            if user_service is None:
                user_service = self.user_service
                if user_service is None:
                    raise AuthenticationError("User service not available")
            
            # Create user using the service method
            user_result = user_service.create_user(
                email=email,
                password=hashed_password,
                name=name,
                role=role
            )
            
            # Extract the actual user_id from the result
            user_id = user_result["user_id"]
            
            return {"user_id": str(user_id)}
        except ValidationError as e:
            raise e  # Re-raise ValidationError to be caught by API endpoint
    
    def refresh_tokens(self, refresh_token: str) -> Dict[str, str]:
        """Refresh access token using refresh token"""
        try:
            # Verify refresh token
            payload = jwt.decode(refresh_token, self.secret_key, algorithms=[self.algorithm])
            
            # Check if it's a refresh token
            if payload.get("type") != "refresh":
                raise AuthenticationError("Invalid refresh token")
            
            # Create new access token with current timestamp to ensure uniqueness
            from datetime import datetime
            access_token = self.create_access_token(
                data={
                    "sub": payload.get("sub"), 
                    "email": payload.get("email"), 
                    "role": payload.get("role"),
                    "iat": int(datetime.utcnow().timestamp())  # Include issued at timestamp
                }
            )
            
            # Create new refresh token with current timestamp to ensure uniqueness
            from datetime import datetime
            new_refresh_token = self.create_refresh_token(
                data={
                    "sub": payload.get("sub"), 
                    "email": payload.get("email"), 
                    "role": payload.get("role"),
                    "iat": int(datetime.utcnow().timestamp())  # Include issued at timestamp
                }
            )
            
            return {
                "access_token": access_token,
                "refresh_token": new_refresh_token,  # Generate new refresh token
                "token_type": "bearer",
                "expires_in": 30 * 60  # 30 minutes in seconds
            }
        except JWTError:
            raise AuthenticationError("Invalid refresh token")
    
    def logout_user(self, token: str) -> bool:
        """
        Logout user (JWT is stateless, so this is mostly for future session management)
        
        - **token**: User access token
        
        Returns success status
        """
        # JWT is stateless, so we can't invalidate tokens directly
        # This method can be enhanced later with token blacklisting
        return True
    
    def change_password(self, user_id: str, current_password: str, new_password: str, user_service) -> bool:
        """Change user password"""
        user = user_service.get_by_id(user_id)
        if not user:
            raise NotFoundError("User not found")
            
        if not self.verify_password(current_password, user["password"]):
            raise ValidationError("Current password is incorrect")
            
        # Hash new password and update
        hashed_password = self.get_password_hash(new_password)
        user_service.update_password(user_id, hashed_password)
        
        return True
    
    def initiate_password_reset(self, email: str, user_service) -> Dict[str, str]:
        """Initiate password reset flow"""
        if user_service is None:
            raise AuthenticationError("User service not available")
            
        try:
            user = user_service.get_user_by_email(email)
            if not user:
                # Don't reveal if email exists or not
                raise ValidationError("If the email exists, a reset link will be sent")
        except NotFoundError:
            # Don't reveal if email exists or not
            raise ValidationError("If the email exists, a reset link will be sent")
        
        # Create reset token with shorter expiration
        reset_token = self.create_access_token(
            data={"sub": user["user_id"], "email": user["email"], "type": "reset"},
            expires_delta=timedelta(hours=1)
        )
        
        # In a real implementation, you would send an email with the reset token
        # For now, just return the token (in production, don't do this!)
        return {
            "message": "Password reset initiated",
            "reset_token": reset_token
        }
    
    def confirm_password_reset(self, reset_token: str, new_password: str, confirm_password: str, user_service) -> bool:
        """Confirm password reset"""
        if new_password != confirm_password:
            raise ValidationError("Passwords do not match")
        
        # Verify reset token
        token_data = self.verify_token(reset_token)
        if token_data.type != "reset":
            raise AuthenticationError("Invalid reset token")
        
        # Update password
        user_service.change_user_password(token_data.sub, new_password)
        
        return True
    
    def validate_password_strength(self, password: str) -> bool:
        """Validate password strength based on requirements"""
        if not password or len(password.strip()) < settings.password_min_length:
            return False
        
        # Check for whitespace
        if any(c.isspace() for c in password):
            return False
        
        has_uppercase = any(c.isupper() for c in password)
        has_lowercase = any(c.islower() for c in password)
        has_number = any(c.isdigit() for c in password)
        has_special = any(not c.isalnum() for c in password)
        
        # Only check requirements that are enabled
        checks = []
        if settings.password_require_uppercase:
            checks.append(has_uppercase)
        if settings.password_require_lowercase:
            checks.append(has_lowercase)
        if settings.password_require_number:
            checks.append(has_number)
        if settings.password_require_special:
            checks.append(has_special)
        
        return all(checks)
    
    def create_session_data(self, user_data: Dict[str, Any]) -> Dict[str, Any]:
        """Create session data from user data"""
        return {
            "user_id": user_data.get("user_id"),
            "email": user_data.get("email"),
            "name": user_data.get("name"),
            "role": user_data.get("role"),
            "session_start": datetime.now(timezone.utc).isoformat()
        }
    
    def validate_session_data(self, session_data: Dict[str, Any]) -> bool:
        """Validate session data"""
        required_fields = ["user_id", "email"]
        return all(field in session_data for field in required_fields)
    
    def sanitize_input(self, input_str: str) -> str:
        """Sanitize input to prevent injection attacks"""
        # Use the enhanced validation version
        from src.core.validation import sanitize_input as validation_sanitize
        return validation_sanitize(input_str)

# Global auth service instance
auth_service = AuthService()