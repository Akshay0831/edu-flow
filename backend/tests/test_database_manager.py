"""
Comprehensive Database Manager Tests

Tests for the enhanced database management system:
- Database connection and pooling
- Migration management
- Health monitoring
- Backup functionality
- Performance statistics
- Error handling and recovery

Author: Edu-Flow Team
"""

import pytest
import asyncio
import json
import tempfile
import os
import time
from datetime import datetime, timedelta
from unittest.mock import Mock, patch, AsyncMock

from src.services.database_manager import (
    EnhancedDatabaseManager, DatabaseStats, db_manager
)
from src.core.database_abstraction import DatabaseType, DatabaseConfig
from src.core.database_migrations import MigrationManager, MigrationStatus
from src.core.exceptions import DatabaseError, MigrationError, ConfigurationError
from src.core.logging import get_logger

logger = get_logger(__name__)


@pytest.fixture(autouse=True)
def reset_settings():
    """Keep configuration tests isolated from one another."""
    from src.config.settings import settings

    settings.database_url = "sqlite+aiosqlite:///edu_flow.db"
    settings.mongodb_url = "mongodb://localhost:27017/edu_flow"
    yield
    settings.database_url = "sqlite+aiosqlite:///edu_flow.db"
    settings.mongodb_url = "mongodb://localhost:27017/edu_flow"


class TestDatabaseConfig:
    """Test database configuration"""
    
    def test_sqlite_config(self):
        """Test SQLite configuration"""
        from src.config.settings import settings
        
        settings.database_url = "sqlite+aiosqlite:///test.db"
        config = db_manager._get_database_config()
        
        assert config.db_type == DatabaseType.SQLITE
        assert config.host == "localhost"
        assert config.port == 0
        assert "test.db" in config.database
    
    def test_postgresql_config(self):
        """Test PostgreSQL configuration"""
        from src.config.settings import settings
        
        settings.database_url = "postgresql+asyncpg://user:pass@localhost:5432/testdb"
        config = db_manager._get_database_config()
        
        assert config.db_type == DatabaseType.POSTGRESQL
        assert config.host == "localhost"
        assert config.port == 5432
        assert config.database == "testdb"
        assert config.username == "user"
        assert config.password == "pass"
    
    def test_mongodb_config(self):
        """Test MongoDB configuration"""
        from src.config.settings import settings
        
        settings.mongodb_url = "mongodb://user:pass@localhost:27017/testdb"
        config = db_manager._get_database_config()
        
        assert config.db_type == DatabaseType.MONGODB
        assert config.host == "localhost"
        assert config.port == 27017
        assert config.database == "testdb"
        assert config.username == "user"
        assert config.password == "pass"
    
    def test_invalid_config(self):
        """Test invalid database configuration"""
        from src.config.settings import settings
        
        settings.database_url = "invalid://localhost/testdb"
        
        with pytest.raises(ConfigurationError):
            db_manager._get_database_config()


class TestDatabaseStats:
    """Test database statistics"""
    
    def test_stats_initialization(self):
        """Test statistics initialization"""
        stats = DatabaseStats()
        
        assert stats.total_connections == 0
        assert stats.active_connections == 0
        assert stats.idle_connections == 0
        assert stats.query_count == 0
        assert stats.error_count == 0
        assert stats.avg_query_time == 0.0
        assert stats.last_health_check is None
        assert stats.is_healthy == False
    
    def test_stats_update(self):
        """Test statistics update"""
        stats = DatabaseStats()
        
        stats.active_connections = 5
        stats.query_count = 100
        stats.error_count = 2
        stats.avg_query_time = 0.5
        stats.is_healthy = True
        
        assert stats.active_connections == 5
        assert stats.query_count == 100
        assert stats.error_count == 2
        assert stats.avg_query_time == 0.5
        assert stats.is_healthy == True


class TestEnhancedDatabaseManager:
    """Test enhanced database manager"""
    
    def setup_method(self):
        """Setup test environment"""
        # Reset database manager
        EnhancedDatabaseManager()
        db_manager._initialized = True
        db_manager.database = Mock()
        db_manager.pool = Mock()
        db_manager.migration_manager = None
        db_manager.stats = DatabaseStats()
        db_manager._query_times = []
    
    def teardown_method(self):
        """Cleanup test environment"""
        # Reset settings
        from src.config.settings import settings
        settings.database_url = "sqlite+aiosqlite:///edu_flow.db"
        settings.mongodb_url = "mongodb://localhost:27017/edu_flow"
        
        # Close database manager if initialized
        if db_manager._initialized:
            asyncio.run(db_manager.close())
    
    @pytest.mark.asyncio
    async def test_database_manager_singleton(self):
        """Test database manager singleton pattern"""
        manager1 = EnhancedDatabaseManager()
        manager2 = EnhancedDatabaseManager()
        
        assert manager1 is manager2
    
    @pytest.mark.asyncio
    async def test_database_manager_initialization(self):
        """Test database manager initialization"""
        manager = EnhancedDatabaseManager()
        manager._initialized = False
        
        # Mock the initialization to avoid actual database connection
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
            
            with patch('src.core.database_abstraction.DatabaseConnectionPool') as mock_pool_class:
                mock_pool_instance = Mock()
                mock_pool_instance.initialize.return_value = None
                mock_pool_class.return_value = mock_pool_instance
                manager.pool = mock_pool_instance
                
                with patch.object(manager, '_run_migrations') as mock_migrations, \
                    patch.object(MigrationManager, 'initialize', new_callable=AsyncMock):
                    mock_migrations.return_value = None
                    
                    with patch.object(manager, '_health_check_loop') as mock_health:
                        async def fake_health_loop():
                            return None
                        mock_health.side_effect = fake_health_loop
                        
                        await manager.initialize()
                        
                        assert manager._initialized == True
                        assert manager.database is not None
                        assert manager.pool is not None
                        assert manager.migration_manager is not None
    
    @pytest.mark.asyncio
    async def test_get_connection(self):
        """Test getting database connection"""
        manager = EnhancedDatabaseManager()
        
        # Mock successful connection
        with patch.object(manager, 'initialize') as mock_init:
            mock_init.return_value = None
            
            with patch.object(manager.pool, 'get_connection') as mock_get_conn:
                mock_get_conn.return_value = Mock()
                
                async with manager.get_connection() as conn:
                    assert conn is not None
                
                # Verify statistics
                assert manager.stats.active_connections == 0
                assert manager.stats.total_connections > 0
    
    @pytest.mark.asyncio
    async def test_connection_error_handling(self):
        """Test connection error handling"""
        manager = EnhancedDatabaseManager()
        
        with patch.object(manager, 'initialize') as mock_init:
            mock_init.return_value = None
            
            with patch.object(manager.pool, 'get_connection') as mock_get_conn:
                mock_get_conn.side_effect = Exception("Connection failed")
                
                with pytest.raises(DatabaseError):
                    async with manager.get_connection() as conn:
                        pass
                
                assert manager.stats.error_count > 0
    
    @pytest.mark.asyncio
    async def test_transaction_management(self):
        """Test transaction management"""
        manager = EnhancedDatabaseManager()
        
        # Mock successful transaction
        with patch.object(manager, 'initialize') as mock_init:
            mock_init.return_value = None
            
            with patch.object(manager.database, 'begin_transaction') as mock_begin:
                mock_begin.return_value = None
                
                with patch.object(manager.database, 'commit_transaction') as mock_commit:
                    mock_commit.return_value = None
                    
                    async with manager.transaction() as db:
                        assert db is not None
                    
                    mock_commit.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_transaction_rollback(self):
        """Test transaction rollback on error"""
        manager = EnhancedDatabaseManager()
        
        with patch.object(manager, 'initialize') as mock_init:
            mock_init.return_value = None
            
            with patch.object(manager.database, 'begin_transaction') as mock_begin:
                mock_begin.return_value = None
                
                with patch.object(manager.database, 'rollback_transaction') as mock_rollback:
                    mock_rollback.return_value = None
                    
                    with pytest.raises(DatabaseError):
                        async with manager.transaction() as db:
                            raise DatabaseError("Test error")
                    
                    mock_rollback.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_execute_query(self):
        """Test query execution"""
        manager = EnhancedDatabaseManager()
        
        with patch.object(manager, 'initialize') as mock_init:
            mock_init.return_value = None
            
            with patch.object(manager.database, 'execute_query') as mock_query:
                mock_query.return_value = [{"id": 1, "name": "test"}]
                
                result = await manager.execute_query("SELECT * FROM test", {"param": "value"})
                
                assert result == [{"id": 1, "name": "test"}]
                assert manager.stats.query_count > 0
                assert manager.stats.avg_query_time > 0
    
    @pytest.mark.asyncio
    async def test_execute_update(self):
        """Test update execution"""
        manager = EnhancedDatabaseManager()
        
        with patch.object(manager, 'initialize') as mock_init:
            mock_init.return_value = None
            
            with patch.object(manager.database, 'execute_update') as mock_update:
                mock_update.return_value = 1
                
                result = await manager.execute_update("INSERT INTO test VALUES (?)", {"param": "value"})
                
                assert result == 1
                assert manager.stats.query_count > 0
    
    @pytest.mark.asyncio
    async def test_health_check(self):
        """Test health check functionality"""
        manager = EnhancedDatabaseManager()
        
        with patch.object(manager, 'initialize') as mock_init:
            mock_init.return_value = None
            
            with patch.object(manager.database, 'health_check') as mock_health:
                mock_health.return_value = True
                
                is_healthy = await manager.health_check()
                
                assert is_healthy == True
                assert manager.stats.is_healthy == True
    
    @pytest.mark.asyncio
    async def test_health_check_failure(self):
        """Test health check failure"""
        manager = EnhancedDatabaseManager()
        
        with patch.object(manager, 'initialize') as mock_init:
            mock_init.return_value = None
            
            with patch.object(manager.database, 'health_check') as mock_health:
                mock_health.return_value = False
                
                is_healthy = await manager.health_check()
                
                assert is_healthy == False
                assert manager.stats.is_healthy == False
    
    @pytest.mark.asyncio
    async def test_get_stats(self):
        """Test getting database statistics"""
        manager = EnhancedDatabaseManager()
        
        with patch.object(manager, 'initialize') as mock_init:
            mock_init.return_value = None
            
            with patch.object(manager, 'health_check') as mock_health:
                mock_health.return_value = True
                
                stats = await manager.get_stats()
                
                assert "database_type" in stats
                assert "total_connections" in stats
                assert "query_count" in stats
                assert "is_healthy" in stats
                assert stats["is_healthy"] == True
    
    @pytest.mark.asyncio
    async def test_migration_management(self):
        """Test migration management"""
        manager = EnhancedDatabaseManager()
        
        with patch.object(manager, 'initialize') as mock_init:
            mock_init.return_value = None
            
            with patch.object(manager, 'run_migrations') as mock_migrations:
                mock_migrations.return_value = {"status": "success", "migrations_applied": 2}
                
                result = await manager.run_migrations()
                
                assert result["status"] == "success"
                assert result["migrations_applied"] == 2
    
    @pytest.mark.asyncio
    async def test_backup_functionality(self):
        """Test database backup functionality"""
        manager = EnhancedDatabaseManager()
        
        with patch.object(manager, 'initialize') as mock_init:
            mock_init.return_value = None
            
            with patch.object(manager, '_backup_mongodb') as mock_backup:
                mock_backup.return_value = {
                    "backup_path": "test_backup.json",
                    "collections_count": 5,
                    "documents_count": 100
                }
                
                with patch.object(manager, '_backup_sql') as mock_sql_backup:
                    mock_sql_backup.return_value = {
                        "backup_path": "test_backup.sql",
                        "tables_count": 10,
                        "total_rows": 500
                    }
                    
                    backup_info = await manager.backup_database()
                    
                    assert "timestamp" in backup_info
                    assert "backup_path" in backup_info
                    assert backup_info["status"] == "completed"
    
    @pytest.mark.asyncio
    async def test_database_close(self):
        """Test database close functionality"""
        manager = EnhancedDatabaseManager()
        
        with patch.object(manager, 'initialize') as mock_init:
            mock_init.return_value = None
            
            with patch.object(manager.pool, 'close') as mock_close:
                mock_close.return_value = None
                
                await manager.close()
                
                assert manager.database is None
                assert manager.pool is None
                assert manager.migration_manager is None


class TestDatabaseManagerIntegration:
    """Integration tests for database manager"""

    def setup_method(self):
        """Provide patchable manager dependencies for integration tests."""
        EnhancedDatabaseManager()
        db_manager._initialized = True
        db_manager.database = Mock()
        db_manager.pool = Mock()
        db_manager.migration_manager = None
        db_manager.stats = DatabaseStats()
        db_manager._query_times = []
    
    @pytest.mark.asyncio
    async def test_full_initialization_flow(self):
        """Test complete initialization flow"""
        manager = EnhancedDatabaseManager()
        manager._initialized = False
        
        # Mock all dependencies
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
            
            with patch.object(manager.pool, 'initialize') as mock_init:
                mock_init.return_value = None
                
                with patch.object(manager, '_run_migrations') as mock_migrations, \
                     patch.object(MigrationManager, 'initialize', new_callable=AsyncMock):
                    mock_migrations.return_value = {"status": "success"}
                    
                    with patch.object(manager, '_health_check_loop') as mock_health:
                        async def fake_health_loop():
                            return None
                        mock_health.side_effect = fake_health_loop
                        
                        # Initialize
                        await manager.initialize()
                        
                        # Test connection
                        async with manager.get_connection() as conn:
                            assert conn is not None
                        
                        # Test query
                        with patch.object(manager.database, 'execute_query') as mock_query:
                            mock_query.return_value = []
                            result = await manager.execute_query("SELECT 1")
                            assert result == []
                        
                        # Test health check
                        with patch.object(manager.database, 'health_check') as mock_health:
                            mock_health.return_value = True
                            is_healthy = await manager.health_check()
                            assert is_healthy == True
                        
                        # Get stats
                        stats = await manager.get_stats()
                        assert "database_type" in stats
                        
                        # Close
                        await manager.close()
                        
                        # Verify everything is cleaned up
                        assert manager.database is None
                        assert manager.pool is None
                        assert manager.migration_manager is None
    
    @pytest.mark.asyncio
    async def test_error_recovery(self):
        """Test error recovery"""
        manager = EnhancedDatabaseManager()
        
        # Mock configuration
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
            
            # Test initialization failure
            with patch.object(manager.pool, 'initialize') as mock_init:
                mock_init.side_effect = Exception("Initialization failed")
                
                with pytest.raises(DatabaseError):
                    await manager.initialize()
                
                # Verify the manager is not marked as initialized
                assert manager._initialized == False
                assert manager.database is None
                assert manager.pool is None
    
    @pytest.mark.asyncio
    async def test_concurrent_operations(self):
        """Test concurrent database operations"""
        manager = EnhancedDatabaseManager()
        
        # Mock setup
        with patch.object(manager, 'initialize') as mock_init:
            mock_init.return_value = None
            
            with patch.object(manager.pool, 'get_connection') as mock_get_conn:
                mock_get_conn.return_value = Mock()
                
                with patch.object(manager.database, 'execute_query') as mock_query:
                    mock_query.return_value = [{"id": i} for i in range(10)]
                    
                    # Run concurrent queries
                    tasks = []
                    for i in range(5):
                        task = asyncio.create_task(
                            manager.execute_query(f"SELECT * FROM table_{i}")
                        )
                        tasks.append(task)
                    
                    results = await asyncio.gather(*tasks)
                    
                    # Verify all queries completed
                    assert len(results) == 5
                    assert all(len(result) == 10 for result in results)
                    
                    # Verify statistics
                    assert manager.stats.query_count == 5


class TestDatabaseManagerPerformance:
    """Performance tests for database manager"""

    def setup_method(self):
        """Provide patchable manager dependencies for performance tests."""
        EnhancedDatabaseManager()
        db_manager._initialized = True
        db_manager.database = Mock()
        db_manager.pool = Mock()
        db_manager.migration_manager = None
        db_manager.stats = DatabaseStats()
        db_manager._query_times = []
    
    @pytest.mark.asyncio
    async def test_query_performance_tracking(self):
        """Test query performance tracking"""
        manager = EnhancedDatabaseManager()
        
        with patch.object(manager, 'initialize') as mock_init:
            mock_init.return_value = None
            
            with patch.object(manager.database, 'execute_query') as mock_query:
                mock_query.return_value = []
                
                # Execute multiple queries
                for i in range(10):
                    await manager.execute_query(f"SELECT * FROM table_{i}")
                
                # Check statistics
                assert manager.stats.query_count == 10
                assert manager.stats.avg_query_time > 0
                assert len(manager._query_times) == 10
    
    @pytest.mark.asyncio
    async def test_query_history_limit(self):
        """Test query history size limit"""
        manager = EnhancedDatabaseManager()
        manager._max_query_history = 5  # Set small limit for testing
        
        with patch.object(manager, 'initialize') as mock_init:
            mock_init.return_value = None
            
            with patch.object(manager.database, 'execute_query') as mock_query:
                mock_query.return_value = []
                
                # Execute more queries than the limit
                for i in range(10):
                    await manager.execute_query(f"SELECT * FROM table_{i}")
                
                # Verify history is limited
                assert len(manager._query_times) == 5
                assert manager.stats.avg_query_time > 0
    
    @pytest.mark.asyncio
    async def test_performance_under_load(self):
        """Test performance under high load"""
        manager = EnhancedDatabaseManager()
        
        with patch.object(manager, 'initialize') as mock_init:
            mock_init.return_value = None
            
            with patch.object(manager.pool, 'get_connection') as mock_get_conn:
                mock_get_conn.return_value = Mock()
                
                with patch.object(manager.database, 'execute_query') as mock_query:
                    mock_query.return_value = [{"id": i} for i in range(100)]
                    
                    # Execute many concurrent queries
                    tasks = []
                    for i in range(50):
                        task = asyncio.create_task(
                            manager.execute_query(f"SELECT * FROM table_{i}")
                        )
                        tasks.append(task)
                    
                    start_time = time.time()
                    results = await asyncio.gather(*tasks)
                    end_time = time.time()
                    
                    # Verify all queries completed
                    assert len(results) == 50
                    assert all(isinstance(result, list) for result in results)
                    
                    # Check performance
                    elapsed_time = end_time - start_time
                    logger.info(f"Executed 50 queries in {elapsed_time:.3f}s")
                    assert elapsed_time < 5.0  # Should complete within 5 seconds


# Fixtures for testing
@pytest.fixture
def mock_database_manager():
    """Create a mock database manager for testing"""
    manager = EnhancedDatabaseManager()
    manager._initialized = True
    manager.database = Mock()
    manager.pool = Mock()
    manager.migration_manager = Mock()
    return manager


@pytest.fixture
def mock_database_config():
    """Create a mock database configuration"""
    return DatabaseConfig(
        db_type=DatabaseType.SQLITE,
        host="localhost",
        port=0,
        database="test.db",
        username="",
        password="",
        max_connections=10,
        min_connections=1
    )