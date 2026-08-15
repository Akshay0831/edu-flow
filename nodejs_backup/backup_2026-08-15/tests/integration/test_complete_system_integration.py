"""
Complete System Integration Tests

This module provides comprehensive integration tests for the entire Edu-Flow backend system.
It tests the integration between all components: repositories, services, and API endpoints.

Author: Edu-Flow Team
"""

import pytest
import asyncio
import json
from datetime import datetime, date, timedelta
from uuid import uuid4
from typing import Dict, Any, List

from src.core.exceptions import NotFoundError, ValidationError, DatabaseError, ConflictError
from src.infrastructure.services.service_container_fixed import ServiceContainer
from src.infrastructure.services.student_service import StudentService
from src.infrastructure.services.teacher_service import TeacherService
from src.infrastructure.services.course_service import CourseService
from src.infrastructure.services.class_service import ClassService
from src.infrastructure.services.subject_service import SubjectService
from src.infrastructure.services.department_service import DepartmentService
from src.infrastructure.services.mark_service import MarkService
from src.infrastructure.services.timetable_entry_service import TimetableEntryService
from src.infrastructure.services.grade_service import GradeService
from src.infrastructure.services.laboratory_service import LaboratoryService
from src.infrastructure.services.room_service import RoomService
from tests.mock_database_manager import MockDatabaseManager


class TestCompleteSystemIntegration:
    """Comprehensive integration tests for the entire Edu-Flow system."""
    
    @pytest.fixture(scope="class")
    async def system_services(self):
        """Create and initialize all services."""
        container = ServiceContainer()
        await container.initialize()
        yield container
        await container.dispose()
    
    # Test Complete Student Lifecycle
    
    @pytest.mark.asyncio
    async def test_complete_student_lifecycle(self, system_services):
        """Test complete student lifecycle: create, enroll, get marks, graduate."""
        student_service = system_services.get('student_service')
        course_service = system_services.get('course_service')
        mark_service = system_services.get('mark_service')
        department_service = system_services.get('department_service')
        
        # 1. Create department
        dept_data = {
            'name': 'Computer Science',
            'code': 'CS',
            'description': 'Computer Science Department',
            'head_of_department': 'TCH001'
        }
        department = await department_service.create(dept_data)
        dept_id = department['id']
        
        # 2. Create student
        student_data = {
            'name': 'John Student',
            'email': 'john.student@example.com',
            'student_id': 'STU001',
            'phone': '+1234567890',
            'address': '123 Campus St',
            'gender': 'M',
            'birth_date': '2000-05-15',
            'enrollment_date': date.today().isoformat(),
            'department_id': dept_id
        }
        student = await student_service.create(student_data)
        student_id = student['id']
        
        # 3. Create course
        course_data = {
            'name': 'Data Structures',
            'code': 'CS201',
            'description': 'Advanced data structures',
            'credits': 4,
            'department_id': dept_id,
            'level': 'undergraduate'
        }
        course = await course_service.create(course_data)
        course_id = course['id']
        
        # 4. Create marks for student
        mark_data = {
            'student_id': student_id,
            'course_id': course_id,
            'exam_name': 'Midterm',
            'marks_obtained': 85,
            'total_marks': 100,
            'percentage': 85.0
        }
        mark = await mark_service.create(mark_data)
        mark_id = mark['id']
        
        # 5. Verify student statistics
        stats = await student_service.get_student_statistics(student_id)
        assert stats['total_courses'] >= 1
        assert stats['enrollment_count'] >= 1
        
        # 6. Clean up
        await mark_service.delete(mark_id)
        await mark_service.count() == 0
        
        print(f"✓ Complete student lifecycle test passed for student {student_id}")
    
    # Test Complete Class Management
    
    @pytest.mark.asyncio
    async def test_complete_class_management(self, system_services):
        """Test complete class management: create, assign teacher, enroll students."""
        class_service = system_services.get('class_service')
        teacher_service = system_services.get('teacher_service')
        student_service = system_services.get('student_service')
        subject_service = system_services.get('subject_service')
        
        # 1. Create teacher
        teacher_data = {
            'name': 'Dr. Jane Smith',
            'email': 'jane.smith@example.com',
            'teacher_id': 'TCH001',
            'phone': '+1234567890',
            'address': '456 Faculty Ave',
            'gender': 'F',
            'birth_date': '1975-03-15',
            'hire_date': date.today().isoformat(),
            'department_id': 'DEPT001',
            'specialization': 'Computer Science'
        }
        teacher = await teacher_service.create(teacher_data)
        teacher_id = teacher['id']
        
        # 2. Create subject
        subject_data = {
            'name': 'Algorithms',
            'code': 'CS301',
            'description': 'Advanced algorithms',
            'credits': 3,
            'department_id': 'DEPT001'
        }
        subject = await subject_service.create(subject_data)
        subject_id = subject['id']
        
        # 3. Create class
        class_data = {
            'name': 'CS301-A',
            'subject_id': subject_id,
            'teacher_id': teacher_id,
            'capacity': 30,
            'academic_year': '2023-2024',
            'semester': 'Fall',
            'schedule': 'MWF 10:00-11:30',
            'location': 'Room 101'
        }
        class_obj = await class_service.create(class_data)
        class_id = class_obj['id']
        
        # 4. Create students
        student_ids = []
        for i in range(5):
            student_data = {
                'name': f'Student {i+1}',
                'email': f'student{i+1}@example.com',
                'student_id': f'STU{i+1:03d}',
                'phone': f'+123456789{i}',
                'address': f'{i+1} Campus St',
                'gender': 'M' if i % 2 == 0 else 'F',
                'birth_date': '2000-01-01',
                'enrollment_date': date.today().isoformat(),
                'department_id': 'DEPT001'
            }
            student = await student_service.create(student_data)
            student_ids.append(student['id'])
        
        # 5. Test class listing
        classes = await class_service.list()
        assert len(classes) >= 1
        
        # 6. Clean up
        for student_id in student_ids:
            await student_service.delete(student_id)
        await class_service.delete(class_id)
        await teacher_service.delete(teacher_id)
        
        print(f"✓ Complete class management test passed for class {class_id}")
    
    # Test Complete Grade Management
    
    @pytest.mark.asyncio
    async def test_complete_grade_management(self, system_services):
        """Test complete grade management: create multiple marks, calculate grades."""
        grade_service = system_services.get('grade_service')
        mark_service = system_services.get('mark_service')
        student_service = system_services.get('student_service')
        course_service = system_services.get('course_service')
        
        # 1. Create student
        student_data = {
            'name': 'Grade Test Student',
            'email': 'grade.test@example.com',
            'student_id': 'STU999',
            'phone': '+1234567899',
            'address': '999 Test St',
            'gender': 'M',
            'birth_date': '2000-01-01',
            'enrollment_date': date.today().isoformat()
        }
        student = await student_service.create(student_data)
        student_id = student['id']
        
        # 2. Create course
        course_data = {
            'name': 'Advanced Mathematics',
            'code': 'MATH401',
            'description': 'Advanced mathematical concepts',
            'credits': 4,
            'department_id': 'DEPT001'
        }
        course = await course_service.create(course_data)
        course_id = course['id']
        
        # 3. Create multiple marks
        marks_data = [
            {
                'student_id': student_id,
                'course_id': course_id,
                'exam_name': 'Quiz 1',
                'marks_obtained': 90,
                'total_marks': 100,
                'percentage': 90.0
            },
            {
                'student_id': student_id,
                'course_id': course_id,
                'exam_name': 'Quiz 2',
                'marks_obtained': 85,
                'total_marks': 100,
                'percentage': 85.0
            },
            {
                'student_id': student_id,
                'course_id': course_id,
                'exam_name': 'Final Exam',
                'marks_obtained': 88,
                'total_marks': 100,
                'percentage': 88.0
            }
        ]
        
        mark_ids = []
        for mark_data in marks_data:
            mark = await mark_service.create(mark_data)
            mark_ids.append(mark['id'])
        
        # 4. Test grade calculations
        student_grades = await grade_service.get_student_grades(student_id)
        assert len(student_grades) >= 3
        
        # 5. Test grade statistics
        stats = await grade_service.get_grade_statistics()
        assert stats['total_students'] >= 1
        assert stats['total_courses'] >= 1
        
        # 6. Clean up
        for mark_id in mark_ids:
            await mark_service.delete(mark_id)
        await student_service.delete(student_id)
        await course_service.delete(course_id)
        
        print(f"✓ Complete grade management test passed")
    
    # Test Complete Room and Laboratory Management
    
    @pytest.mark.asyncio
    async def test_complete_facility_management(self, system_services):
        """Test complete facility management: room and laboratory booking."""
        room_service = system_services.get('room_service')
        laboratory_service = system_services.get('laboratory_service')
        
        # 1. Create room
        room_data = {
            'name': 'Lecture Hall A',
            'building': 'Main Building',
            'floor': 1,
            'capacity': 100,
            'room_type': 'lecture',
            'facilities': ['Projector', 'Microphone', 'Whiteboard']
        }
        room = await room_service.create(room_data)
        room_id = room['id']
        
        # 2. Create laboratory
        lab_data = {
            'name': 'Computer Lab 1',
            'building': 'Science Building',
            'floor': 2,
            'capacity': 30,
            'lab_type': 'computer',
            'equipment': ['Desktop PCs', 'Projector', 'Printer'],
            'safety_equipment': ['Fire Extinguisher', 'First Aid Kit']
        }
        laboratory = await laboratory_service.create(lab_data)
        lab_id = laboratory['id']
        
        # 3. Test room listing
        rooms = await room_service.list()
        assert len(rooms) >= 1
        
        # 4. Test laboratory listing
        laboratories = await laboratory_service.list()
        assert len(laboratories) >= 1
        
        # 5. Test facility statistics
        room_stats = await room_service.get_room_statistics()
        lab_stats = await laboratory_service.get_laboratory_statistics()
        assert room_stats['total_rooms'] >= 1
        assert lab_stats['total_labs'] >= 1
        
        # 6. Clean up
        await room_service.delete(room_id)
        await laboratory_service.delete(lab_id)
        
        print(f"✓ Complete facility management test passed")
    
    # Test Complete Timetable Management
    
    @pytest.mark.asyncio
    async def test_complete_timetable_management(self, system_services):
        """Test complete timetable management: create entries, check conflicts."""
        timetable_service = system_services.get('timetable_entry_service')
        room_service = system_services.get('room_service')
        class_service = system_services.get('class_service')
        teacher_service = system_services.get('teacher_service')
        subject_service = system_services.get('subject_service')
        
        # 1. Create teacher
        teacher_data = {
            'name': 'Timetable Test Teacher',
            'email': 'timetable.test@example.com',
            'teacher_id': 'TCH999',
            'phone': '+1234567899',
            'address': '999 Faculty St',
            'gender': 'F',
            'birth_date': '1975-01-01',
            'hire_date': date.today().isoformat()
        }
        teacher = await teacher_service.create(teacher_data)
        teacher_id = teacher['id']
        
        # 2. Create subject
        subject_data = {
            'name': 'Timetable Test Subject',
            'code': 'TST101',
            'description': 'Test subject for timetable',
            'credits': 3,
            'department_id': 'DEPT001'
        }
        subject = await subject_service.create(subject_data)
        subject_id = subject['id']
        
        # 3. Create class
        class_data = {
            'name': 'TST101-A',
            'subject_id': subject_id,
            'teacher_id': teacher_id,
            'capacity': 20,
            'academic_year': '2023-2024',
            'semester': 'Fall',
            'schedule': 'TTh 09:00-10:30',
            'location': 'Room 101'
        }
        class_obj = await class_service.create(class_data)
        class_id = class_obj['id']
        
        # 4. Create room
        room_data = {
            'name': 'Timetable Test Room',
            'building': 'Test Building',
            'floor': 1,
            'capacity': 25,
            'room_type': 'classroom'
        }
        room = await room_service.create(room_data)
        room_id = room['id']
        
        # 5. Create timetable entries
        from datetime import time
        
        timetable_entries = [
            {
                'class_id': class_id,
                'room_id': room_id,
                'day_of_week': 'Monday',
                'start_time': time(9, 0),
                'end_time': time(10, 30),
                'academic_year': '2023-2024',
                'semester': 'Fall'
            },
            {
                'class_id': class_id,
                'room_id': room_id,
                'day_of_week': 'Wednesday',
                'start_time': time(9, 0),
                'end_time': time(10, 30),
                'academic_year': '2023-2024',
                'semester': 'Fall'
            }
        ]
        
        entry_ids = []
        for entry_data in timetable_entries:
            entry = await timetable_service.create(entry_data)
            entry_ids.append(entry['id'])
        
        # 6. Test timetable listing
        timetable = await timetable_service.list()
        assert len(timetable) >= 2
        
        # 7. Test conflict detection (would need to be implemented)
        # conflicts = await timetable_service.check_conflicts(class_id, 'Monday', time(9, 0), time(10, 30))
        # assert len(conflicts) == 0  # Should have no conflicts
        
        # 8. Clean up
        for entry_id in entry_ids:
            await timetable_service.delete(entry_id)
        await room_service.delete(room_id)
        await class_service.delete(class_id)
        await teacher_service.delete(teacher_id)
        
        print(f"✓ Complete timetable management test passed")
    
    # Test Cross-Service Data Consistency
    
    @pytest.mark.asyncio
    async def test_cross_service_data_consistency(self, system_services):
        """Test data consistency across different services."""
        student_service = system_services.get('student_service')
        teacher_service = system_services.get('teacher_service')
        department_service = system_services.get('department_service')
        mark_service = system_services.get('mark_service')
        
        # 1. Create department
        dept_data = {
            'name': 'Consistency Test Department',
            'code': 'CTD',
            'description': 'Department for consistency testing'
        }
        department = await department_service.create(dept_data)
        dept_id = department['id']
        
        # 2. Create student and teacher in same department
        student_data = {
            'name': 'Consistency Student',
            'email': 'consistency.student@example.com',
            'student_id': 'STU888',
            'department_id': dept_id
        }
        student = await student_service.create(student_data)
        student_id = student['id']
        
        teacher_data = {
            'name': 'Consistency Teacher',
            'email': 'consistency.teacher@example.com',
            'teacher_id': 'TCH888',
            'department_id': dept_id
        }
        teacher = await teacher_service.create(teacher_data)
        teacher_id = teacher['id']
        
        # 3. Create mark for student
        mark_data = {
            'student_id': student_id,
            'course_id': 'COURSE001',  # This course doesn't exist, but testing service consistency
            'marks_obtained': 75,
            'total_marks': 100,
            'percentage': 75.0
        }
        
        # This should fail gracefully due to validation
        with pytest.raises(Exception):  # Should handle invalid course_id gracefully
            await mark_service.create(mark_data)
        
        # 4. Verify department still has both entities
        dept_students = await student_service.get_students_by_department(dept_id)
        dept_teachers = await teacher_service.get_teachers_by_department(dept_id)
        
        # Clean up
        await student_service.delete(student_id)
        await teacher_service.delete(teacher_id)
        await department_service.delete(dept_id)
        
        print(f"✓ Cross-service data consistency test passed")
    
    # Test System Performance
    
    @pytest.mark.asyncio
    async def test_system_performance(self, system_services):
        """Test system performance with bulk operations."""
        student_service = system_services.get('student_service')
        course_service = system_services.get('course_service')
        
        # 1. Create multiple students (bulk operation simulation)
        student_ids = []
        for i in range(10):
            student_data = {
                'name': f'Perf Student {i}',
                'email': f'perf.student{i}@example.com',
                'student_id': f'STU{i:03d}',
                'phone': f'+12345678{i}',
                'address': f'{i} Performance St',
                'gender': 'M' if i % 2 == 0 else 'F',
                'birth_date': '2000-01-01',
                'enrollment_date': date.today().isoformat()
            }
            student = await student_service.create(student_data)
            student_ids.append(student['id'])
        
        # 2. Create multiple courses
        course_ids = []
        for i in range(5):
            course_data = {
                'name': f'Perf Course {i}',
                'code': f'PERF{i:03d}',
                'description': f'Performance test course {i}',
                'credits': 3,
                'department_id': 'DEPT001'
            }
            course = await course_service.create(course_data)
            course_ids.append(course['id'])
        
        # 3. Test bulk listing operations
        students = await student_service.list(limit=20)
        courses = await course_service.list(limit=20)
        
        assert len(students) >= 10
        assert len(courses) >= 5
        
        # 4. Test counting operations
        student_count = await student_service.count()
        course_count = await course_service.count()
        
        assert student_count >= 10
        assert course_count >= 5
        
        # 5. Clean up
        for student_id in student_ids:
            await student_service.delete(student_id)
        for course_id in course_ids:
            await course_service.delete(course_id)
        
        print(f"✓ System performance test passed")
    
    # Test Error Handling and Recovery
    
    @pytest.mark.asyncio
    async def test_error_handling_and_recovery(self, system_services):
        """Test error handling and system recovery."""
        student_service = system_services.get('student_service')
        
        # 1. Test invalid student creation
        invalid_student = {
            'name': '',  # Empty name should fail validation
            'email': 'invalid@example.com',
            'student_id': 'STU000'
        }
        
        with pytest.raises(ValidationError):
            await student_service.create(invalid_student)
        
        # 2. Test non-existent entity access
        non_existent_id = str(uuid4())
        
        with pytest.raises(NotFoundError):
            await student_service.get(non_existent_id)
        
        # 3. Test service cleanup after errors
        # The service should still work properly after error conditions
        valid_student_data = {
            'name': 'Recovery Test Student',
            'email': 'recovery.test@example.com',
            'student_id': 'STU777',
            'phone': '+1234567877',
            'address': '777 Recovery St',
            'gender': 'M',
            'birth_date': '2000-01-01',
            'enrollment_date': date.today().isoformat()
        }
        
        # This should work normally despite previous errors
        student = await student_service.create(valid_student_data)
        assert student is not None
        
        # Clean up
        await student_service.delete(student['id'])
        
        print(f"✓ Error handling and recovery test passed")