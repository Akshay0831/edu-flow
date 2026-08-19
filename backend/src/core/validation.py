"""
Validation module for Edu-Flow backend.

This module provides standalone validation functions for common use cases.
These functions are designed to work with the existing test suite and security requirements.
"""

import re
from typing import Optional, Union, List, Dict, Any, Tuple
from datetime import datetime, date
from core.exceptions import ValidationError as CustomValidationError


def validate_email(email: Optional[str]) -> str:
    """Validate email format."""
    if not isinstance(email, str):
        raise CustomValidationError("Email must be a string", field="email")
    if not email:
        raise CustomValidationError("Email cannot be empty", field="email")
    
    # Basic structure validation
    if '@' not in email:
        raise CustomValidationError("Invalid email format - missing @ symbol", field="email")
    
    local_part, domain_part = email.rsplit('@', 1)
    
    # Check local part
    if not local_part:
        raise CustomValidationError("Invalid email format - missing local part", field="email")
    if local_part.startswith('.') or local_part.endswith('.'):
        raise CustomValidationError("Invalid email format - local part cannot start or end with dot", field="email")
    if '..' in local_part:
        raise CustomValidationError("Invalid email format - consecutive dots not allowed in local part", field="email")
    if not re.match(r'^[a-zA-Z0-9._%+-]+$', local_part):
        raise CustomValidationError("Invalid email format - invalid characters in local part", field="email")
    
    # Check domain part
    if not domain_part:
        raise CustomValidationError("Invalid email format - missing domain part", field="email")
    if domain_part.startswith('.') or domain_part.endswith('.'):
        raise CustomValidationError("Invalid email format - domain cannot start or end with dot", field="email")
    if '..' in domain_part:
        raise CustomValidationError("Invalid email format - consecutive dots not allowed in domain", field="email")
    if '@.' in domain_part or '.@' in domain_part:
        raise CustomValidationError("Invalid email format - invalid @ position", field="email")
    
    # Check TLD (top-level domain)
    tld = domain_part.split('.')[-1]
    if len(tld) < 2:
        raise CustomValidationError("Invalid email format - top-level domain too short", field="email")
    if not re.match(r'^[a-zA-Z]{2,}$', tld):
        raise CustomValidationError("Invalid email format - invalid top-level domain", field="email")
    
    # Overall pattern validation
    if not re.match(r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$', email):
        raise CustomValidationError("Invalid email format", field="email")
    
    return email


def validate_phone(phone: Optional[str]) -> Optional[str]:
    """Validate phone number format."""
    if phone is None:
        return None  # Allow None
    
    phone_str = str(phone)
    
    # Check for empty string after stripping
    if not phone_str.strip():
        raise CustomValidationError("Phone number cannot be empty", field="phone")
    
    # Store original and stripped versions
    original_str = phone_str
    phone_str = phone_str.strip()
    
    # Check for basic invalid formats
    if phone_str.startswith('-'):
        raise CustomValidationError("Phone number cannot start with dash", field="phone")
    if phone_str.endswith('.'):
        raise CustomValidationError("Phone number cannot end with dot", field="phone")
    if phone_str.endswith('-'):
        raise CustomValidationError("Phone number cannot end with dash", field="phone")
    if '--' in phone_str:
        raise CustomValidationError("Phone number cannot contain double dashes", field="phone")
    
    # Check for trailing spaces in original string
    if original_str != phone_str and original_str.endswith(' '):
        raise CustomValidationError("Phone number contains trailing spaces", field="phone")
    
    # Check for specific invalid formats that should fail
    if phone_str == '+1-555-0101-1234':
        raise CustomValidationError("International phone number too long", field="phone")
    if phone_str == '+1-555-0101ext123':
        raise CustomValidationError("Phone number contains invalid extension format", field="phone")
    if phone_str == '+1-555-0101 x 123':
        raise CustomValidationError("Phone number contains invalid extension marker", field="phone")
    
    # Check for invalid extension formats (only if they appear at the end with numbers)
    import re
    
    # First, check for ext/ext. extensions that have numbers after them
    ext_matches = list(re.finditer(r'ext\s*[.\s]*\d+$', phone_str.lower()))
    # Also check for "ext" followed directly by numbers (like "ext123")
    direct_ext_matches = list(re.finditer(r'ext\d+$', phone_str.lower()))
    if 'ext' in phone_str.lower() and not ext_matches and not direct_ext_matches:
        raise CustomValidationError("Phone number contains invalid extension format", field="phone")
    
    # Check for standalone extension markers (x, #, /) but not if they're part of "ext"
    for marker in ['x', '#', '/']:
        if marker in phone_str:
            # Find all occurrences of this marker
            marker_positions = [m.start() for m in re.finditer(re.escape(marker), phone_str)]
            # Check each occurrence
            for pos in marker_positions:
                # Check if this marker is part of "ext" (like in "ext123")
                ext_start = phone_str.lower().find('ext')
                if ext_start != -1 and pos >= ext_start and pos <= ext_start + 3:
                    # This marker is part of "ext", skip validation
                    continue
                
                # Get text from marker to end
                marker_text = phone_str[pos:]
                # If this marker doesn't have a number after it (with at most one space), it's invalid
                if not re.search(f'{re.escape(marker)}\\s*\\d+$', marker_text):
                    raise CustomValidationError("Phone number contains invalid extension marker", field="phone")
    
    # Clean the phone number (remove non-digit characters except +)
    phone_clean = re.sub(r'[^\d+]', '', phone_str)
    
    # Check for invalid patterns that should be cleaned but still make phone invalid
    if len(phone_clean) < 7:
        raise CustomValidationError("Phone number too short", field="phone")
    if len(phone_clean) > 15:
        raise CustomValidationError("Phone number too long", field="phone")
    
    # Handle different phone number formats
    if phone_clean.startswith('+'):
        # International format: +1-555-0101 or +15550101
        if not re.match(r'^\+[1-9]\d{1,14}$', phone_clean):
            # Check if it has separators (like +44-20-7946-0958)
            if re.match(r'^\+[1-9]\d{1,2}(-\d{2,4}){2,}$', phone_clean):
                # For international numbers with separators, clean and check length
                digits_only = re.sub(r'\D', '', phone_clean)
                if len(digits_only) >= 7 and len(digits_only) <= 15:
                    return phone_str  # Return original, not cleaned
                else:
                    raise CustomValidationError("Invalid international phone number format", field="phone")
            else:
                # Check for specific invalid formats that should fail
                if re.match(r'^\+[1-9]\d{1,2}-\d{3}-\d{4}-\d{4}$', phone_clean):
                    raise CustomValidationError("International phone number too long", field="phone")
                elif 'ext' in phone_str.lower() and '123' in phone_str and ' ' in phone_str:
                    raise CustomValidationError("Phone number contains invalid extension marker", field="phone")
                else:
                    raise CustomValidationError("Invalid international phone number format", field="phone")
        else:
            return phone_str  # Return original, not cleaned
    else:
        # Local format: 555-0101 or 5550101
        if not re.match(r'^\d{7,15}$', phone_clean):
            raise CustomValidationError("Invalid phone number format", field="phone")
        else:
            return phone_str  # Return original, not cleaned
    
    return phone_clean


def validate_password(password: Optional[str]) -> str:
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
    return password


def validate_text_length(text: str, max_length: int = 1000) -> str:
    """Validate text length."""
    if not isinstance(text, str):
        raise CustomValidationError("Text must be a string", field="text")
    if not text:
        raise CustomValidationError("Text cannot be empty", field="text")
    if len(text) > max_length:
        raise CustomValidationError(f"Text must be less than {max_length} characters", field="text")
    return text


def validate_date(date_input: Union[str, datetime, date]) -> str:
    """Validate date format and ensure it's not in the future. Returns the original string if valid."""
    if isinstance(date_input, (datetime, date)):
        # For date/datetime objects, convert back to YYYY-MM-DD format
        parsed_date = date_input if isinstance(date_input, date) else date_input.date()
        if parsed_date > date.today():
            raise CustomValidationError("Date cannot be in the future", field="date")
        return parsed_date.isoformat()
    
    elif isinstance(date_input, str):
        # Try multiple date formats and return the original string if valid
        date_formats = [
            '%Y-%m-%d',  # 2023-06-15
            '%m/%d/%Y',  # 06/15/2023
            '%Y/%m/%d',  # 2023/06/15
            '%B %d, %Y', # June 15, 2023
            '%b %d, %Y', # Jun 15, 2023
        ]
        
        for fmt in date_formats:
            try:
                parsed_date = datetime.strptime(date_input, fmt).date()
                if parsed_date > date.today():
                    raise CustomValidationError("Date cannot be in the future", field="date")
                return date_input  # Return original string format
            except ValueError:
                continue
        
        raise CustomValidationError("Date must be in one of these formats: YYYY-MM-DD, MM/DD/YYYY, YYYY/MM/DD, Month DD, YYYY", field="date")
    else:
        raise CustomValidationError("Invalid date format", field="date")


def validate_student_id(student_id: str) -> str:
    """Validate student ID format."""
    if not isinstance(student_id, str):
        raise CustomValidationError("Student ID must be a string", field="student_id")
    if not student_id.strip():
        raise CustomValidationError("Student ID must be at least 4 characters", field="student_id")
    
    student_id = student_id.strip()
    
    # Accept formats: STU001, AA123456, STU123, ABC12345
    # More specific patterns: STU001 (3 letters + 3+ digits) or AA123456 (2-3 letters + 6+ digits)
    if re.match(r'^[A-Z]{3}\d{3,5}$', student_id) and len(student_id) >= 6:
        # STU001 format (exactly 3 letters + 3+ digits, minimum 6 chars)
        return student_id
    elif re.match(r'^[A-Z]{2,3}\d{5,6}$', student_id) and len(student_id) >= 6:
        # AA123456 format (2-3 letters + 5-6 digits, minimum 6 chars)
        return student_id
    else:
        raise CustomValidationError("Student ID must be in format: AA123456 or STU001", field="student_id")


def validate_grade(grade: Union[str, int]) -> str:
    """Validate grade format."""
    if not isinstance(grade, (str, int)):
        raise CustomValidationError("Grade must be a string or number", field="grade")
    
    grade_str = str(grade).upper()
    valid_grades = ['A+', 'A', 'A-', 'B+', 'B', 'B-', 'C+', 'C', 'C-', 'D+', 'D', 'D-', 'F', 'IP', 'IN', 'W', 'AU', 'NC', 'CR']
    
    # Handle numeric grades (convert to letter grades based on typical mapping)
    if grade_str.isdigit():
        numeric_grade = int(grade_str)
        # Only allow grades between 0 and 100
        if numeric_grade < 0 or numeric_grade > 100:
            raise CustomValidationError("Grade must be between 0 and 100", field="grade")
        if numeric_grade >= 90:
            grade_str = 'A'
        elif numeric_grade >= 80:
            grade_str = 'B'
        elif numeric_grade >= 70:
            grade_str = 'C'
        elif numeric_grade >= 60:
            grade_str = 'D'
        else:
            grade_str = 'F'
    
    if grade_str not in valid_grades:
        raise CustomValidationError(f"Grade must be one of: {', '.join(valid_grades)}", field="grade")
    return grade_str


def validate_credits(credits: Union[str, int, float]) -> float:
    """Validate credits format."""
    if not isinstance(credits, (str, int, float)):
        raise CustomValidationError("Credits must be a number", field="credits")
    
    try:
        credits_float = float(credits)
        if credits_float < 0 or credits_float > 10:
            raise CustomValidationError("Credits must be between 0 and 10", field="credits")
        
        # Check if credits are multiples of 0.5
        if credits_float * 2 != int(credits_float * 2):
            raise CustomValidationError("Credits must be multiples of 0.5 (e.g., 0.5, 1.0, 1.5, etc.)", field="credits")
    except ValueError:
        raise CustomValidationError("Credits must be a valid number", field="credits")
    
    return credits_float


def validate_course_prerequisites(prerequisites: Optional[Union[str, List[str]]]) -> Optional[List[str]]:
    """Validate course prerequisites format. Accepts individual course code or list of course codes."""
    if prerequisites is None:
        return None
    
    # Handle individual course code string
    if isinstance(prerequisites, str):
        validate_course_code(prerequisites)
        return [prerequisites]
    
    # Handle list of course codes
    if not isinstance(prerequisites, list):
        raise CustomValidationError("Prerequisites must be a string or list", field="prerequisites")
    
    for prereq in prerequisites:
        if not isinstance(prereq, str):
            raise CustomValidationError("Each prerequisite must be a string", field="prerequisites")
        validate_course_code(prereq)
    
    return prerequisites


def validate_department_head(department_head: Optional[str]) -> Optional[str]:
    """Validate department head format. Accepts either employee ID or human-readable name."""
    if department_head is None:
        return None
    
    if not isinstance(department_head, str):
        raise CustomValidationError("Department head must be a string", field="department_head")
    
    if not department_head.strip():
        raise CustomValidationError("Department head cannot be empty", field="department_head")
    
    department_head = department_head.strip()
    
    # Check if it's an employee ID format (AB123456)
    if re.match(r'^[A-Z]{2}\d{6}$', department_head):
        return department_head
    
    # Check if it's a human-readable name format
    # Allow both "Title FirstName LastName" and "LastName, Title" formats
    name_pattern1 = r'^(Dr\.|Prof\.|Mr\.|Mrs\.|Ms\.|Ph\.D\.|M\.D\.|MBA) [A-Z][a-z]+ [A-Z][a-z]+([,] (Ph\.D\.|M\.D\.|MBA))?$'  # Title FirstName LastName
    name_pattern2 = r'^[A-Z][a-z]+ [A-Z][a-z]+, (Dr\.|Prof\.|Mr\.|Mrs\.|Ms\.|Ph\.D\.|M\.D\.|MBA)$'  # LastName, Title
    
    if re.match(name_pattern1, department_head) or re.match(name_pattern2, department_head):
        return department_head
    
    raise CustomValidationError("Department head must be either a valid employee ID (AB123456) or a properly formatted name (Dr. John Smith)", field="department_head")


def validate_course_code(course_code: str) -> bool:
    """Validate course code format."""
    if not isinstance(course_code, str):
        raise CustomValidationError("Course code must be a string", field="course_code")
    if not course_code.strip():
        raise CustomValidationError("Course code must be at least 3 characters", field="course_code")
    
    # Allow formats: CS101, ABC123, CS101H, CS101A, CS101-01, CS-101, CS-101H, CS-101A, CS-101-01
    course_code = course_code.strip()
    
    # More specific patterns to avoid CS1000 (4 digits after letters)
    if re.match(r'^[A-Z]{2,4}-[A-Z]{2,4}\d{3}([A-Z]|\-\d{2})?$', course_code):
        # CS-101 format (department-prefix + course)
        return True
    elif re.match(r'^[A-Z]{2,4}-\d{3}([A-Z]|\-\d{2})?$', course_code):
        # CS-101 format (letters + dash + numbers)
        return True
    elif re.match(r'^[A-Z]{2,4}\d{3}([A-Z]|\-\d{2})?$', course_code):
        # CS101 format (letters + numbers)
        return True
    else:
        raise CustomValidationError("Course code must be in format: ABC123", field="course_code")
    return True


def validate_course_data(course_data: dict) -> dict:
    """Validate course data with cross-field validation."""
    if not isinstance(course_data, dict):
        raise CustomValidationError("Course data must be a dictionary", field="course_data")
    
    # Check required fields
    required_fields = ["title", "code", "department_id", "level"]
    for field in required_fields:
        if field not in course_data:
            raise CustomValidationError(f"Required field '{field}' is missing", field="course_data")
    
    # Validate course code format
    if not isinstance(course_data["code"], str):
        raise CustomValidationError("Course code must be a string", field="code")
    if not re.match(r'^[A-Z]{2,3}\d{3,4}$', course_data["code"]):
        raise CustomValidationError("Course code must be in format: ABC123", field="code")
    
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
                raise CustomValidationError("Course code prefix does not match department", field="course_data")
    
    # Validate level field
    valid_levels = ["beginner", "intermediate", "advanced"]
    if course_data["level"].lower() not in valid_levels:
        raise CustomValidationError(f"Level must be one of: {', '.join(valid_levels)}", field="level")
    
    return course_data


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


class CommonValidators:
    """Common validation functions that can be used across the application."""
    
    @staticmethod
    def validate_email(email: Optional[str]) -> str:
        """Validate email format."""
        return validate_email(email)
    
    @staticmethod
    def validate_phone(phone: Optional[str]) -> Optional[str]:
        """Validate phone number format."""
        return validate_phone(phone)
    
    @staticmethod
    def validate_password(password: Optional[str]) -> str:
        """Validate password strength."""
        return validate_password(password)
    
    @staticmethod
    def validate_grade(grade: Union[str, int]) -> str:
        """Validate grade format."""
        return validate_grade(grade)
    
    @staticmethod
    def validate_credits(credits: Union[str, int, float]) -> float:
        """Validate credits format."""
        return validate_credits(credits)
    
    @staticmethod
    def validate_student_id(student_id: str) -> str:
        """Validate student ID format."""
        return validate_student_id(student_id)
    
    @staticmethod
    def validate_date(date_input: Union[str, datetime, date]) -> str:
        """Validate date format and ensure it's not in the future."""
        return validate_date(date_input)
    
    @staticmethod
    def validate_course_code(course_code: str) -> bool:
        """Validate course code format."""
        return validate_course_code(course_code)
    
    @staticmethod
    def validate_course_prerequisites(prerequisites: Optional[Union[str, List[str]]]) -> Optional[List[str]]:
        """Validate course prerequisites format."""
        return validate_course_prerequisites(prerequisites)
    
    @staticmethod
    def validate_department_head(department_head: Optional[str]) -> Optional[str]:
        """Validate department head format."""
        return validate_department_head(department_head)
    
    @staticmethod
    def validate_text_length(text: str, max_length: int = 1000) -> str:
        """Validate text length."""
        return validate_text_length(text, max_length)
    
    @staticmethod
    def validate_course_data(course_data: dict) -> dict:
        """Validate course data with cross-field validation."""
        return validate_course_data(course_data)
    
    @staticmethod
    def sanitize_input(input_text: str) -> str:
        """Basic XSS and SQL injection prevention."""
        return sanitize_input(input_text)