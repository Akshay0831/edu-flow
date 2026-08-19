"""
Mark Service Unit Tests

This module provides comprehensive unit tests for the MarkService class.
It tests all CRUD operations, validation, error handling, and business logic.

Author: Edu-Flow Team
"""

import pytest
import asyncio
from datetime import datetime, date
from uuid import uuid4
from unittest.mock import Mock, AsyncMock, patch

from src.core.exceptions import NotFoundError, ValidationError, DatabaseError, ConflictError
from src.infrastructure.services.mark_service import MarkService
from src.infrastructure.repositories.mark_repository import MarkRepository
from src.infrastructure.repositories.base_repository import QueryResult
from tests.mock_database_manager import MockDatabaseManager


class TestMarkServiceUnit:
    """Comprehensive unit tests for MarkService."""
    
    @pytest.fixture
    def mock_repository(self):
        """Create mock mark repository."""
        return Mock(spec=MarkRepository)
    
    @pytest.fixture
    def mark_service(self, mock_repository):
        """Create mark service with mock repository."""
        return MarkService(mock_repository)
    
    @pytest.fixture
    def sample_mark_data(self):
        """Sample mark data for testing."""
        return {
            'student_id': 'STU001',
            'assessment_id': 'ASSESS001',
            'mark_value': 85,
            'graded_by': 'TCH001',
            'graded_date': date.today().isoformat(),
            'exam_name': 'Midterm Exam',
            'marks_obtained': 85,
            'total_marks': 100,
            'percentage': 85.0,
            'grade': 'A',
            'weightage': 0.3,
            'is_final': False,
            'feedback': 'Good performance',
            'status': 'graded'
        }
    
    # Test CRUD Operations
    
    @pytest.mark.asyncio
    async def test_create_mark_success(self, mark_service, mock_repository, sample_mark_data):
        """Test successful mark creation."""
        # Mock filter to return no existing marks
        mock_repository.filter.return_value = QueryResult(success=True, data=[])
        
        mock_repository.create.return_value = AsyncMock()
        mock_repository.create.return_value.id = str(uuid4())
        mock_repository.create.return_value.dict.return_value = {
            'id': str(uuid4()),
            **sample_mark_data
        }
        
        result = await mark_service.create(sample_mark_data)
        
        mock_repository.create.assert_called_once_with(sample_mark_data)
        assert result['student_id'] == sample_mark_data['student_id']
        assert result['course_id'] == sample_mark_data['course_id']
        assert result['marks_obtained'] == sample_mark_data['marks_obtained']
    
    @pytest.mark.asyncio
    async def test_get_mark_success(self, mark_service, mock_repository):
        """Test successful mark retrieval."""
        mark_id = str(uuid4())
        mock_mark = Mock()
        mock_mark.id = mark_id
        mock_mark.dict.return_value = {'id': mark_id, 'marks_obtained': 85}
        mock_repository.get_by_id.return_value = mock_mark
        
        result = await mark_service.get(mark_id)
        
        mock_repository.get_by_id.assert_called_once_with(mark_id)
        assert result is not None
        assert result['id'] == mark_id
    
    @pytest.mark.asyncio
    async def test_get_mark_by_student_course_success(self, mark_service, mock_repository):
        """Test successful mark retrieval by student and course."""
        student_id = 'STU001'
        course_id = 'COURSE001'
        mock_mark = Mock()
        mock_mark.id = str(uuid4())
        mock_mark.dict.return_value = {'id': mock_mark.id, 'student_id': student_id, 'course_id': course_id}
        mock_repository.filter = Mock(return_value=QueryResult(success=True, data=[mock_mark]))
        
        result = await mark_service.get_mark_by_student_course(student_id, course_id)
        
        mock_repository.get_by_student_course.assert_called_once_with(student_id, course_id)
        assert result is not None
        assert result['student_id'] == student_id
    
    @pytest.mark.asyncio
    async def test_update_mark_success(self, mark_service, mock_repository):
        """Test successful mark update."""
        mark_id = str(uuid4())
        update_data = {'marks_obtained': 90, 'feedback': 'Excellent performance'}
        
        mock_mark = Mock()
        mock_mark.id = mark_id
        mock_mark.dict.return_value = {'id': mark_id, 'marks_obtained': 90, 'feedback': 'Excellent performance'}
        mock_repository.update.return_value = mock_mark
        
        result = await mark_service.update(mark_id, update_data)
        
        mock_repository.update.assert_called_once_with(mark_id, update_data)
        assert result['marks_obtained'] == 90
        assert result['feedback'] == 'Excellent performance'
    
    @pytest.mark.asyncio
    async def test_delete_mark_success(self, mark_service, mock_repository):
        """Test successful mark deletion."""
        mark_id = str(uuid4())
        mock_repository.delete.return_value = True
        
        result = await mark_service.delete(mark_id)
        
        mock_repository.delete.assert_called_once_with(mark_id)
        assert result is True
    
    @pytest.mark.asyncio
    async def test_list_marks_success(self, mark_service, mock_repository):
        """Test successful mark listing."""
        mock_marks = [
            Mock(id=str(uuid4()), marks_obtained=85),
            Mock(id=str(uuid4()), marks_obtained=90)
        ]
        for mark in mock_marks:
            mark.dict = Mock(return_value={'id': mark.id, 'marks_obtained': mark.marks_obtained})
        
        mock_repository.list_all.return_value = QueryResult(success=True, data=mock_marks)
        
        result = await mark_service.list(skip=0, limit=10)
        
        mock_repository.get_all.assert_called_once_with(skip=0, limit=10)
        assert len(result) == 2
        assert all('id' in mark for mark in result)
    
    @pytest.mark.asyncio
    async def test_count_marks_success(self, mark_service, mock_repository):
        """Test mark counting."""
        # Mock count functionality
        mock_repository._count = 42
        mock_repository.count = Mock(return_value=42)
        
        result = await mark_service.count()
        
        mock_repository.count.assert_called_once()
        assert result == 42
    
    # Test Business Logic Methods
    
    @pytest.mark.asyncio
    async def test_get_student_marks_success(self, mark_service, mock_repository):
        """Test successful student mark listing."""
        student_id = 'STU001'
        mock_marks = [Mock(id=str(uuid4()), marks_obtained=85)]
        for mark in mock_marks:
            mark.dict = Mock(return_value={'id': mark.id, 'marks_obtained': mark.marks_obtained})
        
        mock_repository.filter = Mock(return_value=QueryResult(success=True, data=mock_marks))
        
        result = await mark_service.get_student_marks(student_id)
        
        mock_repository.get_by_student.assert_called_once_with(student_id)
        assert len(result) == 1
    
    @pytest.mark.asyncio
    async def test_get_course_marks_success(self, mark_service, mock_repository):
        """Test successful course mark listing."""
        course_id = 'COURSE001'
        mock_marks = [Mock(id=str(uuid4()), marks_obtained=85)]
        for mark in mock_marks:
            mark.dict = Mock(return_value={'id': mark.id, 'marks_obtained': mark.marks_obtained})
        
        mock_repository.filter = Mock(return_value=QueryResult(success=True, data=mock_marks))
        
        result = await mark_service.get_course_marks(course_id)
        
        mock_repository.get_by_course.assert_called_once_with(course_id)
        assert len(result) == 1
    
    @pytest.mark.asyncio
    async def test_get_marks_by_exam_success(self, mark_service, mock_repository):
        """Test successful mark listing by exam."""
        exam_name = 'Midterm Exam'
        mock_marks = [Mock(id=str(uuid4()), marks_obtained=85)]
        for mark in mock_marks:
            mark.dict = Mock(return_value={'id': mark.id, 'marks_obtained': mark.marks_obtained})
        
        mock_repository.get_by_exam.return_value = mock_marks
        
        result = await mark_service.get_marks_by_exam(exam_name)
        
        mock_repository.get_by_exam.assert_called_once_with(exam_name)
        assert len(result) == 1
    
    @pytest.mark.asyncio
    async def test_calculate_average_mark_success(self, mark_service, mock_repository):
        """Test average mark calculation."""
        student_id = 'STU001'
        course_id = 'COURSE001'
        mock_average = 85.5
        
        mock_repository.calculate_average.return_value = mock_average
        
        result = await mark_service.calculate_average_mark(student_id, course_id)
        
        mock_repository.calculate_average.assert_called_once_with(student_id, course_id)
        assert result == mock_average
    
    @pytest.mark.asyncio
    async def test_get_mark_statistics_success(self, mark_service, mock_repository):
        """Test mark statistics calculation."""
        mock_stats = Mock()
        mock_stats.dict.return_value = {
            'total_students': 120,
            'average_marks': 85.5,
            'highest_marks': 98,
            'lowest_marks': 45,
            'grade_distribution': {'A': 30, 'B': 45, 'C': 30, 'D': 10, 'F': 5}
        }
        mock_repository.get_statistics.return_value = mock_stats
        
        result = await mark_service.get_mark_statistics()
        
        mock_repository.get_statistics.assert_called_once()
        assert result['total_students'] == 120
        assert result['average_marks'] == 85.5
    
    @pytest.mark.asyncio
    async def test_grade_assignment_success(self, mark_service, mock_repository):
        """Test grade assignment."""
        mark_id = str(uuid4())
        grade = 'A'
        
        mock_mark = Mock()
        mock_mark.id = mark_id
        mock_mark.grade = grade
        mock_mark.dict.return_value = {'id': mark_id, 'grade': grade}
        mock_repository.assign_grade.return_value = mock_mark
        
        result = await mark_service.assign_grade(mark_id, grade)
        
        mock_repository.assign_grade.assert_called_once_with(mark_id, grade)
        assert result['grade'] == grade
    
    @pytest.mark.asyncio
    async def test_add_feedback_success(self, mark_service, mock_repository):
        """Test feedback addition."""
        mark_id = str(uuid4())
        feedback = 'Good performance, needs improvement in problem-solving'
        
        mock_mark = Mock()
        mock_mark.id = mark_id
        mock_mark.feedback = feedback
        mock_mark.dict.return_value = {'id': mark_id, 'feedback': feedback}
        mock_repository.add_feedback.return_value = mock_mark
        
        result = await mark_service.add_feedback(mark_id, feedback)
        
        mock_repository.add_feedback.assert_called_once_with(mark_id, feedback)
        assert result['feedback'] == feedback
    
    @pytest.mark.asyncio
    async def test_update_mark_status_success(self, mark_service, mock_repository):
        """Test mark status update."""
        mark_id = str(uuid4())
        status = 'released'
        
        mock_mark = Mock()
        mock_mark.id = mark_id
        mock_mark.status = status
        mock_mark.dict.return_value = {'id': mark_id, 'status': status}
        mock_repository.update_status.return_value = mock_mark
        
        result = await mark_service.update_mark_status(mark_id, status)
        
        mock_repository.update_status.assert_called_once_with(mark_id, status)
        assert result['status'] == status
    
    # Test Validation
    
    @pytest.mark.asyncio
    async def test_create_mark_validation_error(self, mark_service, mock_repository, sample_mark_data):
        """Test mark creation with validation error."""
        invalid_data = sample_mark_data.copy()
        invalid_data['marks_obtained'] = 150  # Invalid marks should fail validation
        
        with pytest.raises(ValidationError):
            await mark_service.create(invalid_data)
    
    @pytest.mark.asyncio
    async def test_invalid_percentage_error(self, mark_service, mock_repository, sample_mark_data):
        """Test invalid percentage error."""
        invalid_data = sample_mark_data.copy()
        invalid_data['percentage'] = 150.0  # Invalid percentage should fail validation
        
        with pytest.raises(ValidationError):
            await mark_service.create(invalid_data)
    
    @pytest.mark.asyncio
    async def test_mark_not_found_error(self, mark_service, mock_repository):
        """Test mark not found error."""
        mark_id = str(uuid4())
        mock_repository.get_by_id.return_value = None
        
        with pytest.raises(NotFoundError):
            await mark_service.get_mark(mark_id)
    
    @pytest.mark.asyncio
    async def test_invalid_grade_error(self, mark_service, mock_repository):
        """Test invalid grade error."""
        mark_id = str(uuid4())
        invalid_grade = 'Z'  # Invalid grade should fail validation
        
        with pytest.raises(ValidationError):
            await mark_service.assign_grade(mark_id, invalid_grade)
    
    @pytest.mark.asyncio
    async def test_duplicate_mark_error(self, mark_service, mock_repository, sample_mark_data):
        """Test duplicate mark error."""
        mock_repository.create.side_effect = ConflictError("Mark already exists for this student and course")
        
        with pytest.raises(ConflictError):
            await mark_service.create(sample_mark_data)
    
    # Test Service Lifecycle
    
    @pytest.mark.asyncio
    async def test_service_initialization(self, mark_service):
        """Test service initialization."""
        await mark_service.initialize()
        assert mark_service.is_initialized() is True
    
    @pytest.mark.asyncio
    async def test_service_disposal(self, mark_service):
        """Test service disposal."""
        await mark_service.dispose()
        assert mark_service.is_initialized() is False
    
    # Test Error Handling
    
    @pytest.mark.asyncio
    async def test_database_error_handling(self, mark_service, mock_repository, sample_mark_data):
        """Test database error handling."""
        mock_repository.create.side_effect = DatabaseError("Database connection failed")
        
        with pytest.raises(DatabaseError):
            await mark_service.create(sample_mark_data)
    
    @pytest.mark.asyncio
    async def test_cache_invalidation(self, mark_service, mock_repository):
        """Test cache invalidation."""
        mark_id = str(uuid4())
        mock_repository.get_by_id.return_value = None
        
        # First call
        await mark_service.get_mark(mark_id)
        
        # Second call after cache invalidation
        await mark_service.get_mark(mark_id)
        
        # Should be called twice (cache invalidated)
        assert mock_repository.get_by_id.call_count == 2