"""
Class Model for Database Operations

This module provides the SQLAlchemy model for Class entity.
It includes all fields and relationships for academic classes.

Author: Edu-Flow Team
"""

from typing import Dict, Any, Optional, List
from datetime import datetime, time
import logging

from sqlalchemy import Column, String, Integer, Text, DateTime, JSON, Boolean, ForeignKey, Time
from sqlalchemy.orm import relationship

from src.infrastructure.models.base_model import BaseModel
from src.core.exceptions import ValidationError
from src.core.logging import get_logger

logger = get_logger(__name__)


class ClassModel(BaseModel):
    """
    SQLAlchemy model for Class entity.
    
    Represents academic classes with scheduling, enrollment management, and resource allocation.
    """
    __tablename__ = "classes"
    
    # Class identification
    code = Column(String(50), nullable=False, index=True)
    name = Column(String(200), nullable=False, index=True)
    description = Column(Text)
    subject_id = Column(String(50), ForeignKey("subjects.id"), nullable=False)
    
    # Academic details
    semester = Column(Integer, nullable=False)
    academic_year = Column(String(10), nullable=False)  # 2023-2024
    batch = Column(String(20), nullable=False)  # A, B, C, etc.
    section = Column(String(5), nullable=False)  # 1, 2, 3, etc.
    
    # Scheduling details
    start_time = Column(Time, nullable=False)
    end_time = Column(Time, nullable=False)
    start_date = Column(DateTime, nullable=False)
    end_date = Column(DateTime, nullable=False)
    days_of_week = Column(JSON, default=list)  # ["Monday", "Wednesday", "Friday"]
    location = Column(String(100))
    
    # Resource allocation
    allocated_teacher_id = Column(String(50), ForeignKey("users.id"), nullable=False)
    allocated_room_id = Column(String(50), ForeignKey("rooms.id"), nullable=False)
    allocated_laboratory_id = Column(String(50), ForeignKey("laboratories.id"))
    
    # Capacity and enrollment
    max_capacity = Column(Integer, nullable=False, default=0)
    current_enrollment = Column(Integer, nullable=False, default=0)
    waitlist_capacity = Column(Integer, default=0)
    
    # Class status
    status = Column(String(20), nullable=False, default="scheduled")  # scheduled, ongoing, completed, cancelled
    is_virtual = Column(Boolean, default=False)
    is_mandatory = Column(Boolean, default=True)
    
    # Assessment details
    assessment_type = Column(String(50))  # quiz, assignment, exam, project
    weightage = Column(Integer, default=0)  # percentage
    passing_marks = Column(Integer, default=0)
    
    # Schedule metadata
    schedule_metadata = Column(JSON, default=dict)  # recurring schedules, holidays, etc.
    
    # Class metadata
    metadata = Column(JSON, default=dict)
    
    # Relationships
    subject = relationship("SubjectModel", back_populates="classes")
    teacher = relationship("UserModel", foreign_keys=[allocated_teacher_id])
    room = relationship("RoomModel")
    laboratory = relationship("LaboratoryModel")
    enrollments = relationship("EnrollmentModel", back_populates="class")
    assessments = relationship("AssessmentModel")
    
    def __init__(self, **kwargs):
        """Initialize the class model with provided data."""
        # Set default values for optional fields
        kwargs.setdefault('semester', 1)
        kwargs.setdefault('academic_year', '2023-2024')
        kwargs.setdefault('batch', 'A')
        kwargs.setdefault('section', '1')
        kwargs.setdefault('start_time', time(9, 0))
        kwargs.setdefault('end_time', time(10, 30))
        kwargs.setdefault('days_of_week', [])
        kwargs.setdefault('max_capacity', 0)
        kwargs.setdefault('current_enrollment', 0)
        kwargs.setdefault('waitlist_capacity', 0)
        kwargs.setdefault('status', 'scheduled')
        kwargs.setdefault('is_virtual', False)
        kwargs.setdefault('is_mandatory', True)
        kwargs.setdefault('assessment_type', None)
        kwargs.setdefault('weightage', 0)
        kwargs.setdefault('passing_marks', 0)
        kwargs.setdefault('schedule_metadata', {})
        kwargs.setdefault('metadata', {})
        
        super().__init__(**kwargs)
    
    def to_dict(self, include_relationships: bool = False) -> Dict[str, Any]:
        """
        Convert the model to a dictionary.
        
        Args:
            include_relationships: Whether to include relationship data
            
        Returns:
            Dictionary representation of the model
        """
        data = super().to_dict()
        
        # Convert time fields to string format
        if 'start_time' in data and isinstance(data['start_time'], time):
            data['start_time'] = data['start_time'].strftime('%H:%M:%S')
        else:
            data['start_time'] = '09:00:00'
        
        if 'end_time' in data and isinstance(data['end_time'], time):
            data['end_time'] = data['end_time'].strftime('%H:%M:%S')
        else:
            data['end_time'] = '10:30:00'
        
        if 'start_date' in data and isinstance(data['start_date'], datetime):
            data['start_date'] = data['start_date'].isoformat()
        else:
            data['start_date'] = datetime.now().isoformat()
        
        if 'end_date' in data and isinstance(data['end_date'], datetime):
            data['end_date'] = data['end_date'].isoformat()
        else:
            data['end_date'] = datetime.now().isoformat()
        
        # Convert JSON fields to proper format
        if 'days_of_week' in data and isinstance(data['days_of_week'], list):
            data['days_of_week'] = data['days_of_week']
        else:
            data['days_of_week'] = []
        
        if 'schedule_metadata' in data and isinstance(data['schedule_metadata'], dict):
            data['schedule_metadata'] = data['schedule_metadata']
        else:
            data['schedule_metadata'] = {}
        
        if 'metadata' in data and isinstance(data['metadata'], dict):
            data['metadata'] = data['metadata']
        else:
            data['metadata'] = {}
        
        # Calculate additional fields
        data['available_capacity'] = data['max_capacity'] - data['current_enrollment']
        data['is_full'] = data['available_capacity'] <= 0
        data['enrollment_percentage'] = (data['current_enrollment'] / data['max_capacity'] * 100) if data['max_capacity'] > 0 else 0
        
        # Include relationships if requested
        if include_relationships:
            if hasattr(self, 'subject') and self.subject:
                data['subject'] = self.subject.to_dict()
            else:
                data['subject'] = None
            
            if hasattr(self, 'teacher') and self.teacher:
                data['teacher'] = self.teacher.to_dict()
            else:
                data['teacher'] = None
            
            if hasattr(self, 'room') and self.room:
                data['room'] = self.room.to_dict()
            else:
                data['room'] = None
            
            if hasattr(self, 'laboratory') and self.laboratory:
                data['laboratory'] = self.laboratory.to_dict()
            else:
                data['laboratory'] = None
            
            if hasattr(self, 'enrollments') and self.enrollments:
                data['enrollments'] = [enrollment.to_dict() for enrollment in self.enrollments]
            else:
                data['enrollments'] = []
        
        return data
    
    def update(self, **kwargs) -> None:
        """Update the model with new data."""
        # Handle special field updates
        if 'schedule_metadata' in kwargs and isinstance(kwargs['schedule_metadata'], dict):
            self.schedule_metadata = kwargs['schedule_metadata']
        if 'metadata' in kwargs and isinstance(kwargs['metadata'], dict):
            self.metadata = kwargs['metadata']
        
        super().update(**kwargs)
    
    def validate(self) -> bool:
        """
        Validate the class model data.
        
        Returns:
            True if valid, False otherwise
            
        Raises:
            ValidationError: If validation fails
        """
        try:
            # Call base validation
            super().validate()
            
            # Class-specific validations
            if not self.code:
                raise ValidationError("Class code is required")
            
            if not self.name:
                raise ValidationError("Class name is required")
            
            if not self.subject_id:
                raise ValidationError("Subject ID is required")
            
            if not self.allocated_teacher_id:
                raise ValidationError("Teacher ID is required")
            
            if not self.allocated_room_id:
                raise ValidationError("Room ID is required")
            
            if self.semester < 1 or self.semester > 12:
                raise ValidationError("Semester must be between 1 and 12")
            
            if not self.academic_year or len(self.academic_year) != 9:  # 2023-2024
                raise ValidationError("Academic year must be in format YYYY-YYYY")
            
            if not self.batch or not self.section:
                raise ValidationError("Batch and section are required")
            
            # Time validation
            if self.start_time >= self.end_time:
                raise ValidationError("Start time must be before end time")
            
            if self.start_date > self.end_date:
                raise ValidationError("Start date must be before or equal to end date")
            
            # Capacity validation
            if self.max_capacity <= 0:
                raise ValidationError("Maximum capacity must be positive")
            
            if self.current_enrollment < 0:
                raise ValidationError("Current enrollment cannot be negative")
            
            if self.current_enrollment > self.max_capacity:
                raise ValidationError("Current enrollment cannot exceed maximum capacity")
            
            if self.waitlist_capacity < 0:
                raise ValidationError("Waitlist capacity cannot be negative")
            
            # Days of week validation
            if not isinstance(self.days_of_week, list):
                raise ValidationError("Days of week must be a list")
            
            valid_days = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]
            for day in self.days_of_week:
                if day not in valid_days:
                    raise ValidationError(f"Invalid day of week: {day}")
            
            # Schedule metadata validation
            if not isinstance(self.schedule_metadata, dict):
                raise ValidationError("Schedule metadata must be a dictionary")
            
            # Metadata validation
            if not isinstance(self.metadata, dict):
                raise ValidationError("Metadata must be a dictionary")
            
            # Assessment validation
            if self.assessment_type:
                valid_assessment_types = ["quiz", "assignment", "exam", "project", "presentation"]
                if self.assessment_type not in valid_assessment_types:
                    raise ValidationError(f"Invalid assessment type: {self.assessment_type}")
            
            if self.weightage < 0 or self.weightage > 100:
                raise ValidationError("Weightage must be between 0 and 100")
            
            if self.passing_marks < 0:
                raise ValidationError("Passing marks cannot be negative")
            
            logger.info(f"Class {self.code} validation passed")
            return True
            
        except Exception as e:
            logger.error(f"Class validation error: {str(e)}")
            raise ValidationError(f"Class validation error: {str(e)}")
    
    def check_capacity(self) -> bool:
        """
        Check if class has capacity for more students.
        
        Returns:
            True if capacity available
        """
        return self.current_enrollment < self.max_capacity
    
    def check_enrollment(self, student_id: str) -> bool:
        """
        Check if student is enrolled in this class.
        
        Args:
            student_id: Student ID to check
            
        Returns:
            True if enrolled
        """
        # This would check the enrollment relationship in practice
        # For now, return False as placeholder
        return False
    
    def add_enrollment(self, student_id: str) -> bool:
        """
        Add a student enrollment.
        
        Args:
            student_id: Student ID to enroll
            
        Returns:
            True if enrolled successfully
        """
        if self.check_capacity():
            self.current_enrollment += 1
            self.updated_at = datetime.now()
            logger.info(f"Enrolled student {student_id} in class {self.code}")
            return True
        
        return False
    
    def remove_enrollment(self, student_id: str) -> bool:
        """
        Remove a student enrollment.
        
        Args:
            student_id: Student ID to unenroll
            
        Returns:
            True if unenrolled successfully
        """
        if self.current_enrollment > 0:
            self.current_enrollment -= 1
            self.updated_at = datetime.now()
            logger.info(f"Unenrolled student {student_id} from class {self.code}")
            return True
        
        return False
    
    def get_schedule_info(self) -> Dict[str, Any]:
        """
        Get detailed schedule information.
        
        Returns:
            Schedule information dictionary
        """
        return {
            'start_time': self.start_time.strftime('%H:%M:%S'),
            'end_time': self.end_time.strftime('%H:%M:%S'),
            'start_date': self.start_date.isoformat(),
            'end_date': self.end_date.isoformat(),
            'days_of_week': self.days_of_week,
            'duration_minutes': int((datetime.combine(datetime.min, self.end_time) - datetime.combine(datetime.min, self.start_time)).total_seconds() / 60),
            'total_days': len(self.days_of_week),
            'week_days': self.days_of_week
        }
    
    def get_capacity_info(self) -> Dict[str, Any]:
        """
        Get capacity information.
        
        Returns:
            Capacity information dictionary
        """
        return {
            'max_capacity': self.max_capacity,
            'current_enrollment': self.current_enrollment,
            'available_capacity': self.max_capacity - self.current_enrollment,
            'waitlist_capacity': self.waitlist_capacity,
            'is_full': self.current_enrollment >= self.max_capacity,
            'enrollment_percentage': (self.current_enrollment / self.max_capacity * 100) if self.max_capacity > 0 else 0
        }
    
    def update_schedule(self, **schedule_data) -> None:
        """
        Update schedule information.
        
        Args:
            **schedule_data: Schedule data to update
        """
        if 'start_time' in schedule_data:
            self.start_time = schedule_data['start_time']
        if 'end_time' in schedule_data:
            self.end_time = schedule_data['end_time']
        if 'start_date' in schedule_data:
            self.start_date = schedule_data['start_date']
        if 'end_date' in schedule_data:
            self.end_date = schedule_data['end_date']
        if 'days_of_week' in schedule_data:
            self.days_of_week = schedule_data['days_of_week']
        if 'location' in schedule_data:
            self.location = schedule_data['location']
        
        self.updated_at = datetime.now()
        logger.info(f"Updated schedule for class {self.code}")
    
    def update_capacity(self, max_capacity: int, waitlist_capacity: int = 0) -> None:
        """
        Update class capacity.
        
        Args:
            max_capacity: Maximum capacity
            waitlist_capacity: Waitlist capacity
        """
        if max_capacity < 0:
            raise ValidationError("Max capacity cannot be negative")
        
        if waitlist_capacity < 0:
            raise ValidationError("Waitlist capacity cannot be negative")
        
        # Ensure current enrollment doesn't exceed new max capacity
        if self.current_enrollment > max_capacity:
            self.current_enrollment = max_capacity
        
        self.max_capacity = max_capacity
        self.waitlist_capacity = waitlist_capacity
        self.updated_at = datetime.now()
        logger.info(f"Updated capacity for class {self.code}")
    
    def cancel_class(self, reason: str = "") -> None:
        """
        Cancel the class.
        
        Args:
            reason: Reason for cancellation
        """
        self.status = 'cancelled'
        self.metadata['cancellation_reason'] = reason
        self.updated_at = datetime.now()
        logger.info(f"Cancelled class {self.code} with reason: {reason}")
    
    def complete_class(self) -> None:
        """
        Mark class as completed.
        """
        self.status = 'completed'
        self.updated_at = datetime.now()
        logger.info(f"Marked class {self.code} as completed")
    
    def start_class(self) -> None:
        """
        Start the class.
        """
        self.status = 'ongoing'
        self.updated_at = datetime.now()
        logger.info(f"Started class {self.code}")
    
    def is_scheduled(self) -> bool:
        """
        Check if class is scheduled.
        
        Returns:
            True if scheduled
        """
        return self.status == 'scheduled'
    
    def is_ongoing(self) -> bool:
        """
        Check if class is ongoing.
        
        Returns:
            True if ongoing
        """
        return self.status == 'ongoing'
    
    def is_completed(self) -> bool:
        """
        Check if class is completed.
        
        Returns:
            True if completed
        """
        return self.status == 'completed'
    
    def is_cancelled(self) -> bool:
        """
        Check if class is cancelled.
        
        Returns:
            True if cancelled
        """
        return self.status == 'cancelled'
    
    def get_class_type(self) -> str:
        """
        Get class type.
        
        Returns:
            Class type (regular, virtual, lab)
        """
        if self.is_virtual:
            return 'virtual'
        elif self.allocated_laboratory_id:
            return 'laboratory'
        else:
            return 'regular'
    
    def __repr__(self) -> str:
        """String representation of the class model."""
        return f"<ClassModel(code='{self.code}', name='{self.name}', status='{self.status}')>"