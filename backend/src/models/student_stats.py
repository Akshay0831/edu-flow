"""
Student Statistics Model

This module defines Pydantic models for student statistics and analytics:
- Student performance tracking and reporting
- Academic statistics and trends
- Analytics and reporting schemas

Author: Edu-Flow Team
"""

from datetime import datetime
from typing import Optional
from pydantic import BaseModel, Field, ConfigDict
from .student import GradeLevel


class StudentStats(BaseModel):
    """Student statistics schema for academic performance tracking"""
    student_id: str = Field(..., description="Student identifier")
    student_name: str = Field(..., description="Student name")
    total_courses: int = Field(..., description="Total courses taken", ge=0)
    total_marks: int = Field(..., description="Total marks/grades", ge=0)
    average_score: float = Field(..., description="Average score", ge=0.0, le=100.0)
    gpa: float = Field(..., description="Grade point average", ge=0.0, le=4.0)
    registration_date: datetime = Field(..., description="Registration date")
    last_activity: datetime = Field(..., description="Last activity date")
    
    model_config = ConfigDict(from_attributes=True)