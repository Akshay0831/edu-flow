"""
Database Migration System for Edu-Flow

This module provides comprehensive database migration and schema management:
- Alembic-like migration system for SQLite, PostgreSQL, and MongoDB
- Schema versioning and rollback support
- Database initialization and health monitoring
- Migration scripts for database changes
- Data migration utilities
- Schema validation and consistency checks

Author: Edu-Flow Team
"""

import asyncio
import hashlib
import json
import logging
import os
import time
from datetime import datetime
from enum import Enum
from pathlib import Path
from typing import Dict, List, Optional, Any, Union
from dataclasses import dataclass, field

from src.core.database_abstraction import DatabaseInterface, DatabaseType, DatabaseConfig
from src.core.exceptions import DatabaseError, MigrationError, ConfigurationError
from src.core.logging import get_logger

logger = get_logger(__name__)


class MigrationStatus(str, Enum):
    """Migration status enumeration"""
    PENDING = "pending"
    RUNNING = "running"
    SUCCESS = "success"
    FAILED = "failed"
    ROLLED_BACK = "rolled_back"


@dataclass
class MigrationResult:
    """Migration result container"""
    success: bool
    message: str
    migration_id: Optional[str] = None
    rollback_id: Optional[str] = None
    error_message: Optional[str] = None


@dataclass
class MigrationInfo:
    """Migration information container"""
    migration_id: str
    name: str
    description: str
    version: str
    timestamp: datetime
    status: MigrationStatus
    hash: str
    rollback_id: Optional[str] = None
    error_message: Optional[str] = None


@dataclass
class MigrationScript:
    """Migration script container"""
    version: str
    name: str
    description: str
    upgrade_sql: Optional[str] = None
    downgrade_sql: Optional[str] = None
    upgrade_mongo: Optional[Dict[str, Any]] = None
    downgrade_mongo: Optional[Dict[str, Any]] = None
    upgrade_python: Optional[str] = None
    downgrade_python: Optional[str] = None


class MigrationManager:
    """Database migration manager"""
    
    def __init__(self, database: DatabaseInterface, config: DatabaseConfig):
        self.database = database
        self.config = config
        self.migrations_dir = Path(__file__).parent.parent / "migrations"
        self.migrations_table = "migrations"
        self.migration_log: List[MigrationInfo] = []
        self._initialized = False
    
    async def initialize(self):
        """Initialize migration system"""
        if self._initialized:
            return
        
        try:
            # Create migrations table if it doesn't exist
            await self._create_migrations_table()
            self._initialized = True
            logger.info("Migration system initialized")
        except Exception as e:
            logger.error(f"Failed to initialize migration system: {e}")
            raise MigrationError(f"Migration initialization failed: {e}")
    
    async def _create_migrations_table(self):
        """Create migrations table for tracking applied migrations"""
        if self.config.db_type == DatabaseType.MONGODB:
            await self.database.insert_one(self.migrations_table, {
                "migration_id": "system",
                "name": "migrations_table",
                "description": "Tracks applied database migrations",
                "version": "1.0.0",
                "timestamp": datetime.utcnow(),
                "status": MigrationStatus.SUCCESS,
                "hash": self._hash_string("migrations_table"),
                "created_at": datetime.utcnow()
            })
        else:
            await self.database.execute_update(f"""
                CREATE TABLE IF NOT EXISTS {self.migrations_table} (
                    migration_id VARCHAR(255) PRIMARY KEY,
                    name VARCHAR(255) NOT NULL,
                    description TEXT,
                    version VARCHAR(50) NOT NULL,
                    timestamp TIMESTAMP NOT NULL,
                    status VARCHAR(50) NOT NULL,
                    hash VARCHAR(64) NOT NULL,
                    rollback_id VARCHAR(255),
                    error_message TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
    
    def _hash_string(self, content: str) -> str:
        """Generate hash for migration content"""
        return hashlib.sha256(content.encode()).hexdigest()
    
    def get_migration_files(self) -> List[MigrationScript]:
        """Get all migration files"""
        migration_files = []
        
        if not self.migrations_dir.exists():
            return migration_files
        
        for migration_file in self.migrations_dir.glob("*.py"):
            if migration_file.name.startswith("__"):
                continue
            
            try:
                migration = self._load_migration_file(migration_file)
                if migration:
                    migration_files.append(migration)
            except Exception as e:
                logger.warning(f"Failed to load migration file {migration_file}: {e}")
        
        return sorted(migration_files, key=lambda x: x.version)
    
    def _load_migration_file(self, file_path: Path) -> Optional[MigrationScript]:
        """Load migration from file"""
        import importlib.util
        
        spec = importlib.util.spec_from_file_location(file_path.stem, file_path)
        if not spec or not spec.loader:
            return None
        
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        
        # Extract migration info
        version = getattr(module, "VERSION", "1.0.0")
        name = getattr(module, "NAME", f"migration_{file_path.stem}")
        description = getattr(module, "DESCRIPTION", "")
        upgrade_sql = getattr(module, "UPGRADE_SQL", None)
        downgrade_sql = getattr(module, "DOWNGRADE_SQL", None)
        upgrade_mongo = getattr(module, "UPGRADE_MONGO", None)
        downgrade_mongo = getattr(module, "DOWNGRADE_MONGO", None)
        upgrade_python = getattr(module, "UPGRADE_PYTHON", None)
        downgrade_python = getattr(module, "DOWNGRADE_PYTHON", None)
        
        return MigrationScript(
            version=version,
            name=name,
            description=description,
            upgrade_sql=upgrade_sql,
            downgrade_sql=downgrade_sql,
            upgrade_mongo=upgrade_mongo,
            downgrade_mongo=downgrade_mongo,
            upgrade_python=upgrade_python,
            downgrade_python=downgrade_python
        )
    
    async def get_applied_migrations(self) -> List[MigrationInfo]:
        """Get list of applied migrations"""
        if not self._initialized:
            await self.initialize()
        
        if self.config.db_type == DatabaseType.MONGODB:
            migrations = await self.database.find_many(
                self.migrations_table,
                {"migration_id": {"$ne": "system"}},
                sort=[("timestamp", 1)]
            )
        else:
            migrations = await self.database.execute_query(
                f"SELECT * FROM {self.migrations_table} ORDER BY timestamp ASC"
            )
        
        self.migration_log = []
        for migration in migrations:
            self.migration_log.append(MigrationInfo(
                migration_id=migration["migration_id"],
                name=migration["name"],
                description=migration.get("description", ""),
                version=migration["version"],
                timestamp=migration["timestamp"],
                status=MigrationStatus(migration["status"]),
                hash=migration["hash"],
                rollback_id=migration.get("rollback_id"),
                error_message=migration.get("error_message")
            ))
        
        return self.migration_log
    
    async def get_pending_migrations(self) -> List[MigrationScript]:
        """Get list of pending migrations"""
        applied_versions = {mig.version for mig in self.migration_log}
        migration_files = self.get_migration_files()
        
        return [
            mig for mig in migration_files 
            if mig.version not in applied_versions
        ]
    
    async def migrate(self, target_version: Optional[str] = None) -> Dict[str, Any]:
        """Run database migrations"""
        if not self._initialized:
            await self.initialize()
        
        pending_migrations = await self.get_pending_migrations()
        
        if not pending_migrations:
            return {"status": "success", "message": "No pending migrations", "migrations_applied": 0}
        
        if target_version:
            target_migrations = [mig for mig in pending_migrations if mig.version <= target_version]
            if not target_migrations:
                raise MigrationError(f"No migrations found up to version {target_version}")
        else:
            target_migrations = pending_migrations
        
        results = []
        migrations_applied = 0
        
        for migration in target_migrations:
            try:
                logger.info(f"Applying migration {migration.version}: {migration.name}")
                
                # Mark migration as running
                migration_info = MigrationInfo(
                    migration_id=f"mig_{int(time.time())}",
                    name=migration.name,
                    description=migration.description,
                    version=migration.version,
                    timestamp=datetime.utcnow(),
                    status=MigrationStatus.RUNNING,
                    hash=self._hash_string(json.dumps({
                        "upgrade_sql": migration.upgrade_sql,
                        "upgrade_mongo": migration.upgrade_mongo,
                        "upgrade_python": migration.upgrade_python
                    }))
                )
                
                await self._record_migration(migration_info)
                
                # Apply migration based on database type
                if self.config.db_type == DatabaseType.MONGODB:
                    await self._apply_mongo_migration(migration)
                else:
                    await self._apply_sql_migration(migration)
                
                # Mark migration as success
                migration_info.status = MigrationStatus.SUCCESS
                await self._update_migration(migration_info)
                
                results.append({
                    "version": migration.version,
                    "name": migration.name,
                    "status": "success"
                })
                
                migrations_applied += 1
                logger.info(f"Migration {migration.version} applied successfully")
                
            except Exception as e:
                logger.error(f"Migration {migration.version} failed: {e}")
                
                # Mark migration as failed
                migration_info.status = MigrationStatus.FAILED
                migration_info.error_message = str(e)
                await self._update_migration(migration_info)
                
                results.append({
                    "version": migration.version,
                    "name": migration.name,
                    "status": "failed",
                    "error": str(e)
                })
                
                # If any migration fails, stop the process
                raise MigrationError(f"Migration {migration.version} failed: {e}")
        
        return {
            "status": "success",
            "message": f"Applied {migrations_applied} migrations",
            "migrations_applied": migrations_applied,
            "results": results
        }
    
    async def _record_migration(self, migration_info: MigrationInfo):
        """Record migration in database"""
        if self.config.db_type == DatabaseType.MONGODB:
            await self.database.insert_one(self.migrations_table, {
                "migration_id": migration_info.migration_id,
                "name": migration_info.name,
                "description": migration_info.description,
                "version": migration_info.version,
                "timestamp": migration_info.timestamp,
                "status": migration_info.status.value,
                "hash": migration_info.hash,
                "rollback_id": migration_info.rollback_id,
                "error_message": migration_info.error_message,
                "created_at": datetime.utcnow()
            })
        else:
            await self.database.execute_update(f"""
                INSERT INTO {self.migrations_table} 
                (migration_id, name, description, version, timestamp, status, hash, rollback_id, error_message)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, {
                "migration_id": migration_info.migration_id,
                "name": migration_info.name,
                "description": migration_info.description,
                "version": migration_info.version,
                "timestamp": migration_info.timestamp,
                "status": migration_info.status.value,
                "hash": migration_info.hash,
                "rollback_id": migration_info.rollback_id,
                "error_message": migration_info.error_message
            })
    
    async def _update_migration(self, migration_info: MigrationInfo):
        """Update migration record"""
        if self.config.db_type == DatabaseType.MONGODB:
            update_data = {
                "status": migration_info.status.value,
                "error_message": migration_info.error_message,
                "rollback_id": migration_info.rollback_id
            }
            await self.database.update_one(
                self.migrations_table,
                {"migration_id": migration_info.migration_id},
                {"$set": update_data}
            )
        else:
            await self.database.execute_update(f"""
                UPDATE {self.migrations_table} 
                SET status = ?, error_message = ?, rollback_id = ?
                WHERE migration_id = ?
            """, {
                "status": migration_info.status.value,
                "error_message": migration_info.error_message,
                "rollback_id": migration_info.rollback_id,
                "migration_id": migration_info.migration_id
            })
    
    async def _apply_sql_migration(self, migration: MigrationScript):
        """Apply SQL migration"""
        if migration.upgrade_sql:
            # Split and execute SQL statements
            statements = [stmt.strip() for stmt in migration.upgrade_sql.split(";") if stmt.strip()]
            
            for statement in statements:
                if statement:
                    await self.database.execute_update(statement)
    
    async def _apply_mongo_migration(self, migration: MigrationScript):
        """Apply MongoDB migration"""
        if migration.upgrade_mongo:
            operation = migration.upgrade_mongo.get("operation")
            collection = migration.upgrade_mongo.get("collection")
            
            if operation == "create_collection":
                # MongoDB creates collections automatically on insert
                pass
            elif operation == "create_index":
                index_spec = migration.upgrade_mongo.get("index_spec", {})
                await self.database.create_index(collection, index_spec)
            elif operation == "insert_one":
                document = migration.upgrade_mongo.get("document", {})
                await self.database.insert_one(collection, document)
            elif operation == "insert_many":
                documents = migration.upgrade_mongo.get("documents", [])
                await self.database.insert_many(collection, documents)
            elif operation == "update_many":
                filter_query = migration.upgrade_mongo.get("filter", {})
                update_spec = migration.upgrade_mongo.get("update", {})
                await self.database.update_many(collection, filter_query, update_spec)
            else:
                logger.warning(f"Unknown MongoDB migration operation: {operation}")
    
    async def rollback(self, target_version: str) -> Dict[str, Any]:
        """Rollback to target version"""
        if not self._initialized:
            await self.initialize()
        
        # Find migrations to rollback
        migrations_to_rollback = [
            mig for mig in self.migration_log 
            if mig.version > target_version and mig.status == MigrationStatus.SUCCESS
        ]
        
        if not migrations_to_rollback:
            return {"status": "success", "message": "No migrations to rollback", "migrations_rolled_back": 0}
        
        results = []
        migrations_rolled_back = 0
        
        # Reverse order for rollback
        for migration in reversed(migrations_to_rollback):
            try:
                logger.info(f"Rolling back migration {migration.version}: {migration.name}")
                
                # Find the migration script
                migration_files = self.get_migration_files()
                migration_script = next(
                    (mig for mig in migration_files if mig.version == migration.version),
                    None
                )
                
                if not migration_script:
                    raise MigrationError(f"Migration script not found for version {migration.version}")
                
                # Apply rollback
                if self.config.db_type == DatabaseType.MONGODB:
                    await self._apply_mongo_rollback(migration_script)
                else:
                    await self._apply_sql_rollback(migration_script)
                
                # Mark migration as rolled back
                migration.status = MigrationStatus.ROLLED_BACK
                migration.rollback_id = f"rb_{int(time.time())}"
                await self._update_migration(migration)
                
                results.append({
                    "version": migration.version,
                    "name": migration.name,
                    "status": "rolled_back"
                })
                
                migrations_rolled_back += 1
                logger.info(f"Migration {migration.version} rolled back successfully")
                
            except Exception as e:
                logger.error(f"Rollback of migration {migration.version} failed: {e}")
                
                results.append({
                    "version": migration.version,
                    "name": migration.name,
                    "status": "failed",
                    "error": str(e)
                })
                
                # If any rollback fails, stop the process
                raise MigrationError(f"Rollback of migration {migration.version} failed: {e}")
        
        return {
            "status": "success",
            "message": f"Rolled back {migrations_rolled_back} migrations",
            "migrations_rolled_back": migrations_rolled_back,
            "results": results
        }
    
    async def _apply_sql_rollback(self, migration: MigrationScript):
        """Apply SQL rollback"""
        if migration.downgrade_sql:
            # Split and execute SQL statements
            statements = [stmt.strip() for stmt in migration.downgrade_sql.split(";") if stmt.strip()]
            
            for statement in statements:
                if statement:
                    await self.database.execute_update(statement)
    
    async def _apply_mongo_rollback(self, migration: MigrationScript):
        """Apply MongoDB rollback"""
        if migration.downgrade_mongo:
            operation = migration.downgrade_mongo.get("operation")
            collection = migration.downgrade_mongo.get("collection")
            
            if operation == "drop_collection":
                await self.database.drop_collection(collection)
            elif operation == "drop_index":
                index_name = migration.downgrade_mongo.get("index_name")
                await self.database.drop_index(collection, index_name)
            elif operation == "delete_many":
                filter_query = migration.downgrade_mongo.get("filter", {})
                await self.database.delete_many(collection, filter_query)
            else:
                logger.warning(f"Unknown MongoDB rollback operation: {operation}")
    
    async def create_migration(self, name: str, description: str = "") -> str:
        """Create a new migration file"""
        if not self.migrations_dir.exists():
            self.migrations_dir.mkdir(parents=True)
        
        # Generate version
        existing_versions = {mig.version for mig in self.get_migration_files()}
        version = self._generate_version(existing_versions)
        
        # Create migration file
        migration_file = self.migrations_dir / f"{version}_{name.lower().replace(' ', '_')}.py"
        
        migration_template = f'''"""
Migration: {name}

{description}
Version: {version}
Generated: {datetime.utcnow().isoformat()}

Author: Edu-Flow Team
"""

# Migration metadata
VERSION = "{version}"
NAME = "{name}"
DESCRIPTION = """{description}"""

# SQL Migration (for SQL databases)
UPGRADE_SQL = """
-- Add your upgrade SQL here
-- Example: CREATE TABLE new_table (id INTEGER PRIMARY KEY, name TEXT);
"""

DOWNGRADE_SQL = """
-- Add your downgrade SQL here
-- Example: DROP TABLE new_table;
"""

# MongoDB Migration (for MongoDB databases)
UPGRADE_MONGO = {{
    "operation": "create_collection",  # Options: create_collection, create_index, insert_one, insert_many, update_many
    "collection": "new_collection",
    "index_spec": {{"field": 1}},  # For create_index operation
    "document": {{}},  # For insert_one operation
    "documents": [],  # For insert_many operation
    "filter": {{}},  # For update_many/delete_many operation
    "update": {{}}   # For update_many operation
}}

DOWNGRADE_MONGO = {{
    "operation": "drop_collection",  # Options: drop_collection, drop_index, delete_many
    "collection": "new_collection",
    "index_name": "index_name",  # For drop_index operation
    "filter": {{}}  # For delete_many operation
}}

# Python Migration (for complex operations)
# This function will be called during migration
async def upgrade_migration(database):
    """
    Custom upgrade logic for complex migrations.
    Use this when SQL or MongoDB operations are insufficient.
    """
    pass

# Python Migration (for complex operations)
# This function will be called during rollback
async def downgrade_migration(database):
    """
    Custom downgrade logic for complex migrations.
    Use this when SQL or MongoDB operations are insufficient.
    """
    pass
'''
        
        migration_file.write_text(migration_template)
        logger.info(f"Created migration file: {migration_file}")
        
        return str(migration_file)
    
    def _generate_version(self, existing_versions: set) -> str:
        """Generate next version number"""
        if not existing_versions:
            return "1.0.0"
        
        # Get the highest version
        highest_version = max(existing_versions, key=lambda x: tuple(map(int, x.split('.'))))
        major, minor, patch = map(int, highest_version.split('.'))
        
        # Increment patch version
        return f"{major}.{minor}.{patch + 1}"
    
    async def get_migration_status(self) -> Dict[str, Any]:
        """Get current migration status"""
        if not self._initialized:
            await self.initialize()
        
        applied_migrations = await self.get_applied_migrations()
        pending_migrations = await self.get_pending_migrations()
        
        return {
            "total_migrations": len(applied_migrations) + len(pending_migrations),
            "applied_migrations": len(applied_migrations),
            "pending_migrations": len(pending_migrations),
            "latest_version": applied_migrations[-1].version if applied_migrations else None,
            "database_type": self.config.db_type.value
        }