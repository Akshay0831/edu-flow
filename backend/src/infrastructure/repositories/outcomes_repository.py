"""
Outcomes Repository

This module provides the repository layer for Outcomes entity operations.
It handles all database interactions related to outcomes including CRUD operations,
performance tracking, CO-PO mapping, achievement analytics, and curriculum assessment.

Author: Edu-Flow Team
"""

from typing import List, Optional, Dict, Any, Type
from datetime import datetime
import logging
from dataclasses import dataclass
from enum import Enum
import json
import statistics

from core.exceptions import DatabaseError, NotFoundError, ValidationError, ConflictError
from core.logging import get_logger
from infrastructure.repositories.base_repository_with_db import BaseRepositoryWithDB, QueryResult

logger = get_logger(__name__)


class OutcomeType(Enum):
    """Outcome type enumeration."""
    PROGRAM_OUTCOME = "program_outcome"
    COURSE_OUTCOME = "course_outcome"
    LEARNING_OUTCOME = "learning_outcome"


class AchievementLevel(Enum):
    """Achievement level enumeration."""
    EXCELLENT = "excellent"
    GOOD = "good"
    AVERAGE = "average"
    BELOW_AVERAGE = "below_average"
    POOR = "poor"


class OutcomeStatus(Enum):
    """Outcome status enumeration."""
    ACTIVE = "active"
    INACTIVE = "inactive"
    UNDER_REVIEW = "under_review"
    OBSOLETE = "obsolete"


class OutcomesFilter(Enum):
    """Outcomes filter types."""
    BY_TYPE = "type"
    BY_PROGRAM = "program"
    BY_COURSE = "course"
    BY_STATUS = "status"
    BY_ACHIEVEMENT = "achievement"
    BY_DATE_RANGE = "date_range"
    BY_DEPARTMENT = "department"
    BY_MAPPING = "mapping"


class SortOrder(Enum):
    """Sort order for outcomes queries."""
    ASC = "asc"
    DESC = "desc"


@dataclass
class OutcomesQuery:
    """Structured query for outcomes operations."""
    filters: Dict[str, Any] = None
    sort_by: str = None
    sort_order: SortOrder = SortOrder.ASC
    limit: int = 100
    offset: int = 0
    search_term: str = None


class OutcomesRepository(BaseRepositoryWithDB):
    """
    Repository for Outcomes entity operations.
    
    Handles CRUD operations, performance tracking, CO-PO mapping,
    achievement analytics, and curriculum assessment.
    """
    
    def __init__(self, database_manager):
        """
        Initialize the outcomes repository.
        
        Args:
            database_manager: Database connection manager instance
        """
        super().__init__("outcomes", database_manager)
        
    async def create(self, outcome_data: Dict[str, Any]) -> QueryResult:
        """
        Create a new outcome in the database.
        
        Args:
            outcome_data: Outcome data including all required fields
            
        Returns:
            QueryResult with created outcome
        """
        start_time = datetime.now()
        
        try:
            # Validate outcome data
            if not self._validate_entity_data(outcome_data):
                return self._create_result(error="Invalid outcome data")
            
            # Validate required fields
            required_fields = ['code', 'title', 'description', 'type', 'status']
            for field in required_fields:
                if field not in outcome_data:
                    return self._create_result(error=f"Missing required field: {field}")
            
            # Set default values for optional fields
            outcome_data.setdefault('created_at', datetime.now())
            outcome_data.setdefault('updated_at', datetime.now())
            outcome_data.setdefault('program_id', None)
            outcome_data.setdefault('course_id', None)
            outcome_data.setdefault('department_id', None)
            outcome_data.setdefault('mapped_courses', [])
            outcome_data.setdefault('mapped_programs', [])
            outcome_data.setdefault('achievement_data', {})
            outcome_data.setdefault('performance_metrics', {})
            outcome_data.setdefault('target_metrics', {})
            outcome_data.setdefault('assessment_criteria', [])
            outcome_data.setdefault('weightage', 0.0)
            outcome_data.setdefault('is_mapped', False)
            outcome_data.setdefault('is_active', True)
            
            # Validate outcome type
            if not self._validate_outcome_type(outcome_data):
                return self._create_result(error="Invalid outcome type")
            
            # Convert complex fields to JSON strings for storage
            if 'mapped_courses' in outcome_data:
                outcome_data['mapped_courses'] = json.dumps(outcome_data['mapped_courses'])
            if 'mapped_programs' in outcome_data:
                outcome_data['mapped_programs'] = json.dumps(outcome_data['mapped_programs'])
            if 'achievement_data' in outcome_data:
                outcome_data['achievement_data'] = json.dumps(outcome_data['achievement_data'])
            if 'performance_metrics' in outcome_data:
                outcome_data['performance_metrics'] = json.dumps(outcome_data['performance_metrics'])
            if 'target_metrics' in outcome_data:
                outcome_data['target_metrics'] = json.dumps(outcome_data['target_metrics'])
            if 'assessment_criteria' in outcome_data:
                outcome_data['assessment_criteria'] = json.dumps(outcome_data['assessment_criteria'])
            
            # Insert into database
            query = """
            INSERT INTO outcomes 
            (code, title, description, type, status, program_id, course_id, department_id,
             mapped_courses, mapped_programs, achievement_data, performance_metrics,
             target_metrics, assessment_criteria, weightage, is_mapped, is_active, created_at, updated_at)
            VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11, $12, $13, $14, $15, $16, $17, $18, $19)
            RETURNING *
            """
            
            values = [
                outcome_data['code'],
                outcome_data['title'],
                outcome_data['description'],
                outcome_data['type'],
                outcome_data['status'],
                outcome_data.get('program_id'),
                outcome_data.get('course_id'),
                outcome_data.get('department_id'),
                outcome_data.get('mapped_courses'),
                outcome_data.get('mapped_programs'),
                outcome_data.get('achievement_data'),
                outcome_data.get('performance_metrics'),
                outcome_data.get('target_metrics'),
                outcome_data.get('assessment_criteria'),
                outcome_data['weightage'],
                outcome_data['is_mapped'],
                outcome_data['is_active'],
                outcome_data['created_at'],
                outcome_data['updated_at']
            ]
            
            result = await self.db.execute_query(query, values)
            
            if result.success and result.data:
                # Parse JSON fields back to dict
                created_outcome = self._parse_json_fields(result.data[0])
                query_time = (datetime.now() - start_time).total_seconds()
                
                self._log_operation(
                    operation=BaseRepository.RepositoryOperation.CREATE,
                    duration=query_time,
                    success=True
                )
                
                return self._create_result(
                    data=created_outcome,
                    query_time=query_time
                )
            else:
                return self._create_result(error="Failed to create outcome")
                
        except Exception as e:
            query_time = (datetime.now() - start_time).total_seconds()
            self.logger.error(f"Error creating outcome: {str(e)}")
            return self._create_result(
                error=f"Database error creating outcome: {str(e)}",
                query_time=query_time
            )
    
    async def get_by_id(self, outcome_id: str) -> QueryResult:
        """
        Get an outcome by its ID.
        
        Args:
            outcome_id: Unique identifier for the outcome
            
        Returns:
            QueryResult with the outcome data
        """
        start_time = datetime.now()
        
        try:
            if not self._validate_id(outcome_id):
                return self._create_result(error="Invalid outcome ID")
            
            query = "SELECT * FROM outcomes WHERE id = $1"
            result = await self.db.execute_query(query, [outcome_id])
            
            if result.success and result.data:
                outcome = self._parse_json_fields(result.data[0])
                query_time = (datetime.now() - start_time).total_seconds()
                
                self._log_operation(
                    operation=BaseRepository.RepositoryOperation.READ,
                    entity_id=outcome_id,
                    duration=query_time,
                    success=True
                )
                
                return self._create_result(
                    data=outcome,
                    query_time=query_time
                )
            else:
                query_time = (datetime.now() - start_time).total_seconds()
                self._log_operation(
                    operation=BaseRepository.RepositoryOperation.READ,
                    entity_id=outcome_id,
                    duration=query_time,
                    success=False
                )
                return self._create_result(
                    error="Outcome not found",
                    query_time=query_time
                )
                
        except Exception as e:
            query_time = (datetime.now() - start_time).total_seconds()
            self.logger.error(f"Error getting outcome {outcome_id}: {str(e)}")
            return self._create_result(
                error=f"Database error getting outcome: {str(e)}",
                query_time=query_time
            )
    
    async def update(self, outcome_id: str, outcome_data: Dict[str, Any]) -> QueryResult:
        """
        Update an existing outcome.
        
        Args:
            outcome_id: Unique identifier for the outcome
            outcome_data: Updated data for the outcome
            
        Returns:
            QueryResult with the updated outcome
        """
        start_time = datetime.now()
        
        try:
            if not self._validate_id(outcome_id):
                return self._create_result(error="Invalid outcome ID")
            
            if not self._validate_entity_data(outcome_data):
                return self._create_result(error="Invalid outcome data")
            
            # Check if outcome exists
            existing_result = await self.get_by_id(outcome_id)
            if not existing_result.success:
                return existing_result
            
            existing_outcome = existing_result.data
            
            # Convert complex fields to JSON strings
            if 'mapped_courses' in outcome_data:
                outcome_data['mapped_courses'] = json.dumps(outcome_data['mapped_courses'])
            if 'mapped_programs' in outcome_data:
                outcome_data['mapped_programs'] = json.dumps(outcome_data['mapped_programs'])
            if 'achievement_data' in outcome_data:
                outcome_data['achievement_data'] = json.dumps(outcome_data['achievement_data'])
            if 'performance_metrics' in outcome_data:
                outcome_data['performance_metrics'] = json.dumps(outcome_data['performance_metrics'])
            if 'target_metrics' in outcome_data:
                outcome_data['target_metrics'] = json.dumps(outcome_data['target_metrics'])
            if 'assessment_criteria' in outcome_data:
                outcome_data['assessment_criteria'] = json.dumps(outcome_data['assessment_criteria'])
            
            # Update timestamp
            outcome_data['updated_at'] = datetime.now()
            
            # Build update query dynamically
            update_fields = []
            values = []
            
            for field, value in outcome_data.items():
                if field != 'id':
                    update_fields.append(f"{field} = ${len(values) + 1}")
                    values.append(value)
            
            values.append(outcome_id)
            query = f"""
            UPDATE outcomes 
            SET {', '.join(update_fields)} 
            WHERE id = ${len(values)}
            RETURNING *
            """
            
            result = await self.db.execute_query(query, values)
            
            if result.success and result.data:
                updated_outcome = self._parse_json_fields(result.data[0])
                query_time = (datetime.now() - start_time).total_seconds()
                
                self._log_operation(
                    operation=BaseRepository.RepositoryOperation.UPDATE,
                    entity_id=outcome_id,
                    duration=query_time,
                    success=True
                )
                
                return self._create_result(
                    data=updated_outcome,
                    query_time=query_time
                )
            else:
                query_time = (datetime.now() - start_time).total_seconds()
                return self._create_result(
                    error="Failed to update outcome",
                    query_time=query_time
                )
                
        except Exception as e:
            query_time = (datetime.now() - start_time).total_seconds()
            self.logger.error(f"Error updating outcome {outcome_id}: {str(e)}")
            return self._create_result(
                error=f"Database error updating outcome: {str(e)}",
                query_time=query_time
            )
    
    async def delete(self, outcome_id: str) -> QueryResult:
        """
        Delete an outcome by its ID.
        
        Args:
            outcome_id: Unique identifier for the outcome
            
        Returns:
            QueryResult with deletion status
        """
        start_time = datetime.now()
        
        try:
            if not self._validate_id(outcome_id):
                return self._create_result(error="Invalid outcome ID")
            
            # Check if outcome exists
            existing_result = await self.get_by_id(outcome_id)
            if not existing_result.success:
                return existing_result
            
            existing_outcome = existing_result.data
            
            # Check if outcome is mapped
            if existing_outcome.get('is_mapped'):
                return self._create_result(error="Cannot delete mapped outcome")
            
            # Delete the outcome
            query = "DELETE FROM outcomes WHERE id = $1"
            result = await self.db.execute_query(query, [outcome_id])
            
            if result.success:
                query_time = (datetime.now() - start_time).total_seconds()
                
                self._log_operation(
                    operation=BaseRepository.RepositoryOperation.DELETE,
                    entity_id=outcome_id,
                    duration=query_time,
                    success=True
                )
                
                return self._create_result(
                    data={"deleted": True, "outcome_id": outcome_id},
                    query_time=query_time
                )
            else:
                query_time = (datetime.now() - start_time).total_seconds()
                return self._create_result(
                    error="Failed to delete outcome",
                    query_time=query_time
                )
                
        except Exception as e:
            query_time = (datetime.now() - start_time).total_seconds()
            self.logger.error(f"Error deleting outcome {outcome_id}: {str(e)}")
            return self._create_result(
                error=f"Database error deleting outcome: {str(e)}",
                query_time=query_time
            )
    
    async def list_all(self, limit: int = 100, offset: int = 0) -> QueryResult:
        """
        List all outcomes with pagination.
        
        Args:
            limit: Maximum number of outcomes to return
            offset: Number of outcomes to skip
            
        Returns:
            QueryResult with list of outcomes
        """
        start_time = datetime.now()
        
        try:
            query = "SELECT * FROM outcomes ORDER BY created_at DESC LIMIT $1 OFFSET $2"
            result = await self.db.execute_query(query, [limit, offset])
            
            if result.success:
                outcomes = [self._parse_json_fields(outcome) for outcome in result.data]
                query_time = (datetime.now() - start_time).total_seconds()
                
                # Get total count
                count_query = "SELECT COUNT(*) FROM outcomes"
                count_result = await self.db.execute_query(count_query)
                total_count = count_result.data[0][0] if count_result.success else 0
                
                self._log_operation(
                    operation=BaseRepository.RepositoryOperation.LIST,
                    duration=query_time,
                    success=True
                )
                
                return self._create_result(
                    data=outcomes,
                    total_count=total_count,
                    query_time=query_time
                )
            else:
                query_time = (datetime.now() - start_time).total_seconds()
                return self._create_result(
                    error="Failed to list outcomes",
                    query_time=query_time
                )
                
        except Exception as e:
            query_time = (datetime.now() - start_time).total_seconds()
            self.logger.error(f"Error listing outcomes: {str(e)}")
            return self._create_result(
                error=f"Database error listing outcomes: {str(e)}",
                query_time=query_time
            )
    
    async def search(self, search_term: str, limit: int = 100, offset: int = 0) -> QueryResult:
        """
        Search outcomes by term.
        
        Args:
            search_term: Search term for filtering
            limit: Maximum number of outcomes to return
            offset: Number of outcomes to skip
            
        Returns:
            QueryResult with search results
        """
        start_time = datetime.now()
        
        try:
            if not search_term:
                return await self.list_all(limit, offset)
            
            # Search in code, title, description, and mapped_courses
            query = """
            SELECT * FROM outcomes 
            WHERE (LOWER(code) LIKE LOWER($1) OR 
                   LOWER(title) LIKE LOWER($1) OR 
                   LOWER(description) LIKE LOWER($1) OR
                   LOWER(mapped_courses::text) LIKE LOWER($1))
            ORDER BY created_at DESC 
            LIMIT $2 OFFSET $3
            """
            
            search_pattern = f"%{search_term}%"
            result = await self.db.execute_query(query, [search_pattern, limit, offset])
            
            if result.success:
                outcomes = [self._parse_json_fields(outcome) for outcome in result.data]
                query_time = (datetime.now() - start_time).total_seconds()
                
                # Get total count
                count_query = """
                SELECT COUNT(*) FROM outcomes 
                WHERE (LOWER(code) LIKE LOWER($1) OR 
                       LOWER(title) LIKE LOWER($1) OR 
                       LOWER(description) LIKE LOWER($1) OR
                       LOWER(mapped_courses::text) LIKE LOWER($1))
                """
                count_result = await self.db.execute_query(count_query, [search_pattern])
                total_count = count_result.data[0][0] if count_result.success else 0
                
                self._log_operation(
                    operation=BaseRepository.RepositoryOperation.SEARCH,
                    duration=query_time,
                    success=True
                )
                
                return self._create_result(
                    data=outcomes,
                    total_count=total_count,
                    query_time=query_time
                )
            else:
                query_time = (datetime.now() - start_time).total_seconds()
                return self._create_result(
                    error="Failed to search outcomes",
                    query_time=query_time
                )
                
        except Exception as e:
            query_time = (datetime.now() - start_time).total_seconds()
            self.logger.error(f"Error searching outcomes: {str(e)}")
            return self._create_result(
                error=f"Database error searching outcomes: {str(e)}",
                query_time=query_time
            )
    
    async def filter(self, filters: Dict[str, Any], limit: int = 100, offset: int = 0) -> QueryResult:
        """
        Filter outcomes by criteria.
        
        Args:
            filters: Filter criteria
            limit: Maximum number of outcomes to return
            offset: Number of outcomes to skip
            
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
                elif field == 'program_id':
                    conditions.append(f"program_id = ${len(values) + 1}")
                    values.append(value)
                elif field == 'course_id':
                    conditions.append(f"course_id = ${len(values) + 1}")
                    values.append(value)
                elif field == 'department_id':
                    conditions.append(f"department_id = ${len(values) + 1}")
                    values.append(value)
                elif field == 'status':
                    conditions.append(f"status = ${len(values) + 1}")
                    values.append(value)
                elif field == 'is_mapped':
                    conditions.append(f"is_mapped = ${len(values) + 1}")
                    values.append(value)
                elif field == 'is_active':
                    conditions.append(f"is_active = ${len(values) + 1}")
                    values.append(value)
                elif field == 'min_weightage':
                    conditions.append(f"weightage >= ${len(values) + 1}")
                    values.append(value)
                elif field == 'max_weightage':
                    conditions.append(f"weightage <= ${len(values) + 1}")
                    values.append(value)
                elif field == 'mapped_to_programs':
                    conditions.append(f"mapped_programs LIKE ${len(values) + 1}")
                    values.append(f"%{value}%")
                elif field == 'mapped_to_courses':
                    conditions.append(f"mapped_courses LIKE ${len(values) + 1}")
                    values.append(f"%{value}%")
                elif field == 'achievement_level':
                    conditions.append(f"achievement_data ->> 'achievement_level' = ${len(values) + 1}")
                    values.append(value)
                elif field == 'keyword':
                    conditions.append(f"(LOWER(code) LIKE LOWER(${len(values) + 1}) OR "
                                    f"LOWER(title) LIKE LOWER(${len(values) + 1}) OR "
                                    f"LOWER(description) LIKE LOWER(${len(values) + 1}))")
                    keyword_pattern = f"%{value}%"
                    values.extend([keyword_pattern, keyword_pattern, keyword_pattern])
            
            query_conditions = " AND ".join(conditions) if conditions else "1=1"
            query = f"SELECT * FROM outcomes WHERE {query_conditions} ORDER BY created_at DESC LIMIT ${len(values) + 1} OFFSET ${len(values) + 2}"
            
            values.extend([limit, offset])
            result = await self.db.execute_query(query, values)
            
            if result.success:
                outcomes = [self._parse_json_fields(outcome) for outcome in result.data]
                query_time = (datetime.now() - start_time).total_seconds()
                
                # Get total count
                count_query = f"SELECT COUNT(*) FROM outcomes WHERE {query_conditions}"
                count_result = await self.db.execute_query(count_query, values[:-2])
                total_count = count_result.data[0][0] if count_result.success else 0
                
                self._log_operation(
                    operation=BaseRepository.RepositoryOperation.FILTER,
                    duration=query_time,
                    success=True
                )
                
                return self._create_result(
                    data=outcomes,
                    total_count=total_count,
                    query_time=query_time
                )
            else:
                query_time = (datetime.now() - start_time).total_seconds()
                return self._create_result(
                    error="Failed to filter outcomes",
                    query_time=query_time
                )
                
        except Exception as e:
            query_time = (datetime.now() - start_time).total_seconds()
            self.logger.error(f"Error filtering outcomes: {str(e)}")
            return self._create_result(
                error=f"Database error filtering outcomes: {str(e)}",
                query_time=query_time
            )
    
    async def get_program_outcomes(self, program_id: str) -> QueryResult:
        """
        Get all outcomes for a specific program.
        
        Args:
            program_id: Unique identifier for the program
            
        Returns:
            QueryResult with program outcomes
        """
        start_time = datetime.now()
        
        try:
            if not self._validate_id(program_id):
                return self._create_result(error="Invalid program ID")
            
            query = "SELECT * FROM outcomes WHERE type = 'program_outcome' AND program_id = $1 ORDER BY weightage DESC"
            result = await self.db.execute_query(query, [program_id])
            
            if result.success:
                outcomes = [self._parse_json_fields(outcome) for outcome in result.data]
                query_time = (datetime.now() - start_time).total_seconds()
                
                self._log_operation(
                    operation=BaseRepository.RepositoryOperation.READ,
                    entity_id=f"program_{program_id}_outcomes",
                    duration=query_time,
                    success=True
                )
                
                return self._create_result(
                    data=outcomes,
                    query_time=query_time
                )
            else:
                query_time = (datetime.now() - start_time).total_seconds()
                return self._create_result(
                    error="Failed to get program outcomes",
                    query_time=query_time
                )
                
        except Exception as e:
            query_time = (datetime.now() - start_time).total_seconds()
            self.logger.error(f"Error getting program outcomes for {program_id}: {str(e)}")
            return self._create_result(
                error=f"Database error getting program outcomes: {str(e)}",
                query_time=query_time
            )
    
    async def get_course_outcomes(self, course_id: str) -> QueryResult:
        """
        Get all outcomes for a specific course.
        
        Args:
            course_id: Unique identifier for the course
            
        Returns:
            QueryResult with course outcomes
        """
        start_time = datetime.now()
        
        try:
            if not self._validate_id(course_id):
                return self._create_result(error="Invalid course ID")
            
            query = "SELECT * FROM outcomes WHERE type = 'course_outcome' AND course_id = $1 ORDER BY weightage DESC"
            result = await self.db.execute_query(query, [course_id])
            
            if result.success:
                outcomes = [self._parse_json_fields(outcome) for outcome in result.data]
                query_time = (datetime.now() - start_time).total_seconds()
                
                self._log_operation(
                    operation=BaseRepository.RepositoryOperation.READ,
                    entity_id=f"course_{course_id}_outcomes",
                    duration=query_time,
                    success=True
                )
                
                return self._create_result(
                    data=outcomes,
                    query_time=query_time
                )
            else:
                query_time = (datetime.now() - start_time).total_seconds()
                return self._create_result(
                    error="Failed to get course outcomes",
                    query_time=query_time
                )
                
        except Exception as e:
            query_time = (datetime.now() - start_time).total_seconds()
            self.logger.error(f"Error getting course outcomes for {course_id}: {str(e)}")
            return self._create_result(
                error=f"Database error getting course outcomes: {str(e)}",
                query_time=query_time
            )
    
    async def update_achievement_data(self, outcome_id: str, achievement_data: Dict[str, Any]) -> QueryResult:
        """
        Update achievement data for an outcome.
        
        Args:
            outcome_id: Unique identifier for the outcome
            achievement_data: Achievement data to update
            
        Returns:
            QueryResult with updated outcome
        """
        start_time = datetime.now()
        
        try:
            if not self._validate_id(outcome_id):
                return self._create_result(error="Invalid outcome ID")
            
            # Get existing outcome
            existing_result = await self.get_by_id(outcome_id)
            if not existing_result.success:
                return existing_result
            
            existing_outcome = existing_result.data
            
            # Update achievement data
            current_achievement = existing_outcome.get('achievement_data', {})
            current_achievement.update(achievement_data)
            
            update_result = await self.update(outcome_id, {'achievement_data': current_achievement})
            query_time = (datetime.now() - start_time).total_seconds()
            
            self._log_operation(
                operation=BaseRepository.RepositoryOperation.UPDATE,
                entity_id=f"{outcome_id}_achievement",
                duration=query_time,
                success=True
            )
            
            return self._create_result(
                data=update_result.data,
                query_time=query_time
            )
                
        except Exception as e:
            query_time = (datetime.now() - start_time).total_seconds()
            self.logger.error(f"Error updating achievement data for outcome {outcome_id}: {str(e)}")
            return self._create_result(
                error=f"Database error updating achievement data: {str(e)}",
                query_time=query_time
            )
    
    async def calculate_program_achievement_rate(self, program_id: str) -> QueryResult:
        """
        Calculate achievement rate for all outcomes in a program.
        
        Args:
            program_id: Unique identifier for the program
            
        Returns:
            QueryResult with achievement rate calculation
        """
        start_time = datetime.now()
        
        try:
            if not self._validate_id(program_id):
                return self._create_result(error="Invalid program ID")
            
            # Get all program outcomes
            program_outcomes_result = await self.get_program_outcomes(program_id)
            if not program_outcomes_result.success:
                return program_outcomes_result
            
            program_outcomes = program_outcomes_result.data
            if not program_outcomes:
                return self._create_result(
                    data={
                        'program_id': program_id,
                        'achievement_rate': 0.0,
                        'total_outcomes': 0,
                        'achieved_outcomes': 0
                    },
                    query_time=(datetime.now() - start_time).total_seconds()
                )
            
            # Calculate achievement rates
            total_achievement_rate = 0.0
            achieved_outcomes = 0
            
            for outcome in program_outcomes:
                achievement_data = outcome.get('achievement_data', {})
                achievement_rate = achievement_data.get('achievement_rate', 0.0)
                
                if achievement_rate >= 0.7:  # Consider achieved if rate >= 70%
                    achieved_outcomes += 1
                
                total_achievement_rate += achievement_rate
            
            # Calculate overall achievement rate
            overall_rate = total_achievement_rate / len(program_outcomes) if program_outcomes else 0.0
            
            query_time = (datetime.now() - start_time).total_seconds()
            self._log_operation(
                operation=BaseRepository.RepositoryOperation.READ,
                entity_id=f"program_{program_id}_achievement",
                duration=query_time,
                success=True
            )
            
            return self._create_result(
                data={
                    'program_id': program_id,
                    'achievement_rate': overall_rate,
                    'total_outcomes': len(program_outcomes),
                    'achieved_outcomes': achieved_outcomes,
                    'achievement_percentage': (achieved_outcomes / len(program_outcomes)) * 100 if program_outcomes else 0.0
                },
                query_time=query_time
            )
                
        except Exception as e:
            query_time = (datetime.now() - start_time).total_seconds()
            self.logger.error(f"Error calculating program achievement rate for {program_id}: {str(e)}")
            return self._create_result(
                error=f"Database error calculating program achievement rate: {str(e)}",
                query_time=query_time
            )
    
    async def get_outcome_mapping_report(self, program_id: str) -> QueryResult:
        """
        Get CO-PO mapping report for a program.
        
        Args:
            program_id: Unique identifier for the program
            
        Returns:
            QueryResult with mapping report
        """
        start_time = datetime.now()
        
        try:
            if not self._validate_id(program_id):
                return self._create_result(error="Invalid program ID")
            
            # Get program outcomes
            program_outcomes_result = await self.get_program_outcomes(program_id)
            if not program_outcomes_result.success:
                return program_outcomes_result
            
            program_outcomes = program_outcomes_result.data
            
            # Get course outcomes
            course_ids = []
            mapping_data = []
            
            for outcome in program_outcomes:
                mapped_courses = outcome.get('mapped_courses', [])
                for course_id in mapped_courses:
                    if course_id not in course_ids:
                        course_ids.append(course_id)
            
            # Get course outcomes for each course
            course_outcomes_data = {}
            for course_id in course_ids:
                course_outcomes_result = await self.get_course_outcomes(course_id)
                if course_outcomes_result.success:
                    course_outcomes_data[course_id] = course_outcomes_result.data
            
            # Build mapping report
            for outcome in program_outcomes:
                mapped_courses = outcome.get('mapped_courses', [])
                mapping_info = {
                    'program_outcome_code': outcome['code'],
                    'program_outcome_title': outcome['title'],
                    'mapped_courses': [],
                    'mapping_completeness': 0.0
                }
                
                total_mappings = len(mapped_courses)
                completed_mappings = 0
                
                for course_id in mapped_courses:
                    course_outcomes = course_outcomes_data.get(course_id, [])
                    mapping_completeness = 0.0
                    
                    for course_outcome in course_outcomes:
                        if outcome['code'] in course_outcome.get('mapped_programs', []):
                            completed_mappings += 1
                            mapping_completeness += 1
                    
                    mapping_info['mapped_courses'].append({
                        'course_id': course_id,
                        'mapping_completeness': mapping_completeness / len(course_outcomes) if course_outcomes else 0.0
                    })
                
                mapping_info['mapping_completeness'] = completed_mappings / total_mappings if total_mappings > 0 else 0.0
                mapping_data.append(mapping_info)
            
            # Calculate overall mapping statistics
            total_mappings = len(mapping_data)
            completed_mappings = sum(1 for mapping in mapping_data if mapping['mapping_completeness'] > 0.7)
            overall_completeness = sum(mapping['mapping_completeness'] for mapping in mapping_data) / total_mappings if total_mappings > 0 else 0.0
            
            query_time = (datetime.now() - start_time).total_seconds()
            self._log_operation(
                operation=BaseRepository.RepositoryOperation.READ,
                entity_id=f"program_{program_id}_mapping",
                duration=query_time,
                success=True
            )
            
            return self._create_result(
                data={
                    'program_id': program_id,
                    'total_program_outcomes': total_mappings,
                    'mapped_program_outcomes': completed_mappings,
                    'overall_mapping_completeness': overall_completeness,
                    'mapping_percentage': (completed_mappings / total_mappings) * 100 if total_mappings > 0 else 0.0,
                    'detailed_mappings': mapping_data
                },
                query_time=query_time
            )
                
        except Exception as e:
            query_time = (datetime.now() - start_time).total_seconds()
            self.logger.error(f"Error getting outcome mapping report for {program_id}: {str(e)}")
            return self._create_result(
                error=f"Database error getting outcome mapping report: {str(e)}",
                query_time=query_time
            )
    
    def _validate_outcome_type(self, outcome_data: Dict[str, Any]) -> bool:
        """
        Validate outcome type.
        
        Args:
            outcome_data: Outcome data to validate
            
        Returns:
            True if valid, False otherwise
        """
        try:
            outcome_type = outcome_data.get('type')
            return outcome_type in [member.value for member in OutcomeType]
        except (KeyError, AttributeError):
            return False
    
    def _parse_json_fields(self, outcome_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Parse JSON fields back to dictionary format.
        
        Args:
            outcome_data: Outcome data from database
            
        Returns:
            Outcome data with parsed JSON fields
        """
        if not outcome_data:
            return {}
        
        parsed_data = outcome_data.copy()
        
        # Parse JSON fields
        if 'mapped_courses' in parsed_data and parsed_data['mapped_courses']:
            try:
                parsed_data['mapped_courses'] = json.loads(parsed_data['mapped_courses'])
            except json.JSONDecodeError:
                parsed_data['mapped_courses'] = []
        
        if 'mapped_programs' in parsed_data and parsed_data['mapped_programs']:
            try:
                parsed_data['mapped_programs'] = json.loads(parsed_data['mapped_programs'])
            except json.JSONDecodeError:
                parsed_data['mapped_programs'] = []
        
        if 'achievement_data' in parsed_data and parsed_data['achievement_data']:
            try:
                parsed_data['achievement_data'] = json.loads(parsed_data['achievement_data'])
            except json.JSONDecodeError:
                parsed_data['achievement_data'] = {}
        
        if 'performance_metrics' in parsed_data and parsed_data['performance_metrics']:
            try:
                parsed_data['performance_metrics'] = json.loads(parsed_data['performance_metrics'])
            except json.JSONDecodeError:
                parsed_data['performance_metrics'] = {}
        
        if 'target_metrics' in parsed_data and parsed_data['target_metrics']:
            try:
                parsed_data['target_metrics'] = json.loads(parsed_data['target_metrics'])
            except json.JSONDecodeError:
                parsed_data['target_metrics'] = {}
        
        if 'assessment_criteria' in parsed_data and parsed_data['assessment_criteria']:
            try:
                parsed_data['assessment_criteria'] = json.loads(parsed_data['assessment_criteria'])
            except json.JSONDecodeError:
                parsed_data['assessment_criteria'] = []
        
        return parsed_data