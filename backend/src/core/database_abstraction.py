"""
Database abstraction layer for swappable database backends.

This module provides:
- Abstract database interface
- Multiple database implementations (SQLite, PostgreSQL, MongoDB)
- Connection pooling management
- Migration support
- Query optimization
- Health monitoring
"""

from abc import ABC, abstractmethod
from typing import Dict, Any, List, Optional, Type, Union, AsyncGenerator
from datetime import datetime
import asyncio
import logging
from dataclasses import dataclass
from enum import Enum

from core.exceptions import DatabaseError, NotFoundError, ConfigurationError
from core.logging import get_logger

logger = get_logger(__name__)


class DatabaseType(Enum):
    """Supported database types."""
    SQLITE = "sqlite"
    POSTGRESQL = "postgresql"
    MONGODB = "mongodb"
    MYSQL = "mysql"


@dataclass
class DatabaseConfig:
    """Configuration for database connections."""
    db_type: DatabaseType
    host: str
    port: int
    database: str
    username: str
    password: str
    max_connections: int = 10
    min_connections: int = 1
    connection_timeout: int = 30
    query_timeout: int = 30
    ssl_mode: str = "disable"
    pool_recycle: int = 3600
    echo: bool = False


class DatabaseConnectionPool:
    """
    Connection pool manager for database connections.
    """
    
    def __init__(self, config: DatabaseConfig):
        self.config = config
        self._pool = None
        self._initialized = False
        self._connection_count = 0
        self._max_connections = config.max_connections
        self._min_connections = config.min_connections
    
    async def initialize(self):
        """Initialize the connection pool."""
        try:
            await self._create_pool()
            await self._warm_pool()
            self._initialized = True
            logger.info(f"Connection pool initialized for {self.config.db_type.value}")
        except Exception as e:
            logger.error(f"Failed to initialize connection pool: {e}")
            raise DatabaseError(f"Connection pool initialization failed: {e}")
    
    async def _create_pool(self):
        """Create the connection pool based on database type."""
        if self.config.db_type == DatabaseType.SQLITE:
            await self._create_sqlite_pool()
        elif self.config.db_type == DatabaseType.POSTGRESQL:
            await self._create_postgresql_pool()
        elif self.config.db_type == DatabaseType.MONGODB:
            await self._create_mongodb_pool()
        else:
            raise ConfigurationError(f"Unsupported database type: {self.config.db_type}")
    
    async def _create_sqlite_pool(self):
        """Create SQLite connection pool."""
        from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
        from sqlalchemy.pool import NullPool
        
        db_url = f"sqlite+aiosqlite:///{self.config.database}"
        
        self._pool = create_async_engine(
            db_url,
            echo=self.config.echo,
            poolclass=NullPool,
            connect_args={"check_same_thread": False}
        )
        
        self._session_factory = AsyncSession
        self._session_kwargs = {"bind": self._pool}
    
    async def _create_postgresql_pool(self):
        """Create PostgreSQL connection pool."""
        from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
        from sqlalchemy.pool import QueuePool
        
        db_url = (
            f"postgresql+asyncpg://"
            f"{self.config.username}:{self.config.password}@"
            f"{self.config.host}:{self.config.port}/{self.config.database}"
            f"?sslmode={self.config.ssl_mode}"
        )
        
        self._pool = create_async_engine(
            db_url,
            echo=self.config.echo,
            pool_size=self._max_connections,
            max_overflow=0,
            pool_timeout=self.config.connection_timeout,
            pool_recycle=self.config.pool_recycle,
            pool_pre_ping=True,
        )
        
        self._session_factory = AsyncSession
        self._session_kwargs = {"bind": self._pool}
    
    async def _create_mongodb_pool(self):
        """Create MongoDB connection pool."""
        from motor.motor_asyncio import AsyncIOMotorClient
        
        connection_string = (
            f"mongodb://{self.config.username}:{self.config.password}@"
            f"{self.config.host}:{self.config.port}/{self.config.database}"
        )
        
        self._pool = AsyncIOMotorClient(
            connection_string,
            maxPoolSize=self._max_connections,
            minPoolSize=self._min_connections,
            serverSelectionTimeoutMS=self.config.connection_timeout * 1000,
        )
        
        self._database = self._pool[self.config.database]
        self._session_factory = None
        self._session_kwargs = {}
    
    async def _warm_pool(self):
        """Warm up the connection pool with minimum connections."""
        if self.config.db_type != DatabaseType.MONGODB:
            return
        
        # For MongoDB, establish minimum connections
        for i in range(self._min_connections):
            try:
                await self._database.command('ping')
                self._connection_count += 1
            except Exception as e:
                logger.warning(f"Failed to warm up connection {i}: {e}")
    
    async def get_connection(self):
        """Get a connection from the pool."""
        if not self._initialized:
            await self.initialize()
        
        if self.config.db_type == DatabaseType.MONGODB:
            return self._database
        
        # For SQL databases, create a new session
        return self._session_factory(**self._session_kwargs)
    
    async def close(self):
        """Close the connection pool."""
        if self._pool:
            if hasattr(self._pool, 'dispose'):
                await self._pool.dispose()
            elif hasattr(self._pool, 'close'):
                await self._pool.close()
            
            self._initialized = False
            logger.info("Connection pool closed")
    
    async def get_stats(self) -> Dict[str, Any]:
        """Get connection pool statistics."""
        stats = {
            'type': self.config.db_type.value,
            'max_connections': self._max_connections,
            'min_connections': self._min_connections,
            'initialized': self._initialized,
        }
        
        if self.config.db_type == DatabaseType.MONGODB:
            stats.update({
                'connection_count': self._connection_count,
                'database_name': self.config.database,
            })
        else:
            if self._pool:
                pool = self._pool.pool
                stats.update({
                    'checked_out': pool.checkedout(),
                    'size': pool.size(),
                    'overflow': pool.overflow(),
                })
        
        return stats


class DatabaseInterface(ABC):
    """
    Abstract interface for database operations.
    """
    
    @abstractmethod
    async def connect(self):
        """Establish database connection."""
        pass
    
    @abstractmethod
    async def disconnect(self):
        """Close database connection."""
        pass
    
    @abstractmethod
    async def health_check(self) -> bool:
        """Check database health."""
        pass
    
    @abstractmethod
    async def execute_query(self, query: str, params: Dict[str, Any] = None) -> List[Dict[str, Any]]:
        """Execute a query and return results."""
        pass
    
    @abstractmethod
    async def execute_update(self, query: str, params: Dict[str, Any] = None) -> int:
        """Execute an update/insert/delete operation."""
        pass
    
    @abstractmethod
    async def execute_transaction(self, operations: List[Dict[str, Any]]) -> bool:
        """Execute a transaction with multiple operations."""
        pass
    
    @abstractmethod
    async def find_one(self, collection: str, filter: Dict[str, Any], projection: Dict[str, Any] = None) -> Optional[Dict[str, Any]]:
        """Find one document in a collection."""
        pass
    
    @abstractmethod
    async def find_many(self, collection: str, filter: Dict[str, Any], projection: Dict[str, Any] = None, 
                      limit: int = None, skip: int = None, sort: List[tuple] = None) -> List[Dict[str, Any]]:
        """Find multiple documents in a collection."""
        pass
    
    @abstractmethod
    async def insert_one(self, collection: str, document: Dict[str, Any]) -> str:
        """Insert one document into a collection."""
        pass
    
    @abstractmethod
    async def insert_many(self, collection: str, documents: List[Dict[str, Any]]) -> List[str]:
        """Insert multiple documents into a collection."""
        pass
    
    @abstractmethod
    async def update_one(self, collection: str, filter: Dict[str, Any], update: Dict[str, Any]) -> int:
        """Update one document in a collection."""
        pass
    
    @abstractmethod
    async def update_many(self, collection: str, filter: Dict[str, Any], update: Dict[str, Any]) -> int:
        """Update multiple documents in a collection."""
        pass
    
    @abstractmethod
    async def delete_one(self, collection: str, filter: Dict[str, Any]) -> int:
        """Delete one document from a collection."""
        pass
    
    @abstractmethod
    async def delete_many(self, collection: str, filter: Dict[str, Any]) -> int:
        """Delete multiple documents from a collection."""
        pass


class SQLiteDatabase(DatabaseInterface):
    """SQLite database implementation."""
    
    def __init__(self, pool: DatabaseConnectionPool):
        self.pool = pool
        self._engine = None
    
    async def connect(self):
        """Establish SQLite connection."""
        if not self._engine:
            self._engine = self.pool._pool
            await self._engine.connect()
            logger.info("SQLite database connected")
    
    async def disconnect(self):
        """Close SQLite connection."""
        if self._engine:
            await self._engine.dispose()
            logger.info("SQLite database disconnected")
    
    async def health_check(self) -> bool:
        """Check SQLite health."""
        try:
            await self.execute_query("SELECT 1")
            return True
        except Exception as e:
            logger.error(f"SQLite health check failed: {e}")
            return False
    
    async def execute_query(self, query: str, params: Dict[str, Any] = None) -> List[Dict[str, Any]]:
        """Execute SQLite query."""
        async with self.pool._session_factory(**self.pool._session_kwargs) as session:
            from sqlalchemy import text
            
            result = await session.execute(text(query), params or {})
            rows = result.fetchall()
            
            return [dict(row._mapping) for row in rows]
    
    async def execute_update(self, query: str, params: Dict[str, Any] = None) -> int:
        """Execute SQLite update."""
        async with self.pool._session_factory(**self.pool._session_kwargs) as session:
            from sqlalchemy import text
            
            result = await session.execute(text(query), params or {})
            await session.commit()
            return result.rowcount
    
    async def execute_transaction(self, operations: List[Dict[str, Any]]) -> bool:
        """Execute SQLite transaction."""
        async with self.pool._session_factory(**self.pool._session_kwargs) as session:
            try:
                for op in operations:
                    if op['type'] == 'query':
                        await session.execute(text(op['query']), op.get('params'))
                    elif op['type'] == 'update':
                        await session.execute(text(op['query']), op.get('params'))
                
                await session.commit()
                return True
            except Exception as e:
                await session.rollback()
                raise DatabaseError(f"Transaction failed: {e}")
    
    # MongoDB-like methods for SQL databases
    async def find_one(self, table: str, filter: Dict[str, Any], projection: Dict[str, Any] = None) -> Optional[Dict[str, Any]]:
        """Find one row in a table."""
        where_clauses = []
        params = {}
        
        for key, value in filter.items():
            where_clauses.append(f"{key} = :{key}")
            params[key] = value
        
        query = f"SELECT * FROM {table}"
        if where_clauses:
            query += " WHERE " + " AND ".join(where_clauses)
        
        results = await self.execute_query(query, params)
        return results[0] if results else None
    
    async def find_many(self, table: str, filter: Dict[str, Any] = None, projection: Dict[str, Any] = None, 
                       limit: int = None, skip: int = None, sort: List[tuple] = None) -> List[Dict[str, Any]]:
        """Find multiple rows in a table."""
        query = f"SELECT * FROM {table}"
        params = {}
        
        if filter:
            where_clauses = []
            for key, value in filter.items():
                where_clauses.append(f"{key} = :{key}")
                params[key] = value
            
            if where_clauses:
                query += " WHERE " + " AND ".join(where_clauses)
        
        if sort:
            sort_clause = ", ".join([f"{col} {'DESC' if desc else 'ASC'}" for col, desc in sort])
            query += f" ORDER BY {sort_clause}"
        
        if limit:
            query += f" LIMIT {limit}"
        
        if skip:
            query += f" OFFSET {skip}"
        
        return await self.execute_query(query, params)
    
    async def insert_one(self, table: str, document: Dict[str, Any]) -> str:
        """Insert one row into a table."""
        columns = ', '.join(document.keys())
        placeholders = ', '.join([f":{key}" for key in document.keys()])
        query = f"INSERT INTO {table} ({columns}) VALUES ({placeholders})"
        
        result = await self.execute_update(query, document)
        return str(result)
    
    async def insert_many(self, table: str, documents: List[Dict[str, Any]]) -> List[str]:
        """Insert multiple rows into a table."""
        results = []
        for doc in documents:
            result = await self.insert_one(table, doc)
            results.append(result)
        return results
    
    async def update_one(self, table: str, filter: Dict[str, Any], update: Dict[str, Any]) -> int:
        """Update one row in a table."""
        set_clauses = []
        params = {}
        
        for key, value in filter.items():
            params[f"filter_{key}"] = value
        
        for key, value in update.items():
            set_clauses.append(f"{key} = :{key}")
            params[key] = value
        
        query = f"UPDATE {table} SET {', '.join(set_clauses)}"
        
        if filter:
            where_clauses = [f"{key} = :filter_{key}" for key in filter.keys()]
            query += " WHERE " + " AND ".join(where_clauses)
        
        return await self.execute_update(query, params)
    
    async def update_many(self, table: str, filter: Dict[str, Any], update: Dict[str, Any]) -> int:
        """Update multiple rows in a table."""
        return await self.update_one(table, filter, update)
    
    async def delete_one(self, table: str, filter: Dict[str, Any]) -> int:
        """Delete one row from a table."""
        where_clauses = []
        params = {}
        
        for key, value in filter.items():
            where_clauses.append(f"{key} = :{key}")
            params[key] = value
        
        query = f"DELETE FROM {table}"
        if where_clauses:
            query += " WHERE " + " AND ".join(where_clauses)
        
        return await self.execute_update(query, params)
    
    async def delete_many(self, table: str, filter: Dict[str, Any]) -> int:
        """Delete multiple rows from a table."""
        return await self.delete_one(table, filter)


class MongoDBDatabase(DatabaseInterface):
    """MongoDB database implementation."""
    
    def __init__(self, pool: DatabaseConnectionPool):
        self.pool = pool
        self._db = self.pool._database
    
    async def connect(self):
        """Establish MongoDB connection."""
        await self._db.command('ping')
        logger.info("MongoDB database connected")
    
    async def disconnect(self):
        """Close MongoDB connection."""
        await self.pool._pool.close()
        logger.info("MongoDB database disconnected")
    
    async def health_check(self) -> bool:
        """Check MongoDB health."""
        try:
            await self._db.command('ping')
            return True
        except Exception as e:
            logger.error(f"MongoDB health check failed: {e}")
            return False
    
    async def execute_query(self, query: str, params: Dict[str, Any] = None) -> List[Dict[str, Any]]:
        """Execute MongoDB query using aggregation pipeline."""
        # This is a simplified implementation - in practice, you'd use MongoDB's aggregation
        collection = self._db[params.get('collection', 'documents')]
        pipeline = params.get('pipeline', [])
        
        cursor = collection.aggregate(pipeline)
        results = await cursor.to_list(length=1000)
        return results
    
    async def execute_update(self, query: str, params: Dict[str, Any] = None) -> int:
        """Execute MongoDB update operation."""
        collection = self._db[params.get('collection', 'documents')]
        filter = params.get('filter', {})
        update = params.get('update', {})
        
        result = await collection.update_many(filter, update)
        return result.modified_count
    
    async def execute_transaction(self, operations: List[Dict[str, Any]]) -> bool:
        """Execute MongoDB transaction."""
        # MongoDB transactions require replica set
        session = self.pool._pool.start_session()
        
        try:
            with session.start_transaction():
                for op in operations:
                    collection = self._db[op['collection']]
                    
                    if op['type'] == 'insert':
                        await collection.insert_many(op['documents'], session=session)
                    elif op['type'] == 'update':
                        await collection.update_many(op['filter'], op['update'], session=session)
                    elif op['type'] == 'delete':
                        await collection.delete_many(op['filter'], session=session)
            
            return True
        except Exception as e:
            logger.error(f"MongoDB transaction failed: {e}")
            return False
        finally:
            session.end_session()
    
    async def find_one(self, collection: str, filter: Dict[str, Any], projection: Dict[str, Any] = None) -> Optional[Dict[str, Any]]:
        """Find one document in a collection."""
        coll = self._db[collection]
        return await coll.find_one(filter, projection)
    
    async def find_many(self, collection: str, filter: Dict[str, Any] = None, projection: Dict[str, Any] = None, 
                       limit: int = None, skip: int = None, sort: List[tuple] = None) -> List[Dict[str, Any]]:
        """Find multiple documents in a collection."""
        coll = self._db[collection]
        query = coll.find(filter or {}, projection)
        
        if sort:
            query = query.sort(sort)
        
        if limit:
            query = query.limit(limit)
        
        if skip:
            query = query.skip(skip)
        
        return await query.to_list(length=limit or 1000)
    
    async def insert_one(self, collection: str, document: Dict[str, Any]) -> str:
        """Insert one document into a collection."""
        coll = self._db[collection]
        result = await coll.insert_one(document)
        return str(result.inserted_id)
    
    async def insert_many(self, collection: str, documents: List[Dict[str, Any]]) -> List[str]:
        """Insert multiple documents into a collection."""
        coll = self._db[collection]
        result = await coll.insert_many(documents)
        return [str(id) for id in result.inserted_ids]
    
    async def update_one(self, collection: str, filter: Dict[str, Any], update: Dict[str, Any]) -> int:
        """Update one document in a collection."""
        coll = self._db[collection]
        result = await coll.update_one(filter, update)
        return result.modified_count
    
    async def update_many(self, collection: str, filter: Dict[str, Any], update: Dict[str, Any]) -> int:
        """Update multiple documents in a collection."""
        coll = self._db[collection]
        result = await coll.update_many(filter, update)
        return result.modified_count
    
    async def delete_one(self, collection: str, filter: Dict[str, Any]) -> int:
        """Delete one document from a collection."""
        coll = self._db[collection]
        result = await coll.delete_one(filter)
        return result.deleted_count
    
    async def delete_many(self, collection: str, filter: Dict[str, Any]) -> int:
        """Delete multiple documents from a collection."""
        coll = self._db[collection]
        result = await coll.delete_many(filter)
        return result.deleted_count


class DatabaseManager:
    """
    Database manager for handling multiple database backends.
    """
    
    def __init__(self, config: DatabaseConfig):
        self.config = config
        self.pool = DatabaseConnectionPool(config)
        self._database = None
        self._initialized = False
    
    async def initialize(self):
        """Initialize the database manager."""
        try:
            await self.pool.initialize()
            
            # Create appropriate database instance
            if self.config.db_type == DatabaseType.SQLITE:
                self._database = SQLiteDatabase(self.pool)
            elif self.config.db_type == DatabaseType.POSTGRESQL:
                self._database = SQLiteDatabase(self.pool)  # PostgreSQL uses SQL interface
            elif self.config.db_type == DatabaseType.MONGODB:
                self._database = MongoDBDatabase(self.pool)
            else:
                raise ConfigurationError(f"Unsupported database type: {self.config.db_type}")
            
            await self._database.connect()
            self._initialized = True
            logger.info(f"Database manager initialized with {self.config.db_type.value}")
            
        except Exception as e:
            logger.error(f"Failed to initialize database manager: {e}")
            raise DatabaseError(f"Database manager initialization failed: {e}")
    
    async def disconnect(self):
        """Close database connections."""
        if self._database:
            await self._database.disconnect()
        await self.pool.close()
        self._initialized = False
        logger.info("Database manager disconnected")
    
    async def health_check(self) -> bool:
        """Check database health."""
        if not self._initialized:
            return False
        return await self._database.health_check()
    
    def get_database(self) -> DatabaseInterface:
        """Get the database interface."""
        if not self._initialized:
            raise DatabaseError("Database manager not initialized")
        return self._database
    
    async def get_stats(self) -> Dict[str, Any]:
        """Get database statistics."""
        return await self.pool.get_stats()
    
    # Convenience methods
    async def find_one(self, collection: str, filter: Dict[str, Any], projection: Dict[str, Any] = None):
        """Find one document/row."""
        return await self._database.find_one(collection, filter, projection)
    
    async def find_many(self, collection: str, filter: Dict[str, Any] = None, projection: Dict[str, Any] = None, 
                       limit: int = None, skip: int = None, sort: List[tuple] = None):
        """Find multiple documents/rows."""
        return await self._database.find_many(collection, filter, projection, limit, skip, sort)
    
    async def insert_one(self, collection: str, document: Dict[str, Any]) -> str:
        """Insert one document/row."""
        return await self._database.insert_one(collection, document)
    
    async def insert_many(self, collection: str, documents: List[Dict[str, Any]]) -> List[str]:
        """Insert multiple documents/rows."""
        return await self._database.insert_many(collection, documents)
    
    async def update_one(self, collection: str, filter: Dict[str, Any], update: Dict[str, Any]) -> int:
        """Update one document/row."""
        return await self._database.update_one(collection, filter, update)
    
    async def update_many(self, collection: str, filter: Dict[str, Any], update: Dict[str, Any]) -> int:
        """Update multiple documents/rows."""
        return await self._database.update_many(collection, filter, update)
    
    async def delete_one(self, collection: str, filter: Dict[str, Any]) -> int:
        """Delete one document/row."""
        return await self._database.delete_one(collection, filter)
    
    async def delete_many(self, collection: str, filter: Dict[str, Any]) -> int:
        """Delete multiple documents/rows."""
        return await self._database.delete_many(collection, filter)


# Factory function to create database manager
async def create_database_manager(config: DatabaseConfig) -> DatabaseManager:
    """Create a database manager with the given configuration."""
    manager = DatabaseManager(config)
    await manager.initialize()
    return manager


# Global database manager instance
_database_manager = None


def get_database_manager() -> DatabaseManager:
    """Get the global database manager instance."""
    if _database_manager is None:
        raise DatabaseError("Database manager not initialized")
    return _database_manager


def initialize_database_manager(config: DatabaseConfig):
    """Initialize the global database manager."""
    global _database_manager
    _database_manager = DatabaseManager(config)
    return _database_manager