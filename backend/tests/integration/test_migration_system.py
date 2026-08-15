"""
Migration System Integration Tests

Comprehensive tests for the database migration system:
- Migration creation and execution
- Version control and rollback
- Migration status tracking
- Migration error handling and recovery
- Cross-database migration support

Author: Edu-Flow Team
"""

import pytest
import asyncio
import json
import tempfile
import os
from datetime import datetime, timedelta
from unittest.mock import Mock, patch, AsyncMock, mock_open

from src.core.database_migrations import (
    MigrationManager, MigrationStatus, MigrationScript, MigrationResult
)
from src.core.database_abstraction import DatabaseInterface, DatabaseType, DatabaseConfig
from src.core.exceptions import MigrationError, DatabaseError


class TestMigrationCreation:
    """Test migration creation functionality"""
    
    @pytest.mark.asyncio
    async def test_create_migration(self):
        """Test creating a new migration"""
        mock_database = Mock(spec=DatabaseInterface)
        mock_database.db_type = DatabaseType.SQLITE
        
        config = DatabaseConfig(
            db_type=DatabaseType.SQLITE,
            host="localhost",
            port=0,
            database="test.db",
            username="",
            password="",
            max_connections=10,
            min_connections=1
        )
        
        manager = MigrationManager(mock_database, config)
        manager.migrations_dir = tempfile.mkdtemp()
        
        # Mock file system operations
        with patch('os.makedirs'), patch('builtins.open', mock_open()), patch('json.dump'):
            migration_path = await manager.create_migration("test_migration", "Test description")
            
            assert migration_path is not None
            assert migration_path.endswith("001_test_migration.py")
            
            # Verify migration was created
            assert os.path.exists(migration_path)
            
            # Read migration content
            with open(migration_path, 'r') as f:
                content = f.read()
                assert "def upgrade():" in content
                assert "def downgrade():" in content
    
    @pytest.mark.asyncio
    async def test_create_migration_with_dependencies(self):
        """Test creating migration with dependencies"""
        mock_database = Mock(spec=DatabaseInterface)
        mock_database.db_type = DatabaseType.SQLITE
        
        config = DatabaseConfig(
            db_type=DatabaseType.SQLITE,
            host="localhost",
            port=0,
            database="test.db",
            username="",
            password="",
            max_connections=10,
            min_connections=1
        )
        
        manager = MigrationManager(mock_database, config)
        manager.migrations_dir = tempfile.mkdtemp()
        
        # Mock existing migrations
        existing_migration = MigrationScript(
            version="001",
            name="initial_schema",
            description="Initial database schema",
            upgrade_sql=["CREATE TABLE test (id INTEGER)"],
            downgrade_sql=["DROP TABLE test"],
            dependencies=[]
        )
        manager.applied_migrations = {"001": existing_migration}
        
        with patch('os.makedirs'), patch('builtins.open', mock_open()), patch('json.dump'):
            migration_path = await manager.create_migration(
                "dependent_migration", 
                "Depends on initial schema",
                dependencies=["001"]
            )
            
            assert migration_path is not None
            
            # Verify dependency in migration content
            with open(migration_path, 'r') as f:
                content = f.read()
                assert 'dependencies=["001"]' in content
    
    @pytest.mark.asyncio
    async def test_create_migration_error_handling(self):
        """Test migration creation error handling"""
        mock_database = Mock(spec=DatabaseInterface)
        mock_database.db_type = DatabaseType.SQLITE
        
        config = DatabaseConfig(
            db_type=DatabaseType.SQLITE,
            host="localhost",
            port=0,
            database="test.db",
            username="",
            password="",
            max_connections=10,
            min_connections=1
        )
        
        manager = MigrationManager(mock_database, config)
        manager.migrations_dir = "/invalid/path"
        
        with pytest.raises(MigrationError):
            await manager.create_migration("test_migration", "Test description")


class TestMigrationExecution:
    """Test migration execution functionality"""
    
    @pytest.mark.asyncio
    async def test_apply_migration(self):
        """Test applying a single migration"""
        mock_database = Mock(spec=DatabaseInterface)
        mock_database.db_type = DatabaseType.SQLITE
        
        # Mock database operations
        mock_database.execute_update = AsyncMock()
        mock_database.execute_query = AsyncMock(return_value=[])
        
        config = DatabaseConfig(
            db_type=DatabaseType.SQLITE,
            host="localhost",
            port=0,
            database="test.db",
            username="",
            password="",
            max_connections=10,
            min_connections=1
        )
        
        manager = MigrationManager(mock_database, config)
        manager.migrations_dir = tempfile.mkdtemp()
        
        # Create test migration
        migration = MigrationScript(
            version="001",
            name="test_migration",
            description="Test migration",
            upgrade_sql=["CREATE TABLE users (id INTEGER, name TEXT)"],
            downgrade_sql=["DROP TABLE users"],
            dependencies=[]
        )
        
        # Mock migration tracking
        manager.applied_migrations = {}
        
        with patch('os.path.exists', return_value=True), \
             patch('builtins.open', mock_open()), \
             patch('json.dump'), \
             patch('json.load', return_value=[]):
            
            result = await manager.apply_migration(migration)
            
            assert result.status == "success"
            assert mock_database.execute_update.call_count == 1
            
            # Verify migration was tracked
            assert "001" in manager.applied_migrations
            assert manager.applied_migrations["001"].name == "test_migration"
    
    @pytest.mark.asyncio
    async def test_apply_migration_with_dependencies(self):
        """Test applying migration with dependencies"""
        mock_database = Mock(spec=DatabaseInterface)
        mock_database.db_type = DatabaseType.SQLITE
        
        mock_database.execute_update = AsyncMock()
        mock_database.execute_query = AsyncMock(return_value=[])
        
        config = DatabaseConfig(
            db_type=DatabaseType.SQLITE,
            host="localhost",
            port=0,
            database="test.db",
            username="",
            password="",
            max_connections=10,
            min_connections=1
        )
        
        manager = MigrationManager(mock_database, config)
        manager.migrations_dir = tempfile.mkdtemp()
        
        # Create migrations with dependencies
        migration1 = MigrationScript(
            version="001",
            name="initial_schema",
            description="Initial schema",
            upgrade_sql=["CREATE TABLE test (id INTEGER)"],
            downgrade_sql=["DROP TABLE test"],
            dependencies=[]
        )
        
        migration2 = MigrationScript(
            version="002",
            name="dependent_migration",
            description="Depends on initial schema",
            upgrade_sql=["INSERT INTO test VALUES (1)"],
            downgrade_sql=["DELETE FROM test WHERE id = 1"],
            dependencies=["001"]
        )
        
        # Mock migration tracking
        manager.available_migrations = {"001": migration1, "002": migration2}
        manager.applied_migrations = {"001": migration1}  # First migration already applied
        
        with patch('os.path.exists', return_value=True), \
             patch('builtins.open', mock_open()), \
             patch('json.dump'), \
             patch('json.load', return_value=[]):
            
            result = await manager.apply_migration(migration2)
            
            assert result.status == "success"
            assert mock_database.execute_update.call_count == 1
    
    @pytest.mark.asyncio
    async def test_apply_migration_error_handling(self):
        """Test migration application error handling"""
        mock_database = Mock(spec=DatabaseInterface)
        mock_database.db_type = DatabaseType.SQLITE
        
        # Mock database error
        mock_database.execute_update = AsyncMock(side_effect=Exception("SQL Error"))
        
        config = DatabaseConfig(
            db_type=DatabaseType.SQLITE,
            host="localhost",
            port=0,
            database="test.db",
            username="",
            password="",
            max_connections=10,
            min_connections=1
        )
        
        manager = MigrationManager(mock_database, config)
        manager.migrations_dir = tempfile.mkdtemp()
        
        migration = MigrationScript(
            version="001",
            name="error_migration",
            description="Migration that will fail",
            upgrade_sql=["INVALID SQL"],
            downgrade_sql=[],
            dependencies=[]
        )
        
        with patch('os.path.exists', return_value=True), \
             patch('builtins.open', mock_open()), \
             patch('json.dump'), \
             patch('json.load', return_value=[]):
            
            result = await manager.apply_migration(migration)
            
            assert result.status == "failed"
            assert result.error == "SQL Error"
            assert "001" not in manager.applied_migrations
    
    @pytest.mark.asyncio
    async def test_rollback_migration(self):
        """Test rolling back a migration"""
        mock_database = Mock(spec=DatabaseInterface)
        mock_database.db_type = DatabaseType.SQLITE
        
        mock_database.execute_update = AsyncMock()
        mock_database.execute_query = AsyncMock(return_value=[])
        
        config = DatabaseConfig(
            db_type=DatabaseType.SQLITE,
            host="localhost",
            port=0,
            database="test.db",
            username="",
            password="",
            max_connections=10,
            min_connections=1
        )
        
        manager = MigrationManager(mock_database, config)
        manager.migrations_dir = tempfile.mkdtemp()
        
        # Create test migration
        migration = MigrationScript(
            version="001",
            name="test_migration",
            description="Test migration",
            upgrade_sql=["CREATE TABLE users (id INTEGER, name TEXT)"],
            downgrade_sql=["DROP TABLE users"],
            dependencies=[]
        )
        
        # Mock applied migration
        manager.applied_migrations = {"001": migration}
        
        with patch('os.path.exists', return_value=True), \
             patch('builtins.open', mock_open()), \
             patch('json.dump'), \
             patch('json.load', return_value=[]):
            
            result = await manager.rollback_migration(migration)
            
            assert result.status == "success"
            assert mock_database.execute_update.call_count == 1
            
            # Verify migration was untracked
            assert "001" not in manager.applied_migrations
    
    @pytest.mark.asyncio
    async def test_rollback_migration_error_handling(self):
        """Test rollback migration error handling"""
        mock_database = Mock(spec=DatabaseInterface)
        mock_database.db_type = DatabaseType.SQLITE
        
        # Mock rollback error
        mock_database.execute_update = AsyncMock(side_effect=Exception("Rollback Error"))
        
        config = DatabaseConfig(
            db_type=DatabaseType.SQLITE,
            host="localhost",
            port=0,
            database="test.db",
            username="",
            password="",
            max_connections=10,
            min_connections=1
        )
        
        manager = MigrationManager(mock_database, config)
        manager.migrations_dir = tempfile.mkdtemp()
        
        migration = MigrationScript(
            version="001",
            name="error_migration",
            description="Migration that will fail on rollback",
            upgrade_sql=["CREATE TABLE users (id INTEGER, name TEXT)"],
            downgrade_sql=["INVALID ROLLBACK SQL"],
            dependencies=[]
        )
        
        manager.applied_migrations = {"001": migration}
        
        with patch('os.path.exists', return_value=True), \
             patch('builtins.open', mock_open()), \
             patch('json.dump'), \
             patch('json.load', return_value=[]):
            
            result = await manager.rollback_migration(migration)
            
            assert result.status == "failed"
            assert result.error == "Rollback Error"
            # Migration should still be applied since rollback failed
            assert "001" in manager.applied_migrations


class TestMigrationVersionControl:
    """Test migration version control functionality"""
    
    @pytest.mark.asyncio
    async def test_version_conflict_detection(self):
        """Test version conflict detection"""
        mock_database = Mock(spec=DatabaseInterface)
        mock_database.db_type = DatabaseType.SQLITE
        
        config = DatabaseConfig(
            db_type=DatabaseType.SQLITE,
            host="localhost",
            port=0,
            database="test.db",
            username="",
            password="",
            max_connections=10,
            min_connections=1
        )
        
        manager = MigrationManager(mock_database, config)
        manager.migrations_dir = tempfile.mkdtemp()
        
        # Create two migrations with same version
        migration1 = MigrationScript(
            version="001",
            name="first_migration",
            description="First migration",
            upgrade_sql=["CREATE TABLE users (id INTEGER)"],
            downgrade_sql=["DROP TABLE users"],
            dependencies=[]
        )
        
        migration2 = MigrationScript(
            version="001",  # Same version
            name="second_migration",
            description="Second migration",
            upgrade_sql=["CREATE TABLE posts (id INTEGER)"],
            downgrade_sql=["DROP TABLE posts"],
            dependencies=[]
        )
        
        # Mock available migrations
        manager.available_migrations = {"001": migration1}
        
        with patch('os.path.exists', return_value=True), \
             patch('builtins.open', mock_open()), \
             patch('json.dump'), \
             patch('json.load', return_value=[]):
            
            # Try to add duplicate migration
            with pytest.raises(MigrationError, match="Version 001 already exists"):
                await manager._validate_new_migration(migration2)
    
    @pytest.mark.asyncio
    async def test_dependency_cycle_detection(self):
        """Test dependency cycle detection"""
        mock_database = Mock(spec=DatabaseInterface)
        mock_database.db_type = DatabaseType.SQLITE
        
        config = DatabaseConfig(
            db_type=DatabaseType.SQLITE,
            host="localhost",
            port=0,
            database="test.db",
            username="",
            password="",
            max_connections=10,
            min_connections=1
        )
        
        manager = MigrationManager(mock_database, config)
        manager.migrations_dir = tempfile.mkdtemp()
        
        # Create migrations with cycle
        migration1 = MigrationScript(
            version="001",
            name="first",
            description="First migration",
            upgrade_sql=["CREATE TABLE users (id INTEGER)"],
            downgrade_sql=["DROP TABLE users"],
            dependencies=["003"]  # Depends on 003
        )
        
        migration2 = MigrationScript(
            version="002",
            name="second",
            description="Second migration",
            upgrade_sql=["CREATE TABLE posts (id INTEGER)"],
            downgrade_sql=["DROP TABLE posts"],
            dependencies=["001"]
        )
        
        migration3 = MigrationScript(
            version="003",
            name="third",
            description="Third migration",
            upgrade_sql=["CREATE TABLE comments (id INTEGER)"],
            downgrade_sql=["DROP TABLE comments"],
            dependencies=["002"]  # Creates cycle: 001 -> 003 -> 002 -> 001
        )
        
        # Mock available migrations
        manager.available_migrations = {"001": migration1, "002": migration2, "003": migration3}
        
        with patch('os.path.exists', return_value=True), \
             patch('builtins.open', mock_open()), \
             patch('json.dump'), \
             patch('json.load', return_value=[]):
            
            # Try to get sorted order (should detect cycle)
            with pytest.raises(MigrationError, match="Circular dependency detected"):
                await manager._get_sorted_migrations()
    
    @pytest.mark.asyncio
    async def test_version_ordering(self):
        """Test migration version ordering"""
        mock_database = Mock(spec=DatabaseInterface)
        mock_database.db_type = DatabaseType.SQLITE
        
        config = DatabaseConfig(
            db_type=DatabaseType.SQLITE,
            host="localhost",
            port=0,
            database="test.db",
            username="",
            password="",
            max_connections=10,
            min_connections=1
        )
        
        manager = MigrationManager(mock_database, config)
        manager.migrations_dir = tempfile.mkdtemp()
        
        # Create multiple migrations
        migrations = {}
        for i in range(1, 6):
            migration = MigrationScript(
                version=f"{i:03d}",
                name=f"migration_{i}",
                description=f"Migration {i}",
                upgrade_sql=[f"CREATE TABLE table_{i} (id INTEGER)"],
                downgrade_sql=[f"DROP TABLE table_{i}"],
                dependencies=[] if i == 1 else [f"{i-1:03d}"]
            )
            migrations[f"{i:03d}"] = migration
        
        # Mock available migrations
        manager.available_migrations = migrations
        
        with patch('os.path.exists', return_value=True), \
             patch('builtins.open', mock_open()), \
             patch('json.dump'), \
             patch('json.load', return_value=[]):
            
            # Get sorted order
            sorted_migrations = await manager._get_sorted_migrations()
            
            # Verify correct order
            versions = [m.version for m in sorted_migrations]
            expected_versions = ["001", "002", "003", "004", "005"]
            
            assert versions == expected_versions


class TestMigrationStatusTracking:
    """Test migration status tracking functionality"""
    
    @pytest.mark.asyncio
    async def test_get_migration_status(self):
        """Test getting migration status"""
        mock_database = Mock(spec=DatabaseInterface)
        mock_database.db_type = DatabaseType.SQLITE
        
        # Mock schema query
        mock_database.execute_query = AsyncMock(return_value=[{
            "version": "002",
            "name": "test_schema",
            "applied_at": "2023-01-01 00:00:00"
        }])
        
        config = DatabaseConfig(
            db_type=DatabaseType.SQLITE,
            host="localhost",
            port=0,
            database="test.db",
            username="",
            password="",
            max_connections=10,
            min_connections=1
        )
        
        manager = MigrationManager(mock_database, config)
        manager.migrations_dir = tempfile.mkdtemp()
        
        # Mock applied migrations
        applied_migration = MigrationScript(
            version="002",
            name="test_schema",
            description="Test schema",
            upgrade_sql=["CREATE TABLE users (id INTEGER)"],
            downgrade_sql=["DROP TABLE users"],
            dependencies=[]
        )
        manager.applied_migrations = {"002": applied_migration}
        
        with patch('os.path.exists', return_value=True), \
             patch('builtins.open', mock_open()), \
             patch('json.dump'), \
             patch('json.load', return_value=[]):
            
            # Mock available migrations
            manager.available_migrations = {
                "001": Mock(version="001", name="initial"),
                "002": applied_migration,
                "003": Mock(version="003", name="new_feature")
            }
            
            status = await manager.get_migration_status()
            
            assert status["latest_version"] == "003"
            assert status["current_version"] == "002"
            assert status["pending_migrations"] == 1
            assert status["applied_migrations"] == 1
            assert status["available_migrations"] == 3
    
    @pytest.mark.asyncio
    async def test_migration_history_tracking(self):
        """Test migration history tracking"""
        mock_database = Mock(spec=DatabaseInterface)
        mock_database.db_type = DatabaseType.SQLITE
        
        # Mock schema query with history
        mock_database.execute_query = AsyncMock(return_value=[{
            "version": "002",
            "name": "test_schema",
            "applied_at": "2023-01-01 00:00:00"
        }, {
            "version": "001",
            "name": "initial",
            "applied_at": "2023-01-01 00:00:00"
        }])
        
        config = DatabaseConfig(
            db_type=DatabaseType.SQLITE,
            host="localhost",
            port=0,
            database="test.db",
            username="",
            password="",
            max_connections=10,
            min_connections=1
        )
        
        manager = MigrationManager(mock_database, config)
        manager.migrations_dir = tempfile.mkdtemp()
        
        with patch('os.path.exists', return_value=True), \
             patch('builtins.open', mock_open()), \
             patch('json.dump'), \
             patch('json.load', return_value=[]):
            
            # Mock applied migrations
            manager.applied_migrations = {
                "001": Mock(version="001", name="initial"),
                "002": Mock(version="002", name="test_schema")
            }
            
            # Mock available migrations
            manager.available_migrations = {
                "001": Mock(version="001", name="initial"),
                "002": Mock(version="002", name="test_schema"),
                "003": Mock(version="003", name="new_feature")
            }
            
            status = await manager.get_migration_status()
            
            # Verify history is sorted
            assert len(status["migration_history"]) == 2
            assert status["migration_history"][0]["version"] == "001"
            assert status["migration_history"][1]["version"] == "002"


class TestCrossDatabaseMigration:
    """Test cross-database migration support"""
    
    @pytest.mark.asyncio
    async def test_sqlite_migration(self):
        """Test SQLite-specific migration handling"""
        mock_database = Mock(spec=DatabaseInterface)
        mock_database.db_type = DatabaseType.SQLITE
        
        mock_database.execute_update = AsyncMock()
        mock_database.execute_query = AsyncMock(return_value=[])
        
        config = DatabaseConfig(
            db_type=DatabaseType.SQLITE,
            host="localhost",
            port=0,
            database="test.db",
            username="",
            password="",
            max_connections=10,
            min_connections=1
        )
        
        manager = MigrationManager(mock_database, config)
        manager.migrations_dir = tempfile.mkdtemp()
        
        # SQLite-specific migration
        migration = MigrationScript(
            version="001",
            name="sqlite_migration",
            description="SQLite-specific migration",
            upgrade_sql=["CREATE TABLE users (id INTEGER, name TEXT)"],
            downgrade_sql=["DROP TABLE users"],
            dependencies=[]
        )
        
        with patch('os.path.exists', return_value=True), \
             patch('builtins.open', mock_open()), \
             patch('json.dump'), \
             patch('json.load', return_value=[]):
            
            result = await manager.apply_migration(migration)
            
            assert result.status == "success"
            # SQLite uses specific syntax
            assert "CREATE TABLE users" in mock_database.execute_update.call_args[0][0]
    
    @pytest.mark.asyncio
    async def test_postgresql_migration(self):
        """Test PostgreSQL-specific migration handling"""
        mock_database = Mock(spec=DatabaseInterface)
        mock_database.db_type = DatabaseType.POSTGRESQL
        
        mock_database.execute_update = AsyncMock()
        mock_database.execute_query = AsyncMock(return_value=[])
        
        config = DatabaseConfig(
            db_type=DatabaseType.POSTGRESQL,
            host="localhost",
            port=5432,
            database="testdb",
            username="user",
            password="pass",
            max_connections=20,
            min_connections=5
        )
        
        manager = MigrationManager(mock_database, config)
        manager.migrations_dir = tempfile.mkdtemp()
        
        # PostgreSQL-specific migration
        migration = MigrationScript(
            version="001",
            name="postgresql_migration",
            description="PostgreSQL-specific migration",
            upgrade_sql=[
                "CREATE TABLE users (id SERIAL, name VARCHAR(100), created_at TIMESTAMPTZ DEFAULT NOW())",
                "CREATE INDEX idx_users_name ON users (name)"
            ],
            downgrade_sql=[
                "DROP INDEX idx_users_name",
                "DROP TABLE users"
            ],
            dependencies=[]
        )
        
        with patch('os.path.exists', return_value=True), \
             patch('builtins.open', mock_open()), \
             patch('json.dump'), \
             patch('json.load', return_value=[]):
            
            result = await manager.apply_migration(migration)
            
            assert result.status == "success"
            # PostgreSQL uses specific syntax
            assert "SERIAL" in mock_database.execute_update.call_args[0][0]
            assert "TIMESTAMPTZ" in mock_database.execute_update.call_args[0][0]
    
    @pytest.mark.asyncio
    async def test_mongodb_migration(self):
        """Test MongoDB-specific migration handling"""
        mock_database = Mock(spec=DatabaseInterface)
        mock_database.db_type = DatabaseType.MONGODB
        
        mock_database.execute_update = AsyncMock()
        mock_database.execute_query = AsyncMock(return_value=[])
        mock_database.create_collection = AsyncMock()
        mock_database.drop_collection = AsyncMock()
        
        config = DatabaseConfig(
            db_type=DatabaseType.MONGODB,
            host="localhost",
            port=27017,
            database="testdb",
            username="",
            password="",
            max_connections=50,
            min_connections=5
        )
        
        manager = MigrationManager(mock_database, config)
        manager.migrations_dir = tempfile.mkdtemp()
        
        # MongoDB-specific migration
        migration = MigrationScript(
            version="001",
            name="mongodb_migration",
            description="MongoDB-specific migration",
            upgrade_sql=[
                "db.createCollection('users')",
                "db.users.createIndex({name: 1})",
                "db.users.createIndex({email: 1}, {unique: true})"
            ],
            downgrade_sql=[
                "db.users.dropIndex({name: 1})",
                "db.users.dropIndex({email: 1})",
                "db.users.drop()"
            ],
            dependencies=[]
        )
        
        with patch('os.path.exists', return_value=True), \
             patch('builtins.open', mock_open()), \
             patch('json.dump'), \
             patch('json.load', return_value=[]):
            
            result = await manager.apply_migration(migration)
            
            assert result.status == "success"
            # MongoDB uses specific methods
            assert mock_database.create_collection.call_count > 0
            assert mock_database.execute_update.call_count > 0
    
    @pytest.mark.asyncio
    async def test_database_type_detection(self):
        """Test database type detection for migrations"""
        mock_database = Mock(spec=DatabaseInterface)
        mock_database.db_type = DatabaseType.POSTGRESQL
        
        config = DatabaseConfig(
            db_type=DatabaseType.POSTGRESQL,
            host="localhost",
            port=5432,
            database="testdb",
            username="user",
            password="pass",
            max_connections=20,
            min_connections=5
        )
        
        manager = MigrationManager(mock_database, config)
        manager.migrations_dir = tempfile.mkdtemp()
        
        # Test database-specific operations
        assert manager._get_database_specific_operations() == "postgresql"
        
        # Test PostgreSQL-specific SQL generation
        sql = manager._generate_sql("CREATE TABLE users (id SERIAL)")
        assert "SERIAL" in sql


class TestMigrationErrorHandling:
    """Test migration error handling"""
    
    @pytest.mark.asyncio
    async def test_migration_partial_failure(self):
        """Test handling of partial migration failure"""
        mock_database = Mock(spec=DatabaseInterface)
        mock_database.db_type = DatabaseType.SQLITE
        
        # Mock partial failure - first query succeeds, second fails
        execute_calls = []
        mock_database.execute_update = AsyncMock(side_effect=[
            None,  # First query succeeds
            Exception("Constraint violation")  # Second query fails
        ])
        
        config = DatabaseConfig(
            db_type=DatabaseType.SQLITE,
            host="localhost",
            port=0,
            database="test.db",
            username="",
            password="",
            max_connections=10,
            min_connections=1
        )
        
        manager = MigrationManager(mock_database, config)
        manager.migrations_dir = tempfile.mkdtemp()
        
        # Migration with multiple operations
        migration = MigrationScript(
            version="001",
            name="partial_failure_migration",
            description="Migration with partial failure",
            upgrade_sql=[
                "CREATE TABLE users (id INTEGER)",
                "ALTER TABLE users ADD COLUMN name TEXT"  # This will fail
            ],
            downgrade_sql=[
                "DROP TABLE users"
            ],
            dependencies=[]
        )
        
        manager.applied_migrations = {}
        
        with patch('os.path.exists', return_value=True), \
             patch('builtins.open', mock_open()), \
             patch('json.dump'), \
             patch('json.load', return_value=[]):
            
            result = await manager.apply_migration(migration)
            
            assert result.status == "failed"
            assert "Constraint violation" in result.error
            
            # Verify partial cleanup
            assert mock_database.execute_update.call_count == 2  # One success, one failure
            assert manager.applied_migrations.get("001") is None
    
    @pytest.mark.asyncio
    async def test_migration_recovery_after_failure(self):
        """Test migration recovery after failure"""
        mock_database = Mock(spec=DatabaseInterface)
        mock_database.db_type = DatabaseType.SQLITE
        
        # Mock failure then recovery
        execute_calls = []
        mock_database.execute_update = AsyncMock(side_effect=[
            None,  # First query succeeds
            Exception("Constraint violation"),  # Second query fails
            None,  # Cleanup succeeds
            None   # Re-attempt succeeds
        ])
        
        config = DatabaseConfig(
            db_type=DatabaseType.SQLITE,
            host="localhost",
            port=0,
            database="test.db",
            username="",
            password="",
            max_connections=10,
            min_connections=1
        )
        
        manager = MigrationManager(mock_database, config)
        manager.migrations_dir = tempfile.mkdtemp()
        
        migration = MigrationScript(
            version="001",
            name="recovery_migration",
            description="Migration that recovers after failure",
            upgrade_sql=[
                "CREATE TABLE users (id INTEGER)",
                "ALTER TABLE users ADD COLUMN name TEXT"  # This will fail then recover
            ],
            downgrade_sql=[
                "DROP TABLE users"
            ],
            dependencies=[]
        )
        
        with patch('os.path.exists', return_value=True), \
             patch('builtins.open', mock_open()), \
             patch('json.dump'), \
             patch('json.load', return_value=[]):
            
            # Mock retry logic
            with patch.object(manager, '_retry_operation') as mock_retry:
                mock_retry.side_effect = [None, None]  # First operation succeeds, second after retry
                
                result = await manager.apply_migration(migration)
                
                assert result.status == "success"
                assert mock_retry.call_count == 1  # One retry needed
    
    @pytest.mark.asyncio
    async def test_migration_concurrent_execution(self):
        """Test concurrent migration execution"""
        mock_database = Mock(spec=DatabaseInterface)
        mock_database.db_type = DatabaseType.SQLITE
        
        mock_database.execute_update = AsyncMock()
        mock_database.execute_query = AsyncMock(return_value=[])
        
        config = DatabaseConfig(
            db_type=DatabaseType.SQLITE,
            host="localhost",
            port=0,
            database="test.db",
            username="",
            password="",
            max_connections=10,
            min_connections=1
        )
        
        manager = MigrationManager(mock_database, config)
        manager.migrations_dir = tempfile.mkdtemp()
        
        # Mock lock acquisition
        with patch('threading.Lock') as mock_lock:
            mock_lock_instance = Mock()
            mock_lock.return_value = mock_lock_instance
            
            # Create two migrations
            migration1 = MigrationScript(
                version="001",
                name="first_migration",
                description="First migration",
                upgrade_sql=["CREATE TABLE users (id INTEGER)"],
                downgrade_sql=["DROP TABLE users"],
                dependencies=[]
            )
            
            migration2 = MigrationScript(
                version="002",
                name="second_migration",
                description="Second migration",
                upgrade_sql=["CREATE TABLE posts (id INTEGER)"],
                downgrade_sql=["DROP TABLE posts"],
                dependencies=[]
            )
            
            manager.applied_migrations = {}
            
            # Mock migration files
            with patch('os.path.exists', return_value=True), \
                 patch('builtins.open', mock_open()), \
                 patch('json.dump'), \
                 patch('json.load', return_value=[]):
                
                # Create concurrent tasks
                tasks = [
                    asyncio.create_task(manager.apply_migration(migration1)),
                    asyncio.create_task(manager.apply_migration(migration2))
                ]
                
                # Run concurrently
                results = await asyncio.gather(*tasks, return_exceptions=True)
                
                # Verify both migrations succeeded
                assert not any(isinstance(r, Exception) for r in results)
                assert len(results) == 2
                
                # Verify lock was used
                assert mock_lock_instance.__enter__.call_count == 2
                assert mock_lock_instance.__exit__.call_count == 2
                
                # Verify both migrations were applied
                assert "001" in manager.applied_migrations
                assert "002" in manager.applied_migrations


# Mock helper function
def mock_open(file=None, mode='r', **kwargs):
    """Mock open function for testing"""
    from unittest.mock import MagicMock
    
    mock = MagicMock()
    
    if 'w' in mode and 'json' in file:
        # Mock JSON file write
        mock.write.return_value = None
    elif 'r' in mode and 'json' in file:
        # Mock JSON file read
        mock.__enter__.return_value.read.return_value = '[]'
    
    return mock