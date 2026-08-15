"""
Rust AI Services Package

This package provides comprehensive AI services for Edu-Flow:
- Course Recommendations
- Knowledge Search
- Adaptive Learning
- Performance Prediction
- Service Registry
- Configuration Management
- Integration Layer
- Monitoring and Observability

All services are modular, config-based, and easily adaptable.

Author: Edu-Flow Team
"""

from .config import (
    ConfigManager,
    DatabaseConfig,
    CacheConfig,
    ModelConfig,
    AIServiceConfig,
    ServiceRegistryConfig,
    RustAIServicesConfig,
    config_manager,
)

from .registry import (
    ServiceInstance,
    ServiceStatus,
    ServiceRegistry,
    initialize_registry,
    registry,
)

from .course_recommendation_service import (
    CourseRecommendationService,
    StudentProfile,
    CourseRecommendation,
    CourseRecommendationsResult,
)

from .knowledge_search_service import (
    KnowledgeSearchService,
    SearchQuery,
    SearchResult,
    SearchResults,
)

from .adaptive_learning_service import (
    AdaptiveLearningService,
    LearningSession,
    LearningProgress,
    AdaptiveContent,
    AdaptiveSessionResult,
)

from .integration import (
    IntegrationLayer,
    ServiceRequest,
    ServiceResponse,
    integration_layer,
)

from .monitoring import (
    MonitoringSystem,
    ServiceMetrics,
    monitoring,
    track_service_request,
)

from .container import (
    ServiceContainer,
    ServiceInstanceInfo,
    ServiceContainerStats,
    initialize_container,
    shutdown_container,
    get_container,
)

__version__ = "1.0.0"

__all__ = [
    # Configuration
    "ConfigManager",
    "DatabaseConfig",
    "CacheConfig",
    "ModelConfig",
    "AIServiceConfig",
    "ServiceRegistryConfig",
    "RustAIServicesConfig",
    "config_manager",
    
    # Service Registry
    "ServiceInstance",
    "ServiceStatus",
    "ServiceRegistry",
    "initialize_registry",
    "registry",
    
    # Course Recommendation Service
    "CourseRecommendationService",
    "StudentProfile",
    "CourseRecommendation",
    "CourseRecommendationsResult",
    
    # Knowledge Search Service
    "KnowledgeSearchService",
    "SearchQuery",
    "SearchResult",
    "SearchResults",
    
    # Adaptive Learning Service
    "AdaptiveLearningService",
    "LearningSession",
    "LearningProgress",
    "AdaptiveContent",
    "AdaptiveSessionResult",
    
    # Integration Layer
    "IntegrationLayer",
    "ServiceRequest",
    "ServiceResponse",
    "integration_layer",
    
    # Monitoring
    "MonitoringSystem",
    "ServiceMetrics",
    "monitoring",
    "track_service_request",
    
    # Service Container
    "ServiceContainer",
    "ServiceInstanceInfo",
    "ServiceContainerStats",
    "initialize_container",
    "shutdown_container",
    "get_container",
]

__all__