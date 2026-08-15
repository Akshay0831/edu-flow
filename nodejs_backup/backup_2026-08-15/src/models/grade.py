"""
Grade Management Models

This module defines Pydantic models for grade management:
- Grade creation, update, and response schemas
- Grade distribution and statistics
- Grading scale configuration

Author: Edu-Flow Team
"""

from datetime import datetime
from typing import Optional, List, Dict, Any
from enum import Enum
from uuid import uuid4
from pydantic import BaseModel, Field, ConfigDict


class GradeScale(str, Enum):
    """Grade scale enumeration."""
    LETTER = "letter"
    NUMERICAL = "numerical"
    PASS_FAIL = "pass_fail"
    PERCENTAGE = "percentage"


class GradeStatus(str, Enum):
    """Grade status enumeration."""
    PENDING = "pending"
    CALCULATED = "calculated"
    FINALIZED = "finalized"
    APPEALED = "appealed"
    UPDATED = "updated"


class GradeCreate(BaseModel):
    """Grade creation schema."""
    student_id: str = Field(..., description="Student ID")
    course_id: str = Field(..., description="Course ID")
    subject_id: str = Field(..., description="Subject ID")
    assessment_id: str = Field(..., description="Assessment ID")
    mark_value: float = Field(..., description="Mark value", ge=0.0, le=100.0)
    max_mark: float = Field(..., description="Maximum mark", ge=0.0)
    weight: float = Field(..., description="Weight", ge=0.0, le=1.0)
    grade: str = Field(..., description="Grade")
    grade_scale: GradeScale = Field(..., description="Grade scale")
    semester: str = Field(..., description="Semester")
    academic_year: int = Field(..., description="Academic year")
    instructor_id: str = Field(..., description="Instructor ID")
    status: GradeStatus = Field(GradeStatus.PENDING, description="Grade status")
    feedback: Optional[str] = Field(None, description="Feedback")
    
    model_config = ConfigDict(from_attributes=True)


class GradeUpdate(BaseModel):
    """Grade update schema."""
    student_id: Optional[str] = Field(None, description="Student ID")
    course_id: Optional[str] = Field(None, description="Course ID")
    subject_id: Optional[str] = Field(None, description="Subject ID")
    assessment_id: Optional[str] = Field(None, description="Assessment ID")
    mark_value: Optional[float] = Field(None, description="Mark value", ge=0.0, le=100.0)
    max_mark: Optional[float] = Field(None, description="Maximum mark", ge=0.0)
    weight: Optional[float] = Field(None, description="Weight", ge=0.0, le=1.0)
    grade: Optional[str] = Field(None, description="Grade")
    grade_scale: Optional[GradeScale] = Field(None, description="Grade scale")
    semester: Optional[str] = Field(None, description="Semester")
    academic_year: Optional[int] = Field(None, description="Academic year")
    instructor_id: Optional[str] = Field(None, description="Instructor ID")
    status: Optional[GradeStatus] = Field(None, description="Grade status")
    feedback: Optional[str] = Field(None, description="Feedback")
    
    model_config = ConfigDict(from_attributes=True)


class GradeResponse(BaseModel):
    """Grade response schema."""
    id: str = Field(..., description="Grade ID")
    student_id: str = Field(..., description="Student ID")
    course_id: str = Field(..., description="Course ID")
    subject_id: str = Field(..., description="Subject ID")
    assessment_id: str = Field(..., description="Assessment ID")
    mark_value: float = Field(..., description="Mark value", ge=0.0, le=100.0)
    max_mark: float = Field(..., description="Maximum mark", ge=0.0)
    weight: float = Field(..., description="Weight", ge=0.0, le=1.0)
    grade: str = Field(..., description="Grade")
    grade_scale: GradeScale = Field(..., description="Grade scale")
    percentage: float = Field(..., description="Percentage", ge=0.0, le=100.0)
    semester: str = Field(..., description="Semester")
    academic_year: int = Field(..., description="Academic year")
    instructor_id: str = Field(..., description="Instructor ID")
    status: GradeStatus = Field(..., description="Grade status")
    feedback: Optional[str] = Field(None, description="Feedback")
    created_at: datetime = Field(..., description="Creation timestamp")
    updated_at: datetime = Field(..., description="Last update timestamp")
    
    model_config = ConfigDict(from_attributes=True)


class GradeStats(BaseModel):
    """Grade statistics schema."""
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
    final_grade: str = Field(..., description="Final grade")
    final_percentage: float = Field(..., description="Final percentage", ge=0.0, le=100.0)
    pass_status: bool = Field(..., description="Pass status")
    created_at: datetime = Field(..., description="Creation timestamp")
    updated_at: datetime = Field(..., description="Last update timestamp")
    
    model_config = ConfigDict(from_attributes=True)


class GradeDistribution(BaseModel):
    """Grade distribution schema."""
    grade_range: str = Field(..., description="Grade range")
    count: int = Field(..., description="Count", ge=0)
    percentage: float = Field(..., description="Percentage", ge=0.0, le=100.0)
    min_mark: float = Field(..., description="Minimum mark", ge=0.0)
    max_mark: float = Field(..., description="Maximum mark", ge=0.0)
    average_mark: float = Field(..., description="Average mark", ge=0.0, le=100.0)
    
    model_config = ConfigDict(from_attributes=True)


class GradePolicy(BaseModel):
    """Grade policy schema."""
    id: str = Field(..., description="Grade policy ID")
    name: str = Field(..., description="Policy name", min_length=1, max_length=100)
    description: str = Field(..., description="Policy description")
    department_id: str = Field(..., description="Department ID")
    program_id: str = Field(..., description="Program ID")
    academic_year: int = Field(..., description="Academic year")
    semester: str = Field(..., description="Semester")
    grade_scale: GradeScale = Field(..., description="Grade scale")
    passing_grade: str = Field(..., description="Passing grade")
    minimum_passing_mark: float = Field(..., description="Minimum passing mark", ge=0.0)
    max_marks: float = Field(..., description="Maximum marks", ge=0.0)
    weight_policy: Dict[str, float] = Field(..., description="Weight policy")
    bonus_policy: Optional[Dict[str, float]] = Field(None, description="Bonus policy")
    penalty_policy: Optional[Dict[str, float]] = Field(None, description="Penalty policy")
    is_active: bool = Field(True, description="Is active")
    created_by: str = Field(..., description="Created by")
    created_at: datetime = Field(..., description="Creation timestamp")
    updated_at: datetime = Field(..., description="Last update timestamp")
    
    model_config = ConfigDict(from_attributes=True)


class GradeCalculation(BaseModel):
    """Grade calculation schema."""
    id: str = Field(..., description="Calculation ID")
    student_id: str = Field(..., description="Student ID")
    course_id: str = Field(..., description="Course ID")
    subject_id: str = Field(..., description="Subject ID")
    semester: str = Field(..., description="Semester")
    academic_year: int = Field(..., description="Academic year")
    assessment_count: int = Field(..., description="Assessment count", ge=0)
    total_weight: float = Field(..., description="Total weight", ge=0.0)
    weighted_sum: float = Field(..., description="Weighted sum", ge=0.0)
    average_mark: float = Field(..., description="Average mark", ge=0.0, le=100.0)
    final_grade: str = Field(..., description="Final grade")
    grade_status: str = Field(..., description="Grade status")
    calculation_method: str = Field(..., description="Calculation method")
    calculated_by: str = Field(..., description="Calculated by")
    calculated_at: datetime = Field(..., description="Calculation timestamp")
    
    model_config = ConfigDict(from_attributes=True)


class GradeAnalytics(BaseModel):
    """Grade analytics schema."""
    course_id: str = Field(..., description="Course ID")
    subject_id: str = Field(..., description="Subject ID")
    semester: str = Field(..., description="Semester")
    academic_year: int = Field(..., description="Academic year")
    total_students: int = Field(..., description="Total students", ge=0)
    pass_students: int = Field(..., description="Pass students", ge=0)
    fail_students: int = Field(..., description="Fail students", ge=0)
    average_marks: float = Field(..., description="Average marks", ge=0.0, le=100.0)
    highest_marks: float = Field(..., description="Highest marks", ge=0.0, le=100.0)
    lowest_marks: float = Field(..., description="Lowest marks", ge=0.0, le=100.0)
    pass_rate: float = Field(..., description="Pass rate", ge=0.0, le=1.0)
    grade_distribution: Dict[str, int] = Field(..., description="Grade distribution")
    standard_deviation: float = Field(..., description="Standard deviation", ge=0.0)
    median_marks: float = Field(..., description="Median marks", ge=0.0, le=100.0)
    mode_grade: str = Field(..., description="Mode grade")
    created_at: datetime = Field(..., description="Creation timestamp")
    updated_at: datetime = Field(..., description="Last update timestamp")
    
    model_config = ConfigDict(from_attributes=True)


class GradeStatistics(BaseModel):
    """Grade statistics schema."""
    student_id: str = Field(..., description="Student ID")
    course_id: str = Field(..., description="Course ID")
    subject_id: str = Field(..., description="Subject ID")
    semester: str = Field(..., description="Semester")
    academic_year: int = Field(..., description="Academic year")
    assessment_count: int = Field(..., description="Assessment count", ge=0)
    completed_assessments: int = Field(..., description="Completed assessments", ge=0)
    missing_assessments: int = Field(..., description="Missing assessments", ge=0)
    current_average: float = Field(..., description="Current average", ge=0.0, le=100.0)
    projected_final: float = Field(..., description="Projected final", ge=0.0, le=100.0)
    grade_trend: str = Field(..., description="Grade trend")
    improvement_needed: bool = Field(..., description="Improvement needed")
    recommended_grade: str = Field(..., description="Recommended grade")
    created_at: datetime = Field(..., description="Creation timestamp")
    updated_at: datetime = Field(..., description="Last update timestamp")
    
    model_config = ConfigDict(from_attributes=True)


class GradeTrend(BaseModel):
    """Grade trend schema."""
    student_id: str = Field(..., description="Student ID")
    course_id: str = Field(..., description="Course ID")
    subject_id: str = Field(..., description="Subject ID")
    semester: str = Field(..., description="Semester")
    academic_year: int = Field(..., description="Academic year")
    assessment_results: List[Dict[str, Any]] = Field(..., description="Assessment results")
    trend_direction: str = Field(..., description="Trend direction")
    trend_strength: str = Field(..., description="Trend strength")
    consistency_score: float = Field(..., description="Consistency score", ge=0.0, le=1.0)
    predicted_final: float = Field(..., description="Predicted final", ge=0.0, le=100.0)
    confidence_level: float = Field(..., description="Confidence level", ge=0.0, le=1.0)
    created_at: datetime = Field(..., description="Creation timestamp")
    updated_at: datetime = Field(..., description="Last update timestamp")
    
    model_config = ConfigDict(from_attributes=True)


class StudentGradeSummary(BaseModel):
    """Student grade summary schema."""
    student_id: str = Field(..., description="Student ID")
    student_name: str = Field(..., description="Student name")
    total_courses: int = Field(..., description="Total courses", ge=0)
    passed_courses: int = Field(..., description="Passed courses", ge=0)
    failed_courses: int = Field(..., description="Failed courses", ge=0)
    current_gpa: float = Field(..., description="Current GPA", ge=0.0, le=4.0)
    semester_gpa: float = Field(..., description="Semester GPA", ge=0.0, le=4.0)
    overall_gpa: float = Field(..., description="Overall GPA", ge=0.0, le=4.0)
    credit_hours_completed: int = Field(..., description="Credit hours completed", ge=0)
    total_credit_hours: int = Field(..., description="Total credit hours", ge=0)
    semester: str = Field(..., description="Semester")
    academic_year: int = Field(..., description="Academic year")
    standing: str = Field(..., description="Standing")
    honors_status: str = Field(..., description="Honors status")
    created_at: datetime = Field(..., description="Creation timestamp")
    updated_at: datetime = Field(..., description="Last update timestamp")
    
    model_config = ConfigDict(from_attributes=True)


class ClassGradeSummary(BaseModel):
    """Class grade summary schema."""
    class_id: str = Field(..., description="Class ID")
    class_name: str = Field(..., description="Class name")
    course_id: str = Field(..., description="Course ID")
    instructor_id: str = Field(..., description="Instructor ID")
    semester: str = Field(..., description="Semester")
    academic_year: int = Field(..., description="Academic year")
    total_students: int = Field(..., description="Total students", ge=0)
    present_students: int = Field(..., description="Present students", ge=0)
    absent_students: int = Field(..., description="Absent students", ge=0)
    average_attendance: float = Field(..., description="Average attendance", ge=0.0, le=100.0)
    total_assessments: int = Field(..., description="Total assessments", ge=0)
    completed_assessments: int = Field(..., description="Completed assessments", ge=0)
    class_average: float = Field(..., description="Class average", ge=0.0, le=100.0)
    highest_score: float = Field(..., description="Highest score", ge=0.0, le=100.0)
    lowest_score: float = Field(..., description="Lowest score", ge=0.0, le=100.0)
    pass_rate: float = Field(..., description="Pass rate", ge=0.0, le=1.0)
    grade_distribution: Dict[str, int] = Field(..., description="Grade distribution")
    created_at: datetime = Field(..., description="Creation timestamp")
    updated_at: datetime = Field(..., description="Last update timestamp")
    
    model_config = ConfigDict(from_attributes=True)


class SubjectGradeSummary(BaseModel):
    """Subject grade summary schema."""
    subject_id: str = Field(..., description="Subject ID")
    subject_name: str = Field(..., description="Subject name")
    course_id: str = Field(..., description="Course ID")
    department_id: str = Field(..., description="Department ID")
    semester: str = Field(..., description="Semester")
    academic_year: int = Field(..., description="Academic year")
    total_students: int = Field(..., description="Total students", ge=0)
    total_classes: int = Field(..., description="Total classes", ge=0)
    average_attendance: float = Field(..., description="Average attendance", ge=0.0, le=100.0)
    total_assessments: int = Field(..., description="Total assessments", ge=0)
    completed_assessments: int = Field(..., description="Completed assessments", ge=0)
    subject_average: float = Field(..., description="Subject average", ge=0.0, le=100.0)
    highest_score: float = Field(..., description="Highest score", ge=0.0, le=100.0)
    lowest_score: float = Field(..., description="Lowest score", ge=0.0, le=100.0)
    pass_rate: float = Field(..., description="Pass rate", ge=0.0, le=1.0)
    grade_distribution: Dict[str, int] = Field(..., description="Grade distribution")
    created_at: datetime = Field(..., description="Creation timestamp")
    updated_at: datetime = Field(..., description="Last update timestamp")
    
    model_config = ConfigDict(from_attributes=True)