"""
FastAPI/Flask integration module for the logging system.
This module provides easy integration of the logging system with FastAPI applications.
"""

import os
from typing import Optional, List
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from ..config.logging import get_logger, get_component_logger
from ..config.logging_config import setup_logging
from .logging_middleware import LoggingMiddleware, SecurityLoggingMiddleware, PerformanceLoggingMiddleware
from .logging_utils import log_user_action, log_security_event

def setup_logging_middleware(app: FastAPI, environment: str = None):
    """
    Setup logging middleware for a FastAPI application.
    
    Args:
        app: FastAPI application instance
        environment: Environment (development, testing, production)
    """
    # Setup logging configuration
    logging_config = setup_logging(environment)
    
    # Add middleware in order of importance
    app.add_middleware(PerformanceLoggingMiddleware)
    app.add_middleware(SecurityLoggingMiddleware)
    app.add_middleware(LoggingMiddleware)
    
    return logging_config

def create_fastapi_app(
    app_name: str = "Edu-Flow",
    environment: str = None,
    cors_origins: List[str] = None,
    debug: bool = None
) -> FastAPI:
    """
    Create a FastAPI application with logging middleware already configured.
    
    Args:
        app_name: Name of the application
        environment: Environment (development, testing, production)
        cors_origins: List of CORS origins
        debug: Debug mode
        
    Returns:
        Configured FastAPI application
    """
    # Determine environment
    env = environment or os.getenv('ENVIRONMENT', 'development')
    
    # Create FastAPI app
    app = FastAPI(
        title=app_name,
        description="Institution Accreditation and Automation System",
        version="2.0.0",
        debug=debug if debug is not None else (env == 'development')
    )
    
    # Setup CORS middleware
    cors_origins = cors_origins or [
        "http://localhost:3000",
        "http://localhost:8080",
        "http://127.0.0.1:3000",
        "https://localhost:3000"
    ]
    
    app.add_middleware(
        CORSMiddleware,
        allow_origins=cors_origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    
    # Setup logging middleware
    setup_logging_middleware(app, env)
    
    # Add startup and shutdown events for logging
    @app.on_event("startup")
    async def startup_event():
        logger = get_logger('backend')
        logger.info(f"{app_name} starting up", environment=env)
        
        # Log system information
        log_user_action(
            action="system_startup",
            user_id="system",
            resource="application",
            details={
                "app_name": app_name,
                "environment": env,
                "version": "2.0.0"
            }
        )
    
    @app.on_event("shutdown")
    async def shutdown_event():
        logger = get_logger('backend')
        logger.info(f"{app_name} shutting down", environment=env)
        
        # Log system information
        log_user_action(
            action="system_shutdown",
            user_id="system",
            resource="application",
            details={
                "app_name": app_name,
                "environment": env
            }
        )
    
    return app

def log_request_exception_handler(request, exc):
    """
    Custom exception handler for logging unhandled exceptions.
    
    Args:
        request: FastAPI request object
        exc: Exception that occurred
        
    Returns:
        HTTPException response
    """
    logger = get_logger('backend')
    
    # Log the unhandled exception
    logger.error(
        f"Unhandled exception: {str(exc)}",
        error=str(exc),
        exception=repr(exc),
        url=str(request.url),
        method=request.method
    )
    
    # Log security event
    log_security_event(
        event_type="unhandled_exception",
        severity="HIGH",
        ip_address=request.client.host if request.client else "unknown",
        user_agent=request.headers.get("user-agent", "unknown"),
        details={
            "url": str(request.url),
            "method": request.method,
            "error": str(exc)
        }
    )
    
    # Return HTTPException
    raise HTTPException(
        status_code=500,
        detail="Internal server error"
    )

def add_logging_routes(app: FastAPI):
    """
    Add logging-related routes for monitoring and debugging.
    
    Args:
        app: FastAPI application instance
    """
    logger = get_logger('backend')
    
    @app.get("/api/logs/status")
    async def get_logging_status():
        """Get logging system status"""
        return {
            "status": "active",
            "environment": os.getenv('ENVIRONMENT', 'development'),
            "components": ["backend", "frontend", "auth-gateway", "ai-services", "database"],
            "features": [
                "rotating_file_logs",
                "structured_logging",
                "performance_monitoring",
                "security_logging",
                "audit_trails"
            ]
        }
    
    @app.get("/api/logs/backend")
    async def get_backend_logs():
        """Get recent backend logs"""
        # This would typically read from the log files or use a log aggregation service
        return {
            "component": "backend",
            "logs": "Recent log entries would be returned here",
            "count": 0
        }
    
    @app.get("/api/logs/security")
    async def get_security_logs():
        """Get recent security logs"""
        return {
            "component": "security",
            "logs": "Recent security events would be returned here",
            "count": 0
        }
    
    @app.post("/api/logs/clear/{component}")
    async def clear_logs(component: str):
        """Clear log files for a specific component"""
        # This would typically clear the log files for the specified component
        logger.info(f"Clearing logs for component: {component}")
        return {"message": f"Logs cleared for component: {component}"}
    
    logger.info("Logging routes added")

def create_auth_dependency():
    """
    Create authentication dependency that logs authentication attempts.
    
    Returns:
        Authentication dependency function
    """
    logger = get_logger('auth-gateway')
    
    async def auth_dependency(token: str = None):
        """Dependency for authentication with logging"""
        if not token:
            log_security_event(
                event_type="missing_token",
                severity="MEDIUM",
                details={"message": "No authentication token provided"}
            )
            raise HTTPException(
                status_code=401,
                detail="Authentication required"
            )
        
        # Log token validation attempt
        logger.info(
            f"Token validation attempt",
            has_token=bool(token),
            token_prefix=token[:10] + "..." if token else None
        )
        
        # In a real implementation, you would validate the token here
        # For now, just return a placeholder user
        return {"user_id": "placeholder", "token": token}
    
    return auth_dependency

# Factory functions for different loggers
def get_component_loggers():
    """Get loggers for all components"""
    return {
        'backend': get_component_logger('backend'),
        'frontend': get_component_logger('frontend'),
        'auth-gateway': get_component_logger('auth-gateway'),
        'ai-services': get_component_logger('ai-services'),
        'database': get_component_logger('database'),
        'performance': get_component_logger('performance'),
        'security': get_component_logger('security')
    }

def create_logging_context(component: str, **context):
    """
    Create a logging context for a specific component.
    
    Args:
        component: Component name
        context: Additional context to add
        
    Returns:
        Logging context manager
    """
    from .logging_utils import LogContext
    return LogContext(component, **context)