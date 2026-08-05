from datetime import datetime, timedelta
from typing import Optional, Dict, Any
from jose import JWTError, jwt
from fastapi import HTTPException, status
from pydantic import BaseModel
import re
import secrets
import hashlib
import hmac
from .exceptions import AuthenticationError, ValidationError, NotFoundError


class TokenData(BaseModel):
    """Token data model for JWT payload"""
    sub: Optional[str] = None
    role: Optional[str] = None
    email: Optional[str] = None


class AuthService:
    """Authentication service for JWT-based authentication"""
    
    def __init__(self, secret_key: str = None, algorithm: str = "HS256", user_service = None):
        self.secret_key = secret_key or secrets.token_urlsafe(32)
        self.algorithm = algorithm
        self.access_token_expire_minutes = 30
        self.refresh_token_expire_days = 7
        self.user_service = user_service
    
    def verify_password(self, plain_password: str, hashed_password: str) -> bool:
        """Verify password against hash"""
        # Simple hash verification for testing
        return hmac.compare_digest(
            hashlib.sha256((plain_password + "salt").encode()).hexdigest(),
            hashed_password
        )
    
    def get_password_hash(self, password: str) -> str:
        """Generate password hash"""
        # Simple hash generation for testing
        return hashlib.sha256((password + "salt").encode()).hexdigest()
    
    def validate_password_strength(self, password: str) -> bool:
        """Validate password strength requirements"""
        if len(password) < 8:
            return False
        
        # Check for at least one uppercase letter
        if not re.search(r'[A-Z]', password):
            return False
        
        # Check for at least one lowercase letter
        if not re.search(r'[a-z]', password):
            return False
        
        # Check for at least one digit
        if not re.search(r'\d', password):
            return False
        
        # Check for at least one special character
        if not re.search(r'[!@#$%^&*(),.?":{}|<>]', password):
            return False
        
        return True
    
    def validate_email_format(self, email: str) -> bool:
        """Validate email format"""
        email_pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
        return bool(re.match(email_pattern, email))
    
    def create_access_token(self, data: dict, expires_delta: Optional[timedelta] = None) -> str:
        """Create JWT access token"""
        to_encode = data.copy()
        if expires_delta:
            expire = datetime.utcnow() + expires_delta
        else:
            expire = datetime.utcnow() + timedelta(minutes=self.access_token_expire_minutes)
        
        to_encode.update({"exp": expire})
        encoded_jwt = jwt.encode(to_encode, self.secret_key, algorithm=self.algorithm)
        return encoded_jwt
    
    def create_refresh_token(self, data: dict) -> str:
        """Create JWT refresh token"""
        to_encode = data.copy()
        expire = datetime.utcnow() + timedelta(days=self.refresh_token_expire_days)
        to_encode.update({"exp": expire, "type": "refresh"})
        encoded_jwt = jwt.encode(to_encode, self.secret_key, algorithm=self.algorithm)
        return encoded_jwt
    
    def verify_token(self, token: str) -> TokenData:
        """Verify JWT token and return token data"""
        credentials_exception = HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Could not validate credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )
        try:
            payload = jwt.decode(token, self.secret_key, algorithms=[self.algorithm])
            sub: str = payload.get("sub")
            role: str = payload.get("role")
            email: str = payload.get("email")
            if sub is None or role is None:
                raise credentials_exception
            return TokenData(sub=sub, role=role, email=email)
        except JWTError:
            raise credentials_exception
    
    def register_user(self, user_data: Dict[str, Any]) -> str:
        """Register a new user"""
        # Use the user service to register the user
        user = self.user_service.create_user(
            email=user_data["email"],
            password=user_data["password"],
            name=user_data["name"],
            role=user_data["role"]
        )
        return user["user_id"]
    
    def decode_token(self, token: str) -> TokenData:
        """Decode JWT token and return token data"""
        return self.verify_token(token)
    
    def login_user(self, login_data: Dict[str, Any]) -> Dict[str, str]:
        """Authenticate user and return tokens"""
        if not login_data.get("email"):
            raise AuthenticationError("Email is required", status_code=400)
        
        if not login_data.get("password"):
            raise AuthenticationError("Password is required", status_code=400)
        
        # Get user from user service
        try:
            user = self.user_service.get_user_by_email(login_data["email"])
        except NotFoundError:
            raise AuthenticationError("Invalid credentials", status_code=401)
        
        # Verify password
        if not self.verify_password(login_data["password"], user["password_hash"]):
            raise AuthenticationError("Invalid credentials", status_code=401)
        
        # Check if user is active
        if not user["is_active"]:
            raise AuthenticationError("Account is disabled", status_code=401)
        
        # Update last login
        self.user_service.update_user(user["user_id"], last_login=datetime.now())
        
        # Create tokens
        access_token = self.create_access_token({
            "sub": user["user_id"],
            "role": user["role"],
            "email": user["email"]
        })
        
        refresh_token = self.create_refresh_token({
            "sub": user["user_id"],
            "role": user["role"],
            "email": user["email"]
        })
        
        return {
            "access_token": access_token,
            "refresh_token": refresh_token,
            "user_id": user["user_id"],
            "token_type": "bearer"
        }
    
    def logout_user(self, token: str) -> None:
        """Logout user by adding token to blacklist"""
        # In a real implementation, you would add the token to a blacklist
        # For now, we'll just pass
        pass
    
    def refresh_tokens(self, refresh_token: str) -> Dict[str, str]:
        """Refresh access token using refresh token"""
        try:
            # Verify refresh token
            payload = jwt.decode(refresh_token, self.secret_key, algorithms=[self.algorithm])
            
            # Check if it's a refresh token
            if payload.get("type") != "refresh":
                raise AuthenticationError("Invalid refresh token", status_code=401)
            
            # Get user ID from token
            user_id = payload.get("sub")
            if not user_id:
                raise AuthenticationError("Invalid refresh token", status_code=401)
            
            # Get user from user service
            user = self.user_service.get_user(user_id)
            
            # Create new access token
            access_token = self.create_access_token({
                "sub": user["user_id"],
                "role": user["role"],
                "email": user["email"]
            })
            
            return {
                "access_token": access_token,
                "token_type": "bearer"
            }
        except JWTError:
            raise AuthenticationError("Invalid refresh token", status_code=401)
    
    def initiate_password_reset(self, email: str) -> Dict[str, str]:
        """Initiate password reset process"""
        try:
            user = self.user_service.get_user_by_email(email)
            
            # Create reset token
            reset_token = self.create_access_token({
                "sub": f"reset_{user['user_id']}",
                "email": user["email"],
                "type": "password_reset"
            }, expires_delta=timedelta(hours=1))
            
            # In a real implementation, you would send an email with the reset token
            # For now, we'll just return the token
            return {
                "reset_token": reset_token,
                "message": "Password reset token generated"
            }
        except NotFoundError:
            raise AuthenticationError("Email not found", status_code=404)
    
    def confirm_password_reset(self, reset_token: str, new_password: str, confirm_password: str) -> Dict[str, str]:
        """Confirm password reset with new password"""
        if new_password != confirm_password:
            raise ValidationError("Passwords do not match")
        
        try:
            # Verify reset token
            payload = jwt.decode(reset_token, self.secret_key, algorithms=[self.algorithm])
            
            # Check if it's a password reset token
            if payload.get("type") != "password_reset":
                raise AuthenticationError("Invalid reset token", status_code=401)
            
            # Extract user ID from token
            reset_id = payload.get("sub")
            if not reset_id.startswith("reset_"):
                raise AuthenticationError("Invalid reset token", status_code=401)
            
            user_id = reset_id[6:]  # Remove "reset_" prefix
            
            # Update user password
            self.user_service.change_user_password(user_id, new_password)
            
            return {
                "message": "Password reset successful"
            }
        except JWTError:
            raise AuthenticationError("Invalid reset token", status_code=401)
        
        except ValidationError:
            raise
        # For now, we'll simulate a successful login
        user_id = "user_123"
        user_role = "teacher"  # In real implementation, get from database
        
        # Create tokens
        access_token = self.create_access_token({
            "sub": user_id,
            "role": user_role,
            "email": login_data["email"]
        })
        
        refresh_token = self.create_refresh_token({
            "sub": user_id,
            "role": user_role,
            "email": login_data["email"]
        })
        
        return {
            "access_token": access_token,
            "refresh_token": refresh_token,
            "user_id": user_id,
            "token_type": "bearer"
        }
    
    def logout_user(self, token: str) -> bool:
        """Logout user (invalidate token)"""
        # In real implementation, you would add token to blacklist
        # For now, we'll just return success
        return True
    
    def refresh_tokens(self, refresh_token: str) -> Dict[str, str]:
        """Refresh access token using refresh token"""
        try:
            # Verify refresh token
            payload = jwt.decode(refresh_token, self.secret_key, algorithms=[self.algorithm])
            
            # Check if it's a refresh token
            if payload.get("type") != "refresh":
                raise AuthenticationError("Invalid refresh token", status_code=401)
            
            # Create new access token
            access_token = self.create_access_token({
                "sub": payload.get("sub"),
                "role": payload.get("role"),
                "email": payload.get("email")
            })
            
            return {
                "access_token": access_token,
                "token_type": "bearer"
            }
        except JWTError:
            raise AuthenticationError("Invalid refresh token", status_code=401)
    
    def initiate_password_reset(self, email: str) -> Dict[str, str]:
        """Initiate password reset flow"""
        if not email:
            raise ValidationError("Email is required")
        
        if not self.validate_email_format(email):
            raise ValidationError("Invalid email format")
        
        # Generate reset token
        reset_token = self.create_access_token({
            "sub": f"reset_{secrets.token_hex(8)}",
            "email": email,
            "type": "password_reset"
        }, expires_delta=timedelta(hours=1))
        
        # In real implementation, you would send reset email
        # For now, we'll just return the token
        return {
            "reset_token": reset_token,
            "message": "Password reset token generated"
        }
    
    def confirm_password_reset(self, reset_token: str, new_password: str, confirm_password: str) -> Dict[str, str]:
        """Confirm password reset with token"""
        if not reset_token:
            raise ValidationError("Reset token is required")
        
        if not new_password:
            raise ValidationError("New password is required")
        
        if new_password != confirm_password:
            raise ValidationError("Passwords do not match")
        
        if not self.validate_password_strength(new_password):
            raise ValidationError("Password does not meet strength requirements")
        
        try:
            # Verify reset token
            payload = jwt.decode(reset_token, self.secret_key, algorithms=[self.algorithm])
            
            if payload.get("type") != "password_reset":
                raise AuthenticationError("Invalid reset token", status_code=401)
            
            # In real implementation, you would update the user's password
            # For now, we'll just return success
            return {
                "message": "Password reset successful"
            }
        except JWTError:
            raise AuthenticationError("Invalid or expired reset token", status_code=401)