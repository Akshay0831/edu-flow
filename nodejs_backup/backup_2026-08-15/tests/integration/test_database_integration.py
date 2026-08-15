"""
Database Integration Tests

Integration tests for database system components:
- Migration system integration with database manager
- Database connection pooling with migrations
- Health monitoring with database operations
- Backup system integration
- Real-world scenarios and edge cases

Author: Edu-Flow Team
"""

import pytest
import asyncio
import json
import tempfile
import os
from datetime import datetime, timedelta
from unittest.mock import Mock, patch, AsyncMock

from src.services.database_manager import EnhancedDatabaseManager
from src.core.database_abstraction import DatabaseType, DatabaseConfig
from src.core.database_migrations import MigrationManager, MigrationStatus
from src.core.exceptions import DatabaseError, MigrationError


class TestDatabaseMigrationIntegration:
    """Test migration system integration with database manager"""
    
    @pytest.mark.asyncio
    async def test_migration_initialization_flow(self):
        """Test complete migration initialization flow"""
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
            with patch.object(manager.pool, 'initialize') as mock_init:
                mock_init.return_value = None
                
                # Mock migration manager initialization
                with patch.object(manager, '_run_migrations') as mock_migrations:
                    mock_migrations.return_value = {"status": "success", "migrations_applied": 2}
                    
                    # Mock health check loop
                    with patch.object(manager, '_health_check_loop') as mock_health:
                        mock_health.return_value = asyncio.sleep(0.1)
                        
                        # Initialize database manager
                        await manager.initialize()
                        
                        # Verify migration manager was created
                        assert manager.migration_manager is not None
                        
                        # Verify migrations were run
                        mock_migrations.assert_called_once()
                        
                        # Test migration status retrieval
                        with patch.object(manager.migration_manager, 'get_migration_status') as mock_status:
                            mock_status.return_value = {
                                "latest_version": "002",
                                "current_version": "002",
                                "pending_migrations": 0,
                                "applied_migrations": 2
                            }
                            
                            status = await manager.get_migration_status()
                            assert status["pending_migrations"] == 0
                            assert status["applied_migrations"] == 2
    
    @pytest.mark.asyncio
    async def test_migration_with_connection_pooling(self):
        """Test migration execution with connection pooling"""
        manager = EnhancedDatabaseManager()
        
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
                
                # Mock connection pool behavior
                mock_conn1 = Mock()
                mock_conn2 = Mock()
                
                manager.pool.get_connection = AsyncMock()
                manager.pool.get_connection.side_effect = [mock_conn1, mock_conn2]
                
                with patch.object(manager, '_run_migrations') as mock_migrations:
                    mock_migrations.return_value = {"status": "success", "migrations_applied": 1}
                    
                    with patch.object(manager, '_health_check_loop') as mock_health:
                        mock_health.return_value = asyncio.sleep(0.1)
                        
                        await manager.initialize()
                        
                        # Verify connection pool was used during migrations
                        manager.pool.get_connection.assert_called()
                        
                        # Verify connections were returned
                        assert manager.pool.return_connection.call_count == 2
    
    @pytest.mark.asyncio
    async def test_migration_rollback_integration(self):
        """Test migration rollback integration"""
        manager = EnhancedDatabaseManager()
        
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
                
                with patch.object(manager, '_run_migrations') as mock_migrations:
                    mock_migrations.return_value = {"status": "success", "migrations_applied": 2}
                    
                    with patch.object(manager, '_health_check_loop') as mock_health:
                        mock_health.return_value = asyncio.sleep(0.1)
                        
                        await manager.initialize()
                        
                        # Test rollback functionality
                        with patch.object(manager.migration_manager, 'rollback') as mock_rollback:
                            mock_rollback.return_value = {
                                "status": "success",
                                "migrations_rolled_back": 1,
                                "target_version": "001"
                            }
                            
                            result = await manager.rollback_migrations("001")
                            
                            assert result["status"] == "success"
                            assert result["migrations_rolled_back"] == 1
                            mock_rollback.assert_called_once_with("001")
    
    @pytest.mark.asyncio
    async def test_migration_error_handling_integration(self):
        """Test migration error handling integration"""
        manager = EnhancedDatabaseManager()
        
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
                
                with patch.object(manager, '_run_migrations') as mock_migrations:
                    mock_migrations.return_value = {
                        "status": "failed",
                        "message": "Migration failed due to constraint violation",
                        "error": "ForeignKeyConstraintError"
                    }
                    
                    with patch.object(manager, '_health_check_loop') as mock_health:
                        mock_health.return_value = asyncio.sleep(0.1)
                        
                        await manager.initialize()
                        
                        # Test error handling
                        with patch.object(manager.migration_manager, 'get_migration_status') as mock_status:
                            mock_status.return_value = {
                                "latest_version": "000",
                                "current_version": "000",
                                "pending_migrations": 2,
                                "applied_migrations": 0,
                                "error_count": 1
                            }
                            
                            status = await manager.get_migration_status()
                            
                            assert status["pending_migrations"] == 2
                            assert status["applied_migrations"] == 0
                            assert status["error_count"] == 1


class TestDatabaseHealthMonitoringIntegration:
    """Test health monitoring integration with database operations"""
    
    @pytest.mark.asyncio
    async def test_health_check_during_operations(self):
        """Test health check during database operations"""
        manager = EnhancedDatabaseManager()
        
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
                
                with patch.object(manager, '_run_migrations') as mock_migrations:
                    mock_migrations.return_value = {"status": "success"}
                    
                    with patch.object(manager, '_health_check_loop') as mock_health:
                        mock_health.return_value = asyncio.sleep(0.1)
                        
                        await manager.initialize()
                        
                        # Mock successful health check
                        with patch.object(manager.database, 'health_check') as mock_health_check:
                            mock_health_check.return_value = True
                            
                            # Perform operations while health check runs
                            async with manager.get_connection() as conn:
                                pass
                            
                            await manager.execute_query("SELECT 1")
                            await manager.execute_update("INSERT INTO test VALUES (?)", {"param": "value"})
                            
                            # Verify health check was called
                            assert mock_health_check.call_count > 0
                            
                            # Verify statistics
                            assert manager.stats.query_count > 0
                            assert manager.stats.active_connections >= 0
    
    @pytest.mark.asyncio
    async def test_health_check_failure_impact(self):
        """Test impact of health check failure"""
        manager = EnhancedDatabaseManager()
        
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
                
                with patch.object(manager, '_run_migrations') as mock_migrations:
                    mock_migrations.return_value = {"status": "success"}
                    
                    with patch.object(manager, '_health_check_loop') as mock_health:
                        mock_health.return_value = asyncio.sleep(0.1)
                        
                        await manager.initialize()
                        
                        # Simulate health check failure
                        with patch.object(manager.database, 'health_check') as mock_health_check:
                            mock_health_check.side_effect = [True, False, False, False]  # First success, then failures
                            
                            # Perform operations
                            async with manager.get_connection() as conn:
                                pass
                            
                            # Get stats
                            stats = await manager.get_stats()
                            
                            # Verify health check failure reflected in stats
                            assert stats["is_healthy"] == False
                            assert manager.stats.is_healthy == False
    
    @pytest.mark.asyncio
    async def test_health_check_recovery(self):
        """Test health check recovery after failure"""
        manager = EnhancedDatabaseManager()
        
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
                
                with patch.object(manager, '_run_migrations') as mock_migrations:
                    mock_migrations.return_value = {"status": "success"}
                    
                    with patch.object(manager, '_health_check_loop') as mock_health:
                        mock_health.return_value = asyncio.sleep(0.1)
                        
                        await manager.initialize()
                        
                        # Simulate health check recovery
                        with patch.object(manager.database, 'health_check') as mock_health_check:
                            mock_health_check.side_effect = [True, False, True]  # Success, failure, recovery
                            
                            # Perform operations
                            async with manager.get_connection() as conn:
                                pass
                            
                            # Get stats
                            stats = await manager.get_stats()
                            
                            # Verify recovery reflected in stats
                            assert stats["is_healthy"] == True
                            assert manager.stats.is_healthy == True


class TestDatabaseBackupIntegration:
    """Test backup system integration"""
    
    @pytest.mark.asyncio
    async def test_backup_with_migrations(self):
        """Test backup creation with migration state"""
        manager = EnhancedDatabaseManager()
        
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
                
                with patch.object(manager, '_run_migrations') as mock_migrations:
                    mock_migrations.return_value = {"status": "success", "migrations_applied": 2}
                    
                    with patch.object(manager, '_health_check_loop') as mock_health:
                        mock_health.return_value = asyncio.sleep(0.1)
                        
                        await manager.initialize()
                        
                        # Test backup creation
                        with patch.object(manager, '_backup_sql') as mock_backup:
                            mock_backup.return_value = {
                                "backup_path": "test_backup.json",
                                "tables_count": 5,
                                "total_rows": 100
                            }
                            
                            backup_info = await manager.backup_database()
                            
                            assert "timestamp" in backup_info
                            assert "backup_path" in backup_info
                            assert backup_info["status"] == "completed"
                            assert backup_info["tables_count"] == 5
                            assert backup_info["total_rows"] == 100
    
    @pytest.mark.asyncio
    async def test_backup_with_error_handling(self):
        """Test backup error handling"""
        manager = EnhancedDatabaseManager()
        
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
                
                with patch.object(manager, '_run_migrations') as mock_migrations:
                    mock_migrations.return_value = {"status": "success"}
                    
                    with patch.object(manager, '_health_check_loop') as mock_health:
                        mock_health.return_value = asyncio.sleep(0.1)
                        
                        await manager.initialize()
                        
                        # Test backup error handling
                        with patch.object(manager, '_backup_sql') as mock_backup:
                            mock_backup.side_effect = Exception("Backup failed")
                            
                            with pytest.raises(DatabaseError):
                                await manager.backup_database()
                            
                            # Verify error was logged
                            assert manager.stats.error_count > 0
    
    @pytest.mark.asyncio
    async def test_backup_integrity_check(self):
        """Test backup integrity verification"""
        manager = EnhancedDatabaseManager()
        
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
                
                with patch.object(manager, '_run_migrations') as mock_migrations:
                    mock_migrations.return_value = {"status": "success"}
                    
                    with patch.object(manager, '_health_check_loop') as mock_health:
                        mock_health.return_value = asyncio.sleep(0.1)
                        
                        await manager.initialize()
                        
                        # Test backup integrity
                        with patch.object(manager, '_backup_sql') as mock_backup:
                            mock_backup.return_value = {
                                "backup_path": "test_backup.json",
                                "tables_count": 5,
                                "total_rows": 100,
                                "checksum": "abc123"
                            }
                            
                            backup_info = await manager.backup_database()
                            
                            # Verify backup integrity
                            assert "checksum" in backup_info
                            assert backup_info["status"] == "completed"
                            
                            # Verify backup can be loaded
                            import json
                            with open(backup_info["backup_path"], 'r') as f:
                                backup_data = json.load(f)
                            
                            assert "tables" in backup_data
                            assert "data" in backup_data


class TestDatabaseRealWorldScenarios:
    """Test real-world database scenarios"""
    
    @pytest.mark.asyncio
    async def test_concurrent_migrations_and_operations(self):
        """Test concurrent migrations and database operations"""
        manager = EnhancedDatabaseManager()
        
        with patch.object(manager, '_get_database_config') as mock_config:
            mock_config.return_value = DatabaseConfig(
                db_type=DatabaseType.SQLITE,
                host="localhost",
                port=0,
                database="test.db",
                username="",
                password="",
                max_connections=20,
                min_connections=5
            )
            
            with patch.object(manager.pool, 'initialize') as mock_init:
                mock_init.return_value = None
                
                with patch.object(manager, '_run_migrations') as mock_migrations:
                    mock_migrations.return_value = {"status": "success", "migrations_applied": 2}
                    
                    with patch.object(manager, '_health_check_loop') as mock_health:
                        mock_health.return_value = asyncio.sleep(0.1)
                        
                        await manager.initialize()
                        
                        # Mock connection pooling
                        mock_conn = Mock()
                        manager.pool.get_connection = AsyncMock(return_value=mock_conn)
                        manager.pool.return_connection = AsyncMock()
                        
                        # Create concurrent tasks
                        tasks = []
                        
                        # Migration task
                        async def run_migration():
                            return await manager.run_migrations()
                        
                        # Query tasks
                        async def run_query(i):
                            return await manager.execute_query(f"SELECT * FROM table_{i}")
                        
                        # Connection tasks
                        async def get_connection():
                            async with manager.get_connection() as conn:
                                await asyncio.sleep(0.1)
                        
                        # Add tasks
                        tasks.append(asyncio.create_task(run_migration()))
                        
                        for i in range(5):
                            tasks.append(asyncio.create_task(run_query(i)))
                        
                        for i in range(3):
                            tasks.append(asyncio.create_task(get_connection()))
                        
                        # Run all tasks concurrently
                        results = await asyncio.gather(*tasks, return_exceptions=True)
                        
                        # Verify results
                        assert not any(isinstance(r, Exception) for r in results)
                        assert len(results) == 9
                        
                        # Verify connection pooling was used
                        assert manager.pool.get_connection.call_count == 3
                        assert manager.pool.return_connection.call_count == 3
    
    @pytest.mark.asyncio
    async def test_database_failover_scenario(self):
        """Test database failover scenario"""
        manager = EnhancedDatabaseManager()
        
        with patch.object(manager, '_get_database_config') as mock_config:
            mock_config.return_value = DatabaseConfig(
                db_type=DatabaseType.POSTGRESQL,
                host="localhost",
                port=5432,
                database="testdb",
                username="user",
                password="pass",
                max_connections=20,
                min_connections=5
            )
            
            with patch.object(manager.pool, 'initialize') as mock_init:
                mock_init.return_value = None
                
                with patch.object(manager, '_run_migrations') as mock_migrations:
                    mock_migrations.return_value = {"status": "success"}
                    
                    with patch.object(manager, '_health_check_loop') as mock_health:
                        mock_health.return_value = asyncio.sleep(0.1)
                        
                        await manager.initialize()
                        
                        # Simulate failover
                        with patch.object(manager.database, 'health_check') as mock_health:
                            # Initially healthy
                            mock_health.return_value = True
                            
                            # Perform operations
                            await manager.health_check()
                            await manager.execute_query("SELECT 1")
                            
                            # Simulate failover to standby
                            mock_health.return_value = False
                            
                            # Perform operations again (should handle failure gracefully)
                            with pytest.raises(DatabaseError):
                                await manager.health_check()
                            
                            # Verify statistics reflect failover
                            stats = await manager.get_stats()
                            assert stats["is_healthy"] == False
                            assert manager.stats.is_healthy == False
    
    @pytest.mark.asyncio
    async def test_large_dataset_handling(self):
        """Test handling of large datasets"""
        manager = EnhancedDatabaseManager()
        
        with patch.object(manager, '_get_database_config') as mock_config:
            mock_config.return_value = DatabaseConfig(
                db_type=DatabaseType.POSTGRESQL,
                host="localhost",
                port=5432,
                database="testdb",
                username="user",
                password="pass",
                max_connections=20,
                min_connections=5
            )
            
            with patch.object(manager.pool, 'initialize') as mock_init:
                mock_init.return_value = None
                
                with patch.object(manager, '_run_migrations') as mock_migrations:
                    mock_migrations.return_value = {"status": "success"}
                    
                    with patch.object(manager, '_health_check_loop') as mock_health:
                        mock_health.return_value = asyncio.sleep(0.1)
                        
                        await manager.initialize()
                        
                        # Mock large dataset query
                        large_dataset = [{"id": i, "data": f"data_{i}"} for i in range(10000)]
                        
                        with patch.object(manager.database, 'execute_query') as mock_query:
                            mock_query.return_value = large_dataset
                            
                            # Execute large query
                            start_time = time.time()
                            result = await manager.execute_query("SELECT * FROM large_table")
                            end_time = time.time()
                            
                            # Verify performance
                            assert len(result) == 10000
                            elapsed_time = end_time - start_time
                            assert elapsed_time < 5.0  # Should complete within 5 seconds
                            
                            # Verify statistics
                            assert manager.stats.query_count > 0
                            assert manager.stats.avg_query_time > 0


class TestDatabaseEdgeCases:
    """Test database edge cases"""
    
    @pytest.mark.asyncio
    async def test_database_disconnect_recovery(self):
        """Test database disconnect and recovery"""
        manager = EnhancedDatabaseManager()
        
        with patch.object(manager, '_get_database_config') as mock_config:
            mock_config.return_value = DatabaseConfig(
                db_type=DatabaseType.POSTGRESQL,
                host="localhost",
                port=5432,
                database="testdb",
                username="user",
                password="pass",
                max_connections=20,
                min_connections=5
            )
            
            with patch.object(manager.pool, 'initialize') as mock_init:
                mock_init.return_value = None
                
                with patch.object(manager, '_run_migrations') as mock_migrations:
                    mock_migrations.return_value = {"status": "success"}
                    
                    with patch.object(manager, '_health_check_loop') as mock_health:
                        mock_health.return_value = asyncio.sleep(0.1)
                        
                        await manager.initialize()
                        
                        # Simulate disconnect
                        with patch.object(manager.database, 'health_check') as mock_health:
                            mock_health.side_effect = [Exception("Connection lost"), True]
                            
                            # Perform operation (should trigger reconnect)
                            with patch.object(manager.database, 'execute_query') as mock_query:
                                mock_query.return_value = [{"id": 1}]
                                
                                result = await manager.execute_query("SELECT 1")
                                assert result == [{"id": 1}]
                                
                                # Verify health check was called multiple times
                                assert mock_health.call_count > 1
    
    @pytest.mark.asyncio
    async def test_database_timeout_handling(self):
        """Test database timeout handling"""
        manager = EnhancedDatabaseManager()
        
        with patch.object(manager, '_get_database_config') as mock_config:
            mock_config.return_value = DatabaseConfig(
                db_type=DatabaseType.POSTGRESQL,
                host="localhost",
                port=5432,
                database="testdb",
                username="user",
                password="pass",
                max_connections=20,
                min_connections=5,
                timeout=5
            )
            
            with patch.object(manager.pool, 'initialize') as mock_init:
                mock_init.return_value = None
                
                with patch.object(manager, '_run_migrations') as mock_migrations:
                    mock_migrations.return_value = {"status": "success"}
                    
                    with patch.object(manager, '_health_check_loop') as mock_health:
                        mock_health.return_value = asyncio.sleep(0.1)
                        
                        await manager.initialize()
                        
                        # Simulate timeout
                        with patch.object(manager.database, 'execute_query') as mock_query:
                            mock_query.side_effect = asyncio.TimeoutError("Query timeout")
                            
                            with pytest.raises(DatabaseError):
                                await manager.execute_query("SELECT 1")
                            
                            # Verify error was handled
                            assert manager.stats.error_count > 0
    
    @pytest.mark.asyncio
    async def test_database_corruption_recovery(self):
        """Test database corruption recovery"""
        manager = EnhancedDatabaseManager()
        
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
                
                with patch.object(manager, '_run_migrations') as mock_migrations:
                    mock_migrations.return_value = {"status": "success"}
                    
                    with patch.object(manager, '_health_check_loop') as mock_health:
                        mock_health.return_value = asyncio.sleep(0.1)
                        
                        await manager.initialize()
                        
                        # Simulate corruption
                        with patch.object(manager.database, 'health_check') as mock_health:
                            mock_health.side_effect = [Exception("Database corrupted"), True]
                            
                            with patch.object(manager.database, 'repair_database') as mock_repair:
                                mock_repair.return_value = True
                                
                                # Perform operation (should trigger repair)
                                await manager.health_check()
                                
                                # Verify repair was called
                                mock_repair.assert_called_once()