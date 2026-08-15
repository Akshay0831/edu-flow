"""Enhanced authentication endpoints with multi-provider support."""

from datetime import timedelta, datetime
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

router = APIRouter(prefix="/auth/enhanced", tags=["enhanced-authentication"])

# Security scheme for authentication
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
    provider: str

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
    provider: str

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

class TokenResponse(BaseModel):
    """Token response model"""
    access_token: str
    refresh_token: str
    token_type: str
    expires_in: int

# Endpoints

@router.post("/register", response_model=UserRegistrationResponse, status_code=status.HTTP_201_CREATED)
async def register_user(
    user_request: UserRegistrationRequest,
    provider: str = Query(default="jwt", description="Authentication provider")
):
    """
    User registration endpoint with provider support
    
    - **email**: Valid email address
    - **password**: User password (minimum 8 characters)
    - **name**: User display name
    - **role**: User role (student, teacher, admin, staff)
    - **provider**: Authentication provider (jwt, firebase, custom)
    
    Registers a new user and returns user information
    """
    try:
        # Create user using the enhanced auth service with provider support
        result = await auth_gateway.create_user(
            user_data={
                "email": user_request.email,
                "password": user_request.password,
                "name": user_request.name,
                "role": user_request.role
            },
            provider=provider
        )
        
        # Generate tokens for the newly created user
        auth_result = await auth_gateway.authenticate(
            credentials={
                "email": user_request.email,
                "password": user_request.password
            },
            provider=provider
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
async def login_user(
    login_request: LoginRequest,
    provider: str = Query(default="jwt", description="Authentication provider")
):
    """
    User login endpoint with provider support
    
    - **email**: Valid email address
    - **password**: User password
    - **provider**: Authentication provider (jwt, firebase, custom)
    
    Returns JWT tokens for authenticated users
    """
    try:
        # Authenticate using the specified provider
        auth_result = await auth_gateway.authenticate(
            credentials={
                "email": login_request.email,
                "password": login_request.password
            },
            provider=provider
        )
        
        # Generate tokens for the authenticated user
        token_pair = {
            "access_token": "",
            "refresh_token": ""
        }
        
        # Create JWT tokens for API access (regardless of auth provider)
        from src.core.security import AuthService
        auth_service = AuthService()
        token_pair = auth_service.create_token_pair({
            "user_id": auth_result.get("user_id", ""),
            "email": auth_result.get("email", ""),
            "name": auth_result.get("name", ""),
            "role": auth_result.get("role", ""),
            "provider": auth_result.get("provider", provider)
        })
        
        return ResponseFormatter.success({
            "access_token": token_pair["access_token"],
            "refresh_token": token_pair["refresh_token"],
            "token_type": "bearer",
            "user": {
                "id": auth_result.get("user_id", ""),
                "email": auth_result.get("email", ""),
                "name": auth_result.get("name", ""),
                "role": auth_result.get("role", "")
            },
            "expires_in": 30 * 60  # 30 minutes in seconds
        }, "User login successful")
    except AuthenticationError as e:
        return ResponseFormatter.unauthorized(str(e))
    except ValidationError as e:
        return ResponseFormatter.bad_request(str(e))
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
        from src.core.security import AuthService
        auth_service = AuthService()
        result = auth_service.refresh_tokens(request.refresh_token)
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
        from src.core.security import AuthService
        auth_service = AuthService()
        auth_service.logout_user(token)
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
        from src.services.user_service import UserService
        user_service = UserService()
        try:
            user = user_service.get_user_by_email(password_reset.email)
        except NotFoundError:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found"
            )
        
        from src.core.security import AuthService
        auth_service = AuthService()
        auth_service.change_password(
            user_id=user['id'],
            current_password=password_reset.old_password,
            new_password=password_reset.new_password,
            user_service=user_service
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
        from src.core.security import AuthService
        auth_service = AuthService()
        result = auth_service.initiate_password_reset(
            email=request["email"],
            user_service=UserService()
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

@router.get("/providers")
async def list_providers():
    """
    List available authentication providers
    
    Returns information about configured authentication providers
    """
    return ResponseFormatter.success({
        "providers": [
            {
                "name": "jwt",
                "display_name": "JWT Authentication",
                "description": "Standard JSON Web Token authentication",
                "enabled": True,
                "required": True
            },
            {
                "name": "firebase",
                "display_name": "Firebase Authentication",
                "description": "Google Firebase authentication (optional)",
                "enabled": False,  # Will be determined by configuration
                "required": False
            },
            {
                "name": "custom",
                "display_name": "Custom Authentication",
                "description": "Organization-specific authentication",
                "enabled": True,
                "required": False
            }
        ],
        "default_provider": "jwt"
    }, "Providers retrieved successfully")

@router.get("/providers/{provider}/health")
async def check_provider_health(provider: str):
    """
    Check if authentication provider is healthy
    
    - **provider**: Authentication provider to check (jwt, firebase, custom)
    """
    try:
        auth_provider = auth_gateway.get_provider(provider)
        
        # Provider-specific health check
        if provider == AuthProvider.FIREBASE:
            # For Firebase, we'd check if it's configured
            health_status = {"status": "healthy" if auth_provider.configured else "not_configured", "checks": ["configuration"]}
        else:
            health_status = {"status": "healthy", "checks": ["basic"]}
            
        return ResponseFormatter.success({
            "provider": provider,
            "status": health_status["status"],
            "checks": health_status["checks"],
            "timestamp": datetime.now()
        }, "Provider health checked")
    except Exception as e:
        return ResponseFormatter.error({
            "provider": provider,
            "status": "unhealthy",
            "error": str(e),
            "timestamp": datetime.now()
        }, "Provider health check failed")

# Export the router
__all__ = ["router"]
