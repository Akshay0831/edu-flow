"""
Room Model for Database Operations

This module provides the SQLAlchemy model for Room entity.
It includes all fields and relationships for room management.

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


class RoomModel(BaseModel):
    """
    SQLAlchemy model for Room entity.
    
    Represents physical room spaces for various academic and administrative activities.
    """
    __tablename__ = "rooms"
    
    # Room identification
    id = Column(String(50), primary_key=True)
    code = Column(String(50), nullable=False, unique=True, index=True)
    name = Column(String(100), nullable=False)
    abbreviation = Column(String(10), unique=True)
    
    # Room categorization
    type = Column(String(50), nullable=False)  # classroom, lecture_hall, seminar_room, office, lab, library, cafeteria
    department_id = Column(String(50), ForeignKey("departments.id"), nullable=False)
    
    # Location details
    building = Column(String(100), nullable=False)
    floor = Column(Integer, nullable=False)
    wing = Column(String(20))  # North, South, East, West, etc.
    room_number = Column(String(20), nullable=False)
    floor_plan_url = Column(String(255))  # URL to floor plan
    
    # Capacity and layout
    total_capacity = Column(Integer, nullable=False)  # Maximum occupancy
    available_capacity = Column(Integer, default=0)  # Current available capacity
    seating_arrangement = Column(String(50))  # lecture_hall, classroom, seminar, theater
    seating_layout = Column(JSON, default=dict)  # Detailed seating layout
    has_projector = Column(Boolean, default=False)
    has_whiteboard = Column(Boolean, default=True)
    has_blackboard = Column(Boolean, default=False)
    has_air_conditioning = Column(Boolean, default=True)
    has_heating = Column(Boolean, default=True)
    
    # Audio-visual equipment
    av_equipment = Column(JSON, default=list)  # List of AV equipment
    internet_connectivity = Column(JSON, default=dict)  # Internet connectivity details
    power_outlets = Column(JSON, default=list)  # Power outlet locations and types
    
    # Room features and facilities
    accessibility_features = Column(JSON, default=list)  # Accessibility features
    emergency_features = Column(JSON, default=list)  # Emergency equipment
    special_features = Column(JSON, default=list)  # Special features
    storage_space = Column(JSON, default=dict)  # Storage space details
    
    # Room status
    is_active = Column(Boolean, default=True)
    is_available = Column(Boolean, default=True)
    maintenance_status = Column(String(20), default="good")  # good, needs_maintenance, under_maintenance, unavailable
    last_maintenance_date = Column(DateTime)
    next_maintenance_date = Column(DateTime)
    
    # Booking and usage
    booking_policy = Column(Text)  # Booking policies and procedures
    booking_advance_days = Column(Integer, default=7)  # Days in advance to book
    max_booking_duration_hours = Column(Integer, default=4)  # Maximum booking duration
    auto_approve = Column(Boolean, default=False)  # Auto-approve bookings
    require_approval = Column(Boolean, default=True)  # Require approval for bookings
    
    # Room usage statistics
    total_usage_hours = Column(Integer, default=0)  # Total usage hours
    monthly_usage_hours = Column(Integer, default=0)  # Current month usage
    yearly_usage_hours = Column(Integer, default=0)  # Current year usage
    utilization_rate = Column(Integer, default=0)  # Percentage utilization
    
    # Room metadata
    metadata = Column(JSON, default=dict)
    tags = Column(JSON, default=list)  # List of tags
    attachments = Column(JSON, default=list)  # List of attachment paths/URLs
    notes = Column(Text)  # Additional notes
    
    # Relationships
    department = relationship("DepartmentModel")
    timetable_entries = relationship("TimetableEntryModel")
    bookings = relationship("BookingModel")
    equipment_maintenance = relationship("EquipmentMaintenanceModel")
    room_reports = relationship("RoomReportModel")
    
    def __init__(self, **kwargs):
        """Initialize the room model with provided data."""
        # Set default values for optional fields
        kwargs.setdefault('abbreviation', kwargs.get('name', '')[:3].upper())
        kwargs.setdefault('total_capacity', 30)
        kwargs.setdefault('available_capacity', kwargs.get('total_capacity', 30))
        kwargs.setdefault('is_active', True)
        kwargs.setdefault('is_available', True)
        kwargs.setdefault('maintenance_status', 'good')
        kwargs.setdefault('has_projector', False)
        kwargs.setdefault('has_whiteboard', True)
        kwargs.setdefault('has_blackboard', False)
        kwargs.setdefault('has_air_conditioning', True)
        kwargs.setdefault('has_heating', True)
        kwargs.setdefault('booking_advance_days', 7)
        kwargs.setdefault('max_booking_duration_hours', 4)
        kwargs.setdefault('auto_approve', False)
        kwargs.setdefault('require_approval', True)
        kwargs.setdefault('total_usage_hours', 0)
        kwargs.setdefault('monthly_usage_hours', 0)
        kwargs.setdefault('yearly_usage_hours', 0)
        kwargs.setdefault('utilization_rate', 0)
        kwargs.setdefault('seating_layout', {})
        kwargs.setdefault('av_equipment', [])
        kwargs.setdefault('internet_connectivity', {})
        kwargs.setdefault('power_outlets', [])
        kwargs.setdefault('accessibility_features', [])
        kwargs.setdefault('emergency_features', [])
        kwargs.setdefault('special_features', [])
        kwargs.setdefault('storage_space', {})
        kwargs.setdefault('metadata', {})
        kwargs.setdefault('tags', [])
        kwargs.setdefault('attachments', [])
        
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
        
        # Convert date fields to ISO format
        if 'last_maintenance_date' in data and isinstance(data['last_maintenance_date'], datetime):
            data['last_maintenance_date'] = data['last_maintenance_date'].isoformat()
        else:
            data['last_maintenance_date'] = None
        
        if 'next_maintenance_date' in data and isinstance(data['next_maintenance_date'], datetime):
            data['next_maintenance_date'] = data['next_maintenance_date'].isoformat()
        else:
            data['next_maintenance_date'] = None
        
        # Convert JSON fields to proper format
        if 'seating_layout' in data and isinstance(data['seating_layout'], dict):
            data['seating_layout'] = data['seating_layout']
        else:
            data['seating_layout'] = {}
        
        if 'av_equipment' in data and isinstance(data['av_equipment'], list):
            data['av_equipment'] = data['av_equipment']
        else:
            data['av_equipment'] = []
        
        if 'internet_connectivity' in data and isinstance(data['internet_connectivity'], dict):
            data['internet_connectivity'] = data['internet_connectivity']
        else:
            data['internet_connectivity'] = {}
        
        if 'power_outlets' in data and isinstance(data['power_outlets'], list):
            data['power_outlets'] = data['power_outlets']
        else:
            data['power_outlets'] = []
        
        if 'accessibility_features' in data and isinstance(data['accessibility_features'], list):
            data['accessibility_features'] = data['accessibility_features']
        else:
            data['accessibility_features'] = []
        
        if 'emergency_features' in data and isinstance(data['emergency_features'], list):
            data['emergency_features'] = data['emergency_features']
        else:
            data['emergency_features'] = []
        
        if 'special_features' in data and isinstance(data['special_features'], list):
            data['special_features'] = data['special_features']
        else:
            data['special_features'] = []
        
        if 'storage_space' in data and isinstance(data['storage_space'], dict):
            data['storage_space'] = data['storage_space']
        else:
            data['storage_space'] = {}
        
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
        
        # Calculate derived fields
        data['capacity_utilization'] = self.get_capacity_utilization()
        data['is_bookable'] = self.is_bookable()
        data['maintenance_overdue'] = self.maintenance_overdue()
        data['next_maintenance_days'] = self.get_next_maintenance_days()
        data['room_status'] = self.get_room_status()
        data['room_summary'] = self.get_room_summary()
        data['av_equipment_count'] = len(self.av_equipment)
        data['accessibility_features_count'] = len(self.accessibility_features)
        data['emergency_features_count'] = len(self.emergency_features)
        data['special_features_count'] = len(self.special_features)
        data['booking_statistics'] = self.get_booking_statistics()
        
        # Include relationships if requested
        if include_relationships:
            if hasattr(self, 'department') and self.department:
                data['department'] = self.department.to_dict()
            else:
                data['department'] = None
            
            if hasattr(self, 'timetable_entries') and self.timetable_entries:
                data['timetable_entries'] = [entry.to_dict() for entry in self.timetable_entries]
            else:
                data['timetable_entries'] = []
            
            if hasattr(self, 'bookings') and self.bookings:
                data['bookings'] = [booking.to_dict() for booking in self.bookings]
            else:
                data['bookings'] = []
            
            if hasattr(self, 'equipment_maintenance') and self.equipment_maintenance:
                data['equipment_maintenance'] = [maintenance.to_dict() for maintenance in self.equipment_maintenance]
            else:
                data['equipment_maintenance'] = []
            
            if hasattr(self, 'room_reports') and self.room_reports:
                data['room_reports'] = [report.to_dict() for report in self.room_reports]
            else:
                data['room_reports'] = []
        
        return data
    
    def update(self, **kwargs) -> None:
        """Update the model with new data."""
        # Handle special field updates
        if 'seating_layout' in kwargs and isinstance(kwargs['seating_layout'], dict):
            self.seating_layout = kwargs['seating_layout']
        if 'av_equipment' in kwargs and isinstance(kwargs['av_equipment'], list):
            self.av_equipment = kwargs['av_equipment']
        if 'internet_connectivity' in kwargs and isinstance(kwargs['internet_connectivity'], dict):
            self.internet_connectivity = kwargs['internet_connectivity']
        if 'power_outlets' in kwargs and isinstance(kwargs['power_outlets'], list):
            self.power_outlets = kwargs['power_outlets']
        if 'accessibility_features' in kwargs and isinstance(kwargs['accessibility_features'], list):
            self.accessibility_features = kwargs['accessibility_features']
        if 'emergency_features' in kwargs and isinstance(kwargs['emergency_features'], list):
            self.emergency_features = kwargs['emergency_features']
        if 'special_features' in kwargs and isinstance(kwargs['special_features'], list):
            self.special_features = kwargs['special_features']
        if 'storage_space' in kwargs and isinstance(kwargs['storage_space'], dict):
            self.storage_space = kwargs['storage_space']
        if 'metadata' in kwargs and isinstance(kwargs['metadata'], dict):
            self.metadata = kwargs['metadata']
        if 'tags' in kwargs and isinstance(kwargs['tags'], list):
            self.tags = kwargs['tags']
        if 'attachments' in kwargs and isinstance(kwargs['attachments'], list):
            self.attachments = kwargs['attachments']
        
        super().update(**kwargs)
    
    def validate(self) -> bool:
        """
        Validate the room model data.
        
        Returns:
            True if valid, False otherwise
            
        Raises:
            ValidationError: If validation fails
        """
        try:
            # Call base validation
            super().validate()
            
            # Room-specific validations
            if not self.id:
                raise ValidationError("Room ID is required")
            
            if not self.code:
                raise ValidationError("Room code is required")
            
            if not self.name:
                raise ValidationError("Room name is required")
            
            if not self.type:
                raise ValidationError("Room type is required")
            
            if not self.department_id:
                raise ValidationError("Department ID is required")
            
            if not self.building:
                raise ValidationError("Building is required")
            
            if self.floor is not None and self.floor < 0:
                raise ValidationError("Floor must be non-negative")
            
            if not self.room_number:
                raise ValidationError("Room number is required")
            
            if not self.total_capacity or self.total_capacity <= 0:
                raise ValidationError("Total capacity must be positive")
            
            if self.available_capacity < 0:
                raise ValidationError("Available capacity cannot be negative")
            
            if self.available_capacity > self.total_capacity:
                raise ValidationError("Available capacity cannot exceed total capacity")
            
            # Type validation
            valid_types = ['classroom', 'lecture_hall', 'seminar_room', 'office', 
                         'lab', 'library', 'cafeteria', 'conference_room', 'meeting_room']
            if self.type not in valid_types:
                raise ValidationError(f"Invalid room type: {self.type}")
            
            # Seating arrangement validation
            valid_arrangements = ['lecture_hall', 'classroom', 'seminar', 'theater', 'circular', 'u_shape', 'boardroom']
            if self.seating_arrangement and self.seating_arrangement not in valid_arrangements:
                raise ValidationError(f"Invalid seating arrangement: {self.seating_arrangement}")
            
            # Maintenance status validation
            valid_statuses = ['good', 'needs_maintenance', 'under_maintenance', 'unavailable']
            if self.maintenance_status not in valid_statuses:
                raise ValidationError(f"Invalid maintenance status: {self.maintenance_status}")
            
            # Booking policy validation
            if self.booking_advance_days < 0:
                raise ValidationError("Booking advance days cannot be negative")
            
            if self.max_booking_duration_hours <= 0:
                raise ValidationError("Max booking duration must be positive")
            
            # Usage metrics validation
            if self.total_usage_hours < 0:
                raise ValidationError("Total usage hours cannot be negative")
            
            if self.monthly_usage_hours < 0:
                raise ValidationError("Monthly usage hours cannot be negative")
            
            if self.yearly_usage_hours < 0:
                raise ValidationError("Yearly usage hours cannot be negative")
            
            if self.utilization_rate < 0 or self.utilization_rate > 100:
                raise ValidationError("Utilization rate must be between 0 and 100")
            
            # Date validations
            if self.last_maintenance_date and self.last_maintenance_date > datetime.now():
                raise ValidationError("Last maintenance date cannot be in the future")
            
            if self.next_maintenance_date and self.next_maintenance_date < datetime.now():
                raise ValidationError("Next maintenance date cannot be in the past")
            
            # JSON fields validation
            if not isinstance(self.seating_layout, dict):
                raise ValidationError("Seating layout must be a dictionary")
            
            if not isinstance(self.av_equipment, list):
                raise ValidationError("AV equipment must be a list")
            
            if not isinstance(self.internet_connectivity, dict):
                raise ValidationError("Internet connectivity must be a dictionary")
            
            if not isinstance(self.power_outlets, list):
                raise ValidationError("Power outlets must be a list")
            
            if not isinstance(self.accessibility_features, list):
                raise ValidationError("Accessibility features must be a list")
            
            if not isinstance(self.emergency_features, list):
                raise ValidationError("Emergency features must be a list")
            
            if not isinstance(self.special_features, list):
                raise ValidationError("Special features must be a list")
            
            if not isinstance(self.storage_space, dict):
                raise ValidationError("Storage space must be a dictionary")
            
            if not isinstance(self.metadata, dict):
                raise ValidationError("Metadata must be a dictionary")
            
            if not isinstance(self.tags, list):
                raise ValidationError("Tags must be a list")
            
            if not isinstance(self.attachments, list):
                raise ValidationError("Attachments must be a list")
            
            logger.info(f"Room {self.code} validation passed")
            return True
            
        except Exception as e:
            logger.error(f"Room validation error: {str(e)}")
            raise ValidationError(f"Room validation error: {str(e)}")
    
    def add_av_equipment(self, equipment_name: str, equipment_type: str, model: str = "", 
                        manufacturer: str = "", serial_number: str = "", status: str = "available") -> None:
        """
        Add AV equipment to the room.
        
        Args:
            equipment_name: Name of equipment
            equipment_type: Type of equipment
            model: Equipment model (optional)
            manufacturer: Manufacturer name (optional)
            serial_number: Serial number (optional)
            status: Equipment status (default: available)
        """
        equipment = {
            'equipment_name': equipment_name,
            'equipment_type': equipment_type,
            'model': model,
            'manufacturer': manufacturer,
            'serial_number': serial_number,
            'status': status,
            'added_date': datetime.now().isoformat()
        }
        
        self.av_equipment.append(equipment)
        self.updated_at = datetime.now()
        logger.info(f"Added AV equipment {equipment_name} to room {self.code}")
    
    def remove_av_equipment(self, equipment_name: str, equipment_type: str, serial_number: str = "") -> None:
        """
        Remove AV equipment from the room.
        
        Args:
            equipment_name: Name of equipment to remove
            equipment_type: Type of equipment
            serial_number: Serial number to match (optional)
        """
        self.av_equipment = [eq for eq in self.av_equipment 
                           if not (eq['equipment_name'] == equipment_name and 
                                 eq['equipment_type'] == equipment_type and 
                                 (not serial_number or eq['serial_number'] == serial_number))]
        self.updated_at = datetime.now()
        logger.info(f"Removed AV equipment {equipment_name} from room {self.code}")
    
    def add_power_outlet(self, outlet_id: str, outlet_type: str, location: str, 
                       voltage: str = "", amperage: str = "") -> None:
        """
        Add power outlet information.
        
        Args:
            outlet_id: Outlet ID
            outlet_type: Type of outlet
            location: Location of outlet
            voltage: Voltage rating (optional)
            amperage: Amperage rating (optional)
        """
        outlet = {
            'outlet_id': outlet_id,
            'outlet_type': outlet_type,
            'location': location,
            'voltage': voltage,
            'amperage': amperage
        }
        
        self.power_outlets.append(outlet)
        self.updated_at = datetime.now()
        logger.info(f"Added power outlet {outlet_id} to room {self.code}")
    
    def remove_power_outlet(self, outlet_id: str) -> None:
        """
        Remove power outlet information.
        
        Args:
            outlet_id: Outlet ID to remove
        """
        self.power_outlets = [outlet for outlet in self.power_outlets 
                             if outlet['outlet_id'] != outlet_id]
        self.updated_at = datetime.now()
        logger.info(f"Removed power outlet {outlet_id} from room {self.code}")
    
    def update_internet_connectivity(self, connection_type: str, bandwidth: str, 
                                    has_wifi: bool, wifi_networks: List[str] = None) -> None:
        """
        Update internet connectivity information.
        
        Args:
            connection_type: Type of connection
            bandwidth: Bandwidth information
            has_wifi: WiFi availability
            wifi_networks: List of WiFi networks (optional)
        """
        self.internet_connectivity = {
            'connection_type': connection_type,
            'bandwidth': bandwidth,
            'has_wifi': has_wifi,
            'wifi_networks': wifi_networks or [],
            'last_updated': datetime.now().isoformat()
        }
        self.updated_at = datetime.now()
        logger.info(f"Updated internet connectivity for room {self.code}")
    
    def add_accessibility_feature(self, feature_name: str, feature_description: str) -> None:
        """
        Add accessibility feature.
        
        Args:
            feature_name: Feature name
            feature_description: Feature description
        """
        feature = {
            'feature_name': feature_name,
            'feature_description': feature_description,
            'added_date': datetime.now().isoformat()
        }
        
        # Check if feature already exists
        existing_features = [f for f in self.accessibility_features if f['feature_name'] == feature_name]
        if not existing_features:
            self.accessibility_features.append(feature)
            self.updated_at = datetime.now()
            logger.info(f"Added accessibility feature {feature_name} to room {self.code}")
        else:
            logger.warning(f"Accessibility feature {feature_name} already exists in room {self.code}")
    
    def remove_accessibility_feature(self, feature_name: str) -> None:
        """
        Remove accessibility feature.
        
        Args:
            feature_name: Feature name to remove
        """
        self.accessibility_features = [f for f in self.accessibility_features 
                                      if f['feature_name'] != feature_name]
        self.updated_at = datetime.now()
        logger.info(f"Removed accessibility feature {feature_name} from room {self.code}")
    
    def add_emergency_feature(self, feature_name: str, feature_description: str) -> None:
        """
        Add emergency feature.
        
        Args:
            feature_name: Feature name
            feature_description: Feature description
        """
        feature = {
            'feature_name': feature_name,
            'feature_description': feature_description,
            'added_date': datetime.now().isoformat()
        }
        
        # Check if feature already exists
        existing_features = [f for f in self.emergency_features if f['feature_name'] == feature_name]
        if not existing_features:
            self.emergency_features.append(feature)
            self.updated_at = datetime.now()
            logger.info(f"Added emergency feature {feature_name} to room {self.code}")
        else:
            logger.warning(f"Emergency feature {feature_name} already exists in room {self.code}")
    
    def remove_emergency_feature(self, feature_name: str) -> None:
        """
        Remove emergency feature.
        
        Args:
            feature_name: Feature name to remove
        """
        self.emergency_features = [f for f in self.emergency_features 
                                  if f['feature_name'] != feature_name]
        self.updated_at = datetime.now()
        logger.info(f"Removed emergency feature {feature_name} from room {self.code}")
    
    def add_special_feature(self, feature_name: str, feature_description: str) -> None:
        """
        Add special feature.
        
        Args:
            feature_name: Feature name
            feature_description: Feature description
        """
        feature = {
            'feature_name': feature_name,
            'feature_description': feature_description,
            'added_date': datetime.now().isoformat()
        }
        
        # Check if feature already exists
        existing_features = [f for f in self.special_features if f['feature_name'] == feature_name]
        if not existing_features:
            self.special_features.append(feature)
            self.updated_at = datetime.now()
            logger.info(f"Added special feature {feature_name} to room {self.code}")
        else:
            logger.warning(f"Special feature {feature_name} already exists in room {self.code}")
    
    def remove_special_feature(self, feature_name: str) -> None:
        """
        Remove special feature.
        
        Args:
            feature_name: Feature name to remove
        """
        self.special_features = [f for f in self.special_features 
                                if f['feature_name'] != feature_name]
        self.updated_at = datetime.now()
        logger.info(f"Removed special feature {feature_name} from room {self.code}")
    
    def update_storage_space(self, storage_type: str, capacity_cubic_meters: int, 
                            items_stored: List[str] = None) -> None:
        """
        Update storage space information.
        
        Args:
            storage_type: Type of storage
            capacity_cubic_meters: Storage capacity in cubic meters
            items_stored: List of items stored (optional)
        """
        self.storage_space = {
            'storage_type': storage_type,
            'capacity_cubic_meters': capacity_cubic_meters,
            'items_stored': items_stored or [],
            'last_updated': datetime.now().isoformat()
        }
        self.updated_at = datetime.now()
        logger.info(f"Updated storage space for room {self.code}")
    
    def update_maintenance_status(self, status: str, notes: str = "") -> None:
        """
        Update maintenance status.
        
        Args:
            status: Maintenance status
            notes: Additional notes (optional)
        """
        valid_statuses = ['good', 'needs_maintenance', 'under_maintenance', 'unavailable']
        if status not in valid_statuses:
            raise ValidationError(f"Invalid maintenance status: {status}")
        
        self.maintenance_status = status
        
        if status in ['good', 'needs_maintenance']:
            self.last_maintenance_date = datetime.now()
        
        if notes:
            self.metadata['maintenance_notes'] = notes
        
        self.updated_at = datetime.now()
        logger.info(f"Updated maintenance status for room {self.code} to {status}")
    
    def update_maintenance_schedule(self, last_maintenance_date: datetime = None, 
                                 next_maintenance_date: datetime = None) -> None:
        """
        Update maintenance schedule.
        
        Args:
            last_maintenance_date: Last maintenance date (optional)
            next_maintenance_date: Next maintenance date (optional)
        """
        if last_maintenance_date:
            self.last_maintenance_date = last_maintenance_date
        
        if next_maintenance_date:
            self.next_maintenance_date = next_maintenance_date
        
        self.updated_at = datetime.now()
        logger.info(f"Updated maintenance schedule for room {self.code}")
    
    def update_booking_policy(self, policy_text: str, advance_days: int = None, 
                             max_duration_hours: int = None, auto_approve: bool = None,
                             require_approval: bool = None) -> None:
        """
        Update booking policy.
        
        Args:
            policy_text: Booking policy text
            advance_days: Days in advance to book (optional)
            max_duration_hours: Maximum booking duration (optional)
            auto_approve: Auto-approve bookings (optional)
            require_approval: Require approval for bookings (optional)
        """
        self.booking_policy = policy_text
        
        if advance_days is not None:
            self.booking_advance_days = advance_days
        
        if max_duration_hours is not None:
            self.max_booking_duration_hours = max_duration_hours
        
        if auto_approve is not None:
            self.auto_approve = auto_approve
        
        if require_approval is not None:
            self.require_approval = require_approval
        
        self.updated_at = datetime.now()
        logger.info(f"Updated booking policy for room {self.code}")
    
    def update_usage_metrics(self, additional_hours: int, is_monthly: bool = False, 
                           is_yearly: bool = False) -> None:
        """
        Update usage metrics.
        
        Args:
            additional_hours: Additional usage hours
            is_monthly: If monthly usage update (default: False)
            is_yearly: If yearly usage update (default: False)
        """
        if additional_hours < 0:
            raise ValidationError("Additional hours cannot be negative")
        
        self.total_usage_hours += additional_hours
        
        if is_monthly:
            self.monthly_usage_hours += additional_hours
        
        if is_yearly:
            self.yearly_usage_hours += additional_hours
        
        # Calculate utilization rate (monthly)
        total_possible_hours = 720  # 30 days * 24 hours
        if self.total_capacity > 0:
            self.utilization_rate = min(100, (self.monthly_usage_hours / total_possible_hours) * 100)
        
        self.updated_at = datetime.now()
        logger.info(f"Updated usage metrics for room {self.code}")
    
    def get_capacity_utilization(self) -> float:
        """
        Get capacity utilization percentage.
        
        Returns:
            Capacity utilization percentage (0-100)
        """
        if self.total_capacity > 0:
            return (1 - (self.available_capacity / self.total_capacity)) * 100
        return 0.0
    
    def is_bookable(self) -> bool:
        """
        Check if room is bookable.
        
        Returns:
            True if room is bookable
        """
        return (self.is_active and self.is_available and 
                self.maintenance_status == 'good')
    
    def maintenance_overdue(self) -> bool:
        """
        Check if maintenance is overdue.
        
        Returns:
            True if maintenance is overdue
        """
        if not self.next_maintenance_date:
            return False
        
        return datetime.now() > self.next_maintenance_date
    
    def get_next_maintenance_days(self) -> Optional[int]:
        """
        Get days until next maintenance.
        
        Returns:
            Days until next maintenance, or None if no schedule
        """
        if not self.next_maintenance_date:
            return None
        
        delta = self.next_maintenance_date - datetime.now()
        return max(0, delta.days)
    
    def get_room_status(self) -> str:
        """
        Get room status.
        
        Returns:
            Room status string
        """
        if not self.is_active:
            return 'inactive'
        elif self.maintenance_status == 'unavailable':
            return 'unavailable'
        elif self.maintenance_overdue():
            return 'maintenance_overdue'
        elif not self.is_available:
            return 'unavailable'
        elif self.maintenance_status == 'under_maintenance':
            return 'under_maintenance'
        elif self.maintenance_status == 'needs_maintenance':
            return 'needs_maintenance'
        else:
            return 'available'
    
    def get_room_summary(self) -> Dict[str, Any]:
        """
        Get room summary.
        
        Returns:
            Room summary dictionary
        """
        return {
            'id': self.id,
            'code': self.code,
            'name': self.name,
            'type': self.type,
            'status': self.get_room_status(),
            'department_id': self.department_id,
            'building': self.building,
            'floor': self.floor,
            'room_number': self.room_number,
            'total_capacity': self.total_capacity,
            'available_capacity': self.available_capacity,
            'capacity_utilization': self.get_capacity_utilization(),
            'is_active': self.is_active,
            'is_available': self.is_available,
            'maintenance_status': self.maintenance_status,
            'maintenance_overdue': self.maintenance_overdue(),
            'next_maintenance_days': self.get_next_maintenance_days(),
            'total_usage_hours': self.total_usage_hours,
            'monthly_usage_hours': self.monthly_usage_hours,
            'utilization_rate': self.utilization_rate,
            'has_projector': self.has_projector,
            'has_whiteboard': self.has_whiteboard,
            'has_blackboard': self.has_blackboard,
            'has_air_conditioning': self.has_air_conditioning,
            'has_heating': self.has_heating,
            'is_bookable': self.is_bookable(),
            'booking_advance_days': self.booking_advance_days,
            'max_booking_duration_hours': self.max_booking_duration_hours,
            'auto_approve': self.auto_approve,
            'require_approval': self.require_approval,
            'seating_arrangement': self.seating_arrangement,
            'av_equipment_count': len(self.av_equipment),
            'accessibility_features_count': len(self.accessibility_features),
            'emergency_features_count': len(self.emergency_features),
            'special_features_count': len(self.special_features)
        }
    
    def get_booking_statistics(self) -> Dict[str, Any]:
        """
        Get booking statistics.
        
        Returns:
            Booking statistics dictionary
        """
        return {
            'total_bookings': len(self.bookings) if hasattr(self, 'bookings') else 0,
            'active_bookings': len([b for b in self.bookings if hasattr(b, 'status') and b.status == 'active']) if hasattr(self, 'bookings') else 0,
            'total_usage_hours': self.total_usage_hours,
            'monthly_usage_hours': self.monthly_usage_hours,
            'yearly_usage_hours': self.yearly_usage_hours,
            'utilization_rate': self.utilization_rate,
            'average_booking_duration_hours': sum(b.duration_hours for b in self.bookings) / len(self.bookings) if hasattr(self, 'bookings') and self.bookings else 0,
            'most_booked_day': self.get_most_booked_day() if hasattr(self, 'bookings') and self.bookings else None,
            'most_booked_hour': self.get_most_booked_hour() if hasattr(self, 'bookings') and self.bookings else None
        }
    
    def get_most_booked_day(self) -> Optional[str]:
        """
        Get most booked day of week.
        
        Returns:
            Most booked day of week, or None if no bookings
        """
        if not hasattr(self, 'bookings') or not self.bookings:
            return None
        
        day_counts = {}
        for booking in self.bookings:
            if hasattr(booking, 'date') and booking.date:
                day = booking.date.strftime('%A')
                day_counts[day] = day_counts.get(day, 0) + 1
        
        return max(day_counts.items(), key=lambda x: x[1])[0] if day_counts else None
    
    def get_most_booked_hour(self) -> Optional[int]:
        """
        Get most booked hour of day.
        
        Returns:
            Most booked hour (0-23), or None if no bookings
        """
        if not hasattr(self, 'bookings') or not self.bookings:
            return None
        
        hour_counts = {}
        for booking in self.bookings:
            if hasattr(booking, 'date') and booking.date and hasattr(booking, 'start_time'):
                start_hour = booking.date.hour if hasattr(booking.date, 'hour') else booking.start_time.hour
                hour_counts[start_hour] = hour_counts.get(start_hour, 0) + 1
        
        return max(hour_counts.items(), key=lambda x: x[1])[0] if hour_counts else None
    
    def __repr__(self) -> str:
        """String representation of the room model."""
        return f"<RoomModel(code='{self.code}', name='{self.name}', type='{self.type}', status='{self.get_room_status()}')>"