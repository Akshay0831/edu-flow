"""
Edu-Flow API v1

This module provides the main FastAPI application instance and configuration
for the Edu-Flow API version 1. It includes route registration, CORS setup,
authentication middleware, and API documentation.

Author: Edu-Flow Team
"""

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.trustedhost import TrustedHostMiddleware
from fastapi.responses import JSONResponse
from fastapi.openapi.docs import get_swagger_ui_html, get_redoc_html
from fastapi.openapi.utils import get_openapi
import uvicorn
import os
from logging import getLogger
from datetime import datetime
import json

from core.security import SecurityConfig
from core.exceptions import BaseError, AuthenticationError, DatabaseError
from core.config.settings import settings
from .users.routes import router as users_router
from .students.routes import router as students_router
from .courses.routes import router as courses_router
from .endpoints.feedback_processing import router as feedback_processing_router
from .endpoints.excel_integration import router as excel_integration_router
from .endpoints.see_prediction import router as see_prediction_router
from .endpoints.analytics_advanced import router as analytics_advanced_router

logger = getLogger(__name__)

# Create FastAPI app
app = FastAPI(
    title="Edu-Flow API",
    description="Edu-Flow Education Management System API",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
    openapi_url="/openapi.json"
)

# Global exception handlers
@app.exception_handler(BaseError)
async def edu_flow_exception_handler(request: Request, exc: BaseError):
    """Handle Edu-Flow specific exceptions"""
    logger.error(f"Edu-Flow Exception: {exc.message}")
    return JSONResponse(
        status_code=500,
        content={"error": exc.message, "code": exc.error_code}
    )

@app.exception_handler(DatabaseError)
async def database_exception_handler(request: Request, exc: DatabaseError):
    """Handle database errors"""
    logger.error(f"Database Error: {str(exc)}")
    return JSONResponse(
        status_code=500,
        content={"error": "Database error occurred", "code": "DATABASE_ERROR"}
    )

@app.exception_handler(AuthenticationError)
async def authentication_exception_handler(request: Request, exc: AuthenticationError):
    """Handle authentication errors"""
    logger.error(f"Authentication Error: {str(exc)}")
    return JSONResponse(
        status_code=401,
        content={"error": "Authentication failed", "code": "AUTHENTICATION_ERROR"}
    )

@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    """Handle unhandled exceptions"""
    logger.error(f"Unhandled Exception: {str(exc)}")
    return JSONResponse(
        status_code=500,
        content={"error": "Internal server error", "code": "INTERNAL_ERROR"}
    )

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Trusted host middleware
app.add_middleware(
    TrustedHostMiddleware,
    allowed_hosts=["*"]
)

# Request logging middleware
@app.middleware("http")
async def log_requests(request: Request, call_next):
    """Log all incoming requests"""
    start_time = datetime.now()
    
    response = await call_next(request)
    
    process_time = (datetime.now() - start_time).total_seconds()
    
    logger.info(f"Request: {request.method} {request.url} - Status: {response.status_code} - Time: {process_time:.3f}s")
    
    return response

# Include API routes
app.include_router(users_router)
app.include_router(students_router)
app.include_router(courses_router)
app.include_router(feedback_processing_router)
app.include_router(excel_integration_router)
app.include_router(see_prediction_router)
app.include_router(analytics_advanced_router)

# Health check endpoint
@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {"status": "healthy", "timestamp": datetime.now().isoformat()}

# API info endpoint
@app.get("/api/info")
async def api_info():
    """Get API information"""
    return {
        "name": "Edu-Flow API",
        "version": "1.0.0",
        "description": "Edu-Flow Education Management System API",
        "endpoints": {
            "users": "/users",
            "students": "/students",
            "courses": "/courses",
            "feedback": "/feedback",
            "excel": "/excel",
            "see_prediction": "/see-prediction",
            "health": "/health"
        }
    }

# Custom OpenAPI configuration
def custom_openapi():
    if app.openapi_schema:
        return app.openapi_schema
    
    openapi_schema = get_openapi(
        title="Edu-Flow API",
        version="1.0.0",
        description="Edu-Flow Education Management System API",
        routes=app.routes,
    )
    
    # Add security configuration
    openapi_schema["components"]["securitySchemes"] = {
        "OAuth2": {
            "type": "oauth2",
            "description": "OAuth2 token authentication",
            "in": "header",
            "name": "Authorization",
            "scheme": "bearer",
            "bearerFormat": "JWT"
        }
    }
    
    # Apply security to all endpoints
    for path in openapi_schema["paths"].values():
        for method in path.values():
            if method.get("security") is None:
                method["security"] = [{"OAuth2": []}]
    
    app.openapi_schema = openapi_schema
    return app.openapi_schema

app.openapi = custom_openapi

# Root endpoint
@app.get("/")
async def root():
    """Root endpoint"""
    return {"message": "Welcome to Edu-Flow API", "version": "1.0.0"}

# API documentation
@app.get("/docs", include_in_schema=False)
async def custom_docs():
    return get_swagger_ui_html(
        openapi_url="/openapi.json",
        title="Edu-Flow API Documentation",
        oauth2_config=SecurityConfig.OAUTH2_CONFIG
    )

@app.get("/redoc", include_in_schema=False)
async def redoc():
    return get_redoc_html(
        openapi_url="/openapi.json",
        title="Edu-Flow API Documentation"
    )

# API stats endpoint
@app.get("/api/stats")
async def api_stats():
    """Get API statistics"""
    return {
        "endpoints_count": len(app.routes),
        "version": "1.0.0",
        "uptime": datetime.now().isoformat()
    }

if __name__ == "__main__":
    uvicorn.run(
        "src.api.v1:app",
        host=settings.HOST,
        port=settings.PORT,
        reload=settings.DEBUG,
        log_level="info"
    )