"""
Laboratory Management Models

This module defines Pydantic models for laboratory management:
- Laboratory creation, update, and response schemas
- Equipment and resource management
- Laboratory statistics and reporting models

Author: Edu-Flow Team
"""

from datetime import datetime
from typing import Optional, List, Dict, Any
from enum import Enum
from uuid import uuid4
from pydantic import BaseModel, Field, ConfigDict


class LabStatus(str, Enum):
    """Laboratory status enumeration."""
    ACTIVE = "active"
    INACTIVE = "inactive"
    MAINTENANCE = "maintenance"
    RESERVED = "reserved"
    AVAILABLE = "available"


class EquipmentStatus(str, Enum):
    """Equipment status enumeration."""
    OPERATIONAL = "operational"
    UNDER_REPAIR = "under_repair"
    DAMAGED = "damaged"
    CALIBRATION_DUE = "calibration_due"
    RETIRED = "retired"


class LabCreate(BaseModel):
    """Laboratory creation schema."""
    name: str = Field(..., description="Laboratory name", min_length=1, max_length=100)
    code: str = Field(..., description="Laboratory code", min_length=2, max_length=20)
    department_id: str = Field(..., description="Department ID")
    location: str = Field(..., description="Location")
    capacity: int = Field(..., description="Capacity", ge=1)
    description: Optional[str] = Field(None, description="Description")
    facilities: Optional[List[str]] = Field(None, description="Facilities")
    equipment: Optional[List[str]] = Field(None, description="Equipment list")
    status: LabStatus = Field(LabStatus.ACTIVE, description="Status")
    
    model_config = ConfigDict(from_attributes=True)


class LabUpdate(BaseModel):
    """Laboratory update schema."""
    name: Optional[str] = Field(None, description="Laboratory name", min_length=1, max_length=100)
    code: Optional[str] = Field(None, description="Laboratory code", min_length=2, max_length=20)
    department_id: Optional[str] = Field(None, description="Department ID")
    location: Optional[str] = Field(None, description="Location")
    capacity: Optional[int] = Field(None, description="Capacity", ge=1)
    description: Optional[str] = Field(None, description="Description")
    facilities: Optional[List[str]] = Field(None, description="Facilities")
    equipment: Optional[List[str]] = Field(None, description="Equipment list")
    status: Optional[LabStatus] = Field(None, description="Status")
    
    model_config = ConfigDict(from_attributes=True)


class LabResponse(BaseModel):
    """Laboratory response schema."""
    id: str = Field(..., description="Laboratory ID")
    name: str = Field(..., description="Laboratory name")
    code: str = Field(..., description="Laboratory code")
    department_id: str = Field(..., description="Department ID")
    location: str = Field(..., description="Location")
    capacity: int = Field(..., description="Capacity")
    current_utilization: int = Field(..., description="Current utilization", ge=0)
    description: Optional[str] = Field(None, description="Description")
    facilities: Optional[List[str]] = Field(None, description="Facilities")
    equipment: Optional[List[str]] = Field(None, description="Equipment list")
    status: LabStatus = Field(..., description="Status")
    created_at: datetime = Field(..., description="Creation timestamp")
    updated_at: datetime = Field(..., description="Last update timestamp")
    
    model_config = ConfigDict(from_attributes=True)


class EquipmentCreate(BaseModel):
    """Equipment creation schema."""
    name: str = Field(..., description="Equipment name", min_length=1, max_length=100)
    model: str = Field(..., description="Equipment model", min_length=1, max_length=50)
    serial_number: str = Field(..., description="Serial number", min_length=1, max_length=50)
    lab_id: str = Field(..., description="Laboratory ID")
    category: str = Field(..., description="Category")
    status: EquipmentStatus = Field(EquipmentStatus.OPERATIONAL, description="Status")
    purchase_date: Optional[datetime] = Field(None, description="Purchase date")
    warranty_expiry: Optional[datetime] = Field(None, description="Warranty expiry")
    maintenance_schedule: Optional[datetime] = Field(None, description="Maintenance schedule")
    specifications: Optional[Dict[str, str]] = Field(None, description="Specifications")
    description: Optional[str] = Field(None, description="Description")
    
    model_config = ConfigDict(from_attributes=True)


class EquipmentUpdate(BaseModel):
    """Equipment update schema."""
    name: Optional[str] = Field(None, description="Equipment name", min_length=1, max_length=100)
    model: Optional[str] = Field(None, description="Equipment model", min_length=1, max_length=50)
    serial_number: Optional[str] = Field(None, description="Serial number", min_length=1, max_length=50)
    lab_id: Optional[str] = Field(None, description="Laboratory ID")
    category: Optional[str] = Field(None, description="Category")
    status: Optional[EquipmentStatus] = Field(None, description="Status")
    purchase_date: Optional[datetime] = Field(None, description="Purchase date")
    warranty_expiry: Optional[datetime] = Field(None, description="Warranty expiry")
    maintenance_schedule: Optional[datetime] = Field(None, description="Maintenance schedule")
    specifications: Optional[Dict[str, str]] = Field(None, description="Specifications")
    description: Optional[str] = Field(None, description="Description")
    
    model_config = ConfigDict(from_attributes=True)


class EquipmentResponse(BaseModel):
    """Equipment response schema."""
    id: str = Field(..., description="Equipment ID")
    name: str = Field(..., description="Equipment name")
    model: str = Field(..., description="Equipment model")
    serial_number: str = Field(..., description="Serial number")
    lab_id: str = Field(..., description="Laboratory ID")
    category: str = Field(..., description="Category")
    status: EquipmentStatus = Field(..., description="Status")
    purchase_date: Optional[datetime] = Field(None, description="Purchase date")
    warranty_expiry: Optional[datetime] = Field(None, description="Warranty expiry")
    maintenance_schedule: Optional[datetime] = Field(None, description="Maintenance schedule")
    specifications: Optional[Dict[str, str]] = Field(None, description="Specifications")
    description: Optional[str] = Field(None, description="Description")
    created_at: datetime = Field(..., description="Creation timestamp")
    updated_at: datetime = Field(..., description="Last update timestamp")
    
    model_config = ConfigDict(from_attributes=True)


class LabReservation(BaseModel):
    """Laboratory reservation schema."""
    id: str = Field(..., description="Reservation ID")
    lab_id: str = Field(..., description="Laboratory ID")
    lab_name: str = Field(..., description="Laboratory name")
    course_id: str = Field(..., description="Course ID")
    class_id: str = Field(..., description="Class ID")
    instructor_id: str = Field(..., description="Instructor ID")
    reservation_date: datetime = Field(..., description="Reservation date")
    start_time: datetime = Field(..., description="Start time")
    end_time: datetime = Field(..., description="End time")
    purpose: str = Field(..., description="Purpose")
    status: str = Field(..., description="Status")
    required_equipment: Optional[List[str]] = Field(None, description="Required equipment")
    actual_equipment: Optional[List[str]] = Field(None, description="Actual equipment used")
    attendance_count: int = Field(..., description="Attendance count", ge=0)
    created_by: str = Field(..., description="Created by")
    created_at: datetime = Field(..., description="Creation timestamp")
    updated_at: datetime = Field(..., description="Last update timestamp")
    
    model_config = ConfigDict(from_attributes=True)


class LabStats(BaseModel):
    """Laboratory statistics schema."""
    lab_id: str = Field(..., description="Laboratory ID")
    lab_name: str = Field(..., description="Laboratory name")
    department_id: str = Field(..., description="Department ID")
    total_reservations: int = Field(..., description="Total reservations", ge=0)
    completed_reservations: int = Field(..., description="Completed reservations", ge=0)
    cancelled_reservations: int = Field(..., description="Cancelled reservations", ge=0)
    average_utilization: float = Field(..., description="Average utilization", ge=0.0, le=1.0)
    equipment_utilization: float = Field(..., description="Equipment utilization", ge=0.0, le=1.0)
    maintenance_count: int = Field(..., description="Maintenance count", ge=0)
    maintenance_cost: float = Field(..., description="Maintenance cost", ge=0.0)
    created_at: datetime = Field(..., description="Creation timestamp")
    updated_at: datetime = Field(..., description="Last update timestamp")
    
    model_config = ConfigDict(from_attributes=True)


class LabAnalytics(BaseModel):
    """Laboratory analytics schema."""
    lab_id: str = Field(..., description="Laboratory ID")
    lab_name: str = Field(..., description="Laboratory name")
    department_id: str = Field(..., description="Department ID")
    time_period: str = Field(..., description="Time period")
    total_hours_booked: int = Field(..., description="Total hours booked", ge=0)
    total_hours_available: int = Field(..., description="Total hours available", ge=0)
    utilization_rate: float = Field(..., description="Utilization rate", ge=0.0, le=1.0)
    peak_hours: List[str] = Field(..., description="Peak hours")
    peak_days: List[str] = Field(..., description="Peak days")
    popular_equipment: List[str] = Field(..., description="Popular equipment")
    maintenance_history: List[Dict[str, Any]] = Field(..., description="Maintenance history")
    created_at: datetime = Field(..., description="Creation timestamp")
    updated_at: datetime = Field(..., description="Last update timestamp")
    
    model_config = ConfigDict(from_attributes=True)


class LaboratoryBooking(BaseModel):
    """Laboratory booking schema."""
    id: str = Field(..., description="Booking ID")
    laboratory_id: str = Field(..., description="Laboratory ID")
    laboratory_name: str = Field(..., description="Laboratory name")
    course_id: str = Field(..., description="Course ID")
    class_id: str = Field(..., description="Class ID")
    instructor_id: str = Field(..., description="Instructor ID")
    booking_date: datetime = Field(..., description="Booking date")
    start_time: datetime = Field(..., description="Start time")
    end_time: datetime = Field(..., description="End time")
    purpose: str = Field(..., description="Purpose")
    status: str = Field(..., description="Status")
    equipment_required: Optional[List[str]] = Field(None, description="Equipment required")
    equipment_allocated: Optional[List[str]] = Field(None, description="Equipment allocated")
    created_by: str = Field(..., description="Created by")
    created_at: datetime = Field(..., description="Creation timestamp")
    updated_at: datetime = Field(..., description="Last update timestamp")
    
    model_config = ConfigDict(from_attributes=True)


class LaboratoryBookingResponse(BaseModel):
    """Laboratory booking response schema."""
    id: str = Field(..., description="Booking ID")
    laboratory_id: str = Field(..., description="Laboratory ID")
    laboratory_name: str = Field(..., description="Laboratory name")
    course_id: str = Field(..., description="Course ID")
    class_id: str = Field(..., description="Class ID")
    instructor_id: str = Field(..., description="Instructor ID")
    booking_date: datetime = Field(..., description="Booking date")
    start_time: datetime = Field(..., description="Start time")
    end_time: datetime = Field(..., description="End time")
    purpose: str = Field(..., description="Purpose")
    status: str = Field(..., description="Status")
    equipment_required: Optional[List[str]] = Field(None, description="Equipment required")
    equipment_allocated: Optional[List[str]] = Field(None, description="Equipment allocated")
    created_by: str = Field(..., description="Created by")
    created_at: datetime = Field(..., description="Creation timestamp")
    updated_at: datetime = Field(..., description="Last update timestamp")
    
    model_config = ConfigDict(from_attributes=True)


class LaboratoryEquipment(BaseModel):
    """Laboratory equipment schema."""
    id: str = Field(..., description="Equipment ID")
    laboratory_id: str = Field(..., description="Laboratory ID")
    equipment_name: str = Field(..., description="Equipment name")
    equipment_model: str = Field(..., description="Equipment model")
    serial_number: str = Field(..., description="Serial number")
    category: str = Field(..., description="Category")
    status: str = Field(..., description="Status")
    purchase_date: Optional[datetime] = Field(None, description="Purchase date")
    warranty_expiry: Optional[datetime] = Field(None, description="Warranty expiry")
    maintenance_date: Optional[datetime] = Field(None, description="Maintenance date")
    specifications: Optional[Dict[str, str]] = Field(None, description="Specifications")
    created_at: datetime = Field(..., description="Creation timestamp")
    updated_at: datetime = Field(..., description="Last update timestamp")
    
    model_config = ConfigDict(from_attributes=True)


class LaboratoryMaintenance(BaseModel):
    """Laboratory maintenance schema."""
    id: str = Field(..., description="Maintenance ID")
    laboratory_id: str = Field(..., description="Laboratory ID")
    equipment_id: Optional[str] = Field(None, description="Equipment ID")
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


class LaboratoryConflict(BaseModel):
    """Laboratory conflict schema."""
    id: str = Field(..., description="Conflict ID")
    laboratory_id: str = Field(..., description="Laboratory ID")
    booking_id: str = Field(..., description="Booking ID")
    conflict_type: str = Field(..., description="Conflict type")
    conflicting_booking_id: str = Field(..., description="Conflicting booking ID")
    start_time: datetime = Field(..., description="Start time")
    end_time: datetime = Field(..., description="End time")
    severity: str = Field(..., description="Severity")
    resolved: bool = Field(False, description="Resolved")
    resolution_notes: Optional[str] = Field(None, description="Resolution notes")
    created_at: datetime = Field(..., description="Creation timestamp")
    updated_at: datetime = Field(..., description="Last update timestamp")
    
    model_config = ConfigDict(from_attributes=True)


class ResourceAllocation(BaseModel):
    """Resource allocation schema."""
    id: str = Field(..., description="Allocation ID")
    resource_type: str = Field(..., description="Resource type")
    resource_id: str = Field(..., description="Resource ID")
    laboratory_id: str = Field(..., description="Laboratory ID")
    allocated_by: str = Field(..., description="Allocated by")
    allocated_at: datetime = Field(..., description="Allocated at")
    allocation_status: str = Field(..., description="Allocation status")
    allocation_notes: Optional[str] = Field(None, description="Allocation notes")
    created_at: datetime = Field(..., description="Creation timestamp")
    updated_at: datetime = Field(..., description="Last update timestamp")
    
    model_config = ConfigDict(from_attributes=True)