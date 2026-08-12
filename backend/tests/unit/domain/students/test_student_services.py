"""
Unit tests for student domain services

This module contains unit tests for:
- StudentService: Student business logic tests
- AcademicRecordService: Academic record management tests
- EnrollmentService: Enrollment management tests

Author: Edu-Flow Team
"""

import pytest
from datetime import datetime, date, timedelta
from unittest.mock import Mock, AsyncMock, patch

from src.domain.students.services import StudentService, AcademicRecordService, EnrollmentService
from src.domain.students.entities import Student, AcademicRecord, EnrollmentRecord, GradeLevel, AcademicStanding, RiskLevel, EnrollmentStatus
from src.domain.auth.entities import UserRole
from src.infrastructure.exceptions import NotFoundError, ValidationError
from pydantic import ValidationError as PydanticValidationError


def create_student_mock(student_id="STU001", name="John Doe", email="john.doe@example.com", 
                       grade_level=GradeLevel.TENTH, enrollment_date="2023-09-01", **kwargs):
    """Create a mock Student object with required fields"""
    return Student(
        id=student_id.upper(),
        student_id=student_id,
        name=name,
        email=email,
        grade_level=grade_level,
        enrollment_date=enrollment_date,
        **kwargs
    )


@pytest.fixture
def mock_enrollment_repository():
    """Create mock enrollment repository"""
    repository = Mock()
    repository.create = AsyncMock()
    repository.update = AsyncMock()
    repository.get_by_student_id = AsyncMock()
    repository.get_by_id = AsyncMock()
    return repository


@pytest.fixture
def mock_course_repository():
    """Create mock course repository"""
    repository = Mock()
    repository.get_by_id = AsyncMock()
    return repository


@pytest.fixture
def student_service(mock_student_repository, mock_academic_record_repository, mock_enrollment_repository):
    """Create student service fixture"""
    return StudentService(
        mock_student_repository,
        mock_academic_record_repository,
        mock_enrollment_repository
    )


@pytest.fixture
def academic_record_service(mock_academic_record_repository):
    """Create academic record service fixture"""
    return AcademicRecordService(mock_academic_record_repository)


@pytest.fixture
def enrollment_service(mock_enrollment_repository, mock_course_repository):
    """Create enrollment service fixture"""
    return EnrollmentService(mock_enrollment_repository, mock_course_repository)


@pytest.fixture
def sample_student_data():
    """Create sample student data"""
    return {
        "student_id": "STU001",
        "name": "John Doe",
        "email": "john.doe@example.com",
        "grade_level": 10,
        "enrollment_date": "2023-09-01",
        "phone": "123-456-7890",
        "address": "123 Main St"
    }


@pytest.fixture
def sample_academic_record():
    """Create sample academic record"""
    return {
        "student_id": "student-123",
        "course_id": "course-123",
        "grade": 85.0,
        "credits": 3.0,
        "semester": "Fall",
        "academic_year": "2023-2024",
        "grade_letter": "B",
        "instructor_id": "teacher-123"
    }


@pytest.mark.asyncio
async def test_create_student(student_service, sample_student_data, mock_student_repository):
        """Test creating a new student"""
        # Mock repository methods
        mock_student_repository.get_by_email.return_value = None
        mock_student_repository.get_by_student_id.return_value = None
        mock_student_repository.create.return_value = Student(
            id="student-123",
            **sample_student_data
        )
        
        # Create student
        student = await student_service.create_student(sample_student_data)
        
        # Verify repository methods were called
        mock_student_repository.get_by_email.assert_called_once_with("john.doe@example.com")
        mock_student_repository.get_by_student_id.assert_called_once_with("STU001")
        mock_student_repository.create.assert_called_once()
        
        # Verify student was created
        assert student.id is not None
        assert student.name == "John Doe"
        assert student.email == "john.doe@example.com"
        assert student.grade_level == GradeLevel.TENTH
        assert student.is_active == True


@pytest.mark.asyncio
async def test_create_student_duplicate_email(student_service, sample_student_data, mock_student_repository):
    """Test creating student with duplicate email"""
    # Mock repository to return existing student
    mock_student_repository.get_by_email.return_value = Student(
        id="existing-student",
        **sample_student_data
    )
    
    # Attempt to create student with duplicate email
    with pytest.raises(ValidationError):
            await student_service.create_student(sample_student_data)
@pytest.mark.asyncio
async def test_create_student_duplicate_student_id(student_service, sample_student_data, mock_student_repository):
    """Test creating student with duplicate student ID"""
    # Mock repository to return existing student ID
    mock_student_repository.get_by_email.return_value = None
    mock_student_repository.get_by_student_id.return_value = Student(
        id="existing-student",
        **sample_student_data
    )
    
    # Attempt to create student with duplicate ID
    with pytest.raises(ValidationError):
            await student_service.create_student(sample_student_data)
@pytest.mark.asyncio
async def test_get_student_by_id(student_service, mock_student_repository):
    """Test getting student by ID"""
    student_id = "STUDENT123"
    mock_student = create_student_mock(student_id=student_id, is_active=True, created_at=datetime.now())
    mock_student_repository.get_by_id.return_value = mock_student
    
    student = await student_service.get_student_by_id(student_id)
    
    assert student == mock_student
    mock_student_repository.get_by_id.assert_called_once_with(student_id)


@pytest.mark.asyncio
async def test_get_student_by_id_not_found(student_service, mock_student_repository):
    """Test getting student by ID when not found"""
    student_id = "non-existent-student"
    mock_student_repository.get_by_id.return_value = None
    
    with pytest.raises(NotFoundError):
        await student_service.get_student_by_id(student_id)


@pytest.mark.asyncio
async def test_update_student(student_service, mock_student_repository):
    """Test updating student information"""
    student_id = "STUDENT123"
    update_data = {"name": "Jane Doe", "phone": "987-654-3210"}
    
    existing_student = create_student_mock(student_id="STU001", is_active=True, created_at=datetime.now())
    
    mock_student_repository.get_by_id.return_value = existing_student
    mock_student_repository.update.return_value = existing_student
    
    updated_student = await student_service.update_student(student_id, update_data)
    
    assert updated_student.name == "Jane Doe"
    assert updated_student.phone == "987-654-3210"
    mock_student_repository.update.assert_called_once()


@pytest.mark.asyncio
async def test_promote_student(student_service, mock_student_repository):
    """Test promoting student to next grade level"""
    student_id = "STUDENT123"
    
    student = create_student_mock(student_id="STU001", is_active=True, created_at=datetime.now())
    
    mock_student_repository.get_by_id.return_value = student
    mock_student_repository.update.return_value = student
    
    promoted_student = await student_service.promote_student(student_id)
    
    assert promoted_student.grade_level == GradeLevel.ELEVENTH
    mock_student_repository.update.assert_called_once()


@pytest.mark.asyncio
async def test_promote_student_max_grade(student_service, mock_student_repository):
    """Test promoting student at max grade level"""
    student_id = "STUDENT123"
    
    student = create_student_mock(student_id="STU001", grade_level=GradeLevel.TWELFTH, is_active=True, created_at=datetime.now())
    
    mock_student_repository.get_by_id.return_value = student
    
    with pytest.raises(ValidationError):
        await student_service.promote_student(student_id)


@pytest.mark.asyncio
async def test_graduate_student(student_service, mock_student_repository, mock_academic_record_repository):
    """Test graduating student"""
    student_id = "STUDENT123"
    
    # Mock academic records with sufficient credits for graduation
    academic_records = [
            AcademicRecord(
                id="record-1",
                student_id=student_id,
                course_id="course-1",
                grade=85.0,  # Grade >= 60 so credits count
                credits=12.0,  # Enough credits for graduation
                semester="Fall",
                academic_year="2023-2024"
            ),
            AcademicRecord(
                id="record-2",
                student_id=student_id,
                course_id="course-2",
                grade=75.0,  # Grade >= 60 so credits count
                credits=12.0,  # More credits to ensure total >= 24
                semester="Spring",
                academic_year="2023-2024"
            )
        ]
    
    student = create_student_mock(student_id="STU001", grade_level=GradeLevel.TWELFTH, is_active=True, created_at=datetime.now())
    
    mock_student_repository.get_by_id.return_value = student
    mock_student_repository.update.return_value = student
    mock_academic_record_repository.get_by_student_id.return_value = academic_records
    
    graduated_student = await student_service.graduate_student(student_id)
    
    assert graduated_student.status.value == "graduated"
    assert graduated_student.graduation_date is not None
    mock_student_repository.update.assert_called_once()


@pytest.mark.asyncio
async def test_graduate_student_insufficient_credits(student_service, mock_student_repository, mock_academic_record_repository):
    """Test graduating student with insufficient credits"""
    student_id = "STUDENT123"
    
    # Mock insufficient academic records
    academic_records = [
            AcademicRecord(
                id="record-1",
                student_id=student_id,
                course_id="course-1",
                grade=50.0,  # Failing grade
                credits=3.0,
                semester="Fall",
                academic_year="2023-2024"
            )
        ]
    
    student = create_student_mock(student_id="STU001", grade_level=GradeLevel.TWELFTH, is_active=True, created_at=datetime.now())
    
    mock_student_repository.get_by_id.return_value = student
    mock_academic_record_repository.get_by_student_id.return_value = academic_records
    
    with pytest.raises(ValidationError):
        await student_service.graduate_student(student_id)


@pytest.mark.asyncio
async def test_get_student_academic_summary(student_service, mock_student_repository, mock_academic_record_repository):
    """Test getting student academic summary"""
    student_id = "STUDENT123"
    
    student = create_student_mock(student_id="STU001", grade_level=GradeLevel.TENTH, gpa=3.5, is_active=True, created_at=datetime.now())
    
    academic_records = [
        AcademicRecord(
            id="record-1",
            student_id=student_id,
            course_id="course-1",
            grade=85.0,
            credits=3.0,
            semester="Fall",
            academic_year="2023-2024"
        )
    ]
    
    mock_student_repository.get_by_id.return_value = student
    mock_academic_record_repository.get_by_student_id.return_value = academic_records
    
    summary = await student_service.get_student_academic_summary(student_id)
    
    assert summary["student"] == student
    assert summary["academic_records"] == academic_records
    assert summary["total_credits"] == 3.0
    assert summary["average_grade"] == 85.0
    assert summary["gpa"] == 3.5


class TestAcademicRecordService:
    """Test cases for AcademicRecordService"""
    
    @pytest.mark.asyncio
    async def test_create_academic_record(self, academic_record_service, sample_academic_record, mock_academic_record_repository):
        """Test creating academic record"""
        mock_record = AcademicRecord(
            id="record-123",
            **sample_academic_record
        )
        mock_academic_record_repository.create.return_value = mock_record
        
        record = await academic_record_service.create_academic_record(sample_academic_record)
        
        assert record.id == "record-123"
        assert record.student_id == "student-123"
        assert record.grade == 85.0
        assert record.credits == 3.0
        mock_academic_record_repository.create.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_create_academic_record_invalid_grade(self, academic_record_service, sample_academic_record, mock_academic_record_repository):
        """Test creating academic record with invalid grade"""
        invalid_record = {
            **sample_academic_record,
            "grade": 150.0  # Invalid grade
        }
        
        with pytest.raises(PydanticValidationError):
            await academic_record_service.create_academic_record(invalid_record)
    
    @pytest.mark.asyncio
    async def test_get_academic_records_by_student(self, academic_record_service, mock_academic_record_repository):
        """Test getting academic records by student"""
        student_id = "student-123"
        records = [
            AcademicRecord(
                id="record-1",
                student_id=student_id,
                course_id="course-1",
                grade=85.0,
                credits=3.0,
                semester="Fall",
                academic_year="2023-2024"
            )
        ]
        
        mock_academic_record_repository.get_by_student_id.return_value = records
        
        result = await academic_record_service.get_academic_records_by_student(student_id)
        
        assert result == records
        mock_academic_record_repository.get_by_student_id.assert_called_once_with(student_id)
    
    @pytest.mark.asyncio
    async def test_calculate_student_gpa(self, academic_record_service, mock_academic_record_repository):
        """Test calculating student GPA"""
        student_id = "student-123"
        records = [
            AcademicRecord(
                id="record-1",
                student_id=student_id,
                course_id="course-1",
                grade=85.0,  # B = 3.0
                credits=3.0,
                semester="Fall",
                academic_year="2023-2024"
            ),
            AcademicRecord(
                id="record-2",
                student_id=student_id,
                course_id="course-2",
                grade=90.0,  # A = 4.0
                credits=4.0,
                semester="Spring",
                academic_year="2023-2024"
            )
        ]
        
        mock_academic_record_repository.get_by_student_id.return_value = records
        
        gpa = await academic_record_service.calculate_student_gpa(student_id)
        
        # GPA calculation: (3.0 * 3.0 + 4.0 * 4.0) / (3.0 + 4.0) = 3.57
        assert abs(gpa - 3.57) < 0.01
        mock_academic_record_repository.get_by_student_id.assert_called_once_with(student_id)


class TestEnrollmentService:
    """Test cases for EnrollmentService"""
    
    @pytest.mark.asyncio
    async def test_create_enrollment(self, enrollment_service, sample_course, mock_enrollment_repository, mock_course_repository):
        """Test creating enrollment"""
        enrollment_data = {
            "student_id": "student-123",
            "course_id": "course-123",
            "semester": "Fall",
            "academic_year": "2023-2024"
        }
        
        mock_course_repository.get_by_id.return_value = sample_course
        mock_enrollment = EnrollmentRecord(
            id="enrollment-123",
            **enrollment_data
        )
        mock_enrollment_repository.create.return_value = mock_enrollment
        
        enrollment = await enrollment_service.create_enrollment(enrollment_data)
        
        assert enrollment.id == "enrollment-123"
        assert enrollment.student_id == "student-123"
        assert enrollment.course_id == "course-123"
        mock_course_repository.get_by_id.assert_called_once_with("course-123")
        mock_enrollment_repository.create.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_create_enrollment_course_full(self, enrollment_service, mock_enrollment_repository, mock_course_repository):
        """Test creating enrollment when course is full"""
        full_course = Mock(
            id="course-full",
            capacity=30,
            enrolled_students=30,  # Course is full
            name="Full Course"
        )
        
        enrollment_data = {
            "student_id": "student-123",
            "course_id": "course-full",
            "semester": "Fall",
            "academic_year": "2023-2024"
        }
        
        mock_course_repository.get_by_id.return_value = full_course
        
        with pytest.raises(ValidationError):
            await enrollment_service.create_enrollment(enrollment_data)

    @pytest.mark.asyncio
    async def test_get_student_enrollments(self, enrollment_service, mock_enrollment_repository):
        """Test getting student enrollments"""
        student_id = "student-123"
        enrollments = [
            EnrollmentRecord(
                id="enrollment-1",
                student_id=student_id,
                course_id="course-1",
                semester="Fall",
                academic_year="2023-2024"
            )
        ]
        
        mock_enrollment_repository.get_by_student_id.return_value = enrollments
        
        result = await enrollment_service.get_student_enrollments(student_id)
        
        assert result == enrollments
        mock_enrollment_repository.get_by_student_id.assert_called_once_with(student_id)
    
    @pytest.mark.asyncio
    async def test_enroll_student_in_course(self, enrollment_service, sample_course, mock_enrollment_repository, mock_course_repository):
        """Test enrolling student in course"""
        mock_course_repository.get_by_id.return_value = sample_course
        mock_enrollment = EnrollmentRecord(
            id="enrollment-123",
            student_id="student-123",
            course_id="course-123",
            semester="Fall",
            academic_year="2023-2024"
        )
        mock_enrollment_repository.create.return_value = mock_enrollment
        
        enrollment = await enrollment_service.enroll_student_in_course(
            "student-123",
            "course-123",
            "Fall",
            "2023-2024"
        )
        
        assert enrollment.id == "enrollment-123"
        assert enrollment.student_id == "student-123"
        assert enrollment.course_id == "course-123"
        mock_enrollment_repository.create.assert_called_once()