"""
Validation module for Edu-Flow backend.

This module provides standalone validation functions for common use cases.
These functions are designed to work with the existing test suite and security requirements.
"""

import re
from typing import Optional, Union, List, Dict, Any
from datetime import datetime, date
from src.core.exceptions import ValidationError as CustomValidationError


def validate_email(email: Optional[str]) -> bool:
    """Validate email format."""
    if not isinstance(email, str):
        raise CustomValidationError("Email must be a string", field="email")
    if not email:
        raise CustomValidationError("Email cannot be empty", field="email")
    if not re.match(r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$', email):
        raise CustomValidationError("Invalid email format", field="email")
    return True


def validate_phone(phone: Optional[str]) -> bool:
    """Validate phone number format."""
    if not phone:
        return True  # Allow None/empty
    phone_clean = re.sub(r'[^+\d]', '', str(phone))
    if not re.match(r'^\+[1-9]\d{1,14}$', phone_clean):
        raise CustomValidationError("Invalid phone number format", field="phone")
    return True


def validate_password(password: Optional[str]) -> bool:
    """Validate password strength."""
    if not password:
        raise CustomValidationError("Password is required", field="password")
    if len(password) < 8:
        raise CustomValidationError("Password must be at least 8 characters", field="password")
    if not re.search(r'[A-Z]', password):
        raise CustomValidationError("Password must contain at least one uppercase letter", field="password")
    if not re.search(r'[a-z]', password):
        raise CustomValidationError("Password must contain at least one lowercase letter", field="password")
    if not re.search(r'\d', password):
        raise CustomValidationError("Password must contain at least one number", field="password")
    if not re.search(r'[!@#$%^&*(),.?":{}|<>]', password):
        raise CustomValidationError("Password must contain at least one special character", field="password")
    return True


def validate_text_length(text: str, max_length: int = 1000) -> bool:
    """Validate text length."""
    if not isinstance(text, str):
        raise CustomValidationError("Text must be a string", field="text")
    if len(text) > max_length:
        raise CustomValidationError(f"Text must be less than {max_length} characters", field="text")
    return True


def validate_date(date_input: Union[str, datetime, date]) -> bool:
    """Validate date format and ensure it's not in the future."""
    if isinstance(date_input, str):
        try:
            parsed_date = datetime.strptime(date_input, '%Y-%m-%d').date()
        except ValueError:
            raise CustomValidationError("Date must be in YYYY-MM-DD format", field="date")
    elif isinstance(date_input, datetime):
        parsed_date = date_input.date()
    elif isinstance(date_input, date):
        parsed_date = date_input
    else:
        raise CustomValidationError("Invalid date format", field="date")
    
    if parsed_date > date.today():
        raise CustomValidationError("Date cannot be in the future", field="date")
    return True


def validate_student_id(student_id: str) -> bool:
    """Validate student ID format."""
    if not isinstance(student_id, str):
        raise CustomValidationError("Student ID must be a string", field="student_id")
    if not re.match(r'^[A-Z]{2}\d{6}$', student_id):
        raise CustomValidationError("Student ID must be in format: AA123456", field="student_id")
    return True


def validate_grade(grade: Union[str, int]) -> bool:
    """Validate grade format."""
    if not isinstance(grade, (str, int)):
        raise CustomValidationError("Grade must be a string or number", field="grade")
    
    grade_str = str(grade).upper()
    valid_grades = ['A+', 'A', 'A-', 'B+', 'B', 'B-', 'C+', 'C', 'C-', 'D+', 'D', 'F']
    
    if grade_str not in valid_grades:
        raise CustomValidationError(f"Grade must be one of: {', '.join(valid_grades)}", field="grade")
    return True


def validate_credits(credits: Union[str, int, float]) -> bool:
    """Validate credits format."""
    if not isinstance(credits, (str, int, float)):
        raise CustomValidationError("Credits must be a number", field="credits")
    
    try:
        credits_float = float(credits)
        if credits_float <= 0 or credits_float > 20:
            raise CustomValidationError("Credits must be between 0 and 20", field="credits")
    except ValueError:
        raise CustomValidationError("Credits must be a valid number", field="credits")
    
    return True


def validate_course_prerequisites(prerequisites: Optional[List[str]]) -> bool:
    """Validate course prerequisites format."""
    if prerequisites is None:
        return True
    
    if not isinstance(prerequisites, list):
        raise CustomValidationError("Prerequisites must be a list", field="prerequisites")
    
    for prereq in prerequisites:
        if not isinstance(prereq, str):
            raise CustomValidationError("Each prerequisite must be a string", field="prerequisites")
        if not re.match(r'^[A-Z]{2}\d{3}$', prereq):
            raise CustomValidationError("Prerequisites must be in format: ABC123", field="prerequisites")
    
    return True


def validate_department_head(department_head: Optional[str]) -> bool:
    """Validate department head format."""
    if department_head is None:
        return True
    
    if not isinstance(department_head, str):
        raise CustomValidationError("Department head must be a string", field="department_head")
    
    if not re.match(r'^[A-Z]{2}\d{6}$', department_head):
        raise CustomValidationError("Department head must be a valid employee ID", field="department_head")
    
    return True


def validate_course_data(course_data: dict) -> bool:
    """Validate course data with cross-field validation."""
    if not isinstance(course_data, dict):
        return False
    
    # Check required fields
    required_fields = ["title", "code", "department_id", "level"]
    for field in required_fields:
        if field not in course_data:
            return False
    
    # Validate course code format
    if not isinstance(course_data["code"], str):
        return False
    if not re.match(r'^[A-Z]{2,3}\d{3,4}$', course_data["code"]):
        return False
    
    # Cross-field validation: course code should match department
    code = course_data["code"].upper()
    department = course_data["department_id"]
    
    # Define department-code mappings
    department_mappings = {
        "DEPT_CS": ["CS"],
        "DEPT_EE": ["EE"], 
        "DEPT_ME": ["ME"],
        "DEPT_CE": ["CE"]
    }
    
    # Check if course code prefix matches the expected department
    for dept, prefixes in department_mappings.items():
        if department == dept:
            # Check if course code starts with any of the expected prefixes
            if not any(code.startswith(prefix) for prefix in prefixes):
                return False
    
    # Validate level field
    valid_levels = ["beginner", "intermediate", "advanced"]
    if course_data["level"].lower() not in valid_levels:
        return False
    
    return True


def sanitize_input(input_text: str) -> str:
    """Basic XSS and SQL injection prevention by removing dangerous patterns."""
    if not input_text:
        return ""
    
    # Remove script tags and their content
    sanitized = re.sub(r'<script[^>]*>.*?</script>', '', input_text, flags=re.IGNORECASE | re.DOTALL)
    
    # Remove other potentially dangerous patterns
    sanitized = re.sub(r'<iframe[^>]*>', '', sanitized, flags=re.IGNORECASE)
    sanitized = re.sub(r'<img[^>]*onerror[^>]*>', '', sanitized, flags=re.IGNORECASE)
    sanitized = re.sub(r'<div[^>]*onmouseover[^>]*>', '', sanitized, flags=re.IGNORECASE)
    sanitized = re.sub(r'<body[^>]*onload[^>]*>', '', sanitized, flags=re.IGNORECASE)
    sanitized = re.sub(r'<input[^>]*onfocus[^>]*>', '', sanitized, flags=re.IGNORECASE)
    sanitized = re.sub(r'<svg[^>]*onload[^>]*>', '', sanitized, flags=re.IGNORECASE)
    sanitized = re.sub(r'<a[^>]*onclick[^>]*>', '', sanitized, flags=re.IGNORECASE)
    
    # Remove javascript: protocol
    sanitized = re.sub(r'javascript:', '', sanitized, flags=re.IGNORECASE)
    
    # Basic SQL injection prevention - remove dangerous characters and keywords
    sanitized = sanitized.replace(';', '').replace('--', '').replace('\'', '\'\'').replace('\"', '\'\'')
    
    # Remove potentially dangerous SQL keywords (case-insensitive)
    dangerous_sql_keywords = ['DROP', 'SELECT', 'INSERT', 'UPDATE', 'DELETE', 'UNION', 'EXEC', 'EXECUTE', 'DECLARE']
    for keyword in dangerous_sql_keywords:
        # Remove dangerous SQL keywords completely
        sanitized = re.sub(rf'\b{keyword}\b', '', sanitized, flags=re.IGNORECASE)
    
    # Strip whitespace
    return sanitized.strip()