"""
Authentication API Endpoints

This module provides REST API endpoints for authentication operations:
- User registration
- User login
- User logout
- Token refresh
- Password reset
- User authentication validation

Author: Edu-Flow Team
"""

from datetime import datetime, timedelta
from typing import Dict, Any, Optional
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from pydantic import BaseModel, EmailStr, field_validator

from src.core.security import AuthService
from src.core.exceptions import AuthenticationError, ValidationError, NotFoundError
from src.services.user_service import UserService

# Create router
router = APIRouter(prefix="/auth", tags=["auth"])

# Security
security = HTTPBearer()

# Base models
class UserRegistrationRequest(BaseModel):
    """User registration request model"""
    email: EmailStr
    password: str
    name: str
    role: str
    
    @field_validator('password')
    @classmethod
    def validate_password(cls, v):
        if len(v) < 8:
            raise ValueError('Password must be at least 8 characters')
        return v

class UserRegistrationResponse(BaseModel):
    """User registration response model"""
    user_id: str
    email: str
    name: str
    role: str
    message: str

class LoginRequest(BaseModel):
    """Login request model"""
    email: EmailStr
    password: str

class LoginResponse(BaseModel):
    """Login response model"""
    access_token: str
    refresh_token: str
    user_id: str
    token_type: str
    expires_in: int

class TokenRefreshRequest(BaseModel):
    """Token refresh request model"""
    refresh_token: str

class TokenRefreshResponse(BaseModel):
    """Token refresh response model"""
    access_token: str
    expires_in: int

class PasswordResetRequest(BaseModel):
    """Password reset request model"""
    email: EmailStr
    old_password: str
    new_password: str
    
    @field_validator('new_password')
    @classmethod
    def validate_new_password(cls, v):
        if len(v) < 8:
            raise ValueError('New password must be at least 8 characters')
        return v

# Mock services (these should be properly injected in a real app)
user_service = UserService()
auth_service = AuthService()
auth_service.user_service = user_service

# Endpoints

@router.post("/register", response_model=UserRegistrationResponse, status_code=status.HTTP_201_CREATED)
async def register_user(user_request: UserRegistrationRequest):
    """
    User registration endpoint
    
    - **email**: Valid email address
    - **password**: User password (minimum 8 characters)
    - **name**: User display name
    - **role**: User role (student, teacher, admin, staff)
    
    Registers a new user and returns user information
    """
    try:
        user_id = auth_service.create_user(
            email=user_request.email,
            password=user_request.password,
            name=user_request.name,
            role=user_request.role
        )
        
        # Generate tokens
        tokens = auth_service.login_user({
            "email": user_request.email,
            "password": user_request.password
        })
        
        return {
            "message": "User registered successfully",
            "user_id": user_id["user_id"],
            **tokens
        }
    except ValidationError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/login", response_model=LoginResponse)
async def login_user(login_request: LoginRequest):
    """
    User login endpoint
    
    - **email**: Valid email address
    - **password**: User password
    
    Returns JWT tokens for authenticated users
    """
    try:
        result = auth_service.login_user(login_request.dict())
        return LoginResponse(**result)
    except AuthenticationError as e:
        raise HTTPException(status_code=401, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/refresh", response_model=TokenRefreshResponse)
async def refresh_token(request: TokenRefreshRequest):
    """
    Refresh access token endpoint
    
    - **refresh_token**: Valid refresh token
    
    Returns new access token
    """
    try:
        result = auth_service.refresh_token(request.refresh_token)
        return TokenRefreshResponse(**result)
    except AuthenticationError as e:
        raise HTTPException(status_code=401, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/logout")
async def logout_user(credentials: HTTPAuthorizationCredentials = Depends(security)):
    """
    User logout endpoint
    
    - **Authorization**: Bearer access token
    
    Logs out the user and invalidates tokens
    """
    try:
        token = credentials.credentials
        auth_service.logout_user(token)
        return {"message": "Successfully logged out"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/password-reset")
async def reset_password(password_reset: PasswordResetRequest):
    """
    Password reset endpoint
    
    - **email**: Valid email address
    - **old_password**: Current password
    - **new_password**: New password (minimum 8 characters)
    
    Updates user password
    """
    try:
        auth_service.reset_password(
            email=password_reset.email,
            old_password=password_reset.old_password,
            new_password=password_reset.new_password
        )
        return {"message": "Password successfully reset"}
    except AuthenticationError as e:
        raise HTTPException(status_code=401, detail=str(e))
    except ValidationError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/validate", response_model=Dict[str, Any])
async def validate_token(credentials: HTTPAuthorizationCredentials = Depends(security)):
    """
    Token validation endpoint
    
    - **Authorization**: Bearer access token
    
    Returns token validity and user information
    """
    try:
        token = credentials.credentials
        user_data = auth_service.decode_token(token)
        return {
            "valid": True,
            "user_id": user_data["user_id"],
            "email": user_data["email"],
            "role": user_data["role"],
            "exp": user_data.get("exp")
        }
    except Exception as e:
        raise HTTPException(status_code=401, detail=str(e))