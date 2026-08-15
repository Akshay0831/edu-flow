"""
Assessment Model for Database Operations

This module provides the SQLAlchemy model for Assessment entity.
It includes all fields and relationships for academic assessment management.

Author: Edu-Flow Team
"""

from typing import Dict, Any, Optional, List
from datetime import datetime, timedelta
import logging

from sqlalchemy import Column, String, Integer, Text, DateTime, JSON, Boolean, ForeignKey, Float
from sqlalchemy.orm import relationship

from src.infrastructure.models.base_model import BaseModel
from src.core.exceptions import ValidationError
from src.core.logging import get_logger

logger = get_logger(__name__)


class AssessmentModel(BaseModel):
    """
    SQLAlchemy model for Assessment entity.
    
    Represents academic assessments with grading, submission tracking, and evaluation.
    """
    __tablename__ = "assessments"
    
    # Assessment identification
    id = Column(String(50), primary_key=True)
    code = Column(String(50), nullable=False, unique=True, index=True)
    title = Column(String(200), nullable=False, index=True)
    description = Column(Text)
    
    # Assessment categorization
    type = Column(String(50), nullable=False)  # quiz, assignment, exam, project, presentation, practical
    category = Column(String(50), nullable=False)  # formative, summative, continuous, terminal
    subcategory = Column(String(50))  # mid_semester, end_semester, weekly, monthly
    
    # Related entities
    subject_id = Column(String(50), ForeignKey("subjects.id"), nullable=False)
    class_id = Column(String(50), ForeignKey("classes.id"), nullable=False)
    teacher_id = Column(String(50), ForeignKey("users.id"), nullable=False)
    student_id = Column(String(50), ForeignKey("users.id"))  # For individual assessments
    
    # Assessment details
    total_marks = Column(Integer, nullable=False, default=100)
    passing_marks = Column(Integer, default=40)
    weightage = Column(Integer, default=0)  # percentage in overall assessment
    duration_minutes = Column(Integer, default=0)  # Assessment duration in minutes
    max_attempts = Column(Integer, default=1)  # Maximum number of attempts
    
    # Scheduling and timeline
    start_date = Column(DateTime, nullable=False)
    end_date = Column(DateTime, nullable=False)
    submission_start_date = Column(DateTime)
    submission_end_date = Column(DateTime)
    grading_deadline = Column(DateTime)
    results_release_date = Column(DateTime)
    
    # Assessment content
    content = Column(Text)  # Assessment content/description
    instructions = Column(Text)  # Instructions for the assessment
    rubric = Column(Text)  # Grading rubric
    syllabus_coverage = Column(JSON, default=list)  # Topics covered
    learning_objectives = Column(JSON, default=list)  # Learning objectives assessed
    
    # Assessment configuration
    is_timed = Column(Boolean, default=False)
    is_auto_graded = Column(Boolean, default=False)
    is_mandatory = Column(Boolean, default=True)
    allow_late_submission = Column(Boolean, default=False)
    show_results_immediately = Column(Boolean, default=False)
    
    # Submission and evaluation
    submission_status = Column(String(20), default="not_submitted")  # not_submitted, submitted, graded, reviewed
    submission_date = Column(DateTime)
    submitted_file_path = Column(String(200))
    evaluation_status = Column(String(20), default="not_evaluated")  # not_evaluated, in_progress, evaluated, reevaluated
    
    # Grading information
    obtained_marks = Column(Integer, default=0)
    percentage_score = Column(Float, default=0.0)
    grade = Column(String(10))  # A, B, C, D, F, etc.
    feedback = Column(Text)
    reviewer_comments = Column(Text)
    evaluation_date = Column(DateTime)
    
    # Statistics and analytics
    average_marks = Column(Float, default=0.0)
    highest_marks = Column(Integer, default=0)
    lowest_marks = Column(Integer, default=0)
    pass_percentage = Column(Float, default=0.0)
    submission_rate = Column(Float, default=0.0)
    
    # Assessment metadata
    metadata = Column(JSON, default=dict)
    attachments = Column(JSON, default=list)  # List of attachment paths/URLs
    tags = Column(JSON, default=list)  # List of tags for categorization
    
    # Relationships
    subject = relationship("SubjectModel")
    class_model = relationship("ClassModel")
    teacher = relationship("UserModel", foreign_keys=[teacher_id])
    student = relationship("UserModel", foreign_keys=[student_id])
    submissions = relationship("AssessmentSubmissionModel")
    grades = relationship("GradeModel")
    
    def __init__(self, **kwargs):
        """Initialize the assessment model with provided data."""
        # Set default values for optional fields
        kwargs.setdefault('total_marks', 100)
        kwargs.setdefault('passing_marks', 40)
        kwargs.setdefault('weightage', 0)
        kwargs.setdefault('duration_minutes', 0)
        kwargs.setdefault('max_attempts', 1)
        kwargs.setdefault('start_date', datetime.now())
        kwargs.setdefault('end_date', datetime.now())
        kwargs.setdefault('submission_status', 'not_submitted')
        kwargs.setdefault('evaluation_status', 'not_evaluated')
        kwargs.setdefault('obtained_marks', 0)
        kwargs.setdefault('percentage_score', 0.0)
        kwargs.setdefault('is_timed', False)
        kwargs.setdefault('is_auto_graded', False)
        kwargs.setdefault('is_mandatory', True)
        kwargs.setdefault('allow_late_submission', False)
        kwargs.setdefault('show_results_immediately', False)
        kwargs.setdefault('average_marks', 0.0)
        kwargs.setdefault('highest_marks', 0)
        kwargs.setdefault('lowest_marks', 0)
        kwargs.setdefault('pass_percentage', 0.0)
        kwargs.setdefault('submission_rate', 0.0)
        kwargs.setdefault('syllabus_coverage', [])
        kwargs.setdefault('learning_objectives', [])
        kwargs.setdefault('metadata', {})
        kwargs.setdefault('attachments', [])
        kwargs.setdefault('tags', [])
        
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
        if 'start_date' in data and isinstance(data['start_date'], datetime):
            data['start_date'] = data['start_date'].isoformat()
        else:
            data['start_date'] = datetime.now().isoformat()
        
        if 'end_date' in data and isinstance(data['end_date'], datetime):
            data['end_date'] = data['end_date'].isoformat()
        else:
            data['end_date'] = datetime.now().isoformat()
        
        if 'submission_start_date' in data and isinstance(data['submission_start_date'], datetime):
            data['submission_start_date'] = data['submission_start_date'].isoformat()
        else:
            data['submission_start_date'] = None
        
        if 'submission_end_date' in data and isinstance(data['submission_end_date'], datetime):
            data['submission_end_date'] = data['submission_end_date'].isoformat()
        else:
            data['submission_end_date'] = None
        
        if 'grading_deadline' in data and isinstance(data['grading_deadline'], datetime):
            data['grading_deadline'] = data['grading_deadline'].isoformat()
        else:
            data['grading_deadline'] = None
        
        if 'results_release_date' in data and isinstance(data['results_release_date'], datetime):
            data['results_release_date'] = data['results_release_date'].isoformat()
        else:
            data['results_release_date'] = None
        
        if 'submission_date' in data and isinstance(data['submission_date'], datetime):
            data['submission_date'] = data['submission_date'].isoformat()
        else:
            data['submission_date'] = None
        
        if 'evaluation_date' in data and isinstance(data['evaluation_date'], datetime):
            data['evaluation_date'] = data['evaluation_date'].isoformat()
        else:
            data['evaluation_date'] = None
        
        # Convert JSON fields to proper format
        if 'syllabus_coverage' in data and isinstance(data['syllabus_coverage'], list):
            data['syllabus_coverage'] = data['syllabus_coverage']
        else:
            data['syllabus_coverage'] = []
        
        if 'learning_objectives' in data and isinstance(data['learning_objectives'], list):
            data['learning_objectives'] = data['learning_objectives']
        else:
            data['learning_objectives'] = []
        
        if 'metadata' in data and isinstance(data['metadata'], dict):
            data['metadata'] = data['metadata']
        else:
            data['metadata'] = {}
        
        if 'attachments' in data and isinstance(data['attachments'], list):
            data['attachments'] = data['attachments']
        else:
            data['attachments'] = []
        
        if 'tags' in data and isinstance(data['tags'], list):
            data['tags'] = data['tags']
        else:
            data['tags'] = []
        
        # Calculate derived fields
        data='is_active'] = self.is_active()
        data['is_overdue'] = self.is_overdue()
        data='is_submitted'] = self.is_submitted()
        data['is_graded'] = self.is_graded()
        data='is_late_submission'] = self.is_late_submission()
        data='days_until_deadline'] = self.get_days_until_deadline()
        data['can_submit'] = self.can_submit()
        data['can_view_results'] = self.can_view_results()
        data='pass_status'] = self.get_pass_status()
        data['performance_level'] = self.get_performance_level()
        data['assessment_summary'] = self.get_assessment_summary()
        
        # Include relationships if requested
        if include_relationships:
            if hasattr(self, 'subject') and self.subject:
                data['subject'] = self.subject.to_dict()
            else:
                data['subject'] = None
            
            if hasattr(self, 'class_model') and self.class_model:
                data['class_model'] = self.class_model.to_dict()
            else:
                data['class_model'] = None
            
            if hasattr(self, 'teacher') and self.teacher:
                data['teacher'] = self.teacher.to_dict()
            else:
                data['teacher'] = None
            
            if hasattr(self, 'student') and self.student:
                data['student'] = self.student.to_dict()
            else:
                data['student'] = None
            
            if hasattr(self, 'submissions') and self.submissions:
                data['submissions'] = [submission.to_dict() for submission in self.submissions]
            else:
                data['submissions'] = []
            
            if hasattr(self, 'grades') and self.grades:
                data['grades'] = [grade.to_dict() for grade in self.grades]
            else:
                data['grades'] = []
        
        return data
    
    def update(self, **kwargs) -> None:
        """Update the model with new data."""
        # Handle special field updates
        if 'syllabus_coverage' in kwargs and isinstance(kwargs['syllabus_coverage'], list):
            self.syllabus_coverage = kwargs['syllabus_coverage']
        if 'learning_objectives' in kwargs and isinstance(kwargs['learning_objectives'], list):
            self.learning_objectives = kwargs['learning_objectives']
        if 'metadata' in kwargs and isinstance(kwargs['metadata'], dict):
            self.metadata = kwargs['metadata']
        if 'attachments' in kwargs and isinstance(kwargs['attachments'], list):
            self.attachments = kwargs['attachments']
        if 'tags' in kwargs and isinstance(kwargs['tags'], list):
            self.tags = kwargs['tags']
        
        super().update(**kwargs)
    
    def validate(self) -> bool:
        """
        Validate the assessment model data.
        
        Returns:
            True if valid, False otherwise
            
        Raises:
            ValidationError: If validation fails
        """
        try:
            # Call base validation
            super().validate()
            
            # Assessment-specific validations
            if not self.id:
                raise ValidationError("Assessment ID is required")
            
            if not self.code:
                raise ValidationError("Assessment code is required")
            
            if not self.title:
                raise ValidationError("Assessment title is required")
            
            if not self.type:
                raise ValidationError("Assessment type is required")
            
            if not self.category:
                raise ValidationError("Assessment category is required")
            
            if not self.subject_id:
                raise ValidationError("Subject ID is required")
            
            if not self.class_id:
                raise ValidationError("Class ID is required")
            
            if not self.teacher_id:
                raise ValidationError("Teacher ID is required")
            
            # Type validation
            valid_types = ['quiz', 'assignment', 'exam', 'project', 'presentation', 'practical', 'viva']
            if self.type not in valid_types:
                raise ValidationError(f"Invalid assessment type: {self.type}")
            
            # Category validation
            valid_categories = ['formative', 'summative', 'continuous', 'terminal']
            if self.category not in valid_categories:
                raise ValidationError(f"Invalid assessment category: {self.category}")
            
            # Mark validations
            if self.total_marks <= 0:
                raise ValidationError("Total marks must be positive")
            
            if self.passing_marks < 0:
                raise ValidationError("Passing marks cannot be negative")
            
            if self.passing_marks > self.total_marks:
                raise ValidationError("Passing marks cannot exceed total marks")
            
            if self.obtained_marks < 0:
                raise ValidationError("Obtained marks cannot be negative")
            
            if self.obtained_marks > self.total_marks:
                raise ValidationError("Obtained marks cannot exceed total marks")
            
            if self.weightage < 0 or self.weightage > 100:
                raise ValidationError("Weightage must be between 0 and 100")
            
            if self.percentage_score < 0 or self.percentage_score > 100:
                raise ValidationError("Percentage score must be between 0 and 100")
            
            if self.duration_minutes < 0:
                raise ValidationError("Duration minutes cannot be negative")
            
            if self.max_attempts < 1:
                raise ValidationError("Max attempts must be at least 1")
            
            # Date validations
            if self.start_date > self.end_date:
                raise ValidationError("Start date must be before end date")
            
            if self.submission_start_date and self.submission_start_date < self.start_date:
                raise ValidationError("Submission start date must be after assessment start date")
            
            if self.submission_end_date and self.submission_end_date < self.start_date:
                raise ValidationError("Submission end date must be after assessment start date")
            
            if self.grading_deadline and self.grading_deadline < self.start_date:
                raise ValidationError("Grading deadline must be after assessment start date")
            
            if self.results_release_date and self.results_release_date < self.start_date:
                raise ValidationError("Results release date must be after assessment start date")
            
            # Status validations
            valid_submission_statuses = ['not_submitted', 'submitted', 'graded', 'reviewed']
            if self.submission_status not in valid_submission_statuses:
                raise ValidationError(f"Invalid submission status: {self.submission_status}")
            
            valid_evaluation_statuses = ['not_evaluated', 'in_progress', 'evaluated', 'reevaluated']
            if self.evaluation_status not in valid_evaluation_statuses:
                raise ValidationError(f"Invalid evaluation status: {self.evaluation_status}")
            
            # Grade validation
            if self.grade:
                valid_grades = ['A', 'B', 'C', 'D', 'F', 'A+', 'A-', 'B+', 'B-', 'C+', 'C-', 'P', 'NP', 'Pass', 'Fail']
                if self.grade not in valid_grades:
                    raise ValidationError(f"Invalid grade: {self.grade}")
            
            # JSON fields validation
            if not isinstance(self.syllabus_coverage, list):
                raise ValidationError("Syllabus coverage must be a list")
            
            if not isinstance(self.learning_objectives, list):
                raise ValidationError("Learning objectives must be a list")
            
            if not isinstance(self.metadata, dict):
                raise ValidationError("Metadata must be a dictionary")
            
            if not isinstance(self.attachments, list):
                raise ValidationError("Attachments must be a list")
            
            if not isinstance(self.tags, list):
                raise ValidationError("Tags must be a list")
            
            logger.info(f"Assessment {self.code} validation passed")
            return True
            
        except Exception as e:
            logger.error(f"Assessment validation error: {str(e)}")
            raise ValidationError(f"Assessment validation error: {str(e)}")
    
    def submit_assessment(self, student_id: str, obtained_marks: int = None, 
                         submission_date: datetime = None, file_path: str = None) -> None:
        """
        Submit assessment.
        
        Args:
            student_id: Student ID submitting the assessment
            obtained_marks: Marks obtained (optional)
            submission_date: Submission date (optional)
            file_path: File path of submission (optional)
        """
        if not student_id:
            raise ValidationError("Student ID is required")
        
        # Check if submission is allowed
        if not self.can_submit():
            raise ValidationError("Assessment cannot be submitted at this time")
        
        self.student_id = student_id
        self.submission_date = submission_date or datetime.now()
        self.submission_status = 'submitted'
        
        if file_path:
            self.submitted_file_path = file_path
        
        if obtained_marks is not None:
            self.update_marks(obtained_marks)
        
        self.updated_at = datetime.now()
        logger.info(f"Assessment {self.code} submitted by student {student_id}")
    
    def update_marks(self, obtained_marks: int) -> None:
        """
        Update obtained marks and recalculate percentage.
        
        Args:
            obtained_marks: New obtained marks
        """
        if obtained_marks < 0:
            raise ValidationError("Obtained marks cannot be negative")
        
        if obtained_marks > self.total_marks:
            raise ValidationError("Obtained marks cannot exceed total marks")
        
        self.obtained_marks = obtained_marks
        self.percentage_score = (obtained_marks / self.total_marks) * 100 if self.total_marks > 0 else 0.0
        self.updated_at = datetime.now()
        
        # Update grade based on marks
        self.update_grade()
        
        logger.info(f"Updated marks for assessment {self.code}: {obtained_marks}/{self.total_marks}")
    
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
    
    def grade_assessment(self, evaluator_id: str, obtained_marks: int = None, 
                         feedback: str = None, evaluation_date: datetime = None) -> None:
        """
        Grade the assessment.
        
        Args:
            evaluator_id: ID of the evaluator
            obtained_marks: Marks obtained (optional)
            feedback: Feedback text (optional)
            evaluation_date: Evaluation date (optional)
        """
        if evaluator_id:
            # In practice, this would reference a User model
            self.metadata['evaluator_id'] = evaluator_id
        
        if obtained_marks is not None:
            self.update_marks(obtained_marks)
        
        if feedback:
            self.feedback = feedback
        
        self.evaluation_date = evaluation_date or datetime.now()
        self.submission_status = 'graded'
        self.evaluation_status = 'evaluated'
        self.updated_at = datetime.now()
        logger.info(f"Graded assessment {self.code}")
    
    def add_feedback(self, feedback: str) -> None:
        """
        Add feedback to the assessment.
        
        Args:
            feedback: Feedback text
        """
        self.feedback = feedback
        self.updated_at = datetime.now()
        logger.info(f"Added feedback to assessment {self.code}")
    
    def add_attachment(self, attachment_path: str, attachment_type: str = "file") -> None:
        """
        Add an attachment to the assessment.
        
        Args:
            attachment_path: Path or URL to the attachment
            attachment_type: Type of attachment (file, image, document, etc.)
        """
        attachment_data = {
            'path': attachment_path,
            'type': attachment_type,
            'uploaded_at': datetime.now().isoformat()
        }
        
        self.attachments.append(attachment_data)
        self.updated_at = datetime.now()
        logger.info(f"Added attachment to assessment {self.code}: {attachment_path}")
    
    def start_grading(self) -> None:
        """
        Start grading process.
        """
        self.evaluation_status = 'in_progress'
        self.updated_at = datetime.now()
        logger.info(f"Started grading process for assessment {self.code}")
    
    def complete_grading(self) -> None:
        """
        Complete grading process.
        """
        self.evaluation_status = 'evaluated'
        self.updated_at = datetime.now()
        logger.info(f"Completed grading process for assessment {self.code}")
    
    def reevaluate_assessment(self, reason: str = "") -> None:
        """
        Re-evaluate the assessment.
        
        Args:
            reason: Reason for re-evaluation
        """
        self.evaluation_status = 'reevaluated'
        if reason:
            self.metadata['reevaluation_reason'] = reason
        self.updated_at = datetime.now()
        logger.info(f"Re-evaluated assessment {self.code} with reason: {reason}")
    
    def update_statistics(self, **stats) -> None:
        """
        Update assessment statistics.
        
        Args:
            **stats: Statistics to update
        """
        if 'average_marks' in stats:
            self.average_marks = stats['average_marks']
        if 'highest_marks' in stats:
            self.highest_marks = stats['highest_marks']
        if 'lowest_marks' in stats:
            self.lowest_marks = stats['lowest_marks']
        if 'pass_percentage' in stats:
            self.pass_percentage = stats['pass_percentage']
        if 'submission_rate' in stats:
            self.submission_rate = stats['submission_rate']
        
        self.updated_at = datetime.now()
        logger.info(f"Updated statistics for assessment {self.code}")
    
    def is_active(self) -> bool:
        """
        Check if assessment is active.
        
        Returns:
            True if assessment is active
        """
        now = datetime.now()
        return self.start_date <= now <= self.end_date
    
    def is_overdue(self) -> bool:
        """
        Check if assessment is overdue.
        
        Returns:
            True if assessment is overdue
        """
        if self.submission_end_date and datetime.now() > self.submission_end_date:
            return True
        return False
    
    def is_submitted(self) -> bool:
        """
        Check if assessment is submitted.
        
        Returns:
            True if submitted
        """
        return self.submission_status == 'submitted'
    
    def is_graded(self) -> bool:
        """
        Check if assessment is graded.
        
        Returns:
            True if graded
        """
        return self.submission_status == 'graded'
    
    def is_late_submission(self) -> bool:
        """
        Check if submission is late.
        
        Returns:
            True if late submission
        """
        if self.submission_date and self.submission_end_date:
            return self.submission_date > self.submission_end_date
        return False
    
    def can_submit(self) -> bool:
        """
        Check if assessment can be submitted.
        
        Returns:
            True if submission is allowed
        """
        if not self.is_active():
            return False
        
        if self.submission_status == 'submitted':
            # Check if multiple attempts are allowed
            if self.max_attempts > 1:
                # Check if current attempt count is less than max
                attempt_count = self.metadata.get('attempt_count', 0)
                return attempt_count < self.max_attempts
            return False
        
        return True
    
    def can_view_results(self) -> bool:
        """
        Check if results can be viewed.
        
        Returns:
            True if results can be viewed
        """
        if self.show_results_immediately and self.submitted_file_path:
            return True
        
        if self.results_release_date and datetime.now() >= self.results_release_date:
            return True
        
        return False
    
    def get_days_until_deadline(self) -> Optional[int]:
        """
        Get days until submission deadline.
        
        Returns:
            Days until deadline, or None if no deadline
        """
        if self.submission_end_date:
            delta = self.submission_end_date - datetime.now()
            return max(0, delta.days)
        return None
    
    def get_pass_status(self) -> str:
        """
        Get pass status.
        
        Returns:
            Pass status string
        """
        if self.submission_status == 'not_submitted':
            return 'not_submitted'
        elif self.obtained_marks >= self.passing_marks:
            return 'pass'
        else:
            return 'fail'
    
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
    
    def get_assessment_summary(self) -> Dict[str, Any]:
        """
        Get assessment summary.
        
        Returns:
            Assessment summary dictionary
        """
        return {
            'id': self.id,
            'code': self.code,
            'title': self.title,
            'type': self.type,
            'category': self.category,
            'total_marks': self.total_marks,
            'obtained_marks': self.obtained_marks,
            'percentage_score': self.percentage_score,
            'grade': self.grade,
            'passing_marks': self.passing_marks,
            'pass_status': self.get_pass_status(),
            'performance_level': self.get_performance_level(),
            'submission_status': self.submission_status,
            'evaluation_status': self.evaluation_status,
            'is_active': self.is_active(),
            'is_overdue': self.is_overdue(),
            'days_until_deadline': self.get_days_until_deadline(),
            'can_submit': self.can_submit(),
            'can_view_results': self.can_view_results(),
            'attachment_count': len(self.attachments)
        }
    
    def __repr__(self) -> str:
        """String representation of the assessment model."""
        return f"<AssessmentModel(code='{self.code}', title='{self.title}', type='{self.type}', status='{self.submission_status}')>"