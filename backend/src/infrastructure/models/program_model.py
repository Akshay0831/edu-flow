"""
Program Model for Database Operations

This module provides the SQLAlchemy model for Program entity.
It includes all fields and relationships for academic program management.

Author: Edu-Flow Team
"""

from typing import Dict, Any, Optional, List
from datetime import datetime
import logging

from sqlalchemy import Column, String, Integer, Text, DateTime, JSON, Boolean, ForeignKey, Float, Float
from sqlalchemy.orm import relationship

from src.infrastructure.models.base_model import BaseModel
from src.core.exceptions import ValidationError
from src.core.logging import get_logger

logger = get_logger(__name__)


class ProgramModel(BaseModel):
    """
    SQLAlchemy model for Program entity.
    
    Represents academic programs with curriculum structure, outcomes, and enrollment management.
    """
    __tablename__ = "programs"
    
    # Program identification
    id = Column(String(50), primary_key=True)
    code = Column(String(20), unique=True, nullable=False, index=True)
    name = Column(String(200), nullable=False, index=True)
    description = Column(Text)
    short_name = Column(String(100), nullable=False)
    
    # Program details
    level = Column(String(20), nullable=False)  # UG, PG, PhD, Diploma, Certificate
    duration_years = Column(Integer, nullable=False)  # Program duration in years
    duration_months = Column(Integer, default=0)  # Additional months
    total_credits = Column(Integer, nullable=False)  # Total credits required
    
    # Department and affiliation
    department_id = Column(String(50), ForeignKey("departments.id"), nullable=False)
    parent_program_id = Column(String(50), ForeignKey("programs.id"))  # For nested programs
    
    # Academic structure
    curriculum_structure = Column(JSON, default=dict)  # Semester-wise course structure
    core_subject_ids = Column(JSON, default=list)  # List of core subject IDs
    elective_subject_ids = Column(JSON, default=list)  # List of elective subject IDs
    mandatory_subject_ids = Column(JSON, default=list)  # List of mandatory subject IDs
    
    # Program outcomes
    program_outcomes = Column(JSON, default=list)  # List of program outcomes
    course_outcomes = Column(JSON, default=list)  # List of course outcomes
    graduate_attributes = Column(JSON, default=list)  # List of graduate attributes
    
    # Enrollment and capacity
    max_capacity = Column(Integer, default=0)  # Maximum capacity
    current_enrollment = Column(Integer, default=0)  # Current enrollment count
    minimum_gpa = Column(Float, default=0.0)  # Minimum GPA for admission
    admission_requirements = Column(JSON, default=dict)  # Admission requirements
    
    # Program status
    status = Column(String(20), nullable=False, default="active")  # active, inactive, under_review, suspended
    is_active = Column(Boolean, default=True)
    is_open_for_admission = Column(Boolean, default=True)
    is_joint_program = Column(Boolean, default=False)  # Joint program with other institution
    is_online_program = Column(Boolean, default=False)  # Online/Distance learning program
    
    # Accreditation and approval
    accreditation_status = Column(String(50))  # accredited, provisional, not_accredited
    accreditation_expiry = Column(DateTime)
    approval_date = Column(DateTime)
    
    # Timeline and deadlines
    start_date = Column(DateTime)  # Program start date
    end_date = Column(DateTime)  # Program end date
    admission_start_date = Column(DateTime)
    admission_end_date = Column(DateTime)
    
    # Program metadata
    metadata = Column(JSON, default=dict)
    program_highlights = Column(Text)  # Key highlights of the program
    career_opportunities = Column(Text)  # Career opportunities after program
    
    # Relationships
    department = relationship("DepartmentModel", back_populates="programs")
    parent_program = relationship("ProgramModel", remote_side=[id])
    child_programs = relationship("ProgramModel", back_populates="parent_program")
    subjects = relationship("SubjectModel")
    students = relationship("UserModel", foreign_keys="UserModel.program_id")
    enrollments = relationship("EnrollmentModel")
    outcomes = relationship("OutcomesModel", foreign_keys="OutcomesModel.program_id")
    
    def __init__(self, **kwargs):
        """Initialize the program model with provided data."""
        # Set default values for optional fields
        kwargs.setdefault('duration_years', 0)
        kwargs.setdefault('duration_months', 0)
        kwargs.setdefault('total_credits', 0)
        kwargs.setdefault('core_subject_ids', [])
        kwargs.setdefault('elective_subject_ids', [])
        kwargs.setdefault('mandatory_subject_ids', [])
        kwargs.setdefault('program_outcomes', [])
        kwargs.setdefault('course_outcomes', [])
        kwargs.setdefault('graduate_attributes', [])
        kwargs.setdefault('max_capacity', 0)
        kwargs.setdefault('current_enrollment', 0)
        kwargs.setdefault('minimum_gpa', 0.0)
        kwargs.setdefault('admission_requirements', {})
        kwargs.setdefault('status', 'active')
        kwargs.setdefault('is_active', True)
        kwargs.setdefault('is_open_for_admission', True)
        kwargs.setdefault('is_joint_program', False)
        kwargs.setdefault('is_online_program', False)
        kwargs.setdefault('metadata', {})
        kwargs.setdefault('curriculum_structure', {})
        
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
        if 'accreditation_expiry' in data and isinstance(data['accreditation_expiry'], datetime):
            data['accreditation_expiry'] = data['accreditation_expiry'].isoformat()
        else:
            data['accreditation_expiry'] = None
        
        if 'approval_date' in data and isinstance(data['approval_date'], datetime):
            data['approval_date'] = data['approval_date'].isoformat()
        else:
            data['approval_date'] = None
        
        if 'start_date' in data and isinstance(data['start_date'], datetime):
            data['start_date'] = data['start_date'].isoformat()
        else:
            data['start_date'] = None
        
        if 'end_date' in data and isinstance(data['end_date'], datetime):
            data['end_date'] = data['end_date'].isoformat()
        else:
            data['end_date'] = None
        
        if 'admission_start_date' in data and isinstance(data['admission_start_date'], datetime):
            data['admission_start_date'] = data['admission_start_date'].isoformat()
        else:
            data['admission_start_date'] = None
        
        if 'admission_end_date' in data and isinstance(data['admission_end_date'], datetime):
            data['admission_end_date'] = data['admission_end_date'].isoformat()
        else:
            data['admission_end_date'] = None
        
        # Convert JSON fields to proper format
        if 'curriculum_structure' in data and isinstance(data['curriculum_structure'], dict):
            data['curriculum_structure'] = data['curriculum_structure']
        else:
            data['curriculum_structure'] = {}
        
        if 'core_subject_ids' in data and isinstance(data['core_subject_ids'], list):
            data['core_subject_ids'] = data['core_subject_ids']
        else:
            data['core_subject_ids'] = []
        
        if 'elective_subject_ids' in data and isinstance(data['elective_subject_ids'], list):
            data['elective_subject_ids'] = data['elective_subject_ids']
        else:
            data['elective_subject_ids'] = []
        
        if 'mandatory_subject_ids' in data and isinstance(data['mandatory_subject_ids'], list):
            data['mandatory_subject_ids'] = data['mandatory_subject_ids']
        else:
            data['mandatory_subject_ids'] = []
        
        if 'program_outcomes' in data and isinstance(data['program_outcomes'], list):
            data['program_outcomes'] = data['program_outcomes']
        else:
            data['program_outcomes'] = []
        
        if 'course_outcomes' in data and isinstance(data['course_outcomes'], list):
            data['course_outcomes'] = data['course_outcomes']
        else:
            data['course_outcomes'] = []
        
        if 'graduate_attributes' in data and isinstance(data['graduate_attributes'], list):
            data['graduate_attributes'] = data['graduate_attributes']
        else:
            data['graduate_attributes'] = []
        
        if 'admission_requirements' in data and isinstance(data['admission_requirements'], dict):
            data['admission_requirements'] = data['admission_requirements']
        else:
            data['admission_requirements'] = {}
        
        if 'metadata' in data and isinstance(data['metadata'], dict):
            data['metadata'] = data['metadata']
        else:
            data['metadata'] = {}
        
        # Calculate derived fields
        data['total_duration_months'] = (self.duration_years * 12) + self.duration_months
        data['enrollment_percentage'] = (self.current_enrollment / self.max_capacity * 100) if self.max_capacity > 0 else 0
        data['is_full'] = self.current_enrollment >= self.max_capacity
        data['program_type'] = self.get_program_type()
        data['accreditation_status_summary'] = self.get_accreditation_status_summary()
        
        # Include relationships if requested
        if include_relationships:
            if hasattr(self, 'department') and self.department:
                data['department'] = self.department.to_dict()
            else:
                data['department'] = None
            
            if hasattr(self, 'parent_program') and self.parent_program:
                data['parent_program'] = self.parent_program.to_dict()
            else:
                data['parent_program'] = None
            
            if hasattr(self, 'subjects') and self.subjects:
                data['subjects'] = [subject.to_dict() for subject in self.subjects]
            else:
                data['subjects'] = []
            
            if hasattr(self, 'students') and self.students:
                data['students'] = [student.to_dict() for student in self.students]
            else:
                data['students'] = []
            
            if hasattr(self, 'enrollments') and self.enrollments:
                data['enrollments'] = [enrollment.to_dict() for enrollment in self.enrollments]
            else:
                data['enrollments'] = []
            
            if hasattr(self, 'outcomes') and self.outcomes:
                data['outcomes'] = [outcome.to_dict() for outcome in self.outcomes]
            else:
                data['outcomes'] = []
        
        return data
    
    def update(self, **kwargs) -> None:
        """Update the model with new data."""
        # Handle special field updates
        if 'curriculum_structure' in kwargs and isinstance(kwargs['curriculum_structure'], dict):
            self.curriculum_structure = kwargs['curriculum_structure']
        if 'core_subject_ids' in kwargs and isinstance(kwargs['core_subject_ids'], list):
            self.core_subject_ids = kwargs['core_subject_ids']
        if 'elective_subject_ids' in kwargs and isinstance(kwargs['elective_subject_ids'], list):
            self.elective_subject_ids = kwargs['elective_subject_ids']
        if 'mandatory_subject_ids' in kwargs and isinstance(kwargs['mandatory_subject_ids'], list):
            self.mandatory_subject_ids = kwargs['mandatory_subject_ids']
        if 'program_outcomes' in kwargs and isinstance(kwargs['program_outcomes'], list):
            self.program_outcomes = kwargs['program_outcomes']
        if 'course_outcomes' in kwargs and isinstance(kwargs['course_outcomes'], list):
            self.course_outcomes = kwargs['course_outcomes']
        if 'graduate_attributes' in kwargs and isinstance(kwargs['graduate_attributes'], list):
            self.graduate_attributes = kwargs['graduate_attributes']
        if 'admission_requirements' in kwargs and isinstance(kwargs['admission_requirements'], dict):
            self.admission_requirements = kwargs['admission_requirements']
        if 'metadata' in kwargs and isinstance(kwargs['metadata'], dict):
            self.metadata = kwargs['metadata']
        
        super().update(**kwargs)
    
    def validate(self) -> bool:
        """
        Validate the program model data.
        
        Returns:
            True if valid, False otherwise
            
        Raises:
            ValidationError: If validation fails
        """
        try:
            # Call base validation
            super().validate()
            
            # Program-specific validations
            if not self.id:
                raise ValidationError("Program ID is required")
            
            if not self.code:
                raise ValidationError("Program code is required")
            
            if not self.name:
                raise ValidationError("Program name is required")
            
            if not self.short_name:
                raise ValidationError("Program short name is required")
            
            if not self.level:
                raise ValidationError("Program level is required")
            
            if not self.department_id:
                raise ValidationError("Department ID is required")
            
            # Level validation
            valid_levels = ['UG', 'PG', 'PhD', 'Diploma', 'Certificate', 'Foundation']
            if self.level not in valid_levels:
                raise ValidationError(f"Invalid program level: {self.level}")
            
            # Duration validation
            if self.duration_years < 0:
                raise ValidationError("Duration years cannot be negative")
            
            if self.duration_months < 0 or self.duration_months > 11:
                raise ValidationError("Duration months must be between 0 and 11")
            
            # Credits validation
            if self.total_credits <= 0:
                raise ValidationError("Total credits must be positive")
            
            # Capacity validation
            if self.max_capacity < 0:
                raise ValidationError("Maximum capacity cannot be negative")
            
            if self.current_enrollment < 0:
                raise ValidationError("Current enrollment cannot be negative")
            
            if self.current_enrollment > self.max_capacity:
                raise ValidationError("Current enrollment cannot exceed maximum capacity")
            
            # GPA validation
            if self.minimum_gpa < 0 or self.minimum_gpa > 4.0:
                raise ValidationError("Minimum GPA must be between 0 and 4.0")
            
            # Status validation
            valid_statuses = ['active', 'inactive', 'under_review', 'suspended']
            if self.status not in valid_statuses:
                raise ValidationError(f"Invalid status: {self.status}")
            
            # Accreditation status validation
            if self.accreditation_status:
                valid_accreditation_statuses = ['accredited', 'provisional', 'not_accredited', 'pending']
                if self.accreditation_status not in valid_accreditation_statuses:
                    raise ValidationError(f"Invalid accreditation status: {self.accreditation_status}")
            
            # JSON fields validation
            if not isinstance(self.curriculum_structure, dict):
                raise ValidationError("Curriculum structure must be a dictionary")
            
            if not isinstance(self.core_subject_ids, list):
                raise ValidationError("Core subject IDs must be a list")
            
            if not isinstance(self.elective_subject_ids, list):
                raise ValidationError("Elective subject IDs must be a list")
            
            if not isinstance(self.mandatory_subject_ids, list):
                raise ValidationError("Mandatory subject IDs must be a list")
            
            if not isinstance(self.program_outcomes, list):
                raise ValidationError("Program outcomes must be a list")
            
            if not isinstance(self.course_outcomes, list):
                raise ValidationError("Course outcomes must be a list")
            
            if not isinstance(self.graduate_attributes, list):
                raise ValidationError("Graduate attributes must be a list")
            
            if not isinstance(self.admission_requirements, dict):
                raise ValidationError("Admission requirements must be a dictionary")
            
            # Metadata validation
            if not isinstance(self.metadata, dict):
                raise ValidationError("Metadata must be a dictionary")
            
            logger.info(f"Program {self.code} validation passed")
            return True
            
        except Exception as e:
            logger.error(f"Program validation error: {str(e)}")
            raise ValidationError(f"Program validation error: {str(e)}")
    
    def add_subject(self, subject_id: str, subject_type: str = "core") -> bool:
        """
        Add a subject to the program.
        
        Args:
            subject_id: Subject ID to add
            subject_type: Type of subject (core, elective, mandatory)
            
        Returns:
            True if added successfully
        """
        if not subject_id or not isinstance(subject_id, str):
            raise ValidationError("Subject ID must be a non-empty string")
        
        if subject_type == "core":
            if subject_id not in self.core_subject_ids:
                self.core_subject_ids.append(subject_id)
                logger.info(f"Added subject {subject_id} to core subjects for program {self.code}")
                return True
        elif subject_type == "elective":
            if subject_id not in self.elective_subject_ids:
                self.elective_subject_ids.append(subject_id)
                logger.info(f"Added subject {subject_id} to elective subjects for program {self.code}")
                return True
        elif subject_type == "mandatory":
            if subject_id not in self.mandatory_subject_ids:
                self.mandatory_subject_ids.append(subject_id)
                logger.info(f"Added subject {subject_id} to mandatory subjects for program {self.code}")
                return True
        else:
            raise ValidationError(f"Invalid subject type: {subject_type}")
        
        return False
    
    def remove_subject(self, subject_id: str, subject_type: str = "core") -> bool:
        """
        Remove a subject from the program.
        
        Args:
            subject_id: Subject ID to remove
            subject_type: Type of subject (core, elective, mandatory)
            
        Returns:
            True if removed successfully
        """
        if subject_type == "core":
            if subject_id in self.core_subject_ids:
                self.core_subject_ids.remove(subject_id)
                logger.info(f"Removed subject {subject_id} from core subjects for program {self.code}")
                return True
        elif subject_type == "elective":
            if subject_id in self.elective_subject_ids:
                self.elective_subject_ids.remove(subject_id)
                logger.info(f"Removed subject {subject_id} from elective subjects for program {self.code}")
                return True
        elif subject_type == "mandatory":
            if subject_id in self.mandatory_subject_ids:
                self.mandatory_subject_ids.remove(subject_id)
                logger.info(f"Removed subject {subject_id} from mandatory subjects for program {self.code}")
                return True
        else:
            raise ValidationError(f"Invalid subject type: {subject_type}")
        
        return False
    
    def add_program_outcome(self, outcome: str) -> bool:
        """
        Add a program outcome.
        
        Args:
            outcome: Program outcome text
            
        Returns:
            True if added successfully
        """
        if not outcome or not isinstance(outcome, str):
            raise ValidationError("Program outcome must be a non-empty string")
        
        if outcome not in self.program_outcomes:
            self.program_outcomes.append(outcome)
            logger.info(f"Added program outcome to program {self.code}: {outcome}")
            return True
        
        return False
    
    def remove_program_outcome(self, outcome: str) -> bool:
        """
        Remove a program outcome.
        
        Args:
            outcome: Program outcome to remove
            
        Returns:
            True if removed successfully
        """
        if outcome in self.program_outcomes:
            self.program_outcomes.remove(outcome)
            logger.info(f"Removed program outcome from program {self.code}: {outcome}")
            return True
        
        return False
    
    def add_course_outcome(self, outcome: str) -> bool:
        """
        Add a course outcome.
        
        Args:
            outcome: Course outcome text
            
        Returns:
            True if added successfully
        """
        if not outcome or not isinstance(outcome, str):
            raise ValidationError("Course outcome must be a non-empty string")
        
        if outcome not in self.course_outcomes:
            self.course_outcomes.append(outcome)
            logger.info(f"Added course outcome to program {self.code}: {outcome}")
            return True
        
        return False
    
    def remove_course_outcome(self, outcome: str) -> bool:
        """
        Remove a course outcome.
        
        Args:
            outcome: Course outcome to remove
            
        Returns:
            True if removed successfully
        """
        if outcome in self.course_outcomes:
            self.course_outcomes.remove(outcome)
            logger.info(f"Removed course outcome from program {self.code}: {outcome}")
            return True
        
        return False
    
    def add_graduate_attribute(self, attribute: str) -> bool:
        """
        Add a graduate attribute.
        
        Args:
            attribute: Graduate attribute text
            
        Returns:
            True if added successfully
        """
        if not attribute or not isinstance(attribute, str):
            raise ValidationError("Graduate attribute must be a non-empty string")
        
        if attribute not in self.graduate_attributes:
            self.graduate_attributes.append(attribute)
            logger.info(f"Added graduate attribute to program {self.code}: {attribute}")
            return True
        
        return False
    
    def remove_graduate_attribute(self, attribute: str) -> bool:
        """
        Remove a graduate attribute.
        
        Args:
            attribute: Graduate attribute to remove
            
        Returns:
            True if removed successfully
        """
        if attribute in self.graduate_attributes:
            self.graduate_attributes.remove(attribute)
            logger.info(f"Removed graduate attribute from program {self.code}: {attribute}")
            return True
        
        return False
    
    def update_curriculum_structure(self, semester: int, **structure_data) -> None:
        """
        Update curriculum structure for a specific semester.
        
        Args:
            semester: Semester number
            **structure_data: Structure data to update
        """
        if semester < 1 or semester > 8:  # Assuming max 8 semesters
            raise ValidationError("Semester must be between 1 and 8")
        
        if 'curriculum_structure' not in self.metadata:
            self.metadata['curriculum_structure'] = {}
        
        if str(semester) not in self.metadata['curriculum_structure']:
            self.metadata['curriculum_structure'][str(semester)] = {}
        
        self.metadata['curriculum_structure'][str(semester)].update(structure_data)
        self.updated_at = datetime.now()
        logger.info(f"Updated curriculum structure for semester {semester} in program {self.code}")
    
    def get_curriculum_semester(self, semester: int) -> Dict[str, Any]:
        """
        Get curriculum structure for a specific semester.
        
        Args:
            semester: Semester number
            
        Returns:
            Curriculum structure for the semester
        """
        if 'curriculum_structure' not in self.metadata:
            self.metadata['curriculum_structure'] = {}
        
        return self.metadata['curriculum_structure'].get(str(semester), {})
    
    def update_capacity(self, max_capacity: int) -> None:
        """
        Update program capacity.
        
        Args:
            max_capacity: Maximum capacity
        """
        if max_capacity < 0:
            raise ValidationError("Maximum capacity cannot be negative")
        
        self.max_capacity = max_capacity
        
        # Ensure current enrollment doesn't exceed new max capacity
        if self.current_enrollment > max_capacity:
            self.current_enrollment = max_capacity
        
        self.updated_at = datetime.now()
        logger.info(f"Updated capacity for program {self.code}: {max_capacity}")
    
    def enroll_student(self, student_id: str) -> bool:
        """
        Enroll a student in the program.
        
        Args:
            student_id: Student ID to enroll
            
        Returns:
            True if enrolled successfully
        """
        if self.current_enrollment >= self.max_capacity:
            raise ValidationError("Program is at maximum capacity")
        
        if self.current_enrollment < self.max_capacity:
            self.current_enrollment += 1
            self.updated_at = datetime.now()
            logger.info(f"Enrolled student {student_id} in program {self.code}")
            return True
        
        return False
    
    def unenroll_student(self, student_id: str) -> bool:
        """
        Unenroll a student from the program.
        
        Args:
            student_id: Student ID to unenroll
            
        Returns:
            True if unenrolled successfully
        """
        if self.current_enrollment > 0:
            self.current_enrollment -= 1
            self.updated_at = datetime.now()
            logger.info(f"Unenrolled student {student_id} from program {self.code}")
            return True
        
        return False
    
    def update_admission_dates(self, start_date: datetime, end_date: datetime) -> None:
        """
        Update admission dates.
        
        Args:
            start_date: Admission start date
            end_date: Admission end date
        """
        if start_date > end_date:
            raise ValidationError("Start date must be before end date")
        
        self.admission_start_date = start_date
        self.admission_end_date = end_date
        self.updated_at = datetime.now()
        logger.info(f"Updated admission dates for program {self.code}")
    
    def set_accreditation_status(self, status: str, expiry_date: datetime = None) -> None:
        """
        Set accreditation status.
        
        Args:
            status: Accreditation status
            expiry_date: Expiry date (optional)
        """
        valid_statuses = ['accredited', 'provisional', 'not_accredited', 'pending']
        if status not in valid_statuses:
            raise ValidationError(f"Invalid accreditation status: {status}")
        
        self.accreditation_status = status
        self.accreditation_expiry = expiry_date
        self.updated_at = datetime.now()
        logger.info(f"Set accreditation status for program {self.code}: {status}")
    
    def activate_program(self) -> None:
        """
        Activate the program.
        """
        self.status = 'active'
        self.is_active = True
        self.updated_at = datetime.now()
        logger.info(f"Activated program {self.code}")
    
    def deactivate_program(self) -> None:
        """
        Deactivate the program.
        """
        self.status = 'inactive'
        self.is_active = False
        self.updated_at = datetime.now()
        logger.info(f"Deactivated program {self.code}")
    
    def suspend_program(self, reason: str = "") -> None:
        """
        Suspend the program.
        
        Args:
            reason: Reason for suspension
        """
        self.status = 'suspended'
        if reason:
            self.metadata['suspension_reason'] = reason
        self.updated_at = datetime.now()
        logger.info(f"Suspended program {self.code} with reason: {reason}")
    
    def get_program_type(self) -> str:
        """
        Get program type.
        
        Returns:
            Program type string
        """
        if self.is_online_program:
            return 'online'
        elif self.is_joint_program:
            return 'joint'
        elif self.parent_program_id:
            return 'specialization'
        else:
            return 'regular'
    
    def get_accreditation_status_summary(self) -> str:
        """
        Get accreditation status summary.
        
        Returns:
            Accreditation status summary
        """
        if not self.accreditation_status:
            return 'not_accredited'
        
        if self.accreditation_status == 'accredited':
            if self.accreditation_expiry and datetime.now() < self.accreditation_expiry:
                return 'accredited'
            else:
                return 'accredited_expired'
        elif self.accreditation_status == 'provisional':
            return 'provisional'
        elif self.accreditation_status == 'not_accredited':
            return 'not_accredited'
        else:
            return 'pending'
    
    def is_open_for_admission(self) -> bool:
        """
        Check if program is open for admission.
        
        Returns:
            True if open for admission
        """
        if not self.is_active or not self.is_open_for_admission:
            return False
        
        # Check admission dates
        if self.admission_start_date and datetime.now() < self.admission_start_date:
            return False
        
        if self.admission_end_date and datetime.now() > self.admission_end_date:
            return False
        
        return True
    
    def has_capacity(self) -> bool:
        """
        Check if program has capacity.
        
        Returns:
            True if has capacity
        """
        return self.current_enrollment < self.max_capacity
    
    def get_enrollment_info(self) -> Dict[str, Any]:
        """
        Get enrollment information.
        
        Returns:
            Enrollment information dictionary
        """
        return {
            'max_capacity': self.max_capacity,
            'current_enrollment': self.current_enrollment,
            'available_capacity': self.max_capacity - self.current_enrollment,
            'enrollment_percentage': (self.current_enrollment / self.max_capacity * 100) if self.max_capacity > 0 else 0,
            'is_full': self.current_enrollment >= self.max_capacity,
            'is_open_for_admission': self.is_open_for_admission()
        }
    
    def get_program_summary(self) -> Dict[str, Any]:
        """
        Get program summary.
        
        Returns:
            Program summary dictionary
        """
        return {
            'id': self.id,
            'code': self.code,
            'name': self.name,
            'level': self.level,
            'duration_years': self.duration_years,
            'duration_months': self.duration_months,
            'total_credits': self.total_credits,
            'program_type': self.get_program_type(),
            'status': self.status,
            'is_active': self.is_active,
            'enrollment_info': self.get_enrollment_info(),
            'accreditation_status': self.get_accreditation_status_summary()
        }
    
    def __repr__(self) -> str:
        """String representation of the program model."""
        return f"<ProgramModel(code='{self.code}', name='{self.name}', level='{self.level}', status='{self.status}')>"