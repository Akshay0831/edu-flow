"""MongoDB repository implementation using Motor."""

from typing import List, Optional, Dict, Any, Union
from datetime import datetime
from bson import ObjectId
from src.core.base_repository import BaseRepository
from src.core.exceptions import NotFoundError, ValidationError, DatabaseError
from src.database.connection import database_manager
from src.core.validation import validate_email, validate_phone, validate_password


class MongoDBRepository(BaseRepository):
    """MongoDB repository with connection pooling and query optimization."""
    
    def __init__(self, collection_name: str, database_name: str = None):
        super().__init__(collection_name)
        self.database_name = database_name or "edu_flow"
        self.collection = None
        self._collection_ready = False
    
    async def _get_collection(self):
        """Get MongoDB collection with proper connection management."""
        if not self._collection_ready:
            await database_manager.initialize()
            async with database_manager.get_mongodb_collection(self.collection_name) as collection:
                self.collection = collection
                self._collection_ready = True
        return self.collection
    
    async def create(self, data: Dict) -> str:
        """Create a new record in MongoDB."""
        try:
            collection = await self._get_collection()
            
            # Add timestamps
            data['created_at'] = datetime.now(timezone.utc)
            data['updated_at'] = datetime.now(timezone.utc)
            
            # Insert document
            result = await collection.insert_one(data)
            
            if not result.inserted_id:
                raise DatabaseError("Failed to create document")
            
            return str(result.inserted_id)
            
        except Exception as e:
            raise DatabaseError(f"MongoDB create failed: {str(e)}")
    
    async def get(self, id: str) -> Optional[Dict]:
        """Get a record by ID from MongoDB."""
        try:
            collection = await self._get_collection()
            
            # Convert string ID to ObjectId if needed
            if isinstance(id, str) and len(id) == 24 and all(c in '0123456789abcdefABCDEF' for c in id):
                query = {'_id': ObjectId(id)}
            else:
                query = {'id': id}
            
            document = await collection.find_one(query)
            
            if document:
                # Convert ObjectId to string for JSON serialization
                if '_id' in document:
                    document['id'] = str(document['_id'])
                    del document['_id']
                
                return document
            
            return None
            
        except Exception as e:
            raise DatabaseError(f"MongoDB get failed: {str(e)}")
    
    async def update(self, id: str, data: Dict) -> bool:
        """Update a record by ID in MongoDB."""
        try:
            collection = await self._get_collection()
            
            # Convert string ID to ObjectId if needed
            if isinstance(id, str) and len(id) == 24 and all(c in '0123456789abcdefABCDEF' for c in id):
                query = {'_id': ObjectId(id)}
            else:
                query = {'id': id}
            
            # Update timestamp
            data['updated_at'] = datetime.now(timezone.utc)
            
            # Update document
            result = await collection.update_one(
                query,
                {'$set': data}
            )
            
            return result.modified_count > 0
            
        except Exception as e:
            raise DatabaseError(f"MongoDB update failed: {str(e)}")
    
    async def delete(self, id: str) -> bool:
        """Delete a record by ID from MongoDB."""
        try:
            collection = await self._get_collection()
            
            # Convert string ID to ObjectId if needed
            if isinstance(id, str) and len(id) == 24 and all(c in '0123456789abcdefABCDEF' for c in id):
                query = {'_id': ObjectId(id)}
            else:
                query = {'id': id}
            
            result = await collection.delete_one(query)
            
            return result.deleted_count > 0
            
        except Exception as e:
            raise DatabaseError(f"MongoDB delete failed: {str(e)}")
    
    async def list(self, skip: int = 0, limit: int = 100, filters: Dict = None) -> List[Dict]:
        """List records with pagination and filtering."""
        try:
            collection = await self._get_collection()
            
            # Build query with filters
            query = {}
            if filters:
                for key, value in filters.items():
                    if key.startswith('min_'):
                        field = key[4:]
                        query[field] = {'$gte': value}
                    elif key.startswith('max_'):
                        field = key[4:]
                        query[field] = {'$lte': value}
                    elif key.startswith('ne_'):
                        field = key[3:]
                        query[field] = {'$ne': value}
                    elif key.startswith('in_'):
                        field = key[3:]
                        query[field] = {'$in': value}
                    else:
                        query[key] = value
            
            # Apply pagination
            cursor = collection.find(query).skip(skip).limit(limit)
            
            # Apply sorting (default to created_at descending)
            cursor = cursor.sort('created_at', -1)
            
            # Convert results to list
            documents = await cursor.to_list(length=limit)
            
            # Convert ObjectIds to strings
            for doc in documents:
                if '_id' in doc:
                    doc['id'] = str(doc['_id'])
                    del doc['_id']
                
                # Format datetime fields
                for key, value in doc.items():
                    if isinstance(value, datetime):
                        doc[key] = value.isoformat()
            
            return documents
            
        except Exception as e:
            raise DatabaseError(f"MongoDB list failed: {str(e)}")
    
    async def count(self, filters: Dict = None) -> int:
        """Count records with optional filters."""
        try:
            collection = await self._get_collection()
            
            # Build query with filters
            query = {}
            if filters:
                for key, value in filters.items():
                    if key.startswith('min_'):
                        field = key[4:]
                        query[field] = {'$gte': value}
                    elif key.startswith('max_'):
                        field = key[4:]
                        query[field] = {'$lte': value}
                    elif key.startswith('ne_'):
                        field = key[3:]
                        query[field] = {'$ne': value}
                    elif key.startswith('in_'):
                        field = key[3:]
                        query[field] = {'$in': value}
                    else:
                        query[key] = value
            
            # Count documents
            count = await collection.count_documents(query)
            
            return count
            
        except Exception as e:
            raise DatabaseError(f"MongoDB count failed: {str(e)}")
    
    async def find_by_field(self, field: str, value: Any) -> List[Dict]:
        """Find records by a specific field."""
        try:
            collection = await self._get_collection()
            
            query = {field: value}
            cursor = collection.find(query)
            
            documents = await cursor.to_list(None)
            
            # Convert ObjectIds to strings
            for doc in documents:
                if '_id' in doc:
                    doc['id'] = str(doc['_id'])
                    del doc['_id']
            
            return documents
            
        except Exception as e:
            raise DatabaseError(f"MongoDB find_by_field failed: {str(e)}")
    
    async def aggregate(self, pipeline: List[Dict]) -> List[Dict]:
        """Perform aggregation query."""
        try:
            collection = await self._get_collection()
            
            cursor = collection.aggregate(pipeline)
            results = await cursor.to_list(None)
            
            return results
            
        except Exception as e:
            raise DatabaseError(f"MongoDB aggregate failed: {str(e)}")
    
    async def create_indexes(self, index_specs: List[Dict]) -> None:
        """Create indexes for better query performance."""
        try:
            collection = await self._get_collection()
            
            for index_spec in index_specs:
                await collection.create_index(**index_spec)
                
        except Exception as e:
            raise DatabaseError(f"MongoDB create_indexes failed: {str(e)}")
    
    async def bulk_insert(self, data_list: List[Dict]) -> List[str]:
        """Insert multiple records in bulk."""
        try:
            collection = await self._get_collection()
            
            # Add timestamps to all documents
            for data in data_list:
                data['created_at'] = datetime.now(timezone.utc)
                data['updated_at'] = datetime.now(timezone.utc)
            
            # Insert documents
            result = await collection.insert_many(data_list)
            
            return [str(id) for id in result.inserted_ids]
            
        except Exception as e:
            raise DatabaseError(f"MongoDB bulk_insert failed: {str(e)}")
    
    async def bulk_update(self, updates: List[Dict]) -> List[bool]:
        """Update multiple records in bulk."""
        try:
            collection = await self._get_collection()
            
            results = []
            for update in updates:
                doc_id = update['id']
                data = update['data']
                
                # Update timestamp
                data['updated_at'] = datetime.now(timezone.utc)
                
                # Convert string ID to ObjectId if needed
                if isinstance(doc_id, str) and len(doc_id) == 24 and all(c in '0123456789abcdefABCDEF' for c in doc_id):
                    query = {'_id': ObjectId(doc_id)}
                else:
                    query = {'id': doc_id}
                
                result = await collection.update_one(
                    query,
                    {'$set': data}
                )
                
                results.append(result.modified_count > 0)
            
            return results
            
        except Exception as e:
            raise DatabaseError(f"MongoDB bulk_update failed: {str(e)}")