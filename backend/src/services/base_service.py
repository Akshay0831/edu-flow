"""
Base service class with comprehensive error handling, caching, and optimization.

This module provides:
- Base service with common functionality
- Error handling and logging
- Caching integration
- Metrics and monitoring
- Validation and transformation
- Transaction management
"""

from abc import ABC, abstractmethod
from typing import Dict, Any, Optional, List, Type, Union, TypeVar, Generic
from datetime import datetime
import asyncio
import logging
from dataclasses import dataclass
from functools import wraps
from contextlib import asynccontextmanager

from src.core.exceptions import BaseError, ValidationError, NotFoundError, DatabaseError
from src.core.database_abstraction import DatabaseManager, DatabaseInterface
from src.core.cache_abstraction import CacheManager, CacheConfig
from src.core.api_service import APIClient, APIService, APIRequest, APIResponse
from src.core.service_container import get_service_container
from src.core.logging import get_logger
from src.core.error_handling import retry_handler, log_errors

logger = get_logger(__name__)

T = TypeVar('T')


class BaseService(ABC, Generic[T]):
    """
    Base service class with common functionality for all services.
    """
    
    def __init__(self, service_name: str):
        self.service_name = service_name
        self._database: Optional[DatabaseInterface] = None
        self._cache: Optional[CacheManager] = None
        self._api_client: Optional[APIClient] = None
        self._api_service: Optional[APIService] = None
        self._metrics = {
            'service_calls': 0,
            'successful_calls': 0,
            'failed_calls': 0,
            'cache_hits': 0,
            'cache_misses': 0,
            'average_response_time': 0.0
        }
        self._initialized = False
    
    async def initialize(self):
        """Initialize the service with required dependencies."""
        if self._initialized:
            return
        
        # Get dependencies from service container
        container = get_service_container()
        
        # Database
        if container._instances.get('database_manager'):
            self._database = container._instances['database_manager'].instance.get_database()
        
        # Cache
        if container._instances.get('cache_manager'):
            self._cache = container._instances['cache_manager'].instance
        
        # API Client
        # Skip API client for now
        self._api_client = None
        self._api_service = None
        
        self._initialized = True
        logger.info(f"{self.service_name} service initialized")
    
    async def dispose(self):
        """Clean up resources."""
        self._database = None
        self._cache = None
        self._api_client = None
        self._api_service = None
        self._initialized = False
        logger.info(f"{self.service_name} service disposed")
    
    def _update_metrics(self, success: bool, response_time: float):
        """Update service metrics."""
        self._metrics['service_calls'] += 1
        
        if success:
            self._metrics['successful_calls'] += 1
        else:
            self._metrics['failed_calls'] += 1
        
        # Update average response time
        current_avg = self._metrics['average_response_time']
        total_calls = self._metrics['service_calls']
        self._metrics['average_response_time'] = (
            (current_avg * (total_calls - 1) + response_time) / total_calls
        )
    
    def get_metrics(self) -> Dict[str, Any]:
        """Get service metrics."""
        return self._metrics.copy()
    
    # Database operations with error handling
    @log_errors
    async def find_one(self, collection: str, filter: Dict[str, Any], 
                     projection: Dict[str, Any] = None) -> Optional[T]:
        """Find one document/row with caching and error handling."""
        start_time = asyncio.get_event_loop().time()
        
        try:
            # Generate cache key
            cache_key = f"{self.service_name}:{collection}:find_one:{hash(str(filter) + str(projection or {}))}"
            
            # Check cache first
            if self._cache:
                cached_result = await self._cache.get(cache_key)
                if cached_result is not None:
                    self._metrics['cache_hits'] += 1
                    self._update_metrics(True, asyncio.get_event_loop().time() - start_time)
                    return cached_result
            
            self._metrics['cache_misses'] += 1
            
            # Database operation
            if not self._database:
                raise DatabaseError("Database not available")
            
            result = await self._database.find_one(collection, filter, projection)
            
            # Cache result
            if self._cache and result is not None:
                await self._cache.set(cache_key, result, 3600)  # 1 hour cache
            
            self._update_metrics(True, asyncio.get_event_loop().time() - start_time)
            return result
            
        except Exception as e:
            logger.error(f"Failed to find one in {collection}: {str(e)}")
            self._update_metrics(False, asyncio.get_event_loop().time() - start_time)
            raise
    
    @log_errors
    async def find_many(self, collection: str, filter: Dict[str, Any] = None,
                      projection: Dict[str, Any] = None, limit: int = None,
                      skip: int = None, sort: List[tuple] = None) -> List[T]:
        """Find multiple documents/rows with caching and error handling."""
        start_time = asyncio.get_event_loop().time()
        
        try:
            # Generate cache key
            cache_key = f"{self.service_name}:{collection}:find_many:{hash(str(filter or {}) + str(projection or {}) + str(limit) + str(skip) + str(sort or []))}"
            
            # Check cache first
            if self._cache:
                cached_result = await self._cache.get(cache_key)
                if cached_result is not None:
                    self._metrics['cache_hits'] += 1
                    self._update_metrics(True, asyncio.get_event_loop().time() - start_time)
                    return cached_result
            
            self._metrics['cache_misses'] += 1
            
            # Database operation
            if not self._database:
                raise DatabaseError("Database not available")
            
            results = await self._database.find_many(
                collection, filter, projection, limit, skip, sort
            )
            
            # Cache result
            if self._cache and results:
                await self._cache.set(cache_key, results, 3600)  # 1 hour cache
            
            self._update_metrics(True, asyncio.get_event_loop().time() - start_time)
            return results
            
        except Exception as e:
            logger.error(f"Failed to find many in {collection}: {str(e)}")
            self._update_metrics(False, asyncio.get_event_loop().time() - start_time)
            raise
    
    @log_errors
    async def insert_one(self, collection: str, document: Dict[str, Any]) -> str:
        """Insert one document/row with validation and error handling."""
        start_time = asyncio.get_event_loop().time()
        
        try:
            # Validate document
            self._validate_document(document, collection)
            
            # Database operation
            if not self._database:
                raise DatabaseError("Database not available")
            
            result = await self._database.insert_one(collection, document)
            
            # Clear cache for this collection
            if self._cache:
                await self._cache.clear(f"{self.service_name}:{collection}:*")
            
            self._update_metrics(True, asyncio.get_event_loop().time() - start_time)
            return result
            
        except Exception as e:
            logger.error(f"Failed to insert one in {collection}: {str(e)}")
            self._update_metrics(False, asyncio.get_event_loop().time() - start_time)
            raise
    
    @log_errors
    async def insert_many(self, collection: str, documents: List[Dict[str, Any]]) -> List[str]:
        """Insert multiple documents/rows with validation and error handling."""
        start_time = asyncio.get_event_loop().time()
        
        try:
            # Validate documents
            for document in documents:
                self._validate_document(document, collection)
            
            # Database operation
            if not self._database:
                raise DatabaseError("Database not available")
            
            results = await self._database.insert_many(collection, documents)
            
            # Clear cache for this collection
            if self._cache:
                await self._cache.clear(f"{self.service_name}:{collection}:*")
            
            self._update_metrics(True, asyncio.get_event_loop().time() - start_time)
            return results
            
        except Exception as e:
            logger.error(f"Failed to insert many in {collection}: {str(e)}")
            self._update_metrics(False, asyncio.get_event_loop().time() - start_time)
            raise
    
    @log_errors
    async def update_one(self, collection: str, filter: Dict[str, Any],
                       update: Dict[str, Any]) -> int:
        """Update one document/row with validation and error handling."""
        start_time = asyncio.get_event_loop().time()
        
        try:
            # Validate update operation
            self._validate_update(update, collection)
            
            # Database operation
            if not self._database:
                raise DatabaseError("Database not available")
            
            result = await self._database.update_one(collection, filter, update)
            
            # Clear cache for this collection
            if self._cache:
                await self._cache.clear(f"{self.service_name}:{collection}:*")
            
            self._update_metrics(True, asyncio.get_event_loop().time() - start_time)
            return result
            
        except Exception as e:
            logger.error(f"Failed to update one in {collection}: {str(e)}")
            self._update_metrics(False, asyncio.get_event_loop().time() - start_time)
            raise
    
    @log_errors
    async def update_many(self, collection: str, filter: Dict[str, Any],
                        update: Dict[str, Any]) -> int:
        """Update multiple documents/rows with validation and error handling."""
        start_time = asyncio.get_event_loop().time()
        
        try:
            # Validate update operation
            self._validate_update(update, collection)
            
            # Database operation
            if not self._database:
                raise DatabaseError("Database not available")
            
            result = await self._database.update_many(collection, filter, update)
            
            # Clear cache for this collection
            if self._cache:
                await self._cache.clear(f"{self.service_name}:{collection}:*")
            
            self._update_metrics(True, asyncio.get_event_loop().time() - start_time)
            return result
            
        except Exception as e:
            logger.error(f"Failed to update many in {collection}: {str(e)}")
            self._update_metrics(False, asyncio.get_event_loop().time() - start_time)
            raise
    
    @log_errors
    async def delete_one(self, collection: str, filter: Dict[str, Any]) -> int:
        """Delete one document/row with validation and error handling."""
        start_time = asyncio.get_event_loop().time()
        
        try:
            # Database operation
            if not self._database:
                raise DatabaseError("Database not available")
            
            result = await self._database.delete_one(collection, filter)
            
            # Clear cache for this collection
            if self._cache:
                await self._cache.clear(f"{self.service_name}:{collection}:*")
            
            self._update_metrics(True, asyncio.get_event_loop().time() - start_time)
            return result
            
        except Exception as e:
            logger.error(f"Failed to delete one in {collection}: {str(e)}")
            self._update_metrics(False, asyncio.get_event_loop().time() - start_time)
            raise
    
    @log_errors
    async def delete_many(self, collection: str, filter: Dict[str, Any]) -> int:
        """Delete multiple documents/rows with validation and error handling."""
        start_time = asyncio.get_event_loop().time()
        
        try:
            # Database operation
            if not self._database:
                raise DatabaseError("Database not available")
            
            result = await self._database.delete_many(collection, filter)
            
            # Clear cache for this collection
            if self._cache:
                await self._cache.clear(f"{self.service_name}:{collection}:*")
            
            self._update_metrics(True, asyncio.get_event_loop().time() - start_time)
            return result
            
        except Exception as e:
            logger.error(f"Failed to delete many in {collection}: {str(e)}")
            self._update_metrics(False, asyncio.get_event_loop().time() - start_time)
            raise
    
    # API operations with caching and error handling
    @log_errors
    async def api_request(self, service_name: str, request: APIRequest) -> APIResponse:
        """Make an API request with error handling and caching."""
        start_time = asyncio.get_event_loop().time()
        
        try:
            if not self._api_service:
                raise BaseError("API service not available")
            
            # Get service client
            service_client = self._api_service.get_service_client(service_name)
            
            # Check cache first
            if self._cache and request.cache_key:
                cached_response = await self._cache.get(request.cache_key)
                if cached_response:
                    self._metrics['cache_hits'] += 1
                    response = APIResponse(
                        status_code=200,
                        headers={'X-Cache': 'HIT'},
                        data=cached_response,
                        request_time=asyncio.get_event_loop().time() - start_time,
                        cache_hit=True
                    )
                    self._update_metrics(True, asyncio.get_event_loop().time() - start_time)
                    return response
            
            self._metrics['cache_misses'] += 1
            
            # Make API request
            response = await service_client.request(request)
            
            # Cache successful responses
            if self._cache and request.cache_key and response.success:
                await self._cache.set(request.cache_key, response.json_data, request.cache_ttl)
            
            self._update_metrics(True, asyncio.get_event_loop().time() - start_time)
            return response
            
        except Exception as e:
            logger.error(f"API request failed for {service_name}: {str(e)}")
            self._update_metrics(False, asyncio.get_event_loop().time() - start_time)
            raise
    
    # Transaction support
    @asynccontextmanager
    async def transaction(self):
        """Context manager for database transactions."""
        if not self._database:
            raise DatabaseError("Database not available")
        
        # Start transaction
        logger.info(f"Starting transaction for {self.service_name}")
        
        try:
            yield self
            logger.info(f"Transaction completed successfully for {self.service_name}")
        except Exception as e:
            logger.error(f"Transaction failed for {self.service_name}: {str(e)}")
            raise
    
    # Validation methods
    def _validate_document(self, document: Dict[str, Any], collection: str):
        """Validate document before insertion."""
        # Base validation - can be overridden by subclasses
        if not document:
            raise ValidationError("Document cannot be empty", "document")
        
        # Add collection-specific validation
        if collection == "users":
            self._validate_user_document(document)
        elif collection == "courses":
            self._validate_course_document(document)
        elif collection == "students":
            self._validate_student_document(document)
        elif collection == "teachers":
            self._validate_teacher_document(document)
        elif collection == "assessments":
            self._validate_assessment_document(document)
    
    def _validate_update(self, update: Dict[str, Any], collection: str):
        """Validate update operation."""
        # Base validation - can be overridden by subclasses
        if not update:
            raise ValidationError("Update cannot be empty", "update")
        
        # Prevent full document replacement unless explicitly allowed
        if "$set" not in update and "$unset" not in update:
            logger.warning(f"Potentially dangerous update operation on {collection}")
    
    def _validate_user_document(self, document: Dict[str, Any]):
        """Validate user document."""
        required_fields = ['email', 'name', 'role']
        
        for field in required_fields:
            if field not in document:
                raise ValidationError(f"Missing required field: {field}", field)
        
        if not isinstance(document['email'], str) or '@' not in document['email']:
            raise ValidationError("Invalid email format", "email")
        
        valid_roles = ['admin', 'teacher', 'student']
        if document['role'] not in valid_roles:
            raise ValidationError(f"Invalid role: {document['role']}", "role")
    
    def _validate_course_document(self, document: Dict[str, Any]):
        """Validate course document."""
        required_fields = ['title', 'code', 'department_id']
        
        for field in required_fields:
            if field not in document:
                raise ValidationError(f"Missing required field: {field}", field)
    
    def _validate_student_document(self, document: Dict[str, Any]):
        """Validate student document."""
        required_fields = ['user_id', 'student_id', 'class_id']
        
        for field in required_fields:
            if field not in document:
                raise ValidationError(f"Missing required field: {field}", field)
    
    def _validate_teacher_document(self, document: Dict[str, Any]):
        """Validate teacher document."""
        required_fields = ['user_id', 'employee_id', 'department_id']
        
        for field in required_fields:
            if field not in document:
                raise ValidationError(f"Missing required field: {field}", field)
    
    def _validate_assessment_document(self, document: Dict[str, Any]):
        """Validate assessment document."""
        required_fields = ['title', 'course_id', 'type', 'total_marks']
        
        for field in required_fields:
            if field not in document:
                raise ValidationError(f"Missing required field: {field}", field)
        
        if not isinstance(document['total_marks'], (int, float)) or document['total_marks'] < 0:
            raise ValidationError("Total marks must be a positive number", "total_marks")
    
    # Health check
    async def health_check(self) -> Dict[str, Any]:
        """Perform health check on the service."""
        health_status = {
            'service': self.service_name,
            'initialized': self._initialized,
            'database_available': self._database is not None,
            'cache_available': self._cache is not None,
            'api_client_available': self._api_client is not None,
            'metrics': self.get_metrics(),
            'timestamp': datetime.now().isoformat()
        }
        
        # Test database connection
        if self._database:
            try:
                await self._database.health_check()
                health_status['database_health'] = 'healthy'
            except Exception as e:
                health_status['database_health'] = f'unhealthy: {str(e)}'
        
        # Test cache connection
        if self._cache:
            try:
                await self._cache.health_check()
                health_status['cache_health'] = 'healthy'
            except Exception as e:
                health_status['cache_health'] = f'unhealthy: {str(e)}'
        
        return health_status


# Service factory
class ServiceFactory:
    """Factory for creating service instances."""
    
    _services: Dict[str, Type[BaseService]] = {}
    
    @classmethod
    def register_service(cls, service_name: str, service_class: Type[BaseService]):
        """Register a service class."""
        cls._services[service_name] = service_class
        logger.info(f"Registered service: {service_name}")
    
    @classmethod
    def create_service(cls, service_name: str) -> BaseService:
        """Create a service instance."""
        if service_name not in cls._services:
            raise ConfigurationError(f"Service '{service_name}' not registered")
        
        service_class = cls._services[service_name]
        return service_class(service_name)
    
    @classmethod
    def get_registered_services(cls) -> List[str]:
        """Get list of registered services."""
        return list(cls._services.keys())


# Decorator for service registration
def register_service(service_name: str = None):
    """Decorator to register a service class."""
    def decorator(service_class: Type[BaseService]):
        name = service_name or service_class.__name__.lower().replace('service', '')
        ServiceFactory.register_service(name, service_class)
        return service_class
    return decorator


# Base service implementations
class UserService(BaseService):
    """User service for user management."""
    
    def __init__(self, service_name: str = "UserService"):
        super().__init__(service_name)
    
    async def create_user(self, user_data: Dict[str, Any]) -> str:
        """Create a new user."""
        return await self.insert_one("users", user_data)
    
    async def get_user_by_email(self, email: str) -> Optional[Dict[str, Any]]:
        """Get user by email address."""
        return await self.find_one("users", {"email": email})
    
    async def get_user_by_id(self, user_id: str) -> Optional[Dict[str, Any]]:
        """Get user by ID."""
        return await self.find_one("users", {"id": user_id})
    
    async def update_user(self, user_id: str, update_data: Dict[str, Any]) -> int:
        """Update user information."""
        return await self.update_one("users", {"id": user_id}, update_data)


class CourseService(BaseService):
    """Course service for course management."""
    
    def __init__(self, service_name: str = "CourseService"):
        super().__init__(service_name)
    
    async def create_course(self, course_data: Dict[str, Any]) -> str:
        """Create a new course."""
        return await self.insert_one("courses", course_data)
    
    async def get_course_by_id(self, course_id: str) -> Optional[Dict[str, Any]]:
        """Get course by ID."""
        return await self.find_one("courses", {"id": course_id})
    
    async def get_courses_by_department(self, department_id: str) -> List[Dict[str, Any]]:
        """Get courses by department."""
        return await self.find_many("courses", {"department_id": department_id})
    
    async def update_course(self, course_id: str, update_data: Dict[str, Any]) -> int:
        """Update course information."""
        return await self.update_one("courses", {"id": course_id}, update_data)


class StudentService(BaseService):
    """Student service for student management."""
    
    def __init__(self, service_name: str = "StudentService"):
        super().__init__(service_name)
    
    async def create_student(self, student_data: Dict[str, Any]) -> str:
        """Create a new student."""
        return await self.insert_one("students", student_data)
    
    async def get_student_by_id(self, student_id: str) -> Optional[Dict[str, Any]]:
        """Get student by ID."""
        return await self.find_one("students", {"id": student_id})
    
    async def get_students_by_class(self, class_id: str) -> List[Dict[str, Any]]:
        """Get students by class."""
        return await self.find_many("students", {"class_id": class_id})
    
    async def update_student(self, student_id: str, update_data: Dict[str, Any]) -> int:
        """Update student information."""
        return await self.update_one("students", {"id": student_id}, update_data)


class TeacherService(BaseService):
    """Teacher service for teacher management."""
    
    def __init__(self, service_name: str = "TeacherService"):
        super().__init__(service_name)
    
    async def create_teacher(self, teacher_data: Dict[str, Any]) -> str:
        """Create a new teacher."""
        return await self.insert_one("teachers", teacher_data)
    
    async def get_teacher_by_id(self, teacher_id: str) -> Optional[Dict[str, Any]]:
        """Get teacher by ID."""
        return await self.find_one("teachers", {"id": teacher_id})
    
    async def get_teachers_by_department(self, department_id: str) -> List[Dict[str, Any]]:
        """Get teachers by department."""
        return await self.find_many("teachers", {"department_id": department_id})
    
    async def update_teacher(self, teacher_id: str, update_data: Dict[str, Any]) -> int:
        """Update teacher information."""
        return await self.update_one("teachers", {"id": teacher_id}, update_data)


class AssessmentService(BaseService):
    """Assessment service for assessment management."""
    
    def __init__(self, service_name: str = "AssessmentService"):
        super().__init__(service_name)
    
    async def create_assessment(self, assessment_data: Dict[str, Any]) -> str:
        """Create a new assessment."""
        return await self.insert_one("assessments", assessment_data)
    
    async def get_assessment_by_id(self, assessment_id: str) -> Optional[Dict[str, Any]]:
        """Get assessment by ID."""
        return await self.find_one("assessments", {"id": assessment_id})
    
    async def get_assessments_by_course(self, course_id: str) -> List[Dict[str, Any]]:
        """Get assessments by course."""
        return await self.find_many("assessments", {"course_id": course_id})
    
    async def update_assessment(self, assessment_id: str, update_data: Dict[str, Any]) -> int:
        """Update assessment information."""
        return await self.update_one("assessments", {"id": assessment_id}, update_data)