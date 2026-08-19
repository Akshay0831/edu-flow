"""
Service Integration Tests

This module provides comprehensive tests for all service classes and their integration.
It tests functionality, error handling, business logic, and data integrity.

Author: Edu-Flow Team
"""

import pytest
import asyncio
from datetime import datetime, date, time, timedelta
from uuid import uuid4

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
from src.models.student import StudentCreate, StudentResponse, StudentUpdate
from src.models.teacher import TeacherCreate, TeacherResponse
from src.models.course import CourseCreate, CourseResponse
from src.models.class_model import ClassCreate, ClassResponse
from src.models.subject_model import SubjectCreate
from src.models.department_model import DepartmentCreate
from src.models.mark_model import MarkCreate, MarkResponse, MarkStats
from src.models.timetable_entry import TimetableEntryCreate, TimetableEntryResponse
from src.models.grade import GradeCreate, GradeResponse
from src.models.laboratory import LabCreate as LaboratoryCreate, LabResponse as LaboratoryResponse
from src.models.room import RoomCreate, RoomResponse, RoomStats


class TestServiceIntegration:
    """Comprehensive integration tests for all service classes."""
    
    @pytest.fixture(scope="class")
    def service_container(self):
        """Create and initialize service container for testing."""
        container = ServiceContainer()
        return container
    
    @pytest.fixture(scope="class")
    async def initialized_services(self, service_container):
        """Initialize all services."""
        await service_container.initialize()
        yield service_container
        await service_container.dispose()
    
    # Student Service Tests
    
    @pytest.mark.asyncio
    async def test_student_service_crud(self, initialized_services):
        """Test student service CRUD operations."""
        student_service = initialized_services.get('student_service')
        
        # Create student
        student_data = {
            'name': 'Test Student',
            'email': 'test@example.com',
            'student_id': 'STU001',
            'phone': '+1234567890',
            'address': '123 Test St',
            'gender': 'M',
            'birth_date': '2000-01-01'
        }
        
        created_student = await student_service.create_student(student_data)
        assert created_student.name == 'Test Student'
        assert created_student.email == 'test@example.com'
        assert created_student.student_id == 'STU001'
        
        # Get student
        retrieved_student = await student_service.get_student(created_student.id)
        assert retrieved_student.id == created_student.id
        assert retrieved_student.name == 'Test Student'
        
        # Update student
        update_data = {'name': 'Updated Student Name'}
        updated_student = await student_service.update_student(created_student.id, update_data)
        assert updated_student.name == 'Updated Student Name'
        
        # Delete student
        result = await student_service.delete_student(created_student.id)
        assert result is True
        
        # Verify deletion
        with pytest.raises(NotFoundError):
            await student_service.get_student(created_student.id)
    
    @pytest.mark.asyncio
    async def test_student_service_validation(self, initialized_services):
        """Test student service validation."""
        student_service = initialized_services.get('student_service')
        
        # Test invalid student data
        invalid_student = {
            'name': '',  # Empty name
            'email': 'invalid-email',  # Invalid email
            'student_id': '',  # Empty student ID
        }
        
        with pytest.raises(ValidationError):
            await student_service.create_student(invalid_student)
    
    @pytest.mark.asyncio
    async def test_student_service_duplicate(self, initialized_services):
        """Test student service duplicate prevention."""
        student_service = initialized_services.get('student_service')
        
        # Create first student
        student_data = {
            'name': 'Duplicate Student',
            'email': 'duplicate@example.com',
            'student_id': 'STU002',
        }
        
        await student_service.create_student(student_data)
        
        # Try to create duplicate
        duplicate_data = {
            'name': 'Duplicate Student 2',
            'email': 'duplicate@example.com',  # Same email
            'student_id': 'STU003',
        }
        
        with pytest.raises(ConflictError):
            await student_service.create_student(duplicate_data)
    
    # Teacher Service Tests
    
    @pytest.mark.asyncio
    async def test_teacher_service_crud(self, initialized_services):
        """Test teacher service CRUD operations."""
        teacher_service = initialized_services.get('teacher_service')
        
        # Create teacher
        teacher_data = {
            'name': 'Test Teacher',
            'email': 'teacher@example.com',
            'teacher_id': 'TCH001',
            'department_id': 'DEPT001',
            'qualification': 'PhD',
            'experience_years': 10,
            'specialization': 'Computer Science'
        }
        
        created_teacher = await teacher_service.create_teacher(teacher_data)
        assert created_teacher.name == 'Test Teacher'
        assert created_teacher.email == 'teacher@example.com'
        assert created_teacher.teacher_id == 'TCH001'
        
        # Get teacher
        retrieved_teacher = await teacher_service.get_teacher(created_teacher.id)
        assert retrieved_teacher.id == created_teacher.id
        
        # Update teacher
        update_data = {'name': 'Updated Teacher Name'}
        updated_teacher = await teacher_service.update_teacher(created_teacher.id, update_data)
        assert updated_teacher.name == 'Updated Teacher Name'
        
        # Delete teacher
        result = await teacher_service.delete_teacher(created_teacher.id)
        assert result is True
    
    # Course Service Tests
    
    @pytest.mark.asyncio
    async def test_course_service_crud(self, initialized_services):
        """Test course service CRUD operations."""
        course_service = initialized_services.get('course_service')
        
        # Create course
        course_data = {
            'name': 'Test Course',
            'code': 'CS101',
            'description': 'Introduction to Computer Science',
            'credits': 3,
            'department_id': 'DEPT001',
            'level': 100,
            'academic_year': '2023-2024'
        }
        
        created_course = await course_service.create_course(course_data)
        assert created_course.name == 'Test Course'
        assert created_course.code == 'CS101'
        assert created_course.credits == 3
        
        # Get course
        retrieved_course = await course_service.get_course(created_course.id)
        assert retrieved_course.id == created_course.id
        
        # Update course
        update_data = {'credits': 4}
        updated_course = await course_service.update_course(created_course.id, update_data)
        assert updated_course.credits == 4
        
        # Delete course
        result = await course_service.delete_course(created_course.id)
        assert result is True
    
    # Class Service Tests
    
    @pytest.mark.asyncio
    async def test_class_service_crud(self, initialized_services):
        """Test class service CRUD operations."""
        class_service = initialized_services.get('class_service')
        
        # Create class
        class_data = {
            'name': 'Test Class',
            'class_code': 'CL101',
            'subject_id': 'SUB001',
            'teacher_id': 'TCH001',
            'capacity': 30,
            'academic_year': '2023-2024',
            'semester': 'Fall'
        }
        
        created_class = await class_service.create_class(class_data)
        assert created_class.name == 'Test Class'
        assert created_class.class_code == 'CL101'
        assert created_class.capacity == 30
        
        # Get class
        retrieved_class = await class_service.get_class(created_class.id)
        assert retrieved_class.id == created_class.id
        
        # Update class
        update_data = {'capacity': 35}
        updated_class = await class_service.update_class(created_class.id, update_data)
        assert updated_class.capacity == 35
        
        # Delete class
        result = await class_service.delete_class(created_class.id)
        assert result is True
    
    # Subject Service Tests
    
    @pytest.mark.asyncio
    async def test_subject_service_crud(self, initialized_services):
        """Test subject service CRUD operations."""
        subject_service = initialized_services.get('subject_service')
        
        # Create subject
        subject_data = {
            'name': 'Test Subject',
            'code': 'SUB001',
            'description': 'Test Subject Description',
            'department_id': 'DEPT001',
            'credits': 3,
            'level': 100
        }
        
        created_subject = await subject_service.create_subject(subject_data)
        assert created_subject.name == 'Test Subject'
        assert created_subject.code == 'SUB001'
        assert created_subject.credits == 3
        
        # Get subject
        retrieved_subject = await subject_service.get_subject(created_subject.id)
        assert retrieved_subject.id == created_subject.id
        
        # Update subject
        update_data = {'credits': 4}
        updated_subject = await subject_service.update_subject(created_subject.id, update_data)
        assert updated_subject.credits == 4
        
        # Delete subject
        result = await subject_service.delete_subject(created_subject.id)
        assert result is True
    
    # Department Service Tests
    
    @pytest.mark.asyncio
    async def test_department_service_crud(self, initialized_services):
        """Test department service CRUD operations."""
        department_service = initialized_services.get('department_service')
        
        # Create department
        department_data = {
            'name': 'Test Department',
            'code': 'DEPT001',
            'description': 'Test Department Description',
            'head_id': 'TCH001',
            'location': 'Building A'
        }
        
        created_department = await department_service.create_department(department_data)
        assert created_department.name == 'Test Department'
        assert created_department.code == 'DEPT001'
        assert created_department.location == 'Building A'
        
        # Get department
        retrieved_department = await department_service.get_department(created_department.id)
        assert retrieved_department.id == created_department.id
        
        # Update department
        update_data = {'location': 'Building B'}
        updated_department = await department_service.update_department(created_department.id, update_data)
        assert updated_department.location == 'Building B'
        
        # Delete department
        result = await department_service.delete_department(created_department.id)
        assert result is True
    
    # Mark Service Tests
    
    @pytest.mark.asyncio
    async def test_mark_service_crud(self, initialized_services):
        """Test mark service CRUD operations."""
        mark_service = initialized_services.get('mark_service')
        
        # Create mark
        mark_data = {
            'student_id': 'STU001',
            'course_id': 'CSE101',
            'exam_name': 'Midterm Exam',
            'score': 85.5,
            'max_score': 100,
            'weight': 0.3,
            'grading_scale_id': 'GS001'
        }
        
        created_mark = await mark_service.create_mark(mark_data)
        assert created_mark.score == 85.5
        assert created_mark.max_score == 100
        assert created_mark.weight == 0.3
        
        # Get mark
        retrieved_mark = await mark_service.get_mark(created_mark.id)
        assert retrieved_mark.id == created_mark.id
        
        # Update mark
        update_data = {'score': 90.0}
        updated_mark = await mark_service.update_mark(created_mark.id, update_data)
        assert updated_mark.score == 90.0
        
        # Delete mark
        result = await mark_service.delete_mark(created_mark.id)
        assert result is True
    
    @pytest.mark.asyncio
    async def test_mark_service_grade_calculation(self, initialized_services):
        """Test mark service grade calculation."""
        mark_service = initialized_services.get('mark_service')
        
        # Test grade calculation
        grade = await mark_service.calculate_grade(85.5, 100)
        assert grade['percentage'] == 85.5
        assert grade['grade'] in ['A', 'B', 'C', 'D', 'F']  # Depends on grading scale
        
        # Test GPA calculation
        gpa = await mark_service.calculate_gpa([{'percentage': 85.5, 'weight': 0.3}, {'percentage': 90.0, 'weight': 0.7}])
        assert isinstance(gpa, float)
        assert 0.0 <= gpa <= 4.0
    
    # Timetable Entry Service Tests
    
    @pytest.mark.asyncio
    async def test_timetable_entry_service_crud(self, initialized_services):
        """Test timetable entry service CRUD operations."""
        timetable_service = initialized_services.get('timetable_entry_service')
        
        # Create timetable entry
        entry_data = {
            'class_id': 'CL001',
            'subject_id': 'SUB001',
            'teacher_id': 'TCH001',
            'room_id': 'ROOM001',
            'day_of_week': 'Monday',
            'start_time': '09:00',
            'end_time': '10:00',
            'academic_year': '2023-2024',
            'semester': 'Fall'
        }
        
        created_entry = await timetable_service.create_timetable_entry(entry_data)
        assert created_entry.day_of_week == 'Monday'
        assert created_entry.start_time == '09:00'
        assert created_entry.end_time == '10:00'
        
        # Get entry
        retrieved_entry = await timetable_service.get_timetable_entry(created_entry.id)
        assert retrieved_entry.id == created_entry.id
        
        # Update entry
        update_data = {'start_time': '10:00'}
        updated_entry = await timetable_service.update_timetable_entry(created_entry.id, update_data)
        assert updated_entry.start_time == '10:00'
        
        # Delete entry
        result = await timetable_service.delete_timetable_entry(created_entry.id)
        assert result is True
    
    @pytest.mark.asyncio
    async def test_timetable_service_conflict_detection(self, initialized_services):
        """Test timetable service conflict detection."""
        timetable_service = initialized_services.get('timetable_entry_service')
        
        # Create first entry
        entry1_data = {
            'class_id': 'CL001',
            'subject_id': 'SUB001',
            'teacher_id': 'TCH001',
            'room_id': 'ROOM001',
            'day_of_week': 'Monday',
            'start_time': '09:00',
            'end_time': '10:00',
            'academic_year': '2023-2024',
            'semester': 'Fall'
        }
        
        await timetable_service.create_timetable_entry(entry1_data)
        
        # Try to create conflicting entry
        entry2_data = {
            'class_id': 'CL001',
            'subject_id': 'SUB001',
            'teacher_id': 'TCH001',
            'room_id': 'ROOM001',
            'day_of_week': 'Monday',
            'start_time': '09:30',  # Overlaps with first entry
            'end_time': '10:30',
            'academic_year': '2023-2024',
            'semester': 'Fall'
        }
        
        with pytest.raises(ConflictError):
            await timetable_service.create_timetable_entry(entry2_data)
    
    # Grade Service Tests
    
    @pytest.mark.asyncio
    async def test_grade_service_crud(self, initialized_services):
        """Test grade service CRUD operations."""
        grade_service = initialized_services.get('grade_service')
        
        # Create grade
        grade_data = {
            'student_id': 'STU001',
            'grading_scale_id': 'GS001',
            'grade': 'A',
            'percentage': 90.0,
            'weight': 0.3,
            'academic_year': '2023-2024',
            'semester': 'Fall'
        }
        
        created_grade = await grade_service.create_grade(grade_data)
        assert created_grade.grade == 'A'
        assert created_grade.percentage == 90.0
        assert created_grade.weight == 0.3
        
        # Get grade
        retrieved_grade = await grade_service.get_grade(created_grade.id)
        assert retrieved_grade.id == created_grade.id
        
        # Update grade
        update_data = {'grade': 'A+'}
        updated_grade = await grade_service.update_grade(created_grade.id, update_data)
        assert updated_grade.grade == 'A+'
        
        # Delete grade
        result = await grade_service.delete_grade(created_grade.id)
        assert result is True
    
    @pytest.mark.asyncio
    async def test_grade_service_grade_conversion(self, initialized_services):
        """Test grade service grade conversion."""
        grade_service = initialized_services.get('grade_service')
        
        # Test grade to percentage conversion
        percentage = await grade_service.grade_to_percentage('A', 'GS001')
        assert isinstance(percentage, float)
        assert 0.0 <= percentage <= 100.0
        
        # Test percentage to grade conversion
        grade = await grade_service.percentage_to_grade(90.0, 'GS001')
        assert grade in ['A', 'B', 'C', 'D', 'F']
    
    # Laboratory Service Tests
    
    @pytest.mark.asyncio
    async def test_laboratory_service_crud(self, initialized_services):
        """Test laboratory service CRUD operations."""
        lab_service = initialized_services.get('laboratory_service')
        
        # Create laboratory
        lab_data = {
            'name': 'Test Laboratory',
            'building_id': 'BLD001',
            'room_number': '101',
            'capacity': 20,
            'equipment_list': ['Computers', 'Projector'],
            'safety_features': ['Fire Extinguisher', 'First Aid Kit'],
            'lab_type': 'Computer Science'
        }
        
        created_lab = await lab_service.create_laboratory(lab_data)
        assert created_lab.name == 'Test Laboratory'
        assert created_lab.capacity == 20
        assert 'Computers' in created_lab.equipment_list
        
        # Get laboratory
        retrieved_lab = await lab_service.get_laboratory(created_lab.id)
        assert retrieved_lab.id == created_lab.id
        
        # Update laboratory
        update_data = {'capacity': 25}
        updated_lab = await lab_service.update_laboratory(created_lab.id, update_data)
        assert updated_lab.capacity == 25
        
        # Delete laboratory
        result = await lab_service.delete_laboratory(created_lab.id)
        assert result is True
    
    @pytest.mark.asyncio
    async def test_laboratory_service_booking(self, initialized_services):
        """Test laboratory service booking functionality."""
        lab_service = initialized_services.get('laboratory_service')
        
        # Create laboratory
        lab_data = {
            'name': 'Test Laboratory',
            'building_id': 'BLD001',
            'room_number': '101',
            'capacity': 20,
            'equipment_list': ['Computers', 'Projector'],
            'safety_features': ['Fire Extinguisher', 'First Aid Kit'],
            'lab_type': 'Computer Science'
        }
        
        created_lab = await lab_service.create_laboratory(lab_data)
        
        # Book laboratory
        booking_data = {
            'laboratory_id': created_lab.id,
            'user_id': 'USR001',
            'booking_date': '2023-12-01',
            'start_time': '09:00',
            'end_time': '11:00',
            'purpose': 'Test Session',
            'participant_count': 15,
            'equipment_required': ['Computers']
        }
        
        booking = await lab_service.book_laboratory(booking_data)
        assert booking['status'] == 'confirmed'
        assert booking['laboratory_id'] == created_lab.id
        
        # Get booking history
        history = await lab_service.get_laboratory_booking_history(created_lab.id)
        assert len(history) >= 1
        
        # Cancel booking
        result = await lab_service.cancel_laboratory_booking(booking['id'])
        assert result is True
    
    # Room Service Tests
    
    @pytest.mark.asyncio
    async def test_room_service_crud(self, initialized_services):
        """Test room service CRUD operations."""
        room_service = initialized_services.get('room_service')
        
        # Create room
        room_data = {
            'name': 'Test Room',
            'building_id': 'BLD001',
            'room_type': 'classroom',
            'capacity': 30,
            'location': 'First Floor',
            'description': 'Standard classroom with projector',
            'features': ['Projector', 'Whiteboard', 'Air Conditioning']
        }
        
        created_room = await room_service.create_room(room_data)
        assert created_room.name == 'Test Room'
        assert created_room.capacity == 30
        assert created_room.room_type == 'classroom'
        assert 'Projector' in created_room.features
        
        # Get room
        retrieved_room = await room_service.get_room(created_room.id)
        assert retrieved_room.id == created_room.id
        
        # Update room
        update_data = {'capacity': 35}
        updated_room = await room_service.update_room(created_room.id, update_data)
        assert updated_room.capacity == 35
        
        # Delete room
        result = await room_service.delete_room(created_room.id)
        assert result is True
    
    @pytest.mark.asyncio
    async def test_room_service_booking(self, initialized_services):
        """Test room service booking functionality."""
        room_service = initialized_services.get('room_service')
        
        # Create room
        room_data = {
            'name': 'Test Room',
            'building_id': 'BLD001',
            'room_type': 'classroom',
            'capacity': 30,
            'location': 'First Floor',
            'features': ['Projector', 'Whiteboard', 'Air Conditioning']
        }
        
        created_room = await room_service.create_room(room_data)
        
        # Book room
        booking_data = {
            'room_id': created_room.id,
            'user_id': 'USR001',
            'start_date': '2023-12-01',
            'end_date': '2023-12-01',
            'purpose': 'Meeting',
            'required_capacity': 20
        }
        
        booking = await room_service.book_room(booking_data)
        assert booking['status'] == 'confirmed'
        assert booking['room_id'] == created_room.id
        
        # Get room availability
        availability = await room_service.get_room_availability(
            created_room.id, 
            date(2023, 12, 1), 
            date(2023, 12, 1)
        )
        assert availability['room_id'] == created_room.id
        assert 'availability' in availability
        
        # Get booking history
        history = await room_service.get_booking_history(created_room.id)
        assert len(history) >= 1
    
    @pytest.mark.asyncio
    async def test_room_service_waiting_list(self, initialized_services):
        """Test room service waiting list functionality."""
        room_service = initialized_services.get('room_service')
        
        # Create room
        room_data = {
            'name': 'Test Room',
            'building_id': 'BLD001',
            'room_type': 'classroom',
            'capacity': 30,
            'location': 'First Floor',
            'features': ['Projector', 'Whiteboard', 'Air Conditioning']
        }
        
        created_room = await room_service.create_room(room_data)
        
        # Add to waiting list
        waiting_list_data = {
            'room_id': created_room.id,
            'user_id': 'USR001',
            'purpose': 'Meeting',
            'priority': 'normal'
        }
        
        entry = await room_service.add_to_waiting_list(waiting_list_data)
        assert entry['room_id'] == created_room.id
        assert entry['user_id'] == 'USR001'
        
        # Get waiting list
        waiting_list = await room_service.get_waiting_list(created_room.id)
        assert len(waiting_list) >= 1
        
        # Remove from waiting list
        result = await room_service.remove_from_waiting_list(entry['id'])
        assert result is True
    
    # Service Container Tests
    
    @pytest.mark.asyncio
    async def test_service_container_singleton(self, initialized_services):
        """Test service container singleton behavior."""
        # Get same service twice
        service1 = initialized_services.get('student_service')
        service2 = initialized_services.get('student_service')
        
        assert service1 is service2  # Should be the same instance
        
        # Verify it's a singleton
        assert initialized_services.is_singleton('student_service')
        assert not initialized_services.is_singleton('nonexistent_service')
    
    @pytest.mark.asyncio
    async def test_service_container_dependencies(self, initialized_services):
        """Test service container dependency resolution."""
        # Check service dependencies
        student_deps = initialized_services.get_dependencies('student_service')
        assert 'student_repository' in student_deps
        
        # Check that all services are registered
        services = initialized_services.get_registered_services()
        assert 'student_service' in services
        assert 'teacher_service' in services
        assert 'course_service' in services
        assert 'class_service' in services
        assert 'subject_service' in services
        assert 'department_service' in services
        assert 'mark_service' in services
        assert 'timetable_entry_service' in services
        assert 'grade_service' in services
        assert 'laboratory_service' in services
        assert 'room_service' in services
    
    @pytest.mark.asyncio
    async def test_service_container_info(self, initialized_services):
        """Test service container service information."""
        # Get service info
        info = initialized_services.get_service_info('student_service')
        assert info['name'] == 'student_service'
        assert info['instance_exists'] is True
        assert info['dependencies_resolved'] is True
        
        # Test error handling
        with pytest.raises(KeyError):
            initialized_services.get_service_info('nonexistent_service')
    
    # Error Handling Tests
    
    @pytest.mark.asyncio
    async def test_error_handling(self, initialized_services):
        """Test error handling across all services."""
        student_service = initialized_services.get('student_service')
        
        # Test getting non-existent student
        with pytest.raises(NotFoundError):
            await student_service.get_student('nonexistent-id')
        
        # Test updating non-existent student
        with pytest.raises(NotFoundError):
            await student_service.update_student('nonexistent-id', {'name': 'Test'})
        
        # Test deleting non-existent student
        with pytest.raises(NotFoundError):
            await student_service.delete_student('nonexistent-id')
    
    # Performance Tests
    
    @pytest.mark.asyncio
    async def test_performance_bulk_operations(self, initialized_services):
        """Test performance of bulk operations."""
        student_service = initialized_services.get('student_service')
        
        # Create multiple students
        students_data = []
        for i in range(10):
            student_data = {
                'name': f'Student {i}',
                'email': f'student{i}@example.com',
                'student_id': f'STU{i:03d}'
            }
            students_data.append(student_data)
        
        # Create students
        created_students = []
        for student_data in students_data:
            student = await student_service.create_student(student_data)
            created_students.append(student)
        
        # Update students in bulk
        updates = [{'id': student.id, 'name': f'Updated Student {i}'} for i, student in enumerate(created_students)]
        results = await student_service.batch_update_students(updates)
        
        # Verify all updates
        for result in results.values():
            assert result is True
        
        # Delete students in bulk
        student_ids = [student.id for student in created_students]
        delete_results = await student_service.batch_delete_students(student_ids)
        
        # Verify all deletions
        for result in delete_results.values():
            assert result is True
    
    # Integration Tests
    
    @pytest.mark.asyncio
    async def test_cross_service_integration(self, initialized_services):
        """Test integration between different services."""
        student_service = initialized_services.get('student_service')
        course_service = initialized_services.get('course_service')
        mark_service = initialized_services.get('mark_service')
        
        # Create student
        student_data = {
            'name': 'Integration Test Student',
            'email': 'integration@example.com',
            'student_id': 'IT001'
        }
        created_student = await student_service.create_student(student_data)
        
        # Create course
        course_data = {
            'name': 'Integration Test Course',
            'code': 'ITC101',
            'description': 'Test Course for Integration',
            'credits': 3,
            'department_id': 'DEPT001'
        }
        created_course = await course_service.create_course(course_data)
        
        # Create mark
        mark_data = {
            'student_id': created_student.id,
            'course_id': created_course.id,
            'exam_name': 'Integration Test Exam',
            'score': 85.0,
            'max_score': 100,
            'weight': 0.3
        }
        created_mark = await mark_service.create_mark(mark_data)
        
        # Verify relationships
        assert created_mark.student_id == created_student.id
        assert created_mark.course_id == created_course.id
        
        # Clean up
        await mark_service.delete_mark(created_mark.id)
        await course_service.delete_course(created_course.id)
        await student_service.delete_student(created_student.id)
    
    # Analytics Tests
    
    @pytest.mark.asyncio
    async def test_analytics_functionality(self, initialized_services):
        """Test analytics functionality across services."""
        mark_service = initialized_services.get('mark_service')
        room_service = initialized_services.get('room_service')
        
        # Test mark analytics
        stats = await mark_service.get_student_grade_stats('STU001')
        assert isinstance(stats, MarkStats)
        assert stats.total_marks >= 0
        
        # Test room analytics
        room_stats = await room_service.get_room_stats('ROOM001')
        assert isinstance(room_stats, RoomStats)
        assert room_stats.total_bookings >= 0
        
        # Test grade analytics
        grade_distribution = await mark_service.get_grade_distribution('GS001')
        assert isinstance(grade_distribution, dict)
        assert 'total' in grade_distribution
    
    # Batch Operation Tests
    
    @pytest.mark.asyncio
    async def test_batch_operations(self, initialized_services):
        """Test batch operations across services."""
        student_service = initialized_services.get('student_service')
        room_service = initialized_services.get('room_service')
        
        # Create multiple students
        students_data = []
        for i in range(5):
            student_data = {
                'name': f'Batch Student {i}',
                'email': f'batch{i}@example.com',
                'student_id': f'BST{i:03d}'
            }
            students_data.append(student_data)
        
        created_students = []
        for student_data in students_data:
            student = await student_service.create_student(student_data)
            created_students.append(student)
        
        # Batch update
        updates = [{'id': student.id, 'name': f'Updated Batch Student {i}'} for i, student in enumerate(created_students)]
        update_results = await student_service.batch_update_students(updates)
        
        # Verify updates
        for student_id, result in update_results.items():
            assert result is True
        
        # Create multiple rooms
        rooms_data = []
        for i in range(3):
            room_data = {
                'name': f'Batch Room {i}',
                'building_id': 'BLD001',
                'room_type': 'classroom',
                'capacity': 30 + i * 5,
                'location': f'Floor {i+1}'
            }
            rooms_data.append(room_data)
        
        created_rooms = []
        for room_data in rooms_data:
            room = await room_service.create_room(room_data)
            created_rooms.append(room)
        
        # Batch delete rooms
        room_ids = [room.id for room in created_rooms]
        delete_results = await room_service.batch_delete_rooms(room_ids)
        
        # Verify deletions
        for room_id, result in delete_results.items():
            assert result is True


@pytest.fixture(scope="module", autouse=True)
def cleanup():
    """Cleanup after all tests."""
    def cleanup_func():
        # This would run after all tests
        pass
    return cleanup_func