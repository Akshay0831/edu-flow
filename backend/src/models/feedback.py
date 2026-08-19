"""
Feedback Processing Models for Edu-Flow

This module defines the data models for feedback processing:
- Feedback: Student feedback data collection
- FeedbackCategory: Types of feedback categories
- FeedbackResponse: Instructor responses to feedback
- FeedbackAnalysis: Automated feedback analysis results
- FeedbackReport: Generated feedback reports

Author: Edu-Flow Team
"""

from datetime import datetime
from typing import Dict, List, Optional, Any
from enum import Enum
from sqlalchemy import Column, String, Integer, Float, DateTime, ForeignKey, Text, Boolean, JSON, Numeric
from sqlalchemy.orm import relationship
import uuid

from infrastructure.models.base_model import Base

class FeedbackType(Enum):
    """Types of feedback categories"""
    COURSE_CONTENT = "course_content"
    TEACHING_METHOD = "teaching_method"
    ASSESSMENT = "assessment"
    INFRASTRUCTURE = "infrastructure"
    ADMINISTRATION = "administration"
    OVERALL = "overall"

class FeedbackScale(Enum):
    """Feedback rating scales"""
    FIVE_POINT = "five_point"    # 1-5 scale
    TEN_POINT = "ten_point"      # 1-10 scale
    LIKERT_SCALE = "likert_scale"  # Strongly Disagree to Strongly Agree
    CUSTOM = "custom"

class FeedbackStatus(Enum):
    """Feedback processing status"""
    DRAFT = "draft"
    SUBMITTED = "submitted"
    ANALYZED = "analyzed"
    RESPONDED = "responded"
    CLOSED = "closed"

class FeedbackResponseStatus(Enum):
    """Feedback response status"""
    PENDING = "pending"
    DRAFT = "draft"
    SUBMITTED = "submitted"
    APPROVED = "approved"
    PUBLISHED = "published"

class Sentiment(Enum):
    """Feedback sentiment classification"""
    VERY_POSITIVE = "very_positive"
    POSITIVE = "positive"
    NEUTRAL = "neutral"
    NEGATIVE = "negative"
    VERY_NEGATIVE = "very_negative"

class Feedback(Base):
    """Main feedback model"""
    
    __tablename__ = "feedback"
    
    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    student_id = Column(String, nullable=False)
    course_id = Column(String, nullable=False)
    teacher_id = Column(String, nullable=True)
    semester = Column(String, nullable=False)
    academic_year = Column(String, nullable=False)
    
    # Feedback details
    feedback_type = Column(String, nullable=False)
    rating = Column(Numeric(3, 1), nullable=True)  # Decimal rating
    overall_rating = Column(Numeric(3, 1), nullable=True)
    
    # Free text feedback
    comments = Column(Text, nullable=True)
    strengths = Column(Text, nullable=True)
    improvements = Column(Text, nullable=True)
    additional_comments = Column(Text, nullable=True)
    
    # Metadata
    anonymous = Column(Boolean, default=False, nullable=False)
    status = Column(String, default=FeedbackStatus.SUBMITTED.value, nullable=False)
    submission_date = Column(DateTime, default=datetime.utcnow, nullable=False)
    processed_date = Column(DateTime, nullable=True)
    
    # Analysis results
    sentiment_score = Column(Numeric(3, 2), nullable=True)  # -1.0 to 1.0
    sentiment_category = Column(String, nullable=True)
    keyword_analysis = Column(JSON, nullable=True)  # Extracted keywords and topics
    topic_classification = Column(JSON, nullable=True)  # Topic categorization
    
    # Scaled ratings for different aspects
    ratings = Column(JSON, nullable=True)  # Multiple rating aspects
    scale_used = Column(String, default=FeedbackScale.FIVE_POINT.value, nullable=False)
    
    # Generated responses
    auto_response = Column(Text, nullable=True)
    response_suggestion = Column(Text, nullable=True)
    
    # Configuration
    is_processed = Column(Boolean, default=False, nullable=False)
    priority_score = Column(Integer, default=0, nullable=False)
    
    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
    
    # Relationships
    responses = relationship("FeedbackResponse", back_populates="feedback")

class FeedbackCategory(Base):
    """Feedback categories configuration"""
    
    __tablename__ = "feedback_categories"
    
    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    name = Column(String, unique=True, nullable=False)
    description = Column(Text, nullable=True)
    category_code = Column(String, unique=True, nullable=False)
    
    # Configuration
    is_active = Column(Boolean, default=True, nullable=False)
    weight = Column(Numeric(3, 2), default=1.0, nullable=False)
    required = Column(Boolean, default=True, nullable=False)
    min_rating = Column(Numeric(3, 1), default=1.0, nullable=False)
    max_rating = Column(Numeric(3, 1), default=5.0, nullable=False)
    
    # Display settings
    display_name = Column(String, nullable=True)
    description_template = Column(Text, nullable=True)
    rating_labels = Column(JSON, nullable=True)  # Labels for different rating levels
    
    # Metadata
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

class FeedbackResponse(Base):
    """Instructor response to feedback"""
    
    __tablename__ = "feedback_responses"
    
    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    feedback_id = Column(String, ForeignKey("feedback.id"), nullable=False)
    teacher_id = Column(String, nullable=False)
    course_id = Column(String, nullable=False)
    
    # Response content
    response_text = Column(Text, nullable=False)
    action_taken = Column(Text, nullable=True)
    implementation_plan = Column(Text, nullable=True)
    timeline = Column(Text, nullable=True)  # Implementation timeline
    resources_needed = Column(Text, nullable=True)
    
    # Status and metadata
    response_status = Column(String, default=FeedbackResponseStatus.PENDING.value, nullable=False)
    response_date = Column(DateTime, nullable=True)
    publication_date = Column(DateTime, nullable=True)
    
    # Analysis
    response_sentiment = Column(String, nullable=True)
    action_categories = Column(JSON, nullable=True)  # Categorized action items
    priority_level = Column(Integer, default=1, nullable=False)  # 1 = High, 5 = Low
    
    # Approval
    approved_by = Column(String, nullable=True)
    approval_date = Column(DateTime, nullable=True)
    approval_comments = Column(Text, nullable=True)
    
    # Configuration
    is_public = Column(Boolean, default=False, nullable=False)
    allows_comments = Column(Boolean, default=False, nullable=False)
    
    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
    
    # Relationships
    feedback = relationship("Feedback", back_populates="responses")

class FeedbackAnalysis(Base):
    """Automated feedback analysis results"""
    
    __tablename__ = "feedback_analysis"
    
    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    feedback_id = Column(String, ForeignKey("feedback.id"), nullable=False)
    analysis_type = Column(String, nullable=False)  # sentiment, keyword, topic, etc.
    
    # Analysis results
    analysis_results = Column(JSON, nullable=False)
    confidence_score = Column(Numeric(3, 2), nullable=True)  # Confidence in analysis
    processing_time = Column(Numeric(6, 3), nullable=True)  # Processing time in seconds
    
    # Metadata
    model_version = Column(String, nullable=True)
    model_used = Column(String, nullable=True)
    timestamp = Column(DateTime, default=datetime.utcnow, nullable=False)
    
    # Configuration
    is_enabled = Column(Boolean, default=True, nullable=False)
    analysis_config = Column(JSON, nullable=True)  # Configuration for analysis
    
    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

class FeedbackReport(Base):
    """Generated feedback reports"""
    
    __tablename__ = "feedback_reports"
    
    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    report_type = Column(String, nullable=False)
    academic_year = Column(String, nullable=False)
    semester = Column(String, nullable=False)
    generated_by = Column(String, nullable=False)
    
    # Report content
    report_data = Column(JSON, nullable=False)
    summary_stats = Column(JSON, nullable=True)
    key_findings = Column(JSON, nullable=True)
    trend_analysis = Column(JSON, nullable=True)
    recommendations = Column(JSON, nullable=True)
    
    # Report configuration
    format_type = Column(String, default="html", nullable=False)  # html, pdf, json, excel
    include_individual_responses = Column(Boolean, default=False, nullable=False)
    include_anonymized_data = Column(Boolean, default=True, nullable=False)
    
    # Status
    generation_status = Column(String, default="generating", nullable=False)
    download_url = Column(String, nullable=True)
    file_size = Column(Integer, nullable=True)  # File size in bytes
    
    # Metadata
    scheduled_for = Column(DateTime, nullable=True)  # Scheduled generation time
    generated_at = Column(DateTime, nullable=True)
    expires_at = Column(DateTime, nullable=True)  # Expiration date for download
    
    # Configuration
    template_config = Column(JSON, nullable=True)  # Report template configuration
    chart_config = Column(JSON, nullable=True)  # Chart generation settings
    
    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

class FeedbackTemplate(Base):
    """Feedback templates configuration"""
    
    __tablename__ = "feedback_templates"
    
    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    name = Column(String, nullable=False)
    description = Column(Text, nullable=True)
    template_code = Column(String, unique=True, nullable=False)
    
    # Template content
    template_content = Column(JSON, nullable=False)  # Template structure
    categories_config = Column(JSON, nullable=True)  # Categories and their settings
    
    # Display settings
    display_name = Column(String, nullable=True)
    description_template = Column(Text, nullable=True)
    
    # Configuration
    is_active = Column(Boolean, default=True, nullable=False)
    is_default = Column(Boolean, default=False, nullable=False)
    usage_count = Column(Integer, default=0, nullable=False)
    
    # Target audience
    target_audience = Column(String, default="students", nullable=False)  # students, teachers, both
    
    # Metadata
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

class FeedbackCampaign(Base):
    """Feedback campaigns for systematic feedback collection"""
    
    __tablename__ = "feedback_campaigns"
    
    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    name = Column(String, nullable=False)
    description = Column(Text, nullable=True)
    
    # Campaign details
    academic_year = Column(String, nullable=False)
    semester = Column(String, nullable=False)
    start_date = Column(DateTime, nullable=False)
    end_date = Column(DateTime, nullable=False)
    
    # Campaign configuration
    target_audience = Column(String, nullable=False)  # all, specific courses, specific teachers
    campaign_type = Column(String, default="standard", nullable=False)  # standard, targeted, periodic
    frequency = Column(String, default="once", nullable=False)  # once, monthly, quarterly, semester
    
    # Template and distribution
    template_id = Column(String, ForeignKey("feedback_templates.id"), nullable=True)
    distribution_method = Column(String, default="email", nullable=False)  # email, form, manual
    
    # Status
    campaign_status = Column(String, default="active", nullable=False)  # active, completed, cancelled
    response_rate = Column(Numeric(5, 2), nullable=True)  # Percentage of responses
    total_responses = Column(Integer, default=0, nullable=False)
    
    # Analytics
    completion_rate = Column(Numeric(5, 2), nullable=True)
    average_rating = Column(Numeric(3, 1), nullable=True)
    
    # Configuration
    reminder_config = Column(JSON, nullable=True)  # Reminder settings
    notification_config = Column(JSON, nullable=True)  # Notification settings
    
    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
    
    # Relationships
    template = relationship("FeedbackTemplate")