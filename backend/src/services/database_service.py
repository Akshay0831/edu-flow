"""
Database service for Edu-Flow Backend

This module provides database connection and operations:
- MongoDB connection management
- Database collection access
- Basic CRUD operations
- Database health checks
- PostgreSQL integration
- Redis caching

Author: Edu-Flow Team
"""

from motor.motor_asyncio import AsyncIOMotorClient, AsyncIOMotorDatabase, AsyncIOMotorCollection
from typing import Optional, Dict, Any, List, AsyncGenerator
from config.settings import settings
from core.exceptions import DatabaseError, NotFoundError
from core.logging import get_logger
import logging

logger = get_logger(__name__)


class DatabaseService:
    """Database service for MongoDB operations"""
    
    _instance = None
    _initialized = False
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(DatabaseService, cls).__new__(cls)
        return cls._instance
    
    def __init__(self):
        if not self._initialized:
            self.client: Optional[AsyncIOMotorClient] = None
            self.db: Optional[AsyncIOMotorDatabase] = None
            self._initialized = True
        
    async def connect(self) -> AsyncIOMotorDatabase:
        """Connect to MongoDB database"""
        try:
            if not self.client:
                self.client = AsyncIOMotorClient(settings.mongodb_url)
                self.db = self.client[settings.database_name]
                logger.info(f"Connected to MongoDB: {settings.mongodb_url}")
                logger.info(f"Database: {settings.database_name}")
                
                # Create indexes for better performance
                await self._ensure_indexes()
                
            return self.db
            
        except Exception as e:
            logger.error(f"Database connection failed: {e}")
            raise DatabaseError(f"Failed to connect to database: {e}")
    
    async def disconnect(self):
        """Disconnect from database"""
        if self.client:
            self.client.close()
            self.client = None
            self.db = None
            logger.info("Disconnected from MongoDB")
        
        # Close PostgreSQL connection
        try:
            from database.postgresql import close_postgres
            await close_postgres()
        except Exception as e:
            logger.error(f"Failed to close PostgreSQL: {e}")
        
        # Close Redis connection
        try:
            from database.redis import redis_cache
            if redis_cache.client:
                await redis_cache.client.close()
        except Exception as e:
            logger.error(f"Failed to close Redis: {e}")
    
    async def _ensure_indexes(self):
        """Ensure database indexes are created"""
        try:
            # Users collection indexes
            await self.db.users.create_index("email", unique=True)
            await self.db.users.create_index("role")
            await self.db.users.create_index("is_active")
            
            # Courses collection indexes
            await self.db.courses.create_index("code", unique=True)
            await self.db.courses.create_index("department_id")
            await self.db.courses.create_index("status")
            
            # Departments collection indexes
            await self.db.departments.create_index("code", unique=True)
            await self.db.departments.create_index("name")
            
            # Enrollments collection indexes
            await self.db.enrollments.create_index("student_id")
            await self.db.enrollments.create_index("course_id")
            await self.db.enrollments.create_index("status")
            await self.db.enrollments.create_index(["student_id", "course_id"], unique=True)
            
            # Assessments collection indexes
            await self.db.assessments.create_index("course_id")
            await self.db.assessments.create_index("type")
            await self.db.assessments.create_index("is_active")
            
            logger.info("Database indexes created successfully")
            
        except Exception as e:
            logger.error(f"Failed to create indexes: {e}")
            raise DatabaseError(f"Failed to create database indexes: {e}")
    
    def get_collection(self, collection_name: str) -> AsyncIOMotorCollection:
        """Get database collection"""
        if self.db is None:
            raise DatabaseError("Database not connected")
        return self.db[collection_name]
    
    async def find_one(self, collection_name: str, query: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Find one document in collection"""
        try:
            collection = self.get_collection(collection_name)
            result = await collection.find_one(query)
            
            # Convert ObjectId to string for JSON serialization
            if result and '_id' in result:
                result['_id'] = str(result['_id'])
            
            return result
        except Exception as e:
            logger.error(f"Find one failed in {collection_name}: {e}")
            raise DatabaseError(f"Failed to find document in {collection_name}: {e}")
    
    async def find_many(self, collection_name: str, query: Dict[str, Any], limit: int = 100) -> List[Dict[str, Any]]:
        """Find many documents in collection"""
        try:
            # Ensure database is connected
            if self.db is None:
                await self.connect()
            collection = self.get_collection(collection_name)
            cursor = collection.find(query).limit(limit)
            results = await cursor.to_list(length=limit)
            
            # Convert ObjectId to string for JSON serialization
            for doc in results:
                if '_id' in doc:
                    doc['_id'] = str(doc['_id'])
            
            return results
        except Exception as e:
            logger.error(f"Find many failed in {collection_name}: {e}")
            raise DatabaseError(f"Failed to find documents in {collection_name}: {e}")
    
    async def insert_one(self, collection_name: str, document: Dict[str, Any]) -> str:
        """Insert one document into collection"""
        try:
            collection = self.get_collection(collection_name)
            result = await collection.insert_one(document)
            if not result.inserted_id:
                raise DatabaseError("Failed to insert document")
            return str(result.inserted_id)
        except Exception as e:
            logger.error(f"Insert one failed in {collection_name}: {e}")
            raise DatabaseError(f"Failed to insert document in {collection_name}: {e}")
    
    async def update_one(self, collection_name: str, query: Dict[str, Any], update: Dict[str, Any]) -> bool:
        """Update one document in collection"""
        try:
            collection = self.get_collection(collection_name)
            result = await collection.update_one(query, {"$set": update})
            return result.modified_count > 0
        except Exception as e:
            logger.error(f"Update one failed in {collection_name}: {e}")
            raise DatabaseError(f"Failed to update document in {collection_name}: {e}")
    
    async def delete_one(self, collection_name: str, query: Dict[str, Any]) -> bool:
        """Delete one document from collection"""
        try:
            collection = self.get_collection(collection_name)
            result = await collection.delete_one(query)
            return result.deleted_count > 0
        except Exception as e:
            logger.error(f"Delete one failed in {collection_name}: {e}")
            raise DatabaseError(f"Failed to delete document in {collection_name}: {e}")
    
    async def count_documents(self, collection_name: str, query: Dict[str, Any]) -> int:
        """Count documents in collection"""
        try:
            collection = self.get_collection(collection_name)
            count = await collection.count_documents(query)
            return count
        except Exception as e:
            logger.error(f"Count documents failed in {collection_name}: {e}")
            raise DatabaseError(f"Failed to count documents in {collection_name}: {e}")
    
    async def health_check(self) -> Dict[str, Any]:
        """Perform database health check"""
        try:
            if self.db is None:
                await self.connect()
            
            # Test connection
            result = await self.db.command('ping')
            
            # Check collection counts directly without using count_documents
            stats = {}
            for collection in ['users', 'courses', 'departments', 'enrollments', 'assessments']:
                try:
                    coll = self.db[collection]
                    count = await coll.count_documents({})
                    stats[collection] = count
                except Exception as e:
                    stats[collection] = f"Error: {e}"
            
            return {
                "status": "healthy",
                "mongodb_connected": True,
                "ping": result,
                "collections": stats,
                "timestamp": None
            }
        except Exception as e:
            logger.error(f"Database health check failed: {e}")
            return {
                "status": "unhealthy",
                "mongodb_connected": False,
                "error": str(e),
                "collections": {},
                "timestamp": None
            }


# Global database service instance
database_service = DatabaseService()


async def get_database() -> AsyncIOMotorDatabase:
    """Get database connection dependency"""
    return await database_service.connect()


async def initialize_database():
    """Initialize database with default data"""
    try:
        db = await database_service.connect()
        
        # Create default departments
        default_departments = [
            {
                "department_id": "DEPT_CS",
                "name": "Computer Science",
                "code": "CS",
                "description": "Department of Computer Science and Engineering",
                "head_of_department": "Dr. John Smith",
                "contact_email": "cs@eduflow.com",
                "contact_phone": "+1-555-0101",
                "created_at": None,
                "updated_at": None
            },
            {
                "department_id": "DEPT_EE",
                "name": "Electrical Engineering",
                "code": "EE",
                "description": "Department of Electrical Engineering",
                "head_of_department": "Dr. Jane Doe",
                "contact_email": "ee@eduflow.com",
                "contact_phone": "+1-555-0102",
                "created_at": None,
                "updated_at": None
            },
            {
                "department_id": "DEPT_ME",
                "name": "Mechanical Engineering",
                "code": "ME",
                "description": "Department of Mechanical Engineering",
                "head_of_department": "Dr. Robert Johnson",
                "contact_email": "me@eduflow.com",
                "contact_phone": "+1-555-0103",
                "created_at": None,
                "updated_at": None
            }
        ]
        
        # Insert departments if they don't exist
        for dept in default_departments:
            existing = await database_service.find_one("departments", {"department_id": dept["department_id"]})
            if not existing:
                await database_service.insert_one("departments", dept)
        
        logger.info("Database initialized successfully")
        return True
        
    except Exception as e:
        logger.error(f"Database initialization failed: {e}")
        return False