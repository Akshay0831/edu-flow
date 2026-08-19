"""
Service Container

This module provides a dependency injection container for managing service instances.
It supports service registration, retrieval, disposal, and dependency resolution.

Author: Edu-Flow Team
"""

from typing import Dict, Any, Optional, Type, List
from abc import ABC, abstractmethod
import asyncio
import weakref

from core.logging import get_logger
from infrastructure.repositories.base_service import BaseService
from infrastructure.repositories.student_repository import StudentRepository
from infrastructure.repositories.teacher_repository import TeacherRepository
from infrastructure.repositories.course_repository import CourseRepository
from infrastructure.repositories.class_repository import ClassRepository
from infrastructure.repositories.subject_repository import SubjectRepository
from infrastructure.repositories.department_repository import DepartmentRepository
from infrastructure.repositories.mark_repository import MarkRepository
from infrastructure.repositories.timetable_entry_repository import TimetableEntryRepository
from infrastructure.repositories.grade_repository import GradeRepository
from infrastructure.repositories.laboratory_repository import LaboratoryRepository
from infrastructure.repositories.room_repository import RoomRepository

logger = get_logger(__name__)


class ServiceContainer:
    """
    Service container for managing service instances with dependency injection.
    
    Features:
    - Service registration and retrieval
    - Automatic dependency resolution
    - Service lifecycle management
    - Instance caching
    - Circular dependency detection
    - Type-safe service access
    """
    
    def __init__(self):
        self._services: Dict[str, Dict[str, Any]] = {}
        self._instances: Dict[str, BaseService] = {}
        self._circular_detection: Dict[str, bool] = {}
        self._disposables: List[weakref.ref] = []
        self._is_disposing = False
    
    def register(self, name: str, service_class: Type[BaseService], 
                dependencies: List[str] = None, singleton: bool = True,
                auto_dispose: bool = True) -> None:
        """
        Register a service with the container.
        
        Args:
            name: Service identifier name
            service_class: Service class to instantiate
            dependencies: List of dependency service names
            singleton: Whether to create singleton instance
            auto_dispose: Whether to auto-dispose service
        """
        try:
            # Validate service class
            if not issubclass(service_class, BaseService):
                raise ValueError(f"Service {name} must inherit from BaseService")
            
            # Store service metadata
            self._services[name] = {
                'service_class': service_class,
                'dependencies': dependencies or [],
                'singleton': singleton,
                'auto_dispose': auto_dispose,
                'registered_at': asyncio.get_event_loop().time()
            }
            
            logger.info(f"Registered service: {name}")
            
        except Exception as e:
            logger.error(f"Failed to register service {name}: {str(e)}")
            raise
    
    def get(self, name: str) -> BaseService:
        """
        Get a service instance by name.
        
        Args:
            name: Service identifier name
            
        Returns:
            Service instance
            
        Raises:
            KeyError: If service not registered
            RuntimeError: If circular dependency detected
        """
        try:
            # Check if service is registered
            if name not in self._services:
                raise KeyError(f"Service '{name}' not registered")
            
            # Check for circular dependency
            if self._circular_detection.get(name, False):
                raise RuntimeError(f"Circular dependency detected for service: {name}")
            
            # Set circular detection flag
            self._circular_detection[name] = True
            
            try:
                # Get or create service instance
                if self._services[name]['singleton'] and name in self._instances:
                    instance = self._instances[name]
                else:
                    instance = await self._create_instance(name)
                
                return instance
                
            finally:
                # Clear circular detection flag
                self._circular_detection[name] = False
                
        except Exception as e:
            logger.error(f"Failed to get service {name}: {str(e)}")
            raise
    
    async def create(self, name: str) -> BaseService:
        """
        Create a new instance of a service (non-singleton only).
        
        Args:
            name: Service identifier name
            
        Returns:
            New service instance
        """
        try:
            # Check if service is registered and supports non-singleton
            if name not in self._services:
                raise KeyError(f"Service '{name}' not registered")
            
            if self._services[name]['singleton']:
                raise RuntimeError(f"Service {name} is configured as singleton")
            
            # Create new instance
            return await self._create_instance(name)
            
        except Exception as e:
            logger.error(f"Failed to create service {name}: {str(e)}")
            raise
    
    def is_registered(self, name: str) -> bool:
        """Check if a service is registered."""
        return name in self._services
    
    def is_singleton(self, name: str) -> bool:
        """Check if a service is configured as singleton."""
        return self._services.get(name, {}).get('singleton', False)
    
    def get_dependencies(self, name: str) -> List[str]:
        """Get service dependencies."""
        return self._services.get(name, {}).get('dependencies', [])
    
    def get_registered_services(self) -> List[str]:
        """Get list of all registered service names."""
        return list(self._services.keys())
    
    async def initialize(self) -> None:
        """Initialize all services in dependency order."""
        try:
            # Create dependency graph
            dependency_graph = self._build_dependency_graph()
            
            # Topological sort to get initialization order
            init_order = self._topological_sort(dependency_graph)
            
            # Initialize services in order
            for service_name in init_order:
                service = self.get(service_name)
                await service.initialize()
                
            logger.info(f"Initialized {len(init_order)} services in dependency order")
            
        except Exception as e:
            logger.error(f"Failed to initialize services: {str(e)}")
            raise
    
    async def dispose(self) -> None:
        """Dispose all services."""
        if self._is_disposing:
            return
            
        self._is_disposing = True
        try:
            # Dispose in reverse dependency order
            dependency_graph = self._build_dependency_graph()
            reverse_order = reversed(self._topological_sort(dependency_graph))
            
            for service_name in reverse_order:
                if service_name in self._instances:
                    service = self._instances[service_name]
                    await service.dispose()
                    # Remove instance
                    del self._instances[service_name]
                    
                    # Clean up circular detection
                    if service_name in self._circular_detection:
                        del self._circular_detection[service_name]
            
            # Clear disposables
            self._disposables.clear()
            
            logger.info("Disposed all services")
            
        except Exception as e:
            logger.error(f"Error during service disposal: {str(e)}")
        finally:
            self._is_disposing = False
    
    def _build_dependency_graph(self) -> Dict[str, List[str]]:
        """Build dependency graph for services."""
        graph = {}
        
        for service_name in self._services:
            dependencies = self.get_dependencies(service_name)
            graph[service_name] = dependencies
        
        return graph
    
    def _topological_sort(self, graph: Dict[str, List[str]]) -> List[str]:
        """Perform topological sort on dependency graph."""
        # Kahn's algorithm for topological sorting
        in_degree = {node: 0 for node in graph}
        
        # Calculate in-degree for each node
        for node in graph:
            for neighbor in graph[node]:
                in_degree[neighbor] += 1
        
        # Initialize queue with nodes having no dependencies
        queue = [node for node in in_degree if in_degree[node] == 0]
        sorted_order = []
        
        while queue:
            node = queue.pop(0)
            sorted_order.append(node)
            
            # Update in-degree for neighbors
            for neighbor in graph[node]:
                in_degree[neighbor] -= 1
                if in_degree[neighbor] == 0:
                    queue.append(neighbor)
        
        # Check for cycles
        if len(sorted_order) != len(graph):
            raise RuntimeError("Circular dependencies detected in service graph")
        
        return sorted_order
    
    async def _create_instance(self, name: str) -> BaseService:
        """Create a new service instance."""
        try:
            service_info = self._services[name]
            service_class = service_info['service_class']
            dependencies = service_info['dependencies']
            
            # Create dependency instances
            dependency_instances = {}
            for dep_name in dependencies:
                dep_instance = self.get(dep_name)
                dependency_instances[dep_name] = dep_instance
            
            # Create service instance
            instance = service_class(**dependency_instances)
            
            # Initialize if not already done
            if not instance.is_initialized():
                await instance.initialize()
            
            # Store instance if singleton
            if service_info['singleton']:
                self._instances[name] = instance
                
                # Register for auto-dispose if needed
                if service_info['auto_dispose']:
                    self._register_disposable(instance)
            
            logger.debug(f"Created instance of service: {name}")
            return instance
            
        except Exception as e:
            logger.error(f"Failed to create instance of service {name}: {str(e)}")
            raise
    
    def _register_disposable(self, service: BaseService) -> None:
        """Register a service for auto-disposal."""
        def dispose_callback():
            if not self._is_disposing:
                asyncio.create_task(service.dispose())
        
        weak_ref = weakref.ref(service, lambda ref: dispose_callback())
        self._disposables.append(weak_ref)
    
    def get_service_info(self, name: str) -> Dict[str, Any]:
        """Get service information."""
        return self._services.get(name, {}).copy()
    
    def has_instance(self, name: str) -> bool:
        """Check if service has an instance created."""
        return name in self._instances
    
    def clear_instances(self) -> None:
        """Clear all service instances without disposal."""
        self._instances.clear()
    
    async def reload_service(self, name: str) -> BaseService:
        """Reload a service instance (destroy and recreate)."""
        try:
            # Check if service is registered
            if name not in self._services:
                raise KeyError(f"Service '{name}' not registered")
            
            # Check if singleton and instance exists
            if self._services[name]['singleton'] and name in self._instances:
                # Remove existing instance
                del self._instances[name]
            
            # Create new instance
            return await self._create_instance(name)
            
        except Exception as e:
            logger.error(f"Failed to reload service {name}: {str(e)}")
            raise
    
    def get_instance_count(self) -> int:
        """Get number of service instances created."""
        return len(self._instances)
    
    def get_service_status(self) -> Dict[str, Dict[str, Any]]:
        """Get status of all registered services."""
        status = {}
        
        for name in self._services:
            service_info = self._services[name].copy()
            service_info['has_instance'] = name in self._instances
            service_info['is_initialized'] = name in self._instances and self._instances[name].is_initialized()
            
            status[name] = service_info
        
        return status


# Global service container instance
_service_container = None


def get_container() -> ServiceContainer:
    """Get the global service container instance."""
    global _service_container
    if _service_container is None:
        _service_container = ServiceContainer()
    return _service_container


def reset_container() -> ServiceContainer:
    """Reset and create a new global service container."""
    global _service_container
    _service_container = ServiceContainer()
    return _service_container


async def initialize_services() -> None:
    """Initialize all registered services."""
    container = get_container()
    await container.initialize()


async def dispose_services() -> None:
    """Dispose all services."""
    container = get_container()
    await container.dispose()


def register_service(name: str, service_class: Type[BaseService], 
                    dependencies: List[str] = None, singleton: bool = True,
                    auto_dispose: bool = True) -> None:
    """Register a service with the global container."""
    container = get_container()
    container.register(name, service_class, dependencies, singleton, auto_dispose)


def get_service(name: str) -> BaseService:
    """Get a service instance from the global container."""
    container = get_container()
    return container.get(name)


def is_service_registered(name: str) -> bool:
    """Check if a service is registered in the global container."""
    container = get_container()
    return container.is_registered(name)


async def create_service(name: str) -> BaseService:
    """Create a new instance of a service from the global container."""
    container = get_container()
    return await container.create(name)


def get_all_services() -> List[str]:
    """Get all registered service names."""
    container = get_container()
    return container.get_registered_services()


async def reload_service(name: str) -> BaseService:
    """Reload a service instance from the global container."""
    container = get_container()
    return await container.reload_service(name)


async def setup_default_services() -> None:
    """Setup and register default services."""
    try:
        logger.info("Setting up default services...")
        
        # Get container
        container = get_container()
        
        # Clear any existing services
        container.clear_instances()
        
        # Register core services
        container.register("student_repository", StudentRepository, [], True, True)
        container.register("teacher_repository", TeacherRepository, [], True, True)
        container.register("course_repository", CourseRepository, [], True, True)
        container.register("class_repository", ClassRepository, [], True, True)
        container.register("subject_repository", SubjectRepository, [], True, True)
        container.register("department_repository", DepartmentRepository, [], True, True)
        container.register("mark_repository", MarkRepository, [], True, True)
        container.register("timetable_entry_repository", TimetableEntryRepository, [], True, True)
        container.register("grade_repository", GradeRepository, [], True, True)
        container.register("laboratory_repository", LaboratoryRepository, [], True, True)
        container.register("room_repository", RoomRepository, [], True, True)
        
        # Register service layer services (will be created after repository layer)
        # These will depend on the repository services
        
        logger.info("Successfully registered default services")
        
    except Exception as e:
        logger.error(f"Failed to setup default services: {str(e)}")
        raise


# Context manager for service container
class ServiceContainerContext:
    """Context manager for service container lifecycle."""
    
    def __init__(self, services: List[str] = None):
        self._services = services or []
        self._container = None
    
    async def __aenter__(self):
        """Enter context: setup services."""
        from infrastructure.services.student_service import StudentService
        from infrastructure.services.teacher_service import TeacherService
        from infrastructure.services.course_service import CourseService
        from infrastructure.services.class_service import ClassService
        from infrastructure.services.subject_service import SubjectService
        from infrastructure.services.department_service import DepartmentService
        from infrastructure.services.mark_service import MarkService
        from infrastructure.services.timetable_entry_service import TimetableEntryService
        from infrastructure.services.grade_service import GradeService
        from infrastructure.services.laboratory_service import LaboratoryService
        from infrastructure.services.room_service import RoomService
        
        # Get container
        container = get_container()
        
        # Register service layer services
        container.register("student_service", StudentService, ["student_repository"], True, True)
        container.register("teacher_service", TeacherService, ["teacher_repository"], True, True)
        container.register("course_service", CourseService, ["course_repository"], True, True)
        container.register("class_service", ClassService, ["class_repository"], True, True)
        container.register("subject_service", SubjectService, ["subject_repository"], True, True)
        container.register("department_service", DepartmentService, ["department_repository"], True, True)
        container.register("mark_service", MarkService, ["mark_repository"], True, True)
        container.register("timetable_entry_service", TimetableEntryService, ["timetable_entry_repository"], True, True)
        container.register("grade_service", GradeService, ["grade_repository"], True, True)
        container.register("laboratory_service", LaboratoryService, ["laboratory_repository"], True, True)
        container.register("room_service", RoomService, ["room_repository"], True, True)
        
        # Initialize all services
        await container.initialize()
        
        self._container = container
        return container
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Exit context: dispose services."""
        if self._container:
            await self._container.dispose()