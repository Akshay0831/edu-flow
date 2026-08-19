"""
Feedback Management API Endpoints

This module provides REST API endpoints for feedback management operations:
- CRUD operations for feedback
- Feedback submission and collection
- Feedback analysis and reporting
- Response tracking
- Survey management

Author: Edu-Flow Team
"""

from datetime import datetime
from typing import List, Optional, Dict, Any
from uuid import uuid4
from fastapi import APIRouter, Depends, HTTPException, status, Query, Body
from pydantic import BaseModel, Field, validator
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials

from core.security import auth_service
from core.exceptions import ValidationError, NotFoundError, AuthenticationError, AuthorizationError
from infrastructure.repositories.feedback_repository import FeedbackRepository

# Create router
router = APIRouter(prefix="/feedback", tags=["feedback"])

# Security
security = HTTPBearer()

# Repositories
feedback_repo = FeedbackRepository()


# Pydantic models
class FeedbackBase(BaseModel):
    feedback_type: str = Field(..., description="student, teacher, course, program")
    target_id: str = Field(..., min_length=2, description="student_id, teacher_id, course_id, program_id")
    feedback_for_id: str = Field(..., min_length=2, description="feedback receiver_id")
    subject: str = Field(..., max_length=100)
    message: str = Field(..., max_length=2000)
    rating: Optional[int] = Field(None, ge=1, le=5, description="Rating from 1 to 5")
    category: Optional[str] = Field(None, description="feedback category")
    priority: int = Field(1, ge=1, le=5, description="Priority level")
    is_anonymous: bool = Field(False, description="Whether feedback is anonymous")
    metadata: Optional[Dict[str, Any]] = Field(default_factory=dict)


class FeedbackCreate(FeedbackBase):
    pass


class FeedbackUpdate(BaseModel):
    subject: Optional[str] = Field(None, max_length=100)
    message: Optional[str] = Field(None, max_length=2000)
    rating: Optional[int] = Field(None, ge=1, le=5)
    category: Optional[str] = Field(None)
    priority: Optional[int] = Field(None, ge=1, le=5)
    is_anonymous: Optional[bool] = Field(None)
    status: Optional[str] = Field(None, description="pending, in_progress, resolved, closed")


class FeedbackResponse(FeedbackBase):
    id: str
    created_at: datetime
    updated_at: datetime
    status: str
    responded_at: Optional[datetime]
    responded_by_id: Optional[str]
    response_message: Optional[str]
    parent_feedback_id: Optional[str]
    thread_count: int = 0
    response_count: int = 0
    sentiment_score: float = 0.0
    
    class Config:
        from_attributes = True


class FeedbackResponseCreate(BaseModel):
    response_message: str = Field(..., max_length=2000)
    next_action: Optional[str] = Field(None, description="next steps for resolution")


class FeedbackThread(BaseModel):
    feedback_id: str
    parent_id: Optional[str]
    message: str = Field(..., max_length=2000)
    rating: Optional[int] = Field(None, ge=1, le=5)
    metadata: Optional[Dict[str, Any]] = Field(default_factory=dict)


class Survey(BaseModel):
    title: str = Field(..., max_length=100)
    description: str = Field(..., max_length=500)
    survey_type: str = Field(..., description="student, teacher, course, program")
    target_id: str = Field(..., min_length=2, description="student_id, teacher_id, course_id, program_id")
    questions: List[Dict[str, Any]] = Field(..., description="List of survey questions")
    start_date: datetime = Field(..., description="Survey start date")
    end_date: Optional[datetime] = Field(None, description="Survey end date")
    is_active: bool = Field(True)
    anonymous_responses: bool = Field(True)
    metadata: Optional[Dict[str, Any]] = Field(default_factory=dict)


class SurveyCreate(Survey):
    pass


class SurveyResponse(BaseModel):
    survey_id: str
    question_id: str
    response_value: Any
    response_text: Optional[str] = None
    metadata: Optional[Dict[str, Any]] = Field(default_factory=dict)


class FeedbackAnalytics(BaseModel):
    feedback_count: int
    average_rating: float
    sentiment_distribution: Dict[str, int]
    category_distribution: Dict[str, int]
    priority_distribution: Dict[str, int]
    resolution_rate: float
    response_time_avg: float
    resolution_time_avg: float
    top_categories: List[str]
    sentiment_trend: List[Dict[str, Any]]


@router.get("/", response_model=List[FeedbackResponse])
async def get_feedback(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    feedback_type: Optional[str] = Query(None),
    target_id: Optional[str] = Query(None),
    feedback_for_id: Optional[str] = Query(None),
    status: Optional[str] = Query(None),
    priority: Optional[int] = Query(None),
    category: Optional[str] = Query(None),
    has_responses: Optional[bool] = Query(None),
    search: Optional[str] = Query(None),
    created_by: Optional[str] = Query(None)
):
    """
    Get all feedback with optional filtering
    
    Args:
        skip: Number of records to skip
        limit: Maximum number of records to return
        feedback_type: Filter by feedback type
        target_id: Filter by target ID
        feedback_for_id: Filter by feedback receiver ID
        status: Filter by status
        priority: Filter by priority
        category: Filter by category
        has_responses: Filter by response status
        search: Search term in subject or message
        created_by: Filter by creator ID
        
    Returns:
        List of feedback
    """
    try:
        feedback_list = await feedback_repo.get_all(
            skip=skip,
            limit=limit,
            feedback_type=feedback_type,
            target_id=target_id,
            feedback_for_id=feedback_for_id,
            status=status,
            priority=priority,
            category=category,
            has_responses=has_responses,
            search=search,
            created_by=created_by
        )
        
        # Add derived information
        for feedback in feedback_list:
            feedback.thread_count = await feedback_repo.get_thread_count(feedback.id)
            feedback.response_count = await feedback_repo.get_response_count(feedback.id)
            sentiment = await feedback_repo.get_sentiment_score(feedback.id)
            feedback.sentiment_score = sentiment['sentiment_score'] if sentiment else 0.0
        
        return feedback_list
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to fetch feedback: {str(e)}"
        )


@router.get("/{feedback_id}", response_model=FeedbackResponse)
async def get_feedback_details(feedback_id: str):
    """
    Get detailed feedback information
    
    Args:
        feedback_id: Feedback ID
        
    Returns:
        Detailed feedback information
    """
    try:
        feedback = await feedback_repo.get_by_id(feedback_id)
        if not feedback:
            raise NotFoundError(f"Feedback not found with ID: {feedback_id}")
        
        # Add derived information
        feedback.thread_count = await feedback_repo.get_thread_count(feedback_id)
        feedback.response_count = await feedback_repo.get_response_count(feedback_id)
        sentiment = await feedback_repo.get_sentiment_score(feedback_id)
        feedback.sentiment_score = sentiment['sentiment_score'] if sentiment else 0.0
        
        return feedback
        
    except NotFoundError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Feedback not found with ID: {feedback_id}"
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to fetch feedback details: {str(e)}"
        )


@router.post("/", response_model=FeedbackResponse, status_code=status.HTTP_201_CREATED)
async def create_feedback(
    feedback_data: FeedbackCreate,
    credentials: HTTPAuthorizationCredentials = Depends(security)
):
    """
    Create new feedback
    
    Args:
        feedback_data: Feedback data
        credentials: JWT token
        
    Returns:
        Created feedback
    """
    try:
        # Verify authentication
        auth = auth_service.get_current_user(credentials.credentials)
        if not auth:
            raise AuthenticationError("Authentication required")
        
        # Validate feedback type
        valid_types = ['student', 'teacher', 'course', 'program']
        if feedback_data.feedback_type not in valid_types:
            raise ValidationError(f"Invalid feedback type. Must be one of: {valid_types}")
        
        # Validate target_id based on feedback type
        validation_passed = await feedback_repo.validate_target(
            feedback_data.feedback_type,
            feedback_data.target_id
        )
        if not validation_passed:
            raise ValidationError(f"Invalid {feedback_data.feedback_type} ID")
        
        # Validate feedback_for_id
        validation_passed = await feedback_repo.validate_target(
            feedback_data.feedback_type.replace('student', 'teacher').replace('course', 'program'),
            feedback_data.feedback_for_id
        )
        if not validation_passed:
            raise ValidationError(f"Invalid feedback receiver ID")
        
        # Validate rating if provided
        if feedback_data.rating and (feedback_data.rating < 1 or feedback_data.rating > 5):
            raise ValidationError("Rating must be between 1 and 5")
        
        # Create feedback
        feedback = await feedback_repo.create(
            feedback_type=feedback_data.feedback_type,
            target_id=feedback_data.target_id,
            feedback_for_id=feedback_data.feedback_for_id,
            subject=feedback_data.subject,
            message=feedback_data.message,
            rating=feedback_data.rating,
            category=feedback_data.category,
            priority=feedback_data.priority,
            is_anonymous=feedback_data.is_anonymous,
            metadata=feedback_data.metadata,
            created_by_id=auth.get('user_id') or auth.get('id')
        )
        
        return feedback
        
    except ValidationError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Validation error: {str(e)}"
        )
    except AuthenticationError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication required"
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to create feedback: {str(e)}"
        )


@router.put("/{feedback_id}", response_model=FeedbackResponse)
async def update_feedback(
    feedback_id: str,
    feedback_data: FeedbackUpdate,
    credentials: HTTPAuthorizationCredentials = Depends(security)
):
    """
    Update feedback
    
    Args:
        feedback_id: Feedback ID
        feedback_data: Updated feedback data
        credentials: JWT token
        
    Returns:
        Updated feedback
    """
    try:
        # Verify authentication
        auth = auth_service.get_current_user(credentials.credentials)
        if not auth:
            raise AuthenticationError("Authentication required")
        
        # Check if feedback exists
        existing_feedback = await feedback_repo.get_by_id(feedback_id)
        if not existing_feedback:
            raise NotFoundError(f"Feedback not found with ID: {feedback_id}")
        
        # Check if user can modify feedback
        if existing_feedback.created_by_id != auth.get('user_id') and auth.get('role') not in ['admin', 'staff']:
            raise AuthorizationError("Cannot modify this feedback")
        
        # Validate rating if provided
        if feedback_data.rating and (feedback_data.rating < 1 or feedback_data.rating > 5):
            raise ValidationError("Rating must be between 1 and 5")
        
        # Update feedback
        feedback = await feedback_repo.update(
            feedback_id=feedback_id,
            **feedback_data.dict(exclude_unset=True)
        )
        
        return feedback
        
    except NotFoundError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Feedback not found with ID: {feedback_id}"
        )
    except ValidationError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Validation error: {str(e)}"
        )
    except AuthorizationError:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Cannot modify this feedback"
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to update feedback: {str(e)}"
        )


@router.delete("/{feedback_id}")
async def delete_feedback(
    feedback_id: str,
    credentials: HTTPAuthorizationCredentials = Depends(security)
):
    """
    Delete feedback
    
    Args:
        feedback_id: Feedback ID
        credentials: JWT token
        
    Returns:
        Success message
    """
    try:
        # Verify authentication
        auth = auth_service.get_current_user(credentials.credentials)
        if not auth:
            raise AuthenticationError("Authentication required")
        
        # Check if feedback exists
        existing_feedback = await feedback_repo.get_by_id(feedback_id)
        if not existing_feedback:
            raise NotFoundError(f"Feedback not found with ID: {feedback_id}")
        
        # Check if user can delete feedback
        if existing_feedback.created_by_id != auth.get('user_id') and auth.get('role') not in ['admin', 'staff']:
            raise AuthorizationError("Cannot delete this feedback")
        
        # Delete feedback
        await feedback_repo.delete(feedback_id)
        
        return {"message": "Feedback deleted successfully"}
        
    except NotFoundError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Feedback not found with ID: {feedback_id}"
        )
    except AuthorizationError:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Cannot delete this feedback"
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to delete feedback: {str(e)}"
        )


@router.post("/{feedback_id}/response", response_model=FeedbackResponse)
async def respond_to_feedback(
    feedback_id: str,
    response: FeedbackResponseCreate,
    credentials: HTTPAuthorizationCredentials = Depends(security)
):
    """
    Respond to feedback
    
    Args:
        feedback_id: Feedback ID
        response: Response data
        credentials: JWT token
        
    Returns:
        Updated feedback
    """
    try:
        # Verify authentication
        auth = auth_service.get_current_user(credentials.credentials)
        if not auth or auth.get('role') not in ['admin', 'teacher', 'staff']:
            raise AuthorizationError("Insufficient permissions to respond to feedback")
        
        # Check if feedback exists
        existing_feedback = await feedback_repo.get_by_id(feedback_id)
        if not existing_feedback:
            raise NotFoundError(f"Feedback not found with ID: {feedback_id}")
        
        # Respond to feedback
        feedback = await feedback_repo.add_response(
            feedback_id=feedback_id,
            response_message=response.response_message,
            responded_by_id=auth.get('user_id') or auth.get('id'),
            next_action=response.next_action
        )
        
        return feedback
        
    except NotFoundError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Feedback not found with ID: {feedback_id}"
        )
    except AuthorizationError:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Insufficient permissions to respond to feedback"
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to respond to feedback: {str(e)}"
        )


@router.post("/{feedback_id}/add-thread")
async def add_feedback_thread(
    feedback_id: str,
    thread: FeedbackThread,
    credentials: HTTPAuthorizationCredentials = Depends(security)
):
    """
    Add thread to feedback
    
    Args:
        feedback_id: Feedback ID
        thread: Thread data
        credentials: JWT token
        
    Returns:
        Success message
    """
    try:
        # Verify authentication
        auth = auth_service.get_current_user(credentials.credentials)
        if not auth:
            raise AuthenticationError("Authentication required")
        
        # Check if feedback exists
        existing_feedback = await feedback_repo.get_by_id(feedback_id)
        if not existing_feedback:
            raise NotFoundError(f"Feedback not found with ID: {feedback_id}")
        
        # Validate rating if provided
        if thread.rating and (thread.rating < 1 or thread.rating > 5):
            raise ValidationError("Rating must be between 1 and 5")
        
        # Add thread
        await feedback_repo.add_thread(
            feedback_id=feedback_id,
            parent_id=thread.parent_id,
            message=thread.message,
            rating=thread.rating,
            created_by_id=auth.get('user_id') or auth.get('id'),
            metadata=thread.metadata
        )
        
        return {"message": "Thread added successfully"}
        
    except NotFoundError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Feedback not found with ID: {feedback_id}"
        )
    except ValidationError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Validation error: {str(e)}"
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to add thread: {str(e)}"
        )


@router.get("/target/{target_type}/{target_id}")
async def get_feedback_for_target(
    target_type: str,
    target_id: str,
    feedback_type: Optional[str] = Query(None),
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    credentials: HTTPAuthorizationCredentials = Depends(security)
):
    """
    Get feedback for a specific target
    
    Args:
        target_type: Target type (student, teacher, course, program)
        target_id: Target ID
        feedback_type: Filter by feedback type
        skip: Number of records to skip
        limit: Maximum number of records to return
        credentials: JWT token
        
    Returns:
        List of feedback for the target
    """
    try:
        feedback_list = await feedback_repo.get_feedback_for_target(
            target_type=target_type,
            target_id=target_id,
            feedback_type=feedback_type,
            skip=skip,
            limit=limit
        )
        
        # Add derived information
        for feedback in feedback_list:
            feedback.thread_count = await feedback_repo.get_thread_count(feedback.id)
            feedback.response_count = await feedback_repo.get_response_count(feedback.id)
            sentiment = await feedback_repo.get_sentiment_score(feedback.id)
            feedback.sentiment_score = sentiment['sentiment_score'] if sentiment else 0.0
        
        return feedback_list
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to fetch feedback for target: {str(e)}"
        )


@router.get("/analytics/{target_type}/{target_id}")
async def get_feedback_analytics(
    target_type: str,
    target_id: str,
    start_date: Optional[str] = Query(None),
    end_date: Optional[str] = Query(None),
    credentials: HTTPAuthorizationCredentials = Depends(security)
):
    """
    Get feedback analytics for a target
    
    Args:
        target_type: Target type (student, teacher, course, program)
        target_id: Target ID
        start_date: Start date filter (YYYY-MM-DD)
        end_date: End date filter (YYYY-MM-DD)
        credentials: JWT token
        
    Returns:
        Feedback analytics
    """
    try:
        analytics = await feedback_repo.get_feedback_analytics(
            target_type=target_type,
            target_id=target_id,
            start_date=start_date,
            end_date=end_date
        )
        return analytics
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to fetch feedback analytics: {str(e)}"
        )


@router.post("/surveys", response_model=dict, status_code=status.HTTP_201_CREATED)
async def create_survey(
    survey: SurveyCreate,
    credentials: HTTPAuthorizationCredentials = Depends(security)
):
    """
    Create a new survey
    
    Args:
        survey: Survey data
        credentials: JWT token
        
    Returns:
        Created survey
    """
    try:
        # Verify authentication
        auth = auth_service.get_current_user(credentials.credentials)
        if not auth or auth.get('role') not in ['admin', 'teacher', 'staff']:
            raise AuthorizationError("Insufficient permissions to create surveys")
        
        # Validate survey type
        valid_types = ['student', 'teacher', 'course', 'program']
        if survey.survey_type not in valid_types:
            raise ValidationError(f"Invalid survey type. Must be one of: {valid_types}")
        
        # Validate target
        validation_passed = await feedback_repo.validate_target(survey.survey_type, survey.target_id)
        if not validation_passed:
            raise ValidationError(f"Invalid {survey.survey_type} ID")
        
        # Validate questions
        if not survey.questions:
            raise ValidationError("At least one question is required")
        
        for question in survey.questions:
            if 'question_text' not in question:
                raise ValidationError("Each question must have 'question_text'")
            if 'question_type' not in question:
                raise ValidationError("Each question must have 'question_type'")
        
        # Validate dates
        if survey.end_date and survey.end_date < survey.start_date:
            raise ValidationError("End date must be after start date")
        
        # Create survey
        survey_obj = await feedback_repo.create_survey(
            title=survey.title,
            description=survey.description,
            survey_type=survey.survey_type,
            target_id=survey.target_id,
            questions=survey.questions,
            start_date=survey.start_date,
            end_date=survey.end_date,
            is_active=survey.is_active,
            anonymous_responses=survey.anonymous_responses,
            metadata=survey.metadata,
            created_by_id=auth.get('user_id') or auth.get('id')
        )
        
        return survey_obj
        
    except ValidationError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Validation error: {str(e)}"
        )
    except AuthorizationError:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Insufficient permissions"
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to create survey: {str(e)}"
        )