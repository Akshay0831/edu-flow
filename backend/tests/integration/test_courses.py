from tests.test_utils import assert_response_format, assert_error, assert_success
from src.core.exceptions import ValidationError, AuthenticationError, NotFoundError
"""Course management integration tests."""

import pytest
from unittest.mock import Mock, patch

from src.models.course import (
    CourseCreate, CourseUpdate, CourseResponse, CourseCreateResponse,
    CourseOffering, OfferingCreate, OfferingUpdate, OfferingResponse,
    Enrollment, EnrollmentCreate, EnrollmentUpdate, EnrollmentResponse,
    Department, Prerequisite, CourseStatistics, EnrollmentSummary,
    CourseStatus, CourseLevel, CreditType, Semester, Grade
)
from src.services.course_service import CourseService
from src.core.exceptions import ValidationError, NotFoundError, UnauthorizedError
from src.core.security import AuthService


class TestCourseIntegration:
    """Course management integration tests."""

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

        # Test user ID
        self.test_user_id = "USER001"

    def test_create_and_get_course(self):
        """Test complete course creation and retrieval workflow"""
        # Create course
        created_response = self.course_service.create_course(
            CourseCreate(**self.test_course_data), 
            self.test_user_id
        )
        
        assert created_response.course.title == "Test Course"
        assert created_response.course.code == "TEST101"
        assert created_response.message == "Course created successfully"

        # Get course
        retrieved_course = self.course_service.get_course(created_response.course.course_id)
        assert retrieved_course.title == "Test Course"
        assert retrieved_course.code == "TEST101"

    def test_course_update_workflow(self):
        """Test course update workflow"""
        # Create course first
        created = self.course_service.create_course(
            CourseCreate(**self.test_course_data), 
            self.test_user_id
        )

        # Update course
        update_data = CourseUpdate(title="Updated Test Course", description="Updated description")
        updated_course = self.course_service.update_course(
            created.course.course_id, 
            update_data, 
            self.test_user_id
        )

        assert updated_course.title == "Updated Test Course"
        assert updated_course.description == "Updated description"

    def test_course_deletion_workflow(self):
        """Test course deletion workflow"""
        # Create course first
        created = self.course_service.create_course(
            CourseCreate(**self.test_course_data), 
            self.test_user_id
        )

        # Delete course
        deletion_result = self.course_service.delete_course(
            created.course.course_id, 
            self.test_user_id
        )
        assert deletion_result is True

        # Verify course is deleted (should raise NotFoundError)
        with pytest.raises(NotFoundError):
            self.course_service.get_course(created.course.course_id)

    def test_course_offering_workflow(self):
        """Test course offering creation and management"""
        # Create course first
        course = self.course_service.create_course(
            CourseCreate(**self.test_course_data), 
            self.test_user_id
        )

        # Create offering
        offering_data = OfferingCreate(
            course_id=course.course.course_id,
            semester=Semester.FALL,
            academic_year=2024,
            section="001",
            instructor_id="TEACH001",
            max_enrollment=30,
            schedule="Mon, Wed, Fri 10:00-11:30",
            location="Room 101",
            credits=3.0,
            credit_type=CreditType.REGULAR,
            prerequisites=[],
            corequisites=[],
            description="Test course offering",
            learning_objectives="Learn test concepts",
            assessment_methods="Tests and assignments"
        )

        created_offering = self.course_service.create_offering(offering_data, self.test_user_id)
        assert created_offering.course_id == course.course.course_id
        assert created_offering.semester == Semester.FALL
        assert created_offering.current_enrollment == 0

        # Get offering
        retrieved_offering = self.course_service.get_offering(created_offering.offering_id)
        assert retrieved_offering.course_id == course.course.course_id

        # Update offering
        update_data = OfferingUpdate(max_enrollment=35)
        updated_offering = self.course_service.update_offering(
            created_offering.offering_id, 
            update_data, 
            self.test_user_id
        )
        assert updated_offering.max_enrollment == 35

    def test_enrollment_workflow(self):
        """Test student enrollment workflow"""
        # Create course and offering
        course = self.course_service.create_course(
            CourseCreate(**self.test_course_data), 
            self.test_user_id
        )

        offering_data = OfferingCreate(
            course_id=course.course.course_id,
            semester=Semester.FALL,
            academic_year=2024,
            section="001",
            instructor_id="TEACH001",
            max_enrollment=1,  # Small capacity for testing
            schedule="Mon, Wed, Fri 10:00-11:30",
            location="Room 101",
            credits=3.0,
            credit_type=CreditType.REGULAR,
            prerequisites=[],
            corequisites=[],
            description="Test course offering",
            learning_objectives="Learn test concepts",
            assessment_methods="Tests and assignments"
        )

        created_offering = self.course_service.create_offering(offering_data, self.test_user_id)

        # Enroll student
        enrollment_response = self.course_service.enroll_student(
            "STUDENT001", 
            created_offering.offering_id, 
            self.test_user_id
        )
        assert enrollment_response.student_id == "STUDENT001"
        assert enrollment_response.status == "enrolled"

        # Verify enrollment
        student_enrollments = self.course_service.get_student_enrollments("STUDENT001")
        assert len(student_enrollments) == 1
        assert student_enrollments[0].offering_id == created_offering.offering_id

        # Verify offering enrollment count
        offering = self.course_service.get_offering(created_offering.offering_id)
        assert offering.current_enrollment == 1

        # Try to enroll same student again (should fail)
        with pytest.raises(ValidationError):
            self.course_service.enroll_student(
                "STUDENT001", 
                created_offering.offering_id, 
                self.test_user_id
            )

        # Try to enroll another student (should fail due to capacity)
        with pytest.raises(ValidationError):
            self.course_service.enroll_student(
                "STUDENT002", 
                created_offering.offering_id, 
                self.test_user_id
            )

    def test_course_statistics(self):
        """Test course statistics generation"""
        # Create course
        course = self.course_service.create_course(
            CourseCreate(**self.test_course_data), 
            self.test_user_id
        )

        # Create offering
        offering_data = OfferingCreate(
            course_id=course.course.course_id,
            semester=Semester.FALL,
            academic_year=2024,
            section="001",
            instructor_id="TEACH001",
            max_enrollment=30,
            schedule="Mon, Wed, Fri 10:00-11:30",
            location="Room 101",
            credits=3.0,
            credit_type=CreditType.REGULAR,
            prerequisites=[],
            corequisites=[],
            description="Test course offering",
            learning_objectives="Learn test concepts",
            assessment_methods="Tests and assignments"
        )

        created_offering = self.course_service.create_offering(offering_data, self.test_user_id)

        # Enroll students
        for i in range(3):
            self.course_service.enroll_student(f"STUDENT{i}", created_offering.offering_id, self.test_user_id)

        # Update some enrollments to completed status
        enrollments = self.course_service.get_offering_enrollments(created_offering.offering_id)
        for i, enrollment in enumerate(enrollments):
            if i < 2:  # Complete first 2 enrollments
                update_data = EnrollmentUpdate(
                    final_score=85.0 + i * 5,
                    grade=Grade.A if i == 0 else Grade.B_PLUS,
                    credits_earned=3.0
                )
                self.course_service.update_enrollment(enrollment.enrollment_id, update_data, self.test_user_id)

        # Get course statistics
        stats = self.course_service.get_course_statistics(course.course.course_id)
        assert stats.course_id == course.course.course_id
        assert stats.total_enrollments == 3
        assert stats.total_completions == 2
        assert stats.completion_rate == 2/3
        assert stats.average_score == (85.0 + 90.0) / 2  # Average of completed enrollments
        assert "A" in stats.grade_distribution
        assert "B+" in stats.grade_distribution

    def test_student_summary(self):
        """Test student enrollment summary generation"""
        # Create course
        course = self.course_service.create_course(
            CourseCreate(**self.test_course_data), 
            self.test_user_id
        )

        # Create offering
        offering_data = OfferingCreate(
            course_id=course.course.course_id,
            semester=Semester.FALL,
            academic_year=2024,
            section="001",
            instructor_id="TEACH001",
            max_enrollment=30,
            schedule="Mon, Wed, Fri 10:00-11:30",
            location="Room 101",
            credits=3.0,
            credit_type=CreditType.REGULAR,
            prerequisites=[],
            corequisites=[],
            description="Test course offering",
            learning_objectives="Learn test concepts",
            assessment_methods="Tests and assignments"
        )

        created_offering = self.course_service.create_offering(offering_data, self.test_user_id)

        # Enroll student and complete course
        enrollment_response = self.course_service.enroll_student(
            "STUDENT001", 
            created_offering.offering_id, 
            self.test_user_id
        )

        # Update enrollment to completed
        update_data = EnrollmentUpdate(
            final_score=88.5,
            grade=Grade.B_PLUS,
            credits_earned=3.0
        )
        self.course_service.update_enrollment(
            enrollment_response.enrollment_id, 
            update_data, 
            self.test_user_id
        )

        # Get student summary
        summary = self.course_service.get_student_enrollment_summary("STUDENT001")
        assert summary.student_id == "STUDENT001"
        assert summary.total_courses == 1
        assert summary.total_credits == 3.0
        assert summary.completed_enrollments == 1
        assert summary.gpa == 3.5  # B+ = 3.5 GPA
        assert summary.average_score == 88.5

    def test_department_methods(self):
        """Test department-related functionality"""
        # Get all departments
        departments = self.course_service.get_all_departments()
        assert len(departments) >= 3  # Should have at least 3 test departments
        assert any(dept.code == "CS" for dept in departments)
        assert any(dept.code == "MATH" for dept in departments)
        assert any(dept.code == "PHY" for dept in departments)

    def test_prerequisites(self):
        """Test prerequisite functionality"""
        # Create two courses
        course1 = self.course_service.create_course(
            CourseCreate(
                title="Basic Course",
                code="BASIC101",
                description="Basic course content",
                department_id="DEPT001",
                level=CourseLevel.BEGINNER,
                credits=2.0,
                credit_type=CreditType.REGULAR,
                prerequisites=[],
                corequisites=[],
                learning_objectives="Learn basic concepts",
                assessment_methods="Basic assessment",
                duration_weeks=8,
                typical_semesters=[Semester.FALL]
            ), 
            self.test_user_id
        )

        course2 = self.course_service.create_course(
            CourseCreate(
                title="Advanced Course",
                code="ADV201",
                description="Advanced course content",
                department_id="DEPT001",
                level=CourseLevel.INTERMEDIATE,
                credits=3.0,
                credit_type=CreditType.REGULAR,
                prerequisites=[],
                corequisites=[],
                learning_objectives="Learn advanced concepts",
                assessment_methods="Advanced assessment",
                duration_weeks=12,
                typical_semesters=[Semester.SPRING]
            ), 
            self.test_user_id
        )

        # Add prerequisite
        result = self.course_service.add_prerequisite(
            course2.course.course_id,
            {"prerequisite_course_id": course1.course.course_id},
            self.test_user_id
        )
        assert result == f"Prerequisite added successfully for course {course2.course.course_id}"

        # Verify prerequisites
        prerequisites = self.course_service.get_course_prerequisites(course2.course.course_id)
        assert len(prerequisites) == 1
        assert prerequisites[0].prerequisite_course_id == course1.course.course_id

        # Remove prerequisite
        result = self.course_service.remove_prerequisite(
            course2.course.course_id,
            course1.course.course_id,
            self.test_user_id
        )
        assert result == f"Prerequisite removed successfully from course {course2.course.course_id}"

        # Verify removal
        prerequisites = self.course_service.get_course_prerequisites(course2.course.course_id)
        assert len(prerequisites) == 0

    def test_search_functionality(self):
        """Test course search functionality"""
        # Create multiple courses
        courses_data = [
            {
                "title": "Introduction to Python",
                "code": "CS101",
                "description": "Basic Python programming",
                "department_id": "DEPT001",
                "level": CourseLevel.BEGINNER,
                "credits": 3.0,
                "credit_type": CreditType.REGULAR,
                "prerequisites": [],
                "corequisites": [],
                "learning_objectives": "Learn Python basics",
                "assessment_methods": "Programming assignments",
                "duration_weeks": 14,
                "typical_semesters": [Semester.FALL]
            },
            {
                "title": "Advanced Java Programming",
                "code": "CS301",
                "description": "Advanced Java concepts",
                "department_id": "DEPT001",
                "level": CourseLevel.ADVANCED,
                "credits": 4.0,
                "credit_type": CreditType.REGULAR,
                "prerequisites": [],
                "corequisites": [],
                "learning_objectives": "Learn advanced Java",
                "assessment_methods": "Large project",
                "duration_weeks": 16,
                "typical_semesters": [Semester.SPRING]
            },
            {
                "title": "Calculus I",
                "code": "MATH101",
                "description": "Basic calculus concepts",
                "department_id": "DEPT002",
                "level": CourseLevel.BEGINNER,
                "credits": 4.0,
                "credit_type": CreditType.REGULAR,
                "prerequisites": [],
                "corequisites": [],
                "learning_objectives": "Learn calculus basics",
                "assessment_methods": "Exams and homework",
                "duration_weeks": 16,
                "typical_semesters": [Semester.FALL, Semester.SPRING]
            }
        ]

        created_courses = []
        for course_data in courses_data:
            created = self.course_service.create_course(CourseCreate(**course_data), self.test_user_id)
            created_courses.append(created)

        # Test search by title
        results = self.course_service.search_courses({"title": "Python"})
        assert len(results) == 1
        assert results[0].title == "Introduction to Python"

        # Test search by code
        results = self.course_service.search_courses({"code": "CS"})
        assert len(results) == 2
        assert all("CS" in course.code for course in results)

        # Test search by department
        results = self.course_service.search_courses({"department_id": "DEPT001"})
        assert len(results) == 2
        assert all(course.department_id == "DEPT001" for course in results)

        # Test search by level
        results = self.course_service.search_courses({"level": CourseLevel.BEGINNER})
        assert len(results) == 2
        assert all(course.level == CourseLevel.BEGINNER for course in results)

        # Test search by credits range
        results = self.course_service.search_courses({"min_credits": 3.5})
        assert len(results) == 2
        assert all(course.credits >= 3.5 for course in results)
        assert all(course.credits == 4.0 for course in results)  # All should be 4.0 credits

        # Test search by semester
        results = self.course_service.search_courses({"semester": Semester.FALL})
        assert len(results) == 2
        assert all(Semester.FALL in course.typical_semesters for course in results)

        # Test multiple filters
        results = self.course_service.search_courses({
            "department_id": "DEPT001",
            "level": CourseLevel.BEGINNER,
            "min_credits": 2.0
        })
        assert len(results) == 1
        assert results[0].title == "Introduction to Python"

    def test_permission_system(self):
        """Test permission system integration"""
        # Mock different permission levels
        self.auth_service.has_permission.return_value = False

        # Try to create course without permission
        with pytest.raises(UnauthorizedError):
            self.course_service.create_course(
                CourseCreate(**self.test_course_data), 
                self.test_user_id
            )

        # Mock admin permission
        self.auth_service.has_permission.return_value = True

        # Now it should work
        created = self.course_service.create_course(
            CourseCreate(**self.test_course_data), 
            self.test_user_id
        )
        assert created is not None

    def test_error_handling(self):
        """Test error handling and edge cases"""
        # Try to get non-existent course
        with pytest.raises(NotFoundError):
            self.course_service.get_course("NONEXISTENT")

        # Try to update non-existent course
        with pytest.raises(NotFoundError):
            self.course_service.update_course(
                "NONEXISTENT",
                CourseUpdate(title="Updated Title"),
                self.test_user_id
            )

        # Try to delete non-existent course
        with pytest.raises(NotFoundError):
            self.course_service.delete_course("NONEXISTENT", self.test_user_id)

        # Try to enroll in non-existent offering
        with pytest.raises(NotFoundError):
            self.course_service.enroll_student(
                "STUDENT001",
                "NONEXISTENT_OFFERING",
                self.test_user_id
            )

    def test_data_consistency(self):
        """Test data consistency across operations"""
        # Create course
        created = self.course_service.create_course(
            CourseCreate(**self.test_course_data), 
            self.test_user_id
        )

        # Get course directly
        course1 = self.course_service.get_course(created.course.course_id)

        # Get all courses
        all_courses = self.course_service.get_all_courses()
        course2 = next(c for c in all_courses if c.course_id == created.course.course_id)

        # Verify consistency
        assert course1.title == course2.title
        assert course1.code == course2.code
        assert course1.description == course2.description
        assert course1.level == course2.level
        assert course1.credits == course2.credits

        # Update course
        update_data = CourseUpdate(title="Updated Test Course")
        updated = self.course_service.update_course(
            created.course.course_id,
            update_data,
            self.test_user_id
        )

        # Verify update reflects in both methods
        course1_updated = self.course_service.get_course(created.course.course_id)
        all_courses_updated = self.course_service.get_all_courses()
        course2_updated = next(c for c in all_courses_updated if c.course_id == created.course.course_id)

        assert course1_updated.title == "Updated Test Course"
        assert course2_updated.title == "Updated Test Course"

    def teardown_method(self):
        """Clean up test data after each test"""
        # Clear all test data to prevent state contamination
        self.course_service.courses.clear()
        self.course_service.offerings.clear()
        self.course_service.enrollments.clear()