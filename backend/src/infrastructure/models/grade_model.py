"""
Grade Model for Database Operations

This module provides the SQLAlchemy model for Grade entity.
It includes all fields and relationships for academic grade management.

Author: Edu-Flow Team
"""

from typing import Dict, Any, Optional, List
from datetime import datetime
import logging

from sqlalchemy import Column, String, Integer, Text, DateTime, JSON, Boolean, ForeignKey, Float
from sqlalchemy.orm import relationship

from src.infrastructure.models.base_model import BaseModel
from src.core.exceptions import ValidationError
from src.core.logging import get_logger

logger = get_logger(__name__)


class GradeModel(BaseModel):
    """
    SQLAlchemy model for Grade entity.
    
    Represents academic grades for assessments, courses, and overall performance.
    """
    __tablename__ = "grades"
    
    # Grade identification
    id = Column(String(50), primary_key=True)
    code = Column(String(50), nullable=False, unique=True, index=True)
    grade_number = Column(Integer, nullable=False, index=True)  # Sequential grade number
    
    # Related entities
    student_id = Column(String(50), ForeignKey("users.id"), nullable=False)
    teacher_id = Column(String(50), ForeignKey("users.id"), nullable=False)
    subject_id = Column(String(50), ForeignKey("subjects.id"), nullable=False)
    class_id = Column(String(50), ForeignKey("classes.id"), nullable=False)
    assessment_id = Column(String(50), ForeignKey("assessments.id"))  # Optional, for assessment grades
    enrollment_id = Column(String(50), ForeignKey("enrollments.id"))  # Optional, for course grades
    
    # Grade details
    assessment_type = Column(String(50))  # quiz, assignment, exam, project, etc.
    category = Column(String(50), nullable=False)  # formative, summative, continuous, terminal
    academic_year = Column(String(10), nullable=False)  # 2023-2024
    semester = Column(Integer, nullable=False)  # Semester number
    batch = Column(String(20), nullable=False)  # A, B, C, etc.
    section = Column(String(5), nullable=False)  # 1, 2, 3, etc.
    
    # Grade information
    total_marks = Column(Integer, nullable=False)
    obtained_marks = Column(Integer, default=0)
    percentage = Column(Float, default=0.0)
    grade = Column(String(10), nullable=False)  # A, B, C, D, F, etc.
    grade_point = Column(Float, default=0.0)  # Grade points on a 4.0 scale
    gpa_contribution = Column(Float, default=0.0)  # GPA contribution from this grade
    
    # Grade details
    remarks = Column(Text)
    feedback = Column(Text)
    is_final = Column(Boolean, default=False)
    is_pass = Column(Boolean, default=True)  # Whether the grade is a passing grade
    
    # Grade metadata
    metadata = Column(JSON, default=dict)
    grade_history = Column(JSON, default=list)  # List of grade changes
    verification_status = Column(String(20), default="pending")  # pending, verified, disputed
    verification_notes = Column(Text)
    
    # Relationships
    student = relationship("UserModel", foreign_keys=[student_id])
    teacher = relationship("UserModel", foreign_keys=[teacher_id])
    subject = relationship("SubjectModel")
    class_model = relationship("ClassModel")
    assessment = relationship("AssessmentModel")
    enrollment = relationship("EnrollmentModel")
    
    def __init__(self, **kwargs):
        """Initialize the grade model with provided data."""
        # Set default values for optional fields
        kwargs.setdefault('obtained_marks', 0)
        kwargs.setdefault('percentage', 0.0)
        kwargs.setdefault('grade_point', 0.0)
        kwargs.setdefault('gpa_contribution', 0.0)
        kwargs.setdefault('is_final', False)
        kwargs.setdefault('is_pass', True)
        kwargs.setdefault('metadata', {})
        kwargs.setdefault('grade_history', [])
        kwargs.setdefault('verification_status', 'pending')
        
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
        if 'created_at' in data and isinstance(data['created_at'], datetime):
            data['created_at'] = data['created_at'].isoformat()
        else:
            data['created_at'] = datetime.now().isoformat()
        
        if 'updated_at' in data and isinstance(data['updated_at'], datetime):
            data['updated_at'] = data['updated_at'].isoformat()
        else:
            data['updated_at'] = datetime.now().isoformat()
        
        # Convert JSON fields to proper format
        if 'metadata' in data and isinstance(data['metadata'], dict):
            data['metadata'] = data['metadata']
        else:
            data['metadata'] = {}
        
        if 'grade_history' in data and isinstance(data['grade_history'], list):
            data['grade_history'] = data['grade_history']
        else:
            data['grade_history'] = []
        
        # Calculate derived fields
        data='performance_level'] = self.get_performance_level()
        data['grade_status'] = self.get_grade_status()
        data['is_verified'] = self.is_verified()
        data['is_disputed'] = self.is_disputed()
        data['can_modify'] = self.can_modify()
        data='grade_summary'] = self.get_grade_summary()
        
        # Include relationships if requested
        if include_relationships:
            if hasattr(self, 'student') and self.student:
                data['student'] = self.student.to_dict()
            else:
                data['student'] = None
            
            if hasattr(self, 'teacher') and self.teacher:
                data['teacher'] = self.teacher.to_dict()
            else:
                data['teacher'] = None
            
            if hasattr(self, 'subject') and self.subject:
                data['subject'] = self.subject.to_dict()
            else:
                data['subject'] = None
            
            if hasattr(self, 'class_model') and self.class_model:
                data['class_model'] = self.class_model.to_dict()
            else:
                data['class_model'] = None
            
            if hasattr(self, 'assessment') and self.assessment:
                data['assessment'] = self.assessment.to_dict()
            else:
                data['assessment'] = None
            
            if hasattr(self, 'enrollment') and self.enrollment:
                data['enrollment'] = self.enrollment.to_dict()
            else:
                data['enrollment'] = None
        
        return data
    
    def update(self, **kwargs) -> None:
        """Update the model with new data."""
        # Handle special field updates
        if 'metadata' in kwargs and isinstance(kwargs['metadata'], dict):
            self.metadata = kwargs['metadata']
        if 'grade_history' in kwargs and isinstance(kwargs['grade_history'], list):
            self.grade_history = kwargs['grade_history']
        
        super().update(**kwargs)
    
    def validate(self) -> bool:
        """
        Validate the grade model data.
        
        Returns:
            True if valid, False otherwise
            
        Raises:
            ValidationError: If validation fails
        """
        try:
            # Call base validation
            super().validate()
            
            # Grade-specific validations
            if not self.id:
                raise ValidationError("Grade ID is required")
            
            if not self.code:
                raise ValidationError("Grade code is required")
            
            if not self.student_id:
                raise ValidationError("Student ID is required")
            
            if not self.teacher_id:
                raise ValidationError("Teacher ID is required")
            
            if not self.subject_id:
                raise ValidationError("Subject ID is required")
            
            if not self.class_id:
                raise ValidationError("Class ID is required")
            
            if not self.category:
                raise ValidationError("Grade category is required")
            
            if not self.academic_year:
                raise ValidationError("Academic year is required")
            
            if not self.semester:
                raise ValidationError("Semester is required")
            
            if not self.batch:
                raise ValidationError("Batch is required")
            
            if not self.section:
                raise ValidationError("Section is required")
            
            if not self.grade:
                raise ValidationError("Grade is required")
            
            # Category validation
            valid_categories = ['formative', 'summative', 'continuous', 'terminal', 'mid_semester', 'end_semester']
            if self.category not in valid_categories:
                raise ValidationError(f"Invalid grade category: {self.category}")
            
            # Academic year validation
            if len(self.academic_year) != 9 or self.academic_year[4] != '-':  # 2023-2024
                raise ValidationError("Academic year must be in format YYYY-YYYY")
            
            # Semester validation
            if self.semester < 1:
                raise ValidationError("Semester must be positive")
            
            # Mark validations
            if self.total_marks <= 0:
                raise ValidationError("Total marks must be positive")
            
            if self.obtained_marks < 0:
                raise ValidationError("Obtained marks cannot be negative")
            
            if self.obtained_marks > self.total_marks:
                raise ValidationError("Obtained marks cannot exceed total marks")
            
            if self.percentage < 0 or self.percentage > 100:
                raise ValidationError("Percentage must be between 0 and 100")
            
            # Grade validation
            valid_grades = ['A', 'B', 'C', 'D', 'F', 'A+', 'A-', 'B+', 'B-', 'C+', 'C-', 'P', 'NP', 'Pass', 'Fail']
            if self.grade not in valid_grades:
                raise ValidationError(f"Invalid grade: {self.grade}")
            
            # Grade point validation
            if self.grade_point < 0 or self.grade_point > 4.0:
                raise ValidationError("Grade point must be between 0 and 4.0")
            
            if self.gpa_contribution < 0 or self.gpa_contribution > 4.0:
                raise ValidationError("GPA contribution must be between 0 and 4.0")
            
            # Status validation
            valid_verification_statuses = ['pending', 'verified', 'disputed']
            if self.verification_status not in valid_verification_statuses:
                raise ValidationError(f"Invalid verification status: {self.verification_status}")
            
            # JSON fields validation
            if not isinstance(self.metadata, dict):
                raise ValidationError("Metadata must be a dictionary")
            
            if not isinstance(self.grade_history, list):
                raise ValidationError("Grade history must be a list")
            
            logger.info(f"Grade {self.code} validation passed")
            return True
            
        except Exception as e:
            logger.error(f"Grade validation error: {str(e)}")
            raise ValidationError(f"Grade validation error: {str(e)}")
    
    def update_marks(self, obtained_marks: int, total_marks: int = None, 
                     teacher_id: str = None, reason: str = "") -> None:
        """
        Update marks and recalculate grade.
        
        Args:
            obtained_marks: New obtained marks
            total_marks: New total marks (optional)
            teacher_id: Teacher making the change (optional)
            reason: Reason for the change (optional)
        """
        if obtained_marks < 0:
            raise ValidationError("Obtained marks cannot be negative")
        
        if total_marks is not None:
            if total_marks <= 0:
                raise ValidationError("Total marks must be positive")
            self.total_marks = total_marks
        
        if obtained_marks > self.total_marks:
            raise ValidationError("Obtained marks cannot exceed total marks")
        
        # Update marks
        self.obtained_marks = obtained_marks
        
        # Calculate percentage
        self.percentage = (obtained_marks / self.total_marks) * 100 if self.total_marks > 0 else 0.0
        
        # Update grade based on percentage
        self.update_grade()
        
        # Update grade point and GPA contribution
        self.update_grade_point()
        
        # Record grade change in history
        self.record_grade_change(teacher_id, reason)
        
        # Update metadata
        self.metadata['last_updated_by'] = teacher_id
        self.metadata['last_updated_reason'] = reason
        self.metadata['last_updated_at'] = datetime.now().isoformat()
        
        self.updated_at = datetime.now()
        logger.info(f"Updated grade {self.code}: {obtained_marks}/{self.total_marks}")
    
    def update_grade(self) -> None:
        """Update grade based on percentage score."""
        if self.percentage >= 90:
            self.grade = 'A'
        elif self.percentage >= 80:
            self.grade = 'B'
        elif self.percentage >= 70:
            self.grade = 'C'
        elif self.percentage >= 60:
            self.grade = 'D'
        elif self.percentage >= 50:
            self.grade = 'Pass'
        else:
            self.grade = 'Fail'
        
        # Update pass/fail status
        self.is_pass = self.grade in ['A', 'B', 'C', 'D', 'P', 'Pass']
    
    def update_grade_point(self) -> None:
        """
        Update grade point and GPA contribution.
        """
        grade_to_point = {
            'A': 4.0, 'A+': 4.0, 'A-': 3.7,
            'B': 3.0, 'B+': 3.3, 'B-': 2.7,
            'C': 2.0, 'C+': 2.3, 'C-': 1.7,
            'D': 1.0, 'P': 3.0, 'NP': 0.0,
            'Pass': 3.0, 'Fail': 0.0
        }
        
        self.grade_point = grade_to_point.get(self.grade, 0.0)
        self.gpa_contribution = self.grade_point
    
    def record_grade_change(self, teacher_id: str = None, reason: str = "") -> None:
        """
        Record a change in grade history.
        
        Args:
            teacher_id: Teacher making the change (optional)
            reason: Reason for the change (optional)
        """
        change_record = {
            'timestamp': datetime.now().isoformat(),
            'teacher_id': teacher_id,
            'reason': reason,
            'total_marks': self.total_marks,
            'obtained_marks': self.obtained_marks,
            'percentage': self.percentage,
            'grade': self.grade,
            'grade_point': self.grade_point
        }
        
        self.grade_history.append(change_record)
        logger.info(f"Recorded grade change for grade {self.code}")
    
    def verify_grade(self, verifier_id: str, verification_notes: str = "") -> None:
        """
        Verify the grade.
        
        Args:
            verifier_id: ID of the verifier
            verification_notes: Notes about verification (optional)
        """
        self.verification_status = 'verified'
        self.metadata['verified_by'] = verifier_id
        self.metadata['verified_at'] = datetime.now().isoformat()
        
        if verification_notes:
            self.verification_notes = verification_notes
        
        self.updated_at = datetime.now()
        logger.info(f"Verified grade {self.code} by {verifier_id}")
    
    def dispute_grade(self, dispute_reason: str, student_id: str = None) -> None:
        """
        Dispute the grade.
        
        Args:
            dispute_reason: Reason for disputing
            student_id: ID of the student disputing (optional)
        """
        self.verification_status = 'disputed'
        self.metadata['disputed_by'] = student_id
        self.metadata['disputed_at'] = datetime.now().isoformat()
        self.metadata['dispute_reason'] = dispute_reason
        
        self.updated_at = datetime.now()
        logger.info(f"Disputed grade {self.code} with reason: {dispute_reason}")
    
    def resolve_dispute(self, resolution: str, resolver_id: str) -> None:
        """
        Resolve a grade dispute.
        
        Args:
            resolution: Resolution details
            resolver_id: ID of the resolver
        """
        if self.verification_status != 'disputed':
            raise ValidationError("Grade is not in dispute status")
        
        self.verification_status = 'verified'
        self.metadata['dispute_resolution'] = resolution
        self.metadata['resolved_by'] = resolver_id
        self.metadata['resolved_at'] = datetime.now().isoformat()
        
        self.updated_at = datetime.now()
        logger.info(f"Resolved dispute for grade {code}: {resolution}")
    
    def set_final(self, final_date: datetime = None) -> None:
        """
        Set the grade as final.
        
        Args:
            final_date: Date when grade became final (optional)
        """
        self.is_final = True
        if final_date:
            self.metadata['final_date'] = final_date.isoformat()
        else:
            self.metadata['final_date'] = datetime.now().isoformat()
        
        self.updated_at = datetime.now()
        logger.info(f"Set grade {self.code} as final")
    
    def add_feedback(self, feedback: str, teacher_id: str = None) -> None:
        """
        Add feedback to the grade.
        
        Args:
            feedback: Feedback text
            teacher_id: ID of the teacher providing feedback (optional)
        """
        self.feedback = feedback
        if teacher_id:
            self.metadata['feedback_by'] = teacher_id
            self.metadata['feedback_at'] = datetime.now().isoformat()
        
        self.updated_at = datetime.now()
        logger.info(f"Added feedback to grade {self.code}")
    
    def add_remarks(self, remarks: str) -> None:
        """
        Add remarks to the grade.
        
        Args:
            remarks: Remarks text
        """
        self.remarks = remarks
        self.updated_at = datetime.now()
        logger.info(f"Added remarks to grade {self.code}")
    
    def is_verified(self) -> bool:
        """
        Check if grade is verified.
        
        Returns:
            True if verified
        """
        return self.verification_status == 'verified'
    
    def is_disputed(self) -> bool:
        """
        Check if grade is disputed.
        
        Returns:
            True if disputed
        """
        return self.verification_status == 'disputed'
    
    def can_modify(self) -> bool:
        """
        Check if grade can be modified.
        
        Returns:
            True if grade can be modified
        """
        # Grade cannot be modified if it's final and verified
        if self.is_final and self.is_verified():
            return False
        
        # Grade can be modified if it's not final or not verified
        return True
    
    def get_performance_level(self) -> str:
        """
        Get performance level based on grade.
        
        Returns:
            Performance level string
        """
        grade_to_level = {
            'A': 'excellent', 'A+': 'excellent', 'A-': 'excellent',
            'B': 'good', 'B+': 'good', 'B-': 'good',
            'C': 'satisfactory', 'C+': 'satisfactory', 'C-': 'satisfactory',
            'D': 'needs_improvement',
            'F': 'poor', 'NP': 'poor', 'Fail': 'poor'
        }
        
        return grade_to_level.get(self.grade, 'unknown')
    
    def get_grade_status(self) -> str:
        """
        Get grade status.
        
        Returns:
            Grade status string
        """
        if self.is_final:
            return 'final'
        elif self.verification_status == 'disputed':
            return 'disputed'
        elif self.is_verified():
            return 'verified'
        else:
            return 'pending'
    
    def get_grade_summary(self) -> Dict[str, Any]:
        """
        Get grade summary.
        
        Returns:
            Grade summary dictionary
        """
        return {
            'id': self.id,
            'code': self.code,
            'grade': self.grade,
            'grade_point': self.grade_point,
            'total_marks': self.total_marks,
            'obtained_marks': self.obtained_marks,
            'percentage': self.percentage,
            'is_pass': self.is_pass,
            'is_final': self.is_final,
            'performance_level': self.get_performance_level(),
            'grade_status': self.get_grade_status(),
            'verification_status': self.verification_status,
            'category': self.category,
            'academic_year': self.academic_year,
            'semester': self.semester
        }
    
    def calculate_semester_gpa(self, credit_hours: int = 3) -> float:
        """
        Calculate GPA for this grade.
        
        Args:
            credit_hours: Credit hours for the course (default: 3)
            
        Returns:
            GPA for this grade
        """
        if credit_hours <= 0:
            raise ValidationError("Credit hours must be positive")
        
        return self.grade_point * credit_hours
    
    def __repr__(self) -> str:
        """String representation of the grade model."""
        return f"<GradeModel(code='{self.code}', grade='{self.grade}', student_id='{self.student_id}', subject_id='{self.subject_id}')>"