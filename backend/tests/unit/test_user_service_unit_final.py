"""
User Service Unit Tests

This module provides comprehensive unit tests for the UserService class.
It tests validation and core functionality.

Author: Edu-Flow Team
"""

import pytest
from datetime import datetime
from uuid import uuid4
from unittest.mock import Mock, AsyncMock, patch

from src.core.exceptions import NotFoundError, ValidationError, DatabaseError, ConflictError
from src.services.user_service import UserService


class TestUserServiceUnit:
    """Comprehensive unit tests for UserService."""
    
    @pytest.fixture
    def mock_db_manager(self):
        """Mock database manager for testing."""
        mock_db = Mock()
        mock_db.execute_query = Mock(return_value=[])
        mock_db.execute_update = Mock(return_value=1)
        return mock_db
    
    @pytest.fixture
    def user_service(self, mock_db_manager):
        """Create user service instance with mocked database."""
        with patch('src.services.user_service.db_manager', mock_db_manager):
            service = UserService()
            return service
    
    # Test Validation Methods
    def test_validate_email_valid(self, user_service):
        """Test valid email validation."""
        assert user_service.validate_email("test@example.com") == True
        assert user_service.validate_email("user.name@domain.co.uk") == True
    
    def test_validate_email_invalid(self, user_service):
        """Test invalid email validation."""
        assert user_service.validate_email("invalid-email") == False
        assert user_service.validate_email("@domain.com") == False
        assert user_service.validate_email("user@") == False
    
    def test_validate_password_valid(self, user_service):
        """Test valid password validation."""
        assert user_service.validate_password("Password123!") == True
        assert user_service.validate_password("SecurePass456@") == True
    
    def test_validate_password_invalid(self, user_service):
        """Test invalid password validation."""
        assert user_service.validate_password("short") == False
        assert user_service.validate_password("password") == False
        assert user_service.validate_password("PASSWORD123") == False
        assert user_service.validate_password("password123") == False
    
    def test_validate_role_valid(self, user_service):
        """Test valid role validation."""
        assert user_service.validate_role("student") == True
        assert user_service.validate_role("teacher") == True
        assert user_service.validate_role("admin") == True
        assert user_service.validate_role("staff") == True
    
    def test_validate_role_invalid(self, user_service):
        """Test invalid role validation."""
        assert user_service.validate_role("invalid_role") == False
        assert user_service.validate_role("") == False
    
    # Test User Creation
    @pytest.mark.asyncio
    async def test_create_user_success(self, user_service):
        """Test successful user creation."""
        user_data = {
            'email': 'john.doe@example.com',
            'password': 'Password123!',
            'name': 'John Doe',
            'role': 'student'
        }
        
        result = await user_service.create_user(**user_data)
        
        assert result is not None
        assert result['email'] == user_data['email']
        assert result['name'] == user_data['name']
        assert result['role'] == user_data['role']
        assert 'user_id' in result
    
    @pytest.mark.asyncio
    async def test_create_user_invalid_email(self, user_service):
        """Test user creation with invalid email."""
        user_data = {
            'email': 'invalid-email',
            'password': 'Password123!',
            'name': 'John Doe',
            'role': 'student'
        }
        
        with pytest.raises(ValidationError):
            await user_service.create_user(**user_data)
    
    @pytest.mark.asyncio
    async def test_create_user_weak_password(self, user_service):
        """Test user creation with weak password."""
        user_data = {
            'email': 'john.doe@example.com',
            'password': 'weak',
            'name': 'John Doe',
            'role': 'student'
        }
        
        with pytest.raises(ValidationError):
            await user_service.create_user(**user_data)
    
    @pytest.mark.asyncio
    async def test_create_user_invalid_role(self, user_service):
        """Test user creation with invalid role."""
        user_data = {
            'email': 'john.doe@example.com',
            'password': 'Password123!',
            'name': 'John Doe',
            'role': 'invalid_role'
        }
        
        with pytest.raises(ValidationError):
            await user_service.create_user(**user_data)
    
    # Test User Retrieval
    @pytest.mark.asyncio
    async def test_get_user_by_email_success(self, user_service):
        """Test successful user retrieval by email."""
        user_data = {
            'email': 'john.doe@example.com',
            'password': 'Password123!',
            'name': 'John Doe',
            'role': 'student'
        }
        
        # Create user first
        created_user = await user_service.create_user(**user_data)
        
        # Get user by email
        result = await user_service.get_user_by_email(user_data['email'])
        
        assert result is not None
        assert result['user_id'] == created_user['user_id']
        assert result['email'] == user_data['email']
    
    @pytest.mark.asyncio
    async def test_get_user_by_email_not_found(self, user_service):
        """Test user retrieval with non-existent email."""
        result = await user_service.get_user_by_email('nonexistent@example.com')
        assert result is None  # Method should return None for non-existent emails, not raise an exception
    
    @pytest.mark.asyncio
    async def test_get_user_success(self, user_service):
        """Test successful user retrieval by ID."""
        user_data = {
            'email': 'john.doe@example.com',
            'password': 'Password123!',
            'name': 'John Doe',
            'role': 'student'
        }
        
        # Create user first
        created_user = await user_service.create_user(**user_data)
        user_id = created_user['user_id']
        
        # Get user
        result = await user_service.get_user(user_id)
        
        assert result is not None
        assert result['user_id'] == user_id
        assert result['email'] == user_data['email']
    
    @pytest.mark.asyncio
    async def test_get_user_not_found(self, user_service):
        """Test user retrieval with non-existent ID."""
        mock_db = AsyncMock()
        mock_db.execute_query.return_value = []
        with patch('src.services.user_service.db_manager', mock_db):
            with pytest.raises(NotFoundError):
                await user_service.get_user(str(uuid4()))
    
    # Test User Updates
    @pytest.mark.asyncio
    async def test_update_user_success(self, user_service):
        """Test successful user update."""
        user_data = {
            'email': 'john.doe@example.com',
            'password': 'Password123!',
            'name': 'John Doe',
            'role': 'student'
        }
        
        # Create user first
        created_user = await user_service.create_user(**user_data)
        user_id = created_user['user_id']
        
        # Update user
        update_data = {'name': 'John Updated Doe', 'role': 'teacher'}
        result = user_service.update_user(user_id, **update_data)
        
        assert result is not None
        assert result['name'] == 'John Updated Doe'
        assert result['role'] == 'teacher'
        assert result['email'] == user_data['email']
    
    def test_update_user_not_found(self, user_service):
        """Test user update with non-existent ID."""
        with pytest.raises(NotFoundError):
            user_service.update_user(str(uuid4()), name='Updated Name')
    
    # Test User Role Changes
    @pytest.mark.asyncio
    async def test_change_user_role_success(self, user_service):
        """Test successful user role change."""
        user_data = {
            'email': 'john.doe@example.com',
            'password': 'Password123!',
            'name': 'John Doe',
            'role': 'student'
        }
        
        # Create user first
        created_user = await user_service.create_user(**user_data)
        user_id = created_user['user_id']
        
        # Change user role
        result = user_service.change_user_role(user_id, 'teacher')
        
        assert result is not None
        assert result['role'] == 'teacher'
    
    def test_change_user_role_not_found(self, user_service):
        """Test user role change with non-existent ID."""
        with pytest.raises(NotFoundError):
            user_service.change_user_role(str(uuid4()), 'teacher')
    
    # Test User Deletion
    @pytest.mark.asyncio
    async def test_delete_user_success(self, user_service):
        """Test successful user deletion."""
        user_data = {
            'email': 'john.doe@example.com',
            'password': 'Password123!',
            'name': 'John Doe',
            'role': 'student'
        }
        
        # Create user first
        created_user = await user_service.create_user(**user_data)
        user_id = created_user['user_id']
        
        # Delete user
        result = user_service.delete_user(user_id)
        
        assert result is not None
        assert result['user_id'] == user_id
        assert result['is_active'] == False
        
        # Verify user is deactivated but still exists
        deactivated_user = await user_service.get_user(user_id)
        assert deactivated_user['is_active'] == False
    
    def test_delete_user_not_found(self, user_service):
        """Test user deletion with non-existent ID."""
        with pytest.raises(NotFoundError):
            user_service.delete_user(str(uuid4()))
    
    # Test Search Functionality
    @pytest.mark.asyncio
    async def test_search_users_empty_query(self, user_service):
        """Test search users with empty query."""
        # Create a test user
        user_data = {
            'email': 'john.doe@example.com',
            'password': 'Password123!',
            'name': 'John Doe',
            'role': 'student'
        }
        await user_service.create_user(**user_data)
        
        # Search with empty query
        results = user_service.search_users()
        
        assert len(results) >= 1
        assert any(user['email'] == user_data['email'] for user in results)
    
    @pytest.mark.asyncio
    async def test_search_users_by_role(self, user_service):
        """Test search users by role."""
        # Create students
        for i in range(3):
            user_data = {
                'email': f'student{i}@example.com',
                'password': 'Password123!',
                'name': f'Student {i}',
                'role': 'student'
            }
            await user_service.create_user(**user_data)
        
        # Create teacher
        teacher_data = {
            'email': 'teacher@example.com',
            'password': 'Password123!',
            'name': 'Teacher Smith',
            'role': 'teacher'
        }
        await user_service.create_user(**teacher_data)
        
        # Search by role
        results = user_service.search_users(role='student')
        
        assert len(results) == 3
        assert all(user['role'] == 'student' for user in results)
    
    @pytest.mark.asyncio
    async def test_get_user_count(self, user_service):
        """Test get user count."""
        # Create users
        for i in range(5):
            user_data = {
                'email': f'user{i}@example.com',
                'password': 'Password123!',
                'name': f'User {i}',
                'role': 'student'
            }
            await user_service.create_user(**user_data)
        
        count = user_service.get_user_count()
        
        assert count >= 5
    
    @pytest.mark.asyncio
    async def test_get_user_count_by_role(self, user_service):
        """Test get user count by role."""
        # Create students
        for i in range(3):
            user_data = {
                'email': f'student{i}@example.com',
                'password': 'Password123!',
                'name': f'Student {i}',
                'role': 'student'
            }
            await user_service.create_user(**user_data)
        
        # Create teachers
        for i in range(2):
            user_data = {
                'email': f'teacher{i}@example.com',
                'password': 'Password123!',
                'name': f'Teacher {i}',
                'role': 'teacher'
            }
            await user_service.create_user(**user_data)
        
        student_count = user_service.get_user_count(role='student')
        teacher_count = user_service.get_user_count(role='teacher')
        
        assert student_count == 3
        assert teacher_count == 2