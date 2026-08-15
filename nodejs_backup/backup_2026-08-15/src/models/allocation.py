"""
Class & Teacher Allocation Models for Edu-Flow

This module defines the data models for class and teacher allocation:
- ClassAllocation: Maps teachers to specific classes
- TeacherAvailability: Defines teacher availability constraints
- ClassSchedule: Defines class scheduling information
- AllocationConstraint: Defines allocation constraints and rules

Author: Edu-Flow Team
"""

from datetime import datetime, time
from typing import Dict, List, Optional, Any
from enum import Enum
from sqlalchemy import Column, String, Integer, Float, DateTime, ForeignKey, Text, Boolean, JSON
from sqlalchemy.orm import relationship
import uuid

from src.infrastructure.models.base_model import Base

class AllocationStatus(Enum):
    """Enumeration of allocation statuses"""
    PENDING = "pending"
    APPROVED = "approved"
    REJECTED = "rejected"
    CANCELLED = "cancelled"

class DayOfWeek(Enum):
    """Enumeration of days of the week"""
    MONDAY = "monday"
    TUESDAY = "tuesday"
    WEDNESDAY = "wednesday"
    THURSDAY = "thursday"
    FRIDAY = "friday"
    SATURDAY = "saturday"
    SUNDAY = "sunday"

class ResourceType(Enum):
    """Enumeration of resource types"""
    CLASSROOM = "classroom"
    LABORATORY = "laboratory"
    AUDITORIUM = "auditorium"
    ONLINE = "online"

class ConstraintType(Enum):
    """Enumeration of constraint types"""
    AVAILABILITY = "availability"
    QUALIFICATION = "qualification"
    EXPERIENCE = "experience"
    LOAD = "load"
    PREFERENCE = "preference"
    HARD = "hard"
    SOFT = "soft"

class ClassAllocation(Base):
    """Class allocation model"""
    
    __tablename__ = "class_allocations"
    
    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    class_id = Column(String, ForeignKey("classes.id"), nullable=False)
    teacher_id = Column(String, ForeignKey("teachers.id"), nullable=False)
    subject_id = Column(String, ForeignKey("subjects.id"), nullable=False)
    academic_year = Column(String, nullable=False)
    semester = Column(String, nullable=False)
    allocation_status = Column(String, default=AllocationStatus.PENDING.value, nullable=False)
    allocation_priority = Column(Integer, default=1, nullable=False)  # 1 = highest, 5 = lowest
    assigned_date = Column(DateTime, default=datetime.utcnow, nullable=False)
    assigned_by = Column(String, nullable=True)
    notes = Column(Text, nullable=True)
    is_active = Column(Boolean, default=True, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
    
    # Relationships
    class_ = relationship("Class")
    teacher = relationship("Teacher")
    subject = relationship("Subject")
    
    # Configuration-based attributes
    load_percentage = Column(Float, default=100.0, nullable=False)  # Teacher's load percentage for this class
    compensation = Column(String, nullable=True)  # Compensation details
    teaching_method = Column(String, default="lecture", nullable=True)  # lecture, lab, tutorial, seminar
    evaluation_method = Column(String, default="exam", nullable=True)  # exam, assignment, project, continuous

class TeacherAvailability(Base):
    """Teacher availability model"""
    
    __tablename__ = "teacher_availability"
    
    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    teacher_id = Column(String, ForeignKey("teachers.id"), nullable=False)
    day_of_week = Column(String, nullable=False)  # Day of week
    start_time = Column(String, nullable=False)  # HH:MM format
    end_time = Column(String, nullable=False)    # HH:MM format
    is_available = Column(Boolean, default=True, nullable=False)
    academic_year = Column(String, nullable=False)
    semester = Column(String, nullable=False)
    preference_level = Column(Integer, default=1, nullable=False)  # 1 = preferred, 5 = least preferred
    notes = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
    
    # Relationships
    teacher = relationship("Teacher")

class ClassSchedule(Base):
    """Class schedule model"""
    
    __tablename__ = "class_schedules"
    
    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    class_id = Column(String, ForeignKey("classes.id"), nullable=False)
    teacher_id = Column(String, ForeignKey("teachers.id"), nullable=False)
    day_of_week = Column(String, nullable=False)
    start_time = Column(String, nullable=False)
    end_time = Column(String, nullable=False)
    room_id = Column(String, nullable=True)
    resource_type = Column(String, default=ResourceType.CLASSROOM.value, nullable=False)
    is_active = Column(Boolean, default=True, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
    
    # Relationships
    class_ = relationship("Class")
    teacher = relationship("Teacher")

class AllocationConstraint(Base):
    """Allocation constraint model"""
    
    __tablename__ = "allocation_constraints"
    
    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    constraint_type = Column(String, nullable=False)  # availability, qualification, experience, load, preference
    constraint_name = Column(String, nullable=False)
    constraint_description = Column(Text, nullable=True)
    is_active = Column(Boolean, default=True, nullable=False)
    is_hard_constraint = Column(Boolean, default=False, nullable=False)
    priority = Column(Integer, default=1, nullable=False)
    constraint_config = Column(JSON, nullable=True)  # Configuration for the constraint
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

class AllocationRequest(Base):
    """Allocation request model"""
    
    __tablename__ = "allocation_requests"
    
    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    class_id = Column(String, ForeignKey("classes.id"), nullable=False)
    requested_teacher_id = Column(String, ForeignKey("teachers.id"), nullable=True)
    subject_id = Column(String, ForeignKey("subjects.id"), nullable=False)
    academic_year = Column(String, nullable=False)
    semester = Column(String, nullable=False)
    request_reason = Column(Text, nullable=True)
    special_requirements = Column(Text, nullable=True)
    request_status = Column(String, default="pending", nullable=False)
    requested_by = Column(String, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
    
    # Relationships
    class_ = relationship("Class")
    requested_teacher = relationship("Teacher", foreign_keys=[requested_teacher_id])
    subject = relationship("Subject")

class ResourceAvailability(Base):
    """Resource availability model"""
    
    __tablename__ = "resource_availability"
    
    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    resource_id = Column(String, nullable=False)  # Could be classroom, lab, etc.
    resource_type = Column(String, nullable=False)
    day_of_week = Column(String, nullable=False)
    start_time = Column(String, nullable=False)
    end_time = Column(String, nullable=False)
    is_available = Column(Boolean, default=True, nullable=False)
    academic_year = Column(String, nullable=False)
    semester = Column(String, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)