"""
Service Registry for Rust AI Services

This module provides a centralized service registry for:
- Service discovery and registration
- Service health checking
- Service load balancing
- Service failover and recovery
- Dynamic service configuration

The registry is designed to be modular and easily extensible for different
backend implementations (memory, etcd, zookeeper, consul).

Author: Edu-Flow Team
"""

from typing import Dict, List, Optional, Any, Callable
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
import asyncio
import logging
from .config import AIServiceConfig, ModelConfig

logger = logging.getLogger(__name__)


class ServiceStatus(str, Enum):
    """Service health status"""
    HEALTHY = "healthy"
    UNHEALTHY = "unhealthy"
    UNKNOWN = "unknown"
    DEGRADED = "degraded"


@dataclass
class ServiceInstance:
    """Represents a running service instance"""
    service_name: str
    instance_id: str
    instance_url: str
    config: AIServiceConfig
    model_config: Optional[ModelConfig] = None
    status: ServiceStatus = ServiceStatus.UNKNOWN
    last_heartbeat: datetime = field(default_factory=datetime.now)
    metadata: Dict[str, Any] = field(default_factory=dict)
    version: str = "1.0.0"
    created_at: datetime = field(default_factory=datetime.now)
    health_check_url: str = ""
    
    @property
    def uptime(self) -> timedelta:
        """Calculate uptime duration"""
        return datetime.now() - self.last_heartbeat
    
    @property
    def is_healthy(self) -> bool:
        """Check if service is healthy based on last heartbeat"""
        return self.status == ServiceStatus.HEALTHY
    
    @property
    def is_recent(self) -> bool:
        """Check if service heartbeat is recent (within grace period)"""
        grace_period = timedelta(seconds=30)
        return self.last_heartbeat >= datetime.now() - grace_period


class ServiceRegistry:
    """Centralized service registry for service discovery and management"""
    
    def __init__(self, registry_type: str = "memory"):
        """
        Initialize service registry
        
        Args:
            registry_type: Type of registry implementation
        """
        self.registry_type = registry_type
        self._instances: Dict[str, List[ServiceInstance]] = {}
        self._instance_by_id: Dict[str, ServiceInstance] = {}
        self._listeners: List[Callable] = []
        self._discovery_interval: Optional[asyncio.Task] = None
        self._config_manager = None
    
    def set_config_manager(self, config_manager):
        """Set config manager for loading service configurations"""
        self._config_manager = config_manager
    
    def register_service(self, service_instance: ServiceInstance) -> bool:
        """
        Register a service instance
        
        Args:
            service_instance: Service instance to register
            
        Returns:
            bool: True if registration was successful
        """
        service_name = service_instance.service_name
        
        # Check if instance already exists
        if service_instance.instance_id in self._instance_by_id:
            logger.warning(f"Instance {service_instance.instance_id} already registered")
            return False
        
        # Register instance
        self._instance_by_id[service_instance.instance_id] = service_instance
        
        # Add to service list
        if service_name not in self._instances:
            self._instances[service_name] = []
        
        self._instances[service_name].append(service_instance)
        
        logger.info(f"Service {service_name} instance {service_instance.instance_id} registered")
        
        # Notify listeners
        self._notify_listeners(service_instance, "registered")
        
        return True
    
    def deregister_service(self, instance_id: str) -> bool:
        """
        Deregister a service instance
        
        Args:
            instance_id: ID of service instance to deregister
            
        Returns:
            bool: True if deregistration was successful
        """
        if instance_id not in self._instance_by_id:
            logger.warning(f"Instance {instance_id} not found")
            return False
        
        instance = self._instance_by_id[instance_id]
        service_name = instance.service_name
        
        # Remove from service list
        if service_name in self._instances:
            self._instances[service_name] = [
                inst for inst in self._instances[service_name]
                if inst.instance_id != instance_id
            ]
        
        # Remove from instance map
        del self._instance_by_id[instance_id]
        
        logger.info(f"Service {service_name} instance {instance_id} deregistered")
        
        # Notify listeners
        self._notify_listeners(instance, "deregistered")
        
        return True
    
    def get_service(self, service_name: str) -> Optional[ServiceInstance]:
        """
        Get the first available instance of a service
        
        Args:
            service_name: Name of the service
            
        Returns:
            Optional[ServiceInstance]: Service instance or None if not found
        """
        instances = self._get_available_instances(service_name)
        return instances[0] if instances else None
    
    def get_service_instances(self, service_name: str) -> List[ServiceInstance]:
        """
        Get all instances of a service
        
        Args:
            service_name: Name of the service
            
        Returns:
            List[ServiceInstance]: List of service instances
        """
        return self._get_available_instances(service_name)
    
    def get_all_services(self) -> Dict[str, List[ServiceInstance]]:
        """
        Get all registered services
        
        Returns:
            Dict[str, List[ServiceInstance]]: Dictionary mapping service names to instances
        """
        return {
            name: self._get_available_instances(name)
            for name in self._instances.keys()
        }
    
    def _get_available_instances(self, service_name: str) -> List[ServiceInstance]:
        """
        Get available (healthy and recent) instances of a service
        
        Args:
            service_name: Name of the service
            
        Returns:
            List[ServiceInstance]: List of available service instances
        """
        if service_name not in self._instances:
            return []
        
        now = datetime.now()
        grace_period = timedelta(seconds=30)
        
        return [
            instance for instance in self._instances[service_name]
            if instance.is_healthy and instance.is_recent
        ]
    
    def update_heartbeat(self, instance_id: str, status: ServiceStatus = None) -> bool:
        """
        Update service instance heartbeat
        
        Args:
            instance_id: ID of service instance
            status: Optional new status
            
        Returns:
            bool: True if update was successful
        """
        if instance_id not in self._instance_by_id:
            logger.warning(f"Instance {instance_id} not found for heartbeat update")
            return False
        
        instance = self._instance_by_id[instance_id]
        instance.last_heartbeat = datetime.now()
        
        if status:
            instance.status = status
        
        return True
    
    def check_service_health(self, instance_id: str) -> ServiceStatus:
        """
        Check health of a service instance
        
        Args:
            instance_id: ID of service instance
            
        Returns:
            ServiceStatus: Health status
        """
        if instance_id not in self._instance_by_id:
            return ServiceStatus.UNKNOWN
        
        instance = self._instance_by_id[instance_id]
        
        # Perform health check
        if instance.health_check_url:
            try:
                health_status = self._perform_health_check(instance.health_check_url)
                instance.status = health_status
                instance.last_heartbeat = datetime.now()
            except Exception as e:
                logger.error(f"Health check failed for {instance_id}: {e}")
                instance.status = ServiceStatus.UNHEALTHY
        else:
            # If no health check URL, consider as healthy
            instance.status = ServiceStatus.HEALTHY
        
        return instance.status
    
    def _perform_health_check(self, health_check_url: str) -> ServiceStatus:
        """
        Perform health check on service
        
        Args:
            health_check_url: URL for health check endpoint
            
        Returns:
            ServiceStatus: Health status
        """
        # TODO: Implement actual health check
        # This would typically make an HTTP request to the health endpoint
        return ServiceStatus.HEALTHY
    
    def start_discovery(self):
        """Start periodic service discovery"""
        if self._discovery_interval is None:
            logger.info("Starting service discovery")
            self._discovery_interval = asyncio.create_task(self._discovery_loop())
    
    def stop_discovery(self):
        """Stop periodic service discovery"""
        if self._discovery_interval:
            self._discovery_interval.cancel()
            self._discovery_interval = None
            logger.info("Stopped service discovery")
    
    async def _discovery_loop(self):
        """Periodic service discovery loop"""
        try:
            while True:
                await asyncio.sleep(15)  # Check every 15 seconds
                
                for instance_id in list(self._instance_by_id.keys()):
                    self.check_service_health(instance_id)
                    
                    # Remove stale instances
                    instance = self._instance_by_id[instance_id]
                    if not instance.is_recent:
                        logger.warning(f"Removing stale instance {instance_id}")
                        self.deregister_service(instance_id)
                        
        except asyncio.CancelledError:
            pass
    
    def subscribe(self, callback: Callable):
        """
        Subscribe to service registry events
        
        Args:
            callback: Callback function to call on events
        """
        if callback not in self._listeners:
            self._listeners.append(callback)
    
    def unsubscribe(self, callback: Callable):
        """
        Unsubscribe from service registry events
        
        Args:
            callback: Callback function to remove
        """
        if callback in self._listeners:
            self._listeners.remove(callback)
    
    def _notify_listeners(self, instance: ServiceInstance, event_type: str):
        """
        Notify all listeners of a service event
        
        Args:
            instance: Service instance
            event_type: Type of event
        """
        for callback in self._listeners:
            try:
                callback(instance, event_type)
            except Exception as e:
                logger.error(f"Error in service registry listener: {e}")
    
    def get_stats(self) -> Dict[str, Any]:
        """
        Get registry statistics
        
        Returns:
            Dict[str, Any]: Statistics about the registry
        """
        total_instances = len(self._instance_by_id)
        total_services = len(self._instances)
        healthy_instances = sum(
            1 for instance in self._instance_by_id.values()
            if instance.is_healthy and instance.is_recent
        )
        
        return {
            "total_instances": total_instances,
            "total_services": total_services,
            "healthy_instances": healthy_instances,
            "unhealthy_instances": total_instances - healthy_instances,
            "registry_type": self.registry_type,
        }
    
    def __len__(self) -> int:
        """Get total number of registered instances"""
        return len(self._instance_by_id)
    
    def __contains__(self, service_name: str) -> bool:
        """Check if a service is registered"""
        return service_name in self._instances


# Global registry instance
registry = ServiceRegistry()


def initialize_registry(config_manager=None):
    """
    Initialize the service registry
    
    Args:
        config_manager: Optional config manager instance
    """
    global registry
    registry = ServiceRegistry()
    registry.set_config_manager(config_manager)
    registry.start_discovery()
    logger.info("Service registry initialized")
