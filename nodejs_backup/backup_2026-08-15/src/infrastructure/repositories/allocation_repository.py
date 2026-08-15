"""
Allocation Repository

This module provides the repository layer for Allocation entity operations.
It handles all database interactions related to allocations including CRUD operations,
resource availability checks, conflict detection, and schedule management.

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
from src.infrastructure.repositories.base_repository_with_db import BaseRepositoryWithDB, QueryResult

logger = get_logger(__name__)


class AllocationType(Enum):
    """Allocation type enumeration."""
    TEACHER = "teacher"
    ROOM = "room"
    EQUIPMENT = "equipment"
    LABORATORY = "laboratory"
    VENUE = "venue"


class AllocationStatus(Enum):
    """Allocation status enumeration."""
    PENDING = "pending"
    CONFIRMED = "confirmed"
    ACTIVE = "active"
    COMPLETED = "completed"
    CANCELLED = "cancelled"


class AllocationFilter(Enum):
    """Allocation filter types."""
    BY_TYPE = "type"
    BY_RESOURCE = "resource"
    BY_USER = "user"
    BY_STATUS = "status"
    BY_DATE_RANGE = "date_range"
    BY_TIME_SLOT = "time_slot"
    BY_DURATION = "duration"
    BY_CONFLICT = "conflict"


class SortOrder(Enum):
    """Sort order for allocation queries."""
    ASC = "asc"
    DESC = "desc"


@dataclass
class AllocationQuery:
    """Structured query for allocation operations."""
    filters: Dict[str, Any] = None
    sort_by: str = None
    sort_order: SortOrder = SortOrder.ASC
    limit: int = 100
    offset: int = 0
    search_term: str = None


class AllocationRepository(BaseRepositoryWithDB):
    """
    Repository for Allocation entity operations.
    
    Handles CRUD operations, resource availability, conflict detection,
    and schedule management.
    """
    
    def __init__(self, database_manager):
        """
        Initialize the allocation repository.
        
        Args:
            database_manager: Database connection manager instance
        """
        super().__init__("allocations", database_manager)
        
    async def create(self, allocation_data: Dict[str, Any]) -> QueryResult:
        """
        Create a new allocation in the database.
        
        Args:
            allocation_data: Allocation data including all required fields
            
        Returns:
            QueryResult with created allocation
        """
        start_time = datetime.now()
        
        try:
            # Validate allocation data
            if not self._validate_entity_data(allocation_data):
                return self._create_result(error="Invalid allocation data")
            
            # Validate required fields
            required_fields = ['type', 'resource_id', 'allocated_to', 'start_time', 'end_time', 'allocated_by']
            for field in required_fields:
                if field not in allocation_data:
                    return self._create_result(error=f"Missing required field: {field}")
            
            # Set default values for optional fields
            allocation_data.setdefault('created_at', datetime.now())
            allocation_data.setdefault('updated_at', datetime.now())
            allocation_data.setdefault('status', AllocationStatus.PENDING.value)
            allocation_data.setdefault('metadata', {})
            allocation_data.setdefault('notes', '')
            allocation_data.setdefault('duration_minutes', 0)
            allocation_data.setdefault('date', datetime.now().date())
            
            # Calculate duration
            start_time_obj = datetime.strptime(allocation_data['start_time'], '%H:%M:%S').time()
            end_time_obj = datetime.strptime(allocation_data['end_time'], '%H:%M:%S').time()
            duration_minutes = int((datetime.combine(datetime.min, end_time_obj) - datetime.combine(datetime.min, start_time_obj)).total_seconds() / 60)
            allocation_data['duration_minutes'] = duration_minutes
            
            # Validate time slots
            if not self._validate_time_slots(allocation_data):
                return self._create_result(error="Invalid time slots")
            
            # Check for conflicts
            conflict_result = await self._check_allocation_conflicts(
                allocation_data['resource_id'],
                allocation_data['date'],
                allocation_data['start_time'],
                allocation_data['end_time'],
                allocation_data.get('id')
            )
            
            if not conflict_result.success:
                return conflict_result
            
            # Convert complex fields to JSON strings for storage
            if 'metadata' in allocation_data:
                allocation_data['metadata'] = json.dumps(allocation_data['metadata'])
            
            # Insert into database
            query = """
            INSERT INTO allocations 
            (type, resource_id, allocated_to, start_time, end_time, allocated_by, status,
             metadata, notes, duration_minutes, date, created_at, updated_at)
            VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11, $12, $13)
            RETURNING *
            """
            
            values = [
                allocation_data['type'],
                allocation_data['resource_id'],
                allocation_data['allocated_to'],
                allocation_data['start_time'],
                allocation_data['end_time'],
                allocation_data['allocated_by'],
                allocation_data['status'],
                allocation_data.get('metadata'),
                allocation_data.get('notes'),
                allocation_data['duration_minutes'],
                allocation_data['date'],
                allocation_data['created_at'],
                allocation_data['updated_at']
            ]
            
            result = await self.db.execute_query(query, values)
            
            if result.success and result.data:
                # Parse JSON fields back to dict
                created_allocation = self._parse_json_fields(result.data[0])
                query_time = (datetime.now() - start_time).total_seconds()
                
                self._log_operation(
                    operation=BaseRepository.RepositoryOperation.CREATE,
                    duration=query_time,
                    success=True
                )
                
                return self._create_result(
                    data=created_allocation,
                    query_time=query_time
                )
            else:
                return self._create_result(error="Failed to create allocation")
                
        except Exception as e:
            query_time = (datetime.now() - start_time).total_seconds()
            self.logger.error(f"Error creating allocation: {str(e)}")
            return self._create_result(
                error=f"Database error creating allocation: {str(e)}",
                query_time=query_time
            )
    
    async def get_by_id(self, allocation_id: str) -> QueryResult:
        """
        Get an allocation by its ID.
        
        Args:
            allocation_id: Unique identifier for the allocation
            
        Returns:
            QueryResult with the allocation data
        """
        start_time = datetime.now()
        
        try:
            if not self._validate_id(allocation_id):
                return self._create_result(error="Invalid allocation ID")
            
            query = "SELECT * FROM allocations WHERE id = $1"
            result = await self.db.execute_query(query, [allocation_id])
            
            if result.success and result.data:
                allocation = self._parse_json_fields(result.data[0])
                query_time = (datetime.now() - start_time).total_seconds()
                
                self._log_operation(
                    operation=BaseRepository.RepositoryOperation.READ,
                    entity_id=allocation_id,
                    duration=query_time,
                    success=True
                )
                
                return self._create_result(
                    data=allocation,
                    query_time=query_time
                )
            else:
                query_time = (datetime.now() - start_time).total_seconds()
                self._log_operation(
                    operation=BaseRepository.RepositoryOperation.READ,
                    entity_id=allocation_id,
                    duration=query_time,
                    success=False
                )
                return self._create_result(
                    error="Allocation not found",
                    query_time=query_time
                )
                
        except Exception as e:
            query_time = (datetime.now() - start_time).total_seconds()
            self.logger.error(f"Error getting allocation {allocation_id}: {str(e)}")
            return self._create_result(
                error=f"Database error getting allocation: {str(e)}",
                query_time=query_time
            )
    
    async def update(self, allocation_id: str, allocation_data: Dict[str, Any]) -> QueryResult:
        """
        Update an existing allocation.
        
        Args:
            allocation_id: Unique identifier for the allocation
            allocation_data: Updated data for the allocation
            
        Returns:
            QueryResult with the updated allocation
        """
        start_time = datetime.now()
        
        try:
            if not self._validate_id(allocation_id):
                return self._create_result(error="Invalid allocation ID")
            
            if not self._validate_entity_data(allocation_data):
                return self._create_result(error="Invalid allocation data")
            
            # Check if allocation exists
            existing_result = await self.get_by_id(allocation_id)
            if not existing_result.success:
                return existing_result
            
            existing_allocation = existing_result.data
            
            # Update duration if time changed
            if 'start_time' in allocation_data or 'end_time' in allocation_data:
                start_time_obj = datetime.strptime(allocation_data.get('start_time', existing_allocation['start_time']), '%H:%M:%S').time()
                end_time_obj = datetime.strptime(allocation_data.get('end_time', existing_allocation['end_time']), '%H:%M:%S').time()
                duration_minutes = int((datetime.combine(datetime.min, end_time_obj) - datetime.combine(datetime.min, start_time_obj)).total_seconds() / 60)
                allocation_data['duration_minutes'] = duration_minutes
            
            # Validate time slots
            if 'start_time' in allocation_data or 'end_time' in allocation_data:
                if not self._validate_time_slots(allocation_data):
                    return self._create_result(error="Invalid time slots")
            
            # Check for conflicts if time or resource changed
            if (existing_allocation['resource_id'] != allocation_data.get('resource_id') or
                existing_allocation['date'] != allocation_data.get('date') or
                existing_allocation['start_time'] != allocation_data.get('start_time') or
                existing_allocation['end_time'] != allocation_data.get('end_time')):
                
                conflict_result = await self._check_allocation_conflicts(
                    allocation_data.get('resource_id', existing_allocation['resource_id']),
                    allocation_data.get('date', existing_allocation['date']),
                    allocation_data.get('start_time', existing_allocation['start_time']),
                    allocation_data.get('end_time', existing_allocation['end_time']),
                    allocation_id
                )
                
                if not conflict_result.success:
                    return conflict_result
            
            # Convert complex fields to JSON strings
            if 'metadata' in allocation_data:
                allocation_data['metadata'] = json.dumps(allocation_data['metadata'])
            
            # Update timestamp
            allocation_data['updated_at'] = datetime.now()
            
            # Build update query dynamically
            update_fields = []
            values = []
            
            for field, value in allocation_data.items():
                if field != 'id':
                    update_fields.append(f"{field} = ${len(values) + 1}")
                    values.append(value)
            
            values.append(allocation_id)
            query = f"""
            UPDATE allocations 
            SET {', '.join(update_fields)} 
            WHERE id = ${len(values)}
            RETURNING *
            """
            
            result = await self.db.execute_query(query, values)
            
            if result.success and result.data:
                updated_allocation = self._parse_json_fields(result.data[0])
                query_time = (datetime.now() - start_time).total_seconds()
                
                self._log_operation(
                    operation=BaseRepository.RepositoryOperation.UPDATE,
                    entity_id=allocation_id,
                    duration=query_time,
                    success=True
                )
                
                return self._create_result(
                    data=updated_allocation,
                    query_time=query_time
                )
            else:
                query_time = (datetime.now() - start_time).total_seconds()
                return self._create_result(
                    error="Failed to update allocation",
                    query_time=query_time
                )
                
        except Exception as e:
            query_time = (datetime.now() - start_time).total_seconds()
            self.logger.error(f"Error updating allocation {allocation_id}: {str(e)}")
            return self._create_result(
                error=f"Database error updating allocation: {str(e)}",
                query_time=query_time
            )
    
    async def delete(self, allocation_id: str) -> QueryResult:
        """
        Delete an allocation by its ID.
        
        Args:
            allocation_id: Unique identifier for the allocation
            
        Returns:
            QueryResult with deletion status
        """
        start_time = datetime.now()
        
        try:
            if not self._validate_id(allocation_id):
                return self._create_result(error="Invalid allocation ID")
            
            # Check if allocation exists
            existing_result = await self.get_by_id(allocation_id)
            if not existing_result.success:
                return existing_result
            
            existing_allocation = existing_result.data
            
            # Check if allocation is active
            if existing_allocation.get('status') == AllocationStatus.ACTIVE.value:
                return self._create_result(error="Cannot delete active allocation")
            
            # Delete the allocation
            query = "DELETE FROM allocations WHERE id = $1"
            result = await self.db.execute_query(query, [allocation_id])
            
            if result.success:
                query_time = (datetime.now() - start_time).total_seconds()
                
                self._log_operation(
                    operation=BaseRepository.RepositoryOperation.DELETE,
                    entity_id=allocation_id,
                    duration=query_time,
                    success=True
                )
                
                return self._create_result(
                    data={"deleted": True, "allocation_id": allocation_id},
                    query_time=query_time
                )
            else:
                query_time = (datetime.now() - start_time).total_seconds()
                return self._create_result(
                    error="Failed to delete allocation",
                    query_time=query_time
                )
                
        except Exception as e:
            query_time = (datetime.now() - start_time).total_seconds()
            self.logger.error(f"Error deleting allocation {allocation_id}: {str(e)}")
            return self._create_result(
                error=f"Database error deleting allocation: {str(e)}",
                query_time=query_time
            )
    
    async def list_all(self, limit: int = 100, offset: int = 0) -> QueryResult:
        """
        List all allocations with pagination.
        
        Args:
            limit: Maximum number of allocations to return
            offset: Number of allocations to skip
            
        Returns:
            QueryResult with list of allocations
        """
        start_time = datetime.now()
        
        try:
            query = "SELECT * FROM allocations ORDER BY created_at DESC LIMIT $1 OFFSET $2"
            result = await self.db.execute_query(query, [limit, offset])
            
            if result.success:
                allocations = [self._parse_json_fields(alloc) for alloc in result.data]
                query_time = (datetime.now() - start_time).total_seconds()
                
                # Get total count
                count_query = "SELECT COUNT(*) FROM allocations"
                count_result = await self.db.execute_query(count_query)
                total_count = count_result.data[0][0] if count_result.success else 0
                
                self._log_operation(
                    operation=BaseRepository.RepositoryOperation.LIST,
                    duration=query_time,
                    success=True
                )
                
                return self._create_result(
                    data=allocations,
                    total_count=total_count,
                    query_time=query_time
                )
            else:
                query_time = (datetime.now() - start_time).total_seconds()
                return self._create_result(
                    error="Failed to list allocations",
                    query_time=query_time
                )
                
        except Exception as e:
            query_time = (datetime.now() - start_time).total_seconds()
            self.logger.error(f"Error listing allocations: {str(e)}")
            return self._create_result(
                error=f"Database error listing allocations: {str(e)}",
                query_time=query_time
            )
    
    async def search(self, search_term: str, limit: int = 100, offset: int = 0) -> QueryResult:
        """
        Search allocations by term.
        
        Args:
            search_term: Search term for filtering
            limit: Maximum number of allocations to return
            offset: Number of allocations to skip
            
        Returns:
            QueryResult with search results
        """
        start_time = datetime.now()
        
        try:
            if not search_term:
                return await self.list_all(limit, offset)
            
            # Search in resource_id, allocated_to, allocated_by, and notes
            query = """
            SELECT * FROM allocations 
            WHERE (LOWER(resource_id) LIKE LOWER($1) OR 
                   LOWER(allocated_to) LIKE LOWER($1) OR 
                   LOWER(allocated_by) LIKE LOWER($1) OR 
                   LOWER(notes) LIKE LOWER($1))
            ORDER BY created_at DESC 
            LIMIT $2 OFFSET $3
            """
            
            search_pattern = f"%{search_term}%"
            result = await self.db.execute_query(query, [search_pattern, limit, offset])
            
            if result.success:
                allocations = [self._parse_json_fields(alloc) for alloc in result.data]
                query_time = (datetime.now() - start_time).total_seconds()
                
                # Get total count
                count_query = """
                SELECT COUNT(*) FROM allocations 
                WHERE (LOWER(resource_id) LIKE LOWER($1) OR 
                       LOWER(allocated_to) LIKE LOWER($1) OR 
                       LOWER(allocated_by) LIKE LOWER($1) OR 
                       LOWER(notes) LIKE LOWER($1))
                """
                count_result = await self.db.execute_query(count_query, [search_pattern])
                total_count = count_result.data[0][0] if count_result.success else 0
                
                self._log_operation(
                    operation=BaseRepository.RepositoryOperation.SEARCH,
                    duration=query_time,
                    success=True
                )
                
                return self._create_result(
                    data=allocations,
                    total_count=total_count,
                    query_time=query_time
                )
            else:
                query_time = (datetime.now() - start_time).total_seconds()
                return self._create_result(
                    error="Failed to search allocations",
                    query_time=query_time
                )
                
        except Exception as e:
            query_time = (datetime.now() - start_time).total_seconds()
            self.logger.error(f"Error searching allocations: {str(e)}")
            return self._create_result(
                error=f"Database error searching allocations: {str(e)}",
                query_time=query_time
            )
    
    async def filter(self, filters: Dict[str, Any], limit: int = 100, offset: int = 0) -> QueryResult:
        """
        Filter allocations by criteria.
        
        Args:
            filters: Filter criteria
            limit: Maximum number of allocations to return
            offset: Number of allocations to skip
            
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
                elif field == 'resource_id':
                    conditions.append(f"resource_id = ${len(values) + 1}")
                    values.append(value)
                elif field == 'allocated_to':
                    conditions.append(f"allocated_to = ${len(values) + 1}")
                    values.append(value)
                elif field == 'allocated_by':
                    conditions.append(f"allocated_by = ${len(values) + 1}")
                    values.append(value)
                elif field == 'status':
                    conditions.append(f"status = ${len(values) + 1}")
                    values.append(value)
                elif field == 'date':
                    conditions.append(f"date = ${len(values) + 1}")
                    values.append(value)
                elif field == 'start_time':
                    conditions.append(f"start_time >= ${len(values) + 1}")
                    values.append(value)
                elif field == 'end_time':
                    conditions.append(f"end_time <= ${len(values) + 1}")
                    values.append(value)
                elif field == 'min_duration':
                    conditions.append(f"duration_minutes >= ${len(values) + 1}")
                    values.append(value)
                elif field == 'max_duration':
                    conditions.append(f"duration_minutes <= ${len(values) + 1}")
                    values.append(value)
                elif field == 'keyword':
                    conditions.append(f"(LOWER(resource_id) LIKE LOWER(${len(values) + 1}) OR "
                                    f"LOWER(allocated_to) LIKE LOWER(${len(values) + 1}) OR "
                                    f"LOWER(allocated_by) LIKE LOWER(${len(values) + 1}) OR "
                                    f"LOWER(notes) LIKE LOWER(${len(values) + 1}))")
                    keyword_pattern = f"%{value}%"
                    values.extend([keyword_pattern, keyword_pattern, keyword_pattern, keyword_pattern])
            
            query_conditions = " AND ".join(conditions) if conditions else "1=1"
            query = f"SELECT * FROM allocations WHERE {query_conditions} ORDER BY created_at DESC LIMIT ${len(values) + 1} OFFSET ${len(values) + 2}"
            
            values.extend([limit, offset])
            result = await self.db.execute_query(query, values)
            
            if result.success:
                allocations = [self._parse_json_fields(alloc) for alloc in result.data]
                query_time = (datetime.now() - start_time).total_seconds()
                
                # Get total count
                count_query = f"SELECT COUNT(*) FROM allocations WHERE {query_conditions}"
                count_result = await self.db.execute_query(count_query, values[:-2])
                total_count = count_result.data[0][0] if count_result.success else 0
                
                self._log_operation(
                    operation=BaseRepository.RepositoryOperation.FILTER,
                    duration=query_time,
                    success=True
                )
                
                return self._create_result(
                    data=allocations,
                    total_count=total_count,
                    query_time=query_time
                )
            else:
                query_time = (datetime.now() - start_time).total_seconds()
                return self._create_result(
                    error="Failed to filter allocations",
                    query_time=query_time
                )
                
        except Exception as e:
            query_time = (datetime.now() - start_time).total_seconds()
            self.logger.error(f"Error filtering allocations: {str(e)}")
            return self._create_result(
                error=f"Database error filtering allocations: {str(e)}",
                query_time=query_time
            )
    
    async def get_resource_allocations(self, resource_id: str) -> QueryResult:
        """
        Get all allocations for a specific resource.
        
        Args:
            resource_id: Unique identifier for the resource
            
        Returns:
            QueryResult with resource allocations
        """
        start_time = datetime.now()
        
        try:
            if not self._validate_id(resource_id):
                return self._create_result(error="Invalid resource ID")
            
            query = "SELECT * FROM allocations WHERE resource_id = $1 ORDER BY start_time"
            result = await self.db.execute_query(query, [resource_id])
            
            if result.success:
                allocations = [self._parse_json_fields(alloc) for alloc in result.data]
                query_time = (datetime.now() - start_time).total_seconds()
                
                self._log_operation(
                    operation=BaseRepository.RepositoryOperation.READ,
                    entity_id=f"resource_{resource_id}_allocations",
                    duration=query_time,
                    success=True
                )
                
                return self._create_result(
                    data=allocations,
                    query_time=query_time
                )
            else:
                query_time = (datetime.now() - start_time).total_seconds()
                return self._create_result(
                    error="Failed to get resource allocations",
                    query_time=query_time
                )
                
        except Exception as e:
            query_time = (datetime.now() - start_time).total_seconds()
            self.logger.error(f"Error getting resource allocations for {resource_id}: {str(e)}")
            return self._create_result(
                error=f"Database error getting resource allocations: {str(e)}",
                query_time=query_time
            )
    
    async def get_user_allocations(self, user_id: str) -> QueryResult:
        """
        Get all allocations for a specific user.
        
        Args:
            user_id: Unique identifier for the user
            
        Returns:
            QueryResult with user allocations
        """
        start_time = datetime.now()
        
        try:
            if not self._validate_id(user_id):
                return self._create_result(error="Invalid user ID")
            
            query = "SELECT * FROM allocations WHERE allocated_to = $1 ORDER BY start_time"
            result = await self.db.execute_query(query, [user_id])
            
            if result.success:
                allocations = [self._parse_json_fields(alloc) for alloc in result.data]
                query_time = (datetime.now() - start_time).total_seconds()
                
                self._log_operation(
                    operation=BaseRepository.RepositoryOperation.READ,
                    entity_id=f"user_{user_id}_allocations",
                    duration=query_time,
                    success=True
                )
                
                return self._create_result(
                    data=allocations,
                    query_time=query_time
                )
            else:
                query_time = (datetime.now() - start_time).total_seconds()
                return self._create_result(
                    error="Failed to get user allocations",
                    query_time=query_time
                )
                
        except Exception as e:
            query_time = (datetime.now() - start_time).total_seconds()
            self.logger.error(f"Error getting user allocations for {user_id}: {str(e)}")
            return self._create_result(
                error=f"Database error getting user allocations: {str(e)}",
                query_time=query_time
            )
    
    async def check_resource_availability(self, resource_id: str, date: str, start_time: str, end_time: str) -> QueryResult:
        """
        Check if a resource is available for a specific time slot.
        
        Args:
            resource_id: Unique identifier for the resource
            date: Date to check (YYYY-MM-DD)
            start_time: Start time (HH:MM:SS)
            end_time: End time (HH:MM:SS)
            
        Returns:
            QueryResult with availability check result
        """
        start_time_check = datetime.now()
        
        try:
            if not self._validate_id(resource_id):
                return self._create_result(error="Invalid resource ID")
            
            # Check for conflicting allocations
            conflict_result = await self._check_allocation_conflicts(resource_id, date, start_time, end_time)
            
            query_time = (datetime.now() - start_time_check).total_seconds()
            self._log_operation(
                operation=BaseRepository.RepositoryOperation.READ,
                entity_id=f"{resource_id}_availability",
                duration=query_time,
                success=True
            )
            
            return self._create_result(
                data={
                    'resource_id': resource_id,
                    'date': date,
                    'start_time': start_time,
                    'end_time': end_time,
                    'is_available': conflict_result.success and conflict_result.data.get('conflict_count', 0) == 0,
                    'conflicts': conflict_result.data.get('conflicts', []) if conflict_result.data else []
                },
                query_time=query_time
            )
                
        except Exception as e:
            query_time = (datetime.now() - start_time_check).total_seconds()
            self.logger.error(f"Error checking resource availability for {resource_id}: {str(e)}")
            return self._create_result(
                error=f"Database error checking resource availability: {str(e)}",
                query_time=query_time
            )
    
    async def _check_allocation_conflicts(self, resource_id: str, date: str, start_time: str, end_time: str, exclude_allocation_id: str = None) -> QueryResult:
        """
        Check for allocation conflicts.
        
        Args:
            resource_id: Resource ID to check
            date: Date to check
            start_time: Start time
            end_time: End time
            exclude_allocation_id: Allocation ID to exclude from check
            
        Returns:
            QueryResult with conflict check result
        """
        try:
            conditions = ["resource_id = $1", "date = $2"]
            values = [resource_id, date]
            
            # Exclude current allocation if updating
            if exclude_allocation_id:
                conditions.append("id != $3")
                values.append(exclude_allocation_id)
            
            # Check for time slot conflicts
            # New allocation starts during existing allocation
            conditions.append(f"(start_time < $4 AND end_time > $4)")
            values.append(start_time)
            
            # New allocation ends during existing allocation
            conditions.append(f"(start_time < $5 AND end_time > $5)")
            values.append(end_time)
            
            # New allocation completely contains existing allocation
            conditions.append(f"(start_time <= $4 AND end_time >= $5)")
            values.append(start_time)
            values.append(end_time)
            
            query_conditions = " AND ".join(conditions)
            query = f"""
            SELECT id, type, allocated_to, start_time, end_time, status 
            FROM allocations 
            WHERE {query_conditions}
            """
            
            result = await self.db.execute_query(query, values)
            
            if result.success:
                conflicts = result.data
                return self._create_result(
                    data={
                        'conflict_count': len(conflicts),
                        'conflicts': conflicts,
                        'has_conflicts': len(conflicts) > 0
                    }
                )
            else:
                return self._create_result(error="Failed to check allocation conflicts")
                
        except Exception as e:
            self.logger.error(f"Error checking allocation conflicts: {str(e)}")
            return self._create_result(
                error=f"Database error checking allocation conflicts: {str(e)}"
            )
    
    def _validate_time_slots(self, allocation_data: Dict[str, Any]) -> bool:
        """
        Validate time slots format.
        
        Args:
            allocation_data: Allocation data to validate
            
        Returns:
            True if valid, False otherwise
        """
        try:
            start_time = allocation_data.get('start_time')
            end_time = allocation_data.get('end_time')
            
            if not start_time or not end_time:
                return False
            
            # Parse time strings
            start_time_obj = datetime.strptime(start_time, '%H:%M:%S').time()
            end_time_obj = datetime.strptime(end_time, '%H:%M:%S').time()
            
            # Check if start time is before end time
            if start_time_obj >= end_time_obj:
                return False
            
            return True
            
        except (ValueError, TypeError):
            return False
    
    def _parse_json_fields(self, allocation_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Parse JSON fields back to dictionary format.
        
        Args:
            allocation_data: Allocation data from database
            
        Returns:
            Allocation data with parsed JSON fields
        """
        if not allocation_data:
            return {}
        
        parsed_data = allocation_data.copy()
        
        # Parse JSON fields
        if 'metadata' in parsed_data and parsed_data['metadata']:
            try:
                parsed_data['metadata'] = json.loads(parsed_data['metadata'])
            except json.JSONDecodeError:
                parsed_data['metadata'] = {}
        
        return parsed_data