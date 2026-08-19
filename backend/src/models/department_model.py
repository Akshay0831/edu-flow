"""
Department Management Models

This module defines Pydantic models for department management:
- Department creation, update, and response schemas
- Department statistics and reporting models
- Faculty and student metrics

Author: Edu-Flow Team
"""

from datetime import datetime
from typing import Optional, List
from uuid import uuid4
from enum import Enum
from pydantic import BaseModel, Field, ConfigDict


class DepartmentStatus(str, Enum):
    """Department status enumeration."""
    ACTIVE = "active"
    INACTIVE = "inactive"
    ARCHIVED = "archived"


class DepartmentCreate(BaseModel):
    """Department creation schema."""
    name: str = Field(..., description="Department name", min_length=1, max_length=100)
    code: str = Field(..., description="Department code", min_length=2, max_length=10)
    description: Optional[str] = Field(None, description="Department description")
    head_id: Optional[str] = Field(None, description="Department head ID")
    contact_email: Optional[str] = Field(None, description="Contact email")
    contact_phone: Optional[str] = Field(None, description="Contact phone")
    location: Optional[str] = Field(None, description="Location")
    status: DepartmentStatus = Field(DepartmentStatus.ACTIVE, description="Department status")
    
    model_config = ConfigDict(from_attributes=True)


class DepartmentUpdate(BaseModel):
    """Department update schema."""
    name: Optional[str] = Field(None, description="Department name", min_length=1, max_length=100)
    code: Optional[str] = Field(None, description="Department code", min_length=2, max_length=10)
    description: Optional[str] = Field(None, description="Department description")
    head_id: Optional[str] = Field(None, description="Department head ID")
    contact_email: Optional[str] = Field(None, description="Contact email")
    contact_phone: Optional[str] = Field(None, description="Contact phone")
    location: Optional[str] = Field(None, description="Location")
    status: Optional[DepartmentStatus] = Field(None, description="Department status")
    
    model_config = ConfigDict(from_attributes=True)


class DepartmentResponse(BaseModel):
    """Department response schema."""
    id: str = Field(..., description="Department ID")
    name: str = Field(..., description="Department name")
    code: str = Field(..., description="Department code")
    description: Optional[str] = Field(None, description="Department description")
    head_id: Optional[str] = Field(None, description="Department head ID")
    contact_email: Optional[str] = Field(None, description="Contact email")
    contact_phone: Optional[str] = Field(None, description="Contact phone")
    location: Optional[str] = Field(None, description="Location")
    status: DepartmentStatus = Field(..., description="Department status")
    created_at: datetime = Field(..., description="Creation timestamp")
    updated_at: datetime = Field(..., description="Last update timestamp")
    
    model_config = ConfigDict(from_attributes=True)


class DepartmentStats(BaseModel):
    """Department statistics schema."""
    department_id: str = Field(..., description="Department ID")
    department_name: str = Field(..., description="Department name")
    department_code: str = Field(..., description="Department code")
    total_students: int = Field(..., description="Total students", ge=0)
    active_students: int = Field(..., description="Active students", ge=0)
    total_teachers: int = Field(..., description="Total teachers", ge=0)
    active_teachers: int = Field(..., description="Active teachers", ge=0)
    total_subjects: int = Field(..., description="Total subjects", ge=0)
    active_subjects: int = Field(..., description="Active subjects", ge=0)
    total_courses: int = Field(..., description="Total courses", ge=0)
    active_courses: int = Field(..., description="Active courses", ge=0)
    average_gpa: float = Field(..., description="Average GPA", ge=0.0, le=4.0)
    graduation_rate: float = Field(..., description="Graduation rate", ge=0.0, le=1.0)
    created_at: datetime = Field(..., description="Creation timestamp")
    updated_at: datetime = Field(..., description="Last update timestamp")
    
    model_config = ConfigDict(from_attributes=True)