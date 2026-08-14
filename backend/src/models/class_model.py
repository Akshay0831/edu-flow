"""
Class Management Models

This module defines Pydantic models for class management:
- Class creation, update, and response schemas
- Attendance tracking and enrollment
- Statistics and reporting models

Author: Edu-Flow Team
"""

from datetime import datetime, date, time
from typing import Optional, List, Dict, Any
from uuid import uuid4
from enum import Enum
from pydantic import BaseModel, Field, ConfigDict


class ClassStatus(str, Enum):
    """Class status enumeration."""
    ACTIVE = "active"
    INACTIVE = "inactive"
    CANCELLED = "cancelled"
    COMPLETED = "completed"


class ClassType(str, Enum):
    """Class type enumeration."""
    LECTURE = "lecture"
    LAB = "lab"
    SEMINAR = "seminar"
    WORKSHOP = "workshop"
    EXAM = "exam"
    PROJECT = "project"


class ClassCreate(BaseModel):
    """Class creation schema."""
    name: str = Field(..., description="Class name", min_length=1, max_length=100)
    course_id: str = Field(..., description="Associated course ID")
    instructor_id: str = Field(..., description="Instructor ID")
    class_type: ClassType = Field(..., description="Class type")
    capacity: int = Field(..., description="Class capacity", ge=1)
    schedule: str = Field(..., description="Class schedule")
    location: str = Field(..., description="Class location")
    start_time: time = Field(..., description="Start time")
    end_time: time = Field(..., description="End time")
    days_of_week: List[str] = Field(..., description="Days of week")
    semester: str = Field(..., description="Semester")
    academic_year: int = Field(..., description="Academic year")
    description: Optional[str] = Field(None, description="Class description")
    status: ClassStatus = Field(ClassStatus.ACTIVE, description="Class status")
    
    model_config = ConfigDict(from_attributes=True)


class ClassUpdate(BaseModel):
    """Class update schema."""
    name: Optional[str] = Field(None, description="Class name", min_length=1, max_length=100)
    course_id: Optional[str] = Field(None, description="Associated course ID")
    instructor_id: Optional[str] = Field(None, description="Instructor ID")
    class_type: Optional[ClassType] = Field(None, description="Class type")
    capacity: Optional[int] = Field(None, description="Class capacity", ge=1)
    schedule: Optional[str] = Field(None, description="Class schedule")
    location: Optional[str] = Field(None, description="Class location")
    start_time: Optional[time] = Field(None, description="Start time")
    end_time: Optional[time] = Field(None, description="End time")
    days_of_week: Optional[List[str]] = Field(None, description="Days of week")
    semester: Optional[str] = Field(None, description="Semester")
    academic_year: Optional[int] = Field(None, description="Academic year")
    description: Optional[str] = Field(None, description="Class description")
    status: Optional[ClassStatus] = Field(None, description="Class status")
    
    model_config = ConfigDict(from_attributes=True)


class ClassResponse(BaseModel):
    """Class response schema."""
    id: str = Field(..., description="Class ID")
    name: str = Field(..., description="Class name")
    course_id: str = Field(..., description="Associated course ID")
    instructor_id: str = Field(..., description="Instructor ID")
    class_type: ClassType = Field(..., description="Class type")
    capacity: int = Field(..., description="Class capacity")
    current_enrollment: int = Field(..., description="Current enrollment")
    schedule: str = Field(..., description="Class schedule")
    location: str = Field(..., description="Class location")
    start_time: time = Field(..., description="Start time")
    end_time: time = Field(..., description="End time")
    days_of_week: List[str] = Field(..., description="Days of week")
    semester: str = Field(..., description="Semester")
    academic_year: int = Field(..., description="Academic year")
    description: Optional[str] = Field(None, description="Class description")
    status: ClassStatus = Field(..., description="Class status")
    created_at: datetime = Field(..., description="Creation timestamp")
    updated_at: datetime = Field(..., description="Last update timestamp")
    
    model_config = ConfigDict(from_attributes=True)


class ClassStats(BaseModel):
    """Class statistics schema."""
    class_id: str = Field(..., description="Class ID")
    class_name: str = Field(..., description="Class name")
    total_enrollments: int = Field(..., description="Total enrollments", ge=0)
    active_enrollments: int = Field(..., description="Active enrollments", ge=0)
    attendance_rate: float = Field(..., description="Attendance rate", ge=0.0, le=1.0)
    average_score: float = Field(..., description="Average score", ge=0.0, le=100.0)
    completion_rate: float = Field(..., description="Completion rate", ge=0.0, le=1.0)
    instructor_id: str = Field(..., description="Instructor ID")
    course_id: str = Field(..., description="Course ID")
    department_id: str = Field(..., description="Department ID")
    semester: str = Field(..., description="Semester")
    academic_year: int = Field(..., description="Academic year")
    created_at: datetime = Field(..., description="Creation timestamp")
    updated_at: datetime = Field(..., description="Last update timestamp")
    
    model_config = ConfigDict(from_attributes=True)


class AttendanceRecord(BaseModel):
    """Attendance record schema."""
    id: str = Field(..., description="Attendance record ID")
    class_id: str = Field(..., description="Class ID")
    student_id: str = Field(..., description="Student ID")
    attendance_status: str = Field(..., description="Attendance status")
    attendance_date: date = Field(..., description="Attendance date")
    notes: Optional[str] = Field(None, description="Notes")
    recorded_by: str = Field(..., description="Recorded by")
    recorded_at: datetime = Field(..., description="Recorded at")
    
    model_config = ConfigDict(from_attributes=True)