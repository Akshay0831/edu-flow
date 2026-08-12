from src.core.exceptions import ValidationError, AuthenticationError, NotFoundError
"""
Database test script for Edu-Flow Backend

This script tests database connection and operations:
- Database health check
- Collection access
- Database initialization
- CRUD operations

Author: Edu-Flow Team
"""

import asyncio
import pytest_asyncio
import sys
import os
import logging

# Add the project root to Python path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from src.services.database_service import database_service, initialize_database
from src.core.exceptions import DatabaseError

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

@pytest_asyncio.fixture
async def test_database_connection():
    """Test database connection and operations"""
    print('🔍 Testing Database Connection and Operations')
    print('=' * 50)
    
    try:
        # Test database service
        print('✅ Database service imported successfully')
        
        # Test database health check
        health = await database_service.health_check()
        print(f'✅ Database health check: {health["status"]}')
        
        if health['status'] == 'healthy':
            print('✅ MongoDB connection working')
            
            # Test collection access
            collections = health.get('collections', {})
            print(f'📊 Collections status:')
            for collection, count in collections.items():
                print(f'   - {collection}: {count} documents')
            
            # Test database initialization
            success = await initialize_database()
            if success:
                print('✅ Database initialization completed')
            else:
                print('⚠️ Database initialization failed')
            
            # Test departments
            departments = await database_service.find_many('departments', {})
            print(f'📚 Departments found: {len(departments)}')
            for dept in departments:
                print(f'   - {dept.get("name", "Unknown")} ({dept.get("code", "N/A")})')
            
        else:
            print(f'❌ Database health check failed: {health.get("error", "Unknown error")}')
        
    except Exception as e:
        logger.error(f'Database test failed: {e}')
        import traceback
        traceback.print_exc()
    
    print('=' * 50)
    print('🔍 Database test complete')

def main():
    """Main function"""
    try:
        # Run the async test
        asyncio.run(test_database_connection())
    except KeyboardInterrupt:
        print('\n⚠️ Test interrupted by user')
    except Exception as e:
        logger.error(f'Test failed: {e}')

if __name__ == "__main__":
    main()