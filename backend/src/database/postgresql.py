"""
PostgreSQL database configuration and connection management

This module provides PostgreSQL database integration:
- SQLAlchemy async engine setup
- Connection pooling
- Session management
- Database migrations
- Health checks

Author: Edu-Flow Team
"""

import asyncio
from typing import Optional, Dict, Any
from datetime import datetime
from uuid import uuid4
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import NullPool
from sqlalchemy import Column, String, Boolean, DateTime, Float, Text, Integer, Date, text, func
import logging
from contextlib import asynccontextmanager

from config.settings import settings
from core.exceptions import DatabaseError
from core.logging import get_logger

logger = get_logger(__name__)

# Base class for SQLAlchemy models
Base = declarative_base()

class PostgreSQLConnection:
    """PostgreSQL connection management with async support"""
    
    def __init__(self):
        self.engine = None
        self.session_factory = None
        self._initialized = False
        
    async def initialize(self) -> None:
        """Initialize PostgreSQL connection"""
        if self._initialized:
            return
            
        try:
            # Create async engine
            self.engine = create_async_engine(
                settings.database_url,
                poolclass=NullPool,
                echo=settings.debug,
                future=True
            )
            
            # Create session factory
            self.session_factory = async_sessionmaker(
                bind=self.engine,
                class_=AsyncSession,
                expire_on_commit=False
            )
            
            # Create tables
            async with self.engine.begin() as conn:
                await conn.run_sync(Base.metadata.create_all)
            
            self._initialized = True
            logger.info("PostgreSQL connection initialized successfully")
            
        except Exception as e:
            logger.error(f"Failed to initialize PostgreSQL: {str(e)}")
            raise DatabaseError(f"PostgreSQL connection failed: {str(e)}")
    
    async def get_session(self) -> AsyncSession:
        """Get database session"""
        if not self._initialized:
            await self.initialize()
        
        return self.session_factory()
    
    async def close(self) -> None:
        """Close PostgreSQL connection"""
        if self.engine:
            await self.engine.dispose()
            self._initialized = False
            logger.info("PostgreSQL connection closed")

# Global database connection instance
db_connection = PostgreSQLConnection()

# Database models
class User(Base):
    """User model"""
    __tablename__ = "users"
    
    id = Column(String, primary_key=True, default=lambda: str(uuid4()))
    email = Column(String, unique=True, index=True, nullable=False)
    phone = Column(String, unique=True, index=True)
    hashed_password = Column(String, nullable=False)
    first_name = Column(String, nullable=False)
    last_name = Column(String, nullable=False)
    role = Column(String, nullable=False, index=True)  # admin, teacher, student
    is_active = Column(Boolean, default=True, index=True)
    created_at = Column(DateTime, default=datetime.utcnow, index=True)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

class Student(Base):
    """Student model"""
    __tablename__ = "students"
    
    id = Column(String, primary_key=True, default=lambda: str(uuid4()))
    user_id = Column(String, nullable=False, index=True)
    student_id = Column(String, unique=True, index=True, nullable=False)
    department = Column(String, nullable=False, index=True)
    semester = Column(Integer, nullable=False, index=True)
    batch = Column(String, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow, index=True)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

class Teacher(Base):
    """Teacher model"""
    __tablename__ = "teachers"
    
    id = Column(String, primary_key=True, default=lambda: str(uuid4()))
    user_id = Column(String, nullable=False, index=True)
    employee_id = Column(String, unique=True, index=True, nullable=False)
    department = Column(String, nullable=False, index=True)
    designation = Column(String, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow, index=True)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

class Course(Base):
    """Course model"""
    __tablename__ = "courses"
    
    id = Column(String, primary_key=True, default=lambda: str(uuid4()))
    code = Column(String, unique=True, index=True, nullable=False)
    name = Column(String, nullable=False, index=True)
    department = Column(String, nullable=False, index=True)
    credits = Column(Integer, nullable=False)
    semester = Column(Integer, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow, index=True)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

class Subject(Base):
    """Subject model"""
    __tablename__ = "subjects"
    
    id = Column(String, primary_key=True, default=lambda: str(uuid4()))
    code = Column(String, unique=True, index=True, nullable=False)
    name = Column(String, nullable=False, index=True)
    department = Column(String, nullable=False, index=True)
    semester = Column(Integer, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow, index=True)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

class Class(Base):
    """Class model"""
    __tablename__ = "classes"
    
    id = Column(String, primary_key=True, default=lambda: str(uuid4()))
    course_id = Column(String, nullable=False, index=True)
    teacher_id = Column(String, nullable=False, index=True)
    subject_id = Column(String, nullable=False, index=True)
    semester = Column(Integer, nullable=False, index=True)
    batch = Column(String, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow, index=True)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

class Marks(Base):
    """Marks model"""
    __tablename__ = "marks"
    
    id = Column(String, primary_key=True, default=lambda: str(uuid4()))
    student_id = Column(String, nullable=False, index=True)
    class_id = Column(String, nullable=False, index=True)
    subject_id = Column(String, nullable=False, index=True)
    marks = Column(Float, nullable=False)
    max_marks = Column(Float, nullable=False)
    percentage = Column(Float)
    semester = Column(Integer, nullable=False, index=True)
    created_at = Column(DateTime, default=datetime.utcnow, index=True)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

class Feedback(Base):
    """Feedback model"""
    __tablename__ = "feedback"
    
    id = Column(String, primary_key=True, default=lambda: str(uuid4()))
    student_id = Column(String, nullable=False, index=True)
    teacher_id = Column(String, nullable=False, index=True)
    course_id = Column(String, nullable=False, index=True)
    class_id = Column(String, nullable=False, index=True)
    semester = Column(Integer, nullable=False, index=True)
    rating = Column(Float, nullable=False)
    comments = Column(Text)
    created_at = Column(DateTime, default=datetime.utcnow, index=True)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

class Department(Base):
    """Department model"""
    __tablename__ = "departments"
    
    id = Column(String, primary_key=True, default=lambda: str(uuid4()))
    code = Column(String, unique=True, index=True, nullable=False)
    name = Column(String, nullable=False, index=True)
    created_at = Column(DateTime, default=datetime.utcnow, index=True)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

async def get_postgres_session() -> AsyncSession:
    """Get PostgreSQL session"""
    return await db_connection.get_session()

async def initialize_postgres() -> bool:
    """Initialize PostgreSQL database"""
    try:
        await db_connection.initialize()
        logger.info("PostgreSQL database initialized successfully")
        return True
    except Exception as e:
        logger.error(f"Failed to initialize PostgreSQL: {str(e)}")
        return False

async def close_postgres() -> None:
    """Close PostgreSQL connection"""
    await db_connection.close()