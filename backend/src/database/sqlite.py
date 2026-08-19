"""
SQLite database configuration and connection management

This module provides SQLite database integration:
- SQLAlchemy async engine setup
- Connection pooling
- Session management
- Database migrations
- Health checks

Author: Edu-Flow Team
"""

import asyncio
from typing import Optional, Dict, Any, AsyncGenerator
from datetime import datetime
from uuid import uuid4
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import NullPool
from sqlalchemy import Column, String, Boolean, DateTime, Float, Text, Integer, Date, text, func, select
import logging
from contextlib import asynccontextmanager
import aiosqlite

from config.settings import settings
from core.exceptions import DatabaseError
from core.logging import get_logger

logger = get_logger(__name__)

# Base class for SQLAlchemy models
Base = declarative_base()

class SQLiteConnection:
    """SQLite connection management with async support"""
    
    def __init__(self):
        self.engine = None
        self.session_factory = None
        self._initialized = False
        self.db_file = "edu_flow.db"
        
    async def initialize(self) -> None:
        """Initialize SQLite connection"""
        if self._initialized:
            return
            
        try:
            # SQLite URL with async driver
            db_url = f"sqlite+aiosqlite:///{self.db_file}"
            
            # Create async engine
            self.engine = create_async_engine(
                db_url,
                poolclass=NullPool,
                echo=settings.debug,
                future=True,
                connect_args={"check_same_thread": False}
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
            logger.info(f"SQLite connection initialized successfully - database file: {self.db_file}")
            
        except Exception as e:
            logger.error(f"Failed to initialize SQLite: {str(e)}")
            raise DatabaseError(f"SQLite connection failed: {str(e)}")
    
    async def get_session(self) -> AsyncSession:
        """Get database session"""
        if not self._initialized:
            await self.initialize()
        
        return self.session_factory()
    
    async def close(self) -> None:
        """Close SQLite connection"""
        if self.engine:
            await self.engine.dispose()
            self._initialized = False
            logger.info("SQLite connection closed")

# Global SQLite connection instance
sqlite_connection = SQLiteConnection()

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

async def get_sqlite_session() -> AsyncSession:
    """Get SQLite session"""
    return await sqlite_connection.get_session()

async def initialize_sqlite() -> bool:
    """Initialize SQLite database"""
    try:
        await sqlite_connection.initialize()
        logger.info("SQLite database initialized successfully")
        return True
    except Exception as e:
        logger.error(f"Failed to initialize SQLite: {str(e)}")
        return False

async def close_sqlite() -> None:
    """Close SQLite connection"""
    await sqlite_connection.close()