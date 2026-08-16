#!/bin/bash

# Frontend Setup Script for Edu-Flow

echo "Setting up Edu-Flow Frontend..."

# Install Flutter dependencies
echo "Installing Flutter dependencies..."
flutter pub get

# Create .env file if it doesn't exist
if [ ! -f .env ]; then
    cat > .env << EOF
# Backend API
API_BASE_URL=http://localhost:8000
API_TIMEOUT=30

# AI Services
AI_SERVICE_URL=http://localhost:3000

# Storage
PREFS_KEY=edu_flow_prefs
ENCRYPTION_KEY=your-encryption-key-change-in-production

# Theme
PRIMARY_COLOR=#3b82f6
SECONDARY_COLOR=#6366f1

# Feature Flags
ENABLE_DARK_MODE=true
ENABLE_OFFLINE_SUPPORT=true
ENABLE_ANALYTICS=true
EOF
    echo "Created .env file"
fi

# Create build directories
mkdir -p build/web assets/images assets/icons assets/fonts

echo "Frontend setup complete!"
echo "To start the frontend: flutter run"