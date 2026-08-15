"""
Service Interaction Integration Tests

This module tests interactions between different services to ensure proper
data flow, error handling, and system integration.

Author: Edu-Flow Team
"""

import pytest
import asyncio
from datetime import datetime, date, time
from uuid import uuid4
from unittest.mock import Mock, AsyncMock, patch

from src.core.exceptions import NotFoundError, ValidationError, DatabaseError, ConflictError
from src.infrastructure.services.service_container_fixed import ServiceContainer
from src.infrastructure.services.student_service import StudentService
from src.infrastructure.services.teacher_service import TeacherService
from src.infrastructure.services.course_service import CourseService
from src.infrastructure.services.class_service import ClassService
from src.infrastructure.services.mark_service import MarkService
from tests.mock_database_manager import MockDatabaseManager


class TestServiceInteractions:
    """Integration tests for service-to-service interactions."""
    
    @pytest.fixture(scope="class")
    async def system_services(self):
        """Create and initialize all services."""
        container = ServiceContainer()
        await container.initialize()
        yield container
        await container.dispose()
    
    @pytest.mark.asyncio
    async def test_student_teacher_class_interaction(self, system_services):
        """Test the interaction between student, teacher, and class services."""
        student_service = system_services.get('student_service')
        teacher_service = system_services.get('teacher_service')
        class_service = system_services.get('class_service')
        
        # 1. Create teacher
        teacher_data = {
            'name': 'Prof. Smith',
            'email': 'smith@university.edu',
            'teacher_id': 'TCH001',
            'specialization': 'Computer Science',
            'department_id': 'DEPT001'
        }
        teacher = await teacher_service.create(teacher_data)
        teacher_id = teacher['id']
        
        # 2. Create student
        student_data = {
            'name': 'Alice Johnson',
            'email': 'alice.j@university.edu',
            'student_id': 'STU001',
            'department_id': 'DEPT001'
        }
        student = await student_service.create(student_data)
        student_id = student['id']
        
        # 3. Create class
        class_data = {
            'name': 'CS101-A',
            'subject_id': 'SUB001',
            'teacher_id': teacher_id,
            'capacity': 30,
            'academic_year': '2023-2024',
            'semester': 'Fall'
        }
        class_obj = await class_service.create(class_data)
        class_id = class_obj['id']
        
        # 4. Enroll student in class
        updated_class = await class_service.enroll_student(class_id, student_id)
        assert student_id in updated_class['enrolled_students']
        
        # 5. Verify student class enrollment
        student_classes = await student_service.get_student_classes(student_id)
        assert any(c['id'] == class_id for c in student_classes)
        
        # 6. Verify teacher class assignment
        teacher_classes = await teacher_service.get_teacher_classes(teacher_id)
        assert any(c['id'] == class_id for c in teacher_classes)
        
        # 7. Clean up
        await class_service.unenroll_student(class_id, student_id)
        await class_service.delete(class_id)
        await student_service.delete(student_id)
        await teacher_service.delete(teacher_id)
        
        print("✓ Student-Teacher-Class interaction test passed")
    
    @pytest.mark.asyncio
    async def test_course_department_student_flow(self, system_services):
        """Test the flow from course creation to student enrollment."""
        course_service = system_services.get('course_service')
        department_service = system_services.get('department_service')
        student_service = system_services.get('student_service')
        
        # 1. Create department
        dept_data = {
            'name': 'Computer Science',
            'code': 'CS',
            'description': 'Department of Computer Science'
        }
        department = await department_service.create(dept_data)
        dept_id = department['id']
        
        # 2. Create course
        course_data = {
            'name': 'Data Structures',
            'code': 'CS201',
            'credits': 3,
            'department_id': dept_id,
            'level': 'undergraduate'
        }
        course = await course_service.create(course_data)
        course_id = course['id']
        
        # 3. Create student
        student_data = {
            'name': 'Bob Wilson',
            'email': 'bob.w@university.edu',
            'student_id': 'STU002',
            'department_id': dept_id
        }
        student = await student_service.create(student_data)
        student_id = student['id']
        
        # 4. Verify student can access course
        courses = await student_service.get_available_courses(student_id)
        assert any(c['id'] == course_id for c in courses)
        
        # 5. Verify course shows student in department
        dept_courses = await department_service.get_department_courses(dept_id)
        assert any(c['id'] == course_id for c in dept_courses)
        
        # 6. Clean up
        await student_service.delete(student_id)
        await course_service.delete(course_id)
        await department_service.delete(dept_id)
        
        print("✓ Course-Department-Student flow test passed")
    
    @pytest.mark.asyncio
    async def test_mark_grade_calculation_flow(self, system_services):
        """Test the flow from mark creation to grade calculation."""
        mark_service = system_services.get('mark_service')
        grade_service = system_services.get('grade_service')
        student_service = system_services.get('student_service')
        course_service = system_services.get('course_service')
        
        # 1. Create student
        student_data = {
            'name': 'Carol Davis',
            'email': 'carol.d@university.edu',
            'student_id': 'STU003',
            'department_id': 'DEPT001'
        }
        student = await student_service.create(student_data)
        student_id = student['id']
        
        # 2. Create course
        course_data = {
            'name': 'Algorithms',
            'code': 'CS301',
            'credits': 4,
            'department_id': 'DEPT001'
        }
        course = await course_service.create(course_data)
        course_id = course['id']
        
        # 3. Create marks
        marks_data = [
            {
                'student_id': student_id,
                'course_id': course_id,
                'exam_name': 'Midterm',
                'marks_obtained': 85,
                'total_marks': 100,
                'percentage': 85.0
            },
            {
                'student_id': student_id,
                'course_id': course_id,
                'exam_name': 'Final',
                'marks_obtained': 90,
                'total_marks': 100,
                'percentage': 90.0
            }
        ]
        
        mark_ids = []
        for mark_data in marks_data:
            mark = await mark_service.create(mark_data)
            mark_ids.append(mark['id'])
        
        # 4. Calculate grades
        grades = await grade_service.get_student_grades(student_id)
        assert len(grades) >= 2
        
        # 5. Verify statistics
        stats = await grade_service.get_grade_statistics()
        assert stats['total_students'] >= 1
        assert stats['total_courses'] >= 1
        
        # 6. Clean up
        for mark_id in mark_ids:
            await mark_service.delete(mark_id)
        await student_service.delete(student_id)
        await course_service.delete(course_id)
        
        print("✓ Mark-Grade calculation flow test passed")
    
    @pytest.mark.asyncio
    async def test_timetable_room_conflict_detection(self, system_services):
        """Test timetable conflict detection between rooms and classes."""
        timetable_service = system_services.get('timetable_entry_service')
        room_service = system_services.get('room_service')
        class_service = system_services.get('class_service')
        
        # 1. Create room
        room_data = {
            'name': 'Lecture Hall 101',
            'building': 'Main Building',
            'capacity': 50
        }
        room = await room_service.create(room_data)
        room_id = room['id']
        
        # 2. Create class
        class_data = {
            'name': 'CS101-A',
            'subject_id': 'SUB001',
            'teacher_id': 'TCH001',
            'capacity': 30,
            'academic_year': '2023-2024'
        }
        class_obj = await class_service.create(class_data)
        class_id = class_obj['id']
        
        # 3. Create first timetable entry
        timetable_data_1 = {
            'class_id': class_id,
            'room_id': room_id,
            'day_of_week': 'Monday',
            'start_time': time(9, 0),
            'end_time': time(10, 30),
            'academic_year': '2023-2024'
        }
        entry1 = await timetable_service.create(timetable_data_1)
        entry1_id = entry1['id']
        
        # 4. Create second timetable entry (should conflict)
        timetable_data_2 = {
            'class_id': class_id,
            'room_id': room_id,
            'day_of_week': 'Monday',
            'start_time': time(9, 0),
            'end_time': time(10, 30),
            'academic_year': '2023-2024'
        }
        
        # This should raise a conflict error (implementation would need conflict detection)
        try:
            entry2 = await timetable_service.create(timetable_data_2)
            assert False, "Should have detected conflict"
        except (ConflictError, ValidationError):
            pass  # Expected to fail due to conflict
        
        # 5. Clean up
        await timetable_service.delete(entry1_id)
        await class_service.delete(class_id)
        await room_service.delete(room_id)
        
        print("✓ Timetable conflict detection test passed")
    
    @pytest.mark.asyncio
    async def test_cross_service_error_handling(self, system_services):
        """Test error handling across multiple services."""
        student_service = system_services.get('student_service')
        course_service = system_services.get('course_service')
        
        # 1. Create valid student
        student_data = {
            'name': 'Test Student',
            'email': 'test@university.edu',
            'student_id': 'STU999',
            'department_id': 'DEPT001'
        }
        student = await student_service.create(student_data)
        student_id = student['id']
        
        # 2. Test invalid course enrollment
        invalid_course_id = 'INVALID_COURSE_ID'
        
        with pytest.raises(NotFoundError):
            await student_service.enroll_course(student_id, invalid_course_id)
        
        # 3. Test student deletion with dependencies
        # Create course that references student
        course_data = {
            'name': 'Test Course',
            'code': 'TEST999',
            'credits': 3,
            'department_id': 'DEPT001'
        }
        course = await course_service.create(course_data)
        course_id = course['id']
        
        # Try to delete student that has courses (should handle gracefully)
        await student_service.delete(student_id)
        
        # 4. Verify course is still there but student is gone
        try:
            courses = await student_service.get_student_courses(student_id)
            assert len(courses) == 0  # No courses should be associated
        except NotFoundError:
            pass  # Student not found is expected
        
        # 5. Clean up course
        await course_service.delete(course_id)
        
        print("✓ Cross-service error handling test passed")
    
    @pytest.mark.asyncio
    async def test_concurrent_service_operations(self, system_services):
        """Test concurrent operations across multiple services."""
        student_service = system_services.get('student_service')
        course_service = system_services.get('course_service')
        
        # Create multiple students concurrently
        student_tasks = []
        student_ids = []
        
        for i in range(5):
            student_data = {
                'name': f'Concurrent Student {i}',
                'email': f'concurrent{i}@university.edu',
                'student_id': f'STU{i:03d}',
                'department_id': 'DEPT001'
            }
            task = student_service.create(student_data)
            student_tasks.append(task)
        
        # Wait for all students to be created
        students = await asyncio.gather(*student_tasks)
        student_ids = [student['id'] for student in students]
        
        # Create multiple courses concurrently
        course_tasks = []
        course_ids = []
        
        for i in range(3):
            course_data = {
                'name': f'Concurrent Course {i}',
                'code': f'CON{i:03d}',
                'credits': 3,
                'department_id': 'DEPT001'
            }
            task = course_service.create(course_data)
            course_tasks.append(task)
        
        # Wait for all courses to be created
        courses = await asyncio.gather(*course_tasks)
        course_ids = [course['id'] for course in courses]
        
        # Verify all entities were created
        assert len(student_ids) == 5
        assert len(course_ids) == 3
        
        # Clean up
        cleanup_tasks = []
        for student_id in student_ids:
            cleanup_tasks.append(student_service.delete(student_id))
        
        for course_id in course_ids:
            cleanup_tasks.append(course_service.delete(course_id))
        
        await asyncio.gather(*cleanup_tasks)
        
        print("✓ Concurrent service operations test passed")
    
    @pytest.mark.asyncio
    async def test_service_data_consistency(self, system_services):
        """Test data consistency across services."""
        student_service = system_services.get('student_service')
        department_service = system_services.get('department_service')
        
        # 1. Create department
        dept_data = {
            'name': 'Consistency Test Department',
            'code': 'CTD',
            'description': 'Department for consistency testing'
        }
        department = await department_service.create(dept_data)
        dept_id = department['id']
        
        # 2. Create student in department
        student_data = {
            'name': 'Consistency Student',
            'email': 'consistency@university.edu',
            'student_id': 'STU999',
            'department_id': dept_id
        }
        student = await student_service.create(student_data)
        student_id = student['id']
        
        # 3. Verify department has student
        dept_students = await department_service.get_department_students(dept_id)
        assert any(s['id'] == student_id for s in dept_students)
        
        # 4. Verify student has correct department
        student_details = await student_service.get_student_by_id(student_id)
        assert student_details['department_id'] == dept_id
        
        # 5. Test cascading delete
        await department_service.delete(dept_id)
        
        # Student should still exist but department reference should be handled gracefully
        try:
            remaining_student = await student_service.get_student_by_id(student_id)
            assert remaining_student['department_id'] is None or remaining_student['department_id'] == ''
        except NotFoundError:
            pass  # Student might be deleted in cascade
        
        print("✓ Service data consistency test passed")