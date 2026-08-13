"""
Unit tests for teacher domain services

This module contains unit tests for:
- TeacherService: Teacher management service tests
- QualificationService: Qualification management service tests

Author: Edu-Flow Team
"""

import pytest
from datetime import datetime
from unittest.mock import Mock, AsyncMock, patch

from src.domain.teachers.services import TeacherService, QualificationService
from src.domain.teachers.entities import Teacher, Qualification, EmploymentStatus
from src.infrastructure.exceptions import NotFoundError, ValidationError


class TestTeacherService:
    """Test cases for TeacherService"""
    
    @pytest.fixture
    def teacher_repository(self):
        """Create teacher repository mock"""
        return AsyncMock()
    
    @pytest.fixture
    def qualification_repository(self):
        """Create qualification repository mock"""
        return AsyncMock()
    
    @pytest.fixture
    def teacher_service(self, teacher_repository, qualification_repository):
        """Create teacher service fixture"""
        return TeacherService(teacher_repository, qualification_repository)
    
    @pytest.mark.asyncio
    async def test_create_teacher_success(self, teacher_service, teacher_repository, qualification_repository):
        """Test successful teacher creation"""
        # Mock repository behavior
        teacher_repository.find_by_email.return_value = None  # No existing teacher
        teacher_repository.save.return_value = Teacher(
            id="teacher1",
            teacher_id="TCH001",
            name="John Doe",
            email="john.doe@example.com",
            phone="1234567890",
            hire_date=datetime.now(),
            employment_status=EmploymentStatus.ACTIVE,
            department_id="CS",
            specialization="Programming",
            qualifications=[]
        )
        
        # Test data
        teacher_data = {
            "first_name": "John",
            "last_name": "Doe",
            "email": "john.doe@example.com",
            "phone": "1234567890",
            "department": "Computer Science",
            "specialization": "Programming"
        }
        
        # Execute
        result = await teacher_service.create_teacher(teacher_data)
        
        # Assert
        assert result.name == "John Doe"
        assert result.email == "john.doe@example.com"
        assert result.email == "john.doe@example.com"
        teacher_repository.save.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_create_teacher_missing_required_fields(self, teacher_service, teacher_repository):
        """Test teacher creation with missing required fields"""
        # Test data with missing fields
        teacher_data = {
            "first_name": "",
            "last_name": "Doe"
        }
        
        # Execute and assert
        with pytest.raises(ValidationError, match="Teacher first name and last name are required"):
            await teacher_service.create_teacher(teacher_data)
    
    @pytest.mark.asyncio
    async def test_create_teacher_duplicate_email(self, teacher_service, teacher_repository):
        """Test teacher creation with duplicate email"""
        # Mock existing teacher
        teacher_repository.find_by_email.return_value = Teacher(
            id="existing_teacher",
            teacher_id="TCH001",
            name="Jane Smith",
            email="jane.smith@example.com",
            phone="1234567890",
            hire_date=datetime.now(),
            employment_status=EmploymentStatus.ACTIVE,
            department_id="MATH",
            specialization="Statistics",
            qualifications=[]
        )
        
        # Test data with duplicate email
        teacher_data = {
            "first_name": "Jane",
            "last_name": "Smith",
            "email": "jane.smith@example.com"
        }
        
        # Execute and assert
        with pytest.raises(ValidationError, match="Teacher with this email already exists"):
            await teacher_service.create_teacher(teacher_data)
    
    @pytest.mark.asyncio
    async def test_update_teacher_success(self, teacher_service, teacher_repository):
        """Test successful teacher update"""
        # Mock existing teacher
        existing_teacher = Teacher(
            id="teacher1",
            teacher_id="TCH002",
            name="John Doe",
            email="john.doe@example.com",
            phone="1234567890",
            hire_date=datetime.now(),
            employment_status=EmploymentStatus.ACTIVE,
            department_id="CS",
            specialization="Programming",
            qualifications=[]
        )
        teacher_repository.find_by_id.return_value = existing_teacher
        
        # Mock save behavior
        teacher_repository.save.return_value = existing_teacher
        
        # Test data
        update_data = {
            "first_name": "Jonathan",
            "phone": "9876543210"
        }
        
        # Execute
        result = await teacher_service.update_teacher("teacher1", update_data)
        
        # Assert
        assert result.name == "John Doe"
        assert result.phone == "9876543210"
        teacher_repository.save.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_update_teacher_not_found(self, teacher_service, teacher_repository):
        """Test teacher update with non-existent teacher"""
        # Mock not found
        teacher_repository.find_by_id.return_value = None
        
        # Execute and assert
        with pytest.raises(NotFoundError, match="Teacher with ID teacher1 not found"):
            await teacher_service.update_teacher("teacher1", {"first_name": "John"})
    
    @pytest.mark.asyncio
    async def test_promote_teacher_success(self, teacher_service, teacher_repository):
        """Test successful teacher promotion"""
        # Mock existing teacher
        teacher = Teacher(
            id="teacher1",
            teacher_id="TCH003",
            name="John Doe",
            email="john.doe@example.com",
            phone="1234567890",
            hire_date=datetime.now(),
            employment_status=EmploymentStatus.ACTIVE,
            department_id="CS",
            specialization="Programming",
            qualifications=[]
        )
        teacher_repository.find_by_id.return_value = teacher
        teacher_repository.save.return_value = teacher
        
        # Execute
        result = await teacher_service.promote_teacher("teacher1")
        
        # Assert
        assert result.employment_status == EmploymentStatus.INACTIVE
        assert result.promotion_date is not None
        teacher_repository.save.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_promote_teacher_already_highest(self, teacher_service, teacher_repository):
        """Test promotion of teacher already at highest status"""
        # Mock existing teacher
        teacher = Teacher(
            id="teacher1",
            teacher_id="TCH004",
            name="John Doe",
            email="john.doe@example.com",
            phone="1234567890",
            hire_date=datetime.now(),
            employment_status=EmploymentStatus.RETIRED,  # This should be the highest status
            department_id="CS",
            specialization="Programming",
            qualifications=[]
        )
        teacher_repository.find_by_id.return_value = teacher
        
        # Execute and assert
        with pytest.raises(ValidationError, match="Teacher is already at highest employment status"):
            await teacher_service.promote_teacher("teacher1")


class TestQualificationService:
    """Test cases for QualificationService"""
    
    @pytest.fixture
    def qualification_repository(self):
        """Create qualification repository mock"""
        return AsyncMock()
    
    @pytest.fixture
    def qualification_service(self, qualification_repository):
        """Create qualification service fixture"""
        return QualificationService(qualification_repository)
    
    @pytest.mark.asyncio
    async def test_create_qualification_success(self, qualification_service, qualification_repository):
        """Test successful qualification creation"""
        # Mock repository behavior
        qualification_repository.save.return_value = Qualification(
            id="qual1",
            degree="PhD",
            institution="University",
            year_graduated=2020,
            field_of_study="Computer Science",
            teacher_id="teacher1"
        )
        
        # Test data
        qualification_data = {
            "degree": "PhD",
            "institution": "University",
            "year_graduated": 2020,
            "field_of_study": "Computer Science",
            "teacher_id": "teacher1"
        }
        
        # Execute
        result = await qualification_service.create_qualification(qualification_data)
        
        # Assert
        assert result.degree == "PhD"
        assert result.institution == "University"
        assert result.year_graduated == 2020
        qualification_repository.save.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_create_qualification_missing_required_fields(self, qualification_service):
        """Test qualification creation with missing required fields"""
        # Test data with missing fields
        qualification_data = {
            "degree": "",
            "institution": "University"
        }
        
        # Execute and assert
        with pytest.raises(ValidationError, match="Degree and institution are required"):
            await qualification_service.create_qualification(qualification_data)
    
    @pytest.mark.asyncio
    async def test_get_qualification_by_id(self, qualification_service, qualification_repository):
        """Test getting qualification by ID"""
        # Mock repository behavior
        qualification = Qualification(
            id="qual1",
            degree="PhD",
            institution="University",
            year_graduated=2020,
            field_of_study="Computer Science",
            teacher_id="teacher1"
        )
        qualification_repository.find_by_id.return_value = qualification
        
        # Execute
        result = await qualification_service.get_qualification_by_id("qual1")
        
        # Assert
        assert result.id == "qual1"
        assert result.degree == "PhD"
        qualification_repository.find_by_id.assert_called_once_with("qual1")
    
    @pytest.mark.asyncio
    async def test_get_qualification_not_found(self, qualification_service, qualification_repository):
        """Test getting non-existent qualification"""
        # Mock not found
        qualification_repository.find_by_id.return_value = None
        
        # Execute
        result = await qualification_service.get_qualification_by_id("qual1")
        
        # Assert
        assert result is None
        qualification_repository.find_by_id.assert_called_once_with("qual1")