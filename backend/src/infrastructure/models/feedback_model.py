"""
Feedback Model for Database Operations

This module provides the SQLAlchemy model for Feedback entity.
It includes all fields and relationships for feedback management with sentiment analysis.

Author: Edu-Flow Team
"""

from typing import Dict, Any, Optional, List
from datetime import datetime
import logging

from sqlalchemy import Column, String, Integer, Text, DateTime, JSON, Boolean, ForeignKey, Float
from sqlalchemy.orm import relationship

from infrastructure.models.base_model import BaseModel
from core.exceptions import ValidationError
from core.logging import get_logger

logger = get_logger(__name__)


class FeedbackModel(BaseModel):
    """
    SQLAlchemy model for Feedback entity.
    
    Represents feedback management with sentiment analysis and resolution tracking.
    """
    __tablename__ = "feedback"
    
    # Feedback identification
    id = Column(String(50), primary_key=True)
    code = Column(String(50), nullable=False, unique=True, index=True)
    title = Column(String(200), nullable=False, index=True)
    description = Column(Text, nullable=False)
    
    # Feedback categorization
    type = Column(String(50), nullable=False)  # student, teacher, course, infrastructure, administrative
    category = Column(String(50), nullable=False)  # academic, non_academic, technical, facilities
    subcategory = Column(String(50))
    
    # Related entities
    submitted_by_id = Column(String(50), ForeignKey("users.id"), nullable=False)
    assigned_to_id = Column(String(50), ForeignKey("users.id"))  # Assigned resolver
    related_to_id = Column(String(50))  # Related entity (subject_id, class_id, teacher_id, etc.)
    related_to_type = Column(String(50))  # subject, class, teacher, course, etc.
    
    # Feedback content
    content = Column(Text, nullable=False)
    suggestion = Column(Text)  # Suggested solution or improvement
    expected_resolution = Column(Text)  # Expected resolution from the submitter
    
    # Sentiment analysis
    sentiment_score = Column(Float, default=0.0)  # Sentiment score (-1.0 to 1.0)
    sentiment_label = Column(String(20), default="neutral")  # positive, negative, neutral
    sentiment_confidence = Column(Float, default=0.0)  # Confidence in sentiment analysis
    
    # Priority and severity
    priority = Column(String(20), default="medium")  # low, medium, high, critical
    severity = Column(String(20), default="minor")  # minor, moderate, major, critical
    
    # Status and tracking
    status = Column(String(20), nullable=False, default="pending")  # pending, in_progress, resolved, closed, cancelled
    resolution_status = Column(String(20), default="unresolved")  # unresolved, partially_resolved, resolved
    
    # Resolution tracking
    resolution_notes = Column(Text)
    resolution_date = Column(DateTime)
    resolved_by_id = Column(String(50), ForeignKey("users.id"))
    
    # Timeline and deadlines
    submission_date = Column(DateTime, default=datetime.now)
    due_date = Column(DateTime)
    escalation_date = Column(DateTime)
    reminder_dates = Column(JSON, default=list)
    
    # Feedback metadata
    metadata = Column(JSON, default=dict)
    attachments = Column(JSON, default=list)  # List of attachment paths/URLs
    
    # Relationships
    submitted_by = relationship("UserModel", foreign_keys=[submitted_by_id])
    assigned_to = relationship("UserModel", foreign_keys=[assigned_to_id])
    resolved_by = relationship("UserModel", foreign_keys=[resolved_by_id])
    responses = relationship("FeedbackResponseModel")
    ratings = relationship("FeedbackRatingModel")
    
    def __init__(self, **kwargs):
        """Initialize the feedback model with provided data."""
        # Set default values for optional fields
        kwargs.setdefault('priority', 'medium')
        kwargs.setdefault('severity', 'minor')
        kwargs.setdefault('status', 'pending')
        kwargs.setdefault('resolution_status', 'unresolved')
        kwargs.setdefault('sentiment_score', 0.0)
        kwargs.setdefault('sentiment_label', 'neutral')
        kwargs.setdefault('sentiment_confidence', 0.0)
        kwargs.setdefault('metadata', {})
        kwargs.setdefault('attachments', [])
        kwargs.setdefault('reminder_dates', [])
        
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
        if 'submission_date' in data and isinstance(data['submission_date'], datetime):
            data['submission_date'] = data['submission_date'].isoformat()
        else:
            data['submission_date'] = datetime.now().isoformat()
        
        if 'due_date' in data and isinstance(data['due_date'], datetime):
            data['due_date'] = data['due_date'].isoformat()
        else:
            data['due_date'] = None
        
        if 'escalation_date' in data and isinstance(data['escalation_date'], datetime):
            data['escalation_date'] = data['escalation_date'].isoformat()
        else:
            data['escalation_date'] = None
        
        if 'resolution_date' in data and isinstance(data['resolution_date'], datetime):
            data['resolution_date'] = data['resolution_date'].isoformat()
        else:
            data['resolution_date'] = None
        
        # Convert JSON fields to proper format
        if 'metadata' in data and isinstance(data['metadata'], dict):
            data['metadata'] = data['metadata']
        else:
            data['metadata'] = {}
        
        if 'attachments' in data and isinstance(data['attachments'], list):
            data['attachments'] = data['attachments']
        else:
            data['attachments'] = []
        
        if 'reminder_dates' in data and isinstance(data['reminder_dates'], list):
            data['reminder_dates'] = [date.isoformat() if isinstance(date, datetime) else date for date in data['reminder_dates']]
        else:
            data['reminder_dates'] = []
        
        # Calculate derived fields
        data['is_overdue'] = self.is_overdue()
        data['days_until_due'] = self.get_days_until_due()
        data='is_critical'] = self.priority == 'critical' or self.severity == 'critical'
        data='urgency_score'] = self.get_urgency_score()
        data='satisfaction_score'] = self.get_satisfaction_score()
        data='resolution_time'] = self.get_resolution_time()
        
        # Include relationships if requested
        if include_relationships:
            if hasattr(self, 'submitted_by') and self.submitted_by:
                data['submitted_by'] = self.submitted_by.to_dict()
            else:
                data['submitted_by'] = None
            
            if hasattr(self, 'assigned_to') and self.assigned_to:
                data['assigned_to'] = self.assigned_to.to_dict()
            else:
                data['assigned_to'] = None
            
            if hasattr(self, 'resolved_by') and self.resolved_by:
                data['resolved_by'] = self.resolved_by.to_dict()
            else:
                data['resolved_by'] = None
            
            if hasattr(self, 'responses') and self.responses:
                data['responses'] = [response.to_dict() for response in self.responses]
            else:
                data['responses'] = []
            
            if hasattr(self, 'ratings') and self.ratings:
                data['ratings'] = [rating.to_dict() for rating in self.ratings]
            else:
                data['ratings'] = []
        
        return data
    
    def update(self, **kwargs) -> None:
        """Update the model with new data."""
        # Handle special field updates
        if 'metadata' in kwargs and isinstance(kwargs['metadata'], dict):
            self.metadata = kwargs['metadata']
        if 'attachments' in kwargs and isinstance(kwargs['attachments'], list):
            self.attachments = kwargs['attachments']
        if 'reminder_dates' in kwargs and isinstance(kwargs['reminder_dates'], list):
            self.reminder_dates = kwargs['reminder_dates']
        
        super().update(**kwargs)
    
    def validate(self) -> bool:
        """
        Validate the feedback model data.
        
        Returns:
            True if valid, False otherwise
            
        Raises:
            ValidationError: If validation fails
        """
        try:
            # Call base validation
            super().validate()
            
            # Feedback-specific validations
            if not self.id:
                raise ValidationError("Feedback ID is required")
            
            if not self.code:
                raise ValidationError("Feedback code is required")
            
            if not self.title:
                raise ValidationError("Feedback title is required")
            
            if not self.description:
                raise ValidationError("Feedback description is required")
            
            if not self.type:
                raise ValidationError("Feedback type is required")
            
            if not self.category:
                raise ValidationError("Feedback category is required")
            
            if not self.submitted_by_id:
                raise ValidationError("Submitted by ID is required")
            
            # Type validation
            valid_types = ['student', 'teacher', 'course', 'infrastructure', 'administrative', 'alumni']
            if self.type not in valid_types:
                raise ValidationError(f"Invalid feedback type: {self.type}")
            
            # Category validation
            valid_categories = ['academic', 'non_academic', 'technical', 'facilities', 'administrative', 'services']
            if self.category not in valid_categories:
                raise ValidationError(f"Invalid feedback category: {self.category}")
            
            # Priority validation
            valid_priorities = ['low', 'medium', 'high', 'critical']
            if self.priority not in valid_priorities:
                raise ValidationError(f"Invalid priority: {self.priority}")
            
            # Severity validation
            valid_severities = ['minor', 'moderate', 'major', 'critical']
            if self.severity not in valid_severities:
                raise ValidationError(f"Invalid severity: {self.severity}")
            
            # Status validation
            valid_statuses = ['pending', 'in_progress', 'resolved', 'closed', 'cancelled']
            if self.status not in valid_statuses:
                raise ValidationError(f"Invalid status: {self.status}")
            
            # Resolution status validation
            valid_resolution_statuses = ['unresolved', 'partially_resolved', 'resolved']
            if self.resolution_status not in valid_resolution_statuses:
                raise ValidationError(f"Invalid resolution status: {self.resolution_status}")
            
            # Sentiment score validation
            if self.sentiment_score < -1.0 or self.sentiment_score > 1.0:
                raise ValidationError("Sentiment score must be between -1.0 and 1.0")
            
            # Sentiment confidence validation
            if self.sentiment_confidence < 0.0 or self.sentiment_confidence > 1.0:
                raise ValidationError("Sentiment confidence must be between 0.0 and 1.0")
            
            # Sentiment label validation
            valid_sentiment_labels = ['positive', 'negative', 'neutral']
            if self.sentiment_label not in valid_sentiment_labels:
                raise ValidationError(f"Invalid sentiment label: {self.sentiment_label}")
            
            # Metadata validation
            if not isinstance(self.metadata, dict):
                raise ValidationError("Metadata must be a dictionary")
            
            # Attachments validation
            if not isinstance(self.attachments, list):
                raise ValidationError("Attachments must be a list")
            
            # Reminder dates validation
            if not isinstance(self.reminder_dates, list):
                raise ValidationError("Reminder dates must be a list")
            
            for reminder_date in self.reminder_dates:
                if not isinstance(reminder_date, datetime) and not isinstance(reminder_date, str):
                    raise ValidationError("Reminder dates must be datetime objects or strings")
            
            logger.info(f"Feedback {self.code} validation passed")
            return True
            
        except Exception as e:
            logger.error(f"Feedback validation error: {str(e)}")
            raise ValidationError(f"Feedback validation error: {str(e)}")
    
    def update_sentiment_analysis(self, sentiment_score: float, sentiment_label: str, 
                                 sentiment_confidence: float) -> None:
        """
        Update sentiment analysis results.
        
        Args:
            sentiment_score: Sentiment score (-1.0 to 1.0)
            sentiment_label: Sentiment label (positive, negative, neutral)
            sentiment_confidence: Confidence in sentiment analysis (0.0 to 1.0)
        """
        if sentiment_score < -1.0 or sentiment_score > 1.0:
            raise ValidationError("Sentiment score must be between -1.0 and 1.0")
        
        if sentiment_confidence < 0.0 or sentiment_confidence > 1.0:
            raise ValidationError("Sentiment confidence must be between 0.0 and 1.0")
        
        valid_sentiment_labels = ['positive', 'negative', 'neutral']
        if sentiment_label not in valid_sentiment_labels:
            raise ValidationError(f"Invalid sentiment label: {sentiment_label}")
        
        self.sentiment_score = sentiment_score
        self.sentiment_label = sentiment_label
        self.sentiment_confidence = sentiment_confidence
        self.updated_at = datetime.now()
        
        logger.info(f"Updated sentiment analysis for feedback {self.code}: {sentiment_label} ({sentiment_score}, {sentiment_confidence})")
    
    def assign_feedback(self, assigned_to_id: str, due_date: datetime = None) -> None:
        """
        Assign feedback to a resolver.
        
        Args:
            assigned_to_id: User ID to assign to
            due_date: Due date for resolution (optional)
        """
        self.assigned_to_id = assigned_to_id
        self.status = 'in_progress'
        self.due_date = due_date
        
        # Add reminder dates if due date is specified
        if due_date:
            self.add_reminder_dates(due_date)
        
        self.updated_at = datetime.now()
        logger.info(f"Assigned feedback {self.code} to user {assigned_to_id}")
    
    def add_response(self, responder_id: str, response_text: str, response_type: str = "internal") -> None:
        """
        Add a response to the feedback.
        
        Args:
            responder_id: User ID of the responder
            response_text: Response text
            response_type: Type of response (internal, public, action_taken)
        """
        # This would create a FeedbackResponseModel in practice
        # For now, we'll just add to the metadata
        response_data = {
            'responder_id': responder_id,
            'response_text': response_text,
            'response_type': response_type,
            'response_date': datetime.now().isoformat()
        }
        
        if 'responses' not in self.metadata:
            self.metadata['responses'] = []
        
        self.metadata['responses'].append(response_data)
        self.updated_at = datetime.now()
        logger.info(f"Added response to feedback {self.code} from user {responder_id}")
    
    def resolve_feedback(self, resolved_by_id: str, resolution_notes: str, 
                        resolution_date: datetime = None) -> None:
        """
        Resolve the feedback.
        
        Args:
            resolved_by_id: User ID who resolved the feedback
            resolution_notes: Resolution notes
            resolution_date: Resolution date (optional)
        """
        self.resolved_by_id = resolved_by_id
        self.resolution_notes = resolution_notes
        self.resolution_date = resolution_date or datetime.now()
        self.status = 'resolved'
        self.resolution_status = 'resolved'
        self.updated_at = datetime.now()
        
        logger.info(f"Resolved feedback {self.code} by user {resolved_by_id}")
    
    def close_feedback(self, closed_by_id: str, closure_reason: str = "") -> None:
        """
        Close the feedback.
        
        Args:
            closed_by_id: User ID who closed the feedback
            closure_reason: Reason for closure (optional)
        """
        self.status = 'closed'
        if closure_reason:
            self.metadata['closure_reason'] = closure_reason
        self.updated_at = datetime.now()
        
        logger.info(f"Closed feedback {self.code} by user {closed_by_id}")
    
    def cancel_feedback(self, cancelled_by_id: str, cancellation_reason: str) -> None:
        """
        Cancel the feedback.
        
        Args:
            cancelled_by_id: User ID who cancelled the feedback
            cancellation_reason: Reason for cancellation
        """
        self.status = 'cancelled'
        if cancellation_reason:
            self.metadata['cancellation_reason'] = cancellation_reason
        self.updated_at = datetime.now()
        
        logger.info(f"Cancelled feedback {self.code} by user {cancelled_by_id} with reason: {cancellation_reason}")
    
    def add_reminder_dates(self, reminder_dates: List[datetime]) -> None:
        """
        Add reminder dates.
        
        Args:
            reminder_dates: List of reminder dates
        """
        if not isinstance(reminder_dates, list):
            reminder_dates = [reminder_dates]
        
        for reminder_date in reminder_dates:
            if not isinstance(reminder_date, datetime):
                raise ValidationError("Reminder dates must be datetime objects")
            
            if reminder_date not in self.reminder_dates:
                self.reminder_dates.append(reminder_date)
        
        self.updated_at = datetime.now()
        logger.info(f"Added reminder dates for feedback {self.code}")
    
    def add_attachment(self, attachment_path: str, attachment_type: str = "file") -> None:
        """
        Add an attachment.
        
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
        logger.info(f"Added attachment to feedback {self.code}: {attachment_path}")
    
    def get_urgency_score(self) -> int:
        """
        Calculate urgency score based on priority, severity, and due date.
        
        Returns:
            Urgency score (0-100)
        """
        urgency = 0
        
        # Priority scoring
        if self.priority == 'critical':
            urgency += 40
        elif self.priority == 'high':
            urgency += 30
        elif self.priority == 'medium':
            urgency += 20
        else:
            urgency += 10
        
        # Severity scoring
        if self.severity == 'critical':
            urgency += 40
        elif self.severity == 'major':
            urgency += 30
        elif self.severity == 'moderate':
            urgency += 20
        else:
            urgency += 10
        
        # Due date scoring
        if self.due_date:
            days_until_due = self.get_days_until_due()
            if days_until_due <= 0:
                urgency += 20  # Overdue
            elif days_until_due <= 3:
                urgency += 15  # Due soon
            elif days_until_due <= 7:
                urgency += 10  # Due in a week
            else:
                urgency += 5  # Due later
        
        return min(urgency, 100)
    
    def get_satisfaction_score(self) -> float:
        """
        Calculate satisfaction score based on sentiment analysis.
        
        Returns:
            Satisfaction score (-1.0 to 1.0)
        """
        if self.sentiment_score > 0:
            return self.sentiment_score  # Positive feedback
        elif self.sentiment_score < 0:
            return self.sentiment_score * -0.5  # Negative feedback (penalized less)
        else:
            return 0.0  # Neutral feedback
    
    def get_resolution_time(self) -> Optional[int]:
        """
        Get resolution time in days.
        
        Returns:
            Resolution time in days, or None if not resolved
        """
        if self.resolution_date and self.submission_date:
            delta = self.resolution_date - self.submission_date
            return delta.days
        
        return None
    
    def is_overdue(self) -> bool:
        """
        Check if feedback is overdue.
        
        Returns:
            True if overdue
        """
        if self.due_date and datetime.now() > self.due_date:
            return True
        return False
    
    def get_days_until_due(self) -> Optional[int]:
        """
        Get days until due date.
        
        Returns:
            Days until due date, or None if no due date
        """
        if self.due_date:
            delta = self.due_date - datetime.now()
            return max(0, delta.days)
        return None
    
    def is_critical(self) -> bool:
        """
        Check if feedback is critical.
        
        Returns:
            True if critical
        """
        return self.priority == 'critical' or self.severity == 'critical'
    
    def get_feedback_statistics(self) -> Dict[str, Any]:
        """
        Get feedback statistics.
        
        Returns:
            Feedback statistics dictionary
        """
        return {
            'id': self.id,
            'code': self.code,
            'title': self.title,
            'type': self.type,
            'category': self.category,
            'priority': self.priority,
            'severity': self.severity,
            'status': self.status,
            'sentiment': self.sentiment_label,
            'sentiment_score': self.sentiment_score,
            'urgency_score': self.get_urgency_score(),
            'satisfaction_score': self.get_satisfaction_score(),
            'is_overdue': self.is_overdue(),
            'days_until_due': self.get_days_until_due(),
            'resolution_time': self.get_resolution_time(),
            'attachment_count': len(self.attachments),
            'response_count': len(self.metadata.get('responses', []))
        }
    
    def __repr__(self) -> str:
        """String representation of the feedback model."""
        return f"<FeedbackModel(code='{self.code}', title='{self.title}', type='{self.type}', status='{self.status}')>"