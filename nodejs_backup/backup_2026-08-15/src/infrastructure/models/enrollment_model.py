"""
Enrollment Model for Database Operations

This module provides the SQLAlchemy model for Enrollment entity.
It includes all fields and relationships for student enrollment management.

Author: Edu-Flow Team
"""

from typing import Dict, Any, Optional, List
from datetime import datetime, timedelta
import logging

from sqlalchemy import Column, String, Integer, Text, DateTime, JSON, Boolean, ForeignKey, Float
from sqlalchemy.orm import relationship

from src.infrastructure.models.base_model import BaseModel
from src.core.exceptions import ValidationError
from src.core.logging import get_logger

logger = get_logger(__name__)


class EnrollmentModel(BaseModel):
    """
    SQLAlchemy model for Enrollment entity.
    
    Represents student enrollment in classes and programs with progress tracking.
    """
    __tablename__ = "enrollments"
    
    # Enrollment identification
    id = Column(String(50), primary_key=True)
    enrollment_number = Column(String(50), unique=True, nullable=False, index=True)
    code = Column(String(50), nullable=False, index=True)
    
    # Related entities
    student_id = Column(String(50), ForeignKey("users.id"), nullable=False)
    class_id = Column(String(50), ForeignKey("classes.id"), nullable=False)
    program_id = Column(String(50), ForeignKey("programs.id"), nullable=False)
    subject_id = Column(String(50), ForeignKey("subjects.id"), nullable=False)
    
    # Enrollment details
    enrollment_type = Column(String(50), nullable=False)  # program_enrollment, class_enrollment, subject_enrollment
    enrollment_semester = Column(Integer, nullable=False)  # Semester number
    academic_year = Column(String(10), nullable=False)  # 2023-2024
    batch = Column(String(20), nullable=False)  # A, B, C, etc.
    section = Column(String(5), nullable=False)  # 1, 2, 3, etc.
    
    # Enrollment status and progress
    status = Column(String(20), nullable=False, default="active")  # active, dropped, completed, suspended
    enrollment_date = Column(DateTime, nullable=False)
    expected_completion_date = Column(DateTime)
    actual_completion_date = Column(DateTime)
    
    # Progress and performance
    attendance_percentage = Column(Float, default=0.0)  # 0-100
    assignment_completion_percentage = Column(Float, default=0.0)  # 0-100
    overall_progress_percentage = Column(Float, default=0.0)  # 0-100
    current_grade = Column(String(10))  # A, B, C, D, F, etc.
    final_grade = Column(String(10))
    gpa_contribution = Column(Float, default=0.0)  # GPA contribution from this enrollment
    
    # Payment and fees
    tuition_fee = Column(Float, default=0.0)
    scholarship_amount = Column(Float, default=0.0)
    net_fee = Column(Float, default=0.0)
    payment_status = Column(String(20), default="pending")  # paid, pending, overdue
    payment_due_date = Column(DateTime)
    payment_completed_date = Column(DateTime)
    
    # Enrollment conditions and requirements
    prerequisites_met = Column(Boolean, default=True)
    special_requirements = Column(JSON, default=list)  # List of special requirements
    accommodations = Column(JSON, default=dict)  # Accommodations for the student
    
    # Attendance and participation
    attendance_records = Column(JSON, default=list)  # List of attendance records
    participation_score = Column(Float, default=0.0)  # 0-100
    participation_activities = Column(JSON, default=list)  # List of participation activities
    
    # Enrollment metadata
    metadata = Column(JSON, default=dict)
    notes = Column(Text)
    withdrawal_reason = Column(Text)  # Reason for dropping the enrollment
    
    # Relationships
    student = relationship("UserModel", back_populates="enrollments")
    class_model = relationship("ClassModel", back_populates="enrollments")
    program = relationship("ProgramModel")
    subject = relationship("SubjectModel")
    
    def __init__(self, **kwargs):
        """Initialize the enrollment model with provided data."""
        # Set default values for optional fields
        kwargs.setdefault('enrollment_semester', 1)
        kwargs.setdefault('academic_year', '2023-2024')
        kwargs.setdefault('batch', 'A')
        kwargs.setdefault('section', '1')
        kwargs.setdefault('status', 'active')
        kwargs.setdefault('enrollment_date', datetime.now())
        kwargs.setdefault('attendance_percentage', 0.0)
        kwargs.setdefault('assignment_completion_percentage', 0.0)
        kwargs.setdefault('overall_progress_percentage', 0.0)
        kwargs.setdefault('tuition_fee', 0.0)
        kwargs.setdefault('scholarship_amount', 0.0)
        kwargs.setdefault('net_fee', 0.0)
        kwargs.setdefault('payment_status', 'pending')
        kwargs.setdefault('prerequisites_met', True)
        kwargs.setdefault('special_requirements', [])
        kwargs.setdefault('accommodations', {})
        kwargs.setdefault('attendance_records', [])
        kwargs.setdefault('participation_score', 0.0)
        kwargs.setdefault('participation_activities', [])
        kwargs.setdefault('metadata', {})
        
        super().__init__(**kwargs)
        
        # Generate enrollment number if not provided
        if not self.enrollment_number:
            self.generate_enrollment_number()
    
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
        if 'enrollment_date' in data and isinstance(data['enrollment_date'], datetime):
            data['enrollment_date'] = data['enrollment_date'].isoformat()
        else:
            data['enrollment_date'] = datetime.now().isoformat()
        
        if 'expected_completion_date' in data and isinstance(data['expected_completion_date'], datetime):
            data['expected_completion_date'] = data['expected_completion_date'].isoformat()
        else:
            data['expected_completion_date'] = None
        
        if 'actual_completion_date' in data and isinstance(data['actual_completion_date'], datetime):
            data['actual_completion_date'] = data['actual_completion_date'].isoformat()
        else:
            data['actual_completion_date'] = None
        
        if 'payment_due_date' in data and isinstance(data['payment_due_date'], datetime):
            data['payment_due_date'] = data['payment_due_date'].isoformat()
        else:
            data['payment_due_date'] = None
        
        if 'payment_completed_date' in data and isinstance(data['payment_completed_date'], datetime):
            data['payment_completed_date'] = data['payment_completed_date'].isoformat()
        else:
            data['payment_completed_date'] = None
        
        # Convert JSON fields to proper format
        if 'special_requirements' in data and isinstance(data['special_requirements'], list):
            data['special_requirements'] = data['special_requirements']
        else:
            data['special_requirements'] = []
        
        if 'accommodations' in data and isinstance(data['accommodations'], dict):
            data['accommodations'] = data['accommodations']
        else:
            data['accommodations'] = {}
        
        if 'attendance_records' in data and isinstance(data['attendance_records'], list):
            data['attendance_records'] = [record if isinstance(record, str) else str(record) for record in data['attendance_records']]
        else:
            data['attendance_records'] = []
        
        if 'participation_activities' in data and isinstance(data['participation_activities'], list):
            data['participation_activities'] = data['participation_activities']
        else:
            data['participation_activities'] = []
        
        if 'metadata' in data and isinstance(data['metadata'], dict):
            data['metadata'] = data['metadata']
        else:
            data['metadata'] = {}
        
        # Calculate derived fields
        data['days_until_completion'] = self.get_days_until_completion()
        data['is_payment_overdue'] = self.is_payment_overdue()
        data['payment_overdue_days'] = self.get_payment_overdue_days()
        data['is_prerequisites_met'] = self.prerequisites_met
        data['enrollment_duration_days'] = self.get_enrollment_duration_days()
        data='performance_level'] = self.get_performance_level()
        data['completion_status'] = self.get_completion_status()
        
        # Include relationships if requested
        if include_relationships:
            if hasattr(self, 'student') and self.student:
                data['student'] = self.student.to_dict()
            else:
                data['student'] = None
            
            if hasattr(self, 'class_model') and self.class_model:
                data['class_model'] = self.class_model.to_dict()
            else:
                data['class_model'] = None
            
            if hasattr(self, 'program') and self.program:
                data['program'] = self.program.to_dict()
            else:
                data['program'] = None
            
            if hasattr(self, 'subject') and self.subject:
                data['subject'] = self.subject.to_dict()
            else:
                data['subject'] = None
        
        return data
    
    def update(self, **kwargs) -> None:
        """Update the model with new data."""
        # Handle special field updates
        if 'special_requirements' in kwargs and isinstance(kwargs['special_requirements'], list):
            self.special_requirements = kwargs['special_requirements']
        if 'accommodations' in kwargs and isinstance(kwargs['accommodations'], dict):
            self.accommodations = kwargs['accommodations']
        if 'attendance_records' in kwargs and isinstance(kwargs['attendance_records'], list):
            self.attendance_records = kwargs['attendance_records']
        if 'participation_activities' in kwargs and isinstance(kwargs['participation_activities'], list):
            self.participation_activities = kwargs['participation_activities']
        if 'metadata' in kwargs and isinstance(kwargs['metadata'], dict):
            self.metadata = kwargs['metadata']
        
        super().update(**kwargs)
    
    def validate(self) -> bool:
        """
        Validate the enrollment model data.
        
        Returns:
            True if valid, False otherwise
            
        Raises:
            ValidationError: If validation fails
        """
        try:
            # Call base validation
            super().validate()
            
            # Enrollment-specific validations
            if not self.id:
                raise ValidationError("Enrollment ID is required")
            
            if not self.enrollment_number:
                raise ValidationError("Enrollment number is required")
            
            if not self.code:
                raise ValidationError("Enrollment code is required")
            
            if not self.student_id:
                raise ValidationError("Student ID is required")
            
            if not self.class_id:
                raise ValidationError("Class ID is required")
            
            if not self.program_id:
                raise ValidationError("Program ID is required")
            
            if not self.subject_id:
                raise ValidationError("Subject ID is required")
            
            if not self.enrollment_type:
                raise ValidationError("Enrollment type is required")
            
            if not self.enrollment_semester:
                raise ValidationError("Enrollment semester is required")
            
            if not self.academic_year:
                raise ValidationError("Academic year is required")
            
            if not self.batch:
                raise ValidationError("Batch is required")
            
            if not self.section:
                raise ValidationError("Section is required")
            
            # Enrollment type validation
            valid_types = ['program_enrollment', 'class_enrollment', 'subject_enrollment']
            if self.enrollment_type not in valid_types:
                raise ValidationError(f"Invalid enrollment type: {self.enrollment_type}")
            
            # Semester validation
            if self.enrollment_semester < 1:
                raise ValidationError("Enrollment semester must be positive")
            
            # Academic year validation
            if len(self.academic_year) != 9 or self.academic_year[4] != '-':  # 2023-2024
                raise ValidationError("Academic year must be in format YYYY-YYYY")
            
            # Percentage validations
            if self.attendance_percentage < 0 or self.attendance_percentage > 100:
                raise ValidationError("Attendance percentage must be between 0 and 100")
            
            if self.assignment_completion_percentage < 0 or self.assignment_completion_percentage > 100:
                raise ValidationError("Assignment completion percentage must be between 0 and 100")
            
            if self.overall_progress_percentage < 0 or self.overall_progress_percentage > 100:
                raise ValidationError("Overall progress percentage must be between 0 and 100")
            
            if self.participation_score < 0 or self.participation_score > 100:
                raise ValidationError("Participation score must be between 0 and 100")
            
            if self.gpa_contribution < 0 or self.gpa_contribution > 4.0:
                raise ValidationError("GPA contribution must be between 0 and 4.0")
            
            # Fee validations
            if self.tuition_fee < 0:
                raise ValidationError("Tuition fee cannot be negative")
            
            if self.scholarship_amount < 0:
                raise ValidationError("Scholarship amount cannot be negative")
            
            if self.net_fee < 0:
                raise ValidationError("Net fee cannot be negative")
            
            # Payment status validation
            valid_payment_statuses = ['paid', 'pending', 'overdue', 'partial']
            if self.payment_status not in valid_payment_statuses:
                raise ValidationError(f"Invalid payment status: {self.payment_status}")
            
            # Status validation
            valid_statuses = ['active', 'dropped', 'completed', 'suspended']
            if self.status not in valid_statuses:
                raise ValidationError(f"Invalid status: {self.status}")
            
            # Grade validation
            if self.current_grade:
                valid_grades = ['A', 'B', 'C', 'D', 'F', 'A+', 'A-', 'B+', 'B-', 'C+', 'C-', 'P', 'NP', 'Pass', 'Fail']
                if self.current_grade not in valid_grades:
                    raise ValidationError(f"Invalid current grade: {self.current_grade}")
            
            if self.final_grade:
                valid_grades = ['A', 'B', 'C', 'D', 'F', 'A+', 'A-', 'B+', 'B-', 'C+', 'C-', 'P', 'NP', 'Pass', 'Fail']
                if self.final_grade not in valid_grades:
                    raise ValidationError(f"Invalid final grade: {self.final_grade}")
            
            # JSON fields validation
            if not isinstance(self.special_requirements, list):
                raise ValidationError("Special requirements must be a list")
            
            if not isinstance(self.accommodations, dict):
                raise ValidationError("Accommodations must be a dictionary")
            
            if not isinstance(self.attendance_records, list):
                raise ValidationError("Attendance records must be a list")
            
            if not isinstance(self.participation_activities, list):
                raise ValidationError("Participation activities must be a list")
            
            # Metadata validation
            if not isinstance(self.metadata, dict):
                raise ValidationError("Metadata must be a dictionary")
            
            logger.info(f"Enrollment {self.enrollment_number} validation passed")
            return True
            
        except Exception as e:
            logger.error(f"Enrollment validation error: {str(e)}")
            raise ValidationError(f"Enrollment validation error: {str(e)}")
    
    def generate_enrollment_number(self) -> None:
        """Generate enrollment number."""
        # Generate enrollment number based on student ID, academic year, and batch
        enrollment_prefix = f"ENR-{self.academic_year}-{self.batch}-{self.section}"
        enrollment_suffix = f"-{self.student_id[-6:]}"  # Last 6 digits of student ID
        self.enrollment_number = f"{enrollment_prefix}{enrollment_suffix}"
        logger.info(f"Generated enrollment number: {self.enrollment_number}")
    
    def add_attendance_record(self, date: datetime, status: str, notes: str = "") -> None:
        """
        Add attendance record.
        
        Args:
            date: Attendance date
            status: Attendance status (present, absent, late, excused)
            notes: Additional notes (optional)
        """
        valid_statuses = ['present', 'absent', 'late', 'excused']
        if status not in valid_statuses:
            raise ValidationError(f"Invalid attendance status: {status}")
        
        attendance_record = {
            'date': date.isoformat(),
            'status': status,
            'notes': notes,
            'recorded_at': datetime.now().isoformat()
        }
        
        self.attendance_records.append(attendance_record)
        self.calculate_attendance_percentage()
        self.updated_at = datetime.now()
        logger.info(f"Added attendance record for enrollment {self.enrollment_number}")
    
    def calculate_attendance_percentage(self) -> None:
        """Calculate attendance percentage."""
        if not self.attendance_records:
            self.attendance_percentage = 0.0
            return
        
        total_records = len(self.attendance_records)
        present_records = sum(1 for record in self.attendance_records if record.get('status') == 'present')
        
        if total_records > 0:
            self.attendance_percentage = (present_records / total_records) * 100
        else:
            self.attendance_percentage = 0.0
    
    def add_participation_activity(self, activity_name: str, score: float, 
                                  activity_date: datetime = None, notes: str = "") -> None:
        """
        Add participation activity.
        
        Args:
            activity_name: Name of the activity
            score: Score for the activity (0-100)
            activity_date: Activity date (optional)
            notes: Additional notes (optional)
        """
        if score < 0 or score > 100:
            raise ValidationError("Participation score must be between 0 and 100")
        
        if activity_date is None:
            activity_date = datetime.now()
        
        activity_record = {
            'activity_name': activity_name,
            'score': score,
            'activity_date': activity_date.isoformat(),
            'notes': notes,
            'recorded_at': datetime.now().isoformat()
        }
        
        self.participation_activities.append(activity_record)
        self.calculate_participation_score()
        self.updated_at = datetime.now()
        logger.info(f"Added participation activity for enrollment {self.enrollment_number}")
    
    def calculate_participation_score(self) -> None:
        """Calculate participation score."""
        if not self.participation_activities:
            self.participation_score = 0.0
            return
        
        total_activities = len(self.participation_activities)
        total_score = sum(activity.get('score', 0) for activity in self.participation_activities)
        
        if total_activities > 0:
            self.participation_score = total_score / total_activities
        else:
            self.participation_score = 0.0
    
    def update_progress(self, progress_percentage: float) -> None:
        """
        Update overall progress percentage.
        
        Args:
            progress_percentage: Progress percentage (0-100)
        """
        if progress_percentage < 0 or progress_percentage > 100:
            raise ValidationError("Progress percentage must be between 0 and 100")
        
        self.overall_progress_percentage = progress_percentage
        self.updated_at = datetime.now()
        logger.info(f"Updated progress for enrollment {self.enrollment_number}: {progress_percentage}%")
    
    def update_assignment_completion(self, completion_percentage: float) -> None:
        """
        Update assignment completion percentage.
        
        Args:
            completion_percentage: Completion percentage (0-100)
        """
        if completion_percentage < 0 or completion_percentage > 100:
            raise ValidationError("Assignment completion percentage must be between 0 and 100")
        
        self.assignment_completion_percentage = completion_percentage
        self.updated_at = datetime.now()
        logger.info(f"Updated assignment completion for enrollment {self.enrollment_number}: {completion_percentage}%")
    
    def set_grade(self, grade: str, grade_type: str = "current") -> None:
        """
        Set student grade.
        
        Args:
            grade: Grade to set
            grade_type: Type of grade (current, final)
        """
        valid_grades = ['A', 'B', 'C', 'D', 'F', 'A+', 'A-', 'B+', 'B-', 'C+', 'C-', 'P', 'NP', 'Pass', 'Fail']
        if grade not in valid_grades:
            raise ValidationError(f"Invalid grade: {grade}")
        
        if grade_type == "current":
            self.current_grade = grade
        elif grade_type == "final":
            self.final_grade = grade
        else:
            raise ValidationError(f"Invalid grade type: {grade_type}")
        
        # Update GPA contribution based on grade
        self.update_gpa_contribution(grade)
        
        self.updated_at = datetime.now()
        logger.info(f"Set {grade_type} grade for enrollment {self.enrollment_number}: {grade}")
    
    def update_gpa_contribution(self, grade: str) -> None:
        """
        Update GPA contribution based on grade.
        
        Args:
            grade: Grade to calculate GPA for
        """
        grade_to_gpa = {
            'A': 4.0, 'A+': 4.0, 'A-': 3.7,
            'B': 3.0, 'B+': 3.3, 'B-': 2.7,
            'C': 2.0, 'C+': 2.3, 'C-': 1.7,
            'D': 1.0, 'P': 3.0, 'NP': 0.0,
            'Pass': 3.0, 'Fail': 0.0
        }
        
        self.gpa_contribution = grade_to_gpa.get(grade, 0.0)
    
    def update_fee_info(self, tuition_fee: float = None, scholarship_amount: float = None) -> None:
        """
        Update fee information.
        
        Args:
            tuition_fee: Tuition fee (optional)
            scholarship_amount: Scholarship amount (optional)
        """
        if tuition_fee is not None:
            if tuition_fee < 0:
                raise ValidationError("Tuition fee cannot be negative")
            self.tuition_fee = tuition_fee
        
        if scholarship_amount is not None:
            if scholarship_amount < 0:
                raise ValidationError("Scholarship amount cannot be negative")
            self.scholarship_amount = scholarship_amount
        
        self.net_fee = self.tuition_fee - self.scholarship_amount
        self.updated_at = datetime.now()
        logger.info(f"Updated fee info for enrollment {self.enrollment_number}")
    
    def mark_payment_completed(self, payment_date: datetime = None) -> None:
        """
        Mark payment as completed.
        
        Args:
            payment_date: Payment date (optional)
        """
        self.payment_status = 'paid'
        self.payment_completed_date = payment_date or datetime.now()
        self.updated_at = datetime.now()
        logger.info(f"Marked payment completed for enrollment {self.enrollment_number}")
    
    def mark_payment_overdue(self, overdue_date: datetime = None) -> None:
        """
        Mark payment as overdue.
        
        Args:
            overdue_date: Overdue date (optional)
        """
        self.payment_status = 'overdue'
        if overdue_date:
            self.payment_due_date = overdue_date
        self.updated_at = datetime.now()
        logger.info(f"Marked payment overdue for enrollment {self.enrollment_number}")
    
    def complete_enrollment(self, completion_date: datetime = None) -> None:
        """
        Mark enrollment as completed.
        
        Args:
            completion_date: Completion date (optional)
        """
        self.status = 'completed'
        self.actual_completion_date = completion_date or datetime.now()
        self.updated_at = datetime.now()
        logger.info(f"Completed enrollment {self.enrollment_number}")
    
    def drop_enrollment(self, withdrawal_reason: str = "") -> None:
        """
        Drop the enrollment.
        
        Args:
            withdrawal_reason: Reason for withdrawal
        """
        self.status = 'dropped'
        self.withdrawal_reason = withdrawal_reason
        self.updated_at = datetime.now()
        logger.info(f"Dropped enrollment {self.enrollment_number} with reason: {withdrawal_reason}")
    
    def suspend_enrollment(self, suspension_reason: str = "") -> None:
        """
        Suspend the enrollment.
        
        Args:
            suspension_reason: Reason for suspension
        """
        self.status = 'suspended'
        if suspension_reason:
            self.metadata['suspension_reason'] = suspension_reason
        self.updated_at = datetime.now()
        logger.info(f"Suspended enrollment {self.enrollment_number} with reason: {suspension_reason}")
    
    def get_days_until_completion(self) -> Optional[int]:
        """
        Get days until expected completion.
        
        Returns:
            Days until completion, or None if not applicable
        """
        if self.expected_completion_date:
            delta = self.expected_completion_date - datetime.now()
            return max(0, delta.days)
        return None
    
    def get_enrollment_duration_days(self) -> Optional[int]:
        """
        Get enrollment duration in days.
        
        Returns:
            Enrollment duration in days, or None if not applicable
        """
        if self.enrollment_date and (self.actual_completion_date or self.expected_completion_date):
            end_date = self.actual_completion_date or self.expected_completion_date
            delta = end_date - self.enrollment_date
            return max(0, delta.days)
        return None
    
    def is_payment_overdue(self) -> bool:
        """
        Check if payment is overdue.
        
        Returns:
            True if payment is overdue
        """
        if self.payment_due_date and datetime.now() > self.payment_due_date:
            return self.payment_status != 'paid'
        return False
    
    def get_payment_overdue_days(self) -> Optional[int]:
        """
        Get payment overdue days.
        
        Returns:
            Payment overdue days, or None if not overdue
        """
        if self.is_payment_overdue() and self.payment_due_date:
            delta = datetime.now() - self.payment_due_date
            return delta.days
        return None
    
    def get_performance_level(self) -> str:
        """
        Get performance level based on overall progress.
        
        Returns:
            Performance level string
        """
        if self.overall_progress_percentage >= 90:
            return 'excellent'
        elif self.overall_progress_percentage >= 80:
            return 'good'
        elif self.overall_progress_percentage >= 70:
            return 'satisfactory'
        elif self.overall_progress_percentage >= 60:
            return 'needs_improvement'
        else:
            return 'poor'
    
    def get_completion_status(self) -> str:
        """
        Get completion status.
        
        Returns:
            Completion status string
        """
        if self.status == 'completed':
            return 'completed'
        elif self.status == 'dropped':
            return 'dropped'
        elif self.status == 'suspended':
            return 'suspended'
        elif self.overall_progress_percentage >= 90:
            return 'almost_complete'
        elif self.overall_progress_percentage >= 75:
            return 'in_progress_good'
        elif self.overall_progress_percentage >= 50:
            return 'in_progress'
        elif self.overall_progress_percentage > 0:
            return 'just_started'
        else:
            return 'not_started'
    
    def get_enrollment_summary(self) -> Dict[str, Any]:
        """
        Get enrollment summary.
        
        Returns:
            Enrollment summary dictionary
        """
        return {
            'id': self.id,
            'enrollment_number': self.enrollment_number,
            'enrollment_type': self.enrollment_type,
            'status': self.status,
            'enrollment_date': self.enrollment_date.isoformat() if self.enrollment_date else None,
            'expected_completion_date': self.expected_completion_date.isoformat() if self.expected_completion_date else None,
            'actual_completion_date': self.actual_completion_date.isoformat() if self.actual_completion_date else None,
            'attendance_percentage': self.attendance_percentage,
            'assignment_completion_percentage': self.assignment_completion_percentage,
            'overall_progress_percentage': self.overall_progress_percentage,
            'current_grade': self.current_grade,
            'final_grade': self.final_grade,
            'gpa_contribution': self.gpa_contribution,
            'performance_level': self.get_performance_level(),
            'completion_status': self.get_completion_status(),
            'payment_status': self.payment_status,
            'is_payment_overdue': self.is_payment_overdue()
        }
    
    def __repr__(self) -> str:
        """String representation of the enrollment model."""
        return f"<EnrollmentModel(enrollment_number='{self.enrollment_number}', status='{self.status}', student_id='{self.student_id}')>"