"""
Allocation Model for Database Operations

This module provides the SQLAlchemy model for Allocation entity.
It includes all fields and relationships for resource allocation management.

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


class AllocationModel(BaseModel):
    """
    SQLAlchemy model for Allocation entity.
    
    Represents resource allocation with conflict detection and availability checking.
    """
    __tablename__ = "allocations"
    
    # Allocation identification
    code = Column(String(50), nullable=False, index=True)
    name = Column(String(200), nullable=False, index=True)
    description = Column(Text)
    type = Column(String(50), nullable=False)  # room, laboratory, equipment, teacher
    
    # Resource details
    resource_id = Column(String(50), nullable=False)  # ID of the allocated resource
    resource_name = Column(String(200), nullable=False)
    resource_type = Column(String(50), nullable=False)  # classroom, lab, equipment, teacher
    
    # Allocation period
    start_date = Column(DateTime, nullable=False)
    end_date = Column(DateTime, nullable=False)
    start_time = Column(Time, nullable=False)
    end_time = Column(Time, nullable=False)
    days_of_week = Column(JSON, default=list)  # ["Monday", "Wednesday", "Friday"]
    
    # Assignment details
    assigned_to_id = Column(String(50), nullable=False)  # ID of assignee (class, teacher, etc.)
    assigned_to_type = Column(String(50), nullable=False)  # class, teacher, etc.
    assigned_by_id = Column(String(50), ForeignKey("users.id"), nullable=False)
    assigned_at = Column(DateTime, default=datetime.now)
    
    # Status and priority
    status = Column(String(20), nullable=False, default="active")  # active, inactive, cancelled, pending
    priority = Column(Integer, default=0)  # 0-100, higher number = higher priority
    is_recurring = Column(Boolean, default=False)
    is_conflict = Column(Boolean, default=False)
    
    # Usage tracking
    actual_start_time = Column(DateTime)
    actual_end_time = Column(DateTime)
    actual_usage_minutes = Column(Integer, default=0)
    is_used = Column(Boolean, default=False)
    
    # Conflict management
    conflict_resolution = Column(Text)  # Resolution notes if there's a conflict
    alternative_resource_id = Column(String(50))  # Alternative resource ID
    
    # Allocation metadata
    metadata = Column(JSON, default=dict)
    notes = Column(Text)
    
    # Relationships
    assigned_by = relationship("UserModel")
    resource = relationship("ResourceModel")
    allocation_conflicts = relationship("AllocationConflictModel")
    usage_logs = relationship("UsageLogModel")
    
    def __init__(self, **kwargs):
        """Initialize the allocation model with provided data."""
        # Set default values for optional fields
        kwargs.setdefault('days_of_week', [])
        kwargs.setdefault('status', 'active')
        kwargs.setdefault('priority', 0)
        kwargs.setdefault('is_recurring', False)
        kwargs.setdefault('is_conflict', False)
        kwargs.setdefault('actual_usage_minutes', 0)
        kwargs.setdefault('is_used', False)
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
        
        if 'actual_start_time' in data and isinstance(data['actual_start_time'], datetime):
            data['actual_start_time'] = data['actual_start_time'].isoformat()
        else:
            data['actual_start_time'] = None
        
        if 'actual_end_time' in data and isinstance(data['actual_end_time'], datetime):
            data['actual_end_time'] = data['actual_end_time'].isoformat()
        else:
            data['actual_end_time'] = None
        
        # Convert JSON fields to proper format
        if 'days_of_week' in data and isinstance(data['days_of_week'], list):
            data['days_of_week'] = data['days_of_week']
        else:
            data['days_of_week'] = []
        
        if 'metadata' in data and isinstance(data['metadata'], dict):
            data['metadata'] = data['metadata']
        else:
            data['metadata'] = {}
        
        # Calculate allocation duration
        if data['start_date'] and data['end_date'] and data['start_time'] and data['end_time']:
            start_datetime = datetime.fromisoformat(data['start_date'].replace('Z', '+00:00'))
            end_datetime = datetime.fromisoformat(data['end_date'].replace('Z', '+00:00'))
            start_datetime = start_datetime.replace(hour=data['start_time'].split(':')[0], minute=data['start_time'].split(':')[1])
            end_datetime = end_datetime.replace(hour=data['end_time'].split(':')[0], minute=data['end_time'].split(':')[1])
            duration = end_datetime - start_datetime
            data['duration_minutes'] = int(duration.total_seconds() / 60)
        else:
            data['duration_minutes'] = 0
        
        # Include relationships if requested
        if include_relationships:
            if hasattr(self, 'assigned_by') and self.assigned_by:
                data['assigned_by'] = self.assigned_by.to_dict()
            else:
                data['assigned_by'] = None
            
            if hasattr(self, 'resource') and self.resource:
                data['resource'] = self.resource.to_dict()
            else:
                data['resource'] = None
            
            if hasattr(self, 'allocation_conflicts') and self.allocation_conflicts:
                data['allocation_conflicts'] = [conflict.to_dict() for conflict in self.allocation_conflicts]
            else:
                data['allocation_conflicts'] = []
            
            if hasattr(self, 'usage_logs') and self.usage_logs:
                data['usage_logs'] = [log.to_dict() for log in self.usage_logs]
            else:
                data['usage_logs'] = []
        
        return data
    
    def update(self, **kwargs) -> None:
        """Update the model with new data."""
        # Handle special field updates
        if 'days_of_week' in kwargs and isinstance(kwargs['days_of_week'], list):
            self.days_of_week = kwargs['days_of_week']
        if 'metadata' in kwargs and isinstance(kwargs['metadata'], dict):
            self.metadata = kwargs['metadata']
        
        super().update(**kwargs)
    
    def validate(self) -> bool:
        """
        Validate the allocation model data.
        
        Returns:
            True if valid, False otherwise
            
        Raises:
            ValidationError: If validation fails
        """
        try:
            # Call base validation
            super().validate()
            
            # Allocation-specific validations
            if not self.code:
                raise ValidationError("Allocation code is required")
            
            if not self.name:
                raise ValidationError("Allocation name is required")
            
            if not self.type:
                raise ValidationError("Allocation type is required")
            
            if not self.resource_id:
                raise ValidationError("Resource ID is required")
            
            if not self.resource_name:
                raise ValidationError("Resource name is required")
            
            if not self.resource_type:
                raise ValidationError("Resource type is required")
            
            if not self.assigned_to_id:
                raise ValidationError("Assigned to ID is required")
            
            if not self.assigned_to_type:
                raise ValidationError("Assigned to type is required")
            
            if not self.assigned_by_id:
                raise ValidationError("Assigned by ID is required")
            
            # Date and time validation
            if self.start_date > self.end_date:
                raise ValidationError("Start date must be before or equal to end date")
            
            if self.start_time >= self.end_time:
                raise ValidationError("Start time must be before end time")
            
            if self.actual_start_time and self.actual_end_time:
                if self.actual_start_time > self.actual_end_time:
                    raise ValidationError("Actual start time must be before actual end time")
            
            # Priority validation
            if self.priority < 0 or self.priority > 100:
                raise ValidationError("Priority must be between 0 and 100")
            
            # Days of week validation
            if not isinstance(self.days_of_week, list):
                raise ValidationError("Days of week must be a list")
            
            valid_days = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]
            for day in self.days_of_week:
                if day not in valid_days:
                    raise ValidationError(f"Invalid day of week: {day}")
            
            # Metadata validation
            if not isinstance(self.metadata, dict):
                raise ValidationError("Metadata must be a dictionary")
            
            # Type validation
            valid_types = ["room", "laboratory", "equipment", "teacher"]
            if self.type not in valid_types:
                raise ValidationError(f"Invalid allocation type: {self.type}")
            
            # Resource type validation
            valid_resource_types = ["classroom", "laboratory", "equipment", "teacher", "facility"]
            if self.resource_type not in valid_resource_types:
                raise ValidationError(f"Invalid resource type: {self.resource_type}")
            
            # Assigned to type validation
            valid_assigned_types = ["class", "teacher", "program", "event"]
            if self.assigned_to_type not in valid_assigned_types:
                raise ValidationError(f"Invalid assigned to type: {self.assigned_to_type}")
            
            # Status validation
            valid_statuses = ["active", "inactive", "cancelled", "pending", "completed"]
            if self.status not in valid_statuses:
                raise ValidationError(f"Invalid status: {self.status}")
            
            logger.info(f"Allocation {self.code} validation passed")
            return True
            
        except Exception as e:
            logger.error(f"Allocation validation error: {str(e)}")
            raise ValidationError(f"Allocation validation error: {str(e)}")
    
    def check_conflict(self, other_allocation) -> bool:
        """
        Check for conflict with another allocation.
        
        Args:
            other_allocation: Other allocation to check conflict with
            
        Returns:
            True if conflict detected
        """
        # Check if same resource
        if self.resource_id != other_allocation.resource_id:
            return False
        
        # Check time overlap
        self_start = datetime.combine(self.start_date, self.start_time)
        self_end = datetime.combine(self.start_date, self.end_time)
        other_start = datetime.combine(other_allocation.start_date, other_allocation.start_time)
        other_end = datetime.combine(other_allocation.start_date, other_allocation.end_time)
        
        # Check if time ranges overlap
        if self_start < other_end and other_start < self_end:
            # Check day overlap
            if self.days_of_week and other_allocation.days_of_week:
                common_days = set(self.days_of_week) & set(other_allocation.days_of_week)
                if common_days:
                    return True
            elif not self.days_of_week and not other_allocation.days_of_week:
                # No specific days specified - assume conflict
                return True
            elif self.days_of_week or other_allocation.days_of_week:
                # One has specific days, other doesn't - check if any days overlap
                if self.days_of_week and other_allocation.days_of_week:
                    common_days = set(self.days_of_week) & set(other_allocation.days_of_week)
                    if common_days:
                        return True
        
        return False
    
    def mark_conflict(self, conflict_details: str, alternative_resource_id: str = None) -> None:
        """
        Mark allocation as having a conflict.
        
        Args:
            conflict_details: Details of the conflict
            alternative_resource_id: Alternative resource ID
        """
        self.is_conflict = True
        self.conflict_resolution = conflict_details
        self.alternative_resource_id = alternative_resource_id
        self.status = 'pending'
        self.updated_at = datetime.now()
        logger.info(f"Marked allocation {self.code} as conflicted: {conflict_details}")
    
    def resolve_conflict(self, resolution: str) -> None:
        """
        Resolve the conflict.
        
        Args:
            resolution: Resolution details
        """
        self.is_conflict = False
        self.conflict_resolution = resolution
        self.status = 'active'
        self.updated_at = datetime.now()
        logger.info(f"Resolved conflict for allocation {self.code}: {resolution}")
    
    def cancel_allocation(self, reason: str = "") -> None:
        """
        Cancel the allocation.
        
        Args:
            reason: Reason for cancellation
        """
        self.status = 'cancelled'
        if reason:
            self.metadata['cancellation_reason'] = reason
        self.updated_at = datetime.now()
        logger.info(f"Cancelled allocation {self.code} with reason: {reason}")
    
    def complete_allocation(self) -> None:
        """
        Mark allocation as completed.
        """
        self.status = 'completed'
        self.updated_at = datetime.now()
        logger.info(f"Completed allocation {self.code}")
    
    def activate_allocation(self) -> None:
        """
        Activate the allocation.
        """
        self.status = 'active'
        self.updated_at = datetime.now()
        logger.info(f"Activated allocation {self.code}")
    
    def start_usage(self, actual_start_time: datetime = None) -> None:
        """
        Start tracking resource usage.
        
        Args:
            actual_start_time: Actual start time (optional)
        """
        if not actual_start_time:
            actual_start_time = datetime.now()
        
        self.actual_start_time = actual_start_time
        self.is_used = True
        self.updated_at = datetime.now()
        logger.info(f"Started usage tracking for allocation {self.code}")
    
    def end_usage(self, actual_end_time: datetime = None) -> None:
        """
        End tracking resource usage.
        
        Args:
            actual_end_time: Actual end time (optional)
        """
        if not actual_end_time:
            actual_end_time = datetime.now()
        
        if self.actual_start_time:
            duration = actual_end_time - self.actual_start_time
            self.actual_usage_minutes = int(duration.total_seconds() / 60)
            self.actual_end_time = actual_end_time
            self.updated_at = datetime.now()
            logger.info(f"Ended usage tracking for allocation {self.code}: {self.actual_usage_minutes} minutes")
        else:
            raise ValidationError("Cannot end usage without starting usage first")
    
    def get_usage_info(self) -> Dict[str, Any]:
        """
        Get usage information.
        
        Returns:
            Usage information dictionary
        """
        return {
            'is_used': self.is_used,
            'actual_start_time': self.actual_start_time.isoformat() if self.actual_start_time else None,
            'actual_end_time': self.actual_end_time.isoformat() if self.actual_end_time else None,
            'actual_usage_minutes': self.actual_usage_minutes,
            'estimated_duration_minutes': self.get_duration_minutes(),
            'usage_efficiency': (self.actual_usage_minutes / self.get_duration_minutes() * 100) if self.get_duration_minutes() > 0 else 0
        }
    
    def get_duration_minutes(self) -> int:
        """
        Get allocation duration in minutes.
        
        Returns:
            Duration in minutes
        """
        if self.start_date and self.end_date and self.start_time and self.end_time:
            start_datetime = datetime.combine(self.start_date, self.start_time)
            end_datetime = datetime.combine(self.start_date, self.end_time)
            duration = end_datetime - start_datetime
            return int(duration.total_seconds() / 60)
        return 0
    
    def get_schedule_info(self) -> Dict[str, Any]:
        """
        Get schedule information.
        
        Returns:
            Schedule information dictionary
        """
        return {
            'start_date': self.start_date.isoformat(),
            'end_date': self.end_date.isoformat(),
            'start_time': self.start_time.strftime('%H:%M:%S'),
            'end_time': self.end_time.strftime('%H:%M:%S'),
            'days_of_week': self.days_of_week,
            'is_recurring': self.is_recurring,
            'total_days': len(self.days_of_week) if self.days_of_week else 0,
            'duration_minutes': self.get_duration_minutes()
        }
    
    def get_resource_info(self) -> Dict[str, Any]:
        """
        Get resource information.
        
        Returns:
            Resource information dictionary
        """
        return {
            'resource_id': self.resource_id,
            'resource_name': self.resource_name,
            'resource_type': self.resource_type,
            'type': self.type
        }
    
    def is_active_allocation(self) -> bool:
        """
        Check if allocation is active.
        
        Returns:
            True if active
        """
        return self.status == 'active'
    
    def is_conflicted(self) -> bool:
        """
        Check if allocation has conflicts.
        
        Returns:
            True if conflicted
        """
        return self.is_conflict
    
    def is_recurring_allocation(self) -> bool:
        """
        Check if allocation is recurring.
        
        Returns:
            True if recurring
        """
        return self.is_recurring
    
    def is_used_resource(self) -> bool:
        """
        Check if resource is being used.
        
        Returns:
            True if being used
        """
        return self.is_used
    
    def __repr__(self) -> str:
        """String representation of the allocation model."""
        return f"<AllocationModel(code='{self.code}', name='{self.name}', type='{self.type}', status='{self.status}')>"