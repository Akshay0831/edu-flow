"""
FastAPI Application for Edu-Flow Backend

This module initializes the FastAPI application with all necessary components:
- API endpoints
- Database connections
- Security middleware
- CORS configuration
- Error handling
- Health checks
- Dependency injection
- Service management
- Caching
- Circuit breakers

Author: Edu-Flow Team
"""

import uvicorn
import uuid
import time
from fastapi import FastAPI, Request, HTTPException, Depends
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.gzip import GZipMiddleware
from fastapi.responses import JSONResponse
from typing import Optional
from contextlib import asynccontextmanager
import asyncio
import logging

from core.exceptions import (
    BaseError, ValidationError, NotFoundError, AuthenticationError,
    AuthorizationError, ForbiddenError, ConflictError, DatabaseError,
    ExternalServiceError, RateLimitError, ConfigurationError
)
from core.security import auth_service
from core.response_handler import ResponseFormatter
from core.error_handling import setup_error_handling
from core.database_abstraction import DatabaseConfig, DatabaseType, initialize_database_manager
from core.cache_abstraction import CacheConfig, CacheBackend, initialize_cache_manager
from core.service_container import initialize_service_container, configure_services, get_service_container
from core.api_service import initialize_api_client
from src.services.base_service import ServiceFactory, CourseService, StudentService, TeacherService, AssessmentService
from src.services.user_service import UserService as AuthUserService
# Commented out - Rust AI services not available yet
# from services.rust_ai_services import (
#     initialize_container,
#     shutdown_container,
#     get_container,
#     ServiceContainer,
# )
from api.v1.endpoints.auth import router as auth_router
from api.v1.endpoints.auth_enhanced import router as auth_enhanced_router
from api.v1.endpoints.users import router as users_router
from api.v1.endpoints.courses import router as courses_router
from api.v1.endpoints.students import router as students_router
from api.v1.endpoints.teachers_simple import router as teachers_router
from api.v1.endpoints.assessments_simple import router as assessments_router
from api.v1.endpoints.analytics_simple import router as analytics_router
from api.v1.endpoints.see_prediction import router as see_prediction_router
from api.v1.endpoints.analytics_advanced import router as analytics_advanced_router

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Application lifespan
@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan context manager"""
    app.state.startup_time = time.time()
    app.state.request_id = str(uuid.uuid4())
    
    logger.info("🚀 Starting Edu-Flow application...")
    
    try:
        # Initialize service container
        logger.info("📦 Initializing service container...")
        config = {
            'database': {
                'type': 'sqlite',
                'database': 'edu_flow.db',
                'host': 'localhost',
                'port': 5432,
                'username': 'user',
                'password': 'password',
                'options': {
                    'echo': False,
                    'pool_recycle': 3600,
                    'max_connections': 10,
                    'connection_timeout': 30
                }
            },
            'cache': {
                'backend': 'memory',
                'host': 'localhost',
                'port': 6379,
                'database': '0',
                'ttl': 3600,
                'key_prefix': 'edu_flow:',
                'options': {
                    'max_memory_size': 1024 * 1024 * 1024,  # 1GB
                    'eviction_policy': 'lru'
                }
            },
            'api': {
                'base_url': 'http://localhost:8000',
                'timeout': 30,
                'max_concurrent_requests': 10,
                'services': {
                    'database': {
                        'base_url': 'http://localhost:8000/api/v1',
                        'headers': {'Content-Type': 'application/json'}
                    },
                    'auth': {
                        'base_url': 'http://localhost:8000/api/v1',
                        'headers': {'Content-Type': 'application/json'}
                    },
                    'ai': {
                        'base_url': 'http://localhost:8001',
                        'headers': {'Content-Type': 'application/json'}
                    },
                    'notification': {
                        'base_url': 'http://localhost:8002',
                        'headers': {'Content-Type': 'application/json'}
                    }
                }
            }
        }
        
        initialize_service_container(config)
        await configure_services(config)
        
        # Initialize database
        logger.info("🗄️  Initializing database...")
        container = get_service_container()
        
        db_config = await container.resolve('database_config')
        db_manager = initialize_database_manager(db_config)
        await db_manager.initialize()
        container.register_instance('database_manager', db_manager)
        app.state.database = db_manager
        
        # Initialize cache
        logger.info("🏷️  Initializing cache...")
        cache_config = await container.resolve('cache_config')
        cache_manager = initialize_cache_manager(cache_config)
        await cache_manager.initialize()
        container.register_instance('cache_manager', cache_manager)
        
        # Initialize API client
        logger.info("🌐 Initializing API client...")
        api_client, api_service = await initialize_api_client(config['api'])
        container.register_instance('api_client', api_client)
        container.register_instance('api_service', api_service)
        
        # Register services
        logger.info("⚙️  Registering services...")
        ServiceFactory.register_service('user', AuthUserService)
        ServiceFactory.register_service('course', CourseService)
        ServiceFactory.register_service('student', StudentService)
        ServiceFactory.register_service('teacher', TeacherService)
        ServiceFactory.register_service('assessment', AssessmentService)
        
        # Initialize services
        user_service = AuthUserService(database_manager=db_manager)
        logger.info(f"Created user service: {type(user_service)}")
        await user_service.initialize()
        auth_service.user_service = user_service
        import api.v1.endpoints.users as users_endpoint
        users_endpoint.user_service = user_service
        logger.info(f"Assigned user service to auth service: {type(auth_service.user_service)}")
        
        # Initialize Rust AI Services container (placeholder for future implementation)
        logger.info("🤖 Rust AI Services initialization skipped - placeholder for future implementation")
        logger.info("📊 Health check available at /health")
        logger.info("📚 API documentation available at /docs")
        
        yield
        
    except Exception as e:
        logger.error(f"❌ Application startup failed: {str(e)}")
        raise
    
    finally:
        app.state.shutdown_time = time.time()
        
        logger.info("🛑 Shutting down Edu-Flow application...")
        
        try:
            # Clean up Rust AI services (placeholder for future implementation)
            logger.info("🤖 Rust AI Services cleanup completed (placeholder)")
            
            # Clean up services
            if 'user_service' in locals():
                await user_service.dispose()
            
            # Clean up database
            if 'db_manager' in locals():
                await db_manager.disconnect()
            
            # Clean up cache
            if 'cache_manager' in locals():
                await cache_manager.disconnect()
            
            logger.info("✅ Application shutdown completed")
            
        except Exception as e:
            logger.error(f"❌ Error during shutdown: {str(e)}")

# Create FastAPI app with lifespan
app = FastAPI(
    title="Edu-Flow API",
    description="Education Management System API",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
    lifespan=lifespan,
    debug=True
)

# Set up error handling before adding other middleware
setup_error_handling(app)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure this for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
    expose_headers=["*"],
    max_age=600
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
        response.headers["content-security-policy"] = "default-src 'self'; img-src 'self' data:; script-src 'self' 'unsafe-inline'; style-src 'self' 'unsafe-inline'"
        response.headers["x-content-security-policy"] = "default-src 'self'; img-src 'self' data:; script-src 'self' 'unsafe-inline'; style-src 'self' 'unsafe-inline'"
        return response

app.add_middleware(SecurityHeadersMiddleware)

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
    logger.error(f"Unhandled exception: {str(exc)}", exc_info=True)
    return ResponseFormatter.error(
        message="Internal server error",
        error_code="INTERNAL_ERROR",
        status_code=500,
        details={"original_error": str(exc)} if str(exc) != "Internal server error" else None,
        request_id=request_id
    )

# Include API routers
app.include_router(auth_router, prefix="/api/v1", tags=["authentication"])
app.include_router(auth_enhanced_router, prefix="/api/v1", tags=["enhanced-authentication"])
app.include_router(users_router, prefix="/api/v1", tags=["users"])
app.include_router(courses_router, prefix="/api/v1", tags=["courses"])
app.include_router(students_router, prefix="/api/v1", tags=["students"])
app.include_router(teachers_router, prefix="/api/v1", tags=["teachers"])
app.include_router(assessments_router, prefix="/api/v1", tags=["assessments"])
app.include_router(analytics_router, prefix="/api/v1", tags=["analytics"])
app.include_router(see_prediction_router, prefix="/api/v1", tags=["see-prediction"])
app.include_router(analytics_advanced_router, prefix="/api/v1", tags=["advanced-analytics"])

# Rust AI Services routes
def get_rust_ai_health_router():
    """Create router for Rust AI services health endpoints"""
    from fastapi import APIRouter

    router = APIRouter(prefix="/rust-ai", tags=["rust-ai-services"])

    @router.get("/health", summary="Check all Rust AI services health")
    async def check_all_health():
        """Check health of all Rust AI services"""
        from services.rust_ai_services import get_container
        container = get_container()
        return await container.check_all_services_health()

    @router.get("/services/{service_name}", summary="Check specific service health")
    async def check_service_health(service_name: str):
        """Check health of a specific Rust AI service"""
        from services.rust_ai_services import get_container
        container = get_container()
        return await container.get_service_health(service_name)

    @router.get("/stats", summary="Get Rust AI services statistics")
    async def get_stats():
        """Get statistics about Rust AI services"""
        from services.rust_ai_services import get_container, ServiceContainerStats
        container = get_container()
        stats = await container.get_stats()
        return {
            "total_services": stats.total_services,
            "enabled_services": stats.enabled_services,
            "total_requests": stats.total_requests,
            "total_errors": stats.total_errors,
            "average_latency_ms": stats.average_latency_ms,
            "cache_hit_rate": stats.cache_hit_rate,
            "system_health": stats.system_health
        }

    return router

app.include_router(
    get_rust_ai_health_router(),
    tags=["rust-ai-services"]
)


@app.get("/rust-ai/health", tags=["rust-ai-services"])
async def rust_ai_health():
    """Health check for Rust AI Services"""
    from services.rust_ai_services import get_container
    container = get_container()
    health = await container.check_all_services_health()
    return {
        "status": health["overall_health"],
        "services": health["services"],
        "total_services": health["total_services"],
        "healthy_services": health["healthy_services"]
    }


@app.get("/rust-ai/stats", tags=["rust-ai-services"])
async def rust_ai_stats():
    """Statistics for Rust AI Services"""
    from services.rust_ai_services import get_container, ServiceContainerStats
    container = get_container()
    stats = await container.get_stats()
    return {
        "total_services": stats.total_services,
        "enabled_services": stats.enabled_services,
        "total_requests": stats.total_requests,
        "total_errors": stats.total_errors,
        "average_latency_ms": stats.average_latency_ms,
        "cache_hit_rate": stats.cache_hit_rate,
        "system_health": stats.system_health
    }




# Health check endpoint
@app.get("/health")
async def health_check():
    """Application health check endpoint"""
    container = get_service_container()
    
    health_status = {
        "status": "healthy",
        "timestamp": time.time(),
        "version": "1.0.0",
        "components": {}
    }
    
    # Check database health
    try:
        if container.get_service('database_manager'):
            db_manager = container.get_service('database_manager')
            db_health = await db_manager.health_check()
            health_status["components"]["database"] = {
                "status": "healthy" if db_health else "unhealthy",
                "details": db_health
            }
    except Exception as e:
        health_status["components"]["database"] = {
            "status": "unhealthy",
            "error": str(e)
        }
    
    # Check cache health
    try:
        if container.get_service('cache_manager'):
            cache_manager = container.get_service('cache_manager')
            cache_health = await cache_manager.health_check()
            health_status["components"]["cache"] = {
                "status": "healthy" if cache_health else "unhealthy",
                "details": cache_health
            }
    except Exception as e:
        health_status["components"]["cache"] = {
            "status": "unhealthy",
            "error": str(e)
        }
    
    # Check service health
    try:
        service_health = await container.health_check()
        health_status["components"]["services"] = service_health
    except Exception as e:
        health_status["components"]["services"] = {
            "status": "unhealthy",
            "error": str(e)
        }
    
    # Check API service health
    try:
        if container.get_service('api_service'):
            api_service = container.get_service('api_service')
            api_health = await api_service.health_check()
            health_status["components"]["api"] = api_health
    except Exception as e:
        health_status["components"]["api"] = {
            "status": "unhealthy",
            "error": str(e)
        }
    
    # Determine overall status
    unhealthy_components = [
        comp for comp, status in health_status["components"].items()
        if status.get("status") == "unhealthy"
    ]
    
    if unhealthy_components:
        health_status["status"] = "degraded"
        health_status["unhealthy_components"] = unhealthy_components
    
    return health_status

# Root endpoint
@app.get("/")
async def root():
    """Root endpoint with application information"""
    return {
        "message": "Welcome to Edu-Flow API",
        "version": "1.0.0",
        "docs": "/docs",
        "health": "/health",
        "endpoints": {
            "auth": "/api/v1/auth",
            "users": "/api/v1/users",
            "courses": "/api/v1/courses",
            "students": "/api/v1/students",
            "teachers": "/api/v1/teachers",
            "assessments": "/api/v1/assessments",
            "analytics": "/api/v1/analytics"
        }
    }

# Metrics endpoint
@app.get("/metrics")
async def metrics():
    """Application metrics endpoint"""
    container = get_service_container()
    
    metrics = {
        "timestamp": time.time(),
        "uptime": time.time() - getattr(app.state, 'startup_time', time.time()),
        "services": {}
    }
    
    # Get service metrics
    for service_name in ServiceFactory.get_registered_services():
        try:
            service = ServiceFactory.create_service(service_name)
            metrics["services"][service_name] = service.get_metrics()
        except Exception as e:
            metrics["services"][service_name] = {
                "error": str(e)
            }
    
    # Get API client metrics
    try:
        api_client = container.get_service('api_client')
        metrics["api_client"] = api_client.get_metrics()
    except Exception as e:
        metrics["api_client"] = {"error": str(e)}
    
    return metrics

# Service dependencies
def get_user_service() -> AuthUserService:
    """Get user service instance"""
    return ServiceFactory.create_service('user')

def get_course_service() -> CourseService:
    """Get course service instance"""
    return ServiceFactory.create_service('course')

def get_student_service() -> StudentService:
    """Get student service instance"""
    return ServiceFactory.create_service('student')

def get_teacher_service() -> TeacherService:
    """Get teacher service instance"""
    return ServiceFactory.create_service('teacher')

def get_assessment_service() -> AssessmentService:
    """Get assessment service instance"""
    return ServiceFactory.create_service('assessment')

# Run the application
if __name__ == "__main__":
    uvicorn.run(
        "src.main:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="info"
    )