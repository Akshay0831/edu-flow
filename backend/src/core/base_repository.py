"""Base Repository Pattern for all data access operations."""

from abc import ABC, abstractmethod
from typing import List, Optional, Dict, Any, Type
from datetime import datetime
import asyncio
from core.exceptions import NotFoundError, ValidationError


class BaseRepository(ABC):
    """Abstract base repository providing common data access operations."""
    
    def __init__(self, collection_name: str = None):
        self.collection_name = collection_name
        
    @abstractmethod
    async def create(self, data: Dict) -> str:
        """Create a new record in the database.
        
        Args:
            data: The data to create
            
        Returns:
            The ID of the created record
            
        Raises:
            ValidationError: If data validation fails
        """
        pass
    
    @abstractmethod
    async def get(self, id: str) -> Optional[Dict]:
        """Get a record by ID.
        
        Args:
            id: The ID of the record to retrieve
            
        Returns:
            The record data or None if not found
        """
        pass
    
    @abstractmethod
    async def update(self, id: str, data: Dict) -> bool:
        """Update a record by ID.
        
        Args:
            id: The ID of the record to update
            data: The data to update
            
        Returns:
            True if updated successfully, False if not found
        """
        pass
    
    @abstractmethod
    async def delete(self, id: str) -> bool:
        """Delete a record by ID.
        
        Args:
            id: The ID of the record to delete
            
        Returns:
            True if deleted successfully, False if not found
        """
        pass
    
    @abstractmethod
    async def list(self, skip: int = 0, limit: int = 100, filters: Dict = None) -> List[Dict]:
        """List records with pagination and filtering.
        
        Args:
            skip: Number of records to skip (for pagination)
            limit: Maximum number of records to return
            filters: Optional filters to apply
            
        Returns:
            List of records
        """
        pass
    
    @abstractmethod
    async def count(self, filters: Dict = None) -> int:
        """Count records with optional filters.
        
        Args:
            filters: Optional filters to apply
            
        Returns:
            The number of matching records
        """
        pass
    
    async def exists(self, id: str) -> bool:
        """Check if a record exists by ID.
        
        Args:
            id: The ID to check
            
        Returns:
            True if the record exists, False otherwise
        """
        record = await self.get(id)
        return record is not None
    
    async def bulk_create(self, data_list: List[Dict]) -> List[str]:
        """Create multiple records in bulk.
        
        Args:
            data_list: List of data to create
            
        Returns:
            List of created record IDs
        """
        created_ids = []
        for data in data_list:
            try:
                id = await self.create(data)
                created_ids.append(id)
            except Exception as e:
                raise ValidationError(f"Bulk creation failed: {str(e)}")
        return created_ids
    
    async def bulk_update(self, updates: List[Dict]) -> List[bool]:
        """Update multiple records in bulk.
        
        Args:
            updates: List of {id, data} dictionaries
            
        Returns:
            List of success status for each update
        """
        results = []
        for update in updates:
            try:
                result = await self.update(update['id'], update['data'])
                results.append(result)
            except Exception as e:
                results.append(False)
        return results