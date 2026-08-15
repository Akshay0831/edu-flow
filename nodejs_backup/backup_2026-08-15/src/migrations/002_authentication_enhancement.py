"""
Enhanced Authentication System Migration

This migration integrates the enhanced authentication system with the database:
- Add authentication-related fields to users table
- Add session management tables
- Add authentication logs and audit trails
- Support for multiple authentication providers

Author: Edu-Flow Team
"""

# Migration metadata
VERSION = "2.0.0"
NAME = "Enhanced Authentication"
DESCRIPTION = """Enhance authentication system with multi-provider support and session management"""

# SQL Migration (for SQL databases)
UPGRADE_SQL = """
-- Add authentication-related columns to users table
ALTER TABLE users ADD COLUMN IF NOT EXISTS email_verified BOOLEAN DEFAULT FALSE;
ALTER TABLE users ADD COLUMN IF NOT EXISTS phone_verified BOOLEAN DEFAULT FALSE;
ALTER TABLE users ADD COLUMN IF NOT EXISTS two_factor_enabled BOOLEAN DEFAULT FALSE;
ALTER TABLE users ADD COLUMN IF NOT EXISTS failed_login_attempts INTEGER DEFAULT 0;
ALTER TABLE users ADD COLUMN IF NOT EXISTS account_locked_until TIMESTAMP;
ALTER TABLE users ADD COLUMN IF NOT EXISTS last_password_change TIMESTAMP DEFAULT CURRENT_TIMESTAMP;
ALTER TABLE users ADD COLUMN IF NOT EXISTS refresh_token_hash VARCHAR(255);

-- Create sessions table for session management
CREATE TABLE IF NOT EXISTS sessions (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER NOT NULL,
    session_token VARCHAR(255) UNIQUE NOT NULL,
    refresh_token VARCHAR(255) UNIQUE NOT NULL,
    access_token_hash VARCHAR(255) NOT NULL,
    expires_at TIMESTAMP NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    last_accessed TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    ip_address VARCHAR(45),
    user_agent TEXT,
    is_active BOOLEAN DEFAULT TRUE,
    device_fingerprint VARCHAR(255),
    FOREIGN KEY (user_id) REFERENCES users (id) ON DELETE CASCADE
);

-- Create authentication logs table
CREATE TABLE IF NOT EXISTS auth_logs (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER,
    event_type VARCHAR(50) NOT NULL,
    event_details TEXT,
    ip_address VARCHAR(45),
    user_agent TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    status VARCHAR(20) DEFAULT 'success',
    FOREIGN KEY (user_id) REFERENCES users (id) ON DELETE CASCADE
);

-- Create password reset tokens table
CREATE TABLE IF NOT EXISTS password_reset_tokens (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER NOT NULL,
    token VARCHAR(255) UNIQUE NOT NULL,
    expires_at TIMESTAMP NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    used BOOLEAN DEFAULT FALSE,
    FOREIGN KEY (user_id) REFERENCES users (id) ON DELETE CASCADE
);

-- Create OAuth providers table for external authentication
CREATE TABLE IF NOT EXISTS oauth_providers (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER NOT NULL,
    provider_name VARCHAR(50) NOT NULL,
    provider_user_id VARCHAR(255) NOT NULL,
    access_token TEXT,
    refresh_token TEXT,
    expires_at TIMESTAMP,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users (id) ON DELETE CASCADE,
    UNIQUE (user_id, provider_name, provider_user_id)
);

-- Create indexes for better performance
CREATE INDEX IF NOT EXISTS idx_users_email_verified ON users(email_verified);
CREATE INDEX IF NOT EXISTS idx_users_failed_login_attempts ON users(failed_login_attempts);
CREATE INDEX IF NOT EXISTS idx_users_account_locked_until ON users(account_locked_until);

CREATE INDEX IF NOT EXISTS idx_sessions_user_id ON sessions(user_id);
CREATE INDEX IF NOT EXISTS idx_sessions_session_token ON sessions(session_token);
CREATE INDEX IF NOT EXISTS idx_sessions_refresh_token ON sessions(refresh_token);
CREATE INDEX IF NOT EXISTS idx_sessions_expires_at ON sessions(expires_at);
CREATE INDEX IF NOT EXISTS idx_sessions_is_active ON sessions(is_active);

CREATE INDEX IF NOT EXISTS idx_auth_logs_user_id ON auth_logs(user_id);
CREATE INDEX IF NOT EXISTS idx_auth_logs_event_type ON auth_logs(event_type);
CREATE INDEX IF NOT EXISTS idx_auth_logs_created_at ON auth_logs(created_at);

CREATE INDEX IF NOT EXISTS idx_password_reset_tokens_user_id ON password_reset_tokens(user_id);
CREATE INDEX IF NOT EXISTS idx_password_reset_tokens_token ON password_reset_tokens(token);
CREATE INDEX IF NOT EXISTS idx_password_reset_tokens_expires_at ON password_reset_tokens(expires_at);

CREATE INDEX IF NOT EXISTS idx_oauth_providers_user_id ON oauth_providers(user_id);
CREATE INDEX IF NOT EXISTS idx_oauth_providers_provider_name ON oauth_providers(provider_name);
"""

DOWNGRADE_SQL = """
-- Drop indexes
DROP INDEX IF EXISTS idx_oauth_providers_provider_name;
DROP INDEX IF EXISTS idx_oauth_providers_user_id;
DROP INDEX IF EXISTS idx_password_reset_tokens_expires_at;
DROP INDEX IF EXISTS idx_password_reset_tokens_token;
DROP INDEX IF EXISTS idx_password_reset_tokens_user_id;
DROP INDEX IF EXISTS idx_auth_logs_created_at;
DROP INDEX IF EXISTS idx_auth_logs_event_type;
DROP INDEX IF EXISTS idx_auth_logs_user_id;
DROP INDEX IF EXISTS idx_sessions_is_active;
DROP INDEX IF EXISTS idx_sessions_expires_at;
DROP INDEX IF EXISTS idx_sessions_refresh_token;
DROP INDEX IF EXISTS idx_sessions_session_token;
DROP INDEX IF EXISTS idx_sessions_user_id;
DROP INDEX IF EXISTS idx_users_account_locked_until;
DROP INDEX IF EXISTS idx_users_failed_login_attempts;
DROP INDEX IF EXISTS idx_users_email_verified;

-- Drop tables
DROP TABLE IF EXISTS oauth_providers;
DROP TABLE IF EXISTS password_reset_tokens;
DROP TABLE IF EXISTS auth_logs;
DROP TABLE IF EXISTS sessions;

-- Remove authentication-related columns from users table
ALTER TABLE users DROP COLUMN IF EXISTS email_verified;
ALTER TABLE users DROP COLUMN IF EXISTS phone_verified;
ALTER TABLE users DROP COLUMN IF EXISTS two_factor_enabled;
ALTER TABLE users DROP COLUMN IF EXISTS failed_login_attempts;
ALTER TABLE users DROP COLUMN IF EXISTS account_locked_until;
ALTER TABLE users DROP COLUMN IF EXISTS last_password_change;
ALTER TABLE users DROP COLUMN IF EXISTS refresh_token_hash;
"""

# MongoDB Migration (for MongoDB databases)
UPGRADE_MONGO = {
    "operation": "create_collections",
    "collections": [
        {
            "name": "sessions",
            "indexes": [
                {"key": {"user_id": 1}},
                {"key": {"session_token": 1}, "unique": True},
                {"key": {"refresh_token": 1}, "unique": True},
                {"key": {"expires_at": 1}},
                {"key": {"is_active": 1}},
                {"key": {"created_at": 1}}
            ]
        },
        {
            "name": "auth_logs",
            "indexes": [
                {"key": {"user_id": 1}},
                {"key": {"event_type": 1}},
                {"key": {"created_at": 1}},
                {"key": {"status": 1}}
            ]
        },
        {
            "name": "password_reset_tokens",
            "indexes": [
                {"key": {"user_id": 1}},
                {"key": {"token": 1}, "unique": True},
                {"key": {"expires_at": 1}},
                {"key": {"used": 1}}
            ]
        },
        {
            "name": "oauth_providers",
            "indexes": [
                {"key": {"user_id": 1}},
                {"key": {"provider_name": 1}},
                {"key": {"provider_user_id": 1}},
                {"key": {"provider_name": 1, "provider_user_id": 1}, "unique": True},
                {"key": {"expires_at": 1}}
            ]
        }
    ]
}

DOWNGRADE_MONGO = {
    "operation": "drop_collections",
    "collections": ["oauth_providers", "password_reset_tokens", "auth_logs", "sessions"]
}

# Python Migration (for complex operations)
async def upgrade_migration(database):
    """
    Custom upgrade logic for complex migrations.
    """
    # Update existing users to have default authentication fields
    update_data = {
        "$set": {
            "email_verified": False,
            "phone_verified": False,
            "two_factor_enabled": False,
            "failed_login_attempts": 0,
            "last_password_change": datetime.utcnow(),
            "refresh_token_hash": None
        }
    }
    
    await database.update_many("users", {}, update_data)
    
    # Add default authentication providers for existing users
    oauth_providers = [
        {"provider_name": "google", "provider_user_id": "google_id"},
        {"provider_name": "github", "provider_user_id": "github_id"},
        {"provider_name": "microsoft", "provider_user_id": "microsoft_id"}
    ]
    
    for provider in oauth_providers:
        await database.update_many(
            "oauth_providers", 
            {"user_id": {"$exists": True}},
            {"$set": provider}
        )

async def downgrade_migration(database):
    """
    Custom downgrade logic for complex migrations.
    """
    # Clean up authentication-related data
    await database.delete_many("sessions", {})
    await database.delete_many("auth_logs", {})
    await database.delete_many("password_reset_tokens", {})
    await database.delete_many("oauth_providers", {})
    
    # Remove authentication fields from users
    update_data = {
        "$unset": {
            "email_verified": "",
            "phone_verified": "",
            "two_factor_enabled": "",
            "failed_login_attempts": "",
            "account_locked_until": "",
            "last_password_change": "",
            "refresh_token_hash": ""
        }
    }
    
    await database.update_many("users", {}, update_data)