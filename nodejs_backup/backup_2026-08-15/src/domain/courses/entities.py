"""
Course domain entities

This module contains the core domain entities for course management:
- Course: Course entity with business logic
- CoursePrerequisite: Course prerequisite entity
- CourseOffering: Course offering entity
- Schedule: Schedule entity

Author: Edu-Flow Team
"""

from datetime import datetime, date, time, timedelta
from enum import Enum
from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field, field_validator


class CourseLevel(str, Enum):
    """Course level enumeration"""
    BEGINNER = "beginner"
    INTERMEDIATE = "intermediate"
    ADVANCED = "advanced"
    HONORS = "honors"
    AP = "ap"


class CourseStatus(str, Enum):
    """Course status enumeration"""
    DRAFT = "draft"
    ACTIVE = "active"
    INACTIVE = "inactive"
    ARCHIVED = "archived"
    CANCELLED = "cancelled"


class Semester(str, Enum):
    """Semester enumeration"""
    FALL = "fall"
    SPRING = "spring"
    SUMMER = "summer"
    WINTER = "winter"


class DayOfWeek(str, Enum):
    """Day of week enumeration"""
    MONDAY = "monday"
    TUESDAY = "tuesday"
    WEDNESDAY = "wednesday"
    THURSDAY = "thursday"
    FRIDAY = "friday"
    SATURDAY = "saturday"
    SUNDAY = "sunday"


class PrerequisiteType(str, Enum):
    """Prerequisite type enumeration"""
    COURSE = "course"
    GPA = "gpa"
    GRADE = "grade"
    TEST_SCORE = "test_score"
    NONE = "none"


class CoursePrerequisite(BaseModel):
    """Course prerequisite entity"""
    id: str = Field(..., description="Prerequisite identifier")
    course_id: str = Field(..., description="Course identifier")
    type: PrerequisiteType = Field(..., description="Prerequisite type")
    requirement: str = Field(..., description="Prerequisite requirement")
    min_score: Optional[float] = Field(None, description="Minimum required score")
    description: Optional[str] = Field(None, description="Prerequisite description")
    created_at: datetime = Field(default_factory=lambda: datetime.now(), description="Creation timestamp")
    
    @field_validator('requirement')
    @classmethod
    def validate_requirement(cls, v):
        """Validate prerequisite requirement"""
        if not v or not v.strip():
            raise ValueError("Prerequisite requirement cannot be empty")
        return v.strip()


class Schedule(BaseModel):
    """Course schedule entity"""
    id: str = Field(..., description="Schedule identifier")
    course_id: str = Field(..., description="Course identifier")
    day_of_week: DayOfWeek = Field(..., description="Day of week")
    start_time: time = Field(..., description="Start time")
    end_time: time = Field(..., description="End time")
    room_number: Optional[str] = Field(None, description="Room number")
    building: Optional[str] = Field(None, description="Building")
    instructor_id: Optional[str] = Field(None, description="Instructor identifier")
    semester: Semester = Field(..., description="Semester")
    academic_year: str = Field(..., description="Academic year")
    max_capacity: int = Field(..., description="Maximum capacity", gt=0)
    current_enrollment: int = Field(0, description="Current enrollment", ge=0)
    is_active: bool = Field(True, description="Schedule active status")
    created_at: datetime = Field(default_factory=lambda: datetime.now(), description="Creation timestamp")
    
    @field_validator('max_capacity')
    @classmethod
    def validate_max_capacity(cls, v):
        """Validate maximum capacity"""
        if v <= 0:
            raise ValueError("Maximum capacity must be positive")
        return v
    
    @field_validator('current_enrollment')
    @classmethod
    def validate_current_enrollment(cls, v):
        """Validate current enrollment"""
        if v < 0:
            raise ValueError("Current enrollment cannot be negative")
        return v
    
    def has_capacity(self) -> bool:
        """Check if schedule has capacity for more students"""
        return self.current_enrollment < self.max_capacity
    
    def get_available_seats(self) -> int:
        """Get number of available seats"""
        return max(0, self.max_capacity - self.current_enrollment)
    
    def enroll_student(self) -> bool:
        """Enroll a student in this schedule"""
        if self.has_capacity():
            self.current_enrollment += 1
            return True
        return False
    
    def unenroll_student(self) -> bool:
        """Unenroll a student from this schedule"""
        if self.current_enrollment > 0:
            self.current_enrollment -= 1
            return True
        return False
    
    def get_occupancy_rate(self) -> float:
        """Get occupancy rate as percentage"""
        if self.max_capacity == 0:
            return 0.0
        return (self.current_enrollment / self.max_capacity) * 100


class CourseOffering(BaseModel):
    """Course offering entity"""
    id: str = Field(..., description="Offering identifier")
    course_id: str = Field(..., description="Course identifier")
    semester: Semester = Field(..., description="Semester")
    academic_year: str = Field(..., description="Academic year")
    section_number: str = Field(..., description="Section number", min_length=1, max_length=10)
    schedule_id: str = Field(..., description="Schedule identifier")
    instructor_id: Optional[str] = Field(None, description="Instructor identifier")
    max_enrollment: int = Field(..., description="Maximum enrollment", gt=0)
    current_enrollment: int = Field(0, description="Current enrollment", ge=0)
    waitlist_capacity: int = Field(10, description="Waitlist capacity", ge=0)
    current_waitlist: int = Field(0, description="Current waitlist", ge=0)
    credits: float = Field(..., description="Course credits", gt=0)
    tuition: Optional[float] = Field(None, description="Tuition cost", gt=0)
    status: CourseStatus = Field(CourseStatus.ACTIVE, description="Course status")
    created_at: datetime = Field(default_factory=lambda: datetime.now(), description="Creation timestamp")
    updated_at: datetime = Field(default_factory=lambda: datetime.now(), description="Last update timestamp")
    
    @field_validator('section_number')
    @classmethod
    def validate_section_number(cls, v):
        """Validate section number format"""
        if not v.strip():
            raise ValueError("Section number cannot be empty")
        return v.upper()
    
    @field_validator('max_enrollment')
    @classmethod
    def validate_max_enrollment(cls, v):
        """Validate maximum enrollment"""
        if v <= 0:
            raise ValueError("Maximum enrollment must be positive")
        return v
    
    @field_validator('current_enrollment')
    @classmethod
    def validate_current_enrollment(cls, v):
        """Validate current enrollment"""
        if v < 0:
            raise ValueError("Current enrollment cannot be negative")
        return v
    
    @field_validator('waitlist_capacity')
    @classmethod
    def validate_waitlist_capacity(cls, v):
        """Validate waitlist capacity"""
        if v < 0:
            raise ValueError("Waitlist capacity cannot be negative")
        return v
    
    @field_validator('current_waitlist')
    @classmethod
    def validate_current_waitlist(cls, v):
        """Validate current waitlist"""
        if v < 0:
            raise ValueError("Current waitlist cannot be negative")
        return v
    
    def has_capacity(self) -> bool:
        """Check if offering has capacity for more students"""
        return self.current_enrollment < self.max_enrollment
    
    def has_waitlist_capacity(self) -> bool:
        """Check if offering has waitlist capacity"""
        return self.current_waitlist < self.waitlist_capacity
    
    def get_available_seats(self) -> int:
        """Get number of available seats"""
        return max(0, self.max_enrollment - self.current_enrollment)
    
    def get_waitlist_positions(self) -> int:
        """Get number of students on waitlist"""
        return self.current_waitlist
    
    def enroll_student(self) -> bool:
        """Enroll a student in this offering"""
        if self.has_capacity():
            self.current_enrollment += 1
            self.updated_at = datetime.now()
            return True
        return False
    
    def add_to_waitlist(self) -> bool:
        """Add a student to the waitlist"""
        if self.has_waitlist_capacity():
            self.current_waitlist += 1
            self.updated_at = datetime.now()
            return True
        return False
    
    def unenroll_student(self) -> bool:
        """Unenroll a student from this offering"""
        if self.current_enrollment > 0:
            self.current_enrollment -= 1
            
            # Move student from waitlist if available
            if self.current_waitlist > 0:
                self.current_waitlist -= 1
                self.current_enrollment += 1
            
            self.updated_at = datetime.now()
            return True
        return False
    
    def remove_from_waitlist(self) -> bool:
        """Remove a student from the waitlist"""
        if self.current_waitlist > 0:
            self.current_waitlist -= 1
            self.updated_at = datetime.now()
            return True
        return False
    
    def get_enrollment_rate(self) -> float:
        """Get enrollment rate as percentage"""
        if self.max_enrollment == 0:
            return 0.0
        return (self.current_enrollment / self.max_enrollment) * 100
    
    def is_waitlist_full(self) -> bool:
        """Check if waitlist is full"""
        return self.current_waitlist >= self.waitlist_capacity
    
    def can_accept_enrollments(self) -> bool:
        """Check if offering can accept new enrollments"""
        return self.status == CourseStatus.ACTIVE and self.has_capacity()
    
    def set_status(self, status: CourseStatus) -> None:
        """Set course offering status"""
        self.status = status
        self.updated_at = datetime.now()


class Course(BaseModel):
    """Course entity with business logic"""
    id: str = Field(..., description="Unique course identifier")
    title: str = Field(..., description="Course title", min_length=1, max_length=200, pattern=r'.+')
    code: str = Field(..., description="Course code", min_length=3, max_length=15)
    description: Optional[str] = Field(None, description="Course description")
    level: CourseLevel = Field(CourseLevel.INTERMEDIATE, description="Course level")
    department_id: str = Field(..., description="Department assignment")
    prerequisites: List[CoursePrerequisite] = Field(default_factory=list, description="Course prerequisites")
    offerings: List[CourseOffering] = Field(default_factory=list, description="Course offerings")
    credits: float = Field(..., description="Course credits", gt=0)
    duration_weeks: int = Field(..., description="Duration in weeks", gt=0)
    is_mandatory: bool = Field(False, description="Is course mandatory")
    is_elective: bool = Field(True, description="Is course elective")
    tuition: Optional[float] = Field(None, description="Tuition cost", gt=0)
    status: CourseStatus = Field(CourseStatus.ACTIVE, description="Course status")
    created_at: datetime = Field(default_factory=lambda: datetime.now(), description="Creation timestamp")
    updated_at: datetime = Field(default_factory=lambda: datetime.now(), description="Last update timestamp")
    
    @field_validator('code')
    @classmethod
    def validate_code(cls, v):
        """Validate course code format"""
        if not v.isalnum():
            raise ValueError("Course code must be alphanumeric")
        return v.upper()
    
    @field_validator('title')
    @classmethod
    def validate_title(cls, v):
        """Validate course title"""
        if not v or not v.strip():
            raise ValueError("Course title cannot be empty")
        return v.strip()
    
    @field_validator('duration_weeks')
    @classmethod
    def validate_duration_weeks(cls, v):
        """Validate duration in weeks"""
        if v <= 0:
            raise ValueError("Duration must be positive")
        return v
    
    def add_prerequisite(self, prerequisite: CoursePrerequisite) -> None:
        """Add prerequisite to course"""
        self.prerequisites.append(prerequisite)
        self.updated_at = datetime.now()
    
    def remove_prerequisite(self, prerequisite_id: str) -> None:
        """Remove prerequisite from course"""
        self.prerequisites = [p for p in self.prerequisites if p.id != prerequisite_id]
        self.updated_at = datetime.now()
    
    def add_offering(self, offering: CourseOffering) -> None:
        """Add offering to course"""
        self.offerings.append(offering)
        self.updated_at = datetime.now()
    
    def remove_offering(self, offering_id: str) -> None:
        """Remove offering from course"""
        self.offerings = [o for o in self.offerings if o.id != offering_id]
        self.updated_at = datetime.now()
    
    def get_total_capacity(self) -> int:
        """Get total capacity across all offerings"""
        return sum(offering.max_enrollment for offering in self.offerings)
    
    def get_total_enrollment(self) -> int:
        """Get total enrollment across all offerings"""
        return sum(offering.current_enrollment for offering in self.offerings)
    
    def get_total_waitlist(self) -> int:
        """Get total waitlist across all offerings"""
        return sum(offering.current_waitlist for offering in self.offerings)
    
    def get_average_enrollment_rate(self) -> float:
        """Get average enrollment rate across all offerings"""
        if not self.offerings:
            return 0.0
        
        total_capacity = sum(offering.max_enrollment for offering in self.offerings)
        total_enrollment = sum(offering.current_enrollment for offering in self.offerings)
        
        if total_capacity == 0:
            return 0.0
        
        return (total_enrollment / total_capacity) * 100
    
    def is_prerequisite_met(self, completed_courses: List[str], gpa: Optional[float] = None, grades: Dict[str, float] = None) -> bool:
        """Check if prerequisites are met"""
        for prerequisite in self.prerequisites:
            if prerequisite.type == PrerequisiteType.COURSE:
                if prerequisite.requirement not in completed_courses:
                    return False
            elif prerequisite.type == PrerequisiteType.GPA:
                if gpa is None or gpa < prerequisite.min_score:
                    return False
            elif prerequisite.type == PrerequisiteType.GRADE:
                if grades is None or prerequisite.requirement not in grades or grades[prerequisite.requirement] < prerequisite.min_score:
                    return False
        
        return True
    
    def get_available_offerings(self, semester: Semester, academic_year: str) -> List[CourseOffering]:
        """Get available offerings for specific semester and academic year"""
        return [
            offering for offering in self.offerings
            if offering.semester == semester and offering.academic_year == academic_year
            and offering.can_accept_enrollments()
        ]
    
    def get_schedule_conflicts(self, new_schedule: Schedule) -> List[str]:
        """Check for schedule conflicts with existing offerings"""
        conflicts = []
        
        for offering in self.offerings:
            # Check if same semester and academic year
            if offering.schedule_id != new_schedule.id:  # Don't conflict with self
                # This would require checking actual schedule data
                # For now, add placeholder logic
                pass
        
        return conflicts
    
    def set_status(self, status: CourseStatus) -> None:
        """Set course status"""
        self.status = status
        self.updated_at = datetime.now()
    
    def calculate_total_tuition(self) -> float:
        """Calculate total tuition for all offerings"""
        if self.tuition is None:
            return 0.0
        
        total_enrollment = self.get_total_enrollment()
        return self.tuition * total_enrollment