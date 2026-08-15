"""
Base Repository Class

This module provides the abstract base class for all repositories.
It defines the common CRUD operations and database interface that all repositories should implement.

Author: Edu-Flow Team
"""

from abc import ABC, abstractmethod
from typing import List, Optional, Dict, Any, Type
from datetime import datetime
import logging
from dataclasses import dataclass
from enum import Enum

from src.core.exceptions import DatabaseError, NotFoundError, ValidationError
from src.core.logging import get_logger

logger = get_logger(__name__)


class RepositoryOperation(Enum):
    """Repository operation types for logging."""
    CREATE = "create"
    READ = "read"
    UPDATE = "update"
    DELETE = "delete"
    LIST = "list"
    SEARCH = "search"
    FILTER = "filter"


@dataclass
class QueryResult:
    """Standard result structure for repository operations."""
    success: bool
    data: Any = None
    error: Optional[str] = None
    total_count: int = 0
    query_time: float = 0.0


class BaseRepository(ABC):
    """
    Abstract base class for all repositories.
    
    This class provides common CRUD operations and database interface
    that all repositories should implement.
    """
    
    def __init__(self, collection_name: str):
        """
        Initialize the repository.
        
        Args:
            collection_name: Name of the database collection/table
        """
        self.collection_name = collection_name
        self.logger = get_logger(f"{__name__}.{self.__class__.__name__}")
        
    @abstractmethod
    async def create(self, entity_data: Dict[str, Any]) -> QueryResult:
        """
        Create a new entity in the database.
        
        Args:
            entity_data: Data for the new entity
            
        Returns:
            QueryResult with created entity
        """
        pass
    
    @abstractmethod
    async def get_by_id(self, entity_id: str) -> QueryResult:
        """
        Get an entity by its ID.
        
        Args:
            entity_id: Unique identifier for the entity
            
        Returns:
            QueryResult with the entity
        """
        pass
    
    @abstractmethod
    async def update(self, entity_id: str, entity_data: Dict[str, Any]) -> QueryResult:
        """
        Update an existing entity.
        
        Args:
            entity_id: Unique identifier for the entity
            entity_data: Updated data for the entity
            
        Returns:
            QueryResult with the updated entity
        """
        pass
    
    @abstractmethod
    async def delete(self, entity_id: str) -> QueryResult:
        """
        Delete an entity by its ID.
        
        Args:
            entity_id: Unique identifier for the entity
            
        Returns:
            QueryResult with deletion status
        """
        pass
    
    @abstractmethod
    async def list_all(self, limit: int = 100, offset: int = 0) -> QueryResult:
        """
        List all entities with pagination.
        
        Args:
            limit: Maximum number of entities to return
            offset: Number of entities to skip
            
        Returns:
            QueryResult with list of entities
        """
        pass
    
    @abstractmethod
    async def search(self, search_term: str, limit: int = 100, offset: int = 0) -> QueryResult:
        """
        Search entities by term.
        
        Args:
            search_term: Search term for filtering
            limit: Maximum number of entities to return
            offset: Number of entities to skip
            
        Returns:
            QueryResult with search results
        """
        pass
    
    @abstractmethod
    async def filter(self, filters: Dict[str, Any], limit: int = 100, offset: int = 0) -> QueryResult:
        """
        Filter entities by criteria.
        
        Args:
            filters: Filter criteria
            limit: Maximum number of entities to return
            offset: Number of entities to skip
            
        Returns:
            QueryResult with filtered results
        """
        pass
    
    def _validate_id(self, entity_id: str) -> bool:
        """
        Validate that an entity ID is valid.
        
        Args:
            entity_id: ID to validate
            
        Returns:
            True if valid, False otherwise
        """
        if not entity_id or not isinstance(entity_id, str):
            self.logger.error(f"Invalid entity ID: {entity_id}")
            return False
        return True
    
    def _validate_entity_data(self, entity_data: Dict[str, Any]) -> bool:
        """
        Validate entity data structure.
        
        Args:
            entity_data: Entity data to validate
            
        Returns:
            True if valid, False otherwise
        """
        if not entity_data or not isinstance(entity_data, dict):
            self.logger.error("Invalid entity data: must be a non-empty dictionary")
            return False
        return True
    
    def _log_operation(self, operation: RepositoryOperation, entity_id: str = None, duration: float = None, success: bool = True):
        """
        Log repository operation details.
        
        Args:
            operation: Type of operation performed
            entity_id: ID of entity involved (if applicable)
            duration: Time taken for operation (if applicable)
            success: Whether the operation was successful
        """
        log_data = {
            "collection": self.collection_name,
            "operation": operation.value,
            "success": success
        }
        
        if entity_id:
            log_data["entity_id"] = entity_id
        if duration:
            log_data["duration_ms"] = round(duration * 1000, 2)
            
        if success:
            self.logger.info(f"Repository operation successful: {log_data}")
        else:
            self.logger.error(f"Repository operation failed: {log_data}")
    
    def _create_result(self, data: Any = None, error: str = None, total_count: int = 0, query_time: float = 0.0) -> QueryResult:
        """
        Create a standard query result.
        
        Args:
            data: Result data
            error: Error message if any
            total_count: Total count of items
            query_time: Time taken for the query
            
        Returns:
            QueryResult instance
        """
        return QueryResult(
            success=error is None,
            data=data,
            error=error,
            total_count=total_count,
            query_time=query_time
        )