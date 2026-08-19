"""
Database service for development with SQLite and MongoDB

This module provides database connection and operations:
- SQLite connection management
- MongoDB connection management
- Basic CRUD operations
- Database health checks

Author: Edu-Flow Team
"""

import asyncio
from typing import Optional, Dict, Any, List, AsyncGenerator
from datetime import datetime
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker
from sqlalchemy import text
from motor.motor_asyncio import AsyncIOMotorClient, AsyncIOMotorDatabase, AsyncIOMotorCollection
from config.settings import settings
from core.exceptions import DatabaseError, NotFoundError
from database.sqlite import User, Student, Teacher, Course, Subject, Class, Marks, Feedback, Department
from core.logging import get_logger
import logging

logger = get_logger(__name__)


class DatabaseService:
    """Database service for SQLite and MongoDB operations"""
    
    _instance = None
    _initialized = False
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(DatabaseService, cls).__new__(cls)
        return cls._instance
    
    def __init__(self):
        if not self._initialized:
            self.sqlite_engine = None
            self.sqlite_session_factory = None
            self.client: Optional[AsyncIOMotorClient] = None
            self.db: Optional[AsyncIOMotorDatabase] = None
            self._initialized = True
        
    async def initialize_sqlite(self) -> None:
        """Initialize SQLite database"""
        try:
            if not self.sqlite_engine:
                # SQLite URL with async driver
                db_url = f"sqlite+aiosqlite:///edu_flow.db"
                
                self.sqlite_engine = create_async_engine(
                    db_url,
                    echo=settings.debug,
                    future=True,
                    connect_args={"check_same_thread": False}
                )
                
                self.sqlite_session_factory = async_sessionmaker(
                    bind=self.sqlite_engine,
                    class_=AsyncSession,
                    expire_on_commit=False
                )
                
                # Create tables
                from database.sqlite import Base
                async with self.sqlite_engine.begin() as conn:
                    await conn.run_sync(Base.metadata.create_all)
                
                logger.info("SQLite database initialized successfully")
                
        except Exception as e:
            logger.error(f"SQLite initialization failed: {e}")
            raise DatabaseError(f"Failed to initialize SQLite: {e}")
    
    async def initialize_mongodb(self) -> None:
        """Initialize MongoDB database"""
        try:
            if not self.client:
                self.client = AsyncIOMotorClient(settings.mongodb_url)
                self.db = self.client[settings.database_name]
                logger.info(f"Connected to MongoDB: {settings.mongodb_url}")
                logger.info(f"Database: {settings.database_name}")
                
                # Create indexes for better performance
                await self._ensure_indexes()
                
        except Exception as e:
            logger.error(f"MongoDB initialization failed: {e}")
            raise DatabaseError(f"Failed to initialize MongoDB: {e}")
    
    async def initialize(self) -> None:
        """Initialize all databases"""
        try:
            # Initialize SQLite
            await self.initialize_sqlite()
            
            # Initialize MongoDB
            await self.initialize_mongodb()
            
            logger.info("All databases initialized successfully")
            
        except Exception as e:
            logger.error(f"Database initialization failed: {e}")
            raise DatabaseError(f"Failed to initialize databases: {e}")
    

    
    async def get_mongodb_collection(self, collection_name: str) -> AsyncIOMotorCollection:
        """Get MongoDB collection"""
        if self.db is None:
            await self.initialize_mongodb()
        return self.db[collection_name]
    
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
    
    async def disconnect(self):
        """Disconnect from all databases"""
        try:
            # Close SQLite connection
            if self.sqlite_engine:
                await self.sqlite_engine.dispose()
                self.sqlite_engine = None
                self.sqlite_session_factory = None
            
            # Close MongoDB connection
            if self.client:
                self.client.close()
                self.client = None
                self.db = None
            
            logger.info("All database connections closed")
            
        except Exception as e:
            logger.error(f"Failed to close database connections: {e}")
    
    # SQLite CRUD operations
    async def create_sqlite(self, model: str, data: Dict) -> str:
        """Create record in SQLite"""
        try:
            async with self.sqlite_session_factory() as session:
                # Use model string to get the correct class
                model_mapping = {
                    'User': User,
                    'Student': Student,
                    'Teacher': Teacher,
                    'Course': Course,
                    'Subject': Subject,
                    'Class': Class,
                    'Marks': Marks,
                    'Feedback': Feedback,
                    'Department': Department
                }
                model_class = model_mapping.get(model)
                if not model_class:
                    raise ValueError(f"Unknown model: {model}")
                
                record = model_class(**data)
                session.add(record)
                await session.commit()
                await session.refresh(record)
                return str(record.id)
        except Exception as e:
            logger.error(f"SQLite create failed for {model}: {e}")
            raise DatabaseError(f"Failed to create {model}: {e}")
    
    async def get_sqlite(self, model: str, id: str) -> Optional[Dict]:
        """Get record from SQLite"""
        try:
            async with self.sqlite_session_factory() as session:
                # Use model string to get the correct class
                model_mapping = {
                    'User': User,
                    'Student': Student,
                    'Teacher': Teacher,
                    'Course': Course,
                    'Subject': Subject,
                    'Class': Class,
                    'Marks': Marks,
                    'Feedback': Feedback,
                    'Department': Department
                }
                model_class = model_mapping.get(model)
                if not model_class:
                    raise ValueError(f"Unknown model: {model}")
                
                record = await session.get(model_class, id)
                if record:
                    return {c.name: getattr(record, c.name) for c in record.__table__.columns}
                return None
        except Exception as e:
            logger.error(f"SQLite get failed for {model}: {e}")
            raise DatabaseError(f"Failed to get {model}: {e}")
    
    async def delete_sqlite(self, model: str, id: str) -> bool:
        """Delete record from SQLite"""
        try:
            async with self.sqlite_session_factory() as session:
                # Use model string to get the correct class
                model_mapping = {
                    'User': User,
                    'Student': Student,
                    'Teacher': Teacher,
                    'Course': Course,
                    'Subject': Subject,
                    'Class': Class,
                    'Marks': Marks,
                    'Feedback': Feedback,
                    'Department': Department
                }
                model_class = model_mapping.get(model)
                if not model_class:
                    raise ValueError(f"Unknown model: {model}")
                
                record = await session.get(model_class, id)
                if record:
                    await session.delete(record)
                    await session.commit()
                    return True
                return False
        except Exception as e:
            logger.error(f"SQLite delete failed for {model}: {e}")
            raise DatabaseError(f"Failed to delete {model}: {e}")
    
    # MongoDB CRUD operations
    async def create_mongodb(self, collection_name: str, document: Dict) -> str:
        """Create document in MongoDB"""
        try:
            collection = await self.get_mongodb_collection(collection_name)
            
            # Add timestamps
            document['created_at'] = datetime.now()
            document['updated_at'] = datetime.now()
            
            # Insert document
            result = await collection.insert_one(document)
            
            if not result.inserted_id:
                raise DatabaseError("Failed to create document")
            
            return str(result.inserted_id)
            
        except Exception as e:
            logger.error(f"MongoDB create failed in {collection_name}: {e}")
            raise DatabaseError(f"MongoDB create failed: {e}")
    
    async def get_mongodb(self, collection_name: str, query: Dict) -> Optional[Dict]:
        """Get document from MongoDB"""
        try:
            collection = await self.get_mongodb_collection(collection_name)
            document = await collection.find_one(query)
            
            if document:
                # Convert ObjectId to string for JSON serialization
                if '_id' in document:
                    document['id'] = str(document['_id'])
                    del document['_id']
                
                return document
            
            return None
            
        except Exception as e:
            logger.error(f"MongoDB get failed in {collection_name}: {e}")
            raise DatabaseError(f"MongoDB get failed: {e}")
    
    async def find_many_mongodb(self, collection_name: str, query: Dict, limit: int = 100) -> List[Dict]:
        """Find many documents in MongoDB"""
        try:
            collection = await self.get_mongodb_collection(collection_name)
            cursor = collection.find(query).limit(limit)
            results = await cursor.to_list(length=limit)
            
            # Convert ObjectId to string for JSON serialization
            for doc in results:
                if '_id' in doc:
                    doc['id'] = str(doc['_id'])
                    del doc['_id']
            
            return results
        except Exception as e:
            logger.error(f"MongoDB find many failed in {collection_name}: {e}")
            raise DatabaseError(f"MongoDB find many failed: {e}")
    
    async def health_check(self) -> Dict[str, Any]:
        """Perform database health check"""
        try:
            # Check SQLite
            sqlite_status = False
            try:
                session = await self.get_sqlite_session()
                await session.execute(text("SELECT 1"))
                sqlite_status = True
            except Exception as e:
                logger.error(f"SQLite health check failed: {e}")
            
            # Check MongoDB
            mongodb_status = False
            try:
                if self.db is not None:
                    await self.db.command('ping')
                    mongodb_status = True
            except Exception as e:
                logger.error(f"MongoDB health check failed: {e}")
            
            # Check collection counts
            collections = {}
            if mongodb_status:
                try:
                    collections = {
                        'users': await self.db.users.count_documents({}),
                        'courses': await self.db.courses.count_documents({}),
                        'departments': await self.db.departments.count_documents({})
                    }
                except Exception as e:
                    collections = {'error': str(e)}
            
            return {
                "status": "healthy" if sqlite_status or mongodb_status else "unhealthy",
                "sqlite_connected": sqlite_status,
                "mongodb_connected": mongodb_status,
                "collections": collections,
                "timestamp": datetime.now().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Database health check failed: {e}")
            return {
                "status": "unhealthy",
                "sqlite_connected": False,
                "mongodb_connected": False,
                "error": str(e),
                "collections": {},
                "timestamp": datetime.now().isoformat()
            }


# Global database service instance
database_service = DatabaseService()


async def get_database() -> DatabaseService:
    """Get database connection dependency"""
    if not database_service._initialized:
        await database_service.initialize()
    return database_service


async def initialize_database():
    """Initialize database with default data"""
    try:
        db = await database_service.initialize()
        
        # Create default departments if they don't exist
        existing_departments = await database_service.find_many_mongodb("departments", {})
        if len(existing_departments) == 0:
            default_departments = [
                {
                    "department_id": "DEPT_CS",
                    "name": "Computer Science",
                    "code": "CS",
                    "description": "Department of Computer Science and Engineering",
                    "head_of_department": "Dr. John Smith",
                    "contact_email": "cs@eduflow.com",
                    "contact_phone": "+1-555-0101"
                },
                {
                    "department_id": "DEPT_EE",
                    "name": "Electrical Engineering",
                    "code": "EE",
                    "description": "Department of Electrical Engineering",
                    "head_of_department": "Dr. Jane Doe",
                    "contact_email": "ee@eduflow.com",
                    "contact_phone": "+1-555-0102"
                }
            ]
            
            for dept in default_departments:
                await database_service.create_mongodb("departments", dept)
            
            logger.info("Default departments created")
        
        return True
        
    except Exception as e:
        logger.error(f"Database initialization failed: {e}")
        return False