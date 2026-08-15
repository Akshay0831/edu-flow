"""
Course Progress Model

This module defines Pydantic models for course progress tracking:
- Student progress tracking and completion status
- Progress metrics and analytics
- Performance tracking schemas

Author: Edu-Flow Team
"""

from datetime import datetime
from typing import Optional
from pydantic import BaseModel, Field, ConfigDict


class CourseProgress(BaseModel):
    """Course progress schema for student tracking"""
    course_id: str = Field(..., description="Course identifier")
    student_id: str = Field(..., description="Student identifier")
    course_name: str = Field(..., description="Course name")
    total_assignments: int = Field(..., description="Total number of assignments", ge=0)
    completed_assignments: int = Field(..., description="Number of completed assignments", ge=0)
    progress_percentage: float = Field(..., description="Progress percentage", ge=0.0, le=100.0)
    average_score: float = Field(..., description="Average score", ge=0.0, le=100.0)
    last_updated: datetime = Field(..., description="Last update timestamp")
    
    model_config = ConfigDict(from_attributes=True)