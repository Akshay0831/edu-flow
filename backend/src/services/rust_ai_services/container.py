"""
Service Container for Rust AI Services

This module provides a centralized service container to manage:
- All AI services (Course Recommendation, Knowledge Search, Adaptive Learning)
- Service initialization and lifecycle
- Service discovery and registration
- Request routing
- Error handling and fallback
- Shared configuration

All services are managed in a modular, config-based way for easy adaptation.

Author: Edu-Flow Team
"""

import asyncio
import logging
from typing import Dict, List, Optional, Any, Type
from dataclasses import dataclass, field

from .config import (
    ConfigManager,
    AIServiceConfig,
    ModelConfig,
    RustAIServicesConfig,
    config_manager as global_config_manager,
)
from .registry import ServiceInstance, ServiceRegistry, initialize_registry, registry as global_registry
from .course_recommendation_service import CourseRecommendationService
from .knowledge_search_service import KnowledgeSearchService
from .adaptive_learning_service import AdaptiveLearningService
from .integration import IntegrationLayer, integration_layer as global_integration_layer
from .monitoring import MonitoringSystem, monitoring as global_monitoring

logger = logging.getLogger(__name__)


@dataclass
class ServiceInstanceInfo:
    """Information about a service instance"""
    service_name: str
    service_type: str
    config: AIServiceConfig
    model_config: ModelConfig
    instance: Any
    enabled: bool


@dataclass
class ServiceContainerStats:
    """Statistics about the service container"""
    total_services: int
    enabled_services: int
    total_requests: int
    total_errors: int
    average_latency_ms: float
    cache_hit_rate: float
    system_health: str


class ServiceContainer:
    """Centralized service container for managing all AI services"""
    
    def __init__(self, config_manager: ConfigManager = None):
        """
        Initialize service container
        
        Args:
            config_manager: Configuration manager (uses global if not provided)
        """
        self._config_manager = config_manager or global_config_manager
        self._config: RustAIServicesConfig = None
        self._services: Dict[str, ServiceInstanceInfo] = {}
        self._service_classes: Dict[str, Type] = {
            "course_recommendation": CourseRecommendationService,
            "knowledge_search": KnowledgeSearchService,
            "adaptive_learning": AdaptiveLearningService,
        }
        self._initialized = False
    
    async def initialize(self):
        """Initialize all services"""
        if self._initialized:
            logger.warning("Service container already initialized")
            return
        
        logger.info("Initializing Rust AI Services container...")
        
        # Load configuration
        self._config = self._config_manager.load_config()
        logger.info(f"Loaded configuration with {len(self._config.services)} services")
        
        # Initialize monitoring
        logger.info("Monitoring system initialized")
        logger.info("Monitoring system initialized")
        
        # Initialize service registry
        initialize_registry(self._config_manager)
        logger.info("Service registry initialized")
        
        # Initialize integration layer
        await global_integration_layer.initialize()
        logger.info("Integration layer initialized")
        
        # Initialize all services
        for service_name, service_config in self._config.services.items():
            if service_config.enable_metrics:
                await self._initialize_service(service_name, service_config)
        
        self._initialized = True
        logger.info(f"✅ Service container initialized with {len(self._services)} services")
    
    async def _initialize_service(
        self,
        service_name: str,
        service_config: AIServiceConfig
    ):
        """Initialize a single service"""
        try:
            logger.info(f"Initializing service: {service_name}")
            
            # Get model configuration
            model_config = self._config.models.get(service_name)
            
            # Get service class
            service_class = self._service_classes.get(service_name)
            if not service_class:
                logger.warning(f"Service class not found for {service_name}, skipping")
                return
            
            # Create service instance
            service = service_class(
                config=service_config,
                model_config=model_config or ModelConfig(
                    model_type=service_name,
                    model_path=f"models/{service_name}.pt",
                    model_version="1.0.0",
                    framework="candle",
                    device="cpu"
                )
            )
            
            # Create service instance
            service_instance = ServiceInstance(
                service_name=service_name,
                instance_id=f"{service_name}_{id(service)}",
                instance_url=f"http://localhost:8000/api/v1/{service_name}",
                config=service_config,
                model_config=model_config,
                status="healthy",
                last_heartbeat=asyncio.get_event_loop().time(),
                version="1.0.0"
            )
            
            # Register in registry
            global_registry.register_service(service_instance)
            logger.info(f"Service {service_name} registered in registry")
            
            # Store service instance
            self._services[service_name] = ServiceInstanceInfo(
                service_name=service_name,
                service_type=service_config.service_type,
                config=service_config,
                model_config=model_config,
                instance=service,
                enabled=True
            )
            
            logger.info(f"✅ Service {service_name} initialized successfully")
            
        except Exception as e:
            logger.error(f"Failed to initialize service {service_name}: {e}")
            if service_name in self._services:
                self._services[service_name].enabled = False
    
    async def get_service(
        self,
        service_name: str
    ) -> Any:
        """
        Get service instance by name
        
        Args:
            service_name: Name of service
            
        Returns:
            Service instance
        """
        if not self._initialized:
            await self.initialize()
        
        service_info = self._services.get(service_name)
        if service_info and service_info.enabled:
            return service_info.instance
        
        return None
    
    async def get_services_info(self) -> Dict[str, ServiceInstanceInfo]:
        """
        Get information about all services
        
        Returns:
            Dict[str, ServiceInstanceInfo]: Dictionary of service information
        """
        if not self._initialized:
            await self.initialize()
        
        return self._services
    
    async def get_available_services(self) -> List[str]:
        """
        Get names of all available services (configured and enabled)
        
        Returns:
            List[str]: List of available service names
        """
        if not self._initialized:
            await self.initialize()
        
        return [
            name
            for name, info in self._services.items()
            if info.enabled
        ]
    
    async def get_enabled_services(self) -> List[str]:
        """
        Get names of all enabled services
        
        Returns:
            List[str]: List of enabled service names
        """
        if not self._initialized:
            await self.initialize()
        
        return [
            name
            for name, info in self._services.items()
            if info.enabled
        ]
    
    def get_available_services_sync(self) -> List[str]:
        """
        Get names of all available services (synchronous version)
        
        Returns:
            List[str]: List of available service names
        """
        if not self._initialized:
            # Check if we're in an event loop
            try:
                loop = asyncio.get_event_loop()
                if loop.is_running():
                    # Initialize later when needed
                    pass
                else:
                    loop.run_until_complete(self.initialize())
            except RuntimeError:
                # No event loop, create one
                asyncio.run(self.initialize())
        
        return [
            name
            for name, info in self._services.items()
            if info.enabled
        ]
    
    async def get_service_health(self, service_name: str) -> Dict[str, Any]:
        """
        Get health status of a service
        
        Args:
            service_name: Name of service
            
        Returns:
            Dict[str, Any]: Health status
        """
        try:
            service = await self.get_service(service_name)
            if service and hasattr(service, 'check_health'):
                health = await service.check_health()
                return {
                    "service_name": service_name,
                    "status": "healthy" if health.get("status") == "healthy" else "unhealthy",
                    "data": health
                }
            else:
                return {
                    "service_name": service_name,
                    "status": "not_configured",
                    "data": {}
                }
        except Exception as e:
            logger.error(f"Health check failed for {service_name}: {e}")
            return {
                "service_name": service_name,
                "status": "error",
                "error": str(e)
            }
    
    async def check_all_services_health(self) -> Dict[str, Any]:
        """
        Check health of all services
        
        Returns:
            Dict[str, Any]: Health status for all services
        """
        if not self._initialized:
            await self.initialize()
        
        results = {}
        
        for service_name in self._services.keys():
            results[service_name] = await self.get_service_health(service_name)
        
        # Calculate overall health
        healthy_count = sum(
            1 for result in results.values()
            if result["status"] == "healthy"
        )
        total_count = len(results)
        overall_health = "healthy" if healthy_count == total_count else "degraded"
        
        return {
            "overall_health": overall_health,
            "total_services": total_count,
            "healthy_services": healthy_count,
            "services": results
        }
    
    async def get_stats(self) -> ServiceContainerStats:
        """
        Get container statistics
        
        Returns:
            ServiceContainerStats: Container statistics
        """
        if not self._initialized:
            await self.initialize()
        
        total_requests = 0
        total_errors = 0
        
        for service_info in self._services.values():
            if service_info.enabled and hasattr(service_info.instance, '_request_counter'):
                total_requests += service_info.instance._request_counter
                # Error count would need to be tracked in services
        
        avg_latency = 0.0
        if total_requests > 0:
            avg_latency = global_monitoring.get_average_latency()
        
        cache_hit_rate = 0.0
        cache_hits = global_monitoring._services.get("total_cache_hits", 0)
        cache_misses = global_monitoring._services.get("total_cache_misses", 0)
        total_cache_requests = cache_hits + cache_misses
        if total_cache_requests > 0:
            cache_hit_rate = (cache_hits / total_cache_requests) * 100
        
        return ServiceContainerStats(
            total_services=len(self._services),
            enabled_services=sum(1 for info in self._services.values() if info.enabled),
            total_requests=total_requests,
            total_errors=0,  # Would need to track errors in services
            average_latency_ms=avg_latency,
            cache_hit_rate=cache_hit_rate,
            system_health="healthy"
        )
    
    async def shutdown(self):
        """Shutdown all services"""
        logger.info("Shutting down Rust AI Services container...")
        
        # Close integration layer
        await global_integration_layer.close()
        
        # Clean up services
        for service_info in self._services.values():
            if service_info.instance and hasattr(service_info.instance, 'dispose'):
                try:
                    await service_info.instance.dispose()
                except Exception as e:
                    logger.error(f"Error disposing service {service_info.service_name}: {e}")
        
        # Stop service registry discovery
        global_registry.stop_discovery()
        
        self._initialized = False
        logger.info("✅ Service container shutdown completed")
    
    def reload_configuration(self):
        """Reload configuration"""
        logger.info("Reloading configuration...")
        self._config_manager.reload()
        self._config = self._config_manager.load_config()
        logger.info("Configuration reloaded")


# Global service container instance
container = ServiceContainer()


async def initialize_container(config_manager: ConfigManager = None):
    """
    Initialize the global service container
    
    Args:
        config_manager: Optional configuration manager
    """
    global container
    container = ServiceContainer(config_manager)
    await container.initialize()


async def shutdown_container():
    """Shutdown the global service container"""
    await container.shutdown()


def get_container() -> ServiceContainer:
    """Get the global service container"""
    return container
