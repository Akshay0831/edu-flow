"""
Class Repository

This module provides the repository layer for Class entity operations.
It handles all database interactions related to classes including CRUD operations,
enrollment management, scheduling, conflict detection, and capacity management.

Author: Edu-Flow Team
"""

from typing import List, Optional, Dict, Any, Type
from datetime import datetime, time
import logging
from dataclasses import dataclass
from enum import Enum
import json

from src.core.exceptions import DatabaseError, NotFoundError, ValidationError, ConflictError
from src.core.logging import get_logger
from src.infrastructure.repositories.base_repository import BaseRepository, QueryResult
from src.domain.classes.class_entity import Class

logger = get_logger(__name__)


class ClassStatus(Enum):
    """Class status types."""
    SCHEDULED = "scheduled"
    ONGOING = "ongoing"
    COMPLETED = "completed"
    CANCELLED = "cancelled"
    FULL = "full"


class ClassFilter(Enum):
    """Class filter types."""
    BY_TEACHER = "teacher"
    BY_SUBJECT = "subject"
    BY_SEMESTER = "semester"
    BY_DEPARTMENT = "department"
    BY_STATUS = "status"
    BY_CAPACITY = "capacity"
    BY_SCHEDULE = "schedule"
    BY_TIME_SLOT = "time_slot"


class SortOrder(Enum):
    """Sort order for class queries."""
    ASC = "asc"
    DESC = "desc"


@dataclass
class ClassQuery:
    """Structured query for class operations."""
    filters: Dict[str, Any] = None
    sort_by: str = None
    sort_order: SortOrder = SortOrder.ASC
    limit: int = 100
    offset: int = 0
    search_term: str = None


class ClassRepository(BaseRepository):
    """
    Repository for Class entity operations.
    
    Handles CRUD operations, enrollment management, scheduling, 
    conflict detection, and capacity management.
    """
    
    def __init__(self, database_manager):
        """
        Initialize the class repository.
        
        Args:
            database_manager: Database connection manager instance
        """
        super().__init__("classes")
        self.db = database_manager
        self.logger = get_logger(f"{__name__}.{self.__class__.__name__}")
        
    async def create(self, class_data: Dict[str, Any]) -> QueryResult:
        """
        Create a new class in the database.
        
        Args:
            class_data: Class data including all required fields
            
        Returns:
            QueryResult with created class
        """
        start_time = datetime.now()
        
        try:
            # Validate class data
            if not self._validate_entity_data(class_data):
                return self._create_result(error="Invalid class data")
            
            # Validate required fields
            required_fields = ['code', 'name', 'subject_id', 'teacher_id', 'semester', 'max_capacity']
            for field in required_fields:
                if field not in class_data:
                    return self._create_result(error=f"Missing required field: {field}")
            
            # Validate schedule
            if 'schedule' in class_data:
                if not self._validate_schedule(class_data['schedule']):
                    return self._create_result(error="Invalid schedule format")
            
            # Set default values for optional fields
            class_data.setdefault('created_at', datetime.now())
            class_data.setdefault('updated_at', datetime.now())
            class_data.setdefault('status', ClassStatus.SCHEDULED.value)
            class_data.setdefault('current_enrollment', 0)
            class_data.setdefault('room', None)
            class_data.setdefault('description', '')
            class_data.setdefault('metadata', {})
            
            # Convert complex fields to JSON strings for storage
            if 'schedule' in class_data:
                class_data['schedule'] = json.dumps(class_data['schedule'])
            if 'metadata' in class_data:
                class_data['metadata'] = json.dumps(class_data['metadata'])
            
            # Check for schedule conflicts
            conflict_result = await self._check_schedule_conflict(
                class_data['subject_id'], 
                class_data.get('semester', ''),
                class_data['schedule']
            )
            
            if not conflict_result.success:
                return conflict_result
            
            # Insert into database
            query = """
            INSERT INTO classes 
            (code, name, subject_id, teacher_id, semester, max_capacity, current_enrollment,
             schedule, room, description, status, metadata, created_at, updated_at)
            VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11, $12, $13, $14)
            RETURNING *
            """
            
            values = [
                class_data['code'],
                class_data['name'],
                class_data['subject_id'],
                class_data['teacher_id'],
                class_data['semester'],
                class_data['max_capacity'],
                class_data.get('current_enrollment', 0),
                class_data.get('schedule'),
                class_data.get('room'),
                class_data.get('description', ''),
                class_data.get('status'),
                class_data.get('metadata'),
                class_data['created_at'],
                class_data['updated_at']
            ]
            
            result = await self.db.execute_query(query, values)
            
            if result.success and result.data:
                # Parse JSON fields back to dict
                created_class = self._parse_json_fields(result.data[0])
                query_time = (datetime.now() - start_time).total_seconds()
                
                self._log_operation(
                    operation=BaseRepository.RepositoryOperation.CREATE,
                    duration=query_time,
                    success=True
                )
                
                return self._create_result(
                    data=created_class,
                    query_time=query_time
                )
            else:
                return self._create_result(error="Failed to create class")
                
        except Exception as e:
            query_time = (datetime.now() - start_time).total_seconds()
            self.logger.error(f"Error creating class: {str(e)}")
            return self._create_result(
                error=f"Database error creating class: {str(e)}",
                query_time=query_time
            )
    
    async def get_by_id(self, class_id: str) -> QueryResult:
        """
        Get a class by its ID.
        
        Args:
            class_id: Unique identifier for the class
            
        Returns:
            QueryResult with the class data
        """
        start_time = datetime.now()
        
        try:
            if not self._validate_id(class_id):
                return self._create_result(error="Invalid class ID")
            
            query = "SELECT * FROM classes WHERE id = $1"
            result = await self.db.execute_query(query, [class_id])
            
            if result.success and result.data:
                class_entity = self._parse_json_fields(result.data[0])
                query_time = (datetime.now() - start_time).total_seconds()
                
                self._log_operation(
                    operation=BaseRepository.RepositoryOperation.READ,
                    entity_id=class_id,
                    duration=query_time,
                    success=True
                )
                
                return self._create_result(
                    data=class_entity,
                    query_time=query_time
                )
            else:
                query_time = (datetime.now() - start_time).total_seconds()
                self._log_operation(
                    operation=BaseRepository.RepositoryOperation.READ,
                    entity_id=class_id,
                    duration=query_time,
                    success=False
                )
                return self._create_result(
                    error="Class not found",
                    query_time=query_time
                )
                
        except Exception as e:
            query_time = (datetime.now() - start_time).total_seconds()
            self.logger.error(f"Error getting class {class_id}: {str(e)}")
            return self._create_result(
                error=f"Database error getting class: {str(e)}",
                query_time=query_time
            )
    
    async def update(self, class_id: str, class_data: Dict[str, Any]) -> QueryResult:
        """
        Update an existing class.
        
        Args:
            class_id: Unique identifier for the class
            class_data: Updated data for the class
            
        Returns:
            QueryResult with the updated class
        """
        start_time = datetime.now()
        
        try:
            if not self._validate_id(class_id):
                return self._create_result(error="Invalid class ID")
            
            if not self._validate_entity_data(class_data):
                return self._create_result(error="Invalid class data")
            
            # Check if class exists
            existing_result = await self.get_by_id(class_id)
            if not existing_result.success:
                return existing_result
            
            existing_class = existing_result.data
            
            # Validate updated schedule if provided
            if 'schedule' in class_data:
                if not self._validate_schedule(class_data['schedule']):
                    return self._create_result(error="Invalid schedule format")
                
                # Check for schedule conflicts (excluding current class)
                conflict_result = await self._check_schedule_conflict(
                    existing_class['subject_id'],
                    existing_class['semester'],
                    class_data['schedule'],
                    exclude_class_id=class_id
                )
                
                if not conflict_result.success:
                    return conflict_result
            
            # Convert complex fields to JSON strings
            if 'schedule' in class_data:
                class_data['schedule'] = json.dumps(class_data['schedule'])
            if 'metadata' in class_data:
                class_data['metadata'] = json.dumps(class_data['metadata'])
            
            # Update timestamp
            class_data['updated_at'] = datetime.now()
            
            # Build update query dynamically
            update_fields = []
            values = []
            
            for field, value in class_data.items():
                if field != 'id':
                    update_fields.append(f"{field} = ${len(values) + 1}")
                    values.append(value)
            
            values.append(class_id)
            query = f"""
            UPDATE classes 
            SET {', '.join(update_fields)} 
            WHERE id = ${len(values)}
            RETURNING *
            """
            
            result = await self.db.execute_query(query, values)
            
            if result.success and result.data:
                updated_class = self._parse_json_fields(result.data[0])
                query_time = (datetime.now() - start_time).total_seconds()
                
                self._log_operation(
                    operation=BaseRepository.RepositoryOperation.UPDATE,
                    entity_id=class_id,
                    duration=query_time,
                    success=True
                )
                
                return self._create_result(
                    data=updated_class,
                    query_time=query_time
                )
            else:
                query_time = (datetime.now() - start_time).total_seconds()
                return self._create_result(
                    error="Failed to update class",
                    query_time=query_time
                )
                
        except Exception as e:
            query_time = (datetime.now() - start_time).total_seconds()
            self.logger.error(f"Error updating class {class_id}: {str(e)}")
            return self._create_result(
                error=f"Database error updating class: {str(e)}",
                query_time=query_time
            )
    
    async def delete(self, class_id: str) -> QueryResult:
        """
        Delete a class by its ID.
        
        Args:
            class_id: Unique identifier for the class
            
        Returns:
            QueryResult with deletion status
        """
        start_time = datetime.now()
        
        try:
            if not self._validate_id(class_id):
                return self._create_result(error="Invalid class ID")
            
            # Check if class exists
            existing_result = await self.get_by_id(class_id)
            if not existing_result.success:
                return existing_result
            
            # Check if class has enrollments
            enrollment_check = await self._check_enrollments(class_id)
            if enrollment_check.success and enrollment_check.data.get('enrollment_count', 0) > 0:
                return self._create_result(error="Cannot delete class with active enrollments")
            
            # Delete the class
            query = "DELETE FROM classes WHERE id = $1"
            result = await self.db.execute_query(query, [class_id])
            
            if result.success:
                query_time = (datetime.now() - start_time).total_seconds()
                
                self._log_operation(
                    operation=BaseRepository.RepositoryOperation.DELETE,
                    entity_id=class_id,
                    duration=query_time,
                    success=True
                )
                
                return self._create_result(
                    data={"deleted": True, "class_id": class_id},
                    query_time=query_time
                )
            else:
                query_time = (datetime.now() - start_time).total_seconds()
                return self._create_result(
                    error="Failed to delete class",
                    query_time=query_time
                )
                
        except Exception as e:
            query_time = (datetime.now() - start_time).total_seconds()
            self.logger.error(f"Error deleting class {class_id}: {str(e)}")
            return self._create_result(
                error=f"Database error deleting class: {str(e)}",
                query_time=query_time
            )
    
    async def list_all(self, limit: int = 100, offset: int = 0) -> QueryResult:
        """
        List all classes with pagination.
        
        Args:
            limit: Maximum number of classes to return
            offset: Number of classes to skip
            
        Returns:
            QueryResult with list of classes
        """
        start_time = datetime.now()
        
        try:
            query = "SELECT * FROM classes ORDER BY created_at DESC LIMIT $1 OFFSET $2"
            result = await self.db.execute_query(query, [limit, offset])
            
            if result.success:
                classes = [self._parse_json_fields(cls) for cls in result.data]
                query_time = (datetime.now() - start_time).total_seconds()
                
                # Get total count
                count_query = "SELECT COUNT(*) FROM classes"
                count_result = await self.db.execute_query(count_query)
                total_count = count_result.data[0][0] if count_result.success else 0
                
                self._log_operation(
                    operation=BaseRepository.RepositoryOperation.LIST,
                    duration=query_time,
                    success=True
                )
                
                return self._create_result(
                    data=classes,
                    total_count=total_count,
                    query_time=query_time
                )
            else:
                query_time = (datetime.now() - start_time).total_seconds()
                return self._create_result(
                    error="Failed to list classes",
                    query_time=query_time
                )
                
        except Exception as e:
            query_time = (datetime.now() - start_time).total_seconds()
            self.logger.error(f"Error listing classes: {str(e)}")
            return self._create_result(
                error=f"Database error listing classes: {str(e)}",
                query_time=query_time
            )
    
    async def search(self, search_term: str, limit: int = 100, offset: int = 0) -> QueryResult:
        """
        Search classes by term.
        
        Args:
            search_term: Search term for filtering
            limit: Maximum number of classes to return
            offset: Number of classes to skip
            
        Returns:
            QueryResult with search results
        """
        start_time = datetime.now()
        
        try:
            if not search_term:
                return await self.list_all(limit, offset)
            
            # Search in code, name, and description
            query = """
            SELECT * FROM classes 
            WHERE (LOWER(code) LIKE LOWER($1) OR 
                   LOWER(name) LIKE LOWER($1) OR 
                   LOWER(description) LIKE LOWER($1))
            ORDER BY created_at DESC 
            LIMIT $2 OFFSET $3
            """
            
            search_pattern = f"%{search_term}%"
            result = await self.db.execute_query(query, [search_pattern, limit, offset])
            
            if result.success:
                classes = [self._parse_json_fields(cls) for cls in result.data]
                query_time = (datetime.now() - start_time).total_seconds()
                
                # Get total count
                count_query = """
                SELECT COUNT(*) FROM classes 
                WHERE (LOWER(code) LIKE LOWER($1) OR 
                       LOWER(name) LIKE LOWER($1) OR 
                       LOWER(description) LIKE LOWER($1))
                """
                count_result = await self.db.execute_query(count_query, [search_pattern])
                total_count = count_result.data[0][0] if count_result.success else 0
                
                self._log_operation(
                    operation=BaseRepository.RepositoryOperation.SEARCH,
                    duration=query_time,
                    success=True
                )
                
                return self._create_result(
                    data=classes,
                    total_count=total_count,
                    query_time=query_time
                )
            else:
                query_time = (datetime.now() - start_time).total_seconds()
                return self._create_result(
                    error="Failed to search classes",
                    query_time=query_time
                )
                
        except Exception as e:
            query_time = (datetime.now() - start_time).total_seconds()
            self.logger.error(f"Error searching classes: {str(e)}")
            return self._create_result(
                error=f"Database error searching classes: {str(e)}",
                query_time=query_time
            )
    
    async def filter(self, filters: Dict[str, Any], limit: int = 100, offset: int = 0) -> QueryResult:
        """
        Filter classes by criteria.
        
        Args:
            filters: Filter criteria
            limit: Maximum number of classes to return
            offset: Number of classes to skip
            
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
                if field == 'teacher_id':
                    conditions.append(f"teacher_id = ${len(values) + 1}")
                    values.append(value)
                elif field == 'subject_id':
                    conditions.append(f"subject_id = ${len(values) + 1}")
                    values.append(value)
                elif field == 'semester':
                    conditions.append(f"semester = ${len(values) + 1}")
                    values.append(value)
                elif field == 'department_id':
                    conditions.append(f"department_id = ${len(values) + 1}")
                    values.append(value)
                elif field == 'status':
                    conditions.append(f"status = ${len(values) + 1}")
                    values.append(value)
                elif field == 'room':
                    conditions.append(f"room = ${len(values) + 1}")
                    values.append(value)
                elif field == 'max_capacity':
                    conditions.append(f"max_capacity = ${len(values) + 1}")
                    values.append(value)
                elif field == 'current_enrollment':
                    conditions.append(f"current_enrollment = ${len(values) + 1}")
                    values.append(value)
                elif field == 'keyword':
                    conditions.append(f"(LOWER(code) LIKE LOWER(${len(values) + 1}) OR "
                                    f"LOWER(name) LIKE LOWER(${len(values) + 1}) OR "
                                    f"LOWER(description) LIKE LOWER(${len(values) + 1}))")
                    keyword_pattern = f"%{value}%"
                    values.extend([keyword_pattern, keyword_pattern, keyword_pattern])
            
            query_conditions = " AND ".join(conditions) if conditions else "1=1"
            query = f"SELECT * FROM classes WHERE {query_conditions} ORDER BY created_at DESC LIMIT ${len(values) + 1} OFFSET ${len(values) + 2}"
            
            values.extend([limit, offset])
            result = await self.db.execute_query(query, values)
            
            if result.success:
                classes = [self._parse_json_fields(cls) for cls in result.data]
                query_time = (datetime.now() - start_time).total_seconds()
                
                # Get total count
                count_query = f"SELECT COUNT(*) FROM classes WHERE {query_conditions}"
                count_result = await self.db.execute_query(count_query, values[:-2])
                total_count = count_result.data[0][0] if count_result.success else 0
                
                self._log_operation(
                    operation=BaseRepository.RepositoryOperation.FILTER,
                    duration=query_time,
                    success=True
                )
                
                return self._create_result(
                    data=classes,
                    total_count=total_count,
                    query_time=query_time
                )
            else:
                query_time = (datetime.now() - start_time).total_seconds()
                return self._create_result(
                    error="Failed to filter classes",
                    query_time=query_time
                )
                
        except Exception as e:
            query_time = (datetime.now() - start_time).total_seconds()
            self.logger.error(f"Error filtering classes: {str(e)}")
            return self._create_result(
                error=f"Database error filtering classes: {str(e)}",
                query_time=query_time
            )
    
    async def get_classes_for_teacher(self, teacher_id: str) -> QueryResult:
        """
        Get all classes for a specific teacher.
        
        Args:
            teacher_id: Unique identifier for the teacher
            
        Returns:
            QueryResult with teacher's classes
        """
        start_time = datetime.now()
        
        try:
            if not self._validate_id(teacher_id):
                return self._create_result(error="Invalid teacher ID")
            
            query = "SELECT * FROM classes WHERE teacher_id = $1 ORDER BY created_at DESC"
            result = await self.db.execute_query(query, [teacher_id])
            
            if result.success:
                classes = [self._parse_json_fields(cls) for cls in result.data]
                query_time = (datetime.now() - start_time).total_seconds()
                
                self._log_operation(
                    operation=BaseRepository.RepositoryOperation.READ,
                    entity_id=f"teacher_{teacher_id}_classes",
                    duration=query_time,
                    success=True
                )
                
                return self._create_result(
                    data=classes,
                    query_time=query_time
                )
            else:
                query_time = (datetime.now() - start_time).total_seconds()
                return self._create_result(
                    error="Failed to get teacher classes",
                    query_time=query_time
                )
                
        except Exception as e:
            query_time = (datetime.now() - start_time).total_seconds()
            self.logger.error(f"Error getting classes for teacher {teacher_id}: {str(e)}")
            return self._create_result(
                error=f"Database error getting teacher classes: {str(e)}",
                query_time=query_time
            )
    
    async def check_capacity(self, class_id: str) -> QueryResult:
        """
        Check if a class has available capacity.
        
        Args:
            class_id: Unique identifier for the class
            
        Returns:
            QueryResult with capacity information
        """
        start_time = datetime.now()
        
        try:
            if not self._validate_id(class_id):
                return self._create_result(error="Invalid class ID")
            
            # Get class details
            class_result = await self.get_by_id(class_id)
            if not class_result.success:
                return class_result
            
            class_data = class_result.data
            current_enrollment = class_data.get('current_enrollment', 0)
            max_capacity = class_data.get('max_capacity', 0)
            
            available_capacity = max_capacity - current_enrollment
            is_full = available_capacity <= 0
            
            # Update status if full
            if is_full and class_data.get('status') != ClassStatus.FULL.value:
                update_result = await self.update(class_id, {'status': ClassStatus.FULL.value})
                if not update_result.success:
                    self.logger.warning(f"Failed to update class status to full: {update_result.error}")
            
            query_time = (datetime.now() - start_time).total_seconds()
            self._log_operation(
                operation=BaseRepository.RepositoryOperation.READ,
                entity_id=f"{class_id}_capacity",
                duration=query_time,
                success=True
            )
            
            return self._create_result(
                data={
                    'class_id': class_id,
                    'current_enrollment': current_enrollment,
                    'max_capacity': max_capacity,
                    'available_capacity': available_capacity,
                    'is_full': is_full,
                    'capacity_percentage': (current_enrollment / max_capacity * 100) if max_capacity > 0 else 0
                },
                query_time=query_time
            )
                
        except Exception as e:
            query_time = (datetime.now() - start_time).total_seconds()
            self.logger.error(f"Error checking capacity for class {class_id}: {str(e)}")
            return self._create_result(
                error=f"Database error checking capacity: {str(e)}",
                query_time=query_time
            )
    
    async def _check_schedule_conflict(self, subject_id: str, semester: str, schedule: Dict[str, Any], exclude_class_id: str = None) -> QueryResult:
        """
        Check for schedule conflicts.
        
        Args:
            subject_id: Subject ID
            semester: Semester
            schedule: Schedule data
            exclude_class_id: Class ID to exclude from conflict check
            
        Returns:
            QueryResult with conflict check result
        """
        try:
            # Build query to check for conflicts
            conditions = [
                "subject_id = $1",
                "semester = $2"
            ]
            values = [subject_id, semester]
            
            # Exclude current class if updating
            if exclude_class_id:
                conditions.append("id != $3")
                values.append(exclude_class_id)
            
            # Check for time slot conflicts
            if schedule and 'time_slots' in schedule:
                time_slots = schedule['time_slots']
                for i, time_slot in enumerate(time_slots):
                    conditions.append(f"schedule->'time_slots'->>{i}->>'start_time' < $4 AND "
                                     f"schedule->'time_slots'->>{i}->>'end_time' > $4")
                    conditions.append(f"schedule->'time_slots'->>{i}->>'start_time' < $5 AND "
                                     f"schedule->'time_slots'->>{i}->>'end_time' > $5")
                    values.extend([time_slot['start_time'], time_slot['end_time']])
            
            query_conditions = " AND ".join(conditions)
            query = f"SELECT COUNT(*) FROM classes WHERE {query_conditions}"
            
            result = await self.db.execute_query(query, values)
            
            if result.success:
                conflict_count = result.data[0][0]
                if conflict_count > 0:
                    return self._create_result(
                        error=f"Schedule conflict detected: {conflict_count} conflicting classes found"
                    )
                else:
                    return self._create_result(data={'conflict_count': 0})
            else:
                return self._create_result(error="Failed to check schedule conflicts")
                
        except Exception as e:
            self.logger.error(f"Error checking schedule conflicts: {str(e)}")
            return self._create_result(
                error=f"Database error checking schedule conflicts: {str(e)}"
            )
    
    async def _check_enrollments(self, class_id: str) -> QueryResult:
        """
        Check if a class has active enrollments.
        
        Args:
            class_id: Unique identifier for the class
            
        Returns:
            QueryResult with enrollment count
        """
        try:
            query = "SELECT COUNT(*) FROM enrollments WHERE class_id = $1"
            result = await self.db.execute_query(query, [class_id])
            
            if result.success:
                return self._create_result(data={'enrollment_count': result.data[0][0]})
            else:
                return self._create_result(error="Failed to check enrollments")
                
        except Exception as e:
            self.logger.error(f"Error checking enrollments for class {class_id}: {str(e)}")
            return self._create_result(
                error=f"Database error checking enrollments: {str(e)}"
            )
    
    def _validate_schedule(self, schedule: Dict[str, Any]) -> bool:
        """
        Validate schedule format.
        
        Args:
            schedule: Schedule data to validate
            
        Returns:
            True if valid, False otherwise
        """
        if not schedule or not isinstance(schedule, dict):
            return False
        
        required_fields = ['time_slots', 'days', 'duration']
        for field in required_fields:
            if field not in schedule:
                return False
        
        if 'time_slots' in schedule:
            if not isinstance(schedule['time_slots'], list):
                return False
            
            for time_slot in schedule['time_slots']:
                if not isinstance(time_slot, dict):
                    return False
                if 'start_time' not in time_slot or 'end_time' not in time_slot:
                    return False
        
        return True
    
    def _parse_json_fields(self, class_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Parse JSON fields back to dictionary format.
        
        Args:
            class_data: Class data from database
            
        Returns:
            Class data with parsed JSON fields
        """
        if not class_data:
            return {}
        
        parsed_data = class_data.copy()
        
        # Parse JSON fields
        if 'schedule' in parsed_data and parsed_data['schedule']:
            try:
                parsed_data['schedule'] = json.loads(parsed_data['schedule'])
            except json.JSONDecodeError:
                parsed_data['schedule'] = {}
        
        if 'metadata' in parsed_data and parsed_data['metadata']:
            try:
                parsed_data['metadata'] = json.loads(parsed_data['metadata'])
            except json.JSONDecodeError:
                parsed_data['metadata'] = {}
        
        return parsed_data