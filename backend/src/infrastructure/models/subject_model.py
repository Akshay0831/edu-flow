"""
Subject Model for Database Operations

This module provides the SQLAlchemy model for Subject entity.
It includes all fields and relationships for academic subjects.

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


class SubjectModel(BaseModel):
    """
    SQLAlchemy model for Subject entity.
    
    Represents academic subjects with prerequisites, CO-PO mapping, and academic catalog.
    """
    __tablename__ = "subjects"
    
    # Subject identification
    code = Column(String(50), unique=True, nullable=False, index=True)
    name = Column(String(200), nullable=False, index=True)
    description = Column(Text)
    
    # Academic details
    credits = Column(Integer, nullable=False, default=0)
    level = Column(String(20), nullable=False)  # UG, PG, PhD, etc.
    semester = Column(Integer, nullable=False)  # 1-12
    department_id = Column(String(50), ForeignKey("departments.id"), nullable=False)
    
    # Subject content and structure
    syllabus = Column(Text)
    learning_objectives = Column(Text)
    assessment_methods = Column(Text)
    prerequisites = Column(JSON, default=list)  # List of subject codes
    co_po_map = Column(JSON, default=dict)  # Course Outcome to Program Outcome mapping
    course_catalog = Column(JSON, default=dict)  # Course catalog information
    
    # Administrative details
    status = Column(String(20), nullable=False, default="active")  # active, inactive, under_review
    is_elective = Column(Boolean, default=False)
    is_required = Column(Boolean, default=True)
    contact_hours = Column(Integer, default=0)
    lab_hours = Column(Integer, default=0)
    total_hours = Column(Integer, default=0)
    
    # Metadata
    metadata = Column(JSON, default=dict)
    
    # Relationships
    department = relationship("DepartmentModel", back_populates="subjects")
    classes = relationship("ClassModel", back_populates="subject")
    
    def __init__(self, **kwargs):
        """Initialize the subject model with provided data."""
        # Set default values for optional fields
        kwargs.setdefault('credits', 0)
        kwargs.setdefault('level', 'UG')
        kwargs.setdefault('semester', 1)
        kwargs.setdefault('prerequisites', [])
        kwargs.setdefault('co_po_map', {})
        kwargs.setdefault('course_catalog', {})
        kwargs.setdefault('status', 'active')
        kwargs.setdefault('is_elective', False)
        kwargs.setdefault('is_required', True)
        kwargs.setdefault('contact_hours', 0)
        kwargs.setdefault('lab_hours', 0)
        kwargs.setdefault('total_hours', 0)
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
        
        # Convert JSON fields to proper format
        if 'prerequisites' in data and isinstance(data['prerequisites'], list):
            data['prerequisites'] = data['prerequisites']
        else:
            data['prerequisites'] = []
        
        if 'co_po_map' in data and isinstance(data['co_po_map'], dict):
            data['co_po_map'] = data['co_po_map']
        else:
            data['co_po_map'] = {}
        
        if 'course_catalog' in data and isinstance(data['course_catalog'], dict):
            data['course_catalog'] = data['course_catalog']
        else:
            data['course_catalog'] = {}
        
        if 'metadata' in data and isinstance(data['metadata'], dict):
            data['metadata'] = data['metadata']
        else:
            data['metadata'] = {}
        
        # Include relationships if requested
        if include_relationships:
            if hasattr(self, 'department') and self.department:
                data['department'] = self.department.to_dict()
            else:
                data['department'] = None
            
            if hasattr(self, 'classes') and self.classes:
                data['classes'] = [cls.to_dict() for cls in self.classes]
            else:
                data['classes'] = []
        
        return data
    
    def update(self, **kwargs) -> None:
        """Update the model with new data."""
        # Handle special field updates
        if 'prerequisites' in kwargs and isinstance(kwargs['prerequisites'], list):
            self.prerequisites = kwargs['prerequisites']
        if 'co_po_map' in kwargs and isinstance(kwargs['co_po_map'], dict):
            self.co_po_map = kwargs['co_po_map']
        if 'course_catalog' in kwargs and isinstance(kwargs['course_catalog'], dict):
            self.course_catalog = kwargs['course_catalog']
        if 'metadata' in kwargs and isinstance(kwargs['metadata'], dict):
            self.metadata = kwargs['metadata']
        
        super().update(**kwargs)
    
    def validate(self) -> bool:
        """
        Validate the subject model data.
        
        Returns:
            True if valid, False otherwise
            
        Raises:
            ValidationError: If validation fails
        """
        try:
            # Call base validation
            super().validate()
            
            # Subject-specific validations
            if not self.code:
                raise ValidationError("Subject code is required")
            
            if not self.name:
                raise ValidationError("Subject name is required")
            
            if not self.department_id:
                raise ValidationError("Department ID is required")
            
            if self.credits < 0:
                raise ValidationError("Credits cannot be negative")
            
            if self.level not in ['UG', 'PG', 'PhD', 'Diploma', 'Certificate']:
                raise ValidationError("Invalid level")
            
            if self.semester < 1 or self.semester > 12:
                raise ValidationError("Semester must be between 1 and 12")
            
            if self.contact_hours < 0:
                raise ValidationError("Contact hours cannot be negative")
            
            if self.lab_hours < 0:
                raise ValidationError("Lab hours cannot be negative")
            
            if self.total_hours < 0:
                raise ValidationError("Total hours cannot be negative")
            
            if self.total_hours != (self.contact_hours + self.lab_hours):
                raise ValidationError("Total hours must equal contact hours plus lab hours")
            
            # Validate prerequisites format
            if not isinstance(self.prerequisites, list):
                raise ValidationError("Prerequisites must be a list")
            
            for prereq in self.prerequisites:
                if not isinstance(prereq, str) or not prereq.strip():
                    raise ValidationError("Each prerequisite must be a non-empty string")
            
            # Validate CO-PO mapping format
            if not isinstance(self.co_po_map, dict):
                raise ValidationError("CO-PO mapping must be a dictionary")
            
            # Validate course catalog format
            if not isinstance(self.course_catalog, dict):
                raise ValidationError("Course catalog must be a dictionary")
            
            # Validate metadata format
            if not isinstance(self.metadata, dict):
                raise ValidationError("Metadata must be a dictionary")
            
            logger.info(f"Subject {self.code} validation passed")
            return True
            
        except Exception as e:
            logger.error(f"Subject validation error: {str(e)}")
            raise ValidationError(f"Subject validation error: {str(e)}")
    
    def add_prerequisite(self, subject_code: str) -> bool:
        """
        Add a prerequisite subject.
        
        Args:
            subject_code: Code of the prerequisite subject
            
        Returns:
            True if added successfully
        """
        if not subject_code or not isinstance(subject_code, str):
            raise ValidationError("Subject code must be a non-empty string")
        
        if subject_code not in self.prerequisites:
            self.prerequisites.append(subject_code)
            self.updated_at = datetime.now()
            logger.info(f"Added prerequisite {subject_code} to subject {self.code}")
            return True
        
        return False
    
    def remove_prerequisite(self, subject_code: str) -> bool:
        """
        Remove a prerequisite subject.
        
        Args:
            subject_code: Code of the prerequisite subject to remove
            
        Returns:
            True if removed successfully
        """
        if subject_code in self.prerequisites:
            self.prerequisites.remove(subject_code)
            self.updated_at = datetime.now()
            logger.info(f"Removed prerequisite {subject_code} from subject {self.code}")
            return True
        
        return False
    
    def add_co_po_mapping(self, course_outcome: str, program_outcome: str) -> bool:
        """
        Add a CO-PO mapping.
        
        Args:
            course_outcome: Course outcome code
            program_outcome: Program outcome code
            
        Returns:
            True if mapping added successfully
        """
        if not course_outcome or not isinstance(course_outcome, str):
            raise ValidationError("Course outcome must be a non-empty string")
        
        if not program_outcome or not isinstance(program_outcome, str):
            raise ValidationError("Program outcome must be a non-empty string")
        
        self.co_po_map[course_outcome] = program_outcome
        self.updated_at = datetime.now()
        logger.info(f"Added CO-PO mapping: {course_outcome} -> {program_outcome}")
        return True
    
    def remove_co_po_mapping(self, course_outcome: str) -> bool:
        """
        Remove a CO-PO mapping.
        
        Args:
            course_outcome: Course outcome code to remove
            
        Returns:
            True if mapping removed successfully
        """
        if course_outcome in self.co_po_map:
            del self.co_po_map[course_outcome]
            self.updated_at = datetime.now()
            logger.info(f"Removed CO-PO mapping for {course_outcome}")
            return True
        
        return False
    
    def update_course_catalog(self, **catalog_data) -> None:
        """
        Update course catalog information.
        
        Args:
            **catalog_data: Course catalog data to update
        """
        self.course_catalog.update(catalog_data)
        self.updated_at = datetime.now()
        logger.info(f"Updated course catalog for subject {self.code}")
    
    def get_contact_hours(self) -> int:
        """
        Get total contact hours.
        
        Returns:
            Total contact hours
        """
        return self.contact_hours
    
    def get_lab_hours(self) -> int:
        """
        Get total lab hours.
        
        Returns:
            Total lab hours
        """
        return self.lab_hours
    
    def get_total_hours(self) -> int:
        """
        Get total hours.
        
        Returns:
            Total hours (contact + lab)
        """
        return self.contact_hours + self.lab_hours
    
    def is_elective_subject(self) -> bool:
        """
        Check if subject is elective.
        
        Returns:
            True if elective
        """
        return self.is_elective
    
    def is_required_subject(self) -> bool:
        """
        Check if subject is required.
        
        Returns:
            True if required
        """
        return self.is_required
    
    def get_academic_level(self) -> str:
        """
        Get academic level.
        
        Returns:
            Academic level (UG, PG, PhD, etc.)
        """
        return self.level
    
    def __repr__(self) -> str:
        """String representation of the subject model."""
        return f"<SubjectModel(code='{self.code}', name='{self.name}', level='{self.level}', semester={self.semester})>"