"""
User Model for Database Operations

This module provides the SQLAlchemy model for User entity.
It includes all fields and relationships for user management and authentication.

Author: Edu-Flow Team
"""

from typing import Dict, Any, Optional, List
from datetime import datetime
import logging

from sqlalchemy import Column, String, Integer, Text, DateTime, JSON, Boolean, ForeignKey
from sqlalchemy.orm import relationship

from infrastructure.models.base_model import BaseModel
from core.exceptions import ValidationError
from core.logging import get_logger

logger = get_logger(__name__)


class UserModel(BaseModel):
    """
    SQLAlchemy model for User entity.
    
    Represents user management with authentication, roles, and profile information.
    """
    __tablename__ = "users"
    
    # User identification
    id = Column(String(50), primary_key=True)
    username = Column(String(100), unique=True, nullable=False, index=True)
    email = Column(String(255), unique=True, nullable=False, index=True)
    phone = Column(String(20))
    
    # Personal information
    first_name = Column(String(100), nullable=False)
    last_name = Column(String(100), nullable=False)
    middle_name = Column(String(100))
    full_name = Column(String(200), nullable=False)
    date_of_birth = Column(DateTime)
    gender = Column(String(20))  # Male, Female, Other, Prefer not to say
    
    # Address information
    address = Column(Text)
    city = Column(String(100))
    state = Column(String(100))
    country = Column(String(100), nullable=False)
    postal_code = Column(String(20))
    
    # Authentication information
    password_hash = Column(String(255), nullable=False)
    salt = Column(String(255), nullable=False)
    is_active = Column(Boolean, default=True)
    is_verified = Column(Boolean, default=False)
    is_email_verified = Column(Boolean, default=False)
    is_phone_verified = Column(Boolean, default=False)
    
    # User roles and permissions
    role = Column(String(50), nullable=False)  # admin, teacher, student, staff, parent, alumnus
    department_id = Column(String(50), ForeignKey("departments.id"))
    program_id = Column(String(50), ForeignKey("programs.id"))
    batch_year = Column(String(10))
    admission_number = Column(String(50))
    enrollment_number = Column(String(50))
    
    # Academic information
    student_id = Column(String(50))  # Student ID
    teacher_id = Column(String(50))  # Teacher ID
    staff_id = Column(String(50))  # Staff ID
    employee_id = Column(String(50))  # Employee ID
    
    # Academic details
    gpa = Column(Float, default=0.0)  # Grade Point Average
    cgpa = Column(Float, default=0.0)  # Cumulative GPA
    current_semester = Column(Integer, default=1)
    total_credits_completed = Column(Integer, default=0)
    total_credits_required = Column(Integer, default=0)
    
    # Employment information
    employment_status = Column(String(20), default='unemployed')  # employed, unemployed, retired, self_employed
    job_title = Column(String(100))
    organization = Column(String(200))
    experience_years = Column(Integer, default=0)
    
    # User preferences
    language_preference = Column(String(10), default='en')  # en, es, fr, etc.
    timezone = Column(String(50), default='UTC')
    notification_preferences = Column(JSON, default=dict)  # Email, SMS, Push, etc.
    privacy_settings = Column(JSON, default=dict)
    
    # Account settings
    last_login = Column(DateTime)
    login_count = Column(Integer, default=0)
    failed_login_attempts = Column(Integer, default=0)
    account_locked = Column(Boolean, default=False)
    account_locked_until = Column(DateTime)
    password_expires_at = Column(DateTime)
    
    # User metadata
    metadata = Column(JSON, default=dict)
    notes = Column(Text)
    
    # Relationships
    department = relationship("DepartmentModel")
    program = relationship("ProgramModel")
    
    # User-specific relationships
    enrollments = relationship("EnrollmentModel")
    classes_taught = relationship("ClassModel", foreign_keys="ClassModel.allocated_teacher_id")
    feedback_submitted = relationship("FeedbackModel", foreign_keys="FeedbackModel.submitted_by_id")
    feedback_assigned = relationship("FeedbackModel", foreign_keys="FeedbackModel.assigned_to_id")
    feedback_resolved = relationship("FeedbackModel", foreign_keys="FeedbackModel.resolved_by_id")
    assessments_taken = relationship("AssessmentModel")
    grades_received = relationship("GradeModel")
    allocations = relationship("AllocationModel", foreign_keys="AllocationModel.assigned_by_id")
    
    def __init__(self, **kwargs):
        """Initialize the user model with provided data."""
        # Set default values for optional fields
        kwargs.setdefault('is_active', True)
        kwargs.setdefault('is_verified', False)
        kwargs.setdefault('is_email_verified', False)
        kwargs.setdefault('is_phone_verified', False)
        kwargs.setdefault('role', 'student')
        kwargs.setdefault('gpa', 0.0)
        kwargs.setdefault('cgpa', 0.0)
        kwargs.setdefault('current_semester', 1)
        kwargs.setdefault('total_credits_completed', 0)
        kwargs.setdefault('total_credits_required', 0)
        kwargs.setdefault('employment_status', 'unemployed')
        kwargs.setdefault('experience_years', 0)
        kwargs.setdefault('language_preference', 'en')
        kwargs.setdefault('timezone', 'UTC')
        kwargs.setdefault('notification_preferences', {})
        kwargs.setdefault('privacy_settings', {})
        kwargs.setdefault('login_count', 0)
        kwargs.setdefault('failed_login_attempts', 0)
        kwargs.setdefault('account_locked', False)
        kwargs.setdefault('metadata', {})
        
        super().__init__(**kwargs)
        
        # Generate full name
        self.generate_full_name()
    
    def to_dict(self, include_relationships: bool = False) -> Dict[str, Any]:
        """
        Convert the model to a dictionary.
        
        Args:
            include_relationships: Whether to include relationship data
            
        Returns:
            Dictionary representation of the model
        """
        data = super().to_dict()
        
        # Convert date fields to ISO format
        if 'date_of_birth' in data and isinstance(data['date_of_birth'], datetime):
            data['date_of_birth'] = data['date_of_birth'].isoformat()
        else:
            data['date_of_birth'] = None
        
        if 'last_login' in data and isinstance(data['last_login'], datetime):
            data['last_login'] = data['last_login'].isoformat()
        else:
            data['last_login'] = None
        
        if 'account_locked_until' in data and isinstance(data['account_locked_until'], datetime):
            data['account_locked_until'] = data['account_locked_until'].isoformat()
        else:
            data['account_locked_until'] = None
        
        if 'password_expires_at' in data and isinstance(data['password_expires_at'], datetime):
            data['password_expires_at'] = data['password_expires_at'].isoformat()
        else:
            data['password_expires_at'] = None
        
        # Convert JSON fields to proper format
        if 'notification_preferences' in data and isinstance(data['notification_preferences'], dict):
            data['notification_preferences'] = data['notification_preferences']
        else:
            data['notification_preferences'] = {}
        
        if 'privacy_settings' in data and isinstance(data['privacy_settings'], dict):
            data['privacy_settings'] = data['privacy_settings']
        else:
            data['privacy_settings'] = {}
        
        if 'metadata' in data and isinstance(data['metadata'], dict):
            data['metadata'] = data['metadata']
        else:
            data['metadata'] = {}
        
        # Calculate derived fields
        data['is_admin'] = self.role == 'admin'
        data['is_teacher'] = self.role == 'teacher'
        data['is_student'] = self.role == 'student'
        data['is_staff'] = self.role == 'staff'
        data['is_account_locked'] = self.account_locked
        data['is_password_expired'] = self.is_password_expired()
        data['account_lock_status'] = self.get_account_lock_status()
        data['academic_progress'] = self.get_academic_progress()
        
        # Include relationships if requested
        if include_relationships:
            if hasattr(self, 'department') and self.department:
                data['department'] = self.department.to_dict()
            else:
                data['department'] = None
            
            if hasattr(self, 'program') and self.program:
                data['program'] = self.program.to_dict()
            else:
                data['program'] = None
            
            if hasattr(self, 'enrollments') and self.enrollments:
                data['enrollments'] = [enrollment.to_dict() for enrollment in self.enrollments]
            else:
                data['enrollments'] = []
            
            if hasattr(self, 'classes_taught') and self.classes_taught:
                data['classes_taught'] = [cls.to_dict() for cls in self.classes_taught]
            else:
                data['classes_taught'] = []
            
            if hasattr(self, 'feedback_submitted') and self.feedback_submitted:
                data['feedback_submitted'] = [feedback.to_dict() for feedback in self.feedback_submitted]
            else:
                data['feedback_submitted'] = []
            
            if hasattr(self, 'assessments_taken') and self.assessments_taken:
                data['assessments_taken'] = [assessment.to_dict() for assessment in self.assessments_taken]
            else:
                data['assessments_taken'] = []
            
            if hasattr(self, 'grades_received') and self.grades_received:
                data['grades_received'] = [grade.to_dict() for grade in self.grades_received]
            else:
                data['grades_received'] = []
        
        return data
    
    def update(self, **kwargs) -> None:
        """Update the model with new data."""
        # Handle special field updates
        if 'notification_preferences' in kwargs and isinstance(kwargs['notification_preferences'], dict):
            self.notification_preferences = kwargs['notification_preferences']
        if 'privacy_settings' in kwargs and isinstance(kwargs['privacy_settings'], dict):
            self.privacy_settings = kwargs['privacy_settings']
        if 'metadata' in kwargs and isinstance(kwargs['metadata'], dict):
            self.metadata = kwargs['metadata']
        
        super().update(**kwargs)
        
        # Regenerate full name if first/last name changed
        if 'first_name' in kwargs or 'last_name' in kwargs:
            self.generate_full_name()
    
    def validate(self) -> bool:
        """
        Validate the user model data.
        
        Returns:
            True if valid, False otherwise
            
        Raises:
            ValidationError: If validation fails
        """
        try:
            # Call base validation
            super().validate()
            
            # User-specific validations
            if not self.id:
                raise ValidationError("User ID is required")
            
            if not self.username:
                raise ValidationError("Username is required")
            
            if not self.email:
                raise ValidationError("Email is required")
            
            if not self.first_name:
                raise ValidationError("First name is required")
            
            if not self.last_name:
                raise ValidationError("Last name is required")
            
            if not self.full_name:
                raise ValidationError("Full name is required")
            
            if not self.role:
                raise ValidationError("Role is required")
            
            if not self.password_hash:
                raise ValidationError("Password hash is required")
            
            if not self.salt:
                raise ValidationError("Salt is required")
            
            if not self.country:
                raise ValidationError("Country is required")
            
            # Email validation
            if '@' not in self.email:
                raise ValidationError("Invalid email format")
            
            # Username validation
            if not self.username.isalnum() and '_' not in self.username:
                raise ValidationError("Username must be alphanumeric or underscore")
            
            # Role validation
            valid_roles = ['admin', 'teacher', 'student', 'staff', 'parent', 'alumnus']
            if self.role not in valid_roles:
                raise ValidationError(f"Invalid role: {self.role}")
            
            # GPA/CGPA validation
            if self.gpa < 0 or self.gpa > 4.0:
                raise ValidationError("GPA must be between 0 and 4.0")
            
            if self.cgpa < 0 or self.cgpa > 4.0:
                raise ValidationError("CGPA must be between 0 and 4.0")
            
            # Semester validation
            if self.current_semester < 1:
                raise ValidationError("Current semester must be positive")
            
            # Credits validation
            if self.total_credits_completed < 0:
                raise ValidationError("Total credits completed cannot be negative")
            
            if self.total_credits_required < 0:
                raise ValidationError("Total credits required cannot be negative")
            
            if self.total_credits_completed > self.total_credits_required:
                raise ValidationError("Total credits completed cannot exceed total credits required")
            
            # Employment status validation
            valid_statuses = ['employed', 'unemployed', 'retired', 'self_employed']
            if self.employment_status not in valid_statuses:
                raise ValidationError(f"Invalid employment status: {self.employment_status}")
            
            # Experience years validation
            if self.experience_years < 0:
                raise ValidationError("Experience years cannot be negative")
            
            # Language preference validation
            valid_languages = ['en', 'es', 'fr', 'de', 'it', 'pt', 'ru', 'zh', 'ja', 'ko']
            if self.language_preference not in valid_languages:
                raise ValidationError(f"Invalid language preference: {self.language_preference}")
            
            # Timezone validation
            if not self.timezone:
                raise ValidationError("Timezone is required")
            
            # Notification preferences validation
            if not isinstance(self.notification_preferences, dict):
                raise ValidationError("Notification preferences must be a dictionary")
            
            # Privacy settings validation
            if not isinstance(self.privacy_settings, dict):
                raise ValidationError("Privacy settings must be a dictionary")
            
            # Metadata validation
            if not isinstance(self.metadata, dict):
                raise ValidationError("Metadata must be a dictionary")
            
            logger.info(f"User {self.username} validation passed")
            return True
            
        except Exception as e:
            logger.error(f"User validation error: {str(e)}")
            raise ValidationError(f"User validation error: {str(e)}")
    
    def generate_full_name(self) -> None:
        """Generate full name from first name and last name."""
        parts = [self.first_name]
        if self.middle_name:
            parts.append(self.middle_name)
        parts.append(self.last_name)
        self.full_name = ' '.join(parts).strip()
    
    def set_password(self, password: str) -> None:
        """
        Set user password.
        
        Args:
            password: New password
        """
        # Generate salt and hash password
        import bcrypt
        self.salt = bcrypt.gensalt().decode('utf-8')
        self.password_hash = bcrypt.hashpw(password.encode('utf-8'), self.salt.encode('utf-8')).decode('utf-8')
        
        # Set password expiration (e.g., 90 days from now)
        from datetime import timedelta
        self.password_expires_at = datetime.now() + timedelta(days=90)
        
        self.updated_at = datetime.now()
        logger.info(f"Updated password for user {self.username}")
    
    def verify_password(self, password: str) -> bool:
        """
        Verify user password.
        
        Args:
            password: Password to verify
            
        Returns:
            True if password matches
        """
        import bcrypt
        if not self.password_hash or not self.salt:
            return False
        
        hashed_password = bcrypt.hashpw(password.encode('utf-8'), self.salt.encode('utf-8')).decode('utf-8')
        return bcrypt.checkpw(password.encode('utf-8'), self.password_hash.encode('utf-8'))
    
    def is_password_expired(self) -> bool:
        """
        Check if password is expired.
        
        Returns:
            True if password is expired
        """
        if not self.password_expires_at:
            return False
        
        return datetime.now() > self.password_expires_at
    
    def is_account_locked(self) -> bool:
        """
        Check if account is locked.
        
        Returns:
            True if account is locked
        """
        if not self.account_locked:
            return False
        
        if self.account_locked_until and datetime.now() > self.account_locked_until:
            # Lock period expired, unlock account
            self.account_locked = False
            self.account_locked_until = None
            self.failed_login_attempts = 0
            self.updated_at = datetime.now()
            return False
        
        return True
    
    def get_account_lock_status(self) -> str:
        """
        Get account lock status.
        
        Returns:
            Account lock status string
        """
        if not self.account_locked:
            return 'unlocked'
        elif self.account_locked_until and datetime.now() < self.account_locked_until:
            return 'temporarily_locked'
        else:
            return 'permanently_locked'
    
    def update_login_info(self, login_successful: bool = True) -> None:
        """
        Update login information.
        
        Args:
            login_successful: Whether login was successful
        """
        self.last_login = datetime.now()
        self.login_count += 1
        
        if login_successful:
            self.failed_login_attempts = 0
            self.account_locked = False
        else:
            self.failed_login_attempts += 1
            
            # Lock account after 5 failed attempts
            if self.failed_login_attempts >= 5:
                self.account_locked = True
                self.account_locked_until = datetime.now() + timedelta(hours=24)  # 24 hour lock
        
        self.updated_at = datetime.now()
        logger.info(f"Updated login info for user {self.username}: {'success' if login_successful else 'failed'}")
    
    def update_academic_info(self, gpa: float = None, cgpa: float = None, 
                           current_semester: int = None, **academic_info) -> None:
        """
        Update academic information.
        
        Args:
            gpa: Grade Point Average
            cgpa: Cumulative GPA
            current_semester: Current semester
            **academic_info: Additional academic information
        """
        if gpa is not None:
            if gpa < 0 or gpa > 4.0:
                raise ValidationError("GPA must be between 0 and 4.0")
            self.gpa = gpa
        
        if cgpa is not None:
            if cgpa < 0 or cgpa > 4.0:
                raise ValidationError("CGPA must be between 0 and 4.0")
            self.cgpa = cgpa
        
        if current_semester is not None:
            if current_semester < 1:
                raise ValidationError("Current semester must be positive")
            self.current_semester = current_semester
        
        # Update additional academic info
        if 'total_credits_completed' in academic_info:
            self.total_credits_completed = academic_info['total_credits_completed']
        
        if 'total_credits_required' in academic_info:
            self.total_credits_required = academic_info['total_credits_required']
        
        self.updated_at = datetime.now()
        logger.info(f"Updated academic info for user {self.username}")
    
    def update_employment_info(self, **employment_info) -> None:
        """
        Update employment information.
        
        Args:
            **employment_info: Employment information to update
        """
        if 'employment_status' in employment_info:
            valid_statuses = ['employed', 'unemployed', 'retired', 'self_employed']
            if employment_info['employment_status'] not in valid_statuses:
                raise ValidationError(f"Invalid employment status: {employment_info['employment_status']}")
            self.employment_status = employment_info['employment_status']
        
        if 'job_title' in employment_info:
            self.job_title = employment_info['job_title']
        
        if 'organization' in employment_info:
            self.organization = employment_info['organization']
        
        if 'experience_years' in employment_info:
            if employment_info['experience_years'] < 0:
                raise ValidationError("Experience years cannot be negative")
            self.experience_years = employment_info['experience_years']
        
        self.updated_at = datetime.now()
        logger.info(f"Updated employment info for user {self.username}")
    
    def update_contact_info(self, **contact_info) -> None:
        """
        Update contact information.
        
        Args:
            **contact_info: Contact information to update
        """
        if 'email' in contact_info:
            self.email = contact_info['email']
        
        if 'phone' in contact_info:
            self.phone = contact_info['phone']
        
        if 'address' in contact_info:
            self.address = contact_info['address']
        
        if 'city' in contact_info:
            self.city = contact_info['city']
        
        if 'state' in contact_info:
            self.state = contact_info['state']
        
        if 'country' in contact_info:
            self.country = contact_info['country']
        
        if 'postal_code' in contact_info:
            self.postal_code = contact_info['postal_code']
        
        self.updated_at = datetime.now()
        logger.info(f"Updated contact info for user {self.username}")
    
    def get_academic_progress(self) -> Dict[str, Any]:
        """
        Get academic progress information.
        
        Returns:
            Academic progress dictionary
        """
        return {
            'gpa': self.gpa,
            'cgpa': self.cgpa,
            'current_semester': self.current_semester,
            'total_credits_completed': self.total_credits_completed,
            'total_credits_required': self.total_credits_required,
            'credits_progress': (self.total_credits_completed / self.total_credits_required * 100) if self.total_credits_required > 0 else 0,
            'semester_progress': (self.current_semester / 8 * 100) if self.current_semester <= 8 else 100,  # Assuming 8 semesters
            'academic_standing': 'excellent' if self.gpa >= 3.7 else 'good' if self.gpa >= 3.0 else 'satisfactory' if self.gpa >= 2.0 else 'needs_improvement'
        }
    
    def get_user_summary(self) -> Dict[str, Any]:
        """
        Get user summary information.
        
        Returns:
            User summary dictionary
        """
        return {
            'id': self.id,
            'username': self.username,
            'email': self.email,
            'full_name': self.full_name,
            'role': self.role,
            'is_active': self.is_active,
            'is_account_locked': self.account_locked,
            'is_password_expired': self.is_password_expired(),
            'account_lock_status': self.get_account_lock_status(),
            'last_login': self.last_login.isoformat() if self.last_login else None,
            'login_count': self.login_count,
            'failed_login_attempts': self.failed_login_attempts,
            'academic_progress': self.get_academic_progress()
        }
    
    def __repr__(self) -> str:
        """String representation of the user model."""
        return f"<UserModel(id='{self.id}', username='{self.username}', role='{self.role}', active={self.is_active})>"