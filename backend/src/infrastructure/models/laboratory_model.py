"""
Laboratory Model for Database Operations

This module provides the SQLAlchemy model for Laboratory entity.
It includes all fields and relationships for laboratory management.

Author: Edu-Flow Team
"""

from typing import Dict, Any, Optional, List
from datetime import datetime, time
import logging

from sqlalchemy import Column, String, Integer, Text, DateTime, JSON, Boolean, ForeignKey
from sqlalchemy.orm import relationship

from src.infrastructure.models.base_model import BaseModel
from src.core.exceptions import ValidationError
from src.core.logging import get_logger

logger = get_logger(__name__)


class LaboratoryModel(BaseModel):
    """
    SQLAlchemy model for Laboratory entity.
    
    Represents physical laboratory facilities for practical sessions, experiments, and research.
    """
    __tablename__ = "laboratories"
    
    # Laboratory identification
    id = Column(String(50), primary_key=True)
    code = Column(String(50), nullable=False, unique=True, index=True)
    name = Column(String(100), nullable=False)
    abbreviation = Column(String(10), unique=True)
    
    # Laboratory categorization
    type = Column(String(50), nullable=False)  # computer_lab, physics_lab, chemistry_lab, biology_lab, engineering_lab, research_lab
    department_id = Column(String(50), ForeignKey("departments.id"), nullable=False)
    
    # Location and capacity
    building = Column(String(100), nullable=False)
    floor = Column(Integer, nullable=False)
    room_number = Column(String(20), nullable=False)
    total_capacity = Column(Integer, nullable=False)  # Maximum students/staff
    available_capacity = Column(Integer, default=0)  # Current available capacity
    
    # Laboratory equipment and resources
    equipment_list = Column(JSON, default=list)  # List of equipment
    software_list = Column(JSON, default=list)  # List of software
    consumables = Column(JSON, default=dict)  # Consumable materials
    safety_equipment = Column(JSON, default=list)  # Safety equipment
    network_connectivity = Column(JSON, default=dict)  # Network details
    
    # Laboratory details
    description = Column(Text)
    research_areas = Column(JSON, default=list)  # Research areas covered
    courses_supported = Column(JSON, default=list)  # Courses that use this lab
    special_features = Column(JSON, default=list)  # Special features
    
    # Laboratory status
    is_active = Column(Boolean, default=True)
    is_available = Column(Boolean, default=True)
    maintenance_status = Column(String(20), default="good")  # good, needs_maintenance, under_maintenance, unavailable
    last_maintenance_date = Column(DateTime)
    next_maintenance_date = Column(DateTime)
    
    # Access and booking
    booking_policy = Column(Text)  # Booking policies and procedures
    booking_advance_days = Column(Integer, default=7)  # Days in advance to book
    max_booking_duration_hours = Column(Integer, default=4)  # Maximum booking duration
    auto_approve = Column(Boolean, default=False)  # Auto-approve bookings
    require_supervision = Column(Boolean, default=True)  # Require supervision
    
    # Safety and compliance
    safety_certifications = Column(JSON, default=list)  # Safety certifications
    safety_compliance = Column(Boolean, default=True)
    emergency_contacts = Column(JSON, default=list)  # Emergency contact details
    risk_assessment = Column(Text)  # Risk assessment documentation
    
    # Laboratory usage
    total_usage_hours = Column(Integer, default=0)  # Total usage hours
    monthly_usage_hours = Column(Integer, default=0)  # Current month usage
    yearly_usage_hours = Column(Integer, default=0)  # Current year usage
    utilization_rate = Column(Integer, default=0)  # Percentage utilization
    
    # Laboratory metadata
    metadata = Column(JSON, default=dict)
    tags = Column(JSON, default=list)  # List of tags
    attachments = Column(JSON, default=list)  # List of attachment paths/URLs
    notes = Column(Text)  # Additional notes
    
    # Relationships
    department = relationship("DepartmentModel")
    timetable_entries = relationship("TimetableEntryModel")
    equipment_maintenance = relationship("EquipmentMaintenanceModel")
    laboratory_reports = relationship("LaboratoryReportModel")
    bookings = relationship("BookingModel")
    
    def __init__(self, **kwargs):
        """Initialize the laboratory model with provided data."""
        # Set default values for optional fields
        kwargs.setdefault('abbreviation', kwargs.get('name', '')[:3].upper())
        kwargs.setdefault('total_capacity', 30)
        kwargs.setdefault('available_capacity', kwargs.get('total_capacity', 30))
        kwargs.setdefault('is_active', True)
        kwargs.setdefault('is_available', True)
        kwargs.setdefault('maintenance_status', 'good')
        kwargs.setdefault('booking_advance_days', 7)
        kwargs.setdefault('max_booking_duration_hours', 4)
        kwargs.setdefault('auto_approve', False)
        kwargs.setdefault('require_supervision', True)
        kwargs.setdefault('safety_compliance', True)
        kwargs.setdefault('total_usage_hours', 0)
        kwargs.setdefault('monthly_usage_hours', 0)
        kwargs.setdefault('yearly_usage_hours', 0)
        kwargs.setdefault('utilization_rate', 0)
        kwargs.setdefault('equipment_list', [])
        kwargs.setdefault('software_list', [])
        kwargs.setdefault('consumables', {})
        kwargs.setdefault('safety_equipment', [])
        kwargs.setdefault('network_connectivity', {})
        kwargs.setdefault('research_areas', [])
        kwargs.setdefault('courses_supported', [])
        kwargs.setdefault('special_features', [])
        kwargs.setdefault('safety_certifications', [])
        kwargs.setdefault('emergency_contacts', [])
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
        if 'equipment_list' in data and isinstance(data['equipment_list'], list):
            data['equipment_list'] = data['equipment_list']
        else:
            data['equipment_list'] = []
        
        if 'software_list' in data and isinstance(data['software_list'], list):
            data['software_list'] = data['software_list']
        else:
            data['software_list'] = []
        
        if 'consumables' in data and isinstance(data['consumables'], dict):
            data['consumables'] = data['consumables']
        else:
            data['consumables'] = {}
        
        if 'safety_equipment' in data and isinstance(data['safety_equipment'], list):
            data['safety_equipment'] = data['safety_equipment']
        else:
            data['safety_equipment'] = []
        
        if 'network_connectivity' in data and isinstance(data['network_connectivity'], dict):
            data['network_connectivity'] = data['network_connectivity']
        else:
            data['network_connectivity'] = {}
        
        if 'research_areas' in data and isinstance(data['research_areas'], list):
            data['research_areas'] = data['research_areas']
        else:
            data['research_areas'] = []
        
        if 'courses_supported' in data and isinstance(data['courses_supported'], list):
            data['courses_supported'] = data['courses_supported']
        else:
            data['courses_supported'] = []
        
        if 'special_features' in data and isinstance(data['special_features'], list):
            data['special_features'] = data['special_features']
        else:
            data['special_features'] = []
        
        if 'safety_certifications' in data and isinstance(data['safety_certifications'], list):
            data['safety_certifications'] = data['safety_certifications']
        else:
            data['safety_certifications'] = []
        
        if 'emergency_contacts' in data and isinstance(data['emergency_contacts'], list):
            data['emergency_contacts'] = data['emergency_contacts']
        else:
            data['emergency_contacts'] = []
        
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
        data='capacity_utilization'] = self.get_capacity_utilization()
        data='is_bookable'] = self.is_bookable()
        data='maintenance_overdue'] = self.maintenance_overdue()
        data['next_maintenance_days'] = self.get_next_maintenance_days()
        data['laboratory_status'] = self.get_laboratory_status()
        data='laboratory_summary'] = self.get_laboratory_summary()
        data['equipment_count'] = len(self.equipment_list)
        data['software_count'] = len(self.software_list)
        data['safety_certifications_count'] = len(self.safety_certifications)
        data='booking_statistics'] = self.get_booking_statistics()
        
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
            
            if hasattr(self, 'equipment_maintenance') and self.equipment_maintenance:
                data['equipment_maintenance'] = [maintenance.to_dict() for maintenance in self.equipment_maintenance]
            else:
                data['equipment_maintenance'] = []
            
            if hasattr(self, 'laboratory_reports') and self.laboratory_reports:
                data['laboratory_reports'] = [report.to_dict() for report in self.laboratory_reports]
            else:
                data['laboratory_reports'] = []
            
            if hasattr(self, 'bookings') and self.bookings:
                data['bookings'] = [booking.to_dict() for booking in self.bookings]
            else:
                data['bookings'] = []
        
        return data
    
    def update(self, **kwargs) -> None:
        """Update the model with new data."""
        # Handle special field updates
        if 'equipment_list' in kwargs and isinstance(kwargs['equipment_list'], list):
            self.equipment_list = kwargs['equipment_list']
        if 'software_list' in kwargs and isinstance(kwargs['software_list'], list):
            self.software_list = kwargs['software_list']
        if 'consumables' in kwargs and isinstance(kwargs['consumables'], dict):
            self.consumables = kwargs['consumables']
        if 'safety_equipment' in kwargs and isinstance(kwargs['safety_equipment'], list):
            self.safety_equipment = kwargs['safety_equipment']
        if 'network_connectivity' in kwargs and isinstance(kwargs['network_connectivity'], dict):
            self.network_connectivity = kwargs['network_connectivity']
        if 'research_areas' in kwargs and isinstance(kwargs['research_areas'], list):
            self.research_areas = kwargs['research_areas']
        if 'courses_supported' in kwargs and isinstance(kwargs['courses_supported'], list):
            self.courses_supported = kwargs['courses_supported']
        if 'special_features' in kwargs and isinstance(kwargs['special_features'], list):
            self.special_features = kwargs['special_features']
        if 'safety_certifications' in kwargs and isinstance(kwargs['safety_certifications'], list):
            self.safety_certifications = kwargs['safety_certifications']
        if 'emergency_contacts' in kwargs and isinstance(kwargs['emergency_contacts'], list):
            self.emergency_contacts = kwargs['emergency_contacts']
        if 'metadata' in kwargs and isinstance(kwargs['metadata'], dict):
            self.metadata = kwargs['metadata']
        if 'tags' in kwargs and isinstance(kwargs['tags'], list):
            self.tags = kwargs['tags']
        if 'attachments' in kwargs and isinstance(kwargs['attachments'], list):
            self.attachments = kwargs['attachments']
        
        super().update(**kwargs)
    
    def validate(self) -> bool:
        """
        Validate the laboratory model data.
        
        Returns:
            True if valid, False otherwise
            
        Raises:
            ValidationError: If validation fails
        """
        try:
            # Call base validation
            super().validate()
            
            # Laboratory-specific validations
            if not self.id:
                raise ValidationError("Laboratory ID is required")
            
            if not self.code:
                raise ValidationError("Laboratory code is required")
            
            if not self.name:
                raise ValidationError("Laboratory name is required")
            
            if not self.type:
                raise ValidationError("Laboratory type is required")
            
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
            valid_types = ['computer_lab', 'physics_lab', 'chemistry_lab', 'biology_lab', 
                         'engineering_lab', 'research_lab', 'medical_lab', 'electronics_lab']
            if self.type not in valid_types:
                raise ValidationError(f"Invalid laboratory type: {self.type}")
            
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
            if not isinstance(self.equipment_list, list):
                raise ValidationError("Equipment list must be a list")
            
            if not isinstance(self.software_list, list):
                raise ValidationError("Software list must be a list")
            
            if not isinstance(self.consumables, dict):
                raise ValidationError("Consumables must be a dictionary")
            
            if not isinstance(self.safety_equipment, list):
                raise ValidationError("Safety equipment must be a list")
            
            if not isinstance(self.network_connectivity, dict):
                raise ValidationError("Network connectivity must be a dictionary")
            
            if not isinstance(self.research_areas, list):
                raise ValidationError("Research areas must be a list")
            
            if not isinstance(self.courses_supported, list):
                raise ValidationError("Courses supported must be a list")
            
            if not isinstance(self.special_features, list):
                raise ValidationError("Special features must be a list")
            
            if not isinstance(self.safety_certifications, list):
                raise ValidationError("Safety certifications must be a list")
            
            if not isinstance(self.emergency_contacts, list):
                raise ValidationError("Emergency contacts must be a list")
            
            if not isinstance(self.metadata, dict):
                raise ValidationError("Metadata must be a dictionary")
            
            if not isinstance(self.tags, list):
                raise ValidationError("Tags must be a list")
            
            if not isinstance(self.attachments, list):
                raise ValidationError("Attachments must be a list")
            
            logger.info(f"Laboratory {self.code} validation passed")
            return True
            
        except Exception as e:
            logger.error(f"Laboratory validation error: {str(e)}")
            raise ValidationError(f"Laboratory validation error: {str(e)}")
    
    def add_equipment(self, equipment_name: str, equipment_type: str, model: str = "", 
                      manufacturer: str = "", serial_number: str = "", status: str = "available") -> None:
        """
        Add equipment to the laboratory.
        
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
        
        self.equipment_list.append(equipment)
        self.updated_at = datetime.now()
        logger.info(f"Added equipment {equipment_name} to laboratory {self.code}")
    
    def remove_equipment(self, equipment_name: str, equipment_type: str, serial_number: str = "") -> None:
        """
        Remove equipment from the laboratory.
        
        Args:
            equipment_name: Name of equipment to remove
            equipment_type: Type of equipment
            serial_number: Serial number to match (optional)
        """
        self.equipment_list = [eq for eq in self.equipment_list 
                              if not (eq['equipment_name'] == equipment_name and 
                                     eq['equipment_type'] == equipment_type and 
                                     (not serial_number or eq['serial_number'] == serial_number))]
        self.updated_at = datetime.now()
        logger.info(f"Removed equipment {equipment_name} from laboratory {self.code}")
    
    def add_software(self, software_name: str, software_version: str, 
                     license_type: str = "", license_count: int = 1) -> None:
        """
        Add software to the laboratory.
        
        Args:
            software_name: Name of software
            software_version: Software version
            license_type: Type of license (optional)
            license_count: Number of licenses (default: 1)
        """
        software = {
            'software_name': software_name,
            'software_version': software_version,
            'license_type': license_type,
            'license_count': license_count,
            'added_date': datetime.now().isoformat()
        }
        
        self.software_list.append(software)
        self.updated_at = datetime.now()
        logger.info(f"Added software {software_name} to laboratory {self.code}")
    
    def remove_software(self, software_name: str, software_version: str) -> None:
        """
        Remove software from the laboratory.
        
        Args:
            software_name: Name of software to remove
            software_version: Software version
        """
        self.software_list = [sw for sw in self.software_list 
                             if not (sw['software_name'] == software_name and 
                                   sw['software_version'] == software_version)]
        self.updated_at = datetime.now()
        logger.info(f"Removed software {software_name} from laboratory {self.code}")
    
    def update_consumable(self, item_name: str, quantity: int, unit: str) -> None:
        """
        Update consumable quantity.
        
        Args:
            item_name: Name of consumable item
            quantity: Quantity
            unit: Unit of measurement
        """
        self.consumables[item_name] = {
            'quantity': quantity,
            'unit': unit,
            'last_updated': datetime.now().isoformat()
        }
        self.updated_at = datetime.now()
        logger.info(f"Updated consumable {item_name} in laboratory {self.code}")
    
    def add_safety_equipment(self, equipment_name: str, equipment_type: str, 
                             last_maintenance: datetime = None) -> None:
        """
        Add safety equipment.
        
        Args:
            equipment_name: Name of safety equipment
            equipment_type: Type of equipment
            last_maintenance: Last maintenance date (optional)
        """
        equipment = {
            'equipment_name': equipment_name,
            'equipment_type': equipment_type,
            'last_maintenance': last_maintenance.isoformat() if last_maintenance else None,
            'added_date': datetime.now().isoformat()
        }
        
        self.safety_equipment.append(equipment)
        self.updated_at = datetime.now()
        logger.info(f"Added safety equipment {equipment_name} to laboratory {self.code}")
    
    def remove_safety_equipment(self, equipment_name: str, equipment_type: str) -> None:
        """
        Remove safety equipment.
        
        Args:
            equipment_name: Name of safety equipment to remove
            equipment_type: Type of equipment
        """
        self.safety_equipment = [eq for eq in self.safety_equipment 
                               if not (eq['equipment_name'] == equipment_name and 
                                     eq['equipment_type'] == equipment_type)]
        self.updated_at = datetime.now()
        logger.info(f"Removed safety equipment {equipment_name} from laboratory {self.code}")
    
    def update_network_connectivity(self, network_type: str, bandwidth: str, 
                                    internet_available: bool, wifi_available: bool) -> None:
        """
        Update network connectivity information.
        
        Args:
            network_type: Type of network
            bandwidth: Bandwidth information
            internet_available: Internet availability
            wifi_available: WiFi availability
        """
        self.network_connectivity = {
            'network_type': network_type,
            'bandwidth': bandwidth,
            'internet_available': internet_available,
            'wifi_available': wifi_available,
            'last_updated': datetime.now().isoformat()
        }
        self.updated_at = datetime.now()
        logger.info(f"Updated network connectivity for laboratory {self.code}")
    
    def add_research_area(self, research_area: str) -> None:
        """
        Add research area.
        
        Args:
            research_area: Research area name
        """
        if research_area not in self.research_areas:
            self.research_areas.append(research_area)
            self.updated_at = datetime.now()
            logger.info(f"Added research area {research_area} to laboratory {self.code}")
        else:
            logger.warning(f"Research area {research_area} already exists in laboratory {self.code}")
    
    def remove_research_area(self, research_area: str) -> None:
        """
        Remove research area.
        
        Args:
            research_area: Research area to remove
        """
        if research_area in self.research_areas:
            self.research_areas.remove(research_area)
            self.updated_at = datetime.now()
            logger.info(f"Removed research area {research_area} from laboratory {self.code}")
        else:
            logger.warning(f"Research area {research_area} not found in laboratory {self.code}")
    
    def add_course_supported(self, course_code: str, course_name: str) -> None:
        """
        Add supported course.
        
        Args:
            course_code: Course code
            course_name: Course name
        """
        course = {
            'course_code': course_code,
            'course_name': course_name,
            'added_date': datetime.now().isoformat()
        }
        
        # Check if course already exists
        existing_courses = [c for c in self.courses_supported if c['course_code'] == course_code]
        if not existing_courses:
            self.courses_supported.append(course)
            self.updated_at = datetime.now()
            logger.info(f"Added supported course {course_code} to laboratory {self.code}")
        else:
            logger.warning(f"Course {course_code} already supported by laboratory {self.code}")
    
    def remove_course_supported(self, course_code: str) -> None:
        """
        Remove supported course.
        
        Args:
            course_code: Course code to remove
        """
        self.courses_supported = [c for c in self.courses_supported 
                                 if c['course_code'] != course_code]
        self.updated_at = datetime.now()
        logger.info(f"Removed supported course {course_code} from laboratory {self.code}")
    
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
            logger.info(f"Added special feature {feature_name} to laboratory {self.code}")
        else:
            logger.warning(f"Feature {feature_name} already exists in laboratory {self.code}")
    
    def remove_special_feature(self, feature_name: str) -> None:
        """
        Remove special feature.
        
        Args:
            feature_name: Feature name to remove
        """
        self.special_features = [f for f in self.special_features 
                                if f['feature_name'] != feature_name]
        self.updated_at = datetime.now()
        logger.info(f"Removed special feature {feature_name} from laboratory {self.code}")
    
    def add_safety_certification(self, certification_name: str, certification_body: str, 
                                 certification_date: datetime, expiry_date: datetime) -> None:
        """
        Add safety certification.
        
        Args:
            certification_name: Certification name
            certification_body: Certification body
            certification_date: Certification date
            expiry_date: Expiry date
        """
        certification = {
            'certification_name': certification_name,
            'certification_body': certification_body,
            'certification_date': certification_date.isoformat(),
            'expiry_date': expiry_date.isoformat(),
            'status': 'valid'
        }
        
        self.safety_certifications.append(certification)
        self.updated_at = datetime.now()
        logger.info(f"Added safety certification {certification_name} to laboratory {self.code}")
    
    def add_emergency_contact(self, contact_name: str, contact_number: str, 
                             contact_type: str) -> None:
        """
        Add emergency contact.
        
        Args:
            contact_name: Contact name
            contact_number: Contact number
            contact_type: Contact type
        """
        contact = {
            'contact_name': contact_name,
            'contact_number': contact_number,
            'contact_type': contact_type
        }
        
        self.emergency_contacts.append(contact)
        self.updated_at = datetime.now()
        logger.info(f"Added emergency contact {contact_name} to laboratory {self.code}")
    
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
        logger.info(f"Updated maintenance status for laboratory {self.code} to {status}")
    
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
        logger.info(f"Updated maintenance schedule for laboratory {self.code}")
    
    def update_booking_policy(self, policy_text: str, advance_days: int = None, 
                             max_duration_hours: int = None, auto_approve: bool = None,
                             require_supervision: bool = None) -> None:
        """
        Update booking policy.
        
        Args:
            policy_text: Booking policy text
            advance_days: Days in advance to book (optional)
            max_duration_hours: Maximum booking duration (optional)
            auto_approve: Auto-approve bookings (optional)
            require_supervision: Require supervision (optional)
        """
        self.booking_policy = policy_text
        
        if advance_days is not None:
            self.booking_advance_days = advance_days
        
        if max_duration_hours is not None:
            self.max_booking_duration_hours = max_duration_hours
        
        if auto_approve is not None:
            self.auto_approve = auto_approve
        
        if require_supervision is not None:
            self.require_supervision = require_supervision
        
        self.updated_at = datetime.now()
        logger.info(f"Updated booking policy for laboratory {self.code}")
    
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
        logger.info(f"Updated usage metrics for laboratory {self.code}")
    
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
        Check if laboratory is bookable.
        
        Returns:
            True if laboratory is bookable
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
    
    def get_laboratory_status(self) -> str:
        """
        Get laboratory status.
        
        Returns:
            Laboratory status string
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
    
    def get_laboratory_summary(self) -> Dict[str, Any]:
        """
        Get laboratory summary.
        
        Returns:
            Laboratory summary dictionary
        """
        return {
            'id': self.id,
            'code': self.code,
            'name': self.name,
            'type': self.type,
            'status': self.get_laboratory_status(),
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
            'equipment_count': len(self.equipment_list),
            'software_count': len(self.software_list),
            'is_bookable': self.is_bookable(),
            'booking_advance_days': self.booking_advance_days,
            'max_booking_duration_hours': self.max_booking_duration_hours,
            'auto_approve': self.auto_approve,
            'require_supervision': self.require_supervision,
            'safety_compliance': self.safety_compliance,
            'safety_certifications_count': len(self.safety_certifications)
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
            'most_booked_day': self.get_most_booked_day() if hasattr(self, 'bookings') and self.bookings else None
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
    
    def __repr__(self) -> str:
        """String representation of the laboratory model."""
        return f"<LaboratoryModel(code='{self.code}', name='{self.name}', type='{self.type}', status='{self.get_laboratory_status()}')>"