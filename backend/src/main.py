from fastapi import FastAPI, Request, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi.encoders import jsonable_encoder
import time
from typing import Dict, Any
from .core.exceptions import AuthenticationError, ValidationError, NotFoundError, ForbiddenError

# Initialize FastAPI app
app = FastAPI(
    title="Edu-Flow API",
    description="Authentication and User Management Service for Edu-Flow Institution Accreditation System",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc"
)

# Initialize services
from src.services.user_service import UserService
from src.api.v1.endpoints.users import router as users_router
from src.core.security import AuthService

user_service = UserService()
auth_service = AuthService()
auth_service.user_service = user_service  # Set the user service after creation

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure this properly in production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Request middleware for logging
@app.middleware("http")
async def log_requests(request: Request, call_next):
    start_time = time.time()
    
    # Log request
    print(f"Request: {request.method} {request.url}")
    
    response = await call_next(request)
    
    # Log response
    process_time = time.time() - start_time
    print(f"Response: {response.status_code} - {process_time:.4f}s")
    
    return response

# Global exception handlers
@app.exception_handler(AuthenticationError)
async def auth_exception_handler(request: Request, exc: AuthenticationError):
    return JSONResponse(
        status_code=exc.status_code,
        content={"error": exc.detail},
    )

@app.exception_handler(ValidationError)
async def validation_exception_handler(request: Request, exc: ValidationError):
    return JSONResponse(
        status_code=exc.status_code,
        content={"error": exc.detail},
    )

@app.exception_handler(NotFoundError)
async def not_found_exception_handler(request: Request, exc: NotFoundError):
    return JSONResponse(
        status_code=exc.status_code,
        content={"error": exc.detail},
    )

@app.exception_handler(ForbiddenError)
async def forbidden_exception_handler(request: Request, exc: ForbiddenError):
    return JSONResponse(
        status_code=exc.status_code,
        content={"error": exc.detail},
    )

@app.exception_handler(HTTPException)
async def http_exception_handler(request: Request, exc: HTTPException):
    return JSONResponse(
        status_code=exc.status_code,
        content={"error": exc.detail},
    )

@app.exception_handler(Exception)
async def general_exception_handler(request: Request, exc: Exception):
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={"error": "Internal server error"},
    )

# Health check endpoint
@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {"status": "healthy", "message": "Authentication service is running"}

# Root endpoint
@app.get("/")
async def root():
    """Root endpoint"""
    return {
        "message": "Edu-Flow Authentication API",
        "version": "1.0.0",
        "docs": "/docs",
        "health": "/health"
    }

# Authentication endpoints
@app.post("/api/v1/auth/register")
async def register_user(user_data: Dict[str, Any]):
    """
    Register a new user
    
    Args:
        user_data: Dictionary containing user information
            - email (str): User email address
            - password (str): User password
            - name (str): User name
            - role (str): User role (admin, teacher, student)
    
    Returns:
        Dictionary with user ID and tokens
    """
    try:
        user_id = auth_service.register_user(user_data)
        
        # Generate tokens
        tokens = auth_service.login_user({
            "email": user_data["email"],
            "password": user_data["password"]
        })
        
        return {
            "message": "User registered successfully",
            "user_id": user_id,
            **tokens
        }
    except (AuthenticationError, ValidationError) as e:
        raise e
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/v1/auth/login")
async def login_user(login_data: Dict[str, Any]):
    """
    User login endpoint
    
    Args:
        login_data: Dictionary containing login credentials
            - email (str): User email address
            - password (str): User password
    
    Returns:
        Dictionary with access and refresh tokens
    """
    try:
        tokens = auth_service.login_user(login_data)
        return {
            "message": "Login successful",
            **tokens
        }
    except AuthenticationError as e:
        raise e
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/v1/auth/logout")
async def logout_user(request: Request):
    """
    User logout endpoint
    
    Args:
        request: HTTP request containing Authorization header with Bearer token
    
    Returns:
        Dictionary with logout confirmation
    """
    # Get token from Authorization header
    auth_header = request.headers.get("authorization")
    if not auth_header:
        raise AuthenticationError("Authorization header missing")
    
    try:
        token = auth_header.split(" ")[1]
        auth_service.logout_user(token)
        
        return {"message": "Logout successful"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/v1/auth/refresh")
async def refresh_token(refresh_data: Dict[str, Any]):
    """
    Refresh access token endpoint
    
    Args:
        refresh_data: Dictionary containing refresh token
            - refresh_token (str): Refresh token
    
    Returns:
        Dictionary with new access token
    """
    if not refresh_data.get("refresh_token"):
        raise ValidationError("Refresh token is required")
    
    try:
        new_tokens = auth_service.refresh_tokens(refresh_data["refresh_token"])
        return {
            "message": "Token refreshed successfully",
            **new_tokens
        }
    except AuthenticationError as e:
        raise e
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/v1/auth/reset-password")
async def initiate_password_reset(reset_data: Dict[str, Any]):
    """
    Initiate password reset endpoint
    
    Args:
        reset_data: Dictionary containing email
            - email (str): User email address
    
    Returns:
        Dictionary with reset token
    """
    if not reset_data.get("email"):
        raise ValidationError("Email is required")
    
    try:
        result = auth_service.initiate_password_reset(reset_data["email"])
        return result
    except (AuthenticationError, ValidationError) as e:
        raise e
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/v1/auth/confirm-reset")
async def confirm_password_reset(reset_data: Dict[str, Any]):
    """
    Confirm password reset endpoint
    
    Args:
        reset_data: Dictionary containing reset token and new password
            - reset_token (str): Password reset token
            - new_password (str): New password
            - confirm_password (str): Confirm new password
    
    Returns:
        Dictionary with reset confirmation
    """
    try:
        result = auth_service.confirm_password_reset(
            reset_data["reset_token"],
            reset_data["new_password"],
            reset_data["confirm_password"]
        )
        return result
    except (AuthenticationError, ValidationError) as e:
        raise e
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# Protected endpoints requiring authentication
@app.get("/api/v1/users/me")
async def get_current_user(request: Request):
    """
    Get current user information
    
    Args:
        request: HTTP request containing Authorization header with Bearer token
    
    Returns:
        Dictionary with current user information
    """
    auth_header = request.headers.get("authorization")
    if not auth_header:
        raise AuthenticationError("Authorization header missing")
    
    try:
        token = auth_header.split(" ")[1]
        token_data = auth_service.verify_token(token)
        
        return {
            "user_id": token_data.sub,
            "email": token_data.email,
            "role": token_data.role,
            "message": "User information retrieved successfully"
        }
    except AuthenticationError as e:
        raise e
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/v1/teachers/me")
async def get_teacher_profile(request: Request):
    """
    Get teacher profile information
    
    Args:
        request: HTTP request containing Authorization header with Bearer token
    
    Returns:
        Dictionary with teacher profile information
    """
    auth_header = request.headers.get("authorization")
    if not auth_header:
        raise AuthenticationError("Authorization header missing")
    
    try:
        token = auth_header.split(" ")[1]
        token_data = auth_service.verify_token(token)
        
        if token_data.role != "teacher":
            raise ForbiddenError("Access denied. Teacher role required")
        
        return {
            "teacher_id": token_data.sub,
            "email": token_data.email,
            "role": token_data.role,
            "message": "Teacher profile retrieved successfully"
        }
    except (AuthenticationError, ForbiddenError) as e:
        raise e
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/v1/admin/dashboard")
async def get_admin_dashboard(request: Request):
    """
    Get admin dashboard information
    
    Args:
        request: HTTP request containing Authorization header with Bearer token
    
    Returns:
        Dictionary with admin dashboard information
    """
    auth_header = request.headers.get("authorization")
    if not auth_header:
        raise AuthenticationError("Authorization header missing")
    
    try:
        token = auth_header.split(" ")[1]
        token_data = auth_service.verify_token(token)
        
        if token_data.role != "admin":
            raise ForbiddenError("Access denied. Admin role required")
        
        return {
            "admin_id": token_data.sub,
            "email": token_data.email,
            "role": token_data.role,
            "message": "Admin dashboard retrieved successfully"
        }
    except (AuthenticationError, ForbiddenError) as e:
        raise e
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# Endpoint to get password strength requirements
@app.get("/api/v1/auth/password-requirements")
async def get_password_requirements():
    """
    Get password strength requirements
    
    Returns:
        Dictionary with password requirements
    """
    return {
        "requirements": {
            "min_length": 8,
            "uppercase_required": True,
            "lowercase_required": True,
            "digit_required": True,
            "special_character_required": True,
            "allowed_special_characters": "!@#$%^&*(),.?\":{}|<>"
        },
        "message": "Password requirements retrieved successfully"
    }

# Endpoint to get available user roles
@app.get("/api/v1/auth/roles")
async def get_available_roles():
    """
    Get available user roles
    
    Returns:
        Dictionary with available roles
    """
    return {
        "roles": ["admin", "teacher", "student", "staff"],
        "message": "Available roles retrieved successfully"
    }

# Include user management endpoints
app.include_router(users_router, prefix="/api/v1")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)