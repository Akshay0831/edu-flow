"""
Teacher Management Models

This module defines Pydantic models for teacher management:
- Teacher creation, update, and response schemas
- Qualification and certification models
- Teacher statistics and analytics

Author: Edu-Flow Team
"""

from datetime import datetime
from typing import Optional, List
from uuid import uuid4
from enum import Enum
from pydantic import BaseModel, Field, ConfigDict


class TeacherStatus(str, Enum):
    """Teacher status enumeration."""
    ACTIVE = "active"
    INACTIVE = "inactive"
    ON_LEAVE = "on_leave"
    RETIRED = "retired"
    SUSPENDED = "suspended"


class EmploymentType(str, Enum):
    """Employment type enumeration."""
    FULL_TIME = "full_time"
    PART_TIME = "part_time"
    CONTRACT = "contract"
    VISITING = "visiting"


class QualificationLevel(str, Enum):
    """Qualification level enumeration."""
    BACHELOR = "bachelor"
    MASTER = "master"
    PHD = "phd"
    POSTDOC = "postdoc"
    OTHER = "other"


class TeacherCreate(BaseModel):
    """Teacher creation schema."""
    user_id: str = Field(..., description="User ID")
    employee_id: str = Field(..., description="Employee ID", min_length=1, max_length=50)
    first_name: str = Field(..., description="First name", min_length=1, max_length=50)
    last_name: str = Field(..., description="Last name", min_length=1, max_length=50)
    email: str = Field(..., description="Email")
    phone: Optional[str] = Field(None, description="Phone")
    department_id: str = Field(..., description="Department ID")
    employment_type: EmploymentType = Field(EmploymentType.FULL_TIME, description="Employment type")
    status: TeacherStatus = Field(TeacherStatus.ACTIVE, description="Status")
    specialization: Optional[str] = Field(None, description="Specialization")
    experience_years: int = Field(..., description="Experience years", ge=0)
    qualifications: Optional[List[str]] = Field(None, description="Qualifications")
    certifications: Optional[List[str]] = Field(None, description="Certifications")
    bio: Optional[str] = Field(None, description="Biography")
    research_interests: Optional[List[str]] = Field(None, description="Research interests")
    office_location: Optional[str] = Field(None, description="Office location")
    office_hours: Optional[str] = Field(None, description="Office hours")
    
    model_config = ConfigDict(from_attributes=True)


class TeacherUpdate(BaseModel):
    """Teacher update schema."""
    user_id: Optional[str] = Field(None, description="User ID")
    employee_id: Optional[str] = Field(None, description="Employee ID", min_length=1, max_length=50)
    first_name: Optional[str] = Field(None, description="First name", min_length=1, max_length=50)
    last_name: Optional[str] = Field(None, description="Last name", min_length=1, max_length=50)
    email: Optional[str] = Field(None, description="Email")
    phone: Optional[str] = Field(None, description="Phone")
    department_id: Optional[str] = Field(None, description="Department ID")
    employment_type: Optional[EmploymentType] = Field(None, description="Employment type")
    status: Optional[TeacherStatus] = Field(None, description="Status")
    specialization: Optional[str] = Field(None, description="Specialization")
    experience_years: Optional[int] = Field(None, description="Experience years", ge=0)
    qualifications: Optional[List[str]] = Field(None, description="Qualifications")
    certifications: Optional[List[str]] = Field(None, description="Certifications")
    bio: Optional[str] = Field(None, description="Biography")
    research_interests: Optional[List[str]] = Field(None, description="Research interests")
    office_location: Optional[str] = Field(None, description="Office location")
    office_hours: Optional[str] = Field(None, description="Office hours")
    
    model_config = ConfigDict(from_attributes=True)


class TeacherResponse(BaseModel):
    """Teacher response schema."""
    id: str = Field(..., description="Teacher ID")
    user_id: str = Field(..., description="User ID")
    employee_id: str = Field(..., description="Employee ID")
    first_name: str = Field(..., description="First name")
    last_name: str = Field(..., description="Last name")
    full_name: str = Field(..., description="Full name")
    email: str = Field(..., description="Email")
    phone: Optional[str] = Field(None, description="Phone")
    department_id: str = Field(..., description="Department ID")
    department_name: Optional[str] = Field(None, description="Department name")
    employment_type: EmploymentType = Field(..., description="Employment type")
    status: TeacherStatus = Field(..., description="Status")
    specialization: Optional[str] = Field(None, description="Specialization")
    experience_years: int = Field(..., description="Experience years")
    qualifications: Optional[List[str]] = Field(None, description="Qualifications")
    certifications: Optional[List[str]] = Field(None, description="Certifications")
    bio: Optional[str] = Field(None, description="Biography")
    research_interests: Optional[List[str]] = Field(None, description="Research interests")
    office_location: Optional[str] = Field(None, description="Office location")
    office_hours: Optional[str] = Field(None, description="Office hours")
    created_at: datetime = Field(..., description="Creation timestamp")
    updated_at: datetime = Field(..., description="Last update timestamp")
    
    model_config = ConfigDict(from_attributes=True)


class TeacherQualification(BaseModel):
    """Teacher qualification schema."""
    id: str = Field(..., description="Qualification ID")
    teacher_id: str = Field(..., description="Teacher ID")
    degree: str = Field(..., description="Degree")
    institution: str = Field(..., description="Institution")
    field_of_study: str = Field(..., description="Field of study")
    graduation_year: int = Field(..., description="Graduation year")
    gpa: Optional[float] = Field(None, description="GPA", ge=0.0, le=4.0)
    certificate_number: Optional[str] = Field(None, description="Certificate number")
    verification_status: str = Field(..., description="Verification status")
    created_at: datetime = Field(..., description="Creation timestamp")
    updated_at: datetime = Field(..., description="Last update timestamp")
    
    model_config = ConfigDict(from_attributes=True)


class TeacherStats(BaseModel):
    """Teacher statistics schema."""
    teacher_id: str = Field(..., description="Teacher ID")
    teacher_name: str = Field(..., description="Teacher name")
    department_id: str = Field(..., description="Department ID")
    department_name: str = Field(..., description="Department name")
    total_courses: int = Field(..., description="Total courses", ge=0)
    active_courses: int = Field(..., description="Active courses", ge=0)
    total_students: int = Field(..., description="Total students", ge=0)
    average_student_rating: float = Field(..., description="Average student rating", ge=0.0, le=5.0)
    total_classes: int = Field(..., description="Total classes", ge=0)
    average_attendance: float = Field(..., description="Average attendance", ge=0.0, le=100.0)
    publications_count: int = Field(..., description="Publications count", ge=0)
    research_grants: int = Field(..., description="Research grants", ge=0)
    created_at: datetime = Field(..., description="Creation timestamp")
    updated_at: datetime = Field(..., description="Last update timestamp")
    
    model_config = ConfigDict(from_attributes=True)