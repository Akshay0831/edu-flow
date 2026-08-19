"""
Student Data Models

This module defines Pydantic models for student management operations:
- Student creation, update, and response schemas
- Academic record and performance models
- Enrollment and graduation requirement schemas
- Validation and serialization logic

Author: Edu-Flow Team
"""

from datetime import datetime, date
from typing import Optional, List, Dict, Any
from uuid import UUID
from pydantic import BaseModel, Field, field_validator, EmailStr, ConfigDict
from enum import Enum

class UserRole(str, Enum):
    """User role enumeration"""
    ADMIN = "admin"
    TEACHER = "teacher"
    STUDENT = "student"
    STAFF = "staff"

class GradeLevel(int, Enum):
    """Grade level enumeration"""
    NINTH = 9
    TENTH = 10
    ELEVENTH = 11
    TWELFTH = 12

class AcademicStanding(str, Enum):
    """Academic standing enumeration"""
    EXCELLENT = "excellent"
    GOOD = "good"
    SATISFACTORY = "satisfactory"
    NEEDS_IMPROVEMENT = "needs_improvement"
    POOR = "poor"
    ACADEMIC_PROBATION = "academic_probation"
    EXPELLATION = "expellation"

class EnrollmentStatus(str, Enum):
    """Enrollment status enumeration"""
    ACTIVE = "active"
    INACTIVE = "inactive"
    GRADUATED = "graduated"
    TRANSFERRED = "transferred"
    SUSPENDED = "suspended"
    WITHDRAWN = "withdrawn"

class RiskLevel(str, Enum):
    """Risk level enumeration for student interventions"""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"

# Base student schemas
class StudentBase(BaseModel):
    """Base student schema with common fields"""
    student_id: str = Field(..., description="Unique student identifier", min_length=3, max_length=20)
    grade_level: GradeLevel = Field(..., description="Current grade level (9-12)")
    enrollment_date: date = Field(..., description="Date of enrollment")
    department_id: Optional[str] = Field(None, description="Department assignment")
    advisor_id: Optional[str] = Field(None, description="Teacher/advisor assignment")
    gpa: Optional[float] = Field(None, description="Grade point average", ge=0.0, le=4.0)
    attendance_rate: Optional[float] = Field(None, description="Attendance rate", ge=0.0, le=1.0)
    academic_standing: Optional[AcademicStanding] = Field(None, description="Academic standing")
    notes: Optional[str] = Field(None, description="Additional notes")
    
    @field_validator('student_id')
    @classmethod
    def validate_student_id(cls, v):
        """Validate student ID format"""
        if not v.isalnum():
            raise ValueError("Student ID must be alphanumeric")
        return v.upper()

class StudentCreate(StudentBase):
    """Student creation schema"""
    email: EmailStr = Field(..., description="Student email address")
    password: str = Field(..., description="Student password", min_length=8)
    name: str = Field(..., description="Student full name", min_length=1, max_length=100)
    phone: Optional[str] = Field(None, description="Phone number")
    address: Optional[str] = Field(None, description="Address")
    emergency_contact: Optional[Dict[str, str]] = Field(None, description="Emergency contact information")
    medical_info: Optional[str] = Field(None, description="Medical information")
    family_info: Optional[Dict[str, Any]] = Field(None, description="Family information")
    preferences: Optional[Dict[str, Any]] = Field(None, description="Student preferences")
    
    @field_validator('password')
    @classmethod
    def validate_password(cls, v):
        """Validate password strength"""
        if len(v) < 8:
            raise ValueError("Password must be at least 8 characters")
        if not any(c.isupper() for c in v):
            raise ValueError("Password must contain at least one uppercase letter")
        if not any(c.islower() for c in v):
            raise ValueError("Password must contain at least one lowercase letter")
        if not any(c.isdigit() for c in v):
            raise ValueError("Password must contain at least one digit")
        return v

class StudentUpdate(BaseModel):
    """Student update schema"""
    name: Optional[str] = Field(None, description="Student full name", min_length=1, max_length=100)
    phone: Optional[str] = Field(None, description="Phone number")
    address: Optional[str] = Field(None, description="Address")
    department_id: Optional[str] = Field(None, description="Department assignment")
    advisor_id: Optional[str] = Field(None, description="Teacher/advisor assignment")
    gpa: Optional[float] = Field(None, description="Grade point average", ge=0.0, le=4.0)
    attendance_rate: Optional[float] = Field(None, description="Attendance rate", ge=0.0, le=1.0)
    academic_standing: Optional[AcademicStanding] = Field(None, description="Academic standing")
    notes: Optional[str] = Field(None, description="Additional notes")
    emergency_contact: Optional[Dict[str, str]] = Field(None, description="Emergency contact information")
    medical_info: Optional[str] = Field(None, description="Medical information")
    family_info: Optional[Dict[str, Any]] = Field(None, description="Family information")
    preferences: Optional[Dict[str, Any]] = Field(None, description="Student preferences")
    graduation_status: Optional[EnrollmentStatus] = Field(None, description="Graduation status")
    
    @field_validator('graduation_status')
    @classmethod
    def validate_graduation_status(cls, v):
        """Validate graduation status is only set for graduates"""
        if v and v != EnrollmentStatus.GRADUATED:
            raise ValueError("Only graduated students can have graduation status set")
        return v

class StudentResponse(StudentBase):
    """Student response schema (excludes sensitive data)"""
    id: str = Field(..., description="Unique student identifier")
    email: EmailStr = Field(..., description="Student email address")
    name: str = Field(..., description="Student full name")
    phone: Optional[str] = Field(None, description="Phone number")
    role: UserRole = Field(UserRole.STUDENT, description="User role")
    is_active: bool = Field(True, description="Account status")
    created_at: datetime = Field(..., description="Creation timestamp")
    updated_at: datetime = Field(..., description="Last update timestamp")
    last_login: Optional[datetime] = Field(None, description="Last login timestamp")
    
    model_config = ConfigDict(from_attributes=True)
    deactivated_at: Optional[datetime] = Field(None, description="Deactivation timestamp")

# Academic schemas
class AcademicRecord(BaseModel):
    """Academic record schema"""
    id: str = Field(..., description="Academic record identifier")
    student_id: str = Field(..., description="Student identifier")
    course_id: str = Field(..., description="Course identifier")
    grade: float = Field(..., description="Course grade", ge=0.0, le=100.0)
    credits: float = Field(..., description="Course credits", gt=0.0)
    semester: str = Field(..., description="Semester identifier")
    academic_year: str = Field(..., description="Academic year")
    grade_letter: Optional[str] = Field(None, description="Letter grade")
    grade_points: Optional[float] = Field(None, description="Grade points")
    instructor_id: Optional[str] = Field(None, description="Instructor identifier")
    comments: Optional[str] = Field(None, description="Instructor comments")
    submission_date: Optional[date] = Field(None, description="Submission date")
    
    @field_validator('grade')
    @classmethod
    def validate_grade(cls, v):
        """Validate grade is within valid range"""
        if v < 0 or v > 100:
            raise ValueError("Grade must be between 0 and 100")
        return v
    
    @field_validator('credits')
    @classmethod
    def validate_credits(cls, v):
        """Validate credits are positive"""
        if v <= 0:
            raise ValueError("Credits must be positive")
        return v

class EnrollmentRequest(BaseModel):
    """Course enrollment request schema"""
    student_id: str = Field(..., description="Student identifier")
    course_id: str = Field(..., description="Course identifier")
    semester: str = Field(..., description="Semester identifier")
    academic_year: str = Field(..., description="Academic year")
    priority: Optional[int] = Field(1, description="Enrollment priority", ge=1, le=10)
    special_accommodations: Optional[Dict[str, Any]] = Field(None, description="Special accommodations")
    
    @field_validator('student_id', 'course_id')
    @classmethod
    def validate_ids(cls, v):
        """Validate identifier formats"""
        if not v or len(v.strip()) == 0:
            raise ValueError("Identifier cannot be empty")
        return v

class EnrollmentRecord(BaseModel):
    """Enrollment record schema"""
    id: str = Field(..., description="Enrollment identifier")
    student_id: str = Field(..., description="Student identifier")
    course_id: str = Field(..., description="Course identifier")
    semester: str = Field(..., description="Semester identifier")
    academic_year: str = Field(..., description="Academic year")
    enrollment_date: date = Field(..., description="Enrollment date")
    status: EnrollmentStatus = Field(EnrollmentStatus.ACTIVE, description="Enrollment status")
    grade: Optional[float] = Field(None, description="Final grade", ge=0.0, le=100.0)
    credits_earned: Optional[float] = Field(None, description="Credits earned", ge=0.0)
    instructor_id: Optional[str] = Field(None, description="Instructor identifier")
    drop_date: Optional[date] = Field(None, description="Course drop date")
    comments: Optional[str] = Field(None, description="Comments")
    
    model_config = ConfigDict(from_attributes=True)

# Performance and analytics schemas
class PerformanceMetrics(BaseModel):
    """Student performance metrics schema"""
    student_id: str = Field(..., description="Student identifier")
    gpa: float = Field(..., description="Grade point average", ge=0.0, le=4.0)
    attendance_rate: float = Field(..., description="Attendance rate", ge=0.0, le=1.0)
    assignment_completion: float = Field(..., description="Assignment completion rate", ge=0.0, le=1.0)
    assessment_average: float = Field(..., description="Assessment average score", ge=0.0, le=100.0)
    improvement_trend: Optional[str] = Field(None, description="Performance trend")
    risk_level: Optional[RiskLevel] = Field(None, description="Risk level assessment")
    last_assessment_date: Optional[date] = Field(None, description="Last assessment date")
    next_review_date: Optional[date] = Field(None, description="Next review date")
    
    @field_validator('gpa')
    @classmethod
    def validate_gpa(cls, v):
        """Validate GPA range"""
        if v < 0.0 or v > 4.0:
            raise ValueError("GPA must be between 0.0 and 4.0")
        return v

class AcademicSummary(BaseModel):
    """Academic summary schema"""
    student_id: str = Field(..., description="Student identifier")
    total_credits: float = Field(..., description="Total credits earned", ge=0.0)
    total_courses: int = Field(..., description="Total courses taken", ge=0)
    gpa: float = Field(..., description="Grade point average", ge=0.0, le=4.0)
    academic_standing: AcademicStanding = Field(..., description="Academic standing")
    graduation_requirements: Dict[str, Any] = Field(..., description="Graduation requirements status")
    performance_trend: Optional[str] = Field(None, description="Performance trend")
    risk_factors: List[str] = Field(default_factory=list, description="Risk factors")
    recommendations: List[str] = Field(default_factory=list, description="Recommendations")
    
    model_config = ConfigDict(from_attributes=True)

# Graduation schemas
class GraduationRequirement(BaseModel):
    """Graduation requirement schema"""
    id: str = Field(..., description="Requirement identifier")
    requirement_name: str = Field(..., description="Requirement name")
    description: str = Field(..., description="Requirement description")
    required_value: float = Field(..., description="Required value")
    current_value: Optional[float] = Field(None, description="Current value")
    is_met: bool = Field(False, description="Whether requirement is met")
    is_completed: bool = Field(False, description="Whether requirement is completed")
    date_met: Optional[date] = Field(None, description="Date requirement was met")
    
    model_config = ConfigDict(from_attributes=True)

class GraduationStatus(BaseModel):
    """Graduation status schema"""
    student_id: str = Field(..., description="Student identifier")
    is_eligible: bool = Field(..., description="Whether student is eligible for graduation")
    requirements_met: int = Field(..., description="Number of requirements met")
    total_requirements: int = Field(..., description="Total requirements")
    missing_requirements: List[str] = Field(default_factory=list, description="Missing requirements")
    estimated_graduation_date: Optional[date] = Field(None, description="Estimated graduation date")
    graduation_date: Optional[date] = Field(None, description="Actual graduation date")
    honors_status: Optional[str] = Field(None, description="Graduation honors status")
    
    model_config = ConfigDict(from_attributes=True)

# Risk assessment schemas
class RiskAssessment(BaseModel):
    """Student risk assessment schema"""
    student_id: str = Field(..., description="Student identifier")
    risk_level: RiskLevel = Field(..., description="Risk level")
    risk_factors: List[str] = Field(default_factory=list, description="Risk factors")
    academic_performance_score: float = Field(..., description="Academic performance score", ge=0.0, le=100.0)
    attendance_score: float = Field(..., description="Attendance score", ge=0.0, le=100.0)
    behavior_score: float = Field(..., description="Behavior score", ge=0.0, le=100.0)
    social_emotional_score: float = Field(..., description="Social emotional score", ge=0.0, le=100.0)
    intervention_plan: Optional[Dict[str, Any]] = Field(None, description="Intervention plan")
    next_review_date: Optional[date] = Field(None, description="Next review date")
    
    model_config = ConfigDict(from_attributes=True)

# Utility schemas
class StudentSearch(BaseModel):
    """Student search criteria schema"""
    name: Optional[str] = Field(None, description="Student name (partial match)")
    email: Optional[EmailStr] = Field(None, description="Student email")
    student_id: Optional[str] = Field(None, description="Student ID")
    grade_level: Optional[GradeLevel] = Field(None, description="Grade level")
    department_id: Optional[str] = Field(None, description="Department ID")
    advisor_id: Optional[str] = Field(None, description="Advisor ID")
    is_active: Optional[bool] = Field(None, description="Active status")
    enrollment_status: Optional[EnrollmentStatus] = Field(None, description="Enrollment status")
    risk_level: Optional[RiskLevel] = Field(None, description="Risk level")
    created_after: Optional[datetime] = Field(None, description="Created after this date")
    created_before: Optional[datetime] = Field(None, description="Created before this date")
    limit: int = Field(100, description="Maximum results to return", ge=1, le=1000)
    offset: int = Field(0, description="Offset for pagination", ge=0)

class StudentStatistics(BaseModel):
    """Student statistics schema"""
    total_students: int = Field(..., description="Total number of students")
    active_students: int = Field(..., description="Number of active students")
    inactive_students: int = Field(..., description="Number of inactive students")
    by_grade_level: Dict[GradeLevel, int] = Field(..., description="Students by grade level")
    by_department: Dict[str, int] = Field(..., description="Students by department")
    by_advisor: Dict[str, int] = Field(..., description="Students by advisor")
    by_risk_level: Dict[RiskLevel, int] = Field(..., description="Students by risk level")
    average_gpa: float = Field(..., description="Average GPA across all students")
    average_attendance: float = Field(..., description="Average attendance rate")
    
    model_config = ConfigDict(from_attributes=True)

class StudentAudit(BaseModel):
    """Student audit trail schema"""
    audit_id: str = Field(..., description="Audit record identifier")
    student_id: str = Field(..., description="Student identifier")
    action: str = Field(..., description="Action performed")
    performed_by: str = Field(..., description="Who performed the action")
    details: Optional[Dict[str, Any]] = Field(None, description="Action details")
    timestamp: datetime = Field(..., description="Action timestamp")
    ip_address: Optional[str] = Field(None, description="IP address")
    user_agent: Optional[str] = Field(None, description="User agent")
    
    model_config = ConfigDict(from_attributes=True)