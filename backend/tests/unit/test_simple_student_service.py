"""
Simple Student Service Tests

This module provides simplified unit tests for the StudentService class
using a basic mock that doesn't rely on the complex dataclass structure.

Author: Edu-Flow Team
"""

import pytest
import uuid
from datetime import datetime, date, time
from typing import Dict, List, Any, Optional

from src.models.student import StudentResponse, UserRole, GradeLevel
from src.models.student_stats import StudentStats
from src.services.student_service import StudentService
from src.core.exceptions import NotFoundError, ValidationError, DatabaseError, ConflictError


class SimpleStudentRepository:
    """Simple student repository for testing."""
    
    def __init__(self):
        self.students = {}
        self.next_id = 1
    
    async def create(self, student_data: Dict[str, Any]) -> StudentResponse:
        """Create a new student."""
        student_id = str(self.next_id)
        self.next_id += 1
        
        student = StudentResponse(
            id=student_id,
            name=student_data.get('name', ''),
            email=student_data.get('email', ''),
            student_id=student_data.get('student_id', ''),
            phone=student_data.get('phone', ''),
            department_id=student_data.get('department_id', ''),
            gpa=student_data.get('gpa', 0.0),
            enrollment_date=student_data.get('enrollment_date', datetime.now().date()),
            grade_level=GradeLevel.TENTH,
            role=UserRole.STUDENT,
            is_active=True,
            created_at=datetime.now(),
            updated_at=datetime.now()
        )
        
        self.students[student_id] = student
        return student
    
    async def get_by_id(self, student_id: str) -> Optional[StudentResponse]:
        """Get a student by ID."""
        return self.students.get(student_id)
    
    async def get_all(self, skip: int = 0, limit: int = 100) -> List[StudentResponse]:
        """Get all students."""
        students = list(self.students.values())
        return students[skip:skip + limit]
    
    async def update(self, student_id: str, student_data: Dict[str, Any]) -> Optional[StudentResponse]:
        """Update a student."""
        student = self.students.get(student_id)
        if student:
            for key, value in student_data.items():
                if hasattr(student, key):
                    setattr(student, key, value)
            return student
        return None
    
    async def delete(self, student_id: str) -> bool:
        """Delete a student."""
        if student_id in self.students:
            del self.students[student_id]
            return True
        return False
    
    async def get_by_department(self, department_id: str) -> List[StudentResponse]:
        """Get students by department."""
        return [student for student in self.students.values() 
                if student.department_id == department_id]
    
    async def get_by_status(self, status: str) -> List[StudentResponse]:
        """Get students by status."""
        return [student for student in self.students.values() 
                if student.status == status]
    
    async def get_statistics(self) -> StudentStats:
        """Get student statistics."""
        if not self.students:
            return StudentStats(total=0, active=0, inactive=0, average_gpa=0.0)
        
        total = len(self.students)
        active = len([s for s in self.students.values() if s.status == 'active'])
        inactive = total - active
        
        gpa_sum = sum(s.gpa for s in self.students.values())
        average_gpa = gpa_sum / total if total > 0 else 0.0
        
        return StudentStats(
            total=total,
            active=active,
            inactive=inactive,
            average_gpa=average_gpa
        )
    
    async def search(self, query: str) -> List[StudentResponse]:
        """Search students by name or email."""
        query = query.lower()
        return [student for student in self.students.values()
                if query in student.name.lower() or query in student.email.lower()]


@pytest.fixture
def student_repository():
    """Create a simple student repository."""
    return SimpleStudentRepository()


@pytest.fixture
def student_service(student_repository):
    """Create a student service with a simple repository."""
    return StudentService(repository=student_repository)


class TestSimpleStudentService:
    """Simple student service tests."""
    
    def test_create_student(self, student_service):
        """Test creating a student."""
        student_data = {
            'name': 'John Doe',
            'email': 'john@example.com',
            'student_id': 'S001',
            'phone': '123-456-7890',
            'address': '123 Main St',
            'gender': 'Male',
            'birth_date': '1990-01-01',
            'enrollment_date': '2020-01-01',
            'department_id': 'D001',
            'gpa': 3.5,
            'status': 'active'
        }
        
        result = student_service.create_student(student_data)
        
        assert result.id is not None
        assert result.name == 'John Doe'
        assert result.email == 'john@example.com'
        assert result.student_id == 'S001'
        assert result.gpa == 3.5
        assert result.status == 'active'
    
    def test_get_student(self, student_service):
        """Test getting a student by ID."""
        # Create a student first
        student_data = {
            'name': 'Jane Smith',
            'email': 'jane@example.com',
            'student_id': 'S002',
            'phone': '987-654-3210',
            'address': '456 Oak St',
            'gender': 'Female',
            'birth_date': '1992-02-02',
            'enrollment_date': '2020-02-02',
            'department_id': 'D001',
            'gpa': 3.8,
            'status': 'active'
        }
        
        created_student = student_service.create_student(student_data)
        student_id = created_student.id
        
        # Get the student
        retrieved_student = student_service.get_student(student_id)
        
        assert retrieved_student is not None
        assert retrieved_student.id == student_id
        assert retrieved_student.name == 'Jane Smith'
        assert retrieved_student.email == 'jane@example.com'
    
    def test_get_student_not_found(self, student_service):
        """Test getting a student that doesn't exist."""
        with pytest.raises(NotFoundError):
            student_service.get_student('nonexistent')
    
    def test_update_student(self, student_service):
        """Test updating a student."""
        # Create a student first
        student_data = {
            'name': 'Bob Johnson',
            'email': 'bob@example.com',
            'student_id': 'S003',
            'phone': '555-123-4567',
            'address': '789 Pine St',
            'gender': 'Male',
            'birth_date': '1993-03-03',
            'enrollment_date': '2020-03-03',
            'department_id': 'D001',
            'gpa': 3.2,
            'status': 'active'
        }
        
        created_student = student_service.create_student(student_data)
        student_id = created_student.id
        
        # Update the student
        update_data = {
            'name': 'Robert Johnson',
            'gpa': 3.7,
            'status': 'graduated'
        }
        
        updated_student = student_service.update_student(student_id, update_data)
        
        assert updated_student is not None
        assert updated_student.name == 'Robert Johnson'
        assert updated_student.gpa == 3.7
        assert updated_student.status == 'graduated'
    
    def test_delete_student(self, student_service):
        """Test deleting a student."""
        # Create a student first
        student_data = {
            'name': 'Alice Brown',
            'email': 'alice@example.com',
            'student_id': 'S004',
            'phone': '444-123-4567',
            'address': '321 Elm St',
            'gender': 'Female',
            'birth_date': '1994-04-04',
            'enrollment_date': '2020-04-04',
            'department_id': 'D001',
            'gpa': 3.9,
            'status': 'active'
        }
        
        created_student = student_service.create_student(student_data)
        student_id = created_student.id
        
        # Delete the student
        result = student_service.delete_student(student_id)
        assert result is True
        
        # Verify the student is gone
        with pytest.raises(NotFoundError):
            student_service.get_student(student_id)
    
    def test_get_students_by_department(self, student_service):
        """Test getting students by department."""
        # Create students in different departments
        students_data = [
            {
                'name': 'Student 1',
                'email': 's1@example.com',
                'student_id': 'S101',
                'department_id': 'D001',
                'gpa': 3.5
            },
            {
                'name': 'Student 2',
                'email': 's2@example.com',
                'student_id': 'S102',
                'department_id': 'D001',
                'gpa': 3.2
            },
            {
                'name': 'Student 3',
                'email': 's3@example.com',
                'student_id': 'S103',
                'department_id': 'D002',
                'gpa': 3.8
            }
        ]
        
        for data in students_data:
            student_service.create_student(data)
        
        # Get students by department D001
        d001_students = student_service.get_students_by_department('D001')
        assert len(d001_students) == 2
        
        # Get students by department D002
        d002_students = student_service.get_students_by_department('D002')
        assert len(d002_students) == 1
        assert d002_students[0].name == 'Student 3'
    
    def test_get_student_statistics(self, student_service):
        """Test getting student statistics."""
        # Create students with different statuses and GPAs
        students_data = [
            {
                'name': 'Student 1',
                'email': 's1@example.com',
                'student_id': 'S101',
                'department_id': 'D001',
                'gpa': 3.5,
                'status': 'active'
            },
            {
                'name': 'Student 2',
                'email': 's2@example.com',
                'student_id': 'S102',
                'department_id': 'D001',
                'gpa': 3.2,
                'status': 'active'
            },
            {
                'name': 'Student 3',
                'email': 's3@example.com',
                'student_id': 'S103',
                'department_id': 'D001',
                'gpa': 2.8,
                'status': 'inactive'
            }
        ]
        
        for data in students_data:
            student_service.create_student(data)
        
        # Get statistics
        stats = student_service.get_student_statistics()
        
        assert stats.total == 3
        assert stats.active == 2
        assert stats.inactive == 1
        assert stats.average_gpa == (3.5 + 3.2 + 2.8) / 3
    
    def test_search_students(self, student_service):
        """Test searching students."""
        # Create students with different names
        students_data = [
            {
                'name': 'John Smith',
                'email': 'john@example.com',
                'student_id': 'S201'
            },
            {
                'name': 'Jane Smith',
                'email': 'jane@example.com',
                'student_id': 'S202'
            },
            {
                'name': 'John Doe',
                'email': 'john.doe@example.com',
                'student_id': 'S203'
            }
        ]
        
        for data in students_data:
            student_service.create_student(data)
        
        # Search for students with "Smith"
        smith_students = student_service.search_students('Smith')
        assert len(smith_students) == 2
        
        # Search for students with "John"
        john_students = student_service.search_students('John')
        assert len(john_students) == 2
        
        # Search for students with "nonexistent"
        none_students = student_service.search_students('nonexistent')
        assert len(none_students) == 0
    
    def test_validation_errors(self, student_service):
        """Test validation errors."""
        # Test missing required fields
        incomplete_data = {
            'name': 'Test Student',
            # Missing email and other required fields
        }
        
        with pytest.raises(ValidationError):
            student_service.create_student(incomplete_data)
        
        # Test invalid GPA
        invalid_gpa_data = {
            'name': 'Test Student',
            'email': 'test@example.com',
            'student_id': 'S301',
            'gpa': 5.0  # Invalid GPA (should be <= 4.0)
        }
        
        with pytest.raises(ValidationError):
            student_service.create_student(invalid_gpa_data)