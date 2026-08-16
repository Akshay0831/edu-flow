"""Authentication endpoints including login, logout, and JWT management."""

from datetime import timedelta
from typing import Dict, Any, Optional
from fastapi import APIRouter, Depends, HTTPException, status, Query
from fastapi.security import HTTPBearer, OAuth2PasswordRequestForm, HTTPAuthorizationCredentials
from pydantic import BaseModel, EmailStr, field_validator
from src.core.security import AuthService, TokenData
from src.core.auth_gateway import AuthProvider, auth_gateway
from src.core.exceptions import AuthenticationError, ValidationError, NotFoundError
from src.core.response_handler import ResponseFormatter
from src.config.settings import settings
from src.services.user_service import UserService

router = APIRouter(prefix="/auth", tags=["authentication"])

# Security scheme for authentication
security = HTTPBearer()

# User service is attached to global auth service in main.py

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

# Response models
class UserRegistrationResponse(BaseModel):
    """User registration response model"""
    user_id: str
    email: str
    name: str
    role: str
    message: str
    access_token: str
    refresh_token: str

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
    refresh_token: str
    token_type: str
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

# Additional request/response models
class PasswordChangeRequest(BaseModel):
    """Password change request model"""
    current_password: str
    new_password: str
    
    @field_validator('new_password')
    @classmethod
    def validate_new_password(cls, v):
        if len(v) < 8:
            raise ValueError('New password must be at least 8 characters')
        return v

class PasswordResetConfirmRequest(BaseModel):
    """Password reset confirmation request model"""
    email: EmailStr
    new_password: str
    
    @field_validator('new_password')
    @classmethod
    def validate_new_password(cls, v):
        if len(v) < 8:
            raise ValueError('New password must be at least 8 characters')
        return v

class TokenResponse(BaseModel):
    """Token response model"""
    access_token: str
    refresh_token: str
    token_type: str
    expires_in: int

# Import the global auth service
from src.core.security import auth_service as global_auth_service

# Endpoints

@router.post("/register", response_model=UserRegistrationResponse, status_code=status.HTTP_201_CREATED)
async def register_user(
    user_request: UserRegistrationRequest,
    provider: str = Query(default="jwt", description="Authentication provider")
):
    """
    User registration endpoint
    
    - **email**: Valid email address
    - **password**: User password (minimum 8 characters)
    - **name**: User display name
    - **role**: User role (student, teacher, admin, staff)
    - **provider**: Authentication provider (jwt, firebase, custom)
    
    Registers a new user and returns user information
    """
    try:
        # Create user using the enhanced auth service with provider support
        result = await global_auth_service.create_user(
            user_data={
                "email": user_request.email,
                "password": user_request.password,
                "name": user_request.name,
                "role": user_request.role
            },
            provider=provider
        )
        
        # Generate tokens for the newly created user
        auth_result = await global_auth_service.authenticate_user(
            email=user_request.email,
            password=user_request.password
        )
        
        return ResponseFormatter.created({
            "user_id": result.get("user_id", ""),
            "email": user_request.email,
            "name": user_request.name,
            "role": user_request.role,
            "access_token": auth_result.get("access_token", ""),
            "refresh_token": auth_result.get("refresh_token", ""),
            "provider": auth_result.get("provider", provider)
        }, "User registered successfully")
    except ValidationError as e:
        return ResponseFormatter.bad_request(e.message, e.details)
    except AuthenticationError as e:
        return ResponseFormatter.unauthorized(e.message, e.details)
    except Exception as e:
        return ResponseFormatter.error(str(e))

@router.post("/login", response_model=LoginResponse)
async def login_user(login_request: LoginRequest):
    """
    User login endpoint
    
    - **email**: Valid email address
    - **password**: User password
    
    Returns JWT tokens for authenticated users
    """
    try:
        print(f"DEBUG: Login request for {login_request.email}")
        result = await global_auth_service.login_user(login_request.model_dump())
        print(f"DEBUG: Login result: {result}")
        # Extract user info from nested structure to match LoginResponse expectations
        user_info = result.get("user", {})
        login_response = LoginResponse(
            access_token=result["access_token"],
            refresh_token=result["refresh_token"],
            user_id=user_info.get("id", ""),
            token_type=result["token_type"],
            expires_in=30 * 60  # 30 minutes in seconds
        )
        return ResponseFormatter.success({
            "access_token": login_response.access_token,
            "refresh_token": login_response.refresh_token,
            "token_type": login_response.token_type,
            "user": {
                "id": login_response.user_id,
                "email": user_info.get("email", ""),
                "name": user_info.get("name", ""),
                "role": user_info.get("role", "")
            },
            "expires_in": login_response.expires_in
        }, "User login successful")
    except AuthenticationError as e:
        return ResponseFormatter.unauthorized(str(e))
    except Exception as e:
        return ResponseFormatter.error(str(e))

@router.post("/refresh", response_model=TokenRefreshResponse)
async def refresh_token(request: TokenRefreshRequest):
    """
    Refresh access token endpoint
    
    - **refresh_token**: Valid refresh token
    
    Returns new access token
    """
    try:
        result = global_auth_service.refresh_tokens(request.refresh_token)
        return ResponseFormatter.success({
            "access_token": result["access_token"],
            "refresh_token": result["refresh_token"],
            "token_type": result["token_type"],
            "expires_in": result["expires_in"]
        }, "Token refreshed successfully")
    except AuthenticationError as e:
        return ResponseFormatter.unauthorized(str(e))
    except Exception as e:
        return ResponseFormatter.error(str(e))

@router.post("/logout")
async def logout_user(credentials: HTTPAuthorizationCredentials = Depends(security)):
    """
    User logout endpoint
    
    - **Authorization**: Bearer access token
    
    Logs out the user and invalidates tokens
    """
    try:
        token = credentials.credentials
        global_auth_service.logout_user(token)
        return ResponseFormatter.success(None, "Successfully logged out")
    except Exception as e:
        return ResponseFormatter.error(str(e))

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
        # Get user by email first
        try:
            user = global_auth_service.user_service.get_user_by_email(password_reset.email)
        except NotFoundError:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found"
            )
        
        global_auth_service.change_password(
            user_id=user['id'],
            current_password=password_reset.old_password,
            new_password=password_reset.new_password,
            user_service=global_auth_service.user_service
        )
        return ResponseFormatter.success(None, "Password successfully reset")
    except AuthenticationError as e:
        return ResponseFormatter.unauthorized(str(e))
    except ValidationError as e:
        return ResponseFormatter.bad_request(str(e))
    except Exception as e:
        return ResponseFormatter.error(str(e))

@router.post("/forgot-password")
async def forgot_password(request: dict):
    """
    Forgot password endpoint
    
    - **email**: Valid email address
    
    Initiates password reset flow and returns reset token
    """
    try:
        result = global_auth_service.initiate_password_reset(
            email=request["email"],
            user_service=global_auth_service.user_service
        )
        return ResponseFormatter.success({
            "reset_token": result["reset_token"]
        }, "Password reset initiated")
    except AuthenticationError as e:
        return ResponseFormatter.unauthorized(str(e))
    except ValidationError as e:
        return ResponseFormatter.bad_request(str(e))
    except Exception as e:
        return ResponseFormatter.error(str(e))

@router.post("/confirm-password-reset")
async def confirm_password_reset(request: dict):
    """
    Confirm password reset endpoint
    
    - **reset_token**: Valid reset token
    - **new_password**: New password (minimum 8 characters)
    - **confirm_password**: Confirm new password
    
    Confirms password reset with token
    """
    try:
        success = global_auth_service.confirm_password_reset(
            reset_token=request["reset_token"],
            new_password=request["new_password"],
            confirm_password=request["confirm_password"],
            user_service=global_auth_service.user_service
        )
        return ResponseFormatter.success(None, "Password reset successfully")
    except AuthenticationError as e:
        return ResponseFormatter.unauthorized(str(e))
    except ValidationError as e:
        return ResponseFormatter.bad_request(str(e))
    except Exception as e:
        return ResponseFormatter.error(str(e))

@router.get("/validate", response_model=Dict[str, Any])
async def validate_token(credentials: HTTPAuthorizationCredentials = Depends(security)):
    """
    Token validation endpoint
    
    - **Authorization**: Bearer access token
    
    Returns token validity and user information
    """
    try:
        token = credentials.credentials
        user_data = global_auth_service.decode_token(token)
        return {
            "valid": True,
            "user_id": user_data["user_id"],
            "email": user_data["email"],
            "role": user_data["role"],
            "exp": user_data.get("exp")
        }
    except Exception as e:
        raise HTTPException(status_code=401, detail=str(e))