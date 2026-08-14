"""
Mock Database Manager

This module provides a mock database manager for testing repository operations.
It simulates database functionality without requiring a real database connection.

Author: Edu-Flow Team
"""

import asyncio
from typing import Dict, Any, Optional, List
from datetime import datetime
import json

from src.core.logging import get_logger

logger = get_logger(__name__)


class MockDatabaseManager:
    """Mock database manager for testing."""
    
    def __init__(self):
        self.data = {}
        self.collections = {
            "students": {},
            "teachers": {},
            "courses": {},
            "classes": {},
            "subjects": {},
            "departments": {},
            "marks": {},
            "timetable_entries": {},
            "grades": {},
            "laboratories": {},
            "rooms": {}
        }
        
    async def insert_one(self, collection: str, document: Dict[str, Any]) -> str:
        """Insert one document."""
        if collection not in self.collections:
            self.collections[collection] = {}
        
        doc_id = document.get('id', str(len(self.collections[collection])))
        self.collections[collection][doc_id] = document
        return doc_id
    
    async def find_one(self, collection: str, filter: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Find one document."""
        if collection not in self.collections:
            return None
            
        for doc_id, doc in self.collections[collection].items():
            if all(doc.get(k) == v for k, v in filter.items()):
                return doc
        return None
    
    async def find_many(self, collection: str, filter: Dict[str, Any], limit: int = None, skip: int = None) -> List[Dict[str, Any]]:
        """Find multiple documents."""
        if collection not in self.collections:
            return []
            
        result = []
        for doc_id, doc in self.collections[collection].items():
            if all(doc.get(k) == v for k, v in filter.items()):
                result.append(doc)
        
        if skip:
            result = result[skip:]
        if limit:
            result = result[:limit]
        
        return result
    
    async def update_one(self, collection: str, filter: Dict[str, Any], update: Dict[str, Any]) -> int:
        """Update one document."""
        if collection not in self.collections:
            return 0
            
        for doc_id, doc in self.collections[collection].items():
            if all(doc.get(k) == v for k, v in filter.items()):
                self.collections[collection][doc_id].update(update)
                return 1
        return 0
    
    async def delete_one(self, collection: str, filter: Dict[str, Any]) -> int:
        """Delete one document."""
        if collection not in self.collections:
            return 0
            
        for doc_id in list(self.collections[collection].keys()):
            doc = self.collections[collection][doc_id]
            if all(doc.get(k) == v for k, v in filter.items()):
                del self.collections[collection][doc_id]
                return 1
        return 0
    
    async def create_index(self, collection: str, field: str):
        """Create an index (mock implementation)."""
        pass
    
    async def ensure_indexes(self):
        """Ensure all indexes exist (mock implementation)."""
        pass


# Global instance for testing
mock_db_manager = MockDatabaseManager()