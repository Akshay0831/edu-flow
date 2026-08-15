"""
Department Repository

This module provides the repository layer for Department entity operations.
It handles all database interactions related to departments including CRUD operations,
hierarchy management, program and course assignment, and department analytics.

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


class DepartmentStatus(Enum):
    """Department status types."""
    ACTIVE = "active"
    INACTIVE = "inactive"
    UNDER_REVIEW = "under_review"


class DepartmentFilter(Enum):
    """Department filter types."""
    BY_PARENT = "parent"
    BY_STATUS = "status"
    BY_PROGRAM = "program"
    BY_CHILDREN_COUNT = "children_count"
    BY_COURSE_COUNT = "course_count"
    BY_STUDENT_COUNT = "student_count"
    BY_TEACHER_COUNT = "teacher_count"
    BY_NAME = "name"


class SortOrder(Enum):
    """Sort order for department queries."""
    ASC = "asc"
    DESC = "desc"


@dataclass
class DepartmentQuery:
    """Structured query for department operations."""
    filters: Dict[str, Any] = None
    sort_by: str = None
    sort_order: SortOrder = SortOrder.ASC
    limit: int = 100
    offset: int = 0
    search_term: str = None


class DepartmentRepository(BaseRepositoryWithDB):
    """
    Repository for Department entity operations.
    
    Handles CRUD operations, hierarchy management, program and course assignment,
    and department analytics.
    """
    
    def __init__(self, database_manager):
        """
        Initialize the department repository.
        
        Args:
            database_manager: Database connection manager instance
        """
        super().__init__("departments", database_manager)
        
    async def create(self, department_data: Dict[str, Any]) -> QueryResult:
        """
        Create a new department in the database.
        
        Args:
            department_data: Department data including all required fields
            
        Returns:
            QueryResult with created department
        """
        start_time = datetime.now()
        
        try:
            # Validate department data
            if not self._validate_entity_data(department_data):
                return self._create_result(error="Invalid department data")
            
            # Validate required fields
            required_fields = ['code', 'name', 'description', 'status']
            for field in required_fields:
                if field not in department_data:
                    return self._create_result(error=f"Missing required field: {field}")
            
            # Set default values for optional fields
            department_data.setdefault('created_at', datetime.now())
            department_data.setdefault('updated_at', datetime.now())
            department_data.setdefault('parent_id', None)
            department_data.setdefault('children_ids', [])
            department_data.setdefault('program_ids', [])
            department_data.setdefault('course_ids', [])
            department_data.setdefault('metadata', {})
            department_data.setdefault('head_of_department', None)
            department_data.setdefault('contact_email', '')
            department_data.setdefault('contact_phone', '')
            department_data.setdefault('location', '')
            
            # Convert complex fields to JSON strings for storage
            if 'children_ids' in department_data:
                department_data['children_ids'] = json.dumps(department_data['children_ids'])
            if 'program_ids' in department_data:
                department_data['program_ids'] = json.dumps(department_data['program_ids'])
            if 'course_ids' in department_data:
                department_data['course_ids'] = json.dumps(department_data['course_ids'])
            if 'metadata' in department_data:
                department_data['metadata'] = json.dumps(department_data['metadata'])
            
            # Validate parent-child relationship
            if department_data.get('parent_id'):
                parent_result = await self.get_by_id(department_data['parent_id'])
                if not parent_result.success:
                    return self._create_result(error="Parent department not found")
            
            # Insert into database
            query = """
            INSERT INTO departments 
            (code, name, description, status, parent_id, children_ids, program_ids, course_ids,
             head_of_department, contact_email, contact_phone, location, metadata, created_at, updated_at)
            VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11, $12, $13, $14, $15)
            RETURNING *
            """
            
            values = [
                department_data['code'],
                department_data['name'],
                department_data['description'],
                department_data['status'],
                department_data.get('parent_id'),
                department_data.get('children_ids'),
                department_data.get('program_ids'),
                department_data.get('course_ids'),
                department_data.get('head_of_department'),
                department_data.get('contact_email'),
                department_data.get('contact_phone'),
                department_data.get('location'),
                department_data.get('metadata'),
                department_data['created_at'],
                department_data['updated_at']
            ]
            
            result = await self.db.execute_query(query, values)
            
            if result.success and result.data:
                # Parse JSON fields back to dict
                created_department = self._parse_json_fields(result.data[0])
                
                # Update parent's children list if parent_id is set
                if department_data.get('parent_id'):
                    await self._update_parent_children(department_data['parent_id'], result.data[0]['id'])
                
                query_time = (datetime.now() - start_time).total_seconds()
                
                self._log_operation(
                    operation=BaseRepository.RepositoryOperation.CREATE,
                    duration=query_time,
                    success=True
                )
                
                return self._create_result(
                    data=created_department,
                    query_time=query_time
                )
            else:
                return self._create_result(error="Failed to create department")
                
        except Exception as e:
            query_time = (datetime.now() - start_time).total_seconds()
            self.logger.error(f"Error creating department: {str(e)}")
            return self._create_result(
                error=f"Database error creating department: {str(e)}",
                query_time=query_time
            )
    
    async def get_by_id(self, department_id: str) -> QueryResult:
        """
        Get a department by its ID.
        
        Args:
            department_id: Unique identifier for the department
            
        Returns:
            QueryResult with the department data
        """
        start_time = datetime.now()
        
        try:
            if not self._validate_id(department_id):
                return self._create_result(error="Invalid department ID")
            
            query = "SELECT * FROM departments WHERE id = $1"
            result = await self.db.execute_query(query, [department_id])
            
            if result.success and result.data:
                department = self._parse_json_fields(result.data[0])
                query_time = (datetime.now() - start_time).total_seconds()
                
                self._log_operation(
                    operation=BaseRepository.RepositoryOperation.READ,
                    entity_id=department_id,
                    duration=query_time,
                    success=True
                )
                
                return self._create_result(
                    data=department,
                    query_time=query_time
                )
            else:
                query_time = (datetime.now() - start_time).total_seconds()
                self._log_operation(
                    operation=BaseRepository.RepositoryOperation.READ,
                    entity_id=department_id,
                    duration=query_time,
                    success=False
                )
                return self._create_result(
                    error="Department not found",
                    query_time=query_time
                )
                
        except Exception as e:
            query_time = (datetime.now() - start_time).total_seconds()
            self.logger.error(f"Error getting department {department_id}: {str(e)}")
            return self._create_result(
                error=f"Database error getting department: {str(e)}",
                query_time=query_time
            )
    
    async def update(self, department_id: str, department_data: Dict[str, Any]) -> QueryResult:
        """
        Update an existing department.
        
        Args:
            department_id: Unique identifier for the department
            department_data: Updated data for the department
            
        Returns:
            QueryResult with the updated department
        """
        start_time = datetime.now()
        
        try:
            if not self._validate_id(department_id):
                return self._create_result(error="Invalid department ID")
            
            if not self._validate_entity_data(department_data):
                return self._create_result(error="Invalid department data")
            
            # Check if department exists
            existing_result = await self.get_by_id(department_id)
            if not existing_result.success:
                return existing_result
            
            existing_department = existing_result.data
            
            # Validate parent-child relationship update
            if 'parent_id' in department_data and department_data['parent_id'] != existing_department.get('parent_id'):
                if department_data['parent_id'] == department_id:
                    return self._create_result(error="Department cannot be parent of itself")
                
                parent_result = await self.get_by_id(department_data['parent_id'])
                if not parent_result.success:
                    return self._create_result(error="New parent department not found")
                
                # Check for circular reference
                if await self._has_circular_reference(department_data['parent_id'], department_id):
                    return self._create_result(error="Circular reference detected in department hierarchy")
            
            # Convert complex fields to JSON strings
            if 'children_ids' in department_data:
                department_data['children_ids'] = json.dumps(department_data['children_ids'])
            if 'program_ids' in department_data:
                department_data['program_ids'] = json.dumps(department_data['program_ids'])
            if 'course_ids' in department_data:
                department_data['course_ids'] = json.dumps(department_data['course_ids'])
            if 'metadata' in department_data:
                department_data['metadata'] = json.dumps(department_data['metadata'])
            
            # Update timestamp
            department_data['updated_at'] = datetime.now()
            
            # Build update query dynamically
            update_fields = []
            values = []
            
            for field, value in department_data.items():
                if field != 'id':
                    update_fields.append(f"{field} = ${len(values) + 1}")
                    values.append(value)
            
            values.append(department_id)
            query = f"""
            UPDATE departments 
            SET {', '.join(update_fields)} 
            WHERE id = ${len(values)}
            RETURNING *
            """
            
            result = await self.db.execute_query(query, values)
            
            if result.success and result.data:
                updated_department = self._parse_json_fields(result.data[0])
                
                # Update parent's children list if parent_id changed
                if 'parent_id' in department_data:
                    old_parent_id = existing_department.get('parent_id')
                    new_parent_id = department_data['parent_id']
                    
                    if old_parent_id != new_parent_id:
                        if old_parent_id:
                            await self._update_parent_children(old_parent_id, department_id, remove=True)
                        if new_parent_id:
                            await self._update_parent_children(new_parent_id, department_id)
                
                query_time = (datetime.now() - start_time).total_seconds()
                
                self._log_operation(
                    operation=BaseRepository.RepositoryOperation.UPDATE,
                    entity_id=department_id,
                    duration=query_time,
                    success=True
                )
                
                return self._create_result(
                    data=updated_department,
                    query_time=query_time
                )
            else:
                query_time = (datetime.now() - start_time).total_seconds()
                return self._create_result(
                    error="Failed to update department",
                    query_time=query_time
                )
                
        except Exception as e:
            query_time = (datetime.now() - start_time).total_seconds()
            self.logger.error(f"Error updating department {department_id}: {str(e)}")
            return self._create_result(
                error=f"Database error updating department: {str(e)}",
                query_time=query_time
            )
    
    async def delete(self, department_id: str) -> QueryResult:
        """
        Delete a department by its ID.
        
        Args:
            department_id: Unique identifier for the department
            
        Returns:
            QueryResult with deletion status
        """
        start_time = datetime.now()
        
        try:
            if not self._validate_id(department_id):
                return self._create_result(error="Invalid department ID")
            
            # Check if department exists
            existing_result = await self.get_by_id(department_id)
            if not existing_result.success:
                return existing_result
            
            existing_department = existing_result.data
            
            # Check if department has children
            if existing_department.get('children_ids'):
                return self._create_result(error="Cannot delete department with children departments")
            
            # Check if department has programs or courses
            if existing_department.get('program_ids') or existing_department.get('course_ids'):
                return self._create_result(error="Cannot delete department with active programs or courses")
            
            # Remove from parent's children list
            if existing_department.get('parent_id'):
                await self._update_parent_children(existing_department['parent_id'], department_id, remove=True)
            
            # Delete the department
            query = "DELETE FROM departments WHERE id = $1"
            result = await self.db.execute_query(query, [department_id])
            
            if result.success:
                query_time = (datetime.now() - start_time).total_seconds()
                
                self._log_operation(
                    operation=BaseRepository.RepositoryOperation.DELETE,
                    entity_id=department_id,
                    duration=query_time,
                    success=True
                )
                
                return self._create_result(
                    data={"deleted": True, "department_id": department_id},
                    query_time=query_time
                )
            else:
                query_time = (datetime.now() - start_time).total_seconds()
                return self._create_result(
                    error="Failed to delete department",
                    query_time=query_time
                )
                
        except Exception as e:
            query_time = (datetime.now() - start_time).total_seconds()
            self.logger.error(f"Error deleting department {department_id}: {str(e)}")
            return self._create_result(
                error=f"Database error deleting department: {str(e)}",
                query_time=query_time
            )
    
    async def list_all(self, limit: int = 100, offset: int = 0) -> QueryResult:
        """
        List all departments with pagination.
        
        Args:
            limit: Maximum number of departments to return
            offset: Number of departments to skip
            
        Returns:
            QueryResult with list of departments
        """
        start_time = datetime.now()
        
        try:
            query = "SELECT * FROM departments ORDER BY created_at DESC LIMIT $1 OFFSET $2"
            result = await self.db.execute_query(query, [limit, offset])
            
            if result.success:
                departments = [self._parse_json_fields(dept) for dept in result.data]
                query_time = (datetime.now() - start_time).total_seconds()
                
                # Get total count
                count_query = "SELECT COUNT(*) FROM departments"
                count_result = await self.db.execute_query(count_query)
                total_count = count_result.data[0][0] if count_result.success else 0
                
                self._log_operation(
                    operation=BaseRepository.RepositoryOperation.LIST,
                    duration=query_time,
                    success=True
                )
                
                return self._create_result(
                    data=departments,
                    total_count=total_count,
                    query_time=query_time
                )
            else:
                query_time = (datetime.now() - start_time).total_seconds()
                return self._create_result(
                    error="Failed to list departments",
                    query_time=query_time
                )
                
        except Exception as e:
            query_time = (datetime.now() - start_time).total_seconds()
            self.logger.error(f"Error listing departments: {str(e)}")
            return self._create_result(
                error=f"Database error listing departments: {str(e)}",
                query_time=query_time
            )
    
    async def search(self, search_term: str, limit: int = 100, offset: int = 0) -> QueryResult:
        """
        Search departments by term.
        
        Args:
            search_term: Search term for filtering
            limit: Maximum number of departments to return
            offset: Number of departments to skip
            
        Returns:
            QueryResult with search results
        """
        start_time = datetime.now()
        
        try:
            if not search_term:
                return await self.list_all(limit, offset)
            
            # Search in code, name, and description
            query = """
            SELECT * FROM departments 
            WHERE (LOWER(code) LIKE LOWER($1) OR 
                   LOWER(name) LIKE LOWER($1) OR 
                   LOWER(description) LIKE LOWER($1))
            ORDER BY created_at DESC 
            LIMIT $2 OFFSET $3
            """
            
            search_pattern = f"%{search_term}%"
            result = await self.db.execute_query(query, [search_pattern, limit, offset])
            
            if result.success:
                departments = [self._parse_json_fields(dept) for dept in result.data]
                query_time = (datetime.now() - start_time).total_seconds()
                
                # Get total count
                count_query = """
                SELECT COUNT(*) FROM departments 
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
                    data=departments,
                    total_count=total_count,
                    query_time=query_time
                )
            else:
                query_time = (datetime.now() - start_time).total_seconds()
                return self._create_result(
                    error="Failed to search departments",
                    query_time=query_time
                )
                
        except Exception as e:
            query_time = (datetime.now() - start_time).total_seconds()
            self.logger.error(f"Error searching departments: {str(e)}")
            return self._create_result(
                error=f"Database error searching departments: {str(e)}",
                query_time=query_time
            )
    
    async def filter(self, filters: Dict[str, Any], limit: int = 100, offset: int = 0) -> QueryResult:
        """
        Filter departments by criteria.
        
        Args:
            filters: Filter criteria
            limit: Maximum number of departments to return
            offset: Number of departments to skip
            
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
                if field == 'parent_id':
                    conditions.append(f"parent_id = ${len(values) + 1}")
                    values.append(value)
                elif field == 'status':
                    conditions.append(f"status = ${len(values) + 1}")
                    values.append(value)
                elif field == 'head_of_department':
                    conditions.append(f"head_of_department = ${len(values) + 1}")
                    values.append(value)
                elif field == 'contact_email':
                    conditions.append(f"contact_email = ${len(values) + 1}")
                    values.append(value)
                elif field == 'has_children':
                    conditions.append(f"children_ids IS NOT NULL AND children_ids != '[]'")
                elif field == 'has_programs':
                    conditions.append(f"program_ids IS NOT NULL AND program_ids != '[]'")
                elif field == 'has_courses':
                    conditions.append(f"course_ids IS NOT NULL AND course_ids != '[]'")
                elif field == 'keyword':
                    conditions.append(f"(LOWER(code) LIKE LOWER(${len(values) + 1}) OR "
                                    f"LOWER(name) LIKE LOWER(${len(values) + 1}) OR "
                                    f"LOWER(description) LIKE LOWER(${len(values) + 1}))")
                    keyword_pattern = f"%{value}%"
                    values.extend([keyword_pattern, keyword_pattern, keyword_pattern])
            
            query_conditions = " AND ".join(conditions) if conditions else "1=1"
            query = f"SELECT * FROM departments WHERE {query_conditions} ORDER BY created_at DESC LIMIT ${len(values) + 1} OFFSET ${len(values) + 2}"
            
            values.extend([limit, offset])
            result = await self.db.execute_query(query, values)
            
            if result.success:
                departments = [self._parse_json_fields(dept) for dept in result.data]
                query_time = (datetime.now() - start_time).total_seconds()
                
                # Get total count
                count_query = f"SELECT COUNT(*) FROM departments WHERE {query_conditions}"
                count_result = await self.db.execute_query(count_query, values[:-2])
                total_count = count_result.data[0][0] if count_result.success else 0
                
                self._log_operation(
                    operation=BaseRepository.RepositoryOperation.FILTER,
                    duration=query_time,
                    success=True
                )
                
                return self._create_result(
                    data=departments,
                    total_count=total_count,
                    query_time=query_time
                )
            else:
                query_time = (datetime.now() - start_time).total_seconds()
                return self._create_result(
                    error="Failed to filter departments",
                    query_time=query_time
                )
                
        except Exception as e:
            query_time = (datetime.now() - start_time).total_seconds()
            self.logger.error(f"Error filtering departments: {str(e)}")
            return self._create_result(
                error=f"Database error filtering departments: {str(e)}",
                query_time=query_time
            )
    
    async def get_department_hierarchy(self, department_id: str) -> QueryResult:
        """
        Get the complete hierarchy for a department.
        
        Args:
            department_id: Unique identifier for the department
            
        Returns:
            QueryResult with department hierarchy data
        """
        start_time = datetime.now()
        
        try:
            if not self._validate_id(department_id):
                return self._create_result(error="Invalid department ID")
            
            # Get department and build hierarchy
            department_result = await self.get_by_id(department_id)
            if not department_result.success:
                return department_result
            
            department = department_result.data
            hierarchy = await self._build_department_hierarchy(department_id)
            
            query_time = (datetime.now() - start_time).total_seconds()
            self._log_operation(
                operation=BaseRepository.RepositoryOperation.READ,
                entity_id=f"{department_id}_hierarchy",
                duration=query_time,
                success=True
            )
            
            return self._create_result(
                data={
                    'department': department,
                    'hierarchy': hierarchy,
                    'depth': len(hierarchy) - 1
                },
                query_time=query_time
            )
                
        except Exception as e:
            query_time = (datetime.now() - start_time).total_seconds()
            self.logger.error(f"Error getting department hierarchy for {department_id}: {str(e)}")
            return self._create_result(
                error=f"Database error getting department hierarchy: {str(e)}",
                query_time=query_time
            )
    
    async def add_program_to_department(self, department_id: str, program_id: str) -> QueryResult:
        """
        Add a program to a department.
        
        Args:
            department_id: Unique identifier for the department
            program_id: Unique identifier for the program
            
        Returns:
            QueryResult with updated department
        """
        start_time = datetime.now()
        
        try:
            if not self._validate_id(department_id):
                return self._create_result(error="Invalid department ID")
            
            if not self._validate_id(program_id):
                return self._create_result(error="Invalid program ID")
            
            # Get department
            department_result = await self.get_by_id(department_id)
            if not department_result.success:
                return department_result
            
            department = department_result.data
            program_ids = department.get('program_ids', [])
            
            # Check if program already exists
            if program_id in program_ids:
                return self._create_result(error="Program already exists in department")
            
            # Add program
            program_ids.append(program_id)
            
            # Update department
            update_result = await self.update(department_id, {'program_ids': program_ids})
            query_time = (datetime.now() - start_time).total_seconds()
            
            self._log_operation(
                operation=BaseRepository.RepositoryOperation.UPDATE,
                entity_id=f"{department_id}_program_{program_id}",
                duration=query_time,
                success=True
            )
            
            return self._create_result(
                data=update_result.data,
                query_time=query_time
            )
                
        except Exception as e:
            query_time = (datetime.now() - start_time).total_seconds()
            self.logger.error(f"Error adding program {program_id} to department {department_id}: {str(e)}")
            return self._create_result(
                error=f"Database error adding program to department: {str(e)}",
                query_time=query_time
            )
    
    async def remove_program_from_department(self, department_id: str, program_id: str) -> QueryResult:
        """
        Remove a program from a department.
        
        Args:
            department_id: Unique identifier for the department
            program_id: Unique identifier for the program
            
        Returns:
            QueryResult with updated department
        """
        start_time = datetime.now()
        
        try:
            if not self._validate_id(department_id):
                return self._create_result(error="Invalid department ID")
            
            if not self._validate_id(program_id):
                return self._create_result(error="Invalid program ID")
            
            # Get department
            department_result = await self.get_by_id(department_id)
            if not department_result.success:
                return department_result
            
            department = department_result.data
            program_ids = department.get('program_ids', [])
            
            # Check if program exists
            if program_id not in program_ids:
                return self._create_result(error="Program not found in department")
            
            # Remove program
            program_ids.remove(program_id)
            
            # Update department
            update_result = await self.update(department_id, {'program_ids': program_ids})
            query_time = (datetime.now() - start_time).total_seconds()
            
            self._log_operation(
                operation=BaseRepository.RepositoryOperation.UPDATE,
                entity_id=f"{department_id}_program_{program_id}",
                duration=query_time,
                success=True
            )
            
            return self._create_result(
                data=update_result.data,
                query_time=query_time
            )
                
        except Exception as e:
            query_time = (datetime.now() - start_time).total_seconds()
            self.logger.error(f"Error removing program {program_id} from department {department_id}: {str(e)}")
            return self._create_result(
                error=f"Database error removing program from department: {str(e)}",
                query_time=query_time
            )
    
    async def get_department_statistics(self, department_id: str) -> QueryResult:
        """
        Get statistics for a department.
        
        Args:
            department_id: Unique identifier for the department
            
        Returns:
            QueryResult with department statistics
        """
        start_time = datetime.now()
        
        try:
            if not self._validate_id(department_id):
                return self._create_result(error="Invalid department ID")
            
            # Get department
            department_result = await self.get_by_id(department_id)
            if not department_result.success:
                return department_result
            
            department = department_result.data
            
            # Build statistics
            statistics = {
                'department_id': department_id,
                'department_name': department['name'],
                'parent_department': department.get('parent_id'),
                'children_departments': len(department.get('children_ids', [])),
                'programs_count': len(department.get('program_ids', [])),
                'courses_count': len(department.get('course_ids', [])),
                'head_of_department': department.get('head_of_department'),
                'status': department.get('status'),
                'metadata': department.get('metadata', {})
            }
            
            query_time = (datetime.now() - start_time).total_seconds()
            self._log_operation(
                operation=BaseRepository.RepositoryOperation.READ,
                entity_id=f"{department_id}_statistics",
                duration=query_time,
                success=True
            )
            
            return self._create_result(
                data=statistics,
                query_time=query_time
            )
                
        except Exception as e:
            query_time = (datetime.now() - start_time).total_seconds()
            self.logger.error(f"Error getting department statistics for {department_id}: {str(e)}")
            return self._create_result(
                error=f"Database error getting department statistics: {str(e)}",
                query_time=query_time
            )
    
    async def _update_parent_children(self, parent_id: str, child_id: str, remove: bool = False) -> QueryResult:
        """
        Update parent's children list.
        
        Args:
            parent_id: Parent department ID
            child_id: Child department ID
            remove: Whether to remove (True) or add (False) the child
            
        Returns:
            QueryResult with update status
        """
        try:
            parent_result = await self.get_by_id(parent_id)
            if not parent_result.success:
                return parent_result
            
            parent = parent_result.data
            children_ids = parent.get('children_ids', [])
            
            if remove:
                if child_id in children_ids:
                    children_ids.remove(child_id)
            else:
                if child_id not in children_ids:
                    children_ids.append(child_id)
            
            update_result = await self.update(parent_id, {'children_ids': children_ids})
            return update_result
            
        except Exception as e:
            self.logger.error(f"Error updating parent children: {str(e)}")
            return self._create_result(error=f"Database error updating parent children: {str(e)}")
    
    async def _build_department_hierarchy(self, department_id: str) -> List[Dict[str, Any]]:
        """
        Build complete department hierarchy.
        
        Args:
            department_id: Department ID to build hierarchy for
            
        Returns:
            List representing the hierarchy
        """
        try:
            result = await self.get_by_id(department_id)
            if not result.success:
                return []
            
            department = result.data
            hierarchy = [department]
            
            # Recursively build hierarchy for children
            children_ids = department.get('children_ids', [])
            for child_id in children_ids:
                child_hierarchy = await self._build_department_hierarchy(child_id)
                hierarchy.extend(child_hierarchy)
            
            return hierarchy
            
        except Exception as e:
            self.logger.error(f"Error building department hierarchy: {str(e)}")
            return []
    
    async def _has_circular_reference(self, parent_id: str, child_id: str) -> bool:
        """
        Check if adding a parent would create a circular reference.
        
        Args:
            parent_id: Proposed parent department ID
            child_id: Proposed child department ID
            
        Returns:
            True if circular reference would exist, False otherwise
        """
        try:
            # Check if parent is already a descendant of child
            hierarchy = await self._build_department_hierarchy(parent_id)
            descendant_ids = [dept['id'] for dept in hierarchy]
            return child_id in descendant_ids
            
        except Exception as e:
            self.logger.error(f"Error checking circular reference: {str(e)}")
            return True  # Fail-safe: assume circular reference
    
    def _parse_json_fields(self, department_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Parse JSON fields back to dictionary format.
        
        Args:
            department_data: Department data from database
            
        Returns:
            Department data with parsed JSON fields
        """
        if not department_data:
            return {}
        
        parsed_data = department_data.copy()
        
        # Parse JSON fields
        if 'children_ids' in parsed_data and parsed_data['children_ids']:
            try:
                parsed_data['children_ids'] = json.loads(parsed_data['children_ids'])
            except json.JSONDecodeError:
                parsed_data['children_ids'] = []
        
        if 'program_ids' in parsed_data and parsed_data['program_ids']:
            try:
                parsed_data['program_ids'] = json.loads(parsed_data['program_ids'])
            except json.JSONDecodeError:
                parsed_data['program_ids'] = []
        
        if 'course_ids' in parsed_data and parsed_data['course_ids']:
            try:
                parsed_data['course_ids'] = json.loads(parsed_data['course_ids'])
            except json.JSONDecodeError:
                parsed_data['course_ids'] = []
        
        if 'metadata' in parsed_data and parsed_data['metadata']:
            try:
                parsed_data['metadata'] = json.loads(parsed_data['metadata'])
            except json.JSONDecodeError:
                parsed_data['metadata'] = {}
        
        return parsed_data