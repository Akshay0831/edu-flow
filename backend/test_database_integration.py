#!/usr/bin/env python3
"""
Simple integration test for database manager
"""

import asyncio
import tempfile
import os
from unittest.mock import Mock, patch

from src.services.database_manager import EnhancedDatabaseManager
from src.core.database_abstraction import DatabaseType, DatabaseConfig


async def test_database_manager():
    """Test basic database manager functionality"""
    print("Testing database manager...")
    
    # Create database manager instance
    manager = EnhancedDatabaseManager()
    
    # Mock database configuration
    with patch.object(manager, '_get_database_config') as mock_config:
        mock_config.return_value = DatabaseConfig(
            db_type=DatabaseType.SQLITE,
            host="localhost",
            port=0,
            database="test.db",
            username="",
            password="",
            max_connections=10,
            min_connections=1
        )
        
        # Mock pool initialization
        with patch('src.core.database_abstraction.DatabaseConnectionPool') as mock_pool_class:
            mock_pool_instance = Mock()
            mock_pool_instance.initialize.return_value = None
            mock_pool_class.return_value = mock_pool_instance
            
            manager.pool = mock_pool_instance
            
            # Mock database instance
            with patch('src.core.database_abstraction.SQLiteDatabase') as mock_db:
                mock_db_instance = Mock()
                mock_db_instance.health_check.return_value = True
                mock_db_instance.execute_query.return_value = [{"test": "data"}]
                mock_db_instance.execute_update.return_value = 1
                mock_db.return_value = mock_db_instance
                
                # Mock migration manager
                with patch.object(manager, '_run_migrations') as mock_migrations:
                    mock_migrations.return_value = None
                    
                    # Mock health check loop
                    with patch.object(manager, '_health_check_loop') as mock_health:
                        mock_health.return_value = asyncio.sleep(0.1)
                        
                        try:
                            # Initialize database manager
                            await manager.initialize()
                            print("✓ Database manager initialized successfully")
                            
                            # Test health check
                            is_healthy = await manager.health_check()
                            print(f"✓ Health check: {is_healthy}")
                            
                            # Test query execution
                            result = await manager.execute_query("SELECT 1")
                            print(f"✓ Query executed successfully: {result}")
                            
                            # Test update execution
                            update_result = await manager.execute_update("INSERT INTO test VALUES (?)", {"param": "value"})
                            print(f"✓ Update executed successfully: {update_result}")
                            
                            # Test getting stats
                            stats = await manager.get_stats()
                            print(f"✓ Stats retrieved: {stats.get('database_type', 'unknown')}")
                            
                            # Test close
                            await manager.close()
                            print("✓ Database manager closed successfully")
                            
                            print("\n🎉 All tests passed!")
                            
                        except Exception as e:
                            print(f"❌ Test failed: {e}")
                            raise


if __name__ == "__main__":
    asyncio.run(test_database_manager())