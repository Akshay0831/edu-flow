"""
Student domain entities

This module contains the core domain entities for student management:
- Student: Student entity with business logic
- AcademicRecord: Academic record entity
- EnrollmentRecord: Enrollment record entity
- GradeLevel: Grade level enumeration
- AcademicStanding: Academic standing enumeration
- EnrollmentStatus: Enrollment status enumeration
- RiskLevel: Risk level enumeration

Author: Edu-Flow Team
"""

from datetime import datetime, date, timedelta
from enum import Enum
from typing import Optional, List, Dict, Any
from uuid import UUID
from pydantic import BaseModel, Field, field_validator


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


class AcademicRecord(BaseModel):
    """Academic record entity"""
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
    created_at: datetime = Field(default_factory=lambda: datetime.now(), description="Creation timestamp")
    
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
    
    def calculate_grade_points(self) -> float:
        """Calculate grade points based on grade"""
        if self.grade >= 90:
            return 4.0
        elif self.grade >= 80:
            return 3.0
        elif self.grade >= 70:
            return 2.0
        elif self.grade >= 60:
            return 1.0
        else:
            return 0.0


class EnrollmentRecord(BaseModel):
    """Enrollment record entity"""
    id: str = Field(..., description="Enrollment identifier")
    student_id: str = Field(..., description="Student identifier")
    course_id: str = Field(..., description="Course identifier")
    semester: str = Field(..., description="Semester identifier")
    academic_year: str = Field(..., description="Academic year")
    status: EnrollmentStatus = Field(EnrollmentStatus.ACTIVE, description="Enrollment status")
    priority: int = Field(1, description="Enrollment priority", ge=1, le=10)
    special_accommodations: Optional[Dict[str, Any]] = Field(None, description="Special accommodations")
    enrollment_date: datetime = Field(default_factory=lambda: datetime.now(), description="Enrollment date")
    created_at: datetime = Field(default_factory=lambda: datetime.now(), description="Creation timestamp")
    
    @field_validator('priority')
    @classmethod
    def validate_priority(cls, v):
        """Validate priority is within valid range"""
        if v < 1 or v > 10:
            raise ValueError("Priority must be between 1 and 10")
        return v


class Student(BaseModel):
    """Student entity with business logic"""
    id: str = Field(..., description="Unique student identifier")
    student_id: str = Field(..., description="Student ID", min_length=3, max_length=20)
    name: str = Field(..., description="Student full name", min_length=1, max_length=100)
    email: str = Field(..., description="Student email address", pattern=r'^[^@]+@[^@]+\.[^@]+$')
    grade_level: GradeLevel = Field(..., description="Current grade level (9-12)")
    enrollment_date: date = Field(..., description="Date of enrollment")
    department_id: Optional[str] = Field(None, description="Department assignment")
    advisor_id: Optional[str] = Field(None, description="Teacher/advisor assignment")
    gpa: Optional[float] = Field(None, description="Grade point average", ge=0.0, le=4.0)
    attendance_rate: Optional[float] = Field(None, description="Attendance rate", ge=0.0, le=1.0)
    academic_standing: Optional[AcademicStanding] = Field(None, description="Academic standing")
    risk_level: Optional[RiskLevel] = Field(None, description="Risk level")
    status: EnrollmentStatus = Field(EnrollmentStatus.ACTIVE, description="Enrollment status")
    phone: Optional[str] = Field(None, description="Phone number")
    address: Optional[str] = Field(None, description="Address")
    emergency_contact: Optional[Dict[str, str]] = Field(None, description="Emergency contact information")
    medical_info: Optional[str] = Field(None, description="Medical information")
    family_info: Optional[Dict[str, Any]] = Field(None, description="Family information")
    preferences: Optional[Dict[str, Any]] = Field(None, description="Student preferences")
    notes: Optional[str] = Field(None, description="Additional notes")
    is_active: bool = Field(True, description="Account status")
    created_at: datetime = Field(default_factory=lambda: datetime.now(), description="Creation timestamp")
    updated_at: datetime = Field(default_factory=lambda: datetime.now(), description="Last update timestamp")
    last_login: Optional[datetime] = Field(None, description="Last login timestamp")
    graduation_date: Optional[date] = Field(None, description="Graduation date")
    
    @field_validator('student_id')
    @classmethod
    def validate_student_id(cls, v):
        """Validate student ID format"""
        if not v.isalnum():
            raise ValueError("Student ID must be alphanumeric")
        return v.upper()
    
    @field_validator('email')
    @classmethod
    def validate_email(cls, v):
        """Validate email format"""
        if not v or '@' not in v:
            raise ValueError("Invalid email format")
        return v.lower()
    
    @field_validator('name')
    @classmethod
    def validate_name(cls, v):
        """Validate name is not empty"""
        if not v or not v.strip():
            raise ValueError("Name cannot be empty")
        return v.strip()
    
    def update_profile(self, **kwargs) -> None:
        """Update student profile"""
        for key, value in kwargs.items():
            if hasattr(self, key) and key not in ['id', 'student_id', 'email', 'created_at', 'enrollment_date']:
                setattr(self, key, value)
        self.updated_at = datetime.now()
    
    def promote_to_next_grade(self) -> None:
        """Promote student to next grade level"""
        if self.grade_level < GradeLevel.TWELFTH:
            self.grade_level = GradeLevel(self.grade_level + 1)
            self.updated_at = datetime.now()
    
    def update_academic_status(self) -> None:
        """Update academic standing based on GPA"""
        if self.gpa is None:
            return
        
        if self.gpa >= 3.7:
            self.academic_standing = AcademicStanding.EXCELLENT
        elif self.gpa >= 3.0:
            self.academic_standing = AcademicStanding.GOOD
        elif self.gpa >= 2.0:
            self.academic_standing = AcademicStanding.SATISFACTORY
        elif self.gpa >= 1.5:
            self.academic_standing = AcademicStanding.NEEDS_IMPROVEMENT
        else:
            self.academic_standing = AcademicStanding.POOR
    
    def assess_risk_level(self, academic_records: List[AcademicRecord], attendance_rate: Optional[float]) -> None:
        """Assess student risk level based on academic performance and attendance"""
        risk_factors = 0
        
        # Check academic performance
        if academic_records:
            avg_grade = sum(record.grade for record in academic_records) / len(academic_records)
            if avg_grade < 60:
                risk_factors += 2
            elif avg_grade < 70:
                risk_factors += 1
        
        # Check attendance
        if attendance_rate is not None:
            if attendance_rate < 0.8:
                risk_factors += 2
            elif attendance_rate < 0.9:
                risk_factors += 1
        
        # Update risk level
        if risk_factors >= 3:
            self.risk_level = RiskLevel.CRITICAL
        elif risk_factors >= 2:
            self.risk_level = RiskLevel.HIGH
        elif risk_factors >= 1:
            self.risk_level = RiskLevel.MEDIUM
        else:
            self.risk_level = RiskLevel.LOW
    
    def graduate(self) -> None:
        """Mark student as graduated"""
        self.status = EnrollmentStatus.GRADUATED
        self.graduation_date = date.today()
        self.updated_at = datetime.now()
    
    def withdraw(self) -> None:
        """Mark student as withdrawn"""
        self.status = EnrollmentStatus.WITHDRAWN
        self.is_active = False
        self.updated_at = datetime.now()
    
    def transfer(self) -> None:
        """Mark student as transferred"""
        self.status = EnrollmentStatus.TRANSFERRED
        self.is_active = False
        self.updated_at = datetime.now()
    
    def calculate_total_credits(self, academic_records: List[AcademicRecord]) -> float:
        """Calculate total earned credits"""
        return sum(record.credits for record in academic_records if record.grade >= 60)
    
    def calculate_semester_gpa(self, academic_records: List[AcademicRecord]) -> float:
        """Calculate GPA for specific semester"""
        semester_records = [
            record for record in academic_records 
            if record.semester == self.current_semester and record.academic_year == self.current_academic_year
        ]
        
        if not semester_records:
            return 0.0
        
        total_points = sum(record.calculate_grade_points() for record in semester_records)
        return total_points / len(semester_records)
    
    @property
    def current_semester(self) -> str:
        """Get current semester"""
        month = datetime.now().month
        if month in [1, 2, 3, 4, 5, 6]:
            return "Spring"
        else:
            return "Fall"
    
    @property
    def current_academic_year(self) -> str:
        """Get current academic year"""
        year = datetime.now().year
        month = datetime.now().month
        if month in [1, 2, 3, 4, 5, 6]:
            return f"{year-1}-{year}"
        else:
            return f"{year}-{year+1}"