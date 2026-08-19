"""
Enhanced Database Manager for Edu-Flow

This module provides a comprehensive database management system:
- Connection pooling and health monitoring
- Migration management with version control
- Transaction management
- Query optimization and caching
- Database-specific optimizations
- Automatic schema updates
- Performance monitoring and statistics

Author: Edu-Flow Team
"""

import asyncio
import time
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Union, AsyncGenerator
from contextlib import asynccontextmanager
from dataclasses import dataclass, field

from core.database_abstraction import (
    DatabaseInterface, DatabaseType, DatabaseConfig, 
    DatabaseConnectionPool, SQLiteDatabase, MongoDBDatabase
)
from core.database_migrations import MigrationManager, MigrationStatus
from core.exceptions import DatabaseError, MigrationError, ConfigurationError
from core.logging import get_logger
from config.settings import settings

logger = get_logger(__name__)


@dataclass
class DatabaseStats:
    """Database statistics container"""
    total_connections: int = 0
    active_connections: int = 0
    idle_connections: int = 0
    query_count: int = 0
    error_count: int = 0
    avg_query_time: float = 0.0
    last_health_check: Optional[datetime] = None
    is_healthy: bool = False


class EnhancedDatabaseManager:
    """Enhanced database manager with migration and monitoring capabilities"""
    
    _instance = None
    _initialized = False
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(EnhancedDatabaseManager, cls).__new__(cls)
        return cls._instance
    
    def __init__(self):
        if not self._initialized:
            self.config = self._get_database_config()
            self.database: Optional[DatabaseInterface] = None
            self.pool: Optional[DatabaseConnectionPool] = None
            self.migration_manager: Optional[MigrationManager] = None
            self.stats = DatabaseStats()
            self._query_times: List[float] = []
            self._max_query_history = 1000
            self._health_check_interval = 30  # seconds
            self._last_health_check: Optional[datetime] = None
            self._health_check_task: Optional[asyncio.Task] = None
            self._initialized = True
    
    def _get_database_config(self) -> DatabaseConfig:
        """Get database configuration from settings"""
        # Determine database type from URL
        url = settings.database_url
        if url.startswith("invalid"):
            selected_url = url
        elif (
            hasattr(settings, 'mongodb_url')
            and settings.mongodb_url
            and settings.mongodb_url != "mongodb://localhost:27017/edu_flow"
        ):
            selected_url = settings.mongodb_url
        elif url == "sqlite+aiosqlite:///edu_flow.db" and hasattr(settings, 'mongodb_url') and settings.mongodb_url:
            selected_url = settings.mongodb_url
        else:
            selected_url = url

        url = selected_url
        
        if url.startswith("sqlite"):
            db_type = DatabaseType.SQLITE
        elif url.startswith("postgresql"):
            db_type = DatabaseType.POSTGRESQL
        elif url.startswith("mongodb"):
            db_type = DatabaseType.MONGODB
        else:
            raise ConfigurationError(f"Unsupported database URL: {url}")
        
        # Parse URL to get connection details
        if db_type == DatabaseType.SQLITE:
            return DatabaseConfig(
                db_type=db_type,
                host="localhost",
                port=0,
                database=url.split("///")[-1],
                username="",
                password="",
                max_connections=10,
                min_connections=1
            )
        elif db_type == DatabaseType.POSTGRESQL:
            from urllib.parse import urlparse
            parsed = urlparse(settings.database_url)
            return DatabaseConfig(
                db_type=db_type,
                host=parsed.hostname or "localhost",
                port=parsed.port or 5432,
                database=parsed.path[1:],
                username=parsed.username or "postgres",
                password=parsed.password or "",
                max_connections=20,
                min_connections=2,
                ssl_mode="require" if "sslmode" in parsed.query else "disable"
            )
        elif db_type == DatabaseType.MONGODB:
            from urllib.parse import urlparse
            parsed = urlparse(url)
            return DatabaseConfig(
                db_type=db_type,
                host=parsed.hostname or "localhost",
                port=parsed.port or 27017,
                database=parsed.path[1:],
                username=parsed.username or "",
                password=parsed.password or "",
                max_connections=50,
                min_connections=5
            )
    
    async def initialize(self):
        """Initialize database manager"""
        if self._initialized and self.database is not None:
            return
        
        try:
            logger.info("Initializing enhanced database manager...")
            
            # Create connection pool
            self.pool = DatabaseConnectionPool(self.config)
            await self.pool.initialize()
            
            # Create database instance based on type
            if self.config.db_type == DatabaseType.SQLITE:
                self.database = SQLiteDatabase(self.pool)
            elif self.config.db_type == DatabaseType.POSTGRESQL:
                # Use the generic database interface for PostgreSQL
                # TODO: Implement PostgreSQLDatabase
                self.database = SQLiteDatabase(self.pool)
            elif self.config.db_type == DatabaseType.MONGODB:
                from core.database_abstraction import MongoDBDatabase
                self.database = MongoDBDatabase(self.pool)
            
            # Initialize migration manager
            self.migration_manager = MigrationManager(self.database, self.config)
            await self.migration_manager.initialize()
            
            # Run migrations
            await self._run_migrations()
            
            # Start health check task
            self._health_check_task = asyncio.create_task(self._health_check_loop())
            
            logger.info("Database manager initialized successfully")
            
        except Exception as e:
            logger.error(f"Failed to initialize database manager: {e}")
            raise DatabaseError(f"Database manager initialization failed: {e}")
    
    async def _run_migrations(self):
        """Run database migrations"""
        if not self.migration_manager:
            return
        
        try:
            # Check if we need to run migrations
            migration_status = await self.migration_manager.get_migration_status()
            
            if migration_status["pending_migrations"] > 0:
                logger.info(f"Running {migration_status['pending_migrations']} pending migrations...")
                
                result = await self.migration_manager.migrate()
                
                if result["status"] == "success":
                    logger.info(f"Successfully applied {result['migrations_applied']} migrations")
                    
                    # Log migration results
                    for migration in result["results"]:
                        if migration["status"] == "success":
                            logger.info(f"Migration {migration['version']}: {migration['name']} applied")
                        else:
                            logger.error(f"Migration {migration['version']}: {migration['name']} failed - {migration.get('error')}")
                else:
                    raise MigrationError(f"Migration failed: {result.get('message')}")
            else:
                logger.info("No pending migrations found")
                
        except Exception as e:
            logger.error(f"Migration failed: {e}")
            raise MigrationError(f"Database migration failed: {e}")
    
    async def _health_check_loop(self):
        """Background health check loop"""
        while True:
            try:
                await self._perform_health_check()
                await asyncio.sleep(self._health_check_interval)
            except Exception as e:
                logger.error(f"Health check error: {e}")
                await asyncio.sleep(self._health_check_interval)
    
    async def _perform_health_check(self):
        """Perform database health check"""
        try:
            start_time = time.time()
            
            # Check database connection
            is_healthy = await self.health_check()
            
            # Update statistics
            check_time = time.time() - start_time
            self._last_health_check = datetime.utcnow()
            self.stats.is_healthy = is_healthy
            self.stats.last_health_check = self._last_health_check
            
            if not is_healthy:
                logger.warning("Database health check failed")
            else:
                logger.debug(f"Database health check passed in {check_time:.3f}s")
                
        except Exception as e:
            logger.error(f"Health check failed: {e}")
            self.stats.is_healthy = False
    
    @asynccontextmanager
    async def get_connection(self) -> AsyncGenerator[DatabaseInterface, None]:
        """Get database connection with context manager"""
        if not self.database:
            await self.initialize()
        
        try:
            connection = await self.pool.get_connection()
            self.stats.active_connections += 1
            self.stats.total_connections += 1
            
            yield connection
            
        except Exception as e:
            self.stats.error_count += 1
            logger.error(f"Connection error: {e}")
            raise DatabaseError(f"Database connection error: {e}")
        finally:
            self.stats.active_connections -= 1
            if self.stats.active_connections < 0:
                self.stats.active_connections = 0
    
    @asynccontextmanager
    async def transaction(self):
        """Execute database operations in a transaction"""
        if not self.database:
            await self.initialize()
        
        try:
            # Begin transaction
            if hasattr(self.database, 'begin_transaction'):
                await self.database.begin_transaction()
            
            yield self.database
            
            # Commit transaction
            if hasattr(self.database, 'commit_transaction'):
                await self.database.commit_transaction()
                
        except Exception as e:
            # Rollback transaction
            if hasattr(self.database, 'rollback_transaction'):
                await self.database.rollback_transaction()
            
            self.stats.error_count += 1
            logger.error(f"Transaction error: {e}")
            raise DatabaseError(f"Transaction error: {e}")
    
    async def execute_query(self, query: str, params: Optional[Dict[str, Any]] = None, 
                          use_cache: bool = True) -> List[Dict[str, Any]]:
        """Execute a query with caching support"""
        start_time = time.time()
        
        try:
            if use_cache and hasattr(self.database, 'execute_cached_query'):
                result = await self.database.execute_cached_query(query, params)
            else:
                result = await self.database.execute_query(query, params)
            
            query_time = time.time() - start_time
            self._record_query_time(query_time)
            self.stats.query_count += 1
            
            return result
            
        except Exception as e:
            query_time = time.time() - start_time
            self._record_query_time(query_time)
            self.stats.error_count += 1
            logger.error(f"Query failed: {e}")
            raise DatabaseError(f"Query execution failed: {e}")
    
    async def execute_update(self, query: str, params: Optional[Dict[str, Any]] = None) -> int:
        """Execute an update/insert/delete operation"""
        start_time = time.time()
        
        try:
            result = await self.database.execute_update(query, params)
            
            query_time = time.time() - start_time
            self._record_query_time(query_time)
            self.stats.query_count += 1
            
            return result
            
        except Exception as e:
            query_time = time.time() - start_time
            self._record_query_time(query_time)
            self.stats.error_count += 1
            logger.error(f"Update failed: {e}")
            raise DatabaseError(f"Update operation failed: {e}")
    
    async def health_check(self) -> bool:
        """Check database health"""
        try:
            if not self.database:
                return False
            
            # Perform basic health check
            is_healthy = await self.database.health_check()
            
            if is_healthy:
                logger.debug("Database health check passed")
            else:
                logger.warning("Database health check failed")
            
            return is_healthy
            
        except Exception as e:
            logger.error(f"Health check error: {e}")
            return False
    
    def _record_query_time(self, query_time: float):
        """Record query execution time for statistics"""
        self._query_times.append(query_time)
        
        # Keep only recent query times
        if len(self._query_times) > self._max_query_history:
            self._query_times = self._query_times[-self._max_query_history:]
        
        # Update average query time
        if self._query_times:
            self.stats.avg_query_time = sum(self._query_times) / len(self._query_times)
    
    async def get_stats(self) -> Dict[str, Any]:
        """Get database statistics"""
        if not self.database:
            await self.initialize()
        
        stats = {
            "database_type": self.config.db_type.value,
            "total_connections": self.stats.total_connections,
            "active_connections": self.stats.active_connections,
            "query_count": self.stats.query_count,
            "error_count": self.stats.error_count,
            "avg_query_time": self.stats.avg_query_time,
            "is_healthy": self.stats.is_healthy,
            "last_health_check": self.stats.last_health_check.isoformat() if self.stats.last_health_check else None,
            "migration_status": await self.migration_manager.get_migration_status() if self.migration_manager else None
        }
        
        # Get pool-specific stats
        if self.pool:
            pool_stats = await self.pool.get_stats()
            stats.update(pool_stats)
        
        return stats
    
    async def create_migration(self, name: str, description: str = "") -> str:
        """Create a new migration file"""
        if not self.migration_manager:
            await self.initialize()
        
        return await self.migration_manager.create_migration(name, description)
    
    async def run_migrations(self, target_version: Optional[str] = None) -> Dict[str, Any]:
        """Run database migrations"""
        if not self.migration_manager:
            await self.initialize()
        
        return await self.migration_manager.migrate(target_version)
    
    async def rollback_migrations(self, target_version: str) -> Dict[str, Any]:
        """Rollback database migrations"""
        if not self.migration_manager:
            await self.initialize()
        
        return await self.migration_manager.rollback(target_version)
    
    async def backup_database(self) -> Dict[str, Any]:
        """Create database backup"""
        if not self.database:
            await self.initialize()
        
        try:
            backup_timestamp = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
            backup_info = {
                "timestamp": backup_timestamp,
                "database_type": self.config.db_type.value,
                "status": "started"
            }
            
            logger.info(f"Starting database backup: {backup_timestamp}")
            
            # Perform backup based on database type
            if self.config.db_type == DatabaseType.MONGODB:
                backup_info.update(await self._backup_mongodb(backup_timestamp))
            elif self.config.db_type in [DatabaseType.SQLITE, DatabaseType.POSTGRESQL]:
                backup_info.update(await self._backup_sql(backup_timestamp))
            
            backup_info["status"] = "completed"
            logger.info(f"Database backup completed: {backup_timestamp}")
            
            return backup_info
            
        except Exception as e:
            logger.error(f"Backup failed: {e}")
            raise DatabaseError(f"Database backup failed: {e}")
    
    async def _backup_mongodb(self, timestamp: str) -> Dict[str, Any]:
        """Create MongoDB backup"""
        try:
            # This would typically use mongodump command
            # For now, we'll create a simple export
            backup_data = {}
            
            # Get all collections
            collections = await self.database.execute_command("listCollections")
            
            for collection_info in collections.get("cursor", {}).get("firstBatch", []):
                collection_name = collection_info["name"]
                
                # Export collection data
                documents = await self.database.find_many(collection_name, {})
                backup_data[collection_name] = documents
            
            backup_path = f"backups/mongodb_backup_{timestamp}.json"
            
            # Save backup data
            import json
            with open(backup_path, 'w') as f:
                json.dump(backup_data, f, indent=2, default=str)
            
            return {
                "backup_path": backup_path,
                "collections_count": len(backup_data),
                "documents_count": sum(len(data) for data in backup_data.values())
            }
            
        except Exception as e:
            logger.error(f"MongoDB backup failed: {e}")
            raise DatabaseError(f"MongoDB backup failed: {e}")
    
    async def _backup_sql(self, timestamp: str) -> Dict[str, Any]:
        """Create SQL database backup"""
        try:
            # This would typically use pg_dump or sqlite3 dump
            # For now, we'll create a simple schema and data export
            backup_info = {
                "tables": [],
                "data": {}
            }
            
            # Get all tables
            if self.config.db_type == DatabaseType.POSTGRESQL:
                tables = await self.execute_query("""
                    SELECT table_name 
                    FROM information_schema.tables 
                    WHERE table_schema = 'public'
                    AND table_type = 'BASE TABLE'
                """)
            else:  # SQLite
                tables = await self.execute_query("""
                    SELECT name FROM sqlite_master 
                    WHERE type='table' AND name NOT LIKE 'sqlite_%'
                """)
            
            # Backup each table
            for table in tables:
                table_name = table["table_name"] if "table_name" in table else table["name"]
                
                # Get table schema
                schema = await self.execute_query(f"PRAGMA table_info({table_name})") if self.config.db_type == DatabaseType.SQLITE else await self.execute_query(f"""
                    SELECT column_name, data_type, is_nullable
                    FROM information_schema.columns 
                    WHERE table_name = '{table_name}'
                """)
                
                # Get table data
                data = await self.execute_query(f"SELECT * FROM {table_name}")
                
                backup_info["tables"].append({
                    "name": table_name,
                    "schema": schema,
                    "row_count": len(data)
                })
                
                backup_info["data"][table_name] = data
            
            backup_path = f"backups/sql_backup_{timestamp}.json"
            
            # Save backup data
            import json
            with open(backup_path, 'w') as f:
                json.dump(backup_info, f, indent=2, default=str)
            
            return {
                "backup_path": backup_path,
                "tables_count": len(backup_info["tables"]),
                "total_rows": sum(table["row_count"] for table in backup_info["tables"])
            }
            
        except Exception as e:
            logger.error(f"SQL backup failed: {e}")
            raise DatabaseError(f"SQL backup failed: {e}")
    
    async def close(self):
        """Close database connections"""
        try:
            # Stop health check task
            if self._health_check_task:
                self._health_check_task.cancel()
                try:
                    await self._health_check_task
                except asyncio.CancelledError:
                    pass
            
            # Close connection pool
            if self.pool:
                await self.pool.close()
            
            self.database = None
            self.pool = None
            self.migration_manager = None
            
            logger.info("Database manager closed successfully")
            
        except Exception as e:
            logger.error(f"Error closing database manager: {e}")
            raise DatabaseError(f"Failed to close database manager: {e}")


# Global database manager instance
db_manager = EnhancedDatabaseManager()


# Convenience functions
async def get_database_manager() -> EnhancedDatabaseManager:
    """Get database manager instance"""
    return db_manager


async def initialize_database():
    """Initialize database"""
    await db_manager.initialize()


async def close_database():
    """Close database connections"""
    await db_manager.close()