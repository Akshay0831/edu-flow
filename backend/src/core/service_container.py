"""
Service container and dependency injection system.

This module provides:
- Dependency injection container
- Service registration and resolution
- Configuration management
- Service lifecycle management
- Interceptor support
- Service health monitoring
"""

import asyncio
import logging
from typing import Dict, Any, Type, Callable, Optional, List, Union, TypeVar
from dataclasses import dataclass, field
from contextlib import asynccontextmanager
from functools import wraps
import importlib
import inspect

# from .api_service import APIClient, APIService  # Circular import issue
from enum import Enum

from src.core.exceptions import ConfigurationError, ServiceNotFoundError
from src.core.logging import get_logger
from src.core.database_abstraction import DatabaseManager, DatabaseConfig, DatabaseType, create_database_manager
from src.core.cache_abstraction import CacheManager, CacheConfig, CacheBackend, create_cache_manager

logger = get_logger(__name__)

T = TypeVar('T')


class ServiceLifetime(Enum):
    """Service lifetime options."""
    TRANSIENT = "transient"  # New instance each time
    SCOPED = "scoped"      # Instance per scope
    SINGLETON = "singleton"  # Single instance for the entire application


@dataclass
class ServiceDescriptor:
    """Service descriptor for registration."""
    service_type: Type
    implementation: Type
    lifetime: ServiceLifetime
    factory: Optional[Callable] = None
    dependencies: List[str] = field(default_factory=list)
    decorators: List[Callable] = field(default_factory=list)
    config: Dict[str, Any] = field(default_factory=dict)


@dataclass
class ServiceInstance:
    """Service instance with metadata."""
    instance: Any
    descriptor: ServiceDescriptor
    created_at: float
    last_used: float
    usage_count: int = 0


class ServiceContainer:
    """Service container for dependency injection."""
    
    def __init__(self):
        self._services: Dict[str, ServiceDescriptor] = {}
        self._instances: Dict[str, ServiceInstance] = {}
        self._scoped_instances: Dict[str, Dict[str, ServiceInstance]] = {}
        self._singletons: Dict[str, ServiceInstance] = {}
        self._scopes: Dict[str, str] = {}
        self._current_scope: Optional[str] = None
        self._initialized = False
        
        # Built-in services
        self._register_builtin_services()
    
    def _register_builtin_services(self):
        """Register built-in services."""
        self.register_singleton('config', self)
        self.register_singleton('logger', get_logger(__name__))
    
    def register_transient(self, name: str, service_type: Type, implementation: Type = None, 
                         dependencies: List[str] = None, decorators: List[Callable] = None,
                         config: Dict[str, Any] = None):
        """Register a transient service."""
        service_impl = implementation or service_type
        self._services[name] = ServiceDescriptor(
            service_type=service_type,
            implementation=service_impl,
            lifetime=ServiceLifetime.TRANSIENT,
            dependencies=dependencies or [],
            decorators=decorators or [],
            config=config or {}
        )
        logger.debug(f"Registered transient service: {name}")
    
    def register_scoped(self, name: str, service_type: Type, implementation: Type = None,
                       dependencies: List[str] = None, decorators: List[Callable] = None,
                       config: Dict[str, Any] = None):
        """Register a scoped service."""
        service_impl = implementation or service_type
        self._services[name] = ServiceDescriptor(
            service_type=service_type,
            implementation=service_impl,
            lifetime=ServiceLifetime.SCOPED,
            dependencies=dependencies or [],
            decorators=decorators or [],
            config=config or {}
        )
        logger.debug(f"Registered scoped service: {name}")
    
    def register_singleton(self, name: str, service_type: Type, implementation: Type = None,
                         factory: Callable = None, dependencies: List[str] = None,
                         decorators: List[Callable] = None, config: Dict[str, Any] = None):
        """Register a singleton service."""
        service_impl = implementation or service_type
        self._services[name] = ServiceDescriptor(
            service_type=service_type,
            implementation=service_impl,
            lifetime=ServiceLifetime.SINGLETON,
            factory=factory,
            dependencies=dependencies or [],
            decorators=decorators or [],
            config=config or {}
        )
        logger.debug(f"Registered singleton service: {name}")
    
    def register_instance(self, name: str, instance: Any, service_type: Type = None):
        """Register a pre-created service instance."""
        service_type = service_type or type(instance)
        descriptor = ServiceDescriptor(
            service_type=service_type,
            implementation=type(instance),
            lifetime=ServiceLifetime.SINGLETON
        )
        
        service_instance = ServiceInstance(
            instance=instance,
            descriptor=descriptor,
            created_at=asyncio.get_event_loop().time(),
            last_used=asyncio.get_event_loop().time()
        )
        
        self._instances[name] = service_instance
        logger.debug(f"Registered service instance: {name}")
    
    def register_factory(self, name: str, factory: Callable) -> None:
        """Register a factory for creating services."""
        self._services[name] = ServiceDescriptor(
            service_type=object,
            implementation=lambda: factory(),
            lifetime=ServiceLifetime.TRANSIENT,
            dependencies=[],
            decorators=[],
            config={}
        )
        logger.debug(f"Registered factory: {name}")
    
    def create_scope(self, scope_id: str = None) -> str:
        """Create a new scope."""
        if scope_id is None:
            scope_id = f"scope_{asyncio.get_event_loop().time()}"
        
        self._scopes[scope_id] = scope_id
        self._scoped_instances[scope_id] = {}
        self._current_scope = scope_id
        
        logger.debug(f"Created scope: {scope_id}")
        return scope_id
    
    def end_scope(self, scope_id: str):
        """End a scope and clean up scoped instances."""
        if scope_id in self._scoped_instances:
            del self._scoped_instances[scope_id]
        
        if scope_id in self._scopes:
            del self._scopes[scope_id]
        
        logger.debug(f"Ended scope: {scope_id}")
    
    def get_scope(self) -> str:
        """Get the current scope."""
        if self._current_scope:
            return self._current_scope
        
        # Create default scope
        return self.create_scope()
    
    def get_service(self, name: str) -> Any:
        """Get a service instance (synchronous version of resolve)."""
        return self._instances.get(name)
    
    async def resolve(self, name: str) -> Any:
        """Resolve a service by name."""
        if name not in self._services:
            raise ServiceNotFoundError(f"Service '{name}' not found")
        
        descriptor = self._services[name]
        
        # Apply decorators to the implementation
        implementation = descriptor.implementation
        for decorator in descriptor.decorators:
            implementation = decorator(implementation)
        
        # Resolve dependencies
        dependencies = await self._resolve_dependencies(descriptor)
        
        # Create instance based on lifetime
        if descriptor.lifetime == ServiceLifetime.TRANSIENT:
            return await self._create_instance(implementation, dependencies)
        
        elif descriptor.lifetime == ServiceLifetime.SCOPED:
            return await self._get_scoped_instance(name, implementation, dependencies)
        
        elif descriptor.lifetime == ServiceLifetime.SINGLETON:
            return await self._get_singleton_instance(name, implementation, dependencies, descriptor.factory)
        
        else:
            raise ConfigurationError(f"Unknown service lifetime: {descriptor.lifetime}")
    
    async def _resolve_dependencies(self, descriptor: ServiceDescriptor) -> Dict[str, Any]:
        """Resolve service dependencies."""
        dependencies = {}
        
        for dep_name in descriptor.dependencies:
            dependencies[dep_name] = await self.resolve(dep_name)
        
        return dependencies
    
    async def _create_instance(self, implementation: Type, dependencies: Dict[str, Any]) -> Any:
        """Create a new instance of the service."""
        try:
            # Check if implementation has async __init__
            if inspect.iscoroutinefunction(implementation.__init__):
                return await implementation(**dependencies)
            else:
                return implementation(**dependencies)
        except Exception as e:
            logger.error(f"Failed to create service instance: {e}")
            raise
    
    async def _get_scoped_instance(self, name: str, implementation: Type, 
                                 dependencies: Dict[str, Any]) -> Any:
        """Get or create a scoped instance."""
        scope = self.get_scope()
        
        if scope not in self._scoped_instances:
            self._scoped_instances[scope] = {}
        
        if name in self._scoped_instances[scope]:
            instance = self._scoped_instances[scope][name]
            instance.usage_count += 1
            instance.last_used = asyncio.get_event_loop().time()
            return instance.instance
        
        instance = await self._create_instance(implementation, dependencies)
        service_instance = ServiceInstance(
            instance=instance,
            descriptor=self._services[name],
            created_at=asyncio.get_event_loop().time(),
            last_used=asyncio.get_event_loop().time(),
            usage_count=1
        )
        
        self._scoped_instances[scope][name] = service_instance
        return instance
    
    async def _get_singleton_instance(self, name: str, implementation: Type,
                                   dependencies: Dict[str, Any], factory: Callable = None) -> Any:
        """Get or create a singleton instance."""
        if name in self._singletons:
            instance = self._singletons[name]
            instance.usage_count += 1
            instance.last_used = asyncio.get_event_loop().time()
            return instance.instance
        
        if factory:
            instance = await factory(**dependencies)
        else:
            instance = await self._create_instance(implementation, dependencies)
        
        service_instance = ServiceInstance(
            instance=instance,
            descriptor=self._services[name],
            created_at=asyncio.get_event_loop().time(),
            last_used=asyncio.get_event_loop().time(),
            usage_count=1
        )
        
        self._singletons[name] = service_instance
        return instance
    
    def get_service_info(self, name: str) -> Dict[str, Any]:
        """Get information about a service."""
        if name not in self._services:
            raise ServiceNotFoundError(f"Service '{name}' not found")
        
        descriptor = self._services[name]
        
        info = {
            'name': name,
            'service_type': str(descriptor.service_type),
            'implementation': str(descriptor.implementation),
            'lifetime': descriptor.lifetime.value,
            'dependencies': descriptor.dependencies,
            'decorators': [str(d) for d in descriptor.decorators],
            'config': descriptor.config
        }
        
        # Add instance information if exists
        if name in self._instances:
            instance = self._instances[name]
            info['instance'] = {
                'type': str(type(instance.instance)),
                'created_at': instance.created_at,
                'last_used': instance.last_used,
                'usage_count': instance.usage_count
            }
        
        return info
    
    def get_all_services(self) -> Dict[str, Dict[str, Any]]:
        """Get information about all services."""
        return {name: self.get_service_info(name) for name in self._services}
    
    def remove_service(self, name: str):
        """Remove a service from the container."""
        if name in self._services:
            del self._services[name]
            logger.debug(f"Removed service: {name}")
        
        # Clean up instances
        if name in self._instances:
            del self._instances[name]
        
        if name in self._singletons:
            del self._singletons[name]
        
        # Clean up scoped instances
        for scope_instances in self._scoped_instances.values():
            if name in scope_instances:
                del scope_instances[name]
    
    async def dispose(self):
        """Dispose all services and clean up resources."""
        # End all scopes
        for scope_id in list(self._scopes.keys()):
            self.end_scope(scope_id)
        
        # Clear all instances
        self._instances.clear()
        self._singletons.clear()
        self._scoped_instances.clear()
        
        logger.info("Service container disposed")
    
    async def health_check(self) -> Dict[str, Any]:
        """Perform health check on all services."""
        health_status = {
            'total_services': len(self._services),
            'singleton_instances': len(self._singletons),
            'scoped_instances': sum(len(instances) for instances in self._scoped_instances.values()),
            'scopes': len(self._scopes),
            'services': {}
        }
        
        for name in self._services:
            try:
                # Try to resolve the service to check if it's working
                await self.resolve(name)
                health_status['services'][name] = 'healthy'
            except Exception as e:
                health_status['services'][name] = f'error: {str(e)}'
        
        return health_status


# Global service container instance
_service_container = None


def get_service_container() -> ServiceContainer:
    """Get the global service container instance."""
    global _service_container
    if _service_container is None:
        _service_container = ServiceContainer()
    return _service_container


def initialize_service_container(config: Dict[str, Any] = None):
    """Initialize the global service container with configuration."""
    global _service_container
    _service_container = ServiceContainer()
    
    # Register built-in services with configuration
    if config:
        _service_container.register_singleton('app_config', config)
    
    return _service_container


# Decorators for service registration
def inject(service_name: str = None):
    """Decorator to inject a service into a class."""
    def decorator(cls):
        service_name = service_name or cls.__name__.lower()
        container = get_service_container()
        container.register_transient(service_name, cls, cls)
        return cls
    return decorator


def inject_singleton(service_name: str = None):
    """Decorator to inject a service as a singleton."""
    def decorator(cls):
        service_name = service_name or cls.__name__.lower()
        container = get_service_container()
        container.register_singleton(service_name, cls, cls)
        return cls
    return decorator


def scoped(service_name: str = None):
    """Decorator to inject a service as scoped."""
    def decorator(cls):
        service_name = service_name or cls.__name__.lower()
        container = get_service_container()
        container.register_scoped(service_name, cls, cls)
        return cls
    return decorator


# Context manager for scoped services
@asynccontextmanager
async def service_scope(scope_id: str = None):
    """Context manager for creating a service scope."""
    container = get_service_container()
    old_scope = container._current_scope
    
    try:
        container.create_scope(scope_id)
        yield container
    finally:
        if old_scope:
            container._current_scope = old_scope
        else:
            container._current_scope = None


# Convenience functions for service resolution
async def resolve_service(name: str) -> Any:
    """Resolve a service by name."""
    container = get_service_container()
    return await container.resolve(name)


def get_service(name: str) -> Any:
    """Get a service by name (synchronous)."""
    container = get_service_container()
    return container._instances.get(name)


# Service health check
async def check_service_health() -> Dict[str, Any]:
    """Check health of all registered services."""
    container = get_service_container()
    return await container.health_check()


# Service configuration helper
async def configure_services(config: Dict[str, Any]):
    """Configure services with the given configuration."""
    container = get_service_container()
    
    # Configure database
    if 'database' in config:
        db_config = config['database']
        db_type = DatabaseType(db_config.get('type', 'sqlite'))
        db_config_obj = DatabaseConfig(
            db_type=db_type,
            host=db_config.get('host', 'localhost'),
            port=db_config.get('port', 5432),
            database=db_config.get('database', 'edu_flow'),
            username=db_config.get('username', 'user'),
            password=db_config.get('password', 'password'),
            **db_config.get('options', {})
        )
        
        # Initialize database manager first
        db_manager = await create_database_manager(db_config_obj)
        container.register_instance('database_manager', db_manager, DatabaseManager)
        container.register_singleton('database_config', DatabaseConfig, lambda: db_config_obj)
    
    # Configure cache
    if 'cache' in config:
        cache_config = config['cache']
        cache_backend = CacheBackend(cache_config.get('backend', 'memory'))
        cache_config_obj = CacheConfig(
            backend=cache_backend,
            host=cache_config.get('host', 'localhost'),
            port=cache_config.get('port', 6379),
            database=cache_config.get('database', '0'),
            password=cache_config.get('password', ''),
            ttl=cache_config.get('ttl', 3600),
            **cache_config.get('options', {})
        )
        
        # Initialize cache manager first
        cache_manager = await create_cache_manager(cache_config_obj)
        container.register_instance('cache_manager', cache_manager, CacheManager)
        container.register_singleton('cache_config', CacheConfig, lambda: cache_config_obj)
    
    # Configure API services
    if 'api' in config:
        api_config = config['api']
        
        # Register API configuration
        container.register_singleton('api_client_config', dict, api_config)
        
        # Register API services (will be initialized when first accessed)
        container.register_factory('api_client', lambda: APIClient(
            base_url=api_config.get('base_url', ''),
            timeout=api_config.get('timeout', 30),
            max_concurrent_requests=api_config.get('max_concurrent_requests', 10)
        ))
        container.register_factory('api_service', lambda: APIService(
            container.resolve('api_client')
        ))
        
        # Register common API services
        _api_service = None
        
        def register_database_service(base_url: str, **kwargs):
            """Register database service."""
            if _api_service:
                _api_service.register_service('database', base_url, **kwargs)
        
        def register_auth_service(base_url: str, **kwargs):
            """Register authentication service."""
            if _api_service:
                _api_service.register_service('auth', base_url, **kwargs)
        
        def register_ai_service(base_url: str, **kwargs):
            """Register AI service."""
            if _api_service:
                _api_service.register_service('ai', base_url, **kwargs)
        
        def register_notification_service(base_url: str, **kwargs):
            """Register notification service."""
            if _api_service:
                _api_service.register_service('notification', base_url, **kwargs)