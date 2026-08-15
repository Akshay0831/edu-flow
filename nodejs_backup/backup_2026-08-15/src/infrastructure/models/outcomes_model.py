"""
Outcomes Model for Database Operations

This module provides the SQLAlchemy model for Outcomes entity.
It includes all fields and relationships for performance tracking and curriculum assessment.

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


class OutcomesModel(BaseModel):
    """
    SQLAlchemy model for Outcomes entity.
    
    Represents performance tracking, CO-PO mapping, and curriculum assessment outcomes.
    """
    __tablename__ = "outcomes"
    
    # Outcomes identification
    code = Column(String(50), nullable=False, index=True)
    name = Column(String(200), nullable=False, index=True)
    description = Column(Text)
    type = Column(String(50), nullable=False)  # course_outcome, program_outcome, graduate_attribute
    
    # Related entities
    subject_id = Column(String(50), ForeignKey("subjects.id"))  # Related subject for course outcomes
    program_id = Column(String(50), ForeignKey("programs.id"))  # Related program for program outcomes
    student_id = Column(String(50), ForeignKey("users.id"))  # Related student for individual outcomes
    
    # Assessment details
    assessment_type = Column(String(50), nullable=False)  # quiz, assignment, exam, project, presentation
    max_marks = Column(Integer, nullable=False, default=100)
    passing_marks = Column(Integer, default=40)
    weightage = Column(Integer, default=0)  # percentage in overall assessment
    
    # Performance metrics
    achieved_marks = Column(Integer, default=0)
    percentage_score = Column(Float, default=0.0)  # (achieved_marks / max_marks) * 100
    grade = Column(String(10))  # A, B, C, D, F, Pass, Fail, etc.
    status = Column(String(20), nullable=False, default="pending")  # pending, completed, graded, reviewed
    
    # CO-PO mapping
    course_outcome_code = Column(String(50))  # Related course outcome code
    program_outcome_code = Column(String(50))  # Related program outcome code
    mapping_strength = Column(Float, default=0.0)  # Mapping strength score (0-100)
    
    # Achievement analysis
    achievement_level = Column(String(20), default="not_achieved")  # not_achieved, partially_achieved, achieved, exceeded
    competency_score = Column(Float, default=0.0)  # Overall competency score
    improvement_areas = Column(Text)  # Areas for improvement
    
    # Time and tracking
    assessment_date = Column(DateTime)
    submitted_at = Column(DateTime)
    graded_at = Column(DateTime)
    reviewed_at = Column(DateTime)
    
    # Feedback and improvement
    feedback = Column(Text)
    reviewer_comments = Column(Text)
    improvement_actions = Column(Text)
    
    # Outcomes metadata
    metadata = Column(JSON, default=dict)
    notes = Column(Text)
    
    # Relationships
    subject = relationship("SubjectModel")
    program = relationship("ProgramModel")
    student = relationship("UserModel")
    assessments = relationship("AssessmentModel")
    mappings = relationship("OutcomeMappingModel")
    
    def __init__(self, **kwargs):
        """Initialize the outcomes model with provided data."""
        # Set default values for optional fields
        kwargs.setdefault('max_marks', 100)
        kwargs.setdefault('passing_marks', 40)
        kwargs.setdefault('weightage', 0)
        kwargs.setdefault('achieved_marks', 0)
        kwargs.setdefault('percentage_score', 0.0)
        kwargs.setdefault('grade', None)
        kwargs.setdefault('status', 'pending')
        kwargs.setdefault('mapping_strength', 0.0)
        kwargs.setdefault('achievement_level', 'not_achieved')
        kwargs.setdefault('competency_score', 0.0)
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
        
        # Convert date fields to ISO format
        if 'assessment_date' in data and isinstance(data['assessment_date'], datetime):
            data['assessment_date'] = data['assessment_date'].isoformat()
        else:
            data['assessment_date'] = None
        
        if 'submitted_at' in data and isinstance(data['submitted_at'], datetime):
            data['submitted_at'] = data['submitted_at'].isoformat()
        else:
            data['submitted_at'] = None
        
        if 'graded_at' in data and isinstance(data['graded_at'], datetime):
            data['graded_at'] = data['graded_at'].isoformat()
        else:
            data['graded_at'] = None
        
        if 'reviewed_at' in data and isinstance(data['reviewed_at'], datetime):
            data['reviewed_at'] = data['reviewed_at'].isoformat()
        else:
            data['reviewed_at'] = None
        
        # Convert JSON fields to proper format
        if 'metadata' in data and isinstance(data['metadata'], dict):
            data['metadata'] = data['metadata']
        else:
            data['metadata'] = {}
        
        # Calculate derived fields
        data['is_pass'] = self.achieved_marks >= self.passing_marks if self.max_marks > 0 else False
        data['performance_level'] = self.get_performance_level()
        data['achievement_status'] = self.achievement_level
        
        # Include relationships if requested
        if include_relationships:
            if hasattr(self, 'subject') and self.subject:
                data['subject'] = self.subject.to_dict()
            else:
                data['subject'] = None
            
            if hasattr(self, 'program') and self.program:
                data['program'] = self.program.to_dict()
            else:
                data['program'] = None
            
            if hasattr(self, 'student') and self.student:
                data['student'] = self.student.to_dict()
            else:
                data['student'] = None
            
            if hasattr(self, 'assessments') and self.assessments:
                data['assessments'] = [assessment.to_dict() for assessment in self.assessments]
            else:
                data['assessments'] = []
            
            if hasattr(self, 'mappings') and self.mappings:
                data['mappings'] = [mapping.to_dict() for mapping in self.mappings]
            else:
                data['mappings'] = []
        
        return data
    
    def update(self, **kwargs) -> None:
        """Update the model with new data."""
        # Handle special field updates
        if 'metadata' in kwargs and isinstance(kwargs['metadata'], dict):
            self.metadata = kwargs['metadata']
        
        super().update(**kwargs)
    
    def validate(self) -> bool:
        """
        Validate the outcomes model data.
        
        Returns:
            True if valid, False otherwise
            
        Raises:
            ValidationError: If validation fails
        """
        try:
            # Call base validation
            super().validate()
            
            # Outcomes-specific validations
            if not self.code:
                raise ValidationError("Outcome code is required")
            
            if not self.name:
                raise ValidationError("Outcome name is required")
            
            if not self.type:
                raise ValidationError("Outcome type is required")
            
            if not self.assessment_type:
                raise ValidationError("Assessment type is required")
            
            # Score validations
            if self.max_marks <= 0:
                raise ValidationError("Max marks must be positive")
            
            if self.passing_marks < 0:
                raise ValidationError("Passing marks cannot be negative")
            
            if self.passing_marks > self.max_marks:
                raise ValidationError("Passing marks cannot exceed max marks")
            
            if self.achieved_marks < 0:
                raise ValidationError("Achieved marks cannot be negative")
            
            if self.achieved_marks > self.max_marks:
                raise ValidationError("Achieved marks cannot exceed max marks")
            
            if self.weightage < 0 or self.weightage > 100:
                raise ValidationError("Weightage must be between 0 and 100")
            
            if self.mapping_strength < 0 or self.mapping_strength > 100:
                raise ValidationError("Mapping strength must be between 0 and 100")
            
            if self.competency_score < 0 or self.competency_score > 100:
                raise ValidationError("Competency score must be between 0 and 100")
            
            # Percentage score calculation
            if self.max_marks > 0:
                expected_percentage = (self.achieved_marks / self.max_marks) * 100
                # Allow small floating point differences
                if abs(self.percentage_score - expected_percentage) > 0.01:
                    self.percentage_score = expected_percentage
            
            # Grade validation
            if self.grade:
                valid_grades = ['A', 'B', 'C', 'D', 'F', 'Pass', 'Fail', 'A+', 'A-', 'B+', 'B-', 'C+', 'C-', 'P', 'NP']
                if self.grade not in valid_grades:
                    raise ValidationError(f"Invalid grade: {self.grade}")
            
            # Status validation
            valid_statuses = ['pending', 'completed', 'graded', 'reviewed']
            if self.status not in valid_statuses:
                raise ValidationError(f"Invalid status: {self.status}")
            
            # Type validation
            valid_types = ['course_outcome', 'program_outcome', 'graduate_attribute']
            if self.type not in valid_types:
                raise ValidationError(f"Invalid outcome type: {self.type}")
            
            # Achievement level validation
            valid_achievement_levels = ['not_achieved', 'partially_achieved', 'achieved', 'exceeded']
            if self.achievement_level not in valid_achievement_levels:
                raise ValidationError(f"Invalid achievement level: {self.achievement_level}")
            
            # Assessment type validation
            valid_assessment_types = ['quiz', 'assignment', 'exam', 'project', 'presentation', 'practical', 'viva']
            if self.assessment_type not in valid_assessment_types:
                raise ValidationError(f"Invalid assessment type: {self.assessment_type}")
            
            logger.info(f"Outcome {self.code} validation passed")
            return True
            
        except Exception as e:
            logger.error(f"Outcome validation error: {str(e)}")
            raise ValidationError(f"Outcome validation error: {str(e)}")
    
    def update_marks(self, achieved_marks: int, max_marks: int = None) -> None:
        """
        Update achieved marks and recalculate percentage.
        
        Args:
            achieved_marks: New achieved marks
            max_marks: Maximum marks (optional, uses existing if not provided)
        """
        if achieved_marks < 0:
            raise ValidationError("Achieved marks cannot be negative")
        
        if max_marks is not None:
            if max_marks <= 0:
                raise ValidationError("Max marks must be positive")
            self.max_marks = max_marks
        
        if achieved_marks > self.max_marks:
            raise ValidationError("Achieved marks cannot exceed max marks")
        
        self.achieved_marks = achieved_marks
        self.percentage_score = (achieved_marks / self.max_marks) * 100 if self.max_marks > 0 else 0.0
        self.updated_at = datetime.now()
        
        # Update grade based on marks
        self.update_grade()
        
        # Update achievement level
        self.update_achievement_level()
        
        logger.info(f"Updated marks for outcome {self.code}: {achieved_marks}/{self.max_marks}")
    
    def update_grade(self) -> None:
        """Update grade based on percentage score."""
        if self.percentage_score >= 90:
            self.grade = 'A'
        elif self.percentage_score >= 80:
            self.grade = 'B'
        elif self.percentage_score >= 70:
            self.grade = 'C'
        elif self.percentage_score >= 60:
            self.grade = 'D'
        elif self.percentage_score >= self.passing_marks:
            self.grade = 'Pass'
        else:
            self.grade = 'Fail'
    
    def update_achievement_level(self) -> None:
        """Update achievement level based on percentage score."""
        if self.percentage_score >= 100:
            self.achievement_level = 'exceeded'
        elif self.percentage_score >= 80:
            self.achievement_level = 'achieved'
        elif self.percentage_score >= 60:
            self.achievement_level = 'partially_achieved'
        else:
            self.achievement_level = 'not_achieved'
    
    def set_mapping(self, course_outcome_code: str = None, program_outcome_code: str = None, 
                   mapping_strength: float = None) -> None:
        """
        Set CO-PO mapping.
        
        Args:
            course_outcome_code: Related course outcome code
            program_outcome_code: Related program outcome code
            mapping_strength: Mapping strength score
        """
        if course_outcome_code:
            self.course_outcome_code = course_outcome_code
        if program_outcome_code:
            self.program_outcome_code = program_outcome_code
        if mapping_strength is not None:
            if mapping_strength < 0 or mapping_strength > 100:
                raise ValidationError("Mapping strength must be between 0 and 100")
            self.mapping_strength = mapping_strength
        
        self.updated_at = datetime.now()
        logger.info(f"Updated CO-PO mapping for outcome {self.code}")
    
    def submit_assessment(self, assessment_date: datetime = None) -> None:
        """
        Submit the assessment.
        
        Args:
            assessment_date: Assessment date (optional)
        """
        self.submitted_at = assessment_date or datetime.now()
        self.status = 'completed'
        self.updated_at = datetime.now()
        logger.info(f"Submitted assessment for outcome {self.code}")
    
    def grade_assessment(self, grade: str, achieved_marks: int = None, graded_at: datetime = None) -> None:
        """
        Grade the assessment.
        
        Args:
            grade: Grade to assign
            achieved_marks: Achieved marks (optional)
            graded_at: Graded date (optional)
        """
        if achieved_marks is not None:
            self.update_marks(achieved_marks)
        
        self.grade = grade
        self.graded_at = graded_at or datetime.now()
        self.status = 'graded'
        self.updated_at = datetime.now()
        logger.info(f"Graded assessment for outcome {self.code} with grade {grade}")
    
    def review_assessment(self, reviewer_comments: str, competency_score: float = None, 
                         reviewed_at: datetime = None) -> None:
        """
        Review the assessment.
        
        Args:
            reviewer_comments: Comments from reviewer
            competency_score: Competency score (optional)
            reviewed_at: Reviewed date (optional)
        """
        self.reviewer_comments = reviewer_comments
        
        if competency_score is not None:
            if competency_score < 0 or competency_score > 100:
                raise ValidationError("Competency score must be between 0 and 100")
            self.competency_score = competency_score
        
        self.reviewed_at = reviewed_at or datetime.now()
        self.status = 'reviewed'
        self.updated_at = datetime.now()
        logger.info(f"Reviewed assessment for outcome {self.code}")
    
    def add_feedback(self, feedback: str) -> None:
        """
        Add feedback.
        
        Args:
            feedback: Feedback text
        """
        self.feedback = feedback
        self.updated_at = datetime.now()
        logger.info(f"Added feedback for outcome {self.code}")
    
    def add_improvement_actions(self, actions: str) -> None:
        """
        Add improvement actions.
        
        Args:
            actions: Improvement actions text
        """
        self.improvement_actions = actions
        self.updated_at = datetime.now()
        logger.info(f"Added improvement actions for outcome {self.code}")
    
    def get_performance_level(self) -> str:
        """
        Get performance level based on percentage score.
        
        Returns:
            Performance level string
        """
        if self.percentage_score >= 90:
            return 'excellent'
        elif self.percentage_score >= 80:
            return 'good'
        elif self.percentage_score >= 70:
            return 'satisfactory'
        elif self.percentage_score >= 60:
            return 'needs_improvement'
        else:
            return 'poor'
    
    def get_achievement_rate(self) -> float:
        """
        Get achievement rate.
        
        Returns:
            Achievement rate percentage
        """
        if self.max_marks > 0:
            return self.percentage_score
        return 0.0
    
    def is_pass(self) -> bool:
        """
        Check if outcome is pass.
        
        Returns:
            True if pass
        """
        return self.achieved_marks >= self.passing_marks
    
    def is_completed(self) -> bool:
        """
        Check if outcome is completed.
        
        Returns:
            True if completed
        """
        return self.status == 'completed'
    
    def is_graded(self) -> bool:
        """
        Check if outcome is graded.
        
        Returns:
            True if graded
        """
        return self.status == 'graded'
    
    def is_reviewed(self) -> bool:
        """
        Check if outcome is reviewed.
        
        Returns:
            True if reviewed
        """
        return self.status == 'reviewed'
    
    def get_assessment_summary(self) -> Dict[str, Any]:
        """
        Get assessment summary.
        
        Returns:
            Assessment summary dictionary
        """
        return {
            'code': self.code,
            'name': self.name,
            'assessment_type': self.assessment_type,
            'max_marks': self.max_marks,
            'achieved_marks': self.achieved_marks,
            'percentage_score': self.percentage_score,
            'grade': self.grade,
            'passing_marks': self.passing_marks,
            'is_pass': self.is_pass(),
            'status': self.status,
            'performance_level': self.get_performance_level(),
            'achievement_level': self.achievement_level
        }
    
    def get_mapping_info(self) -> Dict[str, Any]:
        """
        Get mapping information.
        
        Returns:
            Mapping information dictionary
        """
        return {
            'course_outcome_code': self.course_outcome_code,
            'program_outcome_code': self.program_outcome_code,
            'mapping_strength': self.mapping_strength,
            'mapping_quality': 'strong' if self.mapping_strength >= 70 else 'medium' if self.mapping_strength >= 40 else 'weak'
        }
    
    def __repr__(self) -> str:
        """String representation of the outcomes model."""
        return f"<OutcomesModel(code='{self.code}', name='{self.name}', type='{self.type}', status='{self.status}')>"