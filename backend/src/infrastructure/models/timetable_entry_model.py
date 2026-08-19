"""
Timetable Entry Model for Database Operations

This module provides the SQLAlchemy model for Timetable Entry entity.
It includes all fields and relationships for individual timetable schedule entries.

Author: Edu-Flow Team
"""

from typing import Dict, Any, Optional, List
from datetime import datetime, time, timedelta, date
import logging

from sqlalchemy import Column, String, Integer, Text, DateTime, JSON, Boolean, ForeignKey, Time
from sqlalchemy.orm import relationship

from infrastructure.models.base_model import BaseModel
from core.exceptions import ValidationError
from core.logging import get_logger

logger = get_logger(__name__)


class TimetableEntryModel(BaseModel):
    """
    SQLAlchemy model for Timetable Entry entity.
    
    Represents individual schedule entries within a timetable.
    """
    __tablename__ = "timetable_entries"
    
    # Entry identification
    id = Column(String(50), primary_key=True)
    code = Column(String(50), nullable=False, unique=True, index=True)
    entry_number = Column(String(50), nullable=False, index=True)
    timetable_id = Column(String(50), ForeignKey("timetables.id"), nullable=False)
    
    # Entry categorization
    type = Column(String(50), nullable=False)  # lecture, tutorial, lab, exam, break, meeting
    subject_code = Column(String(50), nullable=False)  # Associated subject code
    course_code = Column(String(50))  # Associated course code
    
    # Time and date information
    day_of_week = Column(String(20), nullable=False)  # Monday, Tuesday, etc.
    start_time = Column(Time, nullable=False)
    end_time = Column(Time, nullable=False)
    duration_minutes = Column(Integer, nullable=False)
    date = Column(DateTime)  # Specific date if not recurring
    is_recurring = Column(Boolean, default=True)  # Whether entry repeats weekly
    recurring_pattern = Column(JSON, default=list)  # Pattern for recurring entries
    
    # Related entities
    teacher_id = Column(String(50), ForeignKey("users.id"), nullable=False)
    class_id = Column(String(50), ForeignKey("classes.id"), nullable=False)
    room_id = Column(String(50), ForeignKey("rooms.id"))
    laboratory_id = Column(String(50), ForeignKey("laboratories.id"))
    subject_id = Column(String(50), ForeignKey("subjects.id"))
    
    # Entry details
    title = Column(String(200), nullable=False)
    description = Column(Text)
    activity = Column(String(100))  # Specific activity name
    topic = Column(String(200))  # Current topic being covered
    syllabus_coverage = Column(JSON, default=list)  # Topics covered in this session
    
    # Entry status
    status = Column(String(20), default="scheduled")  # scheduled, ongoing, completed, cancelled, rescheduled
    is_mandatory = Column(Boolean, default=True)
    requires_attendance = Column(Boolean, default=True)
    is_virtual = Column(Boolean, default=False)
    
    # Resource allocation
    max_capacity = Column(Integer)  # Maximum students for this entry
    current_enrollment = Column(Integer, default=0)  # Current enrollment count
    requires_resources = Column(JSON, default=list)  # Required resources
    
    # Entry metadata
    metadata = Column(JSON, default=dict)
    tags = Column(JSON, default=list)  # List of tags
    attachments = Column(JSON, default=list)  # List of attachment paths/URLs
    notes = Column(Text)  # Additional notes
    
    # Attendance tracking
    attendance_recorded = Column(Boolean, default=False)
    attendance_records = Column(JSON, default=list)  # List of attendance records
    attendance_percentage = Column(Float, default=0.0)  # Overall attendance percentage
    
    # Entry performance
    engagement_score = Column(Float, default=0.0)  # 0-100
    feedback_score = Column(Float, default=0.0)  # 0-5
    completion_status = Column(String(20), default="not_started")  # not_started, in_progress, completed
    
    # Relationships
    timetable = relationship("TimetableModel", back_populates="timetable_entries")
    teacher = relationship("UserModel", foreign_keys=[teacher_id])
    class_model = relationship("ClassModel")
    room = relationship("RoomModel")
    laboratory = relationship("LaboratoryModel")
    subject = relationship("SubjectModel")
    assessments = relationship("AssessmentModel")
    
    def __init__(self, **kwargs):
        """Initialize the timetable entry model with provided data."""
        # Set default values for optional fields
        kwargs.setdefault('type', 'lecture')
        kwargs.setdefault('is_recurring', True)
        kwargs.setdefault('recurring_pattern', [])
        kwargs.setdefault('is_mandatory', True)
        kwargs.setdefault('requires_attendance', True)
        kwargs.setdefault('is_virtual', False)
        kwargs.setdefault('current_enrollment', 0)
        kwargs.setdefault('requires_resources', [])
        kwargs.setdefault('metadata', {})
        kwargs.setdefault('tags', [])
        kwargs.setdefault('attachments', [])
        kwargs.setdefault('attendance_records', [])
        kwargs.setdefault('attendance_percentage', 0.0)
        kwargs.setdefault('engagement_score', 0.0)
        kwargs.setdefault('feedback_score', 0.0)
        kwargs.setdefault('completion_status', 'not_started')
        
        # Set default date and time
        now = datetime.now()
        if 'day_of_week' not in kwargs:
            kwargs['day_of_week'] = now.strftime('%A')
        if 'start_time' not in kwargs:
            kwargs['start_time'] = time(9, 0)
        if 'end_time' not in kwargs:
            kwargs['end_time'] = time(10, 30)
        if 'date' not in kwargs:
            kwargs['date'] = now
        if 'duration_minutes' not in kwargs:
            duration = (datetime.combine(date.min, kwargs['end_time']) - datetime.combine(date.min, kwargs['start_time'])).total_seconds() / 60
            kwargs['duration_minutes'] = int(duration)
        
        super().__init__(**kwargs)
        
        # Generate entry number if not provided
        if not self.entry_number:
            self.generate_entry_number()
    
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
        if 'date' in data and isinstance(data['date'], datetime):
            data['date'] = data['date'].isoformat()
        else:
            data['date'] = datetime.now().isoformat()
        
        # Convert time fields to string format
        if 'start_time' in data and isinstance(data['start_time'], time):
            data['start_time'] = data['start_time'].strftime('%H:%M')
        else:
            data['start_time'] = '09:00'
        
        if 'end_time' in data and isinstance(data['end_time'], time):
            data['end_time'] = data['end_time'].strftime('%H:%M')
        else:
            data['end_time'] = '10:30'
        
        # Convert JSON fields to proper format
        if 'recurring_pattern' in data and isinstance(data['recurring_pattern'], list):
            data['recurring_pattern'] = data['recurring_pattern']
        else:
            data['recurring_pattern'] = []
        
        if 'syllabus_coverage' in data and isinstance(data['syllabus_coverage'], list):
            data['syllabus_coverage'] = data['syllabus_coverage']
        else:
            data['syllabus_coverage'] = []
        
        if 'requires_resources' in data and isinstance(data['requires_resources'], list):
            data['requires_resources'] = data['requires_resources']
        else:
            data['requires_resources'] = []
        
        if 'metadata' in data and isinstance(data['metadata'], dict):
            data['metadata'] = data['metadata']
        else:
            data['metadata'] = {}
        
        if 'tags' in data and isinstance(data['tags'], list):
            data['tags'] = data['tags']
        else:
            data['tags'] = []
        
        if 'attachments' in data and isinstance(data['attachments'], list):
            data['attachments'] = data['attachments']
        else:
            data['attachments'] = []
        
        if 'attendance_records' in data and isinstance(data['attendance_records'], list):
            data['attendance_records'] = data['attendance_records']
        else:
            data['attendance_records'] = []
        
        # Calculate derived fields
        data='is_overdue'] = self.is_overdue()
        data['is_upcoming'] = self.is_upcoming()
        data['is_current_session'] = self.is_current_session()
        data['time_until_start'] = self.get_time_until_start()
        data['time_until_end'] = self.get_time_until_end()
        data['entry_status'] = self.get_entry_status()
        data='is_full'] = self.is_full()
        data['enrollment_percentage'] = self.get_enrollment_percentage()
        data['entry_summary'] = self.get_entry_summary()
        data='resource_availability'] = self.get_resource_availability()
        data['performance_metrics'] = self.get_performance_metrics()
        
        # Include relationships if requested
        if include_relationships:
            if hasattr(self, 'timetable') and self.timetable:
                data['timetable'] = self.timetable.to_dict()
            else:
                data['timetable'] = None
            
            if hasattr(self, 'teacher') and self.teacher:
                data['teacher'] = self.teacher.to_dict()
            else:
                data['teacher'] = None
            
            if hasattr(self, 'class_model') and self.class_model:
                data['class_model'] = self.class_model.to_dict()
            else:
                data['class_model'] = None
            
            if hasattr(self, 'room') and self.room:
                data['room'] = self.room.to_dict()
            else:
                data['room'] = None
            
            if hasattr(self, 'laboratory') and self.laboratory:
                data['laboratory'] = self.laboratory.to_dict()
            else:
                data['laboratory'] = None
            
            if hasattr(self, 'subject') and self.subject:
                data['subject'] = self.subject.to_dict()
            else:
                data['subject'] = None
            
            if hasattr(self, 'assessments') and self.assessments:
                data['assessments'] = [assessment.to_dict() for assessment in self.assessments]
            else:
                data['assessments'] = []
        
        return data
    
    def update(self, **kwargs) -> None:
        """Update the model with new data."""
        # Handle special field updates
        if 'recurring_pattern' in kwargs and isinstance(kwargs['recurring_pattern'], list):
            self.recurring_pattern = kwargs['recurring_pattern']
        if 'syllabus_coverage' in kwargs and isinstance(kwargs['syllabus_coverage'], list):
            self.syllabus_coverage = kwargs['syllabus_coverage']
        if 'requires_resources' in kwargs and isinstance(kwargs['requires_resources'], list):
            self.requires_resources = kwargs['requires_resources']
        if 'metadata' in kwargs and isinstance(kwargs['metadata'], dict):
            self.metadata = kwargs['metadata']
        if 'tags' in kwargs and isinstance(kwargs['tags'], list):
            self.tags = kwargs['tags']
        if 'attachments' in kwargs and isinstance(kwargs['attachments'], list):
            self.attachments = kwargs['attachments']
        if 'attendance_records' in kwargs and isinstance(kwargs['attendance_records'], list):
            self.attendance_records = kwargs['attendance_records']
        
        super().update(**kwargs)
    
    def validate(self) -> bool:
        """
        Validate the timetable entry model data.
        
        Returns:
            True if valid, False otherwise
            
        Raises:
            ValidationError: If validation fails
        """
        try:
            # Call base validation
            super().validate()
            
            # Entry-specific validations
            if not self.id:
                raise ValidationError("Entry ID is required")
            
            if not self.code:
                raise ValidationError("Entry code is required")
            
            if not self.entry_number:
                raise ValidationError("Entry number is required")
            
            if not self.timetable_id:
                raise ValidationError("Timetable ID is required")
            
            if not self.type:
                raise ValidationError("Entry type is required")
            
            if not self.subject_code:
                raise ValidationError("Subject code is required")
            
            if not self.day_of_week:
                raise ValidationError("Day of week is required")
            
            if not self.start_time:
                raise ValidationError("Start time is required")
            
            if not self.end_time:
                raise ValidationError("End time is required")
            
            if not self.duration_minutes:
                raise ValidationError("Duration minutes is required")
            
            if not self.teacher_id:
                raise ValidationError("Teacher ID is required")
            
            if not self.class_id:
                raise ValidationError("Class ID is required")
            
            # Type validation
            valid_types = ['lecture', 'tutorial', 'lab', 'exam', 'break', 'meeting', 'seminar', 'workshop']
            if self.type not in valid_types:
                raise ValidationError(f"Invalid entry type: {self.type}")
            
            # Day validation
            valid_days = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday']
            if self.day_of_week not in valid_days:
                raise ValidationError(f"Invalid day of week: {self.day_of_week}")
            
            # Time validation
            if self.start_time >= self.end_time:
                raise ValidationError("Start time must be before end time")
            
            # Duration validation
            calculated_duration = int((datetime.combine(date.min, self.end_time) - datetime.combine(date.min, self.start_time)).total_seconds() / 60)
            if self.duration_minutes != calculated_duration:
                raise ValidationError(f"Duration minutes does not match time difference: {calculated_duration}")
            
            if self.duration_minutes <= 0:
                raise ValidationError("Duration minutes must be positive")
            
            # Status validation
            valid_statuses = ['scheduled', 'ongoing', 'completed', 'cancelled', 'rescheduled']
            if self.status not in valid_statuses:
                raise ValidationError(f"Invalid status: {self.status}")
            
            # Completion status validation
            valid_completion_statuses = ['not_started', 'in_progress', 'completed']
            if self.completion_status not in valid_completion_statuses:
                raise ValidationError(f"Invalid completion status: {self.completion_status}")
            
            # Capacity validations
            if self.max_capacity is not None and self.max_capacity <= 0:
                raise ValidationError("Maximum capacity must be positive or null")
            
            if self.current_enrollment < 0:
                raise ValidationError("Current enrollment cannot be negative")
            
            if self.max_capacity is not None and self.current_enrollment > self.max_capacity:
                raise ValidationError("Current enrollment cannot exceed maximum capacity")
            
            # Score validations
            if self.engagement_score < 0 or self.engagement_score > 100:
                raise ValidationError("Engagement score must be between 0 and 100")
            
            if self.feedback_score < 0 or self.feedback_score > 5:
                raise ValidationError("Feedback score must be between 0 and 5")
            
            if self.attendance_percentage < 0 or self.attendance_percentage > 100:
                raise ValidationError("Attendance percentage must be between 0 and 100")
            
            # JSON fields validation
            if not isinstance(self.recurring_pattern, list):
                raise ValidationError("Recurring pattern must be a list")
            
            if not isinstance(self.syllabus_coverage, list):
                raise ValidationError("Syllabus coverage must be a list")
            
            if not isinstance(self.requires_resources, list):
                raise ValidationError("Requires resources must be a list")
            
            if not isinstance(self.metadata, dict):
                raise ValidationError("Metadata must be a dictionary")
            
            if not isinstance(self.tags, list):
                raise ValidationError("Tags must be a list")
            
            if not isinstance(self.attachments, list):
                raise ValidationError("Attachments must be a list")
            
            if not isinstance(self.attendance_records, list):
                raise ValidationError("Attendance records must be a list")
            
            logger.info(f"Timetable entry {self.code} validation passed")
            return True
            
        except Exception as e:
            logger.error(f"Timetable entry validation error: {str(e)}")
            raise ValidationError(f"Timetable entry validation error: {str(e)}")
    
    def generate_entry_number(self) -> None:
        """Generate entry number."""
        # Generate entry number based on timetable ID, day, and time
        time_part = f"{self.start_time.strftime('%H%M')}-{self.end_time.strftime('%H%M')}"
        entry_number = f"TTE-{self.timetable_id[-6:]}-{self.day_of_week[:3]}-{time_part}"
        self.entry_number = entry_number
        logger.info(f"Generated entry number: {entry_number}")
    
    def mark_start(self) -> None:
        """Mark entry as started."""
        self.status = 'ongoing'
        self.metadata['start_time'] = datetime.now().isoformat()
        self.updated_at = datetime.now()
        logger.info(f"Marked entry {self.code} as started")
    
    def mark_completion(self, completion_notes: str = "") -> None:
        """
        Mark entry as completed.
        
        Args:
            completion_notes: Notes about completion (optional)
        """
        self.status = 'completed'
        self.completion_status = 'completed'
        self.metadata['completion_time'] = datetime.now().isoformat()
        
        if completion_notes:
            self.metadata['completion_notes'] = completion_notes
        
        self.updated_at = datetime.now()
        logger.info(f"Marked entry {self.code} as completed")
    
    def cancel_entry(self, cancellation_reason: str = "") -> None:
        """
        Cancel the entry.
        
        Args:
            cancellation_reason: Reason for cancellation (optional)
        """
        self.status = 'cancelled'
        
        if cancellation_reason:
            self.metadata['cancellation_reason'] = cancellation_reason
            self.metadata['cancellation_time'] = datetime.now().isoformat()
        
        self.updated_at = datetime.now()
        logger.info(f"Cancelled entry {self.code}: {cancellation_reason}")
    
    def reschedule_entry(self, new_start_time: time, new_end_time: time, 
                         new_date: datetime = None, reschedule_reason: str = "") -> None:
        """
        Reschedule the entry.
        
        Args:
            new_start_time: New start time
            new_end_time: New end time
            new_date: New date (optional)
            reschedule_reason: Reason for rescheduling (optional)
        """
        if new_start_time >= new_end_time:
            raise ValidationError("New start time must be before new end time")
        
        self.start_time = new_start_time
        self.end_time = new_end_time
        self.duration_minutes = int((datetime.combine(date.min, new_end_time) - datetime.combine(date.min, new_start_time)).total_seconds() / 60)
        
        if new_date:
            self.date = new_date
        
        self.status = 'rescheduled'
        
        if reschedule_reason:
            self.metadata['reschedule_reason'] = reschedule_reason
            self.metadata['reschedule_time'] = datetime.now().isoformat()
        
        self.updated_at = datetime.now()
        logger.info(f"Rescheduled entry {self.code} to {new_start_time}-{new_end_time}")
    
    def add_attendance_record(self, student_id: str, status: str, notes: str = "") -> None:
        """
        Add attendance record for a student.
        
        Args:
            student_id: Student ID
            status: Attendance status (present, absent, late, excused)
            notes: Additional notes (optional)
        """
        valid_statuses = ['present', 'absent', 'late', 'excused']
        if status not in valid_statuses:
            raise ValidationError(f"Invalid attendance status: {status}")
        
        attendance_record = {
            'student_id': student_id,
            'status': status,
            'notes': notes,
            'recorded_at': datetime.now().isoformat()
        }
        
        self.attendance_records.append(attendance_record)
        self.calculate_attendance_percentage()
        self.updated_at = datetime.now()
        logger.info(f"Added attendance record for student {student_id} in entry {self.code}")
    
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
    
    def update_syllabus_coverage(self, topics_covered: List[str]) -> None:
        """
        Update syllabus coverage.
        
        Args:
            topics_covered: List of topics covered
        """
        self.syllabus_coverage = topics_covered
        self.updated_at = datetime.now()
        logger.info(f"Updated syllabus coverage for entry {self.code}")
    
    def add_required_resource(self, resource_type: str, resource_id: str, quantity: int = 1) -> None:
        """
        Add a required resource.
        
        Args:
            resource_type: Type of resource
            resource_id: Resource ID
            quantity: Required quantity (default: 1)
        """
        resource = {
            'resource_type': resource_type,
            'resource_id': resource_id,
            'quantity': quantity
        }
        
        # Check if resource already exists
        existing_resources = [r for r in self.requires_resources 
                           if r['resource_type'] == resource_type and r['resource_id'] == resource_id]
        
        if existing_resources:
            # Update quantity
            existing_resources[0]['quantity'] = quantity
        else:
            # Add new resource
            self.requires_resources.append(resource)
        
        self.updated_at = datetime.now()
        logger.info(f"Added required resource {resource_type}:{resource_id} to entry {self.code}")
    
    def remove_required_resource(self, resource_type: str, resource_id: str) -> None:
        """
        Remove a required resource.
        
        Args:
            resource_type: Type of resource
            resource_id: Resource ID
        """
        self.requires_resources = [r for r in self.requires_resources 
                                 if not (r['resource_type'] == resource_type and r['resource_id'] == resource_id)]
        self.updated_at = datetime.now()
        logger.info(f"Removed required resource {resource_type}:{resource_id} from entry {self.code}")
    
    def update_performance_scores(self, engagement_score: float = None, feedback_score: float = None) -> None:
        """
        Update performance scores.
        
        Args:
            engagement_score: Engagement score (0-100) (optional)
            feedback_score: Feedback score (0-5) (optional)
        """
        if engagement_score is not None:
            if engagement_score < 0 or engagement_score > 100:
                raise ValidationError("Engagement score must be between 0 and 100")
            self.engagement_score = engagement_score
        
        if feedback_score is not None:
            if feedback_score < 0 or feedback_score > 5:
                raise ValidationError("Feedback score must be between 0 and 5")
            self.feedback_score = feedback_score
        
        self.updated_at = datetime.now()
        logger.info(f"Updated performance scores for entry {self.code}")
    
    def enroll_student(self) -> None:
        """
        Enroll a student in this entry.
        """
        if self.max_capacity and self.current_enrollment >= self.max_capacity:
            raise ValidationError("Entry is full")
        
        self.current_enrollment += 1
        self.updated_at = datetime.now()
        logger.info(f"Enrolled student in entry {self.code}: {self.current_enrollment}")
    
    def unenroll_student(self) -> None:
        """
        Unenroll a student from this entry.
        """
        if self.current_enrollment > 0:
            self.current_enrollment -= 1
            self.updated_at = datetime.now()
            logger.info(f"Unenrolled student from entry {self.code}: {self.current_enrollment}")
    
    def is_overdue(self) -> bool:
        """
        Check if entry is overdue.
        
        Returns:
            True if entry is overdue
        """
        if self.date and self.end_time:
            end_datetime = datetime.combine(self.date.date(), self.end_time)
            return datetime.now() > end_datetime
        return False
    
    def is_upcoming(self) -> bool:
        """
        Check if entry is upcoming.
        
        Returns:
            True if entry is upcoming
        """
        if self.date and self.start_time:
            start_datetime = datetime.combine(self.date.date(), self.start_time)
            return datetime.now() < start_datetime
        return False
    
    def is_current_session(self) -> bool:
        """
        Check if entry is currently in session.
        
        Returns:
            True if entry is currently in session
        """
        if self.date and self.start_time and self.end_time:
            now = datetime.now()
            start_datetime = datetime.combine(self.date.date(), self.start_time)
            end_datetime = datetime.combine(self.date.date(), self.end_time)
            return start_datetime <= now <= end_datetime
        return False
    
    def get_time_until_start(self) -> Optional[int]:
        """
        Get time until entry starts in minutes.
        
        Returns:
            Minutes until start, or None if no date
        """
        if self.date and self.start_time:
            start_datetime = datetime.combine(self.date.date(), self.start_time)
            delta = start_datetime - datetime.now()
            return max(0, int(delta.total_seconds() / 60))
        return None
    
    def get_time_until_end(self) -> Optional[int]:
        """
        Get time until entry ends in minutes.
        
        Returns:
            Minutes until end, or None if no date
        """
        if self.date and self.end_time:
            end_datetime = datetime.combine(self.date.date(), self.end_time)
            delta = end_datetime - datetime.now()
            return max(0, int(delta.total_seconds() / 60))
        return None
    
    def get_entry_status(self) -> str:
        """
        Get entry status.
        
        Returns:
            Entry status string
        """
        if self.status == 'cancelled':
            return 'cancelled'
        elif self.is_overdue():
            return 'overdue'
        elif self.is_current_session():
            return 'current'
        elif self.is_upcoming():
            return 'upcoming'
        elif self.status == 'completed':
            return 'completed'
        else:
            return 'scheduled'
    
    def is_full(self) -> bool:
        """
        Check if entry is full.
        
        Returns:
            True if entry is full
        """
        return self.max_capacity is not None and self.current_enrollment >= self.max_capacity
    
    def get_enrollment_percentage(self) -> float:
        """
        Get enrollment percentage.
        
        Returns:
            Enrollment percentage (0-100)
        """
        if self.max_capacity and self.max_capacity > 0:
            return (self.current_enrollment / self.max_capacity) * 100
        return 0.0
    
    def get_entry_summary(self) -> Dict[str, Any]:
        """
        Get entry summary.
        
        Returns:
            Entry summary dictionary
        """
        return {
            'id': self.id,
            'code': self.code,
            'entry_number': self.entry_number,
            'type': self.type,
            'title': self.title,
            'subject_code': self.subject_code,
            'day_of_week': self.day_of_week,
            'start_time': self.start_time.strftime('%H:%M'),
            'end_time': self.end_time.strftime('%H:%M'),
            'duration_minutes': self.duration_minutes,
            'status': self.status,
            'entry_status': self.get_entry_status(),
            'is_recurring': self.is_recurring,
            'teacher_id': self.teacher_id,
            'class_id': self.class_id,
            'room_id': self.room_id,
            'laboratory_id': self.laboratory_id,
            'max_capacity': self.max_capacity,
            'current_enrollment': self.current_enrollment,
            'is_full': self.is_full(),
            'enrollment_percentage': self.get_enrollment_percentage(),
            'attendance_percentage': self.attendance_percentage,
            'completion_status': self.completion_status,
            'date': self.date.isoformat() if self.date else None,
            'requires_attendance': self.requires_attendance,
            'is_mandatory': self.is_mandatory,
            'is_virtual': self.is_virtual
        }
    
    def get_resource_availability(self) -> Dict[str, Any]:
        """
        Get resource availability information.
        
        Returns:
            Resource availability dictionary
        """
        return {
            'total_resources': len(self.requires_resources),
            'resource_types': list(set(r['resource_type'] for r in self.requires_resources)),
            'max_capacity': self.max_capacity,
            'available_capacity': max(0, (self.max_capacity or 0) - self.current_enrollment),
            'enrollment_percentage': self.get_enrollment_percentage()
        }
    
    def get_performance_metrics(self) -> Dict[str, Any]:
        """
        Get performance metrics.
        
        Returns:
            Performance metrics dictionary
        """
        return {
            'engagement_score': self.engagement_score,
            'feedback_score': self.feedback_score,
            'attendance_percentage': self.attendance_percentage,
            'attendance_recorded': self.attendance_recorded,
            'completion_status': self.completion_status,
            'total_attendance_records': len(self.attendance_records)
        }
    
    def __repr__(self) -> str:
        """String representation of the timetable entry model."""
        return f"<TimetableEntryModel(code='{self.code}', title='{self.title}', type='{self.type}', status='{self.status}')>"