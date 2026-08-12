"""
Integration tests for student-teacher domain interactions

This module contains integration tests for:
- Student-teacher assignment and management
- Academic record management
- Course enrollment and teacher assignment

Author: Edu-Flow Team
"""

import pytest
from datetime import datetime, date
from unittest.mock import Mock, AsyncMock

from src.domain.students.services import StudentService, AcademicRecordService
from src.domain.students.entities import Student, AcademicRecord, GradeLevel
from src.domain.teachers.services import TeacherService
from src.domain.teachers.entities import Teacher, Qualification, EmploymentStatus
from src.domain.courses.services import CourseService
from src.domain.courses.entities import Course, CourseOffering, CourseLevel, Semester
from src.infrastructure.exceptions import NotFoundError, ValidationError


class TestStudentTeacherIntegration:
    """Integration tests for student-teacher interactions"""
    
    @pytest.fixture
    def mock_student_repository(self):
        """Create mock student repository"""
        repository = Mock()
        repository.get_by_id = AsyncMock()
        repository.get_by_email = AsyncMock()
        repository.get_by_student_id = AsyncMock()
        repository.create = AsyncMock()
        repository.update = AsyncMock()
        repository.get_by_grade_level = AsyncMock()
        repository.get_by_advisor = AsyncMock()
        return repository
    
    @pytest.fixture
    def mock_teacher_repository(self):
        """Create mock teacher repository"""
        repository = Mock()
        repository.get_by_id = AsyncMock()
        repository.get_by_email = AsyncMock()
        repository.get_by_department = AsyncMock()
        repository.create = AsyncMock()
        repository.update = AsyncMock()
        repository.get_by_subject = AsyncMock()
        return repository
    
    @pytest.fixture
    def mock_academic_record_repository(self):
        """Create mock academic record repository"""
        repository = Mock()
        repository.get_by_student_id = AsyncMock()
        repository.get_by_teacher_id = AsyncMock()
        repository.get_by_course_id = AsyncMock()
        repository.create = AsyncMock()
        repository.update = AsyncMock()
        repository.delete = AsyncMock()
        repository.get_by_id = AsyncMock()
        return repository
    
    @pytest.fixture
    def mock_course_repository(self):
        """Create mock course repository"""
        repository = Mock()
        repository.get_by_id = AsyncMock()
        repository.get_by_department = AsyncMock()
        repository.create = AsyncMock()
        repository.update = AsyncMock()
        return repository
    
    @pytest.fixture
    def mock_enrollment_repository(self):
        """Create mock enrollment repository"""
        repository = Mock()
        repository.get_by_student_id = AsyncMock()
        repository.get_by_teacher_id = AsyncMock()
        repository.get_by_course_id = AsyncMock()
        repository.create = AsyncMock()
        repository.update = AsyncMock()
        repository.delete = AsyncMock()
        repository.get_by_id = AsyncMock()
        return repository
    
    @pytest.fixture
    def mock_qualification_repository(self):
        """Create mock qualification repository"""
        repository = Mock()
        repository.get_by_teacher_id = AsyncMock()
        repository.create = AsyncMock()
        repository.update = AsyncMock()
        repository.delete = AsyncMock()
        repository.get_by_id = AsyncMock()
        return repository
    
    @pytest.fixture
    def student_service(self, mock_student_repository, mock_academic_record_repository, mock_enrollment_repository):
        """Create student service fixture"""
        return StudentService(
            mock_student_repository,
            mock_academic_record_repository,
            mock_enrollment_repository
        )
    
    @pytest.fixture
    def teacher_service(self, mock_teacher_repository, mock_qualification_repository):
        """Create teacher service fixture"""
        return TeacherService(
            mock_teacher_repository,
            mock_qualification_repository
        )
    
    @pytest.fixture
    def academic_record_service(self, mock_academic_record_repository):
        """Create academic record service fixture"""
        return AcademicRecordService(mock_academic_record_repository)
    
    @pytest.fixture
    def sample_student(self):
        """Create sample student"""
        return Student(
            id="student-123",
            student_id="STU001",
            name="John Doe",
            email="john.doe@example.com",
            grade_level=GradeLevel.TENTH,
            enrollment_date=date.today(),
            is_active=True,
            created_at=datetime.now()
        )
    
    @pytest.fixture
    def sample_teacher(self):
        """Create sample teacher"""
        return Teacher(
            id="teacher-123",
            teacher_id="TCH001",
            name="Jane Smith",
            email="jane.smith@example.com",
            employment_status=EmploymentStatus.ACTIVE,
            hire_date=datetime.now(),
            created_at=datetime.now()
        )
    
    @pytest.fixture
    def sample_qualification(self):
        """Create sample qualification"""
        return Qualification(
            id="qual-123",
            teacher_id="teacher-123",
            degree="Master of Education",
            institution="University of Education",
            field_of_study="Mathematics",
            year_graduated=2020,
            verification_status="verified"
        )
    
    @pytest.fixture
    def sample_course(self):
        """Create sample course"""
        return Course(
            id="course-123",
            title="Mathematics 10",
            code="MATH10",
            level=CourseLevel.INTERMEDIATE,
            department_id="dept-123",
            credits=4.0,
            duration_weeks=16,
            status="active",
            created_at=datetime.now()
        )
    
    @pytest.fixture
    def sample_offering(self):
        """Create sample course offering"""
        return CourseOffering(
            id="offering-123",
            course_id="course-123",
            semester=Semester.FALL,
            academic_year="2023-2024",
            section_number="A",
            schedule_id="schedule-123",
            max_enrollment=30,
            credits=4.0,
            status="active",
            created_at=datetime.now()
        )
    
    @pytest.fixture
    def sample_academic_record(self):
        """Create sample academic record"""
        return AcademicRecord(
            id="record-123",
            student_id="student-123",
            course_id="course-123",
            grade=85.0,
            credits=4.0,
            semester="Fall",
            academic_year="2023-2024",
            instructor_id="teacher-123",
            created_at=datetime.now()
        )
    
    def test_assign_advisor_to_student(self, student_service, teacher_service, sample_student, sample_teacher, mock_student_repository, mock_teacher_repository):
        """Test assigning teacher as advisor to student"""
        # Mock student retrieval
        mock_student_repository.get_by_id.return_value = sample_student
        mock_student_repository.update.return_value = sample_student
        
        # Mock teacher retrieval
        mock_teacher_repository.get_by_id.return_value = sample_teacher
        
        # Assign advisor
        student_service.assign_advisor("student-123", "teacher-123")
        
        # Verify student was updated
        assert sample_student.advisor_id == "teacher-123"
        mock_student_repository.update.assert_called_once()
    
    def test_assign_teacher_to_student_as_advisor(self, student_service, teacher_service, sample_student, sample_teacher, mock_student_repository, mock_teacher_repository):
        """Test assigning teacher to student as advisor"""
        # Mock student retrieval
        mock_student_repository.get_by_id.return_value = sample_student
        mock_student_repository.update.return_value = sample_student
        
        # Mock teacher retrieval
        mock_teacher_repository.get_by_id.return_value = sample_teacher
        
        # Assign advisor through student service
        student_service.assign_advisor("student-123", "teacher-123")
        
        # Verify assignment
        assert sample_student.advisor_id == "teacher-123"
        mock_student_repository.update.assert_called_once()
    
    def test_teacher_get_assigned_students(self, student_service, teacher_service, sample_student, sample_teacher, mock_student_repository, mock_teacher_repository):
        """Test getting students assigned to teacher"""
        # Set teacher as advisor
        sample_student.advisor_id = "teacher-123"
        
        # Mock student retrieval
        mock_student_repository.get_by_advisor.return_value = [sample_student]
        
        # Get assigned students
        assigned_students = teacher_service.get_assigned_students("teacher-123")
        
        # Verify assignment
        assert len(assigned_students) == 1
        assert assigned_students[0].id == "student-123"
        mock_student_repository.get_by_advisor.assert_called_once_with("teacher-123")
    
    def test_teacher_student_academic_performance_tracking(self, student_service, teacher_service, sample_student, sample_teacher, sample_academic_record, mock_student_repository, mock_teacher_repository, mock_academic_record_repository):
        """Test teacher tracking student academic performance"""
        # Mock data
        sample_student.advisor_id = "teacher-123"
        sample_academic_record.instructor_id = "teacher-123"
        
        mock_student_repository.get_by_id.return_value = sample_student
        mock_academic_record_repository.get_by_student_id.return_value = [sample_academic_record]
        mock_academic_record_repository.get_by_teacher_id.return_value = [sample_academic_record]
        
        # Get student academic summary
        summary = student_service.get_student_academic_summary("student-123")
        
        # Verify summary includes student and records
        assert summary["student"] == sample_student
        assert len(summary["academic_records"]) == 1
        assert summary["average_grade"] == 85.0
        
        # Get teacher's student performance
        teacher_performance = teacher_service.get_student_performance("teacher-123")
        
        # Verify teacher performance data
        assert len(teacher_performance["students"]) == 1
        assert teacher_performance["average_grade"] == 85.0
        assert teacher_performance["total_students"] == 1
    
    def test_teacher_qualification_validation(self, teacher_service, sample_teacher, sample_qualification, mock_teacher_repository):
        """Test teacher qualification validation"""
        # Mock teacher retrieval
        mock_teacher_repository.get_by_id.return_value = sample_teacher
        mock_teacher_repository.update.return_value = sample_teacher
        
        # Add qualification
        teacher_service.add_qualification("teacher-123", sample_qualification)
        
        # Verify qualification was added
        assert len(sample_teacher.qualifications) == 1
        assert sample_teacher.qualifications[0].id == "qual-123"
        mock_teacher_repository.update.assert_called_once()
    
    def test_teacher_promotion_eligibility_check(self, teacher_service, sample_teacher, mock_teacher_repository):
        """Test teacher promotion eligibility check"""
        # Mock teacher retrieval
        mock_teacher_repository.get_by_id.return_value = sample_teacher
        
        # Check eligibility
        is_eligible = teacher_service.is_eligible_for_promotion("teacher-123")
        
        # Verify eligibility based on criteria
        assert is_eligible == sample_teacher.is_eligible_for_promotion()
    
    def test_course_enrollment_with_teacher_assignment(self, student_service, teacher_service, sample_student, sample_teacher, sample_course, sample_offering, mock_student_repository, mock_teacher_repository, mock_course_repository, mock_enrollment_repository):
        """Test course enrollment with teacher assignment"""
        # Mock data
        sample_offering.instructor_id = "teacher-123"
        
        mock_student_repository.get_by_id.return_value = sample_student
        mock_teacher_repository.get_by_id.return_value = sample_teacher
        mock_course_repository.get_by_id.return_value = sample_course
        mock_enrollment_repository.get_by_student_id.return_value = []
        
        # Enroll student in course
        enrollment = student_service.enroll_student_in_course(
            "student-123",
            "course-123",
            "Fall",
            "2023-2024"
        )
        
        # Verify enrollment
        assert enrollment.student_id == "student-123"
        assert enrollment.course_id == "course-123"
        mock_enrollment_repository.create.assert_called_once()
    
    def test_teacher_course_assignment(self, teacher_service, sample_teacher, sample_course, sample_offering, mock_teacher_repository, mock_course_repository, mock_enrollment_repository):
        """Test teacher course assignment"""
        # Mock data
        sample_offering.instructor_id = "teacher-123"
        
        mock_teacher_repository.get_by_id.return_value = sample_teacher
        mock_course_repository.get_by_id.return_value = sample_course
        mock_enrollment_repository.get_by_teacher_id.return_value = [sample_offering]
        
        # Assign teacher to course
        teacher_service.assign_course("teacher-123", "course-123", "Fall", "2023-2024")
        
        # Verify assignment
        assert "course-123" in sample_teacher.subjects
        mock_teacher_repository.update.assert_called_once()
    
    def test_student_teacher_performance_analysis(self, student_service, teacher_service, sample_student, sample_teacher, sample_academic_record, mock_student_repository, mock_teacher_repository, mock_academic_record_repository):
        """Test performance analysis between student and teacher"""
        # Mock data
        sample_student.advisor_id = "teacher-123"
        sample_academic_record.instructor_id = "teacher-123"
        
        mock_student_repository.get_by_id.return_value = sample_student
        mock_teacher_repository.get_by_id.return_value = sample_teacher
        mock_academic_record_repository.get_by_student_id.return_value = [sample_academic_record]
        mock_academic_record_repository.get_by_teacher_id.return_value = [sample_academic_record]
        
        # Get teacher's students performance
        teacher_performance = teacher_service.get_student_performance("teacher-123")
        
        # Verify performance analysis
        assert len(teacher_performance["students"]) == 1
        assert teacher_performance["average_grade"] == 85.0
        assert teacher_performance["total_students"] == 1
        assert teacher_performance["total_credits"] == 4.0
    
    def test_student_teacher_interaction_logging(self, student_service, teacher_service, sample_student, sample_teacher, mock_student_repository, mock_teacher_repository):
        """Test logging student-teacher interactions"""
        # Mock repositories
        mock_student_repository.get_by_id.return_value = sample_student
        mock_teacher_repository.get_by_id.return_value = sample_teacher
        
        # Simulate interaction
        student_service.assign_advisor("student-123", "teacher-123")
        
        # Verify interaction was logged through repository calls
        mock_student_repository.update.assert_called_once()
    
    def test_teacher_student_feedback_loop(self, student_service, teacher_service, sample_student, sample_teacher, mock_student_repository, mock_teacher_repository):
        """Test feedback loop between teacher and student"""
        # Set up advisor relationship
        sample_student.advisor_id = "teacher-123"
        
        mock_student_repository.get_by_id.return_value = sample_student
        mock_teacher_repository.get_by_id.return_value = sample_teacher
        mock_student_repository.get_by_advisor.return_value = [sample_student]
        
        # Teacher provides feedback
        feedback = "John is showing good improvement in mathematics"
        teacher_service.provide_feedback("teacher-123", "student-123", feedback)
        
        # Verify feedback was recorded (would need feedback repository)
        mock_student_repository.update.assert_called()
    
    def test_teacher_student_progress_monitoring(self, student_service, teacher_service, sample_student, sample_teacher, sample_academic_record, mock_student_repository, mock_teacher_repository, mock_academic_record_repository):
        """Test teacher monitoring student progress"""
        # Set up relationships
        sample_student.advisor_id = "teacher-123"
        sample_academic_record.instructor_id = "teacher-123"
        
        mock_student_repository.get_by_id.return_value = sample_student
        mock_teacher_repository.get_by_id.return_value = sample_teacher
        mock_academic_record_repository.get_by_student_id.return_value = [sample_academic_record]
        
        # Monitor student progress
        progress = teacher_service.monitor_student_progress("teacher-123", "student-123")
        
        # Verify progress monitoring
        assert progress["student_id"] == "student-123"
        assert progress["average_grade"] == 85.0
        assert progress["total_credits"] == 4.0
    
    def test_teacher_student_evaluation(self, student_service, teacher_service, sample_student, sample_teacher, sample_academic_record, mock_student_repository, mock_teacher_repository, mock_academic_record_repository):
        """Test teacher evaluation of student"""
        # Set up relationships
        sample_student.advisor_id = "teacher-123"
        sample_academic_record.instructor_id = "teacher-123"
        
        mock_student_repository.get_by_id.return_value = sample_student
        mock_teacher_repository.get_by_id.return_value = sample_teacher
        mock_academic_record_repository.get_by_student_id.return_value = [sample_academic_record]
        
        # Evaluate student
        evaluation = teacher_service.evaluate_student("teacher-123", "student-123")
        
        # Verify evaluation
        assert evaluation["student_id"] == "student-123"
        assert evaluation["performance_rating"] == "Good"
        assert evaluation["recommendation"] == "Continue current study plan"


class TestAcademicRecordIntegration:
    """Integration tests for academic record management"""
    
    @pytest.fixture
    def academic_record_service(self, mock_academic_record_repository):
        """Create academic record service fixture"""
        return AcademicRecordService(mock_academic_record_repository)
    
    def test_academic_record_creation_and_validation(self, academic_record_service, sample_academic_record, mock_academic_record_repository):
        """Test creating and validating academic record"""
        # Mock record creation
        mock_academic_record_repository.create.return_value = sample_academic_record
        
        # Create record
        record = academic_record_service.create_academic_record({
            "student_id": "student-123",
            "course_id": "course-123",
            "grade": 85.0,
            "credits": 4.0,
            "semester": "Fall",
            "academic_year": "2023-2024"
        })
        
        # Verify record creation
        assert record.id == "record-123"
        assert record.grade == 85.0
        assert record.credits == 4.0
        mock_academic_record_repository.create.assert_called_once()
    
    def test_academic_record_grade_validation(self, academic_record_service, mock_academic_record_repository):
        """Test academic record grade validation"""
        # Test invalid grade
        with pytest.raises(ValidationError):
            academic_record_service.create_academic_record({
                "student_id": "student-123",
                "course_id": "course-123",
                "grade": 150.0,  # Invalid grade
                "credits": 4.0,
                "semester": "Fall",
                "academic_year": "2023-2024"
            })
    
    def test_academic_record_credits_validation(self, academic_record_service, mock_academic_record_repository):
        """Test academic record credits validation"""
        # Test invalid credits
        with pytest.raises(ValidationError):
            academic_record_service.create_academic_record({
                "student_id": "student-123",
                "course_id": "course-123",
                "grade": 85.0,
                "credits": 0.0,  # Invalid credits
                "semester": "Fall",
                "academic_year": "2023-2024"
            })
    
    def test_academic_record_teacher_assignment(self, academic_record_service, sample_academic_record, mock_academic_record_repository):
        """Test assigning teacher to academic record"""
        # Mock record retrieval
        mock_academic_record_repository.get_by_id.return_value = sample_academic_record
        mock_academic_record_repository.update.return_value = sample_academic_record
        
        # Assign teacher
        updated_record = academic_record_service.assign_instructor("record-123", "teacher-123")
        
        # Verify assignment
        assert updated_record.instructor_id == "teacher-123"
        mock_academic_record_repository.update.assert_called_once()
    
    def test_academic_record_student_performance_tracking(self, academic_record_service, sample_student, sample_academic_record, mock_academic_record_repository, mock_student_repository):
        """Test tracking student performance through academic records"""
        # Mock data
        mock_student_repository.get_by_id.return_value = sample_student
        mock_academic_record_repository.get_by_student_id.return_value = [sample_academic_record]
        
        # Get student performance
        performance = academic_record_service.get_student_performance("student-123")
        
        # Verify performance tracking
        assert performance["student_id"] == "student-123"
        assert performance["average_grade"] == 85.0
        assert performance["total_credits"] == 4.0
        assert len(performance["records"]) == 1