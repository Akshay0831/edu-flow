"""
Feedback Repository

This module provides the repository layer for Feedback entity operations.
It handles all database interactions related to feedback including CRUD operations,
resolution tracking, sentiment analysis, and feedback analytics.

Author: Edu-Flow Team
"""

from typing import List, Optional, Dict, Any, Type
from datetime import datetime
import logging
from dataclasses import dataclass
from enum import Enum
import json

from src.core.exceptions import DatabaseError, NotFoundError, ValidationError, ConflictError
from src.core.logging import get_logger
from src.infrastructure.repositories.base_repository_with_db import BaseRepositoryWithDB, QueryResult

logger = get_logger(__name__)


class FeedbackType(Enum):
    """Feedback type enumeration."""
    STUDENT_COURSE = "student_course"
    STUDENT_TEACHER = "student_teacher"
    TEACHER_COURSE = "teacher_course"
    TEACHER_PROGRAM = "teacher_program"
    COURSE_PROGRAM = "course_program"
    ALUMNI = "alumni"
    SYSTEM = "system"


class FeedbackStatus(Enum):
    """Feedback status enumeration."""
    PENDING = "pending"
    RESOLVED = "resolved"
    IN_PROGRESS = "in_progress"
    REJECTED = "rejected"
    ESCALATED = "escalated"


class Priority(Enum):
    """Priority enumeration."""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    URGENT = "urgent"


class FeedbackFilter(Enum):
    """Feedback filter types."""
    BY_TYPE = "type"
    BY_STATUS = "status"
    BY_PRIORITY = "priority"
    BY_USER = "user"
    BY_ASSIGNED_TO = "assigned_to"
    BY_DATE_RANGE = "date_range"
    BY_RESOLUTION_DATE = "resolution_date"
    BY_SENTIMENT = "sentiment"
    BY_CATEGORY = "category"


class SortOrder(Enum):
    """Sort order for feedback queries."""
    ASC = "asc"
    DESC = "desc"


@dataclass
class FeedbackQuery:
    """Structured query for feedback operations."""
    filters: Dict[str, Any] = None
    sort_by: str = None
    sort_order: SortOrder = SortOrder.ASC
    limit: int = 100
    offset: int = 0
    search_term: str = None


class FeedbackRepository(BaseRepositoryWithDB):
    """
    Repository for Feedback entity operations.
    
    Handles CRUD operations, resolution tracking, sentiment analysis,
    and feedback analytics.
    """
    
    def __init__(self, database_manager):
        """
        Initialize the feedback repository.
        
        Args:
            database_manager: Database connection manager instance
        """
        super().__init__("feedback", database_manager)
        
    async def create(self, feedback_data: Dict[str, Any]) -> QueryResult:
        """
        Create a new feedback record in the database.
        
        Args:
            feedback_data: Feedback data including all required fields
            
        Returns:
            QueryResult with created feedback
        """
        start_time = datetime.now()
        
        try:
            # Validate feedback data
            if not self._validate_entity_data(feedback_data):
                return self._create_result(error="Invalid feedback data")
            
            # Validate required fields
            required_fields = ['type', 'user_id', 'content']
            for field in required_fields:
                if field not in feedback_data:
                    return self._create_result(error=f"Missing required field: {field}")
            
            # Set default values for optional fields
            feedback_data.setdefault('created_at', datetime.now())
            feedback_data.setdefault('updated_at', datetime.now())
            feedback_data.setdefault('status', FeedbackStatus.PENDING.value)
            feedback_data.setdefault('priority', Priority.MEDIUM.value)
            feedback_data.setdefault('category', '')
            feedback_data.setdefault('assigned_to', None)
            feedback_data.setdefault('resolution_date', None)
            feedback_data.setdefault('resolution_notes', '')
            feedback_data.setdefault('metadata', {})
            feedback_data.setdefault('sentiment_score', 0.0)
            feedback_data.setdefault('sentiment_label', 'neutral')
            feedback_data.setdefault('tags', [])
            
            # Validate feedback type
            if not self._validate_feedback_type(feedback_data):
                return self._create_result(error="Invalid feedback type")
            
            # Convert complex fields to JSON strings for storage
            if 'metadata' in feedback_data:
                feedback_data['metadata'] = json.dumps(feedback_data['metadata'])
            if 'tags' in feedback_data:
                feedback_data['tags'] = json.dumps(feedback_data['tags'])
            
            # Insert into database
            query = """
            INSERT INTO feedback 
            (type, user_id, content, status, priority, category, assigned_to, resolution_date,
             resolution_notes, metadata, sentiment_score, sentiment_label, tags, created_at, updated_at)
            VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11, $12, $13, $14, $15)
            RETURNING *
            """
            
            values = [
                feedback_data['type'],
                feedback_data['user_id'],
                feedback_data['content'],
                feedback_data['status'],
                feedback_data['priority'],
                feedback_data.get('category'),
                feedback_data.get('assigned_to'),
                feedback_data.get('resolution_date'),
                feedback_data.get('resolution_notes'),
                feedback_data.get('metadata'),
                feedback_data['sentiment_score'],
                feedback_data['sentiment_label'],
                feedback_data.get('tags'),
                feedback_data['created_at'],
                feedback_data['updated_at']
            ]
            
            result = await self.db.execute_query(query, values)
            
            if result.success and result.data:
                # Parse JSON fields back to dict
                created_feedback = self._parse_json_fields(result.data[0])
                query_time = (datetime.now() - start_time).total_seconds()
                
                self._log_operation(
                    operation=BaseRepository.RepositoryOperation.CREATE,
                    duration=query_time,
                    success=True
                )
                
                return self._create_result(
                    data=created_feedback,
                    query_time=query_time
                )
            else:
                return self._create_result(error="Failed to create feedback")
                
        except Exception as e:
            query_time = (datetime.now() - start_time).total_seconds()
            self.logger.error(f"Error creating feedback: {str(e)}")
            return self._create_result(
                error=f"Database error creating feedback: {str(e)}",
                query_time=query_time
            )
    
    async def get_by_id(self, feedback_id: str) -> QueryResult:
        """
        Get a feedback record by its ID.
        
        Args:
            feedback_id: Unique identifier for the feedback
            
        Returns:
            QueryResult with the feedback data
        """
        start_time = datetime.now()
        
        try:
            if not self._validate_id(feedback_id):
                return self._create_result(error="Invalid feedback ID")
            
            query = "SELECT * FROM feedback WHERE id = $1"
            result = await self.db.execute_query(query, [feedback_id])
            
            if result.success and result.data:
                feedback = self._parse_json_fields(result.data[0])
                query_time = (datetime.now() - start_time).total_seconds()
                
                self._log_operation(
                    operation=BaseRepository.RepositoryOperation.READ,
                    entity_id=feedback_id,
                    duration=query_time,
                    success=True
                )
                
                return self._create_result(
                    data=feedback,
                    query_time=query_time
                )
            else:
                query_time = (datetime.now() - start_time).total_seconds()
                self._log_operation(
                    operation=BaseRepository.RepositoryOperation.READ,
                    entity_id=feedback_id,
                    duration=query_time,
                    success=False
                )
                return self._create_result(
                    error="Feedback not found",
                    query_time=query_time
                )
                
        except Exception as e:
            query_time = (datetime.now() - start_time).total_seconds()
            self.logger.error(f"Error getting feedback {feedback_id}: {str(e)}")
            return self._create_result(
                error=f"Database error getting feedback: {str(e)}",
                query_time=query_time
            )
    
    async def update(self, feedback_id: str, feedback_data: Dict[str, Any]) -> QueryResult:
        """
        Update an existing feedback record.
        
        Args:
            feedback_id: Unique identifier for the feedback
            feedback_data: Updated data for the feedback
            
        Returns:
            QueryResult with the updated feedback
        """
        start_time = datetime.now()
        
        try:
            if not self._validate_id(feedback_id):
                return self._create_result(error="Invalid feedback ID")
            
            if not self._validate_entity_data(feedback_data):
                return self._create_result(error="Invalid feedback data")
            
            # Check if feedback exists
            existing_result = await self.get_by_id(feedback_id)
            if not existing_result.success:
                return existing_result
            
            existing_feedback = existing_result.data
            
            # Convert complex fields to JSON strings
            if 'metadata' in feedback_data:
                feedback_data['metadata'] = json.dumps(feedback_data['metadata'])
            if 'tags' in feedback_data:
                feedback_data['tags'] = json.dumps(feedback_data['tags'])
            
            # Update timestamp
            feedback_data['updated_at'] = datetime.now()
            
            # Update resolution date if status changed to resolved
            if 'status' in feedback_data and feedback_data['status'] == FeedbackStatus.RESOLVED.value:
                if existing_feedback.get('status') != FeedbackStatus.RESOLVED.value:
                    feedback_data['resolution_date'] = datetime.now()
            
            # Build update query dynamically
            update_fields = []
            values = []
            
            for field, value in feedback_data.items():
                if field != 'id':
                    update_fields.append(f"{field} = ${len(values) + 1}")
                    values.append(value)
            
            values.append(feedback_id)
            query = f"""
            UPDATE feedback 
            SET {', '.join(update_fields)} 
            WHERE id = ${len(values)}
            RETURNING *
            """
            
            result = await self.db.execute_query(query, values)
            
            if result.success and result.data:
                updated_feedback = self._parse_json_fields(result.data[0])
                query_time = (datetime.now() - start_time).total_seconds()
                
                self._log_operation(
                    operation=BaseRepository.RepositoryOperation.UPDATE,
                    entity_id=feedback_id,
                    duration=query_time,
                    success=True
                )
                
                return self._create_result(
                    data=updated_feedback,
                    query_time=query_time
                )
            else:
                query_time = (datetime.now() - start_time).total_seconds()
                return self._create_result(
                    error="Failed to update feedback",
                    query_time=query_time
                )
                
        except Exception as e:
            query_time = (datetime.now() - start_time).total_seconds()
            self.logger.error(f"Error updating feedback {feedback_id}: {str(e)}")
            return self._create_result(
                error=f"Database error updating feedback: {str(e)}",
                query_time=query_time
            )
    
    async def delete(self, feedback_id: str) -> QueryResult:
        """
        Delete a feedback record by its ID.
        
        Args:
            feedback_id: Unique identifier for the feedback
            
        Returns:
            QueryResult with deletion status
        """
        start_time = datetime.now()
        
        try:
            if not self._validate_id(feedback_id):
                return self._create_result(error="Invalid feedback ID")
            
            # Check if feedback exists
            existing_result = await self.get_by_id(feedback_id)
            if not existing_result.success:
                return existing_result
            
            existing_feedback = existing_result.data
            
            # Check if feedback is resolved
            if existing_feedback.get('status') == FeedbackStatus.RESOLVED.value:
                return self._create_result(error="Cannot delete resolved feedback")
            
            # Delete the feedback
            query = "DELETE FROM feedback WHERE id = $1"
            result = await self.db.execute_query(query, [feedback_id])
            
            if result.success:
                query_time = (datetime.now() - start_time).total_seconds()
                
                self._log_operation(
                    operation=BaseRepository.RepositoryOperation.DELETE,
                    entity_id=feedback_id,
                    duration=query_time,
                    success=True
                )
                
                return self._create_result(
                    data={"deleted": True, "feedback_id": feedback_id},
                    query_time=query_time
                )
            else:
                query_time = (datetime.now() - start_time).total_seconds()
                return self._create_result(
                    error="Failed to delete feedback",
                    query_time=query_time
                )
                
        except Exception as e:
            query_time = (datetime.now() - start_time).total_seconds()
            self.logger.error(f"Error deleting feedback {feedback_id}: {str(e)}")
            return self._create_result(
                error=f"Database error deleting feedback: {str(e)}",
                query_time=query_time
            )
    
    async def list_all(self, limit: int = 100, offset: int = 0) -> QueryResult:
        """
        List all feedback records with pagination.
        
        Args:
            limit: Maximum number of feedback records to return
            offset: Number of feedback records to skip
            
        Returns:
            QueryResult with list of feedback records
        """
        start_time = datetime.now()
        
        try:
            query = "SELECT * FROM feedback ORDER BY created_at DESC LIMIT $1 OFFSET $2"
            result = await self.db.execute_query(query, [limit, offset])
            
            if result.success:
                feedback_list = [self._parse_json_fields(fb) for fb in result.data]
                query_time = (datetime.now() - start_time).total_seconds()
                
                # Get total count
                count_query = "SELECT COUNT(*) FROM feedback"
                count_result = await self.db.execute_query(count_query)
                total_count = count_result.data[0][0] if count_result.success else 0
                
                self._log_operation(
                    operation=BaseRepository.RepositoryOperation.LIST,
                    duration=query_time,
                    success=True
                )
                
                return self._create_result(
                    data=feedback_list,
                    total_count=total_count,
                    query_time=query_time
                )
            else:
                query_time = (datetime.now() - start_time).total_seconds()
                return self._create_result(
                    error="Failed to list feedback",
                    query_time=query_time
                )
                
        except Exception as e:
            query_time = (datetime.now() - start_time).total_seconds()
            self.logger.error(f"Error listing feedback: {str(e)}")
            return self._create_result(
                error=f"Database error listing feedback: {str(e)}",
                query_time=query_time
            )
    
    async def search(self, search_term: str, limit: int = 100, offset: int = 0) -> QueryResult:
        """
        Search feedback records by term.
        
        Args:
            search_term: Search term for filtering
            limit: Maximum number of feedback records to return
            offset: Number of feedback records to skip
            
        Returns:
            QueryResult with search results
        """
        start_time = datetime.now()
        
        try:
            if not search_term:
                return await self.list_all(limit, offset)
            
            # Search in content, category, and tags
            query = """
            SELECT * FROM feedback 
            WHERE (LOWER(content) LIKE LOWER($1) OR 
                   LOWER(category) LIKE LOWER($1) OR 
                   LOWER(tags::text) LIKE LOWER($1))
            ORDER BY created_at DESC 
            LIMIT $2 OFFSET $3
            """
            
            search_pattern = f"%{search_term}%"
            result = await self.db.execute_query(query, [search_pattern, limit, offset])
            
            if result.success:
                feedback_list = [self._parse_json_fields(fb) for fb in result.data]
                query_time = (datetime.now() - start_time).total_seconds()
                
                # Get total count
                count_query = """
                SELECT COUNT(*) FROM feedback 
                WHERE (LOWER(content) LIKE LOWER($1) OR 
                       LOWER(category) LIKE LOWER($1) OR 
                       LOWER(tags::text) LIKE LOWER($1))
                """
                count_result = await self.db.execute_query(count_query, [search_pattern])
                total_count = count_result.data[0][0] if count_result.success else 0
                
                self._log_operation(
                    operation=BaseRepository.RepositoryOperation.SEARCH,
                    duration=query_time,
                    success=True
                )
                
                return self._create_result(
                    data=feedback_list,
                    total_count=total_count,
                    query_time=query_time
                )
            else:
                query_time = (datetime.now() - start_time).total_seconds()
                return self._create_result(
                    error="Failed to search feedback",
                    query_time=query_time
                )
                
        except Exception as e:
            query_time = (datetime.now() - start_time).total_seconds()
            self.logger.error(f"Error searching feedback: {str(e)}")
            return self._create_result(
                error=f"Database error searching feedback: {str(e)}",
                query_time=query_time
            )
    
    async def filter(self, filters: Dict[str, Any], limit: int = 100, offset: int = 0) -> QueryResult:
        """
        Filter feedback records by criteria.
        
        Args:
            filters: Filter criteria
            limit: Maximum number of feedback records to return
            offset: Number of feedback records to skip
            
        Returns:
            QueryResult with filtered results
        """
        start_time = datetime.now()
        
        try:
            if not filters:
                return await self.list_all(limit, offset)
            
            # Build query dynamically based on filters
            conditions = []
            values = []
            
            for field, value in filters.items():
                if field == 'type':
                    conditions.append(f"type = ${len(values) + 1}")
                    values.append(value)
                elif field == 'status':
                    conditions.append(f"status = ${len(values) + 1}")
                    values.append(value)
                elif field == 'priority':
                    conditions.append(f"priority = ${len(values) + 1}")
                    values.append(value)
                elif field == 'user_id':
                    conditions.append(f"user_id = ${len(values) + 1}")
                    values.append(value)
                elif field == 'assigned_to':
                    conditions.append(f"assigned_to = ${len(values) + 1}")
                    values.append(value)
                elif field == 'category':
                    conditions.append(f"category = ${len(values) + 1}")
                    values.append(value)
                elif field == 'has_resolution':
                    conditions.append(f"resolution_date IS NOT NULL")
                elif field == 'no_resolution':
                    conditions.append(f"resolution_date IS NULL")
                elif field == 'sentiment':
                    conditions.append(f"sentiment_label = ${len(values) + 1}")
                    values.append(value)
                elif field == 'min_sentiment_score':
                    conditions.append(f"sentiment_score >= ${len(values) + 1}")
                    values.append(value)
                elif field == 'max_sentiment_score':
                    conditions.append(f"sentiment_score <= ${len(values) + 1}")
                    values.append(value)
                elif field == 'min_priority':
                    conditions.append(f"priority >= ${len(values) + 1}")
                    values.append(value)
                elif field == 'keyword':
                    conditions.append(f"(LOWER(content) LIKE LOWER(${len(values) + 1}) OR "
                                    f"LOWER(category) LIKE LOWER(${len(values) + 1}) OR "
                                    f"LOWER(tags::text) LIKE LOWER(${len(values) + 1}))")
                    keyword_pattern = f"%{value}%"
                    values.extend([keyword_pattern, keyword_pattern, keyword_pattern])
            
            query_conditions = " AND ".join(conditions) if conditions else "1=1"
            query = f"SELECT * FROM feedback WHERE {query_conditions} ORDER BY created_at DESC LIMIT ${len(values) + 1} OFFSET ${len(values) + 2}"
            
            values.extend([limit, offset])
            result = await self.db.execute_query(query, values)
            
            if result.success:
                feedback_list = [self._parse_json_fields(fb) for fb in result.data]
                query_time = (datetime.now() - start_time).total_seconds()
                
                # Get total count
                count_query = f"SELECT COUNT(*) FROM feedback WHERE {query_conditions}"
                count_result = await self.db.execute_query(count_query, values[:-2])
                total_count = count_result.data[0][0] if count_result.success else 0
                
                self._log_operation(
                    operation=BaseRepository.RepositoryOperation.FILTER,
                    duration=query_time,
                    success=True
                )
                
                return self._create_result(
                    data=feedback_list,
                    total_count=total_count,
                    query_time=query_time
                )
            else:
                query_time = (datetime.now() - start_time).total_seconds()
                return self._create_result(
                    error="Failed to filter feedback",
                    query_time=query_time
                )
                
        except Exception as e:
            query_time = (datetime.now() - start_time).total_seconds()
            self.logger.error(f"Error filtering feedback: {str(e)}")
            return self._create_result(
                error=f"Database error filtering feedback: {str(e)}",
                query_time=query_time
            )
    
    async def get_user_feedback(self, user_id: str) -> QueryResult:
        """
        Get all feedback records for a specific user.
        
        Args:
            user_id: Unique identifier for the user
            
        Returns:
            QueryResult with user feedback
        """
        start_time = datetime.now()
        
        try:
            if not self._validate_id(user_id):
                return self._create_result(error="Invalid user ID")
            
            query = "SELECT * FROM feedback WHERE user_id = $1 ORDER BY created_at DESC"
            result = await self.db.execute_query(query, [user_id])
            
            if result.success:
                feedback_list = [self._parse_json_fields(fb) for fb in result.data]
                query_time = (datetime.now() - start_time).total_seconds()
                
                self._log_operation(
                    operation=BaseRepository.RepositoryOperation.READ,
                    entity_id=f"user_{user_id}_feedback",
                    duration=query_time,
                    success=True
                )
                
                return self._create_result(
                    data=feedback_list,
                    query_time=query_time
                )
            else:
                query_time = (datetime.now() - start_time).total_seconds()
                return self._create_result(
                    error="Failed to get user feedback",
                    query_time=query_time
                )
                
        except Exception as e:
            query_time = (datetime.now() - start_time).total_seconds()
            self.logger.error(f"Error getting user feedback for {user_id}: {str(e)}")
            return self._create_result(
                error=f"Database error getting user feedback: {str(e)}",
                query_time=query_time
            )
    
    async def get_assigned_feedback(self, assigned_to: str) -> QueryResult:
        """
        Get all feedback assigned to a specific user.
        
        Args:
            assigned_to: Unique identifier for the assigned user
            
        Returns:
            QueryResult with assigned feedback
        """
        start_time = datetime.now()
        
        try:
            if not self._validate_id(assigned_to):
                return self._create_result(error="Invalid assigned user ID")
            
            query = "SELECT * FROM feedback WHERE assigned_to = $1 ORDER BY created_at DESC"
            result = await self.db.execute_query(query, [assigned_to])
            
            if result.success:
                feedback_list = [self._parse_json_fields(fb) for fb in result.data]
                query_time = (datetime.now() - start_time).total_seconds()
                
                self._log_operation(
                    operation=BaseRepository.RepositoryOperation.READ,
                    entity_id=f"assigned_to_{assigned_to}_feedback",
                    duration=query_time,
                    success=True
                )
                
                return self._create_result(
                    data=feedback_list,
                    query_time=query_time
                )
            else:
                query_time = (datetime.now() - start_time).total_seconds()
                return self._create_result(
                    error="Failed to get assigned feedback",
                    query_time=query_time
                )
                
        except Exception as e:
            query_time = (datetime.now() - start_time).total_seconds()
            self.logger.error(f"Error getting assigned feedback for {assigned_to}: {str(e)}")
            return self._create_result(
                error=f"Database error getting assigned feedback: {str(e)}",
                query_time=query_time
            )
    
    async def resolve_feedback(self, feedback_id: str, resolution_notes: str) -> QueryResult:
        """
        Mark a feedback as resolved.
        
        Args:
            feedback_id: Unique identifier for the feedback
            resolution_notes: Resolution notes
            
        Returns:
            QueryResult with updated feedback
        """
        start_time = datetime.now()
        
        try:
            if not self._validate_id(feedback_id):
                return self._create_result(error="Invalid feedback ID")
            
            # Get existing feedback
            existing_result = await self.get_by_id(feedback_id)
            if not existing_result.success:
                return existing_result
            
            existing_feedback = existing_result.data
            
            # Update feedback with resolved status
            update_data = {
                'status': FeedbackStatus.RESOLVED.value,
                'resolution_date': datetime.now(),
                'resolution_notes': resolution_notes
            }
            
            update_result = await self.update(feedback_id, update_data)
            query_time = (datetime.now() - start_time).total_seconds()
            
            self._log_operation(
                operation=BaseRepository.RepositoryOperation.UPDATE,
                entity_id=f"{feedback_id}_resolved",
                duration=query_time,
                success=True
            )
            
            return self._create_result(
                data=update_result.data,
                query_time=query_time
            )
                
        except Exception as e:
            query_time = (datetime.now() - start_time).total_seconds()
            self.logger.error(f"Error resolving feedback {feedback_id}: {str(e)}")
            return self._create_result(
                error=f"Database error resolving feedback: {str(e)}",
                query_time=query_time
            )
    
    async def assign_feedback(self, feedback_id: str, assigned_to: str) -> QueryResult:
        """
        Assign feedback to a specific user.
        
        Args:
            feedback_id: Unique identifier for the feedback
            assigned_to: Unique identifier for the assigned user
            
        Returns:
            QueryResult with updated feedback
        """
        start_time = datetime.now()
        
        try:
            if not self._validate_id(feedback_id):
                return self._create_result(error="Invalid feedback ID")
            
            if not self._validate_id(assigned_to):
                return self._create_result(error="Invalid assigned user ID")
            
            # Update feedback with assigned user and status
            update_data = {
                'assigned_to': assigned_to,
                'status': FeedbackStatus.IN_PROGRESS.value
            }
            
            update_result = await self.update(feedback_id, update_data)
            query_time = (datetime.now() - start_time).total_seconds()
            
            self._log_operation(
                operation=BaseRepository.RepositoryOperation.UPDATE,
                entity_id=f"{feedback_id}_assigned",
                duration=query_time,
                success=True
            )
            
            return self._create_result(
                data=update_result.data,
                query_time=query_time
            )
                
        except Exception as e:
            query_time = (datetime.now() - start_time).total_seconds()
            self.logger.error(f"Error assigning feedback {feedback_id}: {str(e)}")
            return self._create_result(
                error=f"Database error assigning feedback: {str(e)}",
                query_time=query_time
            )
    
    async def get_feedback_statistics(self) -> QueryResult:
        """
        Get feedback statistics.
        
        Returns:
            QueryResult with feedback statistics
        """
        start_time = datetime.now()
        
        try:
            # Get total feedback count
            total_query = "SELECT COUNT(*) FROM feedback"
            total_result = await self.db.execute_query(total_query)
            total_count = total_result.data[0][0] if total_result.success else 0
            
            # Get status distribution
            status_query = """
            SELECT status, COUNT(*) as count 
            FROM feedback 
            GROUP BY status
            """
            status_result = await self.db.execute_query(status_query)
            status_distribution = status_result.data if status_result.success else []
            
            # Get priority distribution
            priority_query = """
            SELECT priority, COUNT(*) as count 
            FROM feedback 
            GROUP BY priority
            """
            priority_result = await self.db.execute_query(priority_query)
            priority_distribution = priority_result.data if priority_result.success else []
            
            # Get sentiment distribution
            sentiment_query = """
            SELECT sentiment_label, COUNT(*) as count 
            FROM feedback 
            GROUP BY sentiment_label
            """
            sentiment_result = await self.db.execute_query(sentiment_query)
            sentiment_distribution = sentiment_result.data if sentiment_result.success else []
            
            # Get type distribution
            type_query = """
            SELECT type, COUNT(*) as count 
            FROM feedback 
            GROUP BY type
            """
            type_result = await self.db.execute_query(type_query)
            type_distribution = type_result.data if type_result.success else []
            
            # Calculate average resolution time
            resolution_query = """
            SELECT AVG(
                EXTRACT(EPOCH FROM (resolution_date - created_at)) / 86400
            ) as avg_days_to_resolve
            FROM feedback 
            WHERE resolution_date IS NOT NULL AND status = 'resolved'
            """
            resolution_result = await self.db.execute_query(resolution_query)
            avg_resolution_days = resolution_result.data[0][0] if resolution_result.success and resolution_result.data else 0.0
            
            query_time = (datetime.now() - start_time).total_seconds()
            self._log_operation(
                operation=BaseRepository.RepositoryOperation.READ,
                entity_id="feedback_statistics",
                duration=query_time,
                success=True
            )
            
            return self._create_result(
                data={
                    'total_feedback': total_count,
                    'status_distribution': status_distribution,
                    'priority_distribution': priority_distribution,
                    'sentiment_distribution': sentiment_distribution,
                    'type_distribution': type_distribution,
                    'average_resolution_days': avg_resolution_days
                },
                query_time=query_time
            )
                
        except Exception as e:
            query_time = (datetime.now() - start_time).total_seconds()
            self.logger.error(f"Error getting feedback statistics: {str(e)}")
            return self._create_result(
                error=f"Database error getting feedback statistics: {str(e)}",
                query_time=query_time
            )
    
    def _validate_feedback_type(self, feedback_data: Dict[str, Any]) -> bool:
        """
        Validate feedback type.
        
        Args:
            feedback_data: Feedback data to validate
            
        Returns:
            True if valid, False otherwise
        """
        try:
            feedback_type = feedback_data.get('type')
            return feedback_type in [member.value for member in FeedbackType]
        except (KeyError, AttributeError):
            return False
    
    def _parse_json_fields(self, feedback_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Parse JSON fields back to dictionary format.
        
        Args:
            feedback_data: Feedback data from database
            
        Returns:
            Feedback data with parsed JSON fields
        """
        if not feedback_data:
            return {}
        
        parsed_data = feedback_data.copy()
        
        # Parse JSON fields
        if 'metadata' in parsed_data and parsed_data['metadata']:
            try:
                parsed_data['metadata'] = json.loads(parsed_data['metadata'])
            except json.JSONDecodeError:
                parsed_data['metadata'] = {}
        
        if 'tags' in parsed_data and parsed_data['tags']:
            try:
                parsed_data['tags'] = json.loads(parsed_data['tags'])
            except json.JSONDecodeError:
                parsed_data['tags'] = []
        
        return parsed_data