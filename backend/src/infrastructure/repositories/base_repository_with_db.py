"""
Base Repository with Database Manager

This module provides a base repository implementation that includes a database manager.
It's designed for repositories that need direct database access.

Author: Edu-Flow Team
"""

from typing import List, Optional, Dict, Any
from datetime import datetime
from abc import ABC, abstractmethod
import logging

from src.core.exceptions import DatabaseError, NotFoundError, ValidationError
from src.core.logging import get_logger
from src.infrastructure.repositories.base_repository import BaseRepository, QueryResult

logger = get_logger(__name__)


class BaseRepositoryWithDB(BaseRepository):
    """Base repository implementation with database manager support."""
    
    def __init__(self, collection_name: str, database_manager):
        """
        Initialize the repository with database manager.
        
        Args:
            collection_name: Name of the database collection
            database_manager: Database connection manager instance
        """
        super().__init__(collection_name)
        self.db = database_manager
        self.logger = get_logger(f"{__name__}.{self.__class__.__name__}")
        
    async def create(self, entity_data: Dict[str, Any]) -> QueryResult:
        """Create a new entity."""
        try:
            # Validate entity data
            if not self._validate_entity_data(entity_data):
                return QueryResult(success=False, error="Invalid entity data")
            
            # Add timestamps
            if 'created_at' not in entity_data:
                entity_data['created_at'] = datetime.utcnow().isoformat()
            if 'updated_at' not in entity_data:
                entity_data['updated_at'] = datetime.utcnow().isoformat()
            
            # Generate ID if not provided
            if 'id' not in entity_data:
                import uuid
                entity_data['id'] = str(uuid.uuid4())
            
            # Insert document
            doc_id = await self.db.insert_one(self._collection_name, entity_data)
            entity_data['id'] = doc_id
            
            return QueryResult(success=True, data=entity_data)
            
        except Exception as e:
            self.logger.error(f"Failed to create entity: {str(e)}")
            return QueryResult(success=False, error=f"Failed to create entity: {str(e)}")
    
    async def get_by_id(self, entity_id: str) -> QueryResult:
        """Get entity by ID."""
        try:
            entity = await self.db.find_one(self._collection_name, {"id": entity_id})
            
            if entity:
                return QueryResult(success=True, data=entity)
            
            return QueryResult(success=True, data=None)
            
        except Exception as e:
            self.logger.error(f"Failed to get entity by ID {entity_id}: {str(e)}")
            return QueryResult(success=False, error=f"Failed to get entity by ID {entity_id}: {str(e)}")
    
    async def update(self, entity_id: str, entity_data: Dict[str, Any]) -> QueryResult:
        """Update entity."""
        try:
            # Add updated timestamp
            entity_data['updated_at'] = datetime.utcnow().isoformat()
            
            # Update document
            result = await self.db.update_one(self._collection_name, {"id": entity_id}, entity_data)
            
            if result:
                # Get updated document
                updated_entity = await self.db.find_one(self._collection_name, {"id": entity_id})
                return QueryResult(success=True, data=updated_entity)
            
            return QueryResult(success=True, data=None)
            
        except Exception as e:
            self.logger.error(f"Failed to update entity {entity_id}: {str(e)}")
            return QueryResult(success=False, error=f"Failed to update entity {entity_id}: {str(e)}")
    
    async def delete(self, entity_id: str) -> QueryResult:
        """Delete entity."""
        try:
            # Delete document
            result = await self.db.delete_one(self._collection_name, {"id": entity_id})
            
            return QueryResult(success=True, data=bool(result))
            
        except Exception as e:
            self.logger.error(f"Failed to delete entity {entity_id}: {str(e)}")
            return QueryResult(success=False, error=f"Failed to delete entity {entity_id}: {str(e)}")
    
    async def list_all(self, limit: int = 100, offset: int = 0) -> QueryResult:
        """List all entities."""
        try:
            entities = await self.db.find_many(self._collection_name, {}, limit=limit, skip=offset)
            
            return QueryResult(success=True, data=entities)
            
        except Exception as e:
            self.logger.error(f"Failed to list all entities: {str(e)}")
            return QueryResult(success=False, error=f"Failed to list all entities: {str(e)}")
    
    async def search(self, search_term: str, limit: int = 100, offset: int = 0) -> QueryResult:
        """Search entities."""
        try:
            # Simplified search - search in name field
            entities = await self.db.find_many(self._collection_name, {"name": search_term}, limit=limit, skip=offset)
            
            return QueryResult(success=True, data=entities)
            
        except Exception as e:
            self.logger.error(f"Failed to search entities: {str(e)}")
            return QueryResult(success=False, error=f"Failed to search entities: {str(e)}")
    
    async def filter(self, filters: Dict[str, Any], limit: int = 100, offset: int = 0) -> QueryResult:
        """Filter entities."""
        try:
            entities = await self.db.find_many(self._collection_name, filters, limit=limit, skip=offset)
            
            return QueryResult(success=True, data=entities)
            
        except Exception as e:
            self.logger.error(f"Failed to filter entities: {str(e)}")
            return QueryResult(success=False, error=f"Failed to filter entities: {str(e)}")