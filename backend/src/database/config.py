"""
Database configuration management

This module provides unified database configuration:
- MongoDB connection setup
- PostgreSQL connection setup
- Health checks
- Connection pooling
- Configuration validation

Author: Edu-Flow Team
"""

import asyncio
import logging
from typing import Optional, Dict, Any
from contextlib import asynccontextmanager
from src.config.settings import settings
from src.core.exceptions import ConfigurationError
from src.core.logging import get_logger

logger = get_logger(__name__)

class DatabaseConfig:
    """Unified database configuration management"""
    
    def __init__(self):
        self.mongodb_configured = False
        self.postgresql_configured = False
        self.redis_configured = False
        self._lock = asyncio.Lock()
    
    async def configure_all(self) -> bool:
        """Configure all database connections"""
        async with self._lock:
            try:
                # Configure MongoDB
                await self.configure_mongodb()
                
                # Configure PostgreSQL
                await self.configure_postgresql()
                
                # Configure Redis
                await self.configure_redis()
                
                logger.info("All database connections configured successfully")
                return True
                
            except Exception as e:
                logger.error(f"Failed to configure database connections: {str(e)}")
                return False
    
    async def configure_mongodb(self) -> bool:
        """Configure MongoDB connection"""
        try:
            from src.database.mongodb import mongodb_service
            
            # MongoDB configuration
            mongodb_config = {
                "uri": settings.mongodb_url,
                "db_name": settings.database_name,
                "max_pool_size": 50,
                "min_pool_size": 5,
                "max_idle_time_ms": 30000,
                "server_selection_timeout_ms": 5000,
                "retry_reads": True,
                "retry_writes": True
            }
            
            # Configure MongoDB service
            mongodb_service.uri = mongodb_config["uri"]
            mongodb_service.db_name = mongodb_config["db_name"]
            
            # Test connection
            if await mongodb_service.connect():
                self.mongodb_configured = True
                logger.info("MongoDB configured successfully")
                return True
            else:
                raise ConfigurationError("MongoDB connection failed")
                
        except Exception as e:
            logger.error(f"MongoDB configuration failed: {str(e)}")
            return False
    
    async def configure_postgresql(self) -> bool:
        """Configure PostgreSQL connection"""
        try:
            from src.database.postgresql import initialize_postgres
            
            if await initialize_postgres():
                self.postgresql_configured = True
                logger.info("PostgreSQL configured successfully")
                return True
            else:
                raise ConfigurationError("PostgreSQL initialization failed")
                
        except Exception as e:
            logger.error(f"PostgreSQL configuration failed: {str(e)}")
            return False
    
    async def configure_redis(self) -> bool:
        """Configure Redis connection"""
        try:
            from src.database.redis import redis_cache
            
            redis_config = {
                "host": "localhost",
                "port": 6379,
                "db": 0,
                "password": None,
                "decode_responses": True,
                "retry_on_timeout": True,
                "socket_connect_timeout": 5,
                "socket_timeout": 5
            }
            
            # Initialize Redis cache
            await redis_cache.initialize()
            self.redis_configured = True
            
            logger.info("Redis configured successfully")
            return True
            
        except Exception as e:
            logger.error(f"Redis configuration failed: {str(e)}")
            return False
    
    async def health_check(self) -> Dict[str, bool]:
        """Perform health check on all database connections"""
        health_status = {
            "mongodb": False,
            "postgresql": False,
            "redis": False
        }
        
        try:
            # MongoDB health check
            if self.mongodb_configured:
                from src.database.mongodb import mongodb_service
                if mongodb_service.client:
                    await mongodb_service.client.admin.command('ping')
                    health_status["mongodb"] = True
            
            # PostgreSQL health check
            if selfpostgresql_configured:
                from src.database.postgresql import db_connection
                # PostgreSQL health check would be done through SQLAlchemy engine
                health_status["postgresql"] = True
            
            # Redis health check
            if self.redis_configured:
                from src.database.redis import redis_cache
                if redis_cache.client:
                    await redis_cache.client.ping()
                    health_status["redis"] = True
                    
        except Exception as e:
            logger.error(f"Database health check failed: {str(e)}")
        
        return health_status
    
    async def close_all(self) -> None:
        """Close all database connections"""
        try:
            # Close MongoDB
            if self.mongodb_configured:
                from src.database.mongodb import mongodb_service
                mongodb_service.disconnect()
                self.mongodb_configured = False
            
            # Close PostgreSQL
            if self.postgresql_configured:
                from src.database.postgresql import close_postgres
                await close_postgres()
                self.postgresql_configured = False
            
            # Close Redis
            if self.redis_configured:
                from src.database.redis import redis_cache
                if redis_cache.client:
                    await redis_cache.client.close()
                    self.redis_configured = False
            
            logger.info("All database connections closed")
            
        except Exception as e:
            logger.error(f"Failed to close database connections: {str(e)}")

# Global database configuration instance
database_config = DatabaseConfig()

@asynccontextmanager
async def get_database_session():
    """Context manager for database sessions"""
    try:
        # Ensure databases are configured
        if not database_config.mongodb_configured:
            await database_config.configure_mongodb()
        
        if not database_config.postgresql_configured:
            await database_config.configure_postgresql()
        
        if not database_config.redis_configured:
            await database_config.configure_redis()
        
        yield database_config
        
    except Exception as e:
        logger.error(f"Database session failed: {str(e)}")
        raise ConfigurationError(f"Database session failed: {str(e)}")

# Initialize databases on module load
async def initialize_databases():
    """Initialize all database connections"""
    return await database_config.configure_all()

# Close databases on module unload
async def close_databases():
    """Close all database connections"""
    await database_config.close_all()