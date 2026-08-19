"""
Attendance Model for Database Operations

This module provides the SQLAlchemy model for Attendance entity.
It includes all fields and relationships for academic attendance tracking.

Author: Edu-Flow Team
"""

from typing import Dict, Any, Optional, List
from datetime import datetime, time, date, timedelta
import logging

from sqlalchemy import Column, String, Integer, Text, DateTime, JSON, Boolean, ForeignKey, Float
from sqlalchemy.orm import relationship

from infrastructure.models.base_model import BaseModel
from core.exceptions import ValidationError
from core.logging import get_logger

logger = get_logger(__name__)


class AttendanceModel(BaseModel):
    """
    SQLAlchemy model for Attendance entity.
    
    Represents student attendance tracking for classes and courses.
    """
    __tablename__ = "attendances"
    
    # Attendance identification
    id = Column(String(50), primary_key=True)
    code = Column(String(50), nullable=False, unique=True, index=True)
    attendance_number = Column(String(50), unique=True, nullable=False, index=True)
    
    # Related entities
    student_id = Column(String(50), ForeignKey("users.id"), nullable=False)
    teacher_id = Column(String(50), ForeignKey("users.id"), nullable=False)
    class_id = Column(String(50), ForeignKey("classes.id"), nullable=False)
    subject_id = Column(String(50), ForeignKey("subjects.id"), nullable=False)
    enrollment_id = Column(String(50), ForeignKey("enrollments.id"), nullable=False)
    
    # Attendance details
    attendance_type = Column(String(50), nullable=False)  # class_attendance, lab_attendance, online_attendance, event_attendance
    academic_year = Column(String(10), nullable=False)  # 2023-2024
    semester = Column(Integer, nullable=False)  # Semester number
    batch = Column(String(20), nullable=False)  # A, B, C, etc.
    section = Column(String(5), nullable=False)  # 1, 2, 3, etc.
    
    # Date and time information
    attendance_date = Column(DateTime, nullable=False, index=True)
    session_start_time = Column(DateTime, nullable=False)
    session_end_time = Column(DateTime, nullable=False)
    check_in_time = Column(DateTime)
    check_out_time = Column(DateTime)
    is_late_check_in = Column(Boolean, default=False)
    is_early_check_out = Column(Boolean, default=False)
    
    # Attendance status
    status = Column(String(20), nullable=False, default='present')  # present, absent, late, excused, sick, holiday
    is_excused = Column(Boolean, default=False)
    excused_by = Column(String(50))  # User ID who excused the absence
    excused_reason = Column(Text)
    notes = Column(Text)
    
    # Attendance statistics
    duration_minutes = Column(Integer, default=0)  # Actual duration attended
    expected_duration_minutes = Column(Integer, default=0)  # Expected duration of the session
    attendance_percentage = Column(Float, default=0.0)  # 0-100
    is_full_session = Column(Boolean, default=False)  # Whether full session was attended
    
    # Attendance metadata
    metadata = Column(JSON, default=dict)
    location = Column(JSON, default=dict)  # Location information
    device_info = Column(JSON, default=dict)  # Device information for online attendance
    ip_address = Column(String(45))  # IP address for online attendance
    attendance_records = Column(JSON, default=list)  # List of attendance records
    
    # Relationships
    student = relationship("UserModel", foreign_keys=[student_id])
    teacher = relationship("UserModel", foreign_keys=[teacher_id])
    class_model = relationship("ClassModel")
    subject = relationship("SubjectModel")
    enrollment = relationship("EnrollmentModel")
    
    def __init__(self, **kwargs):
        """Initialize the attendance model with provided data."""
        # Set default values for optional fields
        kwargs.setdefault('attendance_type', 'class_attendance')
        kwargs.setdefault('semester', 1)
        kwargs.setdefault('batch', 'A')
        kwargs.setdefault('section', '1')
        kwargs.setdefault('status', 'present')
        kwargs.setdefault('is_excused', False)
        kwargs.setdefault('duration_minutes', 0)
        kwargs.setdefault('expected_duration_minutes', 0)
        kwargs.setdefault('attendance_percentage', 0.0)
        kwargs.setdefault('is_full_session', False)
        kwargs.setdefault('metadata', {})
        kwargs.setdefault('location', {})
        kwargs.setdefault('device_info', {})
        kwargs.setdefault('attendance_records', [])
        
        # Set default date and time
        now = datetime.now()
        if 'attendance_date' not in kwargs:
            kwargs['attendance_date'] = now
        if 'session_start_time' not in kwargs:
            kwargs['session_start_time'] = now
        if 'session_end_time' not in kwargs:
            kwargs['session_end_time'] = now
        
        super().__init__(**kwargs)
        
        # Generate attendance number if not provided
        if not self.attendance_number:
            self.generate_attendance_number()
    
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
        if 'attendance_date' in data and isinstance(data['attendance_date'], datetime):
            data['attendance_date'] = data['attendance_date'].isoformat()
        else:
            data['attendance_date'] = datetime.now().isoformat()
        
        if 'session_start_time' in data and isinstance(data['session_start_time'], datetime):
            data['session_start_time'] = data['session_start_time'].isoformat()
        else:
            data['session_start_time'] = datetime.now().isoformat()
        
        if 'session_end_time' in data and isinstance(data['session_end_time'], datetime):
            data['session_end_time'] = data['session_end_time'].isoformat()
        else:
            data['session_end_time'] = datetime.now().isoformat()
        
        if 'check_in_time' in data and isinstance(data['check_in_time'], datetime):
            data['check_in_time'] = data['check_in_time'].isoformat()
        else:
            data['check_in_time'] = None
        
        if 'check_out_time' in data and isinstance(data['check_out_time'], datetime):
            data['check_out_time'] = data['check_out_time'].isoformat()
        else:
            data['check_out_time'] = None
        
        # Convert JSON fields to proper format
        if 'metadata' in data and isinstance(data['metadata'], dict):
            data['metadata'] = data['metadata']
        else:
            data['metadata'] = {}
        
        if 'location' in data and isinstance(data['location'], dict):
            data['location'] = data['location']
        else:
            data['location'] = {}
        
        if 'device_info' in data and isinstance(data['device_info'], dict):
            data['device_info'] = data['device_info']
        else:
            data['device_info'] = {}
        
        if 'attendance_records' in data and isinstance(data['attendance_records'], list):
            data['attendance_records'] = data['attendance_records']
        else:
            data['attendance_records'] = []
        
        # Calculate derived fields
        data['is_late_check_in'] = self.is_late_check_in
        data['is_early_check_out'] = self.is_early_check_out
        data['attendance_duration_minutes'] = self.get_attendance_duration_minutes()
        data['expected_duration_minutes'] = self.expected_duration_minutes
        data='late_minutes'] = self.get_late_minutes()
        data['early_check_out_minutes'] = self.get_early_check_out_minutes()
        data['attendance_day'] = self.get_attendance_day()
        data='week_number'] = self.get_week_number()
        data['month'] = self.get_month()
        data['year'] = self.get_year()
        data['is_weekday'] = self.is_weekday()
        data='is_weekend'] = self.is_weekend()
        data['is_holiday'] = self.metadata.get('is_holiday', False)
        data['attendance_status_summary'] = self.get_attendance_status_summary()
        data['violations'] = self.get_attendance_violations()
        
        # Include relationships if requested
        if include_relationships:
            if hasattr(self, 'student') and self.student:
                data['student'] = self.student.to_dict()
            else:
                data['student'] = None
            
            if hasattr(self, 'teacher') and self.teacher:
                data['teacher'] = self.teacher.to_dict()
            else:
                data['teacher'] = None
            
            if hasattr(self, 'class_model') and self.class_model:
                data['class_model'] = self.class_model.to_dict()
            else:
                data['class_model'] = None
            
            if hasattr(self, 'subject') and self.subject:
                data['subject'] = self.subject.to_dict()
            else:
                data['subject'] = None
            
            if hasattr(self, 'enrollment') and self.enrollment:
                data['enrollment'] = self.enrollment.to_dict()
            else:
                data['enrollment'] = None
        
        return data
    
    def update(self, **kwargs) -> None:
        """Update the model with new data."""
        # Handle special field updates
        if 'metadata' in kwargs and isinstance(kwargs['metadata'], dict):
            self.metadata = kwargs['metadata']
        if 'location' in kwargs and isinstance(kwargs['location'], dict):
            self.location = kwargs['location']
        if 'device_info' in kwargs and isinstance(kwargs['device_info'], dict):
            self.device_info = kwargs['device_info']
        if 'attendance_records' in kwargs and isinstance(kwargs['attendance_records'], list):
            self.attendance_records = kwargs['attendance_records']
        
        super().update(**kwargs)
    
    def validate(self) -> bool:
        """
        Validate the attendance model data.
        
        Returns:
            True if valid, False otherwise
            
        Raises:
            ValidationError: If validation fails
        """
        try:
            # Call base validation
            super().validate()
            
            # Attendance-specific validations
            if not self.id:
                raise ValidationError("Attendance ID is required")
            
            if not self.code:
                raise ValidationError("Attendance code is required")
            
            if not self.attendance_number:
                raise ValidationError("Attendance number is required")
            
            if not self.student_id:
                raise ValidationError("Student ID is required")
            
            if not self.teacher_id:
                raise ValidationError("Teacher ID is required")
            
            if not self.class_id:
                raise ValidationError("Class ID is required")
            
            if not self.subject_id:
                raise ValidationError("Subject ID is required")
            
            if not self.enrollment_id:
                raise ValidationError("Enrollment ID is required")
            
            if not self.attendance_type:
                raise ValidationError("Attendance type is required")
            
            if not self.academic_year:
                raise ValidationError("Academic year is required")
            
            if not self.semester:
                raise ValidationError("Semester is required")
            
            if not self.batch:
                raise ValidationError("Batch is required")
            
            if not self.section:
                raise ValidationError("Section is required")
            
            if not self.status:
                raise ValidationError("Attendance status is required")
            
            # Type validation
            valid_types = ['class_attendance', 'lab_attendance', 'online_attendance', 'event_attendance']
            if self.attendance_type not in valid_types:
                raise ValidationError(f"Invalid attendance type: {self.attendance_type}")
            
            # Academic year validation
            if len(self.academic_year) != 9 or self.academic_year[4] != '-':  # 2023-2024
                raise ValidationError("Academic year must be in format YYYY-YYYY")
            
            # Semester validation
            if self.semester < 1:
                raise ValidationError("Semester must be positive")
            
            # Date validations
            if self.attendance_date > datetime.now():
                raise ValidationError("Attendance date cannot be in the future")
            
            if self.session_start_time > self.session_end_time:
                raise ValidationError("Session start time must be before session end time")
            
            if self.attendance_date < self.session_start_time or self.attendance_date > self.session_end_time:
                raise ValidationError("Attendance date must be within session time range")
            
            if self.check_in_time and self.check_in_time > self.session_end_time:
                raise ValidationError("Check-in time cannot be after session end time")
            
            if self.check_out_time and self.check_out_time < self.session_start_time:
                raise ValidationError("Check-out time cannot be before session start time")
            
            if self.check_in_time and self.check_out_time and self.check_in_time > self.check_out_time:
                raise ValidationError("Check-in time must be before check-out time")
            
            # Status validation
            valid_statuses = ['present', 'absent', 'late', 'excused', 'sick', 'holiday', 'leave']
            if self.status not in valid_statuses:
                raise ValidationError(f"Invalid attendance status: {self.status}")
            
            # Duration validations
            if self.duration_minutes < 0:
                raise ValidationError("Duration minutes cannot be negative")
            
            if self.expected_duration_minutes < 0:
                raise ValidationError("Expected duration minutes cannot be negative")
            
            if self.attendance_percentage < 0 or self.attendance_percentage > 100:
                raise ValidationError("Attendance percentage must be between 0 and 100")
            
            # Late/early validations
            if self.is_late_check_in and not self.check_in_time:
                raise ValidationError("Late check-in requires check-in time")
            
            if self.is_early_check_out and not self.check_out_time:
                raise ValidationError("Early check-out requires check-out time")
            
            # Excused validation
            if self.is_excused and not self.excused_by:
                raise ValidationError("Excused attendance requires excused_by")
            
            # JSON fields validation
            if not isinstance(self.metadata, dict):
                raise ValidationError("Metadata must be a dictionary")
            
            if not isinstance(self.location, dict):
                raise ValidationError("Location must be a dictionary")
            
            if not isinstance(self.device_info, dict):
                raise ValidationError("Device info must be a dictionary")
            
            if not isinstance(self.attendance_records, list):
                raise ValidationError("Attendance records must be a list")
            
            logger.info(f"Attendance {self.attendance_number} validation passed")
            return True
            
        except Exception as e:
            logger.error(f"Attendance validation error: {str(e)}")
            raise ValidationError(f"Attendance validation error: {str(e)}")
    
    def generate_attendance_number(self) -> None:
        """Generate attendance number."""
        # Generate attendance number based on student ID, academic year, and date
        date_part = self.attendance_date.strftime('%Y%m%d')
        student_part = self.student_id[-4:]  # Last 4 digits of student ID
        attendance_number = f"ATT-{date_part}-{student_part}"
        self.attendance_number = attendance_number
        logger.info(f"Generated attendance number: {attendance_number}")
    
    def mark_check_in(self, check_in_time: datetime = None, location: dict = None, 
                     device_info: dict = None, ip_address: str = None) -> None:
        """
        Mark student check-in.
        
        Args:
            check_in_time: Check-in time (optional)
            location: Location information (optional)
            device_info: Device information (optional)
            ip_address: IP address (optional)
        """
        self.check_in_time = check_in_time or datetime.now()
        
        if location:
            self.location = location
        
        if device_info:
            self.device_info = device_info
        
        if ip_address:
            self.ip_address = ip_address
        
        # Check for late arrival
        if self.check_in_time > self.session_start_time:
            self.is_late_check_in = True
            late_minutes = (self.check_in_time - self.session_start_time).total_seconds() / 60
            self.metadata['late_minutes'] = int(late_minutes)
        else:
            self.is_late_check_in = False
            self.metadata['late_minutes'] = 0
        
        # Add to attendance records
        record = {
            'action': 'check_in',
            'timestamp': self.check_in_time.isoformat(),
            'location': location or self.location,
            'device_info': device_info or self.device_info,
            'ip_address': ip_address or self.ip_address
        }
        self.attendance_records.append(record)
        
        self.updated_at = datetime.now()
        logger.info(f"Marked check-in for attendance {self.attendance_number}")
    
    def mark_check_out(self, check_out_time: datetime = None, location: dict = None,
                      device_info: dict = None, ip_address: str = None) -> None:
        """
        Mark student check-out.
        
        Args:
            check_out_time: Check-out time (optional)
            location: Location information (optional)
            device_info: Device information (optional)
            ip_address: IP address (optional)
        """
        self.check_out_time = check_out_time or datetime.now()
        
        if location:
            self.location = location
        
        if device_info:
            self.device_info = device_info
        
        if ip_address:
            self.ip_address = ip_address
        
        # Calculate attendance duration and percentage
        self.calculate_attendance_metrics()
        
        # Check for early departure
        if self.check_out_time < self.session_end_time:
            self.is_early_check_out = True
            early_minutes = (self.session_end_time - self.check_out_time).total_seconds() / 60
            self.metadata['early_check_out_minutes'] = int(early_minutes)
        else:
            self.is_early_check_out = False
            self.metadata['early_check_out_minutes'] = 0
        
        # Add to attendance records
        record = {
            'action': 'check_out',
            'timestamp': self.check_out_time.isoformat(),
            'location': location or self.location,
            'device_info': device_info or self.device_info,
            'ip_address': ip_address or self.ip_address
        }
        self.attendance_records.append(record)
        
        self.updated_at = datetime.now()
        logger.info(f"Marked check-out for attendance {self.attendance_number}")
    
    def calculate_attendance_metrics(self) -> None:
        """Calculate attendance duration and percentage."""
        if self.check_in_time and self.check_out_time:
            duration = (self.check_out_time - self.check_in_time).total_seconds() / 60
            self.duration_minutes = int(duration)
            
            # Calculate attendance percentage
            if self.expected_duration_minutes > 0:
                self.attendance_percentage = min(100, (self.duration_minutes / self.expected_duration_minutes) * 100)
            else:
                self.attendance_percentage = 100
            
            # Check if full session was attended
            self.is_full_session = self.duration_minutes >= self.expected_duration_minutes
        else:
            self.duration_minutes = 0
            self.attendance_percentage = 0.0
            self.is_full_session = False
    
    def mark_absent(self, reason: str = "", excused: bool = False, excused_by: str = None) -> None:
        """
        Mark student as absent.
        
        Args:
            reason: Reason for absence (optional)
            excused: Whether absence is excused (default: False)
            excused_by: User ID who excused the absence (optional)
        """
        self.status = 'absent'
        self.is_excused = excused
        
        if excused and excused_by:
            self.excused_by = excused_by
        
        if reason:
            self.excused_reason = reason
        
        # Add to attendance records
        record = {
            'action': 'mark_absent',
            'timestamp': datetime.now().isoformat(),
            'reason': reason,
            'excused': excused,
            'excused_by': excused_by
        }
        self.attendance_records.append(record)
        
        self.updated_at = datetime.now()
        logger.info(f"Marked absent for attendance {self.attendance_number}: {reason}")
    
    def mark_late(self, late_reason: str = "") -> None:
        """
        Mark student as late.
        
        Args:
            late_reason: Reason for being late (optional)
        """
        self.status = 'late'
        
        if late_reason:
            self.notes = f"Late: {late_reason}"
        
        # Add to attendance records
        record = {
            'action': 'mark_late',
            'timestamp': datetime.now().isoformat(),
            'reason': late_reason
        }
        self.attendance_records.append(record)
        
        self.updated_at = datetime.now()
        logger.info(f"Marked late for attendance {self.attendance_number}: {late_reason}")
    
    def excuse_absence(self, reason: str, excused_by: str) -> None:
        """
        Excuse an absence.
        
        Args:
            reason: Reason for excusing the absence
            excused_by: User ID who excused the absence
        """
        self.status = 'excused'
        self.is_excused = True
        self.excused_reason = reason
        self.excused_by = excused_by
        
        # Add to attendance records
        record = {
            'action': 'excuse_absence',
            'timestamp': datetime.now().isoformat(),
            'reason': reason,
            'excused_by': excused_by
        }
        self.attendance_records.append(record)
        
        self.updated_at = datetime.now()
        logger.info(f"Excused absence for attendance {self.attendance_number}: {reason}")
    
    def add_attendance_note(self, note: str) -> None:
        """
        Add a note to the attendance record.
        
        Args:
            note: Note text
        """
        self.notes = note
        self.updated_at = datetime.now()
        logger.info(f"Added note to attendance {self.attendance_number}")
    
    def get_attendance_duration_minutes(self) -> int:
        """
        Get attendance duration in minutes.
        
        Returns:
            Attendance duration in minutes
        """
        if self.check_in_time and self.check_out_time:
            duration = (self.check_out_time - self.check_in_time).total_seconds() / 60
            return int(duration)
        return 0
    
    def get_late_minutes(self) -> int:
        """
        Get late minutes.
        
        Returns:
            Late minutes
        """
        if self.is_late_check_in and self.check_in_time and self.session_start_time:
            late_minutes = (self.check_in_time - self.session_start_time).total_seconds() / 60
            return int(late_minutes)
        return 0
    
    def get_early_check_out_minutes(self) -> int:
        """
        Get early check-out minutes.
        
        Returns:
            Early check-out minutes
        """
        if self.is_early_check_out and self.check_out_time and self.session_end_time:
            early_minutes = (self.session_end_time - self.check_out_time).total_seconds() / 60
            return int(early_minutes)
        return 0
    
    def get_attendance_day(self) -> str:
        """
        Get attendance day name.
        
        Returns:
            Day name (Monday, Tuesday, etc.)
        """
        return self.attendance_date.strftime('%A')
    
    def get_week_number(self) -> int:
        """
        Get attendance week number.
        
        Returns:
            Week number (1-52)
        """
        return self.attendance_date.isocalendar()[1]
    
    def get_month(self) -> int:
        """
        Get attendance month.
        
        Returns:
            Month (1-12)
        """
        return self.attendance_date.month
    
    def get_year(self) -> int:
        """
        Get attendance year.
        
        Returns:
            Year
        """
        return self.attendance_date.year
    
    def is_weekday(self) -> bool:
        """
        Check if attendance is on a weekday.
        
        Returns:
            True if weekday
        """
        return self.attendance_date.weekday() < 5  # 0-4 are weekdays
    
    def is_weekend(self) -> bool:
        """
        Check if attendance is on a weekend.
        
        Returns:
            True if weekend
        """
        return self.attendance_date.weekday() >= 5  # 5-6 are weekends
    
    def get_attendance_status_summary(self) -> str:
        """
        Get attendance status summary.
        
        Returns:
            Status summary string
        """
        if self.is_excused:
            return f"Excused {self.status}"
        elif self.status == 'late':
            return f"Late ({self.get_late_minutes()} min)"
        elif self.status == 'present':
            if self.is_late_check_in:
                return f"Present (late {self.get_late_minutes()} min)"
            elif self.is_early_check_out:
                return f"Present (left early {self.get_early_check_out_minutes()} min)"
            else:
                return "Present"
        elif self.status == 'absent':
            return "Absent"
        else:
            return self.status
    
    def get_attendance_violations(self) -> List[str]:
        """
        Get attendance violations.
        
        Returns:
            List of violation strings
        """
        violations = []
        
        if self.is_late_check_in:
            violations.append("Late arrival")
        
        if self.is_early_check_out:
            violations.append("Early departure")
        
        if self.attendance_percentage < 75:
            violations.append("Low attendance")
        
        if self.status == 'absent' and not self.is_excused:
            violations.append("Unexcused absence")
        
        return violations
    
    def __repr__(self) -> str:
        """String representation of the attendance model."""
        return f"<AttendanceModel(attendance_number='{self.attendance_number}', student_id='{self.student_id}', status='{self.status}', date='{self.attendance_date.strftime('%Y-%m-%d')}')>"