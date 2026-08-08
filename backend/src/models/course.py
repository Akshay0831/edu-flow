"""Course management models for FastAPI."""

from datetime import date, datetime, timezone
from enum import Enum
from typing import List, Optional, Dict, Any
from pydantic import BaseModel, field_validator, ConfigDict, Field
from bson import ObjectId
import uuid


class CourseLevel(str, Enum):
    """Course level enumeration."""
    BEGINNER = "beginner"
    INTERMEDIATE = "intermediate"
    ADVANCED = "advanced"
    SPECIALIZED = "specialized"


class CreditType(str, Enum):
    """Credit type enumeration."""
    REGULAR = "regular"
    LAB = "lab"
    PROJECT = "project"
    RESEARCH = "research"
    SEMINAR = "seminar"
    INDEPENDENT = "independent"


class Semester(str, Enum):
    """Semester enumeration."""
    FALL = "fall"
    SPRING = "spring"
    SUMMER = "summer"


class Grade(str, Enum):
    """Grade enumeration."""
    A = "A"
    B_PLUS = "B+"
    B = "B"
    C_PLUS = "C+"
    C = "C"
    D_PLUS = "D+"
    D = "D"
    F = "F"
    INCOMPLETE = "incomplete"
    WITHDRAWN = "withdrawn"


class CourseStatus(str, Enum):
    """Course status enumeration."""
    ACTIVE = "active"
    INACTIVE = "inactive"
    ARCHIVED = "archived"
    DRAFT = "draft"


class Department(BaseModel):
    """Department model."""
    department_id: str
    name: str
    code: str
    description: str
    head_of_department: Optional[str] = None
    contact_email: Optional[str] = None
    contact_phone: Optional[str] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None


class Prerequisite(BaseModel):
    """Prerequisite model."""
    course_id: str
    prerequisite_course_id: str
    min_grade: Optional[Grade] = None
    created_at: Optional[datetime] = None


class Course(BaseModel):
    """Course model."""
    model_config = ConfigDict(
        from_attributes=True,
        populate_by_name=True,
        use_enum_values=True
    )

    course_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    title: str
    code: str
    description: str
    department_id: str
    level: CourseLevel
    credits: float
    credit_type: CreditType
    prerequisites: List[Prerequisite] = []
    corequisites: List[Prerequisite] = []
    learning_objectives: str
    assessment_methods: str
    duration_weeks: int
    typical_semesters: List[Semester]
    is_active: bool = True
    syllabus_file_url: Optional[str] = None
    syllabus_file_name: Optional[str] = None
    prerequisites_approved: bool = False
    created_at: Optional[datetime] = Field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: Optional[datetime] = Field(default_factory=lambda: datetime.now(timezone.utc))

    @field_validator('credits')
    @classmethod
    def validate_credits(cls, v):
        """Validate course credits."""
        if not (0 < v <= 10):
            raise ValueError("Credits must be between 0 and 10, and cannot be 0")
        return v

    @field_validator('duration_weeks')
    @classmethod
    def validate_duration(cls, v):
        """Validate course duration."""
        if not (1 <= v <= 52):
            raise ValueError("Duration must be between 1 and 52 weeks")
        return v

    @field_validator('code')
    @classmethod
    def validate_course_code(cls, v):
        """Validate course code format."""
        if not v or len(v.strip()) < 3:
            raise ValueError("Course code must be at least 3 characters")
        return v.upper()


class CourseCreate(Course):
    """Course create model."""
    pass


class CourseUpdate(BaseModel):
    """Course update model."""
    code: Optional[str] = None
    title: Optional[str] = None
    description: Optional[str] = None
    level: Optional[CourseLevel] = None
    credits: Optional[float] = None
    credit_type: Optional[CreditType] = None
    learning_objectives: Optional[str] = None
    assessment_methods: Optional[str] = None
    duration_weeks: Optional[int] = None
    typical_semesters: Optional[List[Semester]] = None
    syllabus_file_url: Optional[str] = None
    syllabus_file_name: Optional[str] = None


class CourseResponse(BaseModel):
    """Course response model."""
    model_config = ConfigDict(
        from_attributes=True,
        populate_by_name=True,
        use_enum_values=True
    )

    course_id: str
    title: str
    code: str
    description: str
    department_id: str
    level: CourseLevel
    credits: float
    credit_type: CreditType
    prerequisites: List[Prerequisite] = []
    corequisites: List[Prerequisite] = []
    learning_objectives: str
    assessment_methods: str
    duration_weeks: int
    typical_semesters: List[Semester]
    is_active: bool
    syllabus_file_url: Optional[str] = None
    syllabus_file_name: Optional[str] = None
    prerequisites_approved: bool
    created_at: datetime
    updated_at: datetime


class CourseCreateResponse(BaseModel):
    """Course create response model."""
    model_config = ConfigDict(
        from_attributes=True,
        populate_by_name=True,
        use_enum_values=True
    )

    course: CourseResponse
    message: str


class CourseOffering(BaseModel):
    """Course offering model."""
    model_config = ConfigDict(
        from_attributes=True,
        populate_by_name=True,
        use_enum_values=True
    )

    offering_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    course_id: str
    semester: Semester
    academic_year: int
    section: str
    instructor_id: str
    max_enrollment: int
    current_enrollment: int = 0
    current_waitlist: int = 0
    waitlist_capacity: int = 0
    schedule: str
    location: str
    credits: float
    credit_type: CreditType
    prerequisites: List[Prerequisite] = []
    corequisites: List[Prerequisite] = []
    description: str
    learning_objectives: str
    assessment_methods: str
    start_date: Optional[date] = None
    end_date: Optional[date] = None
    prerequisites_approved: bool = False
    is_active: bool = True
    created_at: Optional[datetime] = Field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: Optional[datetime] = Field(default_factory=lambda: datetime.now(timezone.utc))

    @field_validator('academic_year')
    @classmethod
    def validate_academic_year(cls, v):
        """Validate academic year."""
        if not (2000 <= v <= 2100):
            raise ValueError("Academic year must be between 2000 and 2100")
        return v

    @field_validator('max_enrollment')
    @classmethod
    def validate_max_enrollment(cls, v):
        """Validate maximum enrollment."""
        if v < 0:
            raise ValueError("Maximum enrollment must be non-negative")
        return v

    @field_validator('waitlist_capacity')
    @classmethod
    def validate_waitlist_capacity(cls, v):
        """Validate waitlist capacity."""
        if v < 0:
            raise ValueError("Waitlist capacity must be non-negative")
        return v


class OfferingCreate(CourseOffering):
    """Offering create model."""
    pass


class OfferingUpdate(BaseModel):
    """Offering update model."""
    instructor_id: Optional[str] = None
    max_enrollment: Optional[int] = None
    waitlist_capacity: Optional[int] = None
    schedule: Optional[str] = None
    location: Optional[str] = None
    credits: Optional[float] = None
    credit_type: Optional[CreditType] = None
    description: Optional[str] = None
    learning_objectives: Optional[str] = None
    assessment_methods: Optional[str] = None
    start_date: Optional[date] = None
    end_date: Optional[date] = None


class OfferingResponse(BaseModel):
    """Offering response model."""
    model_config = ConfigDict(
        from_attributes=True,
        populate_by_name=True,
        use_enum_values=True
    )

    offering_id: str
    course_id: str
    semester: Semester
    academic_year: int
    section: str
    instructor_id: str
    max_enrollment: int
    current_enrollment: int
    current_waitlist: int
    waitlist_capacity: int
    schedule: str
    location: str
    credits: float
    credit_type: CreditType
    prerequisites: List[Prerequisite] = []
    corequisites: List[Prerequisite] = []
    description: str
    learning_objectives: str
    assessment_methods: str
    start_date: Optional[date] = None
    end_date: Optional[date] = None
    prerequisites_approved: bool
    is_active: bool
    created_at: datetime
    updated_at: datetime


class Enrollment(BaseModel):
    """Enrollment model."""
    model_config = ConfigDict(
        from_attributes=True,
        populate_by_name=True,
        use_enum_values=True
    )

    enrollment_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    student_id: str
    offering_id: str
    course_id: str
    status: str = "enrolled"
    enrollment_date: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    drop_date: Optional[datetime] = None
    attendance_rate: Optional[float] = None
    final_score: Optional[float] = None
    grade: Optional[Grade] = None
    credits_earned: Optional[float] = None
    is_active: bool = True
    notes: Optional[str] = None
    created_at: Optional[datetime] = Field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: Optional[datetime] = Field(default_factory=lambda: datetime.now(timezone.utc))

    @field_validator('attendance_rate')
    @classmethod
    def validate_attendance_rate(cls, v):
        """Validate attendance rate."""
        if v is not None and not (0 <= v <= 1):
            raise ValueError("Attendance rate must be between 0 and 1")
        return v

    @field_validator('final_score')
    @classmethod
    def validate_final_score(cls, v):
        """Validate final score."""
        if v is not None and not (0 <= v <= 100):
            raise ValueError("Final score must be between 0 and 100")
        return v


class EnrollmentCreate(BaseModel):
    """Enrollment create model."""
    offering_id: str


class EnrollmentUpdate(BaseModel):
    """Enrollment update model."""
    status: Optional[str] = None
    attendance_rate: Optional[float] = None
    final_score: Optional[float] = None
    grade: Optional[Grade] = None
    credits_earned: Optional[float] = None
    notes: Optional[str] = None


class EnrollmentResponse(BaseModel):
    """Enrollment response model."""
    model_config = ConfigDict(
        from_attributes=True,
        populate_by_name=True,
        use_enum_values=True
    )

    enrollment_id: str
    student_id: str
    offering_id: str
    course_id: str
    status: str
    enrollment_date: datetime
    drop_date: Optional[datetime] = None
    attendance_rate: Optional[float] = None
    final_score: Optional[float] = None
    grade: Optional[Grade] = None
    credits_earned: Optional[float] = None
    is_active: bool
    notes: Optional[str] = None
    created_at: datetime
    updated_at: datetime


class CourseStatistics(BaseModel):
    """Course statistics model."""
    model_config = ConfigDict(
        from_attributes=True,
        populate_by_name=True,
        use_enum_values=True
    )

    course_id: str
    title: str
    code: str
    department_name: str
    total_offerings: int
    total_enrollments: int
    total_completions: int
    average_enrollment: float
    completion_rate: float
    average_score: Optional[float] = None
    grade_distribution: Optional[Dict[str, int]] = None
    semester_distribution: Optional[Dict[str, int]] = None
    instructor_distribution: Optional[Dict[str, int]] = None
    created_at: datetime
    updated_at: datetime


class EnrollmentSummary(BaseModel):
    """Enrollment summary model."""
    model_config = ConfigDict(
        from_attributes=True,
        populate_by_name=True,
        use_enum_values=True
    )

    student_id: str
    total_courses: int
    total_credits: float
    active_enrollments: int
    completed_enrollments: int
    gpa: Optional[float] = None
    average_attendance: Optional[float] = None
    average_score: Optional[float] = None
    grade_distribution: Optional[Dict[str, int]] = None
    department_distribution: Optional[Dict[str, int]] = None
    level_distribution: Optional[Dict[str, int]] = None
    created_at: datetime
    updated_at: datetime