"""
Teacher domain entities

This module contains the core domain entities for teacher management:
- Teacher: Teacher entity with business logic
- Qualification: Teacher qualification entity
- Subject: Subject entity
- Department: Department entity

Author: Edu-Flow Team
"""

from datetime import datetime
from enum import Enum
from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field, field_validator


class EmploymentStatus(str, Enum):
    """Employment status enumeration"""
    ACTIVE = "active"
    INACTIVE = "inactive"
    ON_LEAVE = "on_leave"
    TERMINATED = "terminated"
    RETIRED = "retired"


class Subject(BaseModel):
    """Subject entity"""
    id: str = Field(..., description="Unique subject identifier")
    name: str = Field(..., description="Subject name", min_length=1, max_length=100)
    code: str = Field(..., description="Subject code", min_length=3, max_length=10)
    description: Optional[str] = Field(None, description="Subject description")
    credits: float = Field(..., description="Subject credits", gt=0)
    department_id: str = Field(..., description="Department assignment")
    created_at: datetime = Field(default_factory=lambda: datetime.now(), description="Creation timestamp")
    
    @field_validator('code')
    @classmethod
    def validate_code(cls, v):
        """Validate subject code format"""
        if not v.isalnum():
            raise ValueError("Subject code must be alphanumeric")
        return v.upper()


class Qualification(BaseModel):
    """Teacher qualification entity"""
    id: str = Field(..., description="Qualification identifier")
    teacher_id: str = Field(..., description="Teacher identifier")
    degree: str = Field(..., description="Degree obtained", min_length=1, max_length=100)
    institution: str = Field(..., description="Institution name", min_length=1, max_length=200)
    field_of_study: str = Field(..., description="Field of study", min_length=1, max_length=100)
    year_graduated: int = Field(..., description="Graduation year", ge=1950, le=2030)
    certificate_number: Optional[str] = Field(None, description="Certificate number")
    verification_status: str = Field("pending", description="Verification status")
    created_at: datetime = Field(default_factory=lambda: datetime.now(), description="Creation timestamp")
    
    @field_validator('year_graduated')
    @classmethod
    def validate_year_graduated(cls, v):
        """Validate graduation year is reasonable"""
        current_year = datetime.now().year
        if v > current_year + 5:
            raise ValueError("Graduation year cannot be more than 5 years in the future")
        return v


class Teacher(BaseModel):
    """Teacher entity with business logic"""
    id: str = Field(..., description="Unique teacher identifier")
    teacher_id: str = Field(..., description="Teacher ID", min_length=3, max_length=20)
    name: str = Field(..., description="Teacher full name", min_length=1, max_length=100)
    email: str = Field(..., description="Teacher email address", pattern=r'^[^@]+@[^@]+\.[^@]+$')
    phone: Optional[str] = Field(None, description="Phone number")
    address: Optional[str] = Field(None, description="Address")
    department_id: Optional[str] = Field(None, description="Department assignment")
    employment_status: EmploymentStatus = Field(EmploymentStatus.ACTIVE, description="Employment status")
    hire_date: datetime = Field(..., description="Hire date")
    specialization: Optional[str] = Field(None, description="Teaching specialization")
    experience_years: Optional[int] = Field(None, description="Years of experience", ge=0)
    qualifications: List[Qualification] = Field(default_factory=list, description="Teacher qualifications")
    subjects: List[str] = Field(default_factory=list, description="Subject assignments")
    salary: Optional[float] = Field(None, description="Annual salary", gt=0)
    is_active: bool = Field(True, description="Account status")
    emergency_contact: Optional[Dict[str, str]] = Field(None, description="Emergency contact information")
    medical_info: Optional[str] = Field(None, description="Medical information")
    promotion_date: Optional[datetime] = Field(None, description="Last promotion date")
    created_at: datetime = Field(default_factory=lambda: datetime.now(), description="Creation timestamp")
    updated_at: datetime = Field(default_factory=lambda: datetime.now(), description="Last update timestamp")
    
    @field_validator('teacher_id')
    @classmethod
    def validate_teacher_id(cls, v):
        """Validate teacher ID format"""
        if not v.isalnum():
            raise ValueError("Teacher ID must be alphanumeric")
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
        """Update teacher profile"""
        for key, value in kwargs.items():
            if hasattr(self, key) and key not in ['id', 'teacher_id', 'email', 'created_at', 'hire_date']:
                setattr(self, key, value)
        self.updated_at = datetime.now()
    
    def add_qualification(self, qualification: Qualification) -> None:
        """Add qualification to teacher"""
        self.qualifications.append(qualification)
        self.updated_at = datetime.now()
    
    def remove_qualification(self, qualification_id: str) -> None:
        """Remove qualification from teacher"""
        self.qualifications = [q for q in self.qualifications if q.id != qualification_id]
        self.updated_at = datetime.now()
    
    def assign_subject(self, subject_id: str) -> None:
        """Assign subject to teacher"""
        if subject_id not in self.subjects:
            self.subjects.append(subject_id)
            self.updated_at = datetime.now()
    
    def remove_subject(self, subject_id: str) -> None:
        """Remove subject assignment from teacher"""
        self.subjects = [s for s in self.subjects if s != subject_id]
        self.updated_at = datetime.now()
    
    def calculate_years_of_experience(self) -> int:
        """Calculate years of experience based on hire date"""
        current_date = datetime.now()
        hire_date = self.hire_date
        experience = current_date.year - hire_date.year
        
        # Adjust if hire date hasn't occurred yet this year
        if (current_date.month, current_date.day) < (hire_date.month, hire_date.day):
            experience -= 1
        
        return max(0, experience)
    
    def promote_to_department_head(self, department_id: str) -> None:
        """Promote teacher to department head"""
        self.department_id = department_id
        self.updated_at = datetime.now()
    
    def put_on_leave(self, leave_type: str = "personal", leave_start: datetime = None, leave_end: datetime = None) -> None:
        """Put teacher on leave"""
        if leave_start is None:
            leave_start = datetime.now()
        
        self.employment_status = EmploymentStatus.ON_LEAVE
        self.updated_at = datetime.now()
        
        # Additional leave details could be stored in an extension or separate entity
    
    def return_from_leave(self) -> None:
        """Return teacher from leave"""
        self.employment_status = EmploymentStatus.ACTIVE
        self.updated_at = datetime.now()
    
    def terminate_employment(self, reason: str = "resignation") -> None:
        """Terminate teacher employment"""
        self.employment_status = EmploymentStatus.TERMINATED
        self.is_active = False
        self.updated_at = datetime.now()
    
    def is_eligible_for_promotion(self) -> bool:
        """Check if teacher is eligible for promotion"""
        # Basic criteria: employed for at least 3 years and has valid qualifications
        experience = self.calculate_years_of_experience()
        has_qualifications = len(self.qualifications) > 0
        is_active = self.employment_status == EmploymentStatus.ACTIVE
        
        return experience >= 3 and has_qualifications and is_active
    
    def get_teaching_load(self) -> Dict[str, int]:
        """Calculate teaching load information"""
        return {
            "assigned_subjects": len(self.subjects),
            "qualifications_count": len(self.qualifications),
            "experience_years": self.experience_years or self.calculate_years_of_experience()
        }