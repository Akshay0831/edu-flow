"""
Class Service Unit Tests

This module provides comprehensive unit tests for the ClassService class.
It tests all CRUD operations, validation, error handling, and business logic.

Author: Edu-Flow Team
"""

import pytest
import asyncio
from datetime import datetime, date, time
from uuid import uuid4
from unittest.mock import Mock, AsyncMock, patch

from src.core.exceptions import NotFoundError, ValidationError, DatabaseError, ConflictError
from src.infrastructure.services.class_service import ClassService
from src.infrastructure.repositories.class_repository import ClassRepository
from tests.mock_database_manager import MockDatabaseManager


class TestClassServiceUnit:
    """Comprehensive unit tests for ClassService."""
    
    @pytest.fixture
    def mock_repository(self):
        """Create mock class repository."""
        return Mock(spec=ClassRepository)
    
    @pytest.fixture
    def class_service(self, mock_repository):
        """Create class service with mock repository."""
        return ClassService(mock_repository)
    
    @pytest.fixture
    def sample_class_data(self):
        """Sample class data for testing."""
        return {
            'name': 'CS201-A',
            'class_code': 'CS201A',
            'description': 'Data Structures Class',
            'subject_id': 'SUB001',
            'teacher_id': 'TCH001',
            'department_id': 'DEPT001',
            'capacity': 30,
            'semester': 'Fall',
            'academic_year': '2023-2024',
            'enrolled_students': ['STU001', 'STU002'],
            'schedule': 'MWF 10:00-11:30',
            'location': 'Room 101',
            'schedule_details': {
                'day_of_week': 'Monday, Wednesday, Friday',
                'start_time': '10:00',
                'end_time': '11:30',
                'duration_minutes': 90
            },
            'class_type': 'lecture',
            'requirements': ['Basic programming knowledge'],
            'objectives': ['Understand data structures', 'Implement algorithms'],
            'assessment_methods': ['Assignments', 'Midterm', 'Final Exam'],
            'resources': ['Textbook', 'Online materials'],
            'status': 'active'
        }
    
    # Test CRUD Operations
    
    @pytest.mark.asyncio
    async def test_create_class_success(self, class_service, mock_repository, sample_class_data):
        """Test successful class creation."""
        mock_repository.create.return_value = AsyncMock()
        mock_repository.create.return_value.id = str(uuid4())
        mock_repository.create.return_value.dict.return_value = {
            'id': str(uuid4()),
            **sample_class_data
        }
        
        result = await class_service.create(sample_class_data)
        
        mock_repository.create.assert_called_once_with(sample_class_data)
        assert result['name'] == sample_class_data['name']
        assert result['capacity'] == sample_class_data['capacity']
    
    @pytest.mark.asyncio
    async def test_get_class_success(self, class_service, mock_repository):
        """Test successful class retrieval."""
        class_id = str(uuid4())
        mock_class = Mock()
        mock_class.id = class_id
        mock_class.dict.return_value = {'id': class_id, 'name': 'CS201-A'}
        mock_repository.get_by_id.return_value = mock_class
        
        result = await class_service.get(class_id)
        
        mock_repository.get_by_id.assert_called_once_with(class_id)
        assert result is not None
        assert result['id'] == class_id
    
    @pytest.mark.asyncio
    async def test_get_class_by_code_success(self, class_service, mock_repository):
        """Test successful class retrieval by code."""
        class_code = 'CS201-A'
        mock_class = Mock()
        mock_class.id = str(uuid4())
        mock_class.dict.return_value = {'id': mock_class.id, 'name': class_code}
        mock_repository.get_by_code.return_value = mock_class
        
        result = await class_service.get_class_by_code(class_code)
        
        mock_repository.get_by_code.assert_called_once_with(class_code)
        assert result is not None
        assert result['name'] == class_code
    
    @pytest.mark.asyncio
    async def test_update_class_success(self, class_service, mock_repository):
        """Test successful class update."""
        class_id = str(uuid4())
        update_data = {'capacity': 35}
        
        mock_class = Mock()
        mock_class.id = class_id
        mock_class.dict.return_value = {'id': class_id, 'capacity': 35}
        mock_repository.update.return_value = mock_class
        
        result = await class_service.update(class_id, update_data)
        
        mock_repository.update.assert_called_once_with(class_id, update_data)
        assert result['capacity'] == 35
    
    @pytest.mark.asyncio
    async def test_delete_class_success(self, class_service, mock_repository):
        """Test successful class deletion."""
        class_id = str(uuid4())
        mock_repository.delete.return_value = True
        
        result = await class_service.delete(class_id)
        
        mock_repository.delete.assert_called_once_with(class_id)
        assert result is True
    
    @pytest.mark.asyncio
    async def test_list_classes_success(self, class_service, mock_repository):
        """Test successful class listing."""
        mock_classes = [
            Mock(id=str(uuid4()), name='CS201-A'),
            Mock(id=str(uuid4()), name='CS201-B')
        ]
        for class_obj in mock_classes:
            class_obj.dict = Mock(return_value={'id': class_obj.id, 'name': class_obj.name})
        
        mock_repository.get_all.return_value = mock_classes
        
        result = await class_service.list(skip=0, limit=10)
        
        mock_repository.get_all.assert_called_once_with(skip=0, limit=10)
        assert len(result) == 2
        assert all('id' in class_obj for class_obj in result)
    
    @pytest.mark.asyncio
    async def test_count_classes_success(self, class_service, mock_repository):
        """Test class counting."""
        mock_repository.count.return_value = 42
        
        result = await class_service.count()
        
        mock_repository.count.assert_called_once()
        assert result == 42
    
    # Test Business Logic Methods
    
    @pytest.mark.asyncio
    async def test_get_classes_by_teacher_success(self, class_service, mock_repository):
        """Test successful class listing by teacher."""
        teacher_id = 'TCH001'
        mock_classes = [Mock(id=str(uuid4()), name='Teacher Class')]
        for class_obj in mock_classes:
            class_obj.dict = Mock(return_value={'id': class_obj.id, 'name': class_obj.name})
        
        mock_repository.get_by_teacher.return_value = mock_classes
        
        result = await class_service.get_classes_by_teacher(teacher_id)
        
        mock_repository.get_by_teacher.assert_called_once_with(teacher_id)
        assert len(result) == 1
    
    @pytest.mark.asyncio
    async def test_get_classes_by_subject_success(self, class_service, mock_repository):
        """Test successful class listing by subject."""
        subject_id = 'SUB001'
        mock_classes = [Mock(id=str(uuid4()), name='Subject Class')]
        for class_obj in mock_classes:
            class_obj.dict = Mock(return_value={'id': class_obj.id, 'name': class_obj.name})
        
        mock_repository.get_by_subject.return_value = mock_classes
        
        result = await class_service.get_classes_by_subject(subject_id)
        
        mock_repository.get_by_subject.assert_called_once_with(subject_id)
        assert len(result) == 1
    
    @pytest.mark.asyncio
    async def test_get_classes_by_academic_year_success(self, class_service, mock_repository):
        """Test successful class listing by academic year."""
        academic_year = '2023-2024'
        mock_classes = [Mock(id=str(uuid4()), name='Year Class')]
        for class_obj in mock_classes:
            class_obj.dict = Mock(return_value={'id': class_obj.id, 'name': class_obj.name})
        
        mock_repository.get_by_academic_year.return_value = mock_classes
        
        result = await class_service.get_classes_by_academic_year(academic_year)
        
        mock_repository.get_by_academic_year.assert_called_once_with(academic_year)
        assert len(result) == 1
    
    @pytest.mark.asyncio
    async def get_classes_by_schedule_success(self, class_service, mock_repository):
        """Test successful class listing by schedule."""
        day_of_week = 'Monday'
        start_time = time(9, 0)
        end_time = time(10, 30)
        mock_classes = [Mock(id=str(uuid4()), name='Schedule Class')]
        for class_obj in mock_classes:
            class_obj.dict = Mock(return_value={'id': class_obj.id, 'name': class_obj.name})
        
        mock_repository.get_by_schedule.return_value = mock_classes
        
        result = await class_service.get_classes_by_schedule(day_of_week, start_time, end_time)
        
        mock_repository.get_by_schedule.assert_called_once_with(day_of_week, start_time, end_time)
        assert len(result) == 1
    
    @pytest.mark.asyncio
    async def test_enroll_student_success(self, class_service, mock_repository):
        """Test successful student enrollment."""
        class_id = str(uuid4())
        student_id = 'STU001'
        
        mock_class = Mock()
        mock_class.id = class_id
        mock_class.capacity = 30
        mock_class.enrolled_students = [student_id]
        mock_class.dict.return_value = {'id': class_id, 'enrolled_students': [student_id]}
        mock_repository.enroll_student.return_value = mock_class
        
        result = await class_service.enroll_student(class_id, student_id)
        
        mock_repository.enroll_student.assert_called_once_with(class_id, student_id)
        assert student_id in result['enrolled_students']
    
    @pytest.mark.asyncio
    async def test_unenroll_student_success(self, class_service, mock_repository):
        """Test successful student unenrollment."""
        class_id = str(uuid4())
        student_id = 'STU001'
        
        mock_class = Mock()
        mock_class.id = class_id
        mock_class.enrolled_students = []
        mock_class.dict.return_value = {'id': class_id, 'enrolled_students': []}
        mock_repository.unenroll_student.return_value = mock_class
        
        result = await class_service.unenroll_student(class_id, student_id)
        
        mock_repository.unenroll_student.assert_called_once_with(class_id, student_id)
        assert student_id not in result['enrolled_students']
    
    @pytest.mark.asyncio
    async def test_get_class_statistics_success(self, class_service, mock_repository):
        """Test class statistics calculation."""
        class_id = str(uuid4())
        mock_stats = Mock()
        mock_stats.dict.return_value = {
            'enrollment_count': 25,
            'capacity_utilization': 0.83,
            'average_grade': 85.5,
            'pass_rate': 92.5,
            'attendance_rate': 88.0
        }
        mock_repository.get_class_statistics.return_value = mock_stats
        
        result = await class_service.get_class_statistics(class_id)
        
        mock_repository.get_class_statistics.assert_called_once_with(class_id)
        assert result['enrollment_count'] == 25
    
    @pytest.mark.asyncio
    async def test_check_capacity_success(self, class_service, mock_repository):
        """Test capacity checking."""
        class_id = str(uuid4())
        current_enrollments = 25
        capacity = 30
        
        mock_repository.get_enrollment_count.return_value = current_enrollments
        mock_repository.get_capacity.return_value = capacity
        
        result = await class_service.check_capacity(class_id)
        
        mock_repository.get_enrollment_count.assert_called_once_with(class_id)
        mock_repository.get_capacity.assert_called_once_with(class_id)
        assert result['available_capacity'] == 5
        assert result['is_available'] is True
    
    # Test Validation
    
    @pytest.mark.asyncio
    async def test_create_class_validation_error(self, class_service, mock_repository, sample_class_data):
        """Test class creation with validation error."""
        invalid_data = sample_class_data.copy()
        invalid_data['name'] = ''  # Empty name should fail validation
        
        with pytest.raises(ValidationError):
            await class_service.create_class(invalid_data)
    
    @pytest.mark.asyncio
    async def test_duplicate_class_code_error(self, class_service, mock_repository, sample_class_data):
        """Test duplicate class code error."""
        mock_repository.create.side_effect = ConflictError("Class code already exists")
        
        with pytest.raises(ConflictError):
            await class_service.create_class(sample_class_data)
    
    @pytest.mark.asyncio
    async def test_class_not_found_error(self, class_service, mock_repository):
        """Test class not found error."""
        class_id = str(uuid4())
        mock_repository.get_by_id.return_value = None
        
        with pytest.raises(NotFoundError):
            await class_service.get_class_by_id(class_id)
    
    @pytest.mark.asyncio
    async def test_capacity_exceeded_error(self, class_service, mock_repository):
        """Test capacity exceeded error."""
        class_id = str(uuid4())
        mock_repository.get_enrollment_count.return_value = 30
        mock_repository.get_capacity.return_value = 30
        
        with pytest.raises(ValidationError):
            await class_service.check_capacity(class_id)
    
    @pytest.mark.asyncio
    async def test_schedule_conflict_error(self, class_service, mock_repository):
        """Test schedule conflict error."""
        class_id = str(uuid4())
        day_of_week = 'Monday'
        start_time = time(10, 0)
        end_time = time(11, 30)
        
        mock_repository.check_schedule_conflict.return_value = True
        
        with pytest.raises(ValidationError):
            await class_service.get_classes_by_schedule(day_of_week, start_time, end_time)
    
    # Test Service Lifecycle
    
    @pytest.mark.asyncio
    async def test_service_initialization(self, class_service):
        """Test service initialization."""
        await class_service.initialize()
        assert class_service.is_initialized() is True
    
    @pytest.mark.asyncio
    async def test_service_disposal(self, class_service):
        """Test service disposal."""
        await class_service.dispose()
        assert class_service.is_initialized() is False
    
    # Test Error Handling
    
    @pytest.mark.asyncio
    async def test_database_error_handling(self, class_service, mock_repository, sample_class_data):
        """Test database error handling."""
        mock_repository.create.side_effect = DatabaseError("Database connection failed")
        
        with pytest.raises(DatabaseError):
            await class_service.create_class(sample_class_data)
    
    @pytest.mark.asyncio
    async def test_cache_invalidation(self, class_service, mock_repository):
        """Test cache invalidation."""
        class_id = str(uuid4())
        mock_repository.get_by_id.return_value = None
        
        # First call
        await class_service.get_class_by_id(class_id)
        
        # Second call after cache invalidation
        await class_service.get_class_by_id(class_id)
        
        # Should be called twice (cache invalidated)
        assert mock_repository.get_by_id.call_count == 2