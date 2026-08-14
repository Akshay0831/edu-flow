"""
Subject Service Unit Tests

This module provides comprehensive unit tests for the SubjectService class.
It tests all CRUD operations, validation, error handling, and business logic.

Author: Edu-Flow Team
"""

import pytest
import asyncio
from datetime import datetime, date
from uuid import uuid4
from unittest.mock import Mock, AsyncMock, patch

from src.core.exceptions import NotFoundError, ValidationError, DatabaseError, ConflictError
from src.infrastructure.services.subject_service import SubjectService
from src.infrastructure.repositories.subject_repository import SubjectRepository
from tests.mock_database_manager import MockDatabaseManager


class TestSubjectServiceUnit:
    """Comprehensive unit tests for SubjectService."""
    
    @pytest.fixture
    def mock_repository(self):
        """Create mock subject repository."""
        return Mock(spec=SubjectRepository)
    
    @pytest.fixture
    def subject_service(self, mock_repository):
        """Create subject service with mock repository."""
        return SubjectService(mock_repository)
    
    @pytest.fixture
    def sample_subject_data(self):
        """Sample subject data for testing."""
        return {
            'name': 'Data Structures',
            'subject_code': 'CS201',
            'description': 'Introduction to data structures and algorithms',
            'credits': 3,
            'department_id': 'DEPT001',
            'level': 'undergraduate',
            'prerequisites': ['CS101'],
            'objectives': ['Understand arrays and linked lists', 'Learn tree and graph algorithms'],
            'outcomes': ['Implement basic data structures', 'Solve algorithmic problems'],
            'syllabus': 'Week 1: Arrays and basic data structures...',
            'assessment_methods': ['Assignments', 'Midterm', 'Final Exam'],
            'textbooks': ['Data Structures and Algorithms by Author'],
            'status': 'active',
            'academic_year': '2023-2024'
        }
    
    # Test CRUD Operations
    
    @pytest.mark.asyncio
    async def test_create_subject_success(self, subject_service, mock_repository, sample_subject_data):
        """Test successful subject creation."""
        mock_repository.create.return_value = AsyncMock()
        mock_repository.create.return_value.id = str(uuid4())
        mock_repository.create.return_value.dict.return_value = {
            'id': str(uuid4()),
            **sample_subject_data
        }
        
        result = await subject_service.create(sample_subject_data)
        
        mock_repository.create.assert_called_once_with(sample_subject_data)
        assert result['name'] == sample_subject_data['name']
        assert result['code'] == sample_subject_data['code']
    
    @pytest.mark.asyncio
    async def test_get_subject_success(self, subject_service, mock_repository):
        """Test successful subject retrieval."""
        subject_id = str(uuid4())
        mock_subject = Mock()
        mock_subject.id = subject_id
        mock_subject.dict.return_value = {'id': subject_id, 'name': 'Data Structures'}
        mock_repository.get_by_id.return_value = mock_subject
        
        result = await subject_service.get(subject_id)
        
        mock_repository.get_by_id.assert_called_once_with(subject_id)
        assert result is not None
        assert result['id'] == subject_id
    
    @pytest.mark.asyncio
    async def test_get_subject_by_code_success(self, subject_service, mock_repository):
        """Test successful subject retrieval by code."""
        subject_code = 'CS201'
        mock_subject = Mock()
        mock_subject.id = str(uuid4())
        mock_subject.dict.return_value = {'id': mock_subject.id, 'code': subject_code}
        mock_repository.get_by_code.return_value = mock_subject
        
        result = await subject_service.get_subject_by_code(subject_code)
        
        mock_repository.get_by_code.assert_called_once_with(subject_code)
        assert result is not None
        assert result['code'] == subject_code
    
    @pytest.mark.asyncio
    async def test_update_subject_success(self, subject_service, mock_repository):
        """Test successful subject update."""
        subject_id = str(uuid4())
        update_data = {'name': 'Advanced Data Structures'}
        
        mock_subject = Mock()
        mock_subject.id = subject_id
        mock_subject.dict.return_value = {'id': subject_id, 'name': 'Advanced Data Structures'}
        mock_repository.update.return_value = mock_subject
        
        result = await subject_service.update(subject_id, update_data)
        
        mock_repository.update.assert_called_once_with(subject_id, update_data)
        assert result['name'] == 'Advanced Data Structures'
    
    @pytest.mark.asyncio
    async def test_delete_subject_success(self, subject_service, mock_repository):
        """Test successful subject deletion."""
        subject_id = str(uuid4())
        mock_repository.delete.return_value = True
        
        result = await subject_service.delete(subject_id)
        
        mock_repository.delete.assert_called_once_with(subject_id)
        assert result is True
    
    @pytest.mark.asyncio
    async def test_list_subjects_success(self, subject_service, mock_repository):
        """Test successful subject listing."""
        mock_subjects = [
            Mock(id=str(uuid4()), name='Data Structures'),
            Mock(id=str(uuid4()), name='Algorithms')
        ]
        for subject in mock_subjects:
            subject.dict = Mock(return_value={'id': subject.id, 'name': subject.name})
        
        mock_repository.get_all.return_value = mock_subjects
        
        result = await subject_service.list(skip=0, limit=10)
        
        mock_repository.get_all.assert_called_once_with(skip=0, limit=10)
        assert len(result) == 2
        assert all('id' in subject for subject in result)
    
    @pytest.mark.asyncio
    async def test_count_subjects_success(self, subject_service, mock_repository):
        """Test subject counting."""
        mock_repository.count.return_value = 42
        
        result = await subject_service.count()
        
        mock_repository.count.assert_called_once()
        assert result == 42
    
    # Test Business Logic Methods
    
    @pytest.mark.asyncio
    async def test_get_subjects_by_department_success(self, subject_service, mock_repository):
        """Test successful subject listing by department."""
        department_id = 'DEPT001'
        mock_subjects = [Mock(id=str(uuid4()), name='Computer Science Subject')]
        for subject in mock_subjects:
            subject.dict = Mock(return_value={'id': subject.id, 'name': subject.name})
        
        mock_repository.get_by_department.return_value = mock_subjects
        
        result = await subject_service.get_subjects_by_department(department_id)
        
        mock_repository.get_by_department.assert_called_once_with(department_id)
        assert len(result) == 1
    
    @pytest.mark.asyncio
    async def test_get_subjects_by_level_success(self, subject_service, mock_repository):
        """Test successful subject listing by level."""
        level = 'undergraduate'
        mock_subjects = [Mock(id=str(uuid4()), name='Undergraduate Subject')]
        for subject in mock_subjects:
            subject.dict = Mock(return_value={'id': subject.id, 'name': subject.name})
        
        mock_repository.get_by_level.return_value = mock_subjects
        
        result = await subject_service.get_subjects_by_level(level)
        
        mock_repository.get_by_level.assert_called_once_with(level)
        assert len(result) == 1
    
    @pytest.mark.asyncio
    async def test_get_subjects_by_credits_success(self, subject_service, mock_repository):
        """Test successful subject listing by credit range."""
        min_credits = 2
        max_credits = 4
        mock_subjects = [Mock(id=str(uuid4()), name='3-Credit Subject')]
        for subject in mock_subjects:
            subject.dict = Mock(return_value={'id': subject.id, 'name': subject.name})
        
        mock_repository.get_by_credits.return_value = mock_subjects
        
        result = await subject_service.get_subjects_by_credits(min_credits, max_credits)
        
        mock_repository.get_by_credits.assert_called_once_with(min_credits, max_credits)
        assert len(result) == 1
    
    @pytest.mark.asyncio
    async def test_get_prerequisites_success(self, subject_service, mock_repository):
        """Test subject prerequisite retrieval."""
        subject_id = str(uuid4())
        mock_prerequisites = [
            Mock(id=str(uuid4()), name='Prerequisite 1'),
            Mock(id=str(uuid4()), name='Prerequisite 2')
        ]
        for prereq in mock_prerequisites:
            prereq.dict = Mock(return_value={'id': prereq.id, 'name': prereq.name})
        
        mock_repository.get_prerequisites.return_value = mock_prerequisites
        
        result = await subject_service.get_prerequisites(subject_id)
        
        mock_repository.get_prerequisites.assert_called_once_with(subject_id)
        assert len(result) == 2
    
    @pytest.mark.asyncio
    async def test_get_subject_statistics_success(self, subject_service, mock_repository):
        """Test subject statistics calculation."""
        subject_id = str(uuid4())
        mock_stats = Mock()
        mock_stats.dict.return_value = {
            'total_enrollments': 120,
            'average_grade': 85.5,
            'pass_rate': 92.5,
            'completion_rate': 88.0
        }
        mock_repository.get_subject_statistics.return_value = mock_stats
        
        result = await subject_service.get_subject_statistics(subject_id)
        
        mock_repository.get_subject_statistics.assert_called_once_with(subject_id)
        assert result['total_enrollments'] == 120
    
    # Test Validation
    
    @pytest.mark.asyncio
    async def test_create_subject_validation_error(self, subject_service, mock_repository, sample_subject_data):
        """Test subject creation with validation error."""
        invalid_data = sample_subject_data.copy()
        invalid_data['name'] = ''  # Empty name should fail validation
        
        with pytest.raises(ValidationError):
            await subject_service.create_subject(invalid_data)
    
    @pytest.mark.asyncio
    async def test_duplicate_subject_code_error(self, subject_service, mock_repository, sample_subject_data):
        """Test duplicate subject code error."""
        mock_repository.create.side_effect = ConflictError("Subject code already exists")
        
        with pytest.raises(ConflictError):
            await subject_service.create_subject(sample_subject_data)
    
    @pytest.mark.asyncio
    async def test_subject_not_found_error(self, subject_service, mock_repository):
        """Test subject not found error."""
        subject_id = str(uuid4())
        mock_repository.get_by_id.return_value = None
        
        with pytest.raises(NotFoundError):
            await subject_service.get_subject_by_id(subject_id)
    
    @pytest.mark.asyncio
    async def test_invalid_subject_code_error(self, subject_service, mock_repository):
        """Test invalid subject code error."""
        invalid_data = {
            'name': 'Subject',
            'code': 'INVALID@CODE',  # Invalid format should fail validation
            'description': 'Test subject'
        }
        
        with pytest.raises(ValidationError):
            await subject_service.create_subject(invalid_data)
    
    # Test Service Lifecycle
    
    @pytest.mark.asyncio
    async def test_service_initialization(self, subject_service):
        """Test service initialization."""
        await subject_service.initialize()
        assert subject_service.is_initialized() is True
    
    @pytest.mark.asyncio
    async def test_service_disposal(self, subject_service):
        """Test service disposal."""
        await subject_service.dispose()
        assert subject_service.is_initialized() is False
    
    # Test Error Handling
    
    @pytest.mark.asyncio
    async def test_database_error_handling(self, subject_service, mock_repository, sample_subject_data):
        """Test database error handling."""
        mock_repository.create.side_effect = DatabaseError("Database connection failed")
        
        with pytest.raises(DatabaseError):
            await subject_service.create_subject(sample_subject_data)
    
    @pytest.mark.asyncio
    async def test_cache_invalidation(self, subject_service, mock_repository):
        """Test cache invalidation."""
        subject_id = str(uuid4())
        mock_repository.get_by_id.return_value = None
        
        # First call
        await subject_service.get_subject_by_id(subject_id)
        
        # Second call after cache invalidation
        await subject_service.get_subject_by_id(subject_id)
        
        # Should be called twice (cache invalidated)
        assert mock_repository.get_by_id.call_count == 2