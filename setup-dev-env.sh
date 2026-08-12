#!/bin/bash

# Development Environment Setup Script
# For Edu-Flow Migration Project

echo "Setting up development environment for Edu-Flow..."

# Install Python dependencies
echo "Installing Python dependencies..."
pip install -r backend/src/requirements.txt

# Install Rust toolchain (for future phases)
echo "Installing Rust toolchain..."
curl --proto '=https' --tlsv1.2 -sSf https://sh.rustup.rs | sh -s -- -y
source ~/.cargo/env

# Install Flutter SDK
echo "Installing Flutter SDK..."
git clone https://github.com/flutter/flutter.git -b stable ~/flutter
export PATH="$PATH:$HOME/flutter/bin"
flutter doctor

# Install Node.js dependencies
echo "Installing Node.js dependencies..."
cd frontend
npm install
cd ..

# Set up MongoDB and Redis services
echo "Setting up database services..."
# Add commands to start MongoDB and Redis
# These can be: docker-compose up -d or service commands

echo "Environment setup completed!"
echo ""
echo "Next steps:"
echo "1. Configure environment variables in backend/src/config/.env"
echo "2. Set up database connections"
echo "3. Run backend tests: python -m pytest backend/tests/"
echo "4. Start development server: cd backend && uvicorn src.main:app --reload"