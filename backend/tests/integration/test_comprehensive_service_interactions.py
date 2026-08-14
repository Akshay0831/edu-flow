"""
Comprehensive Service Interaction Integration Tests

This module provides comprehensive integration tests for service-to-service interactions
within the Edu-Flow backend system. It tests the coordinated functionality across
multiple services to ensure they work together correctly.

Author: Edu-Flow Team
"""

import pytest
import asyncio
from datetime import date, datetime
from typing import Dict, List, Any
import uuid
import time

from src.infrastructure.services.student_service import StudentService
from src.infrastructure.services.teacher_service import TeacherService
from src.infrastructure.services.course_service import CourseService
from src.infrastructure.services.department_service import DepartmentService
from src.infrastructure.services.class_service import ClassService
from src.infrastructure.services.mark_service import MarkService
from src.models.student import StudentResponse, GradeLevel, UserRole
from src.models.teacher import TeacherResponse
from src.models.course import CourseResponse
from src.models.department_model import DepartmentResponse
from src.models.class_model import ClassResponse
from src.models.mark_model import MarkResponse


@pytest.fixture
def setup_test_data():
    """Set up test data for integration tests."""
    from tests.mock_database_manager import MockDatabaseManager
    from src.infrastructure.repositories.student_repository import StudentRepository
    from src.infrastructure.repositories.teacher_repository_fixed import TeacherRepository
    from src.infrastructure.repositories.course_repository import CourseRepository
    from src.infrastructure.repositories.class_repository import ClassRepository
    from src.infrastructure.repositories.department_repository import DepartmentRepository
    from src.infrastructure.repositories.mark_repository import MarkRepository
    
    # Create mock database manager
    mock_db_manager = MockDatabaseManager()
    
    # Create repositories
    student_repository = StudentRepository()
    teacher_repository = TeacherRepository()
    course_repository = CourseRepository(mock_db_manager)
    class_repository = ClassRepository(mock_db_manager)
    department_repository = DepartmentRepository(mock_db_manager)
    mark_repository = MarkRepository(mock_db_manager)
    
    # Import and create services
    from src.infrastructure.services.student_service import StudentService
    from src.infrastructure.services.teacher_service import TeacherService
    from src.infrastructure.services.course_service import CourseService
    from src.infrastructure.services.department_service import DepartmentService
    from src.infrastructure.services.class_service import ClassService
    from src.infrastructure.services.mark_service import MarkService
    
    # Create services with repositories
    student_service = StudentService(student_repository)
    teacher_service = TeacherService(teacher_repository)
    course_service = CourseService(course_repository)
    department_service = DepartmentService(department_repository)
    class_service = ClassService(class_repository)
    mark_service = MarkService(mark_repository)
    
    # Create test departments
        dept1_data = {
            "name": "Computer Science",
            "code": "CS",
            "description": "Computer Science Department",
            "head_id": None
        }
        
        dept2_data = {
            "name": "Mathematics", 
            "code": "MATH",
            "description": "Mathematics Department",
            "head_id": None
        }
        
        dept1 = asyncio.run(department_service.create_department(dept1_data))
        dept2 = asyncio.run(department_service.create_department(dept2_data))
        
        # Create test teachers
        teacher1_data = {
            "name": "Dr. Smith",
            "email": "smith@example.com",
            "employee_id": "T001",
            "department_id": dept1.id,
            "specialization": "Algorithms",
            "qualification": "PhD",
            "experience_years": 10
        }
        
        teacher2_data = {
            "name": "Dr. Johnson",
            "email": "johnson@example.com",
            "employee_id": "T002",
            "department_id": dept2.id,
            "specialization": "Calculus",
            "qualification": "PhD",
            "experience_years": 8
        }
        
        teacher1 = asyncio.run(teacher_service.create_teacher(teacher1_data))
        teacher2 = asyncio.run(teacher_service.create_teacher(teacher2_data))
        
        # Create test courses
        course1_data = {
            "name": "Data Structures",
            "code": "CS101",
            "description": "Introduction to data structures",
            "credits": 3,
            "department_id": dept1.id,
            "level": GradeLevel.TENTH,
            "prerequisites": []
        }
        
        course2_data = {
            "name": "Calculus I",
            "code": "MATH101", 
            "description": "Introduction to differential calculus",
            "credits": 4,
            "department_id": dept2.id,
            "level": GradeLevel.TENTH,
            "prerequisites": []
        }
        
        course1 = asyncio.run(course_service.create_course(course1_data))
        course2 = asyncio.run(course_service.create_course(course2_data))
        "email": "student2@example.com", 
        "password": "Password123",
        "name": "Bob Smith",
        "student_id": "S002",
        "enrollment_date": date(2020, 9, 1),
        "grade_level": GradeLevel.TENTH,
        "department_id": dept2.id,
        "gpa": 3.2
    }
    
student1 = asyncio.run(student_service.create_student(student1_data))
        student2 = asyncio.run(student_service.create_student(student2_data))
    
    # Create test classes
    class1_data = {
        "name": "CS101 - Section A",
        "course_id": course1.id,
        "teacher_id": teacher1.id,
        "academic_year": "2020-2021",
        "semester": "Fall",
        "capacity": 30,
        "schedule": "Mon/Wed/Fri 9:00-10:00"
    }
    
    class2_data = {
        "name": "MATH101 - Section B",
        "course_id": course2.id,
        "teacher_id": teacher2.id,
        "academic_year": "2020-2021", 
        "semester": "Fall",
        "capacity": 25,
        "schedule": "Tue/Thu 11:00-12:30"
    }
    
class1 = asyncio.run(class_service.create_class(class1_data))
        class2 = asyncio.run(class_service.create_class(class2_data))
    
    # Enroll students in classes
    mark1_data = {
        "student_id": student1.id,
        "class_id": class1.id,
        "enrollment_date": date(2020, 9, 15),
        "status": "enrolled"
    }
    
    mark2_data = {
        "student_id": student2.id,
        "class_id": class2.id,
        "enrollment_date": date(2020, 9, 15),
        "status": "enrolled"
    }
    
mark1 = asyncio.run(mark_service.create_enrollment(mark1_data))
        mark2 = asyncio.run(mark_service.create_enrollment(mark2_data))
    
    return {
        'student_service': student_service,
        'teacher_service': teacher_service,
        'course_service': course_service,
        'department_service': department_service,
        'class_service': class_service,
        'mark_service': mark_service,
        'dept1': dept1,
        'dept2': dept2,
        'teacher1': teacher1,
        'teacher2': teacher2,
        'course1': course1,
        'course2': course2,
        'student1': student1,
        'student2': student2,
        'class1': class1,
        'class2': class2,
        'mark1': mark1,
        'mark2': mark2
    }


class TestComprehensiveServiceInteractions:
    """Comprehensive service interaction tests."""
    
    def test_student_teacher_department_flow(self, setup_test_data):
        """Test the complete flow from student to teacher through department."""
        data = setup_test_data
        
        # Get student's department
        student = data['student1']
        dept = data['department_service'].get_department(student.department_id)
        
        # Get all teachers in that department
        teachers = data['teacher_service'].get_teachers_by_department(dept.id)
        
        # Verify the student's teacher is in the department
        teacher_found = any(t.id == data['teacher1'].id for t in teachers)
        assert teacher_found
        
        # Get courses offered by that department
        courses = data['course_service'].get_courses_by_department(dept.id)
        
        # Verify the student's course is offered by the department
        course_found = any(c.id == data['course1'].id for c in courses)
        assert course_found
    
    def test_class_enrollment_flow(self, setup_test_data):
        """Test the complete class enrollment flow."""
        data = setup_test_data
        
        # Get student's enrolled classes
        student = data['student1']
        marks = data['mark_service'].get_marks_by_student(student.id)
        
        # Verify student is enrolled in the correct class
        assert len(marks) == 1
        enrollment = marks[0]
        assert enrollment.status == 'enrolled'
        assert enrollment.student_id == student.id
        
        # Get class details
        class_obj = data['class_service'].get_class(enrollment.class_id)
        
        # Verify class is associated with the correct course and teacher
        assert class_obj.course_id == data['course1'].id
        assert class_obj.teacher_id == data['teacher1'].id
    
    def test_grade_calculation_flow(self, setup_test_data):
        """Test grade calculation and student performance tracking."""
        data = setup_test_data
        
        # Add marks for the student
        student = data['student1']
        class_obj = data['class1']
        
        # Add assignment marks
        assignment_mark = data['mark_service'].create_mark({
            'student_id': student.id,
            'class_id': class_obj.id,
            'assessment_type': 'assignment',
            'title': 'Midterm Exam',
            'max_score': 100,
            'score': 85,
            'weight': 0.3
        })
        
        # Add quiz marks
        quiz_mark = data['mark_service'].create_mark({
            'student_id': student.id,
            'class_id': class_obj.id,
            'assessment_type': 'quiz',
            'title': 'Weekly Quiz 1',
            'max_score': 50,
            'score': 45,
            'weight': 0.2
        })
        
        # Add final exam marks
        final_mark = data['mark_service'].create_mark({
            'student_id': student.id,
            'class_id': class_obj.id,
            'assessment_type': 'final',
            'title': 'Final Exam',
            'max_score': 100,
            'score': 92,
            'weight': 0.5
        })
        
        # Get student's overall performance
        student_marks = data['mark_service'].get_marks_by_student(student.id)
        
        # Verify all marks are recorded
        assert len(student_marks) == 4  # 1 enrollment + 3 assessment marks
        
        # Calculate weighted average
        weighted_sum = (
            assignment_mark.score * assignment_mark.weight +
            quiz_mark.score * quiz_mark.weight +
            final_mark.score * final_mark.weight
        )
        expected_grade = weighted_sum / (assignment_mark.weight + quiz_mark.weight + final_mark.weight)
        
        # Get student statistics
        stats = data['student_service'].get_student_statistics()
        
        # Verify statistics are calculated correctly
        assert stats.total_students >= 2
        assert stats.average_gpa > 0
    
    def test_department_course_prerequisites(self, setup_test_data):
        """Test course prerequisites and academic progression."""
        data = setup_test_data
        
        # Create an advanced course with prerequisites
        advanced_course_data = {
            "name": "Advanced Algorithms",
            "code": "CS201",
            "description": "Advanced algorithm design and analysis",
            "credits": 4,
            "department_id": data['dept1'].id,
            "level": GradeLevel.ELEVENTH,
            "prerequisites": [data['course1'].id]  # Requires Data Structures
        }
        
        advanced_course = data['course_service'].create_course(advanced_course_data)
        
        # Create another advanced course
        advanced_course2_data = {
            "name": "Machine Learning",
            "code": "CS301",
            "description": "Introduction to machine learning",
            "credits": 3,
            "department_id": data['dept1'].id,
            "level": GradeLevel.TWELFTH,
            "prerequisites": [advanced_course.id]  # Requires Advanced Algorithms
        }
        
        advanced_course2 = data['course_service'].create_course(advanced_course2_data)
        
        # Test prerequisite chain
        prerequisites = data['course_service'].get_prerequisites(advanced_course2.id)
        assert len(prerequisites) == 2  # CS101 -> CS201 -> CS301
        
        # Test course level progression
        tenth_courses = data['course_service'].get_courses_by_level(GradeLevel.TENTH)
        eleventh_courses = data['course_service'].get_courses_by_level(GradeLevel.ELEVENTH)
        twelfth_courses = data['course_service'].get_courses_by_level(GradeLevel.TWELFTH)
        
        assert len(tenth_courses) >= 1
        assert len(eleventh_courses) >= 1
        assert len(twelfth_courses) >= 1
    
    def test_student_academic_progression(self, setup_test_data):
        """Test student academic progression through grade levels."""
        data = setup_test_data
        
        # Create students for different grade levels
        ninth_student_data = {
            "email": "ninth@example.com",
            "password": "Password123",
            "name": "Ninth Grade Student",
            "student_id": "S003",
            "enrollment_date": date(2020, 9, 1),
            "grade_level": GradeLevel.NINTH,
            "department_id": data['dept1'].id,
            "gpa": 3.5
        }
        
        twelfth_student_data = {
            "email": "twelfth@example.com",
            "password": "Password123",
            "name": "Twelfth Grade Student",
            "student_id": "S004",
            "enrollment_date": date(2020, 9, 1),
            "grade_level": GradeLevel.TWELFTH,
            "department_id": data['dept1'].id,
            "gpa": 3.9
        }
        
        ninth_student = data['student_service'].create_student(ninth_student_data)
        twelfth_student = data['student_service'].create_student(twelfth_student_data)
        
        # Get students by grade level
        ninth_graders = data['student_service'].get_students_by_grade_level(GradeLevel.NINTH)
        twelfth_graders = data['student_service'].get_students_by_grade_level(GradeLevel.TWELFTH)
        
        assert len(ninth_graders) >= 1
        assert len(twelfth_graders) >= 1
        
        # Verify student statistics include all grade levels
        stats = data['student_service'].get_student_statistics()
        assert stats.by_grade_level[GradeLevel.NINTH] >= 1
        assert stats.by_grade_level[GradeLevel.TWELFTH] >= 1
    
    def test_teacher_course_assignment(self, setup_test_data):
        """Test teacher course assignment and workload management."""
        data = setup_test_data
        
        # Create additional courses for the teacher
        course3_data = {
            "name": "Database Systems",
            "code": "CS201",
            "description": "Introduction to database design",
            "credits": 3,
            "department_id": data['dept1'].id,
            "level": GradeLevel.ELEVENTH,
            "prerequisites": []
        }
        
        course4_data = {
            "name": "Software Engineering",
            "code": "CS301",
            "description": "Software development methodologies",
            "credits": 4,
            "department_id": data['dept1'].id,
            "level": GradeLevel.TWELFTH,
            "prerequisites": []
        }
        
        course3 = data['course_service'].create_course(course3_data)
        course4 = data['course_service'].create_course(course4_data)
        
        # Assign teacher to additional courses by creating classes
        class3_data = {
            "name": "CS201 - Section A",
            "course_id": course3.id,
            "teacher_id": data['teacher1'].id,
            "academic_year": "2020-2021",
            "semester": "Fall",
            "capacity": 25,
            "schedule": "Tue/Thu 14:00-15:30"
        }
        
        class4_data = {
            "name": "CS301 - Section A", 
            "course_id": course4.id,
            "teacher_id": data['teacher1'].id,
            "academic_year": "2020-2021",
            "semester": "Fall",
            "capacity": 20,
            "schedule": "Mon/Wed 14:00-15:30"
        }
        
        class3 = data['class_service'].create_class(class3_data)
        class4 = data['class_service'].create_class(class4_data)
        
        # Get teacher's assigned courses
        teacher_courses = data['course_service'].get_courses_by_teacher(data['teacher1'].id)
        
        # Verify teacher is assigned to multiple courses
        assert len(teacher_courses) >= 3  # Original + 2 new courses
        
        # Get teacher's classes
        teacher_classes = data['class_service'].get_classes_by_teacher(data['teacher1'].id)
        
        # Verify teacher has multiple classes
        assert len(teacher_classes) >= 3
    
    def test_bulk_operations_performance(self, setup_test_data):
        """Test performance of bulk operations across services."""
        data = setup_test_data
        
        import time
        start_time = time.time()
        
        # Create multiple students in bulk
        bulk_students_data = []
        for i in range(20):  # Reduced for performance
            student_data = {
                "email": f"bulk{i}@example.com",
                "password": "Password123",
                "name": f"Bulk Student {i}",
                "student_id": f"BULK{i:03d}",
                "enrollment_date": date(2020, 9, 1),
                "grade_level": GradeLevel.TENTH if i % 2 == 0 else GradeLevel.ELEVENTH,
                "department_id": data['dept1'].id if i % 3 == 0 else data['dept2'].id,
                "gpa": 3.0 + (i % 10) * 0.1
            }
            bulk_students_data.append(student_data)
        
        # Bulk create students
        created_students = []
        for student_data in bulk_students_data:
            student = data['student_service'].create_student(student_data)
            created_students.append(student)
        
        creation_time = time.time() - start_time
        
        # Bulk enroll students in classes
        bulk_enrollments = []
        for i, student in enumerate(created_students[:10]):  # Enroll first 10 students
            enrollment_data = {
                "student_id": student.id,
                "class_id": data['class1'].id if i % 2 == 0 else data['class2'].id,
                "enrollment_date": date(2020, 9, 15),
                "status": "enrolled"
            }
            enrollment = data['mark_service'].create_enrollment(enrollment_data)
            bulk_enrollments.append(enrollment)
        
        enrollment_time = time.time() - start_time - creation_time
        
        # Bulk add marks
        bulk_marks = []
        for i, enrollment in enumerate(bulk_enrollments[:8]):  # Add marks for first 8
            mark_data = {
                "student_id": enrollment.student_id,
                "class_id": enrollment.class_id,
                "assessment_type": "assignment",
                "title": f"Assignment {i+1}",
                "max_score": 100,
                "score": 80 + (i % 20),
                "weight": 0.1
            }
            mark = data['mark_service'].create_mark(mark_data)
            bulk_marks.append(mark)
        
        marking_time = time.time() - start_time - creation_time - enrollment_time
        
        total_time = time.time() - start_time
        
        # Performance assertions
        assert creation_time < 5   # Should complete in under 5 seconds
        assert enrollment_time < 2  # Should complete in under 2 seconds
        assert marking_time < 1     # Should complete in under 1 second
        assert total_time < 8       # Total should be under 8 seconds
        
        # Verify bulk operations completed successfully
        assert len(created_students) == 20
        assert len(bulk_enrollments) == 10
        assert len(bulk_marks) == 8
        
        # Verify data integrity
        final_stats = data['student_service'].get_student_statistics()
        assert final_stats.total_students >= 22  # Original + 20 bulk students