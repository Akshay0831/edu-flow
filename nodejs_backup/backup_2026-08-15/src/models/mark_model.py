"""
Mark Management Models

This module defines Pydantic models for mark management:
- Mark creation, update, and response schemas
- Grade distribution and statistics
- Assessment scoring models

Author: Edu-Flow Team
"""

from datetime import datetime
from typing import Optional, List, Dict, Any
from enum import Enum
from uuid import uuid4
from pydantic import BaseModel, Field, ConfigDict


class Grade(str, Enum):
    """Grade enumeration."""
    A = "A"
    B = "B"
    C = "C"
    D = "D"
    E = "E"
    F = "F"
    INC = "INCOMPLETE"
    AUD = "AUDIT"


class AssessmentType(str, Enum):
    """Assessment type enumeration."""
    QUIZ = "quiz"
    EXAM = "exam"
    ASSIGNMENT = "assignment"
    PROJECT = "project"
    LAB = "lab"
    PARTICIPATION = "participation"
    PRESENTATION = "presentation"


class MarkCreate(BaseModel):
    """Mark creation schema."""
    student_id: str = Field(..., description="Student ID")
    course_id: str = Field(..., description="Course ID")
    subject_id: str = Field(..., description="Subject ID")
    assessment_type: AssessmentType = Field(..., description="Assessment type")
    mark_value: float = Field(..., description="Mark value", ge=0.0, le=100.0)
    max_mark: float = Field(..., description="Maximum mark", ge=0.0)
    weight: float = Field(..., description="Weight", ge=0.0, le=1.0)
    grade: Grade = Field(..., description="Grade")
    semester: str = Field(..., description="Semester")
    academic_year: int = Field(..., description="Academic year")
    feedback: Optional[str] = Field(None, description="Feedback")
    instructor_id: str = Field(..., description="Instructor ID")
    
    model_config = ConfigDict(from_attributes=True)


class MarkUpdate(BaseModel):
    """Mark update schema."""
    student_id: Optional[str] = Field(None, description="Student ID")
    course_id: Optional[str] = Field(None, description="Course ID")
    subject_id: Optional[str] = Field(None, description="Subject ID")
    assessment_type: Optional[AssessmentType] = Field(None, description="Assessment type")
    mark_value: Optional[float] = Field(None, description="Mark value", ge=0.0, le=100.0)
    max_mark: Optional[float] = Field(None, description="Maximum mark", ge=0.0)
    weight: Optional[float] = Field(None, description="Weight", ge=0.0, le=1.0)
    grade: Optional[Grade] = Field(None, description="Grade")
    semester: Optional[str] = Field(None, description="Semester")
    academic_year: Optional[int] = Field(None, description="Academic year")
    feedback: Optional[str] = Field(None, description="Feedback")
    instructor_id: Optional[str] = Field(None, description="Instructor ID")
    
    model_config = ConfigDict(from_attributes=True)


class MarkResponse(BaseModel):
    """Mark response schema."""
    id: str = Field(..., description="Mark ID")
    student_id: str = Field(..., description="Student ID")
    course_id: str = Field(..., description="Course ID")
    subject_id: str = Field(..., description="Subject ID")
    assessment_type: AssessmentType = Field(..., description="Assessment type")
    mark_value: float = Field(..., description="Mark value", ge=0.0, le=100.0)
    max_mark: float = Field(..., description="Maximum mark", ge=0.0)
    weight: float = Field(..., description="Weight", ge=0.0, le=1.0)
    grade: Grade = Field(..., description="Grade")
    percentage: float = Field(..., description="Percentage", ge=0.0, le=100.0)
    semester: str = Field(..., description="Semester")
    academic_year: int = Field(..., description="Academic year")
    feedback: Optional[str] = Field(None, description="Feedback")
    instructor_id: str = Field(..., description="Instructor ID")
    created_at: datetime = Field(..., description="Creation timestamp")
    updated_at: datetime = Field(..., description="Last update timestamp")
    
    model_config = ConfigDict(from_attributes=True)


class MarkStats(BaseModel):
    """Mark statistics schema."""
    student_id: str = Field(..., description="Student ID")
    course_id: str = Field(..., description="Course ID")
    subject_id: str = Field(..., description="Subject ID")
    semester: str = Field(..., description="Semester")
    academic_year: int = Field(..., description="Academic year")
    total_assessments: int = Field(..., description="Total assessments", ge=0)
    average_mark: float = Field(..., description="Average mark", ge=0.0, le=100.0)
    average_percentage: float = Field(..., description="Average percentage", ge=0.0, le=100.0)
    highest_mark: float = Field(..., description="Highest mark", ge=0.0, le=100.0)
    lowest_mark: float = Field(..., description="Lowest mark", ge=0.0, le=100.0)
    standard_deviation: float = Field(..., description="Standard deviation", ge=0.0)
    grade_distribution: Dict[str, int] = Field(..., description="Grade distribution")
    total_weight: float = Field(..., description="Total weight", ge=0.0, le=1.0)
    final_grade: Grade = Field(..., description="Final grade")
    created_at: datetime = Field(..., description="Creation timestamp")
    updated_at: datetime = Field(..., description="Last update timestamp")
    
    model_config = ConfigDict(from_attributes=True)


class GradeDistribution(BaseModel):
    """Grade distribution schema."""
    grade: Grade = Field(..., description="Grade")
    count: int = Field(..., description="Count", ge=0)
    percentage: float = Field(..., description="Percentage", ge=0.0, le=100.0)
    min_mark: float = Field(..., description="Minimum mark", ge=0.0)
    max_mark: float = Field(..., description="Maximum mark", ge=0.0)
    average_mark: float = Field(..., description="Average mark", ge=0.0, le=100.0)
    
    model_config = ConfigDict(from_attributes=True)