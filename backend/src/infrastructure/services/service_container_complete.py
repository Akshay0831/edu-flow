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
from infrastructure.repositories.student_service import StudentService
from infrastructure.repositories.teacher_service import TeacherService
from infrastructure.repositories.course_service import CourseService
from infrastructure.repositories.class_service import ClassService
from infrastructure.repositories.subject_service import SubjectService
from infrastructure.repositories.department_service import DepartmentService
from infrastructure.repositories.mark_service import MarkService
from infrastructure.repositories.timetable_entry_service import TimetableEntryService
from infrastructure.repositories.grade_service import GradeService
from infrastructure.repositories.laboratory_service import LaboratoryService
from infrastructure.repositories.room_service import RoomService
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
        
        # Register default services
        self._register_default_services()
    
    def _register_default_services(self) -> None:
        """Register default services with the container."""
        # Repository instances (these don't need dependency injection)
        student_repository = StudentRepository()
        teacher_repository = TeacherRepository()
        course_repository = CourseRepository()
        class_repository = ClassRepository()
        subject_repository = SubjectRepository()
        department_repository = DepartmentRepository()
        mark_repository = MarkRepository()
        timetable_entry_repository = TimetableEntryRepository()
        grade_repository = GradeRepository()
        laboratory_repository = LaboratoryRepository()
        room_repository = RoomRepository()
        
        # Student Service
        self.register(
            name='student_service',
            service_class=StudentService,
            dependencies=['student_repository'],
            singleton=True,
            auto_dispose=True
        )
        
        # Teacher Service
        self.register(
            name='teacher_service',
            service_class=TeacherService,
            dependencies=['teacher_repository'],
            singleton=True,
            auto_dispose=True
        )
        
        # Course Service
        self.register(
            name='course_service',
            service_class=CourseService,
            dependencies=['course_repository', 'teacher_repository'],
            singleton=True,
            auto_dispose=True
        )
        
        # Class Service
        self.register(
            name='class_service',
            service_class=ClassService,
            dependencies=['class_repository', 'subject_repository', 'teacher_repository'],
            singleton=True,
            auto_dispose=True
        )
        
        # Subject Service
        self.register(
            name='subject_service',
            service_class=SubjectService,
            dependencies=['subject_repository', 'department_repository'],
            singleton=True,
            auto_dispose=True
        )
        
        # Department Service
        self.register(
            name='department_service',
            service_class=DepartmentService,
            dependencies=['department_repository'],
            singleton=True,
            auto_dispose=True
        )
        
        # Mark Service
        self.register(
            name='mark_service',
            service_class=MarkService,
            dependencies=['student_repository', 'course_repository', 'mark_repository'],
            singleton=True,
            auto_dispose=True
        )
        
        # Timetable Entry Service
        self.register(
            name='timetable_entry_service',
            service_class=TimetableEntryService,
            dependencies=['timetable_entry_repository', 'class_repository'],
            singleton=True,
            auto_dispose=True
        )
        
        # Grade Service
        self.register(
            name='grade_service',
            service_class=GradeService,
            dependencies=['grade_repository', 'student_repository'],
            singleton=True,
            auto_dispose=True
        )
        
        # Laboratory Service
        self.register(
            name='laboratory_service',
            service_class=LaboratoryService,
            dependencies=['laboratory_repository', 'room_repository'],
            singleton=True,
            auto_dispose=True
        )
        
        # Room Service
        self.register(
            name='room_service',
            service_class=RoomService,
            dependencies=['room_repository'],
            singleton=True,
            auto_dispose=True
        )
    
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
        
        self._disposables.append(weakref.ref(service, dispose_callback))
    
    def get_service_info(self, name: str) -> Dict[str, Any]:
        """Get detailed information about a service."""
        if name not in self._services:
            raise KeyError(f"Service '{name}' not registered")
        
        info = self._services[name].copy()
        info['instance_exists'] = name in self._instances
        info['dependencies_resolved'] = all(
            dep in self._instances for dep in info['dependencies']
        )
        
        return info