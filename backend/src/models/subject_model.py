"""
Subject Management Models

This module defines Pydantic models for subject management:
- Subject creation, update, and response schemas
- Course outcomes and program objectives mapping
- Subject statistics and reporting models

Author: Edu-Flow Team
"""

from datetime import datetime
from typing import Optional, List
from uuid import uuid4
from enum import Enum
from pydantic import BaseModel, Field, ConfigDict


class SubjectStatus(str, Enum):
    """Subject status enumeration."""
    ACTIVE = "active"
    INACTIVE = "inactive"
    ARCHIVED = "archived"


class SubjectCreate(BaseModel):
    """Subject creation schema."""
    name: str = Field(..., description="Subject name", min_length=1, max_length=200)
    code: str = Field(..., description="Subject code", min_length=3, max_length=20)
    department_id: str = Field(..., description="Department ID")
    credits: int = Field(..., description="Subject credits", ge=1)
    level: str = Field(..., description="Subject level")
    description: Optional[str] = Field(None, description="Subject description")
    prerequisites: Optional[List[str]] = Field(None, description="Prerequisites")
    syllabus: Optional[str] = Field(None, description="Syllabus")
    status: SubjectStatus = Field(SubjectStatus.ACTIVE, description="Subject status")
    
    model_config = ConfigDict(from_attributes=True)


class SubjectUpdate(BaseModel):
    """Subject update schema."""
    name: Optional[str] = Field(None, description="Subject name", min_length=1, max_length=200)
    code: Optional[str] = Field(None, description="Subject code", min_length=3, max_length=20)
    department_id: Optional[str] = Field(None, description="Department ID")
    credits: Optional[int] = Field(None, description="Subject credits", ge=1)
    level: Optional[str] = Field(None, description="Subject level")
    description: Optional[str] = Field(None, description="Subject description")
    prerequisites: Optional[List[str]] = Field(None, description="Prerequisites")
    syllabus: Optional[str] = Field(None, description="Syllabus")
    status: Optional[SubjectStatus] = Field(None, description="Subject status")
    
    model_config = ConfigDict(from_attributes=True)


class SubjectResponse(BaseModel):
    """Subject response schema."""
    id: str = Field(..., description="Subject ID")
    name: str = Field(..., description="Subject name")
    code: str = Field(..., description="Subject code")
    department_id: str = Field(..., description="Department ID")
    credits: int = Field(..., description="Subject credits")
    level: str = Field(..., description="Subject level")
    description: Optional[str] = Field(None, description="Subject description")
    prerequisites: Optional[List[str]] = Field(None, description="Prerequisites")
    syllabus: Optional[str] = Field(None, description="Syllabus")
    status: SubjectStatus = Field(..., description="Subject status")
    created_at: datetime = Field(..., description="Creation timestamp")
    updated_at: datetime = Field(..., description="Last update timestamp")
    
    model_config = ConfigDict(from_attributes=True)


class SubjectStats(BaseModel):
    """Subject statistics schema."""
    subject_id: str = Field(..., description="Subject ID")
    subject_name: str = Field(..., description="Subject name")
    subject_code: str = Field(..., description="Subject code")
    total_enrollments: int = Field(..., description="Total enrollments", ge=0)
    active_enrollments: int = Field(..., description="Active enrollments", ge=0)
    average_score: float = Field(..., description="Average score", ge=0.0, le=100.0)
    completion_rate: float = Field(..., description="Completion rate", ge=0.0, le=1.0)
    department_id: str = Field(..., description="Department ID")
    total_classes: int = Field(..., description="Total classes", ge=0)
    pass_rate: float = Field(..., description="Pass rate", ge=0.0, le=1.0)
    created_at: datetime = Field(..., description="Creation timestamp")
    updated_at: datetime = Field(..., description="Last update timestamp")
    
    model_config = ConfigDict(from_attributes=True)