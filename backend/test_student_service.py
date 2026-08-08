#!/usr/bin/env python3
"""
Simple test script for student service
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from src.services.student_service import StudentService
from src.core.security import AuthService
from src.models.student import GradeLevel
from datetime import date

def test_student_service():
    """Test basic student service functionality"""
    try:
        # Initialize services
        auth_service = AuthService()
        student_service = StudentService(auth_service)
        
        # Test student data
        test_student_data = {
            "email": "test.student@example.com",
            "password": "TestPassword123!",
            "name": "John Doe",
            "student_id": "STU999",
            "grade_level": GradeLevel.TENTH,
            "enrollment_date": date(2024, 9, 1),
            "department_id": "DEPT001",
            "advisor_id": "TEACH001",
            "gpa": 3.5,
            "attendance_rate": 0.95,
            "academic_standing": "good"
        }
        
        print("Testing student creation...")
        # Test student creation
        student = student_service.create_student(test_student_data)
        print(f"✓ Student created successfully with ID: {student.id}")
        
        print("Testing student retrieval...")
        # Test student retrieval
        retrieved_student = student_service.get_student(student.id)
        print(f"✓ Student retrieved successfully: {retrieved_student.name}")
        
        print("Testing student search...")
        # Test student search
        students = student_service.search_students({"name": "John"})
        print(f"✓ Found {len(students)} students matching search criteria")
        
        print("Testing academic summary...")
        # Test academic summary
        summary = student_service.get_student_academic_summary(student.id, [85, 90, 78])
        print(f"✓ Academic summary generated - GPA: {summary.gpa}")
        
        print("Testing risk assessment...")
        # Test risk assessment
        at_risk = student_service.identify_at_risk_students()
        print(f"✓ Identified {len(at_risk)} at-risk students")
        
        print("\n🎉 All tests passed successfully!")
        
    except Exception as e:
        print(f"❌ Test failed with error: {str(e)}")
        import traceback
        traceback.print_exc()
        assert False, f"Test failed with error: {str(e)}"

if __name__ == "__main__":
    test_student_service()