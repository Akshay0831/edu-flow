#!/usr/bin/env python3
"""
Simple test to verify StudentService functionality
"""

import sys
import os
from datetime import date

# Add the current directory to the path so we can import from src
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Add the backend directory to the path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.services.student_service import StudentService

def test_basic_functionality():
    """Test basic StudentService functionality"""
    print("Creating StudentService...")
    service = StudentService()
    
    print(f"Initial students count: {len(service.students)}")
    
    # Test data
    student_data = {
        "email": "test@example.com",
        "password": "Password123",
        "name": "Test Student",
        "student_id": "T001",
        "enrollment_date": date(2020, 1, 1),
        "grade_level": 10,
        "gpa": 3.5
    }
    
    print("Creating student...")
    created_student = service.create_student(student_data)
    
    print(f"Created student ID: {created_student.id}")
    print(f"Created student name: {created_student.name}")
    print(f"Created student email: {created_student.email}")
    
    print(f"Students count after creation: {len(service.students)}")
    
    # Test getting the student
    print("Getting student...")
    retrieved_student = service.get_student(created_student.id)
    print(f"Retrieved student name: {retrieved_student.name}")
    
    print("Test completed successfully!")

if __name__ == "__main__":
    test_basic_functionality()