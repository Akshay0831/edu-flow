"""Database connection management with connection pooling."""

import asyncio
import logging
from typing import Optional, Dict, Any
from motor.motor_asyncio import AsyncIOMotorClient, AsyncIOMotorDatabase
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
import redis.asyncio as redis
from contextlib import asynccontextmanager
from config.settings import settings


class DatabaseManager:
    """Manages database connections with connection pooling."""
    
    def __init__(self):
        self.mongodb_client: Optional[AsyncIOMotorClient] = None
        self.mongodb_db: Optional[AsyncIOMotorDatabase] = None
        self.postgres_engine = None
        self.postgres_session_factory = None
        self.redis_client: Optional[redis.Redis] = None
        self.logger = logging.getLogger(__name__)
        self._initialized = False
    
    async def initialize(self) -> None:
        """Initialize all database connections."""
        if self._initialized:
            return
        
        try:
            # Initialize MongoDB
            await self._initialize_mongodb()
            
            # Initialize PostgreSQL
            await self._initialize_postgresql()
            
            # Initialize Redis
            await self._initialize_redis()
            
            self._initialized = True
            self.logger.info("All database connections initialized successfully")
            
        except Exception as e:
            self.logger.error(f"Failed to initialize database connections: {e}")
            raise
    
    async def _initialize_mongodb(self) -> None:
        """Initialize MongoDB connection with connection pooling."""
        try:
            # Connection pooling configuration
            self.mongodb_client = AsyncIOMotorClient(
                settings.mongodb_url,
                maxPoolSize=100,  # Maximum number of connections in the pool
                minPoolSize=10,   # Minimum number of connections to maintain
                maxIdleTimeMS=30000,  # How long a connection can be idle before being closed
                serverSelectionTimeoutMS=5000,  # How long to wait for server selection
                connectTimeoutMS=3000,  # How long to wait for initial connection
                socketTimeoutMS=3000,  # How long to wait for socket operations
                retryWrites=True,
                retryReads=True
            )
            
            # Test connection
            await self.mongodb_client.admin.command('ping')
            
            # Get database
            self.mongodb_db = self.mongodb_client[settings.app_name.lower().replace(' ', '_')]
            
            self.logger.info("MongoDB connection established successfully")
            
        except Exception as e:
            self.logger.error(f"Failed to initialize MongoDB: {e}")
            raise
    
    async def _initialize_postgresql(self) -> None:
        """Initialize PostgreSQL connection with connection pooling."""
        try:
            # Create async engine with connection pooling
            self.postgres_engine = create_async_engine(
                settings.database_url,
                pool_size=20,  # Number of connections to keep in the pool
                max_overflow=30,  # Maximum number of connections that can be created beyond pool_size
                pool_pre_ping=True,  # Check connections before using them
                pool_recycle=3600,  # Recycle connections after 1 hour
                echo=settings.debug,  # Log SQL queries in debug mode
                future=True  # Use async future API
            )
            
            # Create session factory
            self.postgres_session_factory = async_sessionmaker(
                bind=self.postgres_engine,
                class_=AsyncSession,
                expire_on_commit=False,
                autoflush=False
            )
            
            # Test connection
            async with self.postgres_session_factory() as session:
                await session.execute("SELECT 1")
            
            self.logger.info("PostgreSQL connection established successfully")
            
        except Exception as e:
            self.logger.error(f"Failed to initialize PostgreSQL: {e}")
            raise
    
    async def _initialize_redis(self) -> None:
        """Initialize Redis connection with connection pooling."""
        try:
            # Configure Redis client
            self.redis_client = redis.from_url(
                settings.redis_url,
                decode_responses=True,
                health_check_interval=30,
                retry_on_timeout=True,
                socket_keepalive=True,
                socket_keepalive_options={}
            )
            
            # Test connection
            await self.redis_client.ping()
            
            self.logger.info("Redis connection established successfully")
            
        except Exception as e:
            self.logger.error(f"Failed to initialize Redis: {e}")
            # Redis is optional for caching, don't fail the entire initialization
            self.redis_client = None
    
    @asynccontextmanager
    async def get_mongodb_collection(self, collection_name: str):
        """Get MongoDB collection with proper connection management."""
        if not self.mongodb_db:
            await self.initialize()
        
        collection = self.mongodb_db[collection_name]
        try:
            yield collection
        finally:
            # Connection is automatically managed by Motor
            pass
    
    @asynccontextmanager
    async def get_postgres_session(self):
        """Get PostgreSQL session with proper connection management."""
        if not self.postgres_session_factory:
            await self.initialize()
        
        async with self.postgres_session_factory() as session:
            try:
                yield session
            except Exception as e:
                await session.rollback()
                raise e
            finally:
                await session.commit()
    
    async def get_redis_client(self) -> Optional[redis.Redis]:
        """Get Redis client."""
        if not self.redis_client:
            await self.initialize()
        return self.redis_client
    
    async def close(self) -> None:
        """Close all database connections."""
        try:
            # Close MongoDB connection
            if self.mongodb_client:
                self.mongodb_client.close()
                self.mongodb_client = None
            
            # Close PostgreSQL connection
            if self.postgres_engine:
                await self.postgres_engine.dispose()
                self.postgres_engine = None
            
            # Close Redis connection
            if self.redis_client:
                await self.redis_client.close()
                self.redis_client = None
            
            self._initialized = False
            self.logger.info("All database connections closed successfully")
            
        except Exception as e:
            self.logger.error(f"Error closing database connections: {e}")
            raise
    
    async def health_check(self) -> Dict[str, Any]:
        """Check health of all database connections."""
        health_status = {
            'mongodb': {'status': 'unknown', 'details': {}},
            'postgresql': {'status': 'unknown', 'details': {}},
            'redis': {'status': 'unknown', 'details': {}}
        }
        
        try:
            # Check MongoDB
            if self.mongodb_client:
                await self.mongodb_client.admin.command('ping')
                health_status['mongodb']['status'] = 'healthy'
                health_status['mongodb']['details']['host'] = self.mongodb_client.address[0]
                health_status['mongodb']['details']['port'] = self.mongodb_client.address[1]
        except Exception as e:
            health_status['mongodb']['status'] = 'unhealthy'
            health_status['mongodb']['details']['error'] = str(e)
        
        try:
            # Check PostgreSQL
            if self.postgres_engine:
                async with self.get_postgres_session() as session:
                    await session.execute("SELECT 1")
                    health_status['postgresql']['status'] = 'healthy'
        except Exception as e:
            health_status['postgresql']['status'] = 'unhealthy'
            health_status['postgresql']['details']['error'] = str(e)
        
        try:
            # Check Redis
            if self.redis_client:
                await self.redis_client.ping()
                health_status['redis']['status'] = 'healthy'
        except Exception as e:
            health_status['redis']['status'] = 'unhealthy'
            health_status['redis']['details']['error'] = str(e)
        
        return health_status
    
    async def get_connection_info(self) -> Dict[str, Any]:
        """Get connection information for all databases."""
        info = {
            'mongodb': {
                'connected': self.mongodb_client is not None,
                'database_name': self.mongodb_db.name if self.mongodb_db else None,
                'host': self.mongodb_client.address[0] if self.mongodb_client else None,
                'port': self.mongodb_client.address[1] if self.mongodb_client else None
            },
            'postgresql': {
                'connected': self.postgres_engine is not None,
                'database_url': settings.database_url,
                'pool_size': self.postgres_engine.pool.size() if self.postgres_engine else 0,
                'checked_out': self.postgres_engine.pool.checkedout() if self.postgres_engine else 0
            },
            'redis': {
                'connected': self.redis_client is not None,
                'redis_url': settings.redis_url
            }
        }
        
        return info


# Global database manager instance
database_manager = DatabaseManager()