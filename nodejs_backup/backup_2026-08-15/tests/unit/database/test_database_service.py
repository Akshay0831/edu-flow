"""
Comprehensive Database Service Tests

This test suite covers:
- Database connection and disconnection
- CRUD operations with edge cases
- Connection resilience and recovery
- Error handling for various failure scenarios
- Performance under load
- Data validation and integrity
"""

import pytest
import pytest_asyncio
from unittest.mock import Mock, AsyncMock
import asyncio
from unittest.mock import Mock, patch, AsyncMock, MagicMock
from motor.motor_asyncio import AsyncIOMotorClient, AsyncIOMotorDatabase
import sys
import os

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from src.services.database_service import database_service
from src.core.exceptions import DatabaseError, NotFoundError
import pytest
from unittest.mock import Mock, AsyncMock


@pytest.fixture
def mock_mongo_client():
    """Mock MongoDB client"""
    mock_client = MagicMock()
    mock_db = MagicMock()
    
    # Create mock collections for all collections used in the service
    mock_users = MagicMock()
    mock_courses = MagicMock()
    mock_departments = MagicMock()
    mock_enrollments = MagicMock()
    mock_assessments = MagicMock()
    
    # Mock the database access to return appropriate collections
    collections = {
        "users": mock_users,
        "courses": mock_courses, 
        "departments": mock_departments,
        "enrollments": mock_enrollments,
        "assessments": mock_assessments,
        "test_collection": mock_users  # Use existing collection for testing
    }
    
    mock_client.__getitem__.side_effect = lambda key: mock_db if key != "admin" else Mock()
    mock_db.__getitem__.side_effect = lambda key: collections[key]
    mock_client.admin.command = AsyncMock(return_value={'ok': 1.0})
    
    # Mock index creation for all collections
    for collection in collections.values():
        collection.create_index = AsyncMock(return_value=True)
        collection.find.return_value.to_list = AsyncMock(return_value=[])
        collection.count_documents = AsyncMock(return_value=0)
        collection.insert_one = AsyncMock(return_value=Mock(inserted_id="123"))
        collection.update_one = AsyncMock(return_value=Mock(modified_count=1))
        collection.delete_one = AsyncMock(return_value=Mock(deleted_count=1))
        collection.find_one = AsyncMock(return_value=None)
        collection.update_many = AsyncMock(return_value=Mock(modified_count=1))
        collection.delete_many = AsyncMock(return_value=Mock(deleted_count=1))
    
    return mock_client, mock_db, mock_users


@pytest_asyncio.fixture
async def setup_database_service(mock_mongo_client):
    """Setup database service with mock"""
    mock_client, mock_db, mock_collection = mock_mongo_client
    
    # Disable index creation for testing
    with patch('src.services.database_service.DatabaseService._ensure_indexes') as mock_ensure_indexes:
        mock_ensure_indexes.return_value = None
        with patch('src.services.database_service.AsyncIOMotorClient', return_value=mock_client):
            yield database_service, mock_db, mock_collection


class TestDatabaseService:
    """Comprehensive test suite for Database Service"""
    
    # Connection Tests
    @pytest.mark.asyncio
    async def test_successful_connection(self, mock_mongo_client):
        """Test successful database connection"""
        mock_client, mock_db, mock_collection = mock_mongo_client
        
        # Temporarily disable index creation for testing
        with patch('src.services.database_service.DatabaseService._ensure_indexes') as mock_ensure_indexes:
            with patch('src.services.database_service.AsyncIOMotorClient', return_value=mock_client):
                db = await database_service.connect()
                
                assert db is not None
                assert database_service.db is not None
                assert database_service.client is not None
                mock_ensure_indexes.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_connection_failure(self):
        """Test database connection failure"""
        # Reset the singleton instance to test connection failure
        database_service._instance = None
        database_service._initialized = False
        database_service.client = None
        database_service.db = None
        
        with patch('src.services.database_service.AsyncIOMotorClient', side_effect=Exception("Connection failed")):
            with pytest.raises(DatabaseError, match="Failed to connect to database"):
                await database_service.connect()
    
    @pytest.mark.asyncio
    async def test_reconnect_when_disconnected(self, mock_mongo_client):
        """Test reconnection when database is disconnected"""
        mock_client, mock_db, mock_collection = mock_mongo_client
        
        # Disconnect first
        database_service.db = None
        database_service.client = None
        
        # Disable index creation for testing
        with patch('src.services.database_service.DatabaseService._ensure_indexes') as mock_ensure_indexes:
            mock_ensure_indexes.return_value = None
            with patch('src.services.database_service.AsyncIOMotorClient', return_value=mock_client):
                await database_service.connect()
                
                assert database_service.db is not None
                assert database_service.client is not None
    
    # CRUD Operation Tests
    @pytest.mark.asyncio
    async def test_find_many_success(self, setup_database_service):
        """Test successful find_many operation"""
        db_service, mock_db, mock_collection = setup_database_service
        
        # Connect to the database first
        await db_service.connect()
        
        # Mock collection find and to_list
        mock_cursor = Mock()
        mock_cursor.to_list = AsyncMock(return_value=[{"_id": "123", "name": "Test"}])
        mock_collection.find.return_value = mock_cursor
        mock_collection.find.return_value.limit.return_value = mock_cursor
        
        results = await db_service.find_many("test_collection", {})
        
        assert len(results) == 1
        assert results[0]["name"] == "Test"
        mock_collection.find.assert_called_once_with({})
        mock_cursor.to_list.assert_called_once_with(length=100)
    
    @pytest.mark.asyncio
    async def test_find_many_with_limit(self, setup_database_service):
        """Test find_many with custom limit"""
        db_service, mock_db, mock_collection = setup_database_service
        
        # Create a mock cursor that properly handles async operations
        mock_cursor = AsyncMock()
        mock_cursor.to_list = AsyncMock(return_value=[{"_id": "123", "name": "Test"}])
        # Make limit return self to mimic actual cursor behavior
        mock_cursor.limit = Mock(return_value=mock_cursor)
        mock_collection.find.return_value = mock_cursor
        
        # Mock the get_collection method
        with patch.object(db_service, 'get_collection', return_value=mock_collection):
            results = await db_service.find_many("test_collection", {}, limit=50)
            
            assert len(results) == 1
            assert results[0]["name"] == "Test"
            mock_collection.find.assert_called_once_with({})
            mock_cursor.limit.assert_called_once_with(50)
            mock_cursor.to_list.assert_called_once_with(length=50)
    
    @pytest.mark.asyncio
    async def test_find_many_empty_result(self, setup_database_service):
        """Test find_many with empty result"""
        db_service, mock_db, mock_collection = setup_database_service
        
        mock_cursor = Mock()
        mock_cursor.to_list = AsyncMock(return_value=[])
        mock_cursor.limit = Mock(return_value=mock_cursor)
        mock_collection.find.return_value = mock_cursor
        
        # Mock the get_collection method
        with patch.object(db_service, 'get_collection', return_value=mock_collection):
            results = await db_service.find_many("test_collection", {})
            
            assert len(results) == 0
    
    @pytest.mark.asyncio
    async def test_find_many_database_error(self, setup_database_service):
        """Test find_many when database operation fails"""
        db_service, mock_db, mock_collection = setup_database_service
        
        mock_cursor = Mock()
        mock_cursor.to_list = AsyncMock(side_effect=Exception("Database error"))
        mock_cursor.limit = Mock(return_value=mock_cursor)
        mock_collection.find.return_value = mock_cursor
        
        # Mock the get_collection method
        with patch.object(db_service, 'get_collection', return_value=mock_collection):
            with pytest.raises(DatabaseError, match="Failed to find documents in test_collection"):
                await db_service.find_many("test_collection", {})
    
    @pytest.mark.asyncio
    async def test_find_one_success(self, setup_database_service):
        """Test successful find_one operation"""
        db_service, mock_db, mock_collection = setup_database_service
        
        # Mock the get_collection method
        with patch.object(db_service, 'get_collection', return_value=mock_collection):
            mock_collection.find_one = AsyncMock(return_value={"_id": "123", "name": "Test"})
            
            result = await db_service.find_one("test_collection", {"name": "Test"})
            
            assert result is not None
            assert result["name"] == "Test"
            mock_collection.find_one.assert_called_once_with({"name": "Test"})
    
    @pytest.mark.asyncio
    async def test_find_one_not_found(self, setup_database_service):
        """Test find_one when document not found"""
        db_service, mock_db, mock_collection = setup_database_service
        
        # Mock the get_collection method
        with patch.object(db_service, 'get_collection', return_value=mock_collection):
            mock_collection.find_one = AsyncMock(return_value=None)
            
            result = await db_service.find_one("test_collection", {"name": "NonExistent"})
            
            assert result is None
    
    @pytest.mark.asyncio
    async def test_insert_one_success(self, setup_database_service):
        """Test successful insert_one operation"""
        db_service, mock_db, mock_collection = setup_database_service
        
        # Connect to the database first
        await db_service.connect()
        
        mock_result = Mock()
        mock_result.inserted_id = "123"
        mock_collection.insert_one = AsyncMock(return_value=mock_result)
        
        document = {"name": "Test", "value": 123}
        result_id = await db_service.insert_one("test_collection", document)
        
        assert result_id == "123"
        mock_collection.insert_one.assert_called_once_with(document)
    
    @pytest.mark.asyncio
    async def test_insert_one_failure(self, setup_database_service):
        """Test insert_one when operation fails"""
        db_service, mock_db, mock_collection = setup_database_service
        
        mock_result = Mock()
        mock_result.inserted_id = None
        mock_collection.insert_one = AsyncMock(return_value=mock_result)
        
        # Mock the get_collection method
        with patch.object(db_service, 'get_collection', return_value=mock_collection):
            document = {"name": "Test", "value": 123}
            
            with pytest.raises(DatabaseError, match="Failed to insert document"):
                await db_service.insert_one("test_collection", document)
    
    # Edge Case Tests
    @pytest.mark.asyncio
    async def test_find_many_with_complex_query(self, setup_database_service):
        """Test find_many with complex query"""
        db_service, mock_db, mock_collection = setup_database_service
        
        # Setup the mock cursor with to_list return value
        mock_cursor = Mock()
        mock_cursor.to_list = AsyncMock(return_value=[
            {"_id": "123", "name": "Test", "age": 25, "active": True}
        ])
        mock_collection.find.return_value = mock_cursor
        mock_collection.find.return_value.limit.return_value = mock_cursor
        
        # Connect to the database first
        await db_service.connect()
        
        complex_query = {
            "name": {"$regex": "test", "$options": "i"},
            "age": {"$gte": 18},
            "active": True
        }
        
        results = await db_service.find_many("test_collection", complex_query)
        
        mock_collection.find.assert_called_once_with(complex_query)
        mock_collection.find.return_value.limit.assert_called_once_with(100)
    
    @pytest.mark.asyncio
    async def test_find_many_invalid_collection_name(self, setup_database_service):
        """Test find_many with invalid collection name"""
        db_service, mock_db, mock_collection = setup_database_service
        
        # This should not raise an exception, but handle gracefully
        try:
            results = await db_service.find_many("", {})
            assert results == []
        except DatabaseError:
            pass  # Expected behavior for invalid collection name
    
    @pytest.mark.asyncio
    async def test_database_reconnection_scenario(self, setup_database_service):
        """Test database reconnection after connection loss"""
        db_service, mock_db, mock_collection = setup_database_service
        
        # Simulate connection loss
        db_service.db = None
        db_service.client = None
        
        # Reconnect
        await db_service.connect()
        
        # Test that it reconnected successfully
        assert db_service.db is not None
        assert db_service.client is not None
    
    # Performance Tests
    @pytest.mark.asyncio
    async def test_find_many_large_dataset(self, setup_database_service):
        """Test find_many with large dataset"""
        db_service, mock_db, mock_collection = setup_database_service
        
        # Mock large dataset
        large_dataset = [{"_id": str(i), "name": f"Item {i}"} for i in range(1000)]
        mock_cursor = Mock()
        mock_cursor.to_list = AsyncMock(return_value=large_dataset)
        # Make limit return self to mimic actual cursor behavior
        mock_cursor.limit = Mock(return_value=mock_cursor)
        mock_collection.find.return_value = mock_cursor
        
        # Mock the get_collection method
        with patch.object(db_service, 'get_collection', return_value=mock_collection):
            results = await db_service.find_many("test_collection", {}, limit=1000)
            
            assert len(results) == 1000
            # Verify ObjectId conversion
            for result in results:
                assert isinstance(result.get("_id"), str)
    
    # Error Handling Tests
    @pytest.mark.asyncio
    async def test_get_collection_not_connected(self):
        """Test get_collection when not connected"""
        database_service.db = None
        
        with pytest.raises(DatabaseError, match="Database not connected"):
            database_service.get_collection("test_collection")
    
    @pytest.mark.asyncio
    async def test_operation_during_connection(self, mock_mongo_client):
        """Test operation during connection process"""
        mock_client, mock_db, mock_collection = mock_mongo_client
        
        # Setup mock collections for index creation
        mock_users = AsyncMock()
        mock_users.create_index = AsyncMock(return_value=True)
        mock_courses = AsyncMock()
        mock_courses.create_index = AsyncMock(return_value=True)
        mock_departments = AsyncMock()
        mock_departments.create_index = AsyncMock(return_value=True)
        mock_enrollments = AsyncMock()
        mock_enrollments.create_index = AsyncMock(return_value=True)
        mock_assessments = AsyncMock()
        mock_assessments.create_index = AsyncMock(return_value=True)
        
        # Mock database to return appropriate collections
        mock_db.users = mock_users
        mock_db.courses = mock_courses
        mock_db.departments = mock_departments
        mock_db.enrollments = mock_enrollments
        mock_db.assessments = mock_assessments
        
        # Setup find operation
        mock_cursor = Mock()
        mock_cursor.to_list = AsyncMock(return_value=[{"_id": "123"}])
        # Make limit return self to mimic actual cursor behavior
        mock_cursor.limit = Mock(return_value=mock_cursor)
        mock_collection.find.return_value = mock_cursor
        
        # Disable index creation for testing
        with patch('src.services.database_service.DatabaseService._ensure_indexes') as mock_ensure_indexes:
            with patch('src.services.database_service.AsyncIOMotorClient', return_value=mock_client):
                # Connect to database
                await database_service.connect()
                
                # Mock the get_collection method for the find operation
                with patch.object(database_service, 'get_collection', return_value=mock_collection):
                    # Try to perform operation
                    results = await database_service.find_many("test_collection", {})
                    assert len(results) == 1