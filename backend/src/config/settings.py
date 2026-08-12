"""Centralized configuration management using pydantic-settings."""

import os
from typing import List, Optional
from pydantic_settings import BaseSettings
from pydantic import Field


class Settings(BaseSettings):
    """Application settings with environment variable support."""
    
    # Application settings
    app_name: str = "Edu-Flow API"
    debug: bool = False
    environment: str = Field(default="development")
    host: str = Field(default="0.0.0.0")
    port: int = Field(default=8000)
    
    # Security settings
    secret_key: str = Field(default="your-secret-key-here")
    algorithm: str = Field(default="HS256")
    access_token_expire_minutes: int = Field(default=30)
    refresh_token_expire_days: int = Field(default=7)
    
    # Database settings
    database_name: str = Field(default="edu_flow")
    database_url: str = Field(default="postgresql+asyncpg://user:password@localhost:5432/edu_flow")
    mongodb_url: str = Field(default="mongodb://localhost:27017/edu_flow")
    redis_url: str = Field(default="redis://localhost:6379")
    
    # JWT settings
    jwt_algorithm: str = Field(default="HS256")
    jwt_secret_key: str = Field(default="jwt-secret-key")
    jwt_access_token_expire_minutes: int = Field(default=30)
    jwt_refresh_token_expire_days: int = Field(default=7)
    
    # CORS settings
    cors_origins: List[str] = Field(default=["*"])
    cors_allow_credentials: bool = Field(default=True)
    cors_allow_methods: List[str] = Field(default=["*"])
    cors_allow_headers: List[str] = Field(default=["*"])
    
    # Rate limiting settings
    rate_limit_enabled: bool = Field(default=True)
    rate_limit_requests: int = Field(default=100)
    rate_limit_window: int = Field(default=60)
    
    # Cache settings
    cache_enabled: bool = Field(default=True)
    cache_ttl: int = Field(default=3600)
    cache_max_size: int = Field(default=1000)
    
    # Logging settings
    log_level: str = Field(default="INFO")
    log_format: str = Field(default="json")
    log_file: str = Field(default="logs/backend.log")
    log_max_size: int = Field(default=10 * 1024 * 1024)  # 10MB
    log_backup_count: int = Field(default=5)
    
    # API settings
    api_prefix: str = "/api/v1"
    api_title: str = "Edu-Flow API"
    api_description: str = "Authentication and User Management Service for Edu-Flow"
    api_version: str = "1.0.0"
    docs_url: str = "/docs"
    redoc_url: str = "/redoc"
    
    # Security settings
    password_min_length: int = 8
    password_require_uppercase: bool = True
    password_require_lowercase: bool = True
    password_require_number: bool = True
    password_require_special: bool = True
    
    # Email settings
    email_enabled: bool = False
    email_smtp_server: str = Field(default="smtp.gmail.com")
    email_smtp_port: int = Field(default=587)
    email_smtp_username: str = Field(default="")
    email_smtp_password: str = Field(default="")
    email_from: str = Field(default="noreply@edu-flow.com")
    
    # File upload settings
    upload_dir: str = Field(default="uploads")
    max_file_size: int = Field(default=10 * 1024 * 1024)  # 10MB
    allowed_extensions: List[str] = Field(
        default=[".jpg", ".jpeg", ".png", ".gif", ".pdf", ".doc", ".docx", ".txt"]
    )
    
    # Monitoring settings
    metrics_enabled: bool = Field(default=True)
    health_check_enabled: bool = Field(default=True)
    
    # Development settings
    reload: bool = Field(default=False)
    
    model_config = {
        "env_file": ".env",
        "env_file_encoding": "utf-8",
        "case_sensitive": False
    }
    
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        # Validate settings
        self._validate()
    
    def _validate(self):
        """Validate settings configuration."""
        if self.secret_key == "your-secret-key-here" and self.environment == "production":
            raise ValueError("SECRET_KEY must be set in production")
        
        if not self.mongodb_url:
            raise ValueError("MONGODB_URL must be set")
            
        if not self.database_url:
            raise ValueError("DATABASE_URL must be set")
            
        if self.access_token_expire_minutes <= 0:
            raise ValueError("ACCESS_TOKEN_EXPIRE_MINUTES must be positive")
            
        if self.port <= 0 or self.port > 65535:
            raise ValueError("PORT must be between 1 and 65535")
    
    def is_production(self) -> bool:
        """Check if running in production environment."""
        return self.environment == "production"
    
    def is_development(self) -> bool:
        """Check if running in development environment."""
        return self.environment == "development"
    
    def get_cors_origins_regex(self) -> str:
        """Get CORS origins as regex pattern."""
        if "*" in self.cors_origins:
            return ".*"
        return "|".join([re.escape(origin) for origin in self.cors_origins])
    
    def get_database_config(self) -> dict:
        """Get database configuration dictionary."""
        return {
            "postgresql": self.database_url,
            "mongodb": self.mongodb_url,
            "redis": self.redis_url
        }


# Global settings instance
settings = Settings()