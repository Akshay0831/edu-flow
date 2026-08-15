"""
Teacher Service Unit Tests

This module provides comprehensive unit tests for the TeacherService class.
It tests all CRUD operations, validation, error handling, and business logic.

Author: Edu-Flow Team
"""

import pytest
import asyncio
from datetime import datetime, date
from uuid import uuid4
from unittest.mock import Mock, AsyncMock, patch

from src.core.exceptions import NotFoundError, ValidationError, DatabaseError, ConflictError
from src.infrastructure.services.teacher_service import TeacherService
from src.infrastructure.repositories.teacher_repository_fixed import TeacherRepository
from src.models.teacher import TeacherCreate, TeacherUpdate, TeacherResponse, TeacherStats
from tests.mock_database_manager import MockDatabaseManager


class TestTeacherServiceUnit:
    """Comprehensive unit tests for TeacherService."""
    
    @pytest.fixture
    def mock_repository(self):
        """Create mock teacher repository."""
        mock = Mock(spec=TeacherRepository)
        # Add all missing async methods
        mock.count = AsyncMock(return_value=1)
        mock.get_teacher_count = AsyncMock(return_value=1)
        mock.get_all = AsyncMock(return_value=[])
        mock.get_teacher_classes = AsyncMock(return_value=[])
        mock.get_by_employee_id = AsyncMock(return_value=None)
        mock.get_by_department = AsyncMock(return_value=[])
        mock.get_teacher_stats = AsyncMock(return_value={})
        mock.get_by_subject = AsyncMock(return_value=[])
        mock.get_teacher_evaluations = AsyncMock(return_value=[])
        mock.calculate_workload = AsyncMock(return_value={})
        return mock
    
    @pytest.fixture
    def teacher_service(self, mock_repository):
        """Create teacher service with mock repository."""
        return TeacherService(mock_repository)
    
    @pytest.fixture
    def sample_teacher_data(self):
        """Sample teacher data for testing."""
        return {
            'name': 'Dr. Jane Smith',
            'email': 'jane.smith@example.com',
            'employee_id': 'EMP001',
            'date_of_birth': '1975-03-15',
            'gender': 'female',
            'phone_number': '+1-1234567890',
            'address': '456 Education Ave, City',
            'teacher_id': 'TCH001',
            'hire_date': '2020-08-01',
            'department_id': 'DEPT001',
            'specialization': 'Computer Science',
            'qualification': 'PhD',
            'subjects_taught': ['CS101', 'CS202'],
            'experience_years': 10,
            'status': 'active'
        }
    
    # Test CRUD Operations
    
    @pytest.mark.asyncio
    async def test_create_teacher_success(self, teacher_service, mock_repository, sample_teacher_data):
        """Test successful teacher creation."""
        # Mock repository methods
        mock_repository.get_by_email.return_value = None  # Teacher doesn't exist
        mock_teacher = Mock()
        mock_teacher.id = str(uuid4())
        mock_teacher.dict.return_value = {
            'id': mock_teacher.id,
            **sample_teacher_data
        }
        mock_repository.create.return_value = mock_teacher
        
        # Test
        result = await teacher_service.create(sample_teacher_data)
        
        # Assertions
        mock_repository.create.assert_called_once()
        assert result['name'] == sample_teacher_data['name']
        assert result['email'] == sample_teacher_data['email']
    
    @pytest.mark.asyncio
    async def test_get_teacher_success(self, teacher_service, mock_repository):
        """Test successful teacher retrieval."""
        teacher_id = str(uuid4())
        mock_teacher = Mock()
        mock_teacher.id = teacher_id
        mock_teacher.dict.return_value = {'id': teacher_id, 'name': 'Dr. Jane Smith'}
        mock_repository.get_by_id.return_value = mock_teacher
    
        result = await teacher_service.get(teacher_id)
        
        mock_repository.get_by_id.assert_called_once_with(teacher_id)
        assert result is not None
        assert result['id'] == teacher_id
    
    @pytest.mark.asyncio
    async def test_get_teacher_not_found(self, teacher_service, mock_repository):
        """Test teacher retrieval when teacher doesn't exist."""
        teacher_id = str(uuid4())
        mock_repository.get_by_id.return_value = None
        
        result = await teacher_service.get(teacher_id)
        
        mock_repository.get_by_id.assert_called_once_with(teacher_id)
        assert result is None
    
    @pytest.mark.asyncio
    async def test_update_teacher_success(self, teacher_service, mock_repository):
        """Test successful teacher update."""
        teacher_id = str(uuid4())
        update_data = {'name': 'Dr. Jane Updated'}
        
        mock_teacher = Mock()
        mock_teacher.id = teacher_id
        mock_teacher.dict.return_value = {'id': teacher_id, 'name': 'Dr. Jane Updated'}
        mock_repository.update.return_value = mock_teacher
        
        result = await teacher_service.update(teacher_id, update_data)
        
        mock_repository.update.assert_called_once()
        assert result['name'] == 'Dr. Jane Updated'
    
    @pytest.mark.asyncio
    async def test_delete_teacher_success(self, teacher_service, mock_repository):
        """Test successful teacher deletion."""
        teacher_id = str(uuid4())
        mock_repository.delete.return_value = True
        
        result = await teacher_service.delete(teacher_id)
        
        mock_repository.delete.assert_called_once_with(teacher_id)
        assert result is True
    
    @pytest.mark.asyncio
    async def test_list_teachers_success(self, teacher_service, mock_repository):
        """Test successful teacher listing."""
        mock_teachers = [
            Mock(id=str(uuid4()), name='Teacher 1'),
            Mock(id=str(uuid4()), name='Teacher 2')
        ]
        for teacher in mock_teachers:
            teacher.dict = Mock(return_value={'id': teacher.id, 'name': teacher.name})
        
        mock_repository.get_all.return_value = mock_teachers
        
        result = await teacher_service.list(skip=0, limit=10)
        
        mock_repository.get_all.assert_called_once_with(skip=0, limit=10)
        assert len(result) == 2
        assert all('id' in teacher for teacher in result)
    
    @pytest.mark.asyncio
    async def test_count_teachers_success(self, teacher_service, mock_repository):
        """Test teacher counting."""
        mock_repository.count.return_value = 15
        
        result = await teacher_service.count()
        
        mock_repository.count.assert_called_once()
        assert result == 15
    
    # Test Business Logic Methods
    
    @pytest.mark.asyncio
    async def test_get_teacher_by_teacher_id_success(self, teacher_service, mock_repository):
        """Test teacher retrieval by teacher ID."""
        teacher_id = 'TCH001'
        mock_teacher = Mock()
        mock_teacher.id = str(uuid4())
        mock_teacher.dict.return_value = {'id': mock_teacher.id, 'teacher_id': teacher_id}
        mock_repository.get_by_employee_id.return_value = mock_teacher
        
        result = await teacher_service.get_teacher_by_employee_id(teacher_id)
        
        mock_repository.get_by_employee_id.assert_called_once_with(teacher_id)
        assert result is not None
        assert result['teacher_id'] == teacher_id
    
    @pytest.mark.asyncio
    async def test_get_teachers_by_department_success(self, teacher_service, mock_repository):
        """Test teacher listing by department."""
        department_id = 'DEPT001'
        mock_teachers = [Mock(id=str(uuid4()), name='Teacher 1')]
        for teacher in mock_teachers:
            teacher.dict = Mock(return_value={'id': teacher.id, 'name': teacher.name})
        
        mock_repository.get_by_department.return_value = mock_teachers
        
        result = await teacher_service.get_teachers_by_department(department_id)
        
        mock_repository.get_by_department.assert_called_once_with(department_id='DEPT001', skip=0, limit=100)
        assert len(result) == 1
    
    @pytest.mark.asyncio
    async def test_get_teacher_statistics_success(self, teacher_service, mock_repository):
        """Test teacher statistics calculation."""
        teacher_id = str(uuid4())
        mock_stats = Mock()
        mock_stats.dict.return_value = {
            'total_classes': 8,
            'total_students': 240,
            'average_rating': 4.5,
            'experience_years': 10
        }
        mock_repository.get_teacher_stats.return_value = mock_stats
        
        result = await teacher_service.get_teacher_stats(teacher_id)
        
        mock_repository.get_teacher_stats.assert_called_once_with(teacher_id, None, None)
        assert result['total_classes'] == 8
    
    @pytest.mark.asyncio
    async def test_get_teachers_by_specialization_success(self, teacher_service, mock_repository):
        """Test teacher listing by specialization."""
        specialization = 'Computer Science'
        mock_teachers = [Mock(id=str(uuid4()), name='Teacher 1')]
        for teacher in mock_teachers:
            teacher.dict = Mock(return_value={'id': teacher.id, 'name': teacher.name})
        
        mock_repository.get_by_subject.return_value = mock_teachers
        
        result = await teacher_service.get_teachers_by_subject(specialization)
        
        mock_repository.get_by_subject.assert_called_once_with(subject_id='Computer Science', skip=0, limit=100)
        assert len(result) == 1
    
    # Test Validation
    
    @pytest.mark.asyncio
    async def test_create_teacher_validation_error(self, teacher_service, mock_repository, sample_teacher_data):
        """Test teacher creation with validation error."""
        # Remove required field
        invalid_data = sample_teacher_data.copy()
        del invalid_data['email']
        
        with pytest.raises(ValidationError):
            await teacher_service.create_teacher(invalid_data)
    
    @pytest.mark.asyncio
    async def test_duplicate_teacher_email_error(self, teacher_service, mock_repository, sample_teacher_data):
        """Test duplicate email error."""
        mock_repository.get_by_email.return_value = Mock()  # Teacher already exists
        
        with pytest.raises(ConflictError):
            await teacher_service.create_teacher(sample_teacher_data)
    
    @pytest.mark.asyncio
    async def test_teacher_not_found_error(self, teacher_service, mock_repository):
        """Test teacher not found error."""
        teacher_id = str(uuid4())
        mock_repository.get_by_id.return_value = None
        
        result = await teacher_service.get(teacher_id)
        assert result is None
    
    # Test Service Lifecycle
    
    @pytest.mark.asyncio
    async def test_service_initialization(self, teacher_service):
        """Test service initialization."""
        await teacher_service.initialize()
        assert teacher_service.is_initialized() is True
    
    @pytest.mark.asyncio
    async def test_service_disposal(self, teacher_service):
        """Test service disposal."""
        await teacher_service.dispose()
        assert teacher_service.is_initialized() is False
    
    # Test Error Handling
    
    @pytest.mark.asyncio
    async def test_database_error_handling(self, teacher_service, mock_repository, sample_teacher_data):
        """Test database error handling."""
        mock_repository.get_by_email.return_value = None  # Teacher doesn't exist
        mock_repository.create.side_effect = DatabaseError("Database connection failed")
        
        with pytest.raises(DatabaseError):
            await teacher_service.create_teacher(sample_teacher_data)
    
    @pytest.mark.asyncio 
    async def test_cache_invalidation(self, teacher_service, mock_repository):
        """Test cache invalidation."""
        teacher_id = str(uuid4())
        mock_repository.get_by_id.return_value = None
        
        # First call - should hit database
        await teacher_service.get(teacher_id)
        
        # Second call - should also hit database after cache invalidation
        await teacher_service.get(teacher_id)
        
        # Should be called twice (cache invalidated after each call)
        assert mock_repository.get_by_id.call_count == 2