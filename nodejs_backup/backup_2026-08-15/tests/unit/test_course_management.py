from tests.test_utils import assert_response_format, assert_error, assert_success
from src.core.exceptions import ValidationError, AuthenticationError, NotFoundError
"""Comprehensive unit tests for course management system."""

import pytest
from datetime import date, datetime
from unittest.mock import Mock, patch

from src.models.course import (
    Course, CourseCreate, CourseUpdate, CourseResponse, CourseCreateResponse,
    CourseOffering, OfferingCreate, OfferingUpdate, OfferingResponse,
    Enrollment, EnrollmentCreate, EnrollmentUpdate, EnrollmentResponse,
    Department, Prerequisite, CourseStatistics, EnrollmentSummary,
    CourseStatus, CourseLevel, CreditType, Semester, Grade
)
from src.services.course_service import CourseService
from src.core.exceptions import ValidationError, NotFoundError, UnauthorizedError
from pydantic import ValidationError as PydanticValidationError
from src.core.security import AuthService


class TestCourseManagement:
    """Comprehensive test suite for course management system."""

    def setup_method(self):
        """Set up test fixtures before each test"""
        self.auth_service = Mock(spec=AuthService)
        # Ensure the mock has both permission methods
        self.auth_service.check_permission = Mock(return_value=True)
        self.auth_service.has_permission = Mock(return_value=True)
        self.course_service = CourseService(self.auth_service)

        # Test course data
        self.test_course_data = {
            "title": "Test Course",
            "code": "TEST101",
            "description": "A test course for validation",
            "department_id": "DEPT001",
            "level": CourseLevel.BEGINNER,
            "credits": 3.0,
            "credit_type": CreditType.REGULAR,
            "prerequisites": [],
            "corequisites": [],
            "learning_objectives": "Learn test concepts",
            "assessment_methods": "Tests and assignments",
            "duration_weeks": 16,
            "typical_semesters": [Semester.FALL, Semester.SPRING]
        }

        # Test offering data
        self.test_offering_data = {
            "course_id": "COURSE001",
            "semester": Semester.FALL,
            "academic_year": 2024,
            "section": "001",
            "instructor_id": "TEACH001",
            "max_enrollment": 30,
            "schedule": "Mon, Wed, Fri 10:00-11:30",
            "location": "Room 101",
            "credits": 3.0,
            "credit_type": CreditType.REGULAR,
            "prerequisites": [],
            "corequisites": [],
            "description": "Test course offering",
            "learning_objectives": "Learn test concepts",
            "assessment_methods": "Tests and assignments"
        }

        # Test enrollment data
        self.test_enrollment_data = {
            "offering_id": "OFFERING001"
        }

        # Test student ID
        self.test_student_id = "STUDENT001"
        self.test_user_id = "USER001"

    # Course Management Tests
    
    def test_create_course_success(self):
        """Test successful course creation"""
        course_data = CourseCreate(**self.test_course_data)
        result = self.course_service.create_course(course_data, self.test_user_id)
        
        assert result.course.title == "Test Course"
        assert result.course.code == "TEST101"
        assert result.course.department_id == "DEPT001"
        assert result.course.level == CourseLevel.BEGINNER
        assert result.course.credits == 3.0
        assert result.course.is_active is True
        assert result.course.created_at is not None
        assert result.course.updated_at is not None
        
        # Verify course is stored
        assert result.course.course_id in self.course_service.courses

    def test_create_course_duplicate_code(self):
        """Test creating course with duplicate code"""
        # Create first course
        course_data = CourseCreate(**self.test_course_data)
        self.course_service.create_course(course_data, self.test_user_id)
        
        # Try to create course with same code
        duplicate_data = course_data.model_copy()
        duplicate_data.title = "Different Course"
        
        with pytest.raises(ValidationError, match="Course code TEST101 already exists"):
            self.course_service.create_course(duplicate_data, self.test_user_id)

    def test_create_course_missing_required_fields(self):
        """Test course creation with missing required fields"""
        incomplete_data = {
            "title": "Test Course",
            # Missing required fields
        }
        
        with pytest.raises(PydanticValidationError):
            course_data = CourseCreate(**incomplete_data)
            self.course_service.create_course(course_data, self.test_user_id)

    def test_create_course_invalid_credits(self):
        """Test course creation with invalid credits"""
        invalid_data = self.test_course_data.copy()
        invalid_data["credits"] = 0.0  # Invalid: must be > 0
        
        with pytest.raises(PydanticValidationError, match="Credits must be between 0 and 10, and cannot be 0"):
            course_data = CourseCreate(**invalid_data)
            self.course_service.create_course(course_data, self.test_user_id)

    def test_create_course_invalid_duration(self):
        """Test course creation with invalid duration"""
        invalid_data = self.test_course_data.copy()
        invalid_data["duration_weeks"] = 0  # Invalid: must be > 0
        
        with pytest.raises(PydanticValidationError, match="Duration must be between 1 and 52 weeks"):
            course_data = CourseCreate(**invalid_data)
            self.course_service.create_course(course_data, self.test_user_id)

    def test_get_course_success(self):
        """Test successful course retrieval"""
        # Create course first
        course_data = CourseCreate(**self.test_course_data)
        created = self.course_service.create_course(course_data, self.test_user_id)
        
        # Get course by ID
        retrieved = self.course_service.get_course(created.course.course_id)
        
        assert retrieved.course_id == created.course.course_id
        assert retrieved.title == "Test Course"
        assert retrieved.code == "TEST101"

    def test_get_course_not_found(self):
        """Test retrieving non-existent course"""
        with pytest.raises(NotFoundError, match="Course nonexistent not found"):
            self.course_service.get_course("nonexistent")

    def test_get_course_by_code_success(self):
        """Test successful course retrieval by code"""
        # Create course first
        course_data = CourseCreate(**self.test_course_data)
        created = self.course_service.create_course(course_data, self.test_user_id)
        
        # Get course by code
        retrieved = self.course_service.get_course_by_code("TEST101")
        
        assert retrieved.course_id == created.course.course_id
        assert retrieved.code == "TEST101"

    def test_get_course_by_code_not_found(self):
        """Test retrieving non-existent course by code"""
        with pytest.raises(NotFoundError, match="Course with code nonexistent not found"):
            self.course_service.get_course_by_code("nonexistent")

    def test_get_all_courses(self):
        """Test getting all courses with pagination"""
        # Create multiple courses
        for i in range(3):
            course_data = self.test_course_data.copy()
            course_data["title"] = f"Test Course {i+1}"
            course_data["code"] = f"TEST{i+1}01"
            
            course_create = CourseCreate(**course_data)
            self.course_service.create_course(course_create, self.test_user_id)
        
        # Get all courses
        all_courses = self.course_service.get_all_courses()
        assert len(all_courses) >= 3
        
        # Test pagination
        first_two = self.course_service.get_all_courses(limit=2, offset=0)
        assert len(first_two) <= 2

    def test_update_course_success(self):
        """Test successful course update"""
        # Create course first
        course_data = CourseCreate(**self.test_course_data)
        created = self.course_service.create_course(course_data, self.test_user_id)
        
        # Update course
        update_data = CourseUpdate(
            title="Updated Test Course",
            description="Updated description"
        )
        updated = self.course_service.update_course(
            created.course.course_id, update_data, self.test_user_id
        )
        
        assert updated.title == "Updated Test Course"
        assert updated.description == "Updated description"
        assert updated.code == "TEST101"  # Unchanged
        assert updated.updated_at > created.course.updated_at

    def test_update_course_not_found(self):
        """Test updating non-existent course"""
        update_data = CourseUpdate(title="Updated Title")
        
        with pytest.raises(NotFoundError, match="Course nonexistent not found"):
            self.course_service.update_course("nonexistent", update_data, self.test_user_id)

    def test_update_course_duplicate_code(self):
        """Test updating course to duplicate code"""
        # Create two courses
        course_data1 = CourseCreate(**self.test_course_data)
        course_data2 = CourseCreate(
            title="Different Course",
            code="TEST202",
            description="Different test course",
            department_id="DEPT001",
            level=CourseLevel.BEGINNER,
            credits=3.0,
            credit_type=CreditType.REGULAR,
            prerequisites=[],
            corequisites=[],
            learning_objectives="Learn different concepts",
            assessment_methods="Different tests",
            duration_weeks=16,
            typical_semesters=[Semester.FALL, Semester.SPRING]
        )
        
        created1 = self.course_service.create_course(course_data1, self.test_user_id)
        created2 = self.course_service.create_course(course_data2, self.test_user_id)
        
        # Try to update second course to have same code as first
        update_data = CourseUpdate(code="TEST101")
        
        with pytest.raises(ValidationError, match="Course code TEST101 already exists"):
            self.course_service.update_course(created2.course.course_id, update_data, self.test_user_id)

    def test_delete_course_not_found(self):
        """Test deleting non-existent course"""
        with pytest.raises(NotFoundError, match="Course nonexistent not found"):
            self.course_service.delete_course("nonexistent", self.test_user_id)

    def test_search_courses_by_department(self):
        """Test searching courses by department"""
        # Create course in different department
        course_data = CourseCreate(**self.test_course_data)
        created = self.course_service.create_course(course_data, self.test_user_id)
        
        # Search by department
        results = self.course_service.search_courses({"department_id": "DEPT001"})
        assert len(results) >= 1
        assert all(course.department_id == "DEPT001" for course in results)

    def test_search_courses_by_level(self):
        """Test searching courses by level"""
        # Create course
        course_data = CourseCreate(**self.test_course_data)
        created = self.course_service.create_course(course_data, self.test_user_id)
        
        # Search by level
        results = self.course_service.search_courses({"level": CourseLevel.BEGINNER})
        assert len(results) >= 1
        assert all(course.level == CourseLevel.BEGINNER for course in results)

    def test_search_courses_by_code(self):
        """Test searching courses by code (partial match)"""
        # Create course
        course_data = CourseCreate(**self.test_course_data)
        created = self.course_service.create_course(course_data, self.test_user_id)
        
        # Search by code (partial match)
        results = self.course_service.search_courses({"code": "TEST"})
        assert len(results) >= 1
        assert all("TEST" in course.code for course in results)

    def test_search_courses_by_title(self):
        """Test searching courses by title (partial match)"""
        # Create course
        course_data = CourseCreate(**self.test_course_data)
        created = self.course_service.create_course(course_data, self.test_user_id)
        
        # Search by title (partial match)
        results = self.course_service.search_courses({"title": "Test"})
        assert len(results) >= 1
        assert all("Test" in course.title for course in results)

    def test_search_courses_by_credits_range(self):
        """Test searching courses by credits range"""
        # Create course
        course_data = CourseCreate(**self.test_course_data)
        created = self.course_service.create_course(course_data, self.test_user_id)
        
        # Search by credits range
        results = self.course_service.search_courses({
            "min_credits": 2.0,
            "max_credits": 4.0
        })
        assert len(results) >= 1
        assert all(2.0 <= course.credits <= 4.0 for course in results)

    def test_search_courses_by_semester(self):
        """Test searching courses by typical semester"""
        # Create course
        course_data = CourseCreate(**self.test_course_data)
        created = self.course_service.create_course(course_data, self.test_user_id)
        
        # Search by semester
        results = self.course_service.search_courses({"semester": Semester.FALL})
        assert len(results) >= 1
        assert all(Semester.FALL in course.typical_semesters for course in results)