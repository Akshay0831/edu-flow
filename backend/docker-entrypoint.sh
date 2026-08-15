#!/bin/bash

set -e

# Wait for databases to be ready
wait_for_postgres() {
    echo "Waiting for PostgreSQL to be ready..."
    until python -c "
import os
import psycopg2
from urllib.parse import urlparse

db_url = os.getenv('DATABASE_URL', '')
parsed = urlparse(db_url)

try:
    conn = psycopg2.connect(
        dbname=parsed.path[1:],
        user=parsed.username,
        password=parsed.password,
        host=parsed.hostname,
        port=parsed.port or 5432,
        connect_timeout=5
    )
    conn.close()
    print('PostgreSQL is ready')
except Exception as e:
    print(f'PostgreSQL not ready: {e}')
    exit(1)
    "
    do
        echo "PostgreSQL is unavailable - sleeping"
        sleep 2
    done
}

wait_for_mongodb() {
    echo "Waiting for MongoDB to be ready..."
    until python -c "
import os
from pymongo import MongoClient

try:
    mongo_url = os.getenv('MONGODB_URL', '')
    client = MongoClient(mongo_url, serverSelectionTimeoutMS=5000)
    client.admin.command('ping')
    print('MongoDB is ready')
    client.close()
except Exception as e:
    print(f'MongoDB not ready: {e}')
    exit(1)
    "
    do
        echo "MongoDB is unavailable - sleeping"
        sleep 2
    done
}

wait_for_redis() {
    echo "Waiting for Redis to be ready..."
    until python -c "
import redis
import os

try:
    redis_url = os.getenv('REDIS_URL', '')
    client = redis.from_url(redis_url, socket_timeout=5)
    client.ping()
    print('Redis is ready')
    client.close()
except Exception as e:
    print(f'Redis not ready: {e}')
    exit(1)
    "
    do
        echo "Redis is unavailable - sleeping"
        sleep 2
    done
}

# Function to run database migrations
run_migrations() {
    echo "Running database migrations..."
    
    # Wait for databases to be ready first
    wait_for_postgres
    wait_for_mongodb
    wait_for_redis
    
    # Run Python migrations
    python -c "
import os
import sys
sys.path.append('/app')

from src.core.database_migrations import MigrationManager

try:
    manager = MigrationManager()
    manager.run_migrations()
    print('Database migrations completed successfully')
except Exception as e:
    print(f'Database migration failed: {e}')
    sys.exit(1)
    "
    
    # Run additional setup if needed
    if [ -f \"scripts/setup.py\" ]; then
        echo "Running additional setup scripts..."
        python scripts/setup.py
    fi
}

# Function to run tests
run_tests() {
    if [ \"\$RUN_TESTS\" = \"true\" ]; then
        echo "Running tests..."
        
        # Create reports directory if it doesn't exist
        mkdir -p reports
        
        # Run tests with coverage
        python -m pytest \
            --cov=src \
            --cov-report=xml:reports/coverage.xml \
            --cov-report=html:reports/htmlcov \
            --cov-report=term-missing \
            --junitxml=reports/junit.xml \
            --verbose \
            tests/
        
        # Generate coverage badge
        if command -v coverage-badge &> /dev/null; then
            coverage-badge -o reports/coverage.svg
        fi
        
        echo "Tests completed"
    fi
}

# Function to generate API documentation
generate_docs() {
    echo "Generating API documentation..."
    
    # Generate OpenAPI/Swagger docs
    python -c "
from src.api.v1 import app
import json

# Generate OpenAPI documentation
openapi_docs = app.openapi()
with open('/app/docs/openapi.json', 'w') as f:
    json.dump(openapi_docs, f, indent=2)

print('API documentation generated')
    "
    
    # Generate ReDoc static documentation
    if command -v redoc-cli &> /dev/null; then
        redoc-cli bundle /app/docs/openapi.json --output /app/docs/redoc.html
        echo 'ReDoc documentation generated'
    fi
}

# Function to create log directories
setup_logging() {
    echo "Setting up logging directories..."
    
    # Create log directories
    mkdir -p logs/api
    mkdir -p logs/database
    mkdir -p logs/auth
    mkdir -p logs/errors
    mkdir -p logs/audit
    
    # Set proper permissions
    chown -R appuser:appuser logs/
    
    echo "Logging directories created"
}

# Function to initialize monitoring
setup_monitoring() {
    echo "Setting up monitoring..."
    
    # Initialize monitoring service
    python -c "
import asyncio
from src.core.monitoring_system import init_monitoring

async def init():
    await init_monitoring()
    print('Monitoring initialized')

asyncio.run(init())
    "
    
    echo "Monitoring setup completed"
}

# Function to validate environment
validate_environment() {
    echo "Validating environment..."
    
    # Check required environment variables
    required_vars=(
        \"DATABASE_URL\"
        \"MONGODB_URL\"
        \"REDIS_URL\"
        \"SECRET_KEY\"
        \"HOST\"
        \"PORT\"
    )
    
    for var in \"\${required_vars[@]}\"; do
        if [ -z \"\${!var}\" ]; then
            echo \"Error: Required environment variable $var is not set\"
            exit 1
        fi
    done
    
    # Validate database URLs
    python -c "
import os
from urllib.parse import urlparse

# Validate database URLs
db_url = os.getenv('DATABASE_URL', '')
mongo_url = os.getenv('MONGODB_URL', '')
redis_url = os.getenv('REDIS_URL', '')

if not db_url.startswith(('postgresql://', 'postgres://')):
    print('Error: DATABASE_URL must start with postgresql:// or postgres://')
    exit(1)

if not mongo_url.startswith(('mongodb://', 'mongodb+srv://')):
    print('Error: MONGODB_URL must start with mongodb:// or mongodb+srv://')
    exit(1)

if not redis_url.startswith(('redis://', 'rediss://')):
    print('Error: REDIS_URL must start with redis:// or rediss://')
    exit(1)

print('Environment validation passed')
    "
    
    echo "Environment validation completed"
}

# Function to run pre-start hooks
run_pre_start_hooks() {
    echo "Running pre-start hooks..."
    
    # Create pre-start scripts directory
    mkdir -p scripts/pre-start
    
    # Execute pre-start scripts if they exist
    for script in scripts/pre-start/*.sh; do
        if [ -f \"$script\" ]; then
            echo \"Running pre-start script: $script\"
            bash \"$script\"
        fi
    done
    
    echo "Pre-start hooks completed"
}

# Main function
main() {
    echo "Starting Edu-Flow backend API..."
    
    # Validate environment
    validate_environment
    
    # Setup logging
    setup_logging
    
    # Setup monitoring
    setup_monitoring
    
    # Run database migrations
    run_migrations
    
    # Run pre-start hooks
    run_pre_start_hooks
    
    # Generate documentation if requested
    if [ \"\$GENERATE_DOCS\" = \"true\" ]; then
        generate_docs
    fi
    
    # Run tests if requested
    if [ \"\$RUN_TESTS\" = \"true\" ]; then
        run_tests
    fi
    
    echo "Backend API setup completed"
}

# Parse command line arguments
case \"\$1\" in
    \"migrate\")
        run_migrations
        ;;
    \"test\")
        run_tests
        ;;
    \"docs\")
        generate_docs
        ;;
    \"setup\")
        main
        ;;
    \"pre-start\")
        run_pre_start_hooks
        ;;
    *)
        # If no arguments, run the main setup and start the application
        main
        ;;
esac

# If we reach here, execute the command or start the application
if [ \"\$#\" -eq 0 ]; then
    echo \"Starting the application...\"
    exec uvicorn src.api.v1:app --host 0.0.0.0 --port 8000
else
    exec \"\$@\"
fi