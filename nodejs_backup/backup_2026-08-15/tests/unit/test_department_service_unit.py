"""
Department Service Unit Tests

This module provides comprehensive unit tests for the DepartmentService class.
It tests all CRUD operations, validation, error handling, and business logic.

Author: Edu-Flow Team
"""

import pytest
import asyncio
from datetime import datetime, date
from uuid import uuid4
from unittest.mock import Mock, AsyncMock, patch

from src.core.exceptions import NotFoundError, ValidationError, DatabaseError, ConflictError
from src.infrastructure.services.department_service import DepartmentService
from src.infrastructure.repositories.department_repository import DepartmentRepository
from src.infrastructure.repositories.base_repository import QueryResult
from tests.mock_database_manager import MockDatabaseManager


class TestDepartmentServiceUnit:
    """Comprehensive unit tests for DepartmentService."""
    
    @pytest.fixture
    def mock_repository(self):
        """Create mock department repository."""
        return Mock(spec=DepartmentRepository)
    
    @pytest.fixture
    def department_service(self, mock_repository):
        """Create department service with mock repository."""
        return DepartmentService(mock_repository)
    
    @pytest.fixture
    def sample_department_data(self):
        """Sample department data for testing."""
        return {
            'name': 'Computer Science',
            'department_code': 'CS',
            'description': 'Department of Computer Science',
            'faculty_id': 'FAC001',
            'head_id': 'TCH001',
            'head_of_department': 'TCH001',
            'established_date': '2020-01-01',
            'location': 'Engineering Building A',
            'contact_email': 'cs@university.edu',
            'contact_phone': '+1234567890',
            'website': 'https://cs.university.edu',
            'status': 'active'
        }
    
    # Test CRUD Operations
    
    @pytest.mark.asyncio
    async def test_create_department_success(self, department_service, mock_repository, sample_department_data):
        """Test successful department creation."""
        mock_repository.create.return_value = AsyncMock()
        mock_repository.create.return_value.id = str(uuid4())
        mock_repository.create.return_value.dict.return_value = {
            'id': str(uuid4()),
            **sample_department_data
        }
        
        result = await department_service.create(sample_department_data)
        
        mock_repository.create.assert_called_once_with(sample_department_data)
        assert result['name'] == sample_department_data['name']
        assert result['code'] == sample_department_data['code']
    
    @pytest.mark.asyncio
    async def test_get_department_success(self, department_service, mock_repository):
        """Test successful department retrieval."""
        dept_id = str(uuid4())
        mock_department = Mock()
        mock_department.id = dept_id
        mock_department.dict.return_value = {'id': dept_id, 'name': 'Computer Science'}
        mock_repository.get_by_id.return_value = mock_department
        
        result = await department_service.get(dept_id)
        
        mock_repository.get_by_id.assert_called_once_with(dept_id)
        assert result is not None
        assert result['id'] == dept_id
    
    @pytest.mark.asyncio
    async def test_get_department_by_code_success(self, department_service, mock_repository):
        """Test successful department retrieval by code."""
        dept_code = 'CS'
        mock_department = Mock()
        mock_department.id = str(uuid4())
        mock_department.dict.return_value = {'id': mock_department.id, 'code': dept_code}
        mock_repository.get_by_id = Mock(return_value=QueryResult(success=True, data=mock_department))
        
        result = await department_service.get_department_by_code(dept_code)
        
        mock_repository.get_by_code.assert_called_once_with(dept_code)
        assert result is not None
        assert result['code'] == dept_code
    
    @pytest.mark.asyncio
    async def test_update_department_success(self, department_service, mock_repository):
        """Test successful department update."""
        dept_id = str(uuid4())
        update_data = {'name': 'Department of Computer Science and Engineering'}
        
        mock_department = Mock()
        mock_department.id = dept_id
        mock_department.dict.return_value = {'id': dept_id, 'name': 'Department of Computer Science and Engineering'}
        mock_repository.update.return_value = mock_department
        
        result = await department_service.update(dept_id, update_data)
        
        mock_repository.update.assert_called_once_with(dept_id, update_data)
        assert result['name'] == 'Department of Computer Science and Engineering'
    
    @pytest.mark.asyncio
    async def test_delete_department_success(self, department_service, mock_repository):
        """Test successful department deletion."""
        dept_id = str(uuid4())
        mock_repository.delete.return_value = True
        
        result = await department_service.delete(dept_id)
        
        mock_repository.delete.assert_called_once_with(dept_id)
        assert result is True
    
    @pytest.mark.asyncio
    async def test_list_departments_success(self, department_service, mock_repository):
        """Test successful department listing."""
        mock_departments = [
            Mock(id=str(uuid4()), name='Computer Science'),
            Mock(id=str(uuid4()), name='Mathematics')
        ]
        for dept in mock_departments:
            dept.dict = Mock(return_value={'id': dept.id, 'name': dept.name})
        
        mock_repository.list_all.return_value = QueryResult(success=True, data=mock_departments)
        
        result = await department_service.list(skip=0, limit=10)
        
        mock_repository.get_all.assert_called_once_with(skip=0, limit=10)
        assert len(result) == 2
        assert all('id' in dept for dept in result)
    
    @pytest.mark.asyncio
    async def test_count_departments_success(self, department_service, mock_repository):
        """Test department counting."""
        # Mock count functionality
        mock_repository._count = 42
        mock_repository.count = Mock(return_value=42)
        
        result = await department_service.count()
        
        mock_repository.count.assert_called_once()
        assert result == 42
    
    # Test Business Logic Methods
    
    @pytest.mark.asyncio
    async def test_get_departments_by_head_success(self, department_service, mock_repository):
        """Test successful department listing by head."""
        head_id = 'TCH001'
        mock_departments = [Mock(id=str(uuid4()), name='Computer Science')]
        for dept in mock_departments:
            dept.dict = Mock(return_value={'id': dept.id, 'name': dept.name})
        
        mock_repository.filter = Mock(return_value=QueryResult(success=True, data=mock_departments))
        
        result = await department_service.get_departments_by_head(head_id)
        
        mock_repository.get_by_head.assert_called_once_with(head_id)
        assert len(result) == 1
    
    @pytest.mark.asyncio
    async def test_get_active_departments_success(self, department_service, mock_repository):
        """Test successful active department listing."""
        mock_departments = [Mock(id=str(uuid4()), name='Active Department')]
        for dept in mock_departments:
            dept.dict = Mock(return_value={'id': dept.id, 'name': dept.name})
        
        mock_repository.filter = Mock(return_value=QueryResult(success=True, data=mock_departments))
        
        result = await department_service.get_active_departments()
        
        mock_repository.get_active.assert_called_once()
        assert len(result) == 1
    
    @pytest.mark.asyncio
    async def test_get_department_statistics_success(self, department_service, mock_repository):
        """Test department statistics calculation."""
        dept_id = str(uuid4())
        mock_stats = Mock()
        mock_stats.dict.return_value = {
            'total_students': 150,
            'total_teachers': 25,
            'total_courses': 45,
            'total_classes': 60
        }
        mock_repository.get_department_statistics.return_value = mock_stats
        
        result = await department_service.get_department_statistics(dept_id)
        
        mock_repository.get_department_statistics.assert_called_once_with(dept_id)
        assert result['total_students'] == 150
    
    @pytest.mark.asyncio
    async def test_search_departments_success(self, department_service, mock_repository):
        """Test successful department search."""
        search_term = 'computer'
        mock_departments = [Mock(id=str(uuid4()), name='Computer Science')]
        for dept in mock_departments:
            dept.dict = Mock(return_value={'id': dept.id, 'name': dept.name})
        
        mock_repository.search.return_value = mock_departments
        
        result = await department_service.search_departments(search_term)
        
        mock_repository.search.assert_called_once_with(search_term)
        assert len(result) == 1
    
    # Test Validation
    
    @pytest.mark.asyncio
    async def test_create_department_validation_error(self, department_service, mock_repository, sample_department_data):
        """Test department creation with validation error."""
        invalid_data = sample_department_data.copy()
        invalid_data['name'] = ''  # Empty name should fail validation
        
        with pytest.raises(ValidationError):
            await department_service.create_department(invalid_data)
    
    @pytest.mark.asyncio
    async def test_duplicate_department_code_error(self, department_service, mock_repository, sample_department_data):
        """Test duplicate department code error."""
        mock_repository.create.side_effect = ConflictError("Department code already exists")
        
        with pytest.raises(ConflictError):
            await department_service.create_department(sample_department_data)
    
    @pytest.mark.asyncio
    async def test_department_not_found_error(self, department_service, mock_repository):
        """Test department not found error."""
        dept_id = str(uuid4())
        mock_repository.get_by_id.return_value = QueryResult(success=True, data=None)
        
        with pytest.raises(NotFoundError):
            await department_service.get_department(dept_id)
    
    @pytest.mark.asyncio
    async def test_invalid_department_code_error(self, department_service, mock_repository):
        """Test invalid department code error."""
        invalid_data = {
            'name': 'Department',
            'code': 'INVALID@CODE',  # Invalid format should fail validation
            'description': 'Test department'
        }
        
        with pytest.raises(ValidationError):
            await department_service.create_department(invalid_data)
    
    # Test Service Lifecycle
    
    @pytest.mark.asyncio
    async def test_service_initialization(self, department_service):
        """Test service initialization."""
        await department_service.initialize()
        assert department_service.is_initialized() is True
    
    @pytest.mark.asyncio
    async def test_service_disposal(self, department_service):
        """Test service disposal."""
        await department_service.dispose()
        assert department_service.is_initialized() is False
    
    # Test Error Handling
    
    @pytest.mark.asyncio
    async def test_database_error_handling(self, department_service, mock_repository, sample_department_data):
        """Test database error handling."""
        mock_repository.create.side_effect = DatabaseError("Database connection failed")
        
        with pytest.raises(DatabaseError):
            await department_service.create_department(sample_department_data)
    
    @pytest.mark.asyncio
    async def test_cache_invalidation(self, department_service, mock_repository):
        """Test cache invalidation."""
        dept_id = str(uuid4())
        mock_repository.get_by_id.return_value = QueryResult(success=True, data=None)
        
        # First call
        await department_service.get_department(dept_id)
        
        # Second call after cache invalidation
        await department_service.get_department(dept_id)
        
        # Should be called twice (cache invalidated)
        assert mock_repository.get_by_id.call_count == 2
    
    # Test Complex Business Logic
    
    @pytest.mark.asyncio
    async def test_get_department_hierarchy_success(self, department_service, mock_repository):
        """Test department hierarchy retrieval."""
        dept_id = str(uuid4())
        mock_hierarchy = Mock()
        mock_hierarchy.dict.return_value = {
            'department_id': dept_id,
            'parent_department': None,
            'sub_departments': [
                {'id': str(uuid4()), 'name': 'Sub Dept 1'},
                {'id': str(uuid4()), 'name': 'Sub Dept 2'}
            ]
        }
        mock_repository.get_hierarchy.return_value = mock_hierarchy
        
        result = await department_service.get_department_hierarchy(dept_id)
        
        mock_repository.get_hierarchy.assert_called_once_with(dept_id)
        assert result['department_id'] == dept_id
        assert len(result['sub_departments']) == 2
    
    @pytest.mark.asyncio
    async def test_validate_department_head_assignment_success(self, department_service, mock_repository):
        """Test department head assignment validation."""
        dept_id = str(uuid4())
        teacher_id = 'TCH001'
        
        mock_repository.validate_head_assignment.return_value = True
        
        result = await department_service.validate_department_head_assignment(dept_id, teacher_id)
        
        mock_repository.validate_head_assignment.assert_called_once_with(dept_id, teacher_id)
        assert result is True
    
    @pytest.mark.asyncio
    async def test_get_department_audit_log_success(self, department_service, mock_repository):
        """Test department audit log retrieval."""
        dept_id = str(uuid4())
        mock_audit_logs = [
            Mock(id=str(uuid4()), action='created', timestamp=datetime.now()),
            Mock(id=str(uuid4()), action='updated', timestamp=datetime.now())
        ]
        for log in mock_audit_logs:
            log.dict = Mock(return_value={'id': log.id, 'action': log.action})
        
        mock_repository.get_audit_log.return_value = mock_audit_logs
        
        result = await department_service.get_department_audit_log(dept_id)
        
        mock_repository.get_audit_log.assert_called_once_with(dept_id)
        assert len(result) == 2
    
    # Test Performance Methods
    
    @pytest.mark.asyncio
    async def test_get_department_performance_metrics_success(self, department_service, mock_repository):
        """Test department performance metrics retrieval."""
        dept_id = str(uuid4())
        mock_metrics = Mock()
        mock_metrics.dict.return_value = {
            'completion_rate': 0.85,
            'student_retention': 0.92,
            'faculty_productivity': 0.78,
            'resource_utilization': 0.88
        }
        mock_repository.get_performance_metrics.return_value = mock_metrics
        
        result = await department_service.get_department_performance_metrics(dept_id)
        
        mock_repository.get_performance_metrics.assert_called_once_with(dept_id)
        assert result['completion_rate'] == 0.85