"""
Timetable Model for Database Operations

This module provides the SQLAlchemy model for Timetable entity.
It includes all fields and relationships for academic timetable scheduling.

Author: Edu-Flow Team
"""

from typing import Dict, Any, Optional, List
from datetime import datetime, time, timedelta, date
import logging

from sqlalchemy import Column, String, Integer, Text, DateTime, JSON, Boolean, ForeignKey, Time
from sqlalchemy.orm import relationship

from src.infrastructure.models.base_model import BaseModel
from src.core.exceptions import ValidationError
from src.core.logging import get_logger

logger = get_logger(__name__)


class TimetableModel(BaseModel):
    """
    SQLAlchemy model for Timetable entity.
    
    Represents academic timetable scheduling for classes, courses, and resources.
    """
    __tablename__ = "timetables"
    
    # Timetable identification
    id = Column(String(50), primary_key=True)
    code = Column(String(50), nullable=False, unique=True, index=True)
    timetable_number = Column(String(50), unique=True, nullable=False, index=True)
    title = Column(String(200), nullable=False)
    description = Column(Text)
    
    # Timetable categorization
    type = Column(String(50), nullable=False)  # class_timetable, course_timetable, exam_timetable, faculty_timetable
    academic_year = Column(String(10), nullable=False)  # 2023-2024
    semester = Column(Integer, nullable=False)  # Semester number
    batch = Column(String(20), nullable=False)  # A, B, C, etc.
    section = Column(String(5), nullable=False)  # 1, 2, 3, etc.
    
    # Related entities
    department_id = Column(String(50), ForeignKey("departments.id"), nullable=False)
    program_id = Column(String(50), ForeignKey("programs.id"))
    class_id = Column(String(50), ForeignKey("classes.id"))
    subject_id = Column(String(50), ForeignKey("subjects.id"))
    teacher_id = Column(String(50), ForeignKey("users.id"))
    room_id = Column(String(50), ForeignKey("rooms.id"))
    laboratory_id = Column(String(50), ForeignKey("laboratories.id"))
    
    # Timetable details
    is_active = Column(Boolean, default=True)
    is_published = Column(Boolean, default=False)
    is_locked = Column(Boolean, default=False)
    version = Column(Integer, default=1)  # Version number for changes
    revision_notes = Column(Text)  # Notes about revisions
    
    # Time and date information
    start_date = Column(DateTime, nullable=False)  # Timetable start date
    end_date = Column(DateTime, nullable=False)  # Timetable end date
    generated_date = Column(DateTime, default=datetime.now)  # When timetable was generated
    last_modified_date = Column(DateTime, default=datetime.now)  # Last modification date
    
    # Timetable structure
    working_days = Column(JSON, default=list)  # List of working days ['Monday', 'Tuesday', etc.]
    daily_slots = Column(JSON, default=list)  # List of daily time slots
    breaks = Column(JSON, default=list)  # List of break times
    lunch_break = Column(JSON, default=dict)  # Lunch break information
    
    # Timetable metadata
    metadata = Column(JSON, default=dict)
    constraints = Column(JSON, default=dict)  # Scheduling constraints
    conflicts = Column(JSON, default=list)  # List of conflicts
    generated_by = Column(String(50))  # System or user who generated the timetable
    approved_by = Column(String(50))  # Approver of the timetable
    approval_date = Column(DateTime)
    
    # Relationships
    department = relationship("DepartmentModel")
    program = relationship("ProgramModel")
    class_model = relationship("ClassModel")
    subject = relationship("SubjectModel")
    teacher = relationship("UserModel")
    room = relationship("RoomModel")
    laboratory = relationship("LaboratoryModel")
    timetable_entries = relationship("TimetableEntryModel")
    
    def __init__(self, **kwargs):
        """Initialize the timetable model with provided data."""
        # Set default values for optional fields
        kwargs.setdefault('type', 'class_timetable')
        kwargs.setdefault('semester', 1)
        kwargs.setdefault('batch', 'A')
        kwargs.setdefault('section', '1')
        kwargs.setdefault('is_active', True)
        kwargs.setdefault('is_published', False)
        kwargs.setdefault('is_locked', False)
        kwargs.setdefault('version', 1)
        kwargs.setdefault('working_days', ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday'])
        kwargs.setdefault('daily_slots', self._get_default_slots())
        kwargs.setdefault('breaks', self._get_default_breaks())
        kwargs.setdefault('lunch_break', self._get_default_lunch_break())
        kwargs.setdefault('metadata', {})
        kwargs.setdefault('constraints', {})
        kwargs.setdefault('conflicts', [])
        
        # Set default dates
        now = datetime.now()
        if 'start_date' not in kwargs:
            kwargs['start_date'] = now
        if 'end_date' not in kwargs:
            # Default 4 months from start date
            kwargs['end_date'] = now + timedelta(days=120)
        if 'generated_date' not in kwargs:
            kwargs['generated_date'] = now
        if 'last_modified_date' not in kwargs:
            kwargs['last_modified_date'] = now
        
        super().__init__(**kwargs)
        
        # Generate timetable number if not provided
        if not self.timetable_number:
            self.generate_timetable_number()
    
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
        if 'start_date' in data and isinstance(data['start_date'], datetime):
            data['start_date'] = data['start_date'].isoformat()
        else:
            data['start_date'] = datetime.now().isoformat()
        
        if 'end_date' in data and isinstance(data['end_date'], datetime):
            data['end_date'] = data['end_date'].isoformat()
        else:
            data['end_date'] = (datetime.now() + timedelta(days=120)).isoformat()
        
        if 'generated_date' in data and isinstance(data['generated_date'], datetime):
            data['generated_date'] = data['generated_date'].isoformat()
        else:
            data['generated_date'] = datetime.now().isoformat()
        
        if 'last_modified_date' in data and isinstance(data['last_modified_date'], datetime):
            data['last_modified_date'] = data['last_modified_date'].isoformat()
        else:
            data['last_modified_date'] = datetime.now().isoformat()
        
        if 'approval_date' in data and isinstance(data['approval_date'], datetime):
            data['approval_date'] = data['approval_date'].isoformat()
        else:
            data['approval_date'] = None
        
        # Convert JSON fields to proper format
        if 'working_days' in data and isinstance(data['working_days'], list):
            data['working_days'] = data['working_days']
        else:
            data['working_days'] = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday']
        
        if 'daily_slots' in data and isinstance(data['daily_slots'], list):
            data['daily_slots'] = data['daily_slots']
        else:
            data['daily_slots'] = self._get_default_slots()
        
        if 'breaks' in data and isinstance(data['breaks'], list):
            data['breaks'] = data['breaks']
        else:
            data['breaks'] = self._get_default_breaks()
        
        if 'lunch_break' in data and isinstance(data['lunch_break'], dict):
            data['lunch_break'] = data['lunch_break']
        else:
            data['lunch_break'] = self._get_default_lunch_break()
        
        if 'metadata' in data and isinstance(data['metadata'], dict):
            data['metadata'] = data['metadata']
        else:
            data['metadata'] = {}
        
        if 'constraints' in data and isinstance(data['constraints'], dict):
            data['constraints'] = data['constraints']
        else:
            data['constraints'] = {}
        
        if 'conflicts' in data and isinstance(data['conflicts'], list):
            data['conflicts'] = data['conflicts']
        else:
            data['conflicts'] = []
        
        # Calculate derived fields
        data['duration_days'] = self.get_duration_days()
        data='days_until_start'] = self.get_days_until_start()
        data['days_until_end'] = self.get_days_until_end()
        data['is_current'] = self.is_current()
        data['total_entries'] = len(self.timetable_entries) if hasattr(self, 'timetable_entries') else 0
        data['has_conflicts'] = len(self.conflicts) > 0
        data['timetable_status'] = self.get_timetable_status()
        data['working_days_count'] = len(self.working_days)
        data='timetable_summary'] = self.get_timetable_summary()
        data['availability'] = self.get_availability()
        
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
            
            if hasattr(self, 'class_model') and self.class_model:
                data['class_model'] = self.class_model.to_dict()
            else:
                data['class_model'] = None
            
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
            
            if hasattr(self, 'timetable_entries') and self.timetable_entries:
                data['timetable_entries'] = [entry.to_dict() for entry in self.timetable_entries]
            else:
                data['timetable_entries'] = []
        
        return data
    
    def update(self, **kwargs) -> None:
        """Update the model with new data."""
        # Handle special field updates
        if 'working_days' in kwargs and isinstance(kwargs['working_days'], list):
            self.working_days = kwargs['working_days']
        if 'daily_slots' in kwargs and isinstance(kwargs['daily_slots'], list):
            self.daily_slots = kwargs['daily_slots']
        if 'breaks' in kwargs and isinstance(kwargs['breaks'], list):
            self.breaks = kwargs['breaks']
        if 'lunch_break' in kwargs and isinstance(kwargs['lunch_break'], dict):
            self.lunch_break = kwargs['lunch_break']
        if 'metadata' in kwargs and isinstance(kwargs['metadata'], dict):
            self.metadata = kwargs['metadata']
        if 'constraints' in kwargs and isinstance(kwargs['constraints'], dict):
            self.constraints = kwargs['constraints']
        if 'conflicts' in kwargs and isinstance(kwargs['conflicts'], list):
            self.conflicts = kwargs['conflicts']
        
        super().update(**kwargs)
    
    def validate(self) -> bool:
        """
        Validate the timetable model data.
        
        Returns:
            True if valid, False otherwise
            
        Raises:
            ValidationError: If validation fails
        """
        try:
            # Call base validation
            super().validate()
            
            # Timetable-specific validations
            if not self.id:
                raise ValidationError("Timetable ID is required")
            
            if not self.code:
                raise ValidationError("Timetable code is required")
            
            if not self.timetable_number:
                raise ValidationError("Timetable number is required")
            
            if not self.title:
                raise ValidationError("Timetable title is required")
            
            if not self.type:
                raise ValidationError("Timetable type is required")
            
            if not self.department_id:
                raise ValidationError("Department ID is required")
            
            if not self.academic_year:
                raise ValidationError("Academic year is required")
            
            if not self.semester:
                raise ValidationError("Semester is required")
            
            if not self.batch:
                raise ValidationError("Batch is required")
            
            if not self.section:
                raise ValidationError("Section is required")
            
            # Type validation
            valid_types = ['class_timetable', 'course_timetable', 'exam_timetable', 'faculty_timetable']
            if self.type not in valid_types:
                raise ValidationError(f"Invalid timetable type: {self.type}")
            
            # Academic year validation
            if len(self.academic_year) != 9 or self.academic_year[4] != '-':  # 2023-2024
                raise ValidationError("Academic year must be in format YYYY-YYYY")
            
            # Semester validation
            if self.semester < 1:
                raise ValidationError("Semester must be positive")
            
            # Date validations
            if self.start_date > self.end_date:
                raise ValidationError("Start date must be before end date")
            
            if self.generated_date > datetime.now():
                raise ValidationError("Generated date cannot be in the future")
            
            if self.last_modified_date > datetime.now():
                raise ValidationError("Last modified date cannot be in the future")
            
            if self.approval_date and self.approval_date > datetime.now():
                raise ValidationError("Approval date cannot be in the future")
            
            # Version validation
            if self.version < 1:
                raise ValidationError("Version must be positive")
            
            # Working days validation
            if not isinstance(self.working_days, list) or len(self.working_days) == 0:
                raise ValidationError("Working days must be a non-empty list")
            
            valid_days = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday']
            for day in self.working_days:
                if day not in valid_days:
                    raise ValidationError(f"Invalid working day: {day}")
            
            # Daily slots validation
            if not isinstance(self.daily_slots, list) or len(self.daily_slots) == 0:
                raise ValidationError("Daily slots must be a non-empty list")
            
            for slot in self.daily_slots:
                if not isinstance(slot, dict) or 'start_time' not in slot or 'end_time' not in slot:
                    raise ValidationError("Each slot must be a dictionary with start_time and end_time")
                
                if not isinstance(slot['start_time'], time) or not isinstance(slot['end_time'], time):
                    raise ValidationError("Slot times must be valid time objects")
                
                if slot['start_time'] >= slot['end_time']:
                    raise ValidationError("Slot start time must be before end time")
            
            # Breaks validation
            if not isinstance(self.breaks, list):
                raise ValidationError("Breaks must be a list")
            
            for break_time in self.breaks:
                if not isinstance(break_time, dict) or 'start_time' not in break_time or 'end_time' not in break_time:
                    raise ValidationError("Each break must be a dictionary with start_time and end_time")
                
                if not isinstance(break_time['start_time'], time) or not isinstance(break_time['end_time'], time):
                    raise ValidationError("Break times must be valid time objects")
                
                if break_time['start_time'] >= break_time['end_time']:
                    raise ValidationError("Break start time must be before end time")
            
            # Lunch break validation
            if not isinstance(self.lunch_break, dict):
                raise ValidationError("Lunch break must be a dictionary")
            
            if 'start_time' in self.lunch_break and 'end_time' in self.lunch_break:
                if not isinstance(self.lunch_break['start_time'], time) or not isinstance(self.lunch_break['end_time'], time):
                    raise ValidationError("Lunch break times must be valid time objects")
                
                if self.lunch_break['start_time'] >= self.lunch_break['end_time']:
                    raise ValidationError("Lunch break start time must be before end time")
            
            # JSON fields validation
            if not isinstance(self.metadata, dict):
                raise ValidationError("Metadata must be a dictionary")
            
            if not isinstance(self.constraints, dict):
                raise ValidationError("Constraints must be a dictionary")
            
            if not isinstance(self.conflicts, list):
                raise ValidationError("Conflicts must be a list")
            
            logger.info(f"Timetable {self.code} validation passed")
            return True
            
        except Exception as e:
            logger.error(f"Timetable validation error: {str(e)}")
            raise ValidationError(f"Timetable validation error: {str(e)}")
    
    def _get_default_slots(self) -> List[Dict[str, Any]]:
        """Get default daily time slots."""
        return [
            {'start_time': time(8, 0), 'end_time': time(9, 30)},
            {'start_time': time(9, 45), 'end_time': time(11, 15)},
            {'start_time': time(11, 30), 'end_time': time(13, 0)},
            {'start_time': time(14, 0), 'end_time': time(15, 30)},
            {'start_time': time(15, 45), 'end_time': time(17, 15)}
        ]
    
    def _get_default_breaks(self) -> List[Dict[str, Any]]:
        """Get default break times."""
        return [
            {'start_time': time(9, 30), 'end_time': time(9, 45)},  # Short break
            {'start_time': time(13, 0), 'end_time': time(14, 0)},   # Lunch break
        ]
    
    def _get_default_lunch_break(self) -> Dict[str, Any]:
        """Get default lunch break."""
        return {
            'start_time': time(13, 0),
            'end_time': time(14, 0),
            'duration_minutes': 60
        }
    
    def generate_timetable_number(self) -> None:
        """Generate timetable number."""
        # Generate timetable number based on academic year, semester, and batch
        year_part = self.academic_year.replace('-', '')
        timetable_number = f"TBL-{year_part}-SEM{self.semester}-{self.batch}{self.section}"
        self.timetable_number = timetable_number
        logger.info(f"Generated timetable number: {timetable_number}")
    
    def add_working_day(self, day: str) -> None:
        """
        Add a working day.
        
        Args:
            day: Day of week (Monday, Tuesday, etc.)
        """
        valid_days = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday']
        if day not in valid_days:
            raise ValidationError(f"Invalid working day: {day}")
        
        if day not in self.working_days:
            self.working_days.append(day)
            self.updated_at = datetime.now()
            logger.info(f"Added working day {day} to timetable {self.code}")
        else:
            logger.warning(f"Working day {day} already exists in timetable {self.code}")
    
    def remove_working_day(self, day: str) -> None:
        """
        Remove a working day.
        
        Args:
            day: Day of week to remove
        """
        if day in self.working_days:
            self.working_days.remove(day)
            self.updated_at = datetime.now()
            logger.info(f"Removed working day {day} from timetable {self.code}")
        else:
            logger.warning(f"Working day {day} not found in timetable {self.code}")
    
    def add_time_slot(self, start_time: time, end_time: time, slot_type: str = 'lecture') -> None:
        """
        Add a time slot.
        
        Args:
            start_time: Start time
            end_time: End time
            slot_type: Type of slot (lecture, tutorial, lab, etc.)
        """
        if start_time >= end_time:
            raise ValidationError("Start time must be before end time")
        
        slot = {
            'start_time': start_time,
            'end_time': end_time,
            'slot_type': slot_type,
            'duration_minutes': int((datetime.combine(date.min, end_time) - datetime.combine(date.min, start_time)).total_seconds() / 60)
        }
        
        self.daily_slots.append(slot)
        self.updated_at = datetime.now()
        logger.info(f"Added time slot to timetable {self.code}: {start_time}-{end_time}")
    
    def remove_time_slot(self, start_time: time, end_time: time) -> None:
        """
        Remove a time slot.
        
        Args:
            start_time: Start time of slot to remove
            end_time: End time of slot to remove
        """
        self.daily_slots = [slot for slot in self.daily_slots 
                           if slot['start_time'] != start_time or slot['end_time'] != end_time]
        self.updated_at = datetime.now()
        logger.info(f"Removed time slot from timetable {self.code}: {start_time}-{end_time}")
    
    def add_break(self, start_time: time, end_time: time, break_type: str = 'break') -> None:
        """
        Add a break.
        
        Args:
            start_time: Start time
            end_time: End time
            break_type: Type of break (short_break, lunch_break, prayer_break, etc.)
        """
        if start_time >= end_time:
            raise ValidationError("Break start time must be before end time")
        
        break_time = {
            'start_time': start_time,
            'end_time': end_time,
            'break_type': break_type,
            'duration_minutes': int((datetime.combine(date.min, end_time) - datetime.combine(date.min, start_time)).total_seconds() / 60)
        }
        
        self.breaks.append(break_time)
        self.updated_at = datetime.now()
        logger.info(f"Added break to timetable {code}: {start_time}-{end_time}")
    
    def remove_break(self, start_time: time, end_time: time) -> None:
        """
        Remove a break.
        
        Args:
            start_time: Start time of break to remove
            end_time: End time of break to remove
        """
        self.breaks = [break_time for break_time in self.breaks 
                      if break_time['start_time'] != start_time or break_time['end_time'] != end_time]
        self.updated_at = datetime.now()
        logger.info(f"Removed break from timetable {self.code}: {start_time}-{end_time}")
    
    def update_lunch_break(self, start_time: time, end_time: time) -> None:
        """
        Update lunch break.
        
        Args:
            start_time: Start time
            end_time: End time
        """
        if start_time >= end_time:
            raise ValidationError("Lunch break start time must be before end time")
        
        self.lunch_break = {
            'start_time': start_time,
            'end_time': end_time,
            'duration_minutes': int((datetime.combine(date.min, end_time) - datetime.combine(date.min, start_time)).total_seconds() / 60)
        }
        self.updated_at = datetime.now()
        logger.info(f"Updated lunch break for timetable {self.code}: {start_time}-{end_time}")
    
    def add_constraint(self, constraint_type: str, constraint_data: dict) -> None:
        """
        Add a scheduling constraint.
        
        Args:
            constraint_type: Type of constraint
            constraint_data: Constraint data
        """
        if constraint_type not in self.constraints:
            self.constraints[constraint_type] = []
        
        self.constraints[constraint_type].append(constraint_data)
        self.updated_at = datetime.now()
        logger.info(f"Added constraint {constraint_type} to timetable {self.code}")
    
    def remove_constraint(self, constraint_type: str, constraint_index: int) -> None:
        """
        Remove a scheduling constraint.
        
        Args:
            constraint_type: Type of constraint
            constraint_index: Index of constraint to remove
        """
        if constraint_type in self.constraints and 0 <= constraint_index < len(self.constraints[constraint_type]):
            self.constraints[constraint_type].pop(constraint_index)
            self.updated_at = datetime.now()
            logger.info(f"Removed constraint {constraint_type} from timetable {self.code}")
    
    def add_conflict(self, conflict_type: str, conflict_description: str) -> None:
        """
        Add a conflict to the timetable.
        
        Args:
            conflict_type: Type of conflict
            conflict_description: Description of the conflict
        """
        conflict = {
            'conflict_type': conflict_type,
            'description': conflict_description,
            'reported_at': datetime.now().isoformat(),
            'status': 'open'
        }
        
        self.conflicts.append(conflict)
        self.updated_at = datetime.now()
        logger.info(f"Added conflict to timetable {self.code}: {conflict_type} - {conflict_description}")
    
    def resolve_conflict(self, conflict_index: int, resolution: str) -> None:
        """
        Resolve a conflict.
        
        Args:
            conflict_index: Index of conflict to resolve
            resolution: Resolution description
        """
        if 0 <= conflict_index < len(self.conflicts):
            self.conflicts[conflict_index]['status'] = 'resolved'
            self.conflicts[conflict_index]['resolution'] = resolution
            self.conflicts[conflict_index]['resolved_at'] = datetime.now().isoformat()
            self.updated_at = datetime.now()
            logger.info(f"Resolved conflict {conflict_index} in timetable {self.code}")
        else:
            raise ValidationError("Invalid conflict index")
    
    def publish_timetable(self, published_by: str) -> None:
        """
        Publish the timetable.
        
        Args:
            published_by: User who published the timetable
        """
        if self.has_conflicts():
            raise ValidationError("Cannot publish timetable with conflicts")
        
        self.is_published = True
        self.metadata['published_by'] = published_by
        self.metadata['published_at'] = datetime.now().isoformat()
        self.updated_at = datetime.now()
        logger.info(f"Published timetable {self.code} by {published_by}")
    
    def lock_timetable(self, locked_by: str) -> None:
        """
        Lock the timetable.
        
        Args:
            locked_by: User who locked the timetable
        """
        self.is_locked = True
        self.metadata['locked_by'] = locked_by
        self.metadata['locked_at'] = datetime.now().isoformat()
        self.updated_at = datetime.now()
        logger.info(f"Locked timetable {self.code} by {locked_by}")
    
    def unlock_timetable(self, unlocked_by: str) -> None:
        """
        Unlock the timetable.
        
        Args:
            unlocked_by: User who unlocked the timetable
        """
        self.is_locked = False
        self.metadata['unlocked_by'] = unlocked_by
        self.metadata['unlocked_at'] = datetime.now().isoformat()
        self.updated_at = datetime.now()
        logger.info(f"Unlocked timetable {self.code} by {unlocked_by}")
    
    def approve_timetable(self, approved_by: str) -> None:
        """
        Approve the timetable.
        
        Args:
            approved_by: User who approved the timetable
        """
        self.is_approved = True
        self.approved_by = approved_by
        self.approval_date = datetime.now()
        self.metadata['approved_by'] = approved_by
        self.metadata['approved_at'] = datetime.now().isoformat()
        self.updated_at = datetime.now()
        logger.info(f"Approved timetable {self.code} by {approved_by}")
    
    def increment_version(self, reason: str = "") -> None:
        """
        Increment timetable version.
        
        Args:
            reason: Reason for version increment (optional)
        """
        self.version += 1
        if reason:
            self.revision_notes = reason
        
        self.updated_at = datetime.now()
        logger.info(f"Incremented version for timetable {self.code} to {self.version}")
    
    def get_duration_days(self) -> int:
        """
        Get timetable duration in days.
        
        Returns:
            Duration in days
        """
        if self.start_date and self.end_date:
            delta = self.end_date - self.start_date
            return max(0, delta.days)
        return 0
    
    def get_days_until_start(self) -> Optional[int]:
        """
        Get days until timetable start.
        
        Returns:
            Days until start, or None if no start date
        """
        if self.start_date:
            delta = self.start_date - datetime.now()
            return max(0, delta.days)
        return None
    
    def get_days_until_end(self) -> Optional[int]:
        """
        Get days until timetable end.
        
        Returns:
            Days until end, or None if no end date
        """
        if self.end_date:
            delta = self.end_date - datetime.now()
            return max(0, delta.days)
        return None
    
    def is_current(self) -> bool:
        """
        Check if timetable is current.
        
        Returns:
            True if timetable is current (within date range)
        """
        now = datetime.now()
        return self.start_date <= now <= self.end_date
    
    def has_conflicts(self) -> bool:
        """
        Check if timetable has conflicts.
        
        Returns:
            True if timetable has conflicts
        """
        return len(self.conflicts) > 0
    
    def get_timetable_status(self) -> str:
        """
        Get timetable status.
        
        Returns:
            Timetable status string
        """
        if not self.is_active:
            return 'inactive'
        elif not self.is_published:
            return 'draft'
        elif self.is_locked:
            return 'locked'
        elif self.is_current():
            return 'current'
        elif datetime.now() < self.start_date:
            return 'upcoming'
        else:
            return 'past'
    
    def get_timetable_summary(self) -> Dict[str, Any]:
        """
        Get timetable summary.
        
        Returns:
            Timetable summary dictionary
        """
        return {
            'id': self.id,
            'code': self.code,
            'title': self.title,
            'type': self.type,
            'status': self.get_timetable_status(),
            'academic_year': self.academic_year,
            'semester': self.semester,
            'batch': self.batch,
            'section': self.section,
            'is_active': self.is_active,
            'is_published': self.is_published,
            'is_locked': self.is_locked,
            'version': self.version,
            'working_days': self.working_days,
            'total_slots': len(self.daily_slots),
            'total_breaks': len(self.breaks),
            'has_conflicts': self.has_conflicts(),
            'total_entries': len(self.timetable_entries) if hasattr(self, 'timetable_entries') else 0,
            'start_date': self.start_date.isoformat() if self.start_date else None,
            'end_date': self.end_date.isoformat() if self.end_date else None,
            'duration_days': self.get_duration_days(),
            'is_current': self.is_current()
        }
    
    def get_availability(self) -> Dict[str, Any]:
        """
        Get timetable availability.
        
        Returns:
            Availability information
        """
        return {
            'slots_per_day': len(self.daily_slots),
            'working_days_per_week': len(self.working_days),
            'total_weeks': self.get_duration_days() // 7 if self.get_duration_days() > 0 else 0,
            'daily_hours': sum(slot['duration_minutes'] for slot in self.daily_slots) / 60,
            'weekly_hours': sum(slot['duration_minutes'] for slot in self.daily_slots) * len(self.working_days) / 60,
            'break_count': len(self.breaks),
            'lunch_break_duration': self.lunch_break.get('duration_minutes', 0)
        }
    
    def __repr__(self) -> str:
        """String representation of the timetable model."""
        return f"<TimetableModel(code='{self.code}', title='{self.title}', type='{self.type}', status='{self.get_timetable_status()}')>"