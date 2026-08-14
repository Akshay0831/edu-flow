"""
Room Management Models

This module defines Pydantic models for room management:
- Room creation, update, and response schemas
- Room allocation and reservation models
- Room statistics and analytics

Author: Edu-Flow Team
"""

from datetime import datetime
from typing import Optional, List, Dict
from enum import Enum
from uuid import uuid4
from pydantic import BaseModel, Field, ConfigDict


class RoomStatus(str, Enum):
    """Room status enumeration."""
    AVAILABLE = "available"
    OCCUPIED = "occupied"
    RESERVED = "reserved"
    MAINTENANCE = "maintenance"
    CLEANING = "cleaning"


class RoomType(str, Enum):
    """Room type enumeration."""
    CLASSROOM = "classroom"
    LABORATORY = "laboratory"
    LECTURE_HALL = "lecture_hall"
    CONFERENCE_ROOM = "conference_room"
    MEETING_ROOM = "meeting_room"
    LIBRARY = "library"
    STAFF_ROOM = "staff_room"
    STORAGE = "storage"


class RoomFacility(str, Enum):
    """Room facility enumeration."""
    PROJECTOR = "projector"
    WHITEBOARD = "whiteboard"
    BLACKBOARD = "blackboard"
    AIR_CONDITIONING = "air_conditioning"
    HEATING = "heating"
    VENTILATION = "ventilation"
    INTERNET = "internet"
    POWER_OUTLETS = "power_outlets"
    TV = "tv"
    MICROPHONE = "microphone"
    SPEAKERS = "speakers"
    VIDEO_CONFERENCING = "video_conferencing"


class RoomCreate(BaseModel):
    """Room creation schema."""
    name: str = Field(..., description="Room name", min_length=1, max_length=100)
    code: str = Field(..., description="Room code", min_length=2, max_length=20)
    room_type: RoomType = Field(..., description="Room type")
    building: str = Field(..., description="Building")
    floor: int = Field(..., description="Floor", ge=1)
    capacity: int = Field(..., description="Capacity", ge=1)
    location: str = Field(..., description="Location")
    description: Optional[str] = Field(None, description="Description")
    facilities: Optional[List[RoomFacility]] = Field(None, description="Facilities")
    status: RoomStatus = Field(RoomStatus.AVAILABLE, description="Status")
    department_id: Optional[str] = Field(None, description="Department ID")
    
    model_config = ConfigDict(from_attributes=True)


class RoomUpdate(BaseModel):
    """Room update schema."""
    name: Optional[str] = Field(None, description="Room name", min_length=1, max_length=100)
    code: Optional[str] = Field(None, description="Room code", min_length=2, max_length=20)
    room_type: Optional[RoomType] = Field(None, description="Room type")
    building: Optional[str] = Field(None, description="Building")
    floor: Optional[int] = Field(None, description="Floor", ge=1)
    capacity: Optional[int] = Field(None, description="Capacity", ge=1)
    location: Optional[str] = Field(None, description="Location")
    description: Optional[str] = Field(None, description="Description")
    facilities: Optional[List[RoomFacility]] = Field(None, description="Facilities")
    status: Optional[RoomStatus] = Field(None, description="Status")
    department_id: Optional[str] = Field(None, description="Department ID")
    
    model_config = ConfigDict(from_attributes=True)


class RoomResponse(BaseModel):
    """Room response schema."""
    id: str = Field(..., description="Room ID")
    name: str = Field(..., description="Room name")
    code: str = Field(..., description="Room code")
    room_type: RoomType = Field(..., description="Room type")
    building: str = Field(..., description="Building")
    floor: int = Field(..., description="Floor")
    capacity: int = Field(..., description="Capacity")
    current_occupancy: int = Field(..., description="Current occupancy", ge=0)
    location: str = Field(..., description="Location")
    description: Optional[str] = Field(None, description="Description")
    facilities: Optional[List[RoomFacility]] = Field(None, description="Facilities")
    status: RoomStatus = Field(..., description="Status")
    department_id: Optional[str] = Field(None, description="Department ID")
    created_at: datetime = Field(..., description="Creation timestamp")
    updated_at: datetime = Field(..., description="Last update timestamp")
    
    model_config = ConfigDict(from_attributes=True)


class RoomReservation(BaseModel):
    """Room reservation schema."""
    id: str = Field(..., description="Reservation ID")
    room_id: str = Field(..., description="Room ID")
    room_name: str = Field(..., description="Room name")
    course_id: str = Field(..., description="Course ID")
    class_id: str = Field(..., description="Class ID")
    instructor_id: str = Field(..., description="Instructor ID")
    reservation_date: datetime = Field(..., description="Reservation date")
    start_time: datetime = Field(..., description="Start time")
    end_time: datetime = Field(..., description="End time")
    purpose: str = Field(..., description="Purpose")
    status: str = Field(..., description="Status")
    attendees_count: int = Field(..., description="Attendees count", ge=0)
    requirements: Optional[str] = Field(None, description="Requirements")
    created_by: str = Field(..., description="Created by")
    created_at: datetime = Field(..., description="Creation timestamp")
    updated_at: datetime = Field(..., description="Last update timestamp")
    
    model_config = ConfigDict(from_attributes=True)


class RoomAvailability(BaseModel):
    """Room availability schema."""
    room_id: str = Field(..., description="Room ID")
    room_name: str = Field(..., description="Room name")
    date: datetime = Field(..., description="Date")
    time_slots: List[Dict[str, datetime]] = Field(..., description="Time slots")
    available_slots: int = Field(..., description="Available slots", ge=0)
    total_slots: int = Field(..., description="Total slots", ge=0)
    utilization_rate: float = Field(..., description="Utilization rate", ge=0.0, le=1.0)
    created_at: datetime = Field(..., description="Creation timestamp")
    updated_at: datetime = Field(..., description="Last update timestamp")
    
    model_config = ConfigDict(from_attributes=True)


class RoomStats(BaseModel):
    """Room statistics schema."""
    room_id: str = Field(..., description="Room ID")
    room_name: str = Field(..., description="Room name")
    total_reservations: int = Field(..., description="Total reservations", ge=0)
    successful_reservations: int = Field(..., description="Successful reservations", ge=0)
    cancelled_reservations: int = Field(..., description="Cancelled reservations", ge=0)
    average_utilization: float = Field(..., description="Average utilization", ge=0.0, le=1.0)
    peak_hours: List[str] = Field(..., description="Peak hours")
    peak_days: List[str] = Field(..., description="Peak days")
    maintenance_count: int = Field(..., description="Maintenance count", ge=0)
    created_at: datetime = Field(..., description="Creation timestamp")
    updated_at: datetime = Field(..., description="Last update timestamp")
    
    model_config = ConfigDict(from_attributes=True)


class RoomAnalytics(BaseModel):
    """Room analytics schema."""
    building: str = Field(..., description="Building")
    floor: int = Field(..., description="Floor")
    time_period: str = Field(..., description="Time period")
    total_rooms: int = Field(..., description="Total rooms", ge=0)
    available_rooms: int = Field(..., description="Available rooms", ge=0)
    occupied_rooms: int = Field(..., description="Occupied rooms", ge=0)
    utilization_rate: float = Field(..., description="Utilization rate", ge=0.0, le=1.0)
    popular_rooms: List[str] = Field(..., description="Popular rooms")
    peak_usage_times: List[str] = Field(..., description="Peak usage times")
    room_type_distribution: Dict[str, int] = Field(..., description="Room type distribution")
    created_at: datetime = Field(..., description="Creation timestamp")
    updated_at: datetime = Field(..., description="Last update timestamp")
    
    model_config = ConfigDict(from_attributes=True)


class RoomBooking(BaseModel):
    """Room booking schema."""
    id: str = Field(..., description="Booking ID")
    room_id: str = Field(..., description="Room ID")
    room_name: str = Field(..., description="Room name")
    booking_date: datetime = Field(..., description="Booking date")
    start_time: datetime = Field(..., description="Start time")
    end_time: datetime = Field(..., description="End time")
    purpose: str = Field(..., description="Purpose")
    status: str = Field(..., description="Status")
    created_by: str = Field(..., description="Created by")
    created_at: datetime = Field(..., description="Creation timestamp")
    updated_at: datetime = Field(..., description="Last update timestamp")
    
    model_config = ConfigDict(from_attributes=True)


class RoomBookingResponse(BaseModel):
    """Room booking response schema."""
    id: str = Field(..., description="Booking ID")
    room_id: str = Field(..., description="Room ID")
    room_name: str = Field(..., description="Room name")
    booking_date: datetime = Field(..., description="Booking date")
    start_time: datetime = Field(..., description="Start time")
    end_time: datetime = Field(..., description="End time")
    purpose: str = Field(..., description="Purpose")
    status: str = Field(..., description="Status")
    created_by: str = Field(..., description="Created by")
    created_at: datetime = Field(..., description="Creation timestamp")
    updated_at: datetime = Field(..., description="Last update timestamp")
    
    model_config = ConfigDict(from_attributes=True)


class RoomMaintenance(BaseModel):
    """Room maintenance schema."""
    id: str = Field(..., description="Maintenance ID")
    room_id: str = Field(..., description="Room ID")
    maintenance_type: str = Field(..., description="Maintenance type")
    description: str = Field(..., description="Description")
    scheduled_date: datetime = Field(..., description="Scheduled date")
    completed_date: Optional[datetime] = Field(None, description="Completed date")
    performed_by: str = Field(..., description="Performed by")
    cost: float = Field(..., description="Cost", ge=0.0)
    status: str = Field(..., description="Status")
    created_at: datetime = Field(..., description="Creation timestamp")
    updated_at: datetime = Field(..., description="Last update timestamp")
    
    model_config = ConfigDict(from_attributes=True)