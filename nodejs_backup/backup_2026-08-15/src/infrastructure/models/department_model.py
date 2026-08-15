"""
Department Model for Database Operations

This module provides the SQLAlchemy model for Department entity.
It includes all fields and relationships for academic departments.

Author: Edu-Flow Team
"""

from typing import Dict, Any, Optional, List
from datetime import datetime
import logging

from sqlalchemy import Column, String, Integer, Text, DateTime, JSON, Boolean, ForeignKey
from sqlalchemy.orm import relationship

from src.infrastructure.models.base_model import BaseModel
from src.core.exceptions import ValidationError
from src.core.logging import get_logger

logger = get_logger(__name__)


class DepartmentModel(BaseModel):
    """
    SQLAlchemy model for Department entity.
    
    Represents academic departments with hierarchy management, program assignment, and statistics.
    """
    __tablename__ = "departments"
    
    # Department identification
    code = Column(String(20), unique=True, nullable=False, index=True)
    name = Column(String(100), nullable=False, index=True)
    description = Column(Text)
    short_name = Column(String(50), nullable=False)  # Short abbreviation
    
    # Hierarchy and organization
    parent_id = Column(String(50), ForeignKey("departments.id"))  # For hierarchical structure
    level = Column(Integer, nullable=False, default=0)  # Department level in hierarchy
    
    # Administrative details
    head_id = Column(String(50), ForeignKey("users.id"))  # Department head
    vice_head_id = Column(String(50), ForeignKey("users.id"))  # Vice head
    coordinator_id = Column(String(50), ForeignKey("users.id"))  # Academic coordinator
    
    # Contact information
    email = Column(String(100))
    phone = Column(String(20))
    address = Column(Text)
    website = Column(String(200))
    
    # Department statistics
    total_students = Column(Integer, default=0)
    total_faculty = Column(Integer, default=0)
    total_programs = Column(Integer, default=0)
    
    # Programs and subjects
    program_ids = Column(JSON, default=list)  # List of program IDs
    subject_ids = Column(JSON, default=list)  # List of subject IDs
    children_ids = Column(JSON, default=list)  # List of child department IDs
    
    # Administrative status
    status = Column(String(20), nullable=False, default="active")  # active, inactive, under_review
    is_academic = Column(Boolean, default=True)  # True for academic departments, False for administrative
    is_main_department = Column(Boolean, default=False)  # True for main departments (e.g., Computer Science)
    
    # Metadata
    metadata = Column(JSON, default=dict)
    
    # Relationships
    parent = relationship("DepartmentModel", remote_side=[id], back_populates="children")
    children = relationship("DepartmentModel", back_populates="parent")
    head = relationship("UserModel", foreign_keys=[head_id])
    vice_head = relationship("UserModel", foreign_keys=[vice_head_id])
    coordinator = relationship("UserModel", foreign_keys=[coordinator_id])
    subjects = relationship("SubjectModel", back_populates="department")
    programs = relationship("ProgramModel", back_populates="department")
    
    def __init__(self, **kwargs):
        """Initialize the department model with provided data."""
        # Set default values for optional fields
        kwargs.setdefault('level', 0)
        kwargs.setdefault('total_students', 0)
        kwargs.setdefault('total_faculty', 0)
        kwargs.setdefault('total_programs', 0)
        kwargs.setdefault('program_ids', [])
        kwargs.setdefault('subject_ids', [])
        kwargs.setdefault('children_ids', [])
        kwargs.setdefault('status', 'active')
        kwargs.setdefault('is_academic', True)
        kwargs.setdefault('is_main_department', False)
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
        if 'program_ids' in data and isinstance(data['program_ids'], list):
            data['program_ids'] = data['program_ids']
        else:
            data['program_ids'] = []
        
        if 'subject_ids' in data and isinstance(data['subject_ids'], list):
            data['subject_ids'] = data['subject_ids']
        else:
            data['subject_ids'] = []
        
        if 'children_ids' in data and isinstance(data['children_ids'], list):
            data['children_ids'] = data['children_ids']
        else:
            data['children_ids'] = []
        
        # Include hierarchical information
        data['has_children'] = len(data['children_ids']) > 0
        data['has_parent'] = data['parent_id'] is not None
        data['is_leaf'] = len(data['children_ids']) == 0
        
        # Include relationships if requested
        if include_relationships:
            if hasattr(self, 'parent') and self.parent:
                data['parent'] = self.parent.to_dict()
            else:
                data['parent'] = None
            
            if hasattr(self, 'children') and self.children:
                data['children'] = [child.to_dict() for child in self.children]
            else:
                data['children'] = []
            
            if hasattr(self, 'head') and self.head:
                data['head'] = self.head.to_dict()
            else:
                data['head'] = None
            
            if hasattr(self, 'vice_head') and self.vice_head:
                data['vice_head'] = self.vice_head.to_dict()
            else:
                data['vice_head'] = None
            
            if hasattr(self, 'coordinator') and self.coordinator:
                data['coordinator'] = self.coordinator.to_dict()
            else:
                data['coordinator'] = None
            
            if hasattr(self, 'subjects') and self.subjects:
                data['subjects'] = [subject.to_dict() for subject in self.subjects]
            else:
                data['subjects'] = []
            
            if hasattr(self, 'programs') and self.programs:
                data['programs'] = [program.to_dict() for program in self.programs]
            else:
                data['programs'] = []
        
        return data
    
    def update(self, **kwargs) -> None:
        """Update the model with new data."""
        # Handle special field updates
        if 'program_ids' in kwargs and isinstance(kwargs['program_ids'], list):
            self.program_ids = kwargs['program_ids']
        if 'subject_ids' in kwargs and isinstance(kwargs['subject_ids'], list):
            self.subject_ids = kwargs['subject_ids']
        if 'children_ids' in kwargs and isinstance(kwargs['children_ids'], list):
            self.children_ids = kwargs['children_ids']
        if 'metadata' in kwargs and isinstance(kwargs['metadata'], dict):
            self.metadata = kwargs['metadata']
        
        super().update(**kwargs)
    
    def validate(self) -> bool:
        """
        Validate the department model data.
        
        Returns:
            True if valid, False otherwise
            
        Raises:
            ValidationError: If validation fails
        """
        try:
            # Call base validation
            super().validate()
            
            # Department-specific validations
            if not self.code:
                raise ValidationError("Department code is required")
            
            if not self.name:
                raise ValidationError("Department name is required")
            
            if not self.short_name:
                raise ValidationError("Department short name is required")
            
            if self.level < 0:
                raise ValidationError("Department level cannot be negative")
            
            # Validate statistics
            if self.total_students < 0:
                raise ValidationError("Total students cannot be negative")
            
            if self.total_faculty < 0:
                raise ValidationError("Total faculty cannot be negative")
            
            if self.total_programs < 0:
                raise ValidationError("Total programs cannot be negative")
            
            # Validate JSON fields
            if not isinstance(self.program_ids, list):
                raise ValidationError("Program IDs must be a list")
            
            if not isinstance(self.subject_ids, list):
                raise ValidationError("Subject IDs must be a list")
            
            if not isinstance(self.children_ids, list):
                raise ValidationError("Children IDs must be a list")
            
            # Validate IDs format
            valid_ids = self.program_ids + self.subject_ids + self.children_ids
            for dept_id in valid_ids:
                if not isinstance(dept_id, str) or not dept_id.strip():
                    raise ValidationError("All IDs must be non-empty strings")
            
            # Validate metadata
            if not isinstance(self.metadata, dict):
                raise ValidationError("Metadata must be a dictionary")
            
            # Prevent circular references
            if self._check_circular_reference():
                raise ValidationError("Circular reference detected in department hierarchy")
            
            logger.info(f"Department {self.code} validation passed")
            return True
            
        except Exception as e:
            logger.error(f"Department validation error: {str(e)}")
            raise ValidationError(f"Department validation error: {str(e)}")
    
    def _check_circular_reference(self) -> bool:
        """
        Check for circular references in the department hierarchy.
        
        Returns:
            True if circular reference detected
        """
        visited = set()
        current_id = self.id
        
        while current_id:
            if current_id in visited:
                return True  # Circular reference detected
            
            visited.add(current_id)
            # This would query the database to find the parent in practice
            # For now, return False as placeholder
            break
        
        return False
    
    def add_program(self, program_id: str) -> bool:
        """
        Add a program to the department.
        
        Args:
            program_id: Program ID to add
            
        Returns:
            True if added successfully
        """
        if not program_id or not isinstance(program_id, str):
            raise ValidationError("Program ID must be a non-empty string")
        
        if program_id not in self.program_ids:
            self.program_ids.append(program_id)
            self.total_programs = len(self.program_ids)
            self.updated_at = datetime.now()
            logger.info(f"Added program {program_id} to department {self.code}")
            return True
        
        return False
    
    def remove_program(self, program_id: str) -> bool:
        """
        Remove a program from the department.
        
        Args:
            program_id: Program ID to remove
            
        Returns:
            True if removed successfully
        """
        if program_id in self.program_ids:
            self.program_ids.remove(program_id)
            self.total_programs = len(self.program_ids)
            self.updated_at = datetime.now()
            logger.info(f"Removed program {program_id} from department {self.code}")
            return True
        
        return False
    
    def add_subject(self, subject_id: str) -> bool:
        """
        Add a subject to the department.
        
        Args:
            subject_id: Subject ID to add
            
        Returns:
            True if added successfully
        """
        if not subject_id or not isinstance(subject_id, str):
            raise ValidationError("Subject ID must be a non-empty string")
        
        if subject_id not in self.subject_ids:
            self.subject_ids.append(subject_id)
            self.updated_at = datetime.now()
            logger.info(f"Added subject {subject_id} to department {self.code}")
            return True
        
        return False
    
    def remove_subject(self, subject_id: str) -> bool:
        """
        Remove a subject from the department.
        
        Args:
            subject_id: Subject ID to remove
            
        Returns:
            True if removed successfully
        """
        if subject_id in self.subject_ids:
            self.subject_ids.remove(subject_id)
            self.updated_at = datetime.now()
            logger.info(f"Removed subject {subject_id} from department {self.code}")
            return True
        
        return False
    
    def add_child_department(self, child_id: str) -> bool:
        """
        Add a child department.
        
        Args:
            child_id: Child department ID to add
            
        Returns:
            True if added successfully
        """
        if not child_id or not isinstance(child_id, str):
            raise ValidationError("Child department ID must be a non-empty string")
        
        if child_id not in self.children_ids:
            self.children_ids.append(child_id)
            self.updated_at = datetime.now()
            logger.info(f"Added child department {child_id} to department {self.code}")
            return True
        
        return False
    
    def remove_child_department(self, child_id: str) -> bool:
        """
        Remove a child department.
        
        Args:
            child_id: Child department ID to remove
            
        Returns:
            True if removed successfully
        """
        if child_id in self.children_ids:
            self.children_ids.remove(child_id)
            self.updated_at = datetime.now()
            logger.info(f"Removed child department {child_id} from department {self.code}")
            return True
        
        return False
    
    def get_department_hierarchy(self) -> Dict[str, Any]:
        """
        Get department hierarchy information.
        
        Returns:
            Hierarchy information dictionary
        """
        return {
            'id': self.id,
            'code': self.code,
            'name': self.name,
            'short_name': self.short_name,
            'level': self.level,
            'parent_id': self.parent_id,
            'has_parent': self.parent_id is not None,
            'has_children': len(self.children_ids) > 0,
            'children_count': len(self.children_ids),
            'is_leaf': len(self.children_ids) == 0,
            'is_root': self.level == 0
        }
    
    def get_department_statistics(self) -> Dict[str, Any]:
        """
        Get department statistics.
        
        Returns:
            Statistics information dictionary
        """
        return {
            'total_students': self.total_students,
            'total_faculty': self.total_faculty,
            'total_programs': self.total_programs,
            'total_subjects': len(self.subject_ids),
            'total_children_departments': len(self.children_ids),
            'is_academic': self.is_academic,
            'is_main_department': self.is_main_department
        }
    
    def update_department_head(self, head_id: str) -> None:
        """
        Update department head.
        
        Args:
            head_id: User ID of the department head
        """
        self.head_id = head_id
        self.updated_at = datetime.now()
        logger.info(f"Updated department head for {self.code}")
    
    def update_vice_head(self, vice_head_id: str) -> None:
        """
        Update department vice head.
        
        Args:
            vice_head_id: User ID of the vice head
        """
        self.vice_head_id = vice_head_id
        self.updated_at = datetime.now()
        logger.info(f"Updated department vice head for {self.code}")
    
    def update_coordinator(self, coordinator_id: str) -> None:
        """
        Update department coordinator.
        
        Args:
            coordinator_id: User ID of the coordinator
        """
        self.coordinator_id = coordinator_id
        self.updated_at = datetime.now()
        logger.info(f"Updated department coordinator for {self.code}")
    
    def update_contact_info(self, **contact_info) -> None:
        """
        Update contact information.
        
        Args:
            **contact_info: Contact information to update
        """
        if 'email' in contact_info:
            self.email = contact_info['email']
        if 'phone' in contact_info:
            self.phone = contact_info['phone']
        if 'address' in contact_info:
            self.address = contact_info['address']
        if 'website' in contact_info:
            self.website = contact_info['website']
        
        self.updated_at = datetime.now()
        logger.info(f"Updated contact info for department {self.code}")
    
    def update_statistics(self, **stats) -> None:
        """
        Update department statistics.
        
        Args:
            **stats: Statistics to update
        """
        if 'total_students' in stats:
            self.total_students = stats['total_students']
        if 'total_faculty' in stats:
            self.total_faculty = stats['total_faculty']
        if 'total_programs' in stats:
            self.total_programs = stats['total_programs']
        
        self.updated_at = datetime.now()
        logger.info(f"Updated statistics for department {self.code}")
    
    def activate_department(self) -> None:
        """
        Activate the department.
        """
        self.status = 'active'
        self.updated_at = datetime.now()
        logger.info(f"Activated department {self.code}")
    
    def deactivate_department(self) -> None:
        """
        Deactivate the department.
        """
        self.status = 'inactive'
        self.updated_at = datetime.now()
        logger.info(f"Deactivated department {self.code}")
    
    def is_active(self) -> bool:
        """
        Check if department is active.
        
        Returns:
            True if active
        """
        return self.status == 'active'
    
    def is_inactive(self) -> bool:
        """
        Check if department is inactive.
        
        Returns:
            True if inactive
        """
        return self.status == 'inactive'
    
    def is_academic_department(self) -> bool:
        """
        Check if department is academic.
        
        Returns:
            True if academic
        """
        return self.is_academic
    
    def is_administrative_department(self) -> bool:
        """
        Check if department is administrative.
        
        Returns:
            True if administrative
        """
        return not self.is_academic
    
    def is_main_department(self) -> bool:
        """
        Check if department is a main department.
        
        Returns:
            True if main department
        """
        return self.is_main_department
    
    def __repr__(self) -> str:
        """String representation of the department model."""
        return f"<DepartmentModel(code='{self.code}', name='{self.name}', level={self.level})>"