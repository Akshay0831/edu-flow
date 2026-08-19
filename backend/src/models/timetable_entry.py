"""
Timetable Entry Models

This module defines Pydantic models for timetable entry management:
- Timetable entry creation, update, and response schemas
- Schedule and slot management
- Resource allocation models

Author: Edu-Flow Team
"""

from datetime import datetime, date, time
from typing import Optional, List
from uuid import uuid4
from enum import Enum
from pydantic import BaseModel, Field, ConfigDict


class TimetableStatus(str, Enum):
    """Timetable status enumeration."""
    ACTIVE = "active"
    INACTIVE = "inactive"
    CANCELLED = "cancelled"
    COMPLETED = "completed"


class DayOfWeek(str, Enum):
    """Day of week enumeration."""
    MONDAY = "monday"
    TUESDAY = "tuesday"
    WEDNESDAY = "wednesday"
    THURSDAY = "thursday"
    FRIDAY = "friday"
    SATURDAY = "saturday"
    SUNDAY = "sunday"


class SlotType(str, Enum):
    """Slot type enumeration."""
    LECTURE = "lecture"
    LAB = "lab"
    SEMINAR = "seminar"
    EXAM = "exam"
    MEETING = "meeting"
    BREAK = "break"
    OTHER = "other"


class TimetableEntryCreate(BaseModel):
    """Timetable entry creation schema."""
    course_id: str = Field(..., description="Course ID")
    class_id: str = Field(..., description="Class ID")
    instructor_id: str = Field(..., description="Instructor ID")
    room_id: str = Field(..., description="Room ID")
    day_of_week: DayOfWeek = Field(..., description="Day of week")
    start_time: time = Field(..., description="Start time")
    end_time: time = Field(..., description="End time")
    slot_type: SlotType = Field(..., description="Slot type")
    semester: str = Field(..., description="Semester")
    academic_year: int = Field(..., description="Academic year")
    capacity: int = Field(..., description="Capacity", ge=1)
    description: Optional[str] = Field(None, description="Description")
    status: TimetableStatus = Field(TimetableStatus.ACTIVE, description="Status")
    
    model_config = ConfigDict(from_attributes=True)


class TimetableEntryUpdate(BaseModel):
    """Timetable entry update schema."""
    course_id: Optional[str] = Field(None, description="Course ID")
    class_id: Optional[str] = Field(None, description="Class ID")
    instructor_id: Optional[str] = Field(None, description="Instructor ID")
    room_id: Optional[str] = Field(None, description="Room ID")
    day_of_week: Optional[DayOfWeek] = Field(None, description="Day of week")
    start_time: Optional[time] = Field(None, description="Start time")
    end_time: Optional[time] = Field(None, description="End time")
    slot_type: Optional[SlotType] = Field(None, description="Slot type")
    semester: Optional[str] = Field(None, description="Semester")
    academic_year: Optional[int] = Field(None, description="Academic year")
    capacity: Optional[int] = Field(None, description="Capacity", ge=1)
    description: Optional[str] = Field(None, description="Description")
    status: Optional[TimetableStatus] = Field(None, description="Status")
    
    model_config = ConfigDict(from_attributes=True)


class TimetableEntryResponse(BaseModel):
    """Timetable entry response schema."""
    id: str = Field(..., description="Timetable entry ID")
    course_id: str = Field(..., description="Course ID")
    class_id: str = Field(..., description="Class ID")
    instructor_id: str = Field(..., description="Instructor ID")
    room_id: str = Field(..., description="Room ID")
    day_of_week: DayOfWeek = Field(..., description="Day of week")
    start_time: time = Field(..., description="Start time")
    end_time: time = Field(..., description="End time")
    slot_type: SlotType = Field(..., description="Slot type")
    semester: str = Field(..., description="Semester")
    academic_year: int = Field(..., description="Academic year")
    capacity: int = Field(..., description="Capacity")
    current_enrollment: int = Field(..., description="Current enrollment", ge=0)
    description: Optional[str] = Field(None, description="Description")
    status: TimetableStatus = Field(..., description="Status")
    created_at: datetime = Field(..., description="Creation timestamp")
    updated_at: datetime = Field(..., description="Last update timestamp")
    
    model_config = ConfigDict(from_attributes=True)


class TimetableEntryOccurrence(BaseModel):
    """Timetable occurrence schema."""
    id: str = Field(..., description="Occurrence ID")
    timetable_entry_id: str = Field(..., description="Timetable entry ID")
    occurrence_date: date = Field(..., description="Occurrence date")
    actual_start_time: Optional[time] = Field(None, description="Actual start time")
    actual_end_time: Optional[time] = Field(None, description="Actual end time")
    status: TimetableStatus = Field(..., description="Status")
    attendance_recorded: bool = Field(False, description="Attendance recorded")
    notes: Optional[str] = Field(None, description="Notes")
    created_at: datetime = Field(..., description="Creation timestamp")
    updated_at: datetime = Field(..., description="Last update timestamp")
    
    model_config = ConfigDict(from_attributes=True)


class TimetableEntryConflict(BaseModel):
    """Timetable entry conflict schema."""
    id: str = Field(..., description="Conflict ID")
    timetable_entry_id: str = Field(..., description="Timetable entry ID")
    conflict_type: str = Field(..., description="Conflict type")
    conflicted_with: List[str] = Field(..., description="Conflicted with")
    severity: str = Field(..., description="Severity")
    resolved: bool = Field(False, description="Resolved")
    resolution_notes: Optional[str] = Field(None, description="Resolution notes")
    created_at: datetime = Field(..., description="Creation timestamp")
    updated_at: datetime = Field(..., description="Last update timestamp")
    
    model_config = ConfigDict(from_attributes=True)


class ResourceAllocationRequest(BaseModel):
    """Resource allocation request schema."""
    id: str = Field(..., description="Request ID")
    timetable_entry_id: str = Field(..., description="Timetable entry ID")
    resource_type: str = Field(..., description="Resource type")
    resource_id: str = Field(..., description="Resource ID")
    requested_capacity: int = Field(..., description="Requested capacity", ge=1)
    allocated_capacity: int = Field(..., description="Allocated capacity", ge=0)
    allocation_status: str = Field(..., description="Allocation status")
    priority: int = Field(..., description="Priority", ge=1)
    requested_by: str = Field(..., description="Requested by")
    approval_notes: Optional[str] = Field(None, description="Approval notes")
    created_at: datetime = Field(..., description="Creation timestamp")
    updated_at: datetime = Field(..., description="Last update timestamp")
    
    model_config = ConfigDict(from_attributes=True)


class ResourceAllocationResponse(BaseModel):
    """Resource allocation response schema."""
    id: str = Field(..., description="Allocation ID")
    timetable_entry_id: str = Field(..., description="Timetable entry ID")
    resource_type: str = Field(..., description="Resource type")
    resource_id: str = Field(..., description="Resource ID")
    resource_name: str = Field(..., description="Resource name")
    requested_capacity: int = Field(..., description="Requested capacity", ge=1)
    allocated_capacity: int = Field(..., description="Allocated capacity", ge=0)
    allocation_status: str = Field(..., description="Allocation status")
    priority: int = Field(..., description="Priority", ge=1)
    requested_by: str = Field(..., description="Requested by")
    approved_by: Optional[str] = Field(None, description="Approved by")
    approved_at: Optional[datetime] = Field(None, description="Approved at")
    approval_notes: Optional[str] = Field(None, description="Approval notes")
    created_at: datetime = Field(..., description="Creation timestamp")
    updated_at: datetime = Field(..., description="Last update timestamp")
    
    model_config = ConfigDict(from_attributes=True)


class ResourceAllocation(BaseModel):
    """Resource allocation model."""
    id: str = Field(..., description="Allocation ID")
    timetable_entry_id: str = Field(..., description="Timetable entry ID")
    resource_type: str = Field(..., description="Resource type")
    resource_id: str = Field(..., description="Resource ID")
    resource_name: str = Field(..., description="Resource name")
    requested_capacity: int = Field(..., description="Requested capacity", ge=1)
    allocated_capacity: int = Field(..., description="Allocated capacity", ge=0)
    allocation_status: str = Field(..., description="Allocation status")
    priority: int = Field(..., description="Priority", ge=1)
    requested_by: str = Field(..., description="Requested by")
    requested_at: datetime = Field(..., description="Requested at")
    approved_by: Optional[str] = Field(None, description="Approved by")
    approved_at: Optional[datetime] = Field(None, description="Approved at")
    approval_notes: Optional[str] = Field(None, description="Approval notes")
    created_at: datetime = Field(..., description="Creation timestamp")
    updated_at: datetime = Field(..., description="Last update timestamp")
    
    model_config = ConfigDict(from_attributes=True)


class TimetableStats(BaseModel):
    """Timetable statistics schema."""
    timetable_entry_id: str = Field(..., description="Timetable entry ID")
    course_id: str = Field(..., description="Course ID")
    class_id: str = Field(..., description="Class ID")
    instructor_id: str = Field(..., description="Instructor ID")
    semester: str = Field(..., description="Semester")
    academic_year: int = Field(..., description="Academic year")
    total_occurrences: int = Field(..., description="Total occurrences", ge=0)
    completed_occurrences: int = Field(..., description="Completed occurrences", ge=0)
    cancelled_occurrences: int = Field(..., description="Cancelled occurrences", ge=0)
    average_attendance: float = Field(..., description="Average attendance", ge=0.0, le=100.0)
    resource_utilization_rate: float = Field(..., description="Resource utilization rate", ge=0.0, le=1.0)
    conflict_rate: float = Field(..., description="Conflict rate", ge=0.0, le=1.0)
    on_time_start_rate: float = Field(..., description="On-time start rate", ge=0.0, le=1.0)
    created_at: datetime = Field(..., description="Creation timestamp")
    updated_at: datetime = Field(..., description="Last update timestamp")
    
    model_config = ConfigDict(from_attributes=True)