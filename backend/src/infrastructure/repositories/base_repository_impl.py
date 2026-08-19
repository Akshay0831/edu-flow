"""
Base Repository Implementation

This module provides a concrete implementation of the BaseRepository abstract class.
It includes mock database operations for testing and development purposes.

Author: Edu-Flow Team
"""

from typing import List, Optional, Dict, Any, Type
from datetime import datetime
import logging
from dataclasses import dataclass
from enum import Enum

from core.exceptions import DatabaseError, NotFoundError, ValidationError
from core.logging import get_logger
from infrastructure.repositories.base_repository import BaseRepository, QueryResult, RepositoryOperation

logger = get_logger(__name__)


class MockDatabase:
    """Mock database interface for testing purposes."""
    
    def __init__(self):
        self.data = {}
    
    async def insert_one(self, collection: str, document: Dict[str, Any]) -> str:
        """Insert one document."""
        doc_id = document.get('id', str(len(self.data)))
        self.data[doc_id] = document
        return doc_id
    
    async def find_one(self, collection: str, filter: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Find one document."""
        for doc_id, doc in self.data.items():
            if all(doc.get(k) == v for k, v in filter.items()):
                return doc
        return None
    
    async def find_many(self, collection: str, filter: Dict[str, Any], limit: int = None, skip: int = None, sort: List[tuple] = None) -> List[Dict[str, Any]]:
        """Find multiple documents."""
        result = []
        for doc_id, doc in self.data.items():
            if all(doc.get(k) == v for k, v in filter.items()):
                result.append(doc)
        
        if skip:
            result = result[skip:]
        if limit:
            result = result[:limit]
        
        return result
    
    async def update_one(self, collection: str, filter: Dict[str, Any], update: Dict[str, Any]) -> int:
        """Update one document."""
        for doc_id, doc in self.data.items():
            if all(doc.get(k) == v for k, v in filter.items()):
                self.data[doc_id].update(update)
                return 1
        return 0
    
    async def update_many(self, collection: str, filter: Dict[str, Any], update: Dict[str, Any]) -> int:
        """Update multiple documents."""
        count = 0
        for doc_id, doc in self.data.items():
            if all(doc.get(k) == v for k, v in filter.items()):
                self.data[doc_id].update(update)
                count += 1
        return count
    
    async def delete_one(self, collection: str, filter: Dict[str, Any]) -> int:
        """Delete one document."""
        for doc_id in list(self.data.keys()):
            doc = self.data[doc_id]
            if all(doc.get(k) == v for k, v in filter.items()):
                del self.data[doc_id]
                return 1
        return 0
    
    async def delete_many(self, collection: str, filter: Dict[str, Any]) -> int:
        """Delete multiple documents."""
        count = 0
        for doc_id in list(self.data.keys()):
            doc = self.data[doc_id]
            if all(doc.get(k) == v for k, v in filter.items()):
                del self.data[doc_id]
                count += 1
        return count


class BaseRepositoryImpl(BaseRepository):
    """Concrete implementation of BaseRepository with mock database."""
    
    def __init__(self, collection_name: str):
        super().__init__(collection_name)
        self._db = MockDatabase()
        self._cache = {}
    
    async def create(self, entity_data: Dict[str, Any]) -> QueryResult:
        """Create a new entity."""
        try:
            # Add timestamps
            if 'created_at' not in entity_data:
                entity_data['created_at'] = datetime.utcnow().isoformat()
            if 'updated_at' not in entity_data:
                entity_data['updated_at'] = datetime.utcnow().isoformat()
            
            # Generate ID if not provided
            if 'id' not in entity_data:
                entity_data['id'] = str(len(self._cache))
            
            # Insert document
            doc_id = await self._db.insert_one(self._collection_name, entity_data)
            self._cache[doc_id] = entity_data
            
            return QueryResult(success=True, data=entity_data)
            
        except Exception as e:
            self.logger.error(f"Failed to create entity: {str(e)}")
            return QueryResult(success=False, error=f"Failed to create entity: {str(e)}")
    
    async def get_by_id(self, entity_id: str) -> QueryResult:
        """Get entity by ID."""
        try:
            # Check cache first
            if entity_id in self._cache:
                return QueryResult(success=True, data=self._cache[entity_id])
            
            # Get from database
            entity = await self._db.find_one(self._collection_name, {"id": entity_id})
            
            if entity:
                self._cache[entity_id] = entity
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
            result = await self._db.update_one(self._collection_name, {"id": entity_id}, entity_data)
            
            if result:
                self._cache[entity_id] = entity_data
                return QueryResult(success=True, data=entity_data)
            
            return QueryResult(success=True, data=None)
            
        except Exception as e:
            self.logger.error(f"Failed to update entity {entity_id}: {str(e)}")
            return QueryResult(success=False, error=f"Failed to update entity {entity_id}: {str(e)}")
    
    async def delete(self, entity_id: str) -> QueryResult:
        """Delete entity."""
        try:
            # Remove from cache
            if entity_id in self._cache:
                del self._cache[entity_id]
            
            # Delete document
            result = await self._db.delete_one(self._collection_name, {"id": entity_id})
            
            return QueryResult(success=True, data=bool(result))
            
        except Exception as e:
            self.logger.error(f"Failed to delete entity {entity_id}: {str(e)}")
            return QueryResult(success=False, error=f"Failed to delete entity {entity_id}: {str(e)}")
    
    async def list_all(self, limit: int = 100, offset: int = 0) -> QueryResult:
        """List all entities."""
        try:
            entities = await self._db.find_many(self._collection_name, {}, limit=limit, skip=offset)
            
            # Cache results
            for entity in entities:
                self._cache[entity['id']] = entity
            
            return QueryResult(success=True, data=entities)
            
        except Exception as e:
            self.logger.error(f"Failed to list all entities: {str(e)}")
            return QueryResult(success=False, error=f"Failed to list all entities: {str(e)}")
    
    async def search(self, search_term: str, limit: int = 100, offset: int = 0) -> QueryResult:
        """Search entities."""
        try:
            # Simplified search - search in name field
            filter_dict = {"name": search_term}
            entities = await self._db.find_many(self._collection_name, filter_dict, limit=limit, skip=offset)
            
            # Cache results
            for entity in entities:
                self._cache[entity['id']] = entity
            
            return QueryResult(success=True, data=entities)
            
        except Exception as e:
            self.logger.error(f"Failed to search entities: {str(e)}")
            return QueryResult(success=False, error=f"Failed to search entities: {str(e)}")
    
    async def filter(self, filters: Dict[str, Any], limit: int = 100, offset: int = 0) -> QueryResult:
        """Filter entities."""
        try:
            entities = await self._db.find_many(self._collection_name, filters, limit=limit, skip=offset)
            
            # Cache results
            for entity in entities:
                self._cache[entity['id']] = entity
            
            return QueryResult(success=True, data=entities)
            
        except Exception as e:
            self.logger.error(f"Failed to filter entities: {str(e)}")
            return QueryResult(success=False, error=f"Failed to filter entities: {str(e)}")