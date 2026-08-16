"""
Settings configuration for Edu-Flow Backend

This module provides configuration management for the application:
- Environment variables
- Database configuration
- Security settings
- API configuration
- Logging configuration
- Feature flags

Author: Edu-Flow Team
"""

import os
from typing import Optional, Dict, Any, List
from dataclasses import dataclass, field
from pathlib import Path

@dataclass
class DatabaseSettings:
    """Database configuration settings"""
    url: str = "sqlite:///edu_flow.db"
    echo: bool = False
    pool_recycle: int = 3600
    max_connections: int = 10
    connection_timeout: int = 30
    driver: str = "sqlite"
    
    @property
    def is_sqlite(self) -> bool:
        return "sqlite" in self.url
        
    @property
    def is_postgresql(self) -> bool:
        return "postgresql" in self.url
        
    @property
    def is_mysql(self) -> bool:
        return "mysql" in self.url

@dataclass
class SecuritySettings:
    """Security and authentication settings"""
    secret_key: str = "edu-flow-secret-key-change-in-production"
    algorithm: str = "HS256"
    access_token_expire_minutes: int = 30
    refresh_token_expire_days: int = 7
    jwt_algorithm: str = "HS256"
    
    @property
    def is_production(self) -> bool:
        return os.getenv("ENVIRONMENT", "development") == "production"

@dataclass
class APISettings:
    """API configuration settings"""
    title: str = "Edu-Flow API"
    description: str = "Educational Flow Management System API"
    version: str = "1.0.0"
    debug: bool = True
    
    # CORS settings
    allowed_origins: List[str] = field(default_factory=lambda: [
        "http://localhost:3000",
        "http://localhost:8080", 
        "http://localhost:5173",
        "http://localhost:5000",
        "http://127.0.0.1:3000",
        "http://127.0.0.1:8080",
    ])
    
    # Rate limiting
    rate_limit_requests: int = 100
    rate_limit_period: int = 60  # seconds
    
    # Timeout settings
    request_timeout: int = 30
    connect_timeout: int = 10

@dataclass
class LoggingSettings:
    """Logging configuration settings"""
    level: str = "INFO"
    format: str = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    file_path: Optional[str] = None
    max_file_size: int = 10 * 1024 * 1024  # 10MB
    backup_count: int = 5
    
    # Application-specific logging
    log_api_calls: bool = True
    log_database_queries: bool = False
    log_performance_metrics: bool = True

@dataclass
class FeatureFlags:
    """Application feature flags"""
    enable_caching: bool = True
    enable_rate_limiting: bool = True
    enable_database_migrations: bool = True
    enable_ai_services: bool = False
    enable_advanced_analytics: bool = False
    enable_user_tracking: bool = True
    enable_audit_logging: bool = True

class Settings:
    """Main settings class that aggregates all configuration"""
    
    def __init__(self):
        # Initialize with environment variables with defaults
        self.database = DatabaseSettings(
            url=os.getenv("DATABASE_URL", "sqlite:///edu_flow.db"),
            echo=os.getenv("DATABASE_ECHO", "false").lower() == "true",
            pool_recycle=int(os.getenv("DATABASE_POOL_RECYCLE", "3600")),
            max_connections=int(os.getenv("DATABASE_MAX_CONNECTIONS", "10")),
            connection_timeout=int(os.getenv("DATABASE_CONNECTION_TIMEOUT", "30"))
        )
        
        self.security = SecuritySettings(
            secret_key=os.getenv("SECRET_KEY", "edu-flow-secret-key-change-in-production"),
            algorithm=os.getenv("ALGORITHM", "HS256"),
            access_token_expire_minutes=int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", "30")),
            refresh_token_expire_days=int(os.getenv("REFRESH_TOKEN_EXPIRE_DAYS", "7"))
        )
        
        self.api = APISettings(
            title=os.getenv("API_TITLE", "Edu-Flow API"),
            description=os.getenv("API_DESCRIPTION", "Educational Flow Management System API"),
            version=os.getenv("API_VERSION", "1.0.0"),
            debug=os.getenv("DEBUG", "true").lower() == "true",
            allowed_origins=os.getenv("ALLOWED_ORIGINS", "").split(",") if os.getenv("ALLOWED_ORIGINS") else [
                "http://localhost:3000",
                "http://localhost:8080", 
                "http://localhost:5173",
                "http://localhost:5000",
                "http://127.0.0.1:3000",
                "http://127.0.0.1:8080",
            ]
        )
        
        self.logging = LoggingSettings(
            level=os.getenv("LOG_LEVEL", "INFO"),
            format=os.getenv("LOG_FORMAT", "%(asctime)s - %(name)s - %(levelname)s - %(message)s"),
            file_path=os.getenv("LOG_FILE"),
            log_api_calls=os.getenv("LOG_API_CALLS", "true").lower() == "true",
            log_database_queries=os.getenv("LOG_DATABASE_QUERIES", "false").lower() == "true",
            log_performance_metrics=os.getenv("LOG_PERFORMANCE_METRICS", "true").lower() == "true"
        )
        
        self.features = FeatureFlags(
            enable_caching=os.getenv("ENABLE_CACHING", "true").lower() == "true",
            enable_rate_limiting=os.getenv("ENABLE_RATE_LIMITING", "true").lower() == "true",
            enable_database_migrations=os.getenv("ENABLE_DATABASE_MIGRATIONS", "true").lower() == "true",
            enable_ai_services=os.getenv("ENABLE_AI_SERVICES", "false").lower() == "true",
            enable_advanced_analytics=os.getenv("ENABLE_ADVANCED_ANALYTICS", "false").lower() == "true",
            enable_user_tracking=os.getenv("ENABLE_USER_TRACKING", "true").lower() == "true",
            enable_audit_logging=os.getenv("ENABLE_AUDIT_LOGGING", "true").lower() == "true"
        )
    
    @property
    def cors_origins(self) -> List[str]:
        """Get CORS origins with proper validation"""
        origins = []
        for origin in self.api.allowed_origins:
            if origin.strip():
                origins.append(origin.strip())
        return origins
    
    @property
    def is_development(self) -> bool:
        """Check if running in development mode"""
        return os.getenv("ENVIRONMENT", "development") == "development"
    
    @property
    def is_production(self) -> bool:
        """Check if running in production mode"""
        return os.getenv("ENVIRONMENT", "development") == "production"
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert settings to dictionary"""
        return {
            "database": self.database.__dict__,
            "security": self.security.__dict__,
            "api": self.api.__dict__,
            "logging": self.logging.__dict__,
            "features": self.features.__dict__
        }

# Global settings instance
settings = Settings()