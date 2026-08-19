"""
Actual Student Service Tests

This module provides unit tests for the actual StudentService class.
It tests the service using its internal data storage system.

Author: Edu-Flow Team
"""

import pytest
import uuid
from datetime import datetime, date, time
from typing import Dict, List, Any, Optional

from src.services.student_service import StudentService
from src.models.student import StudentCreate, StudentUpdate, StudentResponse
from src.models.student_stats import StudentStats
from src.core.exceptions import NotFoundError, ValidationError, DatabaseError, ConflictError


@pytest.fixture
def student_service():
    """Create a student service instance."""
    return StudentService()


class TestActualStudentService:
    """Actual student service tests."""
    
    def test_create_student(self, student_service):
        """Test creating a student."""
        student_data = {
            "email": "john@example.com",
            "password": "Password123",
            "name": "John Doe",
            "phone": "123-456-7890",
            "address": "123 Main St",
            "student_id": "S001",
            "enrollment_date": date(2020, 1, 1),
            "grade_level": 10,
            "department_id": "D001",
            "gpa": 3.5
        }
        
        result = student_service.create_student(student_data)
        
        assert result.id is not None
        assert result.name == "John Doe"
        assert result.email == "john@example.com"
        assert result.student_id == "S001"
        assert result.gpa == 3.5
        assert result.is_active is True
    
    def test_get_student(self, student_service):
        """Test getting a student by ID."""
        # Create a student first
        student_data = {
            "email": "jane@example.com",
            "password": "Password123",
            "name": "Jane Smith",
            "phone": "987-654-3210",
            "address": "456 Oak St",
            "student_id": "S002",
            "enrollment_date": date(2020, 2, 2),
            "grade_level": 11,
            "department_id": "D001",
            "gpa": 3.8
        }
        
        created_student = student_service.create_student(student_data)
        student_id = created_student.id
        
        # Get the student
        retrieved_student = student_service.get_student(student_id)
        
        assert retrieved_student is not None
        assert retrieved_student.id == student_id
        assert retrieved_student.name == "Jane Smith"
        assert retrieved_student.email == "jane@example.com"
    
    def test_get_student_not_found(self, student_service):
        """Test getting a student that doesn't exist."""
        with pytest.raises(NotFoundError):
            student_service.get_student('nonexistent')
    
    def test_update_student(self, student_service):
        """Test updating a student."""
        # Create a student first
        student_data = {
            "email": "bob@example.com",
            "password": "Password123",
            "name": "Bob Johnson",
            "phone": "555-123-4567",
            "address": "789 Pine St",
            "student_id": "S003",
            "enrollment_date": date(2020, 3, 3),
            "grade_level": 12,
            "department_id": "D001",
            "gpa": 3.2
        }
        
        created_student = student_service.create_student(student_data)
        student_id = created_student.id
        
        # Update the student
        update_data = {
            "name": "Robert Johnson",
            "gpa": 3.7,
            "notes": "Updated name and GPA"
        }
        
        updated_student = student_service.update_student(student_id, update_data)
        
        assert updated_student is not None
        assert updated_student.name == "Robert Johnson"
        assert updated_student.gpa == 3.7
    
    def test_delete_student(self, student_service):
        """Test deleting a student."""
        # Create a student first
        student_data = {
            "email": "alice@example.com",
            "password": "Password123",
            "name": "Alice Brown",
            "phone": "444-123-4567",
            "address": "321 Elm St",
            "student_id": "S004",
            "enrollment_date": date(2020, 4, 4),
            "grade_level": 9,
            "department_id": "D001",
            "gpa": 3.9
        }
        
        created_student = student_service.create_student(student_data)
        student_id = created_student.id
        
        # Deactivate the student
        deactivated_student = student_service.deactivate_student(student_id)
        assert deactivated_student.is_active is False
        
        # Verify the student is deactivated
        retrieved_student = student_service.get_student(student_id)
        assert retrieved_student.is_active is False
    
    def test_get_all_students(self, student_service):
        """Test getting all students."""
        # Clear any existing students
        student_service.students.clear()
        
        # Create some students
        students_data = [
            {
                "email": "s1@example.com",
                "password": "Password123",
                "name": "Student 1",
                "student_id": "S101",
                "enrollment_date": date(2020, 1, 1),
                "grade_level": 10
            },
            {
                "email": "s2@example.com",
                "password": "Password123",
                "name": "Student 2",
                "student_id": "S102",
                "enrollment_date": date(2020, 2, 2),
                "grade_level": 11
            },
            {
                "email": "s3@example.com",
                "password": "Password123",
                "name": "Student 3",
                "student_id": "S103",
                "enrollment_date": date(2020, 3, 3),
                "grade_level": 12
            }
        ]
        
        for data in students_data:
            student_service.create_student(data)
        
        # Get all students using search
        all_students = student_service.search_students()
        
        assert len(all_students) >= 3  # May include test data from service initialization
        # Filter for our specific test students
        test_students = [s for s in all_students if s.student_id in ['S101', 'S102', 'S103']]
        assert len(test_students) == 3
        student_names = [s.name for s in test_students]
        assert "Student 1" in student_names
        assert "Student 2" in student_names
        assert "Student 3" in student_names
    
    def test_students_by_department(self, student_service):
        """Test getting students by department."""
        # Clear any existing students
        student_service.students.clear()
        
        # Create students in different departments
        students_data = [
            {
                "email": "d1@example.com",
                "password": "Password123",
                "name": "Department 1 Student",
                "student_id": "D1S1",
                "enrollment_date": date(2020, 1, 1),
                "grade_level": 10,
                "department_id": "D001"
            },
            {
                "email": "d2@example.com",
                "password": "Password123",
                "name": "Department 1 Student 2",
                "student_id": "D1S2",
                "enrollment_date": date(2020, 2, 2),
                "grade_level": 11,
                "department_id": "D001"
            },
            {
                "email": "d3@example.com",
                "password": "Password123",
                "name": "Department 2 Student",
                "student_id": "D2S1",
                "enrollment_date": date(2020, 3, 3),
                "grade_level": 12,
                "department_id": "D002"
            }
        ]
        
        for data in students_data:
            student_service.create_student(data)
        
        # Get students by department
        d001_students = student_service.get_students_by_department("D001")
        d002_students = student_service.get_students_by_department("D002")
        
        assert len(d001_students) == 2
        assert len(d002_students) == 1
        assert d002_students[0].name == "Department 2 Student"
    
    def test_student_statistics(self, student_service):
        """Test getting student statistics."""
        # Clear any existing students
        student_service.students.clear()
        
        # Create students with different GPAs
        students_data = [
            {
                "email": "stats1@example.com",
                "password": "Password123",
                "name": "Stats Student 1",
                "student_id": "SS1",
                "enrollment_date": date(2020, 1, 1),
                "grade_level": 10,
                "gpa": 3.5
            },
            {
                "email": "stats2@example.com",
                "password": "Password123",
                "name": "Stats Student 2",
                "student_id": "SS2",
                "enrollment_date": date(2020, 2, 2),
                "grade_level": 11,
                "gpa": 3.2
            },
            {
                "email": "stats3@example.com",
                "password": "Password123",
                "name": "Stats Student 3",
                "student_id": "SS3",
                "enrollment_date": date(2020, 3, 3),
                "grade_level": 12,
                "gpa": 2.8
            }
        ]
        
        for data in students_data:
            student_service.create_student(data)
        
        # Get statistics
        stats = student_service.get_student_statistics()
        
        assert stats.total_students == 3
        assert stats.average_gpa == (3.5 + 3.2 + 2.8) / 3
    
    def test_validation_errors(self, student_service):
        """Test validation errors."""
        # Test missing required fields
        incomplete_data = {
            "name": "Test Student",
            # Missing email and password
        }
        
        with pytest.raises(ValidationError):
            student_service.create_student(incomplete_data)
        
        # Test invalid email
        invalid_email_data = {
            "email": "invalid-email",
            "password": "Password123",
            "name": "Test Student",
            "student_id": "INV001"
        }
        
        with pytest.raises(ValidationError):
            student_service.create_student(invalid_email_data)
        
        # Test invalid GPA
        invalid_gpa_data = {
            "email": "test@example.com",
            "password": "Password123",
            "name": "Test Student",
            "student_id": "INV002",
            "gpa": 5.0  # Invalid GPA
        }
        
        with pytest.raises(ValidationError):
            student_service.create_student(invalid_gpa_data)
    
    def test_search_students(self, student_service):
        """Test searching students by name."""
        # Clear any existing students
        student_service.students.clear()
        
        # Create students with different names
        students_data = [
            {
                "email": "john1@example.com",
                "password": "Password123",
                "name": "John Smith",
                "student_id": "J001",
                "enrollment_date": date(2020, 1, 1),
                "grade_level": 10
            },
            {
                "email": "john2@example.com",
                "password": "Password123",
                "name": "John Doe",
                "student_id": "J002",
                "enrollment_date": date(2020, 2, 2),
                "grade_level": 11
            },
            {
                "email": "jane@example.com",
                "password": "Password123",
                "name": "Jane Smith",
                "student_id": "J003",
                "enrollment_date": date(2020, 3, 3),
                "grade_level": 12
            }
        ]
        
        for data in students_data:
            student_service.create_student(data)
        
        # Search for students by name (using search_criteria)
        john_students = student_service.search_students({"name": "John"})
        assert len(john_students) == 2
        
        # Search for students by name pattern
        smith_students = student_service.search_students({"name": "Smith"})
        assert len(smith_students) == 2
        
        # Search for non-existent name
        no_students = student_service.search_students({"name": "nonexistent"})
        assert len(no_students) == 0