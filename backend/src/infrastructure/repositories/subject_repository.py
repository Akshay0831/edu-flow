"""
Subject Repository

This module provides the repository layer for Subject entity operations.
It handles all database interactions related to subjects including CRUD operations,
prerequisite relationships, CO-PO mapping, and subject management.

Author: Edu-Flow Team
"""

from typing import List, Optional, Dict, Any, Type
from datetime import datetime
import logging
from dataclasses import dataclass
from enum import Enum
import json

from core.exceptions import DatabaseError, NotFoundError, ValidationError
from core.logging import get_logger
from infrastructure.repositories.base_repository_with_db import BaseRepositoryWithDB, QueryResult
from models.subject_model import SubjectCreate, SubjectUpdate, SubjectResponse

logger = get_logger(__name__)


class SubjectFilter(Enum):
    """Subject filter types."""
    BY_DEPARTMENT = "department"
    BY_PROGRAM = "program"
    BY_SEMESTER = "semester"
    BY_PREREQUISITES = "prerequisites"
    BY_CO_PO_MAPPED = "co_po_mapped"
    BY_BLOOM_TAXONOMY = "bloom_taxonomy"
    BY_COURSE_CATALOG = "course_catalog"
    BY_KEYWORD = "keyword"


class SortOrder(Enum):
    """Sort order for subject queries."""
    ASC = "asc"
    DESC = "desc"


@dataclass
class SubjectQuery:
    """Structured query for subject operations."""
    filters: Dict[str, Any] = None
    sort_by: str = None
    sort_order: SortOrder = SortOrder.ASC
    limit: int = 100
    offset: int = 0
    search_term: str = None


class SubjectRepository(BaseRepositoryWithDB):
    """
    Repository for Subject entity operations.
    
    Handles CRUD operations, prerequisite relationships, CO-PO mapping,
    and complex subject management queries.
    """
    
    def __init__(self, database_manager):
        """
        Initialize the subject repository.
        
        Args:
            database_manager: Database connection manager instance
        """
        super().__init__("subjects", database_manager)
    
    async def create(self, subject_data: Dict[str, Any]) -> QueryResult:
        """
        Create a new subject in the database.
        
        Args:
            subject_data: Subject data including all required fields
            
        Returns:
            QueryResult with created subject
        """
        start_time = datetime.now()
        
        try:
            # Validate subject data
            if not self._validate_entity_data(subject_data):
                return self._create_result(error="Invalid subject data")
            
            # Validate required fields
            required_fields = ['code', 'name', 'description', 'credits', 'department_id']
            for field in required_fields:
                if field not in subject_data:
                    return self._create_result(error=f"Missing required field: {field}")
            
            # Set default values for optional fields
            subject_data.setdefault('created_at', datetime.now())
            subject_data.setdefault('updated_at', datetime.now())
            subject_data.setdefault('is_active', True)
            
            # Convert complex fields to JSON strings for storage
            if 'course_catalog' in subject_data:
                subject_data['course_catalog'] = json.dumps(subject_data['course_catalog'])
            if 'prerequisites' in subject_data:
                subject_data['prerequisites'] = json.dumps(subject_data['prerequisites'])
            if 'co_po_map' in subject_data:
                subject_data['co_po_map'] = json.dumps(subject_data['co_po_map'])
            
            # Insert into database
            query = """
            INSERT INTO subjects 
            (code, name, description, credits, department_id, course_catalog, 
             prerequisites, co_po_map, bloom_taxonomy_level, is_active, created_at, updated_at)
            VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11, $12)
            RETURNING *
            """
            
            values = [
                subject_data['code'],
                subject_data['name'],
                subject_data['description'],
                subject_data['credits'],
                subject_data['department_id'],
                subject_data.get('course_catalog'),
                subject_data.get('prerequisites'),
                subject_data.get('co_po_map'),
                subject_data.get('bloom_taxonomy_level'),
                subject_data.get('is_active'),
                subject_data['created_at'],
                subject_data['updated_at']
            ]
            
            result = await self.db.execute_query(query, values)
            
            if result.success and result.data:
                # Parse JSON fields back to dict
                created_subject = self._parse_json_fields(result.data[0])
                query_time = (datetime.now() - start_time).total_seconds()
                
                self._log_operation(
                    operation=BaseRepository.RepositoryOperation.CREATE,
                    duration=query_time,
                    success=True
                )
                
                return self._create_result(
                    data=created_subject,
                    query_time=query_time
                )
            else:
                return self._create_result(error="Failed to create subject")
                
        except Exception as e:
            query_time = (datetime.now() - start_time).total_seconds()
            self.logger.error(f"Error creating subject: {str(e)}")
            return self._create_result(
                error=f"Database error creating subject: {str(e)}",
                query_time=query_time
            )
    
    async def get_by_id(self, subject_id: str) -> QueryResult:
        """
        Get a subject by its ID.
        
        Args:
            subject_id: Unique identifier for the subject
            
        Returns:
            QueryResult with the subject data
        """
        start_time = datetime.now()
        
        try:
            if not self._validate_id(subject_id):
                return self._create_result(error="Invalid subject ID")
            
            query = "SELECT * FROM subjects WHERE id = $1"
            result = await self.db.execute_query(query, [subject_id])
            
            if result.success and result.data:
                subject = self._parse_json_fields(result.data[0])
                query_time = (datetime.now() - start_time).total_seconds()
                
                self._log_operation(
                    operation=BaseRepository.RepositoryOperation.READ,
                    entity_id=subject_id,
                    duration=query_time,
                    success=True
                )
                
                return self._create_result(
                    data=subject,
                    query_time=query_time
                )
            else:
                query_time = (datetime.now() - start_time).total_seconds()
                self._log_operation(
                    operation=BaseRepository.RepositoryOperation.READ,
                    entity_id=subject_id,
                    duration=query_time,
                    success=False
                )
                return self._create_result(
                    error="Subject not found",
                    query_time=query_time
                )
                
        except Exception as e:
            query_time = (datetime.now() - start_time).total_seconds()
            self.logger.error(f"Error getting subject {subject_id}: {str(e)}")
            return self._create_result(
                error=f"Database error getting subject: {str(e)}",
                query_time=query_time
            )
    
    async def update(self, subject_id: str, subject_data: Dict[str, Any]) -> QueryResult:
        """
        Update an existing subject.
        
        Args:
            subject_id: Unique identifier for the subject
            subject_data: Updated data for the subject
            
        Returns:
            QueryResult with the updated subject
        """
        start_time = datetime.now()
        
        try:
            if not self._validate_id(subject_id):
                return self._create_result(error="Invalid subject ID")
            
            if not self._validate_entity_data(subject_data):
                return self._create_result(error="Invalid subject data")
            
            # Check if subject exists
            existing_result = await self.get_by_id(subject_id)
            if not existing_result.success:
                return existing_result
            
            # Convert complex fields to JSON strings
            if 'course_catalog' in subject_data:
                subject_data['course_catalog'] = json.dumps(subject_data['course_catalog'])
            if 'prerequisites' in subject_data:
                subject_data['prerequisites'] = json.dumps(subject_data['prerequisites'])
            if 'co_po_map' in subject_data:
                subject_data['co_po_map'] = json.dumps(subject_data['co_po_map'])
            
            # Update timestamp
            subject_data['updated_at'] = datetime.now()
            
            # Build update query dynamically
            update_fields = []
            values = []
            
            for field, value in subject_data.items():
                if field != 'id':
                    update_fields.append(f"{field} = ${len(values) + 1}")
                    values.append(value)
            
            values.append(subject_id)
            query = f"""
            UPDATE subjects 
            SET {', '.join(update_fields)} 
            WHERE id = ${len(values)}
            RETURNING *
            """
            
            result = await self.db.execute_query(query, values)
            
            if result.success and result.data:
                updated_subject = self._parse_json_fields(result.data[0])
                query_time = (datetime.now() - start_time).total_seconds()
                
                self._log_operation(
                    operation=BaseRepository.RepositoryOperation.UPDATE,
                    entity_id=subject_id,
                    duration=query_time,
                    success=True
                )
                
                return self._create_result(
                    data=updated_subject,
                    query_time=query_time
                )
            else:
                query_time = (datetime.now() - start_time).total_seconds()
                return self._create_result(
                    error="Failed to update subject",
                    query_time=query_time
                )
                
        except Exception as e:
            query_time = (datetime.now() - start_time).total_seconds()
            self.logger.error(f"Error updating subject {subject_id}: {str(e)}")
            return self._create_result(
                error=f"Database error updating subject: {str(e)}",
                query_time=query_time
            )
    
    async def delete(self, subject_id: str) -> QueryResult:
        """
        Delete a subject by its ID.
        
        Args:
            subject_id: Unique identifier for the subject
            
        Returns:
            QueryResult with deletion status
        """
        start_time = datetime.now()
        
        try:
            if not self._validate_id(subject_id):
                return self._create_result(error="Invalid subject ID")
            
            # Check if subject exists
            existing_result = await self.get_by_id(subject_id)
            if not existing_result.success:
                return existing_result
            
            # Delete the subject
            query = "DELETE FROM subjects WHERE id = $1"
            result = await self.db.execute_query(query, [subject_id])
            
            if result.success:
                query_time = (datetime.now() - start_time).total_seconds()
                
                self._log_operation(
                    operation=BaseRepository.RepositoryOperation.DELETE,
                    entity_id=subject_id,
                    duration=query_time,
                    success=True
                )
                
                return self._create_result(
                    data={"deleted": True, "subject_id": subject_id},
                    query_time=query_time
                )
            else:
                query_time = (datetime.now() - start_time).total_seconds()
                return self._create_result(
                    error="Failed to delete subject",
                    query_time=query_time
                )
                
        except Exception as e:
            query_time = (datetime.now() - start_time).total_seconds()
            self.logger.error(f"Error deleting subject {subject_id}: {str(e)}")
            return self._create_result(
                error=f"Database error deleting subject: {str(e)}",
                query_time=query_time
            )
    
    async def list_all(self, limit: int = 100, offset: int = 0) -> QueryResult:
        """
        List all subjects with pagination.
        
        Args:
            limit: Maximum number of subjects to return
            offset: Number of subjects to skip
            
        Returns:
            QueryResult with list of subjects
        """
        start_time = datetime.now()
        
        try:
            query = "SELECT * FROM subjects ORDER BY created_at DESC LIMIT $1 OFFSET $2"
            result = await self.db.execute_query(query, [limit, offset])
            
            if result.success:
                subjects = [self._parse_json_fields(subject) for subject in result.data]
                query_time = (datetime.now() - start_time).total_seconds()
                
                # Get total count
                count_query = "SELECT COUNT(*) FROM subjects"
                count_result = await self.db.execute_query(count_query)
                total_count = count_result.data[0][0] if count_result.success else 0
                
                self._log_operation(
                    operation=BaseRepository.RepositoryOperation.LIST,
                    duration=query_time,
                    success=True
                )
                
                return self._create_result(
                    data=subjects,
                    total_count=total_count,
                    query_time=query_time
                )
            else:
                query_time = (datetime.now() - start_time).total_seconds()
                return self._create_result(
                    error="Failed to list subjects",
                    query_time=query_time
                )
                
        except Exception as e:
            query_time = (datetime.now() - start_time).total_seconds()
            self.logger.error(f"Error listing subjects: {str(e)}")
            return self._create_result(
                error=f"Database error listing subjects: {str(e)}",
                query_time=query_time
            )
    
    async def search(self, search_term: str, limit: int = 100, offset: int = 0) -> QueryResult:
        """
        Search subjects by term.
        
        Args:
            search_term: Search term for filtering
            limit: Maximum number of subjects to return
            offset: Number of subjects to skip
            
        Returns:
            QueryResult with search results
        """
        start_time = datetime.now()
        
        try:
            if not search_term:
                return await self.list_all(limit, offset)
            
            # Search in code, name, and description
            query = """
            SELECT * FROM subjects 
            WHERE (LOWER(code) LIKE LOWER($1) OR 
                   LOWER(name) LIKE LOWER($1) OR 
                   LOWER(description) LIKE LOWER($1))
            ORDER BY created_at DESC 
            LIMIT $2 OFFSET $3
            """
            
            search_pattern = f"%{search_term}%"
            result = await self.db.execute_query(query, [search_pattern, limit, offset])
            
            if result.success:
                subjects = [self._parse_json_fields(subject) for subject in result.data]
                query_time = (datetime.now() - start_time).total_seconds()
                
                # Get total count
                count_query = """
                SELECT COUNT(*) FROM subjects 
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
                    data=subjects,
                    total_count=total_count,
                    query_time=query_time
                )
            else:
                query_time = (datetime.now() - start_time).total_seconds()
                return self._create_result(
                    error="Failed to search subjects",
                    query_time=query_time
                )
                
        except Exception as e:
            query_time = (datetime.now() - start_time).total_seconds()
            self.logger.error(f"Error searching subjects: {str(e)}")
            return self._create_result(
                error=f"Database error searching subjects: {str(e)}",
                query_time=query_time
            )
    
    async def filter(self, filters: Dict[str, Any], limit: int = 100, offset: int = 0) -> QueryResult:
        """
        Filter subjects by criteria.
        
        Args:
            filters: Filter criteria
            limit: Maximum number of subjects to return
            offset: Number of subjects to skip
            
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
                if field == 'department_id':
                    conditions.append(f"department_id = ${len(values) + 1}")
                    values.append(value)
                elif field == 'program_id':
                    conditions.append(f"program_id = ${len(values) + 1}")
                    values.append(value)
                elif field == 'semester':
                    conditions.append(f"semester = ${len(values) + 1}")
                    values.append(value)
                elif field == 'credits':
                    conditions.append(f"credits = ${len(values) + 1}")
                    values.append(value)
                elif field == 'is_active':
                    conditions.append(f"is_active = ${len(values) + 1}")
                    values.append(value)
                elif field == 'bloom_taxonomy_level':
                    conditions.append(f"bloom_taxonomy_level = ${len(values) + 1}")
                    values.append(value)
                elif field == 'keyword':
                    conditions.append(f"(LOWER(code) LIKE LOWER(${len(values) + 1}) OR "
                                    f"LOWER(name) LIKE LOWER(${len(values) + 1}) OR "
                                    f"LOWER(description) LIKE LOWER(${len(values) + 1}))")
                    keyword_pattern = f"%{value}%"
                    values.extend([keyword_pattern, keyword_pattern, keyword_pattern])
            
            query_conditions = " AND ".join(conditions) if conditions else "1=1"
            query = f"SELECT * FROM subjects WHERE {query_conditions} ORDER BY created_at DESC LIMIT ${len(values) + 1} OFFSET ${len(values) + 2}"
            
            values.extend([limit, offset])
            result = await self.db.execute_query(query, values)
            
            if result.success:
                subjects = [self._parse_json_fields(subject) for subject in result.data]
                query_time = (datetime.now() - start_time).total_seconds()
                
                # Get total count
                count_query = f"SELECT COUNT(*) FROM subjects WHERE {query_conditions}"
                count_result = await self.db.execute_query(count_query, values[:-2])
                total_count = count_result.data[0][0] if count_result.success else 0
                
                self._log_operation(
                    operation=BaseRepository.RepositoryOperation.FILTER,
                    duration=query_time,
                    success=True
                )
                
                return self._create_result(
                    data=subjects,
                    total_count=total_count,
                    query_time=query_time
                )
            else:
                query_time = (datetime.now() - start_time).total_seconds()
                return self._create_result(
                    error="Failed to filter subjects",
                    query_time=query_time
                )
                
        except Exception as e:
            query_time = (datetime.now() - start_time).total_seconds()
            self.logger.error(f"Error filtering subjects: {str(e)}")
            return self._create_result(
                error=f"Database error filtering subjects: {str(e)}",
                query_time=query_time
            )
    
    async def get_prerequisites(self, subject_id: str) -> QueryResult:
        """
        Get prerequisites for a subject.
        
        Args:
            subject_id: Unique identifier for the subject
            
        Returns:
            QueryResult with prerequisites data
        """
        start_time = datetime.now()
        
        try:
            if not self._validate_id(subject_id):
                return self._create_result(error="Invalid subject ID")
            
            # Get subject with prerequisites
            subject_result = await self.get_by_id(subject_id)
            if not subject_result.success:
                return subject_result
            
            subject = subject_result.data
            prerequisites = subject.get('prerequisites', [])
            
            query_time = (datetime.now() - start_time).total_seconds()
            self._log_operation(
                operation=BaseRepository.RepositoryOperation.READ,
                entity_id=f"{subject_id}_prerequisites",
                duration=query_time,
                success=True
            )
            
            return self._create_result(
                data=prerequisites,
                query_time=query_time
            )
                
        except Exception as e:
            query_time = (datetime.now() - start_time).total_seconds()
            self.logger.error(f"Error getting prerequisites for subject {subject_id}: {str(e)}")
            return self._create_result(
                error=f"Database error getting prerequisites: {str(e)}",
                query_time=query_time
            )
    
    async def get_co_po_mapping(self, subject_id: str) -> QueryResult:
        """
        Get CO-PO mapping for a subject.
        
        Args:
            subject_id: Unique identifier for the subject
            
        Returns:
            QueryResult with CO-PO mapping data
        """
        start_time = datetime.now()
        
        try:
            if not self._validate_id(subject_id):
                return self._create_result(error="Invalid subject ID")
            
            # Get subject with CO-PO mapping
            subject_result = await self.get_by_id(subject_id)
            if not subject_result.success:
                return subject_result
            
            subject = subject_result.data
            co_po_mapping = subject.get('co_po_map', {})
            
            query_time = (datetime.now() - start_time).total_seconds()
            self._log_operation(
                operation=BaseRepository.RepositoryOperation.READ,
                entity_id=f"{subject_id}_co_po",
                duration=query_time,
                success=True
            )
            
            return self._create_result(
                data=co_po_mapping,
                query_time=query_time
            )
                
        except Exception as e:
            query_time = (datetime.now() - start_time).total_seconds()
            self.logger.error(f"Error getting CO-PO mapping for subject {subject_id}: {str(e)}")
            return self._create_result(
                error=f"Database error getting CO-PO mapping: {str(e)}",
                query_time=query_time
            )
    
    async def validate_prerequisites(self, subject_id: str, student_prerequisites: List[str]) -> QueryResult:
        """
        Validate if a student meets the prerequisites for a subject.
        
        Args:
            subject_id: Unique identifier for the subject
            student_prerequisites: List of subjects the student has completed
            
        Returns:
            QueryResult with validation result
        """
        start_time = datetime.now()
        
        try:
            if not self._validate_id(subject_id):
                return self._create_result(error="Invalid subject ID")
            
            # Get subject prerequisites
            prerequisites_result = await self.get_prerequisites(subject_id)
            if not prerequisites_result.success:
                return prerequisites_result
            
            subject_prerequisites = prerequisites_result.data
            missing_prerequisites = []
            
            # Check if all prerequisites are met
            for prereq in subject_prerequisites:
                if prereq not in student_prerequisites:
                    missing_prerequisites.append(prereq)
            
            query_time = (datetime.now() - start_time).total_seconds()
            self._log_operation(
                operation=BaseRepository.RepositoryOperation.READ,
                entity_id=f"{subject_id}_validation",
                duration=query_time,
                success=True
            )
            
            return self._create_result(
                data={
                    'valid': len(missing_prerequisites) == 0,
                    'missing_prerequisites': missing_prerequisites,
                    'total_prerequisites': len(subject_prerequisites),
                    'met_prerequisites': len(subject_prerequisites) - len(missing_prerequisites)
                },
                query_time=query_time
            )
                
        except Exception as e:
            query_time = (datetime.now() - start_time).total_seconds()
            self.logger.error(f"Error validating prerequisites for subject {subject_id}: {str(e)}")
            return self._create_result(
                error=f"Database error validating prerequisites: {str(e)}",
                query_time=query_time
            )
    
    def _parse_json_fields(self, subject_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Parse JSON fields back to dictionary format.
        
        Args:
            subject_data: Subject data from database
            
        Returns:
            Subject data with parsed JSON fields
        """
        if not subject_data:
            return {}
        
        parsed_data = subject_data.copy()
        
        # Parse JSON fields
        if 'course_catalog' in parsed_data and parsed_data['course_catalog']:
            try:
                parsed_data['course_catalog'] = json.loads(parsed_data['course_catalog'])
            except json.JSONDecodeError:
                parsed_data['course_catalog'] = {}
        
        if 'prerequisites' in parsed_data and parsed_data['prerequisites']:
            try:
                parsed_data['prerequisites'] = json.loads(parsed_data['prerequisites'])
            except json.JSONDecodeError:
                parsed_data['prerequisites'] = []
        
        if 'co_po_map' in parsed_data and parsed_data['co_po_map']:
            try:
                parsed_data['co_po_map'] = json.loads(parsed_data['co_po_map'])
            except json.JSONDecodeError:
                parsed_data['co_po_map'] = {}
        
        return parsed_data