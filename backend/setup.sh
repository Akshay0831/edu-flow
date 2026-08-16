#!/bin/bash

# Backend Setup Script for Edu-Flow

echo "Setting up Edu-Flow Backend..."

# Create necessary directories
mkdir -p logs/ai-services/api logs/ai-services/audit logs/ai-services/errors logs/ai-services/performance \
    logs/auth-gateway/api logs/auth-gateway/audit logs/auth-gateway/errors logs/auth-gateway/performance \
    logs/backend/api logs/backend/audit logs/backend/errors logs/backend/performance \
    logs/database/api logs/database/audit logs/database/errors logs/database/performance \
    logs/frontend/api logs/frontend/audit logs/frontend/errors logs/frontend/performance \
    logs/performance logs/security

# Create .env file if it doesn't exist
if [ ! -f .env ]; then
    cat > .env << EOF
# Database Configuration
DATABASE_URL=postgresql://admin:password123@localhost:5432/eduflow
MONGODB_URI=mongodb://admin:password123@localhost:27017/eduflow?authSource=admin
REDIS_URL=redis://localhost:6379

# Security
SECRET_KEY=your-secret-key-change-in-production
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=30

# AI Services
AI_SERVICE_URL=http://localhost:3000
AI_SERVICE_TIMEOUT=30

# CORS
CORS_ORIGINS=["http://localhost:8080", "http://localhost:3000"]

# Logging
LOG_LEVEL=INFO
LOG_FORMAT=json
EOF
    echo "Created .env file"
fi

# Install Python dependencies
echo "Installing Python dependencies..."
pip install -r requirements.txt

# Run database migrations
echo "Running database migrations..."
python -c "import src.main; import alembic; alembic upgrade head"

echo "Backend setup complete!"
echo "To start the backend: uvicorn src.main:app --reload"