"""
Student Service Unit Tests

This module provides comprehensive unit tests for the StudentService class.
It tests all CRUD operations, validation, error handling, and business logic.

Author: Edu-Flow Team
"""

import pytest
import asyncio
from datetime import datetime, date
from uuid import uuid4
from unittest.mock import Mock, AsyncMock, patch

from src.core.exceptions import NotFoundError, ValidationError, DatabaseError, ConflictError
from src.infrastructure.services.student_service import StudentService
from src.infrastructure.repositories.student_repository import StudentRepository
from src.models.student import StudentCreate, StudentUpdate, StudentResponse, StudentStatistics
from tests.mock_database_manager import MockDatabaseManager


class TestStudentServiceUnit:
    """Comprehensive unit tests for StudentService."""
    
    @pytest.fixture
    def mock_repository(self):
        """Create mock student repository."""
        return Mock(spec=StudentRepository)
    
    @pytest.fixture
    def student_service(self, mock_repository):
        """Create student service with mock repository."""
        return StudentService(mock_repository)
    
    @pytest.fixture
    def sample_student_data(self):
        """Sample student data for testing."""
        return {
            'name': 'John Doe',
            'email': 'john.doe@example.com',
            'registration_number': 'REG001',
            'date_of_birth': '2000-01-01',
            'gender': 'M',
            'phone_number': '+1234567890',
            'address': '123 Main St, City',
            'student_id': 'STU001',
            'enrollment_date': '2023-09-01',
            'department_id': 'DEPT001',
            'status': 'active'
        }
    
    # Test CRUD Operations
    
    @pytest.mark.asyncio
    async def test_create_student_success(self, student_service, mock_repository, sample_student_data):
        """Test successful student creation."""
        # Mock repository methods
        mock_repository.create.return_value = AsyncMock()
        mock_repository.create.return_value.id = str(uuid4())
        mock_repository.create.return_value.dict.return_value = {
            'id': str(uuid4()),
            **sample_student_data
        }
        
        # Test
        result = await student_service.create(sample_student_data)
        
        # Assertions
        mock_repository.create.assert_called_once_with(sample_student_data)
        assert result['name'] == sample_student_data['name']
        assert result['email'] == sample_student_data['email']
    
    @pytest.mark.asyncio
    async def test_get_student_success(self, student_service, mock_repository):
        """Test successful student retrieval."""
        student_id = str(uuid4())
        mock_student = Mock()
        mock_student.id = student_id
        mock_student.dict.return_value = {'id': student_id, 'name': 'John Doe'}
        mock_repository.get_by_id.return_value = mock_student
        
        result = await student_service.get(student_id)
        
        mock_repository.get_by_id.assert_called_once_with(student_id)
        assert result is not None
        assert result['id'] == student_id
    
    @pytest.mark.asyncio
    async def test_get_student_not_found(self, student_service, mock_repository):
        """Test student retrieval when student doesn't exist."""
        student_id = str(uuid4())
        mock_repository.get_by_id.return_value = None
        
        result = await student_service.get(student_id)
        
        mock_repository.get_by_id.assert_called_once_with(student_id)
        assert result is None
    
    @pytest.mark.asyncio
    async def test_update_student_success(self, student_service, mock_repository):
        """Test successful student update."""
        student_id = str(uuid4())
        update_data = {'name': 'Jane Doe'}
        
        mock_student = Mock()
        mock_student.id = student_id
        mock_student.dict.return_value = {'id': student_id, 'name': 'Jane Doe'}
        mock_repository.update.return_value = mock_student
        
        result = await student_service.update(student_id, update_data)
        
        mock_repository.update.assert_called_once_with(student_id, update_data)
        assert result['name'] == 'Jane Doe'
    
    @pytest.mark.asyncio
    async def test_delete_student_success(self, student_service, mock_repository):
        """Test successful student deletion."""
        student_id = str(uuid4())
        mock_repository.delete.return_value = True
        
        result = await student_service.delete(student_id)
        
        mock_repository.delete.assert_called_once_with(student_id)
        assert result is True
    
    @pytest.mark.asyncio
    async def test_list_students_success(self, student_service, mock_repository):
        """Test successful student listing."""
        mock_students = [
            Mock(id=str(uuid4()), name='Student 1'),
            Mock(id=str(uuid4()), name='Student 2')
        ]
        for student in mock_students:
            student.dict = Mock(return_value={'id': student.id, 'name': student.name})
        
        mock_repository.get_all.return_value = mock_students
        
        result = await student_service.list(skip=0, limit=10)
        
        mock_repository.get_all.assert_called_once_with(skip=0, limit=10)
        assert len(result) == 2
        assert all('id' in student for student in result)
    
    @pytest.mark.asyncio
    async def test_count_students_success(self, student_service, mock_repository):
        """Test student counting."""
        mock_repository.count.return_value = 25
        
        result = await student_service.count()
        
        mock_repository.count.assert_called_once()
        assert result == 25
    
    # Test Business Logic Methods
    
    @pytest.mark.asyncio
    async def test_get_student_by_student_id_success(self, student_service, mock_repository):
        """Test student retrieval by student ID."""
        student_id = 'STU001'
        mock_student = Mock()
        mock_student.id = str(uuid4())
        mock_student.dict.return_value = {'id': mock_student.id, 'student_id': student_id}
        mock_repository.get_by_student_id.return_value = mock_student
        
        result = await student_service.get_student_by_student_id(student_id)
        
        mock_repository.get_by_student_id.assert_called_once_with(student_id)
        assert result is not None
        assert result['student_id'] == student_id
    
    @pytest.mark.asyncio
    async def test_get_students_by_department_success(self, student_service, mock_repository):
        """Test student listing by department."""
        department_id = 'DEPT001'
        mock_students = [Mock(id=str(uuid4()), name='Student 1')]
        for student in mock_students:
            student.dict = Mock(return_value={'id': student.id, 'name': student.name})
        
        mock_repository.get_by_department.return_value = mock_students
        
        result = await student_service.get_students_by_department(department_id)
        
        mock_repository.get_by_department.assert_called_once_with(department_id)
        assert len(result) == 1
    
    @pytest.mark.asyncio
    async def test_get_student_statistics_success(self, student_service, mock_repository):
        """Test student statistics calculation."""
        student_id = str(uuid4())
        mock_stats = Mock()
        mock_stats.dict.return_value = {
            'total_courses': 5,
            'average_grade': 85.5,
            'enrollment_count': 1
        }
        mock_repository.get_student_statistics.return_value = mock_stats
        
        result = await student_service.get_student_statistics(student_id)
        
        mock_repository.get_student_statistics.assert_called_once_with(student_id)
        assert result['total_courses'] == 5
    
    # Test Validation
    
    @pytest.mark.asyncio
    async def test_create_student_validation_error(self, student_service, mock_repository, sample_student_data):
        """Test student creation with validation error."""
        # Remove required field
        invalid_data = sample_student_data.copy()
        del invalid_data['email']
        
        with pytest.raises(ValidationError):
            await student_service.create_student(invalid_data)
    
    @pytest.mark.asyncio
    async def test_duplicate_student_email_error(self, student_service, mock_repository, sample_student_data):
        """Test duplicate email error."""
        mock_repository.create.side_effect = ConflictError("Email already exists")
        
        with pytest.raises(ConflictError):
            await student_service.create_student(sample_student_data)
    
    @pytest.mark.asyncio
    async def test_student_not_found_error(self, student_service, mock_repository):
        """Test student not found error."""
        student_id = str(uuid4())
        mock_repository.get_by_id.return_value = None
        
        with pytest.raises(NotFoundError):
            await student_service.get_student_by_id(student_id)
    
    # Test Service Lifecycle
    
    @pytest.mark.asyncio
    async def test_service_initialization(self, student_service):
        """Test service initialization."""
        await student_service.initialize()
        assert student_service.is_initialized() is True
    
    @pytest.mark.asyncio
    async def test_service_disposal(self, student_service):
        """Test service disposal."""
        await student_service.dispose()
        assert student_service.is_initialized() is False
    
    # Test Error Handling
    
    @pytest.mark.asyncio
    async def test_database_error_handling(self, student_service, mock_repository, sample_student_data):
        """Test database error handling."""
        mock_repository.create.side_effect = DatabaseError("Database connection failed")
        
        with pytest.raises(DatabaseError):
            await student_service.create_student(sample_student_data)
    
    @pytest.mark.asyncio 
    async def test_cache_invalidation(self, student_service, mock_repository):
        """Test cache invalidation."""
        student_id = str(uuid4())
        mock_repository.get_by_id.return_value = None
        
        # First call - should hit database
        await student_service.get_student_by_id(student_id)
        
        # Second call - should also hit database after cache invalidation
        await student_service.get_student_by_id(student_id)
        
        # Should be called twice (cache invalidated after each call)
        assert mock_repository.get_by_id.call_count == 2