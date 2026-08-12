"""
FastAPI Application for Edu-Flow Backend

This module initializes the FastAPI application with all necessary components:
- API endpoints
- Database connections
- Security middleware
- CORS configuration
- Error handling
- Health checks

Author: Edu-Flow Team
"""

import uvicorn
import uuid
from fastapi import FastAPI, Request, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.gzip import GZipMiddleware
from fastapi.responses import JSONResponse
import time
from typing import Optional
from contextlib import asynccontextmanager

from src.core.exceptions import (
    BaseError, ValidationError, NotFoundError, AuthenticationError,
    AuthorizationError, ForbiddenError, ConflictError, DatabaseError,
    ExternalServiceError, RateLimitError, ConfigurationError
)
from src.core.security import auth_service
from src.config.settings import settings
from src.services.database_service import database_service, initialize_database
from src.api.v1.endpoints.auth import router as auth_router
from src.services.user_service import UserService

# Application lifespan
@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan context manager"""
    # Startup
    app.state.startup_time = time.time()
    try:
        # Connect to database and initialize
        db = await database_service.connect()
        app.state.database = db
        success = await initialize_database()
        if success:
            print("✅ Database connected and initialized successfully")
        else:
            print("❌ Database initialization failed")
    except Exception as e:
        print(f"❌ Database startup error: {e}")
    
    yield
    
    # Shutdown
    app.state.shutdown_time = time.time()
    try:
        await database_service.disconnect()
        print("✅ Database disconnected successfully")
    except Exception as e:
        print(f"❌ Database shutdown error: {e}")

# Create FastAPI app with lifespan
app = FastAPI(
    title="Edu-Flow API",
    description="Education Management System API",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
    lifespan=lifespan
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
    expose_headers=["*"],
)

# Add GZip compression middleware
app.add_middleware(GZipMiddleware, minimum_size=1000)

# Add security headers middleware
from starlette.middleware.base import BaseHTTPMiddleware
from fastapi import Response

class SecurityHeadersMiddleware(BaseHTTPMiddleware):
    """Middleware to add security headers to all responses"""
    
    async def dispatch(self, request: Request, call_next):
        response = await call_next(request)
        # Add security headers
        response.headers["x-content-type-options"] = "nosniff"
        response.headers["x-frame-options"] = "DENY"
        response.headers["x-xss-protection"] = "1; mode=block"
        response.headers["strict-transport-security"] = "max-age=31536000; includeSubDomains"
        response.headers["content-security-policy"] = "default-src 'self'"
        return response

app.add_middleware(SecurityHeadersMiddleware)

# Import response handler
from src.core.response_handler import ResponseFormatter

# Custom exception handlers using standardized response format
@app.exception_handler(BaseError)
async def base_exception_handler(request: Request, exc: BaseError):
    """Custom HTTP exception handler"""
    request_id = getattr(request.state, 'request_id', None)
    return ResponseFormatter.error(
        message=exc.message,
        error_code=exc.error_code,
        status_code=exc.status_code,
        details=exc.details,
        request_id=request_id
    )

@app.exception_handler(AuthenticationError)
async def auth_exception_handler(request: Request, exc: AuthenticationError):
    """Authentication error handler"""
    return ResponseFormatter.unauthorized(
        message=exc.message,
        details=exc.details
    )

@app.exception_handler(AuthorizationError)
async def authorization_exception_handler(request: Request, exc: AuthorizationError):
    """Authorization error handler"""
    return ResponseFormatter.forbidden(
        message=exc.message,
        details=exc.details
    )

@app.exception_handler(ValidationError)
async def validation_exception_handler(request: Request, exc: ValidationError):
    """Validation error handler"""
    return ResponseFormatter.bad_request(
        message=exc.message,
        details=exc.details
    )

@app.exception_handler(NotFoundError)
async def not_found_exception_handler(request: Request, exc: NotFoundError):
    """Not found error handler"""
    return ResponseFormatter.not_found(
        message=exc.message,
        details=exc.details
    )

@app.exception_handler(ForbiddenError)
async def forbidden_exception_handler(request: Request, exc: ForbiddenError):
    """Forbidden error handler"""
    return ResponseFormatter.forbidden(
        message=exc.message,
        details=exc.details
    )

@app.exception_handler(HTTPException)
async def http_exception_handler(request: Request, exc: HTTPException):
    """Custom HTTP exception handler"""
    return ResponseFormatter.error(
        message=str(exc.detail),
        status_code=exc.status_code
    )

@app.exception_handler(Exception)
async def general_exception_handler(request: Request, exc: Exception):
    """General exception handler"""
    request_id = getattr(request.state, 'request_id', None)
    return ResponseFormatter.error(
        message="Internal server error",
        error_code="INTERNAL_ERROR",
        status_code=500,
        details={"original_error": str(exc)} if str(exc) != "Internal server error" else None,
        request_id=request_id
    )

# Initialize user service and attach to auth service
from src.services.user_service import UserService
user_service = UserService()
from src.core.security import auth_service as global_auth_service
global_auth_service.user_service = user_service

# Include API routers
app.include_router(auth_router, prefix="/api/v1")

# Import and include other API routers
from src.api.v1.endpoints.students import router as students_router
app.include_router(students_router, prefix="/api/v1")

# Add request ID tracking to request state for all endpoints
@app.middleware("http")
async def add_request_id(request: Request, call_next):
    """Add request ID to all requests"""
    request.state.request_id = str(uuid.uuid4())
    response = await call_next(request)
    # Add request ID to headers
    response.headers["x-request-id"] = request.state.request_id
    return response

# API endpoints
@app.get("/")
async def root():
    """Root endpoint with API information"""
    return ResponseFormatter.success({
        "message": "Edu-Flow Backend API",
        "version": "1.0.0",
        "docs_url": "/docs",
        "uptime": time.time() - app.state.startup_time
    })

@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return ResponseFormatter.success({
        "status": "healthy",
        "timestamp": time.time(),
        "uptime": time.time() - app.state.startup_time
    })

@app.get("/api/v1/info")
async def api_info():
    """API information endpoint"""
    return {
        "name": "Edu-Flow Backend API",
        "version": "1.0.0",
        "description": "Backend API for Edu-Flow Institution Management System",
        "endpoints": {
            "auth": "/api/v1/auth",
            "users": "/api/v1/users",
            "students": "/api/v1/students",
            "courses": "/api/v1/courses",
            "teachers": "/api/v1/teachers"
        }
    }

# Protected endpoints requiring authentication
@app.get("/api/v1/users/me")
async def get_current_user(request: Request):
    """Get current user information"""
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
    except IndexError:
        raise AuthenticationError("Invalid token format")
    except Exception as e:
        raise AuthenticationError("Invalid token")

@app.get("/api/v1/teachers/me")
async def get_teacher_profile(request: Request):
    """Get teacher profile information"""
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
    """Get admin dashboard information"""
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
    """Get password strength requirements"""
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
    """Get available user roles"""
    return {
        "roles": ["admin", "teacher", "student", "staff"],
        "message": "Available roles retrieved successfully"
    }

# Include API routers (these will be populated as we create more endpoints)
# app.include_router(users_router, prefix="/api/v1")
# app.include_router(courses_router, prefix="/api/v1") 
# app.include_router(students_router, prefix="/api/v1")

# Database endpoints
@app.get("/api/v1/database/health")
async def database_health_check():
    """Database health check endpoint"""
    try:
        health = await database_service.health_check()
        return {
            "status": "healthy",
            "database": health,
            "message": "Database connection successful"
        }
    except Exception as e:
        raise DatabaseError(f"Database health check failed: {e}")

@app.post("/api/v1/database/initialize")
async def initialize_database_endpoint():
    """Initialize database with default data"""
    try:
        success = await initialize_database()
        if success:
            return {
                "status": "success",
                "message": "Database initialized successfully",
                "timestamp": time.time()
            }
        else:
            raise DatabaseError("Database initialization failed")
    except Exception as e:
        raise DatabaseError(f"Database initialization failed: {e}")

@app.get("/api/v1/database/collections")
async def get_database_collections():
    """Get database collection information"""
    try:
        collections = {}
        for collection_name in ['users', 'courses', 'departments', 'enrollments', 'assessments']:
            try:
                count = await database_service.count_documents(collection_name, {})
                collections[collection_name] = count
            except Exception as e:
                collections[collection_name] = f"Error: {e}"
        
        return {
            "collections": collections,
            "total_collections": len(collections),
            "message": "Collection information retrieved successfully"
        }
    except Exception as e:
        raise DatabaseError(f"Failed to get collection information: {e}")

@app.get("/api/v1/database/departments")
async def get_departments():
    """Get all departments"""
    import logging
    logger = logging.getLogger(__name__)
    
    try:
        # Debug: Check database service state
        logger.debug(f"Database service state - db: {database_service.db}")
        logger.debug(f"Database service state - client: {database_service.client}")
        
        departments = await database_service.find_many("departments", {})
        return {
            "departments": departments,
            "count": len(departments),
            "message": "Departments retrieved successfully"
        }
    except Exception as e:
        logger.error(f"Error in get_departments: {e}")
        raise DatabaseError(f"Failed to get departments: {e}")

@app.post("/api/v1/database/departments")
async def create_department(department_data: dict):
    """Create a new department"""
    try:
        # Validate required fields
        required_fields = ["department_id", "name", "code", "description"]
        for field in required_fields:
            if field not in department_data:
                raise ValidationError(f"Missing required field: {field}")
        
        # Check if department already exists
        existing = await database_service.find_one("departments", {"department_id": department_data["department_id"]})
        if existing:
            raise ConflictError("Department with this ID already exists")
        
        department_id = await database_service.insert_one("departments", department_data)
        return {
            "status": "success",
            "department_id": department_id,
            "message": "Department created successfully"
        }
    except Exception as e:
        raise DatabaseError(f"Failed to create department: {e}")

@app.get("/api/v1/database/courses")
async def get_courses():
    """Get all courses"""
    try:
        courses = await database_service.find_many("courses", {})
        return {
            "courses": courses,
            "count": len(courses),
            "message": "Courses retrieved successfully"
        }
    except Exception as e:
        raise DatabaseError(f"Failed to get courses: {e}")

@app.post("/api/v1/database/courses")
async def create_course(course_data: dict):
    """Create a new course"""
    try:
        # Validate required fields
        required_fields = ["course_id", "title", "code", "department_id", "level", "credits"]
        for field in required_fields:
            if field not in course_data:
                raise ValidationError(f"Missing required field: {field}")
        
        # Check if course already exists
        existing = await database_service.find_one("courses", {"code": course_data["code"]})
        if existing:
            raise ConflictError("Course with this code already exists")
        
        course_id = await database_service.insert_one("courses", course_data)
        return {
            "status": "success",
            "course_id": course_id,
            "message": "Course created successfully"
        }
    except Exception as e:
        raise DatabaseError(f"Failed to create course: {e}")

# Start the application
if __name__ == "__main__":
    uvicorn.run(
        "main:app",
        host=settings.host,
        port=settings.port,
        reload=settings.debug,
        log_level="info"
    )