"""
Configuration management for Rust AI Services

This module provides centralized configuration management for all AI services:
- Service registry and discovery
- Model configurations
- API endpoint configurations
- Database and cache configurations
- Monitoring and logging configurations

All configurations are loaded from environment variables and configuration files,
making them easily adaptable and modular.

Author: Edu-Flow Team
"""

import os
import json
from typing import Dict, List, Optional, Any
from pathlib import Path
from pydantic import BaseModel, Field, validator, HttpUrl
from functools import lru_cache


class DatabaseConfig(BaseModel):
    """Database connection configuration"""
    database_type: str = Field("postgresql", description="Database type")
    host: str = Field("localhost", description="Database host")
    port: int = Field(5432, description="Database port")
    username: str = Field("postgres", description="Database username")
    password: str = Field(..., description="Database password", env="DB_PASSWORD")
    database: str = Field("edu_flow", description="Database name")
    pool_size: int = Field(10, description="Connection pool size")
    pool_recycle: int = Field(3600, description="Connection recycle time in seconds")
    connection_timeout: int = Field(30, description="Connection timeout in seconds")


class CacheConfig(BaseModel):
    """Cache configuration"""
    backend: str = Field("redis", description="Cache backend")
    host: str = Field("localhost", description="Cache host")
    port: int = Field(6379, description="Cache port")
    database: int = Field(0, description="Cache database number")
    key_prefix: str = Field("edu_flow:", description="Key prefix for all cache keys")
    ttl: int = Field(3600, description="Default TTL in seconds")
    max_memory_size: int = Field(1024 * 1024 * 1024, description="Max memory size in bytes")


class ModelConfig(BaseModel):
    """ML model configuration"""
    model_type: str = Field(..., description="Type of model")
    model_path: str = Field(..., description="Path to model file")
    model_version: str = Field(..., description="Model version")
    framework: str = Field("candle", description="ML framework")
    device: str = Field("cpu", description="Device to use (cpu/cuda)")
    preprocessing: Dict[str, Any] = Field(default_factory=dict, description="Preprocessing configuration")
    postprocessing: Dict[str, Any] = Field(default_factory=dict, description="Postprocessing configuration")
    evaluation_metrics: List[str] = Field(default_factory=list, description="Evaluation metrics to compute")


class AIServiceConfig(BaseModel):
    """AI Service configuration"""
    service_name: str = Field(..., description="Service name")
    service_type: str = Field(..., description="Service type")
    api_endpoint: Optional[str] = Field(None, description="API endpoint URL")
    timeout: int = Field(30, description="Request timeout in seconds")
    retry_attempts: int = Field(3, description="Number of retry attempts")
    retry_delay: int = Field(1, description="Retry delay in seconds")
    rate_limit: Optional[int] = Field(None, description="Rate limit requests per second")
    enable_metrics: bool = Field(True, description="Enable metrics collection")


class MonitoringConfig(BaseModel):
    """Monitoring and observability configuration"""
    enable_metrics: bool = Field(True, description="Enable Prometheus metrics")
    metrics_port: int = Field(9090, description="Metrics server port")
    enable_tracing: bool = Field(True, description="Enable distributed tracing")
    tracing_endpoint: Optional[str] = Field(None, description="Tracing endpoint URL")
    log_level: str = Field("INFO", description="Logging level")


class ServiceRegistryConfig(BaseModel):
    """Service registry configuration"""
    registry_type: str = Field("memory", description="Registry type (memory/etcd/zookeeper)")
    registry_url: Optional[str] = Field(None, description="Registry service URL")
    discovery_interval: int = Field(30, description="Service discovery interval in seconds")
    health_check_interval: int = Field(15, description="Health check interval in seconds")
    grace_period: int = Field(30, description="Grace period before removing service")


class RustAIServicesConfig(BaseModel):
    """Main configuration for Rust AI Services"""
    database: DatabaseConfig
    cache: CacheConfig
    models: Dict[str, ModelConfig]
    services: Dict[str, AIServiceConfig]
    monitoring: MonitoringConfig
    registry: ServiceRegistryConfig
    
    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
    
    @validator('models', 'services', pre=True)
    def validate_models_and_services(cls, v):
        if not v:
            return {}
        return v


class ConfigManager:
    """Centralized configuration manager"""
    
    _instance = None
    _config: Optional[RustAIServicesConfig] = None
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(ConfigManager, cls).__new__(cls)
        return cls._instance
    
    def load_config(self, config_path: Optional[str] = None) -> RustAIServicesConfig:
        """Load configuration from path or default location"""
        if self._config is None:
            config_file = config_path or self._find_config_file()
            
            if config_file:
                # Load from JSON config file
                with open(config_file, 'r', encoding='utf-8') as f:
                    config_data = json.load(f)
                self._config = self._build_config_from_json(config_data)
            else:
                # Load from environment variables with defaults
                self._config = self._load_from_env()
        
        return self._config
    
    def _find_config_file(self) -> Optional[str]:
        """Find configuration file in project"""
        search_paths = [
            "rust_ai_config.json",
            "./rust_ai_config.json",
            "../rust_ai_config.json",
            "../config/rust_ai_config.json",
            "src/services/rust_ai_services/rust_ai_config.json",
            "./src/services/rust_ai_services/rust_ai_config.json",
            os.path.join(os.path.dirname(__file__), "..", "..", "src", "services", "rust_ai_services", "rust_ai_config.json"),
        ]
        
        for path in search_paths:
            if os.path.exists(path):
                return path
        
        return None
    
    def _load_from_env(self) -> RustAIServicesConfig:
        """Load configuration from environment variables"""
        # If we have config_data, use it to build configs
        if hasattr(self, '_config_data') and self._config_data:
            return self._build_config_from_json(self._config_data)
        
        # Fallback: Create basic configs with defaults
        db_config = DatabaseConfig()
        cache_config = CacheConfig()
        monitoring_config = MonitoringConfig()
        registry_config = ServiceRegistryConfig()
        
        # Load service configurations from environment
        services = self._load_services_from_env()
        
        # Load model configurations from environment
        models = self._load_models_from_env()
        
        return RustAIServicesConfig(
            database=db_config,
            cache=cache_config,
            models=models,
            services=services,
            monitoring=monitoring_config,
            registry=registry_config,
        )
    
    def _build_config_from_json(self, config_data: Dict[str, Any]) -> RustAIServicesConfig:
        """Build configuration from JSON data"""
        # Extract nested configs
        db_data = config_data.get('database', {})
        cache_data = config_data.get('cache', {})
        monitoring_data = config_data.get('monitoring', {})
        registry_data = config_data.get('registry', {})
        services_data = config_data.get('services', {})
        models_data = config_data.get('models', {})
        
        # Build config objects from data
        db_config = DatabaseConfig(**db_data)
        cache_config = CacheConfig(**cache_data)
        monitoring_config = MonitoringConfig(**monitoring_data)
        registry_config = ServiceRegistryConfig(**registry_data)
        
        return RustAIServicesConfig(
            database=db_config,
            cache=cache_config,
            models=models_data,
            services=services_data,
            monitoring=monitoring_config,
            registry=registry_config,
        )
    
    def _load_services_from_env(self) -> Dict[str, AIServiceConfig]:
        """Load AI service configurations from environment variables"""
        services = {}
        
        service_names = ["performance_prediction", "course_recommendation", 
                        "knowledge_search", "adaptive_learning"]
        
        for service_name in service_names:
            # Check if service is enabled
            if os.getenv(f"{service_name.upper()}_ENABLED", "false").lower() == "true":
                services[service_name] = AIServiceConfig(
                    service_name=service_name,
                    service_type=service_name.replace("_", "-"),
                    api_endpoint=os.getenv(f"{service_name.upper()}_API_ENDPOINT"),
                    timeout=int(os.getenv(f"{service_name.upper()}_TIMEOUT", "30")),
                    retry_attempts=int(os.getenv(f"{service_name.upper()}_RETRY_ATTEMPTS", "3")),
                    retry_delay=int(os.getenv(f"{service_name.upper()}_RETRY_DELAY", "1")),
                    rate_limit=int(os.getenv(f"{service_name.upper()}_RATE_LIMIT", "100")) if os.getenv(f"{service_name.upper()}_RATE_LIMIT") else None,
                    enable_metrics=os.getenv(f"{service_name.upper()}_ENABLE_METRICS", "true").lower() == "true",
                )
        
        return services
    
    def _load_models_from_env(self) -> Dict[str, ModelConfig]:
        """Load model configurations from environment variables"""
        models = {}
        
        model_names = ["performance_prediction", "course_recommendation", 
                     "knowledge_search", "adaptive_learning"]
        
        for model_name in model_names:
            if os.getenv(f"{model_name.upper()}_ENABLED", "false").lower() == "true":
                models[model_name] = ModelConfig(
                    model_type=os.getenv(f"{model_name.upper()}_MODEL_TYPE", model_name),
                    model_path=os.getenv(f"{model_name.upper()}_MODEL_PATH", f"models/{model_name}.pt"),
                    model_version=os.getenv(f"{model_name.upper()}_VERSION", "1.0.0"),
                    framework=os.getenv(f"{model_name.upper()}_FRAMEWORK", "candle"),
                    device=os.getenv(f"{model_name.upper()}_DEVICE", "cpu"),
                    preprocessing=self._load_preprocessing_config(model_name),
                    postprocessing=self._load_postprocessing_config(model_name),
                    evaluation_metrics=self._load_evaluation_metrics(model_name),
                )
        
        return models
    
    def _load_preprocessing_config(self, model_name: str) -> Dict[str, Any]:
        """Load preprocessing configuration for model"""
        return {
            "normalize": os.getenv(f"{model_name.upper()}_NORMALIZE", "true").lower() == "true",
            "handle_missing": os.getenv(f"{model_name.upper()}_HANDLE_MISSING", "mean").lower(),
            "encoding_method": os.getenv(f"{model_name.upper()}_ENCODING", "onehot"),
        }
    
    def _load_postprocessing_config(self, model_name: str) -> Dict[str, Any]:
        """Load postprocessing configuration for model"""
        return {
            "confidence_threshold": float(os.getenv(f"{model_name.upper()}_CONFIDENCE_THRESHOLD", "0.7")),
            "risk_threshold": float(os.getenv(f"{model_name.upper()}_RISK_THRESHOLD", "0.6")),
            "explainability": os.getenv(f"{model_name.upper()}_EXPLAINABILITY", "true").lower() == "true",
        }
    
    def _load_evaluation_metrics(self, model_name: str) -> List[str]:
        """Load evaluation metrics for model"""
        metrics_str = os.getenv(f"{model_name.upper()}_METRICS", "")
        return [m.strip() for m in metrics_str.split(",")] if metrics_str else []
    
    @lru_cache()
    def get_database_config(self) -> DatabaseConfig:
        """Get database configuration"""
        return self.load_config().database
    
    @lru_cache()
    def get_cache_config(self) -> CacheConfig:
        """Get cache configuration"""
        return self.load_config().cache
    
    @lru_cache()
    def get_model_config(self, model_name: str) -> Optional[ModelConfig]:
        """Get model configuration by name"""
        config = self.load_config()
        return config.models.get(model_name)
    
    @lru_cache()
    def get_service_config(self, service_name: str) -> Optional[AIServiceConfig]:
        """Get service configuration by name"""
        config = self.load_config()
        return config.services.get(service_name)
    
    @lru_cache()
    def get_config(self) -> RustAIServicesConfig:
        """Get complete configuration"""
        return self.load_config()
    
    def reload(self):
        """Reload configuration"""
        self._config = None
        self.load_config()


# Global configuration manager instance
config_manager = ConfigManager()
