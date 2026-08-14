"""
Basic Performance Tests

This module provides simple performance tests that work with basic operations.
It tests basic mock performance without complex dataclass structures.

Author: Edu-Flow Team
"""

import pytest
import time
import asyncio

class SimpleMockDB:
    """Simple mock database for performance testing."""
    
    def __init__(self):
        self.data = {}
        self.next_id = 1
    
    async def create(self, collection, data):
        """Create a new item in the collection."""
        if collection not in self.data:
            self.data[collection] = {}
        
        item_id = str(self.next_id)
        self.next_id += 1
        
        item = {
            'id': item_id,
            'created_at': time.time(),
            **data
        }
        
        self.data[collection][item_id] = item
        return item
    
    async def get(self, collection, item_id):
        """Get an item by ID."""
        if collection not in self.data:
            return None
        return self.data[collection].get(item_id)
    
    async def get_all(self, collection, skip=0, limit=100):
        """Get all items in a collection."""
        if collection not in self.data:
            return []
        items = list(self.data[collection].values())
        return items[skip:skip + limit]
    
    async def update(self, collection, item_id, data):
        """Update an item."""
        if collection not in self.data or item_id not in self.data[collection]:
            return None
        
        item = self.data[collection][item_id]
        item.update(data)
        item['updated_at'] = time.time()
        return item
    
    async def delete(self, collection, item_id):
        """Delete an item."""
        if collection not in self.data:
            return False
        
        if item_id in self.data[collection]:
            del self.data[collection][item_id]
            return True
        return False
    
    async def clear(self):
        """Clear all data."""
        self.data.clear()
        self.next_id = 1


class TestBasicPerformance:
    """Basic performance tests."""
    
    @pytest.fixture
    def mock_db(self):
        """Create a simple mock database."""
        return SimpleMockDB()
    
    @pytest.mark.asyncio
    async def test_creation_performance(self, mock_db):
        """Test creation performance."""
        start_time = time.time()
        
        # Create 100 items
        for i in range(100):
            await mock_db.create('students', {
                'name': f'Student {i}',
                'email': f'student{i}@test.com',
                'age': 20 + (i % 5)
            })
        
        end_time = time.time()
        duration = end_time - start_time
        
        ops_per_second = 100 / duration
        print(f"Creation performance: {ops_per_second:.2f} ops/sec")
        assert ops_per_second > 50
    
    @pytest.mark.asyncio
    async def test_query_performance(self, mock_db):
        """Test query performance."""
        # Create test data first
        for i in range(50):
            await mock_db.create('students', {
                'name': f'Student {i}',
                'email': f'student{i}@test.com',
                'age': 20 + (i % 5)
            })
        
        # Test query performance
        start_time = time.time()
        
        # Query all students
        students = await mock_db.get_all('students')
        
        end_time = time.time()
        duration = end_time - start_time
        
        queries_per_second = 1 / duration
        print(f"Query performance: {queries_per_second:.2f} queries/sec")
        assert queries_per_second > 100
    
    @pytest.mark.asyncio
    async def test_update_performance(self, mock_db):
        """Test update performance."""
        # Create a test item
        item = await mock_db.create('students', {
            'name': 'Test Student',
            'email': 'test@test.com',
            'age': 20
        })
        item_id = item['id']
        
        # Test update performance
        start_time = time.time()
        
        # Update the item 10 times
        for i in range(10):
            await mock_db.update('students', item_id, {
                'name': f'Updated Student {i}',
                'email': f'updated{i}@test.com'
            })
        
        end_time = time.time()
        duration = end_time - start_time
        
        updates_per_second = 10 / duration
        print(f"Update performance: {updates_per_second:.2f} updates/sec")
        assert updates_per_second > 50
    
    @pytest.mark.asyncio
    async def test_concurrent_operations(self, mock_db):
        """Test concurrent operations performance."""
        async def create_items(start_idx, count):
            """Create multiple items."""
            for i in range(count):
                await mock_db.create('students', {
                    'name': f'Concurrent Student {start_idx + i}',
                    'email': f'concurrent{start_idx + i}@test.com',
                    'age': 20 + (i % 5)
                })
        
        async def query_items(count):
            """Query items multiple times."""
            for i in range(count):
                await mock_db.get_all('students')
        
        # Create concurrent tasks
        start_time = time.time()
        
        tasks = []
        # Create 5 tasks to create 20 items each
        for i in range(5):
            task = create_items(i * 20, 20)
            tasks.append(task)
        
        # Create 3 tasks to query items
        for i in range(3):
            task = query_items(10)
            tasks.append(task)
        
        # Run all tasks concurrently
        await asyncio.gather(*tasks)
        
        end_time = time.time()
        duration = end_time - start_time
        
        total_operations = 5 * 20 + 3 * 10  # 100 creations + 30 queries
        operations_per_second = total_operations / duration
        print(f"Concurrent operations performance: {operations_per_second:.2f} ops/sec")
        assert operations_per_second > 30
        
        # Clean up
        await mock_db.clear()
    
    @pytest.mark.asyncio
    async def test_bulk_operations(self, mock_db):
        """Test bulk operations performance."""
        start_time = time.time()
        
        # Create 200 items in bulk
        for i in range(200):
            if i % 2 == 0:
                await mock_db.create('students', {
                    'name': f'Student {i}',
                    'email': f'student{i}@test.com',
                    'age': 20 + (i % 5)
                })
            else:
                await mock_db.create('courses', {
                    'name': f'Course {i}',
                    'code': f'CS{i:03d}',
                    'credits': 3
                })
        
        end_time = time.time()
        duration = end_time - start_time
        
        operations_per_second = 200 / duration
        print(f"Bulk operations performance: {operations_per_second:.2f} ops/sec")
        assert operations_per_second > 20
        
        # Clean up
        await mock_db.clear()