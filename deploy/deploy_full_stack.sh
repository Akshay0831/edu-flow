#!/bin/bash

# Edu-Flow Full Stack Deployment Script
# This script deploys both backend and frontend services

set -e

echo "🚀 Starting Edu-Flow Full Stack Deployment..."

# Configuration
BACKEND_PORT=8001
FRONTEND_PORT=8080
BACKEND_NAME="edu-flow-backend"
FRONTEND_NAME="edu-flow-frontend"
DB_HOST="${DB_HOST:-localhost}"
DB_PORT="${DB_PORT:-5432}"
DB_NAME="${DB_NAME:-edu_flow}"
DB_USER="${DB_USER:-postgres}"
DB_PASSWORD="${DB_PASSWORD:-password}"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

log_info() {
    echo -e "${GREEN}[INFO]${NC} $1"
}

log_warn() {
    echo -e "${YELLOW}[WARN]${NC} $1"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

log_step() {
    echo -e "${BLUE}[STEP]${NC} $1"
}

# Check if Docker is installed
if ! command -v docker &> /dev/null; then
    log_error "Docker is not installed. Please install Docker first."
    exit 1
fi

# Check if Docker Compose is installed
if ! command -v docker-compose &> /dev/null; then
    log_error "Docker Compose is not installed. Please install Docker Compose first."
    exit 1
fi

# Check if required ports are available
check_port() {
    if netstat -tlnp | grep -q ":$1"; then
        log_error "Port $1 is already in use. Please free up this port or configure a different port."
        exit 1
    fi
}

log_step "Checking port availability..."
check_port $BACKEND_PORT
check_port $FRONTEND_PORT

# Create necessary directories
log_info "Creating necessary directories..."
mkdir -p logs
mkdir -p data
mkdir -p uploads
mkdir -p frontend/build

# Build and deploy backend
log_step "Deploying backend..."
cd backend

# Copy environment file if it doesn't exist
if [ ! -f ".env" ]; then
    log_info "Creating backend .env file..."
    cat > .env << EOF
# Database Configuration
DATABASE_URL=postgresql+asyncpg://${DB_USER}:${DB_PASSWORD}@${DB_HOST}:${DB_PORT}/${DB_NAME}
REDIS_URL=redis://${DB_HOST}:${DB_PORT:-6379}/0

# Security Configuration
SECRET_KEY=${SECRET_KEY:-$(openssl rand -hex 32)}
ACCESS_TOKEN_EXPIRE_MINUTES=30
REFRESH_TOKEN_EXPIRE_DAYS=7

# API Configuration
API_HOST=0.0.0.0
API_PORT=${BACKEND_PORT}
DEBUG=false

# CORS Configuration
ALLOWED_ORIGINS=["http://localhost:${FRONTEND_PORT}", "http://localhost:3000", "http://localhost:8080"]

# Email Configuration (if needed)
SMTP_HOST=${SMTP_HOST:-smtp.gmail.com}
SMTP_PORT=${SMTP_PORT:-587}
SMTP_USER=${SMTP_USER:-}
SMTP_PASSWORD=${SMTP_PASSWORD:-}
FROM_EMAIL=${FROM_EMAIL:-noreply@edu-flow.com}

# Logging Configuration
LOG_LEVEL=INFO
LOG_FILE=logs/edu_flow.log
EOF
fi

# Build backend image
log_info "Building backend Docker image..."
docker build -t ${BACKEND_NAME}:latest .

# Stop existing backend container
if docker ps -q -f name=${BACKEND_NAME} | grep -q .; then
    log_info "Stopping existing backend container..."
    docker stop ${BACKEND_NAME}
fi

# Remove existing backend container
if docker ps -aq -f name=${BACKEND_NAME} | grep -q .; then
    log_info "Removing existing backend container..."
    docker rm ${BACKEND_NAME}
fi

# Deploy backend
log_info "Starting backend service..."
docker run -d \
    --name ${BACKEND_NAME} \
    --restart unless-stopped \
    -p ${BACKEND_PORT}:8001 \
    -v "$(pwd)/logs:/app/logs" \
    -v "$(pwd)/data:/app/data" \
    -v "$(pwd)/uploads:/app/uploads" \
    -e DATABASE_URL="postgresql+asyncpg://${DB_USER}:${DB_PASSWORD}@${DB_HOST}:${DB_PORT}/${DB_NAME}" \
    -e REDIS_URL="redis://${DB_HOST}:${DB_PORT:-6379}/0" \
    -e SECRET_KEY=${SECRET_KEY:-$(openssl rand -hex 32)} \
    -e ACCESS_TOKEN_EXPIRE_MINUTES=30 \
    -e REFRESH_TOKEN_EXPIRE_DAYS=7 \
    -e API_HOST=0.0.0.0 \
    -e API_PORT=8001 \
    -e DEBUG=false \
    -e LOG_LEVEL=INFO \
    -e LOG_FILE=/app/logs/edu_flow.log \
    ${BACKEND_NAME}:latest

cd ..

# Build and deploy frontend
log_step "Deploying frontend..."
cd frontend

# Copy environment file if it doesn't exist
if [ ! -f ".env" ]; then
    log_info "Creating frontend .env file..."
    cat > .env << EOF
# API Configuration
API_BASE_URL=http://${DB_HOST}:${BACKEND_PORT}
API_TIMEOUT=30

# App Configuration
APP_NAME=Edu-Flow
APP_VERSION=1.0.0
DEBUG=false

# Firebase Configuration (if needed)
FIREBASE_API_KEY=${FIREBASE_API_KEY:-}
FIREBASE_AUTH_DOMAIN=${FIREBASE_AUTH_DOMAIN:-}
FIREBASE_PROJECT_ID=${FIREBASE_PROJECT_ID:-}
FIREBASE_STORAGE_BUCKET=${FIREBASE_STORAGE_BUCKET:-}
FIREBASE_MESSAGING_SENDER_ID=${FIREBASE_MESSAGING_SENDER_ID:-}
FIREBASE_APP_ID=${FIREBASE_APP_ID:-}

# CDN Configuration (if needed)
CDN_URL=${CDN_URL:-}
CDN_ENABLED=${CDN_ENABLED:-false}

# Analytics Configuration (if needed)
ANALYTICS_ENABLED=${ANALYTICS_ENABLED:-false}
ANALYTICS_ID=${ANALYTICS_ID:-}
EOF
fi

# Build Flutter web application
log_info "Building Flutter web application..."
flutter clean
flutter pub get
flutter build web --release --web-renderer canvaskit

# Build frontend image
log_info "Building frontend Docker image..."
docker build -t ${FRONTEND_NAME}:latest .

# Stop existing frontend container
if docker ps -q -f name=${FRONTEND_NAME} | grep -q .; then
    log_info "Stopping existing frontend container..."
    docker stop ${FRONTEND_NAME}
fi

# Remove existing frontend container
if docker ps -aq -f name=${FRONTEND_NAME} | grep -q .; then
    log_info "Removing existing frontend container..."
    docker rm ${FRONTEND_NAME}
fi

# Deploy frontend
log_info "Starting frontend service..."
docker run -d \
    --name ${FRONTEND_NAME} \
    --restart unless-stopped \
    -p ${FRONTEND_PORT}:80 \
    -v "$(pwd)/build/web:/usr/share/nginx/html" \
    -v "$(pwd)/logs:/var/log/nginx" \
    -e API_BASE_URL=http://${DB_HOST}:${BACKEND_PORT} \
    -e APP_NAME=Edu-Flow \
    -e APP_VERSION=1.0.0 \
    -e DEBUG=false \
    nginx:alpine

cd ..

# Wait for services to start
log_step "Waiting for services to start..."
sleep 15

# Check if services are running
log_step "Checking service status..."

# Check backend
if docker ps -q -f name=${BACKEND_NAME} | grep -q .; then
    log_info "✅ Backend is running on port ${BACKEND_PORT}"
    
    # Check backend health
    if curl -f http://localhost:${BACKEND_PORT}/health > /dev/null 2>&1; then
        log_info "✅ Backend health check passed"
    else
        log_warn "⚠️ Backend health check failed"
    fi
    
    # Check backend API docs
    if curl -f http://localhost:${BACKEND_PORT}/docs > /dev/null 2>&1; then
        log_info "✅ Backend API documentation is accessible"
    else
        log_warn "⚠️ Backend API documentation not accessible"
    fi
else
    log_error "❌ Backend failed to start"
    exit 1
fi

# Check frontend
if docker ps -q -f name=${FRONTEND_NAME} | grep -q .; then
    log_info "✅ Frontend is running on port ${FRONTEND_PORT}"
    
    # Check frontend accessibility
    if curl -f http://localhost:${FRONTEND_PORT} > /dev/null 2>&1; then
        log_info "✅ Frontend is accessible"
    else
        log_warn "⚠️ Frontend not accessible yet"
    fi
else
    log_error "❌ Frontend failed to start"
    exit 1
fi

# Run smoke tests
log_step "Running smoke tests..."
log_info "Testing backend API connectivity..."
curl -f http://localhost:${BACKEND_PORT}/health > /dev/null 2>&1
if [ $? -eq 0 ]; then
    log_info "✅ Backend API connectivity test passed"
else
    log_warn "⚠️ Backend API connectivity test failed"
fi

log_info "Testing frontend connectivity..."
curl -f http://localhost:${FRONTEND_PORT} > /dev/null 2>&1
if [ $? -eq 0 ]; then
    log_info "✅ Frontend connectivity test passed"
else
    log_warn "⚠️ Frontend connectivity test failed"
fi

# Create admin user
log_step "Creating admin user..."
ADMIN_CREATED=false
BACKEND_URL="http://localhost:${BACKEND_PORT}"

# Try to create admin user
curl -X POST "${BACKEND_URL}/api/v1/auth/register" \
    -H "Content-Type: application/json" \
    -d '{
        "email": "admin@example.com",
        "password": "Admin123!",
        "name": "Administrator",
        "role": "admin"
    }' > /dev/null 2>&1 && ADMIN_CREATED=true

if [ "$ADMIN_CREATED" = true ]; then
    log_info "✅ Admin user created (admin@example.com / Admin123!)"
else
    log_warn "⚠️ Admin user creation failed (might already exist)"
fi

# Print deployment summary
echo ""
echo "🎉 Deployment completed successfully!"
echo "============================================"
echo "🌐 Frontend URL: http://localhost:${FRONTEND_PORT}"
echo "🔗 Backend URL: http://localhost:${BACKEND_PORT}"
echo "📚 Backend API Docs: http://localhost:${BACKEND_PORT}/docs"
echo "🏥 Health Check: http://localhost:${BACKEND_PORT}/health"
echo ""
echo "🔧 Default Admin Account:"
echo "   Email: admin@example.com"
echo "   Password: Admin123!"
echo ""
echo "📋 Management Commands:"
echo "   - View backend logs: docker logs -f ${BACKEND_NAME}"
echo "   - View frontend logs: docker logs -f ${FRONTEND_NAME}"
echo "   - Stop backend: docker stop ${BACKEND_NAME}"
echo "   - Stop frontend: docker stop ${FRONTEND_NAME}"
echo "   - Restart backend: docker restart ${BACKEND_NAME}"
echo "   - Restart frontend: docker restart ${FRONTEND_NAME}"
echo ""
echo "🔗 Database Configuration:"
echo "   Host: ${DB_HOST}:${DB_PORT}"
echo "   Database: ${DB_NAME}"
echo "   User: ${DB_USER}"
echo ""
echo "📊 Monitoring:"
echo "   - Docker status: docker ps -a"
echo "   - System resources: docker stats"
echo "   - Container logs: docker logs [container_name]"
echo ""
echo "🚀 Next Steps:"
echo "   1. Open http://localhost:${FRONTEND_PORT} to access the application"
echo "   2. Use the admin credentials to log in"
echo "   3. Explore the API documentation at http://localhost:${BACKEND_PORT}/docs"
echo "   4. Monitor the logs for any issues"
echo ""